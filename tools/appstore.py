import json
import requests
from datetime import date, timedelta
from typing import Annotated
from agents import function_tool
from config import APPSTORE_APP_ID, DEFAULT_DAYS_LOOKBACK, COUNTRY


@function_tool
def fetch_appstore_reviews(
    start_date: Annotated[str, "Start date YYYY-MM-DD. Filters reviews on or after this date."] = "",
    end_date: Annotated[str, "End date YYYY-MM-DD. Filters reviews on or before this date. Defaults to today."] = "",
    days: Annotated[int, "Days to look back from today. Used only if start_date is not provided."] = DEFAULT_DAYS_LOOKBACK,
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

        if start_date:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date) if end_date else date.today()
        else:
            end = date.today()
            start = end - timedelta(days=days)

        all_reviews = []
        for entry in entries:
            if "im:rating" not in entry:
                continue
            review_date = date.fromisoformat(entry["updated"]["label"][:10])
            if not (start <= review_date <= end):
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

        period = f"{start.isoformat()} to {end.isoformat()}"
        return json.dumps({
            "source": "app_store",
            "total_reviews": len(all_reviews),
            "period": period,
            "app_id": app_id,
            "avg_rating": round(sum(r["rating"] for r in all_reviews) / len(all_reviews), 2) if all_reviews else 0,
            "reviews": all_reviews,
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "source": "app_store"})
