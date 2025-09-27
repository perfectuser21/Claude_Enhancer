#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 - Optimized Docker Build Script
# Multi-stage build with layer caching and health checks
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="claude-enhancer"
VERSION="${VERSION:-1.0.0}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_TARGET="${BUILD_TARGET:-production}"
FRONTEND_BUILD_TARGET="${FRONTEND_BUILD_TARGET:-production}"

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

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    log_success "All dependencies are available"
}

# Build backend image
build_backend() {
    log_info "Building backend image..."

    docker build \
        --target $BUILD_TARGET \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VCS_REF="$VCS_REF" \
        --build-arg VERSION="$VERSION" \
        --tag ${PROJECT_NAME}-backend:${VERSION} \
        --tag ${PROJECT_NAME}-backend:latest \
        --file Dockerfile \
        .

    log_success "Backend image built successfully"
}

# Build frontend image
build_frontend() {
    log_info "Building frontend image..."

    cd frontend

    docker build \
        --target $FRONTEND_BUILD_TARGET \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VCS_REF="$VCS_REF" \
        --build-arg VERSION="$VERSION" \
        --build-arg REACT_APP_API_URL="/api" \
        --build-arg REACT_APP_ENVIRONMENT="$BUILD_TARGET" \
        --tag ${PROJECT_NAME}-frontend:${VERSION} \
        --tag ${PROJECT_NAME}-frontend:latest \
        --file Dockerfile \
        .

    cd ..
    log_success "Frontend image built successfully"
}

# Build with cache optimization
build_with_cache() {
    log_info "Building with cache optimization..."

    # Use BuildKit for better caching
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1

    # Build images with cache
    docker-compose build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VCS_REF="$VCS_REF" \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_TARGET="$BUILD_TARGET" \
        --build-arg FRONTEND_BUILD_TARGET="$FRONTEND_BUILD_TARGET"

    log_success "Images built with cache optimization"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."

    # Start services
    docker-compose up -d

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30

    # Check backend health
    log_info "Checking backend health..."
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend is healthy"
    else
        log_error "Backend health check failed"
        docker-compose logs backend
        return 1
    fi

    # Check frontend health
    log_info "Checking frontend health..."
    if curl -f http://localhost:80/health > /dev/null 2>&1; then
        log_success "Frontend is healthy"
    else
        log_error "Frontend health check failed"
        docker-compose logs frontend
        return 1
    fi

    # Check database health
    log_info "Checking database health..."
    if docker-compose exec -T database pg_isready -U claude_user -d claude_enhancer > /dev/null 2>&1; then
        log_success "Database is healthy"
    else
        log_error "Database health check failed"
        docker-compose logs database
        return 1
    fi

    # Check Redis health
    log_info "Checking Redis health..."
    if docker-compose exec -T cache redis-cli ping | grep -q PONG; then
        log_success "Redis is healthy"
    else
        log_error "Redis health check failed"
        docker-compose logs cache
        return 1
    fi

    log_success "All health checks passed"
}

# Clean up unused images
cleanup() {
    log_info "Cleaning up unused images..."

    docker image prune -f
    docker container prune -f

    log_success "Cleanup completed"
}

# Performance test
performance_test() {
    log_info "Running basic performance test..."

    # Simple load test with curl
    for i in {1..10}; do
        curl -s -o /dev/null -w "%{time_total}\n" http://localhost:8000/health
    done | awk '{sum+=$1; count++} END {print "Average response time: " sum/count " seconds"}'

    log_success "Performance test completed"
}

# Main execution
main() {
    log_info "Starting Claude Enhancer 5.1 build process..."
    log_info "Version: $VERSION"
    log_info "Build target: $BUILD_TARGET"
    log_info "Frontend target: $FRONTEND_BUILD_TARGET"
    log_info "VCS Ref: $VCS_REF"

    check_dependencies

    case "${1:-all}" in
        "backend")
            build_backend
            ;;
        "frontend")
            build_frontend
            ;;
        "cache")
            build_with_cache
            ;;
        "health")
            run_health_checks
            ;;
        "cleanup")
            cleanup
            ;;
        "performance")
            performance_test
            ;;
        "all")
            build_with_cache
            run_health_checks
            performance_test
            cleanup
            ;;
        *)
            log_error "Usage: $0 {backend|frontend|cache|health|cleanup|performance|all}"
            exit 1
            ;;
    esac

    log_success "Build process completed successfully!"
}

# Handle signals
trap 'log_error "Build interrupted"; docker-compose down; exit 1' INT TERM

# Execute main function
main "$@"