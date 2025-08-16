# our-crm-ai/commands.py
import uuid

from agent_selector import suggest_agents
from api_client import BASE_URL, handle_api_error, make_api_request
from pm_agent_gateway import PMAgentGateway


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
    return len(task_id) >= 8 and all(c.isalnum() or c == "-" for c in task_id)


def suggest_owner_for_task(title, description, use_pm_gateway=True):
    """Suggest AI owner using PM Agent Gateway for intelligent analysis."""
    if use_pm_gateway:
        try:
            print("\n🎯 Using PM Agent Gateway for intelligent task analysis...")
            pm_gateway = PMAgentGateway()
            result = pm_gateway.create_managed_task(title, description)

            if result["type"] == "direct_assignment":
                suggested_agent = result["assigned_agent"]
                priority = result["priority"]
                estimated_hours = result["analysis"]["estimated_hours"]

                print(f"\n💡 PM Recommendation: {suggested_agent}")
                print(f"📊 Priority: {priority}, Estimated: {estimated_hours} hours")

                use_suggestion = (
                    input(f"Use PM recommendation ({suggested_agent})? (y/n): ")
                    .strip()
                    .lower()
                )
                if use_suggestion == "y":
                    return suggested_agent

            elif result["type"] == "complex_task":
                print("\n⚠️  Complex task detected!")
                print(
                    f"🔄 PM Gateway recommends breaking into {len(result['subtasks'])} subtasks"
                )
                print(f"📊 Priority: {result['priority']}")

                for i, subtask in enumerate(result["subtasks"][:3], 1):
                    print(f"  {i}. {subtask['title']} → {subtask['agent']}")

                if len(result["subtasks"]) > 3:
                    print(f"  ... and {len(result['subtasks']) - 3} more subtasks")

                primary_agent = (
                    result["analysis"]["required_agents"][0]
                    if result["analysis"]["required_agents"]
                    else "business-analyst"
                )

                create_subtasks = (
                    input(
                        f"Create as complex task with primary agent ({primary_agent})? (y/n): "
                    )
                    .strip()
                    .lower()
                )
                if create_subtasks == "y":
                    return primary_agent

        except Exception as e:
            print(f"⚠️  PM Gateway error: {e}, falling back to basic agent selector...")

    combined_text = f"{title} {description}"
    suggestions = suggest_agents(combined_text, max_suggestions=3)

    if suggestions:
        print("\n🤖 Basic Agent Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            confidence = suggestion["confidence"]
            agent = suggestion["agent"]
            keywords = ", ".join(suggestion["matched_keywords"])
            print(f"  {i}. {agent} ({confidence:.1f}% confidence)")
            print(f"     Keywords: {keywords}")

        top_suggestion = suggestions[0]["agent"]
        print(f"\n💡 Recommended: {top_suggestion}")

        use_suggestion = (
            input(f"Use {top_suggestion} as owner? (y/n): ").strip().lower()
        )
        if use_suggestion == "y":
            return top_suggestion

    return None


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
        "columnId": todo_column_id,
    }

    owner = args.owner

    if not owner and not args.no_ai_suggest:
        print("\n🔍 Analyzing task for AI agent suggestions...")
        suggested_owner = suggest_owner_for_task(args.title, args.description)
        if suggested_owner:
            owner = suggested_owner

    if owner:
        owner_sticker_config = config.get("ai_owner_sticker")
        if not owner_sticker_config:
            print(
                "Error: 'ai_owner_sticker' not found in config.json. Please run setup."
            )
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
    if not validate_task_id(args.task_id):
        print(
            "❌ Error: Invalid task ID format. Task ID must be a valid UUID or alphanumeric string."
        )
        return

    print(f"Updating task: {args.task_id}...")

    if not args.owner:
        print(
            "Error: Nothing to update. Please provide an attribute to update (e.g., --owner)."
        )
        return

    update_data = {}

    if args.owner:
        owner_sticker_config = config.get("ai_owner_sticker")
        if not owner_sticker_config:
            print(
                "Error: 'ai_owner_sticker' not found in config.json. Please run setup."
            )
            return

        sticker_id = owner_sticker_config.get("id")
        owner_state_id = owner_sticker_config.get("states", {}).get(args.owner)

        if not owner_state_id:
            print(
                f"Error: Owner '{args.owner}' is not a valid AI agent role in config."
            )
            available_agents = list(owner_sticker_config.get("states", {}).keys())
            print(
                f"Available agents ({len(available_agents)}): {', '.join(sorted(available_agents)[:5])}..."
            )
            return

        update_data["stickers"] = {sticker_id: owner_state_id}

    response = make_api_request(
        "PUT", f"{BASE_URL}/tasks/{args.task_id}", json=update_data
    )

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

        by_status = {}
        for task in all_tasks:
            status = task["columnName"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)

        print(f"\n📊 Found {len(all_tasks)} tasks across {len(by_status)} columns")
        print("=" * 60)

        for status, tasks in by_status.items():
            print(f"\n📂 {status} ({len(tasks)} tasks)")
            print("-" * 40)

            for task in tasks:
                print(f"  🎫 ID: {task['id']}")
                print(f"     Title: {task['title']}")

                owner_sticker_config = config.get("ai_owner_sticker", {})
                sticker_id = owner_sticker_config.get("id")
                task_stickers = task.get("stickers", {})

                if sticker_id and sticker_id in task_stickers:
                    owner_state_id = task_stickers[sticker_id]
                    states_map = {
                        v: k for k, v in owner_sticker_config.get("states", {}).items()
                    }
                    owner_name = states_map.get(owner_state_id, "Unknown")
                    print(f"     👤 Owner: {owner_name}")

                print()

    except requests.exceptions.RequestException as e:
        print(f"❌ An API error occurred: {e}")


