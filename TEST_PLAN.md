# End-to-End Test Plan

This document outlines the end-to-end test plan for the AI-CRM application.

## 1. Objectives
- Verify that all critical user journeys are functioning correctly in a production-like environment.
- Ensure the application is stable, reliable, and free of major defects.
- Validate that the frontend and backend are correctly integrated.

## 2. Scope
This test plan covers the following key functionalities:
- User authentication and authorization.
- Task creation, viewing, updating, and moving.
- AI agent suggestion and assignment.
- Commenting on tasks.
- Listing all tasks.

## 3. Test Cases

### 3.1. User Authentication
- **TC-001:** Verify that a user can successfully log in with valid credentials.
- **TC-002:** Verify that a user cannot log in with invalid credentials.
- **TC-003:** Verify that a logged-in user can successfully log out.

### 3.2. Task Management
- **TC-004:** Verify that a user can create a new task with a title and description.
- **TC-005:** Verify that a user can view the details of a created task.
- **TC-006:** Verify that a user can update the owner of a task.
- **TC-007:** Verify that a user can move a task between columns ("To Do", "In Progress", "Done").
- **TC-008:** Verify that a user can add a comment to a task.

### 3.3. AI Functionality
- **TC-009:** Verify that when creating a task without an owner, the system suggests a relevant AI agent.
- **TC-010:** Verify that the PM Agent Gateway can be invoked for complex task analysis.

## 4. Test Environment
- **URL:** `https://crm.zae.life`
- **Browser:** Google Chrome (latest version)
- **API Endpoint:** `https://api.crm.zae.life`

## 5. Test Execution
- The tests will be executed manually based on the test cases outlined above.
- Any defects found will be reported and tracked in the YouGile CRM.
