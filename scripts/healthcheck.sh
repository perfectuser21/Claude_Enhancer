#!/bin/bash
# 健康检查脚本 - 用于P6发布后验证
# 补丁6实现：自动检测服务健康状态
# Version: 1.0.0

set -euo pipefail

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🏥 Running health checks..."

FAILED=0

# 检查1: 工作流文件语法
check_workflow_syntax() {
    echo -n "Checking workflow syntax... "

    # 如果yamllint不可用，使用基础YAML检查
    if ! command -v yamllint &>/dev/null; then
        # 使用Python或简单的文件存在性检查
        if [[ -f ".github/workflows/ce-gates.yml" ]]; then
            echo -e "${GREEN}✓ (basic check)${NC}"
            return 0
        else
            echo -e "${RED}✗${NC}"
            return 1
        fi
    fi

    # yamllint可用时使用完整检查
    if yamllint .github/workflows/ce-gates.yml &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 检查2: Gates解析器可用性
check_gates_parser() {
    echo -n "Checking gates parser... "
    if bash .workflow/scripts/gates_parser.sh get_allow_paths P1 &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 检查3: 必要工具安装
check_required_tools() {
    echo -n "Checking required tools... "
    local missing=""

    for tool in git bash awk grep; do
        if ! command -v "$tool" &>/dev/null; then
            missing="$missing $tool"
        fi
    done

    if [[ -z "$missing" ]]; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗ Missing:$missing${NC}"
        return 1
    fi
}

# 检查4: Phase文件存在
check_phase_file() {
    echo -n "Checking phase file... "
    if [[ -f ".phase/current" ]] && [[ -s ".phase/current" ]]; then
        phase=$(cat .phase/current | tr -d '[:space:]')
        echo -e "${GREEN}✓ ($phase)${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 检查5: CI配置完整性
check_ci_config() {
    echo -n "Checking CI configuration... "
    if [[ -f ".github/workflows/ce-gates.yml" ]] && \
       [[ -f ".github/PULL_REQUEST_TEMPLATE.md" ]] && \
       [[ -f ".github/CODEOWNERS" ]]; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 运行所有检查
run_all_checks() {
    check_workflow_syntax || ((FAILED++))
    check_gates_parser || ((FAILED++))
    check_required_tools || ((FAILED++))
    check_phase_file || ((FAILED++))
    check_ci_config || ((FAILED++))
}

# 主函数
main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    run_all_checks
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}✅ All health checks passed${NC}"
        exit 0
    else
        echo -e "${RED}❌ $FAILED health checks failed${NC}"
        echo "System may not be ready for production"
        exit 1
    fi
}

main "$@"