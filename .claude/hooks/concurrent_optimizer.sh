#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer - 并发优化器
# 智能并发控制和资源优化

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [concurrent_optimizer.sh] triggered by ${USER:-claude}" >> "$LOG_FILE"

set -euo pipefail

# 性能优化配置
export LC_ALL=C
readonly OPTIMIZER_TIMEOUT=0.08
readonly CONCURRENCY_CACHE="/tmp/claude_concurrency_cache"
readonly MAX_CONCURRENT_HOOKS=4
readonly CPU_THRESHOLD=75
readonly MEMORY_THRESHOLD=80

# 创建缓存目录
mkdir -p "$CONCURRENCY_CACHE" 2>/dev/null || true

# 获取系统资源状态
get_system_load() {
    local cpu_usage=0
    local memory_usage=0
    local load_avg="0.0"

    # 快速CPU使用率检查
    if [[ -r /proc/stat ]]; then
        cpu_usage=$(awk '/^cpu / {usage=($2+$4)*100/($2+$3+$4+$5)} END {print int(usage)}' /proc/stat 2>/dev/null || echo "0")
    fi

    # 快速内存使用率检查
    if [[ -r /proc/meminfo ]]; then
        memory_usage=$(awk '/MemTotal|MemAvailable/ {if($1=="MemTotal:") total=$2; if($1=="MemAvailable:") avail=$2} END {if(total>0) print int((total-avail)*100/total); else print 0}' /proc/meminfo 2>/dev/null || echo "0")
    fi

    # 系统负载
    if [[ -r /proc/loadavg ]]; then
        load_avg=$(cut -d' ' -f1 /proc/loadavg 2>/dev/null || echo "0.0")
    fi

    echo "$cpu_usage,$memory_usage,$load_avg"
}

# 计算最优并发度
calculate_optimal_concurrency() {
    local system_load="$1"
    local cpu_usage=$(echo "$system_load" | cut -d',' -f1)
    local memory_usage=$(echo "$system_load" | cut -d',' -f2)
    local load_avg=$(echo "$system_load" | cut -d',' -f3)

    local optimal_concurrency=$MAX_CONCURRENT_HOOKS

    # 基于CPU使用率调整
    if [[ ${cpu_usage:-0} -gt $CPU_THRESHOLD ]]; then
        optimal_concurrency=$((optimal_concurrency - 1))
    fi

    # 基于内存使用率调整
    if [[ ${memory_usage:-0} -gt $MEMORY_THRESHOLD ]]; then
        optimal_concurrency=$((optimal_concurrency - 1))
    fi

    # 基于系统负载调整
    local load_int=$(echo "$load_avg" | cut -d'.' -f1)
    if [[ ${load_int:-0} -gt 2 ]]; then
        optimal_concurrency=$((optimal_concurrency - 1))
    fi

    # 确保最小并发度为1
    if [[ $optimal_concurrency -lt 1 ]]; then
        optimal_concurrency=1
    fi

    echo "$optimal_concurrency"
}

# 检查运行中的Hook进程
check_running_hooks() {
    local running_hooks=0

    # 检查Claude相关进程
    if command -v pgrep >/dev/null 2>&1; then
        running_hooks=$(pgrep -cf "claude.*hook" 2>/dev/null || echo 0)

        # 如果没有找到，检查bash进程中的hook
        if [[ $running_hooks -eq 0 ]]; then
            running_hooks=$(pgrep -cf "bash.*\.sh" 2>/dev/null | head -1 || echo 0)
        fi
    fi

    echo "$running_hooks"
}

# 生成并发建议
generate_concurrency_advice() {
    local current_load="$1"
    local optimal_concurrency="$2"
    local running_hooks="$3"

    local cpu_usage=$(echo "$current_load" | cut -d',' -f1)
    local memory_usage=$(echo "$current_load" | cut -d',' -f2)
    local load_avg=$(echo "$current_load" | cut -d',' -f3)

    # 生成建议
    local advice=""

    if [[ ${cpu_usage:-0} -gt $CPU_THRESHOLD ]]; then
        advice+="⚠️ CPU高负载(${cpu_usage}%)，建议减少并发度 "
    fi

    if [[ ${memory_usage:-0} -gt $MEMORY_THRESHOLD ]]; then
        advice+="⚠️ 内存高使用(${memory_usage}%)，建议优化内存使用 "
    fi

    if [[ $running_hooks -gt $optimal_concurrency ]]; then
        advice+="🔄 当前Hook过多($running_hooks > $optimal_concurrency)，建议等待 "
    fi

    if [[ -z "$advice" ]]; then
        if [[ ${cpu_usage:-0} -lt 50 && ${memory_usage:-0} -lt 60 ]]; then
            advice="✅ 系统资源充足，可以增加并发度"
        else
            advice="📊 系统资源正常，维持当前并发度"
        fi
    fi

    echo "$advice"
}

