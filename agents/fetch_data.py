from agents.fpl_fetch import run_fpl
from agents.summary_agent import generate_all_summaries

def run_all():
    run_fpl()
    generate_all_summaries()

if __name__ == "__main__":
    run_all()