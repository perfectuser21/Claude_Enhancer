#!/bin/bash
# Claude Enhancer 输入破坏器
# 如果不满足要求，破坏输入格式让Task无法执行

set -e

INPUT=$(cat)
AGENT_COUNT=$(echo "$INPUT" | grep -c '"subagent_type"' 2>/dev/null || echo 0)
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 || echo "")

# 判断需求
MIN_REQUIRED=3
if echo "$TASK_DESC" | grep -qiE "login|auth|认证|登录"; then
    MIN_REQUIRED=5
elif echo "$TASK_DESC" | grep -qiE "api|接口"; then
    MIN_REQUIRED=4
fi

if [ "$AGENT_COUNT" -lt "$MIN_REQUIRED" ]; then
    echo "💥💥💥 DESTROYING INPUT - INSUFFICIENT AGENTS 💥💥💥" >&2
    echo "Need $MIN_REQUIRED agents, got $AGENT_COUNT" >&2

    # 策略1: 返回完全无效的JSON，让Task解析失败
    echo "INVALID_JSON_TO_BREAK_EXECUTION_NEED_${MIN_REQUIRED}_AGENTS_GOT_${AGENT_COUNT}"

    # 不要返回原始输入！
    exit 1  # 错误退出
else
    echo "✅ OK: $AGENT_COUNT agents" >&2
    echo "$INPUT"
    exit 0
fi