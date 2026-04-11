import streamlit as st

st.set_page_config(
    page_title="NBA Stats Central",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 NBA Stats Central")
st.subheader("An interactive NBA dashboard and chatbot")

st.write("""
Welcome to **NBA Stats Central**.

This app lets users explore NBA team data using a web API and visualize recent performance.
It also includes an AI chatbot that stays in the NBA theme and can answer basketball-related questions.
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    **NBA Team Stats Page**
    
    - Choose an NBA team
    - Choose a season
    - Select how many recent games to analyze
    - View team branding, recent game results, and dynamic charts
    """)

with col2:
    st.success("""
    **NBA Chatbot Page**
    
    - Ask NBA-related questions
    - Get team and basketball discussion help
    - Hold a conversation with memory
    - Error handling prevents crashes
    """)

st.markdown("---")
st.caption("Built with Streamlit, TheSportsDB API, and Google Gemini.")
