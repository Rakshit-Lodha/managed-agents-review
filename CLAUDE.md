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
- **Marketing page** — `frontend/app/marketing/` (Next.js route, CSS module)
  - Full Editorial Quiet landing page: hero, before/after browser split, metrics strip, correlation cluster, features grid, testimonial, CTA, footer
  - Scroll-reveal animations via IntersectionObserver (no looping animations)
  - `frontend/app/page.tsx` redirects `/` → `/marketing`
- **Auth page** — `frontend/app/auth/` (reworked April 2026)
  - Split layout: left = form, right = live pulse teaser card (matching `Rivue Login.html` design)
  - Google OAuth via Supabase (`signInWithOAuth`)
  - Email + password: sign in and sign up tabs (`signUp` / `signInWithPassword`)
  - No GitHub — Google + email only
  - Middleware (`frontend/middleware.ts`) guards `/onboarding` — redirects unauthenticated users to `/auth?next=...`
  - Single Supabase project shared across apps — no extra cost

### In Progress
- **Multi-tenant architecture** — `config.py` is currently hardcoded for ET Money (MVP test app). Needs a `tenants` DB table so multiple companies can onboard independently.
- **Client onboarding persistence** — the frontend has the onboarding experience and live source enrichment, but does not yet write tenants/sources/preferences to a database.
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

# Run the Next.js frontend (dev)
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000 → redirects to /marketing
```

## Environment Variables

**Root `.env`** (Python backend — Streamlit + FastAPI):
- `OPENAI_API_KEY` — used by the OpenAI Agents SDK
- `YOUTUBE_API_KEY` — YouTube Data API v3
- `X_API_KEY` — X/Twitter API bearer token (per-post pricing — cache responses aggressively)
- `SUPABASE_URL` / `SUPABASE_KEY` — server-side Supabase access

**`frontend/.env.local`** (Next.js — must be inside `frontend/`, not project root):
- `NEXT_PUBLIC_SUPABASE_URL` — Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase publishable anon key (`sb_publishable_...`)
- `NEXT_PUBLIC_API_BASE` — FastAPI preview base URL (default `http://localhost:8000`)

**Supabase Auth setup** — add these to Redirect URLs in Supabase Dashboard → Authentication → URL Configuration:
- `http://localhost:3000/auth/callback` (local dev)
- Your production URL when deploying

## Architecture

**Entry points:**
- `app.py` — Streamlit chat UI. Manages chat history in `st.session_state`, calls `agent.py` for each query.
- `agent.py` — Core agent definition. Creates an OpenAI `Agent` (GPT-4o) with a system prompt and tool list. Uses `SQLiteSession` for persistent conversation memory stored in `feedback_agent_memory.db`. Exposes `run_agent()` (async, returns string) and `run_agent_streamed()` (async generator).
- `backend/main.py` — FastAPI preview backend for onboarding source enrichment. It is not yet the main agent API.
- `frontend/app/page.tsx` — redirects `/` to `/marketing`.
- `frontend/app/marketing/page.tsx` — Editorial Quiet marketing/landing page (client component, IntersectionObserver scroll reveals).
- `frontend/app/marketing/marketing.module.css` — all marketing page styles (CSS module; tokens scoped to `.page` class, not `:root`).
- `frontend/app/auth/page.tsx` — sign in / sign up page. Split layout, Google OAuth + email/password, no GitHub.
- `frontend/app/auth/auth.module.css` — auth page styles (Editorial Quiet, CSS module).
- `frontend/app/auth/callback/route.ts` — OAuth code exchange route. Reads `?next=` param and redirects after Supabase session is established.
- `frontend/app/onboarding/page.tsx` — onboarding flow. Protected by middleware.
- `frontend/app/globals.css` — onboarding visual system (dark theme). Do not touch — kept isolated from marketing/auth styles.
- `frontend/middleware.ts` — guards `/onboarding/*` (redirects to `/auth`); redirects authenticated users away from `/auth`.

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
- **CSS modules for marketing/auth, globals.css for onboarding:** Marketing and auth styles live in CSS modules (`.module.css`) to avoid conflicts with the dark-theme onboarding styles in `globals.css`. All CSS token variables in modules must be scoped to a class (e.g., `.page { --teal: ... }`), not `:root`, due to Next.js CSS module purity rules.
- **Single Supabase project for all apps:** No separate Supabase project per app. All auth flows point at the same project. Add allowed redirect URLs in Supabase Dashboard → Authentication → URL Configuration.
- **Auth providers:** Google OAuth + email/password only. GitHub was intentionally excluded. Do not add it back without explicit instruction.
- **`.env.local` must live inside `frontend/`:** Next.js only reads `frontend/.env.local`, not the root `.env`. Root `.env` is for Python (FastAPI/Streamlit). Keep them separate.
- **Design source of truth:** `Rivue Login.html`, `Rivue Landing.html`, and related files in `/Users/Rakshit.Lodha/Downloads/rivue/project/` are the authoritative design references. CLAUDE.md's Frontend Design System section reflects them.

