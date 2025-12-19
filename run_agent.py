import sys
import os

sys.path.append(os.getcwd())

from agent_logic.graph import run_agent

if __name__ == "__main__":
    print("🤖 Запускаю Агента...")
    run_agent()