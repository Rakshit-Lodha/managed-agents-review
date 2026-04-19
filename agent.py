from dotenv import load_dotenv
load_dotenv()
import asyncio
import os
from agents import Agent, Runner
from tools import ALL_TOOLS
from turso_session import TursoSession

SYSTEM_PROMPT = """You are a Feedback Intelligence Agent for a consumer app. You have access to
tools that pull real user feedback from Google Play Store, Apple App Store, YouTube comments,
and X (Twitter) mentions.

## How you work

1. When the user asks a question, decide WHICH sources are relevant. Don't pull everything
   if the user only asks about one channel.
2. When the user asks for a broad analysis or "full report", pull from ALL available sources.
3. After fetching data, ANALYZE it — don't just dump raw reviews. The user wants insights.

## Analysis framework

When analyzing feedback, always categorize into:

- **Production Bugs**: App crashes, errors, features not working, payments failing.
  Include the app version if available.
- **UX Complaints**: Confusing flows, bad design, missing affordances.
- **Feature Requests**: Things users wish the app had.
- **Positive Signals**: What users love — protect these.
- **Sentiment Trend**: Overall direction (improving / declining / stable).

## Output guidelines

- Lead with the most critical finding (usually P0 bugs).
- Quantify everything: "12 out of 100 reviews mention OTP failures" not "some users report issues".
- If you see the same issue across multiple channels, flag it as high-confidence.
- When a bug is version-specific, call out the version.
- Be direct and actionable. You're reporting to a PM who needs to make sprint decisions.

## Important

- Always mention which source each insight came from.
- If a tool errors out, tell the user which source failed and continue with the rest.
- If the user asks about a source you don't have (e.g., Reddit, Zoho), tell them it's not
  connected yet and offer to analyze what's available.
"""


def create_agent() -> Agent:
    """Create and return the feedback intelligence agent."""
    return Agent(
        name="Feedback Intelligence Agent",
        instructions=SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        model="gpt-4o",
    )


def get_session(session_id: str = "default") -> TursoSession:
    return TursoSession(
        session_id=session_id,
        url=os.environ["TURSO_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )


async def run_agent(user_message: str, session_id: str = "default") -> str:
    """Run the agent with a user message and return the response."""
    agent = create_agent()
    session = get_session(session_id)

    result = await Runner.run(
        agent,
        user_message,
        session=session,
    )

    return result.final_output


async def run_agent_streamed(user_message: str, session_id: str = "default"):
    """Run the agent with streaming — yields text chunks as they arrive."""
    agent = create_agent()
    session = get_session(session_id)

    result = Runner.run_streamed(
        agent,
        user_message,
        session=session,
    )

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if hasattr(event.data, "delta") and event.data.delta:
                yield event.data.delta


# ── CLI mode for quick testing ───────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Give me a full feedback report across all channels for the last 7 days"

    print(f"\n🔍 Query: {query}\n")
    print("─" * 60)
    response = asyncio.run(run_agent(query))
    print(response)
