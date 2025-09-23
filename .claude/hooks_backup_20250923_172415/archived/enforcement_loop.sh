#!/bin/bash
# Claude Enhancer Enforcement Loop - 强制循环直到符合标准
# 不是阻止执行，而是强制Claude Code重试直到满足要求

set -e

# 状态文件
STATE_FILE="/tmp/claude_enhancer_retry_state.json"
LOG_FILE="/tmp/claude_enhancer_enforcement.log"

# 读取输入
INPUT=$(cat)

# 初始化或读取重试状态
if [ -f "$STATE_FILE" ]; then
    RETRY_COUNT=$(cat "$STATE_FILE" | grep -oP '"retry_count":\s*\d+' | grep -oP '\d+' || echo 0)
    LAST_TASK=$(cat "$STATE_FILE" | grep -oP '"last_task":\s*"[^"]+' | cut -d'"' -f4 || echo "")
else
    RETRY_COUNT=0
    LAST_TASK=""
fi

# 提取当前任务信息
CURRENT_TASK=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 || echo "unknown")
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u || true)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . 2>/dev/null || echo 0)

# 检测任务类型
detect_task_type() {
    local desc="$1"

    if echo "$desc" | grep -qiE "认证|登录|用户|auth|login|jwt|password|security|身份|验证"; then
        echo "authentication"
        return
    fi

    if echo "$desc" | grep -qiE "api|接口|rest|graphql|endpoint|route|swagger|服务"; then
        echo "api_development"
        return
    fi

    if echo "$desc" | grep -qiE "数据库|database|表|table|schema|sql|postgres|mysql"; then
        echo "database_design"
        return
    fi

    if echo "$desc" | grep -qiE "前端|界面|页面|组件|frontend|ui|react|vue|angular"; then
        echo "frontend_development"
        return
    fi

    if echo "$desc" | grep -qiE "测试|test|单元|集成|e2e|性能|quality"; then
        echo "testing"
        return
    fi

    echo "general"
}

# 获取任务类型
TASK_TYPE=$(detect_task_type "$CURRENT_TASK")

# 定义每种任务的要求
get_requirements() {
    case "$1" in
        authentication)
            echo "5:backend-architect security-auditor api-designer database-specialist test-engineer"
            ;;
        api_development)
            echo "4:api-designer backend-architect test-engineer technical-writer"
            ;;
        database_design)
            echo "3:database-specialist backend-architect performance-engineer"
            ;;
        frontend_development)
            echo "4:frontend-specialist react-pro ux-designer test-engineer"
            ;;
        testing)
            echo "4:test-engineer performance-tester security-auditor code-reviewer"
            ;;
        *)
            echo "3:backend-architect test-engineer technical-writer"
            ;;
    esac
}

# 获取要求
REQUIREMENTS=$(get_requirements "$TASK_TYPE")
REQUIRED_COUNT=$(echo "$REQUIREMENTS" | cut -d: -f1)
REQUIRED_AGENTS=$(echo "$REQUIREMENTS" | cut -d: -f2)

# 检查是否是同一个任务的重试
if [ "$CURRENT_TASK" != "$LAST_TASK" ]; then
    RETRY_COUNT=0
fi

# 记录日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Task: $TASK_TYPE | Agents: $AGENT_COUNT/$REQUIRED_COUNT | Retry: $RETRY_COUNT" >> "$LOG_FILE"

# 检查是否符合要求
if [ "$AGENT_COUNT" -lt "$REQUIRED_COUNT" ]; then
    # 更新重试计数
    RETRY_COUNT=$((RETRY_COUNT + 1))

    # 保存状态
    echo "{\"retry_count\": $RETRY_COUNT, \"last_task\": \"$CURRENT_TASK\"}" > "$STATE_FILE"

    # 检查重试限制
    if [ $RETRY_COUNT -ge 3 ]; then
        echo "🔴 CLAUDE_ENHANCER_MAX_RETRIES_EXCEEDED" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "已尝试 $RETRY_COUNT 次但仍未满足要求" >&2
        echo "任务类型: $TASK_TYPE" >&2
        echo "需要 $REQUIRED_COUNT 个agents，当前只有 $AGENT_COUNT 个" >&2
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
        echo "请手动介入或调整要求" >&2

        # 清除状态
        rm -f "$STATE_FILE"

        # 仍然返回成功，不阻止执行（因为不能阻止）
        exit 0
    fi

    # 构造缺失的agents列表
    MISSING_AGENTS=""
    for agent in $REQUIRED_AGENTS; do
        if ! echo "$AGENTS" | grep -q "$agent"; then
            MISSING_AGENTS="$MISSING_AGENTS $agent"
        fi
    done

    # 返回强制重试指令
    echo "🔴 CLAUDE_ENHANCER_MANDATORY_RETRY" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "STATUS: VIOLATION_MUST_RETRY" >&2
    echo "RETRY_NUMBER: $RETRY_COUNT/3" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "TASK_TYPE: $TASK_TYPE" >&2
    echo "CURRENT_AGENTS: $AGENT_COUNT ($AGENTS)" >&2
    echo "REQUIRED_AGENTS: $REQUIRED_COUNT" >&2
    echo "MISSING_AGENTS: $MISSING_AGENTS" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "MANDATORY_ACTION: You MUST retry with ALL these agents in ONE function_calls block:" >&2
    echo "" >&2

    # 生成完整的调用示例
    echo "<function_calls>" >&2
    for agent in $REQUIRED_AGENTS; do
        echo "  <invoke name=\"Task\">" >&2
        echo "    <parameter name=\"description\">...</parameter>" >&2
        echo "    <parameter name=\"prompt\">...</parameter>" >&2
        echo "    <parameter name=\"subagent_type\">$agent</parameter>" >&2
        echo "  </invoke>" >&2
    done
    echo "</function_calls>" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "This is retry $RETRY_COUNT of 3. Compliance is mandatory." >&2

else
    # 符合要求，清除重试状态
    if [ -f "$STATE_FILE" ]; then
        rm -f "$STATE_FILE"
    fi

    echo "✅ CLAUDE_ENHANCER_COMPLIANCE_VERIFIED" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "Task Type: $TASK_TYPE" >&2
    echo "Agents Used: $AGENT_COUNT ($AGENTS)" >&2
    echo "Status: APPROVED - Meets Claude Enhancer Standards" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2

    if [ $RETRY_COUNT -gt 0 ]; then
        echo "Good job! Succeeded after $RETRY_COUNT retry(ies)" >&2
    fi
fi

# 总是返回0（因为exit 2不工作）
exit 0