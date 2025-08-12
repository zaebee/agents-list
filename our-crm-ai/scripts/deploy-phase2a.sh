#!/bin/bash
# AI-CRM Phase 2A Production Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_ENV=${1:-production}
COMPOSE_FILE="docker-compose.phase2a.yml"
PROJECT_NAME="aicrm"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

echo -e "${BLUE}🚀 AI-CRM Phase 2A Deployment Script${NC}"
echo "====================================="
echo "Environment: $DEPLOYMENT_ENV"
echo "Compose File: $COMPOSE_FILE"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose v2 is not available"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found, creating from .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration"
            exit 1
        else
            print_error ".env.example file not found"
            exit 1
        fi
    fi
    
    print_status "Prerequisites check completed"
}

# Validate environment variables
validate_environment() {
    print_status "Validating environment variables..."
    
    source .env
    
    # Check required variables
    required_vars=("DB_PASSWORD")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    # Check AI API keys (at least one should be present)
    if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$MISTRAL_API_KEY" ]; then
        missing_vars+=("At least one AI API key (ANTHROPIC_API_KEY, OPENAI_API_KEY, or MISTRAL_API_KEY)")
    fi
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
    
    # Warnings for optional but recommended variables
    if [ -z "$STRIPE_SECRET_KEY" ]; then
        print_warning "STRIPE_SECRET_KEY not set - billing functionality will be disabled"
    fi
    
    if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" == "your-jwt-secret-key-change-in-production" ]; then
        print_warning "JWT_SECRET_KEY should be changed from default value"
    fi
    
    print_status "Environment validation completed"
}

# Setup directories
setup_directories() {
    print_status "Setting up directories..."
    
    mkdir -p $LOG_DIR $BACKUP_DIR
    mkdir -p ./data ./monitoring/grafana/{dashboards,datasources}
    
    # Set appropriate permissions
    chmod 755 $LOG_DIR $BACKUP_DIR ./data
    
    print_status "Directories setup completed"
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Pull latest images
    docker compose -f $COMPOSE_FILE pull
    
    # Build the application
    docker compose -f $COMPOSE_FILE build --no-cache aicrm-app
    
    # Start core services (without monitoring by default)
    docker compose -f $COMPOSE_FILE up -d postgres redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Start main application
    docker compose -f $COMPOSE_FILE up -d aicrm-app celery-worker
    
    print_status "Services deployment completed"
}

# Setup monitoring (optional)
setup_monitoring() {
    if [ "${ENABLE_MONITORING:-false}" == "true" ]; then
        print_status "Setting up monitoring stack..."
        docker compose -f $COMPOSE_FILE --profile monitoring up -d
        print_status "Monitoring stack is available at http://localhost:3000 (Grafana)"
    else
        print_warning "Monitoring disabled. Set ENABLE_MONITORING=true to enable"
    fi
}

# Health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check main application
    if curl -f http://localhost/health &> /dev/null; then
        print_status "Application health check passed"
    else
        print_error "Application health check failed"
        docker compose -f $COMPOSE_FILE logs aicrm-app
        exit 1
    fi
    
    # Check API endpoints
    if curl -f http://localhost/api/health &> /dev/null; then
        print_status "API health check passed"
    else
        print_warning "API health check failed"
    fi
    
    # Check database connectivity
    if docker compose -f $COMPOSE_FILE exec -T postgres pg_isready -U aicrm_user -d aicrm_db &> /dev/null; then
        print_status "Database connectivity check passed"
    else
        print_error "Database connectivity check failed"
        exit 1
    fi
    
    print_status "Health checks completed"
}

# Display deployment summary
show_deployment_summary() {
    echo ""
    echo -e "${GREEN}🎉 Deployment Completed Successfully!${NC}"
    echo "====================================="
    echo ""
    echo "📊 Service URLs:"
    echo "  • Main Application: http://localhost"
    echo "  • API Documentation: http://localhost/docs"
    echo "  • Health Check: http://localhost/health"
    
    if [ "${ENABLE_MONITORING:-false}" == "true" ]; then
        echo "  • Grafana: http://localhost:3000 (admin/admin123)"
        echo "  • Prometheus: http://localhost:9090"
    fi
    
    echo ""
    echo "📋 Available Commands:"
    echo "  • View logs: docker compose -f $COMPOSE_FILE logs -f"
    echo "  • Scale workers: docker compose -f $COMPOSE_FILE up -d --scale celery-worker=3"
    echo "  • Database backup: ./scripts/backup.sh"
    echo "  • Stop services: docker compose -f $COMPOSE_FILE down"
    echo ""
    
    # Show service status
    echo "🔍 Current Service Status:"
    docker compose -f $COMPOSE_FILE ps
    
    echo ""
    echo -e "${BLUE}🔧 Next Steps:${NC}"
    echo "1. Configure your domain and SSL certificates"
    echo "2. Set up monitoring alerts"
    echo "3. Configure backup schedules"
    echo "4. Review security settings"
    echo ""
}

# Backup existing deployment
backup_existing() {
    if docker compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        print_status "Backing up existing deployment..."
        
        # Create backup directory with timestamp
        backup_timestamp=$(date +%Y%m%d_%H%M%S)
        backup_path="$BACKUP_DIR/pre_deploy_$backup_timestamp"
        mkdir -p "$backup_path"
        
        # Database backup
        if docker compose -f $COMPOSE_FILE exec -T postgres pg_dump -U aicrm_user aicrm_db > "$backup_path/database.sql" 2>/dev/null; then
            print_status "Database backup created: $backup_path/database.sql"
        else
            print_warning "Database backup failed or database not running"
        fi
        
        # Configuration backup
        cp -r ./logs "$backup_path/" 2>/dev/null || true
        
        print_status "Backup completed: $backup_path"
    fi
}

# Rollback function
rollback() {
    print_error "Deployment failed. Rolling back..."
    
    # Stop current deployment
    docker compose -f $COMPOSE_FILE down
    
    # Show logs for debugging
    print_status "Recent logs:"
    docker compose -f $COMPOSE_FILE logs --tail=50
    
    exit 1
}

# Main deployment flow
main() {
    # Set trap for cleanup on failure
    trap rollback ERR
    
    case "${1:-deploy}" in
        "deploy"|"")
            check_prerequisites
            validate_environment
            setup_directories
            backup_existing
            deploy_services
            setup_monitoring
            run_health_checks
            show_deployment_summary
            ;;
        "stop")
            print_status "Stopping AI-CRM services..."
            docker compose -f $COMPOSE_FILE down
            print_status "Services stopped"
            ;;
        "restart")
            print_status "Restarting AI-CRM services..."
            docker compose -f $COMPOSE_FILE restart
            print_status "Services restarted"
            ;;
        "logs")
            docker compose -f $COMPOSE_FILE logs -f
            ;;
        "status")
            docker compose -f $COMPOSE_FILE ps
            ;;
        "backup")
            ./scripts/backup.sh
            ;;
        "help")
            echo "AI-CRM Deployment Script"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  deploy     - Deploy the application (default)"
            echo "  stop       - Stop all services"
            echo "  restart    - Restart all services"
            echo "  logs       - Follow application logs"
            echo "  status     - Show service status"
            echo "  backup     - Create database backup"
            echo "  help       - Show this help message"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"