import argparse
import re
import os
import subprocess
import sys

# Add project root to path to allow sibling imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from crm import CRMClient
# from rag.query_rag import query_rag # No longer used


def recognize_intent(command):
    """Recognizes the user's intent from the command."""
    command_lower = command.lower()

    # Intent: query_rag (prioritized)
    if command_lower.startswith(("what is", "what's", "tell me about")):
        return "query_rag", {"query": command}

    # Intent: list_tasks
    if any(
        keyword in command_lower for keyword in ["list", "show all", "board", "tasks"]
    ):
        return "list_tasks", {}

    # Intent: view_task
    view_keywords = ["view task", "show task", "details for task", "show me task"]
    if any(keyword in command_lower for keyword in view_keywords):
        # Try to find a UUID in the command
        match = re.search(
            r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
            command_lower,
        )
        if match:
            return "view_task", {"task_id": match.group(1)}

    return "unknown", {}


def execute_action(intent, params):
    """Executes the action corresponding to the intent."""

    # This function is now quieter, it will not print status messages.
    # The caller (either main() or the API) is responsible for printing.

    if intent == "list_tasks":
        try:
            client = CRMClient()
            tasks = client.list_tasks()
            if not tasks:
                return "No tasks found on the board."

            response = "--- Tasks on Board ---\n"
            for task in tasks:
                response += f"- ID: {task['id']}\n"
                response += f"  Title: {task['title']}\n"
                response += f"  Status: {task['columnName']}\n"
            return response
        except Exception as e:
            return f"Error listing tasks: {e}"

    elif intent == "view_task":
        try:
            client = CRMClient()
            task_id = params.get("task_id")
            if not task_id:
                return "Error: Task ID not provided for 'view_task' intent."

            task = client.view_task(task_id)
            if not task:
                return f"Error: Task with ID '{task_id}' not found."

            response = f"--- Task Details for {task_id} ---\n"
            response += f"Title: {task.get('title')}\n"
            response += f"Description: {task.get('description', 'No description.')}\n"
            response += "\n--- Comments ---\n"
            if not task.get("comments"):
                response += "No comments found."
            else:
                for msg in reversed(task["comments"]):
                    response += f"- {msg.get('text')}\n"
            return response
        except Exception as e:
            return f"Error viewing task: {e}"

    elif intent == "query_rag":
        try:
            query = params.get("query")
            if not query:
                return "Error: Query not provided for 'query_rag' intent."

            rag_script_path = os.path.join(
                os.path.dirname(__file__), "../rag/rag_system.py"
            )
            index_path = os.path.join(
                os.path.dirname(__file__), "../rag/index.faiss"
            )

            # Check if the index exists, if not, build it.
            if not os.path.exists(index_path):
                print("RAG index not found. Building it now...")
                prepare_result = subprocess.run(
                    ["python3", rag_script_path, "prepare"],
                    capture_output=True,
                    text=True,
                )
                if prepare_result.returncode != 0:
                    return f"Error building RAG index:\n{prepare_result.stderr}"
                print("RAG index built successfully.")

            # Now, query the RAG system
            result = subprocess.run(
                ["python3", rag_script_path, "query", query],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except Exception as e:
            return f"An unexpected error occurred during RAG query: {e}"

    else:  # unknown intent
        return "Sorry, I didn't understand that command. Please try again."


def handle_command(command_string):
    """
    Handles a natural language command and returns the result.
    This is the main entry point for using the PM agent as a library.
    """
    print(f"PM Agent received command: '{command_string}'")

    # 1. Recognize intent
    intent, params = recognize_intent(command_string)

    # 2. Execute action
    print(f"Executing action for intent '{intent}' with params {params}")
    result = execute_action(intent, params)

    return result


def main():
    """Main function for the PM Agent CLI."""
    parser = argparse.ArgumentParser(
        description="Project Manager Agent for our-crm-ai."
    )
    parser.add_argument(
        "command",
        type=str,
        nargs="+",
        help="The natural language command for the PM agent.",
    )

    args = parser.parse_args()
    full_command = " ".join(args.command)

    result = handle_command(full_command)

    # 3. Print result
    print("\n--- PM Agent Response ---")
    print(result)


if __name__ == "__main__":
    main()
