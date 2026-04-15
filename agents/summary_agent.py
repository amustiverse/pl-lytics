import sqlite3
import os
import requests
from dotenv import load_dotenv
from datetime import date

load_dotenv()

MODEL = "gemma4:latest"

def get_db_path():
    default_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'football.db')
    return os.environ.get("DB_PATH", os.path.abspath(default_path))

def generate_page_summary(page, context_data, context_label):
    host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    host = host.rstrip('/')
    url = f"{host}/api/generate"
    
    prompt = (
        f"Role: Senior Sports Data Journalist. "
        f"Analyze this {context_label} data: {str(context_data)}. "
        f"Provide 3 sentences of insight. Use ONLY the provided data."
    )

    response = requests.post(
        url, 
        json={"model": MODEL, "prompt": prompt, "stream": False}
    )
    
    data = response.json()
    summary = data["response"]
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM summaries WHERE page = ?", (page,))
    cursor.execute("INSERT INTO summaries (page, summary, generated_date) VALUES (?, ?, ?)", 
                   (page, summary, date.today().isoformat()))
    conn.commit()
    conn.close()
    print(f"Summary saved for {page}")

def generate_all_summaries():
    conn = sqlite3.connect(get_db_path())
    
    standings_query = """
        SELECT * FROM (
            SELECT t.team_name, s.position, s.points, s.form 
            FROM standings s JOIN teams t ON s.team_id = t.team_id 
            ORDER BY s.position ASC LIMIT 5
        )
        UNION ALL
        SELECT * FROM (
            SELECT t.team_name, s.position, s.points, s.form 
            FROM standings s JOIN teams t ON s.team_id = t.team_id 
            ORDER BY s.position DESC LIMIT 5
        )
    """
    standings = conn.execute(standings_query).fetchall()
    
    players = conn.execute("""
        SELECT p.player_name, t.team_name, p.goals 
        FROM player_stats p JOIN teams t ON p.team_id = t.team_id 
        ORDER BY p.goals DESC LIMIT 5
    """).fetchall()
    
    conn.close()

    generate_page_summary("Standings", standings, "top and bottom league standings")
    generate_page_summary("Players", players, "top scorers")

if __name__ == "__main__":
    generate_all_summaries()