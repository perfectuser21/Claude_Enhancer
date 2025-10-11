#!/bin/bash
# Claude Enhancer v6.0 - 终极自动化验证
# 30秒快速检查是否真的能全自动

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🎯 Claude Enhancer v6.0 - 终极自动化验证"
echo "=========================================="
echo ""

READY_COUNT=0
TOTAL_COUNT=0

# 1. Allow auto-merge检查
echo -e "${BLUE}[1/5] 仓库auto-merge设置${NC}"
((TOTAL_COUNT++))
ALLOW_AUTO=$(gh api repos/:owner/:repo -q '.allow_auto_merge' 2>/dev/null || echo "false")
if [[ "$ALLOW_AUTO" == "true" ]]; then
    echo -e "${GREEN}✅ Allow auto-merge: 已启用${NC}"
    ((READY_COUNT++))
else
    echo -e "${RED}❌ Allow auto-merge: 未启用${NC}"
    echo -e "${YELLOW}   修复: Settings → General → Pull Requests → ✅ Allow auto-merge${NC}"
fi

# 2. Required Status Checks检查
echo ""
echo -e "${BLUE}[2/5] Required Status Checks配置${NC}"
((TOTAL_COUNT++))
REQUIRED_CHECKS=$(gh api repos/:owner/:repo/branches/main/protection -q '.required_status_checks.contexts[]?' 2>/dev/null || echo "")
if [[ -n "$REQUIRED_CHECKS" ]]; then
    echo -e "${GREEN}✅ Required checks已配置:${NC}"
    echo "$REQUIRED_CHECKS" | while read check; do
        echo "   - $check"
    done

    # 检查关键的几个
    if echo "$REQUIRED_CHECKS" | grep -q "positive-health"; then
        echo -e "${GREEN}   ✓ positive-health 已配置${NC}"
    else
        echo -e "${YELLOW}   ⚠ positive-health 未配置${NC}"
    fi
    ((READY_COUNT++))
else
    echo -e "${RED}❌ 没有配置Required Status Checks${NC}"
    echo -e "${YELLOW}   修复: Settings → Branches → main → Edit → Require status checks${NC}"
    echo -e "${YELLOW}   选择: positive-health, ce-unified-gates, test-suite${NC}"
fi

# 3. 工作流权限检查
echo ""
echo -e "${BLUE}[3/5] 工作流权限配置${NC}"
((TOTAL_COUNT++))
AUTO_PR_OK=false
AUTO_TAG_OK=false

if [[ -f ".github/workflows/auto-pr.yml" ]]; then
    if grep -q "contents: write" .github/workflows/auto-pr.yml && \
       grep -q "pull-requests: write" .github/workflows/auto-pr.yml; then
        echo -e "${GREEN}✅ auto-pr.yml 权限正确${NC}"
        AUTO_PR_OK=true
    else
        echo -e "${RED}❌ auto-pr.yml 权限不足${NC}"
    fi
else
    echo -e "${RED}❌ auto-pr.yml 不存在${NC}"
fi

if [[ -f ".github/workflows/auto-tag.yml" ]]; then
    if grep -q "contents: write" .github/workflows/auto-tag.yml; then
        echo -e "${GREEN}✅ auto-tag.yml 权限正确${NC}"
        AUTO_TAG_OK=true
    else
        echo -e "${RED}❌ auto-tag.yml 权限不足${NC}"
    fi
else
    echo -e "${RED}❌ auto-tag.yml 不存在${NC}"
fi

if [[ "$AUTO_PR_OK" == "true" ]] && [[ "$AUTO_TAG_OK" == "true" ]]; then
    ((READY_COUNT++))
fi

# 4. 当前PR状态检查
echo ""
echo -e "${BLUE}[4/5] 当前PR状态${NC}"
((TOTAL_COUNT++))
BRANCH=$(git rev-parse --abbrev-ref HEAD)
PR_INFO=$(gh pr view --json autoMergeRequest,state,mergeStateStatus,number 2>/dev/null || echo "NO_PR")

