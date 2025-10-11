#!/bin/bash
# Claude Enhancer v6.0 - 启用完全自动化
# 一键配置，实现真·全自动

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo "🤖 Claude Enhancer v6.0 - 完全自动化配置"
echo "==========================================="
echo ""
echo "目标: Push代码后全自动(PR→CI→合并→Tag→Release)"
echo ""

# 检查当前状态
echo -e "${BLUE}[检查] 当前自动化状态${NC}"

# 1. 检查分支
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 当前分支: $BRANCH"

# 2. 检查工作流文件
echo ""
echo -e "${BLUE}[验证] 自动化工作流${NC}"
if [[ -f ".github/workflows/auto-pr.yml" ]]; then
    echo -e "${GREEN}✅ auto-pr.yml 已就绪${NC}"
else
    echo -e "${RED}❌ 缺少 auto-pr.yml${NC}"
fi

if [[ -f ".github/workflows/auto-tag.yml" ]]; then
    echo -e "${GREEN}✅ auto-tag.yml 已就绪${NC}"
else
    echo -e "${RED}❌ 缺少 auto-tag.yml${NC}"
fi

echo ""
echo "==========================================="
echo ""

# 显示需要的手动步骤
echo -e "${YELLOW}📋 需要手动完成的步骤:${NC}"
echo ""

echo "1️⃣ 在GitHub仓库开启自动合并:"
echo "   浏览器打开: https://github.com/perfectuser21/Claude_Enhancer/settings"
echo "   → General → Pull Requests → ✅ Allow auto-merge"
echo ""

echo "2️⃣ 配置Required Status Checks (可选但推荐):"
echo "   Settings → Branches → main → Edit"
echo "   → Require status checks → 选择:"
echo "     - positive-health"
echo "     - ce-unified-gates"
echo "     - test-suite"
echo ""

echo "3️⃣ 推送代码触发全自动流程:"
echo -e "${GREEN}   git push origin $BRANCH${NC}"
echo ""

echo "==========================================="
echo ""

# 生成快速命令
echo -e "${GREEN}🚀 一键执行命令:${NC}"
echo ""

cat << 'COMMANDS'
# 推送当前分支（触发auto-pr.yml）
git push origin feature/v6-unification

# 然后观察自动流程:
# 1. Actions页面看到 "Auto PR & Merge" 运行
# 2. 自动创建PR
# 3. 自动启用auto-merge
# 4. CI运行并通过
# 5. 自动合并到main
# 6. 自动创建tag (auto-tag.yml)
# 7. 自动创建GitHub Release
COMMANDS

echo ""
echo "==========================================="
echo ""

# 实时检查
echo -e "${BLUE}[实时] 检查自动化链路${NC}"

# 检查auto-merge设置
echo -n "仓库auto-merge设置: "
AUTO_MERGE=$(gh api repos/:owner/:repo -q '.allow_auto_merge' 2>/dev/null || echo "unknown")
if [[ "$AUTO_MERGE" == "true" ]]; then
    echo -e "${GREEN}已启用 ✅${NC}"
else
    echo -e "${YELLOW}未启用 (需要在GitHub页面开启)${NC}"
fi

# 检查是否有PR
echo -n "当前分支PR状态: "
PR_EXISTS=$(gh pr list --head "$BRANCH" --json number -q '.[0].number' 2>/dev/null || echo "")
if [[ -n "$PR_EXISTS" ]]; then
    echo -e "${GREEN}PR #$PR_EXISTS 已存在${NC}"
else
    echo -e "${YELLOW}无PR (push后会自动创建)${NC}"
fi

echo ""
echo "==========================================="
echo ""

# 最终总结
if [[ "$AUTO_MERGE" == "true" ]] && [[ -f ".github/workflows/auto-pr.yml" ]]; then
    echo -e "${GREEN}✅ 自动化链路已就绪！${NC}"
    echo "只需要: git push origin $BRANCH"
    echo "剩下全部自动完成！"
else
    echo -e "${YELLOW}⚠️ 还需要完成上述手动步骤${NC}"
    echo "完成后即可实现完全自动化"
fi

echo ""
echo "📊 自动化流程图:"
echo ""
cat << 'FLOW'
   You                GitHub Actions           GitHub
    │                      │                      │
    ├─push feature/*──────>│                      │
    │                      ├──auto-pr.yml────────>│
    │                      │                      ├─Create PR
    │                      │<─────PR #123─────────┤
    │                      ├──enable auto-merge──>│
    │                      │                      ├─Run CI
    │                      │                      ├─All checks pass
    │                      │                      ├─Auto merge to main
    │                      │<────Merged───────────┤
    │                      ├──auto-tag.yml───────>│
    │                      │                      ├─Create tag v6.0.0
    │                      │                      ├─Create Release
    │<─────────────────────┼──────Done───────────┤
    │                      │                      │
   完成！                   │                      │
FLOW

echo ""
echo -e "${GREEN}🎯 核心理念: 你只管push，剩下全自动！${NC}"