#!/bin/bash
# Agent错误自动恢复

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
            echo "🔧 Recovered agent: $agent_name"
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
