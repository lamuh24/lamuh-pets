import os
import time
from pathlib import Path

# Configuration
CONVERSATION_ID = "dce2e5ff-1e9f-427a-8393-389ea276c1e0"
BRAIN_DIR = Path(r"C:\Users\qchee\.gemini\antigravity\brain") / CONVERSATION_ID
TASK_FILE = BRAIN_DIR / "task.md"
PLAN_FILE = BRAIN_DIR / "implementation_plan.md"
STATE_FILE = "state.txt"

# Timeouts in seconds
ACTIVE_TIMEOUT = 10 

def get_file_mtime(filepath):
    try:
        return os.path.getmtime(filepath)
    except:
        return 0

def get_file_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

def main():
    print(f"Starting Antigravity Watcher for Conv ID: {CONVERSATION_ID}")
    
    last_task_mtime = 0
    last_plan_mtime = 0
    
    current_state = "idle"
    
    while True:
        try:
            task_mtime = get_file_mtime(TASK_FILE)
            plan_mtime = get_file_mtime(PLAN_FILE)
            now = time.time()
            
            new_state = "idle"
            
            # Check if planning
            if plan_mtime > 0 and (now - plan_mtime) < ACTIVE_TIMEOUT:
                new_state = "review"
            
            # Check if running tasks
            elif task_mtime > 0:
                task_content = get_file_content(TASK_FILE)
                # If task.md was recently modified OR it has in-progress items
                if (now - task_mtime) < ACTIVE_TIMEOUT or "[/]" in task_content:
                    new_state = "running"
                elif "[x]" in task_content and "[ ]" not in task_content:
                    new_state = "idle"
                    
            if new_state != current_state:
                print(f"State changed: {current_state} -> {new_state}")
                current_state = new_state
                with open(STATE_FILE, 'w', encoding='utf-8') as f:
                    f.write(new_state)
                    
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    main()
