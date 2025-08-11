# AI-Powered CRM & Project Management System

This project is a sophisticated, AI-powered system for managing tasks and projects. It combines a powerful command-line interface (CLI) with a modern web-based user interface (UI) to provide a comprehensive solution for individuals and teams. The system is built on a multi-agent architecture, leveraging a suite of specialized AI agents to automate and streamline project management workflows.

## 🚀 Key Features

- **Modern Web UI**: A responsive and intuitive web interface built with React and TypeScript, providing a visual way to manage tasks, interact with agents, and monitor project progress.
- **Intelligent Task Management**: The system analyzes task descriptions to automatically suggest the most suitable AI agent for the job, streamlining task assignment and ensuring expertise is matched to the task.
- **Advanced PM Agent Gateway**: For complex projects, a dedicated Project Manager agent can analyze high-level goals, decompose them into actionable subtasks, and create a comprehensive execution plan with dependencies.
- **Multi-Agent Collaboration**: The architecture supports seamless collaboration between specialized agents, allowing for complex workflows that mimic a real-world development team.
- **Full CRUD Operations**: Comprehensive task management capabilities, including creating, reading, updating, and deleting tasks, as well as commenting and moving tasks between columns.
- **Direct YouGile Integration**: Uses the YouGile API as a robust backend for project management, ensuring that all tasks and project data are stored in a centralized and reliable system.
- **Secure and Robust**: Features a secure authentication system, API call retries with exponential backoff, and validation to prevent common security vulnerabilities.

## 🏛️ Architecture Overview

The system is composed of three main layers:

1.  **Frontend (Web UI)**: A React application (in the `frontend` directory) that provides the user interface for interacting with the system. It communicates with the backend via a RESTful API.
2.  **Backend (FastAPI)**: A Python-based backend powered by FastAPI that serves the API, handles business logic, and orchestrates the AI agents.
3.  **AI Agent Core**: A collection of specialized AI agents (defined in the `agents` directory) that perform various tasks, from code generation to documentation and security analysis.

```mermaid
graph TD
    subgraph "User Interfaces"
        A[Web UI (React)]
        B[CLI (crm_enhanced.py)]
    end

    subgraph "Backend Services"
        C[API Server (FastAPI)]
        D[Authentication Service]
        E[Agent Selector]
        F[PM Agent Gateway]
    end

    subgraph "AI Agents"
        G[Specialized Agents]
        H[Context Manager]
    end

    subgraph "Data & Integration"
        I[YouGile API]
        J[Database (PostgreSQL)]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    C --> F
    E --> G
    F --> G
    G --> H
    C --> I
    C --> J
```

## 🛠️ Setup and Installation

### Prerequisites

- Python 3.9+
- Node.js 16+ and npm
- Docker and Docker Compose
- A YouGile account and API key

### Environment Setup

1.  **YouGile API Key**: Set your YouGile API key as an environment variable.
    ```bash
    export YOUGILE_API_KEY="your_api_key_here"
    ```

2.  **Backend Dependencies**: Install the required Python libraries.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Frontend Dependencies**: Install the required Node.js packages.
    ```bash
    cd frontend
    npm install
    ```

### Initial Project Setup

Before using the CRM, you need to run the setup script once to initialize the project structure in YouGile. This will create the necessary project, board, columns, and agent "stickers".

```bash
# Use --project-id to connect to an existing project
python3 crm_setup_enhanced.py --project-id "your_project_id"
```
This will create a `config.json` file in the `our-crm-ai` directory, which is required for the application to run.

## 🏃 Running the Application

You can run the application in development mode using the provided shell script, which will start both the backend and frontend servers.

```bash
./start-dev.sh
```

-   **Web UI**: Access the application at `http://localhost:3000`.
-   **Backend API**: The API will be available at `http://localhost:8000`.
-   **API Docs**: Interactive API documentation (Swagger UI) can be found at `http://localhost:8000/docs`.

##  CLI Usage

The `crm_enhanced.py` script provides a powerful command-line interface for interacting with the system.

### Create a Task
```bash
python3 crm_enhanced.py create --title "<task_title>" --description "<task_description>" [--owner <agent_name>]
```

### Analyze a Task with the PM Agent
```bash
python3 crm_enhanced.py pm --title "<task_title>" --description "<task_description>"
```

### Other Commands
For a full list of commands and their options, you can use the `--help` flag.
```bash
python3 crm_enhanced.py --help
python3 crm_enhanced.py create --help
```

## 📚 Documentation

For more detailed information about the system, please refer to the main documentation in the `docs` directory:

-   **`docs/AGENT_GUIDE.md`**: A comprehensive guide to all the available AI agents and their specializations.
-   **`docs/DEPLOYMENT_GUIDE.md`**: Instructions for deploying the application to production environments.
-   **`docs/WEB_UI_GUIDE.md`**: A guide to using the web-based user interface.