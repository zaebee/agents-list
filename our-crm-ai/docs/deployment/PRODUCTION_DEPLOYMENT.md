# 🎯 AI Project Manager - Production Deployment Guide

## Overview

This guide covers deploying the AI Project Manager to production with enhanced security, scalability, and monitoring. The system now includes:

- **Modern Flask Application** with JWT authentication and RBAC
- **PostgreSQL Database** with connection pooling and migrations
- **Real AI Agent Integration** with multiple providers
- **Production Infrastructure** with Docker, Nginx, and monitoring
- **Comprehensive Security** with rate limiting and input validation

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 15+ for production database
- Domain name and SSL certificates
- API keys for AI providers (Anthropic, OpenAI)

### 1. Environment Setup

Copy and configure environment variables:

```bash
cp .env.production .env
```

**Critical: Update these values in `.env`:**

```bash
# Database (use strong passwords)
DATABASE_PASSWORD=your_secure_database_password

# Application Security
SECRET_KEY=generate_a_secure_random_key_here
ALLOWED_ORIGINS=https://yourdomain.com

# AI Providers
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Monitoring
GRAFANA_PASSWORD=secure_grafana_password
REDIS_PASSWORD=secure_redis_password
```

### 2. SSL Certificate Setup

For development/testing with self-signed certificates:

```bash
mkdir -p nginx/ssl
openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes
```

For production, use Let's Encrypt or your certificate provider.

### 3. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose -f docker-compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f aipm_app
```

### 4. Initialize Database

```bash
# Run database migrations
docker exec aipm_application python database_migrations.py

# Verify database health
docker exec aipm_application python postgres_manager.py
```

### 5. Verify Deployment

- **Application**: https://your-domain.com
- **Health Check**: https://your-domain.com/health
- **Metrics**: https://your-domain.com/metrics (restricted)
- **Grafana**: http://your-domain.com:3000 (admin/[GRAFANA_PASSWORD])

## 📋 Production Checklist

### Security

- [ ] Updated all default passwords in `.env`
- [ ] Configured real SSL certificates
- [ ] Set up proper firewall rules
- [ ] Configured CORS origins for your domain
- [ ] Set up backup encryption keys
- [ ] Reviewed and updated security headers

### Database

- [ ] PostgreSQL running with secure passwords
- [ ] Database backups configured and tested
- [ ] Connection pooling optimized for load
- [ ] Database monitoring set up
- [ ] Migrations completed successfully

### Monitoring

- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards configured
- [ ] Health checks responding correctly
- [ ] Log aggregation working
- [ ] Alert notifications configured

### Performance

- [ ] Load testing completed
- [ ] Auto-scaling policies configured
- [ ] CDN configured for static assets
- [ ] Database indexes optimized
- [ ] Connection limits tuned

## 🔧 Configuration Details

### Application Architecture

```
Internet → Nginx (SSL/Load Balancer) → Flask App → PostgreSQL
                                    ↓
                              Redis (Sessions/Cache)
                                    ↓
                              AI Agents (Anthropic/OpenAI)
```

### Key Components

1. **production_dashboard.py** - Modern Flask app with authentication
2. **postgres_manager.py** - Database operations with connection pooling
3. **agent_integration_framework.py** - Real AI agent execution
4. **production_monitoring.py** - Comprehensive monitoring system

### Default Users

The system creates a default admin user:
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ Change this password immediately after first login!**

### API Endpoints

- `POST /api/auth/login` - User authentication
- `GET /api/auth/verify` - Token verification
- `GET /api/executive-dashboard` - Dashboard data
- `POST /api/users` - Create user (admin only)
- `GET /api/health` - Health check
- `GET /metrics` - Prometheus metrics

## 🔒 Security Features

### Authentication & Authorization

- JWT-based authentication with configurable expiration
- Role-based access control (admin, pm, stakeholder, viewer)
- Account lockout after failed login attempts
- Session management with Redis

### Security Headers

- HSTS for HTTPS enforcement
- XSS protection
- Content Security Policy
- Frame options protection
- CSRF protection

### Rate Limiting

- API endpoints: 10 requests/second
- Authentication: 1 request/second
- Configurable burst limits

### Input Validation

- SQL injection prevention
- XSS sanitization
- Request size limits
- File upload restrictions

## 📊 Monitoring & Observability

### Metrics Collection

The system collects comprehensive metrics:

- **HTTP Requests**: Count, duration, status codes
- **Database**: Query performance, connection pool stats
- **AI Agents**: Task execution, costs, quality scores
- **Business**: Project metrics, ROI calculations
- **System**: CPU, memory, disk usage

### Health Checks

Multiple health check endpoints:

- `/health` - Simple up/down status
- `/health/detailed` - Component-level health
- Individual component health checks

### Dashboards

Grafana dashboards for:

- Application performance monitoring
- Database performance
- AI agent execution metrics
- Business intelligence metrics
- Infrastructure monitoring

## 🔄 Backup & Recovery

### Automated Backups

Daily PostgreSQL backups at 2 AM:

```bash
# Manual backup
docker exec aipm_postgres pg_dump -U aipm_user aipm_db > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i aipm_postgres psql -U aipm_user aipm_db < backup_20240101.sql
```

### Backup Strategy

- **Daily**: Full database backup
- **Weekly**: System configuration backup
- **Monthly**: Complete system image
- **Retention**: 30 days local, 90 days offsite

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use external load balancer (AWS ALB, Cloudflare)
2. **Multiple App Instances**: Scale Flask app containers
3. **Database**: PostgreSQL read replicas
4. **Redis Cluster**: For session storage scaling

### Vertical Scaling

1. **Memory**: Increase for better database caching
2. **CPU**: More cores for AI agent processing
3. **Storage**: Fast SSD for database performance

### Auto-scaling

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aipm-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: aipm
        image: aipm:production
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
```

## 🚨 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check database status
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

**2. AI Agent Failures**
```bash
# Check API keys
docker exec aipm_application python agent_integration_framework.py

# View agent logs
docker-compose logs aipm_app | grep agent
```

**3. Authentication Issues**
```bash
# Reset admin password
docker exec -it aipm_postgres psql -U aipm_user -d aipm_db
UPDATE users SET password_hash = 'new_hash' WHERE username = 'admin';
```

**4. Performance Issues**
```bash
# Check system resources
docker stats

# Check database performance
docker exec aipm_application python postgres_manager.py
```

### Log Locations

- **Application**: `/app/logs/` inside container
- **Nginx**: `/var/log/nginx/`
- **PostgreSQL**: Docker logs
- **System**: Collected by Promtail

## 🔗 Production URLs

After deployment, access these services:

- **Main Application**: https://yourdomain.com
- **API Documentation**: https://yourdomain.com/api/
- **Health Status**: https://yourdomain.com/health/detailed
- **Prometheus**: http://yourdomain.com:9090
- **Grafana**: http://yourdomain.com:3000

## 📞 Support

### Health Check Commands

```bash
# Overall system health
curl -f https://yourdomain.com/health

# Detailed component health
curl -s https://yourdomain.com/health/detailed | jq

# Database health
docker exec aipm_application python -c "
import asyncio
from postgres_manager import db_manager
print(asyncio.run(db_manager.health_check()))
"

# Agent health
docker exec aipm_application python -c "
import asyncio
from agent_integration_framework import agent_framework
health = asyncio.run(agent_framework.health_check_all_agents())
print(f'Healthy agents: {sum(health.values())}/{len(health)}')
"
```

### Performance Monitoring

```bash
# View real-time metrics
watch -n 1 'curl -s localhost:5001/metrics | grep aipm_http_requests_total'

# Database connection pool status
docker exec aipm_application python -c "
import asyncio
from postgres_manager import db_manager
asyncio.run(db_manager.initialize())
print(f'Pool size: {db_manager.pool.get_size()}/{db_manager.pool.get_max_size()}')
"
```

## 🎉 Success Criteria

Your deployment is successful when:

- [ ] All health checks return "healthy"
- [ ] Authentication works with JWT tokens
- [ ] AI agents execute tasks successfully
- [ ] Database queries complete under 100ms
- [ ] Monitoring dashboards show data
- [ ] SSL certificates are valid
- [ ] Backup processes complete successfully

**Congratulations! Your AI Project Manager is now production-ready! 🚀**