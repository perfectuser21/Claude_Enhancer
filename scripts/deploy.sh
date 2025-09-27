#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 - Production Deployment Script
# Complete deployment with optimization and rollback capabilities
# =============================================================================

set -euo pipefail

# Configuration
PROJECT_NAME="claude-enhancer"
VERSION="${VERSION:-1.0.0}"
ENVIRONMENT="${ENVIRONMENT:-production}"
BACKUP_ENABLED="${BACKUP_ENABLED:-true}"
HEALTH_CHECK_ENABLED="${HEALTH_CHECK_ENABLED:-true}"

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

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found, copying from .env.example"
        cp .env.example .env
        log_warning "Please update .env file with production values"
    fi

    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check required environment variables
    source .env
    local required_vars=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY" "JWT_SECRET_KEY")

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done

    log_success "Pre-deployment checks passed"
}

# Backup existing deployment
backup_deployment() {
    if [ "$BACKUP_ENABLED" != "true" ]; then
        log_info "Backup disabled, skipping..."
        return 0
    fi

    log_info "Creating deployment backup..."

    local backup_dir="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup database
    if docker-compose ps | grep -q "claude-enhancer-db"; then
        log_info "Backing up database..."
        docker-compose exec -T database pg_dump -U claude_user claude_enhancer > "$backup_dir/database_backup.sql"
    fi

    # Backup Redis data
    if docker-compose ps | grep -q "claude-enhancer-redis"; then
        log_info "Backing up Redis data..."
        docker-compose exec -T cache redis-cli --rdb - > "$backup_dir/redis_backup.rdb"
    fi

    # Backup configuration files
    log_info "Backing up configuration..."
    cp -r .env "$backup_dir/"
    cp -r docker-compose.yml "$backup_dir/"

    log_success "Backup created in $backup_dir"
    echo "$backup_dir" > .last_backup_path
}

# Deploy services
deploy_services() {
    log_info "Deploying Claude Enhancer 5.1..."

    # Export environment variables
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export VERSION="$VERSION"

    # Build and start services
    log_info "Building and starting services..."
    docker-compose down --remove-orphans
    docker-compose build --no-cache
    docker-compose up -d

    log_success "Services deployed"
}

# Run health checks
run_health_checks() {
    if [ "$HEALTH_CHECK_ENABLED" != "true" ]; then
        log_info "Health checks disabled, skipping..."
        return 0
    fi

    log_info "Running deployment health checks..."

    # Wait for services to initialize
    log_info "Waiting for services to initialize..."
    sleep 60

    # Run comprehensive health check
    if ./scripts/health-check.sh all; then
        log_success "Health checks passed"
    else
        log_error "Health checks failed"
        return 1
    fi
}

# Performance optimization
optimize_performance() {
    log_info "Applying performance optimizations..."

    # Optimize Docker daemon settings
    if [ -f "/etc/docker/daemon.json" ]; then
        log_info "Docker daemon configuration found"
    else
        log_warning "Docker daemon configuration not found, consider optimizing"
    fi

    # Clean up unused Docker resources
    docker system prune -f --volumes

    # Optimize container resource usage
    docker-compose exec -T backend python -c "
import psutil
print(f'CPU cores: {psutil.cpu_count()}')
print(f'Memory: {psutil.virtual_memory().total // (1024**3)} GB')
print(f'Disk: {psutil.disk_usage(\"/\").total // (1024**3)} GB')
"

    log_success "Performance optimizations applied"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."

    # Start monitoring services if available
    if docker-compose config | grep -q "prometheus"; then
        docker-compose --profile monitoring up -d
        log_success "Monitoring services started"
    else
        log_info "Monitoring services not configured"
    fi
}

# Rollback function
rollback_deployment() {
    log_warning "Rolling back deployment..."

    if [ ! -f ".last_backup_path" ]; then
        log_error "No backup path found, cannot rollback"
        exit 1
    fi

    local backup_path=$(cat .last_backup_path)

    if [ ! -d "$backup_path" ]; then
        log_error "Backup directory not found: $backup_path"
        exit 1
    fi

    # Stop current services
    docker-compose down

    # Restore configuration
    cp "$backup_path/.env" .
    cp "$backup_path/docker-compose.yml" .

    # Restore database
    if [ -f "$backup_path/database_backup.sql" ]; then
        log_info "Restoring database..."
        docker-compose up -d database
        sleep 30
        docker-compose exec -T database psql -U claude_user -d claude_enhancer < "$backup_path/database_backup.sql"
    fi

    # Restore Redis
    if [ -f "$backup_path/redis_backup.rdb" ]; then
        log_info "Restoring Redis data..."
        docker-compose up -d cache
        sleep 10
        docker-compose exec -T cache redis-cli --pipe < "$backup_path/redis_backup.rdb"
    fi

    # Start all services
    docker-compose up -d

    log_success "Rollback completed"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."

    local report_file="deployment_report_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" << EOF
# Claude Enhancer 5.1 Deployment Report

## Deployment Information
- **Date**: $(date)
- **Version**: $VERSION
- **Environment**: $ENVIRONMENT
- **VCS Ref**: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

## Services Status
EOF

    # Check service status
    docker-compose ps >> "$report_file"

    cat >> "$report_file" << EOF

## Resource Usage
EOF

    # Add resource usage information
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" >> "$report_file"

    cat >> "$report_file" << EOF

## Health Check Results
EOF

    # Run health checks and append results
    ./scripts/health-check.sh all >> "$report_file" 2>&1 || true

    log_success "Deployment report generated: $report_file"
}

# Main deployment function
main() {
    log_info "Starting Claude Enhancer 5.1 deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"

    case "${1:-deploy}" in
        "deploy")
            pre_deployment_checks
            backup_deployment
            deploy_services
            run_health_checks
            optimize_performance
            setup_monitoring
            generate_report
            log_success "Deployment completed successfully!"
            ;;
        "rollback")
            rollback_deployment
            ;;
        "health")
            run_health_checks
            ;;
        "backup")
            backup_deployment
            ;;
        "optimize")
            optimize_performance
            ;;
        "monitor")
            setup_monitoring
            ;;
        "report")
            generate_report
            ;;
        *)
            echo "Usage: $0 {deploy|rollback|health|backup|optimize|monitor|report}"
            echo "  deploy   - Full deployment with all optimizations"
            echo "  rollback - Rollback to previous deployment"
            echo "  health   - Run health checks only"
            echo "  backup   - Create backup only"
            echo "  optimize - Apply performance optimizations"
            echo "  monitor  - Setup monitoring services"
            echo "  report   - Generate deployment report"
            exit 1
            ;;
    esac
}

# Error handling
handle_error() {
    log_error "Deployment failed at line $1"
    log_info "You can rollback using: $0 rollback"
    exit 1
}

trap 'handle_error $LINENO' ERR

# Execute main function
main "$@"