#!/bin/bash
# Development startup script for AI-CRM Web UI

echo "🚀 Starting AI-CRM Web UI Development Environment"
echo "================================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your YouGile API key before continuing"
    exit 1
fi

# Check if YOUGILE_API_KEY is set
if grep -q "your_yougile_api_key_here" .env; then
    echo "❌ Please set your YOUGILE_API_KEY in the .env file"
    exit 1
fi

# Check if CRM config exists
if [ ! -f "../our-crm-ai/config.json" ]; then
    echo "❌ CRM config.json not found. Please run CRM setup first."
    echo "   cd ../our-crm-ai && python crm_setup_enhanced.py"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

echo "✅ Environment configured"
echo "📋 YOUGILE_API_KEY: ${YOUGILE_API_KEY:0:10}..."

# Start services
echo "🐳 Starting services with Docker Compose..."
docker-compose up --build

echo "🎉 Services should be running at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"