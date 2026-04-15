import json
import requests
from typing import Annotated
from agents import function_tool
from config import APPSTORE_APP_ID, COUNTRY


@function_tool
def fetch_appstore_reviews(
    app_id: Annotated[str, "Apple App Store app ID"] = APPSTORE_APP_ID,
    country: Annotated[str, "Country code (e.g. 'in', 'us')"] = COUNTRY,
) -> str:
    """Fetch the most recent Apple App Store reviews for the app.
    Use this when the user asks about App Store feedback, iOS reviews,
    iPhone/iPad user complaints, or Apple app ratings."""

    try:
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortby=mostRecent/json"

        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }, timeout=15)
        response.raise_for_status()

        data = response.json()
        entries = data["feed"].get("entry", [])

        all_reviews = []
        for entry in entries:
            # Skip the first entry if it's the app metadata, not a review
            if "im:rating" not in entry:
                continue

            all_reviews.append({
                "source": "app_store",
                "author": entry["author"]["name"]["label"],
                "rating": int(entry["im:rating"]["label"]),
                "title": entry["title"]["label"],
                "content": entry["content"]["label"],
                "date": entry["updated"]["label"][:10],
                "version": entry["im:version"]["label"],
            })

        return json.dumps({
            "total_reviews": len(all_reviews),
            "app_id": app_id,
            "avg_rating": round(sum(r["rating"] for r in all_reviews) / len(all_reviews), 2) if all_reviews else 0,
            "reviews": all_reviews,
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "source": "app_store"})
