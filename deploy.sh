#!/bin/bash

# =============================================================================
# Claude Enhancer 5.1 自动化云部署脚本
# 支持AWS多环境部署和完整的CI/CD流程
# =============================================================================

set -e
set -u
set -o pipefail

# 脚本信息
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日志函数
log() {
    local level=$1; shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        ERROR) echo -e "${RED}[ERROR]${NC} ${timestamp} - ${message}" >&2 ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} ${timestamp} - ${message}" >&2 ;;
        INFO)  echo -e "${GREEN}[INFO]${NC} ${timestamp} - ${message}" ;;
        DEBUG) echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - ${message}" ;;
    esac
}

error() { log ERROR "$@"; }
warn() { log WARN "$@"; }
info() { log INFO "$@"; }

# 进度显示
show_progress() {
    local step=$1
    local total=$2
    local description=$3
    local percent=$((step * 100 / total))
    local bar_length=50
    local filled_length=$((percent * bar_length / 100))

    printf "\r${BLUE}["
    printf "%${filled_length}s" | tr ' ' '█'
    printf "%$((bar_length - filled_length))s" | tr ' ' '░'
    printf "] %3d%% (%d/%d) %s${NC}" "$percent" "$step" "$total" "$description"

    if [ $step -eq $total ]; then
        echo
    fi
}

show_help() {
    cat << EOF
${CYAN}Claude Enhancer 5.1 云部署脚本 v${VERSION}${NC}

用法: $0 [选项] <命令>

命令:
  plan      显示Terraform执行计划
  apply     部署AWS基础设施
  destroy   销毁AWS基础设施
  build     构建并推送Docker镜像到ECR
  deploy    完整部署流程 (构建 + 基础设施 + 应用)
  status    显示当前部署状态
  logs      查看应用日志
  scale     扩缩容服务
  cleanup   清理未使用的资源

选项:
  -e, --environment ENV   环境 [dev|staging|prod] (默认: dev)
  -r, --region REGION     AWS区域 (默认: us-east-1)
  -v, --version VERSION   应用版本标签 (默认: git commit)
  --dry-run              仅显示将要执行的操作
  --auto-approve         自动批准Terraform操作
  --service SERVICE      指定服务名称 (用于logs/scale)
  --replicas NUM         副本数量 (用于scale)
  --follow               跟踪日志输出
  -h, --help            显示帮助

示例:
  $0 deploy -e prod -r us-east-1           # 部署到生产环境
  $0 plan --dry-run                        # 预览部署计划
  $0 scale --service=core --replicas=10    # 扩容core服务
  $0 logs --service=auth --follow          # 查看auth服务日志

EOF
}

check_dependencies() {
    info "🔍 检查依赖..."

    local deps=("aws:请安装AWS CLI" "terraform:请安装Terraform" "docker:请安装Docker" "jq:请安装jq")
    local missing_deps=()

    for dep in "${deps[@]}"; do
        local cmd="${dep%%:*}"
        local msg="${dep##*:}"
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
            error "$msg"
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "缺少依赖: ${missing_deps[*]}"
        exit 1
    fi

    info "✅ 依赖检查通过"
}

verify_aws_credentials() {
    info "🔐 验证AWS凭证..."

    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS凭证验证失败，请运行 'aws configure'"
        exit 1
    fi

    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local user_arn=$(aws sts get-caller-identity --query Arn --output text)

    info "✅ AWS凭证验证成功"
    info "账户ID: $account_id"
    info "用户: $user_arn"
}

terraform_init() {
    info "🏗️ 初始化Terraform..."
    cd "$SCRIPT_DIR/terraform"

    if [ "$DRY_RUN" = "true" ]; then
        info "[DRY RUN] terraform init"
        return 0
    fi

    terraform init -backend-config="key=${ENVIRONMENT}/terraform.tfstate" -backend-config="region=${REGION}"
}

terraform_plan() {
    info "📋 生成Terraform执行计划..."
    cd "$SCRIPT_DIR/terraform"

    if [ "$DRY_RUN" = "true" ]; then
        info "[DRY RUN] terraform plan"
        return 0
    fi

    terraform plan -var="environment=${ENVIRONMENT}" -var="aws_region=${REGION}" -out="${ENVIRONMENT}.tfplan"
    info "✅ Terraform计划已保存"
}

terraform_apply() {
    info "🚀 应用Terraform配置..."
    cd "$SCRIPT_DIR/terraform"

    if [ "$DRY_RUN" = "true" ]; then
        info "[DRY RUN] terraform apply"
        return 0
    fi

    local args=("-var=environment=${ENVIRONMENT}" "-var=aws_region=${REGION}")
    if [ "$AUTO_APPROVE" = "true" ]; then
        args+=(-auto-approve)
    fi

    terraform apply "${args[@]}"
    info "✅ 基础设施部署完成"
}

