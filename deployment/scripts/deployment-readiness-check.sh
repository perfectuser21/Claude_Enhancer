#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 部署准备状态检查脚本
# 验证系统是否准备好进行生产部署
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
readonly READINESS_LOG="${SCRIPT_DIR}/readiness-check-$(date +%Y%m%d_%H%M%S).log"

# 全局变量
declare -A CHECK_RESULTS
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# =============================================================================
# 工具函数
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$READINESS_LOG"
}

log_info() { log "INFO" "${BLUE}$*${NC}"; }
log_warn() { log "WARN" "${YELLOW}$*${NC}"; }
log_error() { log "ERROR" "${RED}$*${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$*${NC}"; }

show_header() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                Claude Enhancer 5.1 部署准备状态检查                         ║"
    echo "║                   Deployment Readiness Assessment                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
}

# 执行检查
run_check() {
    local check_name="$1"
    local check_description="$2"
    local check_command="$3"
    local severity="${4:-error}"  # error, warning, info

    ((TOTAL_CHECKS++))

    echo -n "检查 $check_description... "

    if eval "$check_command" &>/dev/null; then
        echo -e "${GREEN}✅ 通过${NC}"
        CHECK_RESULTS["$check_name"]="PASS"
        ((PASSED_CHECKS++))
        return 0
    else
        if [[ "$severity" == "warning" ]]; then
            echo -e "${YELLOW}⚠️ 警告${NC}"
            CHECK_RESULTS["$check_name"]="WARNING"
            ((WARNING_CHECKS++))
            return 1
        else
            echo -e "${RED}❌ 失败${NC}"
            CHECK_RESULTS["$check_name"]="FAIL"
            ((FAILED_CHECKS++))
            return 1
        fi
    fi
}

# =============================================================================
# 基础设施检查
# =============================================================================

check_infrastructure() {
    echo -e "${BLUE}━━━ 基础设施检查 ━━━${NC}"

    # Docker检查
    run_check "docker_running" "Docker服务运行状态" "docker info"

    # Kubernetes连接检查
    run_check "k8s_connection" "Kubernetes集群连接" "kubectl cluster-info"

    # Kubernetes节点检查
    run_check "k8s_nodes_ready" "Kubernetes节点就绪状态" "kubectl get nodes | grep -v NotReady"

    # 命名空间检查
    run_check "namespace_exists" "目标命名空间存在" "kubectl get namespace claude-enhancer"

    # 资源配额检查
    check_resource_quota

    # 存储检查
    run_check "storage_available" "存储空间充足" "df -h /var/lib/docker | awk 'NR==2 {if(\$5+0 < 80) exit 0; else exit 1}'"

    echo
}

