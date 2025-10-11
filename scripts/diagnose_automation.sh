#!/bin/bash
# Claude Enhancer v6.0 - 自动化链路诊断脚本
# 2分钟定位为什么不能全自动

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🔍 Claude Enhancer v6.0 自动化链路诊断"
echo "========================================"
echo ""

# 0) 基础环境检查
echo -e "${BLUE}[0] 基础环境${NC}"
echo -n "当前分支: "
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "$BRANCH"

echo -n "远程仓库: "
git remote -v | grep origin | head -1 | awk '{print $2}'

echo ""

# 1) gh CLI 状态检查
echo -e "${BLUE}[1] GitHub CLI 状态${NC}"
if command -v gh >/dev/null 2>&1; then
    echo -e "${GREEN}✅ gh CLI 已安装${NC}"

    # 检查登录状态
    if gh auth status >/dev/null 2>&1; then
        echo -e "${GREEN}✅ gh 已登录${NC}"
        gh auth status 2>&1 | grep "Logged in" | head -1 || true
    else
        echo -e "${RED}❌ gh 未登录或Token无效${NC}"
        echo -e "${YELLOW}  修复: gh auth login${NC}"
    fi
else
    echo -e "${RED}❌ gh CLI 未安装${NC}"
    echo -e "${YELLOW}  修复: 安装 GitHub CLI${NC}"
fi

echo ""

# 2) PR 状态检查
echo -e "${BLUE}[2] Pull Request 状态${NC}"
PR_INFO=$(gh pr view --json number,state,mergeStateStatus,headRefName,baseRefName 2>/dev/null || echo "NO_PR")

if [[ "$PR_INFO" == "NO_PR" ]]; then
    echo -e "${YELLOW}⚠️ 当前分支没有关联的PR${NC}"
    echo "  需要创建PR: gh pr create"
else
    echo "PR信息:"
    echo "$PR_INFO" | jq -r '. as $x | "  PR #\($x.number) [\($x.state)] \($x.headRefName) → \($x.baseRefName)"'
    MERGE_STATE=$(echo "$PR_INFO" | jq -r '.mergeStateStatus')

    case "$MERGE_STATE" in
        "MERGEABLE")
            echo -e "${GREEN}  ✅ 可以合并${NC}"
            ;;
        "CONFLICTING")
            echo -e "${RED}  ❌ 有冲突需要解决${NC}"
            ;;
        "BLOCKED")
            echo -e "${YELLOW}  ⚠️ 被阻止（检查未通过或需要更新）${NC}"
            ;;
        *)
            echo "  状态: $MERGE_STATE"
            ;;
    esac
fi

echo ""

# 3) Branch Protection 检查
echo -e "${BLUE}[3] Branch Protection 配置${NC}"
BP_INFO=$(gh api repos/:owner/:repo/branches/main/protection 2>/dev/null || echo "NO_PROTECTION")

if [[ "$BP_INFO" == "NO_PROTECTION" ]]; then
    echo -e "${YELLOW}⚠️ main分支没有保护规则${NC}"
    echo "  这可能导致直推而非PR流程"
else
    echo "Required Status Checks:"
    REQUIRED_CHECKS=$(echo "$BP_INFO" | jq -r '.required_status_checks.contexts[]?' 2>/dev/null || echo "  无")
    if [[ -z "$REQUIRED_CHECKS" || "$REQUIRED_CHECKS" == "无" ]]; then
        echo -e "${YELLOW}  ⚠️ 没有配置必需检查${NC}"
    else
        echo "$REQUIRED_CHECKS" | while read check; do
            echo "  - $check"
        done
    fi

    # 检查自动合并设置
    ALLOW_AUTO=$(gh api repos/:owner/:repo -q '.allow_auto_merge' 2>/dev/null || echo "false")
    if [[ "$ALLOW_AUTO" == "true" ]]; then
        echo -e "${GREEN}✅ 仓库允许自动合并${NC}"
    else
        echo -e "${YELLOW}⚠️ 仓库未开启自动合并${NC}"
        echo "  修复: Settings → General → Allow auto-merge"
    fi
