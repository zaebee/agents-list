# AI-CRM User Guide - Phase 2A

Welcome to AI-CRM, the comprehensive AI-powered project management platform with 59+ specialized agents across multiple providers.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Subscription Plans](#subscription-plans)
3. [Using AI Agents](#using-ai-agents)
4. [Task Management](#task-management)
5. [Analytics Dashboard](#analytics-dashboard)
6. [Billing Management](#billing-management)
7. [API Integration](#api-integration)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Account Setup
1. **Sign Up**: Visit [app.aicrm.com](https://app.aicrm.com) and create your account
2. **Email Verification**: Check your email and verify your account
3. **Choose Plan**: Start with our Free tier or upgrade to Pro/Enterprise
4. **API Keys**: Configure your AI provider API keys in Settings

### First Steps
1. **Dashboard Overview**: Familiarize yourself with the main dashboard
2. **Agent Exploration**: Browse available AI agents by category
3. **Create First Task**: Try creating a simple task to get familiar
4. **Real-time Updates**: Enable notifications for task progress

## Subscription Plans

### Free Tier - $0/month
**Perfect for individuals and small teams**
- ✅ 9 Haiku-powered agents
- ✅ 10 tasks per month
- ✅ Basic analytics
- ✅ Community support
- ✅ Web interface access

**Available Agents:**
- Data Scientist, Business Analyst, Frontend Developer
- Debugger, Test Automator, Content Marketer
- Customer Support, Documentation Linter, Tutorial Engineer

### Pro Tier - $49/month
**Ideal for growing teams and businesses**
- ✅ 46 total agents (9 Haiku + 37 Sonnet)
- ✅ Unlimited tasks
- ✅ Advanced analytics
- ✅ Priority email support
- ✅ API access
- ✅ Real-time updates
- ✅ Task automation

**Additional Agents Include:**
- Backend Architect, Security Auditor, DevOps Troubleshooter
- Performance Engineer, Code Reviewer, Database Optimizer
- Cloud Architect, Language Specialists (Python, JavaScript, etc.)
- Mobile Developer, Payment Integration, GraphQL Architect

### Enterprise Tier - $299/month
**For large organizations with complex needs**
- ✅ All 59 agents (including 13 Opus-powered)
- ✅ Custom agent training
- ✅ Dedicated support manager
- ✅ SSO integration
- ✅ Advanced security features
- ✅ On-premise deployment
- ✅ SLA guarantees

**Exclusive Opus Agents:**
- AI Engineer, ML Engineer, MLOps Engineer
- Data Engineer, Quantitative Analyst, Risk Manager
- Legal Advisor, Documentation Architect, Context Manager
- Incident Responder, DX Optimizer, Sales Automator, Prompt Engineer

## Using AI Agents

### Agent Selection
1. **Browse by Category**: Navigate to Agents section
2. **Filter by Capability**: Use filters to find specialized agents
3. **View Agent Details**: Click on any agent to see capabilities
4. **Check Availability**: Green indicators show agent availability

### Task Creation
1. **Describe Your Task**: Write a clear, detailed description
2. **Select Agent** (Optional): Choose specific agent or let AI decide
3. **Add Context**: Provide relevant files, links, or background
4. **Set Priority**: Choose urgency level
5. **Submit**: Task is queued for execution

### Best Practices
- **Be Specific**: Detailed descriptions get better results
- **Provide Context**: Include relevant background information
- **Choose Right Agent**: Match task complexity to agent capability
- **Monitor Progress**: Use real-time updates to track completion

## Task Management

### Task Lifecycle
1. **Created**: Task is submitted and queued
2. **Analyzing**: AI agent analyzes requirements
3. **In Progress**: Agent is actively working
4. **Review**: Results are being formatted
5. **Completed**: Task finished successfully
6. **Failed**: Task encountered an error (auto-retry available)

### Task Operations
- **View Details**: Click task to see full information
- **Download Results**: Export task outputs in multiple formats
- **Clone Task**: Create similar tasks based on previous ones
- **Share Results**: Generate shareable links for collaboration
- **Archive**: Move completed tasks to archive

### Task Categories
- **Code Review**: Pull request analysis, security audits
- **Data Analysis**: Statistical analysis, visualization, insights
- **Content Creation**: Documentation, marketing copy, tutorials
- **System Design**: Architecture planning, database design
- **Business Analysis**: Market research, requirement gathering

## Analytics Dashboard

### Key Metrics
- **Task Completion Rate**: Percentage of successful tasks
- **Agent Utilization**: Most used agents and efficiency
- **Cost Tracking**: Monthly spend and token usage
- **Performance Trends**: Success rates over time

### Charts and Visualizations
- **Task Trends**: Daily/weekly task volume
- **Agent Performance**: Success rates and response times
- **Cost Analysis**: Spending patterns and optimization
- **Usage Patterns**: Peak usage times and patterns

### Custom Reports
- **Date Ranges**: Filter by specific time periods
- **Agent Groups**: Focus on specific agent categories
- **Export Options**: Download reports as PDF or CSV
- **Scheduled Reports**: Set up automated reporting

## Billing Management

### Subscription Management
- **View Current Plan**: See active subscription details
- **Usage Monitoring**: Track monthly limits and consumption
- **Upgrade/Downgrade**: Change plans as needed
- **Billing History**: Access invoices and payment records

### Payment Methods
- **Credit Cards**: Visa, MasterCard, American Express
- **Bank Transfer**: Available for Enterprise customers
- **Invoice Billing**: Net-30 terms for qualified accounts
- **Multiple Cards**: Backup payment methods

### Cost Optimization
- **Usage Alerts**: Get notified when approaching limits
- **Agent Selection**: Choose cost-effective agents for tasks
- **Bulk Operations**: Process multiple tasks efficiently
- **Annual Billing**: Save up to 20% with yearly plans

## API Integration

### Authentication
```bash
curl -X POST https://api.aicrm.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your-email", "password":"your-password"}'
```

### Common Operations
```bash
# List available agents
curl -H "Authorization: Bearer $TOKEN" \
  https://api.aicrm.com/api/agents

# Create a task
curl -X POST https://api.aicrm.com/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Review this code", "agent_id":"code-reviewer"}'

# Get task results
curl -H "Authorization: Bearer $TOKEN" \
  https://api.aicrm.com/api/tasks/{task_id}
```

### Webhooks
Set up webhooks to receive real-time notifications:
```json
{
  "endpoint": "https://your-app.com/webhook",
  "events": ["task.completed", "task.failed"],
  "secret": "your-webhook-secret"
}
```

### SDKs
- **JavaScript**: `npm install @aicrm/api-client`
- **Python**: `pip install aicrm-api`
- **Go**: `go get github.com/aicrm/go-client`
- **Ruby**: `gem install aicrm`

## Troubleshooting

### Common Issues

#### Task Failed
**Symptoms**: Task shows "Failed" status
**Solutions**:
1. Check task description for clarity
2. Verify agent is appropriate for task type
3. Check account limits and billing status
4. Contact support if issue persists

#### Agent Not Available
**Symptoms**: Preferred agent shows as unavailable
**Solutions**:
1. Wait a few minutes and retry
2. Choose alternative agent with similar capabilities
3. Upgrade plan if agent requires higher tier
4. Check system status at status.aicrm.com

#### API Authentication Errors
**Symptoms**: 401 Unauthorized responses
**Solutions**:
1. Check JWT token is valid and not expired
2. Verify token format: `Bearer <token>`
3. Confirm account is active and in good standing
4. Regenerate API token if needed

#### Slow Performance
**Symptoms**: Tasks taking longer than expected
**Solutions**:
1. Check system status for any issues
2. Simplify task description if overly complex
3. Try during off-peak hours
4. Consider upgrading to higher tier for priority processing

### Getting Help

#### Support Channels
- **Email**: support@aicrm.com (24-hour response)
- **Chat**: Available in-app during business hours
- **Documentation**: docs.aicrm.com
- **Community**: community.aicrm.com
- **Status**: status.aicrm.com

#### What to Include in Support Requests
1. Account email address
2. Task ID or screenshot of issue
3. Steps to reproduce the problem
4. Expected vs. actual behavior
5. Browser/OS information (for web issues)

#### Enterprise Support
Enterprise customers receive:
- Dedicated support engineer
- Priority response (1-hour SLA)
- Phone support during business hours
- Quarterly business reviews
- Custom onboarding and training

## Advanced Features

### Custom Agent Training
Enterprise customers can create custom agents:
1. Provide training data and examples
2. Define agent specializations
3. Test and validate performance
4. Deploy to your organization

### Integration Ecosystem
Connect AI-CRM with your existing tools:
- **Slack**: Get task notifications in Slack channels
- **GitHub**: Automatic code review on pull requests  
- **Jira**: Sync tasks with your project management
- **Zapier**: Connect with 3000+ apps

### Workflow Automation
Create automated workflows:
1. Define trigger conditions
2. Set up agent sequences
3. Configure approval gates
4. Monitor automated tasks

### Security Features
- **SSO**: Single sign-on with your identity provider
- **RBAC**: Role-based access controls
- **Audit Logs**: Comprehensive activity tracking
- **Data Encryption**: End-to-end encryption for sensitive data

## Best Practices

### Task Description Guidelines
- Be specific about desired output format
- Include relevant context and constraints
- Specify target audience if applicable
- Provide examples when possible

### Agent Selection Tips
- Match task complexity to agent tier
- Consider cost vs. quality trade-offs
- Use specialized agents for domain-specific tasks
- Experiment with different agents for optimization

### Performance Optimization
- Batch similar tasks together
- Use templates for recurring task types
- Monitor agent performance metrics
- Optimize task descriptions based on results

---

## Quick Reference

### Keyboard Shortcuts
- `Ctrl+N`: Create new task
- `Ctrl+D`: Dashboard
- `Ctrl+A`: Agents view
- `Ctrl+T`: Tasks view
- `Ctrl+B`: Billing
- `Ctrl+/`: Help

### Status Indicators
- 🟢 **Available**: Agent ready for tasks
- 🟡 **Busy**: Agent currently working
- 🔴 **Offline**: Agent unavailable
- ⚪ **Maintenance**: Agent under maintenance

### Task Priority Levels
- 🔴 **Critical**: Highest priority, immediate processing
- 🟡 **High**: Priority processing within 1 hour
- 🟢 **Normal**: Standard processing queue
- ⚪ **Low**: Background processing when resources available

---

For the latest updates and detailed API documentation, visit [docs.aicrm.com](https://docs.aicrm.com)