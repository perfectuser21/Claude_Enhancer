#!/bin/bash
# 优化版性能监控Hook - 超快速执行
# 专注核心性能指标，100ms内完成

set -euo pipefail

# 配置
readonly TIMEOUT=0.1  # 100ms超时
readonly CACHE_DIR="/tmp/.claude_perf_cache"
readonly PERF_LOG="${CACHE_DIR}/performance.log"

# 快速初始化
init_perf_monitor() {
    [[ -d "$CACHE_DIR" ]] || mkdir -p "$CACHE_DIR"
    exec 3>/dev/null 2>&3  # 静默错误输出
}

# 超快速性能检查
quick_perf_check() {
    local start_time=$EPOCHREALTIME

    # 读取输入（非阻塞）
    local input
    if ! input=$(timeout 0.01 cat 2>/dev/null); then
        echo "⚡ 快速模式: 跳过性能检查" >&2
        return 0
    fi

    # 提取工具名称（优化版）
    local tool_name
    tool_name=$(echo "$input" | grep -om1 '"tool"[[:space:]]*:[[:space:]]*"[^"]*' | cut -d'"' -f4 2>/dev/null || echo "unknown")

    # 计算执行时间
    local end_time=$EPOCHREALTIME
    local exec_time=$(echo "($end_time - $start_time) * 1000" | bc -l 2>/dev/null | cut -d. -f1)

    # 快速性能判断
    if [[ ${exec_time:-0} -gt 1000 ]]; then
        echo "⚠️ 慢速工具: $tool_name (${exec_time}ms)" >&2
    fi

    # 异步记录日志
    {
        echo "$(date '+%H:%M:%S')|$tool_name|${exec_time:-0}ms" >> "$PERF_LOG" &
    } 2>/dev/null

    return 0
}

# 主执行逻辑
main() {
    # 超时保护
    (
        sleep $TIMEOUT
        echo "⚡ 性能监控: 快速模式" >&2
        exit 0
    ) &
    local timeout_pid=$!

    # 初始化并执行检查
    init_perf_monitor
    quick_perf_check

    # 清理超时进程
    kill $timeout_pid 2>/dev/null || true
    wait $timeout_pid 2>/dev/null || true

    exit 0
}

# 执行主逻辑
main "$@"