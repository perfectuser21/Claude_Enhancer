#!/bin/bash
# Claude Enhancer Agent Validator Hook - Advisory Mode
# 只提供建议，不阻止执行

set -e

# 读取输入
INPUT=$(cat)

# 提取所有agent types
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . || echo 0)

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 | tr '[:upper:]' '[:lower:]')

# 检测任务类型
detect_task_type() {
    local desc="$1"

    if echo "$desc" | grep -qiE "登录|认证|auth|用户|权限|jwt|oauth|session|password"; then
        echo "authentication"
        return
    fi

    if echo "$desc" | grep -qiE "api|接口|rest|graphql|endpoint|route|swagger"; then
        echo "api_development"
        return
    fi

    if echo "$desc" | grep -qiE "数据库|database|schema|sql|mongodb|redis|表结构"; then
        echo "database_design"
        return
    fi

    echo "general"
}

TASK_TYPE=$(detect_task_type "$TASK_DESC")

# 获取推荐的agents
get_required_agents() {
    case "$1" in
        authentication)
            echo "backend-architect security-auditor api-designer database-specialist test-engineer"
            ;;
        api_development)
            echo "api-designer backend-architect test-engineer technical-writer"
            ;;
        database_design)
            echo "database-specialist backend-architect performance-engineer"
            ;;
        *)
            echo "backend-architect test-engineer technical-writer"
            ;;
    esac
}

REQUIRED_AGENTS=$(get_required_agents "$TASK_TYPE")
REQUIRED_COUNT=$(echo "$REQUIRED_AGENTS" | wc -w)

# 只输出建议信息
echo "╔══════════════════════════════════════════╗" >&2
echo "║     Claude Enhancer Agent Validator (Advisory)  ║" >&2
echo "╠══════════════════════════════════════════╣" >&2
echo "║ Task Type: $TASK_TYPE                     " >&2
echo "║ Agents Used: $AGENT_COUNT                 " >&2
echo "║ Recommended: $REQUIRED_COUNT              " >&2
echo "╠══════════════════════════════════════════╣" >&2

if [ "$AGENT_COUNT" -lt "$REQUIRED_COUNT" ]; then
    echo "║ ⚠️  建议使用更多Agent:                    " >&2
    echo "║                                          " >&2
    for agent in $REQUIRED_AGENTS; do
        if ! echo "$AGENTS" | grep -q "$agent"; then
            echo "║   • $agent                           " >&2
        fi
    done
else
    echo "║ ✅ Agent数量符合建议!                     " >&2
fi

echo "╚══════════════════════════════════════════╝" >&2

# 总是返回成功，不阻止执行
exit 0