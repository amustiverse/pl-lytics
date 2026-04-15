import subprocess
import time
from agents.db_setup import create_database
from agents.fetch_data import run_all

def start():
    overall_start = time.time()
    
    print("--- Initializing Football Dashboard ---")
    

    step_start = time.time()
    create_database()
    print(f" Database Setup took: {time.time() - step_start:.2f} seconds")
    

    print("--- Running Data Fetch & AI Agents ---")
    step_start = time.time()
    run_all()
    ai_time = time.time() - step_start
    print(f" Data & AI Phase took: {ai_time:.2f} seconds ({ai_time/60:.2f} minutes)")
    
    total_duration = time.time() - overall_start
    print(f"\n Total Startup Time: {total_duration/60:.2f} minutes")
    print("Launching Streamlit UI...")
    

    subprocess.run(["streamlit", "run", "dashboard/home.py"])

if __name__ == "__main__":
    start()