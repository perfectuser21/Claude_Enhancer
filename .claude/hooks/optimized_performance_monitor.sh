#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - 优化性能监控器
# 超轻量级：<100ms执行，最小资源占用

set -euo pipefail

# 性能优化配置
export LC_ALL=C
readonly MONITOR_TIMEOUT=0.05
readonly STATS_FILE="/tmp/claude_perf_stats"
readonly ALERT_THRESHOLD_CPU=80
readonly ALERT_THRESHOLD_MEM=85

# 快速系统信息获取（无外部命令依赖）
get_quick_stats() {
    local stats=""

    # CPU使用率（从/proc/stat快速计算）
    if [[ -r /proc/stat ]]; then
        local cpu_line=$(head -1 /proc/stat 2>/dev/null || echo "cpu 0 0 0 0")
        local cpu_usage=$(echo "$cpu_line" | awk '{
            idle=$5; total=0;
            for(i=2;i<=NF;i++) total+=$i;
            if(total>0) print int((total-idle)*100/total); else print 0
        }')
        stats+="cpu:${cpu_usage}%"
    fi

    # 内存使用率（从/proc/meminfo）
    if [[ -r /proc/meminfo ]]; then
        local mem_info=$(head -3 /proc/meminfo 2>/dev/null)
        local mem_usage=$(echo "$mem_info" | awk '
            /MemTotal/ {total=$2}
            /MemAvailable/ {avail=$2}
            END {if(total>0) print int((total-avail)*100/total); else print 0}
        ')
        stats+=",mem:${mem_usage}%"
    fi

    # 负载平均值（简化版）
    if [[ -r /proc/loadavg ]]; then
        local load1=$(cut -d' ' -f1 /proc/loadavg 2>/dev/null || echo "0.0")
        stats+=",load:${load1}"
    fi

    echo "$stats"
}

# 检查Claude进程状态（快速版）
check_claude_process() {
    local claude_procs=0

    # 快速检查Claude相关进程
    if command -v pgrep >/dev/null 2>&1; then
        claude_procs=$(pgrep -cf "claude" 2>/dev/null || echo 0)
    fi

    echo "claude_procs:${claude_procs}"
}

# 磁盘使用检查（仅检查当前工作目录）
check_disk_usage() {
    local disk_usage="0"

    if command -v df >/dev/null 2>&1; then
        disk_usage=$(df . 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%' || echo "0")
    fi

    echo "disk:${disk_usage}%"
}

# Hook执行统计
update_hook_stats() {
    local hook_name="${1:-unknown}"
    local execution_time="${2:-0}"
    local success="${3:-true}"

    # 简单的统计更新（异步）
    {
        echo "$(date +%s),${hook_name},${execution_time},${success}" >> "${STATS_FILE}_hooks" 2>/dev/null || true

        # 保持文件大小合理（只保留最后100行）
        if [[ -f "${STATS_FILE}_hooks" ]]; then
            tail -100 "${STATS_FILE}_hooks" > "${STATS_FILE}_hooks.tmp" 2>/dev/null || true
            mv "${STATS_FILE}_hooks.tmp" "${STATS_FILE}_hooks" 2>/dev/null || true
        fi
    } &
}

# 主监控逻辑
main() {
    local start_time=$(date +%s.%N)

    # 超时保护
    (sleep $MONITOR_TIMEOUT; exit 0) &
    local timeout_pid=$!

    # 获取快速系统统计
    local system_stats=$(get_quick_stats)
    local claude_stats=$(check_claude_process)
    local disk_stats=$(check_disk_usage)

    # 解析CPU和内存使用率进行告警检查
    local cpu_usage=$(echo "$system_stats" | grep -o 'cpu:[0-9]*' | cut -d':' -f2 | tr -d '%' || echo "0")
    local mem_usage=$(echo "$system_stats" | grep -o 'mem:[0-9]*' | cut -d':' -f2 | tr -d '%' || echo "0")

    # 性能告警（仅在超出阈值时输出）
    local alerts=""
    if [[ ${cpu_usage:-0} -gt $ALERT_THRESHOLD_CPU ]]; then
        alerts+="⚠️ High CPU: ${cpu_usage}% "
    fi

    if [[ ${mem_usage:-0} -gt $ALERT_THRESHOLD_MEM ]]; then
        alerts+="⚠️ High Memory: ${mem_usage}% "
    fi

    # 计算执行时间
    local execution_time=$(echo "scale=3; $(date +%s.%N) - $start_time" | bc 2>/dev/null || echo "0.001")

    # 输出结果（仅在有告警或调试模式时输出到stderr）
    if [[ -n "$alerts" ]] || [[ "${DEBUG_HOOKS:-false}" == "true" ]]; then
        {
            echo "📊 Performance: $system_stats,$claude_stats,$disk_stats (${execution_time}s)"
            [[ -n "$alerts" ]] && echo "$alerts"
        } >&2
    fi

    # 更新Hook统计（异步）
    update_hook_stats "performance_monitor" "$execution_time" "true"

    # 清理
    kill $timeout_pid 2>/dev/null || true

    # 成功输出（JSON格式，供其他系统使用）
    if [[ "${OUTPUT_JSON:-false}" == "true" ]]; then
        echo "{\"system_stats\":\"$system_stats\",\"claude_stats\":\"$claude_stats\",\"disk_stats\":\"$disk_stats\",\"execution_time\":$execution_time,\"alerts\":\"$alerts\"}"
    fi

    exit 0
}

# 特殊模式：如果作为函数调用
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi