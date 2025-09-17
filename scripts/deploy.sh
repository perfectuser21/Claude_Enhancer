#!/bin/bash
# Perfect21 Production Deployment Script
# Usage: ./scripts/deploy.sh [environment] [action]
# Examples:
#   ./scripts/deploy.sh staging deploy
#   ./scripts/deploy.sh production rollback
#   ./scripts/deploy.sh staging health-check

set -euo pipefail

# ==============================================
# CONFIGURATION
# ==============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${1:-staging}"
ACTION="${2:-deploy}"
NAMESPACE="perfect21-${ENVIRONMENT}"
TIMEOUT="600"
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_NAME="${IMAGE_NAME:-perfect21/perfect21}"

# ==============================================
# UTILITY FUNCTIONS
# ==============================================
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Wait for deployment to be ready
wait_for_deployment() {
    local deployment="$1"
    local namespace="$2"
    local timeout="${3:-600}"

    log "Waiting for deployment $deployment to be ready..."
    if kubectl rollout status deployment/"$deployment" -n "$namespace" --timeout="${timeout}s"; then
        success "Deployment $deployment is ready"
    else
        error "Deployment $deployment failed to become ready within ${timeout}s"
    fi
}

# Health check function
health_check() {
    local service_url="$1"
    local max_attempts="${2:-30}"
    local attempt=1

    log "Performing health check on $service_url"

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$service_url/health" >/dev/null 2>&1; then
            success "Health check passed (attempt $attempt/$max_attempts)"
            return 0
        else
            warning "Health check failed (attempt $attempt/$max_attempts)"
            sleep 10
            attempt=$((attempt + 1))
        fi
    done

    error "Health check failed after $max_attempts attempts"
}

# ==============================================
# PREREQUISITES CHECK
# ==============================================
check_prerequisites() {
    log "Checking prerequisites..."

    # Check required commands
    local required_commands=("kubectl" "docker" "git")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            error "Required command '$cmd' not found. Please install it."
        fi
    done

    # Check kubectl context
    local current_context
    current_context=$(kubectl config current-context)
    log "Current kubectl context: $current_context"

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        warning "Namespace $NAMESPACE does not exist. Creating..."
        kubectl create namespace "$NAMESPACE" || error "Failed to create namespace $NAMESPACE"
    fi

    # Check environment file
    if [[ ! -f .env && ! -f ".env.$ENVIRONMENT" ]]; then
        warning "No environment file found. Using defaults."
    fi

    success "Prerequisites check completed"
}

# ==============================================
# BUILD AND PUSH IMAGE
# ==============================================
build_and_push() {
    log "Building and pushing Docker image..."

    local git_sha
    git_sha=$(git rev-parse --short HEAD)
    local image_tag="${REGISTRY}/${IMAGE_NAME}:${git_sha}"
    local latest_tag="${REGISTRY}/${IMAGE_NAME}:latest"

    # Build image
    log "Building image: $image_tag"
    docker build \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$git_sha" \
        --build-arg VERSION="$git_sha" \
        --tag "$image_tag" \
        --tag "$latest_tag" \
        .

    # Push image
    log "Pushing image: $image_tag"
    docker push "$image_tag"
    docker push "$latest_tag"

    success "Image built and pushed: $image_tag"
    echo "$image_tag"
}

# ==============================================
# DEPLOY APPLICATION
# ==============================================
deploy() {
    log "Starting deployment to $ENVIRONMENT environment..."

    # Build and push image
    local image_tag
    image_tag=$(build_and_push)

    # Apply Kubernetes manifests
    log "Applying Kubernetes manifests..."

    # Apply in order
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/secrets.yaml -n "$NAMESPACE"
    kubectl apply -f k8s/persistent-volumes.yaml -n "$NAMESPACE"
    kubectl apply -f k8s/configmap.yaml -n "$NAMESPACE"
    kubectl apply -f k8s/postgres.yaml -n "$NAMESPACE"
    kubectl apply -f k8s/redis.yaml -n "$NAMESPACE"

    # Wait for database to be ready
    wait_for_deployment "postgres" "$NAMESPACE"
    wait_for_deployment "redis" "$NAMESPACE"

    # Update deployment with new image
    log "Updating Perfect21 API deployment with image: $image_tag"
    kubectl set image deployment/perfect21-api \
        perfect21-api="$image_tag" \
        -n "$NAMESPACE"

    # Apply remaining manifests
    kubectl apply -f k8s/deployment.yaml -n "$NAMESPACE"
    kubectl apply -f k8s/autoscaling.yaml -n "$NAMESPACE"
    kubectl apply -f k8s/monitoring.yaml -n "$NAMESPACE"

    # Wait for main deployment
    wait_for_deployment "perfect21-api" "$NAMESPACE"

    # Perform health checks
    local service_url
    if [[ "$ENVIRONMENT" == "production" ]]; then
        service_url="https://perfect21.example.com"
    else
        service_url="https://staging.perfect21.example.com"
    fi

    health_check "$service_url"

    success "Deployment completed successfully!"
}

