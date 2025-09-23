#!/bin/bash
# Claude Enhancer 激进阻止策略
# 尝试多种方法强制阻止执行

set -e

INPUT=$(cat)

# 快速检查
AGENT_COUNT=$(echo "$INPUT" | grep -c '"subagent_type"' 2>/dev/null || echo 0)
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 || echo "")

# 判断最小需求
MIN_REQUIRED=3
if echo "$TASK_DESC" | grep -qiE "login|auth|认证"; then
    MIN_REQUIRED=5
elif echo "$TASK_DESC" | grep -qiE "api|接口"; then
    MIN_REQUIRED=4
fi

if [ "$AGENT_COUNT" -lt "$MIN_REQUIRED" ]; then
    # 策略1: 大声警告
    echo "⛔⛔⛔ STOP! VIOLATION DETECTED! ⛔⛔⛔" >&2
    echo "════════════════════════════════════════" >&2
    echo "❌ BLOCKED: Only $AGENT_COUNT agents, need $MIN_REQUIRED" >&2
    echo "════════════════════════════════════════" >&2

    # 策略2: 返回错误JSON替代原输入
    echo '{"error": "CLAUDE_ENHANCER_BLOCKED", "need": '"$MIN_REQUIRED"', "got": '"$AGENT_COUNT"'}'

    # 策略3: 设置环境变量标记
    export CLAUDE_ENHANCER_VIOLATION=1

    # 策略4: 写入临时文件作为标记
    echo "BLOCKED at $(date)" > /tmp/claude_enhancer_blocked.flag

    # 策略5: 尝试各种退出码
    # exit 2 应该阻止（按文档）
    # exit 1 表示错误
    # exit 127 命令未找到
    exit 2
else
    echo "✅ Approved: $AGENT_COUNT agents" >&2
    echo "$INPUT"
    exit 0
fi