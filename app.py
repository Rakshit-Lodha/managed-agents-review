import streamlit as st
import asyncio
from agent import create_agent, get_session
from agents import Runner

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
        st.rerun()

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

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("Fetching and analyzing feedback..."):
            agent = create_agent()
            session = get_session(st.session_state.session_id)

            try:
                result = asyncio.run(
                    Runner.run(agent, user_input, session=session)
                )
                response = result.final_output
            except Exception as e:
                response = f"⚠️ Error running agent: {str(e)}"

        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
