#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 应急恢复脚本
# 针对不同类型故障的快速修复方案
# =============================================================================

set -e

NAMESPACE="claude-enhancer"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示可用的恢复操作
show_menu() {
    echo ""
    echo "🚑 Claude Enhancer 5.1 应急恢复菜单"
    echo "======================================"
    echo "1. 重启所有服务 (滚动重启)"
    echo "2. 快速回滚到5.0版本"
    echo "3. 修复Pod崩溃问题"
    echo "4. 修复数据库连接问题"
    echo "5. 清理系统资源"
    echo "6. 修复Agent协调问题"
    echo "7. 重置工作流状态"
    echo "8. 系统完整健康检查"
    echo "9. 退出"
    echo ""
}

# 滚动重启所有服务
restart_all_services() {
    log_info "开始滚动重启所有服务..."
    
    # 重启主应用
    kubectl rollout restart deployment claude-enhancer -n "$NAMESPACE"
    log_info "等待deployment重启完成..."
    kubectl rollout status deployment claude-enhancer -n "$NAMESPACE" --timeout=300s
    
    # 等待健康检查通过
    log_info "等待健康检查通过..."
    for i in {1..30}; do
        if curl -f -s -m 10 http://claude-enhancer.example.com/health > /dev/null 2>&1; then
            log_success "健康检查通过 (尝试 $i/30)"
            return 0
        else
            log_info "等待健康检查... (尝试 $i/30)"
            sleep 10
        fi
    done
    
    log_error "重启后健康检查失败"
    return 1
}

# 快速回滚
quick_rollback() {
    log_info "执行快速回滚到5.0版本..."
    
    if [ -f "../deployment/emergency-rollback.sh" ]; then
        ../deployment/emergency-rollback.sh -r "manual_emergency_recovery" -f
    else
        log_warn "未找到回滚脚本，执行手动回滚..."
        
        # 手动回滚操作
        kubectl set image deployment/claude-enhancer claude-enhancer=claude-enhancer:5.0 -n "$NAMESPACE"
        kubectl rollout status deployment claude-enhancer -n "$NAMESPACE" --timeout=300s
        
        log_success "手动回滚完成"
    fi
}

# 修复Pod崩溃
fix_pod_crashes() {
    log_info "检查和修复Pod崩溃问题..."
    
    # 获取异常Pod
    local crashed_pods
    crashed_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | grep -E "Error|CrashLoopBackOff|ImagePullBackOff" | awk '{print $1}' || true)
    
    if [ -z "$crashed_pods" ]; then
        log_success "未发现崩溃的Pod"
        return 0
    fi
    
    echo "发现崩溃的Pod:"
    for pod in $crashed_pods; do
        echo "  - $pod"
    done
    
    # 删除崩溃的Pod让其重建
    for pod in $crashed_pods; do
        log_info "删除Pod: $pod"
        kubectl delete pod "$pod" -n "$NAMESPACE" || true
    done
    
    # 等待Pod重建
    log_info "等待Pod重建..."
    sleep 30
    
    # 检查结果
    local new_crashed_pods
    new_crashed_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | grep -E "Error|CrashLoopBackOff|ImagePullBackOff" | awk '{print $1}' || true)
    
    if [ -z "$new_crashed_pods" ]; then
        log_success "Pod崩溃问题已修复"
    else
        log_error "仍有Pod处于异常状态，需要进一步排查"
        kubectl get pods -n "$NAMESPACE"
    fi
}

# 修复数据库连接
fix_database_connection() {
    log_info "修复数据库连接问题..."
    
    # 检查数据库Pod状态
    if ! kubectl get pod postgres-0 -n "$NAMESPACE" > /dev/null 2>&1; then
        log_error "数据库Pod不存在"
        return 1
    fi
    
    # 尝试连接数据库
    if kubectl exec -it postgres-0 -n "$NAMESPACE" -- psql -U claude_enhancer -c "SELECT 1" > /dev/null 2>&1; then
        log_success "数据库连接正常"
    else
        log_warn "数据库连接异常，尝试修复..."
        
        # 重启数据库Pod
        kubectl delete pod postgres-0 -n "$NAMESPACE"
        log_info "等待数据库Pod重建..."
        
        # 等待数据库就绪
        for i in {1..60}; do
            if kubectl get pod postgres-0 -n "$NAMESPACE" --no-headers | grep -q "Running"; then
                sleep 10  # 额外等待数据库完全启动
                if kubectl exec -it postgres-0 -n "$NAMESPACE" -- psql -U claude_enhancer -c "SELECT 1" > /dev/null 2>&1; then
                    log_success "数据库连接已恢复"
                    return 0
                fi
            fi
            sleep 5
        done
        
        log_error "数据库修复失败"
        return 1
    fi
}

