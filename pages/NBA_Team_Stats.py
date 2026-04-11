import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="NBA Team Stats",
    page_icon="📊",
    layout="wide"
)

st.title("📊 NBA Team Stats Dashboard")
st.write("Explore NBA team performance using live data from TheSportsDB.")

API_KEY = "123"
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

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

SEASONS = [
    "2025-2026", "2024-2025", "2023-2024", "2022-2023", "2021-2022"
]

# ----------------------------
# User inputs
# ----------------------------
selected_team = st.selectbox("Choose an NBA team:", NBA_TEAMS, index=1)
selected_season = st.selectbox("Choose a season:", SEASONS, index=1)
recent_game_count = st.slider("How many recent team games should be analyzed?", 5, 20, 10)

# ----------------------------
# API helpers
# ----------------------------
@st.cache_data(show_spinner=False)
def get_team_data(team_name):
    url = f"{BASE_URL}/searchteams.php"
    response = requests.get(url, params={"t": team_name}, timeout=15)
    response.raise_for_status()
    data = response.json()

    teams = data.get("teams")
    if not teams:
        return None

    # take first exact-ish result
    return teams[0]

@st.cache_data(show_spinner=False)
def get_season_events(season):
    # NBA league id on TheSportsDB
    url = f"{BASE_URL}/eventsseason.php"
    response = requests.get(url, params={"id": "4387", "s": season}, timeout=20)
    response.raise_for_status()
    data = response.json()

    return data.get("events", [])

def process_team_games(events, team_name):
    rows = []

    for event in events:
        home_team = event.get("strHomeTeam", "")
        away_team = event.get("strAwayTeam", "")

        if team_name not in (home_team, away_team):
            continue

        home_score = event.get("intHomeScore")
        away_score = event.get("intAwayScore")

        # skip games without scores
        if home_score is None or away_score is None:
            continue

        try:
            home_score = int(home_score)
            away_score = int(away_score)
        except (TypeError, ValueError):
            continue

        if team_name == home_team:
            opponent = away_team
            team_score = home_score
            opponent_score = away_score
            location = "Home"
        else:
            opponent = home_team
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
        df = df.sort_values("Date")
        df["Date Label"] = df["Date"].dt.strftime("%Y-%m-%d")
        df = df.tail(recent_game_count)

    return df

# ----------------------------
# Main logic
# ----------------------------
if st.button("Load NBA Data"):
    try:
        team_data = get_team_data(selected_team)
        season_events = get_season_events(selected_season)

        if team_data is None:
            st.error("Team data could not be found.")
            st.stop()

        df = process_team_games(season_events, selected_team)

        st.session_state["team_data"] = team_data
        st.session_state["team_games_df"] = df
        st.session_state["team_name"] = selected_team
        st.session_state["season"] = selected_season

    except requests.exceptions.RequestException:
        st.error("There was a problem connecting to the sports API. Please try again.")
    except Exception:
        st.error("Something went wrong while processing the NBA data.")

# ----------------------------
# Display section
# ----------------------------
if "team_data" in st.session_state and "team_games_df" in st.session_state:
    team_data = st.session_state["team_data"]
    df = st.session_state["team_games_df"]

    st.markdown("---")
    st.subheader(f"{st.session_state['team_name']} Overview")

    col1, col2 = st.columns([1, 2])

    with col1:
        badge = team_data.get("strBadge")
        fanart = team_data.get("strFanart1")

        if badge:
            st.image(badge, width=200)

        if fanart:
            st.image(fanart, use_container_width=True)

    with col2:
        st.write(f"**Team:** {team_data.get('strTeam', 'N/A')}")
        st.write(f"**League:** {team_data.get('strLeague', 'N/A')}")
        st.write(f"**Stadium:** {team_data.get('strStadium', 'N/A')}")
        st.write(f"**Location:** {team_data.get('strLocation', 'N/A')}")
        st.write(f"**Formed Year:** {team_data.get('intFormedYear', 'N/A')}")
        description = team_data.get("strDescriptionEN")
        if description:
            st.write("**Team Description:**")
            st.write(description[:500] + "...")

    st.markdown("---")
    st.subheader(f"Recent {len(df)} Games in {st.session_state['season']}")

    if df.empty:
        st.warning("No scored games were available for this team and season.")
    else:
        display_df = df[[
            "Date Label", "Opponent", "Location", "Team Score",
            "Opponent Score", "Point Differential", "Result"
        ]].rename(columns={"Date Label": "Date"})

        st.dataframe(display_df, use_container_width=True)

        wins = int((df["Result"] == "Win").sum())
        losses = int((df["Result"] == "Loss").sum())
        avg_points = round(df["Team Score"].mean(), 1)
        avg_allowed = round(df["Opponent Score"].mean(), 1)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wins", wins)
        c2.metric("Losses", losses)
        c3.metric("Avg Points", avg_points)
        c4.metric("Avg Points Allowed", avg_allowed)

        st.markdown("---")
        st.subheader("Points Scored by Game")

        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(df["Date Label"], df["Team Score"], marker="o")
        ax1.set_xlabel("Game Date")
        ax1.set_ylabel("Points Scored")
        ax1.set_title(f"{st.session_state['team_name']} Points Scored")
        plt.xticks(rotation=45)
        st.pyplot(fig1)

        st.markdown("---")
        st.subheader("Wins vs Losses")

        result_counts = df["Result"].value_counts()

        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.bar(result_counts.index, result_counts.values)
        ax2.set_xlabel("Result")
        ax2.set_ylabel("Number of Games")
        ax2.set_title("Recent Win/Loss Breakdown")
        st.pyplot(fig2)