terraform_destroy() {
    warn "⚠️ 准备销毁环境: $ENVIRONMENT"

    if [ "$ENVIRONMENT" = "prod" ] && [ "$DRY_RUN" != "true" ]; then
        warn "您正在尝试销毁生产环境！"
        read -p "请输入 'DELETE PROD' 确认: " confirm
        if [ "$confirm" != "DELETE PROD" ]; then
            info "操作已取消"
            return 0
        fi
    fi

    cd "$SCRIPT_DIR/terraform"

    if [ "$DRY_RUN" = "true" ]; then
        info "[DRY RUN] terraform destroy"
        return 0
    fi

    local args=("-var=environment=${ENVIRONMENT}" "-var=aws_region=${REGION}")
    if [ "$AUTO_APPROVE" = "true" ]; then
        args+=(-auto-approve)
    fi

    terraform destroy "${args[@]}"
    info "✅ 基础设施已销毁"
}

build_and_push_images() {
    info "🐳 构建并推送Docker镜像..."

    if [ "$DRY_RUN" = "true" ]; then
        info "[DRY RUN] 构建镜像"
        return 0
    fi

    # ECR登录
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${account_id}.dkr.ecr.${REGION}.amazonaws.com"

    # 构建镜像
    docker build -t "claude-enhancer:${VERSION}" \
                 -t "claude-enhancer:latest" \
                 --target production \
                 --build-arg VERSION="$VERSION" .

    # 标记并推送到ECR
    local ecr_repo="${account_id}.dkr.ecr.${REGION}.amazonaws.com/claude-enhancer"
    docker tag "claude-enhancer:${VERSION}" "${ecr_repo}:${VERSION}"
    docker tag "claude-enhancer:${VERSION}" "${ecr_repo}:latest"
    docker push "${ecr_repo}:${VERSION}"
    docker push "${ecr_repo}:latest"

    info "✅ 镜像构建和推送完成"
}

deploy_docker_dev() {
    log_info "Deploying development environment with Docker Compose..."

    # Copy development environment file
    if [[ ! -f .env ]]; then
        cp .env.development .env
        log_info "Created .env file from .env.development"
    fi

    # Start services
    docker-compose up -d

    log_success "Development environment deployed"
    log_info "Application will be available at: http://localhost:8080"
    log_info "API Documentation: http://localhost:8080/docs"
    log_info "Grafana: http://localhost:3001 (admin/admin123)"
    log_info "pgAdmin: http://localhost:5050 (admin@claude-enhancer.local/admin123)"
}

deploy_docker_prod() {
    log_info "Deploying production environment with Docker Compose..."

    # Check if production environment file exists
    if [[ ! -f .env.production ]]; then
        log_error "Production environment file (.env.production) not found"
        log_info "Please create .env.production with your production settings"
        exit 1
    fi

    # Copy production environment file
    cp .env.production .env

    # Deploy production stack
    docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d

    log_success "Production environment deployed"
    log_info "Application will be available at: https://your-domain.com"
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi

    # Apply Kubernetes manifests
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secrets.yaml
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/redis.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/claude-enhancer.yaml
    kubectl apply -f k8s/monitoring.yaml

    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/claude-enhancer -n claude-enhancer

    log_success "Kubernetes deployment completed"
}

undeploy_kubernetes() {
    log_info "Removing Kubernetes deployment..."

    kubectl delete -f k8s/ --ignore-not-found=true

    log_success "Kubernetes deployment removed"
}

check_health() {
    log_info "Checking deployment health..."

    # Check Docker Compose deployment
    if docker-compose ps | grep -q "Up"; then
        log_info "Docker Compose services:"
        docker-compose ps

        # Check application health
        if curl -f http://localhost:8080/api/v1/health &> /dev/null; then
            log_success "Application is healthy"
        else
            log_warning "Application health check failed"
        fi
    fi

    # Check Kubernetes deployment
    if kubectl get namespace claude-enhancer &> /dev/null; then
        log_info "Kubernetes deployment status:"
        kubectl get pods -n claude-enhancer
        kubectl get services -n claude-enhancer
    fi
}

show_logs() {
    log_info "Showing application logs..."

    # Docker Compose logs
    if docker-compose ps | grep -q "Up"; then
        docker-compose logs -f claude-enhancer
    elif kubectl get namespace claude-enhancer &> /dev/null; then
        # Kubernetes logs
        kubectl logs -f deployment/claude-enhancer -n claude-enhancer
    else
        log_warning "No running deployment found"
    fi
}

clean_resources() {
    log_info "Cleaning up resources..."

    # Stop Docker Compose
    docker-compose down -v --remove-orphans 2>/dev/null || true

    # Remove Docker images
    docker rmi "${PROJECT_NAME}:${VERSION}" 2>/dev/null || true
    docker rmi "${PROJECT_NAME}:latest" 2>/dev/null || true

    # Clean up Kubernetes
    undeploy_kubernetes 2>/dev/null || true

    log_success "Resources cleaned up"
}

