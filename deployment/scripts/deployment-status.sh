#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 部署状态检查脚本
# 实时监控部署状态和关键指标
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

# 配置
REFRESH_INTERVAL=10
PROMETHEUS_URL="http://prometheus.monitoring.svc.cluster.local:9090"

# 显示标题
show_header() {
    clear
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                  Claude Enhancer 5.1 部署状态监控                           ║"
    echo "║                     Deployment Status Monitor                               ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${CYAN}更新时间: $(date)${NC}"
    echo -e "${CYAN}刷新间隔: ${REFRESH_INTERVAL}秒${NC}"
    echo
}

# 获取指标函数
get_error_rate() {
    curl -s "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=rate(http_requests_total{status=~\"5..\"}[5m]) * 100" 2>/dev/null | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0"
}

get_response_time_p95() {
    curl -s "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=histogram_quantile(0.95, http_request_duration_seconds) * 1000" 2>/dev/null | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0"
}

get_throughput() {
    curl -s "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=rate(http_requests_total[5m])" 2>/dev/null | \
        jq -r '.data.result[0].value[1] // "0"' 2>/dev/null || echo "0"
}

# 检查部署阶段
get_deployment_phase() {
    # 检查金丝雀部署
    if kubectl get deployment claude-enhancer-canary &>/dev/null; then
        local canary_replicas
        canary_replicas=$(kubectl get deployment claude-enhancer-canary -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
        local canary_ready
        canary_ready=$(kubectl get deployment claude-enhancer-canary -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

        if [[ "$canary_replicas" -gt 0 ]]; then
            # 检查流量分配确定阶段
            local traffic_weight
            traffic_weight=$(kubectl get virtualservice claude-enhancer-traffic -o jsonpath='{.spec.http[1].route[1].weight}' 2>/dev/null || echo "0")

            if [[ "$traffic_weight" -le 5 ]]; then
                echo "Phase 1: 金丝雀启动 (5%)"
            elif [[ "$traffic_weight" -le 20 ]]; then
                echo "Phase 2: 金丝雀扩展 (20%)"
            else
                echo "Phase 3: 蓝绿准备 (50%)"
            fi
            return
        fi
    fi

    # 检查服务版本
    local service_version
    service_version=$(kubectl get service claude-enhancer-service -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "unknown")

    if [[ "$service_version" == "5.1" ]]; then
        echo "Phase 4: 完全切换 (100%)"
    elif [[ "$service_version" == "5.0" ]]; then
        echo "稳定运行 (5.0版本)"
    else
        echo "未知状态"
    fi
}

# 获取Agent状态
get_agent_status() {
    local total_agents=61
    local active_agents_51=0
    local active_agents_50=0

    # 5.1版本Agent
    if kubectl get pods -l app=claude-enhancer,version=5.1 &>/dev/null; then
        active_agents_51=$(kubectl get pods -l app=claude-enhancer,version=5.1 -o jsonpath='{.items[*].status.containerStatuses[0].ready}' 2>/dev/null | grep -o true | wc -l || echo "0")
    fi

    # 5.0版本Agent
    if kubectl get pods -l app=claude-enhancer,version=5.0 &>/dev/null; then
        active_agents_50=$(kubectl get pods -l app=claude-enhancer,version=5.0 -o jsonpath='{.items[*].status.containerStatuses[0].ready}' 2>/dev/null | grep -o true | wc -l || echo "0")
    fi

    echo "$active_agents_51,$active_agents_50,$total_agents"
}

# 获取工作流状态
get_workflow_status() {
    # 这里可以从Prometheus获取实际的工作流指标
    curl -s "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=claude_enhancer_workflow_success_rate * 100" 2>/dev/null | \
        jq -r '.data.result[0].value[1] // "98"' 2>/dev/null || echo "98"
}

# 显示性能指标
show_performance_metrics() {
    echo -e "${BLUE}━━━ 性能指标 ━━━${NC}"

    local error_rate
    local response_time
    local throughput

    error_rate=$(get_error_rate)
    response_time=$(get_response_time_p95)
    throughput=$(get_throughput)

    # 错误率状态
    local error_status="✅"
    local error_color="$GREEN"
    if (( $(echo "$error_rate > 0.1" | bc -l) )); then
        error_status="⚠️"
        error_color="$YELLOW"
        if (( $(echo "$error_rate > 0.5" | bc -l) )); then
            error_status="❌"
            error_color="$RED"
        fi
    fi

    # 响应时间状态
    local response_status="✅"
    local response_color="$GREEN"
    if (( $(echo "$response_time > 500" | bc -l) )); then
        response_status="⚠️"
        response_color="$YELLOW"
        if (( $(echo "$response_time > 1000" | bc -l) )); then
            response_status="❌"
            response_color="$RED"
        fi
    fi

    # 吞吐量状态
    local throughput_status="✅"
    local throughput_color="$GREEN"
    if (( $(echo "$throughput < 1000" | bc -l) )); then
        throughput_status="⚠️"
        throughput_color="$YELLOW"
        if (( $(echo "$throughput < 500" | bc -l) )); then
            throughput_status="❌"
            throughput_color="$RED"
        fi
    fi

    printf "%-20s %s ${error_color}%6.2f%%${NC}   (目标: < 0.1%%)\n" "错误率:" "$error_status" "$error_rate"
    printf "%-20s %s ${response_color}%6.0fms${NC}  (目标: < 500ms)\n" "P95响应时间:" "$response_status" "$response_time"
    printf "%-20s %s ${throughput_color}%6.0f/s${NC}   (目标: >= 1000/s)\n" "请求吞吐量:" "$throughput_status" "$throughput"
    echo
}

# 显示部署状态
show_deployment_status() {
    echo -e "${BLUE}━━━ 部署状态 ━━━${NC}"

    local phase
    phase=$(get_deployment_phase)
    echo -e "当前阶段: ${CYAN}$phase${NC}"

    # 显示流量分布
    local traffic_info=""
    if kubectl get virtualservice claude-enhancer-traffic &>/dev/null; then
        local stable_weight
        local canary_weight
        stable_weight=$(kubectl get virtualservice claude-enhancer-traffic -o jsonpath='{.spec.http[1].route[0].weight}' 2>/dev/null || echo "100")
        canary_weight=$(kubectl get virtualservice claude-enhancer-traffic -o jsonpath='{.spec.http[1].route[1].weight}' 2>/dev/null || echo "0")
        traffic_info="稳定版本: ${stable_weight}%, 新版本: ${canary_weight}%"
    else
        local service_version
        service_version=$(kubectl get service claude-enhancer-service -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "unknown")
        traffic_info="当前版本: $service_version (100%)"
    fi

    echo -e "流量分布: ${CYAN}$traffic_info${NC}"
    echo
}

# 显示Agent状态
show_agent_status() {
    echo -e "${BLUE}━━━ Agent系统状态 ━━━${NC}"

    local agent_info
    agent_info=$(get_agent_status)
    IFS=',' read -r agents_51 agents_50 total_agents <<< "$agent_info"

    # Agent状态显示
    local agent_51_color="$GREEN"
    local agent_50_color="$GREEN"

    if [[ "$agents_51" -lt 60 ]]; then
        agent_51_color="$YELLOW"
        if [[ "$agents_51" -lt 58 ]]; then
            agent_51_color="$RED"
        fi
    fi

    if [[ "$agents_50" -lt 60 ]]; then
        agent_50_color="$YELLOW"
        if [[ "$agents_50" -lt 58 ]]; then
            agent_50_color="$RED"
        fi
    fi

    if [[ "$agents_51" -gt 0 ]]; then
        printf "%-20s ${agent_51_color}%2d${NC}/${total_agents} 活跃\n" "5.1版本Agent:" "$agents_51"
    fi

    if [[ "$agents_50" -gt 0 ]]; then
        printf "%-20s ${agent_50_color}%2d${NC}/${total_agents} 活跃\n" "5.0版本Agent:" "$agents_50"
    fi

    # 工作流状态
    local workflow_rate
    workflow_rate=$(get_workflow_status)
    local workflow_color="$GREEN"
    local workflow_status="✅"

    if (( $(echo "$workflow_rate < 98" | bc -l) )); then
        workflow_color="$YELLOW"
        workflow_status="⚠️"
        if (( $(echo "$workflow_rate < 95" | bc -l) )); then
            workflow_color="$RED"
            workflow_status="❌"
        fi
    fi

    printf "%-20s %s ${workflow_color}%5.1f%%${NC}  (目标: >= 98%%)\n" "工作流成功率:" "$workflow_status" "$workflow_rate"
    echo
}

# 显示Kubernetes状态
show_kubernetes_status() {
    echo -e "${BLUE}━━━ Kubernetes状态 ━━━${NC}"

    # 检查部署状态
    echo "部署状态:"

    if kubectl get deployment claude-enhancer-canary &>/dev/null; then
        local canary_replicas
        local canary_ready
        canary_replicas=$(kubectl get deployment claude-enhancer-canary -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
        canary_ready=$(kubectl get deployment claude-enhancer-canary -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

        local canary_color="$GREEN"
        if [[ "$canary_ready" -ne "$canary_replicas" ]]; then
            canary_color="$YELLOW"
            if [[ "$canary_ready" -eq 0 ]]; then
                canary_color="$RED"
            fi
        fi

        printf "  %-20s ${canary_color}%d/%d${NC} 就绪\n" "金丝雀实例:" "$canary_ready" "$canary_replicas"
    fi

    if kubectl get deployment claude-enhancer-green &>/dev/null; then
        local green_replicas
        local green_ready
        green_replicas=$(kubectl get deployment claude-enhancer-green -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
        green_ready=$(kubectl get deployment claude-enhancer-green -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

        local green_color="$GREEN"
        if [[ "$green_ready" -ne "$green_replicas" ]]; then
            green_color="$YELLOW"
            if [[ "$green_ready" -eq 0 ]]; then
                green_color="$RED"
            fi
        fi

        printf "  %-20s ${green_color}%d/%d${NC} 就绪\n" "绿色环境实例:" "$green_ready" "$green_replicas"
    fi

    if kubectl get deployment claude-enhancer-blue &>/dev/null; then
        local blue_replicas
        local blue_ready
        blue_replicas=$(kubectl get deployment claude-enhancer-blue -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
        blue_ready=$(kubectl get deployment claude-enhancer-blue -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

        local blue_color="$GREEN"
        if [[ "$blue_ready" -ne "$blue_replicas" ]]; then
            blue_color="$YELLOW"
            if [[ "$blue_ready" -eq 0 ]]; then
                blue_color="$RED"
            fi
        fi

        printf "  %-20s ${blue_color}%d/%d${NC} 就绪\n" "蓝色环境实例:" "$blue_ready" "$blue_replicas"
    fi

    # 检查服务状态
    echo
    echo "服务状态:"
    if kubectl get service claude-enhancer-service &>/dev/null; then
        local service_version
        service_version=$(kubectl get service claude-enhancer-service -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "unknown")
        printf "  %-20s ${CYAN}%s${NC}\n" "服务版本:" "$service_version"

        local service_ip
        service_ip=$(kubectl get service claude-enhancer-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "unknown")
        printf "  %-20s ${CYAN}%s${NC}\n" "服务IP:" "$service_ip"
    fi
    echo
}

# 显示系统健康检查
show_health_status() {
    echo -e "${BLUE}━━━ 系统健康检查 ━━━${NC}"

    # API健康检查
    local health_status="❌"
    local health_color="$RED"
    local health_message="无响应"

    if curl -s -f http://claude-enhancer.example.com/health &>/dev/null; then
        health_status="✅"
        health_color="$GREEN"
        health_message="正常"
    elif curl -s -f http://localhost:8080/health &>/dev/null; then
        health_status="⚠️"
        health_color="$YELLOW"
        health_message="本地可访问"
    fi

    printf "%-20s %s ${health_color}%s${NC}\n" "API健康检查:" "$health_status" "$health_message"

    # 数据库连接检查
    local db_status="❌"
    local db_color="$RED"
    local db_message="无法连接"

    if kubectl exec -it postgres-main -- pg_isready &>/dev/null; then
        db_status="✅"
        db_color="$GREEN"
        db_message="正常连接"
    fi

    printf "%-20s %s ${db_color}%s${NC}\n" "数据库连接:" "$db_status" "$db_message"

    # Redis连接检查
    local redis_status="❌"
    local redis_color="$RED"
    local redis_message="无法连接"

    if kubectl exec -it redis-main -- redis-cli ping | grep -q PONG 2>/dev/null; then
        redis_status="✅"
        redis_color="$GREEN"
        redis_message="正常连接"
    fi

    printf "%-20s %s ${redis_color}%s${NC}\n" "Redis连接:" "$redis_status" "$redis_message"
    echo
}

# 显示告警状态
show_alerts_status() {
    echo -e "${BLUE}━━━ 告警状态 ━━━${NC}"

    # 检查Prometheus告警
    local active_alerts
    active_alerts=$(curl -s "${PROMETHEUS_URL}/api/v1/alerts" 2>/dev/null | jq -r '.data.alerts | length' 2>/dev/null || echo "unknown")

    if [[ "$active_alerts" == "0" ]]; then
        echo -e "活跃告警: ${GREEN}✅ 无活跃告警${NC}"
    elif [[ "$active_alerts" == "unknown" ]]; then
        echo -e "活跃告警: ${YELLOW}⚠️ 无法获取告警状态${NC}"
    else
        echo -e "活跃告警: ${RED}❌ $active_alerts 个活跃告警${NC}"
    fi

    # 检查最近的告警历史
    echo "最近告警历史: (最近1小时)"
    curl -s "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=ALERTS{alertstate=\"firing\"}" 2>/dev/null | \
        jq -r '.data.result[] | "  • " + .metric.alertname + ": " + .metric.severity' 2>/dev/null || echo "  无法获取告警历史"

    echo
}

# 显示操作提示
show_operation_hints() {
    echo -e "${PURPLE}━━━ 操作提示 ━━━${NC}"
    echo "快捷键:"
    echo "  q/Q - 退出监控"
    echo "  r/R - 手动刷新"
    echo "  h/H - 显示帮助"
    echo "  d/D - 显示详细诊断"
    echo
    echo "紧急操作:"
    echo "  如需回滚: ./emergency-rollback.sh -r \"manual_intervention\""
    echo "  如需暂停: kubectl scale deployment claude-enhancer-canary --replicas=0"
    echo "  紧急联系: deployment-lead@example.com"
    echo
}

# 详细诊断
show_detailed_diagnostics() {
    clear
    echo -e "${PURPLE}━━━ 详细系统诊断 ━━━${NC}\n"

    echo -e "${CYAN}=== Pod详细状态 ===${NC}"
    kubectl get pods -l app=claude-enhancer -o wide

    echo -e "\n${CYAN}=== 最近事件 ===${NC}"
    kubectl get events --sort-by=.metadata.creationTimestamp | tail -10

    echo -e "\n${CYAN}=== VirtualService配置 ===${NC}"
    kubectl get virtualservice claude-enhancer-traffic -o yaml | grep -A 10 -B 5 weight || echo "无VirtualService配置"

    echo -e "\n${CYAN}=== 服务端点 ===${NC}"
    kubectl get endpoints claude-enhancer-service

    echo -e "\n${CYAN}=== 资源使用情况 ===${NC}"
    kubectl top pods -l app=claude-enhancer 2>/dev/null || echo "无法获取资源使用情况"

    echo -e "\n${CYAN}按任意键返回主界面...${NC}"
    read -n 1 -s
}

# 主监控循环
monitor_loop() {
    while true; do
        show_header
        show_deployment_status
        show_performance_metrics
        show_agent_status
        show_kubernetes_status
        show_health_status
        show_alerts_status
        show_operation_hints

        echo -e "${YELLOW}下次刷新: ${REFRESH_INTERVAL}秒 (按 q 退出)${NC}"

        # 非阻塞读取用户输入
        if read -t $REFRESH_INTERVAL -n 1 -s input 2>/dev/null; then
            case "$input" in
                q|Q)
                    echo -e "\n${GREEN}退出监控...${NC}"
                    exit 0
                    ;;
                r|R)
                    continue
                    ;;
                h|H)
                    show_usage
                    read -p "按Enter键继续..." -r
                    ;;
                d|D)
                    show_detailed_diagnostics
                    ;;
            esac
        fi
    done
}

# 显示使用说明
show_usage() {
    clear
    cat << EOF
${PURPLE}━━━ Claude Enhancer 5.1 部署状态监控帮助 ━━━${NC}

${BLUE}功能说明:${NC}
  实时监控Claude Enhancer 5.1部署过程中的关键指标和状态

${BLUE}监控指标:${NC}
  • 性能指标: 错误率、响应时间、吞吐量
  • 部署状态: 当前阶段、流量分布
  • Agent状态: 61个Agent的运行状态
  • 系统健康: API、数据库、Redis连接状态
  • K8s状态: Pod、Service、Deployment状态

${BLUE}状态指示:${NC}
  ✅ 正常    ⚠️ 警告    ❌ 异常

${BLUE}快捷键:${NC}
  q/Q - 退出监控
  r/R - 立即刷新
  h/H - 显示此帮助
  d/D - 显示详细诊断信息

${BLUE}告警阈值:${NC}
  错误率: > 0.1% (警告), > 0.5% (严重)
  响应时间: > 500ms (警告), > 1000ms (严重)
  Agent: < 60个 (警告), < 58个 (严重)
  工作流: < 98% (警告), < 95% (严重)

${BLUE}紧急操作:${NC}
  如需回滚: ./emergency-rollback.sh -r "manual_intervention"
  如需支持: deployment-lead@example.com

EOF
}

# 单次状态检查
check_once() {
    show_header
    show_deployment_status
    show_performance_metrics
    show_agent_status
    show_kubernetes_status
    show_health_status
    show_alerts_status
    echo -e "${GREEN}状态检查完成${NC}"
}

# 主函数
main() {
    local mode="monitor"

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -o|--once)
                mode="once"
                shift
                ;;
            -i|--interval)
                REFRESH_INTERVAL="$2"
                shift 2
                ;;
            *)
                echo "未知参数: $1"
                echo "使用 $0 --help 查看帮助"
                exit 1
                ;;
        esac
    done

    # 检查必要工具
    local required_tools=("kubectl" "curl" "jq" "bc")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            echo -e "${RED}错误: 缺少必要工具 $tool${NC}"
            exit 1
        fi
    done

    # 执行相应模式
    case "$mode" in
        "monitor")
            monitor_loop
            ;;
        "once")
            check_once
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi