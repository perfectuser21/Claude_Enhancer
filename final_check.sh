#!/bin/bash
# 最终验证所有hooks是否已修复

cd "/home/xx/dev/Claude Enhancer 5.0/.claude/hooks"

echo "🎯 Claude Enhancer v5.5.2 - 最终验证"
echo "====================================="
echo

# 统计
TOTAL_HOOKS=$(ls -1 *.sh 2>/dev/null | wc -l)
FIXED_HOOKS=$(grep -l 'CE_SILENT_MODE.*!=' *.sh 2>/dev/null | wc -l)
UNFIXED=0

echo "📊 Hook统计："
echo "  总hooks数: $TOTAL_HOOKS"
echo "  已修复: $FIXED_HOOKS"
echo

# 检查未修复的
echo "🔍 检查结果："
UNFIXED_LIST=""
for file in *.sh; do
    if [[ -f "$file" ]]; then
        if ! grep -q 'CE_SILENT_MODE.*!=' "$file"; then
            UNFIXED_LIST="$UNFIXED_LIST  ❌ $file\n"
            ((UNFIXED++))
        fi
    fi
done

if [[ $UNFIXED -eq 0 ]]; then
    echo "  ✅ 所有hooks都已实现CE_SILENT_MODE支持！"
else
    echo "  未修复的hooks ($UNFIXED个):"
    echo -e "$UNFIXED_LIST"
fi

# 计算实现率
if [[ $TOTAL_HOOKS -gt 0 ]]; then
    RATE=$((FIXED_HOOKS * 100 / TOTAL_HOOKS))
    echo
    echo "📈 实现进度："
    echo "  实现率: ${RATE}%"

    # 进度条
    PROGRESS=""
    for i in {1..20}; do
        if [[ $((i * 5)) -le $RATE ]]; then
            PROGRESS="${PROGRESS}█"
        else
            PROGRESS="${PROGRESS}░"
        fi
    done
    echo "  $PROGRESS $RATE%"
fi

echo
echo "📋 已修复的hooks列表："
ls -1 *.sh | while read file; do
    if grep -q 'CE_SILENT_MODE.*!=' "$file"; then
        # 检查是否也支持CE_COMPACT_OUTPUT
        if grep -q 'CE_COMPACT_OUTPUT' "$file"; then
            echo "  ✅ $file (完整支持)"
        else
            echo "  ⚠️ $file (仅静默模式)"
        fi
    fi
done

echo
echo "🏁 验证完成！"

# 检查已删除的重复hooks
echo
echo "📦 已归档的重复hooks："
ARCHIVED_COUNT=$(ls -1 archive/duplicates/*.sh 2>/dev/null | wc -l)
echo "  已移除 $ARCHIVED_COUNT 个重复/过时的hooks到archive/duplicates/"

# 总结
echo
echo "════════════════════════════════════"
echo "📊 总结："
echo "  • 原始hooks: 51个"
echo "  • 删除重复: ${ARCHIVED_COUNT}个"
echo "  • 当前hooks: ${TOTAL_HOOKS}个"
echo "  • 已修复: ${FIXED_HOOKS}个"
echo "  • 实现率: ${RATE}%"

if [[ $RATE -eq 100 ]]; then
    echo
    echo "🎉 恭喜！所有hooks已完全实现静默模式！"
    echo "✨ Claude Enhancer v5.5.2 - 100%实现完成！"
fi