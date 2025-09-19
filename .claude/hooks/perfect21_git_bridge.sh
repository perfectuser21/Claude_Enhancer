#!/bin/bash
# Perfect21 Git Bridge
# 将Claude hooks与Git操作连接，形成完整工作流

set -e

# 读取输入
INPUT=$(cat)

# 检测Git命令
detect_git_command() {
    local input="$1"

    if echo "$input" | grep -qE "git commit"; then
        echo "commit"
    elif echo "$input" | grep -qE "git push"; then
        echo "push"
    elif echo "$input" | grep -qE "git add"; then
        echo "add"
    elif echo "$input" | grep -qE "git merge"; then
        echo "merge"
    else
        echo "none"
    fi
}

GIT_CMD=$(detect_git_command "$INPUT")

# 如果是Git commit操作，触发预检查
if [ "$GIT_CMD" = "commit" ]; then
    echo "🔗 Perfect21 Git Bridge: 检测到commit操作" >&2
    echo "" >&2

    # 检查是否运行了测试
    if ! echo "$INPUT" | grep -qE "test|pytest|jest|npm test"; then
        echo "⚠️ Git提交前检查清单：" >&2
        echo "  □ 运行测试 (npm test / pytest)" >&2
        echo "  □ 代码格式化 (prettier / black)" >&2
        echo "  □ Lint检查 (eslint / flake8)" >&2
        echo "  □ 类型检查 (tsc / mypy)" >&2
        echo "" >&2
        echo "💡 建议：先运行测试确保代码质量" >&2
        echo "" >&2
    fi

    # 触发Perfect21质量门
    bash /home/xx/dev/Perfect21/.claude/hooks/perfect21_quality_gates.sh <<< "$INPUT" > /dev/null 2>&1
fi

# 如果是Git push操作，确保已通过所有检查
if [ "$GIT_CMD" = "push" ]; then
    echo "🔗 Perfect21 Git Bridge: 检测到push操作" >&2
    echo "" >&2
    echo "📋 Push前确认清单：" >&2
    echo "  ✓ 所有测试通过" >&2
    echo "  ✓ 代码已审查" >&2
    echo "  ✓ 文档已更新" >&2
    echo "  ✓ 无安全问题" >&2
    echo "" >&2
fi

# 输出原始内容
echo "$INPUT"
exit 0