check_resource_quota() {
    echo -n "检查资源配额... "

    # 检查CPU和内存可用性
    local cpu_capacity
    local memory_capacity
    local cpu_allocatable
    local memory_allocatable

    cpu_capacity=$(kubectl top nodes --no-headers 2>/dev/null | awk '{sum+=$2} END {print sum}' | sed 's/m//' || echo "0")
    memory_capacity=$(kubectl top nodes --no-headers 2>/dev/null | awk '{sum+=$4} END {print sum}' | sed 's/Mi//' || echo "0")

    # 检查是否有足够资源部署
    # 金丝雀 + 绿色环境大约需要 15 CPUs 和 30GB内存
    if [[ "$cpu_capacity" -gt 15000 ]] && [[ "$memory_capacity" -gt 30000 ]]; then
        echo -e "${GREEN}✅ 通过${NC}"
        CHECK_RESULTS["resource_quota"]="PASS"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}⚠️ 警告 (CPU: ${cpu_capacity}m, Memory: ${memory_capacity}Mi)${NC}"
        CHECK_RESULTS["resource_quota"]="WARNING"
        ((WARNING_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# =============================================================================
# 应用配置检查
# =============================================================================

check_application_config() {
    echo -e "${BLUE}━━━ 应用配置检查 ━━━${NC}"

    # Docker镜像检查
    run_check "docker_image_exists" "Docker镜像存在" "docker manifest inspect claude-enhancer:5.1"

    # 配置文件检查
    run_check "deployment_configs" "部署配置文件完整" "[[ -f '$PROJECT_ROOT/deployment/deployment-config.yaml' ]]"

    # Agent配置检查
    run_check "agent_configs" "61个Agent配置文件" "[[ -d '$PROJECT_ROOT/.claude/agents' ]] && [[ \$(find '$PROJECT_ROOT/.claude/agents' -name '*.yaml' | wc -l) -eq 61 ]]"

    # 工作流配置检查
    run_check "workflow_config" "8-Phase工作流配置" "[[ -f '$PROJECT_ROOT/.phase/current' ]]"

    # Git Hooks检查
    run_check "git_hooks" "Git Hooks安装" "[[ -f '$PROJECT_ROOT/.git/hooks/pre-commit' ]] && [[ -x '$PROJECT_ROOT/.git/hooks/pre-commit' ]]"

    # 环境变量检查
    check_environment_variables

    # 密钥配置检查
    run_check "secrets_config" "Kubernetes密钥配置" "kubectl get secrets claude-enhancer-secrets"

    echo
}

check_environment_variables() {
    echo -n "检查环境变量配置... "

    local required_vars=("SLACK_WEBHOOK_URL" "PROMETHEUS_URL")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -eq 0 ]]; then
        echo -e "${GREEN}✅ 通过${NC}"
        CHECK_RESULTS["environment_variables"]="PASS"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}⚠️ 警告 (缺少: ${missing_vars[*]})${NC}"
        CHECK_RESULTS["environment_variables"]="WARNING"
        ((WARNING_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# =============================================================================
# 网络和服务检查
# =============================================================================

check_network_services() {
    echo -e "${BLUE}━━━ 网络和服务检查 ━━━${NC}"

    # 服务存在检查
    run_check "service_exists" "主服务存在" "kubectl get service claude-enhancer-service"

    # Ingress检查
    run_check "ingress_config" "Ingress配置" "kubectl get ingress claude-enhancer-ingress" "warning"

    # 服务网格检查 (如果使用Istio)
    run_check "service_mesh" "服务网格配置" "kubectl get virtualservice claude-enhancer-traffic" "warning"

    # DNS解析检查
    run_check "dns_resolution" "DNS解析正常" "nslookup claude-enhancer.example.com" "warning"

    # 端口可用性检查
    run_check "port_availability" "关键端口可用" "! netstat -tulpn | grep -E ':8080|:5432|:6379'"

    # 网络策略检查
    run_check "network_policies" "网络策略配置" "kubectl get networkpolicy" "warning"

    echo
}

# =============================================================================
# 数据库和存储检查
# =============================================================================

check_database_storage() {
    echo -e "${BLUE}━━━ 数据库和存储检查 ━━━${NC}"

    # 数据库连接检查
    run_check "database_connection" "数据库连接正常" "kubectl exec -it postgres-main -- pg_isready"

    # 数据库版本检查
    run_check "database_version" "数据库版本兼容" "kubectl exec -it postgres-main -- psql -c 'SELECT version();' | grep -E 'PostgreSQL (12|13|14|15)'"

    # Redis连接检查
    run_check "redis_connection" "Redis连接正常" "kubectl exec -it redis-main -- redis-cli ping"

    # 数据库备份检查
    run_check "database_backup" "数据库备份存在" "[[ -f '/backup/latest/postgres_backup.sql' ]]" "warning"

    # 存储卷检查
    run_check "persistent_volumes" "持久化卷就绪" "kubectl get pv | grep Available"

    # 数据库迁移脚本检查
    run_check "migration_scripts" "数据库迁移脚本" "[[ -d '$PROJECT_ROOT/database/migrations' ]]" "warning"

    echo
}

# =============================================================================
# 监控和告警检查
# =============================================================================

check_monitoring_alerting() {
    echo -e "${BLUE}━━━ 监控和告警检查 ━━━${NC}"

    # Prometheus检查
    run_check "prometheus_running" "Prometheus运行正常" "kubectl get pods -n monitoring | grep prometheus | grep Running"

    # Grafana检查
    run_check "grafana_running" "Grafana运行正常" "kubectl get pods -n monitoring | grep grafana | grep Running"

    # AlertManager检查
    run_check "alertmanager_running" "AlertManager运行正常" "kubectl get pods -n monitoring | grep alertmanager | grep Running" "warning"

    # 监控指标检查
    check_prometheus_metrics

    # 告警规则检查
    run_check "alert_rules" "告警规则配置" "[[ -f '$PROJECT_ROOT/deployment/monitoring/alert_rules.yml' ]]"

    # 通知渠道检查
    check_notification_channels

    echo
}

check_prometheus_metrics() {
    echo -n "检查Prometheus指标可用性... "

    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    local test_query="up"

    if curl -s "${prometheus_url}/api/v1/query?query=${test_query}" | grep -q "success" 2>/dev/null; then
        echo -e "${GREEN}✅ 通过${NC}"
        CHECK_RESULTS["prometheus_metrics"]="PASS"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}⚠️ 警告${NC}"
        CHECK_RESULTS["prometheus_metrics"]="WARNING"
        ((WARNING_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

check_notification_channels() {
    echo -n "检查通知渠道配置... "

    local channels_ok=true

    # Slack检查
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        if ! curl -s -o /dev/null -w "%{http_code}" "$SLACK_WEBHOOK_URL" | grep -q "404\|400"; then
            channels_ok=false
        fi
    fi

    # PagerDuty检查
    if [[ -n "${PAGERDUTY_KEY:-}" ]]; then
        # 这里可以添加PagerDuty连通性测试
        :
    fi

    if $channels_ok; then
        echo -e "${GREEN}✅ 通过${NC}"
        CHECK_RESULTS["notification_channels"]="PASS"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}⚠️ 警告${NC}"
        CHECK_RESULTS["notification_channels"]="WARNING"
        ((WARNING_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# =============================================================================
# 安全配置检查
# =============================================================================

check_security_config() {
    echo -e "${BLUE}━━━ 安全配置检查 ━━━${NC}"

    # RBAC检查
    run_check "rbac_config" "RBAC配置存在" "kubectl get clusterrole claude-enhancer-role" "warning"

    # 服务账户检查
    run_check "service_account" "服务账户配置" "kubectl get serviceaccount claude-enhancer-sa"

    # Pod安全策略检查
    run_check "pod_security" "Pod安全策略" "kubectl get podsecuritypolicy claude-enhancer-psp" "warning"

    # 网络策略检查
    run_check "network_security" "网络安全策略" "kubectl get networkpolicy -n claude-enhancer" "warning"

    # 密钥轮转检查
    run_check "secret_rotation" "密钥轮转策略" "[[ -f '$PROJECT_ROOT/scripts/rotate-secrets.sh' ]]" "warning"

    # TLS证书检查
    run_check "tls_certificates" "TLS证书有效" "kubectl get secret claude-enhancer-tls -o jsonpath='{.data.tls\\.crt}' | base64 -d | openssl x509 -checkend 2592000 -noout"

    echo
}

# =============================================================================
# 部署脚本检查
# =============================================================================

check_deployment_scripts() {
    echo -e "${BLUE}━━━ 部署脚本检查 ━━━${NC}"

    # 主部署脚本检查
    run_check "main_deploy_script" "主部署脚本可执行" "[[ -x '$PROJECT_ROOT/deployment/deploy-5.1.sh' ]]"

    # 回滚脚本检查
    run_check "rollback_script" "回滚脚本可执行" "[[ -x '$PROJECT_ROOT/deployment/emergency-rollback.sh' ]]"

    # 协调脚本检查
    run_check "coordinator_script" "协调脚本可执行" "[[ -x '$PROJECT_ROOT/deployment/scripts/deployment-coordinator.sh' ]]"

    # 验证脚本检查
    run_check "validation_script" "验证脚本可执行" "[[ -x '$PROJECT_ROOT/deployment/scripts/deployment-validator.sh' ]]" "warning"

    # Kubernetes配置检查
    run_check "k8s_configs" "Kubernetes配置文件" "[[ -d '$PROJECT_ROOT/deployment/k8s' ]] && [[ \$(find '$PROJECT_ROOT/deployment/k8s' -name '*.yaml' | wc -l) -ge 4 ]]"

    # 脚本依赖检查
    check_script_dependencies

    echo
}

check_script_dependencies() {
    echo -n "检查脚本依赖工具... "

    local required_tools=("kubectl" "curl" "jq" "bc" "docker")
    local missing_tools=()

    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [[ ${#missing_tools[@]} -eq 0 ]]; then
        echo -e "${GREEN}✅ 通过${NC}"
        CHECK_RESULTS["script_dependencies"]="PASS"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}❌ 失败 (缺少: ${missing_tools[*]})${NC}"
        CHECK_RESULTS["script_dependencies"]="FAIL"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# =============================================================================
# 系统健康检查
# =============================================================================

check_system_health() {
    echo -e "${BLUE}━━━ 系统健康检查 ━━━${NC}"

    # 当前系统负载检查
    run_check "system_load" "系统负载正常" "[[ \$(uptime | awk -F'load average:' '{print \$2}' | awk '{print \$1}' | sed 's/,//') < 2.0 ]]" "warning"

    # 当前错误率检查
    check_current_error_rate

    # 当前响应时间检查
    check_current_response_time

    # Agent系统状态检查
    check_agent_system_status

    # 工作流状态检查
    run_check "workflow_status" "工作流系统正常" "kubectl get pods -l app=claude-enhancer | grep Running"

    echo
}

check_current_error_rate() {
    echo -n "检查当前错误率... "

    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    local query="rate(http_requests_total{status=~\"5..\"}[5m]) * 100"

    local error_rate
    error_rate=$(curl -s "${prometheus_url}/api/v1/query" --data-urlencode "query=${query}" 2>/dev/null | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")

    if (( $(echo "$error_rate <= 0.5" | bc -l) )); then
        echo -e "${GREEN}✅ 通过 (${error_rate}%)${NC}"
        CHECK_RESULTS["current_error_rate"]="PASS"
        ((PASSED_CHECKS++))
    else
        echo -e "${RED}❌ 失败 (${error_rate}%)${NC}"
        CHECK_RESULTS["current_error_rate"]="FAIL"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

check_current_response_time() {
    echo -n "检查当前响应时间... "

    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    local query="histogram_quantile(0.95, http_request_duration_seconds) * 1000"

    local response_time
    response_time=$(curl -s "${prometheus_url}/api/v1/query" --data-urlencode "query=${query}" 2>/dev/null | jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0")

    if (( $(echo "$response_time <= 1000" | bc -l) )); then
        echo -e "${GREEN}✅ 通过 (${response_time}ms)${NC}"
        CHECK_RESULTS["current_response_time"]="PASS"
        ((PASSED_CHECKS++))
    else
        echo -e "${YELLOW}⚠️ 警告 (${response_time}ms)${NC}"
        CHECK_RESULTS["current_response_time"]="WARNING"
        ((WARNING_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

check_agent_system_status() {
    echo -n "检查Agent系统状态... "

    local active_agents
    active_agents=$(kubectl get pods -l app=claude-enhancer -o jsonpath='{.items[*].status.containerStatuses[0].ready}' 2>/dev/null | grep -o true | wc -l || echo "0")

    if [[ "$active_agents" -ge 58 ]]; then  # 允许3个Agent离线
        echo -e "${GREEN}✅ 通过 (${active_agents}/61)${NC}"
        CHECK_RESULTS["agent_system_status"]="PASS"
        ((PASSED_CHECKS++))
    elif [[ "$active_agents" -ge 55 ]]; then
        echo -e "${YELLOW}⚠️ 警告 (${active_agents}/61)${NC}"
        CHECK_RESULTS["agent_system_status"]="WARNING"
        ((WARNING_CHECKS++))
    else
        echo -e "${RED}❌ 失败 (${active_agents}/61)${NC}"
        CHECK_RESULTS["agent_system_status"]="FAIL"
        ((FAILED_CHECKS++))
    fi
    ((TOTAL_CHECKS++))
}

# =============================================================================
# 报告生成和显示
# =============================================================================

show_summary() {
    echo
    echo -e "${PURPLE}━━━ 检查结果摘要 ━━━${NC}"

    local success_rate=0
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    fi

    echo -e "总检查项: ${CYAN}$TOTAL_CHECKS${NC}"
    echo -e "通过项数: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "警告项数: ${YELLOW}$WARNING_CHECKS${NC}"
    echo -e "失败项数: ${RED}$FAILED_CHECKS${NC}"
    echo -e "成功率: ${CYAN}${success_rate}%${NC}"

    echo
    local readiness_status=""
    local readiness_color=""

    if [[ $FAILED_CHECKS -eq 0 ]] && [[ $WARNING_CHECKS -le 3 ]]; then
        readiness_status="✅ 准备就绪"
        readiness_color="$GREEN"
        echo -e "${GREEN}🎉 Claude Enhancer 5.1 已准备好进行生产部署！${NC}"
    elif [[ $FAILED_CHECKS -le 2 ]] && [[ $WARNING_CHECKS -le 5 ]]; then
        readiness_status="⚠️ 基本就绪"
        readiness_color="$YELLOW"
        echo -e "${YELLOW}⚠️ Claude Enhancer 5.1 基本准备就绪，建议修复警告项后部署${NC}"
    else
        readiness_status="❌ 未就绪"
        readiness_color="$RED"
        echo -e "${RED}❌ Claude Enhancer 5.1 尚未准备好部署，请修复失败项${NC}"
    fi

    echo -e "\n部署建议: ${readiness_color}${readiness_status}${NC}"
}

show_failed_checks() {
    if [[ $FAILED_CHECKS -gt 0 ]] || [[ $WARNING_CHECKS -gt 0 ]]; then
        echo
        echo -e "${PURPLE}━━━ 需要注意的检查项 ━━━${NC}"

        for check in "${!CHECK_RESULTS[@]}"; do
            case "${CHECK_RESULTS[$check]}" in
                "FAIL")
                    echo -e "${RED}❌ $check: 失败${NC}"
                    ;;
                "WARNING")
                    echo -e "${YELLOW}⚠️ $check: 警告${NC}"
                    ;;
            esac
        done
    fi
}

generate_readiness_report() {
    local report_file="${SCRIPT_DIR}/readiness-report-$(date +%Y%m%d_%H%M%S).json"
    local success_rate=0

    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    fi

    # 生成JSON报告
    cat > "$report_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "summary": {
    "total_checks": $TOTAL_CHECKS,
    "passed_checks": $PASSED_CHECKS,
    "warning_checks": $WARNING_CHECKS,
    "failed_checks": $FAILED_CHECKS,
    "success_rate": $success_rate
  },
  "readiness_status": "$(
    if [[ $FAILED_CHECKS -eq 0 ]] && [[ $WARNING_CHECKS -le 3 ]]; then
      echo "READY"
    elif [[ $FAILED_CHECKS -le 2 ]] && [[ $WARNING_CHECKS -le 5 ]]; then
      echo "BASIC_READY"
    else
      echo "NOT_READY"
    fi
  )",
  "check_results": {
EOF

    local first=true
    for check in "${!CHECK_RESULTS[@]}"; do
        if [[ $first == true ]]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        echo -n "    \"$check\": \"${CHECK_RESULTS[$check]}\"" >> "$report_file"
    done

    cat >> "$report_file" << EOF

  },
  "recommendations": [
    $(if [[ $FAILED_CHECKS -gt 0 ]]; then echo "\"修复失败的检查项\","; fi)
    $(if [[ $WARNING_CHECKS -gt 3 ]]; then echo "\"处理过多的警告项\","; fi)
    "\"执行最终部署前验证\""
  ]
}
EOF

    log_info "准备状态报告已生成: $report_file"
    echo "$report_file"
}

# =============================================================================
# 主函数
# =============================================================================

show_usage() {
    cat << EOF
使用方法: $0 [选项]

选项:
  -h, --help              显示此帮助信息
  -v, --verbose           详细输出模式
  -q, --quiet             安静模式（仅显示结果）
  -r, --report-only       仅生成报告，不显示详情
  -c, --category CATEGORY 仅检查指定类别
  --skip-slow-checks      跳过耗时的检查项

检查类别:
  infrastructure          基础设施检查
  application            应用配置检查
  network                网络和服务检查
  database               数据库和存储检查
  monitoring             监控和告警检查
  security               安全配置检查
  deployment             部署脚本检查
  health                 系统健康检查

示例:
  $0                      # 执行完整检查
  $0 -c infrastructure   # 仅检查基础设施
  $0 --report-only       # 仅生成报告
  $0 --skip-slow-checks  # 跳过耗时检查
EOF
}

main() {
    local verbose=false
    local quiet=false
    local report_only=false
    local category=""
    local skip_slow_checks=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -q|--quiet)
                quiet=true
                shift
                ;;
            -r|--report-only)
                report_only=true
                shift
                ;;
            -c|--category)
                category="$2"
                shift 2
                ;;
            --skip-slow-checks)
                skip_slow_checks=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    if [[ $quiet == false ]]; then
        show_header
        log_info "开始Claude Enhancer 5.1部署准备状态检查"
        echo
    fi

    # 根据类别或全部检查
    case "$category" in
        "infrastructure"|"")
            if [[ -z "$category" ]] || [[ "$category" == "infrastructure" ]]; then
                check_infrastructure
                [[ -n "$category" ]] && exit 0
            fi
            ;;&
        "application"|"")
            if [[ -z "$category" ]] || [[ "$category" == "application" ]]; then
                check_application_config
                [[ -n "$category" ]] && exit 0
            fi
            ;;&
        "network"|"")
            if [[ -z "$category" ]] || [[ "$category" == "network" ]]; then
                check_network_services
                [[ -n "$category" ]] && exit 0
            fi
            ;;&
        "database"|"")
            if [[ -z "$category" ]] || [[ "$category" == "database" ]]; then
                check_database_storage
                [[ -n "$category" ]] && exit 0
            fi
            ;;&
        "monitoring"|"")
            if [[ -z "$category" ]] || [[ "$category" == "monitoring" ]]; then
                check_monitoring_alerting
                [[ -n "$category" ]] && exit 0
            fi
            ;;&
        "security"|"")
            if [[ -z "$category" ]] || [[ "$category" == "security" ]]; then
                check_security_config
                [[ -n "$category" ]] && exit 0
            fi
            ;;&
        "deployment"|"")
            if [[ -z "$category" ]] || [[ "$category" == "deployment" ]]; then
                check_deployment_scripts
                [[ -n "$category" ]] && exit 0
            fi
            ;;&
        "health"|"")
            if [[ -z "$category" ]] || [[ "$category" == "health" ]]; then
                check_system_health
                [[ -n "$category" ]] && exit 0
            fi
            ;;
        *)
            log_error "未知检查类别: $category"
            show_usage
            exit 1
            ;;
    esac

    # 显示结果摘要
    if [[ $quiet == false ]] && [[ $report_only == false ]]; then
        show_summary
        show_failed_checks
    fi

    # 生成报告
    local report_file
    report_file=$(generate_readiness_report)

    if [[ $quiet == false ]]; then
        echo
        echo -e "详细检查日志: ${CYAN}$READINESS_LOG${NC}"
        echo -e "JSON格式报告: ${CYAN}$report_file${NC}"
    fi

    # 根据检查结果设置退出码
    if [[ $FAILED_CHECKS -eq 0 ]] && [[ $WARNING_CHECKS -le 3 ]]; then
        exit 0  # 准备就绪
    elif [[ $FAILED_CHECKS -le 2 ]] && [[ $WARNING_CHECKS -le 5 ]]; then
        exit 1  # 基本就绪（警告）
    else
        exit 2  # 未就绪（错误）
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi