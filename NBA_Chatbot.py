import streamlit as st
import google.generativeai as genai

st.set_page_config(
    page_title="NBA Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 NBA Chatbot")
st.write("Chat with an AI assistant about NBA teams, players, games, and basketball topics.")

st.info(
    "This chatbot stays in the NBA theme and remembers previous messages in the conversation."
)

# ---------------------------------------------------
# Gemini API key
# Paste your real API key between the quotes below
# ---------------------------------------------------
api_key = "PASTE_YOUR_GEMINI_API_KEY_HERE"

try:
    genai.configure(api_key=api_key)
except Exception:
    st.error("There was a problem setting up the Gemini API key.")
    st.stop()

# ---------------------------------------------------
# Chat memory
# ---------------------------------------------------
if "nba_chat_messages" not in st.session_state:
    st.session_state["nba_chat_messages"] = [
        {
            "role": "assistant",
            "content": (
                "Hey! I'm your NBA assistant. Ask me about teams, players, "
                "matchups, playoff talk, or basketball strategy."
            )
        }
    ]

# Show previous chat messages
for message in st.session_state["nba_chat_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------
# Helper function to build conversation history
# ---------------------------------------------------
def build_history(messages):
    history = ""
    for msg in messages:
        if msg["role"] == "user":
            history += f"User: {msg['content']}\n"
        else:
            history += f"Assistant: {msg['content']}\n"
    return history

# ---------------------------------------------------
# User input
# ---------------------------------------------------
user_input = st.chat_input("Ask something NBA-related...")

if user_input:
    # Save user message
    st.session_state["nba_chat_messages"].append({
        "role": "user",
        "content": user_input
    })

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate assistant response
    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
You are a helpful NBA chatbot in a student Streamlit app.

Rules:
- Only talk about NBA basketball and closely related basketball topics.
- Be conversational, clear, and helpful.
- Keep responses school-appropriate.
- Use prior conversation for memory.
- Give thoughtful but not overly long answers.

Conversation so far:
{build_history(st.session_state["nba_chat_messages"])}

Respond to the user's latest message.
"""

            response = model.generate_content(prompt)
            assistant_reply = response.text

        except Exception:
            assistant_reply = (
                "Sorry, something went wrong while generating a response. "
                "Please try again."
            )

        st.markdown(assistant_reply)

        # Save assistant response
        st.session_state["nba_chat_messages"].append({
            "role": "assistant",
            "content": assistant_reply
        })

# ---------------------------------------------------
# Clear chat button
# ---------------------------------------------------
st.markdown("---")

if st.button("Clear Chat History"):
    st.session_state["nba_chat_messages"] = [
        {
            "role": "assistant",
            "content": "Chat cleared. Ask me anything about the NBA."
        }
    ]
    st.rerun()
