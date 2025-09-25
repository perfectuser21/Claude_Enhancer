#!/bin/bash

# 清理嵌套的备份目录
PROJECT_ROOT="/home/xx/dev/Claude_Enhancer"

echo "🧹 清理嵌套备份目录..."

# 查找所有docs_backup目录
find "$PROJECT_ROOT" -name "docs_backup_*" -type d | while read -r backup_dir; do
    echo "删除备份目录: $backup_dir"
    rm -rf "$backup_dir"
done

echo "✅ 嵌套备份清理完成"

# 统计剩余的Claude Enhancer引用（排除git和备份）
claude-enhancer_count=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
echo "📊 剩余 Claude Enhancer 引用: $claude-enhancer_count 处"