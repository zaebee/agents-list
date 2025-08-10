# Plan: Implement "Mark as Completed" Feature

This document outlines the plan to add a dedicated command for marking tasks as complete in the AI-CRM.

## 1. Objective
To provide a simple and intuitive command for users to mark a task as complete, improving the overall user experience and workflow efficiency.

## 2. "Completed" Definition
For the purpose of this feature, "completed" is defined as moving a task to the **"Done"** column. This allows for a final review of completed work before it is moved to the "Archived" column.

## 3. Implementation Details

### 3.1. New CLI Command
- **Command:** `complete`
- **Syntax:** `python3 our-crm-ai/crm_enhanced.py complete <task_id>`
- **Functionality:** This command will act as a shortcut, using the existing `move` logic to move the specified task to the "Done" column.

### 3.2. Code Changes
- **File:** `our-crm-ai/crm_enhanced.py`
- **Actions:**
    1. Add a new subparser for the `complete` command.
    2. Create a `complete_task` handler function that:
        - Takes a `task_id` as an argument.
        - Retrieves the "Done" column ID from `config.json`.
        - Calls the YouGile API to update the task's `columnId`.

### 3.3. Documentation Updates
- **File:** `our-crm-ai/README.md`
- **Action:** Add a new section documenting the `complete` command and its usage.

## 4. Tracking
- This plan will be tracked by a dedicated task in the AI-CRM.
- Progress will be logged as comments on the task.
