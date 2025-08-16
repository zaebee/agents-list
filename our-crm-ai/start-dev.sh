#!/bin/bash
set -e

echo "🚀 Starting AI-CRM Development Server..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📋 Creating .env from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo "🔧 Please edit .env and add your API keys for full functionality"
    else
        echo "❌ Error: .env.example template not found!"
        exit 1
    fi
fi

# Load environment variables safely
echo "🔧 Loading environment variables..."
set -a  # Export all variables
source .env
set +a  # Stop exporting

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.11"
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "⚠️ Warning: Python 3.11+ recommended, found $python_version"
    echo "📖 Some features may not work correctly"
fi

# Check for minimal dependencies flag
USE_MINIMAL=${USE_MINIMAL:-true}

if [ "$USE_MINIMAL" = "true" ]; then
    echo "📦 Installing minimal development dependencies..."
    echo "💡 This skips heavy ML dependencies for faster startup"
    echo "🔧 Set USE_MINIMAL=false to install full dependencies"
    pip install --upgrade pip
    pip install -r requirements-dev-minimal.txt
else
    echo "📦 Installing full dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Install additional development dependencies
echo "📚 Installing additional development tools..."
pip install python-dotenv uvicorn[standard] --quiet

# Database setup and validation
echo "🗄️ Setting up database..."

# Check database type and provide helpful feedback
DATABASE_URL=${DATABASE_URL:-sqlite:///./ai_crm.db}
if [[ $DATABASE_URL == sqlite* ]]; then
    echo "📱 Using SQLite database (recommended for development)"
    echo "📁 Database file: ${DATABASE_URL#sqlite:///}"
elif [[ $DATABASE_URL == postgresql* ]]; then
    echo "🐘 Using PostgreSQL database"
    echo "🔌 Testing PostgreSQL connection..."
    # Test PostgreSQL connection
    python3 -c "
import os
import sys
try:
    import psycopg2
    from urllib.parse import urlparse
    url = urlparse(os.getenv('DATABASE_URL'))
    conn = psycopg2.connect(
        host=url.hostname, port=url.port or 5432,
        user=url.username, password=url.password,
        database=url.path[1:]
    )
    conn.close()
    print('✅ PostgreSQL connection successful!')
except ImportError:
    print('❌ psycopg2 not installed. Install with: pip install psycopg2-binary')
    sys.exit(1)
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    print('💡 Consider using SQLite for development: DATABASE_URL=sqlite:///./ai_crm.db')
    sys.exit(1)
    " || exit 1
fi

# Initialize database
python3 -c "
import os
import sys
from dotenv import load_dotenv
load_dotenv()

try:
    from auth_database import create_tables, seed_default_data, SessionLocal
    print('📊 Creating database tables...')
    create_tables()
    
    print('👤 Creating default admin user...')
    db = SessionLocal()
    try:
        seed_default_data(db)
        print('✅ Database initialization complete!')
    finally:
        db.close()
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    print('🔧 Check your DATABASE_URL and database setup')
    sys.exit(1)
"

# Final health check
echo "🔍 Running final health check..."
python3 -c "
from dotenv import load_dotenv
load_dotenv()

try:
    from auth_database import SessionLocal
    db = SessionLocal()
    # Test basic query
    result = db.execute('SELECT 1').fetchone()
    db.close()
    print('✅ Database health check passed!')
except Exception as e:
    print(f'⚠️ Database health check warning: {e}')
    print('🚀 Proceeding with startup anyway...')
"

# Display startup information
echo ""
echo "🎉 AI-CRM Development Server Starting!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Server URL: http://localhost:5001"
echo "📖 API Documentation: http://localhost:5001/docs"
echo "🔐 Admin Login: admin / admin123"
echo "🗄️ Database: $DATABASE_URL"
echo "🔧 Environment: ${ENVIRONMENT:-development}"
echo "📊 Log Level: ${LOG_LEVEL:-INFO}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Set default port from environment or fallback to 5001
PORT=${PORT:-5001}
HOST=${HOST:-127.0.0.1}

# Run the FastAPI application with development settings
echo "🚀 Starting uvicorn server..."
uvicorn api:app --host "$HOST" --port "$PORT" --reload --log-level debug
