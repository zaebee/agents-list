#!/usr/bin/env python3
"""
Revises the statuses of tasks in the AI-CRM.
"""

import asyncio
from datetime import datetime, timedelta
import os

from models import TaskStatus
from repositories import (
    create_configuration_repository,
    create_task_repository,
)


async def main():
    """
    Main function to revise task statuses.
    """
    # Load configuration
    config_repo = await create_configuration_repository(
        "our-crm-ai/config_enhanced.json"
    )
    config = await config_repo.get_configuration()

    # Get API key from environment
    api_key = os.getenv("YOUGILE_API_KEY")
    if not api_key:
        print("Error: YOUGILE_API_KEY environment variable not set.")
        return

    # Create task repository
    task_repo = await create_task_repository(api_key, config)

    # Get all tasks
    print("Fetching all tasks...")
    all_tasks = await task_repo.list_tasks()
    print(f"Found {len(all_tasks)} tasks.")

    # Get current time
    now = datetime.utcnow()

    # Revise tasks
    for task in all_tasks:
        # Check for stale "In Progress" tasks
        if task.status == TaskStatus.IN_PROGRESS and task.updated_at:
            if now - task.updated_at > timedelta(days=7):
                print(f"Task '{task.title}' is stale. Adding a comment.")
                await task_repo.add_comment(
                    task.id,
                    "This task has been in progress for over a week. Please provide an update.",
                )

        # Check for old "To Do" tasks
        if task.status == TaskStatus.TODO and task.created_at:
            if now - task.created_at > timedelta(days=30):
                print(f"Task '{task.title}' is over 30 days old. Archiving.")
                await task_repo.move_task(task.id, TaskStatus.ARCHIVED)

        # Check for "done" tasks not in the "Done" column
        if (
            "done" in task.title.lower() or "completed" in task.title.lower()
        ) and task.status != TaskStatus.DONE:
            print(f"Task '{task.title}' seems to be done. Moving to 'Done' column.")
            await task_repo.move_task(task.id, TaskStatus.DONE)

    print("Task revision complete.")


if __name__ == "__main__":
    asyncio.run(main())
