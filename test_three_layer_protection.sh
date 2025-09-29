#!/bin/bash
# 测试Claude Enhancer三层保障机制
# 验证是否真正强制执行工作流

set -euo pipefail

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Claude Enhancer 三层保障机制验证测试             ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# 测试结果
PASSED=0
FAILED=0

# 测试函数
test_layer() {
    local layer_name="$1"
    local test_command="$2"
    local expected_result="$3"

    echo -e "${BLUE}测试: $layer_name${NC}"

    if eval "$test_command" 2>/dev/null; then
        if [ "$expected_result" = "pass" ]; then
            echo -e "${GREEN}✅ 通过${NC}"
            ((PASSED++))
        else
            echo -e "${RED}❌ 失败 - 应该被阻止但通过了${NC}"
            ((FAILED++))
        fi
    else
        if [ "$expected_result" = "fail" ]; then
            echo -e "${GREEN}✅ 正确阻止${NC}"
            ((PASSED++))
        else
            echo -e "${RED}❌ 失败 - 不应该被阻止${NC}"
            ((FAILED++))
        fi
    fi
    echo ""
}

echo -e "${YELLOW}第一层：工作流框架层（8-Phase系统）${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查工作流配置
test_layer "检查8-Phase工作流定义" \
    "[ -f '.claude/WORKFLOW.md' ] && grep -q 'P0-P7' .claude/WORKFLOW.md" \
    "pass"

test_layer "检查smart_agent_selector存在" \
    "[ -x '.claude/hooks/smart_agent_selector.sh' ]" \
    "pass"

echo -e "${YELLOW}第二层：Claude Hooks辅助层${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查Claude hooks配置
test_layer "检查settings.json配置" \
    "[ -f '.claude/settings.json' ] && grep -q 'hooks' .claude/settings.json" \
    "pass"

test_layer "检查quality_gate.sh存在" \
    "[ -x '.claude/hooks/quality_gate.sh' ]" \
    "pass"

echo -e "${YELLOW}第三层：Git Hooks强制层（工作流硬闸）${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查工作流激活状态
WORKFLOW_ACTIVE=false
if [ -f ".workflow/ACTIVE" ]; then
    WORKFLOW_ACTIVE=true
fi

test_layer "检查pre-push hook已安装" \
    "[ -x 'hooks/pre-push' ]" \
    "pass"

test_layer "检查工作流激活状态" \
    "[ -f '.workflow/ACTIVE' ]" \
    "pass"

# 模拟推送测试
if [ "$WORKFLOW_ACTIVE" = true ]; then
    test_layer "已激活工作流，模拟推送（应通过）" \
        "bash hooks/pre-push < /dev/null" \
        "pass"
else
    test_layer "未激活工作流，模拟推送（应失败）" \
        "bash hooks/pre-push < /dev/null" \
        "fail"
fi

echo -e "${YELLOW}CI/CD层：GitHub Actions检查${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_layer "检查GitHub Actions配置存在" \
    "[ -f '.github/workflows/ce-workflow-active.yml' ]" \
    "pass"

test_layer "检查Quality Gates配置存在" \
    "[ -f '.github/workflows/ce-quality-gates.yml' ]" \
    "pass"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}测试结果汇总${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

TOTAL=$((PASSED + FAILED))
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$((PASSED * 100 / TOTAL))
else
    SUCCESS_RATE=0
fi

echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo -e "总计: $TOTAL"
echo -e "成功率: ${SUCCESS_RATE}%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║    ✅ 三层保障机制完全正常！                         ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"

    echo ""
    echo -e "${CYAN}保障机制总结：${NC}"
    echo "1. 工作流框架层 ✅ - 8-Phase系统定义完整"
    echo "2. Claude Hooks ✅ - 智能辅助工具就绪"
    echo "3. Git Hooks层 ✅ - 强制执行机制激活"
    echo "4. CI/CD检查 ✅ - GitHub Actions配置完整"

    if [ "$WORKFLOW_ACTIVE" = true ]; then
        echo ""
        echo -e "${GREEN}当前工作流已激活，可以正常开发！${NC}"
    else
        echo ""
        echo -e "${YELLOW}提示：运行 'ce start \"任务\"' 激活工作流${NC}"
    fi
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║    ⚠️  有 $FAILED 项测试失败，请检查配置             ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════╝${NC}"
fi