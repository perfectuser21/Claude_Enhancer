#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 紧急回滚脚本
# 在检测到严重问题时快速回滚到5.0版本
# =============================================================================

set -euo pipefail

# 配置常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ROLLBACK_LOG="${SCRIPT_DIR}/rollback-$(date +%Y%m%d_%H%M%S).log"
readonly ROLLBACK_START_TIME=$(date +%s)

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# 全局变量
ROLLBACK_REASON=""
CURRENT_PHASE=""
ROLLBACK_SUCCESS=false

# =============================================================================
# 工具函数
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$ROLLBACK_LOG"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "${YELLOW}$*${NC}"; }
log_error() { log "ERROR" "${RED}$*${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$*${NC}"; }

# 显示倒计时
countdown() {
    local seconds=$1
    local message=${2:-""}

    for ((i=seconds; i>0; i--)); do
        echo -ne "\r${YELLOW}${message} ${i}秒后继续...${NC}"
        sleep 1
    done
    echo ""
}

# =============================================================================
# 检测当前部署状态
# =============================================================================

detect_current_phase() {
    log_info "检测当前部署状态..."

    # 检查金丝雀部署
    if kubectl get deployment claude-enhancer-canary &> /dev/null; then
        local canary_replicas
        canary_replicas=$(kubectl get deployment claude-enhancer-canary -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")

        if [[ "$canary_replicas" -gt 0 ]]; then
            CURRENT_PHASE="canary"
            log_info "检测到金丝雀部署阶段，副本数: $canary_replicas"
            return
        fi
    fi

    # 检查绿色部署
    if kubectl get deployment claude-enhancer-green &> /dev/null; then
        local green_replicas
        green_replicas=$(kubectl get deployment claude-enhancer-green -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")

        if [[ "$green_replicas" -gt 0 ]]; then
            CURRENT_PHASE="blue-green"
            log_info "检测到蓝绿部署阶段，绿色副本数: $green_replicas"
            return
        fi
    fi

    # 检查服务选择器
    local service_version
    service_version=$(kubectl get service claude-enhancer-service -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "unknown")

    if [[ "$service_version" == "5.1" ]]; then
        CURRENT_PHASE="full-switch"
        log_info "检测到完全切换阶段，当前版本: 5.1"
    else
        CURRENT_PHASE="stable"
        log_info "当前处于稳定状态，版本: $service_version"
    fi
}

# =============================================================================
# 系统健康检查
# =============================================================================

check_system_health() {
    log_info "检查系统健康状态..."

    local health_issues=()

    # 检查错误率
    local error_rate
    error_rate=$(get_current_error_rate)
    if (( $(echo "$error_rate > 0.5" | bc -l) )); then
        health_issues+=("错误率过高: ${error_rate}%")
    fi

    # 检查响应时间
    local response_time
    response_time=$(get_response_time_p95)
    if (( $(echo "$response_time > 1000" | bc -l) )); then
        health_issues+=("响应时间过慢: ${response_time}ms")
    fi

    # 检查Agent状态
    if ! check_agent_health; then
        health_issues+=("Agent协调异常")
    fi

    # 检查资源使用
    check_resource_health health_issues

    if [[ ${#health_issues[@]} -eq 0 ]]; then
        log_info "系统健康状态正常"
        return 0
    else
        log_warn "发现以下健康问题:"
        for issue in "${health_issues[@]}"; do
            log_warn "  - $issue"
        done
        return 1
    fi
}

get_current_error_rate() {
    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    local query="sum(rate(istio_requests_total{destination_app=\"claude-enhancer\",response_code=~\"5..\"}[5m])) / sum(rate(istio_requests_total{destination_app=\"claude-enhancer\"}[5m])) * 100"

    curl -s "${prometheus_url}/api/v1/query" \
        --data-urlencode "query=${query}" | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0"
}

get_response_time_p95() {
    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    local query="histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket{destination_app=\"claude-enhancer\"}[5m])) by (le))"

    curl -s "${prometheus_url}/api/v1/query" \
        --data-urlencode "query=${query}" | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0"
}

check_agent_health() {
    local active_agents
    active_agents=$(kubectl get pods -l app=claude-enhancer -o jsonpath='{.items[*].status.containerStatuses[0].ready}' 2>/dev/null | grep -o true | wc -l || echo "0")

    if [[ "$active_agents" -ge 58 ]]; then  # 允许3个Agent离线
        return 0
    else
        return 1
    fi
}

check_resource_health() {
    local -n issues_ref=$1

    # 检查内存使用率
    local memory_usage
    memory_usage=$(kubectl top pods -l app=claude-enhancer --no-headers 2>/dev/null | awk '{sum+=$3} END {print sum/NR}' | sed 's/Mi//' || echo "0")

    if [[ -n "$memory_usage" ]] && (( $(echo "$memory_usage > 3000" | bc -l) )); then  # 3GB阈值
        issues_ref+=("内存使用率过高: ${memory_usage}Mi")
    fi

    # 检查CPU使用率
    local cpu_usage
    cpu_usage=$(kubectl top pods -l app=claude-enhancer --no-headers 2>/dev/null | awk '{sum+=$2} END {print sum/NR}' | sed 's/m//' || echo "0")

    if [[ -n "$cpu_usage" ]] && (( $(echo "$cpu_usage > 1500" | bc -l) )); then  # 1.5 CPU阈值
        issues_ref+=("CPU使用率过高: ${cpu_usage}m")
    fi
}

# =============================================================================
# 回滚执行函数
# =============================================================================

execute_canary_rollback() {
    log_info "执行金丝雀阶段回滚..."

    # 1. 停止金丝雀流量
    log_info "切换流量到稳定版本..."
    kubectl apply -f "${SCRIPT_DIR}/k8s/virtual-service-stable.yaml" || {
        log_error "流量切换失败"
        return 1
    }

    # 2. 删除金丝雀部署
    log_info "删除金丝雀部署..."
    kubectl delete deployment claude-enhancer-canary --ignore-not-found=true || {
        log_warn "删除金丝雀部署失败，但继续执行"
    }

    # 3. 清理监控资源
    kubectl delete -f "${SCRIPT_DIR}/k8s/canary-monitoring.yaml" --ignore-not-found=true || {
        log_warn "清理监控资源失败，但继续执行"
    }

    # 4. 验证回滚成功
    sleep 10
    if verify_stable_traffic; then
        log_success "金丝雀回滚成功"
        return 0
    else
        log_error "金丝雀回滚验证失败"
        return 1
    fi
}

execute_blue_green_rollback() {
    log_info "执行蓝绿阶段回滚..."

    # 1. 立即切换流量到蓝色环境
    log_info "切换流量到蓝色环境..."
    kubectl apply -f "${SCRIPT_DIR}/k8s/virtual-service-stable.yaml" || {
        log_error "流量切换失败"
        return 1
    }

    # 2. 缩减绿色环境
    log_info "缩减绿色环境..."
    kubectl scale deployment claude-enhancer-green --replicas=0 || {
        log_warn "缩减绿色环境失败"
    }

    # 3. 删除金丝雀部署（如果存在）
    kubectl delete deployment claude-enhancer-canary --ignore-not-found=true

    # 4. 验证回滚成功
    sleep 15
    if verify_stable_traffic; then
        log_success "蓝绿回滚成功"
        return 0
    else
        log_error "蓝绿回滚验证失败"
        return 1
    fi
}

execute_full_switch_rollback() {
    log_info "执行完全切换阶段回滚..."

    # 1. 立即切换服务选择器到5.0版本
    log_info "切换服务到5.0版本..."
    kubectl patch service claude-enhancer-service -p '{"spec":{"selector":{"version":"5.0"}}}' || {
        log_error "服务切换失败"
        return 1
    }

    # 2. 确保蓝色环境有足够副本
    log_info "扩展蓝色环境..."
    kubectl scale deployment claude-enhancer-blue --replicas=10 || {
        log_warn "扩展蓝色环境失败"
    }

    # 3. 关闭绿色环境
    log_info "关闭绿色环境..."
    kubectl scale deployment claude-enhancer-green --replicas=0 || {
        log_warn "关闭绿色环境失败"
    }

    # 4. 删除5.1版本配置
    kubectl delete configmap claude-enhancer-5.1-agents --ignore-not-found=true
    kubectl delete configmap claude-enhancer-5.1-workflows --ignore-not-found=true

    # 5. 验证回滚成功
    sleep 30
    if verify_stable_traffic && verify_service_version "5.0"; then
        log_success "完全切换回滚成功"
        return 0
    else
        log_error "完全切换回滚验证失败"
        return 1
    fi
}

# =============================================================================
# 验证函数
# =============================================================================

verify_stable_traffic() {
    local attempts=0
    local max_attempts=10

    while [[ $attempts -lt $max_attempts ]]; do
        local health_response
        health_response=$(curl -s -o /dev/null -w "%{http_code}" http://claude-enhancer.example.com/health 2>/dev/null || echo "000")

        if [[ "$health_response" == "200" ]]; then
            log_info "健康检查通过"
            return 0
        fi

        attempts=$((attempts + 1))
        log_info "健康检查失败 (${attempts}/${max_attempts})，等待重试..."
        sleep 5
    done

    log_error "健康检查最终失败"
    return 1
}

verify_service_version() {
    local expected_version=$1
    local actual_version

    actual_version=$(kubectl get service claude-enhancer-service -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "unknown")

    if [[ "$actual_version" == "$expected_version" ]]; then
        log_info "服务版本验证通过: $expected_version"
        return 0
    else
        log_error "服务版本验证失败: 期望 $expected_version，实际 $actual_version"
        return 1
    fi
}

# =============================================================================
# 数据备份和恢复
# =============================================================================

backup_current_state() {
    log_info "备份当前系统状态..."

    local backup_dir="${SCRIPT_DIR}/backups/rollback-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # 备份Kubernetes配置
    kubectl get deployment claude-enhancer-canary -o yaml > "${backup_dir}/canary-deployment.yaml" 2>/dev/null || true
    kubectl get deployment claude-enhancer-green -o yaml > "${backup_dir}/green-deployment.yaml" 2>/dev/null || true
    kubectl get service claude-enhancer-service -o yaml > "${backup_dir}/service.yaml" 2>/dev/null || true
    kubectl get virtualservice claude-enhancer-canary-5 -o yaml > "${backup_dir}/virtualservice.yaml" 2>/dev/null || true

    # 备份监控数据
    curl -s "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query_range?query=claude_enhancer_deployment_status&start=$(date -d '1 hour ago' +%s)&end=$(date +%s)&step=60" > "${backup_dir}/deployment-metrics.json" 2>/dev/null || true

    log_info "状态备份完成: $backup_dir"
    echo "$backup_dir" > "${SCRIPT_DIR}/.last_backup"
}

# =============================================================================
# 通知系统
# =============================================================================

send_rollback_start_notification() {
    local message="🚨 Claude Enhancer 5.1 紧急回滚启动\n原因: $ROLLBACK_REASON\n阶段: $CURRENT_PHASE\n时间: $(date)"

    send_notification "$message" "critical"
}

send_rollback_completion_notification() {
    local duration=$(($(date +%s) - ROLLBACK_START_TIME))
    local status_emoji="✅"
    local status_text="成功"

    if [[ "$ROLLBACK_SUCCESS" == false ]]; then
        status_emoji="❌"
        status_text="失败"
    fi

    local message="${status_emoji} Claude Enhancer 5.1 紧急回滚${status_text}\n原因: $ROLLBACK_REASON\n耗时: ${duration}秒\n时间: $(date)"

    send_notification "$message" "high"
}

send_notification() {
    local message=$1
    local priority=${2:-"normal"}

    # Slack通知
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="good"
        case $priority in
            "critical") color="danger" ;;
            "high") color="warning" ;;
        esac

        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\", \"color\":\"$color\"}" \
            "$SLACK_WEBHOOK_URL" &>/dev/null || true
    fi

    # PagerDuty通知（如果是紧急情况）
    if [[ "$priority" == "critical" && -n "${PAGERDUTY_KEY:-}" ]]; then
        curl -X POST "https://events.pagerduty.com/v2/enqueue" \
            -H "Content-Type: application/json" \
            -d "{
                \"routing_key\": \"$PAGERDUTY_KEY\",
                \"event_action\": \"trigger\",
                \"payload\": {
                    \"summary\": \"Claude Enhancer 5.1 Emergency Rollback\",
                    \"severity\": \"critical\",
                    \"source\": \"deployment-system\",
                    \"custom_details\": {
                        \"reason\": \"$ROLLBACK_REASON\",
                        \"phase\": \"$CURRENT_PHASE\"
                    }
                }
            }" &>/dev/null || true
    fi
}

# =============================================================================
# 主执行函数
# =============================================================================

show_usage() {
    cat << EOF
使用方法: $0 [OPTIONS]

选项:
    -r, --reason REASON     回滚原因 (必需)
    -f, --force            强制回滚，跳过确认
    -y, --yes              自动确认所有提示
    -h, --help             显示帮助信息

示例:
    $0 -r "error_rate_high" -f
    $0 --reason "agent_coordination_failed" --yes

支持的回滚原因:
    error_rate_high         错误率过高
    response_time_slow      响应时间过慢
    agent_coordination_failed  Agent协调失败
    resource_exhaustion     资源耗尽
    user_reported_issues    用户报告问题
    manual_intervention     人工干预
EOF
}

main() {
    local force_rollback=false
    local auto_confirm=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -r|--reason)
                ROLLBACK_REASON="$2"
                shift 2
                ;;
            -f|--force)
                force_rollback=true
                shift
                ;;
            -y|--yes)
                auto_confirm=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # 验证必需参数
    if [[ -z "$ROLLBACK_REASON" ]]; then
        log_error "必须指定回滚原因 (-r)"
        show_usage
        exit 1
    fi

    log_info "开始Claude Enhancer 5.1紧急回滚程序"
    log_info "回滚原因: $ROLLBACK_REASON"

    # 检测当前状态
    detect_current_phase

    # 发送开始通知
    send_rollback_start_notification

    # 如果不是强制模式，进行健康检查
    if [[ "$force_rollback" == false ]]; then
        if check_system_health; then
            log_warn "系统当前状态正常，确认是否继续回滚？"
            if [[ "$auto_confirm" == false ]]; then
                read -p "继续回滚? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "用户取消回滚"
                    exit 0
                fi
            fi
        fi
    fi

    # 备份当前状态
    backup_current_state

    # 显示回滚倒计时
    if [[ "$auto_confirm" == false && "$force_rollback" == false ]]; then
        log_warn "即将开始回滚操作"
        countdown 10 "🚨 最后警告!"
    fi

    # 根据当前阶段执行相应的回滚
    case $CURRENT_PHASE in
        "canary")
            if execute_canary_rollback; then
                ROLLBACK_SUCCESS=true
            fi
            ;;
        "blue-green")
            if execute_blue_green_rollback; then
                ROLLBACK_SUCCESS=true
            fi
            ;;
        "full-switch")
            if execute_full_switch_rollback; then
                ROLLBACK_SUCCESS=true
            fi
            ;;
        "stable")
            log_info "系统已处于稳定状态，无需回滚"
            ROLLBACK_SUCCESS=true
            ;;
        *)
            log_error "未知部署阶段: $CURRENT_PHASE"
            ROLLBACK_SUCCESS=false
            ;;
    esac

    # 发送完成通知
    send_rollback_completion_notification

    # 生成回滚报告
    generate_rollback_report

    if [[ "$ROLLBACK_SUCCESS" == true ]]; then
        log_success "🎉 紧急回滚成功完成！"
        log_info "系统已回滚到Claude Enhancer 5.0版本"
        exit 0
    else
        log_error "❌ 紧急回滚失败，需要人工干预"
        log_error "请查看日志文件: $ROLLBACK_LOG"
        exit 1
    fi
}

