from tools.playstore import fetch_playstore_reviews
from tools.appstore import fetch_appstore_reviews
from tools.youtube import fetch_youtube_feedback
from tools.twitter import fetch_x_mentions

ALL_TOOLS = [
    fetch_playstore_reviews,
    fetch_appstore_reviews,
    fetch_youtube_feedback,
    fetch_x_mentions,
]
