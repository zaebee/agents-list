import requests
import json
import os
import sys
import time
from pathlib import Path
from functools import wraps

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
            # Add timeout if not specified
            if 'timeout' not in kwargs:
                kwargs['timeout'] = DEFAULT_TIMEOUT
            
            # Ensure SSL verification
            kwargs['verify'] = True
            
            result = func(*args, **kwargs)
            time.sleep(delay)  # Rate limit delay
            return result
        return wrapper
    return decorator

@rate_limited_request()
def make_api_request(method: str, url: str, **kwargs):
    """Rate-limited API request wrapper."""
    return requests.request(method, url, **kwargs)

PROJECT_NAME = "AI Team Communication"
BOARD_NAME = "AI Team Tasks"
COLUMN_NAMES = ["To Do", "In Progress", "Done"]

def get_all_agent_names():
    """Load all agent names from the parent directory's markdown files."""
    # Go up one level to the agents directory
    agents_dir = Path(__file__).parent.parent
    agent_files = list(agents_dir.glob('*.md'))
    # Exclude README and other non-agent files
    agent_files = [f for f in agent_files if f.name not in ['README.md']]
    
    agent_names = [f.stem for f in agent_files]
    agent_names.sort()  # Sort for consistent ordering
    
    print(f"Found {len(agent_names)} agents:")
    for i, name in enumerate(agent_names, 1):
        print(f"  {i:2d}. {name}")
    
    return agent_names

def main():
    """
    Sets up the initial project structure in YouGile with all available agents.
    """
    if not API_KEY:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        print("Please set it to your YouGile API key.")
        return

    # Get all available agents
    try:
        ai_owner_roles = get_all_agent_names()
        print(f"\nWill create {len(ai_owner_roles)} AI owner roles in YouGile.")
        
        # Confirm before proceeding
        response = input("\nProceed with setup? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
            
    except Exception as e:
        print(f"Error loading agent names: {e}")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    print(f"\nStarting YouGile project setup with {len(ai_owner_roles)} agents...")

    try:
        # 1. Create Project
        print(f"Creating project: '{PROJECT_NAME}'...")
        project_data = {"title": PROJECT_NAME}
        project_res = make_api_request("POST", f"{BASE_URL}/projects", headers=HEADERS, json=project_data)
        project_res.raise_for_status()
        project_id = project_res.json().get("id")
        print(f"Project created with ID: {project_id}")

        # 2. Create Board
        print(f"Creating board: '{BOARD_NAME}'...")
        board_data = {"title": BOARD_NAME, "projectId": project_id}
        board_res = make_api_request("POST", f"{BASE_URL}/boards", headers=HEADERS, json=board_data)
        board_res.raise_for_status()
        board_id = board_res.json().get("id")
        print(f"Board created with ID: {board_id}")

        # 3. Create Columns
        print("Creating columns...")
        column_ids = {}
        for column_name in COLUMN_NAMES:
            print(f"  - Creating column: '{column_name}'")
            column_data = {"title": column_name, "boardId": board_id}
            column_res = make_api_request("POST", f"{BASE_URL}/columns", headers=HEADERS, json=column_data)
            column_res.raise_for_status()
            column_id = column_res.json().get("id")
            column_ids[column_name] = column_id
            print(f"    Column '{column_name}' created with ID: {column_id}")

        # 4. Create AI Owner Sticker (at company level)
        print("Creating 'AI Owner' sticker...")
        sticker_data = {"name": "AI Owner"}
        sticker_res = make_api_request("POST", f"{BASE_URL}/string-stickers", headers=HEADERS, json=sticker_data)
        sticker_res.raise_for_status()
        sticker_id = sticker_res.json().get("id")
        print(f"'AI Owner' sticker created with ID: {sticker_id}")

        # 5. Associate Sticker with Board
        print(f"Associating sticker with board '{BOARD_NAME}'...")
        board_details_res = make_api_request("GET", f"{BASE_URL}/boards/{board_id}", headers=HEADERS)
        board_details_res.raise_for_status()
        board_stickers = board_details_res.json().get("stickers", {})
        if "custom" not in board_stickers:
            board_stickers["custom"] = {}
        board_stickers["custom"][sticker_id] = True

        update_board_data = {"stickers": board_stickers}
        update_board_res = make_api_request("PUT", f"{BASE_URL}/boards/{board_id}", headers=HEADERS, json=update_board_data)
        update_board_res.raise_for_status()
        print("Sticker associated successfully.")

        # 6. Create States for AI Owner Sticker (ALL AGENTS)
        print(f"Creating states for 'AI Owner' sticker ({len(ai_owner_roles)} agents)...")
        owner_state_ids = {}
        
        # Create states in batches to avoid API rate limiting
        batch_size = 5
        for i in range(0, len(ai_owner_roles), batch_size):
            batch = ai_owner_roles[i:i + batch_size]
            print(f"  Creating batch {i//batch_size + 1}: {', '.join(batch)}")
            
            for role_name in batch:
                try:
                    state_data = {"name": role_name}
                    state_res = make_api_request("POST", f"{BASE_URL}/string-stickers/{sticker_id}/states", headers=HEADERS, json=state_data)
                    state_res.raise_for_status()
                    state_id = state_res.json().get("id")
                    owner_state_ids[role_name] = state_id
                    print(f"    ✓ {role_name}")
                except requests.exceptions.RequestException as e:
                    print(f"    ✗ {role_name}: {e}")
                    # Continue with other agents even if one fails
            
            # Delay between batches to prevent overwhelming the API
            if i + batch_size < len(ai_owner_roles):
                print(f"  ⏳ Waiting {BATCH_DELAY}s before next batch...")
                time.sleep(BATCH_DELAY)

        print(f"✅ Successfully created {len(owner_state_ids)} agent states")

        # 7. Save configuration
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
                "setup_version": "enhanced_v1.0",
                "created_with": "crm_setup_enhanced.py"
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        
        print(f"\n✅ Configuration saved to {config_path}")
        print(f"✅ Setup complete!")
        print(f"\nSummary:")
        print(f"  - Project: {project_id}")
        print(f"  - Board: {board_id}")
        print(f"  - Columns: {len(column_ids)}")
        print(f"  - AI Agents: {len(owner_state_ids)}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ An API error occurred: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()