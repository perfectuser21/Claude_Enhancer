#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 应急演练脚本
# 模拟各种故障场景，测试应急响应能力
# =============================================================================

set -e

NAMESPACE="claude-enhancer"
DRILL_LOG="/tmp/emergency-drill-$(date +%Y%m%d_%H%M%S).log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$DRILL_LOG"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# 显示演练菜单
show_drill_menu() {
    echo ""
    echo "🧪 Claude Enhancer 5.1 应急演练系统"
    echo "==================================="
    echo "1. 模拟Pod崩溃故障"
    echo "2. 模拟高负载压力"
    echo "3. 模拟数据库连接问题"
    echo "4. 模拟网络分区"
    echo "5. 模拟配置文件损坏"
    echo "6. 全面故障恢复演练"
    echo "7. 查看演练历史"
    echo "8. 退出"
    echo ""
}

# 演练1: Pod崩溃故障
drill_pod_crash() {
    log_info "🚨 开始演练：Pod崩溃故障"
    
    # 随机选择一个Pod
    local pod=$(kubectl get pods -n "$NAMESPACE" -l app=claude-enhancer -o name | shuf -n 1)
    if [ -z "$pod" ]; then
        log_error "未找到可用的Pod进行演练"
        return 1
    fi
    
    log_info "目标Pod: $pod"
    
    # 记录演练开始时间
    local start_time=$(date +%s)
    
    # 删除Pod模拟崩溃
    log_warn "删除Pod模拟崩溃..."
    kubectl delete "$pod" -n "$NAMESPACE"
    
    # 监控恢复过程
    log_info "监控系统恢复过程..."
    local recovery_success=false
    
    for i in {1..60}; do
        local running_pods=$(kubectl get pods -n "$NAMESPACE" -l app=claude-enhancer --no-headers | grep "Running" | wc -l)
        if [ "$running_pods" -gt 0 ]; then
            # 检查健康状态
            if curl -f -s -m 10 http://claude-enhancer.example.com/health > /dev/null 2>&1; then
                local end_time=$(date +%s)
                local recovery_time=$((end_time - start_time))
                log_success "✅ Pod崩溃恢复成功！恢复时间: ${recovery_time}秒"
                recovery_success=true
                break
            fi
        fi
        
        log_info "等待恢复... (${i}/60)"
        sleep 10
    done
    
    if [ "$recovery_success" = false ]; then
        log_error "❌ Pod崩溃恢复失败或超时"
        return 1
    fi
    
    # 验证系统功能
    log_info "验证系统关键功能..."
    local function_checks=(
        "http://claude-enhancer.example.com/health"
        "http://claude-enhancer.example.com/api/v1/agents"
    )
    
    for endpoint in "${function_checks[@]}"; do
        if curl -f -s -m 15 "$endpoint" > /dev/null 2>&1; then
            log_success "✅ $endpoint 功能正常"
        else
            log_error "❌ $endpoint 功能异常"
        fi
    done
    
    log_info "🎯 Pod崩溃演练完成"
}

