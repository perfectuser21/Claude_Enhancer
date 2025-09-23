#!/bin/bash
# =============================================================================
# Canary Deployment Script for Claude Enhancer Claude Enhancer
# Gradual traffic shifting with automatic rollback on failure
# =============================================================================

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-claude-enhancer}"
APP_NAME="${APP_NAME:-claude-enhancer}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CANARY_PERCENTAGE="${CANARY_PERCENTAGE:-10}"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-/health}"
TIMEOUT="${TIMEOUT:-600}"

# Colors for output
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

# Deploy canary version
deploy_canary() {
    log "🐦 Deploying canary version..."

    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $APP_NAME-canary
  namespace: $NAMESPACE
  labels:
    app: $APP_NAME
    version: canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $APP_NAME
      version: canary
  template:
    metadata:
      labels:
        app: $APP_NAME
        version: canary
    spec:
      containers:
      - name: $APP_NAME
        image: ghcr.io/perfect21/claude-enhancer:$IMAGE_TAG
        ports:
        - containerPort: 8080
        env:
        - name: CLAUDE_ENV
          value: "production"
        - name: VERSION
          value: "canary"
        livenessProbe:
          httpGet:
            path: $HEALTH_CHECK_URL
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: $HEALTH_CHECK_URL
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
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
  name: $APP_NAME-canary-service
  namespace: $NAMESPACE
spec:
  selector:
    app: $APP_NAME
    version: canary
  ports:
  - port: 80
    targetPort: 8080
EOF

    success "Canary deployment created"
}

# Configure traffic splitting
configure_traffic_split() {
    local percentage=$1
    log "🔀 Configuring traffic split: ${percentage}% to canary"

    # Using NGINX ingress with traffic splitting
    cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: $APP_NAME-ingress
  namespace: $NAMESPACE
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "$percentage"
    nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    nginx.ingress.kubernetes.io/canary-by-header-value: "true"
spec:
  rules:
  - host: claude-enhancer.perfect21.dev
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: $APP_NAME-canary-service
            port:
              number: 80
EOF

    success "Traffic split configured: ${percentage}% to canary"
}

# Monitor canary metrics
monitor_canary() {
    local duration=$1
    log "📊 Monitoring canary for ${duration} seconds..."

    local end_time=$(($(date +%s) + duration))
    local success_count=0
    local error_count=0

    while [[ $(date +%s) -lt $end_time ]]; do
        # Test canary endpoint directly
        if curl -sf -H "X-Canary: true" "http://claude-enhancer.perfect21.dev$HEALTH_CHECK_URL" > /dev/null; then
            ((success_count++))
        else
            ((error_count++))
        fi

        sleep 10
    done

    local total_requests=$((success_count + error_count))
    local error_rate=0

    if [[ $total_requests -gt 0 ]]; then
        error_rate=$(( (error_count * 100) / total_requests ))
    fi

    log "📈 Canary metrics: Success: $success_count, Errors: $error_count, Error rate: ${error_rate}%"

    # Fail if error rate is above 5%
    if [[ $error_rate -gt 5 ]]; then
        error "Canary error rate too high: ${error_rate}%"
        return 1
    fi

    success "Canary metrics are healthy"
    return 0
}

# Promote canary to production
promote_canary() {
    log "🚀 Promoting canary to production..."

    # Scale up canary deployment
    kubectl scale deployment "$APP_NAME-canary" -n "$NAMESPACE" --replicas=3
    kubectl rollout status deployment/"$APP_NAME-canary" -n "$NAMESPACE" --timeout="${TIMEOUT}s"

    # Update main service to point to canary
    kubectl patch service "$APP_NAME-service" -n "$NAMESPACE" -p '{"spec":{"selector":{"version":"canary"}}}'

    # Remove traffic splitting
    kubectl delete ingress "$APP_NAME-ingress" -n "$NAMESPACE" || true

    # Remove old production deployment
    kubectl delete deployment "$APP_NAME-production" -n "$NAMESPACE" || true

    # Rename canary to production
    kubectl patch deployment "$APP_NAME-canary" -n "$NAMESPACE" -p '{"metadata":{"name":"'$APP_NAME'-production"},"spec":{"selector":{"matchLabels":{"version":"production"}},"template":{"metadata":{"labels":{"version":"production"}}}}}'

    success "Canary promoted to production"
}

# Rollback canary
rollback_canary() {
    error "🔄 Rolling back canary deployment..."

    # Remove traffic splitting
    kubectl delete ingress "$APP_NAME-ingress" -n "$NAMESPACE" || true

    # Remove canary deployment
    kubectl delete deployment "$APP_NAME-canary" -n "$NAMESPACE" || true
    kubectl delete service "$APP_NAME-canary-service" -n "$NAMESPACE" || true

    success "Canary rollback completed"
}

# Main deployment function
main() {
    log "🐦 Starting Canary deployment for $APP_NAME"
    log "📦 Image: ghcr.io/perfect21/claude-enhancer:$IMAGE_TAG"
    log "📊 Initial canary traffic: ${CANARY_PERCENTAGE}%"

    # Deploy canary
    if ! deploy_canary; then
        error "Failed to deploy canary"
        exit 1
    fi

    # Wait for canary to be ready
    if ! kubectl rollout status deployment/"$APP_NAME-canary" -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
        error "Canary deployment failed to become ready"
        rollback_canary
        exit 1
    fi

    # Configure initial traffic split
    configure_traffic_split "$CANARY_PERCENTAGE"

    # Monitor canary for 5 minutes
    if ! monitor_canary 300; then
        error "Canary monitoring failed"
        rollback_canary
        exit 1
    fi

    # Gradually increase traffic
    for percentage in 25 50 75 100; do
        log "🔀 Increasing canary traffic to ${percentage}%"
        configure_traffic_split "$percentage"

        # Monitor for 3 minutes at each stage
        if ! monitor_canary 180; then
            error "Canary failed at ${percentage}% traffic"
            rollback_canary
            exit 1
        fi
    done

    # Promote canary to production
    if ! promote_canary; then
        error "Failed to promote canary"
        rollback_canary
        exit 1
    fi

    success "🎉 Canary deployment completed successfully!"
    log "✅ $APP_NAME canary has been promoted to production"
}

# Handle script interruption
trap 'error "Canary deployment interrupted"; rollback_canary; exit 1' INT TERM

# Run main function
main "$@"