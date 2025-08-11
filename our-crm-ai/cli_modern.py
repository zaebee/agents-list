#!/usr/bin/env python3
"""
Modern AI-CRM CLI Interface
Clean, modern CLI using the refactored CRM service architecture.
"""

import asyncio
import logging
import os
import sys
from typing import Optional, Any
import argparse

# Rich for better CLI output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.text import Text

    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None

# Project imports
from models import (
    TaskCreateRequest,
    TaskStatus,
    TaskPriority,
    PMAnalysisRequest,
)
from exceptions import CRMError, TaskNotFoundError
from crm_service import create_crm_service


class ModernCLI:
    """Modern CLI interface with rich output and async support."""

    def __init__(self):
        self.console = Console() if HAS_RICH else None
        self.service: Optional[Any] = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Set up CLI logging."""
        logger = logging.getLogger("ai_crm_cli")
        logger.setLevel(logging.INFO)

        # Only add handler if none exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def print_success(self, message: str):
        """Print success message."""
        if self.console:
            self.console.print(f"✅ {message}", style="bold green")
        else:
            print(f"✅ {message}")

    def print_error(self, message: str):
        """Print error message."""
        if self.console:
            self.console.print(f"❌ {message}", style="bold red")
        else:
            print(f"❌ {message}")

    def print_warning(self, message: str):
        """Print warning message."""
        if self.console:
            self.console.print(f"⚠️  {message}", style="bold yellow")
        else:
            print(f"⚠️  {message}")

    def print_info(self, message: str):
        """Print info message."""
        if self.console:
            self.console.print(f"ℹ️  {message}", style="bold blue")
        else:
            print(f"ℹ️  {message}")

    async def initialize(self, api_key: str, config_path: str = "config.json"):
        """Initialize the CRM service."""
        try:
            if self.console:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task(
                        "Initializing AI-CRM service...", total=None
                    )
                    self.service = await create_crm_service(api_key, config_path)
            else:
                print("Initializing AI-CRM service...")
                self.service = await create_crm_service(api_key, config_path)

            self.print_success("AI-CRM service initialized successfully")

        except Exception as e:
            self.print_error(f"Failed to initialize service: {str(e)}")
            raise

    async def create_task_interactive(self, args):
        """Interactive task creation with PM analysis."""
        try:
            # Get task details
            title = args.title or (
                Prompt.ask("Task title") if HAS_RICH else input("Task title: ")
            )
            description = args.description or (
                Prompt.ask("Task description (optional)", default="")
                if HAS_RICH
                else input("Task description (optional): ")
            )

            # Priority selection
            if not args.priority:
                if HAS_RICH:
                    priority_choices = [p.value for p in TaskPriority]
                    priority = Prompt.ask(
                        "Priority", choices=priority_choices, default="medium"
                    )
                else:
                    priority = (
                        input("Priority (low/medium/high/urgent) [medium]: ")
                        or "medium"
                    )
            else:
                priority = args.priority

            # Create request
            task_request = TaskCreateRequest(
                title=title,
                description=description,
                priority=TaskPriority(priority),
                assigned_agent=args.owner,
                use_pm_analysis=not args.no_pm_analysis,
                auto_assign=not args.no_auto_assign,
            )

            # Show analysis if enabled
            if not args.no_pm_analysis and not args.quiet:
                self.print_info("🎯 Analyzing task with PM Agent Gateway...")

                if self.console:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=self.console,
                    ) as progress:
                        task = progress.add_task(
                            "Analyzing task complexity...", total=None
                        )

                        # Get PM analysis
                        pm_request = PMAnalysisRequest(
                            title=title, description=description, auto_assign=True
                        )

                        try:
                            pm_result = await self.service.pm_analyze_task(pm_request)
                            progress.update(task, completed=True)

                            # Display analysis
                            self._display_pm_analysis(pm_result)

                        except Exception as e:
                            self.print_warning(f"PM analysis failed: {e}")

            # Create task
            if self.console:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task("Creating task...", total=None)
                    response = await self.service.create_task(task_request)
            else:
                print("Creating task...")
                response = await self.service.create_task(task_request)

            if response.success:
                self.print_success(f"Task created: {response.task.title}")
                self._display_task_summary(response.task)

                # Display warnings if any
                for warning in response.warnings:
                    self.print_warning(warning)
            else:
                self.print_error(f"Task creation failed: {response.message}")

        except Exception as e:
            self.print_error(f"Failed to create task: {str(e)}")

    def _display_pm_analysis(self, analysis):
        """Display PM analysis results."""
        if self.console:
            # Create analysis table
            table = Table(
                title="🎯 PM Agent Analysis",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Attribute", style="cyan", width=20)
            table.add_column("Value", style="green")

            table.add_row("Task Type", analysis.task_type.title())
            table.add_row("Complexity", analysis.complexity.value.title())
            table.add_row("Priority", analysis.priority.value.title())
            table.add_row("Estimated Hours", f"{analysis.estimated_hours} hours")
            table.add_row("Recommended Agent", analysis.recommended_agent or "None")

            if analysis.required_agents:
                table.add_row("Required Agents", ", ".join(analysis.required_agents))

            self.console.print(table)

            # Risk factors
            if analysis.risk_factors:
                risk_panel = Panel(
                    "\n".join(f"• {risk}" for risk in analysis.risk_factors),
                    title="⚠️  Risk Factors",
                    border_style="yellow",
                )
                self.console.print(risk_panel)

            # Success criteria
            if analysis.success_criteria:
                success_panel = Panel(
                    "\n".join(
                        f"• {criteria}" for criteria in analysis.success_criteria
                    ),
                    title="✅ Success Criteria",
                    border_style="green",
                )
                self.console.print(success_panel)
        else:
            print("\n🎯 PM Agent Analysis:")
            print(f"  Task Type: {analysis.task_type.title()}")
            print(f"  Complexity: {analysis.complexity.value.title()}")
            print(f"  Priority: {analysis.priority.value.title()}")
            print(f"  Estimated: {analysis.estimated_hours} hours")
            print(f"  Recommended: {analysis.recommended_agent or 'None'}")

            if analysis.risk_factors:
                print(f"  Risks: {', '.join(analysis.risk_factors)}")

    def _display_task_summary(self, task):
        """Display task summary."""
        if self.console:
            # Create task summary
            summary_text = f"[bold]ID:[/bold] {task.id}\n"
            summary_text += f"[bold]Status:[/bold] {task.status.value}\n"
            summary_text += f"[bold]Priority:[/bold] {task.priority.value}\n"

            if task.assigned_agent:
                summary_text += f"[bold]Agent:[/bold] {task.assigned_agent}\n"

            if task.created_at:
                summary_text += f"[bold]Created:[/bold] {task.created_at.strftime('%Y-%m-%d %H:%M')}\n"

            panel = Panel(summary_text, title="📋 Task Summary", border_style="blue")
            self.console.print(panel)
        else:
            print("\n📋 Task Summary:")
            print(f"  ID: {task.id}")
            print(f"  Status: {task.status.value}")
            print(f"  Priority: {task.priority.value}")
            if task.assigned_agent:
                print(f"  Agent: {task.assigned_agent}")

    async def list_tasks(self, args):
        """List tasks with filtering."""
        try:
            # Parse filters
            status = TaskStatus(args.status) if args.status else None

            if self.console:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task("Fetching tasks...", total=None)
                    tasks = await self.service.list_tasks(
                        status=status,
                        assigned_agent=args.agent,
                        limit=args.limit,
                        offset=args.offset,
                    )
            else:
                print("Fetching tasks...")
                tasks = await self.service.list_tasks(
                    status=status,
                    assigned_agent=args.agent,
                    limit=args.limit,
                    offset=args.offset,
                )

            if not tasks:
                self.print_info("No tasks found matching criteria")
                return

            # Display tasks
            if self.console and not args.simple:
                self._display_tasks_table(tasks)
            else:
                self._display_tasks_simple(tasks)

        except Exception as e:
            self.print_error(f"Failed to list tasks: {str(e)}")

    def _display_tasks_table(self, tasks):
        """Display tasks in rich table format."""
        table = Table(
            title=f"📋 Tasks ({len(tasks)})",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("ID", style="cyan", width=12)
        table.add_column("Title", style="white", width=40)
        table.add_column("Status", style="green", width=12)
        table.add_column("Priority", style="yellow", width=10)
        table.add_column("Agent", style="blue", width=20)
        table.add_column("Created", style="dim", width=16)

        for task in tasks:
            # Status styling
            status_style = {
                TaskStatus.TODO: "yellow",
                TaskStatus.IN_PROGRESS: "blue",
                TaskStatus.DONE: "green",
            }.get(task.status, "white")

            # Priority styling
            priority_style = {
                TaskPriority.LOW: "dim",
                TaskPriority.MEDIUM: "white",
                TaskPriority.HIGH: "yellow",
                TaskPriority.URGENT: "red",
            }.get(task.priority, "white")

            created_str = (
                task.created_at.strftime("%Y-%m-%d %H:%M")
                if task.created_at
                else "Unknown"
            )

            table.add_row(
                task.id[:12] + "..." if len(task.id) > 12 else task.id,
                task.title[:37] + "..." if len(task.title) > 40 else task.title,
                f"[{status_style}]{task.status.value}[/{status_style}]",
                f"[{priority_style}]{task.priority.value}[/{priority_style}]",
                task.assigned_agent or "Unassigned",
                created_str,
            )

        self.console.print(table)

    def _display_tasks_simple(self, tasks):
        """Display tasks in simple format."""
        print(f"\n📋 Tasks ({len(tasks)}):")
        print("=" * 80)

        for task in tasks:
            print(f"\n🎫 {task.id}")
            print(f"   Title: {task.title}")
            print(f"   Status: {task.status.value}")
            print(f"   Priority: {task.priority.value}")
            if task.assigned_agent:
                print(f"   Agent: {task.assigned_agent}")
            if task.created_at:
                print(f"   Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}")

    async def view_task(self, args):
        """View detailed task information."""
        try:
            task = await self.service.get_task(args.task_id)

            if self.console:
                self._display_task_detail(task)
            else:
                self._display_task_detail_simple(task)

            # Get comments if requested
            if args.include_comments:
                comments = await self.service.get_task_comments(args.task_id)
                self._display_comments(comments)

        except TaskNotFoundError:
            self.print_error(f"Task '{args.task_id}' not found")
        except Exception as e:
            self.print_error(f"Failed to view task: {str(e)}")

    def _display_task_detail(self, task):
        """Display detailed task information with rich formatting."""
        # Main task info
        task_info = f"[bold]Title:[/bold] {task.title}\n"
        task_info += f"[bold]ID:[/bold] {task.id}\n"
        task_info += f"[bold]Status:[/bold] {task.status.value}\n"
        task_info += f"[bold]Priority:[/bold] {task.priority.value}\n"

        if task.assigned_agent:
            task_info += f"[bold]Assigned Agent:[/bold] {task.assigned_agent}\n"

        if task.created_at:
            task_info += f"[bold]Created:[/bold] {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if task.updated_at:
            task_info += f"[bold]Updated:[/bold] {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        panel = Panel(task_info, title="📋 Task Details", border_style="blue")
        self.console.print(panel)

        # Description
        if task.description:
            desc_panel = Panel(
                task.description, title="📝 Description", border_style="green"
            )
            self.console.print(desc_panel)

        # Metadata
        if task.metadata and (
            task.metadata.risk_factors or task.metadata.success_criteria
        ):
            metadata_text = ""

            if task.metadata.risk_factors:
                metadata_text += "[bold red]Risk Factors:[/bold red]\n"
                for risk in task.metadata.risk_factors:
                    metadata_text += f"  • {risk}\n"
                metadata_text += "\n"

            if task.metadata.success_criteria:
                metadata_text += "[bold green]Success Criteria:[/bold green]\n"
                for criteria in task.metadata.success_criteria:
                    metadata_text += f"  • {criteria}\n"

            if metadata_text:
                meta_panel = Panel(
                    metadata_text.strip(), title="📊 Task Metadata", border_style="cyan"
                )
                self.console.print(meta_panel)

    def _display_task_detail_simple(self, task):
        """Display task details in simple format."""
        print("\n📋 Task Details")
        print("=" * 50)
        print(f"ID: {task.id}")
        print(f"Title: {task.title}")
        print(f"Status: {task.status.value}")
        print(f"Priority: {task.priority.value}")

        if task.assigned_agent:
            print(f"Agent: {task.assigned_agent}")

        if task.created_at:
            print(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if task.description:
            print("\n📝 Description:")
            print(task.description)

    def _display_comments(self, comments):
        """Display task comments."""
        if not comments:
            self.print_info("No comments found")
            return

        if self.console:
            comments_text = ""
            for comment in comments:
                timestamp = comment.get("createdAt", "Unknown")
                text = comment.get("text", "")
                comments_text += f"[dim]{timestamp}[/dim]\n{text}\n\n"

            if comments_text:
                panel = Panel(
                    comments_text.strip(),
                    title=f"💬 Comments ({len(comments)})",
                    border_style="yellow",
                )
                self.console.print(panel)
        else:
            print(f"\n💬 Comments ({len(comments)}):")
            print("-" * 40)
            for comment in comments:
                timestamp = comment.get("createdAt", "Unknown")
                text = comment.get("text", "")
                print(f"{timestamp}: {text}\n")

    async def suggest_agents(self, args):
        """Get agent suggestions for a task description."""
        try:
            task_description = args.description

            response = await self.service.suggest_agents(
                task_description, max_suggestions=args.limit
            )

            if not response.suggestions:
                self.print_info("No agent suggestions found")
                return

            if self.console:
                # Create suggestions table
                table = Table(
                    title="🤖 Agent Suggestions",
                    show_header=True,
                    header_style="bold magenta",
                )
                table.add_column("Rank", style="cyan", width=6)
                table.add_column("Agent", style="green", width=25)
                table.add_column("Confidence", style="yellow", width=12)
                table.add_column("Workload", style="blue", width=10)
                table.add_column("Status", style="white", width=12)
                table.add_column("Reasoning", style="dim", width=40)

                for i, suggestion in enumerate(response.suggestions, 1):
                    workload_color = (
                        "green"
                        if suggestion.workload_factor < 1.2
                        else "yellow"
                        if suggestion.workload_factor < 1.5
                        else "red"
                    )

                    table.add_row(
                        str(i),
                        suggestion.agent_name,
                        f"{suggestion.confidence:.1f}%",
                        f"[{workload_color}]{suggestion.workload_factor:.1f}x[/{workload_color}]",
                        suggestion.availability_status,
                        suggestion.reasoning[:37] + "..."
                        if len(suggestion.reasoning) > 40
                        else suggestion.reasoning,
                    )

                self.console.print(table)

                # Show recommendation
                rec_panel = Panel(
                    response.recommendation,
                    title="💡 Recommendation",
                    border_style="green",
                )
                self.console.print(rec_panel)
            else:
                print(f"\n🤖 Agent Suggestions for: '{task_description}'")
                print("=" * 60)

                for i, suggestion in enumerate(response.suggestions, 1):
                    print(
                        f"{i}. {suggestion.agent_name} ({suggestion.confidence:.1f}% confidence)"
                    )
                    print(f"   Workload: {suggestion.workload_factor:.1f}x")
                    print(f"   Status: {suggestion.availability_status}")
                    print(f"   Reasoning: {suggestion.reasoning}")
                    print()

                print(f"💡 {response.recommendation}")

        except Exception as e:
            self.print_error(f"Failed to get agent suggestions: {str(e)}")

    async def show_system_stats(self, args):
        """Show system statistics."""
        try:
            stats = await self.service.get_system_stats()

            if self.console:
                # Overview panel
                overview_text = f"[bold]Total Tasks:[/bold] {stats.total_tasks}\n"
                overview_text += (
                    f"[bold]Success Rate:[/bold] {stats.success_rate:.1%}\n"
                )
                overview_text += (
                    f"[bold]System Health:[/bold] {stats.system_health.title()}\n"
                )

                if stats.average_completion_time_hours:
                    overview_text += f"[bold]Avg Completion:[/bold] {stats.average_completion_time_hours:.1f} hours\n"

                overview_panel = Panel(
                    overview_text, title="📊 System Overview", border_style="blue"
                )
                self.console.print(overview_panel)

                # Status distribution
                if stats.tasks_by_status:
                    status_table = Table(title="Tasks by Status", show_header=True)
                    status_table.add_column("Status", style="cyan")
                    status_table.add_column("Count", style="green")
                    status_table.add_column("Percentage", style="yellow")

                    for status, count in stats.tasks_by_status.items():
                        percentage = (
                            (count / stats.total_tasks) * 100
                            if stats.total_tasks > 0
                            else 0
                        )
                        status_table.add_row(
                            status.value if hasattr(status, "value") else str(status),
                            str(count),
                            f"{percentage:.1f}%",
                        )

                    self.console.print(status_table)

                # Top agents
                if stats.most_active_agents:
                    agents_text = "\n".join(
                        f"• {agent}" for agent in stats.most_active_agents[:5]
                    )
                    agents_panel = Panel(
                        agents_text, title="🏆 Most Active Agents", border_style="green"
                    )
                    self.console.print(agents_panel)
            else:
                print("\n📊 System Statistics")
                print("=" * 40)
                print(f"Total Tasks: {stats.total_tasks}")
                print(f"Success Rate: {stats.success_rate:.1%}")
                print(f"System Health: {stats.system_health.title()}")

                if stats.average_completion_time_hours:
                    print(
                        f"Average Completion: {stats.average_completion_time_hours:.1f} hours"
                    )

                if stats.tasks_by_status:
                    print("\nTasks by Status:")
                    for status, count in stats.tasks_by_status.items():
                        percentage = (
                            (count / stats.total_tasks) * 100
                            if stats.total_tasks > 0
                            else 0
                        )
                        status_name = (
                            status.value if hasattr(status, "value") else str(status)
                        )
                        print(f"  {status_name}: {count} ({percentage:.1f}%)")

                if stats.most_active_agents:
                    print("\nMost Active Agents:")
                    for agent in stats.most_active_agents[:5]:
                        print(f"  • {agent}")

        except Exception as e:
            self.print_error(f"Failed to get system statistics: {str(e)}")

    async def cleanup(self):
        """Clean up resources."""
        if self.service:
            try:
                await self.service.close()
            except Exception as e:
                self.logger.warning(f"Error during cleanup: {e}")


async def main():
    """Main CLI entry point."""
    # Check for API key
    api_key = os.getenv("YOUGILE_API_KEY")
    if not api_key:
        print("❌ Error: YOUGILE_API_KEY environment variable not set.")
        sys.exit(1)

    # Initialize CLI
    cli = ModernCLI()

    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(
            description="🤖 Modern AI-CRM CLI - Intelligent task management with AI agents",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s create --title "Fix login bug" --description "Users can't log in"
  %(prog)s create --title "Add dashboard" --owner frontend-developer --priority high
  %(prog)s list --status "In Progress" --agent backend-architect
  %(prog)s suggest --description "optimize database performance"
  %(prog)s stats
            """,
        )

        parser.add_argument(
            "--config", default="config.json", help="Configuration file path"
        )
        parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")

        subparsers = parser.add_subparsers(
            dest="command", required=True, help="Available commands"
        )

        # Create command
        create_parser = subparsers.add_parser("create", help="Create a new task")
        create_parser.add_argument("--title", help="Task title")
        create_parser.add_argument("--description", help="Task description")
        create_parser.add_argument(
            "--priority", choices=[p.value for p in TaskPriority], help="Task priority"
        )
        create_parser.add_argument("--owner", help="Assign to specific agent")
        create_parser.add_argument(
            "--no-pm-analysis", action="store_true", help="Skip PM Gateway analysis"
        )
        create_parser.add_argument(
            "--no-auto-assign",
            action="store_true",
            help="Skip automatic agent assignment",
        )
        create_parser.set_defaults(func=cli.create_task_interactive)

        # List command
        list_parser = subparsers.add_parser("list", help="List tasks")
        list_parser.add_argument(
            "--status", choices=[s.value for s in TaskStatus], help="Filter by status"
        )
        list_parser.add_argument("--agent", help="Filter by assigned agent")
        list_parser.add_argument(
            "--limit", type=int, default=20, help="Maximum tasks to show"
        )
        list_parser.add_argument(
            "--offset", type=int, default=0, help="Skip first N tasks"
        )
        list_parser.add_argument(
            "--simple", action="store_true", help="Simple output format"
        )
        list_parser.set_defaults(func=cli.list_tasks)

        # View command
        view_parser = subparsers.add_parser("view", help="View task details")
        view_parser.add_argument("task_id", help="Task ID to view")
        view_parser.add_argument(
            "--include-comments", action="store_true", help="Include task comments"
        )
        view_parser.set_defaults(func=cli.view_task)

        # Suggest command
        suggest_parser = subparsers.add_parser("suggest", help="Get agent suggestions")
        suggest_parser.add_argument(
            "--description", required=True, help="Task description to analyze"
        )
        suggest_parser.add_argument(
            "--limit", type=int, default=5, help="Maximum suggestions"
        )
        suggest_parser.set_defaults(func=cli.suggest_agents)

        # Stats command
        stats_parser = subparsers.add_parser("stats", help="Show system statistics")
        stats_parser.set_defaults(func=cli.show_system_stats)

        # Health command
        health_parser = subparsers.add_parser("health", help="Check system health")
        health_parser.set_defaults(
            func=lambda args: cli.service.health_check()
            if cli.service
            else print("Service not initialized")
        )

        # Parse arguments
        args = parser.parse_args()

        # Initialize service
        await cli.initialize(api_key, args.config)

        # Execute command
        await args.func(args)

    except KeyboardInterrupt:
        cli.print_info("Operation cancelled by user")
    except CRMError as e:
        cli.print_error(f"CRM Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        cli.print_error(f"Unexpected error: {str(e)}")
        if not args.quiet:
            import traceback

            traceback.print_exc()
        sys.exit(1)
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    # Handle Windows event loop policy
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(main())
