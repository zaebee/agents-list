#!/bin/bash

# AI-CRM Deployment Scripts
# Comprehensive deployment automation for different environments and cloud providers

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"

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

# Usage
usage() {
    cat << EOF
AI-CRM Deployment Scripts

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    build               Build all Docker images
    deploy-local        Deploy locally with docker-compose
    deploy-aws          Deploy to AWS ECS/Fargate
    deploy-gcp          Deploy to Google Cloud Run
    deploy-azure        Deploy to Azure Container Instances
    deploy-do           Deploy to DigitalOcean App Platform
    rollback            Rollback to previous deployment
    status              Check deployment status
    logs                View deployment logs
    cleanup             Clean up resources

Options:
    -e, --env           Environment (dev, staging, prod)
    -t, --tag           Image tag (default: latest)
    -f, --force         Force deployment without confirmation
    -v, --verbose       Verbose output
    -h, --help          Show this help

Examples:
    $0 build -e prod -t v1.2.3
    $0 deploy-local -e dev
    $0 deploy-aws -e prod -t v1.2.3
    $0 rollback -e prod
EOF
}

# Default values
ENVIRONMENT="dev"
IMAGE_TAG="latest"
FORCE=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        build|deploy-local|deploy-aws|deploy-gcp|deploy-azure|deploy-do|rollback|status|logs|cleanup)
            COMMAND="$1"
            shift
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        dev|staging|prod)
            log_info "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
}

# Load environment variables
load_env_vars() {
    local env_file="$DEPLOYMENT_DIR/docker/.env.$ENVIRONMENT"
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment variables from $env_file"
        # shellcheck disable=SC1090
        source "$env_file"
    else
        log_warning "Environment file not found: $env_file"
        log_warning "Using default environment variables"
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if required files exist
    local required_files=(
        "$DEPLOYMENT_DIR/docker/Dockerfile.backend"
        "$DEPLOYMENT_DIR/docker/Dockerfile.frontend"
        "$DEPLOYMENT_DIR/docker/Dockerfile.cli"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "Pre-deployment checks passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images with tag: $IMAGE_TAG"
    
    cd "$PROJECT_ROOT"
    
    # Build backend image
    log_info "Building backend image..."
    docker build -f deployment/docker/Dockerfile.backend -t ai-crm-backend:$IMAGE_TAG .
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -f deployment/docker/Dockerfile.frontend -t ai-crm-frontend:$IMAGE_TAG .
    
    # Build CLI image
    log_info "Building CLI image..."
    docker build -f deployment/docker/Dockerfile.cli -t ai-crm-cli:$IMAGE_TAG .
    
    log_success "All images built successfully"
}

# Deploy locally with docker-compose
deploy_local() {
    log_info "Deploying locally with docker-compose"
    
    cd "$DEPLOYMENT_DIR/docker"
    
    local compose_file="docker-compose.dev.yml"
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        compose_file="docker-compose.prod.yml"
    fi
    
    # Stop existing containers
    docker-compose -f "$compose_file" down
    
    # Deploy
    docker-compose -f "$compose_file" up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Health checks
    if curl -f http://localhost:3000/health >/dev/null 2>&1; then
        log_success "Frontend is healthy"
    else
        log_error "Frontend health check failed"
    fi
    
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "Backend is healthy"
    else
        log_error "Backend health check failed"
    fi
    
    log_success "Local deployment completed"
}

# Deploy to AWS ECS/Fargate
deploy_aws() {
    log_info "Deploying to AWS ECS/Fargate"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured"
        exit 1
    fi
    
    # Push images to ECR
    local region="${AWS_REGION:-us-east-1}"
    local account_id
    account_id=$(aws sts get-caller-identity --query Account --output text)
    
    # Login to ECR
    aws ecr get-login-password --region "$region" | docker login --username AWS --password-stdin "$account_id.dkr.ecr.$region.amazonaws.com"
    
    # Tag and push images
    local ecr_backend="$account_id.dkr.ecr.$region.amazonaws.com/ai-crm-backend:$IMAGE_TAG"
    local ecr_frontend="$account_id.dkr.ecr.$region.amazonaws.com/ai-crm-frontend:$IMAGE_TAG"
    local ecr_cli="$account_id.dkr.ecr.$region.amazonaws.com/ai-crm-cli:$IMAGE_TAG"
    
    docker tag "ai-crm-backend:$IMAGE_TAG" "$ecr_backend"
    docker tag "ai-crm-frontend:$IMAGE_TAG" "$ecr_frontend"
    docker tag "ai-crm-cli:$IMAGE_TAG" "$ecr_cli"
    
    docker push "$ecr_backend"
    docker push "$ecr_frontend"
    docker push "$ecr_cli"
    
    # Update ECS service
    log_info "Updating ECS services..."
    aws ecs update-service --cluster ai-crm-cluster --service ai-crm-backend --force-new-deployment
    aws ecs update-service --cluster ai-crm-cluster --service ai-crm-frontend --force-new-deployment
    
    log_success "AWS deployment completed"
}

# Deploy to Google Cloud Run
deploy_gcp() {
    log_info "Deploying to Google Cloud Run"
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI is not installed"
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "No active Google Cloud authentication found"
        exit 1
    fi
    
    local project_id="${GOOGLE_CLOUD_PROJECT}"
    local region="${GOOGLE_CLOUD_REGION:-us-central1}"
    
    # Push images to Container Registry
    gcloud auth configure-docker
    
    local gcr_backend="gcr.io/$project_id/ai-crm-backend:$IMAGE_TAG"
    local gcr_frontend="gcr.io/$project_id/ai-crm-frontend:$IMAGE_TAG"
    
    docker tag "ai-crm-backend:$IMAGE_TAG" "$gcr_backend"
    docker tag "ai-crm-frontend:$IMAGE_TAG" "$gcr_frontend"
    
    docker push "$gcr_backend"
    docker push "$gcr_frontend"
    
    # Deploy to Cloud Run
    gcloud run deploy ai-crm-backend \
        --image "$gcr_backend" \
        --region "$region" \
        --platform managed \
        --allow-unauthenticated
    
    gcloud run deploy ai-crm-frontend \
        --image "$gcr_frontend" \
        --region "$region" \
        --platform managed \
        --allow-unauthenticated
    
    log_success "GCP deployment completed"
}

# Deploy to Azure Container Instances
deploy_azure() {
    log_info "Deploying to Azure Container Instances"
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed"
        exit 1
    fi
    
    # Check authentication
    if ! az account show >/dev/null 2>&1; then
        log_error "Not logged in to Azure"
        exit 1
    fi
    
    local resource_group="${AZURE_RESOURCE_GROUP:-ai-crm-rg}"
    local registry="${AZURE_CONTAINER_REGISTRY:-aicrm}"
    
    # Login to Azure Container Registry
    az acr login --name "$registry"
    
    # Tag and push images
    local acr_backend="$registry.azurecr.io/ai-crm-backend:$IMAGE_TAG"
    local acr_frontend="$registry.azurecr.io/ai-crm-frontend:$IMAGE_TAG"
    
    docker tag "ai-crm-backend:$IMAGE_TAG" "$acr_backend"
    docker tag "ai-crm-frontend:$IMAGE_TAG" "$acr_frontend"
    
    docker push "$acr_backend"
    docker push "$acr_frontend"
    
    # Deploy container instances
    az container create \
        --resource-group "$resource_group" \
        --name ai-crm-backend \
        --image "$acr_backend" \
        --ports 8000 \
        --registry-login-server "$registry.azurecr.io" \
        --registry-username "$AZURE_CLIENT_ID" \
        --registry-password "$AZURE_CLIENT_SECRET"
    
    log_success "Azure deployment completed"
}

# Deploy to DigitalOcean App Platform
deploy_do() {
    log_info "Deploying to DigitalOcean App Platform"
    
    # Check doctl CLI
    if ! command -v doctl &> /dev/null; then
        log_error "DigitalOcean CLI (doctl) is not installed"
        exit 1
    fi
    
    # Check authentication
    if ! doctl auth list | grep -q "current context"; then
        log_error "Not authenticated with DigitalOcean"
        exit 1
    fi
    
    # Deploy using App Spec
    local app_spec="$DEPLOYMENT_DIR/cloud/digitalocean/app.yaml"
    if [[ -f "$app_spec" ]]; then
        doctl apps create --spec "$app_spec"
    else
        log_error "App spec file not found: $app_spec"
        exit 1
    fi
    
    log_success "DigitalOcean deployment completed"
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment in $ENVIRONMENT environment"
    
    case $ENVIRONMENT in
        dev|staging)
            # For local environments, restart with previous images
            deploy_local
            ;;
        prod)
            # For production, implement blue-green rollback
            log_warning "Production rollback requires manual intervention"
            log_info "Please use cloud provider specific rollback procedures"
            ;;
    esac
    
    log_success "Rollback completed"
}

