#!/bin/bash
# 动态获取Claude Enhancer项目路径
CLAUDE_ENHANCER_HOME="${CLAUDE_ENHANCER_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
export CLAUDE_ENHANCER_HOME

# Claude Enhancer Agent Validator Hook
# 验证Agent选择是否符合Claude Enhancer规则

set -e

# 读取输入
INPUT=$(cat)

# 配置文件路径
RULES_FILE="${CLAUDE_ENHANCER_HOME}/rules/claude_enhancer_rules.yaml"

# 提取所有agent types
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . || echo 0)

# 提取任务描述来识别任务类型
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 | tr '[:upper:]' '[:lower:]')

# 检测任务类型
detect_task_type() {
    local desc="$1"

    # 认证相关
    if echo "$desc" | grep -qiE "登录|认证|auth|用户|权限|jwt|oauth|session|password"; then
        echo "authentication"
        return
    fi

    # API开发
    if echo "$desc" | grep -qiE "api|接口|rest|graphql|endpoint|route|swagger"; then
        echo "api_development"
        return
    fi

    # 数据库
    if echo "$desc" | grep -qiE "数据库|database|schema|sql|mongodb|redis|表结构|migration"; then
        echo "database_design"
        return
    fi

    # 前端开发
    if echo "$desc" | grep -qiE "前端|frontend|react|vue|ui|组件|页面|component|界面"; then
        echo "frontend_development"
        return
    fi

    # 全栈开发
    if echo "$desc" | grep -qiE "全栈|fullstack|完整功能|前后端|full-stack"; then
        echo "fullstack_development"
        return
    fi

    # 性能优化
    if echo "$desc" | grep -qiE "性能|优化|performance|速度|缓存|optimize|cache"; then
        echo "performance_optimization"
        return
    fi

    # 测试
    if echo "$desc" | grep -qiE "测试|test|spec|jest|mocha|pytest|unit|e2e|integration"; then
        echo "testing"
        return
    fi

    echo "general"
}

# 获取任务类型
TASK_TYPE=$(detect_task_type "$TASK_DESC")

# 定义必需的Agent组合
get_required_agents() {
    case "$1" in
        authentication)
            echo "backend-architect security-auditor test-engineer api-designer database-specialist"
            ;;
        api_development)
            echo "api-designer backend-architect test-engineer technical-writer"
            ;;
        database_design)
            echo "database-specialist backend-architect performance-engineer"
            ;;
        frontend_development)
            echo "frontend-specialist ux-designer test-engineer"
            ;;
        fullstack_development)
            echo "fullstack-engineer database-specialist test-engineer devops-engineer"
            ;;
        performance_optimization)
            echo "performance-engineer backend-architect monitoring-specialist"
            ;;
        testing)
            echo "test-engineer e2e-test-specialist performance-tester"
            ;;
        general)
            echo ""  # 通用任务至少3个agent即可
            ;;
    esac
}

# 验证Agent数量
if [ "$AGENT_COUNT" -eq 0 ]; then
    # 不是Task调用，直接放行
    echo "$INPUT"
    exit 0
fi

if [ "$AGENT_COUNT" -lt 3 ]; then
    echo "❌ Claude Enhancer 规则违反：Agent数量不足" >&2
    echo "" >&2
    echo "📊 当前状态：" >&2
    echo "  • 使用了 $AGENT_COUNT 个Agent" >&2
    echo "  • 最少需要 3 个Agent" >&2
    echo "  • 任务类型：$TASK_TYPE" >&2
    echo "" >&2
    echo "✅ 正确做法：" >&2

    REQUIRED_AGENTS=$(get_required_agents "$TASK_TYPE")
    if [ -n "$REQUIRED_AGENTS" ]; then
        echo "  对于 $TASK_TYPE 任务，必须使用：" >&2
        echo "  $REQUIRED_AGENTS" | tr ' ' '\n' | sed 's/^/    - /' >&2
    else
        echo "  至少选择3个相关的Agent并行执行" >&2
    fi

    echo "" >&2
    echo "💡 请重新设计方案，确保使用足够的Agent" >&2
    exit 1
fi

# 验证特定任务类型的Agent组合
if [ "$TASK_TYPE" != "general" ]; then
    REQUIRED_AGENTS=$(get_required_agents "$TASK_TYPE")
    if [ -n "$REQUIRED_AGENTS" ]; then
        MISSING_AGENTS=""
        for agent in $REQUIRED_AGENTS; do
            if ! echo "$AGENTS" | grep -q "^$agent$"; then
                MISSING_AGENTS="$MISSING_AGENTS $agent"
            fi
        done

        if [ -n "$MISSING_AGENTS" ]; then
            echo "⚠️ Claude Enhancer 规则提醒：Agent组合不完整" >&2
            echo "" >&2
            echo "📊 任务类型：$TASK_TYPE" >&2
            echo "" >&2
            echo "🔍 当前使用的Agents：" >&2
            echo "$AGENTS" | sed 's/^/    ✓ /' >&2
            echo "" >&2
            echo "❌ 缺少必需的Agents：" >&2
            echo "$MISSING_AGENTS" | tr ' ' '\n' | grep -v '^$' | sed 's/^/    ✗ /' >&2
            echo "" >&2
            echo "💡 建议：添加缺少的Agents以获得更好的结果" >&2
            echo "" >&2
            echo "📝 注意：这是建议而非强制，但强烈推荐使用完整组合" >&2
        fi
    fi
fi

# 检查是否并行执行（通过检查是否在同一个function_calls块中）
if echo "$INPUT" | grep -q "function_calls" && [ "$AGENT_COUNT" -gt 1 ]; then
    # 计算Task调用之间的距离（简单检查）
    TASK_POSITIONS=$(echo "$INPUT" | grep -n "Task" | cut -d: -f1)
    if [ -n "$TASK_POSITIONS" ]; then
        FIRST=$(echo "$TASK_POSITIONS" | head -1)
        LAST=$(echo "$TASK_POSITIONS" | tail -1)
        DISTANCE=$((LAST - FIRST))

        # 如果Task调用相距太远（超过50行），可能不是并行
        if [ "$DISTANCE" -gt 50 ] && [ "$AGENT_COUNT" -gt 1 ]; then
            echo "⚠️ Claude Enhancer 提醒：请确保所有Agent在同一个function_calls块中并行执行" >&2
        fi
    fi
fi

# 记录执行日志
LOG_FILE="/tmp/claude_enhancer_agent_log.txt"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Task: $TASK_TYPE, Agents: $AGENT_COUNT, List: $(echo $AGENTS | tr '\n' ' ')" >> "$LOG_FILE"

# 验证通过，输出原始内容
echo "$INPUT"
exit 0