generate_rollback_report() {
    local report_file="${SCRIPT_DIR}/rollback-report-$(date +%Y%m%d_%H%M%S).md"
    local total_duration=$(($(date +%s) - ROLLBACK_START_TIME))

    cat > "$report_file" << EOF
# Claude Enhancer 5.1 紧急回滚报告

## 回滚概览
- **开始时间**: $(date -d "@$ROLLBACK_START_TIME")
- **完成时间**: $(date)
- **总耗时**: ${total_duration}秒
- **回滚状态**: $(if [[ "$ROLLBACK_SUCCESS" == true ]]; then echo "✅ 成功"; else echo "❌ 失败"; fi)
- **回滚原因**: $ROLLBACK_REASON
- **回滚阶段**: $CURRENT_PHASE

## 执行操作
- 检测部署状态
- 备份当前配置
- 执行阶段性回滚
- 验证回滚成功

## 系统状态
- **当前错误率**: $(get_current_error_rate)%
- **P95响应时间**: $(get_response_time_p95)ms
- **Active Agents**: $(kubectl get pods -l app=claude-enhancer,version=5.0 -o jsonpath='{.items[*].status.containerStatuses[0].ready}' | grep -o true | wc -l)/61

## 后续行动
- [ ] 监控系统稳定性24小时
- [ ] 调查回滚原因并修复
- [ ] 更新部署策略避免重复问题
- [ ] 安排5.1版本重新部署时间

## 详细日志
日志文件: $ROLLBACK_LOG
备份文件: $(cat "${SCRIPT_DIR}/.last_backup" 2>/dev/null || echo "未找到")

---
**报告生成时间**: $(date)
**操作人员**: $(whoami)@$(hostname)
EOF

    log_info "回滚报告已生成: $report_file"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi