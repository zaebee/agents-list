import requests
import json
import os
import argparse

# --- Configuration ---
API_KEY = os.environ.get("YOUGILE_API_KEY")
BASE_URL = "https://yougile.com/api-v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def load_config():
    """Loads the configuration from config.json."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found.")
        print("Please run the crm_setup.py script first.")
        return None

def handle_api_error(response):
    """Handles API errors by printing details."""
    print(f"Error: API request failed with status code {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except json.JSONDecodeError:
        print(f"Response: {response.text}")

# --- Command Handlers ---

def create_task(args, config):
    """Creates a new task in the 'To Do' column."""
    print(f"Creating task: '{args.title}'...")

    todo_column_id = config["columns"].get("To Do")
    if not todo_column_id:
        print("Error: 'To Do' column ID not found in config.json.")
        return

    task_data = {
        "title": args.title,
        "description": args.description,
        "columnId": todo_column_id
    }

    # Handle AI Owner sticker
    if args.owner:
        owner_sticker_config = config.get("ai_owner_sticker")
        if not owner_sticker_config:
            print("Error: 'ai_owner_sticker' not found in config.json. Please run setup.")
            return

        sticker_id = owner_sticker_config.get("id")
        owner_state_id = owner_sticker_config.get("states", {}).get(args.owner)

        if not owner_state_id:
            print(f"Error: Owner '{args.owner}' is not a valid AI agent role in config.")
            return

        task_data["stickers"] = {sticker_id: owner_state_id}

    response = requests.post(f"{BASE_URL}/tasks", headers=HEADERS, json=task_data)

    if response.status_code == 201:
        task_id = response.json().get("id")
        print(f"Task created successfully with ID: {task_id}")
    else:
        handle_api_error(response)

def list_tasks(args, config):
    """Lists all tasks on the board."""
    print("Fetching tasks from the board...")
    board_id = config["board_id"]
    column_ids = config["columns"].values()

    all_tasks = []
    try:
        # Get tasks from each column since there's no direct board filter
        for column_name, column_id in config["columns"].items():
            params = {"columnId": column_id, "limit": 1000}
            response = requests.get(f"{BASE_URL}/task-list", headers=HEADERS, params=params)
            response.raise_for_status()
            tasks = response.json().get("content", [])
            for task in tasks:
                task["columnName"] = column_name
            all_tasks.extend(tasks)

        if not all_tasks:
            print("No tasks found on the board.")
            return

        print("\n--- Tasks on Board ---")
        for task in all_tasks:
            print(f"  - ID: {task['id']}")
            print(f"    Title: {task['title']}")
            print(f"    Status: {task['columnName']}")
            print("-" * 20)

    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")

def view_task(args, config):
    """Views a single task and its comments."""
    task_id = args.task_id
    print(f"Fetching details for task: {task_id}...")

    try:
        # Get task details
        task_response = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=HEADERS)
        task_response.raise_for_status()
        task = task_response.json()

        print("\n--- Task Details ---")
        print(f"ID: {task.get('id')}")
        print(f"Title: {task.get('title')}")

        # Display AI Owner if present
        owner_sticker_config = config.get("ai_owner_sticker", {})
        sticker_id = owner_sticker_config.get("id")
        task_stickers = task.get("stickers", {})

        if sticker_id and sticker_id in task_stickers:
            owner_state_id = task_stickers[sticker_id]
            # Invert the states mapping to find the name from the ID
            states_map = {v: k for k, v in owner_sticker_config.get("states", {}).items()}
            owner_name = states_map.get(owner_state_id, "Unknown")
            print(f"AI Owner: {owner_name}")

        print(f"Description:\n{task.get('description', 'No description.')}")

        # Get task comments (from chat)
        print("\n--- Comments ---")
        # Assuming task ID is the chat ID for the task
        chat_response = requests.get(f"{BASE_URL}/chats/{task_id}/messages", headers=HEADERS)
        if chat_response.status_code == 200:
            messages = chat_response.json().get("content", [])
            if not messages:
                print("No comments found.")
            else:
                for msg in reversed(messages): # Show oldest first
                    print(f"- {msg.get('text')}")
        else:
            print("Could not fetch comments for this task.")

    except requests.exceptions.RequestException as e:
        handle_api_error(e.response)

def comment_on_task(args, config):
    """Adds a comment to a task."""
    task_id = args.task_id
    print(f"Adding comment to task: {task_id}...")

    comment_data = {"text": args.message}
    # Assuming task ID is the chat ID
    response = requests.post(f"{BASE_URL}/chats/{task_id}/messages", headers=HEADERS, json=comment_data)

    if response.status_code == 201:
        print("Comment added successfully.")
    else:
        handle_api_error(response)

def move_task(args, config):
    """Moves a task to a different column."""
    task_id = args.task_id
    target_column_name = args.column
    print(f"Moving task {task_id} to column '{target_column_name}'...")

    target_column_id = config["columns"].get(target_column_name)
    if not target_column_id:
        print(f"Error: Column '{target_column_name}' not found in config.")
        print(f"Available columns are: {list(config['columns'].keys())}")
        return

    update_data = {"columnId": target_column_id}
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", headers=HEADERS, json=update_data)

    if response.status_code == 200:
        print("Task moved successfully.")
    else:
        handle_api_error(response)

def main():
    """Main function to parse arguments and call handlers."""
    if not API_KEY:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        return

    config = load_config()
    if not config:
        return

    parser = argparse.ArgumentParser(description="A CLI for interacting with the YouGile-based CRM.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new task.")
    create_parser.add_argument("--title", required=True, help="The title of the task.")
    create_parser.add_argument("--description", default="", help="The description of the task.")
    create_parser.add_argument("--owner", help="The AI agent owner for the task.")
    create_parser.set_defaults(func=create_task)

    # List command
    list_parser = subparsers.add_parser("list", help="List all tasks.")
    list_parser.set_defaults(func=list_tasks)

    # View command
    view_parser = subparsers.add_parser("view", help="View a specific task.")
    view_parser.add_argument("task_id", help="The ID of the task to view.")
    view_parser.set_defaults(func=view_task)

    # Comment command
    comment_parser = subparsers.add_parser("comment", help="Add a comment to a task.")
    comment_parser.add_argument("task_id", help="The ID of the task to comment on.")
    comment_parser.add_argument("--message", required=True, help="The comment message.")
    comment_parser.set_defaults(func=comment_on_task)

    # Move command
    move_parser = subparsers.add_parser("move", help="Move a task to a different column.")
    move_parser.add_argument("task_id", help="The ID of the task to move.")
    move_parser.add_argument("--column", required=True, help="The name of the target column.")
    move_parser.set_defaults(func=move_task)

    args = parser.parse_args()
    args.func(args, config)

if __name__ == "__main__":
    main()
