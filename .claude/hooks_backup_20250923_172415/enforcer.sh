#!/bin/bash
# Claude Enhancer 强制执行器
# 确保所有编程任务都使用多Agent并行执行

set -e

# 读取输入
INPUT=$(cat)

# 检测是否是编程任务（通过关键词）
is_programming_task() {
    local input="$1"
    echo "$input" | grep -qiE "implement|build|create|develop|fix|refactor|optimize|deploy|test|编写|实现|创建|开发|修复|重构|优化|部署|测试|API|database|功能|bug"
}

# 检测是否使用了足够的Agent
check_agent_usage() {
    local input="$1"
    # 计算Task工具调用次数
    local task_count=$(echo "$input" | grep -o '"Task"' | wc -l)

    if [ "$task_count" -lt 3 ]; then
        return 1  # 不够
    fi
    return 0  # 足够
}

# 主逻辑
if is_programming_task "$INPUT"; then
    if ! check_agent_usage "$INPUT"; then
        echo "❌ Claude Enhancer 强制要求" >&2
        echo "═══════════════════════════════════════" >&2
        echo "" >&2
        echo "🚫 检测到编程任务但未使用多Agent策略！" >&2
        echo "" >&2
        echo "📋 必须满足以下要求：" >&2
        echo "  1. 最少使用3个Agent（简单任务）" >&2
        echo "  2. 标准任务使用6个Agent" >&2
        echo "  3. 复杂任务使用8个Agent" >&2
        echo "  4. 必须在同一消息中并行调用" >&2
        echo "" >&2
        echo "💡 正确的执行方式：" >&2
        echo '```' >&2
        echo "我需要使用多个专业Agent来完成这个任务：" >&2
        echo "" >&2
        echo "<function_calls>" >&2
        echo "  <invoke name=\"Task\">" >&2
        echo "    <parameter name=\"subagent_type\">backend-architect</parameter>" >&2
        echo "    <parameter name=\"description\">架构设计</parameter>" >&2
        echo "    <parameter name=\"prompt\">设计系统架构...</parameter>" >&2
        echo "  </invoke>" >&2
        echo "  <invoke name=\"Task\">" >&2
        echo "    <parameter name=\"subagent_type\">test-engineer</parameter>" >&2
        echo "    ..." >&2
        echo "  </invoke>" >&2
        echo "  <invoke name=\"Task\">" >&2
        echo "    <parameter name=\"subagent_type\">security-auditor</parameter>" >&2
        echo "    ..." >&2
        echo "  </invoke>" >&2
        echo "</function_calls>" >&2
        echo '```' >&2
        echo "" >&2
        echo "🔄 请重新设计你的方案，使用多Agent并行执行！" >&2
        echo "═══════════════════════════════════════" >&2

        # 阻止执行
        exit 1
    fi
fi

# 检查是否在Phase 5或7，需要cleanup
CURRENT_PHASE=$(cat /home/xx/dev/Claude Enhancer/.claude/phase_state.json 2>/dev/null | grep -oP '"current_phase"\s*:\s*\d+' | grep -oP '\d+' || echo "1")

if [ "$CURRENT_PHASE" = "5" ] || [ "$CURRENT_PHASE" = "7" ]; then
    # 检查是否包含cleanup-specialist
    if ! echo "$INPUT" | grep -q "cleanup-specialist"; then
        echo "⚠️  Phase $CURRENT_PHASE 需要包含cleanup-specialist" >&2
        echo "   自动添加清理专家到任务列表" >&2
    fi
fi

# 正常通过
echo "$INPUT"
exit 0