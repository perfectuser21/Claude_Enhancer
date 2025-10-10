#!/usr/bin/env bash
set -euo pipefail

echo "╔════════════════════════════════════════╗"
echo "║  Claude Enhancer 完整验证测试          ║"
echo "╚════════════════════════════════════════╝"

# 颜色配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 统计
TOTAL=0
PASS=0
FAIL=0

# 测试函数
test_item() {
    local name="$1"
    local cmd="$2"
    TOTAL=$((TOTAL + 1))
    echo -n "Testing: $name ... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

echo -e "\n${BLUE}1. 环境检查${NC}"
test_item "Git配置" "git config --get core.hooksPath | grep -q githooks"
test_item "Hooks目录" "test -d .githooks"
test_item "Scripts目录" "test -d scripts"
test_item "Workflow目录" "test -d .workflow"

echo -e "\n${BLUE}2. 核心文件${NC}"
test_item "commit-msg hook" "test -f .githooks/commit-msg"
test_item "pre-push hook" "test -f .githooks/pre-push"
test_item "权限修复脚本" "test -f scripts/fix_permissions.sh"
test_item "Chaos防御脚本" "test -f scripts/chaos_defense.sh"
test_item "快速测试脚本" "test -f scripts/quick_chaos_test.sh"

echo -e "\n${BLUE}3. 执行权限${NC}"
test_item "commit-msg可执行" "test -x .githooks/commit-msg"
test_item "pre-push可执行" "test -x .githooks/pre-push"
test_item "fix_permissions可执行" "test -x scripts/fix_permissions.sh"

echo -e "\n${BLUE}4. 工作流文档${NC}"
test_item "PLAN.md" "test -f .workflow/PLAN.md"
test_item "REVIEW.md" "test -f .workflow/REVIEW.md"
test_item "FIXES.md" "test -f FIXES.md"
test_item "README_WORKFLOW.md" "test -f README_WORKFLOW.md"

echo -e "\n${BLUE}5. 功能测试${NC}"
test_item "权限修复功能" "bash scripts/fix_permissions.sh"
test_item "Hook配置验证" "grep -q '8-Phase' .claude/hooks/workflow_enforcer.sh"

# 最终统计
echo -e "\n════════════════════════════════════════"
echo -e "${BLUE}验证结果统计：${NC}"
echo -e "  总测试: $TOTAL"
echo -e "  ${GREEN}通过: $PASS${NC}"
echo -e "  ${RED}失败: $FAIL${NC}"
echo -e "  通过率: $(( PASS * 100 / TOTAL ))%"

# 评分
SCORE=$(( PASS * 100 / TOTAL ))
if [[ $SCORE -ge 90 ]]; then
    echo -e "\n${GREEN}✨ 优秀！系统状态良好 (${SCORE}/100)${NC}"
elif [[ $SCORE -ge 70 ]]; then
    echo -e "\n${YELLOW}⚠️ 良好，但有待改进 (${SCORE}/100)${NC}"
else
    echo -e "\n${RED}❌ 需要修复 (${SCORE}/100)${NC}"
fi

echo -e "════════════════════════════════════════\n"

# 返回状态
if [[ $FAIL -eq 0 ]]; then
    exit 0
else
    exit 1
fi
