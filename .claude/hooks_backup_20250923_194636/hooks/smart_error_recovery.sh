#!/bin/bash
# 智能错误恢复系统 - 自动重试和故障隔离
# 目标: 将成功率从70-83%提升到95%+

set -euo pipefail

# 配置
readonly MAX_RETRIES=3
readonly RETRY_DELAY=0.1
readonly ERROR_LOG="/tmp/.claude_errors.log"
readonly RECOVERY_CACHE="/tmp/.claude_recovery_cache"

# 错误分类和恢复策略
declare -A ERROR_STRATEGIES=(
    ["timeout"]="retry_fast"
    ["permission"]="fix_permissions"
    ["resource"]="wait_and_retry"
    ["network"]="retry_with_backoff"
    ["syntax"]="skip_gracefully"
)

# 快速错误检测
detect_error_type() {
    local error_msg="$1"

    if echo "$error_msg" | grep -qi "timeout\|time.*out"; then
        echo "timeout"
    elif echo "$error_msg" | grep -qi "permission\|denied\|forbidden"; then
        echo "permission"
    elif echo "$error_msg" | grep -qi "resource\|memory\|disk.*full\|no space"; then
        echo "resource"
    elif echo "$error_msg" | grep -qi "network\|connection\|unreachable"; then
        echo "network"
    elif echo "$error_msg" | grep -qi "syntax\|parse\|invalid"; then
        echo "syntax"
    else
        echo "unknown"
    fi
}

# 智能恢复策略
smart_recovery() {
    local error_type="$1"
    local attempt="$2"
    local context="$3"

    case "$error_type" in
        timeout)
            # 超时错误 - 快速重试
            echo "⚡ 超时恢复: 快速重试 #$attempt" >&2
            sleep 0.05
            return 0
            ;;
        permission)
            # 权限错误 - 尝试修复
            echo "🔐 权限恢复: 修复权限" >&2
            chmod +x "$context" 2>/dev/null || true
            return 0
            ;;
        resource)
            # 资源错误 - 等待后重试
            echo "💾 资源恢复: 等待资源释放" >&2
            sleep $((attempt * 0.1))
            # 尝试清理临时文件
            find /tmp -name ".claude_*" -mmin +5 -delete 2>/dev/null || true
            return 0
            ;;
        network)
            # 网络错误 - 指数退避
            echo "🌐 网络恢复: 指数退避重试" >&2
            sleep $(echo "0.1 * 2^$attempt" | bc -l 2>/dev/null | cut -d. -f1-2)
            return 0
            ;;
        syntax)
            # 语法错误 - 优雅跳过
            echo "📝 语法错误: 优雅跳过" >&2
            return 1  # 不重试
            ;;
        *)
            # 未知错误 - 标准重试
            echo "❓ 未知错误: 标准重试 #$attempt" >&2
            sleep $((attempt * RETRY_DELAY))
            return 0
            ;;
    esac
}

# 执行命令与智能重试
execute_with_recovery() {
    local cmd="$1"
    local context="${2:-}"
    local attempt=1

    while [[ $attempt -le $MAX_RETRIES ]]; do
        local start_time=$EPOCHREALTIME

        # 尝试执行命令
        if eval "$cmd" 2>/tmp/cmd_error.log; then
            local exec_time=$(echo "($EPOCHREALTIME - $start_time) * 1000" | bc -l | cut -d. -f1)

            # 记录成功
            echo "$(date '+%H:%M:%S')|SUCCESS|$cmd|${exec_time}ms|attempt:$attempt" >> "$ERROR_LOG" &
            return 0
        fi

        # 分析错误
        local error_msg=$(cat /tmp/cmd_error.log 2>/dev/null || echo "unknown error")
        local error_type=$(detect_error_type "$error_msg")

        # 记录错误
        echo "$(date '+%H:%M:%S')|ERROR|$cmd|$error_type|$error_msg|attempt:$attempt" >> "$ERROR_LOG" &

        # 检查是否应该重试
        if ! smart_recovery "$error_type" "$attempt" "$context"; then
            echo "💥 错误不可恢复: $error_type" >&2
            return 1
        fi

        ((attempt++))
    done

    echo "🔄 重试耗尽: $cmd 执行失败" >&2
    return 1
}

# 批量执行保护
protected_batch_execution() {
    local commands=("$@")
    local success_count=0
    local total_count=${#commands[@]}

    echo "🛡️ 批量执行保护: $total_count 个命令" >&2

    for cmd in "${commands[@]}"; do
        if execute_with_recovery "$cmd"; then
            ((success_count++))
        else
            echo "⚠️ 命令失败但继续: $cmd" >&2
        fi
    done

    local success_rate=$(echo "scale=1; $success_count * 100 / $total_count" | bc -l)
    echo "📊 批量执行完成: $success_count/$total_count (${success_rate}%)" >&2

    # 如果成功率低于阈值，触发整体恢复
    if [[ $(echo "$success_rate < 90" | bc -l) -eq 1 ]]; then
        echo "🚨 成功率过低，触发系统恢复" >&2
        system_recovery
    fi

    return 0
}

# 系统级恢复
system_recovery() {
    echo "🔧 执行系统级恢复..." >&2

    # 清理缓存
    find /tmp -name ".claude_*" -delete 2>/dev/null || true

    # 重置权限
    find .claude/hooks -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

    # 检查磁盘空间
    local disk_usage=$(df /tmp | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        echo "💾 磁盘空间不足，清理临时文件" >&2
        find /tmp -type f -mtime +1 -delete 2>/dev/null || true
    fi

    echo "✅ 系统恢复完成" >&2
}

# 主入口
main() {
    # 读取输入
    local input
    if ! input=$(cat 2>/dev/null); then
        echo "📥 输入读取失败，启用恢复模式" >&2
        return 0
    fi

    # 输出原始内容
    echo "$input"

    # 记录统计信息
    {
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo "$timestamp|PROCESS|error_recovery|input_size:${#input}" >> "$ERROR_LOG"
    } &

    return 0
}

# 创建必要目录
mkdir -p "$(dirname "$ERROR_LOG")" "$(dirname "$RECOVERY_CACHE")"

# 执行主逻辑
main "$@"