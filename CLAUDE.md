# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What We're Building

**Feedback Intelligence** — a SaaS product that aggregates user feedback from multiple channels (app stores, social, support desks) and delivers actionable product insights to PMs and founders. The core value is cross-channel correlation: surfacing when the same issue appears on Play Store *and* X *and* Zoho Desk, and routing that signal to the right place (Jira ticket, Slack alert, daily digest).

**Target users:** Small companies and enterprises who need a unified view of what users are saying, without manually checking 5 different platforms every morning.

**Long-term vision:**
- **V1 (current):** Play Store + App Store + YouTube + X → conversational analysis + daily digest
- **V2:** Zoho Desk + Freshdesk integration (support ticket layer — the key differentiator)
- **V3:** Jira ticket creation via MCP, Slack digest notifications, scheduled daily reports

## Current Scope & Status

### Done
- Core agent built on OpenAI Agents SDK (GPT-4o) with 4 feedback tools
- Streamlit chat UI with session memory via `SQLiteSession` (persisted in `feedback_agent_memory.db`)
- Tools for Play Store (scraper), App Store (iTunes RSS), YouTube (Data API v3), X/Twitter (API v2)
- Analysis framework: bugs, UX complaints, feature requests, positive signals, sentiment trend
- CLI mode for quick testing
- Wireframes and design system for onboarding flow (in Pencil — 4-screen dark UI with glassmorphism)
- **Desktop-first Next.js onboarding frontend** in `frontend/`
  - 4-step flow: Name workspace → Connect public channels → Set baseline → Ready
  - Left rail shows setup progress and live source count
  - Source cards support Play Store, App Store, and X
  - Inputs use local React state; no tenant is persisted yet
  - Live preview panel changes through idle/loading/error/success states
- **FastAPI onboarding preview API** in `backend/main.py`
  - `GET /api/preview/playstore?url=...`
  - `GET /api/preview/appstore?url=...`
  - `GET /api/preview/x?url=...`
  - `GET /health`
  - CORS allows localhost/127.0.0.1 dev ports via regex
- **Onboarding delight behavior**
  - Play Store URL resolves to app name, developer, icon, rating, review count, installs, category, version
  - App Store URL resolves to app name, developer, icon, rating, review count, category, version
  - X URL/handle resolves to profile name, username, avatar, followers, tweet count, and recent mentions from the last 7 days
  - The goal is to make each pasted source feel like immediate progress, not just form entry

### In Progress
- **Multi-tenant architecture** — `config.py` is currently hardcoded for ET Money (MVP test app). Needs a `tenants` DB table so multiple companies can onboard independently.
- **Client onboarding persistence** — the frontend now has the onboarding experience and live source enrichment, but does not yet write tenants/sources/preferences to a database.
- **X API response caching** — to control API costs, raw posts should be stored in SQLite with `(handle, post_id, created_at)` and only delta-fetched on subsequent calls.

### Planned Next
- Improve onboarding visual design now that the delight loop is working:
  - stronger verified-state animation
  - more polished preview cards
  - better empty/loading states
  - clearer "what happens next" final screen
- Add tenant persistence behind onboarding
- Add YouTube source preview to onboarding
- Named chat sessions (multiple conversations per tenant, not just one `session_id`)
- Cron job for 6am daily digest
- Slack webhook for digest delivery

## Commands

```bash
# Install dependencies (use a venv)
pip install -r requirements.txt

# Run the Streamlit UI
streamlit run app.py

# Run the agent from CLI
python agent.py                          # default full report
python agent.py "What are the top bugs?" # specific query

# Run the FastAPI preview backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Run the Next.js onboarding frontend
cd frontend
npm install
npm run build
npm run start -- -p 3002
```

## Environment Variables

Requires a `.env` file with:
- `OPENAI_API_KEY` — used by the OpenAI Agents SDK
- `YOUTUBE_API_KEY` — YouTube Data API v3
- `X_API_KEY` — X/Twitter API bearer token (per-post pricing — cache responses aggressively)

## Architecture