# 缓存并发配置
cache_concurrency_config() {
    local optimal_concurrency="$1"
    local system_load="$2"
    local timestamp=$(date +%s)

    # 创建配置缓存
    cat > "${CONCURRENCY_CACHE}/config" << EOF
{
  "timestamp": $timestamp,
  "optimal_concurrency": $optimal_concurrency,
  "system_load": "$system_load",
  "recommendation": "使用${optimal_concurrency}个并发Hook"
}
EOF
}

# 检查是否应该延迟执行
should_delay_execution() {
    local running_hooks="$1"
    local optimal_concurrency="$2"

    if [[ $running_hooks -gt $optimal_concurrency ]]; then
        return 0  # 应该延迟
    else
        return 1  # 不需要延迟
    fi
}

# 智能延迟策略
smart_delay() {
    local running_hooks="$1"
    local optimal_concurrency="$2"

    if [[ $running_hooks -gt $optimal_concurrency ]]; then
        local delay_time=$(echo "scale=2; 0.05 * ($running_hooks - $optimal_concurrency)" | bc 2>/dev/null || echo "0.05")

        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "🕐 智能延迟: ${delay_time}s (等待Hook完成)" >&2
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Optimizer] 延迟${delay_time}s" >&2
        fi
        sleep "$delay_time"
    fi
}

# 主优化逻辑
main() {
    local start_time=$(date +%s.%N)

    # 超时保护
    (sleep $OPTIMIZER_TIMEOUT; exit 0) &
    local timeout_pid=$!

    # 获取系统状态
    local system_load=$(get_system_load)
    local running_hooks=$(check_running_hooks)
    local optimal_concurrency=$(calculate_optimal_concurrency "$system_load")

    # 生成建议
    local advice=$(generate_concurrency_advice "$system_load" "$optimal_concurrency" "$running_hooks")

    # 输出优化建议（仅在有重要信息时）
    if echo "$advice" | grep -q "⚠️\|🔄"; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            {
                echo "🔧 并发优化建议:"
                echo "   $advice"
                echo "   推荐并发度: $optimal_concurrency"
                echo "   当前运行: $running_hooks Hook(s)"
            } >&2
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Optimizer] $advice (并发:$optimal_concurrency)" >&2
        fi
    elif [[ "${DEBUG_HOOKS:-false}" == "true" ]]; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            {
                echo "🔧 并发状态: CPU:$(echo "$system_load" | cut -d',' -f1)% MEM:$(echo "$system_load" | cut -d',' -f2)% LOAD:$(echo "$system_load" | cut -d',' -f3)"
                echo "   并发度: $optimal_concurrency (运行中:$running_hooks)"
            } >&2
        fi
    fi

    # 应用智能延迟
    smart_delay "$running_hooks" "$optimal_concurrency"

    # 缓存配置（异步）
    cache_concurrency_config "$optimal_concurrency" "$system_load" &

    # 计算执行时间
    local execution_time=$(echo "scale=3; $(date +%s.%N) - $start_time" | bc 2>/dev/null || echo "0.001")

    # 性能日志
    if [[ "${DEBUG_HOOKS:-false}" == "true" ]]; then
        echo "DEBUG: concurrent_optimizer executed in ${execution_time}s" >&2
    fi

    # 清理
    kill $timeout_pid 2>/dev/null || true

    # 输出优化结果（JSON格式）
    if [[ "${OUTPUT_JSON:-false}" == "true" ]]; then
        echo "{\"optimal_concurrency\":$optimal_concurrency,\"running_hooks\":$running_hooks,\"system_load\":\"$system_load\",\"execution_time\":$execution_time}"
    fi

    exit 0
}

# 特殊功能：并发统计
if [[ "${1:-}" == "--stats" ]]; then
    if [[ -f "${CONCURRENCY_CACHE}/config" ]]; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "📊 并发优化统计:"
            cat "${CONCURRENCY_CACHE}/config" 2>/dev/null || echo "无缓存数据"
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Optimizer] Stats: $(grep optimal_concurrency "${CONCURRENCY_CACHE}/config" | cut -d':' -f2 | tr -d ' ,')"
        fi
    else
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "暂无并发优化数据"
        fi
    fi
    exit 0
fi

# 特殊功能：设置最大并发度
if [[ "${1:-}" == "--set-max" ]] && [[ -n "${2:-}" ]]; then
    if [[ "$2" =~ ^[0-9]+$ ]] && [[ "$2" -ge 1 ]] && [[ "$2" -le 8 ]]; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "设置最大并发度为: $2"
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Optimizer] Max=$2"
        fi
        # 这里可以写入配置文件
        echo "MAX_CONCURRENT_HOOKS=$2" > "${CONCURRENCY_CACHE}/max_concurrency"
        exit 0
    else
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "错误: 并发度必须是1-8之间的数字" >&2
        fi
        exit 1
    fi
fi

# 主执行入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