## Adding a New Feedback Source

1. Create `tools/<source>.py` with a `@function_tool`-decorated function returning JSON
2. Import and add it to `ALL_TOOLS` in `tools/__init__.py`
3. The agent automatically discovers and uses new tools

For external services (Jira, Zoho), prefer MCP servers over direct API integrations.

---

## Frontend Design System

All frontend work for this product — marketing page, onboarding, dashboard — follows the **Editorial Quiet** aesthetic established in `Rivue Landing.html`. These are non-negotiable principles, not suggestions.

### Visual Identity

| Element | Choice | Reason |
|---------|--------|--------|
| Display/headline font | `Fraunces` (serif, italic) | Editorial weight; makes headlines feel authored, not generated |
| Body font | `Inter` | Neutral, legible, premium-feeling at small sizes |
| Mono/label font | `JetBrains Mono` | Technical register for metrics, timestamps, section labels |
| Background | `#fafaf8` (warm paper) | Editorial canvas; not clinical white |
| Surface/card | `#ffffff` | Clean lift above paper |
| Subtle surface | `#f3f2ed`, `#eeece5` | Depth without shadow overuse |
| Primary accent | `#00a889` (teal) | Brand color — CTAs, verified states, positive signals |
| Teal ink (text) | `#007a65` | Teal used in body copy or italic emphasis |
| Teal soft (bg tint) | `#cdeee6` | Teal used as a chip or highlight background |
| Text primary | `#0f1115` (near-black ink) | Not pure black; softer on cream paper |
| Text secondary | `#3a3b3e` | Body copy, descriptions |
| Text tertiary | `#6b6c6f` | Labels, captions, metadata |
| Text disabled | `#a3a4a6` | Placeholders, inactive states |
| Border | `#e7e5df` (line), `#d8d5cc` (line-2) | Warm-toned dividers; not cool grey |

### Signal Colors — Data Only

These appear exclusively on data signals (bugs, sentiment, trends). Never use them for decorative or brand purposes.

| Role | Color | Use |
|------|-------|-----|
| Critical / negative | `#d14343` | Bug reports, crash signals, negative sentiment |
| Warning / friction | `#d69418` | Feature friction, growing complaints, watch signals |
| Positive | `#2e8f4f` | Rising ratings, positive sentiment, wins |

### Color Has a Job, Not Just a Vibe

- **Teal** appears on: CTAs, verified states, the Rivue logo dot, positive signal dots, hover states, italic headline emphasis
- **Signal colors** appear on: digest cards, sentiment badges, trend indicators — never on UI chrome
- **Paper/cream** is the canvas — clean, readable, never clinical

Never use dark backgrounds, neon colors, or glowing effects. Never introduce purple, blue-purple gradients, electric cyan, or dark-mode-style treatments. This is an editorial product, not a dashboard or security tool.

### Design Principles

**1. Editorial Quiet — one committed aesthetic.**
Every element reinforces the same story: a premium, trustworthy product that respects the reader's time. The frame is a morning newspaper briefing, not a monitoring dashboard. If something feels "startup-y" or "SaaS-dark," it's wrong.

**2. Serif headlines carry the emotional weight.**
Use `Fraunces` italic for the key phrase in every hero or section heading. Mixed case, not all-caps. The italic should feel *authored* — like a byline — not decorative. Example: "Five tabs of chaos. *One morning digest.*"

**3. Show the product. Don't describe it.**
Render real digest cards, real browser chrome with tab fatigue, real signal summaries. People buy from "that's exactly what I see every morning," not feature bullets. Every section should include a product artifact.

**4. Three-register typography — strict hierarchy:**
- `Fraunces` italic — hero headlines, section emotional anchor, key phrase per section
- `Inter` — all body copy, descriptions, nav, buttons, form labels
- `JetBrains Mono` — section labels (`§01 DISCOVERY`), metrics, timestamps, code, monospaced data

**5. Minimal animation — earn every motion.**
Scroll reveals only: `opacity: 0 → 1` + `translateY(24px → 0)` via IntersectionObserver, 0.5s ease-out. No looping animations on load. No floating elements, no radar sweeps, no custom cursors. Motion should feel like pages turning, not a live dashboard pulsing.

**6. Clean grid with editorial rhythm.**
Use consistent column grids (12-col, maxWidth 1200px, padding 40px). Cards share a consistent border radius (`--r-lg: 10px`). Spacing follows multiples of 8. Don't break the grid for visual effect — let content density and typography create hierarchy instead.

**7. Copy leads with the user's morning, not the product's features.**
"You're checking 5 tabs" is the problem. "One digest" is the solution. Name the pain before naming the product. Section labels use the `§01 PRODUCT` format to give the page a document-like chapter structure.

**8. Buttons are calm, not loud.**
Primary button: `background: #0f1115` (ink), white text — understated authority. Ghost button: transparent with `border: 1px solid #d8d5cc`. No gradient buttons, no glow, no shadow-on-hover drama. Active state: `translateY(1px)` only.

### Reusable CSS Tokens

```css
:root {
  /* Paper + ink */
  --paper:     #fafaf8;
  --paper-2:   #f3f2ed;
  --paper-3:   #eeece5;
  --card:      #ffffff;

  --ink:       #0f1115;
  --ink-2:     #3a3b3e;
  --ink-3:     #6b6c6f;
  --ink-4:     #a3a4a6;

  --line:      #e7e5df;
  --line-2:    #d8d5cc;

  /* Brand accent */
  --teal:      #00a889;
  --teal-ink:  #007a65;
  --teal-soft: #cdeee6;

  /* Signal — data only */
  --sig-red:   #d14343;
  --sig-amber: #d69418;
  --sig-green: #2e8f4f;

  /* Type */
  --f-sans:  'Inter', system-ui, -apple-system, sans-serif;
  --f-serif: 'Fraunces', Georgia, serif;
  --f-mono:  'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace;

  /* Radii + shadows */
  --r-sm: 4px;
  --r-md: 6px;
  --r-lg: 10px;
  --shadow-1: 0 1px 2px rgba(15,17,21,0.04), 0 2px 10px rgba(15,17,21,0.04);
  --shadow-2: 0 1px 2px rgba(15,17,21,0.06), 0 8px 30px rgba(15,17,21,0.08);
}
```

### Google Fonts Import

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:ital,wght@0,400;0,500;1,400;1,500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Section Label Pattern

Section labels use `§01 LABEL · context` format, rendered in `JetBrains Mono` 11px, `letter-spacing: 0.14em`, `color: var(--ink-3)`. A thin 1px `var(--line)` border-bottom separates the label from the content below.

### What to Avoid

- Dark backgrounds (`#04060F`, dark-mode treatments of any kind)
- Neon or electric colors (cyan `#00FFD1`, glowing borders, neon shadows)
- `Bebas Neue`, `Syne`, `DM Mono`, `Space Grotesk`, or system fonts
- Looping animations on load (radars, floating pills, pulsing dots, custom cursors)
- All-caps headlines as the primary voice — use serif italic instead
- Gradient buttons, glowing CTAs, or any hover effect beyond subtle color/border changes
- Cards with drop shadows as the primary elevation signal — use borders on paper instead
- Section titles that describe ("Our Features") instead of framing ("§03 SIGNAL · How it works")
