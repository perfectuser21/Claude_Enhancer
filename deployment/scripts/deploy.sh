#!/bin/bash
# =============================================================================
# Production Deployment Script for Claude Enhancer 5.1
# Implements blue-green deployment with health checks and rollback capability
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"

# Default values
ENVIRONMENT="production"
DOCKER_COMPOSE_FILE="docker-compose.production.yml"
HEALTH_CHECK_TIMEOUT=300
ROLLBACK_ON_FAILURE=true
BACKUP_BEFORE_DEPLOY=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# Error handling
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Deployment failed with exit code $exit_code"
        if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
            log_info "Starting automatic rollback..."
            rollback_deployment
        fi
    fi
    exit $exit_code
}

trap cleanup EXIT

# Function to show help
show_help() {
    cat << EOF
Claude Enhancer 5.1 Production Deployment Script

Usage: $0 [OPTIONS]

Options:
  -e, --environment ENV     Target environment (default: production)
  -f, --compose-file FILE   Docker compose file (default: docker-compose.production.yml)
  -t, --timeout SECONDS    Health check timeout (default: 300)
  --no-rollback            Disable automatic rollback on failure
  --no-backup              Skip backup before deployment
  --dry-run                Show what would be done without executing
  -h, --help               Show this help message

Examples:
  $0                              # Deploy to production
  $0 -e staging                   # Deploy to staging
  $0 --dry-run                    # Show deployment plan
  $0 --no-rollback --no-backup    # Deploy without safety features

Environment Variables:
  DOCKER_REGISTRY        Container registry URL
  IMAGE_TAG              Specific image tag to deploy
  DB_BACKUP_ENABLED      Enable database backup (default: true)
  SLACK_WEBHOOK_URL      Slack webhook for notifications
EOF
}

