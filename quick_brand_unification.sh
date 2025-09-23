#!/bin/bash

# =============================================================================
# 快速品牌统一脚本 - 直接执行主要替换
# =============================================================================

set -e

PROJECT_ROOT="/home/xx/dev/Perfect21"

echo "🚀 开始 Claude Enhancer 品牌统一..."

# 统计执行前状态
claude_enhancer_before=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git --exclude-dir=docs_backup_* 2>/dev/null | wc -l)
perfect21_before=$(grep -r "Perfect21" "$PROJECT_ROOT" --exclude-dir=.git --exclude-dir=docs_backup_* 2>/dev/null | wc -l)
perfect21_lower_before=$(grep -r "perfect21" "$PROJECT_ROOT" --exclude-dir=.git --exclude-dir=docs_backup_* 2>/dev/null | wc -l)

echo "📊 执行前统计:"
echo "  - Claude Enhancer: $claude_enhancer_before"
echo "  - Perfect21: $perfect21_before"
echo "  - perfect21: $perfect21_lower_before"

echo "🔄 执行品牌替换..."

# 1. 替换 Perfect21 为 Claude Enhancer（排除备份目录）
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -not -path "*/docs_backup_*" \
    -not -path "*backup*" \
    -exec sed -i 's/Perfect21/Claude Enhancer/g' {} \; 2>/dev/null

# 2. 替换 perfect21 为 claude-enhancer
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -not -path "*/docs_backup_*" \
    -not -path "*backup*" \
    -exec sed -i 's/perfect21/claude-enhancer/g' {} \; 2>/dev/null

# 3. 修复目录路径引用（保持 Perfect21 作为目录名）
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -not -path "*/docs_backup_*" \
    -not -path "*backup*" \
    -exec sed -i 's|/home/xx/dev/Claude Enhancer|/home/xx/dev/Perfect21|g' {} \; 2>/dev/null

# 4. 特殊域名和容器名替换
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -not -path "*/docs_backup_*" \
    -not -path "*backup*" \
    -exec sed -i 's/claude-enhancer\.com/claude-enhancer.dev/g' {} \; 2>/dev/null

echo "✅ 品牌替换完成"

# 统计执行后状态
claude_enhancer_after=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git --exclude-dir=docs_backup_* 2>/dev/null | wc -l)
perfect21_after=$(grep -r "Perfect21" "$PROJECT_ROOT" --exclude-dir=.git --exclude-dir=docs_backup_* 2>/dev/null | wc -l)
perfect21_lower_after=$(grep -r "perfect21" "$PROJECT_ROOT" --exclude-dir=.git --exclude-dir=docs_backup_* 2>/dev/null | wc -l)

echo "📊 执行后统计:"
echo "  - Claude Enhancer: $claude_enhancer_after (+$((claude_enhancer_after - claude_enhancer_before)))"
echo "  - Perfect21: $perfect21_after (-$((perfect21_before - perfect21_after)))"
echo "  - perfect21: $perfect21_lower_after (-$((perfect21_lower_before - perfect21_lower_after)))"

# 显示剩余的Perfect21引用（如果有的话）
if [ "$perfect21_after" -gt 0 ] || [ "$perfect21_lower_after" -gt 0 ]; then
    echo ""
    echo "⚠️  剩余引用需要手动检查:"
    if [ "$perfect21_after" -gt 0 ]; then
        echo "Perfect21 剩余 ($perfect21_after 处):"
        grep -r "Perfect21" "$PROJECT_ROOT" --exclude-dir=.git --exclude-dir=docs_backup_* 2>/dev/null | head -5
    fi
    if [ "$perfect21_lower_after" -gt 0 ]; then
        echo "perfect21 剩余 ($perfect21_lower_after 处):"
        grep -r "perfect21" "$PROJECT_ROOT" --exclude-dir=.git --exclude-dir=docs_backup_* 2>/dev/null | head -5
    fi
else
    echo "🎉 品牌统一完全成功！"
fi

echo "✅ Claude Enhancer 品牌统一完成"