# 🏥 AI-CRM Production Monitoring

Comprehensive monitoring and health check system for AI-CRM production deployments.

## Overview

The AI-CRM monitoring system provides:
- **Real-time Health Checks**: Continuous monitoring of all system components
- **Performance Metrics**: System resource tracking and performance analysis
- **Business Intelligence**: Task completion rates, agent utilization, user engagement
- **Production Dashboard**: Web-based real-time monitoring interface
- **Alert Management**: Multi-channel alerting (email, Slack, webhooks)
- **Historical Tracking**: Time-series data collection and trend analysis

## Quick Start

### 1. Automated Setup
```bash
# Run automated setup script
./setup-monitoring.sh

# Quick system health check
./quick-health-check.sh
```

### 2. Manual Setup
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Start health monitoring (background)
python3 health-checks.py &

# Start production dashboard
python3 production-dashboard.py --port 9090 &

# Access dashboard
open http://localhost:9090/dashboard
```

### 3. Docker Deployment
```bash
# Build and start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Check logs
docker logs ai-crm-health-monitor
docker logs ai-crm-dashboard
```

## Components

### 1. Health Check System (`health-checks.py`)

**Comprehensive system monitoring with:**
- **Service Health**: API endpoints, database, PM Gateway status
- **System Metrics**: CPU, memory, disk usage monitoring
- **Performance Tracking**: Response times, error rates, throughput
- **Alert Generation**: Multi-channel alerts based on thresholds
- **Historical Data**: Time-series metrics collection

**Usage:**
```bash
# Continuous monitoring (production)
python3 health-checks.py

# Single health check
python3 health-checks.py --once

# Custom configuration
python3 health-checks.py --config custom-config.json
```

**Configuration** (`monitoring-config.json`):
```json
{
  "endpoints": {
    "backend": "http://localhost:8000/health",
    "frontend": "http://localhost:3000/health",
    "pm_gateway": "http://localhost:8000/pm/health"
  },
  "alert_thresholds": {
    "response_time_ms": 2000,
    "cpu_usage_percent": 80,
    "memory_usage_percent": 85,
    "disk_usage_percent": 90
  },
  "alert_channels": {
    "email": {"enabled": false},
    "slack": {"enabled": false}, 
    "webhook": {"enabled": false},
    "console": {"enabled": true}
  }
}
```

### 2. Production Dashboard (`production-dashboard.py`)

**Real-time web-based monitoring dashboard:**
- **System Overview**: Health status, resource utilization, uptime
- **Service Status**: Individual component health and performance
- **Agent Performance**: AI agent response times, success rates, utilization
- **Business Metrics**: Task completion rates, user engagement, feature usage
- **Visual Analytics**: Charts and graphs for trend analysis
- **Auto-refresh**: Real-time updates every 30 seconds

**Usage:**
```bash
# Start dashboard server
python3 production-dashboard.py --port 9090

# Generate static HTML dashboard
python3 production-dashboard.py --generate-file dashboard.html

