#!/bin/bash
# Validate minimum agent count

# Extract agent count from Task invocations
AGENT_COUNT=$(echo "$@" | grep -o "Task" | wc -l)

if [ "$AGENT_COUNT" -lt "${MIN_AGENTS:-3}" ]; then
    echo "❌ BLOCKED: 工作流要求最少3个Agent！" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    echo "当前Agent数量: $AGENT_COUNT" >&2
    echo "最低要求: ${MIN_AGENTS:-3}" >&2
    echo "" >&2
    echo "必须使用至少3个Agent并行执行：" >&2
    echo "" >&2
    echo "示例组合：" >&2
    echo "  - backend-architect: 系统设计" >&2
    echo "  - frontend-specialist: UI开发" >&2
    echo "  - test-engineer: 测试保证" >&2
    echo "" >&2
    echo "或根据任务类型选择：" >&2
    echo "  API开发: api-designer + backend-architect + test-engineer" >&2
    echo "  Web应用: frontend-specialist + backend-architect + database-specialist" >&2
    echo "  AI项目: ai-engineer + data-scientist + mlops-engineer" >&2
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
    exit 2  # 强制阻止执行
fi

exit 0  # 通过验证