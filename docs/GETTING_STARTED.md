# 🚀 Getting Started with AI-CRM System

Welcome to the AI-CRM system - a sophisticated task management platform powered by 59+ specialized AI agents. This guide will help you get up and running quickly.

## 📋 What is AI-CRM?

The AI-CRM system is an intelligent task management platform that automatically assigns the best AI specialist to handle your tasks. Whether you need to fix bugs, build features, optimize performance, or create documentation, our AI agents have the expertise to help.

**Key Features:**
- 🤖 **59+ Specialized AI Agents** - From Python developers to security auditors
- 🎯 **Intelligent Task Assignment** - AI analyzes your tasks and suggests the best agent
- 📊 **PM Gateway** - Advanced project management with task decomposition
- 🌐 **Modern Web Interface** - User-friendly drag-and-drop task management
- 🔐 **Enterprise Authentication** - Secure user accounts with subscription tiers
- ⚡ **CLI & Web Access** - Use the command line or web interface

## 🎯 Quick Setup (5 Minutes)

### Prerequisites

1. **Python 3.7+** (for CLI usage)
2. **YouGile Account** - Free project management backend ([Sign up here](https://yougile.com))
3. **Docker & Docker Compose** (for web interface)
4. **Node.js 18+** (for local web development)

### Step 1: Get Your YouGile API Key

1. Log into your YouGile account
2. Go to Settings → API Integration
3. Generate a new API key
4. Copy the key - you'll need it shortly

### Step 2: Choose Your Installation Method

#### 🖥️ Option A: Command Line Only (Fastest)

```bash
# Clone the repository
git clone https://github.com/wshobson/agents.git
cd agents/our-crm-ai

# Install Python dependencies
pip install -r requirements.txt

# Set your API key
export YOUGILE_API_KEY="your_api_key_here"

# Initialize the system (one-time setup)
python3 crm_setup_enhanced.py

# Create your first task!
python3 crm_enhanced.py create --title "Set up development environment" --description "Configure my workspace for Python development"
```

#### 🌐 Option B: Full Web Interface (Recommended)

```bash
# Clone and setup
git clone https://github.com/wshobson/agents.git
cd agents

# Quick start with Docker
cd web-ui
cp .env.example .env
# Edit .env and add your YOUGILE_API_KEY

# Start everything with one command
./start-dev.sh

# Access the web interface
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### Step 3: Create Your First Task

#### Using CLI:
```bash
python3 crm_enhanced.py create --title "Learn AI-CRM system" --description "Explore the features and capabilities"
```

#### Using Web Interface:
1. Open http://localhost:3000
2. Register a new account or log in
3. Click "New Task" button
4. Enter title and description
5. Watch AI suggest the perfect agent!

## 🎓 Understanding AI Agents

### Agent Categories

**🔧 Development Specialists**
- `python-pro` - Python development expert
- `javascript-pro` - JavaScript/Node.js specialist  
- `frontend-developer` - React/UI specialist
- `backend-architect` - API and database design

**🏗️ Infrastructure Experts**
- `devops-troubleshooter` - Production issues and deployments
- `cloud-architect` - AWS/Azure/GCP infrastructure
- `security-auditor` - Security vulnerabilities and compliance
- `database-optimizer` - Query performance and optimization

**📊 Data & Analytics**
- `data-scientist` - Data analysis and insights
- `ml-engineer` - Machine learning pipelines
- `business-analyst` - KPIs and business metrics

**📝 Documentation & Communication**
- `docs-architect` - Technical documentation
- `content-marketer` - Blog posts and marketing content
- `customer-support` - User support and FAQs

### How Agent Selection Works

1. **Automatic Analysis** - AI reads your task title and description
2. **Keyword Matching** - Identifies key technologies and requirements
3. **Complexity Assessment** - Determines if multiple agents are needed
4. **Confidence Scoring** - Provides confidence percentage for suggestions
5. **Smart Assignment** - Assigns the most qualified specialist

Example:
```bash
# Task: "Fix slow database queries in production"
# AI Analysis: Keywords "database", "queries", "performance" → database-optimizer (95% confidence)

# Task: "Build React dashboard with charts"  
# AI Analysis: Keywords "React", "dashboard", "UI" → frontend-developer (92% confidence)
```

## 💡 Basic Usage Patterns

### 1. Simple Task Creation
```bash
# Let AI choose the best agent
python3 crm_enhanced.py create --title "Add user authentication" --description "Implement JWT login system"

# Force a specific agent
python3 crm_enhanced.py create --title "Database backup" --owner database-admin
```

### 2. Complex Project Analysis
```bash
# Use PM Gateway for complex projects
python3 crm_enhanced.py pm --title "Build e-commerce platform" --description "Full marketplace with payments, user accounts, and product catalog"

# This will break down the project into subtasks with different specialists
```

### 3. Task Management
```bash
# List all tasks
python3 crm_enhanced.py list

# View task details
python3 crm_enhanced.py view <task_id>

# Move task between columns
python3 crm_enhanced.py move <task_id> --column "In Progress"

# Add comments
python3 crm_enhanced.py comment <task_id> --message "Started working on this"

# Mark complete
python3 crm_enhanced.py complete <task_id>
```

### 4. Getting Help and Suggestions
```bash
# List all available agents
python3 crm_enhanced.py agents

# Get agent suggestions without creating a task
python3 crm_enhanced.py suggest "implement caching with Redis"
```

## 🌐 Web Interface Basics

### Dashboard Overview
- **Kanban Board** - Drag tasks between "To Do", "In Progress", "Done"
- **New Task Button** - Create tasks with AI suggestions
- **Task Cards** - Click to view details, comments, and history
- **Agent Badges** - See which specialist is assigned to each task

### User Account Features
- **Profile Management** - Update your information and preferences
- **Session Management** - View and revoke active sessions
- **Subscription Tiers** - Free, Pro, Enterprise with different agent access
- **Usage Analytics** - Track your monthly usage and limits

### Task Management Features
- **Drag & Drop** - Move tasks between columns
- **Real-time Updates** - See changes instantly across devices
- **Rich Comments** - Collaborate with team members
- **Task History** - Track all changes and assignments

## 🔧 Common Use Cases

### For Developers
```bash
# Code review
python3 crm_enhanced.py create --title "Review authentication module" --description "Security review of JWT implementation"
→ Assigned to: security-auditor

# Performance optimization  
python3 crm_enhanced.py create --title "Optimize API response times" --description "Database queries are slow"
→ Assigned to: performance-engineer

# Bug fixes
python3 crm_enhanced.py create --title "Fix login redirect bug" --description "Users not redirected after login"
→ Assigned to: frontend-developer
```

### For Project Managers
```bash
# Project planning
python3 crm_enhanced.py pm --title "Q4 feature roadmap" --description "Plan major features for next quarter"
→ Comprehensive analysis with timeline and resource allocation

# Risk assessment
python3 crm_enhanced.py pm --title "Migration to microservices" --description "Move from monolith to microservice architecture"
→ Risk analysis, dependency mapping, and phased approach
```

### For Business Teams
```bash
# Content creation
python3 crm_enhanced.py create --title "Write product announcement" --description "Blog post for new feature launch"
→ Assigned to: content-marketer

# Data analysis
python3 crm_enhanced.py create --title "Analyze user engagement metrics" --description "Monthly user behavior report"
→ Assigned to: data-scientist
```

## 🚨 Troubleshooting

### Common Issues

**"No module named" errors:**
```bash
# Make sure you're in the right directory
cd agents/our-crm-ai

# Reinstall dependencies
pip install -r requirements.txt
```

**API connection failed:**
```bash
# Verify your API key is set
echo $YOUGILE_API_KEY

# If empty, set it again
export YOUGILE_API_KEY="your_actual_key"
```

**Configuration not found:**
```bash
# Run the setup script again
python3 crm_setup_enhanced.py
```

**Web UI not loading:**
```bash
# Check if services are running
docker-compose ps

# Restart services
docker-compose down
docker-compose up --build
```

### Getting Help

1. **Documentation** - Check `/docs` folder for detailed guides
2. **Health Check** - Use `python3 crm_enhanced.py list` to test connectivity
3. **Log Files** - Check `ai-crm.log` for error details
4. **Web API** - Visit http://localhost:8000/health for backend status

## 🎯 Next Steps

Now that you're set up, explore these guides:

1. **[User Manual](USER_MANUAL.md)** - Complete feature documentation
2. **[AI Agent Guide](AGENT_GUIDE.md)** - Deep dive into the 59+ specialists
3. **[Web UI Guide](WEB_UI_GUIDE.md)** - Master the web interface
4. **[Advanced Features](ADVANCED_FEATURES.md)** - PM Gateway and complex workflows

## 🎉 Welcome to AI-Powered Task Management!

You're now ready to leverage the power of 59+ AI specialists to handle your tasks intelligently. Whether you prefer the command line or web interface, the AI-CRM system adapts to your workflow and helps you get things done efficiently.

**Quick tips for success:**
- ✅ Be descriptive in your task titles and descriptions
- ✅ Let the AI suggest agents - it's usually right!
- ✅ Use the PM Gateway for complex projects
- ✅ Check the web interface for a visual overview
- ✅ Don't hesitate to experiment with different agents

Happy task managing! 🚀