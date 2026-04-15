import os
import json
import isodate
from datetime import datetime, timedelta
from typing import Annotated
from agents import function_tool
from googleapiclient.discovery import build
from config import YOUTUBE_HANDLE, DEFAULT_DAYS_LOOKBACK


def _get_youtube_client():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY not set in environment")
    return build("youtube", "v3", developerKey=api_key)


def _find_channel_id(handle: str) -> str:
    yt = _get_youtube_client()
    response = yt.channels().list(forHandle=handle, part="id,snippet").execute()
    if not response.get("items"):
        raise ValueError(f"No channel found for handle: {handle}")
    return response["items"][0]["id"]


def _get_comments_for_video(video_id: str, max_comments: int = 50) -> list:
    yt = _get_youtube_client()
    all_comments = []
    next_page_token = None

    while len(all_comments) < max_comments:
        response = yt.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, max_comments - len(all_comments)),
            pageToken=next_page_token,
            textFormat="plainText",
            order="time",
        ).execute()

        for item in response.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            all_comments.append({
                "author": top.get("authorDisplayName"),
                "text": top.get("textDisplay"),
                "published_at": top.get("publishedAt"),
                "like_count": top.get("likeCount", 0),
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return all_comments


@function_tool
def fetch_youtube_feedback(
    days: Annotated[int, "Number of days to look back for videos"] = DEFAULT_DAYS_LOOKBACK,
    handle: Annotated[str, "YouTube channel handle (e.g. '@ETMONEY')"] = YOUTUBE_HANDLE,
    max_comments_per_video: Annotated[int, "Max comments to fetch per video"] = 30,
) -> str:
    """Fetch recent YouTube video comments for the brand's channel.
    Use this when the user asks about YouTube feedback, video comments,
    audience sentiment on YouTube, or what people are saying on the channel."""

    try:
        channel_id = _find_channel_id(handle)
        yt = _get_youtube_client()

        after = (datetime.utcnow() - timedelta(days=days)).isoformat("T") + "Z"

        search = yt.search().list(
            channelId=channel_id,
            publishedAfter=after,
            type="video",
            order="date",
            part="id",
            maxResults=10,
        ).execute()

        video_ids = [item["id"]["videoId"] for item in search.get("items", [])]

        if not video_ids:
            return json.dumps({"source": "youtube", "message": "No videos found in this period", "videos": []})

        stats = yt.videos().list(
            id=",".join(video_ids),
            part="snippet,statistics,contentDetails",
        ).execute()

        videos = []
        for v in stats.get("items", []):
            vid_id = v["id"]
            comments = _get_comments_for_video(vid_id, max_comments_per_video)

            videos.append({
                "title": v["snippet"]["title"],
                "video_id": vid_id,
                "link": f"https://youtube.com/watch?v={vid_id}",
                "views": int(v["statistics"].get("viewCount", 0)),
                "likes": int(v["statistics"].get("likeCount", 0)),
                "comment_count": int(v["statistics"].get("commentCount", 0)),
                "published_date": v["snippet"].get("publishedAt"),
                "duration_secs": isodate.parse_duration(v["contentDetails"]["duration"]).total_seconds(),
                "comments": comments,
            })

        return json.dumps({
            "source": "youtube",
            "channel": handle,
            "total_videos": len(videos),
            "videos": videos,
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "source": "youtube"})
