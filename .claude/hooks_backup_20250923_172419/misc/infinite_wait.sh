#!/bin/bash
# Claude Enhancer 无限等待器
# 如果不满足要求，永远不返回，造成超时

set -e

INPUT=$(cat)
AGENT_COUNT=$(echo "$INPUT" | grep -c '"subagent_type"' 2>/dev/null || echo 0)
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 || echo "")

MIN_REQUIRED=3
if echo "$TASK_DESC" | grep -qiE "login|auth|认证|登录"; then
    MIN_REQUIRED=5
elif echo "$TASK_DESC" | grep -qiE "api|接口"; then
    MIN_REQUIRED=4
fi

if [ "$AGENT_COUNT" -lt "$MIN_REQUIRED" ]; then
    echo "⏰ BLOCKING BY TIMEOUT - Need $MIN_REQUIRED agents, got $AGENT_COUNT" >&2
    echo "This hook will wait forever to prevent execution..." >&2

    # 无限循环，永不返回
    while true; do
        sleep 1
        echo "Still blocking... Need $MIN_REQUIRED agents" >&2
    done
else
    echo "✅ OK: $AGENT_COUNT agents" >&2
    echo "$INPUT"
    exit 0
fi