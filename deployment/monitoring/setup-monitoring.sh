#!/bin/bash

# AI-CRM Production Monitoring Setup Script
# Sets up comprehensive monitoring and health check infrastructure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
MONITORING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$MONITORING_DIR/../.." && pwd)"

log_info "Setting up AI-CRM production monitoring..."
log_info "Monitoring directory: $MONITORING_DIR"
log_info "Project root: $PROJECT_ROOT"

# Check Python version
check_python() {
    log_info "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
        log_success "Python $PYTHON_VERSION found"
    else
        log_error "Python 3 is required but not found"
        exit 1
    fi
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies for monitoring..."
    
    # Create requirements file if it doesn't exist
    if [ ! -f "$MONITORING_DIR/requirements.txt" ]; then
        cat > "$MONITORING_DIR/requirements.txt" << EOF
aiohttp>=3.8.0
psutil>=5.9.0
requests>=2.28.0
aiohttp-cors>=0.7.0
asyncio-mqtt>=0.11.0
prometheus-client>=0.14.0
grafana-api>=1.0.3
slack-sdk>=3.18.0
EOF
        log_info "Created requirements.txt for monitoring dependencies"
    fi
    
    # Install dependencies
    if command -v pip3 &> /dev/null; then
        pip3 install -r "$MONITORING_DIR/requirements.txt"
        log_success "Dependencies installed successfully"
    else
        log_error "pip3 is required but not found"
        exit 1
    fi
}

# Setup monitoring configuration
setup_config() {
    log_info "Setting up monitoring configuration..."
    
    # Copy default config if it doesn't exist
    if [ ! -f "$MONITORING_DIR/monitoring-config.json" ]; then
        log_warning "monitoring-config.json not found, using default configuration"
    fi
    
    # Create logs directory
    mkdir -p "$MONITORING_DIR/logs"
    log_success "Created logs directory"
    
    # Create data directory for metrics storage
    mkdir -p "$MONITORING_DIR/data"
    log_success "Created data directory"
}

# Setup systemd services (Linux only)
setup_systemd_services() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "Setting up systemd services for automatic startup..."
        
        # Health monitor service
        cat > "/tmp/ai-crm-health-monitor.service" << EOF
[Unit]
Description=AI-CRM Health Monitor
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$MONITORING_DIR
ExecStart=python3 health-checks.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

        # Dashboard service
        cat > "/tmp/ai-crm-dashboard.service" << EOF
[Unit]
Description=AI-CRM Production Dashboard
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$MONITORING_DIR
ExecStart=python3 production-dashboard.py --port 9090
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        log_info "Systemd service files created in /tmp/"
        log_info "To install services, run as root:"
        log_info "  sudo mv /tmp/ai-crm-*.service /etc/systemd/system/"
        log_info "  sudo systemctl daemon-reload"
        log_info "  sudo systemctl enable ai-crm-health-monitor"
        log_info "  sudo systemctl enable ai-crm-dashboard"
        log_info "  sudo systemctl start ai-crm-health-monitor"
        log_info "  sudo systemctl start ai-crm-dashboard"
        
    else
        log_warning "Systemd services not applicable for this OS"
    fi
}

