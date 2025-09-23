#!/bin/bash
# Claude Enhancer 性能监控Hook
# 监控执行时间并提供性能优化建议（非阻塞）

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
SLOW_THRESHOLD=1000
VERY_SLOW_THRESHOLD=3000

# 性能分析
if [ "$EXEC_TIME" -gt "$VERY_SLOW_THRESHOLD" ]; then
    echo "⚠️ 性能警告: $TOOL_NAME 执行时间 ${EXEC_TIME}ms"
    echo "💡 建议: 考虑优化或使用缓存"
elif [ "$EXEC_TIME" -gt "$SLOW_THRESHOLD" ]; then
    echo "🔍 性能提示: $TOOL_NAME 执行时间 ${EXEC_TIME}ms"
fi

# 记录到性能日志（使用文件锁）
PERF_LOG=".claude/logs/performance.log"
if [ -n "$TOOL_NAME" ]; then
    mkdir -p $(dirname "$PERF_LOG") 2>/dev/null || true
    {
        flock -x 200
        echo "$(date '+%Y-%m-%d %H:%M:%S') | $TOOL_NAME | ${EXEC_TIME}ms" >> "$PERF_LOG"
    } 200>"$PERF_LOG.lock" 2>/dev/null || true
fi

# 非阻塞，始终返回成功
exit 0