# 演练2: 高负载压力测试
drill_high_load() {
    log_info "🚨 开始演练：高负载压力测试"
    
    # 检查是否有压力测试工具
    if ! command -v ab &> /dev/null && ! command -v wrk &> /dev/null; then
        log_warn "未安装压力测试工具 (apache-bench 或 wrk)，跳过此演练"
        return 1
    fi
    
    local start_time=$(date +%s)
    
    # 启动压力测试
    log_info "启动压力测试 (持续60秒)..."
    
    if command -v ab &> /dev/null; then
        # 使用Apache Bench
        timeout 60 ab -n 1000 -c 10 http://claude-enhancer.example.com/health > /dev/null 2>&1 &
    elif command -v wrk &> /dev/null; then
        # 使用wrk
        timeout 60 wrk -t4 -c10 -d60s http://claude-enhancer.example.com/health > /dev/null 2>&1 &
    fi
    
    local load_pid=$!
    
    # 监控系统响应
    local max_response_time=0
    local error_count=0
    
    for i in {1..12}; do  # 监控60秒，每5秒检查一次
        local response_time=$(curl -w "%{time_total}" -s -o /dev/null http://claude-enhancer.example.com/health 2>/dev/null || echo "999")
        local response_code=$(curl -w "%{http_code}" -s -o /dev/null http://claude-enhancer.example.com/health 2>/dev/null || echo "000")
        
        log_info "响应时间: ${response_time}s, 状态码: $response_code"
        
        # 记录最大响应时间
        if (( $(echo "$response_time > $max_response_time" | bc -l 2>/dev/null || echo "0") )); then
            max_response_time=$response_time
        fi
        
        # 统计错误
        if [ "$response_code" != "200" ]; then
            ((error_count++))
        fi
        
        sleep 5
    done
    
    # 停止压力测试
    kill $load_pid 2>/dev/null || true
    wait $load_pid 2>/dev/null || true
    
    # 分析结果
    log_info "高负载演练结果分析:"
    log_info "最大响应时间: ${max_response_time}s"
    log_info "错误次数: $error_count/12"
    
    if (( $(echo "$max_response_time < 5" | bc -l 2>/dev/null || echo "0") )) && [ "$error_count" -lt 3 ]; then
        log_success "✅ 高负载压力测试通过"
    else
        log_warn "⚠️ 高负载压力测试存在性能问题"
    fi
    
    log_info "🎯 高负载演练完成"
}

# 演练3: 数据库连接问题
drill_database_issue() {
    log_info "🚨 开始演练：数据库连接问题"
    
    # 检查数据库Pod是否存在
    if ! kubectl get pod postgres-0 -n "$NAMESPACE" > /dev/null 2>&1; then
        log_warn "数据库Pod不存在，跳过此演练"
        return 1
    fi
    
    local start_time=$(date +%s)
    
    # 模拟数据库重启
    log_warn "重启数据库Pod模拟连接中断..."
    kubectl delete pod postgres-0 -n "$NAMESPACE"
    
    # 监控恢复过程
    log_info "监控数据库恢复过程..."
    local db_recovery_success=false
    
    for i in {1..120}; do  # 数据库恢复可能需要更长时间
        if kubectl get pod postgres-0 -n "$NAMESPACE" --no-headers 2>/dev/null | grep -q "Running"; then
            # 等待数据库完全启动
            sleep 10
            
            # 测试数据库连接
            if kubectl exec -it postgres-0 -n "$NAMESPACE" -- psql -U claude_enhancer -c "SELECT 1" > /dev/null 2>&1; then
                local end_time=$(date +%s)
                local recovery_time=$((end_time - start_time))
                log_success "✅ 数据库恢复成功！恢复时间: ${recovery_time}秒"
                db_recovery_success=true
                break
            fi
        fi
        
        log_info "等待数据库恢复... (${i}/120)"
        sleep 5
    done
    
    if [ "$db_recovery_success" = false ]; then
        log_error "❌ 数据库恢复失败或超时"
        return 1
    fi
    
    # 验证应用恢复
    log_info "验证应用数据库连接恢复..."
    for i in {1..30}; do
        if curl -f -s -m 15 http://claude-enhancer.example.com/api/v1/agents > /dev/null 2>&1; then
            log_success "✅ 应用数据库连接恢复正常"
            break
        fi
        
        log_info "等待应用恢复... (${i}/30)"
        sleep 10
    done
    
    log_info "🎯 数据库连接演练完成"
}

# 演练4: 配置文件损坏
drill_config_corruption() {
    log_info "🚨 开始演练：配置文件损坏"
    
    # 备份原始配置
    log_info "备份原始配置..."
    kubectl get configmap claude-enhancer-config -n "$NAMESPACE" -o yaml > "/tmp/backup-config-$(date +%s).yaml" 2>/dev/null || true
    
    # 模拟配置损坏
    log_warn "模拟配置文件损坏..."
    kubectl patch configmap claude-enhancer-config -n "$NAMESPACE" -p '{"data":{"config.yaml":"invalid: yaml: content"}}' 2>/dev/null || {
        log_warn "配置文件不存在或无法修改，跳过此演练"
        return 1
    }
    
    # 重启应用触发配置重载
    kubectl rollout restart deployment claude-enhancer -n "$NAMESPACE"
    
    # 监控应用状态
    log_info "监控应用状态..."
    sleep 30
    
    local config_issue_detected=false
    local pods_with_issues=$(kubectl get pods -n "$NAMESPACE" -l app=claude-enhancer --no-headers | grep -E "Error|CrashLoopBackOff" | wc -l)
    
    if [ "$pods_with_issues" -gt 0 ]; then
        log_warn "检测到配置问题导致的Pod异常"
        config_issue_detected=true
    fi
    
    # 恢复配置
    log_info "恢复正确的配置..."
    if [ -f "/tmp/backup-config-$(date +%s).yaml" ]; then
        kubectl apply -f "/tmp/backup-config-$(date +%s).yaml" 2>/dev/null || true
    else
        # 使用默认配置
        kubectl patch configmap claude-enhancer-config -n "$NAMESPACE" -p '{"data":{"config.yaml":"# Default config\nversion: 5.1\n"}}' 2>/dev/null || true
    fi
    
    # 重启应用恢复
    kubectl rollout restart deployment claude-enhancer -n "$NAMESPACE"
    kubectl rollout status deployment claude-enhancer -n "$NAMESPACE" --timeout=300s
    
    # 验证恢复
    if curl -f -s -m 15 http://claude-enhancer.example.com/health > /dev/null 2>&1; then
        log_success "✅ 配置恢复成功"
    else
        log_error "❌ 配置恢复失败"
    fi
    
    log_info "🎯 配置文件损坏演练完成"
}

# 演练6: 全面故障恢复演练
drill_comprehensive_recovery() {
    log_info "🚨 开始演练：全面故障恢复演练"
    
    local start_time=$(date +%s)
    local overall_success=true
    
    # 阶段1: Pod故障
    log_info "阶段1/3: Pod故障模拟"
    if ! drill_pod_crash; then
        overall_success=false
    fi
    sleep 30
    
    # 阶段2: 数据库问题
    log_info "阶段2/3: 数据库问题模拟"
    if ! drill_database_issue; then
        overall_success=false
    fi
    sleep 30
    
    # 阶段3: 高负载测试
    log_info "阶段3/3: 高负载测试"
    if ! drill_high_load; then
        overall_success=false
    fi
    
    local end_time=$(date +%s)
    local total_time=$((end_time - start_time))
    
    # 最终验证
    log_info "执行最终系统验证..."
    local final_health_check=true
    
    local critical_endpoints=(
        "http://claude-enhancer.example.com/health"
        "http://claude-enhancer.example.com/api/v1/agents"
        "http://claude-enhancer.example.com/api/v1/workflows"
    )
    
    for endpoint in "${critical_endpoints[@]}"; do
        if ! curl -f -s -m 15 "$endpoint" > /dev/null 2>&1; then
            log_error "❌ 关键端点异常: $endpoint"
            final_health_check=false
        fi
    done
    
    # 演练总结
    log_info "=== 全面故障恢复演练总结 ==="
    log_info "总演练时间: ${total_time}秒"
    log_info "各阶段状态: $([ "$overall_success" = true ] && echo "全部通过" || echo "存在问题")"
    log_info "最终健康检查: $([ "$final_health_check" = true ] && echo "通过" || echo "失败")"
    
    if [ "$overall_success" = true ] && [ "$final_health_check" = true ]; then
        log_success "🎉 全面故障恢复演练成功完成！"
    else
        log_error "⚠️ 全面故障恢复演练发现问题，需要进一步调查"
    fi
    
    log_info "🎯 全面故障恢复演练完成"
}

# 查看演练历史
show_drill_history() {
    log_info "📊 演练历史记录"
    
    local log_files=$(find /tmp -name "emergency-drill-*.log" -type f 2>/dev/null | sort -r | head -10)
    
    if [ -z "$log_files" ]; then
        log_info "暂无演练历史记录"
        return
    fi
    
    echo ""
    echo "最近10次演练记录:"
    echo "=================="
    
    for log_file in $log_files; do
        local drill_date=$(basename "$log_file" .log | sed 's/emergency-drill-//')
        local drill_time=$(echo "$drill_date" | sed 's/_/ /')
        local drill_status=$(grep -c "SUCCESS" "$log_file" 2>/dev/null || echo "0")
        local drill_errors=$(grep -c "ERROR" "$log_file" 2>/dev/null || echo "0")
        
        echo "日期: $drill_time | 成功: $drill_status | 错误: $drill_errors | 日志: $log_file"
    done
}

# 主菜单循环
main() {
    echo "🧪 Claude Enhancer 5.1 应急演练系统启动"
    echo "演练日志: $DRILL_LOG"
    echo ""
    
    while true; do
        show_drill_menu
        read -p "请选择演练类型 (1-8): " choice
        
        case $choice in
            1)
                drill_pod_crash
                ;;
            2)
                drill_high_load
                ;;
            3)
                drill_database_issue
                ;;
            4)
                log_warn "网络分区演练功能开发中..."
                ;;
            5)
                drill_config_corruption
                ;;
            6)
                drill_comprehensive_recovery
                ;;
            7)
                show_drill_history
                ;;
            8)
                log_info "退出应急演练系统"
                exit 0
                ;;
            *)
                log_error "无效选择，请输入1-8"
                ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

# 确认演练环境
echo "⚠️  警告：这是应急演练脚本，将在 $NAMESPACE 命名空间中执行故障模拟"
echo "请确保这是测试环境，而不是生产环境！"
echo ""
read -p "确认继续演练? (输入 'YES' 确认): " confirm

if [ "$confirm" != "YES" ]; then
    echo "演练已取消"
    exit 1
fi

# 运行主程序
main
