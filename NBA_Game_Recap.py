import streamlit as st
import requests
import pandas as pd
import google.generativeai as genai

st.set_page_config(
    page_title="NBA Game Recap Generator",
    page_icon="📰",
    layout="wide"
)

st.title("📰 NBA Game Recap Generator")
st.write("Use NBA API data and Gemini AI to create a sports-style team recap.")

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

team = st.selectbox("Choose a team:", NBA_TEAMS)
season = st.selectbox("Choose a season:", SEASONS, index=1)
game_count = st.slider("How many recent games should Gemini analyze?", 3, 15, 8)
tone = st.selectbox(
    "Choose the writing style:",
    ["Sports news article", "ESPN-style recap", "Hype social media recap", "Simple beginner explanation"]
)

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

if st.button("Generate NBA Recap"):
    try:
        team_data = get_team_data(team)
        events = get_season_events(season)
        df = process_games(events, team, game_count)

        if team_data is None:
            st.error("Could not find team data.")
            st.stop()

        if df.empty:
            st.warning("No completed games were found for this team and season.")
            st.stop()

        st.subheader(f"{team} Data Used")

        col1, col2 = st.columns([1, 2])

        with col1:
            badge = team_data.get("strBadge")
            if badge:
                st.image(badge, width=180)

        with col2:
            st.write(f"**Team:** {team}")
            st.write(f"**Season:** {season}")
            st.write(f"**Games analyzed:** {len(df)}")
            st.write(f"**Wins:** {(df['Result'] == 'Win').sum()}")
            st.write(f"**Losses:** {(df['Result'] == 'Loss').sum()}")
            st.write(f"**Average points scored:** {round(df['Team Score'].mean(), 1)}")
            st.write(f"**Average points allowed:** {round(df['Opponent Score'].mean(), 1)}")

        st.dataframe(df, use_container_width=True)

        game_summary = df.to_string(index=False)

        prompt = f"""
You are a sports writer creating content for a student NBA stats app.

Use the NBA API data below to write a {tone.lower()} about the {team}.
The recap should be based only on the provided data.

Team: {team}
Season: {season}

Recent game data:
{game_summary}

Include:
- overall recent performance
- strongest trend
- weakness or concern
- one short conclusion
Keep it school appropriate and easy to understand.
"""

        with st.spinner("Gemini is writing your NBA recap..."):
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)

        st.markdown("---")
        st.subheader("Generated NBA Recap")
        st.write(response.text)

    except requests.exceptions.RequestException:
        st.error("There was a problem connecting to the NBA API.")
    except Exception:
        st.error("Something went wrong while generating the recap. Please try again.")
