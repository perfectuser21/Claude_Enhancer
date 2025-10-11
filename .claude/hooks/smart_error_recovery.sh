#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - 智能错误恢复系统
# 高性能错误检测和自动恢复机制

set -euo pipefail

# 性能优化配置
export LC_ALL=C
readonly RECOVERY_TIMEOUT=0.1
readonly ERROR_CACHE_DIR="/tmp/claude_error_cache"
readonly ERROR_PATTERNS_FILE="${ERROR_CACHE_DIR}/error_patterns"
readonly RECOVERY_LOG="${ERROR_CACHE_DIR}/recovery.log"

# 创建缓存目录
mkdir -p "$ERROR_CACHE_DIR" 2>/dev/null || true

# 预定义错误模式和恢复策略
init_error_patterns() {
    if [[ ! -f "$ERROR_PATTERNS_FILE" ]]; then
        cat > "$ERROR_PATTERNS_FILE" << 'EOF'
# 错误模式 | 恢复策略 | 优先级
timeout|retry_with_extended_timeout|9
permission denied|fix_permissions|8
file not found|create_missing_file|7
connection refused|restart_service|6
out of memory|cleanup_memory|9
disk full|cleanup_disk|8
process not found|restart_process|5
network unreachable|check_network|4
invalid syntax|fix_syntax|6
import error|install_dependencies|7
EOF
    fi
}

# 快速错误检测
detect_error() {
    local input="$1"
    local error_type=""
    local error_details=""

    # 高效的错误模式匹配
    case "$input" in
        *"timeout"*|*"TimeoutError"*)
            error_type="timeout"
            error_details=$(echo "$input" | grep -o "timeout.*" | head -1)
            ;;
        *"Permission denied"*|*"PermissionError"*)
            error_type="permission"
            error_details=$(echo "$input" | grep -o "Permission.*" | head -1)
            ;;
        *"No such file"*|*"FileNotFoundError"*)
            error_type="file_not_found"
            error_details=$(echo "$input" | grep -o "No such file.*\|FileNotFoundError.*" | head -1)
            ;;
        *"Connection refused"*|*"ConnectionError"*)
            error_type="connection"
            error_details=$(echo "$input" | grep -o "Connection.*" | head -1)
            ;;
        *"Out of memory"*|*"MemoryError"*)
            error_type="memory"
            error_details=$(echo "$input" | grep -o ".*memory.*" | head -1)
            ;;
        *"No space left"*|*"DiskError"*)
            error_type="disk_full"
            error_details=$(echo "$input" | grep -o "No space.*\|disk.*" | head -1)
            ;;
        *"ModuleNotFoundError"*|*"ImportError"*)
            error_type="import_error"
            error_details=$(echo "$input" | grep -o "ModuleNotFoundError.*\|ImportError.*" | head -1)
            ;;
        *"SyntaxError"*)
            error_type="syntax_error"
            error_details=$(echo "$input" | grep -o "SyntaxError.*" | head -1)
            ;;
    esac

    if [[ -n "$error_type" ]]; then
        echo "$error_type|$error_details"
        return 0
    else
        return 1
    fi
}

# 生成恢复建议
generate_recovery_suggestion() {
    local error_type="$1"
    local error_details="$2"

    case "$error_type" in
        timeout)
            echo "建议: 增加超时时间，或将任务分解为更小的步骤"
            echo "命令: 重试当前操作，timeout设置为原来的2倍"
            ;;
        permission)
            echo "建议: 检查文件权限，可能需要sudo或修改文件所有者"
            echo "命令: chmod +x <文件> 或 sudo chown \$USER <文件>"
            ;;
        file_not_found)
            local missing_file=$(echo "$error_details" | grep -o "'[^']*'" | tr -d "'" | head -1)
            echo "建议: 创建缺失的文件或检查路径"
            echo "命令: touch '$missing_file' 或检查文件路径是否正确"
            ;;
        connection)
            echo "建议: 检查网络连接或服务状态"
            echo "命令: ping <目标地址> 或 systemctl status <服务名>"
            ;;
        memory)
            echo "建议: 释放内存或增加交换空间"
            echo "命令: 关闭不必要的进程，或考虑分批处理数据"
            ;;
        disk_full)
            echo "建议: 清理磁盘空间"
            echo "命令: df -h 查看使用情况，rm 删除不需要的文件"
            ;;
        import_error)
            local missing_module=$(echo "$error_details" | grep -o "No module named '[^']*'" | cut -d"'" -f2)
            echo "建议: 安装缺失的Python模块"
            echo "命令: pip install ${missing_module:-<module_name>}"
            ;;
        syntax_error)
            echo "建议: 检查代码语法错误"
            echo "命令: 检查最近修改的代码，注意括号、引号匹配"
            ;;
        *)
            echo "建议: 通用错误恢复 - 检查日志和重试"
            echo "命令: 查看详细错误信息，尝试重新执行"
            ;;
    esac
}

