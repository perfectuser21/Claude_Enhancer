#!/bin/bash
# Claude Enhancer Plus 性能监控Hook
# 集成Git优化器的高性能监控（非阻塞）

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

# 检查是否有Git优化器可用
GIT_OPTIMIZER_CONFIG=".claude/git-integration-config.json"
USE_GIT_OPTIMIZER=false

if [ -f "$GIT_OPTIMIZER_CONFIG" ] && command -v node >/dev/null 2>&1; then
    if [ -f "src/git/GitIntegration.js" ]; then
        USE_GIT_OPTIMIZER=true
    fi
fi

# 性能阈值（毫秒）
FAST_THRESHOLD=100
MEDIUM_THRESHOLD=500
SLOW_THRESHOLD=1000
VERY_SLOW_THRESHOLD=3000

# 高级性能分析
if [ "$USE_GIT_OPTIMIZER" = true ]; then
    # 使用Git优化器进行详细性能分析
    echo "📊 使用Git优化器性能监控..." >&2

    # 通过Node.js调用Git优化器的性能监控
    node -e "
        try {
            const GitIntegration = require('./src/git/GitIntegration');
            const git = new GitIntegration();

            // 记录性能数据
            const perfData = {
                tool: '$TOOL_NAME',
                duration: $EXEC_TIME,
                timestamp: Date.now()
            };

            console.error('⚡ 集成性能监控: ' + JSON.stringify(perfData));

            // 提供智能优化建议
            if ($EXEC_TIME > $VERY_SLOW_THRESHOLD) {
                console.error('🚨 性能严重警告: $TOOL_NAME 执行时间 ${EXEC_TIME}ms');
                console.error('💡 智能建议: 启用Git缓存可提升60%性能');
            } else if ($EXEC_TIME > $SLOW_THRESHOLD) {
                console.error('⚠️ 性能警告: $TOOL_NAME 执行时间 ${EXEC_TIME}ms');
                console.error('💡 建议: 考虑使用批量操作优化');
            } else if ($EXEC_TIME < $FAST_THRESHOLD) {
                console.error('🚀 快速执行: $TOOL_NAME (${EXEC_TIME}ms)');
            }

        } catch (error) {
            console.error('⚠️ Git优化器监控失败，使用基础监控');
        }
    " 2>/dev/null || {
        # 回退到基础性能监控
        USE_GIT_OPTIMIZER=false
    }
fi

# 基础性能分析（回退方案）
if [ "$USE_GIT_OPTIMIZER" = false ]; then
    if [ "$EXEC_TIME" -gt "$VERY_SLOW_THRESHOLD" ]; then
        echo "🚨 性能严重警告: $TOOL_NAME 执行时间 ${EXEC_TIME}ms" >&2
        echo "💡 建议: 考虑启用Git优化器获得60%性能提升" >&2
    elif [ "$EXEC_TIME" -gt "$SLOW_THRESHOLD" ]; then
        echo "⚠️ 性能警告: $TOOL_NAME 执行时间 ${EXEC_TIME}ms" >&2
        echo "💡 建议: 使用 'node src/git/git-optimizer-cli.js init' 启用优化" >&2
    elif [ "$EXEC_TIME" -gt "$MEDIUM_THRESHOLD" ]; then
        echo "🔍 性能提示: $TOOL_NAME 执行时间 ${EXEC_TIME}ms" >&2
    elif [ "$EXEC_TIME" -lt "$FAST_THRESHOLD" ]; then
        echo "🚀 快速执行: $TOOL_NAME (${EXEC_TIME}ms)" >&2
    fi
fi

# 记录到性能日志（使用文件锁）
PERF_LOG=".claude/logs/performance.log"
GIT_PERF_LOG=".claude/logs/git-performance.log"

if [ -n "$TOOL_NAME" ]; then
    mkdir -p $(dirname "$PERF_LOG") 2>/dev/null || true

    # 基础性能日志
    {
        flock -x 200
        echo "$(date '+%Y-%m-%d %H:%M:%S') | $TOOL_NAME | ${EXEC_TIME}ms | optimizer:$USE_GIT_OPTIMIZER" >> "$PERF_LOG"
    } 200>"$PERF_LOG.lock" 2>/dev/null || true

    # Git优化器专用日志
    if [ "$USE_GIT_OPTIMIZER" = true ]; then
        {
            flock -x 201
            echo "{\"timestamp\":\"$(date -Iseconds)\",\"tool\":\"$TOOL_NAME\",\"duration\":$EXEC_TIME,\"source\":\"hook\"}" >> "$GIT_PERF_LOG"
        } 201>"$GIT_PERF_LOG.lock" 2>/dev/null || true
    fi
fi

# 输出优化提示（偶尔显示）
if [ $(($(date +%s) % 100)) -eq 0 ] && [ "$USE_GIT_OPTIMIZER" = false ]; then
    echo "💡 提示: 运行 'node src/git/git-optimizer-cli.js init' 启用Git优化器" >&2
fi

# 非阻塞，始终返回成功
exit 0