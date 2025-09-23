#!/bin/bash
# Agent验证器 - 调试版本，记录所有输入输出

LOG_FILE="/tmp/claude_enhancer_hook_debug.log"
INPUT=$(cat)

# 记录时间和输入
echo "========================================" >> $LOG_FILE
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hook triggered" >> $LOG_FILE
echo "Raw input:" >> $LOG_FILE
echo "$INPUT" >> $LOG_FILE

# 提取agents
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u || true)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . 2>/dev/null || echo 0)

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 | tr '[:upper:]' '[:lower:]' || echo "")

# 记录解析结果
echo "Parsed agents: $AGENTS" >> $LOG_FILE
echo "Agent count: $AGENT_COUNT" >> $LOG_FILE
echo "Task description: $TASK_DESC" >> $LOG_FILE

# 检测任务类型
if echo "$TASK_DESC" | grep -qiE "认证|登录|用户|auth|login|jwt|password"; then
    TASK_TYPE="authentication"
    REQUIRED_AGENTS="backend-architect security-auditor api-designer database-specialist test-engineer"
    MIN_COUNT=5
elif echo "$TASK_DESC" | grep -qiE "api|接口|rest|endpoint|route"; then
    TASK_TYPE="api_development"
    REQUIRED_AGENTS="api-designer backend-architect test-engineer technical-writer"
    MIN_COUNT=4
else
    TASK_TYPE="general"
    REQUIRED_AGENTS="backend-architect test-engineer technical-writer"
    MIN_COUNT=3
fi

echo "Task type: $TASK_TYPE" >> $LOG_FILE
echo "Required: $MIN_COUNT agents" >> $LOG_FILE

# 输出到stderr供用户看到
echo "══════════════════════════════════════" >&2
echo "Claude Enhancer Validator (Debug Mode)" >&2
echo "Task Type: $TASK_TYPE" >&2
echo "Agents: $AGENT_COUNT/$MIN_COUNT" >&2

if [ "$AGENT_COUNT" -lt "$MIN_COUNT" ]; then
    echo "❌ BLOCKING: Need $MIN_COUNT agents" >&2
    echo "Decision: BLOCK (exit 2)" >> $LOG_FILE
    echo "══════════════════════════════════════" >&2
    exit 2
fi

echo "✅ Validation passed!" >&2
echo "Decision: ALLOW (exit 0)" >> $LOG_FILE
exit 0