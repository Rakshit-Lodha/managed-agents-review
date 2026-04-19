from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qs, unquote, unquote as url_unquote, urlparse

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google_play_scraper import app as playstore_app

load_dotenv()

app = FastAPI(title="Feedback Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/preview/playstore")
def preview_playstore(url: str = Query(..., min_length=3)) -> dict[str, Any]:
    app_id = _parse_playstore_id(url)
    if not app_id:
        raise HTTPException(status_code=400, detail="Could not find a Play Store app id in that URL.")

    try:
        details = playstore_app(app_id, lang="en", country="in")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Play Store lookup failed: {exc}") from exc

    return {
        "source": "playstore",
        "app_id": app_id,
        "name": details.get("title"),
        "developer": details.get("developer"),
        "icon": details.get("icon"),
        "rating": _round(details.get("score")),
        "reviews": details.get("reviews"),
        "installs": details.get("installs"),
        "category": details.get("genre"),
        "version": details.get("version"),
        "status": "Verified on Google Play",
        "delight": "Android feedback can be pulled as soon as onboarding finishes.",
    }


@app.get("/api/preview/appstore")
def preview_appstore(url: str = Query(..., min_length=3), country: str = "in") -> dict[str, Any]:
    app_id = _parse_appstore_id(url)
    if not app_id:
        raise HTTPException(status_code=400, detail="Could not find an App Store app id in that URL.")

    try:
        response = requests.get(
            "https://itunes.apple.com/lookup",
            params={"id": app_id, "country": country},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"App Store lookup failed: {exc}") from exc

    results = payload.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="No App Store app found for that id.")

    details = results[0]
    return {
        "source": "appstore",
        "app_id": app_id,
        "name": details.get("trackName"),
        "developer": details.get("sellerName") or details.get("artistName"),
        "icon": details.get("artworkUrl100"),
        "rating": _round(details.get("averageUserRating")),
        "reviews": details.get("userRatingCount"),
        "category": details.get("primaryGenreName"),
        "version": details.get("version"),
        "status": "Verified on App Store",
        "delight": "iOS reviews are ready to join your cross-channel report.",
    }


@app.get("/api/preview/x")
def preview_x(url: str = Query(..., min_length=2), days: int = 7) -> dict[str, Any]:
    handle = _parse_x_handle(url)
    if not handle:
        raise HTTPException(status_code=400, detail="Could not find an X handle in that URL.")

    bearer = url_unquote(os.getenv("X_API_KEY") or "")
    if not bearer:
        raise HTTPException(status_code=503, detail="X_API_KEY is not configured on the backend.")

    headers = {"Authorization": f"Bearer {bearer}"}

    try:
        user_response = requests.get(
            f"https://api.x.com/2/users/by/username/{handle}",
            headers=headers,
            params={
                "user.fields": "created_at,description,profile_image_url,public_metrics,verified",
            },
            timeout=15,
        )
        user_response.raise_for_status()
        user_payload = user_response.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"X profile lookup failed: {exc}") from exc

    user = user_payload.get("data")
    if not user:
        raise HTTPException(status_code=404, detail="No X profile found for that handle.")

    mentions = _count_recent_mentions(user["id"], headers, days)
    metrics = user.get("public_metrics", {})

    return {
        "source": "x",
        "id": user.get("id"),
        "name": user.get("name"),
        "username": user.get("username"),
        "description": user.get("description"),
        "avatar": user.get("profile_image_url"),
        "verified": user.get("verified", False),
        "followers": metrics.get("followers_count"),
        "following": metrics.get("following_count"),
        "tweet_count": metrics.get("tweet_count"),
        "listed_count": metrics.get("listed_count"),
        "mentions_7d": mentions,
        "status": "Connected to X",
        "delight": f"Found recent social signal from the last {days} days.",
    }


def _parse_playstore_id(value: str) -> str | None:
    cleaned = value.strip()
    parsed = urlparse(cleaned)
    query_id = parse_qs(parsed.query).get("id", [None])[0]
    if query_id:
        return query_id.strip()
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+", cleaned):
        return cleaned
    return None


def _parse_appstore_id(value: str) -> str | None:
    cleaned = value.strip()
    match = re.search(r"/id(\d+)", cleaned)
    if match:
        return match.group(1)
    match = re.search(r"(^|[?&])id=(\d+)", cleaned)
    if match:
        return match.group(2)
    if cleaned.isdigit():
        return cleaned
    return None


def _parse_x_handle(value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned:
        return None

    parsed = urlparse(cleaned if "://" in cleaned else f"https://x.com/{cleaned}")
    path = unquote(parsed.path).strip("/")
    handle = path.split("/")[0] if path else cleaned
    handle = handle.removeprefix("@").strip()

    if re.fullmatch(r"[A-Za-z0-9_]{1,15}", handle):
        return handle
    return None


def _count_recent_mentions(user_id: str, headers: dict[str, str], days: int) -> int | None:
    start_time = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 30)))
    params = {
        "tweet.fields": "created_at",
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_results": 100,
    }

    total = 0
    try:
        for _ in range(5):
            response = requests.get(
                f"https://api.x.com/2/users/{user_id}/mentions",
                headers=headers,
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            total += int(data.get("meta", {}).get("result_count", len(data.get("data", []))))
            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break
            params["pagination_token"] = next_token
    except requests.RequestException:
        return None

    return total


def _round(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None
