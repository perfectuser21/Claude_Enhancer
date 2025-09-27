#!/bin/bash
# P5阶段审查准备器
echo "ℹ️ Review preparation active"

# 审查准备清单
echo "💡 审查准备:"
echo "  - 代码复杂度分析"
echo "  - 安全漏洞扫描"
echo "  - 性能瓶颈识别"
echo "  - 文档完整性"

# 检查REVIEW.md
if [ -f "docs/REVIEW.md" ]; then
    echo "  ✅ 审查报告已准备"
    # 检查关键章节
    grep -q "## 代码质量" docs/REVIEW.md || echo "  ⚠️ 建议添加代码质量分析"
    grep -q "## 安全评估" docs/REVIEW.md || echo "  ⚠️ 建议添加安全评估"
else
    echo "  ⚠️ 需要生成REVIEW.md"
fi

# 统计代码变更
if [ -d ".git" ]; then
    changes=$(git diff --stat HEAD~1 2>/dev/null | tail -1)
    [ -n "$changes" ] && echo "  📊 变更统计: $changes"
fi