**Entry points:**
- `app.py` — Streamlit chat UI. Manages chat history in `st.session_state`, calls `agent.py` for each query.
- `agent.py` — Core agent definition. Creates an OpenAI `Agent` (GPT-4o) with a system prompt and tool list. Uses `SQLiteSession` for persistent conversation memory stored in `feedback_agent_memory.db`. Exposes `run_agent()` (async, returns string) and `run_agent_streamed()` (async generator).
- `backend/main.py` — FastAPI preview backend for onboarding source enrichment. It is not yet the main agent API.
- `frontend/app/page.tsx` — desktop-first onboarding UI. Calls FastAPI preview endpoints from the browser.
- `frontend/app/globals.css` — onboarding visual system and layout.

**Two layers of memory — important distinction:**
- `st.session_state.messages` — purely visual, renders chat bubbles, gone on refresh
- `SQLiteSession` — the real memory sent to GPT-4o each turn; full history, no summarization; scoped by `session_id`

**Tools (`tools/` directory):**
Each tool is a `@function_tool`-decorated function that fetches feedback from one source and returns a JSON string. All tools are registered in `tools/__init__.py` via the `ALL_TOOLS` list.

| Tool | Source | API/Library |
|------|--------|-------------|
| `fetch_playstore_reviews` | Google Play | `google-play-scraper` (no API key needed) |
| `fetch_appstore_reviews` | Apple App Store | iTunes RSS feed (no API key needed) |
| `fetch_youtube_feedback` | YouTube comments | `google-api-python-client` (needs `YOUTUBE_API_KEY`) |
| `fetch_x_mentions` | X/Twitter mentions | X API v2 REST (needs `X_API_KEY`) |

**Configuration (`config.py`):**
Currently hardcoded for ET Money (MVP). Will be replaced by a `tenants` table once multi-tenant work begins. Fields: Play Store app ID, App Store app ID, YouTube handle, X handle, default review count, lookback days, country/language.

**Onboarding preview backend (`backend/main.py`):**
- Play Store parsing accepts a full Google Play URL or package name and extracts `id=...`.
- App Store parsing accepts a full App Store URL or numeric app id and extracts `/id...`.
- X parsing accepts `https://x.com/<handle>`, `https://twitter.com/<handle>`, `@handle`, or `handle`.
- X mention count is bounded: the backend pages through up to 5 pages / 500 mentions to avoid turning onboarding into an expensive crawl.
- Frontend default API base is `http://localhost:8000`; override with `NEXT_PUBLIC_API_BASE`.

## Key Architectural Decisions

- **URL parsing on onboarding:** Users paste full Play Store / App Store URLs; backend extracts the app ID. YouTube and X take handles directly (`@ETMONEY`, `ETMONEY`).
- **No user-facing API keys:** YouTube and X credentials are platform-owned, not collected from customers during onboarding.
- **Onboarding as delight loop:** Onboarding should not feel like a static setup form. Every pasted source should produce immediate feedback: loading state → verified card → concrete metrics → "ready for report" copy.
- **Frontend/backend split:** Product onboarding is now Next.js + FastAPI, not Streamlit. Streamlit remains useful for the prototype chat UI until the dashboard/chat experience moves to Next.js.
- **X caching strategy:** Store raw posts in SQLite with post_id as dedup key. On each fetch, only request posts newer than the latest cached timestamp for that handle.
- **MCP for Jira:** When Jira integration arrives, use MCP server (`MCPServerStreamableHttp`) rather than building a custom integration — the agent auto-discovers tools.

## Adding a New Feedback Source

1. Create `tools/<source>.py` with a `@function_tool`-decorated function returning JSON
2. Import and add it to `ALL_TOOLS` in `tools/__init__.py`
3. The agent automatically discovers and uses new tools

For external services (Jira, Zoho), prefer MCP servers over direct API integrations.

---

## Frontend Design System

The marketing page (`marketing.html`) and all future frontend work for this product follows a specific, non-negotiable aesthetic. These are the principles — not suggestions.

### Visual Identity

| Element | Choice | Reason |
|---------|--------|--------|
| Display font | `Bebas Neue` | Tall, editorial, powerful — makes words into architecture |
| Body font | `Syne` | Geometric, distinctive, human |
| Data/mono font | `DM Mono` | Technical register for metrics, code, labels |
| Background | `#04060F` (near-black) | Signal-in-the-dark aesthetic; not pure black |
| Primary accent | `#00FFD1` (electric cyan) | Represents signal, insight, action |
| Warning accent | `#F5A623` (amber) | Represents pain, urgency, the problem state |
| Text | `#F0EDE8` (warm off-white) | Softer than pure white; less harsh on dark bg |

