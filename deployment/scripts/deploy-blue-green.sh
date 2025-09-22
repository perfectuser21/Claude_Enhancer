#!/bin/bash
# =============================================================================
# Blue-Green Deployment Script for Perfect21 Claude Enhancer
# Zero-downtime deployment with automatic rollback capability
# =============================================================================

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-claude-enhancer}"
APP_NAME="${APP_NAME:-claude-enhancer}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-/health}"
READINESS_CHECK_URL="${READINESS_CHECK_URL:-/ready}"
TIMEOUT="${TIMEOUT:-600}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
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

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."

    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi

    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        error "Namespace $NAMESPACE does not exist"
        exit 1
    fi

    success "Prerequisites check passed"
}

# Determine current active environment
get_current_environment() {
    log "🔍 Determining current active environment..."

    # Check which environment is currently receiving traffic
    local service_selector=$(kubectl get service "$APP_NAME-service" -n "$NAMESPACE" -o jsonpath='{.spec.selector.environment}' 2>/dev/null || echo "")

    if [[ "$service_selector" == "blue" ]]; then
        echo "blue"
    elif [[ "$service_selector" == "green" ]]; then
        echo "green"
    else
        # No current deployment, default to blue
        echo "blue"
    fi
}

# Get target environment
get_target_environment() {
    local current=$1
    if [[ "$current" == "blue" ]]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Deploy to target environment
deploy_to_environment() {
    local env=$1
    log "🚀 Deploying to $env environment..."

    # Create deployment manifest
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $APP_NAME-$env
  namespace: $NAMESPACE
  labels:
    app: $APP_NAME
    environment: $env
    version: $IMAGE_TAG
spec:
  replicas: 3
  selector:
    matchLabels:
      app: $APP_NAME
      environment: $env
  template:
    metadata:
      labels:
        app: $APP_NAME
        environment: $env
        version: $IMAGE_TAG
    spec:
      containers:
      - name: $APP_NAME
        image: ghcr.io/perfect21/claude-enhancer:$IMAGE_TAG
        ports:
        - containerPort: 8080
        env:
        - name: CLAUDE_ENV
          value: "production"
        - name: ENVIRONMENT
          value: "$env"
        livenessProbe:
          httpGet:
            path: $HEALTH_CHECK_URL
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: $READINESS_CHECK_URL
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: $APP_NAME-$env-service
  namespace: $NAMESPACE
  labels:
    app: $APP_NAME
    environment: $env
spec:
  selector:
    app: $APP_NAME
    environment: $env
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
EOF

    success "Deployment manifest applied for $env environment"
}

# Wait for deployment to be ready
wait_for_deployment() {
    local env=$1
    log "⏳ Waiting for $env deployment to be ready..."

    if kubectl rollout status deployment/"$APP_NAME-$env" -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
        success "$env deployment is ready"
        return 0
    else
        error "$env deployment failed to become ready within $TIMEOUT seconds"
        return 1
    fi
}

# Perform health checks
health_check() {
    local env=$1
    log "🏥 Performing health check for $env environment..."

    local service_name="$APP_NAME-$env-service"
    local pod_name=$(kubectl get pods -n "$NAMESPACE" -l "app=$APP_NAME,environment=$env" -o jsonpath='{.items[0].metadata.name}')

    if [[ -z "$pod_name" ]]; then
        error "No pods found for $env environment"
        return 1
    fi

    # Port forward to test the application
    kubectl port-forward -n "$NAMESPACE" pod/"$pod_name" 8081:8080 &
    local port_forward_pid=$!

    sleep 5

    local health_check_passed=false
    for i in {1..10}; do
        if curl -sf "http://localhost:8081$HEALTH_CHECK_URL" > /dev/null; then
            health_check_passed=true
            break
        fi
        sleep 2
    done

    kill $port_forward_pid 2>/dev/null || true

    if [[ "$health_check_passed" == "true" ]]; then
        success "Health check passed for $env environment"
        return 0
    else
        error "Health check failed for $env environment"
        return 1
    fi
}

# Switch traffic to new environment
switch_traffic() {
    local target_env=$1
    log "🔄 Switching traffic to $target_env environment..."

    # Update the main service to point to the new environment
    kubectl patch service "$APP_NAME-service" -n "$NAMESPACE" -p '{"spec":{"selector":{"environment":"'$target_env'"}}}'

    success "Traffic switched to $target_env environment"
}

# Create main service if it doesn't exist
ensure_main_service() {
    if ! kubectl get service "$APP_NAME-service" -n "$NAMESPACE" &> /dev/null; then
        log "🔧 Creating main service..."

        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: $APP_NAME-service
  namespace: $NAMESPACE
  labels:
    app: $APP_NAME
spec:
  selector:
    app: $APP_NAME
    environment: blue  # Default to blue
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
EOF

        success "Main service created"
    fi
}

# Cleanup old environment
cleanup_old_environment() {
    local old_env=$1
    log "🧹 Cleaning up $old_env environment..."

    # Keep the old environment for a short period for quick rollback
    warning "Keeping $old_env environment for potential rollback"
    warning "Manual cleanup required: kubectl delete deployment $APP_NAME-$old_env -n $NAMESPACE"
}

# Rollback function
rollback() {
    local rollback_env=$1
    error "🔄 Rolling back to $rollback_env environment..."

    switch_traffic "$rollback_env"
    success "Rollback completed to $rollback_env environment"
}

# Main deployment function
main() {
    log "🚀 Starting Blue-Green deployment for $APP_NAME"
    log "📦 Image: ghcr.io/perfect21/claude-enhancer:$IMAGE_TAG"

    check_prerequisites
    ensure_main_service

    local current_env=$(get_current_environment)
    local target_env=$(get_target_environment "$current_env")

    log "📊 Current environment: $current_env"
    log "🎯 Target environment: $target_env"

    # Deploy to target environment
    if ! deploy_to_environment "$target_env"; then
        error "Failed to deploy to $target_env environment"
        exit 1
    fi

    # Wait for deployment to be ready
    if ! wait_for_deployment "$target_env"; then
        error "Deployment to $target_env environment failed"
        cleanup_old_environment "$target_env"
        exit 1
    fi

    # Perform health checks
    if ! health_check "$target_env"; then
        error "Health check failed for $target_env environment"
        rollback "$current_env"
        cleanup_old_environment "$target_env"
        exit 1
    fi

    # Switch traffic
    if ! switch_traffic "$target_env"; then
        error "Failed to switch traffic to $target_env environment"
        rollback "$current_env"
        exit 1
    fi

    # Final verification
    sleep 10
    if ! health_check "$target_env"; then
        error "Post-switch health check failed"
        rollback "$current_env"
        exit 1
    fi

    success "🎉 Blue-Green deployment completed successfully!"
    log "✅ $APP_NAME is now running on $target_env environment"

    # Schedule cleanup of old environment
    cleanup_old_environment "$current_env"
}

# Handle script interruption
trap 'error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"