#!/bin/bash
# 紧急修复：如果发现Perfect21，运行此脚本

echo "🔍 紧急搜索Perfect21..."
echo ""

# 显示所有包含Perfect21的文件
echo "📋 找到的Perfect21引用："
grep -r "Perfect21" . \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=venv \
    --exclude-dir=.venv \
    --exclude="*.pyc" \
    --exclude="emergency_fix_perfect21.sh" 2>/dev/null | while read line; do

    echo "  $line"

    # 提取文件名
    file=$(echo "$line" | cut -d: -f1)

    # 自动替换
    if [[ -f "$file" ]]; then
        sed -i 's/Perfect21/Claude Enhancer/g' "$file" 2>/dev/null
        echo "    ✅ 已修复: $file"
    fi
done

echo ""
echo "🎯 修复完成！"
echo ""

# 再次验证
remaining=$(grep -r "Perfect21" . \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude="emergency_fix_perfect21.sh" 2>/dev/null | wc -l)

if [ $remaining -eq 0 ]; then
    echo "✅ 所有Perfect21已清除！"
else
    echo "⚠️  还有 $remaining 个Perfect21引用"
    echo "请运行: grep -r 'Perfect21' . --exclude-dir=.git"
fi