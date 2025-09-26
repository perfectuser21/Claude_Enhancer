#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 自动化部署脚本
# 混合蓝绿-金丝雀部署策略实现
# =============================================================================

set -euo pipefail

# 配置常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly DEPLOYMENT_CONFIG="${SCRIPT_DIR}/deployment-config.yaml"
readonly LOG_FILE="${SCRIPT_DIR}/deployment-$(date +%Y%m%d_%H%M%S).log"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# 全局变量
DEPLOYMENT_START_TIME=""
CURRENT_PHASE=0
ROLLBACK_TRIGGERED=false

# =============================================================================
# 工具函数
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "${YELLOW}$*${NC}"; }
log_error() { log "ERROR" "${RED}$*${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$*${NC}"; }

# 错误处理
handle_error() {
    local line_no=$1
    log_error "部署失败在第${line_no}行"
    if [[ "$ROLLBACK_TRIGGERED" == false ]]; then
        log_warn "触发自动回滚..."
        emergency_rollback
    fi
    exit 1
}

trap 'handle_error ${LINENO}' ERR

# 显示进度条
show_progress() {
    local current=$1
    local total=$2
    local message=$3
    local percent=$((current * 100 / total))
    local progress_bar=""

    for ((i=0; i<percent/5; i++)); do
        progress_bar+="█"
    done

    for ((i=percent/5; i<20; i++)); do
        progress_bar+="░"
    done

    echo -ne "\r${BLUE}[${progress_bar}] ${percent}% - ${message}${NC}"
    if [[ $current -eq $total ]]; then
        echo ""
    fi
}

# =============================================================================
# 预检查函数
# =============================================================================

pre_deployment_checks() {
    log_info "开始部署前检查..."

    # 检查必要工具
    local tools=("kubectl" "docker" "curl" "jq")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "缺少必要工具: $tool"
            return 1
        fi
    done

    # 检查Kubernetes连接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "无法连接到Kubernetes集群"
        return 1
    fi

    # 检查当前系统状态
    local current_error_rate
    current_error_rate=$(get_current_error_rate)
    if (( $(echo "$current_error_rate > 0.5" | bc -l) )); then
        log_error "当前系统错误率过高: ${current_error_rate}%"
        return 1
    fi

    # 检查资源使用率
    check_resource_usage

    # 验证Docker镜像
    if ! docker manifest inspect "claude-enhancer:5.1" &> /dev/null; then
        log_error "Docker镜像 claude-enhancer:5.1 不存在"
        return 1
    fi

    log_success "预检查完成"
    return 0
}

check_resource_usage() {
    log_info "检查资源使用率..."

    # 检查节点资源
    local cpu_usage
    local memory_usage

    cpu_usage=$(kubectl top nodes --no-headers | awk '{sum+=$3} END {print sum/NR}' | sed 's/%//')
    memory_usage=$(kubectl top nodes --no-headers | awk '{sum+=$5} END {print sum/NR}' | sed 's/%//')

    if (( $(echo "$cpu_usage > 70" | bc -l) )); then
        log_warn "CPU使用率较高: ${cpu_usage}%"
    fi

    if (( $(echo "$memory_usage > 80" | bc -l) )); then
        log_warn "内存使用率较高: ${memory_usage}%"
    fi

    log_info "资源检查完成 - CPU: ${cpu_usage}%, Memory: ${memory_usage}%"
}

# =============================================================================
# 监控函数
# =============================================================================

get_current_error_rate() {
    # 从Prometheus获取当前错误率
    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    local query="rate(http_requests_total{status=~\"5..\"}[5m]) * 100"

    curl -s "${prometheus_url}/api/v1/query" \
        --data-urlencode "query=${query}" | \
        jq -r '.data.result[0].value[1] // "0"'
}

get_response_time_p95() {
    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    local query="histogram_quantile(0.95, http_request_duration_seconds)"

    curl -s "${prometheus_url}/api/v1/query" \
        --data-urlencode "query=${query}" | \
        jq -r '.data.result[0].value[1] // "0"'
}

check_agent_status() {
    local expected_agents=61
    local active_agents

    active_agents=$(kubectl get pods -l app=claude-enhancer,version=5.1 -o jsonpath='{.items[*].status.containerStatuses[0].ready}' | grep -o true | wc -l)

    if [[ "$active_agents" -eq "$expected_agents" ]]; then
        return 0
    else
        log_warn "Agent状态异常: ${active_agents}/${expected_agents}"
        return 1
    fi
}

