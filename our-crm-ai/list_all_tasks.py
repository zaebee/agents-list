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

def make_api_request(method: str, url: str, **kwargs):
    """Makes an API request."""
    return requests.request(method, url, headers=HEADERS, **kwargs)

def list_all_projects():
    """Lists all projects for the company."""
    print("Fetching all projects...")
    try:
        response = make_api_request("GET", f"{BASE_URL}/projects")
        response.raise_for_status()
        return response.json().get("content", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching projects: {e}")
        return []

def list_all_boards():
    """Lists all boards for the company."""
    print("Fetching all boards...")
    try:
        response = make_api_request("GET", f"{BASE_URL}/boards")
        response.raise_for_status()
        return response.json().get("content", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching boards: {e}")
        return []

def list_all_columns():
    """Lists all columns for the company."""
    print("Fetching all columns...")
    try:
        response = make_api_request("GET", f"{BASE_URL}/columns")
        response.raise_for_status()
        return response.json().get("content", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching columns: {e}")
        return []

def list_tasks_for_board(board_id, all_columns):
    """Lists all tasks for a given board."""
    all_tasks = []
    
    board_columns = [c for c in all_columns if c.get('boardId') == board_id]

    for column in board_columns:
        try:
            tasks_response = make_api_request("GET", f"{BASE_URL}/task-list", params={"columnId": column['id']})
            tasks_response.raise_for_status()
            tasks = tasks_response.json().get("content", [])
            for task in tasks:
                task["columnName"] = column['title']
            all_tasks.extend(tasks)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tasks for column {column['id']}: {e}")
            
    return all_tasks

def main():
    """Main function."""
    if not API_KEY:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        return

    projects = list_all_projects()
    if not projects:
        print("No projects found.")
        return
        
    project_map = {p['id']: p['title'] for p in projects}

    boards = list_all_boards()
    if not boards:
        print("No boards found.")
        return
        
    all_columns = list_all_columns()
    if not all_columns:
        print("No columns found.")
        return

    print(f"\nFound {len(boards)} boards across {len(projects)} projects. Fetching tasks...\n")
    
    # Group boards by project
    boards_by_project = {}
    for board in boards:
        project_id = board.get('projectId')
        if project_id not in boards_by_project:
            boards_by_project[project_id] = []
        boards_by_project[project_id].append(board)

    for project_id, project_boards in boards_by_project.items():
        project_title = project_map.get(project_id, f"Unknown Project ({project_id})")
        print("="*80)
        print(f"Project: {project_title} (ID: {project_id})")
        print("="*80)

        for board in project_boards:
            print(f"\n  Board: {board['title']} (ID: {board['id']})")
            print("  " + "-"*60)
            
            tasks = list_tasks_for_board(board['id'], all_columns)
            if not tasks:
                print("    No tasks found on this board.")
                continue

            for task in tasks:
                print(f"    - Task: {task['title']} (ID: {task['id']})")
                print(f"      Status: {task['columnName']}")

if __name__ == "__main__":
    main()
