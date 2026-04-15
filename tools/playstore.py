import json
from typing import Annotated
from agents import function_tool
from google_play_scraper import reviews, Sort
from config import GOOGLE_PLAY_APP_ID, DEFAULT_REVIEW_COUNT, COUNTRY, LANGUAGE


@function_tool
def fetch_playstore_reviews(
    count: Annotated[int, "Number of reviews to fetch (max 200)"] = DEFAULT_REVIEW_COUNT,
    app_id: Annotated[str, "Google Play app ID"] = GOOGLE_PLAY_APP_ID,
) -> str:
    """Fetch the most recent Google Play Store reviews for the app.
    Use this when the user asks about Play Store feedback, Android reviews,
    Google Play ratings, or app store sentiment from Android users."""

    try:
        result, _ = reviews(
            app_id,
            lang=LANGUAGE,
            country=COUNTRY,
            sort=Sort.NEWEST,
            count=min(count, 200),
        )

        all_reviews = []
        for r in result:
            all_reviews.append({
                "source": "google_play",
                "author": r["userName"],
                "rating": r["score"],
                "content": r["content"],
                "version": r.get("reviewCreatedVersion"),
                "date": r["at"].strftime("%Y-%m-%d"),
                "thumbs_up": r.get("thumbsUpCount", 0),
            })

        return json.dumps({
            "total_reviews": len(all_reviews),
            "app_id": app_id,
            "avg_rating": round(sum(r["rating"] for r in all_reviews) / len(all_reviews), 2) if all_reviews else 0,
            "reviews": all_reviews,
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "source": "google_play"})