fi

echo ""

# 4) CI 运行状态
echo -e "${BLUE}[4] CI 工作流状态${NC}"
if [[ "$PR_INFO" != "NO_PR" ]]; then
    echo "检查PR的CI状态..."
    gh pr checks 2>/dev/null | head -10 || echo "  无法获取CI状态"
else
    echo "最近的工作流运行:"
    gh run list --limit 3 2>/dev/null || echo "  无法获取工作流状态"
fi

echo ""

# 5) CI Job名称对比
echo -e "${BLUE}[5] CI Job名称匹配检查${NC}"
echo "实际运行的CI Job名称:"
ACTUAL_JOBS=$(gh api repos/:owner/:repo/commits/HEAD/check-runs -q '.check_runs[].name' 2>/dev/null || echo "")
if [[ -n "$ACTUAL_JOBS" ]]; then
    echo "$ACTUAL_JOBS" | nl
else
    echo -e "${YELLOW}  ⚠️ 没有运行中的CI${NC}"
fi

echo ""

# 6) 自动化断点分析
echo -e "${BLUE}[6] 自动化断点分析${NC}"

ISSUES=0

# 检查是否在main分支
if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
    echo -e "${RED}❌ 在主分支上，无法创建PR${NC}"
    echo -e "${YELLOW}  修复: git checkout -b feature/xxx${NC}"
    ((ISSUES++))
fi

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${YELLOW}⚠️ 有未提交的更改${NC}"
    echo -e "${YELLOW}  修复: git add -A && git commit${NC}"
    ((ISSUES++))
fi

# 检查是否有未推送的提交
if [[ $(git rev-list HEAD...origin/"$BRANCH" 2>/dev/null | wc -l) -gt 0 ]]; then
    echo -e "${YELLOW}⚠️ 有未推送的提交${NC}"
    echo -e "${YELLOW}  修复: git push origin $BRANCH${NC}"
    ((ISSUES++))
fi

# 检查自动化工作流是否存在
if [[ ! -f ".github/workflows/auto-pr.yml" ]]; then
    echo -e "${YELLOW}⚠️ 缺少auto-pr.yml自动化工作流${NC}"
    echo -e "${YELLOW}  需要创建自动PR和合并的工作流${NC}"
    ((ISSUES++))
fi

if [[ $ISSUES -eq 0 ]]; then
    echo -e "${GREEN}✅ 没有发现自动化断点${NC}"
else
    echo -e "${RED}发现 $ISSUES 个潜在问题${NC}"
fi

echo ""

# 7) 推荐的修复方案
echo -e "${BLUE}[7] 推荐修复方案${NC}"

if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
    echo "1. 切换到feature分支:"
    echo "   git checkout -b feature/v6-final"
fi

if [[ "$PR_INFO" == "NO_PR" ]]; then
    echo "2. 创建PR:"
    echo "   gh pr create --base main --title 'v6.0.0' --body-file PR_DESCRIPTION_v6.0.md"
fi

if [[ "$ALLOW_AUTO" != "true" ]]; then
    echo "3. 开启仓库自动合并:"
    echo "   在GitHub Settings → General → 勾选 Allow auto-merge"
fi

if [[ ! -f ".github/workflows/auto-pr.yml" ]]; then
    echo "4. 创建自动化工作流:"
    echo "   需要auto-pr.yml和auto-tag.yml"
fi

echo ""
echo "========================================"
echo ""

# 最终诊断结果
if [[ $ISSUES -eq 0 ]] && [[ "$ALLOW_AUTO" == "true" ]] && [[ -f ".github/workflows/auto-pr.yml" ]]; then
    echo -e "${GREEN}🎉 自动化链路完整！${NC}"
    echo "只需要: git push origin $BRANCH"
    echo "剩下的会自动完成"
else
    echo -e "${YELLOW}⚠️ 自动化链路有断点，需要修复${NC}"
    echo "按照上面的修复方案操作即可实现全自动"
fi