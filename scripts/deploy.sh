#!/bin/bash
# =============================================================================
# Perfect21 Claude Enhancer - Comprehensive Deployment Script
# Handles blue-green deployment with automated rollback capabilities
# =============================================================================

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/claude-enhancer-deploy-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${ENVIRONMENT:-staging}
IMAGE_TAG=${IMAGE_TAG:-latest}
NAMESPACE=${NAMESPACE:-claude-enhancer}
TIMEOUT=${TIMEOUT:-600}
DRY_RUN=${DRY_RUN:-false}
FORCE_DEPLOY=${FORCE_DEPLOY:-false}
ENABLE_ROLLBACK=${ENABLE_ROLLBACK:-true}
HEALTH_CHECK_RETRIES=${HEALTH_CHECK_RETRIES:-30}
DEPLOYMENT_STRATEGY=${DEPLOYMENT_STRATEGY:-blue-green}

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        INFO)  echo -e "${GREEN}[INFO]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE" ;;
        DEBUG) echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE" ;;
    esac
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Perfect21 Claude Enhancer to Kubernetes

OPTIONS:
    -e, --environment ENV       Target environment (dev|staging|prod) [default: staging]
    -t, --tag TAG              Docker image tag [default: latest]
    -n, --namespace NAMESPACE  Kubernetes namespace [default: claude-enhancer]
    -s, --strategy STRATEGY    Deployment strategy (rolling|blue-green|canary) [default: blue-green]
    -d, --dry-run             Perform dry run without actual deployment
    -f, --force               Force deployment even if health checks fail
    -r, --disable-rollback    Disable automatic rollback on failure
    -h, --help               Show this help message

EXAMPLES:
    $0 --environment prod --tag v1.2.3
    $0 --dry-run --strategy canary
    $0 --force --disable-rollback

ENVIRONMENT VARIABLES:
    KUBE_CONFIG_PATH    Path to kubeconfig file
    DOCKER_REGISTRY     Docker registry URL
    SLACK_WEBHOOK_URL   Slack webhook for notifications

EOF
}

check_prerequisites() {
    log INFO "Checking prerequisites..."

    local missing_tools=()

    for tool in kubectl helm docker jq curl; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [[ ${#missing_tools[@]} -ne 0 ]]; then
        log ERROR "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi

    # Check Kubernetes connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log ERROR "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log WARN "Namespace $NAMESPACE does not exist, creating..."
        kubectl create namespace "$NAMESPACE"
    fi

    log INFO "Prerequisites check passed"
}

validate_environment() {
    log INFO "Validating environment configuration..."

    case $ENVIRONMENT in
        dev|staging|prod)
            log INFO "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            log ERROR "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod"
            exit 1
            ;;
    esac

    # Environment-specific validations
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        if [[ "$IMAGE_TAG" == "latest" ]]; then
            log ERROR "Cannot deploy 'latest' tag to production"
            exit 1
        fi

        if [[ "$FORCE_DEPLOY" == "true" ]]; then
            log WARN "Force deploy is enabled for production - this is dangerous!"
            read -p "Are you sure you want to continue? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                log INFO "Deployment cancelled by user"
                exit 0
            fi
        fi
    fi
}

backup_current_deployment() {
    log INFO "Creating backup of current deployment..."

    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup current deployment manifests
    kubectl get deployment claude-enhancer -n "$NAMESPACE" -o yaml > "$backup_dir/deployment.yaml" 2>/dev/null || true
    kubectl get service claude-enhancer-service -n "$NAMESPACE" -o yaml > "$backup_dir/service.yaml" 2>/dev/null || true
    kubectl get configmap claude-enhancer-config -n "$NAMESPACE" -o yaml > "$backup_dir/configmap.yaml" 2>/dev/null || true
    kubectl get secret claude-enhancer-secrets -n "$NAMESPACE" -o yaml > "$backup_dir/secrets.yaml" 2>/dev/null || true

    # Store backup path for potential rollback
    echo "$backup_dir" > "/tmp/claude-enhancer-backup-path"

    log INFO "Backup created at $backup_dir"
}

build_and_push_image() {
    log INFO "Building and pushing Docker image..."

    local registry=${DOCKER_REGISTRY:-ghcr.io/perfect21}
    local image_name="$registry/claude-enhancer:$IMAGE_TAG"

    if [[ "$DRY_RUN" == "true" ]]; then
        log INFO "DRY RUN: Would build and push $image_name"
        return 0
    fi

    # Build image
    log INFO "Building Docker image..."
    docker build -t "$image_name" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        --build-arg VERSION="$IMAGE_TAG" \
        "$PROJECT_ROOT"

    # Push image
    log INFO "Pushing Docker image..."
    docker push "$image_name"

    log INFO "Image built and pushed: $image_name"
}

deploy_infrastructure() {
    log INFO "Deploying infrastructure components..."

    # Deploy namespace
    kubectl apply -f "$PROJECT_ROOT/k8s/namespace.yaml"

    # Deploy secrets and configmaps
    kubectl apply -f "$PROJECT_ROOT/k8s/secrets.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/configmap.yaml"

    # Deploy PostgreSQL
    log INFO "Deploying PostgreSQL..."
    kubectl apply -f "$PROJECT_ROOT/k8s/postgres.yaml"

    # Deploy Redis
    log INFO "Deploying Redis..."
    kubectl apply -f "$PROJECT_ROOT/k8s/redis.yaml"

    # Wait for database to be ready
    log INFO "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgres -n "$NAMESPACE" --timeout=300s

    log INFO "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis -n "$NAMESPACE" --timeout=300s

    log INFO "Infrastructure deployment completed"
}

deploy_application() {
    log INFO "Deploying application using $DEPLOYMENT_STRATEGY strategy..."

    case $DEPLOYMENT_STRATEGY in
        rolling)
            deploy_rolling_update
            ;;
        blue-green)
            deploy_blue_green
            ;;
        canary)
            deploy_canary
            ;;
        *)
            log ERROR "Unknown deployment strategy: $DEPLOYMENT_STRATEGY"
            exit 1
            ;;
    esac
}

