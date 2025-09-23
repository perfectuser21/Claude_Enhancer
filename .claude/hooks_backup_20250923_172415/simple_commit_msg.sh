#!/bin/bash
# 简单的commit-msg hook - 确保有意义的提交信息

commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|build|ci): .{3,}'
commit_msg=$(cat "$1")

# 检查提交信息格式
if ! echo "$commit_msg" | grep -qE "$commit_regex"; then
    echo "❌ 提交信息格式不正确"
    echo ""
    echo "正确格式: <type>: <description>"
    echo ""
    echo "类型:"
    echo "  feat:     新功能"
    echo "  fix:      修复bug"
    echo "  docs:     文档更新"
    echo "  style:    代码格式"
    echo "  refactor: 重构"
    echo "  test:     测试"
    echo "  chore:    其他修改"
    echo "  perf:     性能优化"
    echo ""
    echo "例子: feat: 添加用户登录功能"
    exit 1
fi

# 检查是否太短
if [ ${#commit_msg} -lt 10 ]; then
    echo "❌ 提交信息太短，请详细描述改动"
    exit 1
fi

echo "✅ 提交信息检查通过"
exit 0