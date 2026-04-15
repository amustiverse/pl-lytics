import sqlite3
import os

def get_db_path():

    default_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'football.db')
    return os.environ.get("DB_PATH", os.path.abspath(default_path))

def create_database():
    db_path = get_db_path()
   
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    

    cursor.execute("CREATE TABLE IF NOT EXISTS teams (team_id INTEGER PRIMARY KEY, team_name TEXT, short_name TEXT)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS standings (
            standing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER REFERENCES teams(team_id),
            matchweek INTEGER, position INTEGER, played INTEGER, 
            won INTEGER, drawn INTEGER, lost INTEGER, 
            goals_for INTEGER, goals_against INTEGER, 
            goal_difference INTEGER, points INTEGER, form TEXT
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_stats (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT, team_id INTEGER REFERENCES teams(team_id),
            matchweek INTEGER, goals INTEGER, assists INTEGER, 
            minutes_played INTEGER, fetch_date TEXT,
            UNIQUE(player_name, team_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            page TEXT NOT NULL, summary TEXT NOT NULL, generated_date TEXT NOT NULL
        )""")
    
    conn.commit()
    conn.close()
    print(f" Database initialized at: {db_path}")

if __name__ == "__main__":
    create_database()