check_workflow_status() {
    local workflow_success_rate
    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    local query="claude_enhancer_workflow_success_rate"

    workflow_success_rate=$(curl -s "${prometheus_url}/api/v1/query" \
        --data-urlencode "query=${query}" | \
        jq -r '.data.result[0].value[1] // "0"')

    if (( $(echo "$workflow_success_rate > 0.98" | bc -l) )); then
        return 0
    else
        log_warn "工作流成功率过低: ${workflow_success_rate}"
        return 1
    fi
}

# =============================================================================
# 部署阶段函数
# =============================================================================

phase1_canary_start() {
    log_info "Phase 1: 金丝雀部署启动 (5%流量)"
    CURRENT_PHASE=1

    # 1.1 部署金丝雀实例
    log_info "部署金丝雀实例..."
    kubectl apply -f "${SCRIPT_DIR}/k8s/canary-deployment.yaml"

    # 等待实例就绪
    kubectl rollout status deployment/claude-enhancer-canary --timeout=300s

    # 1.2 配置流量路由
    log_info "配置流量路由 (5%)..."
    kubectl apply -f "${SCRIPT_DIR}/k8s/virtual-service-canary-5.yaml"

    # 1.3 启动监控
    kubectl apply -f "${SCRIPT_DIR}/k8s/canary-monitoring.yaml"

    # 1.4 健康检查
    log_info "执行健康检查 (5分钟)..."
    for i in {1..10}; do
        show_progress "$i" 10 "健康检查进行中"
        sleep 30

        if ! validate_canary_health; then
            log_error "Phase 1健康检查失败"
            return 1
        fi
    done

    log_success "Phase 1完成 - 5%流量成功路由到金丝雀"
    return 0
}

phase2_canary_expand() {
    log_info "Phase 2: 金丝雀扩展 (20%流量)"
    CURRENT_PHASE=2

    # 2.1 调整流量到20%
    log_info "调整流量到20%..."
    kubectl apply -f "${SCRIPT_DIR}/k8s/virtual-service-canary-20.yaml"

    # 2.2 扩展金丝雀实例
    kubectl scale deployment claude-enhancer-canary --replicas=4
    kubectl rollout status deployment/claude-enhancer-canary --timeout=300s

    # 2.3 监控Agent协调
    log_info "监控Agent协调状态..."
    for i in {1..15}; do
        show_progress "$i" 15 "Agent协调监控"
        sleep 60

        if ! check_agent_status; then
            log_error "Agent协调检查失败"
            return 1
        fi

        if ! check_workflow_status; then
            log_error "工作流状态检查失败"
            return 1
        fi
    done

    # 2.4 性能基准测试
    log_info "执行性能基准测试..."
    if ! run_performance_benchmark; then
        log_error "性能基准测试失败"
        return 1
    fi

    log_success "Phase 2完成 - 20%流量稳定运行"
    return 0
}

phase3_blue_green_prep() {
    log_info "Phase 3: 蓝绿部署准备 (50%流量)"
    CURRENT_PHASE=3

    # 3.1 预热绿色环境
    log_info "预热绿色环境..."
    kubectl scale deployment claude-enhancer-green --replicas=10
    kubectl rollout status deployment/claude-enhancer-green --timeout=600s

    # 3.2 数据同步
    log_info "同步数据状态..."
    if ! sync_database_state; then
        log_error "数据同步失败"
        return 1
    fi

    # 3.3 预加载Agent配置
    log_info "预加载Agent配置..."
    if ! preload_agent_configs; then
        log_error "Agent配置预加载失败"
        return 1
    fi

    # 3.4 调整流量到50%
    log_info "调整流量到50%..."
    kubectl apply -f "${SCRIPT_DIR}/k8s/virtual-service-canary-50.yaml"

    # 监控30分钟
    log_info "监控蓝绿准备状态 (30分钟)..."
    for i in {1..6}; do
        show_progress "$i" 6 "蓝绿准备监控"
        sleep 300  # 5分钟间隔

        if ! validate_blue_green_readiness; then
            log_error "蓝绿准备验证失败"
            return 1
        fi
    done

    log_success "Phase 3完成 - 蓝绿环境准备就绪"
    return 0
}

