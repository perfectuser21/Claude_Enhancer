#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Agent错误自动恢复

# 统一日志记录（激活追踪）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [agent_error_recovery.sh] triggered by ${USER:-claude}" >> "$LOG_FILE"

MAX_RETRIES=2
RETRY_DELAY=0.5

# 错误恢复函数
recover_agent() {
    local agent_name=$1
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        # 尝试恢复
        sleep $RETRY_DELAY

        # 检查Agent状态
        if [ -f "/tmp/agent_${agent_name}.lock" ]; then
            rm -f "/tmp/agent_${agent_name}.lock"
            if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
                echo "🔧 Recovered agent: $agent_name"
            elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
                echo "[Recovery] $agent_name"
            fi
            return 0
        fi

        retry_count=$((retry_count + 1))
    done

    return 1
}

# 监控Agent健康
if [ -n "$AGENT_NAME" ]; then
    recover_agent "$AGENT_NAME"
fi
