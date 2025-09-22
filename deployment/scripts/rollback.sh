#!/bin/bash
# =============================================================================
# Rollback Script for Perfect21 Claude Enhancer
# Emergency rollback functionality with version management
# =============================================================================

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-claude-enhancer}"
APP_NAME="${APP_NAME:-claude-enhancer}"
ROLLBACK_VERSION="${1:-previous}"
TIMEOUT="${TIMEOUT:-300}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Show rollout history
show_history() {
    log "📜 Showing rollout history..."
    kubectl rollout history deployment/"$APP_NAME" -n "$NAMESPACE"
}

# Perform rollback
perform_rollback() {
    local target_revision=$1

    log "🔄 Performing rollback to revision: $target_revision"

    if [[ "$target_revision" == "previous" ]]; then
        kubectl rollout undo deployment/"$APP_NAME" -n "$NAMESPACE"
    else
        kubectl rollout undo deployment/"$APP_NAME" -n "$NAMESPACE" --to-revision="$target_revision"
    fi

    success "Rollback command executed"
}

# Wait for rollback completion
wait_for_rollback() {
    log "⏳ Waiting for rollback to complete..."

    if kubectl rollout status deployment/"$APP_NAME" -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
        success "Rollback completed successfully"
        return 0
    else
        error "Rollback failed or timed out"
        return 1
    fi
}

# Verify rollback
verify_rollback() {
    log "🔍 Verifying rollback..."

    # Get a pod and test health
    local pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=$APP_NAME" -o jsonpath='{.items[0].metadata.name}')

    if [[ -z "$pod_name" ]]; then
        error "No pods found for verification"
        return 1
    fi

    # Port forward and test
    kubectl port-forward -n "$NAMESPACE" pod/"$pod_name" 8082:8080 &
    local port_forward_pid=$!
    sleep 5

    local health_check_passed=false
    for i in {1..10}; do
        if curl -sf "http://localhost:8082/health" > /dev/null 2>&1; then
            health_check_passed=true
            break
        fi
        sleep 3
    done

    kill $port_forward_pid 2>/dev/null || true

    if [[ "$health_check_passed" == "true" ]]; then
        success "Rollback verification passed"
        return 0
    else
        error "Rollback verification failed"
        return 1
    fi
}

# Get current deployment info
get_current_info() {
    log "📊 Current deployment information:"

    local current_image=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}')
    local current_replicas=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    local ready_replicas=$(kubectl get deployment "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')

    echo "  Image: $current_image"
    echo "  Replicas: $ready_replicas/$current_replicas"
}

# Confirm rollback
confirm_rollback() {
    warning "⚠️  You are about to rollback deployment '$APP_NAME' in namespace '$NAMESPACE'"
    warning "⚠️  Target revision: $ROLLBACK_VERSION"

    if [[ "${FORCE_ROLLBACK:-false}" != "true" ]]; then
        read -p "Are you sure you want to proceed? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log "Rollback cancelled by user"
            exit 0
        fi
    fi
}

# Main function
main() {
    log "🔄 Starting rollback process for $APP_NAME"

    # Check if deployment exists
    if ! kubectl get deployment "$APP_NAME" -n "$NAMESPACE" &> /dev/null; then
        error "Deployment $APP_NAME does not exist in namespace $NAMESPACE"
        exit 1
    fi

    # Show current state
    get_current_info

    # Show history
    show_history

    # Confirm rollback
    confirm_rollback

    # Perform rollback
    if ! perform_rollback "$ROLLBACK_VERSION"; then
        error "Failed to initiate rollback"
        exit 1
    fi

    # Wait for completion
    if ! wait_for_rollback; then
        error "Rollback failed"
        exit 1
    fi

    # Verify rollback
    if ! verify_rollback; then
        error "Rollback verification failed"
        exit 1
    fi

    success "🎉 Rollback completed successfully!"

    # Show new state
    log "📊 Post-rollback deployment information:"
    get_current_info
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [REVISION]

Rollback Perfect21 Claude Enhancer deployment.

Arguments:
  REVISION    Target revision number or 'previous' (default: previous)

Environment Variables:
  NAMESPACE        Kubernetes namespace (default: claude-enhancer)
  APP_NAME         Application name (default: claude-enhancer)
  TIMEOUT          Rollback timeout in seconds (default: 300)
  FORCE_ROLLBACK   Skip confirmation prompt (default: false)

Examples:
  $0                    # Rollback to previous revision
  $0 previous           # Same as above
  $0 5                  # Rollback to revision 5
  FORCE_ROLLBACK=true $0 # Force rollback without confirmation

EOF
}

# Handle help flag
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Handle interruption
trap 'error "Rollback interrupted"; exit 1' INT TERM

main "$@"