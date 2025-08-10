# AI-CRM Web UI

A modern web interface for the AI-powered YouGile CRM system, providing task management with intelligent agent routing capabilities.

## Features

- 🎯 **AI-Powered Task Assignment**: Automatic agent suggestions based on task content
- 📋 **Kanban Board Interface**: Drag-and-drop task management across columns
- 🤖 **PM Agent Gateway**: Intelligent task analysis and workflow planning
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile devices
- 🔄 **Real-time Updates**: Live task status synchronization
- 💬 **Task Comments**: Collaborative communication on tasks
- 🎨 **Modern UI**: Clean, professional interface built with React and Tailwind CSS

## Architecture

- **Frontend**: React 18 with TypeScript, Tailwind CSS, React DnD
- **Backend**: FastAPI with Python 3.11
- **Integration**: Direct integration with existing CLI CRM system
- **Deployment**: Docker containerization with Nginx reverse proxy

## Quick Start

### Prerequisites

1. **YouGile API Key**: Set up your YouGile API key from your YouGile account
2. **Existing CRM Setup**: Ensure the CLI CRM system is properly configured
3. **Docker & Docker Compose**: For containerized deployment
4. **Node.js 18+**: For local development

### Environment Setup

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Configure your YouGile API key**:
   ```bash
   # Edit .env file
   YOUGILE_API_KEY=your_actual_api_key_here
   ```

### Development Setup

#### Option 1: Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Option 2: Local Development

**Backend Setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Ensure YOUGILE_API_KEY is set in your environment
export YOUGILE_API_KEY=your_api_key_here

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup**:
```bash
cd frontend
npm install
npm start

# Access at http://localhost:3000
```

### Production Deployment

```bash
# Use production profile with Nginx
docker-compose --profile production up -d

# Access via http://localhost
```

## API Documentation

The FastAPI backend provides comprehensive API documentation:
- **Interactive docs**: http://localhost:8000/docs
- **OpenAPI schema**: http://localhost:8000/openapi.json

### Core Endpoints

- `GET /tasks` - List all tasks
- `POST /tasks` - Create new task with AI suggestions
- `PUT /tasks/{id}/move` - Move task between columns
- `GET /tasks/{id}` - Get task details and comments
- `POST /tasks/{id}/comments` - Add comment to task
- `GET /agents` - List available AI agents
- `POST /agents/suggest` - Get AI agent suggestions
- `POST /pm/analyze` - PM Agent Gateway analysis

## Usage Guide

### Creating Tasks

1. Click "New Task" button
2. Enter task title and description
3. Use "PM Analysis" for intelligent task breakdown
4. Review AI agent suggestions
5. Assign agent manually if needed
6. Submit to create task

### Managing Tasks

- **Drag & Drop**: Move tasks between columns
- **Task Details**: Click any task to view details and add comments
- **AI Assignment**: Get automatic agent suggestions based on task content
- **Status Tracking**: Visual progress across To Do → In Progress → Done

### AI Agent Features

- **Smart Suggestions**: AI analyzes task content and suggests appropriate agents
- **PM Gateway**: Comprehensive task analysis with complexity assessment
- **Agent Specializations**: 59+ specialized agents for different task types
- **Confidence Scoring**: AI suggestions include confidence percentages

## Configuration

### CRM Integration

The web UI integrates with the existing CLI CRM system by:
- Reading the same `config.json` file
- Using the same YouGile API endpoints
- Maintaining compatibility with existing agents and stickers

### Agent Categories

Available agent types include:
- **Development**: Frontend, Backend, Full-stack developers
- **Infrastructure**: DevOps, Cloud architects, Security specialists
- **Data & AI**: Data scientists, ML engineers, AI specialists
- **Business**: Analysts, Content creators, Sales automation
- **Documentation**: Technical writers, API documenters

## Security

- **Input Validation**: All API inputs are validated with Pydantic models
- **CSRF Protection**: Built-in CSRF protection for state-changing operations
- **Timeout Handling**: API requests have configurable timeouts
- **Rate Limiting**: Nginx-based rate limiting in production
- **Security Headers**: Proper security headers for web security

## Troubleshooting

### Common Issues

1. **API Connection Failed**:
   - Verify YOUGILE_API_KEY is set correctly
   - Check network connectivity to YouGile API
   - Ensure CRM configuration is valid

2. **Task Creation Failed**:
   - Verify agent stickers are properly configured
   - Check task validation requirements
   - Review API error messages

3. **Drag & Drop Not Working**:
   - Ensure JavaScript is enabled
   - Try refreshing the page
   - Check browser compatibility

### Health Checks

- **Backend Health**: http://localhost:8000/health
- **API Status**: Check `/health` endpoint response
- **Configuration**: Verify `config_loaded: true` in health response

## Development

### Project Structure

```
web-ui/
├── backend/           # FastAPI backend
│   ├── main.py       # Main application
│   └── requirements.txt
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/      # Custom hooks
│   │   ├── services/   # API services
│   │   └── types/      # TypeScript types
│   └── package.json
├── docker-compose.yml # Container orchestration
└── README.md         # This file
```

### Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Contributing

1. Follow existing code style and structure
2. Add proper TypeScript types for new features
3. Include error handling and loading states
4. Test on both desktop and mobile devices
5. Update documentation for new features

## License

This project extends the existing AI-CRM system and follows the same licensing terms.

## Support

For issues and questions:
1. Check this README for common solutions
2. Review API documentation at `/docs`
3. Check browser console for error messages
4. Verify environment configuration

---

**Built with**: React, TypeScript, FastAPI, Python, Docker, Tailwind CSS