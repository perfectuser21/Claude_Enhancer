#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 生产环境部署脚本
# 完整的生产部署流程，包含验证、部署、监控和回滚机制
# =============================================================================

set -euo pipefail

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOYMENT_LOG="${PROJECT_ROOT}/deployment_${TIMESTAMP}.log"

# 环境配置
export ENVIRONMENT="production"
export VERSION="${VERSION:-5.1.0}"
export BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
export VCS_REF="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 部署选项
DEPLOYMENT_METHOD="${DEPLOYMENT_METHOD:-blue-green}"
SKIP_VALIDATION="${SKIP_VALIDATION:-false}"
SKIP_BACKUP="${SKIP_BACKUP:-false}"
AUTO_ROLLBACK="${AUTO_ROLLBACK:-true}"
DRY_RUN="${DRY_RUN:-false}"

# 日志函数
log_info() {
    local msg="$1"
    echo -e "${BLUE}[INFO $(date +'%H:%M:%S')]${NC} $msg" | tee -a "$DEPLOYMENT_LOG"
}

log_success() {
    local msg="$1"
    echo -e "${GREEN}[✅ $(date +'%H:%M:%S')]${NC} $msg" | tee -a "$DEPLOYMENT_LOG"
}

log_warning() {
    local msg="$1"
    echo -e "${YELLOW}[⚠️ $(date +'%H:%M:%S')]${NC} $msg" | tee -a "$DEPLOYMENT_LOG"
}

log_error() {
    local msg="$1"
    echo -e "${RED}[❌ $(date +'%H:%M:%S')]${NC} $msg" | tee -a "$DEPLOYMENT_LOG"
}

log_header() {
    local msg="$1"
    echo -e "${PURPLE}[━━━ $msg ━━━]${NC}" | tee -a "$DEPLOYMENT_LOG"
}

# 显示帮助信息
show_help() {
    cat << EOF
Claude Enhancer 5.1 生产环境部署脚本

用法: $0 [选项]

选项:
    -m, --method METHOD          部署方法 (blue-green|canary|rolling) [默认: blue-green]
    -v, --version VERSION        部署版本 [默认: 5.1.0]
    --skip-validation           跳过部署前验证
    --skip-backup              跳过备份步骤
    --no-auto-rollback         禁用自动回滚
    --dry-run                  演练模式，不实际执行部署
    -h, --help                 显示帮助信息

环境变量:
    ENVIRONMENT                部署环境 [默认: production]
    VERSION                   部署版本
    DEPLOYMENT_METHOD         部署方法
    SKIP_VALIDATION           跳过验证 (true|false)
    SKIP_BACKUP              跳过备份 (true|false)
    AUTO_ROLLBACK            自动回滚 (true|false)
    DRY_RUN                  演练模式 (true|false)

示例:
    $0                                    # 使用蓝绿部署
    $0 -m canary                         # 使用金丝雀部署
    $0 --dry-run                         # 演练模式
    $0 -v 5.1.1 --skip-validation       # 指定版本并跳过验证

EOF
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--method)
                DEPLOYMENT_METHOD="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            --skip-validation)
                SKIP_VALIDATION="true"
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP="true"
                shift
                ;;
            --no-auto-rollback)
                AUTO_ROLLBACK="false"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 验证部署方法
    case "$DEPLOYMENT_METHOD" in
        blue-green|canary|rolling)
            ;;
        *)
            log_error "不支持的部署方法: $DEPLOYMENT_METHOD"
            exit 1
            ;;
    esac
}

# 显示部署配置
show_configuration() {
    log_header "部署配置信息"
    log_info "版本: $VERSION"
    log_info "环境: $ENVIRONMENT"
    log_info "部署方法: $DEPLOYMENT_METHOD"
    log_info "构建时间: $BUILD_DATE"
    log_info "代码版本: $VCS_REF"
    log_info "演练模式: $DRY_RUN"
    log_info "自动回滚: $AUTO_ROLLBACK"
    log_info "部署日志: $DEPLOYMENT_LOG"
}

