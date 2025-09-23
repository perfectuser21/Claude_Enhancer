#!/bin/bash

# 清理嵌套的备份目录
PROJECT_ROOT="/home/xx/dev/Perfect21"

echo "🧹 清理嵌套备份目录..."

# 查找所有docs_backup目录
find "$PROJECT_ROOT" -name "docs_backup_*" -type d | while read -r backup_dir; do
    echo "删除备份目录: $backup_dir"
    rm -rf "$backup_dir"
done

echo "✅ 嵌套备份清理完成"

# 统计剩余的Perfect21引用（排除git和备份）
perfect21_count=$(grep -r "Perfect21" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
echo "📊 剩余 Perfect21 引用: $perfect21_count 处"