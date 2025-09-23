#!/bin/bash
# Claude Enhancer Agent Validator - Enforced Mode
# 强制执行规则，提供清晰的修正指导

set -e

INPUT=$(cat)

# 提取agents
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u || true)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . 2>/dev/null || echo 0)

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 | tr '[:upper:]' '[:lower:]' || echo "")

# 检测任务类型
if echo "$TASK_DESC" | grep -qiE "认证|登录|用户|auth|login|jwt|password"; then
    TASK_TYPE="authentication"
    REQUIRED_AGENTS="backend-architect security-auditor api-designer database-specialist test-engineer"
    MIN_COUNT=5
elif echo "$TASK_DESC" | grep -qiE "api|接口|rest|endpoint|route"; then
    TASK_TYPE="api_development"
    REQUIRED_AGENTS="api-designer backend-architect test-engineer technical-writer"
    MIN_COUNT=4
elif echo "$TASK_DESC" | grep -qiE "数据库|database|table|schema|sql"; then
    TASK_TYPE="database"
    REQUIRED_AGENTS="database-specialist backend-architect performance-engineer"
    MIN_COUNT=3
else
    TASK_TYPE="general"
    REQUIRED_AGENTS="backend-architect test-engineer technical-writer"
    MIN_COUNT=3
fi

# 检查缺失的agents
MISSING=""
for agent in $REQUIRED_AGENTS; do
    if ! echo "$AGENTS" | grep -q "$agent"; then
        MISSING="$MISSING $agent"
    fi
done

# 输出验证结果
echo "══════════════════════════════════════" >&2
echo "Claude Enhancer Agent Validator" >&2
echo "Task Type: $TASK_TYPE" >&2
echo "Agents: $AGENT_COUNT/$MIN_COUNT" >&2

if [ "$AGENT_COUNT" -lt "$MIN_COUNT" ] || [ -n "$MISSING" ]; then
    echo "❌ BLOCKED: Need $MIN_COUNT agents" >&2
    echo "Missing: $MISSING" >&2
    echo "══════════════════════════════════════" >&2
    echo "CORRECT APPROACH:" >&2
    echo "Use all these agents in ONE message:" >&2
    for agent in $REQUIRED_AGENTS; do
        echo "  - $agent" >&2
    done
    exit 2  # 强制阻止执行
fi

echo "✅ All validations passed!" >&2
exit 0