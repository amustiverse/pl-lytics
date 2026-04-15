import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

def get_db_path():
    default_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'football.db')
    return os.environ.get("DB_PATH", os.path.abspath(default_path))

def get_connection():
    return sqlite3.connect(get_db_path())

def get_summary(page_name):
    conn = get_connection()
    row = conn.execute(
        "SELECT summary, generated_date FROM summaries WHERE page=? ORDER BY summary_id DESC LIMIT 1", 
        (page_name,)
    ).fetchone()
    conn.close()
    return row

def format_player_name(full_name):
    parts = full_name.split()
    if len(parts) > 1:
        return f"{parts[0][0]}. {' '.join(parts[1:])}"
    return full_name

def get_last_refresh():
    """Returns the date of the latest summary as a proxy for the last data refresh."""
    try:
        conn = get_connection()
        row = conn.execute("SELECT generated_date FROM summaries ORDER BY summary_id DESC LIMIT 1").fetchone()
        conn.close()
        if row:
            return row[0]
        return "Unknown"
    except:
        return "Database Syncing..."

# --- PAGE CONFIG ---
st.set_page_config(page_title="Premier League Analytics", layout="wide")

# --- HEADER ---
st.title("Premier League Dashboard")
last_sync = get_last_refresh()
st.caption(f"Season 2025/26 | Performance Analytics | Last Data Sync:** {last_sync} ")
st.divider()

# --- TOP LEVEL METRICS ---
conn = get_connection()
col_m1, col_m2, col_m3 = st.columns(3)

leader = conn.execute("SELECT t.team_name FROM teams t JOIN standings s ON t.team_id = s.team_id ORDER BY s.position LIMIT 1").fetchone()
top_p = conn.execute("SELECT player_name, goals FROM player_stats ORDER BY goals DESC LIMIT 1").fetchone()
top_a = conn.execute("SELECT player_name, assists FROM player_stats ORDER BY assists DESC LIMIT 1").fetchone()

with col_m1: st.metric("League Leader", leader[0] if leader else "N/A")
with col_m2: st.metric("Top Scorer", top_p[0] if top_p else "N/A")
with col_m3: st.metric("Assists Leader", top_a[0] if top_a else "N/A")

# --- MAIN NAVIGATION ---
tab1, tab2 = st.tabs(["League Standings", "Player Performance"])

with tab1:
    # 1. Narrative Analysis
    report = get_summary("Standings")
    if report:
        st.subheader("Standings Analysis")
        st.info(report[0])
    
    st.divider()
    
    # 2. Main Standings Table
    st.subheader("League Table")
    df_standings = pd.read_sql("""
        SELECT s.position as 'Pos', t.team_name as 'Team', t.short_name as 'Abbr',
               s.played as 'P', s.won as 'W', s.drawn as 'D', s.lost as 'L', 
               s.goals_for as 'GF', s.goals_against as 'GA', 
               s.goal_difference as 'GD', s.points as 'Pts', s.form as 'Form'
        FROM standings s 
        JOIN teams t ON s.team_id = t.team_id 
        ORDER BY s.position ASC
    """, conn)
    st.dataframe(df_standings.drop(columns=['Abbr']), width='stretch', hide_index=True)

    st.divider()
    
    # 3. Team Performance Insights
    st.subheader("Points Accumulation")
    st.caption("Checking the gap—who’s cruising at the top and who’s desperately looking over their shoulder?")
    pts_scope = st.selectbox("Filter Scope:", ["Top 10", "Bottom 10", "All"], key="pts_scope")
    df_pts = df_standings.head(10) if pts_scope == "Top 10" else df_standings.tail(10) if pts_scope == "Bottom 10" else df_standings
    fig_points = px.bar(df_pts, x="Abbr", y="Pts", color="Pts", color_continuous_scale="reds")
    st.plotly_chart(fig_points, width='stretch')

    st.divider()

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.subheader("Goals Scored vs Conceded")
        st.caption("The 'Sweet Spot'—spot the teams scoring for fun while keeping it tight at the back.")
        scat_scope = st.selectbox("Filter Scope:", ["Top 10", "Bottom 10", "All"], key="scat_scope")
        df_scat = df_standings.head(10) if scat_scope == "Top 10" else df_standings.tail(10) if scat_scope == "Bottom 10" else df_standings
        
        fig_scatter = px.scatter(
            df_scat, x="GF", y="GA", text="Abbr", color="GF", color_continuous_scale="reds",
            hover_data={"Team": True, "GF": True, "GA": True, "GD": True},
            labels={"GF": "Goals Scored", "GA": "Goals Conceded", "GD": "Goal Difference"}
        )
        fig_scatter.update_traces(textposition="top center")
        st.plotly_chart(fig_scatter, width='stretch')

    with col_v2:
        st.subheader("Goal Difference Distribution")
        st.caption("Separating the lucky winners from the genuine heavyweights—it’s hard to hide behind a bad GD.")
        gd_scope = st.selectbox("Filter Scope:", ["Top 10", "Bottom 10", "All"], key="gd_scope")
        df_gd = df_standings.head(10) if gd_scope == "Top 10" else df_standings.tail(10) if gd_scope == "Bottom 10" else df_standings
        fig_gd = px.bar(df_gd.sort_values(by="GD", ascending=False), x="Abbr", y="GD", color="GD", color_continuous_scale="rdylgn")
        fig_gd.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
        st.plotly_chart(fig_gd, width='stretch')