### Color Has a Job, Not Just a Vibe

- **Cyan** appears on: CTAs, verified states, Rivue-branded elements, positive signals, interactive hover states
- **Amber** appears on: pain points, warning badges, notification dots, the "before Rivue" state
- **Near-black** is the canvas — the noise the product cuts through

Never introduce purple, blue-purple gradients, or pastel schemes. This product is a signal intelligence tool, not a productivity app.

### Design Principles

**1. Commit to one extreme aesthetic — no hedging.**
Every element must reinforce the same story. If the story is "radar/signal intelligence," then the hero is a radar, the colors are signal-green and warning-amber, and the font is editorial and powerful. Split aesthetics = no aesthetic.

**2. Make the product feel alive on load.**
Animations should run before the user scrolls. Floating pills, sweeping radars, pulsing dots — the page should already be *doing something* when it arrives. This creates the subconscious sense that the product itself is alive and monitoring.

**3. Show the product. Don't describe it.**
Browser tab mockups with real notification badges. A rendered digest card that looks like what users will actually receive. A correlation viz with real percentages. People buy from "that's exactly what I see every morning," not from feature bullets.

**4. Typography is layout, not just content.**
Use `Bebas Neue` at large sizes (80–160px) as a structural element. Headlines should feel like they're *holding the page up*. Use the three font registers (display / body / mono) to signal hierarchy without relying on size alone.

**5. Every animation earns its place.**
- Floating review pills → shows the volume and variety of the problem
- Radar sweep → shows the product monitoring in real time
- Scroll reveals → creates hierarchy and guides attention
- Animated connector particle → shows flow between steps
Nothing spins just to spin. Decorative elements must also reinforce the narrative.

**6. Spatial tension over safe grids.**
Break the grid deliberately: the featured pricing card pushes out of alignment vertically. Wide feature cards span two columns asymmetrically. The orbit diagram fills the viewport. Safe, equal-column grids feel like templates.

**7. Copy leads with pain, not product.**
The user's problem must land before any feature is named. "You're checking 5 tabs. Users are screaming on 4 of them." is the frame everything else sits inside.

**8. Three-register copy hierarchy:**
- `Bebas Neue` ALL CAPS — section titles, emotional statements
- `Syne` sentence case — descriptions, explanations, testimonials
- `DM Mono` lowercase — labels, metrics, timestamps, technical context

### Reusable CSS Tokens

```css
:root {
  --bg: #04060F;
  --bg2: #080C1A;
  --cyan: #00FFD1;
  --cyan-dim: rgba(0, 255, 209, 0.15);
  --cyan-glow: rgba(0, 255, 209, 0.4);
  --amber: #F5A623;
  --amber-dim: rgba(245, 166, 35, 0.15);
  --white: #F0EDE8;
  --muted: rgba(240, 237, 232, 0.45);
  --border: rgba(0, 255, 209, 0.12);
  --border-white: rgba(240, 237, 232, 0.08);
}
```

### Animation Patterns That Work for This Product

- **Scroll reveal:** `opacity: 0 → 1` + `translateY(32px → 0)` via IntersectionObserver, 0.7s ease, stagger siblings with `transition-delay`
- **Radar sweep:** SVG `<g>` with `transform-origin` at center, `animation: rotate 4s linear infinite`
- **Pulse dot:** `scale(1 → 1.2) + box-shadow spread` at 1.5s ease infinite — use for live/active states
- **Floating pills:** `translateY(120vh → -20vh)` with random `--drift` custom property for horizontal variance
- **Marquee:** duplicate content, `translateX(0 → -50%)` at fixed duration
- **Animated SVG paths:** SMIL `<animate attributeName="d">` for morphing shapes; `<animateMotion>` for particles traveling along paths
- **Custom cursor:** dot at exact mouse position + ring that lerps toward it at 0.12 factor per frame

### What to Avoid

- Inter, Roboto, Arial, Space Grotesk, system fonts
- Purple gradient on white backgrounds
- Cards with identical heights in a perfect grid
- Animations that loop with no semantic meaning
- Section titles that describe ("Our Features") instead of stating ("BUILT FOR TEAMS WHO MOVE FAST")
