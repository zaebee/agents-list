# 🚀 AI-CRM Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- AI API keys (recommended: Anthropic Claude)

## 1. Quick Docker Deployment

```bash
# Clone the repository
git clone <your-repo-url>
cd our-crm-ai

# Copy environment configuration
cp .env.docker .env

# Edit .env with your API keys (optional - demo keys included)
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here

# Start all services
docker-compose -f docker-compose.phase2a.yml up -d

# Check status
docker-compose -f docker-compose.phase2a.yml ps

# View logs
docker-compose -f docker-compose.phase2a.yml logs -f aicrm-app
```

## 2. Access the System

**API Endpoints:**
- Main API: http://localhost:8080
- API Documentation: http://localhost:8080/docs
- Health Check: http://localhost:8080/health

**Monitoring (optional profiles):**
```bash
# Start with monitoring
docker-compose -f docker-compose.phase2a.yml --profile monitoring up -d

# Access monitoring
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

## 3. Test Authentication

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