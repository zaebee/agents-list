# 🎯 PM Agent Gateway - Complete Usage Guide

## Overview

The PM Agent Gateway is an intelligent project management system that provides comprehensive task analysis, workflow planning, and multi-agent orchestration. It acts as a virtual PM that analyzes tasks, recommends optimal agent assignments, and coordinates complex project workflows.

## 🚀 Quick Start

### Basic Task Analysis
```bash
# Simple PM analysis
python3 crm_enhanced.py pm --title "Fix login bug" --description "Users can't authenticate"

# Complex project analysis
python3 crm_enhanced.py pm --title "Build recommendation engine" --description "ML-powered product suggestions with A/B testing"
```

### Integrated Task Creation
```bash
# Create task with automatic PM intelligence
python3 crm_enhanced.py create --title "Optimize database" --description "Slow queries affecting performance"

# Skip PM analysis for simple tasks
python3 crm_enhanced.py create --title "Update documentation" --no-ai-suggest
```

## 📋 CLI Commands Reference

### 1. PM Analysis Command

**Command:** `python3 crm_enhanced.py pm`

**Purpose:** Comprehensive task analysis with strategic recommendations

**Parameters:**
- `--title` (required): Task title for analysis
- `--description` (optional): Detailed task description for better analysis

**Examples:**
```bash
# Basic analysis
python3 crm_enhanced.py pm --title "Implement OAuth2"

# Detailed analysis
python3 crm_enhanced.py pm --title "Build API Gateway" --description "Microservices routing with authentication, rate limiting, and monitoring"
```

**Output Includes:**
- **Task Complexity**: SIMPLE, MODERATE, COMPLEX, EPIC
- **Estimated Hours**: Time-based effort assessment  
- **Priority Level**: LOW, MEDIUM, HIGH, URGENT
- **Recommended Agents**: Optimal specialist assignments
- **Risk Factors**: Potential challenges and concerns
- **Success Criteria**: Definition of done requirements
- **Workflow Decomposition**: For complex tasks, detailed subtask breakdown

### 2. Enhanced Task Creation

**Command:** `python3 crm_enhanced.py create`

**Purpose:** Create tasks with integrated PM Gateway intelligence

**Parameters:**
- `--title` (required): Task title
- `--description` (optional): Task description  
- `--owner` (optional): Specific agent assignment
- `--no-ai-suggest`: Skip AI analysis and suggestions

**PM Integration:**
- Automatically invokes PM Gateway for task analysis
- Provides intelligent agent recommendations
- Handles complex task decomposition
- Shows priority and risk assessment

**Examples:**
```bash
# Auto-analyzed task creation
python3 crm_enhanced.py create --title "Implement payment processing" --description "Stripe integration with webhooks"

# Force specific agent assignment
python3 crm_enhanced.py create --title "Database backup" --owner database-admin

# Skip PM analysis
python3 crm_enhanced.py create --title "Update README" --no-ai-suggest
```

### 3. Agent Intelligence Commands

**Command:** `python3 crm_enhanced.py suggest`

**Purpose:** Get AI agent recommendations without task creation

**Example:**
```bash
python3 crm_enhanced.py suggest "implement JWT authentication with refresh tokens"
```

**Command:** `python3 crm_enhanced.py agents`

**Purpose:** List all available agents by specialization

```bash
python3 crm_enhanced.py agents
```

### 4. Standalone PM Gateway CLI

**Command:** `python3 pm_agent_gateway.py`

**Purpose:** Direct access to PM Gateway functionality

**Subcommands:**
- `analyze`: Comprehensive task analysis
- `monitor`: Task progress monitoring (placeholder)
- `decompose`: Task breakdown into subtasks

**Examples:**
```bash
# Direct PM analysis
python3 pm_agent_gateway.py analyze --title "Build microservices architecture" --description "Container orchestration with Kubernetes"

# Task decomposition
python3 pm_agent_gateway.py decompose --title "E-commerce platform" --description "Full marketplace solution"

# Progress monitoring
python3 pm_agent_gateway.py monitor task-id-12345
```

## 🧠 PM Gateway Intelligence Features

### Task Complexity Assessment

**SIMPLE (2-4 hours)**
- Single agent capability
- Straightforward implementation
- Minimal dependencies
- Low risk factors

Example Output:
```
🎯 PM Agent analyzing task: 'Fix CSS styling bug'
📊 Analysis Results:
   Complexity: SIMPLE
   Estimated: 2 hours
   Priority: MEDIUM
   Required agents: frontend-developer
✅ Recommended assignment: frontend-developer
```

**MODERATE (8-16 hours)**
- 1-2 agents required
- Moderate complexity
- Some dependencies
- Standard risk profile

Example Output:
```
🎯 PM Agent analyzing task: 'Implement user authentication'
📊 Analysis Results:
   Complexity: MODERATE
   Estimated: 8 hours
   Priority: HIGH
   Required agents: security-auditor, backend-architect
   ⚠️  Risk factors: Security compliance requirements
✅ Recommended assignment: security-auditor
```

