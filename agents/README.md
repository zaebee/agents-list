# AI Agents Directory

This directory contains all specialized AI agent definitions for the AI-CRM system.

## Structure

All agent markdown files are organized in this directory with standardized naming conventions:

- `*-pro.md` - Language and technology specialists (python-pro, javascript-pro, etc.)
- `*-developer.md` - Development specialists (frontend-developer, mobile-developer, etc.)
- `*-engineer.md` - Engineering specialists (data-engineer, ml-engineer, etc.)
- `*-architect.md` - Architecture specialists (backend-architect, cloud-architect, etc.)
- `*-specialist.md` - Domain specialists (security-auditor, performance-engineer, etc.)

## Agent Categories

### Backend & Infrastructure
- backend-architect, cloud-architect, devops-troubleshooter
- database-admin, database-optimizer, deployment-engineer
- network-engineer, security-auditor

### Frontend & Mobile
- frontend-developer, mobile-developer, ui-ux-designer
- javascript-pro, typescript-pro, react specialists

### Data & AI/ML
- data-engineer, data-scientist, ml-engineer, mlops-engineer
- ai-engineer, prompt-engineer

### DevOps & Quality
- test-automator, code-reviewer, debugger
- performance-engineer, incident-responder

### Business & Content
- business-analyst, content-marketer, customer-support
- legal-advisor, sales-automator

### Language Specialists
- python-pro, java-pro, golang-pro, rust-pro, scala-pro
- c-pro, cpp-pro, csharp-pro, php-pro, elixir-pro

## AI-CRM Integration

Each agent file includes:
- Frontmatter with agent metadata (name, description, model, tools)
- Specialized expertise and focus areas
- AI-CRM sync logic for task management
- Integration instructions for seamless collaboration

## Usage

Agents are automatically discovered by the AI-CRM system and can be:
- Selected automatically based on task analysis
- Assigned manually for specific requirements
- Used in PM Gateway workflows for complex projects
- Integrated with task management and progress tracking

## Validation

Run `python validate_agents.py` from the project root to validate all agent definitions.