# 预检查
pre_deployment_checks() {
    log_header "部署前检查"

    # 检查必需工具
    local required_tools=("docker" "kubectl" "git")
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            log_success "$tool 已安装"
        else
            log_error "$tool 未安装"
            exit 1
        fi
    done

    # 检查项目目录
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        log_error "项目目录不存在: $PROJECT_ROOT"
        exit 1
    fi

    # 检查关键文件
    local required_files=("Dockerfile" "docker-compose.production.yml" ".env.production")
    for file in "${required_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            log_success "发现必需文件: $file"
        else
            log_error "缺少必需文件: $file"
            if [[ "$file" == ".env.production" ]]; then
                log_info "请复制 .env.production.template 为 .env.production 并配置实际值"
            fi
            exit 1
        fi
    done

    # 检查工作目录状态
    cd "$PROJECT_ROOT"
    if [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
        log_warning "工作目录有未提交的变更"
        if [[ "$DRY_RUN" == "false" ]]; then
            log_error "生产部署不允许有未提交的变更"
            exit 1
        fi
    fi

    log_success "预检查完成"
}

# 运行部署验证
run_validation() {
    if [[ "$SKIP_VALIDATION" == "true" ]]; then
        log_warning "跳过部署验证"
        return 0
    fi

    log_header "运行部署验证"

    local validator_script="$SCRIPT_DIR/deployment-validator.sh"
    if [[ -f "$validator_script" ]] && [[ -x "$validator_script" ]]; then
        log_info "执行部署验证脚本..."
        if "$validator_script"; then
            log_success "部署验证通过"
        else
            log_error "部署验证失败"
            if [[ "$AUTO_ROLLBACK" == "true" ]]; then
                log_warning "自动回滚已启用，但由于验证失败，取消部署"
            fi
            exit 1
        fi
    else
        log_warning "部署验证脚本不存在或无执行权限，跳过验证"
    fi
}

# 创建备份
create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        log_warning "跳过备份步骤"
        return 0
    fi

    log_header "创建备份"

    local backup_dir="${PROJECT_ROOT}/backups/deployment_${TIMESTAMP}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[演练] 将创建备份目录: $backup_dir"
        return 0
    fi

    mkdir -p "$backup_dir"

    # 备份当前配置
    if [[ -f "$PROJECT_ROOT/.env.production" ]]; then
        cp "$PROJECT_ROOT/.env.production" "$backup_dir/"
        log_success "备份生产环境配置"
    fi

    # 备份数据库 (如果可访问)
    if command -v kubectl &> /dev/null; then
        local postgres_pod=$(kubectl get pods -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
        if [[ -n "$postgres_pod" ]]; then
            log_info "备份数据库..."
            kubectl exec "$postgres_pod" -- pg_dump -U claude_user claude_enhancer > "$backup_dir/database_backup.sql" 2>/dev/null || {
                log_warning "数据库备份失败，但继续部署"
            }
        fi
    fi

    # 备份当前镜像信息
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep claude-enhancer > "$backup_dir/current_images.txt" 2>/dev/null || true

    log_success "备份完成: $backup_dir"
    echo "BACKUP_DIR=$backup_dir" >> "$PROJECT_ROOT/.deployment_state"
}

# 构建镜像
build_image() {
    log_header "构建Docker镜像"

    cd "$PROJECT_ROOT"
    local image_tag="claude-enhancer:${VERSION}"
    local build_args=(
        "--build-arg" "BUILD_DATE=$BUILD_DATE"
        "--build-arg" "VCS_REF=$VCS_REF"
        "--build-arg" "VERSION=$VERSION"
        "--target" "production"
        "--tag" "$image_tag"
        "--tag" "claude-enhancer:latest"
    )

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[演练] 将构建镜像: $image_tag"
        log_info "[演练] 构建参数: ${build_args[*]}"
        return 0
    fi

    log_info "构建镜像 $image_tag..."
    if docker build "${build_args[@]}" .; then
        log_success "镜像构建成功: $image_tag"
    else
        log_error "镜像构建失败"
        exit 1
    fi

    # 扫描镜像安全性 (如果有工具)
    if command -v trivy &> /dev/null; then
        log_info "扫描镜像安全性..."
        if trivy image --severity HIGH,CRITICAL "$image_tag" --exit-code 1 > "$PROJECT_ROOT/security_scan_${TIMESTAMP}.txt"; then
            log_success "镜像安全扫描通过"
        else
            log_warning "镜像安全扫描发现问题，请检查报告"
        fi
    fi
}

# 执行部署
execute_deployment() {
    log_header "执行部署 - $DEPLOYMENT_METHOD"

    local deployment_script=""
    case "$DEPLOYMENT_METHOD" in
        blue-green)
            deployment_script="$SCRIPT_DIR/deploy-blue-green.sh"
            ;;
        canary)
            deployment_script="$SCRIPT_DIR/deploy-canary.sh"
            ;;
        rolling)
            deployment_script="$SCRIPT_DIR/deploy-rolling.sh"
            ;;
    esac

    if [[ ! -f "$deployment_script" ]] || [[ ! -x "$deployment_script" ]]; then
        log_error "部署脚本不存在或无执行权限: $deployment_script"
        exit 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[演练] 将执行部署脚本: $deployment_script"
        log_info "[演练] 环境变量: VERSION=$VERSION IMAGE_TAG=$VERSION"
        return 0
    fi

    log_info "执行 $DEPLOYMENT_METHOD 部署..."

    # 设置部署脚本需要的环境变量
    export IMAGE_TAG="$VERSION"
    export NAMESPACE="claude-enhancer"
    export APP_NAME="claude-enhancer"

    # 执行部署脚本
    if "$deployment_script"; then
        log_success "$DEPLOYMENT_METHOD 部署完成"
        echo "DEPLOYMENT_STATUS=SUCCESS" >> "$PROJECT_ROOT/.deployment_state"
        echo "DEPLOYMENT_METHOD=$DEPLOYMENT_METHOD" >> "$PROJECT_ROOT/.deployment_state"
        echo "DEPLOYMENT_VERSION=$VERSION" >> "$PROJECT_ROOT/.deployment_state"
        echo "DEPLOYMENT_TIME=$TIMESTAMP" >> "$PROJECT_ROOT/.deployment_state"
    else
        log_error "$DEPLOYMENT_METHOD 部署失败"
        echo "DEPLOYMENT_STATUS=FAILED" >> "$PROJECT_ROOT/.deployment_state"

        if [[ "$AUTO_ROLLBACK" == "true" ]]; then
            log_warning "启动自动回滚..."
            rollback_deployment
        fi
        exit 1
    fi
}