**COMPLEX (32-60 hours)**
- 2-4 agents coordination
- Multi-stage workflow
- Dependencies and integration
- Higher risk factors

**EPIC (80+ hours)**
- 4+ agents orchestration
- Multi-week timeline
- Complex dependencies
- Significant risk management

Example Output:
```
🎯 PM Agent analyzing task: 'Build complete e-commerce platform'
📊 Analysis Results:
   Complexity: EPIC
   Estimated: 80 hours
   Priority: LOW
   Required agents: payment-integration, devops-troubleshooter, security-auditor
🔄 Complex task detected - recommending decomposition
📋 Suggested subtasks (7):
   1. Requirements Analysis → business-analyst (8.0 hours)
   2. API Design → backend-architect (12.0 hours)
   3. Frontend Design → frontend-developer (16.0 hours)
   4. Implementation → payment-integration (32.0 hours)
   5. Testing → test-automator (8.0 hours)
   6. Security Review → security-auditor (4.0 hours)
   7. Deployment → devops-troubleshooter (6.0 hours)
```

### Priority Assessment

**Priority Indicators:**
- **URGENT**: Critical issues, outages, security breaches
- **HIGH**: Production bugs, security tasks, performance issues
- **MEDIUM**: New features, enhancements, optimizations
- **LOW**: Documentation, minor improvements, research tasks

### Risk Factor Analysis

**Common Risk Factors:**
- Legacy system integration risk
- Security compliance requirements  
- Performance and scalability concerns
- Data migration and consistency risks

### Success Criteria Definition

**Automatic Criteria Generation:**
- Task completed successfully
- Quality standards met
- All tests passing (for test-related tasks)
- Successfully deployed to production (for deployment tasks)
- Performance benchmarks met (for optimization tasks)

## 🔄 Multi-Agent Orchestration

### Workflow Templates

The PM Gateway includes pre-built workflow templates for common project patterns:

**Full-Stack Feature Development**
1. Requirements Analysis → business-analyst
2. API Design → backend-architect  
3. Frontend Design → frontend-developer
4. Implementation → auto-selected specialist
5. Testing → test-automator
6. Security Review → security-auditor
7. Deployment → devops-troubleshooter

**Data Analysis Project**
1. Data Collection → data-engineer
2. Analysis → data-scientist
3. Visualization → business-analyst
4. Reporting → docs-architect

**Infrastructure Setup**
1. Architecture Design → cloud-architect
2. Infrastructure Code → terraform-specialist
3. Deployment → deployment-engineer  
4. Monitoring → devops-troubleshooter
5. Security Hardening → security-auditor

### Dependency Management

Complex tasks automatically include dependency chains:
```
Subtask 2: API Design
→ Depends on: Subtask 1 (Requirements Analysis)

Subtask 3: Frontend Design  
→ Depends on: Subtask 2 (API Design)
```

## 💡 Best Practices

### 1. Effective Task Descriptions

**Good Examples:**
```bash
# Specific and contextual
python3 crm_enhanced.py pm --title "Optimize checkout performance" --description "Database queries during payment processing are slow, affecting conversion rates"

# Includes technical constraints
python3 crm_enhanced.py pm --title "Implement caching" --description "Redis-based caching for API responses, must handle TTL and cache invalidation"
```

**Avoid:**
```bash
# Too vague
python3 crm_enhanced.py pm --title "Fix bug"

# Missing context
python3 crm_enhanced.py pm --title "Add feature"
```

### 2. Leveraging PM Intelligence

**When to use PM analysis:**
- New feature development
- Complex technical implementations
- Cross-functional projects
- Performance optimization initiatives
- Security implementations

**When to skip PM analysis:**
- Simple bug fixes
- Documentation updates
- Minor configuration changes
- Routine maintenance tasks

### 3. Working with Complex Tasks

For EPIC-level tasks, the PM Gateway will recommend decomposition:

1. **Review the subtask breakdown** - Understand the suggested workflow
2. **Validate dependencies** - Ensure the sequence makes sense for your project
3. **Consider creating parent/child task structure** - Use your task management system to organize
4. **Assign different subtasks to team members** - Leverage the specialist recommendations

### 4. Integrating with Team Workflows

**For Team Leads:**
```bash
# Analyze project scope before sprint planning
python3 crm_enhanced.py pm --title "User dashboard redesign" --description "Complete UI overhaul with new branding and mobile responsiveness"
```

**For Individual Contributors:**
```bash  
# Get intelligent agent suggestions for unfamiliar tasks
python3 crm_enhanced.py pm --title "Implement WebSocket real-time updates" --description "Live notifications for task status changes"
```

**For Project Managers:**
```bash
# Use backlog analyzer for strategic planning
python3 backlog_analyzer.py
```

## 🔧 Advanced Configuration

### Environment Setup

The PM Gateway uses the same configuration as the main CRM system:

