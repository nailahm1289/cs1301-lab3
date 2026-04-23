import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai

st.set_page_config(
    page_title="NBA Data Chatbot",
    page_icon="💬",
    layout="wide"
)

st.title("💬 NBA Data Chatbot")
st.write("Ask questions about a selected NBA team using real API data as context.")

API_KEY = "123"
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

GEMINI_API_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE"
genai.configure(api_key=GEMINI_API_KEY)

NBA_TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "LA Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans",
    "New York Knicks", "Oklahoma City Thunder", "Orlando Magic",
    "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
    "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors", "Utah Jazz",
    "Washington Wizards"
]

SEASONS = ["2025-2026", "2024-2025", "2023-2024", "2022-2023", "2021-2022"]

team = st.selectbox("Choose a team for the chatbot to know about:", NBA_TEAMS)
season = st.selectbox("Choose a season:", SEASONS, index=1)
game_count = st.slider("Number of recent games to give the chatbot:", 3, 15, 8)

@st.cache_data(show_spinner=False)
def get_team_data(team_name):
    url = f"{BASE_URL}/searchteams.php"
    response = requests.get(url, params={"t": team_name}, timeout=15)
    response.raise_for_status()
    data = response.json()
    teams = data.get("teams")
    if teams:
        return teams[0]
    return None

@st.cache_data(show_spinner=False)
def get_season_events(season_choice):
    url = f"{BASE_URL}/eventsseason.php"
    response = requests.get(url, params={"id": "4387", "s": season_choice}, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("events", [])

def process_games(events, team_name, limit):
    rows = []

    for event in events:
        home = event.get("strHomeTeam", "")
        away = event.get("strAwayTeam", "")

        if team_name not in [home, away]:
            continue

        home_score = event.get("intHomeScore")
        away_score = event.get("intAwayScore")

        if home_score is None or away_score is None:
            continue

        try:
            home_score = int(home_score)
            away_score = int(away_score)
        except ValueError:
            continue

        if team_name == home:
            opponent = away
            team_score = home_score
            opponent_score = away_score
            location = "Home"
        else:
            opponent = home
            team_score = away_score
            opponent_score = home_score
            location = "Away"

        result = "Win" if team_score > opponent_score else "Loss"

        rows.append({
            "Date": event.get("dateEvent", "Unknown"),
            "Opponent": opponent,
            "Location": location,
            "Team Score": team_score,
            "Opponent Score": opponent_score,
            "Point Differential": team_score - opponent_score,
            "Result": result
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.sort_values("Date").tail(limit)

    return df

def build_api_context(team_data, df, team_name, season_choice):
    if df.empty:
        return "No completed game data is available."

    wins = int((df["Result"] == "Win").sum())
    losses = int((df["Result"] == "Loss").sum())
    avg_scored = round(df["Team Score"].mean(), 1)
    avg_allowed = round(df["Opponent Score"].mean(), 1)

    context = f"""
Team: {team_name}
Season: {season_choice}
League: {team_data.get("strLeague", "NBA")}
Stadium: {team_data.get("strStadium", "Unknown")}
Location: {team_data.get("strLocation", "Unknown")}
Recent record from provided games: {wins} wins and {losses} losses
Average points scored: {avg_scored}
Average points allowed: {avg_allowed}

Recent game data:
{df.to_string(index=False)}
"""
    return context

if st.button("Load Team Data for Chatbot"):
    try:
        team_data = get_team_data(team)
        events = get_season_events(season)

        if team_data is None:
            st.error("Could not find team data.")
            st.stop()

        df = process_games(events, team, game_count)

        st.session_state["lab4_team"] = team
        st.session_state["lab4_season"] = season
        st.session_state["lab4_team_data"] = team_data
        st.session_state["lab4_df"] = df
        st.session_state["lab4_context"] = build_api_context(team_data, df, team, season)

        st.session_state["lab4_messages"] = [
            {
                "role": "assistant",
                "content": f"I loaded data for the {team}. Ask me about their recent performance."
            }
        ]

    except requests.exceptions.RequestException:
        st.error("There was a problem connecting to the NBA API.")
    except Exception:
        st.error("Something went wrong while loading team data.")

if "lab4_context" in st.session_state:
    st.success(f"Loaded API data for {st.session_state['lab4_team']}.")

    team_data = st.session_state["lab4_team_data"]
    df = st.session_state["lab4_df"]

    with st.expander("View API data being given to chatbot"):
        badge = team_data.get("strBadge")
        if badge:
            st.image(badge, width=150)
        st.dataframe(df, use_container_width=True)

    if "lab4_messages" not in st.session_state:
        st.session_state["lab4_messages"] = []

    for message in st.session_state["lab4_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input("Ask about this team's API data...")

    if user_question:
        st.session_state["lab4_messages"].append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            try:
                history = ""
                for msg in st.session_state["lab4_messages"]:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    history += f"{role}: {msg['content']}\n"

                prompt = f"""
You are an NBA data chatbot in a student Streamlit app.

Use the API data below as your main source of information.
If the user asks something not answered by the data, say that the data does not include that detail.

API DATA CONTEXT:
{st.session_state["lab4_context"]}

Conversation history:
{history}

Answer the latest user question clearly and conversationally.
"""

                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                answer = response.text

            except Exception:
                answer = (
                    "Sorry, something went wrong while generating a response. "
                    "Please try again."
                )

            st.markdown(answer)

            st.session_state["lab4_messages"].append({
                "role": "assistant",
                "content": answer
            })

    st.markdown("---")
    if st.button("Clear Data Chat"):
        st.session_state["lab4_messages"] = [
            {
                "role": "assistant",
                "content": f"Chat cleared. Ask me another question about the {st.session_state['lab4_team']}."
            }
        ]
        st.rerun()

else:
    st.warning("Choose a team and click **Load Team Data for Chatbot** first.")
