# 🚀 Deployment Guide for End Users

This comprehensive guide helps you deploy the AI-CRM system in various environments, from simple single-server setups to enterprise-grade multi-cloud deployments. Whether you're a startup or an enterprise, this guide provides the deployment strategy that fits your needs.

## 📋 Table of Contents

1. [Deployment Overview](#-deployment-overview)
2. [Prerequisites & Requirements](#-prerequisites--requirements)
3. [Quick Start Deployment](#-quick-start-deployment)
4. [Single Server Production](#-single-server-production)
5. [Cloud Deployment Options](#-cloud-deployment-options)
6. [Enterprise Deployment](#-enterprise-deployment)
7. [Security & SSL Configuration](#-security--ssl-configuration)
8. [Monitoring & Maintenance](#-monitoring--maintenance)
9. [Backup & Recovery](#-backup--recovery)
10. [Troubleshooting](#-troubleshooting)

## 🎯 Deployment Overview

### Deployment Options

The AI-CRM system offers flexible deployment options to match your needs:

| Deployment Type | Best For | Complexity | Scalability | Cost |
|----------------|----------|------------|-------------|------|
| **Development** | Testing, prototyping | Low | Limited | Free |
| **Single Server** | Small teams, startups | Medium | Moderate | Low |
| **Cloud Managed** | Growing businesses | Medium | High | Medium |
| **Multi-Cloud** | Large organizations | High | Very High | High |
| **Enterprise** | Large enterprises | Very High | Unlimited | Premium |

### Architecture Components

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React Web App]
        B[Mobile App]
    end
    
    subgraph "API Layer"
        C[FastAPI Backend]
        D[Authentication Service]
        E[AI Agent Router]
    end
    
    subgraph "Data Layer"
        F[PostgreSQL Database]
        G[Redis Cache]
        H[File Storage]
    end
    
    subgraph "Infrastructure"
        I[Load Balancer]
        J[SSL Termination]
        K[Monitoring]
    end
    
    A --> I
    B --> I
    I --> C
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
    K --> C
```

## 🛠️ Prerequisites & Requirements

### System Requirements

#### Minimum Requirements (Development)
- **CPU**: 2 cores, 2.4 GHz
- **RAM**: 4GB
- **Storage**: 20GB available space
- **Network**: Stable internet connection (10 Mbps)
- **Operating System**: Linux, macOS, or Windows 10+

#### Recommended Requirements (Production)
- **CPU**: 4 cores, 3.0 GHz
- **RAM**: 8GB (16GB for high traffic)
- **Storage**: 100GB SSD
- **Network**: High-speed internet (100 Mbps+)
- **Operating System**: Ubuntu 20.04+ or CentOS 8+

#### Enterprise Requirements
- **CPU**: 8+ cores, 3.5 GHz
- **RAM**: 32GB+
- **Storage**: 500GB+ NVMe SSD
- **Network**: Dedicated bandwidth (1 Gbps+)
- **High Availability**: Load balancers, redundant systems

### Software Dependencies

#### Required Software
```bash
# Core dependencies
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- OpenSSL 1.1.1+

# Optional but recommended
- Nginx 1.20+ (for reverse proxy)
- PostgreSQL 13+ (for external database)
- Redis 6.0+ (for caching)
```

#### API Keys & Accounts
- **YouGile Account** - For task management backend
- **YouGile API Key** - Generated from your YouGile account
- **Domain Name** - For production deployment (optional)
- **SSL Certificate** - For HTTPS (can be auto-generated)

### Network & Security Requirements

#### Firewall Ports
```bash
# Required ports
80/tcp    - HTTP traffic (redirects to HTTPS)
443/tcp   - HTTPS traffic (main application)
22/tcp    - SSH access for management

# Optional ports  
8000/tcp  - Direct API access (development only)
3000/tcp  - Direct frontend access (development only)
5432/tcp  - PostgreSQL (if external database)
6379/tcp  - Redis (if external cache)
```

#### Domain & SSL Requirements
- **Domain name** for production deployment
- **SSL certificate** (Let's Encrypt recommended for free SSL)
- **DNS configuration** pointing to your server IP

## ⚡ Quick Start Deployment

### Option 1: One-Command Deployment

For immediate testing and development:

```bash
# Clone and start in development mode
git clone https://github.com/wshobson/agents.git
cd agents/web-ui

# Set your API key
echo "YOUGILE_API_KEY=your_api_key_here" > .env

# Start everything with one command
./start-dev.sh

# Access the application
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
```

### Option 2: Docker Compose Deployment

For more control over the deployment:

```bash
# 1. Clone the repository
git clone https://github.com/wshobson/agents.git
cd agents/web-ui

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# 3. Start services
docker-compose up -d

# 4. Check status
docker-compose ps
```

#### Environment Configuration (.env)
```bash
# API Configuration
YOUGILE_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here

# Database Configuration (optional - uses built-in SQLite by default)
DATABASE_URL=postgresql://user:password@localhost:5432/aicrm

# Application Settings
ENVIRONMENT=production
DEBUG=false
API_BASE_URL=http://localhost:8000

# Security Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
JWT_EXPIRE_MINUTES=30
```

### Verification Steps

After deployment, verify everything is working:

```bash
# 1. Check container status
docker-compose ps

# 2. Test API health
curl http://localhost:8000/health

# 3. Test frontend
curl -I http://localhost:3000

# 4. Check logs for errors
docker-compose logs frontend
docker-compose logs backend
```

## 🏢 Single Server Production

### Production Docker Deployment

For production on a single server with SSL and domain:

#### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application user
sudo useradd -m -s /bin/bash aicrm
sudo usermod -aG docker aicrm
```

#### 2. Application Setup
```bash
# Switch to application user
sudo su - aicrm

# Clone and setup
git clone https://github.com/wshobson/agents.git
cd agents/web-ui

# Configure for production
cp docker-compose.prod.yml docker-compose.yml
cp .env.example .env
```

#### 3. Production Configuration
```bash
# Edit production environment
nano .env
```

```bash
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Domain and SSL
DOMAIN=yourdomain.com
SSL_EMAIL=admin@yourdomain.com

# API Configuration  
YOUGILE_API_KEY=your_actual_api_key
SECRET_KEY=your_production_secret_key_here

# Database (production PostgreSQL recommended)
DATABASE_URL=postgresql://aicrm:secure_password@db:5432/aicrm_prod

# Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com
JWT_SECRET_KEY=another_secure_secret
BCRYPT_ROUNDS=12

# Performance
REDIS_URL=redis://redis:6379
WORKERS=4
```

#### 4. SSL Certificate Setup
```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx -y

# Generate certificate (requires domain pointing to your server)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be stored in /etc/letsencrypt/live/yourdomain.com/
```

#### 5. Production Deployment
```bash
# Start production stack
docker-compose up -d

# Verify deployment
docker-compose ps
curl -I https://yourdomain.com
```

### Nginx Reverse Proxy (Optional)

For additional performance and security:

```nginx
# /etc/nginx/sites-available/aicrm
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Frontend (React app)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
    }
}
```

## ☁️ Cloud Deployment Options

### AWS Deployment

#### AWS ECS with Fargate
```yaml
# docker-compose-aws.yml
version: '3.8'
services:
  frontend:
    image: aicrm/frontend:latest
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  backend:
    image: aicrm/backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - YOUGILE_API_KEY=${YOUGILE_API_KEY}
      - REDIS_URL=${REDIS_URL}
    deploy:
      resources:
        limits:
          memory: 1024M
        reservations:
          memory: 512M

  database:
    image: postgres:13
    environment:
      - POSTGRES_DB=aicrm
      - POSTGRES_USER=aicrm
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### AWS Infrastructure as Code (Terraform)
```hcl
# main.tf for AWS deployment
provider "aws" {
  region = var.aws_region
}

# VPC and Networking
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "aicrm-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "aicrm-public-${count.index + 1}"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "aicrm-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "aicrm-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false
}

# RDS Database
resource "aws_db_instance" "main" {
  identifier             = "aicrm-db"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  max_allocated_storage  = 100
  storage_type           = "gp2"
  storage_encrypted      = true

  db_name  = "aicrm"
  username = "aicrm"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = true
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "aicrm-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id         = "aicrm-redis"
  description                  = "Redis cluster for AI-CRM"
  node_type                    = "cache.t3.micro"
  port                         = 6379
  parameter_group_name         = "default.redis6.x"
  num_cache_clusters           = 2
  at_rest_encryption_enabled   = true
  transit_encryption_enabled   = true
  subnet_group_name           = aws_elasticache_subnet_group.main.name
  security_group_ids          = [aws_security_group.redis.id]
}
```

### Google Cloud Platform (GCP)

#### GKE Deployment
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aicrm-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aicrm-frontend
  template:
    metadata:
      labels:
        app: aicrm-frontend
    spec:
      containers:
      - name: frontend
        image: gcr.io/your-project/aicrm-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: "https://api.yourdomain.com"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aicrm-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aicrm-backend
  template:
    metadata:
      labels:
        app: aicrm-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/your-project/aicrm-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aicrm-secrets
              key: database-url
        - name: YOUGILE_API_KEY
          valueFrom:
            secretKeyRef:
              name: aicrm-secrets
              key: yougile-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Microsoft Azure

#### Azure Container Instances
```yaml
# azure-container-group.yaml
apiVersion: 2019-12-01
location: eastus
name: aicrm-container-group
properties:
  containers:
  - name: aicrm-frontend
    properties:
      image: aicrm/frontend:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 1
      ports:
      - protocol: TCP
        port: 3000
        
  - name: aicrm-backend
    properties:
      image: aicrm/backend:latest
      resources:
        requests:
          cpu: 2
          memoryInGb: 2
      ports:
      - protocol: TCP
        port: 8000
      environmentVariables:
      - name: DATABASE_URL
        secureValue: postgresql://user:pass@server:5432/db
      - name: YOUGILE_API_KEY
        secureValue: your_api_key
        
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
    dnsNameLabel: aicrm-app
```

## 🏢 Enterprise Deployment

### High Availability Architecture

#### Multi-Region Setup
```mermaid
graph TB
    subgraph "Region 1 (Primary)"
        A1[Load Balancer]
        B1[Frontend Cluster]
        C1[Backend Cluster]
        D1[Database Primary]
        E1[Redis Cluster]
    end
    
    subgraph "Region 2 (Secondary)"
        A2[Load Balancer]
        B2[Frontend Cluster]
        C2[Backend Cluster]
        D2[Database Replica]
        E2[Redis Cluster]
    end
    
    F[Global Load Balancer] --> A1
    F --> A2
    D1 --> D2
    E1 -.-> E2
```

#### Kubernetes Enterprise Deployment
```yaml
# enterprise/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aicrm-production
  labels:
    environment: production
    app: aicrm

---
# enterprise/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aicrm-config
  namespace: aicrm-production
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  WORKERS: "4"
  API_RATE_LIMIT: "1000"

---
# enterprise/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: aicrm-secrets
  namespace: aicrm-production
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres-service:5432/aicrm"
  YOUGILE_API_KEY: "your_production_api_key"
  JWT_SECRET: "your_jwt_secret"
  REDIS_URL: "redis://redis-service:6379"

---
# enterprise/hpa.yaml  
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aicrm-backend-hpa
  namespace: aicrm-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aicrm-backend
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### Enterprise Database Setup
```sql
-- PostgreSQL enterprise configuration
-- postgresql.conf settings for production

# Connection Settings
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Write Performance
wal_buffers = 16MB
checkpoint_completion_target = 0.9
wal_compression = on
checkpoint_timeout = 10min

# Query Performance
random_page_cost = 1.1
effective_io_concurrency = 200
seq_page_cost = 1
default_statistics_target = 100

# Replication Settings (for HA)
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
```

### Enterprise Security Configuration

#### Network Security
```yaml
# Network policies for Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: aicrm-network-policy
  namespace: aicrm-production
spec:
  podSelector:
    matchLabels:
      app: aicrm
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
```

#### SSL/TLS Configuration
```nginx
# Enterprise SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /path/to/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

## 🔒 Security & SSL Configuration

### SSL Certificate Management

#### Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal setup
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

#### Manual SSL Certificate
```bash
# For custom SSL certificates
sudo mkdir -p /etc/ssl/certs/aicrm
sudo mkdir -p /etc/ssl/private/aicrm

# Copy your certificates
sudo cp yourdomain.crt /etc/ssl/certs/aicrm/
sudo cp yourdomain.key /etc/ssl/private/aicrm/
sudo cp ca-bundle.crt /etc/ssl/certs/aicrm/

# Set proper permissions
sudo chmod 600 /etc/ssl/private/aicrm/yourdomain.key
sudo chmod 644 /etc/ssl/certs/aicrm/*
```

### Firewall Configuration

#### UFW (Ubuntu Firewall)
```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow specific IPs for admin access
sudo ufw allow from 203.0.113.0/24 to any port 22

# Check status
sudo ufw status verbose
```

#### Advanced iptables Rules
```bash
#!/bin/bash
# iptables-rules.sh - Advanced firewall rules

# Clear existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow SSH (rate limited)
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m limit --limit 3/min --limit-burst 3 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Rate limiting for HTTP
iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -m limit --limit 25/min --limit-burst 50 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m conntrack --ctstate NEW -m limit --limit 25/min --limit-burst 50 -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "DROPPED: "

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Application Security

#### Environment Security
```bash
# Secure environment file permissions
chmod 600 .env
chown app:app .env

# Use secrets management in production
# Example with Docker secrets
echo "your_secret_key" | docker secret create jwt_secret -
echo "your_api_key" | docker secret create yougile_api_key -
```

#### Security Headers
```python
# security.py - Enhanced security middleware
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import Response
import time

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY" 
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.yougile.com"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response
```

## 📊 Monitoring & Maintenance

### System Monitoring

#### Prometheus & Grafana Setup
```yaml
# monitoring/docker-compose-monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    ports:
      - "9100:9100"

volumes:
  prometheus_data:
  grafana_data:
```

#### Application Metrics
```python
# metrics.py - Application monitoring
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Metrics definitions
REQUEST_COUNT = Counter('aicrm_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('aicrm_request_duration_seconds', 'Request duration')
ACTIVE_USERS = Gauge('aicrm_active_users', 'Number of active users')
TASK_CREATION_RATE = Counter('aicrm_tasks_created_total', 'Tasks created')
AGENT_USAGE = Counter('aicrm_agent_usage_total', 'Agent usage', ['agent_name'])

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Process request
            await self.app(scope, receive, send)
            
            # Record metrics
            duration = time.time() - start_time
            method = scope["method"]
            path = scope["path"]
            
            REQUEST_DURATION.observe(duration)
            REQUEST_COUNT.labels(method=method, endpoint=path, status="200").inc()
        else:
            await self.app(scope, receive, send)

# Start metrics server
start_http_server(8001)
```

### Health Checks

#### Comprehensive Health Check
```python
# health.py - Advanced health checking
from fastapi import APIRouter, HTTPException
import asyncio
import time
from typing import Dict, Any

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive system health check"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Database health
    try:
        db_start = time.time()
        await check_database_connection()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": (time.time() - db_start) * 1000
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Redis health
    try:
        redis_start = time.time()
        await check_redis_connection()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": (time.time() - redis_start) * 1000
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # YouGile API health
    try:
        api_start = time.time()
        await check_yougile_api()
        health_status["checks"]["yougile_api"] = {
            "status": "healthy",
            "response_time_ms": (time.time() - api_start) * 1000
        }
    except Exception as e:
        health_status["checks"]["yougile_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # System resources
    health_status["checks"]["system"] = await check_system_resources()
    
    return health_status

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    # Check if application is ready to serve requests
    checks = ["database", "redis", "configuration"]
    
    for check in checks:
        if not await is_component_ready(check):
            raise HTTPException(status_code=503, detail=f"{check} not ready")
    
    return {"status": "ready"}

@router.get("/live")  
async def liveness_check():
    """Kubernetes liveness probe"""
    # Simple check if application is alive
    return {"status": "alive", "timestamp": time.time()}
```

### Log Management

#### Structured Logging
```python
# logging_config.py - Structured logging setup
import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
            
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/aicrm/app.log')
    ]
)

# Set JSON formatter for production
if os.getenv('ENVIRONMENT') == 'production':
    for handler in logging.getLogger().handlers:
        handler.setFormatter(JSONFormatter())
```

#### Log Rotation & Archival
```bash
# /etc/logrotate.d/aicrm
/var/log/aicrm/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 0644 aicrm aicrm
    postrotate
        docker kill -s HUP aicrm_backend
    endscript
}

# Test logrotate
sudo logrotate -d /etc/logrotate.d/aicrm
sudo logrotate -f /etc/logrotate.d/aicrm
```

## 💾 Backup & Recovery

### Database Backup Strategy

#### Automated PostgreSQL Backups
```bash
#!/bin/bash
# backup-database.sh - Automated database backup

# Configuration
DB_HOST="localhost"
DB_NAME="aicrm"
DB_USER="aicrm"
BACKUP_DIR="/var/backups/aicrm"
RETENTION_DAYS=30
S3_BUCKET="aicrm-backups"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/aicrm_backup_$TIMESTAMP.sql.gz"

# Create backup
echo "Starting database backup..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    --verbose \
    | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
    
    # Upload to S3 (optional)
    if [ ! -z "$S3_BUCKET" ]; then
        aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/database/"
        echo "Backup uploaded to S3"
    fi
    
    # Cleanup old backups
    find "$BACKUP_DIR" -name "aicrm_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up"
else
    echo "Backup failed!"
    exit 1
fi
```

#### Database Recovery Procedure
```bash
#!/bin/bash
# restore-database.sh - Database restoration

# Configuration
BACKUP_FILE="$1"
DB_HOST="localhost"
DB_NAME="aicrm"
DB_USER="aicrm"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Create new database (drop existing)
echo "Creating new database..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME}_restore;"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME}_restore;"

# Restore from backup
echo "Restoring from backup..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    zcat "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "${DB_NAME}_restore"
else
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "${DB_NAME}_restore" < "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    echo "Restore successful to ${DB_NAME}_restore"
    echo "To switch to restored database, run:"
    echo "1. Stop application"
    echo "2. Rename databases: mv $DB_NAME ${DB_NAME}_old && mv ${DB_NAME}_restore $DB_NAME"
    echo "3. Start application"
else
    echo "Restore failed!"
    exit 1
fi
```

### Application Backup

#### Complete System Backup
```bash
#!/bin/bash
# full-system-backup.sh - Complete application backup

BACKUP_ROOT="/var/backups/aicrm-system"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

echo "Starting full system backup..."

# 1. Database backup
echo "Backing up database..."
./backup-database.sh
cp /var/backups/aicrm/aicrm_backup_*.sql.gz "$BACKUP_DIR/"

# 2. Application configuration
echo "Backing up configuration..."
cp -r /app/config "$BACKUP_DIR/"
cp /app/.env "$BACKUP_DIR/" 2>/dev/null || true

# 3. SSL certificates
echo "Backing up SSL certificates..."
mkdir -p "$BACKUP_DIR/ssl"
cp -r /etc/letsencrypt/live/yourdomain.com "$BACKUP_DIR/ssl/" 2>/dev/null || true

# 4. User uploaded files
echo "Backing up user files..."
cp -r /app/uploads "$BACKUP_DIR/" 2>/dev/null || true

# 5. Docker compose and environment files
echo "Backing up deployment files..."
cp /app/docker-compose.yml "$BACKUP_DIR/"
cp /app/docker-compose.prod.yml "$BACKUP_DIR/" 2>/dev/null || true

# 6. Create manifest
echo "Creating backup manifest..."
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
AI-CRM System Backup
Timestamp: $TIMESTAMP  
Database: $(ls $BACKUP_DIR/*.sql.gz 2>/dev/null | wc -l) files
Configuration: $(test -d $BACKUP_DIR/config && echo "included" || echo "not found")
SSL Certificates: $(test -d $BACKUP_DIR/ssl && echo "included" || echo "not found")  
User Files: $(test -d $BACKUP_DIR/uploads && echo "included" || echo "not found")
EOF

# 7. Create compressed archive
echo "Creating compressed archive..."
tar -czf "$BACKUP_ROOT/aicrm_full_backup_$TIMESTAMP.tar.gz" -C "$BACKUP_ROOT" "$TIMESTAMP"

# 8. Upload to remote storage
if [ ! -z "$S3_BUCKET" ]; then
    aws s3 cp "$BACKUP_ROOT/aicrm_full_backup_$TIMESTAMP.tar.gz" "s3://$S3_BUCKET/full-backups/"
fi

# 9. Cleanup
rm -rf "$BACKUP_DIR"
find "$BACKUP_ROOT" -name "aicrm_full_backup_*.tar.gz" -mtime +7 -delete

echo "Full system backup completed: aicrm_full_backup_$TIMESTAMP.tar.gz"
```

### Disaster Recovery Plan

#### Recovery Runbook
```markdown
# AI-CRM Disaster Recovery Runbook

## Severity Levels
- **P0**: Complete system outage
- **P1**: Major functionality impaired  
- **P2**: Minor functionality issues
- **P3**: Planned maintenance

## P0 - Complete System Outage

### Initial Response (0-15 minutes)
1. **Assess Impact**
   - Verify outage scope (database, application, network)
   - Check monitoring dashboards
   - Review recent changes/deployments

2. **Communication**
   - Post status page update
   - Notify stakeholders via Slack/email
   - Set up incident bridge call

### Recovery Steps (15-60 minutes)
1. **Quick Fixes**
   ```bash
   # Check service status
   docker-compose ps
   
   # Restart services if needed
   docker-compose restart
   
   # Check logs for errors
   docker-compose logs --tail=100
   ```

2. **Database Issues**
   ```bash
   # Check database connectivity
   docker-compose exec backend python -c "from database import engine; print(engine.connect())"
   
   # Restore from backup if corrupted
   ./restore-database.sh /var/backups/aicrm/latest_backup.sql.gz
   ```

3. **Application Issues**
   ```bash
   # Rebuild and redeploy
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Post-Recovery (60+ minutes)
1. **Verification**
   - Test critical user paths
   - Verify data integrity
   - Monitor system performance

2. **Communication**
   - Update status page (resolved)
   - Send post-mortem summary
   - Schedule retrospective meeting

3. **Documentation**
   - Record incident timeline
   - Document lessons learned
   - Update runbook procedures
```

## 🔧 Troubleshooting

### Common Deployment Issues

#### Docker-Related Problems

**Problem: Container fails to start**
```bash
# Debug container startup
docker-compose logs <service_name>

# Check container configuration
docker-compose config

# Test container individually
docker run -it <image_name> /bin/bash
```

**Problem: Port conflicts**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8000
sudo ss -tulpn | grep :8000

# Stop conflicting service
sudo systemctl stop <service_name>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Change external port
```

**Problem: Permission issues with volumes**
```bash
# Fix volume permissions
sudo chown -R 1000:1000 ./data
sudo chmod -R 755 ./data

# Or specify user in docker-compose.yml
user: "1000:1000"
```

#### Database Connection Issues

**Problem: Database connection refused**
```bash
# Check if database is running
docker-compose ps database

# Check database logs
docker-compose logs database

# Test connection manually
docker-compose exec backend python -c "
import psycopg2
conn = psycopg2.connect('postgresql://user:pass@db:5432/aicrm')
print('Connection successful')
"
```

**Problem: Database migration failures**
```bash
# Run migrations manually
docker-compose exec backend python -m alembic upgrade head

# Reset database if needed
docker-compose exec backend python init_db.py --reset

# Check migration status
docker-compose exec backend python -m alembic current
```

#### SSL/HTTPS Issues

**Problem: SSL certificate errors**
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout

# Test SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Renew Let's Encrypt certificate
sudo certbot renew --dry-run
sudo certbot renew
```

**Problem: Mixed content warnings**
```bash
# Ensure all API calls use HTTPS
# Check for hardcoded HTTP URLs in code
grep -r "http://" ./src/

# Update configuration
REACT_APP_API_URL=https://yourdomain.com
API_BASE_URL=https://yourdomain.com
```

### Performance Issues

#### High Memory Usage
```bash
# Check memory usage by container
docker stats

# Optimize database connections
# In backend configuration:
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Adjust container memory limits
deploy:
  resources:
    limits:
      memory: 512M
```

#### Slow Response Times
```bash
# Enable query logging
# In postgresql.conf:
log_statement = 'all'
log_duration = on
log_min_duration_statement = 1000

# Check slow queries
docker-compose exec database tail -f /var/log/postgresql/postgresql.log

# Add database indexes
CREATE INDEX CONCURRENTLY idx_tasks_status ON tasks(status);
CREATE INDEX CONCURRENTLY idx_tasks_created_at ON tasks(created_at);
```

### Network & Connectivity Issues

**Problem: API calls failing from frontend**
```bash
# Check CORS configuration
CORS_ALLOWED_ORIGINS=https://yourdomain.com,http://localhost:3000

# Debug network connectivity
docker-compose exec frontend curl -I http://backend:8000/health

# Check firewall rules
sudo ufw status
sudo iptables -L
```

**Problem: WebSocket connections failing**
```nginx
# Ensure Nginx supports WebSocket
location /api/ws {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

### Getting Additional Help

#### Log Analysis Commands
```bash
# Search for errors in logs
docker-compose logs | grep -i error
docker-compose logs --since="1h" | grep -E "(error|exception|failed)"

# Monitor logs in real-time
docker-compose logs -f

# Export logs for analysis
docker-compose logs > aicrm_logs_$(date +%Y%m%d_%H%M%S).log
```

#### System Diagnostic Script
```bash
#!/bin/bash
# diagnostic.sh - System health diagnostic

echo "=== AI-CRM System Diagnostic ==="
echo "Timestamp: $(date)"
echo

echo "=== System Information ==="
uname -a
echo "Memory: $(free -h | grep ^Mem | awk '{print $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $4}')"
echo

echo "=== Docker Status ==="
docker --version
docker-compose --version
docker-compose ps
echo

echo "=== Service Health ==="
curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
echo

echo "=== Recent Logs (last 50 lines) ==="
docker-compose logs --tail=50
echo

echo "=== Port Usage ==="
sudo netstat -tulpn | grep -E ":80|:443|:3000|:8000|:5432|:6379"
echo

echo "=== Certificate Status ==="
if [ -f /etc/letsencrypt/live/*/cert.pem ]; then
    openssl x509 -in /etc/letsencrypt/live/*/cert.pem -noout -dates
fi
```

#### Support Resources
- **Documentation**: Complete guides in `/docs` folder
- **Health Endpoints**: `/health`, `/ready`, `/metrics`
- **Log Files**: Container logs via `docker-compose logs`
- **Monitoring**: Grafana dashboard at port 3001
- **Community**: GitHub Issues and Discussions

This comprehensive deployment guide provides everything needed to successfully deploy the AI-CRM system in any environment, from development to enterprise production. Choose the deployment option that best fits your needs and follow the step-by-step instructions for a smooth deployment experience.