import requests
import json
import os
import argparse

BASE_URL = "https://yougile.com/api-v2"

class CRMClient:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.environ.get("YOUGILE_API_KEY")

        if not api_key:
            raise ValueError("YOUGILE_API_KEY not provided or set as an environment variable.")

        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.config = self._load_config()

    def _load_config(self):
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

    def _handle_api_error(self, response):
        """Handles API errors by printing details."""
        print(f"Error: API request failed with status code {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except json.JSONDecodeError:
            print(f"Response: {response.text}")

    def create_task(self, title, description="", owner=None):
        """Creates a new task in the 'To Do' column."""
        print(f"Creating task: '{title}'...")

        if not self.config:
            print("Error: Configuration not loaded.")
            return None

        todo_column_id = self.config["columns"].get("To Do")
        if not todo_column_id:
            print("Error: 'To Do' column ID not found in config.json.")
            return None

        task_data = {
            "title": title,
            "description": description,
            "columnId": todo_column_id
        }

        if owner:
            owner_sticker_config = self.config.get("ai_owner_sticker")
            if not owner_sticker_config:
                print("Error: 'ai_owner_sticker' not found in config.json.")
                return None

            sticker_id = owner_sticker_config.get("id")
            owner_state_id = owner_sticker_config.get("states", {}).get(owner)

            if not owner_state_id:
                print(f"Error: Owner '{owner}' is not a valid AI agent role in config.")
                return None

            task_data["stickers"] = {sticker_id: owner_state_id}

        response = requests.post(f"{BASE_URL}/tasks", headers=self.headers, json=task_data)

        if response.status_code == 201:
            task_id = response.json().get("id")
            print(f"Task created successfully with ID: {task_id}")
            return task_id
        else:
            self._handle_api_error(response)
            return None

    def update_task(self, task_id, owner):
        """Updates an existing task's owner."""
        print(f"Updating task: {task_id}...")

        if not self.config:
            print("Error: Configuration not loaded.")
            return False

        update_data = {}
        owner_sticker_config = self.config.get("ai_owner_sticker")
        if not owner_sticker_config:
            print("Error: 'ai_owner_sticker' not found in config.json.")
            return False

        sticker_id = owner_sticker_config.get("id")
        owner_state_id = owner_sticker_config.get("states", {}).get(owner)

        if not owner_state_id:
            print(f"Error: Owner '{owner}' is not a valid AI agent role in config.")
            return False

        update_data["stickers"] = {sticker_id: owner_state_id}
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", headers=self.headers, json=update_data)

        if response.status_code == 200:
            print("Task updated successfully.")
            return True
        else:
            self._handle_api_error(response)
            return False

    def list_tasks(self):
        """Lists all tasks on the board."""
        print("Fetching tasks from the board...")
        if not self.config:
            print("Error: Configuration not loaded.")
            return []

        all_tasks = []
        try:
            for column_name, column_id in self.config["columns"].items():
                params = {"columnId": column_id, "limit": 1000}
                response = requests.get(f"{BASE_URL}/task-list", headers=self.headers, params=params)
                response.raise_for_status()
                tasks = response.json().get("content", [])
                for task in tasks:
                    task["columnName"] = column_name
                all_tasks.extend(tasks)

            return all_tasks
        except requests.exceptions.RequestException as e:
            print(f"An API error occurred: {e}")
            return []

    def view_task(self, task_id):
        """Views a single task and its comments."""
        print(f"Fetching details for task: {task_id}...")
        if not self.config:
            print("Error: Configuration not loaded.")
            return None

        try:
            task_response = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=self.headers)
            task_response.raise_for_status()
            task = task_response.json()

            chat_response = requests.get(f"{BASE_URL}/chats/{task_id}/messages", headers=self.headers)
            if chat_response.status_code == 200:
                task['comments'] = chat_response.json().get("content", [])
            else:
                task['comments'] = []

            return task
        except requests.exceptions.RequestException as e:
            self._handle_api_error(e.response)
            return None

    def comment_on_task(self, task_id, message):
        """Adds a comment to a task."""
        print(f"Adding comment to task: {task_id}...")
        comment_data = {"text": message}
        response = requests.post(f"{BASE_URL}/chats/{task_id}/messages", headers=self.headers, json=comment_data)

        if response.status_code == 201:
            print("Comment added successfully.")
            return True
        else:
            self._handle_api_error(response)
            return False

    def move_task(self, task_id, column_name):
        """Moves a task to a different column."""
        print(f"Moving task {task_id} to column '{column_name}'...")
        if not self.config:
            print("Error: Configuration not loaded.")
            return False

        target_column_id = self.config["columns"].get(column_name)
        if not target_column_id:
            print(f"Error: Column '{column_name}' not found in config.")
            print(f"Available columns are: {list(self.config['columns'].keys())}")
            return False

        update_data = {"columnId": target_column_id}
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", headers=self.headers, json=update_data)

        if response.status_code == 200:
            print("Task moved successfully.")
            return True
        else:
            self._handle_api_error(response)
            return False

def main():
    """Main function to parse arguments and call CLI handlers."""
    try:
        client = CRMClient()
    except ValueError as e:
        print(e)
        return

    parser = argparse.ArgumentParser(description="A CLI for interacting with the YouGile-based CRM.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new task.")
    create_parser.add_argument("--title", required=True, help="The title of the task.")
    create_parser.add_argument("--description", default="", help="The description of the task.")
    create_parser.add_argument("--owner", help="The AI agent owner for the task.")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing task.")
    update_parser.add_argument("task_id", help="The ID of the task to update.")
    update_parser.add_argument("--owner", required=True, help="The new AI agent owner for the task.")

    # List command
    list_parser = subparsers.add_parser("list", help="List all tasks.")

    # View command
    view_parser = subparsers.add_parser("view", help="View a specific task.")
    view_parser.add_argument("task_id", help="The ID of the task to view.")

    # Comment command
    comment_parser = subparsers.add_parser("comment", help="Add a comment to a task.")
    comment_parser.add_argument("task_id", help="The ID of the task to comment on.")
    comment_parser.add_argument("--message", required=True, help="The comment message.")

    # Move command
    move_parser = subparsers.add_parser("move", help="Move a task to a different column.")
    move_parser.add_argument("task_id", help="The ID of the task to move.")
    move_parser.add_argument("--column", required=True, help="The name of the target column.")

    args = parser.parse_args()

    if args.command == "create":
        client.create_task(args.title, args.description, args.owner)
    elif args.command == "update":
        client.update_task(args.task_id, args.owner)
    elif args.command == "list":
        tasks = client.list_tasks()
        if tasks:
            print("\n--- Tasks on Board ---")
            for task in tasks:
                print(f"  - ID: {task['id']}")
                print(f"    Title: {task['title']}")
                print(f"    Status: {task['columnName']}")
                print("-" * 20)
    elif args.command == "view":
        task = client.view_task(args.task_id)
        if task:
            print("\n--- Task Details ---")
            print(f"ID: {task.get('id')}")
            print(f"Title: {task.get('title')}")
            # Simplified owner display for brevity in this refactoring
            print(f"Description:\n{task.get('description', 'No description.')}")
            print("\n--- Comments ---")
            if not task.get('comments'):
                print("No comments found.")
            else:
                for msg in reversed(task['comments']):
                    print(f"- {msg.get('text')}")
    elif args.command == "comment":
        client.comment_on_task(args.task_id, args.message)
    elif args.command == "move":
        client.move_task(args.task_id, args.column)

if __name__ == "__main__":
    main()
