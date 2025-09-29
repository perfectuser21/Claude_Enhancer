#!/bin/bash
# self_test.sh - 工作流硬闸系统验收自测
# 一键验证所有功能是否正常工作

set -euo pipefail

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 测试结果统计
PASSED=0
FAILED=0
SKIPPED=0

# 获取脚本和仓库路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT"

# 测试函数
test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

test_skip() {
    echo -e "${YELLOW}⏭️  SKIP${NC}: $1"
    ((SKIPPED++))
}

section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 保存当前状态
ORIGINAL_BRANCH=$(git branch --show-current)
ORIGINAL_HOOKS_PATH=$(git config core.hooksPath || echo "")
TEST_BRANCH="test-workflow-guard-$$"

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 正在清理测试环境...${NC}"

    # 恢复原始分支
    git checkout "$ORIGINAL_BRANCH" 2>/dev/null || true

    # 删除测试分支
    git branch -D "$TEST_BRANCH" 2>/dev/null || true

    # 恢复hooks配置
    if [ -n "$ORIGINAL_HOOKS_PATH" ]; then
        git config core.hooksPath "$ORIGINAL_HOOKS_PATH"
    else
        git config --unset core.hooksPath 2>/dev/null || true
    fi

    # 清理测试文件
    rm -f .workflow/ACTIVE
    rm -f test-file-$$.txt

    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 设置退出时清理
trap cleanup EXIT

# 开始测试
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Claude Enhancer 工作流硬闸 - 自动化验收测试      ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"

section "1️⃣  环境检查"

# 检查CLI工具
if [ -x "$SCRIPT_DIR/ce-start" ]; then
    test_pass "ce-start 脚本存在且可执行"
else
    test_fail "ce-start 脚本不存在或不可执行"
fi

if [ -x "$SCRIPT_DIR/ce-stop" ]; then
    test_pass "ce-stop 脚本存在且可执行"
else
    test_fail "ce-stop 脚本不存在或不可执行"
fi

# 检查hooks
if [ -x "$GIT_ROOT/hooks/pre-push" ]; then
    test_pass "pre-push hook 存在且可执行"
else
    test_fail "pre-push hook 不存在或不可执行"
fi

# 检查setup脚本
if [ -x "$GIT_ROOT/setup_hooks.sh" ]; then
    test_pass "setup_hooks.sh 存在且可执行"
else
    test_fail "setup_hooks.sh 不存在或不可执行"
fi

section "2️⃣  安装Hooks"

echo -e "${YELLOW}正在安装hooks...${NC}"
if bash "$GIT_ROOT/setup_hooks.sh" > /dev/null 2>&1; then
    test_pass "Hooks 安装成功"

    # 验证配置
    HOOKS_PATH=$(git config core.hooksPath)
    if [ "$HOOKS_PATH" = "hooks/" ] || [ "$HOOKS_PATH" = "$GIT_ROOT/hooks" ]; then
        test_pass "Hooks 路径配置正确: $HOOKS_PATH"
    else
        test_fail "Hooks 路径配置错误: $HOOKS_PATH"
    fi
else
    test_fail "Hooks 安装失败"
fi

section "3️⃣  工作流激活测试"

# 清理可能存在的ACTIVE
rm -f .workflow/ACTIVE

# 测试在main分支激活（应该失败）
echo -e "${YELLOW}测试: 在main分支激活（预期失败）${NC}"
if ! "$SCRIPT_DIR/ce-start" "测试任务" 2>/dev/null; then
    test_pass "正确拒绝在main分支激活"
else
    test_fail "错误地允许在main分支激活"
fi

# 创建测试分支
echo -e "${YELLOW}创建测试分支: $TEST_BRANCH${NC}"
git checkout -b "$TEST_BRANCH" 2>/dev/null

# 测试激活工作流
echo -e "${YELLOW}测试: 在feature分支激活${NC}"
if "$SCRIPT_DIR/ce-start" "测试任务：验证工作流系统" > /dev/null; then
    test_pass "成功激活工作流"

    # 检查ACTIVE文件
    if [ -f ".workflow/ACTIVE" ]; then
        test_pass "ACTIVE 文件已创建"

        # 验证文件内容
        if grep -q "ticket=T-" .workflow/ACTIVE && \
           grep -q "branch=$TEST_BRANCH" .workflow/ACTIVE && \
           grep -q "note=测试任务：验证工作流系统" .workflow/ACTIVE; then
            test_pass "ACTIVE 文件内容正确"
        else
            test_fail "ACTIVE 文件内容不完整"
        fi
    else
        test_fail "ACTIVE 文件未创建"
    fi
