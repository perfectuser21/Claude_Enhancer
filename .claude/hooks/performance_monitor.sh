#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 性能监控Hook

set -e

# 记录开始时间
START_TIME=$(date +%s%3N 2>/dev/null || date +%s)

# 读取输入
INPUT=$(cat)

# 提取工具名称
TOOL_NAME=$(echo "$INPUT" | grep -oP '"tool"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "unknown")

# 计算执行时间（毫秒）
END_TIME=$(date +%s%3N 2>/dev/null || date +%s)
EXEC_TIME=$((END_TIME - START_TIME))

# 性能阈值（毫秒）
FAST_THRESHOLD=100
MEDIUM_THRESHOLD=500
SLOW_THRESHOLD=1000
VERY_SLOW_THRESHOLD=3000

# 性能分析与输出
if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    if [ "$EXEC_TIME" -gt "$VERY_SLOW_THRESHOLD" ]; then
        echo "🚨 性能严重警告: $TOOL_NAME 执行时间 ${EXEC_TIME}ms" >&2
        echo "💡 建议: 考虑优化或使用缓存" >&2
    elif [ "$EXEC_TIME" -gt "$SLOW_THRESHOLD" ]; then
        echo "⚠️ 性能警告: $TOOL_NAME 执行时间 ${EXEC_TIME}ms" >&2
        echo "💡 建议: 使用批量操作优化" >&2
    elif [ "$EXEC_TIME" -gt "$MEDIUM_THRESHOLD" ]; then
        echo "🔍 性能提示: $TOOL_NAME 执行时间 ${EXEC_TIME}ms" >&2
    elif [ "$EXEC_TIME" -lt "$FAST_THRESHOLD" ]; then
        echo "🚀 快速执行: $TOOL_NAME (${EXEC_TIME}ms)" >&2
    fi
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    # 紧凑输出模式
    if [ "$EXEC_TIME" -gt "$VERY_SLOW_THRESHOLD" ]; then
        echo "[Perf] 🚨 ${TOOL_NAME} ${EXEC_TIME}ms" >&2
    elif [ "$EXEC_TIME" -gt "$SLOW_THRESHOLD" ]; then
        echo "[Perf] ⚠️ ${TOOL_NAME} ${EXEC_TIME}ms" >&2
    elif [ "$EXEC_TIME" -lt "$FAST_THRESHOLD" ]; then
        echo "[Perf] 🚀 ${TOOL_NAME} ${EXEC_TIME}ms" >&2
    fi
fi

# 记录到性能日志（静默进行）
PERF_LOG=".claude/logs/performance.log"
if [ -n "$TOOL_NAME" ]; then
    mkdir -p $(dirname "$PERF_LOG") 2>/dev/null || true
    {
        flock -x 200
        echo "$(date '+%Y-%m-%d %H:%M:%S') | $TOOL_NAME | ${EXEC_TIME}ms" >> "$PERF_LOG"
    } 200>"$PERF_LOG.lock" 2>/dev/null || true
fi

# 输出原始内容
echo "$INPUT"
exit 0