#!/bin/bash
# Task预检查 - 在执行前检查是否符合Claude Enhancer规则
# 这个脚本会在UserPromptSubmit时运行，提示需要哪些Agent

set -e

# 读取用户输入
INPUT=$(cat)
INPUT_LOWER=$(echo "$INPUT" | tr '[:upper:]' '[:lower:]')

# 检测任务类型
detect_task() {
    local input="$1"

    if echo "$input" | grep -qiE "认证|登录|用户|权限|auth|login|jwt|password|security"; then
        echo "authentication"
        return
    fi

    if echo "$input" | grep -qiE "api|接口|rest|endpoint|服务|swagger"; then
        echo "api_development"
        return
    fi

    if echo "$input" | grep -qiE "数据库|database|表|schema|sql|postgres|mysql"; then
        echo "database_design"
        return
    fi

    if echo "$input" | grep -qiE "前端|界面|页面|组件|frontend|ui|react|vue"; then
        echo "frontend_development"
        return
    fi

    if echo "$input" | grep -qiE "测试|test|单元|集成|e2e|quality"; then
        echo "testing"
        return
    fi

    echo "general"
}

# 获取任务类型
TASK_TYPE=$(detect_task "$INPUT_LOWER")

# 根据任务类型获取必需的Agents
case "$TASK_TYPE" in
    authentication)
        AGENTS="backend-architect, security-auditor, api-designer, database-specialist, test-engineer"
        COUNT=5
        ;;
    api_development)
        AGENTS="api-designer, backend-architect, test-engineer, technical-writer"
        COUNT=4
        ;;
    database_design)
        AGENTS="database-specialist, backend-architect, performance-engineer"
        COUNT=3
        ;;
    frontend_development)
        AGENTS="frontend-specialist, react-pro, ux-designer, test-engineer"
        COUNT=4
        ;;
    testing)
        AGENTS="test-engineer, performance-tester, security-auditor, code-reviewer"
        COUNT=4
        ;;
    *)
        AGENTS="backend-architect, test-engineer, technical-writer"
        COUNT=3
        ;;
esac

# 输出建议
echo "╔════════════════════════════════════════════════╗" >&2
echo "║         Claude Enhancer Task Pre-Check               ║" >&2
echo "╠════════════════════════════════════════════════╣" >&2
echo "║ 📋 Task Type Detected: $TASK_TYPE              " >&2
echo "║                                                ║" >&2
echo "║ 🤖 Required Agents ($COUNT):                  ║" >&2
echo "║    $AGENTS                                     " >&2
echo "║                                                ║" >&2
echo "║ ⚡ Remember:                                   ║" >&2
echo "║    • Use ALL agents in ONE message            ║" >&2
echo "║    • Parallel execution is required           ║" >&2
echo "║    • Hooks will block if not compliant        ║" >&2
echo "╚════════════════════════════════════════════════╝" >&2

# 不阻止执行，只是提醒
exit 0