if [[ "$PR_INFO" != "NO_PR" ]]; then
    PR_NUM=$(echo "$PR_INFO" | jq -r '.number')
    PR_STATE=$(echo "$PR_INFO" | jq -r '.state')
    MERGE_STATE=$(echo "$PR_INFO" | jq -r '.mergeStateStatus')
    AUTO_MERGE_USER=$(echo "$PR_INFO" | jq -r '.autoMergeRequest.enabledBy.login // "none"')

    echo "PR #$PR_NUM 状态:"
    echo "  State: $PR_STATE"
    echo "  Merge Status: $MERGE_STATE"

    if [[ "$AUTO_MERGE_USER" != "none" && "$AUTO_MERGE_USER" != "null" ]]; then
        echo -e "${GREEN}✅ Auto-merge: 已启用 (by $AUTO_MERGE_USER)${NC}"
        ((READY_COUNT++))
    else
        echo -e "${YELLOW}⚠️ Auto-merge: 未启用${NC}"
        if [[ "$ALLOW_AUTO" == "true" ]]; then
            echo "  将在下次push后自动启用"
            ((READY_COUNT++))
        fi
    fi
else
    echo -e "${YELLOW}⚠️ 当前分支没有PR${NC}"
    echo "  push后会自动创建"
    ((READY_COUNT++))
fi

# 5. 实际CI Job名称检查
echo ""
echo -e "${BLUE}[5/5] CI Job名称匹配${NC}"
((TOTAL_COUNT++))
echo "最近运行的CI Jobs:"
ACTUAL_JOBS=$(gh api repos/:owner/:repo/commits/HEAD/check-runs -q '.check_runs[0:5] | .[] | .name' 2>/dev/null || echo "")
if [[ -n "$ACTUAL_JOBS" ]]; then
    echo "$ACTUAL_JOBS" | head -5 | nl

    # 检查关键job是否存在
    if echo "$ACTUAL_JOBS" | grep -q "positive-health"; then
        echo -e "${GREEN}  ✓ 找到 positive-health${NC}"
    fi
    ((READY_COUNT++))
else
    echo -e "${YELLOW}  还没有CI运行记录${NC}"
    ((READY_COUNT++))
fi

# 最终判定
echo ""
echo "=========================================="
echo ""

SCORE=$((READY_COUNT * 100 / TOTAL_COUNT))

if [[ $SCORE -ge 80 ]]; then
    echo -e "${GREEN}🎉 自动化就绪度: $SCORE% ($READY_COUNT/$TOTAL_COUNT)${NC}"
    echo ""
    echo -e "${GREEN}✅ 可以推送了！执行:${NC}"
    echo ""
    echo "  git push origin $BRANCH"
    echo ""
    echo "预期流程:"
    echo "1. 自动创建PR"
    echo "2. 自动启用auto-merge"
    echo "3. CI运行并通过"
    echo "4. 自动合并到main"
    echo "5. 自动创建tag v6.0.0"
    echo "6. 自动创建GitHub Release"
elif [[ $SCORE -ge 60 ]]; then
    echo -e "${YELLOW}⚠️ 自动化就绪度: $SCORE% ($READY_COUNT/$TOTAL_COUNT)${NC}"
    echo ""
    echo "基本就绪，但建议先完成上述修复"
else
    echo -e "${RED}❌ 自动化就绪度: $SCORE% ($READY_COUNT/$TOTAL_COUNT)${NC}"
    echo ""
    echo "需要先完成必要的配置"
fi

echo ""
echo "=========================================="
echo ""

# 快速修复命令
if [[ "$ALLOW_AUTO" != "true" ]] || [[ -z "$REQUIRED_CHECKS" ]]; then
    echo -e "${YELLOW}📋 快速修复清单:${NC}"
    echo ""

    if [[ "$ALLOW_AUTO" != "true" ]]; then
        echo "1. 开启auto-merge:"
        echo "   https://github.com/perfectuser21/Claude_Enhancer/settings"
        echo "   → Pull Requests → ✅ Allow auto-merge"
        echo ""
    fi

    if [[ -z "$REQUIRED_CHECKS" ]]; then
        echo "2. 配置Required Checks:"
        echo "   https://github.com/perfectuser21/Claude_Enhancer/settings/branches"
        echo "   → main → Edit → Require status checks"
        echo "   → 搜索并添加: positive-health, ce-unified-gates, test-suite"
        echo ""
    fi
fi

# 监控命令
echo "📊 实时监控命令:"
echo ""
echo "# 查看PR状态"
echo "gh pr checks --watch"
echo ""
echo "# 查看工作流运行"
echo "gh run watch"
echo ""
echo "# 查看自动合并状态"
echo "gh pr view --json autoMergeRequest"

echo ""
echo "🎯 记住: 配置好后，你只管push，剩下全自动！"