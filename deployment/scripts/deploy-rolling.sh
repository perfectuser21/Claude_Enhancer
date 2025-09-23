#!/bin/bash
# =============================================================================
# Rolling Deployment Script for Claude Enhancer Claude Enhancer
# Standard Kubernetes rolling update with health verification
# =============================================================================

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-claude-enhancer}"
APP_NAME="${APP_NAME:-claude-enhancer}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
TIMEOUT="${TIMEOUT:-600}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Update deployment image
update_deployment() {
    log "🔄 Updating deployment image to: ghcr.io/perfect21/claude-enhancer:$IMAGE_TAG"

    kubectl set image deployment/"$APP_NAME" \
        "$APP_NAME"=ghcr.io/perfect21/claude-enhancer:"$IMAGE_TAG" \
        -n "$NAMESPACE"

    success "Deployment image updated"
}

# Wait for rollout
wait_for_rollout() {
    log "⏳ Waiting for rolling update to complete..."

    if kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
        success "Rolling update completed successfully"
        return 0
    else
        error "Rolling update failed or timed out"
        return 1
    fi
}

# Verify deployment
verify_deployment() {
    log "🔍 Verifying deployment health..."

    # Get service endpoint
    local service_ip=$(kubectl get service "$APP_NAME-service" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

    if [[ -z "$service_ip" ]]; then
        # Fallback to port-forward for testing
        local pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=$APP_NAME" -o jsonpath='{.items[0].metadata.name}')
        kubectl port-forward -n "$NAMESPACE" pod/"$pod_name" 8081:8080 &
        local port_forward_pid=$!
        sleep 5
        local test_url="http://localhost:8081"
    else
        local test_url="http://$service_ip"
    fi

    # Health check
    for i in {1..30}; do
        if curl -sf "$test_url/health" > /dev/null 2>&1; then
            success "Health check passed"
            [[ -n "${port_forward_pid:-}" ]] && kill $port_forward_pid 2>/dev/null || true
            return 0
        fi
        sleep 10
    done

    error "Health check failed after 5 minutes"
    [[ -n "${port_forward_pid:-}" ]] && kill $port_forward_pid 2>/dev/null || true
    return 1
}

# Main function
main() {
    log "🚀 Starting rolling deployment for $APP_NAME"
    log "📦 Target image: ghcr.io/perfect21/claude-enhancer:$IMAGE_TAG"

    # Check if deployment exists
    if ! kubectl get deployment "$APP_NAME" -n "$NAMESPACE" &> /dev/null; then
        error "Deployment $APP_NAME does not exist in namespace $NAMESPACE"
        exit 1
    fi

    # Update deployment
    if ! update_deployment; then
        error "Failed to update deployment"
        exit 1
    fi

    # Wait for rollout
    if ! wait_for_rollout; then
        error "Rolling update failed"
        exit 1
    fi

    # Verify deployment
    if ! verify_deployment; then
        error "Deployment verification failed"
        exit 1
    fi

    success "🎉 Rolling deployment completed successfully!"
    log "✅ $APP_NAME is now running with image: ghcr.io/perfect21/claude-enhancer:$IMAGE_TAG"
}

# Handle interruption
trap 'error "Rolling deployment interrupted"; exit 1' INT TERM

main "$@"