parse_arguments() {
    ENVIRONMENT="dev"
    REGION="us-east-1"
    DRY_RUN="false"
    AUTO_APPROVE="false"
    VERSION=""
    COMMAND=""
    SERVICE=""
    REPLICAS=""
    FOLLOW=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment) ENVIRONMENT="$2"; shift 2 ;;
            -r|--region) REGION="$2"; shift 2 ;;
            -v|--version) VERSION="$2"; shift 2 ;;
            --dry-run) DRY_RUN="true"; shift ;;
            --auto-approve) AUTO_APPROVE="true"; shift ;;
            --service) SERVICE="$2"; shift 2 ;;
            --replicas) REPLICAS="$2"; shift 2 ;;
            --follow) FOLLOW="--follow"; shift ;;
            -h|--help) show_help; exit 0 ;;
            plan|apply|destroy|build|deploy|status|logs|scale|cleanup) COMMAND="$1"; shift ;;
            *) error "未知选项: $1"; show_help; exit 1 ;;
        esac
    done

    if [ -z "$COMMAND" ]; then
        error "请指定命令"
        show_help
        exit 1
    fi

    if [ -z "$VERSION" ]; then
        if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
            VERSION=$(git rev-parse --short HEAD)
        else
            VERSION="latest"
        fi
    fi

    case $ENVIRONMENT in
        dev|staging|prod) ;;
        *) error "无效环境: $ENVIRONMENT"; exit 1 ;;
    esac
}

show_status() {
    info "📊 部署状态"
    echo "环境: $ENVIRONMENT"
    echo "区域: $REGION"
    echo "版本: $VERSION"

    # 检查ECS服务状态
    local cluster_name="claude-enhancer-${ENVIRONMENT}-cluster"
    local services=("auth" "core" "agent" "workflow")

    printf "%-15s %-10s %-10s %-10s\n" "SERVICE" "STATUS" "DESIRED" "RUNNING"
    printf "%-15s %-10s %-10s %-10s\n" "-------" "------" "-------" "-------"

    for service in "${services[@]}"; do
        local service_name="claude-enhancer-${ENVIRONMENT}-${service}"
        if aws ecs describe-services --region "$REGION" --cluster "$cluster_name" --services "$service_name" &> /dev/null; then
            local service_info=$(aws ecs describe-services --region "$REGION" --cluster "$cluster_name" --services "$service_name" --query 'services[0]' --output json)
            local status=$(echo "$service_info" | jq -r '.status')
            local desired=$(echo "$service_info" | jq -r '.desiredCount')
            local running=$(echo "$service_info" | jq -r '.runningCount')
            printf "%-15s %-10s %-10s %-10s\n" "$service" "$status" "$desired" "$running"
        else
            printf "%-15s %-10s %-10s %-10s\n" "$service" "NOT_FOUND" "-" "-"
        fi
    done
}

show_logs() {
    local service=${SERVICE:-"auth"}
    local log_group="/ecs/claude-enhancer-${ENVIRONMENT}-${service}"
    info "📜 查看日志: $service"

    aws logs tail "$log_group" --region "$REGION" --since "1h" $FOLLOW
}

scale_service() {
    local service=${SERVICE:-"core"}
    local replicas=${REPLICAS:-"3"}
    local cluster_name="claude-enhancer-${ENVIRONMENT}-cluster"
    local service_name="claude-enhancer-${ENVIRONMENT}-${service}"

    info "📊 扩缩容服务: $service -> $replicas 副本"

    if [ "$DRY_RUN" = "true" ]; then
        info "[DRY RUN] 扩缩容: $service_name -> $replicas"
        return 0
    fi

    aws ecs update-service --region "$REGION" --cluster "$cluster_name" --service "$service_name" --desired-count "$replicas"
    aws ecs wait services-stable --region "$REGION" --cluster "$cluster_name" --services "$service_name"
    info "✅ 扩缩容完成"
}

cleanup_resources() {
    info "🧹 清理未使用的资源..."

    if [ "$DRY_RUN" = "true" ]; then
        info "[DRY RUN] 清理资源"
        return 0
    fi

    docker system prune -f
    info "✅ 资源清理完成"
}

main() {
    info "${CYAN}Claude Enhancer 5.1 云部署脚本 v${VERSION}${NC}"
    info "环境: $ENVIRONMENT | 区域: $REGION | 版本: $VERSION"
    echo

    check_dependencies
    verify_aws_credentials
    terraform_init

    case $COMMAND in
        plan)    terraform_plan ;;
        apply)   terraform_apply ;;
        destroy) terraform_destroy ;;
        build)   build_and_push_images ;;
        deploy)
            info "🚀 开始完整部署流程..."
            build_and_push_images
            terraform_apply
            show_status
            info "🎉 部署完成！"
            ;;
        status)  show_status ;;
        logs)    show_logs ;;
        scale)   scale_service ;;
        cleanup) cleanup_resources ;;
        *)       error "未知命令: $COMMAND"; exit 1 ;;
    esac
}

# 脚本入口
parse_arguments "$@"
main

info "✅ 脚本执行完成"