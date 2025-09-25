#!/bin/bash
# 🚀 Claude Enhancer 一键部署脚本
#
# 使用方法:
#   ./deploy.sh [environment] [strategy]
#
# 示例:
#   ./deploy.sh production rolling
#   ./deploy.sh staging blue-green
#   ./deploy.sh development recreate

set -euo pipefail

# 脚本配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly LOG_FILE="/var/log/claude-enhancer/deployment.log"

# 部署参数
ENVIRONMENT="${1:-production}"
DEPLOYMENT_STRATEGY="${2:-rolling}"
FORCE_DEPLOY="${3:-false}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE" >&2
}

log_step() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] STEP: $1${NC}" | tee -a "$LOG_FILE"
}

print_banner() {
    cat << 'EOF'

 ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗
██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝
██║     ██║     ███████║██║   ██║██║  ██║█████╗
██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝
╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝

    ███████╗███╗   ██╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗███████╗██████╗
    ██╔════╝████╗  ██║██║  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝██╔══██╗
    █████╗  ██╔██╗ ██║███████║███████║██╔██╗ ██║██║     █████╗  ██████╔╝
    ██╔══╝  ██║╚██╗██║██╔══██║██╔══██║██║╚██╗██║██║     ██╔══╝  ██╔══██╗
    ███████╗██║ ╚████║██║  ██║██║  ██║██║ ╚████║╚██████╗███████╗██║  ██║
    ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═╝  ╚═╝

                    🚀 Enterprise Performance Optimization System 🚀
                                v4.1.0 - Ready for Production

EOF
}