# Custom configuration
python3 production-dashboard.py --config custom-config.json --port 8080
```

**Dashboard Access:**
- **Main Dashboard**: http://localhost:9090/dashboard
- **Metrics API**: http://localhost:9090/api/metrics

### 3. Monitoring Configuration

**Core Configuration File** (`monitoring-config.json`):
```json
{
  "endpoints": {
    "backend": "http://localhost:8000/health",
    "frontend": "http://localhost:3000/health",
    "pm_gateway": "http://localhost:8000/pm/health",
    "database": "http://localhost:8000/db/health"
  },
  "alert_thresholds": {
    "response_time_ms": 2000,
    "cpu_usage_percent": 80,
    "memory_usage_percent": 85,
    "disk_usage_percent": 90,
    "error_rate_percent": 5,
    "task_processing_time_ms": 5000,
    "agent_response_time_ms": 3000
  },
  "check_intervals": {
    "health_checks": 30,
    "system_metrics": 60,
    "detailed_analysis": 300,
    "agent_performance": 120
  },
  "alert_channels": {
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "recipients": ["ops@company.com"]
    },
    "slack": {
      "enabled": false,
      "webhook_url": "https://hooks.slack.com/...",
      "channel": "#ai-crm-alerts"
    },
    "console": {
      "enabled": true,
      "log_level": "INFO"
    }
  }
}
```

## Monitoring Metrics

### System Health Metrics
- **CPU Usage**: Processor utilization percentage
- **Memory Usage**: RAM utilization and availability
- **Disk Usage**: Storage space utilization
- **Network**: Connection count and bandwidth
- **Uptime**: System availability and restart frequency

### Application Performance Metrics  
- **Response Times**: API endpoint response latencies
- **Error Rates**: HTTP error percentages and patterns
- **Throughput**: Requests per second and concurrent users
- **Task Processing**: PM Gateway analysis times
- **Agent Performance**: AI agent response times and success rates

### Business Intelligence Metrics
- **Task Creation Rate**: New tasks per day/hour
- **Completion Rate**: Task completion percentage
- **Agent Utilization**: Usage distribution across 59 agents
- **User Engagement**: Active users and feature adoption
- **PM Gateway Usage**: Intelligence feature adoption rates

## Alert Management

### Alert Levels
- **HEALTHY**: All systems operating normally
- **WARNING**: Performance degradation or minor issues
- **CRITICAL**: Service failures or severe performance issues
- **UNKNOWN**: Unable to determine system status

### Alert Channels
1. **Console Alerts**: Real-time console logging
2. **Email Alerts**: SMTP-based email notifications
3. **Slack Integration**: Slack channel notifications
4. **Webhook Alerts**: Custom HTTP webhook integrations
5. **Dashboard Alerts**: Web dashboard visual alerts

### Alert Thresholds
```json
{
  "response_time_ms": 2000,        // API response time limit
  "cpu_usage_percent": 80,         // CPU usage warning threshold
  "memory_usage_percent": 85,      // Memory usage warning threshold  
  "disk_usage_percent": 90,        // Disk space warning threshold
  "error_rate_percent": 5,         // Error rate alert threshold
  "task_processing_time_ms": 5000, // PM Gateway processing limit
  "agent_response_time_ms": 3000   // AI agent response time limit
}
```

## Production Deployment

### Systemd Services (Linux)
```bash
# Install as system services
sudo ./setup-monitoring.sh

# Service management
sudo systemctl start ai-crm-health-monitor
sudo systemctl start ai-crm-dashboard
sudo systemctl enable ai-crm-health-monitor
sudo systemctl enable ai-crm-dashboard

# View logs
journalctl -u ai-crm-health-monitor -f
journalctl -u ai-crm-dashboard -f
```

### Docker Deployment
```bash
# Production deployment with Docker
docker-compose -f docker-compose.monitoring.yml up -d

# Scale monitoring
docker-compose -f docker-compose.monitoring.yml up -d --scale health-monitor=2

# View logs
docker logs -f ai-crm-health-monitor
docker logs -f ai-crm-dashboard
```

### Cloud Deployment
The monitoring system integrates with:
- **AWS CloudWatch**: Metrics and log streaming
- **GCP Operations Suite**: Monitoring and alerting
- **Azure Monitor**: Application insights and metrics
- **Prometheus/Grafana**: Advanced metrics and visualization

## Utility Scripts

### Quick Health Check (`quick-health-check.sh`)
```bash
# Basic system health verification
./quick-health-check.sh

# Output:
# ✅ Backend API: HEALTHY
# ✅ Frontend UI: HEALTHY  
# ✅ Dashboard: HEALTHY
# 📊 CPU Usage: 23%
# 📊 Memory: 4.2G/16G
# 📊 Disk: 45% used
```

### Monitoring Status (`monitoring-status.sh`)
```bash
# Check monitoring service status
./monitoring-status.sh

# Output:
# ✅ Health Monitor: RUNNING
# ✅ Production Dashboard: RUNNING
#    Access: http://localhost:9090/dashboard
# 📄 Health Monitor Log: 1247 lines
```

## Troubleshooting

### Common Issues

**1. Monitoring Services Not Starting**
```bash
# Check Python version and dependencies
python3 --version
pip3 list | grep -E "(aiohttp|psutil|requests)"

# Verify configuration
python3 -c "import json; print(json.load(open('monitoring-config.json')))"
```

**2. Dashboard Not Accessible**
```bash
# Check if dashboard is running
ps aux | grep production-dashboard.py

# Check port availability
netstat -tulpn | grep 9090

