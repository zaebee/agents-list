# 🐳 Docker Stack Setup Guide

## Quick Start

### 1. Environment Setup

Before starting the Docker stack, you need to configure your environment variables with your actual API keys.

#### Option A: Use Demo Configuration (Testing)
```bash
# Copy the Docker environment template
cp .env.docker .env.local

# Start the stack with demo keys (limited functionality)
docker-compose -f docker-compose.phase2a.yml up --build
```

#### Option B: Production Setup (Recommended)
```bash
# Copy the production template
cp .env.production .env.local

# Edit the file with your real API keys
nano .env.local  # or use your preferred editor
```

### 2. Required API Keys

Update `.env.local` with your actual API keys:

```bash
# AI Provider Keys (at least one required for full functionality)
ANTHROPIC_API_KEY=sk-ant-api03-your_actual_key_here
OPENAI_API_KEY=sk-your_actual_openai_key_here
MISTRAL_API_KEY=your_actual_mistral_key_here

# Optional: Billing (for subscription features)
STRIPE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Security (generate secure random strings)
SECRET_KEY=your_super_secure_secret_key_256_bits
JWT_SECRET_KEY=your_super_secure_jwt_secret_256_bits
```

### 3. Start the Docker Stack

```bash
# Basic services (app, database, redis)
docker-compose -f docker-compose.phase2a.yml up --build

# With monitoring (includes Prometheus & Grafana)
docker-compose -f docker-compose.phase2a.yml --profile monitoring up --build

# With backups (includes automated backup service)
docker-compose -f docker-compose.phase2a.yml --profile backup up --build

# All services
docker-compose -f docker-compose.phase2a.yml --profile monitoring --profile backup up --build
```

## Service Access Points

Once the stack is running:

- **Main Application**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **PostgreSQL**: localhost:5432 (aicrm_user/aicrm123)
- **Redis**: localhost:6379
- **Grafana (monitoring profile)**: http://localhost:3000 (admin/admin123)
- **Prometheus (monitoring profile)**: http://localhost:9090

## Environment Files Explained

### `.env.docker` (Template)
- Contains placeholder values for all configuration
- Safe to commit to version control (no real secrets)
- Used by Docker Compose for environment variable loading

### `.env.production` (Template)
- Production-ready configuration template
- Contains detailed comments for each setting
- Should be customized for your deployment

### `.env.local` (Your Configuration)
- Your actual configuration with real API keys
- **NEVER commit this file to version control**
- Add to `.gitignore` if not already present

## Security Best Practices

### 1. API Key Management
```bash
# Generate secure random keys
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY

# Store API keys securely
# - Use environment variables in production
# - Use secret management systems (AWS Secrets Manager, etc.)
# - Never hardcode in configuration files
```

### 2. Database Security
```bash
# Change default database password
DATABASE_PASSWORD=your_secure_random_password_here

# In production, use managed database services
DATABASE_URL=postgresql://user:pass@managed-db-host:5432/db
```

### 3. Environment Isolation
```bash
# Development
ENVIRONMENT=development
DEBUG=true

# Production  
ENVIRONMENT=production
DEBUG=false
FORCE_HTTPS=true
```

## Monitoring Stack

Enable monitoring to get insights into your system:

```bash
# Start with monitoring
docker-compose -f docker-compose.phase2a.yml --profile monitoring up -d

# Access Grafana
open http://localhost:3000
# Login: admin/admin123

# Access Prometheus  
open http://localhost:9090
```

## Backup System

Enable automated backups:

```bash
# Start with backups
docker-compose -f docker-compose.phase2a.yml --profile backup up -d

# Manual backup
docker exec aicrm_backup /backup.sh

# Check backup files
ls -la ./backups/
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
```bash
# Check what's using ports
netstat -tulpn | grep :8080
netstat -tulpn | grep :5432

# Change ports in docker-compose.phase2a.yml if needed
```

2. **Permission Issues**
```bash
# Fix log/data directory permissions
sudo chown -R $USER:$USER ./logs ./data
```

3. **Database Connection Issues**
```bash
# Check PostgreSQL container logs
docker logs aicrm_postgres

# Connect to database manually
docker exec -it aicrm_postgres psql -U aicrm_user -d aicrm_db
```

4. **API Key Issues**
```bash
# Check environment variables are loaded
docker exec aicrm_app env | grep ANTHROPIC_API_KEY

# Test API connectivity
docker exec aicrm_app curl -s "https://api.anthropic.com/v1/messages" \
  -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json"
```

### Health Checks

```bash
# Check all services
docker-compose -f docker-compose.phase2a.yml ps

# Check specific service health
docker inspect aicrm_app | grep -A 10 "Health"

# Application health endpoint
curl http://localhost:8080/health
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.phase2a.yml logs

# Follow logs for specific service
docker-compose -f docker-compose.phase2a.yml logs -f aicrm-app

# Check application logs
tail -f ./logs/app.log
```

## Production Deployment

For production deployment, see:
- [Production Deployment Guide](DEPLOYMENT_GUIDE.md)
- [AWS Terraform Setup](terraform/README.md)
- [Security Checklist](SECURITY_CHECKLIST.md)

## Cleanup

```bash
# Stop and remove containers
docker-compose -f docker-compose.phase2a.yml down

# Remove volumes (WARNING: deletes all data)
docker-compose -f docker-compose.phase2a.yml down -v

# Remove images
docker-compose -f docker-compose.phase2a.yml down --rmi all
```