# Setup Docker monitoring (if Docker is available)
setup_docker_monitoring() {
    if command -v docker &> /dev/null; then
        log_info "Setting up Docker-based monitoring stack..."
        
        cat > "$MONITORING_DIR/docker-compose.monitoring.yml" << EOF
version: '3.8'

services:
  # AI-CRM Health Monitor
  health-monitor:
    build:
      context: .
      dockerfile: Dockerfile.monitoring
    container_name: ai-crm-health-monitor
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./monitoring-config.json:/app/monitoring-config.json
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "health-checks.py", "--once"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Production Dashboard
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.monitoring
    container_name: ai-crm-dashboard
    ports:
      - "9090:9090"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./monitoring-config.json:/app/monitoring-config.json
    command: ["python3", "production-dashboard.py", "--port", "9090"]
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
    depends_on:
      - health-monitor

networks:
  monitoring:
    driver: bridge
EOF

        # Create Dockerfile for monitoring
        cat > "$MONITORING_DIR/Dockerfile.monitoring" << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy monitoring scripts
COPY *.py ./
COPY *.json ./

# Create directories
RUN mkdir -p logs data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD python3 health-checks.py --once || exit 1

CMD ["python3", "health-checks.py"]
EOF
        
        log_success "Docker monitoring setup created"
        log_info "To start Docker monitoring:"
        log_info "  cd $MONITORING_DIR"
        log_info "  docker-compose -f docker-compose.monitoring.yml up -d"
        
    else
        log_warning "Docker not found, skipping Docker monitoring setup"
    fi
}

# Create monitoring scripts
create_monitoring_scripts() {
    log_info "Creating monitoring utility scripts..."
    
    # Quick health check script
    cat > "$MONITORING_DIR/quick-health-check.sh" << 'EOF'
#!/bin/bash
# Quick health check for AI-CRM services

echo "🏥 AI-CRM Quick Health Check"
echo "============================"

# Check if services are running
check_service() {
    local service_name=$1
    local port=$2
    
    if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $service_name: HEALTHY"
    else
        echo "❌ $service_name: UNHEALTHY or not running"
    fi
}

check_service "Backend API" 8000
check_service "Frontend UI" 3000
check_service "Dashboard" 9090

# System resources
echo ""
echo "📊 System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//' | head -1)"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk '/\// {print $5 " used"}')"
EOF

    chmod +x "$MONITORING_DIR/quick-health-check.sh"
    
    # Monitoring status script
    cat > "$MONITORING_DIR/monitoring-status.sh" << 'EOF'
#!/bin/bash
# Check status of AI-CRM monitoring services

echo "🔍 AI-CRM Monitoring Status"
echo "==========================="

# Check if health monitor is running
if pgrep -f "health-checks.py" > /dev/null; then
    echo "✅ Health Monitor: RUNNING"
else
    echo "❌ Health Monitor: NOT RUNNING"
fi

# Check if dashboard is running
if pgrep -f "production-dashboard.py" > /dev/null; then
    echo "✅ Production Dashboard: RUNNING"
    echo "   Access: http://localhost:9090/dashboard"
else
    echo "❌ Production Dashboard: NOT RUNNING"
fi

# Check log files
if [ -f "logs/health-monitor.log" ]; then
    echo "📄 Health Monitor Log: $(wc -l < logs/health-monitor.log) lines"
else
    echo "📄 Health Monitor Log: Not found"
fi

echo ""
echo "🔧 To start monitoring:"
echo "  python3 health-checks.py &"
echo "  python3 production-dashboard.py &"
EOF

    chmod +x "$MONITORING_DIR/monitoring-status.sh"
    
    log_success "Monitoring utility scripts created"
}

# Main setup function
main() {
    log_info "Starting AI-CRM monitoring setup..."
    
    check_python
    install_dependencies
    setup_config
    create_monitoring_scripts
    setup_docker_monitoring
    setup_systemd_services
    
    log_success "AI-CRM monitoring setup completed!"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Review and customize monitoring-config.json"
    echo "2. Start monitoring services:"
    echo "   ./quick-health-check.sh      # Quick system check"
    echo "   python3 health-checks.py &   # Background health monitoring"
    echo "   python3 production-dashboard.py --port 9090 &  # Dashboard"
    echo "3. Access dashboard: http://localhost:9090/dashboard"
    echo "4. Check monitoring status: ./monitoring-status.sh"
    echo ""
    echo "📚 Documentation:"
    echo "- Health checks: python3 health-checks.py --help"
    echo "- Dashboard: python3 production-dashboard.py --help"
    echo "- Configuration: monitoring-config.json"
    echo ""
    echo "✨ Production monitoring is now ready!"
}

# Run main function
main "$@"