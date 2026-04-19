import os
import json
import requests
from datetime import datetime, timedelta
from typing import Annotated
from urllib.parse import unquote
from agents import function_tool
from config import X_HANDLE, DEFAULT_DAYS_LOOKBACK


def _get_bearer_token() -> str:
    token = os.getenv("X_API_KEY")
    if not token:
        raise ValueError("X_API_KEY not set in environment")
    return unquote(token)


def _get_user_id(handle: str) -> str:
    bearer = _get_bearer_token()
    url = f"https://api.x.com/2/users/by/username/{handle}"
    headers = {"Authorization": f"Bearer {bearer}"}
    params = {"user.fields": "created_at,description,public_metrics,verified"}

    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if "data" not in data:
        raise ValueError(f"User not found: {handle}. Errors: {data.get('errors', [])}")

    return data["data"]["id"]


@function_tool
def fetch_x_mentions(
    days: Annotated[int, "Number of days to look back for mentions"] = DEFAULT_DAYS_LOOKBACK,
    handle: Annotated[str, "X/Twitter handle (without @)"] = X_HANDLE,
) -> str:
    """Fetch recent X (Twitter) mentions of the brand.
    Use this when the user asks about Twitter/X mentions, social media complaints,
    tweets about the app, or what people are saying on X/Twitter."""

    try:
        bearer = _get_bearer_token()
        user_id = _get_user_id(handle)

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        url = f"https://api.x.com/2/users/{user_id}/mentions"
        headers = {"Authorization": f"Bearer {bearer}"}
        params = {
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username,verified",
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "max_results": 100,
        }

        all_posts = []
        # Map author IDs to usernames from includes
        author_map = {}

        while True:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Build author lookup from includes
            for user in data.get("includes", {}).get("users", []):
                author_map[user["id"]] = user.get("username", "unknown")

            if "data" in data:
                all_posts.extend(data["data"])

            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break
            params["pagination_token"] = next_token

        mentions = []
        for post in all_posts:
            mentions.append({
                "source": "x_twitter",
                "author": author_map.get(post.get("author_id"), "unknown"),
                "text": post["text"],
                "created_at": post["created_at"],
                "likes": post.get("public_metrics", {}).get("like_count", 0),
                "retweets": post.get("public_metrics", {}).get("retweet_count", 0),
                "replies": post.get("public_metrics", {}).get("reply_count", 0),
            })

        return json.dumps({
            "source": "x_twitter",
            "handle": handle,
            "total_mentions": len(mentions),
            "period": f"Last {days} days",
            "mentions": mentions,
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "source": "x_twitter"})
