from agents.db_setup import create_database
from agents.fetch_data import run_all

def run_refresh():
    # These prints act as "heartbeats" in your log file
    print("Refresh started...")

    try:
        # 1. Ensure DB exists/is structured correctly
        create_database()
        print("Database initialized.")

        # 2. Pull data and generate AI summaries
        run_all()
        print("Data fetch and AI summaries complete.")
        
        print("Refresh successful.")
    except Exception as e:
        # This is CRITICAL: if it fails, you want the error in your log!
        print(f"ERROR during refresh: {str(e)}")

if __name__ == "__main__":
    run_refresh()