def view_task(args, config):
    """Views a single task and its comments with enhanced display."""
    task_id = args.task_id

    if not validate_task_id(task_id):
        print(
            "❌ Error: Invalid task ID format. Task ID must be a valid UUID or alphanumeric string."
        )
        return

    print(f"📖 Fetching details for task: {task_id}...")

    try:
        task_response = make_api_request("GET", f"{BASE_URL}/tasks/{task_id}")
        task_response.raise_for_status()
        task = task_response.json()

        print("\n" + "=" * 60)
        print("📋 TASK DETAILS")
        print("=" * 60)
        print(f"ID: {task.get('id')}")
        print(f"Title: {task.get('title')}")

        owner_sticker_config = config.get("ai_owner_sticker", {})
        sticker_id = owner_sticker_config.get("id")
        task_stickers = task.get("stickers", {})

        if sticker_id and sticker_id in task_stickers:
            owner_state_id = task_stickers[sticker_id]
            states_map = {
                v: k for k, v in owner_sticker_config.get("states", {}).items()
            }
            owner_name = states_map.get(owner_state_id, "Unknown")
            print(f"AI Owner: 👤 {owner_name}")

        print("\nDescription:")
        print(f"{task.get('description', 'No description.')}")

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

    if not validate_task_id(task_id):
        print(
            "❌ Error: Invalid task ID format. Task ID must be a valid UUID or alphanumeric string."
        )
        return

    print(f"💬 Adding comment to task: {task_id}...")

    comment_data = {"text": args.message}
    response = make_api_request(
        "POST", f"{BASE_URL}/chats/{task_id}/messages", json=comment_data
    )

    if response.status_code == 201:
        print("✅ Comment added successfully.")
    else:
        handle_api_error(response)


def move_task(args, config):
    """Moves a task to a different column."""
    task_id = args.task_id
    target_column_name = args.column

    if not validate_task_id(task_id):
        print(
            "❌ Error: Invalid task ID format. Task ID must be a valid UUID or alphanumeric string."
        )
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


