#!/bin/bash
# 彻底移除所有Claude Enhancer引用，替换为Claude Enhancer

echo "🔄 开始彻底移除Claude Enhancer..."
echo ""

# 创建替换日志
LOG_FILE="claude-enhancer_removal_log_$(date +%Y%m%d_%H%M%S).txt"

# 统计原始数量
echo "📊 统计原始Claude Enhancer引用..."
ORIGINAL_COUNT=$(grep -r "Claude Enhancer" . --exclude-dir=.git --exclude-dir=node_modules 2>/dev/null | wc -l)
echo "发现 $ORIGINAL_COUNT 个Claude Enhancer引用"
echo ""

# 1. 批量替换文件内容
echo "📝 第1步：替换文件内容中的Claude Enhancer..."
find . -type f \( \
    -name "*.md" -o \
    -name "*.sh" -o \
    -name "*.py" -o \
    -name "*.json" -o \
    -name "*.yaml" -o \
    -name "*.yml" -o \
    -name "*.txt" -o \
    -name "*.js" -o \
    -name "*.ts" \
    \) \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -not -path "./venv/*" \
    -not -path "./*backup*/*" | while read file; do

    if grep -q "Claude Enhancer" "$file" 2>/dev/null; then
        echo "  处理: $file" | tee -a "$LOG_FILE"

        # 替换各种形式的Claude Enhancer
        sed -i 's/Claude Enhancer/Claude Enhancer/g' "$file"
        sed -i 's/claude-enhancer/claude-enhancer/g' "$file"
        sed -i 's/CLAUDE_ENHANCER/CLAUDE_ENHANCER/g' "$file"

        # 特殊路径替换
        sed -i 's|/home/xx/dev/Claude Enhancer|/home/xx/dev/Claude_Enhancer|g' "$file"
    fi
done

echo ""
echo "📝 第2步：重命名包含Claude Enhancer的文件..."
# 查找并重命名包含Claude Enhancer的文件名
find . -type f -name "*Claude Enhancer*" -o -name "*claude-enhancer*" | while read file; do
    if [ -f "$file" ]; then
        # 计算新文件名
        newname=$(echo "$file" | sed 's/Claude Enhancer/Claude_Enhancer/g' | sed 's/claude-enhancer/claude_enhancer/g')

        # 如果新文件名不同，则重命名
        if [ "$file" != "$newname" ]; then
            echo "  重命名: $file → $newname" | tee -a "$LOG_FILE"
            mv "$file" "$newname" 2>/dev/null || true
        fi
    fi
done

echo ""
echo "📝 第3步：清理备份文件..."
# 清理所有备份文件
find . -type f \( \
    -name "*.backup.claude-enhancer" -o \
    -name "*.bak.claude-enhancer" -o \
    -name "*.claude-enhancer.bak" -o \
    -name "*claude-enhancer*.backup" \
    \) -exec rm -f {} \; 2>/dev/null

# 清理包含claude-enhancer的备份目录
find . -type d -name "*claude-enhancer*backup*" -exec rm -rf {} \; 2>/dev/null || true

echo ""
echo "📝 第4步：更新Git Hooks中的引用..."
# 特别处理Git hooks
for hook in .git/hooks/*; do
    if [ -f "$hook" ] && grep -q "Claude Enhancer\|claude-enhancer" "$hook" 2>/dev/null; then
        echo "  更新Git Hook: $(basename $hook)" | tee -a "$LOG_FILE"
        sed -i 's/Claude Enhancer/Claude Enhancer/g' "$hook"
        sed -i 's/claude-enhancer/claude-enhancer/g' "$hook"
    fi
done

echo ""
echo "✅ 验证结果..."
# 验证是否还有Claude Enhancer引用
REMAINING_COUNT=$(grep -r "Claude Enhancer\|claude-enhancer" . \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude="$LOG_FILE" \
    --exclude="complete_removal_claude-enhancer.sh" 2>/dev/null | wc -l)

echo ""
echo "═══════════════════════════════════════════"
echo "📊 最终统计："
echo "  - 原始Claude Enhancer引用: $ORIGINAL_COUNT"
echo "  - 剩余Claude Enhancer引用: $REMAINING_COUNT"
echo "  - 成功移除: $((ORIGINAL_COUNT - REMAINING_COUNT))"
echo "═══════════════════════════════════════════"

if [ $REMAINING_COUNT -eq 0 ]; then
    echo ""
    echo "🎉 成功！Claude Enhancer已被彻底移除！"
    echo "   项目现在完全使用Claude Enhancer品牌"
else
    echo ""
    echo "⚠️  还有 $REMAINING_COUNT 个引用需要手动处理"
    echo "   运行以下命令查看详情："
    echo "   grep -r 'Claude Enhancer\|claude-enhancer' . --exclude-dir=.git --exclude-dir=node_modules"
fi

echo ""
echo "📝 详细日志保存在: $LOG_FILE"

# 删除此脚本自身
echo ""
echo "🗑️  删除此移除脚本..."
rm -f "$0"