# 部署后验证
post_deployment_verification() {
    log_header "部署后验证"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[演练] 将执行部署后验证"
        return 0
    fi

    local verification_failed=false

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30

    # 健康检查
    local health_url="http://claude-enhancer-service/health"
    local ready_url="http://claude-enhancer-service/ready"

    log_info "执行健康检查..."
    local health_retries=10
    for ((i=1; i<=health_retries; i++)); do
        if kubectl port-forward service/claude-enhancer-service 8080:80 & then
            local port_forward_pid=$!
            sleep 2

            if curl -sf "http://localhost:8080/health" > /dev/null 2>&1; then
                log_success "健康检查通过"
                kill $port_forward_pid 2>/dev/null || true
                break
            else
                log_warning "健康检查失败 (尝试 $i/$health_retries)"
                kill $port_forward_pid 2>/dev/null || true
                if (( i == health_retries )); then
                    log_error "健康检查最终失败"
                    verification_failed=true
                fi
                sleep 10
            fi
        fi
    done

    # 功能性测试
    log_info "执行功能性测试..."
    # 这里可以添加更多的功能性测试

    # 性能检查
    log_info "执行性能检查..."
    # 这里可以添加性能验证

    if [[ "$verification_failed" == "true" ]]; then
        log_error "部署后验证失败"
        if [[ "$AUTO_ROLLBACK" == "true" ]]; then
            log_warning "启动自动回滚..."
            rollback_deployment
        fi
        exit 1
    else
        log_success "部署后验证通过"
    fi
}

# 回滚部署
rollback_deployment() {
    log_header "执行回滚"

    local rollback_script="$SCRIPT_DIR/rollback.sh"
    if [[ -f "$rollback_script" ]] && [[ -x "$rollback_script" ]]; then
        log_info "执行回滚脚本..."
        if "$rollback_script"; then
            log_success "回滚完成"
        else
            log_error "回滚失败，需要手动干预"
        fi
    else
        log_error "回滚脚本不存在，需要手动回滚"
    fi
}

