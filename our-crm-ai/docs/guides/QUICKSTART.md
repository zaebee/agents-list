# 🚀 AI-CRM Quick Start Guide (Phase 2A)

## Prerequisites

- **Docker and Docker Compose** for containerized deployment
- **Python 3.11+** with uv package manager (for local development)
- **uv** - Fast Python package installer ([install guide](https://docs.astral.sh/uv/))
- **AI API keys** (recommended: Anthropic Claude)
- **Git** for cloning the repository

## 1. Quick Docker Deployment (Phase 2A)

```bash
# Clone the repository
git clone <your-repo-url>
cd our-crm-ai

# Copy environment configuration
cp .env.docker .env

# Edit .env with your API keys and settings
vim .env  # or nano .env
# Required: ANTHROPIC_API_KEY=your_key_here
# Optional: OPENAI_API_KEY=your_key_here
# Security: JWT_SECRET_KEY=your_32_char_secret_key

# Start Phase 2A production services
docker-compose -f docker-compose.phase2a.yml up -d

# Verify deployment
docker-compose -f docker-compose.phase2a.yml ps
curl http://localhost:8080/health

# View application logs
docker-compose -f docker-compose.phase2a.yml logs -f aicrm-app
```

## 2. Access the System

**Phase 2A Endpoints:**
- **Frontend & API**: http://localhost:8080 (nginx reverse proxy)
- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health
- **Metrics**: http://localhost:8080/metrics

**Optional Monitoring:**
```bash
# Start with full monitoring stack
docker-compose -f docker-compose.phase2a.yml --profile monitoring up -d

# Access monitoring dashboards
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

## 3. Development Setup (Alternative)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <your-repo-url>
cd our-crm-ai

# Install dependencies with uv
uv sync

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start development server
./start-dev.sh
# Access: http://localhost:5001
```

## 4. Test Authentication

### Register a New User
```bash
curl -X POST "http://localhost:8080/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com", 
       "password": "securepassword123",
       "full_name": "Test User"
     }'
```

### Login and Get Token
```bash
curl -X POST "http://localhost:8080/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser", 
       "password": "securepassword123"
     }'
```

### Use Protected Endpoints
```bash
# Use the access_token from login response
TOKEN="your_access_token_here"

curl -X GET "http://localhost:8080/api/auth/me" \
     -H "Authorization: Bearer $TOKEN"
```

### Default Admin Account
```bash
# Login as admin (created automatically)
curl -X POST "http://localhost:8080/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "password": "admin123"
     }'
```

## 5. Test AI Agents

### Using the CLI
```bash
# Development environment
uv run python crm_enhanced.py create --title "Test Task" --description "Testing the system"

# Docker environment
docker-compose -f docker-compose.phase2a.yml exec aicrm-app python crm_enhanced.py --help
```

### Using the API
```bash
# Get available agents
curl -X GET "http://localhost:8080/api/agents" \
     -H "Authorization: Bearer $TOKEN"

# Create a task
curl -X POST "http://localhost:8080/api/tasks" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test API Task",
       "description": "Testing task creation via API"
     }'
```

## 6. Troubleshooting

### Check Service Status
```bash
# Docker deployment
docker-compose -f docker-compose.phase2a.yml ps
docker-compose -f docker-compose.phase2a.yml logs aicrm-app

# Development
curl http://localhost:5001/health  # Development server
curl http://localhost:8080/health  # Docker deployment
```

### Common Issues

**Port already in use:**
```bash
# Check what's using port 8080
sudo netstat -tulpn | grep :8080

# Kill the process or change port in docker-compose.phase2a.yml
```

**Database connection errors:**
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.phase2a.yml logs postgres

# Reset database
docker-compose -f docker-compose.phase2a.yml down -v
docker-compose -f docker-compose.phase2a.yml up -d
```

**Missing API keys:**
```bash
# Check environment variables
docker-compose -f docker-compose.phase2a.yml exec aicrm-app env | grep API_KEY

# Update .env file and restart
docker-compose -f docker-compose.phase2a.yml restart aicrm-app
```

## 7. Next Steps

### Development
- Read [Architecture Guide](../architecture/AI_INTEGRATION_GUIDE.md)
- Explore [Agent System](../architecture/PM_GATEWAY_GUIDE.md) 
- Check [User Guide](USER_GUIDE.md) for detailed features

### Production
- Review [Docker Guide](../../DOCKER_GUIDE.md) for production deployment
- Configure SSL certificates for https
- Set up monitoring and alerting
- Review security settings in [Security Audit](../../SECURITY_AUDIT_SUMMARY.md)

### Resources
- **API Documentation**: http://localhost:8080/docs
- **Phase Strategy**: [PHASES.md](../../PHASES.md)
- **Architecture Overview**: [ARCHITECTURE.md](../../ARCHITECTURE.md)

---

**You're ready to go!** 🚀

**Phase 2A Features Available:**
✅ Production-ready deployment  
✅ Secure authentication system  
✅ 28+ AI agents  
✅ Modern Python tooling (uv)  
✅ Comprehensive monitoring  

**Support**: Check logs and documentation for issues

**Default Admin Login:**
- Username: `admin`
- Password: `admin123`

**Test Login:**
```bash
curl -X POST "http://localhost:8080/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
```

## 4. Execute Commands

```bash
# Get access token from login response, then:
curl -X POST "http://localhost:8080/api/command" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -d '{"command": "Create a simple hello world task"}'
```

## 5. Development Setup

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment
cp .env.docker .env

# Initialize database
python -c "
from auth_database import create_tables, seed_default_data, SessionLocal
create_tables()
db = SessionLocal()
try:
    seed_default_data(db)
finally:
    db.close()
"

# Start development server
./start-dev.sh
```

## 6. Code Quality

```bash
# Run linting and formatting
ruff check . --fix
black .
mypy .

# Run tests (when available)
pytest
```

## 🛑 Troubleshooting

**Common Issues:**

1. **Port conflicts:** Change ports in docker-compose.phase2a.yml
2. **Permission denied:** Run `sudo docker-compose...`
3. **Database connection:** Wait for PostgreSQL startup (30-60 seconds)
4. **API keys:** Check .env file configuration

**Logs:**
```bash
# Application logs
docker-compose -f docker-compose.phase2a.yml logs aicrm-app

# Database logs
docker-compose -f docker-compose.phase2a.yml logs postgres

# All services
docker-compose -f docker-compose.phase2a.yml logs
```

**Reset:**
```bash
# Stop and remove all containers and volumes
docker-compose -f docker-compose.phase2a.yml down -v

# Restart fresh
docker-compose -f docker-compose.phase2a.yml up -d
```

## 📚 Next Steps

- Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production setup
- Check [README.md](README.md) for detailed architecture
- Explore API documentation at `/docs` endpoint

**System Status:**
✅ PostgreSQL database integration
✅ JWT authentication system  
✅ RESTful API with FastAPI
✅ Docker containerization
✅ Code quality standards (ruff, mypy, black)
✅ Production-ready configuration