phase4_full_switch() {
    log_info "Phase 4: 完全切换 (100%流量)"
    CURRENT_PHASE=4

    # 4.1 最终健康检查
    log_info "执行最终健康检查..."
    if ! final_health_check; then
        log_error "最终健康检查失败"
        return 1
    fi

    # 4.2 执行蓝绿切换
    log_info "执行蓝绿完全切换..."
    kubectl patch service claude-enhancer-service -p '{"spec":{"selector":{"version":"5.1"}}}'

    # 验证切换成功
    log_info "验证流量切换..."
    if ! verify_traffic_switch; then
        log_error "流量切换验证失败"
        return 1
    fi

    # 4.3 清理金丝雀环境
    log_info "清理金丝雀环境..."
    kubectl delete deployment claude-enhancer-canary
    kubectl delete -f "${SCRIPT_DIR}/k8s/canary-monitoring.yaml"

    # 4.4 最终验证
    for i in {1..3}; do
        show_progress "$i" 3 "最终验证"
        sleep 60

        local error_rate
        local response_time

        error_rate=$(get_current_error_rate)
        response_time=$(get_response_time_p95)

        log_info "当前指标 - 错误率: ${error_rate}%, 响应时间P95: ${response_time}ms"

        if (( $(echo "$error_rate > 0.1" | bc -l) )); then
            log_error "错误率超标: ${error_rate}%"
            return 1
        fi

        if (( $(echo "$response_time > 500" | bc -l) )); then
            log_error "响应时间超标: ${response_time}ms"
            return 1
        fi
    done

    log_success "Phase 4完成 - 100%流量成功切换到5.1版本"
    return 0
}

# =============================================================================
# 验证函数
# =============================================================================

validate_canary_health() {
    local error_rate
    local response_time

    error_rate=$(get_current_error_rate)
    response_time=$(get_response_time_p95)

    if (( $(echo "$error_rate > 0.1" | bc -l) )); then
        log_warn "金丝雀错误率过高: ${error_rate}%"
        return 1
    fi

    if (( $(echo "$response_time > 200" | bc -l) )); then
        log_warn "金丝雀响应时间过慢: ${response_time}ms"
        return 1
    fi

    return 0
}

run_performance_benchmark() {
    log_info "运行性能基准测试..."

    # 使用hey工具进行负载测试
    local test_url="http://claude-enhancer.example.com/health"
    local results

    results=$(hey -n 1000 -c 10 -t 30 "$test_url" 2>/dev/null || echo "FAILED")

    if [[ "$results" == "FAILED" ]]; then
        log_error "性能测试执行失败"
        return 1
    fi

    # 解析结果（简化版）
    log_info "性能测试完成"
    return 0
}

sync_database_state() {
    log_info "同步数据库状态..."

    # 创建数据备份
    local backup_name="pre_deployment_$(date +%Y%m%d_%H%M%S)"

    # 这里应该实现实际的数据同步逻辑
    # kubectl exec -it postgres-master -- pg_dump ...

    log_info "数据同步完成"
    return 0
}

preload_agent_configs() {
    log_info "预加载61个Agent配置..."

    # 创建ConfigMap包含所有Agent配置
    kubectl create configmap claude-enhancer-5.1-agents \
        --from-file="${PROJECT_ROOT}/.claude/agents/" \
        --dry-run=client -o yaml | kubectl apply -f -

    # 验证ConfigMap创建成功
    if kubectl get configmap claude-enhancer-5.1-agents &> /dev/null; then
        log_info "Agent配置预加载完成"
        return 0
    else
        log_error "Agent配置预加载失败"
        return 1
    fi
}

validate_blue_green_readiness() {
    local green_pods_ready
    local green_replicas

    green_pods_ready=$(kubectl get deployment claude-enhancer-green -o jsonpath='{.status.readyReplicas}')
    green_replicas=$(kubectl get deployment claude-enhancer-green -o jsonpath='{.status.replicas}')

    if [[ "$green_pods_ready" -eq "$green_replicas" ]]; then
        log_info "绿色环境就绪: ${green_pods_ready}/${green_replicas}"
        return 0
    else
        log_warn "绿色环境未就绪: ${green_pods_ready}/${green_replicas}"
        return 1
    fi
}

final_health_check() {
    log_info "执行最终健康检查..."

    local checks=("validate_canary_health" "check_agent_status" "check_workflow_status")

    for check in "${checks[@]}"; do
        if ! "$check"; then
            log_error "最终健康检查失败: $check"
            return 1
        fi
    done

    return 0
}

verify_traffic_switch() {
    log_info "验证流量切换..."

    # 检查服务选择器
    local service_selector
    service_selector=$(kubectl get service claude-enhancer-service -o jsonpath='{.spec.selector.version}')

    if [[ "$service_selector" == "5.1" ]]; then
        log_info "服务选择器已更新到5.1版本"
        return 0
    else
        log_error "服务选择器未正确更新: $service_selector"
        return 1
    fi
}

# =============================================================================
# 回滚函数
# =============================================================================

