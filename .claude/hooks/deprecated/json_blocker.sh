#!/bin/bash
# Claude Enhancer JSON阻止机制
# 使用文档中描述的JSON格式尝试阻止

set -e

INPUT=$(cat)

# 计算agent数量
AGENT_COUNT=$(echo "$INPUT" | grep -c '"subagent_type"' 2>/dev/null || echo 0)
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 || echo "")

# 判断最小需求
MIN_REQUIRED=3
TASK_TYPE="general"

if echo "$TASK_DESC" | grep -qiE "login|auth|认证|登录|用户"; then
    MIN_REQUIRED=5
    TASK_TYPE="authentication"
elif echo "$TASK_DESC" | grep -qiE "api|接口|rest|endpoint"; then
    MIN_REQUIRED=4
    TASK_TYPE="api"
elif echo "$TASK_DESC" | grep -qiE "database|数据库|sql"; then
    MIN_REQUIRED=3
    TASK_TYPE="database"
fi

if [ "$AGENT_COUNT" -lt "$MIN_REQUIRED" ]; then
    # 根据文档，返回JSON格式阻止执行
    cat << EOF
{
  "continue": false,
  "stopReason": "Claude Enhancer: Need $MIN_REQUIRED agents for $TASK_TYPE task, but only found $AGENT_COUNT",
  "permissionDecision": "deny",
  "feedback": "❌ BLOCKED: This $TASK_TYPE task requires at least $MIN_REQUIRED agents working in parallel. Currently only $AGENT_COUNT agent(s) configured. Please reconfigure with the required number of agents.",
  "suggestions": [
    "Use at least $MIN_REQUIRED agents for this task type",
    "Configure agents in a single function_calls block for parallel execution",
    "Required agents for $TASK_TYPE: backend-architect, security-auditor, api-designer, database-specialist, test-engineer"
  ]
}
EOF
    # 同时输出到stderr供查看
    echo "🚫 Blocking: $AGENT_COUNT < $MIN_REQUIRED for $TASK_TYPE" >&2

    # 根据文档应该用exit 2
    exit 2
else
    # 满足要求，允许执行
    cat << EOF
{
  "continue": true,
  "permissionDecision": "allow",
  "feedback": "✅ Approved: Using $AGENT_COUNT agents for $TASK_TYPE task (minimum: $MIN_REQUIRED)"
}
EOF
    echo "✅ Approved: $AGENT_COUNT agents for $TASK_TYPE" >&2

    # 输出原始内容
    echo "$INPUT"
    exit 0
fi