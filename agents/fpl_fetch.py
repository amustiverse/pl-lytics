import sqlite3
import requests
import os
from datetime import date

FPL_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIX_URL = "https://fantasy.premierleague.com/api/fixtures/"

def get_db_path():
    default_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'football.db')
    return os.environ.get("DB_PATH", os.path.abspath(default_path))

def run_fpl():
    print("Fetching fresh data from FPL...")
    data = requests.get(FPL_URL).json()
    fixtures = requests.get(FIX_URL).json()
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()


    for team in data['teams']:
        cursor.execute("INSERT OR REPLACE INTO teams VALUES (?, ?, ?)", 
                       (team['id'], team['name'], team['short_name']))

    stats = {t['id']: {
        'played': 0, 'won': 0, 'drawn': 0, 'lost': 0, 
        'gf': 0, 'ga': 0, 'pts': 0, 'form': []
    } for t in data['teams']}

    fixtures_sorted = sorted([f for f in fixtures if f['finished']], key=lambda x: x['kickoff_time'])

    for f in fixtures_sorted:
        h_id, a_id = f['team_h'], f['team_a']
        h_score, a_score = f['team_h_score'], f['team_a_score']
        stats[h_id]['played'] += 1
        stats[a_id]['played'] += 1
        stats[h_id]['gf'] += h_score
        stats[h_id]['ga'] += a_score
        stats[a_id]['gf'] += a_score
        stats[a_id]['ga'] += h_score

        if h_score > a_score:
            stats[h_id]['won'] += 1; stats[h_id]['pts'] += 3; stats[h_id]['form'].append('W')
            stats[a_id]['lost'] += 1; stats[a_id]['form'].append('L')
        elif a_score > h_score:
            stats[a_id]['won'] += 1; stats[a_id]['pts'] += 3; stats[a_id]['form'].append('W')
            stats[h_id]['lost'] += 1; stats[h_id]['form'].append('L')
        else:
            stats[h_id]['drawn'] += 1; stats[h_id]['pts'] += 1; stats[h_id]['form'].append('D')
            stats[a_id]['drawn'] += 1; stats[a_id]['pts'] += 1; stats[a_id]['form'].append('D')

    cursor.execute("DELETE FROM standings")
    sorted_teams = sorted(stats.items(), key=lambda x: (x[1]['pts'], x[1]['gf'] - x[1]['ga'], x[1]['gf']), reverse=True)

    for i, (t_id, s) in enumerate(sorted_teams, 1):
        gd = s['gf'] - s['ga']
        form_str = "".join(s['form'][-5:])
        cursor.execute("""
            INSERT INTO standings (team_id, matchweek, position, played, won, drawn, lost, goals_for, goals_against, goal_difference, points, form)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (t_id, 0, i, s['played'], s['won'], s['drawn'], s['lost'], s['gf'], s['ga'], gd, s['pts'], form_str))

    cursor.execute("DELETE FROM player_stats")
    current_gw = max([e['id'] for e in data['events'] if e['finished']], default=0)
    

    players = sorted(data['elements'], key=lambda x: (x['goals_scored'] + x['assists']), reverse=True)[:50]
    
    for p in players:
        full_name = f"{p['first_name']} {p['second_name']}"
        cursor.execute("""
            INSERT INTO player_stats (player_name, team_id, matchweek, goals, assists, minutes_played, fetch_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (full_name, p['team'], current_gw, p['goals_scored'], p['assists'], p['minutes'], date.today().isoformat()))

    conn.commit()
    conn.close()
    print("--- FPL Fetch, Standings, and Players complete ---")

if __name__ == "__main__":
    run_fpl()