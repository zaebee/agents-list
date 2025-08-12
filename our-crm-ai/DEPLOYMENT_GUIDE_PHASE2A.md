# AI-CRM Phase 2A Deployment Guide

Complete deployment guide for AI-CRM Phase 2A production system with billing infrastructure, multi-provider AI agents, and comprehensive analytics.

## Overview

This guide covers deployment of the complete AI-CRM system including:
- Multi-provider AI agent integration (Anthropic, OpenAI, Mistral)
- Tiered pricing and billing system (Stripe integration)
- Real-time analytics dashboard
- Production-ready infrastructure (Docker, AWS/GCP)
- CI/CD pipeline with automated testing

## Prerequisites

### Required Software
- Docker & Docker Compose v2+
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Git
- AWS CLI or GCP SDK (for cloud deployment)

### Required API Keys
- **Anthropic API Key**: For Claude agents
- **OpenAI API Key**: For GPT agents  
- **Mistral API Key**: For Mistral agents
- **Stripe Secret Key**: For billing (production)
- **JWT Secret Key**: For authentication

### Infrastructure Requirements
- **Minimum**: 4 CPU cores, 8GB RAM, 50GB storage
- **Recommended**: 8 CPU cores, 16GB RAM, 100GB storage
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Load Balancer**: Nginx or AWS ALB

## Quick Start (Docker)

### 1. Clone Repository
```bash
git clone https://github.com/your-org/ai-crm.git
cd ai-crm
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://aicrm_user:your_password@postgres:5432/aicrm_db

# AI Providers (at least one required)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
MISTRAL_API_KEY=your_mistral_key

# Billing
STRIPE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Security
JWT_SECRET_KEY=your_jwt_secret_key
```

### 3. Deploy with Docker Compose
```bash
# Production deployment
./scripts/deploy-phase2a.sh

# Or manually:
docker compose -f docker-compose.phase2a.yml up -d
```

### 4. Verify Deployment
```bash
# Check all services are running
docker compose -f docker-compose.phase2a.yml ps

# Test API health
curl http://localhost/health

# Test billing endpoints
curl http://localhost/api/billing/pricing
```

## Manual Deployment

### Backend Setup

1. **Create Python Environment**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Database Setup**
```bash
# PostgreSQL setup
sudo apt-get install postgresql-15
sudo -u postgres createdb aicrm_db
sudo -u postgres createuser aicrm_user

# Set password
sudo -u postgres psql -c "ALTER USER aicrm_user PASSWORD 'your_password';"

# Run migrations
python database_migrations.py
```

3. **Redis Setup**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

4. **Start Backend**
```bash
# Development
python api.py

# Production with Gunicorn
gunicorn api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd frontend
npm ci
```

2. **Build Production Assets**
```bash
npm run build
```

3. **Serve with Nginx**
```bash
sudo cp build/* /var/www/html/
# Configure nginx (see nginx configuration below)
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }
    
    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Cloud Deployment (AWS)

### Prerequisites
```bash
# Install Terraform
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# Configure AWS CLI
aws configure
```

### Deploy Infrastructure
```bash
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="environments/production.tfvars"

# Deploy infrastructure
terraform apply -var-file="environments/production.tfvars"
```

### Configure Secrets
```bash
# Add API keys to AWS Secrets Manager
aws secretsmanager put-secret-value \
  --secret-id aicrm-production-anthropic-api-key \
  --secret-string "your_anthropic_key"

aws secretsmanager put-secret-value \
  --secret-id aicrm-production-stripe-secret-key \
  --secret-string "your_stripe_key"

aws secretsmanager put-secret-value \
  --secret-id aicrm-production-jwt-secret-key \
  --secret-string "your_jwt_secret"
```

### Deploy Application
```bash
# Build and push Docker image
docker build -f Dockerfile.production -t your-registry/aicrm:latest .
docker push your-registry/aicrm:latest

# Update ECS service
aws ecs update-service \
  --cluster aicrm-production-cluster \
  --service aicrm-production-service \
  --force-new-deployment
