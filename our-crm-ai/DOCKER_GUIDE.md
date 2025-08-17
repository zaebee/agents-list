# 🐳 AI-CRM Docker Deployment Guide

## 📊 Current Status: Phase 2A Production Setup

**Recommended**: `docker-compose.phase2a.yml` ⭐ **CURRENT PRODUCTION**

---

## 🎯 Docker Configuration Files Overview

### ⭐ docker-compose.phase2a.yml - **CURRENT PRODUCTION**
**Status**: ✅ **ACTIVE** - Use this for all deployments

**Features:**
- 🏗️ **Production Architecture**: nginx + FastAPI + PostgreSQL + Redis
- 🔒 **Security Hardened**: Multi-stage builds, non-root users, health checks
- 📊 **Monitoring Ready**: Prometheus metrics, health endpoints
- 🚀 **Performance Optimized**: nginx reverse proxy, static file serving
- 🔧 **Environment Flexible**: Supports dev/staging/production configs

**Services:**
```yaml
services:
  aicrm-app:      # Main application (FastAPI + nginx)
  postgres:       # PostgreSQL database  
  redis:          # Redis cache/session store
  # Optional profiles:
  prometheus:     # Metrics collection
  grafana:        # Monitoring dashboard
```

**Usage:**
```bash
# Standard deployment
docker-compose -f docker-compose.phase2a.yml up -d

# With monitoring
docker-compose -f docker-compose.phase2a.yml --profile monitoring up -d

# Access points
# Frontend/API: http://localhost:8080
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

---

### 🚧 Other Docker Files (Legacy/Specialized)

#### docker-compose.dev.yml - Development
**Status**: 🔄 **LEGACY** - Use Phase 2A for all environments

**Original Purpose**: Development environment with hot-reload
**Current Recommendation**: Use `./start-dev.sh` for development instead

#### docker-compose.production.yml - Old Production  
**Status**: 🚫 **DEPRECATED** - Replaced by Phase 2A

**Issues**: 
- Missing security hardening
- No nginx reverse proxy
- Outdated dependency management

#### docker-compose.prod.yml - Alternative Production
**Status**: 🚫 **DEPRECATED** - Consolidated into Phase 2A

**Issues**:
- Duplicate functionality
- Inconsistent with current architecture

---

## 🚀 Deployment Instructions

### Quick Start (Recommended)
```bash
# 1. Clone and setup
git clone <repository>
cd our-crm-ai

# 2. Environment configuration
cp .env.docker .env
# Edit .env with your specific settings

# 3. Deploy Phase 2A
docker-compose -f docker-compose.phase2a.yml up -d

# 4. Verify deployment
curl http://localhost:8080/health
```

### Development Setup
```bash
# Use local development instead of Docker for development
uv sync
./start-dev.sh
# Access: http://localhost:5001
```

### Production Deployment
```bash
# Full production with monitoring
docker-compose -f docker-compose.phase2a.yml --profile monitoring up -d

# Verify all services
docker-compose -f docker-compose.phase2a.yml ps
docker-compose -f docker-compose.phase2a.yml logs -f aicrm-app
```

---

## 🔧 Configuration Management

### Environment Files

**Production**: `.env.docker` → `.env`
```bash
# Database
DATABASE_URL=postgresql://aicrm_user:your_password@postgres:5432/aicrm_db

# AI APIs
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Security
JWT_SECRET_KEY=your_jwt_secret_32_chars_minimum
ENCRYPTION_KEY=your_32_character_encryption_key

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
WORKERS=4
```

**Development**: Use `.env` for local development
```bash
# Database (SQLite for dev)
DATABASE_URL=sqlite:///./ai_crm.db

# Or PostgreSQL for dev
DATABASE_URL=postgresql://user:pass@localhost:5432/aicrm_dev

# Same API keys as production
```

### Port Configuration

**Phase 2A (Current)**:
- **Frontend/API**: `:8080` → nginx → FastAPI
- **Direct API**: `:5001` (development only)
- **Database**: `:5432` (PostgreSQL)
- **Redis**: `:6379`
- **Monitoring**: `:3000` (Grafana), `:9090` (Prometheus)

---

## 🔍 Health Checks & Monitoring

### Application Health
```bash
# Main health check
curl http://localhost:8080/health

# API documentation
curl http://localhost:8080/docs

# Metrics endpoint
curl http://localhost:8080/metrics
```

### Service Status
```bash
# Check all services
docker-compose -f docker-compose.phase2a.yml ps

