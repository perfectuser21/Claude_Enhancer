#!/bin/bash
# Claude Enhancer 动态任务分析器
# 框架固定，内容灵活

set -e

# 读取输入
INPUT=$(cat)

# 提取任务描述
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
if [ -z "$TASK_DESC" ]; then
    TASK_DESC=$(echo "$INPUT" | grep -oP '"description"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
fi

if [ -n "$TASK_DESC" ]; then
    # 动态分析任务需要什么能力
    echo "📊 Claude Enhancer 动态任务分析" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2
    echo "🎯 任务内容: $(echo "$TASK_DESC" | head -c 100)..." >&2
    echo "" >&2
    echo "🔄 框架步骤（固定）:" >&2
    echo "  1. 需求分析阶段" >&2
    echo "  2. 设计规划阶段" >&2
    echo "  3. 实现开发阶段" >&2
    echo "  4. 测试验证阶段" >&2
    echo "  5. 文档交付阶段" >&2
    echo "" >&2
    echo "💡 内容建议（灵活）:" >&2

    # 根据任务内容动态建议
    echo "$TASK_DESC" | {
        # 动态分析需要的能力
        NEEDS_API=false
        NEEDS_DB=false
        NEEDS_SECURITY=false
        NEEDS_FRONTEND=false
        NEEDS_PERFORMANCE=false

        # 智能识别需求（不是固定映射）
        grep -qi "api\|接口\|endpoint\|rest" && NEEDS_API=true
        grep -qi "数据\|存储\|database\|sql" && NEEDS_DB=true
        grep -qi "安全\|加密\|auth\|认证" && NEEDS_SECURITY=true
        grep -qi "页面\|界面\|frontend\|ui" && NEEDS_FRONTEND=true
        grep -qi "性能\|优化\|速度\|快" && NEEDS_PERFORMANCE=true

        echo "  根据你的需求，建议考虑：" >&2
        [ "$NEEDS_API" = true ] && echo "    • API设计和规范" >&2
        [ "$NEEDS_DB" = true ] && echo "    • 数据模型设计" >&2
        [ "$NEEDS_SECURITY" = true ] && echo "    • 安全架构设计" >&2
        [ "$NEEDS_FRONTEND" = true ] && echo "    • 用户体验设计" >&2
        [ "$NEEDS_PERFORMANCE" = true ] && echo "    • 性能基准测试" >&2

        # 不强制特定Agent，只是建议
        echo "" >&2
        echo "  这只是建议，实际Agent选择由你决定" >&2
    }

    echo "" >&2
    echo "═══════════════════════════════════════════" >&2
fi

# 输出原始内容
echo "$INPUT"
exit 0