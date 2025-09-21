#!/bin/bash
# Claude Enhancer 强制返回机制
# 尝试通过修改输出来强制Claude Code重新分配

set -e

# 读取输入
INPUT=$(cat)

# 提取任务信息
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 || echo "unknown")
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 || true)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . 2>/dev/null || echo 0)

# 检测任务类型和要求
detect_requirements() {
    local desc="$1"

    if echo "$desc" | grep -qiE "login|auth|jwt|password|认证|登录"; then
        echo "5:authentication"
    elif echo "$desc" | grep -qiE "api|接口|rest|endpoint"; then
        echo "4:api"
    elif echo "$desc" | grep -qiE "database|数据库|sql"; then
        echo "3:database"
    elif echo "$desc" | grep -qiE "frontend|界面|ui|react|vue"; then
        echo "4:frontend"
    elif echo "$desc" | grep -qiE "test|测试"; then
        echo "4:testing"
    else
        echo "3:general"
    fi
}

REQUIREMENTS=$(detect_requirements "$TASK_DESC")
MIN_REQUIRED=$(echo "$REQUIREMENTS" | cut -d: -f1)
TASK_TYPE=$(echo "$REQUIREMENTS" | cut -d: -f2)

# 如果不满足要求，修改输出强制返回
if [ "$AGENT_COUNT" -lt "$MIN_REQUIRED" ]; then
    echo "🚫 BLOCKING: Requirements Not Met" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "Task Type: $TASK_TYPE" >&2
    echo "Minimum Required: $MIN_REQUIRED agents" >&2
    echo "Actually Found: $AGENT_COUNT agents" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "" >&2
    echo "❌ EXECUTION BLOCKED" >&2
    echo "" >&2
    echo "📋 Required Agent Configuration:" >&2

    case "$TASK_TYPE" in
        authentication)
            echo "  1. backend-architect - System architecture" >&2
            echo "  2. security-auditor - Security review" >&2
            echo "  3. api-designer - API design" >&2
            echo "  4. database-specialist - Data model" >&2
            echo "  5. test-engineer - Test strategy" >&2
            ;;
        api)
            echo "  1. api-designer - API specification" >&2
            echo "  2. backend-architect - Implementation" >&2
            echo "  3. test-engineer - Testing" >&2
            echo "  4. technical-writer - Documentation" >&2
            ;;
        database)
            echo "  1. database-specialist - Schema design" >&2
            echo "  2. backend-architect - Integration" >&2
            echo "  3. performance-engineer - Optimization" >&2
            ;;
        *)
            echo "  Need at least $MIN_REQUIRED specialized agents" >&2
            ;;
    esac

    echo "" >&2
    echo "🔄 MANDATORY ACTION: Reconfigure with $MIN_REQUIRED agents" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2

    # 返回修改后的输入，强制Claude Code看到这个问题
    cat << EOF
{
  "CLAUDE_ENHANCER_BLOCKED": true,
  "reason": "Insufficient agents: need $MIN_REQUIRED, got $AGENT_COUNT",
  "task_type": "$TASK_TYPE",
  "required_agents": $MIN_REQUIRED,
  "actual_agents": $AGENT_COUNT,
  "action_required": "MUST use $MIN_REQUIRED agents in parallel",
  "original_input": $INPUT
}
EOF

    # 尝试各种退出码
    exit 2  # 按文档应该阻止

else
    # 满足要求，正常执行
    echo "✅ APPROVED: Using $AGENT_COUNT agents for $TASK_TYPE task" >&2
    echo "$INPUT"
    exit 0
fi