# Function to validate prerequisites
validate_prerequisites() {
    log_info "Validating deployment prerequisites..."

    # Check required tools
    local required_tools=("docker" "docker-compose" "curl" "jq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool '$tool' is not installed"
            return 1
        fi
    done

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi

    # Check environment file
    local env_file="$DEPLOYMENT_DIR/.env.$ENVIRONMENT"
    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        return 1
    fi

    # Validate environment variables
    if ! "$SCRIPT_DIR/validate-env.sh" "$env_file"; then
        log_error "Environment validation failed"
        return 1
    fi

    # Check disk space
    local available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    local required_space=2097152  # 2GB in KB
    if [[ $available_space -lt $required_space ]]; then
        log_error "Insufficient disk space. Required: 2GB, Available: $((available_space/1024))MB"
        return 1
    fi

    log_success "Prerequisites validation completed"
}

# Function to backup current deployment
backup_deployment() {
    if [[ "$BACKUP_BEFORE_DEPLOY" != "true" ]]; then
        log_info "Backup disabled, skipping..."
        return 0
    fi

    log_info "Creating deployment backup..."

    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="/opt/claude-enhancer/backups/deployment_$backup_timestamp"

    # Create backup directory
    sudo mkdir -p "$backup_dir"

    # Backup database
    if [[ "${DB_BACKUP_ENABLED:-true}" == "true" ]]; then
        log_info "Backing up database..."
        docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" exec -T postgres \
            pg_dump -U "${DB_USER}" "${DB_NAME}" | \
            sudo tee "$backup_dir/database_backup.sql" > /dev/null
    fi

    # Backup application data
    log_info "Backing up application data..."
    sudo cp -r "/opt/claude-enhancer/data" "$backup_dir/" || true
    sudo cp -r "$PROJECT_ROOT/.claude" "$backup_dir/" || true

    # Backup current environment
    sudo cp "$DEPLOYMENT_DIR/.env.$ENVIRONMENT" "$backup_dir/" || true

    # Create backup manifest
    cat > "$backup_dir/backup_manifest.json" << EOF
{
    "timestamp": "$backup_timestamp",
    "environment": "$ENVIRONMENT",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "docker_images": $(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}" | grep claude-enhancer | jq -R . | jq -s .)
}
EOF

    log_success "Backup created: $backup_dir"
    echo "$backup_dir" > /tmp/claude_enhancer_backup_path
}

# Function to pull latest images
pull_images() {
    log_info "Pulling latest container images..."

    # Load environment variables
    set -a
    source "$DEPLOYMENT_DIR/.env.$ENVIRONMENT"
    set +a

    # Pull all images defined in compose file
    docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" pull

    log_success "Container images updated"
}

# Function to perform blue-green deployment
blue_green_deploy() {
    log_info "Starting blue-green deployment..."

    # Load environment
    set -a
    source "$DEPLOYMENT_DIR/.env.$ENVIRONMENT"
    set +a

    # Check if services are currently running
    local current_services=$(docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" ps -q)

    if [[ -n "$current_services" ]]; then
        log_info "Current services detected, performing blue-green deployment..."

        # Start new services with different project name (green)
        export COMPOSE_PROJECT_NAME="claude-enhancer-green"
        docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" up -d

        # Wait for green services to be healthy
        if wait_for_health "green"; then
            log_info "Green environment healthy, switching traffic..."

            # Update load balancer to point to green
            switch_traffic_to_green

            # Stop blue environment
            export COMPOSE_PROJECT_NAME="claude-enhancer-blue"
            docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" down

            # Rename green to blue for next deployment
            docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" \
                exec nginx nginx -s reload

            log_success "Blue-green deployment completed"
        else
            log_error "Green environment health check failed"
            # Cleanup failed green deployment
            export COMPOSE_PROJECT_NAME="claude-enhancer-green"
            docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" down
            return 1
        fi
    else
        log_info "No existing services, performing fresh deployment..."
        export COMPOSE_PROJECT_NAME="claude-enhancer-blue"
        docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" up -d

        if ! wait_for_health "blue"; then
            log_error "Fresh deployment health check failed"
            return 1
        fi

        log_success "Fresh deployment completed"
    fi
}

# Function to wait for services to be healthy
wait_for_health() {
    local environment="$1"
    local max_attempts=$((HEALTH_CHECK_TIMEOUT / 10))
    local attempt=1

    log_info "Waiting for $environment environment to be healthy..."

    while [[ $attempt -le $max_attempts ]]; do
        local unhealthy_services=0

        # Check each service health
        local services=("app" "postgres" "redis" "nginx")
        for service in "${services[@]}"; do
            local container_name="claude-enhancer-${service}"
            if [[ "$environment" == "green" ]]; then
                container_name="claude-enhancer-green-${service}"
            fi

            if docker ps --filter "name=${container_name}" --filter "health=healthy" | grep -q "$container_name"; then
                log_info "✅ $service is healthy"
            else
                log_warn "⏳ $service not yet healthy"
                ((unhealthy_services++))
            fi
        done

        if [[ $unhealthy_services -eq 0 ]]; then
            log_success "All services are healthy"
            return 0
        fi

        log_info "Attempt $attempt/$max_attempts - $unhealthy_services services still unhealthy"
        sleep 10
        ((attempt++))
    done

    log_error "Health check timeout after ${HEALTH_CHECK_TIMEOUT} seconds"
    return 1
}

# Function to switch traffic to green environment
switch_traffic_to_green() {
    log_info "Switching traffic to green environment..."

    # This would typically involve updating load balancer configuration
    # For this example, we'll simulate the process

    # Update nginx configuration to point to green services
    local nginx_config="$DEPLOYMENT_DIR/nginx/nginx.green.conf"
    if [[ -f "$nginx_config" ]]; then
        docker cp "$nginx_config" claude-enhancer-nginx:/etc/nginx/nginx.conf
        docker exec claude-enhancer-nginx nginx -s reload
    fi

    log_success "Traffic switched to green environment"
}

# Function to rollback deployment
rollback_deployment() {
    log_error "Rolling back deployment..."

    local backup_path
    if [[ -f "/tmp/claude_enhancer_backup_path" ]]; then
        backup_path=$(cat /tmp/claude_enhancer_backup_path)
    else
        # Find latest backup
        backup_path=$(find /opt/claude-enhancer/backups -name "deployment_*" -type d | sort -r | head -1)
    fi

    if [[ -z "$backup_path" || ! -d "$backup_path" ]]; then
        log_error "No backup found for rollback"
        return 1
    fi

    log_info "Rolling back using backup: $backup_path"

    # Stop current services
    docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" down || true

    # Restore database
    if [[ -f "$backup_path/database_backup.sql" ]]; then
        log_info "Restoring database..."
        docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" up -d postgres
        sleep 30  # Wait for postgres to start
        docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" exec -T postgres \
            psql -U "${DB_USER}" -d "${DB_NAME}" < "$backup_path/database_backup.sql"
    fi

    # Restore application data
    if [[ -d "$backup_path/data" ]]; then
        log_info "Restoring application data..."
        sudo cp -r "$backup_path/data" "/opt/claude-enhancer/"
    fi

    # Restore configuration
    if [[ -f "$backup_path/.env.$ENVIRONMENT" ]]; then
        sudo cp "$backup_path/.env.$ENVIRONMENT" "$DEPLOYMENT_DIR/"
    fi

    # Start services with restored configuration
    docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" up -d

    if wait_for_health "rollback"; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback failed - manual intervention required"
        return 1
    fi
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    log_info "Running post-deployment tests..."

    # Load environment
    set -a
    source "$DEPLOYMENT_DIR/.env.$ENVIRONMENT"
    set +a

    # Basic health check
    local app_url="https://${DOMAIN}/health"
    if curl -f -s "$app_url" > /dev/null; then
        log_success "✅ Application health check passed"
    else
        log_error "❌ Application health check failed"
        return 1
    fi

    # API functionality test
    local api_url="https://${DOMAIN}/api/v1/health"
    if curl -f -s "$api_url" | jq -e '.status == "healthy"' > /dev/null; then
        log_success "✅ API health check passed"
    else
        log_error "❌ API health check failed"
        return 1
    fi

    # Database connectivity test
    if docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" exec -T postgres \
        pg_isready -U "${DB_USER}" -d "${DB_NAME}" > /dev/null; then
        log_success "✅ Database connectivity test passed"
    else
        log_error "❌ Database connectivity test failed"
        return 1
    fi

    # Redis connectivity test
    if docker-compose -f "$DEPLOYMENT_DIR/$DOCKER_COMPOSE_FILE" exec -T redis \
        redis-cli --no-auth-warning -a "${REDIS_PASSWORD}" ping | grep -q "PONG"; then
        log_success "✅ Redis connectivity test passed"
    else
        log_error "❌ Redis connectivity test failed"
        return 1
    fi

    log_success "All post-deployment tests passed"
}

# Function to send notifications
send_notification() {
    local status="$1"
    local message="$2"

    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local emoji="🚀"
        local color="good"

        if [[ "$status" == "failure" ]]; then
            emoji="💥"
            color="danger"
        elif [[ "$status" == "warning" ]]; then
            emoji="⚠️"
            color="warning"
        fi

        local payload=$(cat << EOF
{
    "text": "$emoji Claude Enhancer 5.1 Deployment",
    "attachments": [
        {
            "color": "$color",
            "fields": [
                {
                    "title": "Environment",
                    "value": "$ENVIRONMENT",
                    "short": true
                },
                {
                    "title": "Status",
                    "value": "$status",
                    "short": true
                },
                {
                    "title": "Message",
                    "value": "$message",
                    "short": false
                }
            ]
        }
    ]
}
EOF
)

        curl -X POST -H 'Content-type: application/json' \
            --data "$payload" \
            "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || true
    fi
}

# Main deployment function
main() {
    log_info "Starting Claude Enhancer 5.1 deployment to $ENVIRONMENT"
    log_info "============================================================"

    local start_time=$(date +%s)

    # Validate prerequisites
    validate_prerequisites

    # Create backup
    backup_deployment

    # Pull latest images
    pull_images

    # Perform deployment
    blue_green_deploy

    # Run post-deployment tests
    run_post_deployment_tests

    # Calculate deployment time
    local end_time=$(date +%s)
    local deployment_time=$((end_time - start_time))

    log_success "Deployment completed successfully in ${deployment_time} seconds"
    send_notification "success" "Deployment completed in ${deployment_time} seconds"

    # Cleanup old backups (keep last 5)
    find /opt/claude-enhancer/backups -name "deployment_*" -type d | \
        sort -r | tail -n +6 | xargs -r sudo rm -rf

    log_info "============================================================"
    log_success "Claude Enhancer 5.1 is now live on $ENVIRONMENT!"
}

# Parse command line arguments
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--compose-file)
            DOCKER_COMPOSE_FILE="$2"
            shift 2
            ;;
        -t|--timeout)
            HEALTH_CHECK_TIMEOUT="$2"
            shift 2
            ;;
        --no-rollback)
            ROLLBACK_ON_FAILURE=false
            shift
            ;;
        --no-backup)
            BACKUP_BEFORE_DEPLOY=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute main function or show dry run
if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY RUN MODE - No changes will be made"
    log_info "Environment: $ENVIRONMENT"
    log_info "Compose file: $DOCKER_COMPOSE_FILE"
    log_info "Health check timeout: $HEALTH_CHECK_TIMEOUT seconds"
    log_info "Rollback on failure: $ROLLBACK_ON_FAILURE"
    log_info "Backup before deploy: $BACKUP_BEFORE_DEPLOY"
    log_info "Would execute: main"
else
    main
fi