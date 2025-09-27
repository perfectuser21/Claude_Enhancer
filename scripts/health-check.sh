#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 - Enhanced Health Check Script
# Comprehensive health monitoring for all services
# =============================================================================

set -euo pipefail

# Configuration
TIMEOUT=30
RETRY_COUNT=3
RETRY_INTERVAL=5

# Service endpoints
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:80}"
DATABASE_HOST="${DATABASE_HOST:-localhost}"
DATABASE_PORT="${DATABASE_PORT:-5432}"
DATABASE_USER="${DATABASE_USER:-claude_user}"
DATABASE_NAME="${DATABASE_NAME:-claude_enhancer}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
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

# Health check functions
check_backend() {
    local url="$BACKEND_URL/health"
    log_info "Checking backend health: $url"

    for i in $(seq 1 $RETRY_COUNT); do
        if curl -sf --max-time $TIMEOUT "$url" > /dev/null; then
            log_success "Backend is healthy"
            return 0
        fi

        if [ $i -lt $RETRY_COUNT ]; then
            log_warning "Backend check failed (attempt $i/$RETRY_COUNT), retrying in ${RETRY_INTERVAL}s..."
            sleep $RETRY_INTERVAL
        fi
    done

    log_error "Backend health check failed after $RETRY_COUNT attempts"
    return 1
}

check_frontend() {
    local url="$FRONTEND_URL/health"
    log_info "Checking frontend health: $url"

    for i in $(seq 1 $RETRY_COUNT); do
        if curl -sf --max-time $TIMEOUT "$url" > /dev/null; then
            log_success "Frontend is healthy"
            return 0
        fi

        if [ $i -lt $RETRY_COUNT ]; then
            log_warning "Frontend check failed (attempt $i/$RETRY_COUNT), retrying in ${RETRY_INTERVAL}s..."
            sleep $RETRY_INTERVAL
        fi
    done

    log_error "Frontend health check failed after $RETRY_COUNT attempts"
    return 1
}

check_database() {
    log_info "Checking database health: $DATABASE_HOST:$DATABASE_PORT"

    for i in $(seq 1 $RETRY_COUNT); do
        if pg_isready -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER" -d "$DATABASE_NAME" > /dev/null 2>&1; then
            log_success "Database is healthy"
            return 0
        fi

        if [ $i -lt $RETRY_COUNT ]; then
            log_warning "Database check failed (attempt $i/$RETRY_COUNT), retrying in ${RETRY_INTERVAL}s..."
            sleep $RETRY_INTERVAL
        fi
    done

    log_error "Database health check failed after $RETRY_COUNT attempts"
    return 1
}

check_redis() {
    log_info "Checking Redis health: $REDIS_HOST:$REDIS_PORT"

    for i in $(seq 1 $RETRY_COUNT); do
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; then
            log_success "Redis is healthy"
            return 0
        fi

        if [ $i -lt $RETRY_COUNT ]; then
            log_warning "Redis check failed (attempt $i/$RETRY_COUNT), retrying in ${RETRY_INTERVAL}s..."
            sleep $RETRY_INTERVAL
        fi
    done

    log_error "Redis health check failed after $RETRY_COUNT attempts"
    return 1
}

check_api_endpoints() {
    log_info "Checking API endpoints..."

    # Check API documentation endpoint
    if curl -sf --max-time $TIMEOUT "$BACKEND_URL/docs" > /dev/null; then
        log_success "API documentation endpoint is accessible"
    else
        log_warning "API documentation endpoint is not accessible"
    fi

    # Check API version endpoint
    if curl -sf --max-time $TIMEOUT "$BACKEND_URL/api/v1/version" > /dev/null; then
        log_success "API version endpoint is accessible"
    else
        log_warning "API version endpoint is not accessible"
    fi
}

check_container_resources() {
    log_info "Checking container resources..."

    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not available for resource checking"
        return 0
    fi

    # Check container memory usage
    local containers=("claude-enhancer-backend" "claude-enhancer-frontend" "claude-enhancer-db" "claude-enhancer-redis")

    for container in "${containers[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "$container"; then
            local memory_usage=$(docker stats --no-stream --format "{{.MemUsage}}" "$container" 2>/dev/null || echo "N/A")
            local cpu_usage=$(docker stats --no-stream --format "{{.CPUPerc}}" "$container" 2>/dev/null || echo "N/A")
            log_info "$container - Memory: $memory_usage, CPU: $cpu_usage"
        else
            log_warning "Container $container is not running"
        fi
    done
}

check_disk_space() {
    log_info "Checking disk space..."

    local available_space=$(df -h . | awk 'NR==2 {print $4}')
    local usage_percent=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')

    log_info "Available disk space: $available_space"

    if [ "$usage_percent" -gt 90 ]; then
        log_warning "Disk usage is high: ${usage_percent}%"
    elif [ "$usage_percent" -gt 95 ]; then
        log_error "Disk usage is critical: ${usage_percent}%"
        return 1
    else
        log_success "Disk usage is normal: ${usage_percent}%"
    fi
}

perform_comprehensive_check() {
    log_info "Starting comprehensive health check..."

    local failed_checks=0

    # Core service checks
    check_database || ((failed_checks++))
    check_redis || ((failed_checks++))
    check_backend || ((failed_checks++))
    check_frontend || ((failed_checks++))

    # Additional checks
    check_api_endpoints
    check_container_resources
    check_disk_space || ((failed_checks++))

    # Summary
    if [ $failed_checks -eq 0 ]; then
        log_success "All health checks passed successfully!"
        return 0
    else
        log_error "$failed_checks health check(s) failed"
        return 1
    fi
}

# Main execution
main() {
    case "${1:-all}" in
        "backend")
            check_backend
            ;;
        "frontend")
            check_frontend
            ;;
        "database")
            check_database
            ;;
        "redis")
            check_redis
            ;;
        "api")
            check_api_endpoints
            ;;
        "resources")
            check_container_resources
            ;;
        "disk")
            check_disk_space
            ;;
        "all")
            perform_comprehensive_check
            ;;
        *)
            echo "Usage: $0 {backend|frontend|database|redis|api|resources|disk|all}"
            echo "  backend   - Check backend service health"
            echo "  frontend  - Check frontend service health"
            echo "  database  - Check PostgreSQL database health"
            echo "  redis     - Check Redis cache health"
            echo "  api       - Check API endpoints"
            echo "  resources - Check container resource usage"
            echo "  disk      - Check disk space"
            echo "  all       - Run all health checks"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"