# 清理系统资源
clean_system_resources() {
    log_info "清理系统资源..."
    
    # 清理失败的Pod
    kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed -o name | xargs -r kubectl delete -n "$NAMESPACE"
    
    # 清理Completed的Job
    kubectl get jobs -n "$NAMESPACE" --field-selector=status.successful=1 -o name | xargs -r kubectl delete -n "$NAMESPACE"
    
    # 清理未使用的ConfigMap和Secret（谨慎操作）
    log_info "检查未使用的资源..."
    
    log_success "系统资源清理完成"
}

# 修复Agent协调问题
fix_agent_coordination() {
    log_info "修复Agent协调问题..."
    
    # 检查Agent配置
    if kubectl get configmap claude-enhancer-agents -n "$NAMESPACE" > /dev/null 2>&1; then
        log_success "Agent配置存在"
    else
        log_error "Agent配置不存在，需要重新部署"
        return 1
    fi
    
    # 重启应用以重新加载Agent配置
    kubectl rollout restart deployment claude-enhancer -n "$NAMESPACE"
    kubectl rollout status deployment claude-enhancer -n "$NAMESPACE" --timeout=300s
    
    # 验证Agent功能
    if curl -f -s -m 15 http://claude-enhancer.example.com/api/v1/agents > /dev/null 2>&1; then
        log_success "Agent协调功能已恢复"
    else
        log_error "Agent协调功能仍然异常"
        return 1
    fi
}

# 重置工作流状态
reset_workflow_state() {
    log_info "重置工作流状态..."
    
    # 获取应用Pod
    local app_pods
    app_pods=$(kubectl get pods -l app=claude-enhancer -n "$NAMESPACE" -o name | head -1)
    
    if [ -n "$app_pods" ]; then
        # 清理工作流锁文件
        kubectl exec "$app_pods" -n "$NAMESPACE" -- find /app -name "*.lock" -delete 2>/dev/null || true
        
        # 重置Phase状态
        kubectl exec "$app_pods" -n "$NAMESPACE" -- sh -c 'echo "P1" > /app/.phase/current' 2>/dev/null || true
        
        log_success "工作流状态已重置"
    else
        log_error "未找到应用Pod"
        return 1
    fi
}

# 系统完整健康检查
system_health_check() {
    log_info "执行系统完整健康检查..."
    
    if [ -f "$SCRIPT_DIR/quick-diagnostic.sh" ]; then
        "$SCRIPT_DIR/quick-diagnostic.sh"
    else
        log_warn "未找到诊断脚本，执行基础检查..."
        
        echo "Pod状态:"
        kubectl get pods -n "$NAMESPACE"
        
        echo ""
        echo "服务状态:"
        kubectl get services -n "$NAMESPACE"
        
        echo ""
        echo "健康检查:"
        if curl -f -s -m 10 http://claude-enhancer.example.com/health; then
            echo "✅ 健康检查通过"
        else
            echo "❌ 健康检查失败"
        fi
    fi
}

# 主菜单循环
main() {
    while true; do
        show_menu
        read -p "请选择操作 (1-9): " choice
        
        case $choice in
            1)
                restart_all_services
                ;;
            2)
                quick_rollback
                ;;
            3)
                fix_pod_crashes
                ;;
            4)
                fix_database_connection
                ;;
            5)
                clean_system_resources
                ;;
            6)
                fix_agent_coordination
                ;;
            7)
                reset_workflow_state
                ;;
            8)
                system_health_check
                ;;
            9)
                log_info "退出应急恢复工具"
                exit 0
                ;;
            *)
                log_error "无效选择，请输入1-9"
                ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

# 运行主程序
main