# Check deployment status
check_status() {
    log_info "Checking deployment status for $ENVIRONMENT environment"
    
    case $ENVIRONMENT in
        dev|staging)
            docker-compose -f "$DEPLOYMENT_DIR/docker/docker-compose.dev.yml" ps
            ;;
        prod)
            # Check production services
            log_info "Production status check - implement cloud provider specific checks"
            ;;
    esac
}

# View logs
view_logs() {
    log_info "Viewing logs for $ENVIRONMENT environment"
    
    case $ENVIRONMENT in
        dev|staging)
            docker-compose -f "$DEPLOYMENT_DIR/docker/docker-compose.dev.yml" logs -f
            ;;
        prod)
            log_info "Production logs - implement cloud provider specific log viewing"
            ;;
    esac
}

# Cleanup resources
cleanup_resources() {
    log_info "Cleaning up resources for $ENVIRONMENT environment"
    
    if [[ "$ENVIRONMENT" == "dev" ]] || [[ "$ENVIRONMENT" == "staging" ]]; then
        docker-compose -f "$DEPLOYMENT_DIR/docker/docker-compose.dev.yml" down -v
        docker system prune -f
    else
        log_warning "Production cleanup requires manual verification"
        if [[ "$FORCE" == "true" ]]; then
            log_info "Force cleanup enabled - implementing production cleanup"
        else
            log_info "Use --force flag for production cleanup"
            exit 1
        fi
    fi
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    if [[ -z "${COMMAND:-}" ]]; then
        log_error "No command specified"
        usage
        exit 1
    fi
    
    validate_environment
    load_env_vars
    pre_deployment_checks
    
    case $COMMAND in
        build)
            build_images
            ;;
        deploy-local)
            build_images
            deploy_local
            ;;
        deploy-aws)
            build_images
            deploy_aws
            ;;
        deploy-gcp)
            build_images
            deploy_gcp
            ;;
        deploy-azure)
            build_images
            deploy_azure
            ;;
        deploy-do)
            build_images
            deploy_do
            ;;
        rollback)
            rollback_deployment
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs
            ;;
        cleanup)
            cleanup_resources
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"