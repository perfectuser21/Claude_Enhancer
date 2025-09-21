#!/bin/bash
# Claude Enhancer 输入劫持器
# 如果不满足要求，修改任务为无害的内容

set -e

INPUT=$(cat)
AGENT_COUNT=$(echo "$INPUT" | grep -c '"subagent_type"' 2>/dev/null || echo 0)
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 || echo "")

MIN_REQUIRED=3
TASK_TYPE="general"
if echo "$TASK_DESC" | grep -qiE "login|auth|认证|登录"; then
    MIN_REQUIRED=5
    TASK_TYPE="authentication"
elif echo "$TASK_DESC" | grep -qiE "api|接口"; then
    MIN_REQUIRED=4
    TASK_TYPE="api"
fi

if [ "$AGENT_COUNT" -lt "$MIN_REQUIRED" ]; then
    echo "🔄 HIJACKING INPUT - Replacing with safe task" >&2
    echo "Original task blocked: Need $MIN_REQUIRED agents" >&2

    # 劫持输入，改为一个报告违规的任务
    cat << EOF
{
  "subagent_type": "technical-writer",
  "prompt": "VIOLATION REPORT: User tried to execute $TASK_TYPE task with only $AGENT_COUNT agents instead of required $MIN_REQUIRED. Please generate a report explaining why this violates Claude Enhancer quality standards and list the $MIN_REQUIRED required agents for this task type.",
  "description": "Violation Report"
}
EOF
else
    echo "✅ OK: $AGENT_COUNT agents" >&2
    echo "$INPUT"
fi