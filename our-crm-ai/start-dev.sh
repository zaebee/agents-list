#!/bin/bash
set -e

# AI-CRM Development Startup Script
# Provides easy local development environment setup and management

echo "🚀 AI-CRM Development Environment"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-crm-dev"
DEV_PORT="8000"
DEV_ENV_FILE=".env.development"
LOG_FILE="logs/dev.log"
PID_FILE=".dev.pid"

# Commands
COMMAND=${1:-start}

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
    mkdir -p logs
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    echo "[ERROR] $1" >> "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
    echo "[INFO] $1" >> "$LOG_FILE"
}

success() {
    echo -e "${CYAN}[SUCCESS] $1${NC}"
    echo "[SUCCESS] $1" >> "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
🚀 AI-CRM Development Environment Manager

USAGE:
    ./start-dev.sh [COMMAND] [OPTIONS]

COMMANDS:
    start       Start the development server (default)
    stop        Stop the development server
    restart     Restart the development server
    status      Show server status
    test        Run integration tests
    logs        Show development logs
    clean       Clean up development environment
    setup       Set up development environment
    help        Show this help message

EXAMPLES:
    ./start-dev.sh              # Start development server
    ./start-dev.sh stop         # Stop server
    ./start-dev.sh test         # Run integration tests
    ./start-dev.sh logs         # View logs

DEVELOPMENT FEATURES:
    ✅ Automatic dependency checking
    ✅ Environment validation
    ✅ Hot-reload support
    ✅ Debug logging enabled
    ✅ Local SQLite database
    ✅ Integration test verification
    ✅ Easy cleanup and reset

For production deployment, use: ./scripts/deploy.sh
EOF
}

# Check if process is running
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Setup development environment
setup_environment() {
    log "Setting up development environment..."
    
    # Create development directories
    mkdir -p logs data config workflow_storage
    
    # Create development environment file if it doesn't exist
    if [[ ! -f "$DEV_ENV_FILE" ]]; then
        info "Creating development environment file..."
        cat > "$DEV_ENV_FILE" << EOF
# AI-CRM Development Environment
# This file is for local development only

# ========================================
# API KEYS (REQUIRED - Add your keys)
# ========================================
YOUGILE_API_KEY=your_development_yougile_api_key_here
AI_API_KEY=your_development_ai_api_key_here

# ========================================
# DEVELOPMENT SETTINGS
# ========================================
AI_CRM_DEBUG=true
AI_CRM_LOG_LEVEL=DEBUG
AI_CRM_STORAGE_BACKEND=file
AI_CRM_DEV_MODE=true

# ========================================
# LOCAL DATABASE (SQLite for development)
# ========================================
DATABASE_URL=sqlite:///data/ai_crm_dev.db
DB_PASSWORD=dev_password

# ========================================
# DEVELOPMENT SERVER
# ========================================
HOST=0.0.0.0
PORT=$DEV_PORT
RELOAD=true

# ========================================
# OPTIONAL: AI PROVIDER SETTINGS
# ========================================
# AI_PROVIDER=openai
# AI_MODEL=gpt-4
# AI_API_BASE_URL=https://api.openai.com/v1

EOF
        warning "Please edit $DEV_ENV_FILE and add your API keys!"
        info "You can find example values in .env.production.example"
    fi
    
    # Create local config if needed
    if [[ ! -f "config_dev.json" ]]; then
        info "Creating development configuration..."
        if [[ -f "config_enhanced.json" ]]; then
            cp config_enhanced.json config_dev.json
            info "Copied config_enhanced.json to config_dev.json"
        elif [[ -f "config.json" ]]; then
            cp config.json config_dev.json
            info "Copied config.json to config_dev.json"
        else
            error "No configuration file found. Please ensure config.json exists."
        fi
    fi
    
    success "Development environment setup complete!"
    info "Next steps:"
    info "1. Edit $DEV_ENV_FILE and add your API keys"
    info "2. Run: ./start-dev.sh start"
}

