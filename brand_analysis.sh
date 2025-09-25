#!/bin/bash

# =============================================================================
# Claude Enhancer 品牌分析脚本
# 分析需要统一的Claude Enhancer/claude-enhancer引用
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

echo -e "${CYAN}🔍 Claude Enhancer 品牌使用分析${NC}"
echo -e "项目路径: $PROJECT_ROOT"
echo

# 统计当前品牌使用情况
echo -e "${BLUE}📊 品牌使用统计:${NC}"

claude_enhancer_count=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
claude-enhancer_count=$(grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
claude-enhancer_lower_count=$(grep -r "claude-enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)
claude_enhancer_lower=$(grep -r "claude enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l)

echo "- Claude Enhancer: $claude_enhancer_count 处"
echo "- Claude Enhancer: $claude-enhancer_count 处"
echo "- claude-enhancer: $claude-enhancer_lower_count 处"
echo "- claude enhancer: $claude_enhancer_lower 处"

# 分析Claude Enhancer引用类型
echo -e "\n${PURPLE}📋 Claude Enhancer 引用分析 (前20个):${NC}"
grep -r "Claude Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | head -20 | while read -r line; do
    echo "  📄 $line"
done

# 分析claude-enhancer引用类型
echo -e "\n${PURPLE}📋 claude-enhancer 引用分析 (前20个):${NC}"
grep -r "claude-enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | head -20 | while read -r line; do
    echo "  📄 $line"
done

# 按文件类型分析
echo -e "\n${YELLOW}📂 按文件类型分布:${NC}"

echo "Markdown 文件:"
find "$PROJECT_ROOT" -name "*.md" -type f -not -path "*/.git/*" -exec grep -l "Claude Enhancer\|claude-enhancer" {} \; 2>/dev/null | wc -l | xargs echo "  - .md:"

echo "配置文件:"
find "$PROJECT_ROOT" \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) -type f -not -path "*/.git/*" -exec grep -l "Claude Enhancer\|claude-enhancer" {} \; 2>/dev/null | wc -l | xargs echo "  - config:"

echo "脚本文件:"
find "$PROJECT_ROOT" \( -name "*.sh" -o -name "*.py" \) -type f -not -path "*/.git/*" -exec grep -l "Claude Enhancer\|claude-enhancer" {} \; 2>/dev/null | wc -l | xargs echo "  - scripts:"

echo "前端文件:"
find "$PROJECT_ROOT" \( -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) -type f -not -path "*/.git/*" -exec grep -l "Claude Enhancer\|claude-enhancer" {} \; 2>/dev/null | wc -l | xargs echo "  - frontend:"

# 检查关键目录路径引用
echo -e "\n${RED}⚠️  关键路径引用检查:${NC}"
grep -r "/home/xx/dev/Claude_Enhancer" "$PROJECT_ROOT" --exclude-dir=.git 2>/dev/null | wc -l | xargs echo "  - 正确路径引用:"

# 生成预期替换建议
echo -e "\n${GREEN}🎯 建议的替换规则:${NC}"
echo "1. Claude Enhancer → Claude Enhancer (品牌名称)"
echo "2. claude-enhancer → claude-enhancer (技术标识)"
echo "3. Claude Enhancer System → Claude Enhancer System"
echo "4. Claude Enhancer工作流 → Claude Enhancer工作流"
echo "5. claude-enhancer.com → claude-enhancer.dev"
echo "6. claude-enhancer-api → claude-enhancer-api"
echo "7. claude-enhancer_test → claude_enhancer_test"
echo "8. 保持 /home/xx/dev/Claude_Enhancer 目录路径不变"

# 风险评估
echo -e "\n${YELLOW}⚠️  风险评估:${NC}"
echo "- 低风险: 文档和注释中的品牌名称"
echo "- 中风险: 配置文件中的服务名称"
echo "- 高风险: 数据库名称和API端点"
echo "- 需保留: 实际目录路径和Git日志"

echo -e "\n${CYAN}📋 建议执行步骤:${NC}"
echo "1. 创建当前状态备份"
echo "2. 先处理低风险文档文件"
echo "3. 逐步处理配置文件"
echo "4. 测试关键功能"
echo "5. 提交变更"

echo -e "\n${GREEN}✅ 品牌分析完成${NC}"