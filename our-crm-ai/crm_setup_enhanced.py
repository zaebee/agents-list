import requests
import os
import json
import argparse
from pathlib import Path
from functools import wraps
import time

# --- Configuration ---
API_KEY = os.environ.get("YOUGILE_API_KEY")
BASE_URL = "https://yougile.com/api-v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Rate limiting configuration
RATE_LIMIT_DELAY = 0.5  # seconds between API calls
BATCH_DELAY = 2.0      # seconds between batches
DEFAULT_TIMEOUT = 30

def rate_limited_request(delay=RATE_LIMIT_DELAY):
    """Decorator to add rate limiting to API requests."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'timeout' not in kwargs:
                kwargs['timeout'] = DEFAULT_TIMEOUT
            kwargs['verify'] = True
            result = func(*args, **kwargs)
            time.sleep(delay)
            return result
        return wrapper
    return decorator

@rate_limited_request()
def make_api_request(method: str, url: str, **kwargs):
    """Rate-limited API request wrapper."""
    return requests.request(method, url, headers=HEADERS, **kwargs)

PROJECT_NAME = "AI Team Communication"
BOARD_NAME = "AI Team Tasks"
COLUMN_NAMES = ["To Do", "In Progress", "Done", "Archived"]

def get_all_agent_names():
    """Load all agent names from the parent directory's agents folder."""
    agents_dir = Path(__file__).parent.parent / 'agents'
    agent_files = [f for f in agents_dir.glob('*.md') if f.name not in ['README.md']]
    agent_names = sorted([f.stem for f in agent_files])
    print(f"Found {len(agent_names)} agents:")
    for i, name in enumerate(agent_names, 1):
        print(f"  {i:2d}. {name}")
    return agent_names

def get_or_create_project(project_id=None):
    """Get an existing project or create a new one."""
    if project_id:
        print(f"Using existing project with ID: {project_id}")
        # Verify project exists
        res = make_api_request("GET", f"{BASE_URL}/projects/{project_id}")
        res.raise_for_status()
        return project_id
    else:
        print(f"Creating project: '{PROJECT_NAME}'...")
        project_data = {"title": PROJECT_NAME}
        project_res = make_api_request("POST", f"{BASE_URL}/projects", json=project_data)
        project_res.raise_for_status()
        new_project_id = project_res.json().get("id")
        print(f"Project created with ID: {new_project_id}")
        return new_project_id

def get_or_create_board(project_id):
    """Get an existing board or create a new one."""
    boards_res = make_api_request("GET", f"{BASE_URL}/projects/{project_id}/boards")
    boards_res.raise_for_status()
    boards = boards_res.json()
    
    for board in boards:
        if board['title'] == BOARD_NAME:
            board_id = board['id']
            print(f"Found existing board '{BOARD_NAME}' with ID: {board_id}")
            return board_id

    print(f"Creating board: '{BOARD_NAME}'...")
    board_data = {"title": BOARD_NAME, "projectId": project_id}
    board_res = make_api_request("POST", f"{BASE_URL}/boards", json=board_data)
    board_res.raise_for_status()
    new_board_id = board_res.json().get("id")
    print(f"Board created with ID: {new_board_id}")
    return new_board_id

def get_or_create_columns(board_id):
    """Get existing columns or create new ones."""
    columns_res = make_api_request("GET", f"{BASE_URL}/boards/{board_id}/columns")
    columns_res.raise_for_status()
    existing_columns = {c['title']: c['id'] for c in columns_res.json()}
    
    column_ids = {}
    for name in COLUMN_NAMES:
        if name in existing_columns:
            column_ids[name] = existing_columns[name]
            print(f"Found existing column '{name}' with ID: {existing_columns[name]}")
        else:
            print(f"Creating column: '{name}'...")
            column_data = {"title": name, "boardId": board_id}
            column_res = make_api_request("POST", f"{BASE_URL}/columns", json=column_data)
            column_res.raise_for_status()
            column_id = column_res.json().get("id")
            column_ids[name] = column_id
            print(f"Column '{name}' created with ID: {column_id}")
    return column_ids

def main():
    parser = argparse.ArgumentParser(description="Set up the YouGile project for the AI-CRM.")
    parser.add_argument("--project-id", help="The ID of an existing YouGile project to use.")
    args = parser.parse_args()

    if not API_KEY:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        return

    try:
        ai_owner_roles = get_all_agent_names()
        print(f"\nWill ensure {len(ai_owner_roles)} AI owner roles exist in YouGile.")
        
        response = input("\nProceed with setup? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
            
    except Exception as e:
        print(f"Error loading agent names: {e}")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    print(f"\nStarting YouGile project setup...")

    try:
        project_id = get_or_create_project(args.project_id)
        board_id = get_or_create_board(project_id)
        column_ids = get_or_create_columns(board_id)

        print("Creating 'AI Owner' sticker...")
        sticker_data = {"name": "AI Owner"}
        sticker_res = make_api_request("POST", f"{BASE_URL}/string-stickers", json=sticker_data)
        sticker_res.raise_for_status()
        sticker_id = sticker_res.json().get("id")
        print(f"'AI Owner' sticker created with ID: {sticker_id}")

        print(f"Associating sticker with board '{BOARD_NAME}'...")
        board_details_res = make_api_request("GET", f"{BASE_URL}/boards/{board_id}")
        board_details_res.raise_for_status()
        board_stickers = board_details_res.json().get("stickers", {})
        if "custom" not in board_stickers:
            board_stickers["custom"] = {}
        board_stickers["custom"][sticker_id] = True

        update_board_data = {"stickers": board_stickers}
        update_board_res = make_api_request("PUT", f"{BASE_URL}/boards/{board_id}", json=update_board_data)
        update_board_res.raise_for_status()
        print("Sticker associated successfully.")

        print(f"Creating states for 'AI Owner' sticker ({len(ai_owner_roles)} agents)...")
        owner_state_ids = {}
        
        batch_size = 5
        for i in range(0, len(ai_owner_roles), batch_size):
            batch = ai_owner_roles[i:i + batch_size]
            print(f"  Creating batch {i//batch_size + 1}: {', '.join(batch)}")
            
            for role_name in batch:
                try:
                    state_data = {"name": role_name}
                    state_res = make_api_request("POST", f"{BASE_URL}/string-stickers/{sticker_id}/states", json=state_data)
                    state_res.raise_for_status()
                    state_id = state_res.json().get("id")
                    owner_state_ids[role_name] = state_id
                    print(f"    ✓ {role_name}")
                except requests.exceptions.RequestException as e:
                    print(f"    ✗ {role_name}: {e}")
            
            if i + batch_size < len(ai_owner_roles):
                print(f"  ⏳ Waiting {BATCH_DELAY}s before next batch...")
                time.sleep(BATCH_DELAY)

        print(f"✅ Successfully created {len(owner_state_ids)} agent states")

        config = {
            "project_id": project_id,
            "board_id": board_id,
            "columns": column_ids,
            "ai_owner_sticker": {
                "id": sticker_id,
                "states": owner_state_ids
            },
            "metadata": {
                "total_agents": len(ai_owner_roles),
                "setup_version": "enhanced_v1.2",
                "created_with": "crm_setup_enhanced.py"
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        
        print(f"\n✅ Configuration saved to {config_path}")
        print(f"✅ Setup complete!")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ An API error occurred: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
