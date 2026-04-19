import streamlit as st
import asyncio
from datetime import datetime, timedelta
from agent import run_agent

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Feedback Intelligence Agent",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Feedback Intelligence Agent")
st.caption("Ask anything about your app's user feedback across Play Store, App Store, YouTube & X")

# ── Session state ────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_default"

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    st.session_state.session_id = st.text_input(
        "Session ID (for memory)",
        value=st.session_state.session_id,
        help="Change this to start a fresh conversation or switch between projects",
    )

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        try:
            from agent import get_session
            asyncio.run(get_session(st.session_state.session_id).clear_session())
        except Exception:
            pass
        st.rerun()

    st.divider()
    st.subheader("📅 Date Range")
    today = datetime.now().date()
    start_date = st.date_input("From", value=today - timedelta(days=7), max_value=today)
    end_date = st.date_input("To", value=today, max_value=today)
    if start_date > end_date:
        st.warning("Start date must be before end date.")

    st.divider()
    st.subheader("📡 Connected Sources")
    st.markdown("""
    - ✅ Google Play Store
    - ✅ Apple App Store
    - ✅ YouTube Comments
    - ✅ X (Twitter) Mentions
    - 🔜 Reddit
    - 🔜 Zoho Desk
    """)

    st.divider()
    st.subheader("💡 Try asking")
    example_queries = [
        "What are the top complaints on the Play Store this week?",
        "Give me a full feedback report across all channels",
        "Are there any production bugs reported on Twitter?",
        "What do iOS users think about the latest version?",
        "Compare Play Store vs App Store sentiment",
        "What features are users requesting the most?",
    ]
    for q in example_queries:
        if st.button(q, key=q):
            st.session_state.pending_query = q
            st.rerun()

# ── Chat display ─────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Handle input ─────────────────────────────────────────────
user_input = st.chat_input("Ask about your app's feedback...")

# Check for pending query from sidebar buttons
if "pending_query" in st.session_state:
    user_input = st.session_state.pending_query
    del st.session_state.pending_query

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Inject date range as context prefix so the agent passes it to tools
    date_context = f"[Date range: {start_date.isoformat()} to {end_date.isoformat()}] "
    augmented_input = date_context + user_input

    # Run agent (also triggers summarization if conversation is long)
    with st.chat_message("assistant"):
        with st.spinner("Fetching and analyzing feedback..."):
            try:
                response = asyncio.run(
                    run_agent(augmented_input, st.session_state.session_id)
                )
            except Exception as e:
                import traceback
                response = f"⚠️ Error running agent: {str(e)}"
                st.error(traceback.format_exc())

        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