def set_task_completion_status(args, config, completed: bool):
    """Sets the completion status of a task."""
    task_id = args.task_id
    if not validate_task_id(task_id):
        print("❌ Error: Invalid task ID format.")
        return

    action = "Completing" if completed else "Un-completing"
    print(f"🔄 {action} task: {task_id}...")

    update_data = {"completed": completed}
    response = make_api_request("PUT", f"{BASE_URL}/tasks/{task_id}", json=update_data)

    if response.status_code == 200:
        print("✅ Task status updated successfully.")
    else:
        handle_api_error(response)


def complete_task(args, config):
    """Marks a task as complete."""
    set_task_completion_status(args, config, True)


def uncomplete_task(args, config):
    """Marks a task as not complete."""
    set_task_completion_status(args, config, False)


def set_task_archived_status(args, config, archived: bool):
    """Sets the archived status of a task."""
    task_id = args.task_id
    if not validate_task_id(task_id):
        print("❌ Error: Invalid task ID format.")
        return

    action = "Archiving" if archived else "Un-archiving"
    print(f"🔄 {action} task: {task_id}...")

    update_data = {"archived": archived}
    response = make_api_request("PUT", f"{BASE_URL}/tasks/{task_id}", json=update_data)

    if response.status_code == 200:
        print("✅ Task status updated successfully.")
    else:
        handle_api_error(response)


def archive_task(args, config):
    """Marks a task as archived."""
    set_task_archived_status(args, config, True)


def unarchive_task(args, config):
    """Marks a task as not archived."""
    set_task_archived_status(args, config, False)


def list_agents(args, config):
    """Lists all available AI agents."""
    owner_sticker_config = config.get("ai_owner_sticker", {})
    agents = list(owner_sticker_config.get("states", {}).keys())

    if not agents:
        print("❌ No AI agents found in configuration.")
        return

    print(f"🤖 Available AI Agents ({len(agents)}):")
    print("=" * 50)

    categories = {
        "Language Specialists": [
            a
            for a in agents
            if any(
                lang in a
                for lang in [
                    "python",
                    "javascript",
                    "java",
                    "golang",
                    "rust",
                    "cpp",
                    "csharp",
                    "php",
                    "scala",
                    "elixir",
                ]
            )
        ],
        "Architecture & Backend": [
            a
            for a in agents
            if any(arch in a for arch in ["architect", "backend", "api", "graphql"])
        ],
        "Frontend & Mobile": [
            a
            for a in agents
            if any(fe in a for fe in ["frontend", "ui-ux", "mobile", "ios", "unity"])
        ],
        "Data & AI": [
            a
            for a in agents
            if any(data in a for data in ["data-", "ai-", "ml-", "mlops"])
        ],
        "Infrastructure": [
            a
            for a in agents
            if any(
                infra in a
                for infra in [
                    "devops",
                    "cloud",
                    "deployment",
                    "terraform",
                    "network",
                    "database",
                ]
            )
        ],
        "Quality & Security": [
            a
            for a in agents
            if any(
                qual in a
                for qual in [
                    "security",
                    "test",
                    "code-reviewer",
                    "performance",
                    "debugger",
                ]
            )
        ],
        "Documentation": [
            a
            for a in agents
            if any(
                doc in a for doc in ["docs", "api-documenter", "tutorial", "reference"]
            )
        ],
        "Business & Support": [
            a
            for a in agents
            if any(
                biz in a
                for biz in ["business", "sales", "customer", "content", "legal"]
            )
        ],
    }

    uncategorized = set(agents)
    for category, category_agents in categories.items():
        if category_agents:
            print(f"\n📁 {category}:")
            for agent in sorted(category_agents):
                print(f"  • {agent}")
                uncategorized.discard(agent)

    if uncategorized:
        print("\n📁 Other:")
        for agent in sorted(uncategorized):
            print(f"  • {agent}")
