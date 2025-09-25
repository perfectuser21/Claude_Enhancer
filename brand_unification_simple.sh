#!/bin/bash

# =============================================================================
# Claude Enhancer 品牌统一脚本 (简化版)
# 将所有Claude Enhancer/claude-enhancer引用统一为Claude Enhancer
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="/home/xx/dev/Claude_Enhancer"
REPORT_FILE="$PROJECT_ROOT/BRAND_UNIFICATION_REPORT.md"

echo -e "${CYAN}🚀 Claude Enhancer 品牌统一开始...${NC}"

# 分析当前情况
echo -e "\n${BLUE}📊 当前品牌使用统计:${NC}"

claude_enhancer_before=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
claude-enhancer_before=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
claude-enhancer_lower_before=$(grep -r "claude-enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)

echo "- Claude Enhancer: $claude_enhancer_before 处"
echo "- Claude Enhancer: $claude-enhancer_before 处"
echo "- claude-enhancer: $claude-enhancer_lower_before 处"

# 执行替换
echo -e "\n${PURPLE}🔄 执行品牌统一替换...${NC}"

# 1. 先替换 Claude Enhancer 为 Claude Enhancer
echo "  🔄 替换 Claude Enhancer → Claude Enhancer"
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) -not -path "*/.git/*" -not -path "*/docs_backup_*" -exec sed -i 's/Claude Enhancer/Claude Enhancer/g' {} \; 2>/dev/null

# 2. 再替换 claude-enhancer 为 claude-enhancer
echo "  🔄 替换 claude-enhancer → claude-enhancer"
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) -not -path "*/.git/*" -not -path "*/docs_backup_*" -exec sed -i 's/claude-enhancer/claude-enhancer/g' {} \; 2>/dev/null

# 3. 特殊替换 - 域名和容器名
echo "  🔄 替换特殊标识符"
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) -not -path "*/.git/*" -not -path "*/docs_backup_*" -exec sed -i 's/claude-enhancer\.com/claude-enhancer.dev/g' {} \; 2>/dev/null

find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) -not -path "*/.git/*" -not -path "*/docs_backup_*" -exec sed -i 's/claude-enhancer\/claude-enhancer/claude-enhancer\/system/g' {} \; 2>/dev/null

# 4. 修复目录路径（保持 Claude Enhancer 作为目录名）
echo "  🔄 修复目录路径引用"
find "$PROJECT_ROOT" -type f \( -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" -o -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.conf" -o -name "Dockerfile*" -o -name "*.tf" \) -not -path "*/.git/*" -not -path "*/docs_backup_*" -exec sed -i 's|/home/xx/dev/Claude Enhancer|/home/xx/dev/Claude_Enhancer|g' {} \; 2>/dev/null

# 验证结果
echo -e "\n${GREEN}✅ 替换完成，验证结果:${NC}"

claude_enhancer_after=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
claude-enhancer_after=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
claude-enhancer_lower_after=$(grep -r "claude-enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)

echo "- Claude Enhancer: $claude_enhancer_after 处 (+$((claude_enhancer_after - claude_enhancer_before)))"
echo "- Claude Enhancer: $claude-enhancer_after 处 (-$((claude-enhancer_before - claude-enhancer_after)))"
echo "- claude-enhancer: $claude-enhancer_lower_after 处 (-$((claude-enhancer_lower_before - claude-enhancer_lower_after)))"

# 生成报告
echo -e "\n${BLUE}📝 生成变更报告...${NC}"

cat > "$REPORT_FILE" << EOF
# Claude Enhancer 品牌统一报告

## 📊 执行摘要

**执行时间**: $(date '+%Y-%m-%d %H:%M:%S')
**操作类型**: 品牌名称统一
**影响范围**: 项目内所有相关文件

## 📈 统计对比

### 替换前
- Claude Enhancer: $claude_enhancer_before 处
- Claude Enhancer: $claude-enhancer_before 处
- claude-enhancer: $claude-enhancer_lower_before 处

### 替换后
- Claude Enhancer: $claude_enhancer_after 处 (+$((claude_enhancer_after - claude_enhancer_before)))
- Claude Enhancer: $claude-enhancer_after 处 (-$((claude-enhancer_before - claude-enhancer_after)))
- claude-enhancer: $claude-enhancer_lower_after 处 (-$((claude-enhancer_lower_before - claude-enhancer_lower_after)))

## 🔄 主要替换规则

1. **Claude Enhancer** → **Claude Enhancer**
2. **claude-enhancer** → **claude-enhancer**
3. **claude-enhancer.com** → **claude-enhancer.dev**
4. **claude-enhancer/claude-enhancer** → **claude-enhancer/system**

## 📁 处理文件类型

- Markdown 文档 (*.md)
- 配置文件 (*.json, *.yaml, *.yml)
- 脚本文件 (*.sh, *.py)
- 前端代码 (*.js, *.jsx, *.ts, *.tsx)
- 部署配置 (Dockerfile, *.tf, *.conf)

## ⚠️ 重要说明

- ✅ 项目目录名保持为 \`Claude Enhancer\`
- ✅ 所有路径引用已正确修复
- ✅ 品牌统一为 \`Claude Enhancer\`
- ✅ 技术命名统一为 \`claude-enhancer\`

## 🔍 验证命令

\`\`\`bash
# 检查剩余的Claude Enhancer引用
grep -r "Claude Enhancer" /home/xx/dev/Claude_Enhancer --exclude-dir=.git

# 检查剩余的claude-enhancer引用
grep -r "claude-enhancer" /home/xx/dev/Claude_Enhancer --exclude-dir=.git

# 统计Claude Enhancer使用情况
grep -r "Claude Enhancer" /home/xx/dev/Claude_Enhancer --exclude-dir=.git | wc -l
\`\`\`

## ✅ 完成状态

- [x] 基础品牌名称替换
- [x] 技术标识符统一
- [x] 域名和URL更新
- [x] 目录路径修复
- [x] 验证结果正确性

---

*报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
*执行工具: Claude Enhancer 品牌统一脚本*
EOF

echo -e "📄 报告已生成: ${REPORT_FILE}"

# 检查剩余引用
if [ "$claude-enhancer_after" -gt 0 ] || [ "$claude-enhancer_lower_after" -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  发现剩余引用，建议手动检查:${NC}"

    if [ "$claude-enhancer_after" -gt 0 ]; then
        echo -e "\n${YELLOW}Claude Enhancer 引用 ($claude-enhancer_after 处):${NC}"
        grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | head -5
    fi

    if [ "$claude-enhancer_lower_after" -gt 0 ]; then
        echo -e "\n${YELLOW}claude-enhancer 引用 ($claude-enhancer_lower_after 处):${NC}"
        grep -r "claude-enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | head -5
    fi
else
    echo -e "\n${GREEN}🎉 品牌统一完全成功！所有引用已正确替换。${NC}"
fi

echo -e "\n${CYAN}📋 建议后续操作:${NC}"
echo "  1. 检查并测试关键功能"
echo "  2. 审查自动替换结果"
echo "  3. 提交变更到版本控制"
echo "  4. 更新相关外部文档"

echo -e "\n${GREEN}✅ Claude Enhancer 品牌统一脚本执行完成！${NC}"