else
    test_fail "激活工作流失败"
fi

section "4️⃣  Pre-push Hook测试"

# 创建一个测试提交
echo "test" > test-file-$$.txt
git add test-file-$$.txt
git commit -m "test: workflow guard validation" > /dev/null 2>&1

# 模拟push（使用dry-run避免真实推送）
echo -e "${YELLOW}测试: 已激活状态下的push（预期成功）${NC}"

# 直接测试pre-push hook
if bash "$GIT_ROOT/hooks/pre-push" < /dev/null 2>&1; then
    test_pass "已激活工作流，hook允许推送"
else
    test_fail "已激活工作流，但hook拒绝推送"
fi

# 停用工作流
echo -e "${YELLOW}停用工作流...${NC}"
if "$SCRIPT_DIR/ce-stop" > /dev/null 2>&1; then
    test_pass "成功停用工作流"

    # 检查归档
    if ls .workflow/archive/ACTIVE-*.txt > /dev/null 2>&1; then
        test_pass "ACTIVE 文件已归档"
    else
        test_fail "ACTIVE 文件未归档"
    fi

    # 检查ACTIVE已删除
    if [ ! -f ".workflow/ACTIVE" ]; then
        test_pass "ACTIVE 文件已移除"
    else
        test_fail "ACTIVE 文件未移除"
    fi
else
    test_fail "停用工作流失败"
fi

# 测试未激活状态的push
echo -e "${YELLOW}测试: 未激活状态下的push（预期失败）${NC}"
if ! bash "$GIT_ROOT/hooks/pre-push" < /dev/null 2>&1; then
    test_pass "未激活工作流，hook正确拒绝推送"
else
    test_fail "未激活工作流，但hook允许推送"
fi

section "5️⃣  分支匹配测试"

# 重新激活
"$SCRIPT_DIR/ce-start" "分支匹配测试" > /dev/null 2>&1

# 创建另一个分支
git checkout -b "test-another-branch-$$" 2>/dev/null

echo -e "${YELLOW}测试: 分支不匹配的push（预期失败）${NC}"
if ! bash "$GIT_ROOT/hooks/pre-push" < /dev/null 2>&1; then
    test_pass "分支不匹配，hook正确拒绝推送"
else
    test_fail "分支不匹配，但hook允许推送"
fi

# 回到原测试分支
git checkout "$TEST_BRANCH" 2>/dev/null
git branch -D "test-another-branch-$$" 2>/dev/null

section "6️⃣  可选功能测试"

# 测试锁定/解锁脚本
if [ -x "$SCRIPT_DIR/lock_main.sh" ] && [ -x "$SCRIPT_DIR/unlock_main.sh" ]; then
    echo -e "${YELLOW}测试: main分支锁定功能${NC}"
    test_pass "锁定/解锁脚本存在"
else
    test_skip "锁定/解锁脚本（可选功能）"
fi

section "📊 测试结果汇总"

TOTAL=$((PASSED + FAILED + SKIPPED))
SUCCESS_RATE=0
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
fi

echo ""
echo -e "${CYAN}┌─────────────────────────────────┐${NC}"
echo -e "${CYAN}│         测试统计               │${NC}"
echo -e "${CYAN}├─────────────────────────────────┤${NC}"
echo -e "${CYAN}│${NC} ${GREEN}通过: ${PASSED}${NC}"
echo -e "${CYAN}│${NC} ${RED}失败: ${FAILED}${NC}"
echo -e "${CYAN}│${NC} ${YELLOW}跳过: ${SKIPPED}${NC}"
echo -e "${CYAN}│${NC} 总计: ${TOTAL}"
echo -e "${CYAN}│${NC} 成功率: ${SUCCESS_RATE}%"
echo -e "${CYAN}└─────────────────────────────────┘${NC}"

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║    🎉 恭喜！所有测试通过，工作流硬闸系统正常运行    ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║    ⚠️  有 ${FAILED} 个测试失败，请检查并修复问题         ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════╝${NC}"
    exit 1
fi