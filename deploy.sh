#!/bin/bash
# =============================================================================
# Deployment Script for Claude Enhancer Claude Enhancer
# Supports Docker Compose and Kubernetes deployment
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="perfect21-claude-enhancer"
VERSION="${VERSION:-latest}"
ENVIRONMENT="${ENVIRONMENT:-development}"

# Functions
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

show_help() {
    cat << EOF
Claude Enhancer Claude Enhancer Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    docker:dev          Deploy using Docker Compose (development)
    docker:prod         Deploy using Docker Compose (production)
    k8s:deploy          Deploy to Kubernetes
    k8s:undeploy        Remove from Kubernetes
    build               Build Docker images
    clean               Clean up resources
    health              Check deployment health
    logs                Show application logs
    help                Show this help message

Options:
    -v, --version       Specify version tag (default: latest)
    -e, --env           Specify environment (development|production)
    --skip-build        Skip building images
    --force             Force deployment (remove existing)

Examples:
    $0 docker:dev                   # Deploy development environment
    $0 docker:prod -v 1.0.0        # Deploy production with specific version
    $0 k8s:deploy -e production     # Deploy to Kubernetes production
    $0 build -v 1.2.3              # Build images with version 1.2.3
    $0 health                       # Check deployment health

EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

build_images() {
    log_info "Building Docker images..."

    docker build \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="$VERSION" \
        -t "${PROJECT_NAME}:${VERSION}" \
        -t "${PROJECT_NAME}:latest" \
        .

    log_success "Docker images built successfully"
}

deploy_docker_dev() {
    log_info "Deploying development environment with Docker Compose..."

    # Copy development environment file
    if [[ ! -f .env ]]; then
        cp .env.development .env
        log_info "Created .env file from .env.development"
    fi

    # Start services
    docker-compose up -d

    log_success "Development environment deployed"
    log_info "Application will be available at: http://localhost:8080"
    log_info "API Documentation: http://localhost:8080/docs"
    log_info "Grafana: http://localhost:3001 (admin/admin123)"
    log_info "pgAdmin: http://localhost:5050 (admin@claude-enhancer.local/admin123)"
}

deploy_docker_prod() {
    log_info "Deploying production environment with Docker Compose..."

    # Check if production environment file exists
    if [[ ! -f .env.production ]]; then
        log_error "Production environment file (.env.production) not found"
        log_info "Please create .env.production with your production settings"
        exit 1
    fi

    # Copy production environment file
    cp .env.production .env

    # Deploy production stack
    docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d

    log_success "Production environment deployed"
    log_info "Application will be available at: https://your-domain.com"
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    # Apply Kubernetes manifests
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secrets.yaml
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/redis.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/claude-enhancer.yaml
    kubectl apply -f k8s/monitoring.yaml

    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/claude-enhancer -n claude-enhancer

    log_success "Kubernetes deployment completed"
}

undeploy_kubernetes() {
    log_info "Removing Kubernetes deployment..."

    kubectl delete -f k8s/ --ignore-not-found=true

    log_success "Kubernetes deployment removed"
}

check_health() {
    log_info "Checking deployment health..."

    # Check Docker Compose deployment
    if docker-compose ps | grep -q "Up"; then
        log_info "Docker Compose services:"
        docker-compose ps

        # Check application health
        if curl -f http://localhost:8080/api/v1/health &> /dev/null; then
            log_success "Application is healthy"
        else
            log_warning "Application health check failed"
        fi
    fi

    # Check Kubernetes deployment
    if kubectl get namespace claude-enhancer &> /dev/null; then
        log_info "Kubernetes deployment status:"
        kubectl get pods -n claude-enhancer
        kubectl get services -n claude-enhancer
    fi
}

show_logs() {
    log_info "Showing application logs..."

    # Docker Compose logs
    if docker-compose ps | grep -q "Up"; then
        docker-compose logs -f claude-enhancer
    elif kubectl get namespace claude-enhancer &> /dev/null; then
        # Kubernetes logs
        kubectl logs -f deployment/claude-enhancer -n claude-enhancer
    else
        log_warning "No running deployment found"
    fi
}

clean_resources() {
    log_info "Cleaning up resources..."

    # Stop Docker Compose
    docker-compose down -v --remove-orphans 2>/dev/null || true

    # Remove Docker images
    docker rmi "${PROJECT_NAME}:${VERSION}" 2>/dev/null || true
    docker rmi "${PROJECT_NAME}:latest" 2>/dev/null || true

    # Clean up Kubernetes
    undeploy_kubernetes 2>/dev/null || true

    log_success "Resources cleaned up"
}

# Parse command line arguments
SKIP_BUILD=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            COMMAND="$1"
            shift
            break
            ;;
    esac
done

# Main execution
case "${COMMAND:-help}" in
    docker:dev)
        check_prerequisites
        if [[ "$SKIP_BUILD" == "false" ]]; then
            build_images
        fi
        deploy_docker_dev
        ;;
    docker:prod)
        check_prerequisites
        if [[ "$SKIP_BUILD" == "false" ]]; then
            build_images
        fi
        deploy_docker_prod
        ;;
    k8s:deploy)
        if [[ "$SKIP_BUILD" == "false" ]]; then
            build_images
        fi
        deploy_kubernetes
        ;;
    k8s:undeploy)
        undeploy_kubernetes
        ;;
    build)
        check_prerequisites
        build_images
        ;;
    health)
        check_health
        ;;
    logs)
        show_logs
        ;;
    clean)
        clean_resources
        ;;
    help)
        show_help
        ;;
    *)
        log_error "Unknown command: ${COMMAND:-}"
        show_help
        exit 1
        ;;
esac