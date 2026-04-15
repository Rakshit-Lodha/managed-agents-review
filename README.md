# 🔍 Feedback Intelligence Agent

A conversational AI agent that pulls user feedback from multiple channels (Google Play, App Store, YouTube, X/Twitter) and delivers actionable product insights.

Built with the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/).

## Architecture

```
User Question
    │
    ▼
┌─────────────────────────────────┐
│   Feedback Intelligence Agent   │
│   (GPT-4o + System Prompt)      │
│                                 │
│   Session Memory (SQLite)       │
│   ─ remembers past analyses     │
│   ─ can compare across runs     │
├─────────────────────────────────┤
│   Tools:                        │
│   ├── fetch_playstore_reviews   │
│   ├── fetch_appstore_reviews    │
│   ├── fetch_youtube_feedback    │
│   └── fetch_x_mentions          │
└─────────────────────────────────┘
    │
    ▼
Structured Analysis:
  • Production Bugs (with version)
  • UX Complaints
  • Feature Requests
  • Positive Signals
  • Sentiment Trend
```

## Setup

```bash
# 1. Clone and enter the project
cd feedback-agent

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Usage

### Streamlit UI (recommended)
```bash
streamlit run app.py
```

### CLI (quick testing)
```bash
# Default full report
python agent.py

# Specific question
python agent.py "What are the top bugs on Play Store?"
```

### Python (embed in your code)
```python
import asyncio
from agent import run_agent

response = asyncio.run(run_agent("What are iOS users complaining about?"))
print(response)
```

## Configuration

Edit `config.py` to change the target app:

```python
GOOGLE_PLAY_APP_ID = "com.smartspends"    # Your Play Store app ID
APPSTORE_APP_ID = "1212752482"            # Your App Store app ID
YOUTUBE_HANDLE = "@ETMONEY"               # Your YouTube channel
X_HANDLE = "ETMONEY"                      # Your X/Twitter handle
```

## Adding New Sources (Roadmap)

Each new source is just a new `@function_tool`:

```python
# tools/reddit.py
@function_tool
def fetch_reddit_posts(subreddit: str = "etmoney", days: int = 7) -> str:
    """Fetch recent Reddit posts mentioning the app."""
    # Your Reddit scraping logic
    ...
```

Then add it to `tools/__init__.py` and it's automatically available to the agent.

For external services like Jira and Zoho, use MCP servers:

```python
from agents.mcp import MCPServerStreamableHttp

jira_server = MCPServerStreamableHttp(url="https://your-jira-mcp/mcp")

agent = Agent(
    tools=ALL_TOOLS,
    mcp_servers=[jira_server],  # Agent auto-discovers Jira tools
)
```

## Roadmap

- [x] Google Play Store reviews
- [x] Apple App Store reviews
- [x] YouTube comments
- [x] X (Twitter) mentions
- [ ] Reddit monitoring
- [ ] Zoho Desk tickets
- [ ] Jira ticket creation (via MCP)
- [ ] Scheduled daily reports
- [ ] Long-term memory (recurring issue tracking)
- [ ] Slack/WhatsApp alert integration
