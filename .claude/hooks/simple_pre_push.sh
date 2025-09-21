#!/bin/bash
# 简单的pre-push hook - 推送前的最后检查

echo "🚀 推送前检查..."

# 1. 运行测试（如果有测试命令）
if [ -f "package.json" ] && grep -q '"test"' package.json; then
    echo "  运行测试..."
    npm test || {
        echo "❌ 测试失败，请修复后再推送"
        exit 1
    }
elif [ -f "pytest.ini" ] || [ -f "setup.py" ]; then
    echo "  运行Python测试..."
    if command -v pytest >/dev/null 2>&1; then
        pytest --quiet || {
            echo "❌ 测试失败，请修复后再推送"
            exit 1
        }
    fi
fi

# 2. 检查是否有未完成的TODO
TODO_COUNT=$(git diff HEAD origin/$(git rev-parse --abbrev-ref HEAD) 2>/dev/null | grep -c "^+.*TODO" || echo 0)
if [ "$TODO_COUNT" -gt 0 ]; then
    echo "⚠️  发现 $TODO_COUNT 个新的TODO标记"
    echo "确认要推送？(y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
fi

# 3. 检查是否推送到主分支
current_branch=$(git rev-parse --abbrev-ref HEAD)
protected_branches="main master"
for branch in $protected_branches; do
    if [[ "$current_branch" == "$branch" ]]; then
        echo "⚠️  警告：正在推送到保护分支 '$branch'"
        echo "确认要推送？(y/n)"
        read -r response
        if [[ "$response" != "y" ]]; then
            exit 1
        fi
    fi
done

echo "✅ 推送检查通过"
exit 0