# 自动恢复尝试（安全模式）
attempt_auto_recovery() {
    local error_type="$1"
    local recovery_attempts=0
    local max_attempts=2

    # 仅对安全的错误类型进行自动恢复
    case "$error_type" in
        permission)
            if [[ $recovery_attempts -lt $max_attempts ]]; then
                echo "🔧 尝试自动恢复: 修复权限"
                # 安全的权限修复（仅对当前用户文件）
                find . -maxdepth 1 -user "$USER" -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
                recovery_attempts=$((recovery_attempts + 1))
                echo "✅ 已尝试修复脚本执行权限"
            fi
            ;;
        memory)
            if [[ $recovery_attempts -lt $max_attempts ]]; then
                echo "🔧 尝试自动恢复: 内存清理"
                # 安全的内存清理
                sync 2>/dev/null || true
                echo 1 > /proc/sys/vm/drop_caches 2>/dev/null || true
                recovery_attempts=$((recovery_attempts + 1))
                echo "✅ 已尝试清理系统缓存"
            fi
            ;;
        timeout)
            echo "🔧 建议: 下次操作时增加超时时间"
            ;;
        *)
            echo "ℹ️ 错误类型不支持自动恢复，请手动处理"
            ;;
    esac
}

# 记录错误和恢复历史
log_error_recovery() {
    local error_type="$1"
    local recovery_action="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # 异步记录（不阻塞主流程）
    {
        echo "$timestamp|$error_type|$recovery_action" >> "$RECOVERY_LOG"

        # 保持日志文件大小（最多保留500行）
        if [[ -f "$RECOVERY_LOG" ]]; then
            tail -500 "$RECOVERY_LOG" > "${RECOVERY_LOG}.tmp" 2>/dev/null || true
            mv "${RECOVERY_LOG}.tmp" "$RECOVERY_LOG" 2>/dev/null || true
        fi
    } &
}

# 主错误恢复逻辑
main() {
    local start_time=$(date +%s.%N)

    # 超时保护
    (sleep $RECOVERY_TIMEOUT; exit 0) &
    local timeout_pid=$!

    # 初始化错误模式
    init_error_patterns

    # 读取输入（快速模式）
    local input=""
    if ! input=$(timeout 0.05 cat 2>/dev/null); then
        # 如果没有输入，检查是否有历史错误
        if [[ -f "$RECOVERY_LOG" ]]; then
            local recent_errors=$(tail -5 "$RECOVERY_LOG" 2>/dev/null | wc -l)
            if [[ $recent_errors -gt 3 ]]; then
                echo "⚠️ 检测到频繁错误，建议检查系统状态" >&2
            fi
        fi
        kill $timeout_pid 2>/dev/null || true
        exit 0
    fi

    # 错误检测
    local error_info
    if error_info=$(detect_error "$input"); then
        local error_type=$(echo "$error_info" | cut -d'|' -f1)
        local error_details=$(echo "$error_info" | cut -d'|' -f2)

        # 输出错误分析
        {
            echo "🚨 错误检测: $error_type"
            echo "📋 详情: $error_details"
            echo ""
            generate_recovery_suggestion "$error_type" "$error_details"
            echo ""
        } >&2

        # 尝试自动恢复
        attempt_auto_recovery "$error_type"

        # 记录错误和恢复尝试
        log_error_recovery "$error_type" "auto_recovery_attempted"

    else
        # 如果没有检测到已知错误，但输入包含"error"关键词
        if echo "$input" | grep -qi "error\|failed\|exception"; then
            echo "ℹ️ 检测到可能的错误，但无法自动分类。请检查详细错误信息。" >&2
            log_error_recovery "unknown_error" "manual_review_needed"
        fi
    fi

    # 计算执行时间
    local execution_time=$(echo "scale=3; $(date +%s.%N) - $start_time" | bc 2>/dev/null || echo "0.001")

    # 性能日志（调试模式）
    if [[ "${DEBUG_HOOKS:-false}" == "true" ]]; then
        echo "DEBUG: smart_error_recovery executed in ${execution_time}s" >&2
    fi

    # 清理
    kill $timeout_pid 2>/dev/null || true

    # 成功输出（传递原始输入）
    echo "$input"
    exit 0
}

# 特殊功能：错误统计报告
if [[ "${1:-}" == "--stats" ]]; then
    if [[ -f "$RECOVERY_LOG" ]]; then
        echo "📊 错误恢复统计（最近24小时）:"
        local cutoff_time=$(date -d "24 hours ago" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -v-24H '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "")

        if [[ -n "$cutoff_time" ]]; then
            awk -F'|' -v cutoff="$cutoff_time" '$1 >= cutoff {print $2}' "$RECOVERY_LOG" 2>/dev/null | sort | uniq -c | sort -nr
        else
            tail -100 "$RECOVERY_LOG" 2>/dev/null | awk -F'|' '{print $2}' | sort | uniq -c | sort -nr
        fi
    else
        echo "暂无错误恢复记录"
    fi
    exit 0
fi

# 主执行入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi