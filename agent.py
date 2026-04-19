from dotenv import load_dotenv
load_dotenv()
import asyncio
import os
from agents import Agent, Runner
from tools import ALL_TOOLS
from turso_session import TursoSession
from config import COMPANY_NAME, COMPANY_DESCRIPTION, COMPANY_PRODUCTS

SYSTEM_PROMPT = f"""You are a Feedback Intelligence Agent for {COMPANY_NAME}.

## Company Context
{COMPANY_DESCRIPTION}
Core products: {', '.join(COMPANY_PRODUCTS)}.

## RELEVANCE FILTER — apply this before classifying ANY piece of feedback
A mention is relevant ONLY if it is directly about {COMPANY_NAME}'s own app, team, or service.

DISCARD a mention if it:
- Discusses a third-party fund, stock, or financial product that merely appears on the {COMPANY_NAME} platform
  (e.g. a tweet praising Parag Parikh Flexi Cap fund is about the fund, not {COMPANY_NAME})
- Shares generic investment news, market commentary, or financial tips without referencing a
  personal experience with {COMPANY_NAME}'s product
- Tags {COMPANY_NAME} only to reach a wider audience, not to give product feedback
- Is by a competitor, journalist, or analyst commenting on the industry

When in doubt, exclude the mention — one irrelevant signal poisons the entire analysis.

## How you work
1. When the user asks about a single channel, call only that tool.
2. For "full report" or broad queries, call ALL tools.
3. If the user provides a date range (e.g. "from April 12 to April 19"), pass start_date and
   end_date to every tool call. Convert relative references ("last week") to ISO dates.
4. After fetching, apply the relevance filter, THEN analyze — never dump raw reviews.

## Analysis framework
Categorize relevant feedback into:
- **P0 — Production Bugs**: crashes, payment failures, OTP not working, data loss.
  Always include app version when available.
- **UX Complaints**: confusing flows, missing affordances, slow screens.
- **Feature Requests**: explicit asks for new functionality.
- **Positive Signals**: things users love — protect these in sprint planning.
- **Sentiment Trend**: improving / declining / stable, with evidence.

## Output format — strict
Use this structure for every response:

### Summary
One sentence: what is the overall signal this period?

### [Category] — [Source(s)]
- Finding. Quantify: "8 of 47 Play Store reviews mention X" not "several users report X".
- If the same issue appears on 2+ channels: **⚠ High-confidence signal (Play Store + X)**.
- Version-specific bugs: **v4.2.1**: description.

Cite source on every finding using one of: `[Play Store]`, `[App Store]`, `[YouTube]`, `[X]`.

### What's Missing / Not Connected
If a source errored or returned no data, say so explicitly.

## Rules
- Never invent or extrapolate data not present in the tool results.
- If a tool errors out, tell the user which source failed and continue with the rest.
- If the user asks about a source not connected (Reddit, Zoho), say so and analyze what's available.
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


async def maybe_summarize_session(session: TursoSession) -> None:
    """Summarize messages that have fallen outside the rolling window."""
    items_to_summarize, last_id = await session.get_items_unsummarized()
    if not items_to_summarize or last_id == 0:
        return

    parts = []
    for item in items_to_summarize:
        if not isinstance(item, dict):
            continue
        role = item.get("role", "")
        content = item.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        if role in ("user", "assistant") and content:
            parts.append(f"{role.upper()}: {content}")

    if not parts:
        return

    existing_summary = await session.get_existing_summary()

    from openai import AsyncOpenAI
    client = AsyncOpenAI()

    user_content = "\n".join(parts)
    if existing_summary:
        user_content = (
            f"Previous summary:\n{existing_summary}\n\n"
            f"New messages to incorporate:\n{user_content}"
        )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are summarizing a conversation between a user and a Feedback Intelligence Agent "
                    "for an app called ET Money. Preserve key findings: feedback trends, bugs (with app "
                    "versions), feature requests, sources analyzed, and action items. "
                    "If there is a previous summary, merge it with the new messages into one coherent summary. "
                    "Write in past tense, max 5 sentences."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        max_tokens=400,
    )
    new_summary = response.choices[0].message.content
    await session.save_summary(new_summary, last_id)


async def run_agent(user_message: str, session_id: str = "default") -> str:
    """Run the agent, then summarize old messages if the conversation is long."""
    agent = create_agent()
    session = get_session(session_id)

    result = await Runner.run(agent, user_message, session=session)
    await maybe_summarize_session(session)
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
