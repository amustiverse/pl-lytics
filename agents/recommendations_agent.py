import sqlite3
import os
import requests
from dotenv import load_dotenv
from datetime import date

load_dotenv(os.path.expanduser("~/football_dashboard/.env"))

OLLAMA_URL = os.getenv("OLLAMA_HOST") + "/api/generate"
MODEL = "gemma4:26b"

def get_db_path():
    return os.environ.get("DB_PATH", os.path.expanduser("~/football_dashboard/data/football.db"))

def get_all_data():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.team_name, s.position, s.points, s.won,
               s.drawn, s.lost, s.goals_for, s.goals_against,
               s.goal_difference, s.form
        FROM standings s JOIN teams t ON s.team_id = t.team_id
        ORDER BY s.position
    """)
    standings = cursor.fetchall()

    cursor.execute("""
        SELECT p.player_name, t.team_name, p.goals,
               p.assists, p.minutes_played
        FROM player_stats p JOIN teams t ON p.team_id = t.team_id
        ORDER BY p.goals DESC
    """)
    players = cursor.fetchall()

    conn.close()
    return standings, players

def get_existing_charts():
    app_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'Home.py')
    charts = []
    with open(app_path, 'r') as f:
        for line in f:
            if 'st.subheader(' in line:
                # Extract the subheader text
                start = line.index('"') + 1 if '"' in line else line.index("'") + 1
                end = line.rindex('"') if '"' in line else line.rindex("'")
                charts.append(line[start:end])
    return charts

def generate_recommendations():
    standings, players = get_all_data()
    existing = get_existing_charts()
    existing_charts = "\n".join([f"{i+1}. {c}" for i, c in enumerate(existing)])

    prompt = (
        "You are a data visualisation expert analysing Premier League data. "
        "Based on the data below, suggest exactly 3 NEW chart ideas that would reveal "
        "interesting insights not already covered by the existing charts.\n\n"
        "EXISTING CHARTS (do not suggest these again):\n"
        + existing_charts +
        "\n\nSuggestions must be different from the above. For each suggestion provide:\n"
        "1. Chart title\n"
        "2. Chart type (bar, scatter, line etc)\n"
        "3. What data to plot\n"
        "4. Why it would be insightful\n\n"
        "Standings (team, position, points, won, drawn, lost, gf, ga, gd, form):\n"
        + str(standings) +
        "\n\nPlayer stats (player, team, goals, assists, minutes):\n"
        + str(players) +
        "\n\nToday's date: " + str(date.today())
    )

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })

    recommendations = response.json()['response']
    print("\n--- WEEKLY CHART RECOMMENDATIONS ---")
    print(recommendations)
    print("------------------------------------\n")
    return recommendations

if __name__ == "__main__":
    generate_recommendations()