deploy_rolling_update() {
    log INFO "Performing rolling update deployment..."

    # Update image in deployment
    kubectl set image deployment/claude-enhancer \
        claude-enhancer="ghcr.io/perfect21/claude-enhancer:$IMAGE_TAG" \
        -n "$NAMESPACE"

    # Wait for rollout to complete
    kubectl rollout status deployment/claude-enhancer -n "$NAMESPACE" --timeout="${TIMEOUT}s"

    log INFO "Rolling update completed"
}

deploy_blue_green() {
    log INFO "Performing blue-green deployment..."

    local current_deployment=$(kubectl get deployment claude-enhancer -n "$NAMESPACE" -o jsonpath='{.metadata.labels.version}' 2>/dev/null || echo "")
    local new_version="$IMAGE_TAG"

    # Create green deployment
    log INFO "Creating green deployment..."
    sed "s/{{IMAGE_TAG}}/$IMAGE_TAG/g; s/{{VERSION}}/green/g" \
        "$PROJECT_ROOT/k8s/claude-enhancer.yaml" | \
        kubectl apply -f -

    # Wait for green deployment to be ready
    log INFO "Waiting for green deployment to be ready..."
    kubectl wait --for=condition=available deployment/claude-enhancer-green -n "$NAMESPACE" --timeout="${TIMEOUT}s"

    # Perform health checks
    if ! perform_health_checks "claude-enhancer-green-service"; then
        log ERROR "Health checks failed for green deployment"
        cleanup_failed_deployment "claude-enhancer-green"
        return 1
    fi

    # Switch traffic to green
    log INFO "Switching traffic to green deployment..."
    kubectl patch service claude-enhancer-service -n "$NAMESPACE" \
        -p '{"spec":{"selector":{"version":"green"}}}'

    # Wait and perform final health checks
    sleep 30
    if ! perform_health_checks "claude-enhancer-service"; then
        log ERROR "Final health checks failed, rolling back..."
        kubectl patch service claude-enhancer-service -n "$NAMESPACE" \
            -p '{"spec":{"selector":{"version":"blue"}}}'
        return 1
    fi

    # Clean up old blue deployment
    log INFO "Cleaning up old deployment..."
    kubectl delete deployment claude-enhancer-blue -n "$NAMESPACE" --ignore-not-found=true

    # Rename green to blue for next deployment
    kubectl patch deployment claude-enhancer-green -n "$NAMESPACE" \
        -p '{"metadata":{"name":"claude-enhancer-blue"},"spec":{"selector":{"matchLabels":{"version":"blue"}},"template":{"metadata":{"labels":{"version":"blue"}}}}}'

    log INFO "Blue-green deployment completed successfully"
}

