#!/bin/bash
# P5阶段提交质量门
echo "ℹ️ Commit quality gate active"

# 提交前检查清单
echo "💡 提交前检查:"
echo "  - [ ] 代码已格式化"
echo "  - [ ] 测试全部通过"
echo "  - [ ] 无console.log/print调试"
echo "  - [ ] commit message符合规范"

# 检查commit message规范
if [ -d ".git" ]; then
    last_msg=$(git log -1 --pretty=%B 2>/dev/null | head -1)
    if [[ $last_msg =~ ^(feat|fix|docs|style|refactor|test|chore): ]]; then
        echo "  ✅ 最近提交符合规范"
    else
        echo "  ⚠️ 提交信息应以feat/fix/docs等前缀开头"
    fi
fi

# 建议的提交格式
echo "  建议格式:"
echo "    feat: 新功能"
echo "    fix: 修复bug"
echo "    docs: 文档更新"
