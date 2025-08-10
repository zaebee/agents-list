import requests
import json
import os

# --- Configuration ---
API_KEY = os.environ.get("YOUGILE_API_KEY")
BASE_URL = "https://yougile.com/api-v2"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

PROJECT_NAME = "AI Team Communication"
BOARD_NAME = "AI Team Tasks"
COLUMN_NAMES = ["To Do", "In Progress", "Done"]
AI_OWNER_ROLES = [
    "api-documenter",
    "ai-engineer",
    "frontend-developer",
    "deployment-engineer",
    "business-analyst",
]


def main():
    """
    Sets up the initial project structure in YouGile.
    """
    if not API_KEY:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        print("Please set it to your YouGile API key.")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    print("Starting YouGile project setup...")

    try:
        # 1. Create Project
        print(f"Creating project: '{PROJECT_NAME}'...")
        project_data = {"title": PROJECT_NAME}
        project_res = requests.post(
            f"{BASE_URL}/projects", headers=HEADERS, json=project_data
        )
        project_res.raise_for_status()
        project_id = project_res.json().get("id")
        print(f"Project created with ID: {project_id}")

        # 2. Create Board
        print(f"Creating board: '{BOARD_NAME}'...")
        board_data = {"title": BOARD_NAME, "projectId": project_id}
        board_res = requests.post(
            f"{BASE_URL}/boards", headers=HEADERS, json=board_data
        )
        board_res.raise_for_status()
        board_id = board_res.json().get("id")
        print(f"Board created with ID: {board_id}")

        # 3. Create Columns
        print("Creating columns...")
        column_ids = {}
        for column_name in COLUMN_NAMES:
            print(f"  - Creating column: '{column_name}'")
            column_data = {"title": column_name, "boardId": board_id}
            column_res = requests.post(
                f"{BASE_URL}/columns", headers=HEADERS, json=column_data
            )
            column_res.raise_for_status()
            column_id = column_res.json().get("id")
            column_ids[column_name] = column_id
            print(f"    Column '{column_name}' created with ID: {column_id}")

        # 4. Create AI Owner Sticker (at company level)
        print("Creating 'AI Owner' sticker...")
        sticker_data = {"name": "AI Owner"}
        sticker_res = requests.post(
            f"{BASE_URL}/string-stickers", headers=HEADERS, json=sticker_data
        )
        sticker_res.raise_for_status()
        sticker_id = sticker_res.json().get("id")
        print(f"'AI Owner' sticker created with ID: {sticker_id}")

        # 5. Associate Sticker with Board
        print(f"Associating sticker with board '{BOARD_NAME}'...")
        board_details_res = requests.get(
            f"{BASE_URL}/boards/{board_id}", headers=HEADERS
        )
        board_details_res.raise_for_status()
        board_stickers = board_details_res.json().get("stickers", {})
        if "custom" not in board_stickers:
            board_stickers["custom"] = {}
        board_stickers["custom"][sticker_id] = True

        update_board_data = {"stickers": board_stickers}
        update_board_res = requests.put(
            f"{BASE_URL}/boards/{board_id}", headers=HEADERS, json=update_board_data
        )
        update_board_res.raise_for_status()
        print("Sticker associated successfully.")

        # 6. Create States for AI Owner Sticker
        print("Creating states for 'AI Owner' sticker...")
        owner_state_ids = {}
        for role_name in AI_OWNER_ROLES:
            print(f"  - Creating state: '{role_name}'")
            state_data = {"name": role_name}
            state_res = requests.post(
                f"{BASE_URL}/string-stickers/{sticker_id}/states",
                headers=HEADERS,
                json=state_data,
            )
            state_res.raise_for_status()
            state_id = state_res.json().get("id")
            owner_state_ids[role_name] = state_id
            print(f"    State '{role_name}' created with ID: {state_id}")

        # 7. Save configuration
        config = {
            "project_id": project_id,
            "board_id": board_id,
            "columns": column_ids,
            "ai_owner_sticker": {"id": sticker_id, "states": owner_state_ids},
        }
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        print(f"\nConfiguration saved to {config_path}")
        print("Setup complete!")

    except requests.exceptions.RequestException as e:
        print(f"\nAn API error occurred: {e}")
        if e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")


if __name__ == "__main__":
    main()
