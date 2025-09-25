#!/bin/bash
# 紧急修复：如果发现Claude Enhancer 5.0，运行此脚本

echo "🔍 紧急搜索Claude Enhancer 5.0..."
echo ""

# 显示所有包含Claude Enhancer 5.0的文件
echo "📋 找到的Claude Enhancer 5.0引用："
grep -r "Claude Enhancer 5.0" . \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude-dir=venv \
    --exclude-dir=.venv \
    --exclude="*.pyc" \
    --exclude="emergency_fix_claude-enhancer.sh" 2>/dev/null | while read line; do

    echo "  $line"

    # 提取文件名
    file=$(echo "$line" | cut -d: -f1)

    # 自动替换
    if [[ -f "$file" ]]; then
        sed -i 's/Claude Enhancer 5.0/Claude Enhancer/g' "$file" 2>/dev/null
        echo "    ✅ 已修复: $file"
    fi
done

echo ""
echo "🎯 修复完成！"
echo ""

# 再次验证
remaining=$(grep -r "Claude Enhancer 5.0" . \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    --exclude="emergency_fix_claude-enhancer.sh" 2>/dev/null | wc -l)

if [ $remaining -eq 0 ]; then
    echo "✅ 所有Claude Enhancer 5.0已清除！"
else
    echo "⚠️  还有 $remaining 个Claude Enhancer 5.0引用"
    echo "请运行: grep -r 'Claude Enhancer 5.0' . --exclude-dir=.git"
fi