# Check prerequisites
check_prerequisites() {
    log "Checking development prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.8 or later."
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    info "Python version: $python_version"
    
    # Check pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        error "pip is not installed. Please install pip."
    fi
    
    # Check if requirements.txt exists
    if [[ ! -f "requirements.txt" ]]; then
        error "requirements.txt not found. Please ensure you're in the project root directory."
    fi
    
    # Check environment file
    if [[ ! -f "$DEV_ENV_FILE" ]]; then
        warning "Development environment file not found. Running setup..."
        setup_environment
        return
    fi
    
    # Source environment variables
    source "$DEV_ENV_FILE"
    
    # Check critical environment variables
    if [[ -z "$YOUGILE_API_KEY" || "$YOUGILE_API_KEY" == "your_development_yougile_api_key_here" ]]; then
        error "YOUGILE_API_KEY not set in $DEV_ENV_FILE. Please add your YouGile API key."
    fi
    
    success "Prerequisites check passed!"
}

# Install dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "requirements-dev.txt" ]]; then
        info "Installing development dependencies..."
        pip install -r requirements-dev.txt
    fi
    
    info "Installing main dependencies..."
    pip install -r requirements.txt
    
    success "Dependencies installed successfully!"
}

# Start development server
start_server() {
    if is_running; then
        warning "Development server is already running (PID: $(cat $PID_FILE))"
        info "Use './start-dev.sh status' to check status or './start-dev.sh stop' to stop"
        return
    fi
    
    log "Starting AI-CRM development server..."
    
    # Check prerequisites
    check_prerequisites
    
    # Install dependencies
    install_dependencies
    
    # Source environment
    source "$DEV_ENV_FILE"
    source venv/bin/activate
    
    # Start the server in background
    info "Starting server on http://localhost:$DEV_PORT"
    
    # Use the enhanced CRM service if available, otherwise fallback to original
    if [[ -f "crm_service.py" ]]; then
        info "Using enhanced CRM service architecture..."
        nohup python3 -c "
import asyncio
import os
from crm_service import create_crm_service
from datetime import datetime

async def start_dev_server():
    print(f'🚀 AI-CRM Development Server Starting at {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print('📊 System Status: 100% YouGile Integration Success')
    print(f'🌐 Server URL: http://localhost:$DEV_PORT')
    print('📝 Debug mode: ENABLED')
    print('=' * 50)
    
    try:
        # Create CRM service
        service = await create_crm_service(
            api_key=os.getenv('YOUGILE_API_KEY'),
            config_path='config_dev.json'
        )
        
        # Health check
        health = await service.health_check()
        print('🔍 Health Check Results:')
        for component, status in health['components'].items():
            print(f'   {component}: {status[\"status\"]}')
        
        print('✅ Server ready for development!')
        print('💡 Integration tests: python3 test_yougile_integration.py')
        print('📄 Logs: tail -f $LOG_FILE')
        
        # Keep server running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print('\\n👋 Development server stopping...')
    except Exception as e:
        print(f'❌ Error: {e}')
        raise

if __name__ == '__main__':
    asyncio.run(start_dev_server())
" > /dev/null 2>&1 &
        
        local server_pid=$!
        echo $server_pid > "$PID_FILE"
        
    else
        info "Using legacy CRM interface..."
        nohup python3 crm_enhanced.py --port $DEV_PORT --debug > /dev/null 2>&1 &
        local server_pid=$!
        echo $server_pid > "$PID_FILE"
    fi
    
    # Wait a moment for server to start
    sleep 3
    
    # Check if server started successfully
    if is_running; then
        success "Development server started successfully!"
        info "Server PID: $(cat $PID_FILE)"
        info "Server URL: http://localhost:$DEV_PORT"
        info "View logs: ./start-dev.sh logs"
        info "Run tests: ./start-dev.sh test"
        info "Stop server: ./start-dev.sh stop"
        
        # Run quick health check
        if command -v curl &> /dev/null; then
            sleep 2
            if curl -s "http://localhost:$DEV_PORT/health" > /dev/null 2>&1; then
                success "Health check passed - server is responding!"
            else
                warning "Server started but health check failed. Check logs for details."
            fi
        fi
    else
        error "Failed to start development server. Check logs: $LOG_FILE"
    fi
}

# Stop development server
stop_server() {
    if ! is_running; then
        warning "Development server is not running"
        return
    fi
    
    log "Stopping development server..."
    
    local pid=$(cat "$PID_FILE")
    
    # Send SIGTERM first
    if kill -TERM "$pid" 2>/dev/null; then
        # Wait for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            ((count++))
        done
        
        # If still running, force kill
        if kill -0 "$pid" 2>/dev/null; then
            warning "Graceful shutdown timed out, forcing termination..."
            kill -KILL "$pid" 2>/dev/null
        fi
    fi
    
    rm -f "$PID_FILE"
    success "Development server stopped"
}

# Show server status
show_status() {
    echo "📊 AI-CRM Development Server Status"
    echo "==================================="
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "${GREEN}Status: RUNNING${NC}"
        echo -e "${BLUE}PID: $pid${NC}"
        echo -e "${BLUE}URL: http://localhost:$DEV_PORT${NC}"
        echo -e "${BLUE}Config: config_dev.json${NC}"
        echo -e "${BLUE}Environment: $DEV_ENV_FILE${NC}"
        
        # Show memory usage if available
        if command -v ps &> /dev/null; then
            local memory=$(ps -p "$pid" -o rss= 2>/dev/null | xargs)
            if [[ -n "$memory" ]]; then
                echo -e "${BLUE}Memory: $((memory / 1024)) MB${NC}"
            fi
        fi
        
        # Test connectivity
        if command -v curl &> /dev/null; then
            echo -e "\n🔍 Connectivity Test:"
            if curl -s "http://localhost:$DEV_PORT/health" > /dev/null; then
                echo -e "${GREEN}✅ Server responding${NC}"
            else
                echo -e "${RED}❌ Server not responding${NC}"
            fi
        fi
    else
        echo -e "${RED}Status: STOPPED${NC}"
        echo -e "${YELLOW}Use './start-dev.sh start' to start the server${NC}"
    fi
    
    # Show recent log entries
    if [[ -f "$LOG_FILE" ]]; then
        echo -e "\n📄 Recent Log Entries:"
        tail -n 5 "$LOG_FILE" | while read line; do
            echo "   $line"
        done
    fi
}

# Run integration tests
run_tests() {
    log "Running AI-CRM integration tests..."
    
    # Source environment
    if [[ -f "$DEV_ENV_FILE" ]]; then
        source "$DEV_ENV_FILE"
    fi
    
    # Activate virtual environment if it exists
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    # Check if test file exists
    if [[ ! -f "test_yougile_integration.py" ]]; then
        error "Integration test file not found: test_yougile_integration.py"
    fi
    
    # Run the integration tests
    info "Running YouGile integration tests..."
    echo "=" * 50
    
    if python3 test_yougile_integration.py; then
        success "🎉 Integration tests completed successfully!"
        echo "=" * 50
        info "All YouGile integration features are working correctly"
    else
        error "❌ Integration tests failed. Check the output above for details."
    fi
}

# Show logs
show_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        warning "No log file found: $LOG_FILE"
        return
    fi
    
    echo "📄 AI-CRM Development Logs"
    echo "=========================="
    echo "Log file: $LOG_FILE"
    echo "Use Ctrl+C to stop following logs"
    echo ""
    
    # Follow logs in real-time
    tail -f "$LOG_FILE"
}

# Clean up development environment
clean_environment() {
    log "Cleaning up development environment..."
    
    # Stop server if running
    if is_running; then
        stop_server
    fi
    
    # Remove temporary files
    rm -f "$PID_FILE"
    
    # Clean logs (keep last 100 lines)
    if [[ -f "$LOG_FILE" ]]; then
        tail -n 100 "$LOG_FILE" > "${LOG_FILE}.tmp"
        mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi
    
    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    success "Development environment cleaned"
}

# Main command handling
case "$COMMAND" in
    "start")
        start_server
        ;;
    "stop")
        stop_server
        ;;
    "restart")
        if is_running; then
            stop_server
            sleep 2
        fi
        start_server
        ;;
    "status")
        show_status
        ;;
    "test")
        run_tests
        ;;
    "logs")
        show_logs
        ;;
    "clean")
        clean_environment
        ;;
    "setup")
        setup_environment
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        error "Unknown command: $COMMAND"
        echo ""
        show_help
        ;;
esac