print_deployment_info() {
    cat << EOF

${CYAN}📋 部署配置信息${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 目标环境:     ${ENVIRONMENT}
🚀 部署策略:     ${DEPLOYMENT_STRATEGY}
📂 项目目录:     ${PROJECT_DIR}
📝 日志文件:     ${LOG_FILE}
👤 执行用户:     ${USER}
🕐 开始时间:     $(date '+%Y-%m-%d %H:%M:%S')
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
}

check_prerequisites() {
    log_step "检查部署前置条件..."

    # 检查必需的命令
    local required_commands=("docker" "docker-compose" "git" "curl" "jq")

    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log_error "必需命令未找到: $cmd"
            return 1
        fi
    done

    # 检查 Docker 服务
    if ! systemctl is-active --quiet docker; then
        log_error "Docker 服务未运行"
        return 1
    fi

    # 检查项目目录
    if [ ! -d "$PROJECT_DIR/.claude" ]; then
        log_error "Claude Enhancer 配置目录不存在: $PROJECT_DIR/.claude"
        return 1
    fi

    # 检查部署脚本
    local script_dir="$PROJECT_DIR/deployment/scripts"
    if [ ! -d "$script_dir" ]; then
        log_error "部署脚本目录不存在: $script_dir"
        return 1
    fi

    log_info "✅ 前置条件检查通过"
    return 0
}

confirm_deployment() {
    if [ "$FORCE_DEPLOY" = "true" ]; then
        log_info "🔥 强制部署模式，跳过确认"
        return 0
    fi

    echo ""
    echo -e "${YELLOW}⚠️ 确认部署信息${NC}"
    echo -e "环境: ${RED}${ENVIRONMENT}${NC}"
    echo -e "策略: ${RED}${DEPLOYMENT_STRATEGY}${NC}"
    echo ""

    if [ "$ENVIRONMENT" = "production" ]; then
        echo -e "${RED}🚨 警告: 这是生产环境部署！${NC}"
        echo -e "${RED}🚨 请确保已经完成所有测试和验证！${NC}"
        echo ""
    fi

    read -p "确认继续部署? (yes/no): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "用户取消部署"
        exit 0
    fi

    log_info "✅ 用户确认部署"
}

execute_deployment_phase() {
    local phase_number="$1"
    local phase_name="$2"
    local script_path="$3"

    log_step "Phase $phase_number: $phase_name"

    local start_time=$(date +%s)

    # 显示进度条
    echo -ne "${CYAN}执行中"
    for i in {1..3}; do
        sleep 0.5
        echo -ne "."
    done
    echo -e "${NC}"

    if [ -f "$script_path" ]; then
        if bash "$script_path"; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            log_info "✅ Phase $phase_number 完成 (耗时: ${duration}s)"
            return 0
        else
            log_error "❌ Phase $phase_number 失败"
            return 1
        fi
    else
        log_error "❌ 脚本文件不存在: $script_path"
        return 1
    fi
}

run_deployment_pipeline() {
    log_info "🚀 启动部署流水线..."

    local pipeline_start=$(date +%s)
    local scripts_dir="$PROJECT_DIR/deployment/scripts"

    # 设置环境变量
    export ENVIRONMENT
    export DEPLOYMENT_STRATEGY

    # Phase 1: 部署前检查
    if ! execute_deployment_phase "1" "部署前检查" "$scripts_dir/01_pre_deployment_check.sh"; then
        log_error "部署前检查失败，终止部署"
        return 1
    fi

    # Phase 2: 系统备份
    if ! execute_deployment_phase "2" "系统备份" "$scripts_dir/02_backup_current_system.sh"; then
        log_error "系统备份失败，终止部署"
        return 1
    fi

    # Phase 3: 应用部署
    if ! execute_deployment_phase "3" "应用部署" "$scripts_dir/03_deploy_application.sh"; then
        log_error "应用部署失败，开始回滚"
        bash "$scripts_dir/rollback.sh" --auto
        return 1
    fi

    # Phase 4: 数据库迁移
    if ! execute_deployment_phase "4" "数据库迁移" "$scripts_dir/04_database_migration.sh"; then
        log_error "数据库迁移失败，开始回滚"
        bash "$scripts_dir/rollback.sh" --auto
        return 1
    fi

    # Phase 5: 部署后验证
    if ! execute_deployment_phase "5" "部署后验证" "$scripts_dir/05_post_deployment_verify.sh"; then
        log_error "部署后验证失败，开始回滚"
        bash "$scripts_dir/rollback.sh" --auto
        return 1
    fi

    # Phase 6: 监控配置
    if ! execute_deployment_phase "6" "监控配置" "$scripts_dir/06_monitoring_setup.sh"; then
        log_warn "监控配置失败，但部署继续（非关键性失败）"
    fi

    local pipeline_end=$(date +%s)
    local total_duration=$((pipeline_end - pipeline_start))

    log_info "🎉 部署流水线成功完成！"
    log_info "📊 总耗时: ${total_duration}s"

    return 0
}

verify_deployment() {
    log_step "验证部署结果..."

    # 基础健康检查
    local max_attempts=12
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "🔍 健康检查尝试 $attempt/$max_attempts"

        if curl -f -s --max-time 10 http://localhost:8080/health >/dev/null 2>&1; then
            log_info "✅ 应用健康检查通过"
            break
        fi

        if [ $attempt -eq $max_attempts ]; then
            log_error "❌ 应用健康检查失败"
            return 1
        fi

        log_info "⏳ 等待应用启动..."
        sleep 10
        ((attempt++))
    done

    # 功能验证
    log_info "🧪 执行功能验证..."

    # 检查关键端点
    local endpoints=("/health" "/api/agents/status" "/api/workflow/status")

    for endpoint in "${endpoints[@]}"; do
        if curl -f -s --max-time 5 "http://localhost:8080$endpoint" >/dev/null 2>&1; then
            log_info "✅ 端点验证通过: $endpoint"
        else
            log_error "❌ 端点验证失败: $endpoint"
            return 1
        fi
    done

    log_info "✅ 部署验证完成"
    return 0
}

print_deployment_summary() {
    local deployment_end=$(date +%s)
    local deployment_start="${DEPLOYMENT_START_TIME:-$deployment_end}"
    local total_time=$((deployment_end - deployment_start))

    cat << EOF

${GREEN}🎉 部署成功完成！${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 部署统计:
   • 目标环境: ${ENVIRONMENT}
   • 部署策略: ${DEPLOYMENT_STRATEGY}
   • 总耗时: ${total_time}s
   • 完成时间: $(date '+%Y-%m-%d %H:%M:%S')
   • 版本: $(cd "$PROJECT_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "unknown")

🌐 应用访问:
   • 主应用: http://localhost:8080
   • 健康检查: http://localhost:8080/health
   • 性能监控: http://localhost:8080/dashboard
   • API文档: http://localhost:8080/docs

📋 后续建议:
   • 密切监控应用运行状态 (建议24小时)
   • 检查监控告警配置
   • 验证关键业务功能
   • 准备应急响应团队
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
}

print_failure_summary() {
    cat << EOF

${RED}❌ 部署失败！${NC}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 失败信息:
   • 环境: ${ENVIRONMENT}
   • 策略: ${DEPLOYMENT_STRATEGY}
   • 失败时间: $(date '+%Y-%m-%d %H:%M:%S')

🔍 故障排查:
   • 查看日志: tail -f ${LOG_FILE}
   • 检查服务: docker-compose ps
   • 手动回滚: bash deployment/scripts/rollback.sh
   • 联系支持: 查看 TROUBLESHOOTING.md

📞 应急联系:
   • 技术负责人: [请填写联系方式]
   • 运维团队: [请填写联系方式]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
}

send_notification() {
    local status="$1"
    local message="$2"

    # Slack 通知 (如果配置了webhook)
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local emoji="✅"
        local color="good"

        if [ "$status" != "success" ]; then
            emoji="❌"
            color="danger"
        fi

        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data "{
                \"text\": \"$emoji Claude Enhancer 部署通知\",
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"fields\": [
                        {\"title\": \"状态\", \"value\": \"$status\", \"short\": true},
                        {\"title\": \"环境\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                        {\"title\": \"消息\", \"value\": \"$message\", \"short\": false}
                    ]
                }]
            }" >/dev/null 2>&1 || true
    fi

    # 邮件通知 (如果配置了邮件)
    if [ -n "${NOTIFICATION_EMAIL:-}" ]; then
        echo "$message" | mail -s "Claude Enhancer 部署通知 - $status" "$NOTIFICATION_EMAIL" 2>/dev/null || true
    fi
}

cleanup_on_exit() {
    local exit_code=$?

    if [ $exit_code -ne 0 ]; then
        log_error "部署过程异常退出 (退出码: $exit_code)"
        print_failure_summary
        send_notification "failure" "部署过程异常终止，退出码: $exit_code"
    fi
}

show_help() {
    cat << EOF
🚀 Claude Enhancer 一键部署脚本

使用方法:
  $0 [ENVIRONMENT] [STRATEGY] [FORCE]

参数:
  ENVIRONMENT     部署环境 (默认: production)
                  可选: development, staging, production

  STRATEGY        部署策略 (默认: rolling)
                  可选: rolling, blue-green, canary, recreate

  FORCE          强制部署，跳过确认 (默认: false)
                  可选: true, false

示例:
  $0 production rolling         # 生产环境滚动部署
  $0 staging blue-green        # 测试环境蓝绿部署
  $0 development recreate true # 开发环境重建部署(强制)

环境变量:
  DATABASE_URL         数据库连接地址
  REDIS_URL           Redis连接地址
  SLACK_WEBHOOK_URL   Slack通知webhook
  NOTIFICATION_EMAIL  邮件通知地址

更多信息:
  部署文档: DEPLOYMENT_GUIDE.md
  故障排查: TROUBLESHOOTING.md
  API文档: API_REFERENCE.md

EOF
}

main() {
    # 设置退出处理
    trap cleanup_on_exit EXIT

    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"

    # 记录部署开始时间
    export DEPLOYMENT_START_TIME=$(date +%s)

    # 显示帮助
    if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
        show_help
        exit 0
    fi

    # 显示横幅和配置信息
    print_banner
    print_deployment_info

    log_info "🚀 开始 Claude Enhancer 部署流程"

    # 执行部署流程
    if check_prerequisites && \
       confirm_deployment && \
       run_deployment_pipeline && \
       verify_deployment; then

        print_deployment_summary
        send_notification "success" "Claude Enhancer 部署成功完成！环境: $ENVIRONMENT"

        log_info "🎉 部署流程全部完成！"
        exit 0
    else
        print_failure_summary
        send_notification "failure" "Claude Enhancer 部署失败！环境: $ENVIRONMENT"

        log_error "❌ 部署流程失败！"
        exit 1
    fi
}

# 执行主函数
main "$@"