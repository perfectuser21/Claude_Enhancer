#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 应急健康监控脚本
# 实时监控系统健康状态，自动检测并报告问题
# =============================================================================

set -euo pipefail

# 配置变量
NAMESPACE="claude-enhancer"
HEALTH_ENDPOINT="http://claude-enhancer.example.com/health"
API_ENDPOINT="http://claude-enhancer.example.com/api/v1"
CHECK_INTERVAL=10
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_ERROR_RATE=5

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志文件
LOG_DIR="/tmp/claude-enhancer-monitoring"
mkdir -p "$LOG_DIR"
HEALTH_LOG="$LOG_DIR/health-$(date +%Y%m%d).log"

# 日志函数
log_info() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[INFO]${NC} ${timestamp} - ${message}" | tee -a "$HEALTH_LOG"
}

log_warn() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[WARN]${NC} ${timestamp} - ${message}" | tee -a "$HEALTH_LOG"
}

log_error() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[ERROR]${NC} ${timestamp} - ${message}" | tee -a "$HEALTH_LOG"
}

log_success() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[SUCCESS]${NC} ${timestamp} - ${message}" | tee -a "$HEALTH_LOG"
}

# 健康检查函数
check_http_health() {
    local endpoint="$1"
    local timeout="${2:-10}"
    
    if curl -f -s -m "$timeout" "$endpoint" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Pod状态检查
check_pod_health() {
    local issues=()
    
    # 获取所有Pod状态
    local pods_info
    pods_info=$(kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null || echo "")
    
    if [ -z "$pods_info" ]; then
        issues+=("无法获取Pod信息")
        return 1
    fi
    
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            local name=$(echo "$line" | awk '{print $1}')
            local ready=$(echo "$line" | awk '{print $2}')
            local status=$(echo "$line" | awk '{print $3}')
            local restarts=$(echo "$line" | awk '{print $4}')
            
            case "$status" in
                "Running")
                    if [[ "$ready" != *"/"* ]] || [[ "${ready##*/}" != "${ready%%/*}" ]]; then
                        if [[ "$ready" != "1/1" ]] && [[ "$ready" != "2/2" ]]; then
                            issues+=("Pod $name 未完全就绪: $ready")
                        fi
                    fi
                    
                    if [ "$restarts" -gt 5 ]; then
                        issues+=("Pod $name 重启次数过多: $restarts")
                    fi
                    ;;
                "Pending"|"ContainerCreating")
                    issues+=("Pod $name 处于等待状态: $status")
                    ;;
                "Error"|"CrashLoopBackOff"|"ImagePullBackOff")
                    issues+=("Pod $name 状态异常: $status")
                    ;;
            esac
        fi
    done <<< "$pods_info"
    
    if [ ${#issues[@]} -gt 0 ]; then
        for issue in "${issues[@]}"; do
            log_error "Pod问题: $issue"
        done
        return 1
    else
        return 0
    fi
}

# 资源使用检查
check_resource_usage() {
    local issues=()
    
    # 检查节点资源
    local nodes_info
    nodes_info=$(kubectl top nodes --no-headers 2>/dev/null || echo "")
    
    if [ -n "$nodes_info" ]; then
        while IFS= read -r line; do
            if [ -n "$line" ]; then
                local node=$(echo "$line" | awk '{print $1}')
                local cpu_usage=$(echo "$line" | awk '{print $2}' | sed 's/%//')
                local memory_usage=$(echo "$line" | awk '{print $4}' | sed 's/%//')
                
                if [ "$cpu_usage" -gt "$ALERT_THRESHOLD_CPU" ]; then
                    issues+=("节点 $node CPU使用率过高: ${cpu_usage}%")
                fi
                
                if [ "$memory_usage" -gt "$ALERT_THRESHOLD_MEMORY" ]; then
                    issues+=("节点 $node 内存使用率过高: ${memory_usage}%")
                fi
            fi
        done <<< "$nodes_info"
    fi
    
    # 检查Pod资源
    local pods_resources
    pods_resources=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null || echo "")
    
    if [ -n "$pods_resources" ]; then
        while IFS= read -r line; do
            if [ -n "$line" ]; then
                local pod=$(echo "$line" | awk '{print $1}')
                local cpu=$(echo "$line" | awk '{print $2}' | sed 's/m//')
                local memory=$(echo "$line" | awk '{print $3}' | sed 's/Mi//')
                
                # 检查是否超过合理阈值（这里假设单个Pod不应超过2000m CPU和2000Mi内存）
                if [ "$cpu" -gt 2000 ]; then
                    issues+=("Pod $pod CPU使用异常高: ${cpu}m")
                fi
                
                if [ "$memory" -gt 2000 ]; then
                    issues+=("Pod $pod 内存使用异常高: ${memory}Mi")
                fi
            fi
        done <<< "$pods_resources"
    fi
    
    if [ ${#issues[@]} -gt 0 ]; then
        for issue in "${issues[@]}"; do
            log_warn "资源问题: $issue"
        done
        return 1
    else
        return 0
    fi
}

# 错误日志检查
check_error_logs() {
    local error_count
    error_count=$(kubectl logs -l app=claude-enhancer -n "$NAMESPACE" --since="${CHECK_INTERVAL}s" 2>/dev/null | grep -i -E "error|exception|fatal" | wc -l || echo "0")
    
    if [ "$error_count" -gt "$ALERT_THRESHOLD_ERROR_RATE" ]; then
        log_error "最近${CHECK_INTERVAL}秒内错误日志过多: $error_count 条"
        
        # 显示最新的错误日志
        log_info "最新错误日志:"
        kubectl logs -l app=claude-enhancer -n "$NAMESPACE" --since="${CHECK_INTERVAL}s" 2>/dev/null | grep -i -E "error|exception|fatal" | tail -5 | while IFS= read -r line; do
            log_error "  $line"
        done
        
        return 1
    else
        return 0
    fi
}

# API功能检查
check_api_functionality() {
    local issues=()
    
    # 检查健康端点
    if ! check_http_health "$HEALTH_ENDPOINT" 10; then
        issues+=("健康检查端点无响应")
    fi
    
    # 检查主要API端点
    local api_endpoints=(
        "$API_ENDPOINT/agents"
        "$API_ENDPOINT/workflows"
        "$API_ENDPOINT/auth/status"
    )
    
    for endpoint in "${api_endpoints[@]}"; do
        if ! check_http_health "$endpoint" 15; then
            issues+=("API端点无响应: $endpoint")
        fi
    done
    
    if [ ${#issues[@]} -gt 0 ]; then
        for issue in "${issues[@]}"; do
            log_error "API问题: $issue"
        done
        return 1
    else
        return 0
    fi
}

# 数据库连接检查
check_database_health() {
    local db_pod="postgres-0"
    local db_user="claude_enhancer"
    local db_name="claude_enhancer"
    
    # 检查数据库连接
    if kubectl exec -it "$db_pod" -n "$NAMESPACE" -- psql -U "$db_user" -d "$db_name" -c "SELECT 1" > /dev/null 2>&1; then
        # 检查连接数
        local connection_count
        connection_count=$(kubectl exec -it "$db_pod" -n "$NAMESPACE" -- psql -U "$db_user" -d "$db_name" -t -c "SELECT count(*) FROM pg_stat_activity" 2>/dev/null | tr -d ' \n' || echo "0")
        
        if [ "$connection_count" -gt 80 ]; then
            log_warn "数据库连接数过多: $connection_count"
            return 1
        fi
        
        return 0
    else
        log_error "数据库连接失败"
        return 1
    fi
}

# 发送告警通知
send_alert() {
    local alert_level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 这里可以集成Slack、邮件或其他通知系统
    local alert_file="$LOG_DIR/alerts-$(date +%Y%m%d).log"
    echo "[$timestamp] [$alert_level] $message" >> "$alert_file"
    
    # 如果配置了Slack Webhook
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local color="good"
        case "$alert_level" in
            "CRITICAL") color="danger" ;;
            "WARNING") color="warning" ;;
        esac
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 Claude Enhancer Alert [$alert_level]\\n$message\", \"color\":\"$color\"}" \
            "$SLACK_WEBHOOK_URL" &>/dev/null || true
    fi
}

# 综合健康检查
perform_health_check() {
    local overall_health=0
    local issues=()
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Claude Enhancer 5.1 健康检查 - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 1. Pod健康检查
    echo "🚀 检查Pod状态..."
    if check_pod_health; then
        log_success "Pod状态正常"
    else
        issues+=("Pod状态异常")
        overall_health=1
    fi
    
    # 2. 资源使用检查
    echo "💻 检查资源使用..."
    if check_resource_usage; then
        log_success "资源使用正常"
    else
        issues+=("资源使用异常")
        overall_health=1
    fi
    
    # 3. API功能检查
    echo "🌐 检查API功能..."
    if check_api_functionality; then
        log_success "API功能正常"
    else
        issues+=("API功能异常")
        overall_health=2  # API问题更严重
    fi
    
    # 4. 数据库检查
    echo "🛢️  检查数据库..."
    if check_database_health; then
        log_success "数据库连接正常"
    else
        issues+=("数据库异常")
        overall_health=2
    fi
    
    # 5. 错误日志检查
    echo "📋 检查错误日志..."
    if check_error_logs; then
        log_success "错误日志正常"
    else
        issues+=("错误日志异常")
        overall_health=$((overall_health > 1 ? overall_health : 1))
    fi
    
    # 总结
    echo ""
    if [ "$overall_health" -eq 0 ]; then
        log_success "🎉 系统整体健康状况良好"
    elif [ "$overall_health" -eq 1 ]; then
        log_warn "⚠️  系统存在警告级别问题"
        send_alert "WARNING" "系统健康检查发现问题: ${issues[*]}"
    else
        log_error "🚨 系统存在严重问题，需要立即处理"
        send_alert "CRITICAL" "系统健康检查发现严重问题: ${issues[*]}"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    return $overall_health
}

# 连续监控模式
continuous_monitoring() {
    echo "开始连续监控模式（每${CHECK_INTERVAL}秒检查一次）"
    echo "按 Ctrl+C 停止监控"
    
    while true; do
        if perform_health_check; then
            echo "✅ $(date '+%H:%M:%S') - 系统正常"
        else
            echo "❌ $(date '+%H:%M:%S') - 发现问题"
        fi
        
        sleep "$CHECK_INTERVAL"
        clear
    done
}

# 帮助信息
show_help() {
    cat << EOF
Claude Enhancer 5.1 应急健康监控工具

用法: $0 [选项]

选项:
    -c, --continuous    连续监控模式
    -i, --interval N    检查间隔（秒，默认10）
    -n, --namespace NS  K8s命名空间（默认claude-enhancer）
    -e, --endpoint URL  健康检查端点URL
    -h, --help         显示帮助信息

示例:
    $0                    # 执行一次性健康检查
    $0 -c                 # 启动连续监控
    $0 -c -i 30          # 每30秒检查一次
    $0 -n production      # 检查production命名空间

环境变量:
    SLACK_WEBHOOK_URL    # Slack告警Webhook URL

