import requests
import json
import os

# --- Configuration ---
API_KEY = os.environ.get("YOUGILE_API_KEY")
BASE_URL = "https://yougile.com/api-v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

PROJECT_NAME = "AI Team Communication"
BOARD_NAME = "AI Team Tasks"
COLUMN_NAMES = ["To Do", "In Progress", "Done"]

def main():
    """
    Sets up the initial project structure in YouGile.
    """
    if not API_KEY:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        print("Please set it to your YouGile API key.")
        return

    print("Starting YouGile project setup...")

    try:
        # 1. Create Project
        print(f"Creating project: '{PROJECT_NAME}'...")
        project_data = {"title": PROJECT_NAME}
        project_res = requests.post(f"{BASE_URL}/projects", headers=HEADERS, json=project_data)
        project_res.raise_for_status()
        project_id = project_res.json().get("id")
        if not project_id:
            print("Error: Could not get project ID.")
            return
        print(f"Project created with ID: {project_id}")

        # 2. Create Board
        print(f"Creating board: '{BOARD_NAME}'...")
        board_data = {"title": BOARD_NAME, "projectId": project_id}
        board_res = requests.post(f"{BASE_URL}/boards", headers=HEADERS, json=board_data)
        board_res.raise_for_status()
        board_id = board_res.json().get("id")
        if not board_id:
            print("Error: Could not get board ID.")
            return
        print(f"Board created with ID: {board_id}")

        # 3. Create Columns
        print("Creating columns...")
        column_ids = {}
        for column_name in COLUMN_NAMES:
            print(f"  - Creating column: '{column_name}'")
            column_data = {"title": column_name, "boardId": board_id}
            column_res = requests.post(f"{BASE_URL}/columns", headers=HEADERS, json=column_data)
            column_res.raise_for_status()
            column_id = column_res.json().get("id")
            if not column_id:
                print(f"Error: Could not create column '{column_name}'.")
                continue
            column_ids[column_name] = column_id
            print(f"    Column '{column_name}' created with ID: {column_id}")

        if len(column_ids) != len(COLUMN_NAMES):
            print("Error: Not all columns were created successfully.")
            return

        # 4. Save configuration
        config = {
            "project_id": project_id,
            "board_id": board_id,
            "columns": column_ids
        }
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        print("\nConfiguration saved to config.json")
        print("Setup complete!")

    except requests.exceptions.RequestException as e:
        print(f"\nAn API error occurred: {e}")
        if e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")

if __name__ == "__main__":
    main()