with tab2:
    # 1. Narrative Analysis
    p_report = get_summary("Players")
    if p_report:
        st.subheader("Player Performance Analysis")
        st.info(p_report[0])

    st.divider()
    
    # 2. Leaderboard Tables
    col_lead_l, col_lead_r = st.columns(2)
    with col_lead_l:
        st.subheader("Top Scorers")
        df_scorers = pd.read_sql_query("SELECT p.player_name AS Player, t.team_name AS Team, p.goals AS Goals FROM player_stats p JOIN teams t ON p.team_id = t.team_id ORDER BY p.goals DESC LIMIT 10", conn)
        st.dataframe(df_scorers, width='stretch', hide_index=True)

    with col_lead_r:
        st.subheader("Top Assisters")
        df_assists = pd.read_sql_query("SELECT p.player_name AS Player, t.team_name AS Team, p.assists AS Assists FROM player_stats p JOIN teams t ON p.team_id = t.team_id ORDER BY p.assists DESC LIMIT 10", conn)
        st.dataframe(df_assists, width='stretch', hide_index=True)

    st.divider()
    
    # 3. Player Efficiency Metrics
    st.subheader("Scoring Volume: Goals vs Minutes Played")
    st.caption("Pure instinct—see which finishers are making every second count without needing all day to find the net.")
    eff_scope_1 = st.selectbox("Filter Scope:", ["Top 5", "Top 10", "Top 20"], key="eff_1")
    lim_1 = int(eff_scope_1.split()[1])
    df_eff_1 = pd.read_sql_query(f"SELECT player_name, goals, minutes_played FROM player_stats ORDER BY goals DESC LIMIT {lim_1}", conn)
    df_eff_1['Player'] = df_eff_1['player_name'].apply(format_player_name)
    fig_eff_1 = px.scatter(df_eff_1, x="minutes_played", y="goals", text="Player", color="goals", color_continuous_scale="reds")
    fig_eff_1.update_traces(textposition="top center")
    st.plotly_chart(fig_eff_1, width='stretch')

    st.divider()

    col_eff_a, col_eff_b = st.columns(2)
    with col_eff_a:
        st.subheader("Playmaking Volume: Assists vs Minutes Played")
        st.caption("The Visionaries—tracking the players who have an eye for a pass no matter how much time they get.")
        eff_scope_2 = st.selectbox("Filter Scope:", ["Top 5", "Top 10", "Top 20"], key="eff_2")
        lim_2 = int(eff_scope_2.split()[1])
        df_eff_2 = pd.read_sql_query(f"SELECT player_name, assists, minutes_played FROM player_stats ORDER BY assists DESC LIMIT {lim_2}", conn)
        df_eff_2['Player'] = df_eff_2['player_name'].apply(format_player_name)
        fig_eff_2 = px.scatter(df_eff_2, x="minutes_played", y="assists", text="Player", color="assists", color_continuous_scale="blues")
        fig_eff_2.update_traces(textposition="top center")
        st.plotly_chart(fig_eff_2, width='stretch')

    with col_eff_b:
        st.subheader("Total Contribution: G+A vs Minutes Played")
        st.caption("The Game Changers—who’s doing the most damage and putting up the biggest numbers per shift?")
        eff_scope_3 = st.selectbox("Filter Scope:", ["Top 5", "Top 10", "Top 20"], key="eff_3")
        lim_3 = int(eff_scope_3.split()[1])
        df_eff_3 = pd.read_sql_query(f"SELECT player_name, goals, assists, minutes_played FROM player_stats ORDER BY (goals + assists) DESC LIMIT {lim_3}", conn)
        df_eff_3['Player'] = df_eff_3['player_name'].apply(format_player_name)
        df_eff_3['G+A'] = df_eff_3['goals'] + df_eff_3['assists']
        fig_eff_3 = px.scatter(df_eff_3, x="minutes_played", y="G+A", text="Player", color="G+A", color_continuous_scale="greens")
        fig_eff_3.update_traces(textposition="top center")
        st.plotly_chart(fig_eff_3, width='stretch')

conn.close()