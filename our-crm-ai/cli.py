# our-crm-ai/cli.py
import argparse
import os
import json
from commands import (
    create_task,
    update_task,
    list_tasks,
    view_task,
    comment_on_task,
    move_task,
    complete_task,
    uncomplete_task,
    archive_task,
    unarchive_task,
    list_agents,
)
from agent_selector import suggest_agents
from pm_agent_gateway import PMAgentGateway


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


def print_agent_suggestions(description):
    """Print agent suggestions for a given description."""
    suggestions = suggest_agents(description, max_suggestions=5)

    if suggestions:
        print(f"🤖 AI Agent Suggestions for: '{description}'")
        print("=" * 60)

        for i, suggestion in enumerate(suggestions, 1):
            confidence = suggestion["confidence"]
            agent = suggestion["agent"]
            keywords = ", ".join(suggestion["matched_keywords"])

            print(f"{i}. {agent} ({confidence:.1f}% confidence)")
            print(f"   Keywords: {keywords}")
            print()

        print(f"💡 Top Recommendation: {suggestions[0]['agent']}")
    else:
        print("❌ No specific agent suggestions found.")
        print("💡 Consider using 'search-specialist' for general research tasks.")


def pm_analyze_task(args, config):
    """Use PM Agent Gateway to analyze and provide comprehensive task recommendations."""
    try:
        pm_gateway = PMAgentGateway()
        result = pm_gateway.create_managed_task(args.title, args.description or "")

        print("\n🎯 PM Agent Analysis Complete!")
        print("=" * 60)

        if result["type"] == "direct_assignment":
            print(f"📋 Task: {result['task']['title']}")
            print(f"🎯 Recommended Agent: {result['assigned_agent']}")
            print(f"📊 Priority: {result['priority']}")
            print(f"⏰ Estimated: {result['analysis']['estimated_hours']} hours")
            print(f"🔧 Complexity: {result['analysis']['complexity']}")

            if result["analysis"]["risk_factors"]:
                print("⚠️  Risk Factors:")
                for risk in result["analysis"]["risk_factors"]:
                    print(f"   • {risk}")

            print("✅ Success Criteria:")
            for criteria in result["analysis"]["success_criteria"]:
                print(f"   • {criteria}")

        elif result["type"] == "complex_task":
            print(f"📋 Complex Task: {result['original_task']['title']}")
            print(f"📊 Priority: {result['priority']}")
            print(f"⏰ Total Estimated: {result['analysis']['estimated_hours']} hours")
            print(f"🔧 Complexity: {result['analysis']['complexity']}")

            print(f"\n🔄 Recommended Subtasks ({len(result['subtasks'])}):")
            for i, subtask in enumerate(result["subtasks"], 1):
                print(f"   {i}. {subtask['title']}")
                print(f"      → Agent: {subtask['agent']}")
                print(f"      → Time: {subtask['estimated_hours']} hours")
                if subtask.get("depends_on"):
                    print(f"      → Depends on: {subtask['depends_on']}")
                print()

        print(f"💡 Recommendation: {result['recommendation']}")

    except Exception as e:
        print(f"❌ PM Analysis failed: {e}")
        print("💡 Falling back to basic agent suggestions...")
        print_agent_suggestions(f"{args.title} {args.description or ''}")


def main():
    """Enhanced main function with better CLI."""
    API_KEY = os.environ.get("YOUGILE_API_KEY")
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
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create", help="Create a new task with AI agent suggestions."
    )
    create_parser.add_argument("--title", required=True, help="The title of the task.")
    create_parser.add_argument(
        "--description", default="", help="The description of the task."
    )
    create_parser.add_argument("--owner", help="The AI agent owner for the task.")
    create_parser.add_argument(
        "--no-ai-suggest", action="store_true", help="Skip AI agent suggestions."
    )
    create_parser.set_defaults(func=create_task)

    update_parser = subparsers.add_parser("update", help="Update an existing task.")
    update_parser.add_argument("task_id", help="The ID of the task to update.")
    update_parser.add_argument("--owner", help="The new AI agent owner for the task.")
    update_parser.set_defaults(func=update_task)

    list_parser = subparsers.add_parser(
        "list", help="List all tasks grouped by status."
    )
    list_parser.set_defaults(func=list_tasks)

    view_parser = subparsers.add_parser(
        "view", help="View a specific task with details."
    )
    view_parser.add_argument("task_id", help="The ID of the task to view.")
    view_parser.set_defaults(func=view_task)

    comment_parser = subparsers.add_parser("comment", help="Add a comment to a task.")
    comment_parser.add_argument("task_id", help="The ID of the task to comment on.")
    comment_parser.add_argument("--message", required=True, help="The comment message.")
    comment_parser.set_defaults(func=comment_on_task)

    move_parser = subparsers.add_parser(
        "move", help="Move a task to a different column."
    )
    move_parser.add_argument("task_id", help="The ID of the task to move.")
    move_parser.add_argument(
        "--column", required=True, help="The name of the target column."
    )
    move_parser.set_defaults(func=move_task)

    complete_parser = subparsers.add_parser("complete", help="Mark a task as complete.")
    complete_parser.add_argument("task_id", help="The ID of the task to complete.")
    complete_parser.set_defaults(func=complete_task)

    uncomplete_parser = subparsers.add_parser(
        "uncomplete", help="Mark a task as not complete."
    )
    uncomplete_parser.add_argument("task_id", help="The ID of the task to un-complete.")
    uncomplete_parser.set_defaults(func=uncomplete_task)

    archive_parser = subparsers.add_parser(
        "archive", help="Archive a task by marking it as complete."
    )
    archive_parser.add_argument("task_id", help="The ID of the task to archive.")
    archive_parser.set_defaults(func=archive_task)

    unarchive_parser = subparsers.add_parser("unarchive", help="Unarchive a task.")
    unarchive_parser.add_argument("task_id", help="The ID of the task to unarchive.")
    unarchive_parser.set_defaults(func=unarchive_task)

    agents_parser = subparsers.add_parser(
        "agents", help="List all available AI agents."
    )
    agents_parser.set_defaults(func=list_agents)

    suggest_parser = subparsers.add_parser(
        "suggest", help="Suggest AI agents for a task description."
    )
    suggest_parser.add_argument("description", help="Task description to analyze.")
    suggest_parser.set_defaults(
        func=lambda args, config: print_agent_suggestions(args.description)
    )

    pm_parser = subparsers.add_parser(
        "pm",
        help="PM Agent Gateway - comprehensive task analysis and workflow planning.",
    )
    pm_parser.add_argument("--title", required=True, help="Task title to analyze.")
    pm_parser.add_argument(
        "--description", help="Task description for detailed analysis."
    )
    pm_parser.set_defaults(func=pm_analyze_task)

    args = parser.parse_args()
    args.func(args, config)


if __name__ == "__main__":
    main()
