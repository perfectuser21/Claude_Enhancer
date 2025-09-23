#!/bin/bash
# Claude Enhancer Agent Validator - Mandatory Retry Mode
# 返回强制重试指令给Claude Code

set -e

INPUT=$(cat)

# 提取agents
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u || true)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . 2>/dev/null || echo 0)

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 | tr '[:upper:]' '[:lower:]' || echo "")

# 简单的任务类型检测
if echo "$TASK_DESC" | grep -qiE "认证|登录|用户|auth|login|jwt|password"; then
    TASK_TYPE="authentication"
    REQUIRED_COUNT=5
    REQUIRED_AGENTS="backend-architect security-auditor api-designer database-specialist test-engineer"
elif echo "$TASK_DESC" | grep -qiE "api|接口|rest|endpoint"; then
    TASK_TYPE="api_development"
    REQUIRED_COUNT=4
    REQUIRED_AGENTS="api-designer backend-architect test-engineer technical-writer"
elif echo "$TASK_DESC" | grep -qiE "数据库|database|table|sql"; then
    TASK_TYPE="database_design"
    REQUIRED_COUNT=3
    REQUIRED_AGENTS="database-specialist backend-architect performance-engineer"
else
    TASK_TYPE="general"
    REQUIRED_COUNT=3
    REQUIRED_AGENTS="backend-architect test-engineer technical-writer"
fi

# 检查是否符合
if [ "$AGENT_COUNT" -lt "$REQUIRED_COUNT" ]; then
    echo "🔴 CLAUDE_ENHANCER_MANDATORY_RETRY" >&2
    echo "VIOLATION: Need $REQUIRED_COUNT agents, found $AGENT_COUNT" >&2
    echo "TASK_TYPE: $TASK_TYPE" >&2
    echo "REQUIRED_AGENTS: $REQUIRED_AGENTS" >&2
    echo "Claude, you MUST retry with all required agents!" >&2
else
    echo "✅ CLAUDE_ENHANCER_APPROVED" >&2
    echo "Using $AGENT_COUNT agents - meets requirement" >&2
fi

exit 0