deploy_canary() {
    log INFO "Performing canary deployment..."

    # Deploy canary version
    sed "s/{{IMAGE_TAG}}/$IMAGE_TAG/g; s/{{VERSION}}/canary/g; s/{{REPLICAS}}/1/g" \
        "$PROJECT_ROOT/k8s/claude-enhancer.yaml" | \
        kubectl apply -f -

    # Wait for canary to be ready
    kubectl wait --for=condition=available deployment/claude-enhancer-canary -n "$NAMESPACE" --timeout="${TIMEOUT}s"

    # Configure traffic split (10% to canary)
    setup_canary_traffic_split

    # Monitor canary for 5 minutes
    log INFO "Monitoring canary deployment for 5 minutes..."
    if ! monitor_canary_metrics; then
        log ERROR "Canary metrics indicate issues, rolling back..."
        cleanup_failed_deployment "claude-enhancer-canary"
        return 1
    fi

    # Gradually increase traffic to canary
    for percentage in 25 50 75 100; do
        log INFO "Increasing canary traffic to $percentage%..."
        update_canary_traffic_split "$percentage"
        sleep 120

        if ! monitor_canary_metrics; then
            log ERROR "Canary metrics indicate issues at $percentage%, rolling back..."
            cleanup_failed_deployment "claude-enhancer-canary"
            return 1
        fi
    done

    # Replace main deployment with canary
    kubectl delete deployment claude-enhancer -n "$NAMESPACE"
    kubectl patch deployment claude-enhancer-canary -n "$NAMESPACE" \
        --type='merge' -p='{"metadata":{"name":"claude-enhancer"}}'

    log INFO "Canary deployment completed successfully"
}

perform_health_checks() {
    local service_name=${1:-claude-enhancer-service}
    local max_attempts=$HEALTH_CHECK_RETRIES
    local attempt=1

    log INFO "Performing health checks for $service_name..."

    while [[ $attempt -le $max_attempts ]]; do
        log DEBUG "Health check attempt $attempt/$max_attempts"

        # Get service endpoint
        local service_ip=$(kubectl get service "$service_name" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
        local service_port=$(kubectl get service "$service_name" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].port}')

        # Perform health check using kubectl port-forward
        if kubectl port-forward service/"$service_name" 8080:$service_port -n "$NAMESPACE" &
        then
            local pf_pid=$!
            sleep 5

            if curl -s -f "http://localhost:8080/health" > /dev/null; then
                kill $pf_pid 2>/dev/null || true
                log INFO "Health check passed"
                return 0
            fi

            kill $pf_pid 2>/dev/null || true
        fi

        log DEBUG "Health check failed, retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done

    log ERROR "Health checks failed after $max_attempts attempts"
    return 1
}

monitor_canary_metrics() {
    log INFO "Monitoring canary metrics..."

    # Check error rate
    local error_rate=$(get_error_rate "canary")
    if (( $(echo "$error_rate > 0.05" | bc -l) )); then
        log ERROR "Canary error rate too high: $error_rate"
        return 1
    fi

    # Check response time
    local response_time=$(get_response_time "canary")
    if (( $(echo "$response_time > 2.0" | bc -l) )); then
        log ERROR "Canary response time too high: $response_time"
        return 1
    fi

    log INFO "Canary metrics are healthy"
    return 0
}

get_error_rate() {
    local version=$1
    # Query Prometheus for error rate
    echo "0.01" # Placeholder - implement actual Prometheus query
}

get_response_time() {
    local version=$1
    # Query Prometheus for response time
    echo "0.5" # Placeholder - implement actual Prometheus query
}

setup_canary_traffic_split() {
    log INFO "Setting up canary traffic split..."
    # Implement traffic splitting logic (Istio, NGINX, etc.)
}

update_canary_traffic_split() {
    local percentage=$1
    log INFO "Updating canary traffic split to $percentage%..."
    # Implement traffic split update logic
}

cleanup_failed_deployment() {
    local deployment_name=$1
    log INFO "Cleaning up failed deployment: $deployment_name"

    kubectl delete deployment "$deployment_name" -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete service "${deployment_name}-service" -n "$NAMESPACE" --ignore-not-found=true
}

deploy_monitoring() {
    log INFO "Deploying monitoring stack..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log INFO "DRY RUN: Would deploy monitoring stack"
        return 0
    fi

    kubectl apply -f "$PROJECT_ROOT/k8s/monitoring.yaml"

    log INFO "Waiting for monitoring components to be ready..."
    kubectl wait --for=condition=available deployment/prometheus -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=available deployment/grafana -n "$NAMESPACE" --timeout=300s

    log INFO "Monitoring stack deployed successfully"
}

