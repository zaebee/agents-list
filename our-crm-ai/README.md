# AI-Powered CRM & Project Management System

This project is a sophisticated, AI-powered system for managing tasks and projects. It combines a powerful command-line interface (CLI) with a modern web-based user interface (UI) to provide a comprehensive solution for individuals and teams. The system is built on a multi-agent architecture, leveraging a suite of specialized AI agents to automate and streamline project management workflows.

## 🚀 Key Features

- **Modern Web UI**: A responsive and intuitive web interface built with React and TypeScript, providing a visual way to manage tasks, interact with agents, and monitor project progress.
- **Enterprise Authentication**: Comprehensive JWT-based authentication system with user registration, secure login, session management, and role-based access control.
- **Subscription Management**: Tiered pricing model (Free, Pro, Enterprise) with feature gating, usage tracking, and Stripe integration for billing.
- **Intelligent Task Management**: The system analyzes task descriptions to automatically suggest the most suitable AI agent for the job, streamlining task assignment and ensuring expertise is matched to the task.
- **Advanced PM Agent Gateway**: For complex projects, a dedicated Project Manager agent can analyze high-level goals, decompose them into actionable subtasks, and create a comprehensive execution plan with dependencies.
- **Multi-Agent Collaboration**: The architecture supports seamless collaboration between specialized agents, allowing for complex workflows that mimic a real-world development team.
- **Analytics Dashboard**: Real-time analytics with system health monitoring, task completion tracking, and performance metrics visualization.
- **Full CRUD Operations**: Comprehensive task management capabilities, including creating, reading, updating, and deleting tasks, as well as commenting and moving tasks between columns.
- **Direct YouGile Integration**: Uses the YouGile API as a robust backend for project management, ensuring that all tasks and project data are stored in a centralized and reliable system.
- **Production-Ready Security**: Features secure Argon2 password hashing, input validation, audit logging, rate limiting, and OWASP-compliant security measures.

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
        G[Billing Service]
        H[Analytics Engine]
    end

    subgraph "AI Agents"
        I[Specialized Agents]
        J[Context Manager]
    end

    subgraph "Data & Integration"
        K[YouGile API]
        L[Database (SQLite/PostgreSQL)]
        M[Stripe API]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
    E --> I
    F --> I
    I --> J
    C --> K
    C --> L
    G --> M
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

2.  **Authentication Setup**: Configure the authentication system.
    ```bash
    # Generate a secure secret key for JWT tokens
    export SECRET_KEY="your_secure_secret_key_here"
    
    # Optional: Configure database URL (defaults to SQLite)
    export DATABASE_URL="sqlite:///./ai_crm.db"
    # For PostgreSQL: export DATABASE_URL="postgresql://user:password@localhost/ai_crm"
    ```

3.  **Billing Setup (Optional)**: For subscription features, configure Stripe.
    ```bash
    export STRIPE_SECRET_KEY="your_stripe_secret_key"
    export STRIPE_PUBLISHABLE_KEY="your_stripe_publishable_key"
    ```

4.  **Backend Dependencies**: Install the required Python libraries.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Frontend Dependencies**: Install the required Node.js packages.
    ```bash
    cd frontend
    npm install
    ```

6.  **Database Initialization**: Initialize the authentication database.
    ```bash
    python3 -c "from auth_database import create_tables, seed_default_data, SessionLocal; create_tables(); db = SessionLocal(); seed_default_data(db); db.close()"
    ```

### Initial Project Setup

Before using the CRM, you need to run the setup script once to initialize the project structure in YouGile. This will create the necessary project, board, columns, and agent "stickers".

```bash
# Use --project-id to connect to an existing project
python3 crm_setup_enhanced.py --project-id "your_project_id"
```
This will create a `config.json` file in the `our-crm-ai` directory, which is required for the application to run.

## 🏃 Development

To run the application in development mode, use the provided shell script. This will start the backend server with hot-reloading enabled.

```bash
./start-dev.sh
```

-   **Web UI**: You will need to start the frontend separately.
    ```bash
    cd frontend
    npm start
    ```
-   **Backend API**: The API will be available at `http://localhost:5001`.
-   **API Docs**: Interactive API documentation (Swagger UI) can be found at `http://localhost:5001/docs`.

### Authentication Usage

The system now includes a comprehensive authentication system. Here are the key endpoints:

#### User Registration
```bash
curl -X POST "http://localhost:5001/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "newuser",
       "email": "user@example.com",
       "password": "securepassword123",
       "full_name": "New User"
     }'
```

#### User Login
```bash
curl -X POST "http://localhost:5001/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "newuser",
       "password": "securepassword123"
     }'
```

#### Using Protected Endpoints
```bash
# Use the access_token from login response
curl -X GET "http://localhost:5001/api/auth/me" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Subscription Tiers

- **Free Tier**: 10 command executions/month, 9 Haiku agents
- **Pro Tier ($49/month)**: Unlimited commands, 46 agents, analytics dashboard
- **Enterprise Tier ($299/month)**: All 59 agents, custom features, priority support

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