import streamlit as st
import google.generativeai as genai

st.set_page_config(
    page_title="NBA Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 NBA Chatbot")
st.write("Chat with an AI assistant about NBA teams, players, matchups, and basketball topics.")

st.info("""
This chatbot stays in the same overall theme as the app: NBA basketball.
It does not pull data from the API page, which helps match the lab requirement.
""")

# ----------------------------
# Configure Gemini
# ----------------------------
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("Gemini API key not found. Add GEMINI_API_KEY to Streamlit secrets.")
    st.stop()

# ----------------------------
# Session state memory
# ----------------------------
if "nba_chat_messages" not in st.session_state:
    st.session_state["nba_chat_messages"] = [
        {
            "role": "assistant",
            "content": (
                "Hey! I'm your NBA assistant. Ask me about teams, player comparisons, "
                "basketball strategy, playoff talk, or game breakdowns."
            )
        }
    ]

for message in st.session_state["nba_chat_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def build_history(messages):
    history_text = ""
    for msg in messages:
        role_name = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role_name}: {msg['content']}\n"
    return history_text

user_input = st.chat_input("Ask something NBA-related...")

if user_input:
    st.session_state["nba_chat_messages"].append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
You are a helpful NBA chatbot inside a student Streamlit project.

Rules:
- Stay focused on NBA basketball.
- You can discuss teams, players, strategies, season storylines, rivalries, and general basketball advice.
- Keep responses school-appropriate.
- Be conversational and clear.
- Use prior conversation for memory.

Conversation:
{build_history(st.session_state["nba_chat_messages"])}

Respond to the latest user message.
"""

            response = model.generate_content(prompt)
            assistant_reply = response.text

        except Exception:
            assistant_reply = (
                "Sorry, something went wrong while generating a response. "
                "This may be caused by rate limits, a temporary Gemini issue, "
                "or a blocked prompt. Please try again."
            )

        st.markdown(assistant_reply)
        st.session_state["nba_chat_messages"].append({
            "role": "assistant",
            "content": assistant_reply
        })

st.markdown("---")
if st.button("Clear Chat History"):
    st.session_state["nba_chat_messages"] = [
        {
            "role": "assistant",
            "content": "Chat cleared. Ask me anything NBA-related."
        }
    ]
    st.rerun()