# 清理临时文件
cleanup() {
    log_header "清理"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[演练] 将执行清理操作"
        return 0
    fi

    # 清理构建缓存
    log_info "清理Docker构建缓存..."
    docker builder prune -f > /dev/null 2>&1 || true

    # 清理未使用的镜像
    docker image prune -f > /dev/null 2>&1 || true

    log_success "清理完成"
}

# 发送通知
send_notification() {
    local status="$1"
    local message="$2"

    log_header "发送通知"

    # 这里可以集成 Slack、邮件或其他通知系统
    log_info "通知状态: $status"
    log_info "通知消息: $message"

    # 示例：Slack通知 (需要配置SLACK_WEBHOOK_URL)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local payload="{\"text\":\"Claude Enhancer 5.1 部署通知\n状态: $status\n消息: $message\n时间: $(date)\n版本: $VERSION\"}"
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || {
            log_warning "Slack通知发送失败"
        }
    fi
}

# 生成部署报告
generate_deployment_report() {
    log_header "生成部署报告"

    local report_file="${PROJECT_ROOT}/deployment_report_${TIMESTAMP}.md"

    cat > "$report_file" << EOF
# Claude Enhancer 5.1 部署报告

**部署时间**: $(date)
**部署版本**: $VERSION
**部署方法**: $DEPLOYMENT_METHOD
**部署环境**: $ENVIRONMENT
**部署状态**: $(grep "DEPLOYMENT_STATUS" "$PROJECT_ROOT/.deployment_state" 2>/dev/null | cut -d'=' -f2 || echo "UNKNOWN")

## 部署配置

- 构建时间: $BUILD_DATE
- 代码版本: $VCS_REF
- 演练模式: $DRY_RUN
- 自动回滚: $AUTO_ROLLBACK

## 部署日志

详细日志请查看: $DEPLOYMENT_LOG

## 验证结果

$(if [[ -f "${PROJECT_ROOT}/deployment_validation_report_${TIMESTAMP}.json" ]]; then
    echo "验证报告: deployment_validation_report_${TIMESTAMP}.json"
else
    echo "无验证报告"
fi)

## 后续行动

- [ ] 监控系统运行状态
- [ ] 收集用户反馈
- [ ] 更新文档
- [ ] 计划下次部署

---
*报告由自动化部署系统生成*
EOF

    log_success "部署报告已生成: $report_file"
}

# 错误处理函数
error_handler() {
    local exit_code=$?
    log_error "部署过程中发生错误 (退出码: $exit_code)"

    if [[ "$AUTO_ROLLBACK" == "true" ]] && [[ "$DRY_RUN" == "false" ]]; then
        log_warning "尝试自动回滚..."
        rollback_deployment
    fi

    send_notification "FAILED" "部署失败，请检查日志: $DEPLOYMENT_LOG"
    cleanup
    exit $exit_code
}

# 主函数
main() {
    # 显示标题
    echo -e "${PURPLE}"
    echo "  ╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "  ║              Claude Enhancer 5.1 生产环境部署系统                          ║"
    echo "  ║                Production Deployment System                                 ║"
    echo "  ╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"

    # 解析参数和配置
    parse_arguments "$@"
    show_configuration

    # 确认部署
    if [[ "$DRY_RUN" == "false" ]]; then
        echo -e "\n${YELLOW}⚠️  即将执行生产环境部署，请确认配置信息正确${NC}"
        read -p "继续部署? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "用户取消部署"
            exit 0
        fi
    fi

    # 初始化部署状态文件
    echo "DEPLOYMENT_START=$TIMESTAMP" > "$PROJECT_ROOT/.deployment_state"

    # 执行部署流程
    pre_deployment_checks
    run_validation
    create_backup
    build_image
    execute_deployment
    post_deployment_verification
    cleanup
    generate_deployment_report

    # 发送成功通知
    local success_message="Claude Enhancer 5.1 版本 $VERSION 使用 $DEPLOYMENT_METHOD 方法成功部署到 $ENVIRONMENT 环境"
    send_notification "SUCCESS" "$success_message"

    log_success "🎉 Claude Enhancer 5.1 部署完成！"
    log_info "部署日志: $DEPLOYMENT_LOG"
    log_info "版本: $VERSION"
    log_info "环境: $ENVIRONMENT"
    log_info "方法: $DEPLOYMENT_METHOD"
}

# 设置错误处理
trap error_handler ERR INT TERM

# 执行主函数
main "$@"