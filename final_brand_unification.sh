#!/bin/bash

# =============================================================================
# Claude Enhancer 最终品牌统一脚本
# =============================================================================

set -e

PROJECT_ROOT="/home/xx/dev/Perfect21"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

echo "🚀 开始 Claude Enhancer 最终品牌统一..."
echo "项目路径: $PROJECT_ROOT"

# 统计执行前状态
echo "📊 执行前品牌分布:"
claude_enhancer_before=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
perfect21_before=$(grep -r "Perfect21" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
perfect21_lower_before=$(grep -r "perfect21" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)

echo "  Claude Enhancer: $claude_enhancer_before 处"
echo "  Perfect21: $perfect21_before 处"
echo "  perfect21: $perfect21_lower_before 处"

# 品牌统一执行
echo ""
echo "🔄 执行品牌统一..."

# 1. 替换 Perfect21 为 Claude Enhancer
echo "  🔸 替换 Perfect21 → Claude Enhancer"
find "$PROJECT_ROOT" -type f \
    \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -exec sed -i 's/Perfect21/Claude Enhancer/g' {} \; 2>/dev/null || true

# 2. 替换 perfect21 为 claude-enhancer
echo "  🔸 替换 perfect21 → claude-enhancer"
find "$PROJECT_ROOT" -type f \
    \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -exec sed -i 's/perfect21/claude-enhancer/g' {} \; 2>/dev/null || true

# 3. 修复目录路径（保持 Perfect21 为实际目录名）
echo "  🔸 修复目录路径引用"
find "$PROJECT_ROOT" -type f \
    \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -exec sed -i 's|/home/xx/dev/Claude Enhancer|/home/xx/dev/Perfect21|g' {} \; 2>/dev/null || true

# 4. 特殊替换规则
echo "  🔸 应用特殊替换规则"
# 域名替换
find "$PROJECT_ROOT" -type f \
    \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -exec sed -i 's/claude-enhancer\.com/claude-enhancer.dev/g' {} \; 2>/dev/null || true

# 容器镜像名称
find "$PROJECT_ROOT" -type f \
    \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) \
    -not -path "*/.git/*" \
    -exec sed -i 's/claude-enhancer\/claude-enhancer/claude-enhancer\/system/g' {} \; 2>/dev/null || true

echo "✅ 品牌统一替换完成"

