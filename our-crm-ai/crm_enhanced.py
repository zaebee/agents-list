import requests
import json
import os
import argparse
import time
import uuid
from functools import wraps
from agent_selector import suggest_agents

# --- Configuration ---
API_KEY = os.environ.get("YOUGILE_API_KEY")
BASE_URL = "https://yougile.com/api-v2"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# API Configuration
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def retry_api_call(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Decorator to add retry logic for API calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        print(f"❌ API call failed after {max_retries} attempts: {e}")
                        break
                    
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    print(f"⚠️  API call failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator

def validate_task_id(task_id: str) -> bool:
    """Validate task ID format to prevent injection attacks."""
    if not task_id or not isinstance(task_id, str):
        return False
    
    # Try UUID format first
    try:
        uuid.UUID(task_id)
        return True
    except ValueError:
        pass
    
    # Fallback: alphanumeric with minimum length
    return len(task_id) >= 8 and all(c.isalnum() or c == '-' for c in task_id)

@retry_api_call()
def make_api_request(method: str, url: str, **kwargs):
    """Enhanced API request wrapper with timeout and retry logic."""
    # Add default timeout if not specified
    if 'timeout' not in kwargs:
        kwargs['timeout'] = DEFAULT_TIMEOUT
    
    # Ensure SSL verification
    kwargs['verify'] = True
    
    # Add headers
    if 'headers' not in kwargs:
        kwargs['headers'] = HEADERS
    
    return requests.request(method, url, **kwargs)

def load_config():
    """Loads the configuration from config.json."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found.")
        print("Please run the crm_setup_enhanced.py script first.")
        return None

def handle_api_error(response):
    """Handles API errors by printing details."""
    print(f"Error: API request failed with status code {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except json.JSONDecodeError:
        print(f"Response: {response.text}")

def suggest_owner_for_task(title, description):
    """Suggest AI owner based on task content using the agent selector."""
    combined_text = f"{title} {description}"
    suggestions = suggest_agents(combined_text, max_suggestions=3)
    
    if suggestions:
        print(f"\n🤖 AI Agent Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            confidence = suggestion['confidence']
            agent = suggestion['agent']
            keywords = ', '.join(suggestion['matched_keywords'])
            print(f"  {i}. {agent} ({confidence:.1f}% confidence)")
            print(f"     Keywords: {keywords}")
        
        top_suggestion = suggestions[0]['agent']
        print(f"\n💡 Recommended: {top_suggestion}")
        
        # Ask user if they want to use the suggestion
        use_suggestion = input(f"Use {top_suggestion} as owner? (y/n): ").strip().lower()
        if use_suggestion == 'y':
            return top_suggestion
    
    return None

# --- Command Handlers ---

def create_task(args, config):
    """Creates a new task in the 'To Do' column with enhanced AI owner suggestion."""
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
    owner = args.owner
    
    # If no owner specified, suggest one based on task content
    if not owner and not args.no_ai_suggest:
        print("\n🔍 Analyzing task for AI agent suggestions...")
        suggested_owner = suggest_owner_for_task(args.title, args.description)
        if suggested_owner:
            owner = suggested_owner

    if owner:
        owner_sticker_config = config.get("ai_owner_sticker")
        if not owner_sticker_config:
            print("Error: 'ai_owner_sticker' not found in config.json. Please run setup.")
            return

        sticker_id = owner_sticker_config.get("id")
        owner_state_id = owner_sticker_config.get("states", {}).get(owner)

        if not owner_state_id:
            print(f"Error: Owner '{owner}' is not a valid AI agent role in config.")
            available_agents = list(owner_sticker_config.get("states", {}).keys())
            print(f"Available agents: {', '.join(sorted(available_agents)[:10])}...")
            return

        task_data["stickers"] = {sticker_id: owner_state_id}
        print(f"🎯 Assigned to: {owner}")

    response = make_api_request("POST", f"{BASE_URL}/tasks", json=task_data)

    if response.status_code == 201:
        task_id = response.json().get("id")
        print(f"✅ Task created successfully with ID: {task_id}")
    else:
        handle_api_error(response)

def update_task(args, config):
    """Updates an existing task with enhanced validation."""
    # Validate task ID format
    if not validate_task_id(args.task_id):
        print("❌ Error: Invalid task ID format. Task ID must be a valid UUID or alphanumeric string.")
        return
        
    print(f"Updating task: {args.task_id}...")

    if not args.owner:
        print("Error: Nothing to update. Please provide an attribute to update (e.g., --owner).")
        return

    update_data = {}

    if args.owner:
        owner_sticker_config = config.get("ai_owner_sticker")
        if not owner_sticker_config:
            print("Error: 'ai_owner_sticker' not found in config.json. Please run setup.")
            return

        sticker_id = owner_sticker_config.get("id")
        owner_state_id = owner_sticker_config.get("states", {}).get(args.owner)

        if not owner_state_id:
            print(f"Error: Owner '{args.owner}' is not a valid AI agent role in config.")
            available_agents = list(owner_sticker_config.get("states", {}).keys())
            print(f"Available agents ({len(available_agents)}): {', '.join(sorted(available_agents)[:5])}...")
            return

        update_data["stickers"] = {sticker_id: owner_state_id}

    response = make_api_request("PUT", f"{BASE_URL}/tasks/{args.task_id}", json=update_data)

    if response.status_code == 200:
        print("✅ Task updated successfully.")
    else:
        handle_api_error(response)

def list_tasks(args, config):
    """Lists all tasks on the board with enhanced display."""
    print("📋 Fetching tasks from the board...")
    board_id = config["board_id"]

    all_tasks = []
    try:
        # Get tasks from each column
        for column_name, column_id in config["columns"].items():
            params = {"columnId": column_id, "limit": 1000}
            response = make_api_request("GET", f"{BASE_URL}/task-list", params=params)
            response.raise_for_status()
            tasks = response.json().get("content", [])
            for task in tasks:
                task["columnName"] = column_name
            all_tasks.extend(tasks)

        if not all_tasks:
            print("No tasks found on the board.")
            return

        # Group by status
        by_status = {}
        for task in all_tasks:
            status = task['columnName']
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)

        print(f"\n📊 Found {len(all_tasks)} tasks across {len(by_status)} columns")
        print("=" * 60)

        for status, tasks in by_status.items():
            print(f"\n📂 {status} ({len(tasks)} tasks)")
            print("-" * 40)
            
            for task in tasks:
                print(f"  🎫 ID: {task['id'][:8]}...")
                print(f"     Title: {task['title']}")
                
                # Show AI Owner if present
                owner_sticker_config = config.get("ai_owner_sticker", {})
                sticker_id = owner_sticker_config.get("id")
                task_stickers = task.get("stickers", {})
                
                if sticker_id and sticker_id in task_stickers:
                    owner_state_id = task_stickers[sticker_id]
                    states_map = {v: k for k, v in owner_sticker_config.get("states", {}).items()}
                    owner_name = states_map.get(owner_state_id, "Unknown")
                    print(f"     👤 Owner: {owner_name}")
                
                print()

    except requests.exceptions.RequestException as e:
        print(f"❌ An API error occurred: {e}")

def view_task(args, config):
    """Views a single task and its comments with enhanced display."""
    task_id = args.task_id
    
    # Validate task ID format
    if not validate_task_id(task_id):
        print("❌ Error: Invalid task ID format. Task ID must be a valid UUID or alphanumeric string.")
        return
        
    print(f"📖 Fetching details for task: {task_id}...")

    try:
        # Get task details
        task_response = make_api_request("GET", f"{BASE_URL}/tasks/{task_id}")
        task_response.raise_for_status()
        task = task_response.json()

        print("\n" + "=" * 60)
        print("📋 TASK DETAILS")
        print("=" * 60)
        print(f"ID: {task.get('id')}")
        print(f"Title: {task.get('title')}")

        # Display AI Owner if present
        owner_sticker_config = config.get("ai_owner_sticker", {})
        sticker_id = owner_sticker_config.get("id")
        task_stickers = task.get("stickers", {})

        if sticker_id and sticker_id in task_stickers:
            owner_state_id = task_stickers[sticker_id]
            states_map = {v: k for k, v in owner_sticker_config.get("states", {}).items()}
            owner_name = states_map.get(owner_state_id, "Unknown")
            print(f"AI Owner: 👤 {owner_name}")

        print(f"\nDescription:")
        print(f"{task.get('description', 'No description.')}")

        # Get task comments
        print("\n" + "-" * 60)
        print("💬 COMMENTS")
        print("-" * 60)
        
        chat_response = make_api_request("GET", f"{BASE_URL}/chats/{task_id}/messages")
        if chat_response.status_code == 200:
            messages = chat_response.json().get("content", [])
            if not messages:
                print("No comments found.")
            else:
                for msg in reversed(messages):
                    print(f"• {msg.get('text')}")
        else:
            print("Could not fetch comments for this task.")

    except requests.exceptions.RequestException as e:
        handle_api_error(e.response)

def comment_on_task(args, config):
    """Adds a comment to a task."""
    task_id = args.task_id
    
    # Validate task ID format
    if not validate_task_id(task_id):
        print("❌ Error: Invalid task ID format. Task ID must be a valid UUID or alphanumeric string.")
        return
        
    print(f"💬 Adding comment to task: {task_id}...")

    comment_data = {"text": args.message}
    response = make_api_request("POST", f"{BASE_URL}/chats/{task_id}/messages", json=comment_data)

    if response.status_code == 201:
        print("✅ Comment added successfully.")
    else:
        handle_api_error(response)

def move_task(args, config):
    """Moves a task to a different column."""
    task_id = args.task_id
    target_column_name = args.column
    
    # Validate task ID format
    if not validate_task_id(task_id):
        print("❌ Error: Invalid task ID format. Task ID must be a valid UUID or alphanumeric string.")
        return
        
    print(f"🔄 Moving task {task_id} to column '{target_column_name}'...")

    target_column_id = config["columns"].get(target_column_name)
    if not target_column_id:
        print(f"❌ Error: Column '{target_column_name}' not found in config.")
        print(f"Available columns are: {list(config['columns'].keys())}")
        return

    update_data = {"columnId": target_column_id}
    response = make_api_request("PUT", f"{BASE_URL}/tasks/{task_id}", json=update_data)

    if response.status_code == 200:
        print("✅ Task moved successfully.")
    else:
        handle_api_error(response)

def list_agents(args, config):
    """Lists all available AI agents."""
    owner_sticker_config = config.get("ai_owner_sticker", {})
    agents = list(owner_sticker_config.get("states", {}).keys())
    
    if not agents:
        print("❌ No AI agents found in configuration.")
        return
    
    print(f"🤖 Available AI Agents ({len(agents)}):")
    print("=" * 50)
    
    # Group by category (rough categorization)
    categories = {
        'Language Specialists': [a for a in agents if any(lang in a for lang in ['python', 'javascript', 'java', 'golang', 'rust', 'cpp', 'csharp', 'php', 'scala', 'elixir'])],
        'Architecture & Backend': [a for a in agents if any(arch in a for arch in ['architect', 'backend', 'api', 'graphql'])],
        'Frontend & Mobile': [a for a in agents if any(fe in a for fe in ['frontend', 'ui-ux', 'mobile', 'ios', 'unity'])],
        'Data & AI': [a for a in agents if any(data in a for data in ['data-', 'ai-', 'ml-', 'mlops'])],
        'Infrastructure': [a for a in agents if any(infra in a for infra in ['devops', 'cloud', 'deployment', 'terraform', 'network', 'database'])],
        'Quality & Security': [a for a in agents if any(qual in a for qual in ['security', 'test', 'code-reviewer', 'performance', 'debugger'])],
        'Documentation': [a for a in agents if any(doc in a for doc in ['docs', 'api-documenter', 'tutorial', 'reference'])],
        'Business & Support': [a for a in agents if any(biz in a for biz in ['business', 'sales', 'customer', 'content', 'legal'])],
    }
    
    uncategorized = set(agents)
    for category, category_agents in categories.items():
        if category_agents:
            print(f"\n📁 {category}:")
            for agent in sorted(category_agents):
                print(f"  • {agent}")
                uncategorized.discard(agent)
    
    if uncategorized:
        print(f"\n📁 Other:")
        for agent in sorted(uncategorized):
            print(f"  • {agent}")

def main():
    """Enhanced main function with better CLI."""
    if not API_KEY:
        print("❌ Error: YOUGILE_API_KEY environment variable not set.")
        return

    config = load_config()
    if not config:
        return

    parser = argparse.ArgumentParser(
        description="Enhanced CLI for AI-powered YouGile CRM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create --title "Fix login bug" --description "Users can't log in"
  %(prog)s create --title "Add dashboard" --owner frontend-developer
  %(prog)s list
  %(prog)s agents
  %(prog)s suggest "optimize database performance"
        """
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new task with AI agent suggestions.")
    create_parser.add_argument("--title", required=True, help="The title of the task.")
    create_parser.add_argument("--description", default="", help="The description of the task.")
    create_parser.add_argument("--owner", help="The AI agent owner for the task.")
    create_parser.add_argument("--no-ai-suggest", action="store_true", help="Skip AI agent suggestions.")
    create_parser.set_defaults(func=create_task)

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing task.")
    update_parser.add_argument("task_id", help="The ID of the task to update.")
    update_parser.add_argument("--owner", help="The new AI agent owner for the task.")
    update_parser.set_defaults(func=update_task)

    # List command
    list_parser = subparsers.add_parser("list", help="List all tasks grouped by status.")
    list_parser.set_defaults(func=list_tasks)

    # View command
    view_parser = subparsers.add_parser("view", help="View a specific task with details.")
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
    
    # Agents command
    agents_parser = subparsers.add_parser("agents", help="List all available AI agents.")
    agents_parser.set_defaults(func=list_agents)

    # Suggest command (standalone agent suggestion)
    suggest_parser = subparsers.add_parser("suggest", help="Suggest AI agents for a task description.")
    suggest_parser.add_argument("description", help="Task description to analyze.")
    suggest_parser.set_defaults(func=lambda args, config: print_agent_suggestions(args.description))

    args = parser.parse_args()
    args.func(args, config)

def print_agent_suggestions(description):
    """Print agent suggestions for a given description."""
    suggestions = suggest_agents(description, max_suggestions=5)
    
    if suggestions:
        print(f"🤖 AI Agent Suggestions for: '{description}'")
        print("=" * 60)
        
        for i, suggestion in enumerate(suggestions, 1):
            confidence = suggestion['confidence']
            agent = suggestion['agent']
            keywords = ', '.join(suggestion['matched_keywords'])
            
            print(f"{i}. {agent} ({confidence:.1f}% confidence)")
            print(f"   Keywords: {keywords}")
            print()
        
        print(f"💡 Top Recommendation: {suggestions[0]['agent']}")
    else:
        print("❌ No specific agent suggestions found.")
        print("💡 Consider using 'search-specialist' for general research tasks.")

if __name__ == "__main__":
    main()