# ==============================================
# ROLLBACK DEPLOYMENT
# ==============================================
rollback() {
    log "Rolling back deployment in $ENVIRONMENT environment..."

    # Get previous revision
    local previous_revision
    previous_revision=$(kubectl rollout history deployment/perfect21-api -n "$NAMESPACE" | tail -2 | head -1 | awk '{print $1}')

    if [[ -z "$previous_revision" ]]; then
        error "No previous revision found for rollback"
    fi

    log "Rolling back to revision: $previous_revision"
    kubectl rollout undo deployment/perfect21-api -n "$NAMESPACE" --to-revision="$previous_revision"

    # Wait for rollback to complete
    wait_for_deployment "perfect21-api" "$NAMESPACE"

    # Perform health checks
    local service_url
    if [[ "$ENVIRONMENT" == "production" ]]; then
        service_url="https://perfect21.example.com"
    else
        service_url="https://staging.perfect21.example.com"
    fi

    health_check "$service_url"

    success "Rollback completed successfully!"
}

# ==============================================
# SCALE DEPLOYMENT
# ==============================================
scale() {
    local replicas="${3:-3}"
    log "Scaling Perfect21 API to $replicas replicas..."

    kubectl scale deployment/perfect21-api --replicas="$replicas" -n "$NAMESPACE"
    wait_for_deployment "perfect21-api" "$NAMESPACE"

    success "Scaled to $replicas replicas"
}

# ==============================================
# STATUS CHECK
# ==============================================
status() {
    log "Checking status of $ENVIRONMENT environment..."

    echo -e "\n${BLUE}=== DEPLOYMENTS ===${NC}"
    kubectl get deployments -n "$NAMESPACE"

    echo -e "\n${BLUE}=== PODS ===${NC}"
    kubectl get pods -n "$NAMESPACE"

    echo -e "\n${BLUE}=== SERVICES ===${NC}"
    kubectl get services -n "$NAMESPACE"

    echo -e "\n${BLUE}=== INGRESS ===${NC}"
    kubectl get ingress -n "$NAMESPACE"

    echo -e "\n${BLUE}=== HPA ===${NC}"
    kubectl get hpa -n "$NAMESPACE"

    echo -e "\n${BLUE}=== PVC ===${NC}"
    kubectl get pvc -n "$NAMESPACE"
}

# ==============================================
# LOGS
# ==============================================
logs() {
    local service="${3:-perfect21-api}"
    local follow="${4:-false}"

    log "Fetching logs for $service..."

    if [[ "$follow" == "true" ]]; then
        kubectl logs -f deployment/"$service" -n "$NAMESPACE"
    else
        kubectl logs deployment/"$service" -n "$NAMESPACE" --tail=100
    fi
}

# ==============================================
# CLEANUP
# ==============================================
cleanup() {
    log "Cleaning up $ENVIRONMENT environment..."

    read -p "Are you sure you want to delete all resources in $NAMESPACE? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete namespace "$NAMESPACE"
        success "Cleanup completed"
    else
        log "Cleanup cancelled"
    fi
}

# ==============================================
# MAIN EXECUTION
# ==============================================
main() {
    log "Perfect21 Deployment Script"
    log "Environment: $ENVIRONMENT"
    log "Action: $ACTION"
    log "Namespace: $NAMESPACE"

    # Check prerequisites
    check_prerequisites

    # Execute action
    case "$ACTION" in
        "deploy")
            deploy
            ;;
        "rollback")
            rollback
            ;;
        "scale")
            scale "$@"
            ;;
        "status")
            status
            ;;
        "logs")
            logs "$@"
            ;;
        "health-check")
            if [[ "$ENVIRONMENT" == "production" ]]; then
                health_check "https://perfect21.example.com"
            else
                health_check "https://staging.perfect21.example.com"
            fi
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            error "Unknown action: $ACTION. Available actions: deploy, rollback, scale, status, logs, health-check, cleanup"
            ;;
    esac
}

# Run main function with all arguments
main "$@"