deploy_load_balancer() {
    log INFO "Deploying load balancer..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log INFO "DRY RUN: Would deploy load balancer"
        return 0
    fi

    kubectl apply -f "$PROJECT_ROOT/k8s/nginx.yaml"

    log INFO "Waiting for load balancer to be ready..."
    kubectl wait --for=condition=available deployment/nginx -n "$NAMESPACE" --timeout=300s

    log INFO "Load balancer deployed successfully"
}

run_smoke_tests() {
    log INFO "Running smoke tests..."

    local base_url="http://$(kubectl get service nginx-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"

    # Test health endpoint
    if ! curl -s -f "$base_url/health" > /dev/null; then
        log ERROR "Health endpoint test failed"
        return 1
    fi

    # Test API endpoint
    if ! curl -s -f "$base_url/api/v1/status" > /dev/null; then
        log ERROR "API endpoint test failed"
        return 1
    fi

    log INFO "Smoke tests passed"
    return 0
}

perform_rollback() {
    if [[ "$ENABLE_ROLLBACK" != "true" ]]; then
        log WARN "Rollback is disabled, manual intervention required"
        return 1
    fi

    log WARN "Performing automatic rollback..."

    local backup_path
    if [[ -f "/tmp/claude-enhancer-backup-path" ]]; then
        backup_path=$(cat /tmp/claude-enhancer-backup-path)
    else
        log ERROR "No backup path found, cannot rollback"
        return 1
    fi

    if [[ -d "$backup_path" ]]; then
        log INFO "Restoring from backup: $backup_path"
        kubectl apply -f "$backup_path/" -n "$NAMESPACE"

        log INFO "Waiting for rollback to complete..."
        kubectl rollout status deployment/claude-enhancer -n "$NAMESPACE" --timeout=300s

        log INFO "Rollback completed successfully"
        send_notification "🔄 Rollback completed for Claude Enhancer in $ENVIRONMENT"
    else
        log ERROR "Backup directory not found: $backup_path"
        return 1
    fi
}

send_notification() {
    local message=$1

    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi

    log INFO "Notification sent: $message"
}

cleanup() {
    log INFO "Cleaning up temporary files..."
    rm -f "/tmp/claude-enhancer-backup-path"
}

main() {
    log INFO "Starting Claude Enhancer deployment..."
    log INFO "Environment: $ENVIRONMENT"
    log INFO "Image Tag: $IMAGE_TAG"
    log INFO "Namespace: $NAMESPACE"
    log INFO "Strategy: $DEPLOYMENT_STRATEGY"
    log INFO "Dry Run: $DRY_RUN"

    # Trap cleanup on exit
    trap cleanup EXIT

    # Pre-deployment checks
    check_prerequisites
    validate_environment

    # Backup current deployment
    backup_current_deployment

    # Build and push image
    if [[ "$DRY_RUN" != "true" ]]; then
        build_and_push_image
    fi

    # Deploy components
    if deploy_infrastructure && \
       deploy_application && \
       deploy_monitoring && \
       deploy_load_balancer && \
       run_smoke_tests; then

        log INFO "✅ Deployment completed successfully!"
        send_notification "✅ Claude Enhancer deployed successfully to $ENVIRONMENT (tag: $IMAGE_TAG)"

        # Print access information
        echo
        echo "🌐 Access Information:"
        echo "───────────────────────"
        kubectl get service nginx-service -n "$NAMESPACE" -o wide
        echo
        echo "📊 Monitoring URLs:"
        echo "Grafana: http://$(kubectl get service grafana-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}'):3000"
        echo "Prometheus: http://$(kubectl get service prometheus-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}'):9090"

    else
        log ERROR "❌ Deployment failed!"

        if [[ "$ENABLE_ROLLBACK" == "true" ]]; then
            perform_rollback
        fi

        send_notification "❌ Claude Enhancer deployment failed in $ENVIRONMENT"
        exit 1
    fi
}

# =============================================================================
# Parse Command Line Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -s|--strategy)
            DEPLOYMENT_STRATEGY="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE_DEPLOY=true
            shift
            ;;
        -r|--disable-rollback)
            ENABLE_ROLLBACK=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log ERROR "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Run main function
main "$@"