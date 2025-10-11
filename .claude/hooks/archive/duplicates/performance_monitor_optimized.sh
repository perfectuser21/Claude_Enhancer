#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# 优化版性能监控 - 异步记录

LOG_FILE="/tmp/claude_performance.log"

# 异步记录性能数据
{
    TIMESTAMP=$(date +%s%3N)
    echo "$TIMESTAMP,hook_execution,success" >> "$LOG_FILE"
} &

# 立即返回，不阻塞
exit 0
