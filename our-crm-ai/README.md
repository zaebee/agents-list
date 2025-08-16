# 🤖 AI-CRM: AI-Powered Project Management System

Enterprise-grade AI-powered CRM and project management system with multi-agent architecture, complete authentication, and production-ready deployment.

## ⚡ Quick Start

```bash
# Development Setup
git clone <repository>
cd our-crm-ai
./start-dev.sh

# Production Deployment  
docker-compose -f docker-compose.phase2a.yml up -d
```

## 🎯 Key Features

- **🔐 Enterprise Authentication** - JWT-based auth with role-based access control
- **🤖 Multi-Agent AI System** - 59+ specialized AI agents for task automation  
- **📊 Analytics Dashboard** - Real-time metrics and performance monitoring
- **🐳 Production Ready** - Complete Docker stack with PostgreSQL, Redis, monitoring
- **🔒 Security Hardened** - OWASP compliance, Argon2 hashing, audit logging
- **💰 Subscription Tiers** - Free/Pro/Enterprise with feature gating and Stripe billing

## 📚 Documentation

Complete documentation is available in the [`docs/`](./docs/) directory:

- **🚀 [Quick Start](./docs/guides/QUICKSTART.md)** - Get up and running in minutes
- **🐳 [Docker Setup](./docs/deployment/DOCKER_SETUP_GUIDE.md)** - Production deployment guide  
- **🔐 [Authentication](./docs/api/authentication.md)** - Complete auth system documentation
- **🏗️ [Architecture](./docs/architecture/)** - Technical design and AI integration guides
- **📊 [Reports](./docs/reports/)** - Production readiness and test reports

## 🏛️ Architecture

**3-Layer Architecture:**
- **Frontend**: React/TypeScript web UI with modern design
- **Backend**: FastAPI with PostgreSQL, Redis, and JWT authentication  
- **AI Layer**: 59+ specialized agents with intelligent task routing

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
        K[PostgreSQL Database]
        L[Authentication System]
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

- Python 3.11+
- Node.js 18+ and npm/bun
- Docker and Docker Compose
- PostgreSQL 15+ (or SQLite for development)
- AI API keys (Anthropic Claude recommended)

### Environment Setup

1.  **Environment Configuration**: Copy and configure the environment file.
    ```bash
    cp .env.docker .env
    # Edit .env with your specific configuration
    ```

2.  **Database Setup**: Configure PostgreSQL or SQLite database.
    ```bash
    # For PostgreSQL (recommended for production)
    export DATABASE_URL="postgresql://aicrm_user:password@localhost:5432/aicrm_db"
    
    # For SQLite (development only)
    export DATABASE_URL="sqlite:///./ai_crm.db"
    
    # Generate a secure secret key for JWT tokens
    export SECRET_KEY="your_secure_secret_key_here"
    ```

3.  **AI API Keys**: Configure AI provider API keys.
    ```bash
    export ANTHROPIC_API_KEY="your_anthropic_api_key"
    export OPENAI_API_KEY="your_openai_api_key"  # Optional
    export MISTRAL_API_KEY="your_mistral_api_key"  # Optional
    ```

4.  **Billing Setup (Optional)**: For subscription features, configure Stripe.
    ```bash
    export STRIPE_SECRET_KEY="your_stripe_secret_key"
    export STRIPE_PUBLISHABLE_KEY="your_stripe_publishable_key"
    ```

### Development Setup

1.  **Backend Dependencies**: Install the required Python libraries.
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt  # For development tools
    ```

2.  **Database Initialization**: Set up database tables and admin user.
    ```bash
    # Initialize database with admin user (admin/admin123)
    python -c "
    from auth_database import create_tables, seed_default_data, SessionLocal
    create_tables()
    db = SessionLocal()
    try:
        seed_default_data(db)
    finally:
        db.close()
    "
    ```

3.  **Frontend Dependencies**: Install the required Node.js packages.
    ```bash
    cd frontend
    npm install  # or bun install
    ```


### Initial Project Setup

The system is now fully integrated with PostgreSQL for robust data management. No external project management platform setup is required - everything runs locally with your own database.

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

> **Note**: Development server runs on port **5001**, while Docker deployment uses port **8080**.

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

> **Note**: Replace `localhost:5001` with `localhost:8080` when using Docker deployment.

### Subscription Tiers

- **Free Tier**: 10 command executions/month, 9 Haiku agents
- **Pro Tier ($49/month)**: Unlimited commands, 46 agents, analytics dashboard
- **Enterprise Tier ($299/month)**: All 59 agents, custom features, priority support

## 🛠️ Docker Deployment

For production deployment, use Docker Compose:

```bash
# Build and start all services
docker-compose -f docker-compose.phase2a.yml up --build

# Run in background
docker-compose -f docker-compose.phase2a.yml up -d

# Check logs
docker-compose -f docker-compose.phase2a.yml logs -f

# Stop services
docker-compose -f docker-compose.phase2a.yml down
```

The system will be available at:
- **API**: http://localhost:5001
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:5001/docs

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