# Start dashboard manually
python3 production-dashboard.py --port 9090
```

**3. Health Checks Failing**
```bash
# Test individual endpoints
curl -f http://localhost:8000/health
curl -f http://localhost:3000/health

# Check health monitor logs
tail -f logs/health-monitor.log

# Run single health check with debug
python3 health-checks.py --once --verbose
```

**4. Alert Configuration Issues**
```bash
# Test email configuration
python3 -c "
import json
config = json.load(open('monitoring-config.json'))
print('Email config:', config['alert_channels']['email'])
"

# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test alert from AI-CRM monitoring"}' \
  YOUR_SLACK_WEBHOOK_URL
```

### Performance Optimization

**1. Reduce Check Frequency**
```json
{
  "check_intervals": {
    "health_checks": 60,     // Increase from 30 seconds
    "system_metrics": 120,   // Increase from 60 seconds
    "detailed_analysis": 600 // Increase from 300 seconds
  }
}
```

**2. Optimize Resource Usage**
```bash
# Limit monitoring resource usage
ulimit -v 1048576  # Limit virtual memory to 1GB
nice -n 10 python3 health-checks.py  # Lower process priority
```

**3. Data Retention Management**
```json
{
  "retention_days": 3,  // Reduce from 7 days for storage optimization
  "cleanup_interval": 3600  // Clean old data every hour
}
```

## Security Considerations

### Access Control
- Dashboard should be behind authentication in production
- API endpoints should use proper authentication tokens
- Webhook URLs should include authentication tokens

### Network Security
- Monitor services should run on internal networks only
- Use HTTPS for external monitoring endpoints
- Implement rate limiting for dashboard access

### Data Privacy
- Avoid logging sensitive data in health checks
- Implement data encryption for metrics storage
- Regular audit of monitoring logs and data retention

## Integration Examples

### Slack Integration
```python
# slack-alerts.py
import aiohttp
import json

async def send_slack_alert(webhook_url, message, channel="#ai-crm-alerts"):
    payload = {
        "text": message,
        "channel": channel,
        "username": "AI-CRM Monitor",
        "icon_emoji": ":robot_face:"
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=payload)
```

### Email Alerts
```python
# email-alerts.py  
import smtplib
from email.mime.text import MIMEText

def send_email_alert(smtp_config, subject, body, recipients):
    msg = MIMEText(body)
    msg['Subject'] = f"AI-CRM Alert: {subject}"
    msg['From'] = smtp_config['username']
    msg['To'] = ', '.join(recipients)
    
    with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
        server.starttls()
        server.login(smtp_config['username'], smtp_config['password'])
        server.send_message(msg)
```

### Custom Webhooks
```python
# webhook-integration.py
import aiohttp

async def send_webhook_alert(webhook_url, alert_data, headers=None):
    headers = headers or {'Content-Type': 'application/json'}
    
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=alert_data, headers=headers)
```

## Monitoring Best Practices

### 1. Baseline Establishment
- Monitor systems for 1-2 weeks to establish performance baselines
- Adjust alert thresholds based on normal operating patterns
- Document expected performance ranges for different load levels

### 2. Alert Fatigue Prevention
- Use progressive alert escalation (warning → critical)
- Implement alert suppression during maintenance windows
- Group related alerts to avoid notification spam

### 3. Regular Maintenance
- Review and update monitoring configurations monthly
- Clean up old monitoring data regularly
- Update alert contact information and escalation procedures

### 4. Performance Monitoring
- Track key business metrics alongside technical metrics
- Monitor user experience metrics (page load times, task completion rates)
- Implement synthetic transaction monitoring for critical workflows

---

## Support and Documentation

### Additional Resources
- **Health Check API**: Detailed endpoint documentation
- **Dashboard Customization**: Guide for custom dashboard development
- **Alert Integration**: Examples for popular monitoring platforms
- **Performance Tuning**: Optimization guide for high-load environments

### Getting Help
1. **Check Logs**: Review health-monitor.log for detailed error information
2. **Configuration Validation**: Verify monitoring-config.json syntax and values
3. **Network Connectivity**: Test endpoint accessibility from monitoring system
4. **Resource Availability**: Ensure adequate system resources for monitoring overhead

---

*AI-CRM Production Monitoring v2.0.0*  
*Built for enterprise-grade reliability and comprehensive system visibility*