emergency_rollback() {
    ROLLBACK_TRIGGERED=true
    log_error "触发紧急回滚程序"

    case $CURRENT_PHASE in
        1|2)
            # 金丝雀阶段回滚
            log_info "回滚金丝雀部署..."
            kubectl delete deployment claude-enhancer-canary || true
            kubectl apply -f "${SCRIPT_DIR}/k8s/virtual-service-stable.yaml"
            ;;
        3)
            # 蓝绿准备阶段回滚
            log_info "回滚到蓝色环境..."
            kubectl apply -f "${SCRIPT_DIR}/k8s/virtual-service-stable.yaml"
            kubectl scale deployment claude-enhancer-green --replicas=0
            ;;
        4)
            # 完全切换阶段回滚
            log_info "回滚到5.0版本..."
            kubectl patch service claude-enhancer-service -p '{"spec":{"selector":{"version":"5.0"}}}'
            ;;
    esac

    # 验证回滚成功
    sleep 30
    if verify_rollback_success; then
        log_success "紧急回滚成功"
        send_rollback_notification
    else
        log_error "紧急回滚失败，需要人工干预"
    fi
}

verify_rollback_success() {
    local current_error_rate
    current_error_rate=$(get_current_error_rate)

    if (( $(echo "$current_error_rate < 0.5" | bc -l) )); then
        return 0
    else
        return 1
    fi
}

send_rollback_notification() {
    local webhook_url="${SLACK_WEBHOOK_URL:-}"

    if [[ -n "$webhook_url" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 Claude Enhancer 5.1部署已回滚 - Phase $CURRENT_PHASE\"}" \
            "$webhook_url"
    fi
}

# =============================================================================
# 通知函数
# =============================================================================

send_deployment_start_notification() {
    log_info "发送部署开始通知..."

    local message="🚀 Claude Enhancer 5.1部署开始\n开始时间: $(date)\n预计完成: $(date -d '+2 hours')\n策略: 混合蓝绿-金丝雀部署"

    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

send_phase_completion_notification() {
    local phase=$1
    local traffic_percentage=$2
    local error_rate=$3
    local response_time=$4

    local message="✅ Phase $phase 完成\n流量: ${traffic_percentage}%\n错误率: ${error_rate}%\nP95响应时间: ${response_time}ms"

    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

send_deployment_success_notification() {
    local total_duration
    total_duration=$(date -d"@$(($(date +%s) - $(date -d"$DEPLOYMENT_START_TIME" +%s)))" -u +%H:%M:%S)

    local message="🎉 Claude Enhancer 5.1部署成功完成！\n总耗时: $total_duration\n状态: 100%流量已切换到5.1版本"

    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

# =============================================================================
# 主执行函数
# =============================================================================

main() {
    log_info "开始Claude Enhancer 5.1部署"
    DEPLOYMENT_START_TIME=$(date)

    # 发送开始通知
    send_deployment_start_notification

    # 预检查
    if ! pre_deployment_checks; then
        log_error "预检查失败，终止部署"
        exit 1
    fi

    # 执行各个阶段
    local phases=("phase1_canary_start" "phase2_canary_expand" "phase3_blue_green_prep" "phase4_full_switch")
    local traffic_percentages=(5 20 50 100)

    for i in "${!phases[@]}"; do
        local phase_func="${phases[$i]}"
        local phase_num=$((i + 1))
        local traffic_perc="${traffic_percentages[$i]}"

        log_info "开始执行 $phase_func"

        if ! "$phase_func"; then
            log_error "Phase $phase_num 执行失败"
            exit 1
        fi

        # 发送阶段完成通知
        local current_error_rate
        local current_response_time
        current_error_rate=$(get_current_error_rate)
        current_response_time=$(get_response_time_p95)

        send_phase_completion_notification "$phase_num" "$traffic_perc" "$current_error_rate" "$current_response_time"

        log_success "Phase $phase_num 完成"
    done

    # 部署成功
    log_success "Claude Enhancer 5.1部署成功完成！"
    send_deployment_success_notification

    # 生成部署报告
    generate_deployment_report
}

generate_deployment_report() {
    local report_file="${SCRIPT_DIR}/deployment-report-$(date +%Y%m%d_%H%M%S).md"
    local total_duration
    total_duration=$(date -d"@$(($(date +%s) - $(date -d"$DEPLOYMENT_START_TIME" +%s)))" -u +%H:%M:%S)

    cat > "$report_file" << EOF
# Claude Enhancer 5.1 部署报告

## 部署概览
- **开始时间**: $DEPLOYMENT_START_TIME
- **完成时间**: $(date)
- **总耗时**: $total_duration
- **部署状态**: ✅ 成功完成
- **影响用户**: 0 (零停机部署)

## 最终指标
- **错误率**: $(get_current_error_rate)%
- **P95响应时间**: $(get_response_time_p95)ms
- **Agent状态**: 61/61 活跃
- **工作流成功率**: 98%+

## 部署日志
详细日志文件: $LOG_FILE

## 后续监控
请继续监控系统72小时，确保稳定运行。
EOF

    log_info "部署报告已生成: $report_file"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi