# streamlit_app.py
import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Text-to-SQL Agent",
    page_icon="🗄️",
    layout="wide"
)

st.title("🗄️ Text-to-SQL Deep Agent")
st.caption("Ask questions in plain English — powered by LangChain Deep Agents + Groq")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    This agent uses **LangChain Deep Agents** to:
    - Plan multi-step SQL queries
    - Explore your database schema
    - Write and validate SQL
    - Return plain-English answers
    """)
    st.divider()

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    st.subheader("Example Questions")
    examples = [
        "How many customers are from Canada?",
        "What are the top 5 best-selling artists?",
        "Which employee generated the most revenue?",
        "Show total sales by country",
    ]
    for ex in examples:
        if st.button(ex, key=ex):
            st.session_state.prefill = ex
            st.rerun()

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
prefill = st.session_state.pop("prefill", "")
question = st.chat_input("Ask a question about your database...") or prefill

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        # Show live status while waiting
        status = st.empty()
        result_box = st.empty()

        status.info("🔍 Agent is thinking...")

        try:
            # Use longer timeout + stream=True for faster first byte
            with requests.post(
                f"{API_URL}/query",
                json={"question": question},
                timeout=300,
                stream=True
            ) as response:
                if response.status_code == 200:
                    status.empty()
                    data = response.json()
                    answer = data["answer"]
                    result_box.markdown(answer)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })
                elif response.status_code == 503:
                    status.empty()
                    st.warning(
                        "⏳ AI service is busy right now. "
                        "The system already retried 3 times. "
                        "Please wait 1-2 minutes and try again."
                    )
                else:
                    status.empty()
                    error = response.json().get("detail", "Unknown error")
                    st.error(f"API Error: {error}")

        except requests.exceptions.ConnectionError:
            status.empty()
            st.error("Cannot connect to API. Make sure FastAPI is running on port 8000.")
        except requests.exceptions.Timeout:
            status.empty()
            st.error(
                "⏱️ Request timed out. Try a simpler question or restart the API server."
            )
        except Exception as e:
            status.empty()
            st.error(f"Unexpected error: {str(e)}")