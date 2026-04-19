"""
Configuration for the Feedback Intelligence Agent.
Update these values for your app/brand.
"""

# ── Company Identity ─────────────────────────────────────────
COMPANY_NAME = "ET Money"
COMPANY_DESCRIPTION = (
    "ET Money is an Indian personal finance app that lets retail investors "
    "invest in mutual funds (direct plans, SIP), track expenses, buy term and "
    "health insurance, check credit scores, and access NPS. It is owned by "
    "HDFC Bank. The app itself — not the third-party funds or financial products "
    "it distributes — is the subject of feedback analysis."
)
COMPANY_PRODUCTS = [
    "mutual fund investments (direct plans, SIP)",
    "expense tracking",
    "term insurance & health insurance",
    "NPS (National Pension System)",
    "credit score monitoring",
    "loan discovery",
]

# ── App Identifiers ──────────────────────────────────────────
GOOGLE_PLAY_APP_ID = "com.smartspends"           # ET Money
APPSTORE_APP_ID = "1212752482"                    # ET Money iOS
YOUTUBE_HANDLE = "@ETMONEY"
X_HANDLE = "ETMONEY"

# ── Defaults ─────────────────────────────────────────────────
DEFAULT_REVIEW_COUNT = 50
DEFAULT_DAYS_LOOKBACK = 7
COUNTRY = "in"
LANGUAGE = "en"
