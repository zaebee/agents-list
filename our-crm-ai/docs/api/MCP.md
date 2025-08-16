# Model Context Protocol (MCP)

## 1. Introduction

The Model Context Protocol (MCP) is a standardized set of rules and data structures designed to facilitate clear, efficient, and context-aware communication between specialized AI agents working within the `our-crm-ai` project. Its primary purpose is to ensure that agents can seamlessly request actions, share task-related information, and report results without ambiguity.

By adhering to this protocol, we can build a robust system where each AI agent, regardless of its specific role (e.g., `frontend-developer`, `api-documenter`), can understand and act upon information provided by its peers.

## 2. Core Principles

- **Clarity and Explicitness:** All communication should be unambiguous. The intent of a message and the data it carries must be explicitly defined.
- **Statelessness:** Whenever possible, requests between agents should be stateless. Each message should contain all the necessary context for the receiving agent to perform its task.
- **JSON as the Standard:** All data structures within the MCP will be defined as JSON schemas for universal compatibility and ease of use.

## 3. Communication Objects

The protocol is built around three core communication objects:

1.  **`TaskContext`**: Represents the complete state and details of a specific task from the CRM.
2.  **`AgentAction`**: Used by one agent to request a specific action from another.
3.  **`AgentResponse`**: Used by an agent to send back the result of a requested action.

---

### 3.1. `TaskContext` Schema

This object encapsulates all relevant information about a task. It is used to provide a complete picture to an agent that needs to work on the task.

**JSON Schema:**
```json
{
  "type": "object",
  "properties": {
    "taskId": { "type": "string", "description": "The unique identifier of the task in the CRM." },
    "title": { "type": "string", "description": "The title of the task." },
    "description": { "type": "string", "description": "The detailed description of the task." },
    "owner": { "type": "string", "description": "The role of the AI agent currently assigned to the task (e.g., 'ai-engineer')." },
    "status": { "type": "string", "description": "The current status of the task (e.g., 'To Do', 'In Progress', 'Done')." },
    "comments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "author": { "type": "string" },
          "text": { "type": "string" }
        },
        "required": ["author", "text"]
      }
    },
    "relatedFiles": {
      "type": "array",
      "items": { "type": "string" },
      "description": "A list of file paths relevant to the task."
    }
  },
  "required": ["taskId", "title", "description", "owner", "status"]
}
```

**Example:**
```json
{
  "taskId": "9e258593-8552-4502-9899-979c4d9c1558",
  "title": "Design MCP for Agent Communication",
  "description": "Define a clear 'Model Context Protocol' (MCP) that other AI agents can use to interact with the CRM.",
  "owner": "ai-engineer",
  "status": "In Progress",
  "comments": [],
  "relatedFiles": ["our-crm-ai/crm.py", "our-crm-ai/config.json"]
}
```

---

### 3.2. `AgentAction` Schema

This object is used when one agent needs to delegate a task or request a specific operation from another agent.

**JSON Schema:**
```json
{
  "type": "object",
  "properties": {
    "actionName": { "type": "string", "description": "The name of the action to be performed (e.g., 'implement_feature', 'review_code', 'write_documentation')." },
    "targetAgentRole": { "type": "string", "description": "The role of the agent that should perform the action." },
    "parameters": { "type": "object", "description": "A flexible object containing the parameters required for the action." },
    "context": {
      "type": "object",
      "properties": {
        "taskId": { "type": "string" }
      },
      "description": "A reference to the parent task context."
    }
  },
  "required": ["actionName", "targetAgentRole", "parameters"]
}
```

**Example:**
```json
{
  "actionName": "implement_feature",
  "targetAgentRole": "frontend-developer",
  "parameters": {
    "feature_description": "Create a new login button on the main page.",
    "relevant_files": ["src/components/HomePage.js"]
  },
  "context": {
    "taskId": "720da49f-0609-40a9-9ab0-a6f5351c731b"
  }
}
```

---

### 3.3. `AgentResponse` Schema

This object is the standard format for an agent to respond after completing an action. It indicates success or failure and provides any relevant output.

**JSON Schema:**
```json
{
  "type": "object",
  "properties": {
    "status": { "type": "string", "enum": ["success", "failure"], "description": "The status of the completed action." },
    "message": { "type": "string", "description": "A summary message describing the outcome." },
    "artifacts": {
      "type": "array",
      "items": { "type": "string" },
      "description": "A list of paths to any files created or modified during the action."
    },
    "error": { "type": "string", "description": "An error message if the action failed." }
  },
  "required": ["status", "message"]
}
```

**Example (Success):**
```json
{
  "status": "success",
  "message": "Login button was created and tested successfully.",
  "artifacts": ["src/components/HomePage.js", "src/components/LoginButton.js", "tests/LoginButton.test.js"]
}
```

**Example (Failure):**
```json
{
  "status": "failure",
  "message": "Failed to implement the feature due to a missing dependency.",
  "error": "Module 'auth-lib' not found."
}
```