```

## CI/CD Pipeline

### GitHub Actions Setup

1. **Configure Secrets**
Add these secrets to your GitHub repository:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY` 
- `MISTRAL_API_KEY`
- `STRIPE_SECRET_KEY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

2. **Workflow Configuration**
The CI/CD pipeline in `.github/workflows/ci-cd.yml` includes:
- Frontend testing and building
- Backend testing with PostgreSQL
- Security scanning with Trivy
- Docker image building and publishing
- Automated deployment to staging/production

3. **Deployment Process**
- **Push to `develop`**: Deploys to staging
- **Create release**: Deploys to production
- **Pull requests**: Run tests and security scans

## Monitoring and Observability

### Application Monitoring
```bash
# Enable monitoring stack
ENABLE_MONITORING=true docker compose -f docker-compose.phase2a.yml --profile monitoring up -d
```

Services included:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert notifications

### Health Checks
- **Application**: `GET /health`
- **API**: `GET /api/health`
- **Database**: Connection testing
- **Redis**: Connection testing
- **External APIs**: Provider health checks

### Logging
- **Application logs**: `/app/logs/`
- **Access logs**: Nginx/ALB logs
- **Error logs**: Centralized in CloudWatch/Grafana

## Security Configuration

### SSL/TLS Setup
```bash
# Using Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Manual certificate
sudo nginx -s reload
```

### Firewall Configuration
```bash
# UFW setup
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Security Headers
```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
```

## Backup and Recovery

### Database Backup
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker compose -f docker-compose.phase2a.yml exec -T postgres \
  pg_dump -U aicrm_user aicrm_db > "$BACKUP_DIR/db_backup_$DATE.sql"

# Compress and upload to S3
gzip "$BACKUP_DIR/db_backup_$DATE.sql"
aws s3 cp "$BACKUP_DIR/db_backup_$DATE.sql.gz" s3://your-backup-bucket/
```

### Recovery Process
```bash
# Restore from backup
gunzip db_backup_20241201_120000.sql.gz
docker compose -f docker-compose.phase2a.yml exec -T postgres \
  psql -U aicrm_user aicrm_db < db_backup_20241201_120000.sql
```

## Performance Optimization

### Database Tuning
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

### Redis Configuration
```bash
# Redis optimization in redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Application Scaling
```bash
# Scale workers
docker compose -f docker-compose.phase2a.yml up -d --scale celery-worker=4

# Scale web application
docker compose -f docker-compose.phase2a.yml up -d --scale aicrm-app=3
```

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
docker compose -f docker-compose.phase2a.yml logs aicrm-app

# Check disk space
df -h

# Check memory usage
free -h
```

#### Database Connection Issues
```bash
# Test database connectivity
docker compose -f docker-compose.phase2a.yml exec postgres pg_isready -U aicrm_user

# Check database logs
docker compose -f docker-compose.phase2a.yml logs postgres
```

#### High Memory Usage
```bash
# Monitor container resources
docker stats

# Check for memory leaks in application logs
grep -i "memory\|oom" logs/*.log
```

#### API Rate Limits
```bash
# Check rate limit headers
curl -I -H "Authorization: Bearer $TOKEN" http://localhost/api/agents

# Monitor rate limit usage
grep "rate_limit" logs/access.log
```

### Performance Issues
1. **Slow API responses**: Check database query performance
2. **High CPU usage**: Scale application containers
3. **Memory leaks**: Review application logs and restart services
4. **Database locks**: Monitor active queries and connections

### Recovery Procedures
1. **Service failure**: Restart individual containers
2. **Database corruption**: Restore from backup
3. **Full system failure**: Redeploy from infrastructure as code
4. **Data loss**: Restore from point-in-time backup

## Maintenance

### Regular Tasks
- **Daily**: Check system health and logs
- **Weekly**: Review performance metrics and usage
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Performance optimization and capacity planning

### Update Process
```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt
cd frontend && npm update

# Rebuild and deploy
docker compose -f docker-compose.phase2a.yml build
docker compose -f docker-compose.phase2a.yml up -d
```

### Scaling Guidelines
- **CPU > 80%**: Scale horizontally (more containers)
- **Memory > 85%**: Scale vertically (more RAM)
- **Disk > 80%**: Add storage or archive old data
- **Network > 70%**: Optimize queries or add CDN

## Support and Resources

### Documentation
- **API Docs**: `/docs` endpoint
- **User Guide**: `USER_GUIDE.md`
- **Architecture**: `ARCHITECTURE.md`

### Getting Help
- **Issues**: Create GitHub issue
- **Email**: support@aicrm.com
- **Status**: status.aicrm.com
- **Community**: community.aicrm.com

### Contributing
1. Fork the repository
2. Create feature branch
3. Submit pull request
4. Ensure tests pass
5. Update documentation

---

This deployment guide provides comprehensive coverage for production deployment of AI-CRM Phase 2A. For specific questions or issues, please refer to the troubleshooting section or contact support.