# Service logs
docker-compose -f docker-compose.phase2a.yml logs -f aicrm-app
docker-compose -f docker-compose.phase2a.yml logs -f postgres
docker-compose -f docker-compose.phase2a.yml logs -f redis

# Container inspection
docker-compose -f docker-compose.phase2a.yml exec aicrm-app /app/healthcheck.sh
```

### Monitoring Dashboard
```bash
# Access Grafana (if monitoring profile enabled)
# http://localhost:3000
# Login: admin/admin123

# Prometheus metrics
# http://localhost:9090
```

---

## 🛠️ Maintenance & Operations

### Database Operations
```bash
# Database migrations
docker-compose -f docker-compose.phase2a.yml exec aicrm-app python database_migrations.py

# Database backup
docker-compose -f docker-compose.phase2a.yml exec postgres pg_dump -U aicrm_user aicrm_db > backup.sql

# Database restore
docker-compose -f docker-compose.phase2a.yml exec -T postgres psql -U aicrm_user aicrm_db < backup.sql
```

### Application Updates
```bash
# Pull latest images
docker-compose -f docker-compose.phase2a.yml pull

# Restart services
docker-compose -f docker-compose.phase2a.yml up -d --no-deps aicrm-app

# Rolling update (zero downtime)
docker-compose -f docker-compose.phase2a.yml up -d --force-recreate --no-deps aicrm-app
```

### Log Management
```bash
# Tail logs
docker-compose -f docker-compose.phase2a.yml logs -f

# Export logs
docker-compose -f docker-compose.phase2a.yml logs > application.log

# Log rotation (cleanup)
docker system prune -f
```

---

## 🔒 Security Considerations

### Production Security
- ✅ **Non-root containers**: All services run as non-root users
- ✅ **Network isolation**: Services communicate on internal network
- ✅ **Health checks**: Built-in container health monitoring
- ✅ **Security headers**: nginx configured with security headers
- ✅ **SSL ready**: nginx configured for SSL termination

### Environment Security
```bash
# Secure environment file permissions
chmod 600 .env

# Rotate secrets regularly
# Update JWT_SECRET_KEY, DATABASE_PASSWORD, etc.

# Monitor security
docker-compose -f docker-compose.phase2a.yml exec aicrm-app uv run safety scan
```

---

## 🚨 Troubleshooting

### Common Issues

**Port Conflicts**:
```bash
# Check if ports are in use
netstat -tulpn | grep -E ':(8080|5432|6379)'

# Change ports in docker-compose.phase2a.yml if needed
```

**Database Connection Issues**:
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.phase2a.yml logs postgres

# Test database connection
docker-compose -f docker-compose.phase2a.yml exec postgres psql -U aicrm_user -d aicrm_db -c "SELECT version();"
```

**Application Startup Issues**:
```bash
# Check application logs
docker-compose -f docker-compose.phase2a.yml logs aicrm-app

# Check health status
curl -f http://localhost:8080/health || echo "Health check failed"

# Restart specific service
docker-compose -f docker-compose.phase2a.yml restart aicrm-app
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor application metrics
curl http://localhost:8080/metrics

# Database performance
docker-compose -f docker-compose.phase2a.yml exec postgres psql -U aicrm_user -d aicrm_db -c "SELECT * FROM pg_stat_activity;"
```

---

## 📋 File Cleanup Recommendations

**Recommended Actions:**
```bash
# Remove deprecated files (after backup)
# mv docker-compose.dev.yml docker-compose.dev.yml.bak
# mv docker-compose.production.yml docker-compose.production.yml.bak  
# mv docker-compose.prod.yml docker-compose.prod.yml.bak

# Keep only current production setup
# docker-compose.phase2a.yml (current)
# .env.docker (template)
```

---

## 🎯 Summary

**Use This**: `docker-compose.phase2a.yml` ⭐  
**Environment**: `.env` (copied from `.env.docker`)  
**Access**: http://localhost:8080  
**Command**: `docker-compose -f docker-compose.phase2a.yml up -d`

**Phase 2A provides:**
✅ Production-ready architecture  
✅ Security hardening  
✅ Monitoring capabilities  
✅ Scalable infrastructure  
✅ Development/production parity

---

**Last Updated**: August 16, 2025  
**Docker Setup**: Phase 2A (Current Production)  
**Recommended For**: All deployment environments