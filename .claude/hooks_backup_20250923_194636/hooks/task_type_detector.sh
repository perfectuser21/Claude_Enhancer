#!/bin/bash
# Perfect21 任务类型检测器
# 在用户输入后立即分析并提醒正确的工作流程

set -e

# 获取用户输入（从stdin或参数）
if [ -n "$1" ]; then
    USER_INPUT="$1"
else
    USER_INPUT=$(cat)
fi

# 转换为小写便于匹配
INPUT_LOWER=$(echo "$USER_INPUT" | tr '[:upper:]' '[:lower:]')

# 开发任务关键词
DEV_KEYWORDS="压力测试|性能|优化|重构|新功能|架构|设计|实现|开发|测试|debug|修复|feature|implement|refactor|optimize|test|benchmark"

# 检测是否是开发任务
if echo "$INPUT_LOWER" | grep -qE "$DEV_KEYWORDS"; then
    echo "╔═══════════════════════════════════════════════════╗" >&2
    echo "║     🎯 Perfect21 智能工作流引导系统 🎯           ║" >&2
    echo "╚═══════════════════════════════════════════════════╝" >&2
    echo "" >&2
    echo "📝 任务分析：检测到【开发任务】" >&2
    echo "" >&2

    # 判断任务复杂度
    if echo "$INPUT_LOWER" | grep -qE "压力测试|性能优化|架构|重构|全栈"; then
        echo "📊 复杂度评估：🔴 复杂任务（需要6-8个Agent）" >&2
        echo "" >&2
        echo "🤖 必需的Agent组合：" >&2
        echo "   1️⃣ performance-engineer - 性能分析专家" >&2
        echo "   2️⃣ test-engineer - 测试方案设计" >&2
        echo "   3️⃣ backend-architect - 系统架构设计" >&2
        echo "   4️⃣ monitoring-specialist - 监控与观测" >&2
        echo "   5️⃣ devops-engineer - 部署与优化" >&2
        echo "   6️⃣ security-auditor - 安全审计" >&2
        echo "   7️⃣ code-reviewer - 代码质量审查" >&2
        echo "   8️⃣ technical-writer - 技术文档" >&2
    else
        echo "📊 复杂度评估：🟡 标准任务（需要4-6个Agent）" >&2
        echo "" >&2
        echo "🤖 推荐Agent组合：" >&2
        echo "   1️⃣ backend-architect - 方案设计" >&2
        echo "   2️⃣ backend-engineer - 功能实现" >&2
        echo "   3️⃣ test-engineer - 测试保证" >&2
        echo "   4️⃣ code-reviewer - 代码审查" >&2
    fi

    echo "" >&2
    echo "📋 强制执行的8-Phase工作流：" >&2
    echo "   Phase 0: 创建分支 → git checkout -b feature/xxx" >&2
    echo "   Phase 1: 需求分析 → 使用Task调用分析Agent" >&2
    echo "   Phase 2: 设计规划 → 使用Task调用设计Agent" >&2
    echo "   Phase 3: 并行开发 → 【关键】多Agent并行实现" >&2
    echo "   Phase 4: 本地测试 → 运行测试套件" >&2
    echo "   Phase 5: 代码提交 → git commit（触发hooks）" >&2
    echo "   Phase 6: 代码审查 → 创建PR" >&2
    echo "   Phase 7: 合并部署 → 完成任务" >&2
    echo "" >&2
    echo "⚠️  重要提醒：" >&2
    echo "   • 不要直接写代码！使用Task工具调用Agent" >&2
    echo "   • 所有Agent必须在同一个function_calls块中并行调用" >&2
    echo "   • 这是Perfect21的核心要求，不是可选项" >&2
    echo "" >&2
    echo "💡 正确的第一步：" >&2
    echo '   使用Task工具：Task(subagent_type="...", prompt="...")' >&2
    echo "═══════════════════════════════════════════════════" >&2

    # 记录任务检测
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Detected dev task: ${USER_INPUT:0:100}" >> /tmp/perfect21_tasks.log
fi

# 检查是否需要清理
if echo "$INPUT_LOWER" | grep -qE "清理|cleanup|clean|整理|organize"; then
    echo "🧹 检测到清理需求 - 建议使用cleanup-specialist Agent" >&2
fi

# 输出原始内容
echo "$USER_INPUT"
exit 0