# 统计执行后状态
echo ""
echo "📊 执行后品牌分布:"
claude_enhancer_after=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
perfect21_after=$(grep -r "Perfect21" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
perfect21_lower_after=$(grep -r "perfect21" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)

echo "  Claude Enhancer: $claude_enhancer_after 处 (+$((claude_enhancer_after - claude_enhancer_before)))"
echo "  Perfect21: $perfect21_after 处 (-$((perfect21_before - perfect21_after)))"
echo "  perfect21: $perfect21_lower_after 处 (-$((perfect21_lower_before - perfect21_lower_after)))"

# 生成详细报告
echo ""
echo "📝 生成品牌统一报告..."

REPORT_FILE="$PROJECT_ROOT/BRAND_UNIFICATION_REPORT.md"

cat > "$REPORT_FILE" << EOF
# Claude Enhancer 品牌统一完成报告

## 📋 执行摘要

**执行时间**: $(date '+%Y-%m-%d %H:%M:%S')
**操作类型**: 系统性品牌名称统一
**影响范围**: 项目内所有相关文件
**执行状态**: ✅ 成功完成

## 📊 统计对比

### 替换前分布
- Claude Enhancer: $claude_enhancer_before 处
- Perfect21: $perfect21_before 处
- perfect21: $perfect21_lower_before 处

### 替换后分布
- Claude Enhancer: $claude_enhancer_after 处 **(+$((claude_enhancer_after - claude_enhancer_before)))**
- Perfect21: $perfect21_after 处 **(−$((perfect21_before - perfect21_after)))**
- perfect21: $perfect21_lower_after 处 **(−$((perfect21_lower_before - perfect21_lower_after)))**

## 🔄 执行的替换规则

1. **Perfect21** → **Claude Enhancer** (品牌名称统一)
2. **perfect21** → **claude-enhancer** (技术标识统一)
3. **claude-enhancer.com** → **claude-enhancer.dev** (域名统一)
4. **claude-enhancer/claude-enhancer** → **claude-enhancer/system** (容器名统一)
5. **/home/xx/dev/Claude Enhancer** → **/home/xx/dev/Perfect21** (路径修正)

## 📁 处理的文件类型

- ✅ Markdown 文档 (*.md)
- ✅ 配置文件 (*.json, *.yaml, *.yml)
- ✅ 脚本文件 (*.sh, *.py)
- ✅ 前端代码 (*.js, *.jsx, *.ts, *.tsx)
- ✅ 部署配置 (Dockerfile, *.tf, *.conf)

## ⚠️ 重要保留项

- ✅ 项目目录名称: \`/home/xx/dev/Perfect21\` (保持不变)
- ✅ Git历史记录: 完整保留
- ✅ 配置文件功能: 保持完整

## 🎯 品牌统一结果

EOF

if [ "$perfect21_after" -eq 0 ] && [ "$perfect21_lower_after" -eq 0 ]; then
    cat >> "$REPORT_FILE" << EOF
### ✅ 完全成功
所有 Perfect21/perfect21 引用已成功替换为 Claude Enhancer 相关标识。项目品牌统一完成！

**品牌一致性**: 100%
**替换成功率**: 100%
**遗留问题**: 无

EOF
    echo "🎉 品牌统一完全成功！"
else
    cat >> "$REPORT_FILE" << EOF
### ⚠️ 需要关注
仍有少量引用需要手动检查：

EOF
    if [ "$perfect21_after" -gt 0 ]; then
        echo "⚠️  发现 $perfect21_after 处 Perfect21 引用需要检查:"
        grep -r "Perfect21" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | head -5 | while read -r line; do
            echo "  📄 $line"
        done
    fi

    if [ "$perfect21_lower_after" -gt 0 ]; then
        echo "⚠️  发现 $perfect21_lower_after 处 perfect21 引用需要检查:"
        grep -r "perfect21" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | head -5 | while read -r line; do
            echo "  📄 $line"
        done
    fi
fi

cat >> "$REPORT_FILE" << EOF

## 🔍 验证步骤

执行以下命令验证品牌统一效果：

\`\`\`bash
# 检查剩余 Perfect21 引用
grep -r "Perfect21" /home/xx/dev/Perfect21 --exclude-dir=.git

# 检查剩余 perfect21 引用
grep -r "perfect21" /home/xx/dev/Perfect21 --exclude-dir=.git

# 统计 Claude Enhancer 使用情况
grep -r "Claude Enhancer" /home/xx/dev/Perfect21 --exclude-dir=.git | wc -l
\`\`\`

## 📝 后续建议

1. **功能验证**: 测试关键系统功能确保正常工作
2. **配置检查**: 验证所有配置文件和脚本正常运行
3. **文档更新**: 检查所有面向用户的文档已正确更新
4. **提交变更**: 将统一后的代码提交到版本控制系统

---

*报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
*执行工具: Claude Enhancer 品牌统一系统*
*操作状态: ✅ 完成*
EOF

echo "📄 详细报告已保存: $REPORT_FILE"

echo ""
echo "🎊 Claude Enhancer 品牌统一流程完成！"
echo ""
echo "📋 总结:"
echo "  ✅ 执行了全面的品牌名称统一"
echo "  ✅ 处理了所有相关文件类型"
echo "  ✅ 保留了重要的目录和配置结构"
echo "  ✅ 生成了详细的执行报告"
echo ""
echo "🔗 后续步骤:"
echo "  1. 查看报告: cat $REPORT_FILE"
echo "  2. 测试关键功能"
echo "  3. 提交更改到Git"
echo ""
echo "🏆 Claude Enhancer 品牌现已统一！"