import requests
import os
import json

# --- Configuration ---
API_KEY = os.environ.get("YOUGILE_API_KEY")
BASE_URL = "https://yougile.com/api-v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
TARGET_PROJECT_NAME = "AI Team Communication"
SOURCE_PROJECT_NAMES = ["claude", "gemini"]

def make_api_request(method: str, url: str, **kwargs):
    """Makes an API request."""
    return requests.request(method, url, headers=HEADERS, **kwargs)

def get_all_projects():
    """Gets all projects."""
    response = make_api_request("GET", f"{BASE_URL}/projects")
    response.raise_for_status()
    return response.json().get("content", [])

def get_all_boards():
    """Gets all boards."""
    response = make_api_request("GET", f"{BASE_URL}/boards")
    response.raise_for_status()
    return response.json().get("content", [])

def get_all_columns():
    """Gets all columns."""
    response = make_api_request("GET", f"{BASE_URL}/columns")
    response.raise_for_status()
    return response.json().get("content", [])

def get_tasks_for_board(board_id, all_columns):
    """Gets all tasks for a given board."""
    all_tasks = []
    board_columns = [c for c in all_columns if c.get('boardId') == board_id]
    for column in board_columns:
        tasks_response = make_api_request("GET", f"{BASE_URL}/task-list", params={"columnId": column['id']})
        tasks_response.raise_for_status()
        tasks = tasks_response.json().get("content", [])
        for task in tasks:
            task["columnName"] = column['title']
        all_tasks.extend(tasks)
    return all_tasks

def main():
    """Main function."""
    if not API_KEY:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        return

    all_projects = get_all_projects()
    all_boards = get_all_boards()
    all_columns = get_all_columns()

    # Find target project
    target_project = next((p for p in all_projects if p['title'] == TARGET_PROJECT_NAME), None)
    if not target_project:
        print(f"Error: Target project '{TARGET_PROJECT_NAME}' not found.")
        return
    target_project_id = target_project['id']
    print(f"Found target project '{TARGET_PROJECT_NAME}' with ID: {target_project_id}")

    # Find target board and columns
    target_board = next((b for b in all_boards if b.get('projectId') == target_project_id), None)
    if not target_board:
        print(f"Error: No board found in target project '{TARGET_PROJECT_NAME}'.")
        return
    target_board_id = target_board['id']
    target_columns = {c['title']: c['id'] for c in all_columns if c.get('boardId') == target_board_id}
    print(f"Found target board '{target_board['title']}' with ID: {target_board_id}")

    # Find source projects
    source_projects = [p for p in all_projects if p['title'] in SOURCE_PROJECT_NAMES]
    if not source_projects:
        print("No source projects found.")
        return

    # Move tasks
    for project in source_projects:
        project_id = project['id']
        project_title = project['title']
        print(f"\nProcessing project: {project_title}")
        
        source_boards = [b for b in all_boards if b.get('projectId') == project_id]
        for board in source_boards:
            tasks = get_tasks_for_board(board['id'], all_columns)
            print(f"  Found {len(tasks)} tasks on board '{board['title']}'")
            for task in tasks:
                status = task['columnName']
                target_column_id = target_columns.get(status)
                if not target_column_id:
                    print(f"    - Warning: No matching column for status '{status}' in target board. Skipping task '{task['title']}'.")
                    continue

                print(f"    - Moving task '{task['title']}' to '{TARGET_PROJECT_NAME}'")
                try:
                    update_data = {"columnId": target_column_id}
                    response = make_api_request("PUT", f"{BASE_URL}/tasks/{task['id']}", json=update_data)
                    response.raise_for_status()
                    print(f"      ✓ Moved successfully.")
                except requests.exceptions.RequestException as e:
                    print(f"      ✗ Error moving task: {e}")

    print("\n✅ Task consolidation complete.")

if __name__ == "__main__":
    main()