1. **Ensure CRM is configured:**
   ```bash
   cd our-crm-ai
   python3 crm_setup_enhanced.py
   ```

2. **API Key Configuration:**
   ```bash
   export YOUGILE_API_KEY="your_api_key_here"
   ```

3. **Verify configuration:**
   ```bash
   python3 crm_enhanced.py agents  # Should show all 59 agents
   ```

### Custom Agent Specializations

The PM Gateway includes built-in knowledge about agent specializations:

```python
agent_specializations = {
    'frontend-developer': ['ui', 'ux', 'react', 'vue', 'html', 'css'],
    'backend-architect': ['api', 'microservices', 'database', 'architecture'],
    'devops-troubleshooter': ['deployment', 'infrastructure', 'monitoring'],
    'security-auditor': ['authentication', 'authorization', 'vulnerabilities'],
    # ... and 55 more agents
}
```

These specializations inform the intelligent routing decisions.

## 📊 Output Format Reference

### Direct Assignment Response
```
🎯 PM Agent Analysis Complete!
============================================================
📋 Task: Optimize database queries
🎯 Recommended Agent: database-optimizer
📊 Priority: HIGH  
⏰ Estimated: 8 hours
🔧 Complexity: MODERATE
⚠️  Risk Factors:
   • Performance and scalability concerns
✅ Success Criteria:
   • Task completed successfully
   • Quality standards met
   • Performance benchmarks met
💡 Recommendation: Assign to database-optimizer - estimated 8 hours
```

### Complex Task Decomposition Response
```
🎯 PM Agent Analysis Complete!
============================================================
📋 Complex Task: Build recommendation engine
📊 Priority: MEDIUM
⏰ Total Estimated: 32 hours
🔧 Complexity: COMPLEX

🔄 Recommended Subtasks (5):
   1. Data Collection and Analysis
      → Agent: data-engineer
      → Time: 8.0 hours

   2. ML Model Development  
      → Agent: ml-engineer
      → Time: 12.0 hours
      → Depends on: Data Collection and Analysis

   3. API Implementation
      → Agent: backend-architect
      → Time: 6.0 hours  
      → Depends on: ML Model Development

   4. Frontend Integration
      → Agent: frontend-developer
      → Time: 4.0 hours
      → Depends on: API Implementation

   5. Testing and Deployment
      → Agent: test-automator
      → Time: 2.0 hours
      → Depends on: Frontend Integration

💡 Recommendation: Break this task into subtasks for better management
```

## 🚨 Troubleshooting

### Common Issues

**1. PM Gateway Not Found**
```bash
Error: No module named 'pm_agent_gateway'
```
**Solution:** Ensure you're in the `our-crm-ai` directory and the file exists.

**2. Configuration Not Loaded**
```bash
Error: Failed to load CRM configuration
```
**Solution:** Run `python3 crm_setup_enhanced.py` to initialize the configuration.

**3. Agent Not Recognized**
```bash
Error: Owner 'invalid-agent' is not a valid AI agent role
```
**Solution:** Use `python3 crm_enhanced.py agents` to see available agents.

**4. API Key Issues**
```bash
Error: YOUGILE_API_KEY environment variable not set
```
**Solution:** Set your YouGile API key: `export YOUGILE_API_KEY="your_key"`

### Performance Optimization

For large-scale usage:

1. **Batch Analysis:** Use the standalone CLI for multiple tasks
2. **Caching:** The PM Gateway caches agent knowledge for faster responses
3. **Parallel Processing:** Complex task analysis can handle multiple subtasks efficiently

## 🔄 Integration Examples

### With CI/CD Pipelines
```bash
# Pre-deployment task analysis
python3 crm_enhanced.py pm --title "Deploy v2.1.0" --description "Production deployment with database migrations"
```

### With Project Management Tools
```bash
# Export task analysis for external tools
python3 pm_agent_gateway.py analyze --title "Feature X" --description "..." | jq .
```

### With Team Automation
```bash
#!/bin/bash
# Auto-assign tasks based on PM recommendations
TASK_TITLE="$1"
TASK_DESC="$2"

RECOMMENDATION=$(python3 crm_enhanced.py pm --title "$TASK_TITLE" --description "$TASK_DESC" | grep "Recommended Agent:" | cut -d: -f2 | xargs)

python3 crm_enhanced.py create --title "$TASK_TITLE" --description "$TASK_DESC" --owner "$RECOMMENDATION"
```

---

## 🎯 Next Steps

The PM Agent Gateway is production-ready and provides:

- ✅ Intelligent task analysis and agent routing
- ✅ Complex project decomposition with dependency management  
- ✅ Strategic priority and risk assessment
- ✅ Seamless integration with the enhanced CRM system
- ✅ Multi-modal access (CLI, Web UI, API endpoints)

**Ready for Phase 2B enhancements:**
- Advanced analytics and reporting
- Custom workflow template creation
- Team performance metrics and optimization
- Integration with enterprise project management tools

---

*Generated as part of the AI-CRM Phase 2A completion*