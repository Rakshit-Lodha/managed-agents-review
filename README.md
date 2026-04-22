# Feedback Intelligence

Feedback Intelligence is a SaaS product for aggregating user feedback across public channels and turning it into product signals a team can act on. The current repository contains two main surfaces:

- A conversational feedback agent built on the OpenAI Agents SDK
- A desktop-first onboarding flow built with Next.js and a FastAPI preview backend

The product thesis is cross-channel correlation: the same issue showing up in Play Store reviews, App Store reviews, YouTube comments, and X mentions should be easier to spot, easier to prioritize, and easier to route.

Live app: https://managed-agents-review.onrender.com

## Current Product Scope

Current channels:

- Google Play Store
- Apple App Store
- YouTube
- X / Twitter

Current experiences:

- Streamlit chat UI for querying feedback conversationally
- FastAPI preview API for onboarding source verification
- Next.js onboarding flow with live enrichment for public sources

Planned next:

- Multi-tenant persistence
- YouTube onboarding preview
- Named chat sessions per tenant
- Scheduled daily digest
- Slack and Jira workflows

## Repo Structure

```text
.
├── agent.py                  # Core OpenAI agent and session-aware runner
├── app.py                    # Streamlit chat UI
├── backend/main.py           # FastAPI preview API for onboarding
├── config.py                 # Current single-tenant app configuration
├── turso_session.py          # Persistent session storage for agent memory
├── tools/                    # Source-specific feedback tools
│   ├── playstore.py
│   ├── appstore.py
│   ├── youtube.py
│   └── twitter.py
├── frontend/                 # Next.js onboarding frontend
│   └── app/
└── supabase/                 # Early auth / persistence work
```

## Architecture

### 1. Feedback agent

`agent.py` creates an OpenAI agent with:

- A strict analysis prompt for product feedback classification
- Function tools for Play Store, App Store, YouTube, and X
- Persistent memory via `TursoSession`

The agent is designed to classify relevant feedback into:

- P0 production bugs
- UX complaints
- Feature requests
- Positive signals
- Sentiment trend

It also applies a relevance filter before analysis so off-topic mentions do not poison the output.

### 2. Streamlit prototype UI

`app.py` is the current fastest way to test the agent interactively. It provides:

- A chat interface
- A user-controlled `session_id`
- Date-range injection into prompts
- Lightweight visual chat history in `st.session_state`

Important distinction:

- `st.session_state.messages` is only UI state
- `TursoSession` is the real conversation memory sent back to the model

### 3. Onboarding preview backend

`backend/main.py` exposes source verification endpoints used by the frontend:

- `GET /health`
- `GET /api/preview/playstore?url=...`
- `GET /api/preview/appstore?url=...`
- `GET /api/preview/x?url=...`

Behavior today:

- Play Store accepts a full URL or package id
- App Store accepts a full URL or numeric app id
- X accepts profile URLs, `@handle`, or bare handles
- X mention lookup is bounded to avoid expensive onboarding crawls

### 4. Next.js onboarding frontend

The onboarding frontend in `frontend/` is desktop-first and currently focused on the delight loop rather than persistence.

Current flow:

1. Name workspace
2. Connect public channels
3. Set baseline
4. Confirm ready state

Current behavior:

- Source cards for Play Store, App Store, and X
- Local React state only
- Live preview panel with idle, loading, success, and error states
- No tenant or source persistence yet

## Source Tooling

All feedback tools live in `tools/` and are registered through `tools/__init__.py`.

| Tool | Source | Notes |
| --- | --- | --- |
| `fetch_playstore_reviews` | Google Play | Uses `google-play-scraper` |
| `fetch_appstore_reviews` | App Store | Uses iTunes RSS / lookup APIs |
| `fetch_youtube_feedback` | YouTube | Uses YouTube Data API v3 |
| `fetch_x_mentions` | X / Twitter | Uses X API v2 |

Adding a new source is intentionally simple:

1. Create a new `@function_tool` in `tools/<source>.py`
2. Return structured JSON as a string
3. Export it via `tools/__init__.py`

The agent will automatically be able to call it once registered.

## Tech Stack

Backend and agent:

- Python
- OpenAI Agents SDK
- FastAPI
- Streamlit
- `libsql-client` for Turso-backed session persistence

Frontend:

- Next.js 14
- React 18
- TypeScript

## Environment Variables

Create a `.env` file in the repo root.

Required for the current stack:

- `OPENAI_API_KEY` - used by the OpenAI Agents SDK
- `YOUTUBE_API_KEY` - used for YouTube Data API requests
- `X_API_KEY` - bearer token for X API v2
- `TURSO_URL` - Turso database URL for agent memory
- `TURSO_AUTH_TOKEN` - Turso auth token

Frontend:

- `NEXT_PUBLIC_API_BASE` - optional override for the FastAPI base URL, defaults to `http://localhost:8000`

## Local Setup

### Python app

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend app

```bash
cd frontend
npm install
```

## Running the Project

### 1. Run the Streamlit feedback UI

```bash
streamlit run app.py
```

### 2. Run the agent from CLI

```bash
python agent.py
python agent.py "What are the top bugs?"
```

### 3. Run the FastAPI onboarding preview backend

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 4. Run the Next.js onboarding frontend

```bash
cd frontend
npm run dev
```

If you want a production-style run locally:

```bash
cd frontend
npm run build
npm run start -- -p 3002
```

## Current Limitations

- `config.py` is still hardcoded for ET Money and needs to move to tenant-backed persistence
- The onboarding flow does not yet write tenants, sources, or preferences to a database
- YouTube preview is not yet part of the onboarding experience
- X response caching is not fully implemented yet
- Streamlit remains the primary chat surface; the dashboard experience has not yet moved to Next.js

## Product and Design Direction

The product is not meant to feel like a generic analytics dashboard. The current design direction is a dark, editorial, signal-intelligence aesthetic:

- `Bebas Neue` for display typography
- `Syne` for body text
- `DM Mono` for system and data text
- Near-black background with electric cyan and amber accents

That direction is documented in `AGENTS.md` and should be treated as the project’s visual standard for frontend work.

## Deployment Notes

- `render.yaml` is present for deployment configuration
- `runtime.txt` pins the Python runtime for hosted environments
- `supabase/` contains early migration work for persistence and auth

## Roadmap

- Tenant model and onboarding persistence
- YouTube onboarding preview
- Cached X ingestion with delta fetching
- Multi-session chat per tenant
- Scheduled daily digests
- Slack delivery
- Jira ticket creation through MCP

## License

No license file is currently included in this repository.
