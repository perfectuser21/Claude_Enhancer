#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# CI快速验证脚本 - 5分钟快速检查
# ═══════════════════════════════════════════════════════════════
# 用途：在CI中快速验证核心功能
# 执行时间：< 2分钟
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

check() {
    local name="$1"
    local command="$2"

    echo -ne "${CYAN}▶${NC} $name ... "

    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Claude Enhancer - CI快速验证${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"

# 1. 基础结构检查
echo -e "${YELLOW}[1/5] 项目结构${NC}"
check "Git仓库" "git rev-parse --git-dir"
check "Gates配置" "test -f $PROJECT_ROOT/.workflow/gates.yml"
check "Pre-commit hook" "test -f $PROJECT_ROOT/.git/hooks/pre-commit"
check "Phase目录" "test -d $PROJECT_ROOT/.phase"

# 2. Hook功能检查
echo -e "\n${YELLOW}[2/5] Hook功能${NC}"
check "Hook可执行" "test -x $PROJECT_ROOT/.git/hooks/pre-commit"
check "Gates.yml语法" "grep -q 'phase_order:' $PROJECT_ROOT/.workflow/gates.yml"
check "Allow_paths配置" "grep -q 'allow_paths:' $PROJECT_ROOT/.workflow/gates.yml"

# 3. 安全检查功能
echo -e "\n${YELLOW}[3/5] 安全扫描${NC}"
check "密码检测模式" "grep -q 'password.*=' $PROJECT_ROOT/.git/hooks/pre-commit"
check "API密钥检测" "grep -q 'api.*key' $PROJECT_ROOT/.git/hooks/pre-commit"
check "私钥检测" "grep -q 'PRIVATE KEY' $PROJECT_ROOT/.git/hooks/pre-commit"

# 4. Phase配置完整性
echo -e "\n${YELLOW}[4/5] Phase配置${NC}"
for phase in P0 P1 P2 P3 P4 P5 P6 P7; do
    check "$phase配置" "grep -q \"^  $phase:\" $PROJECT_ROOT/.workflow/gates.yml"
done

# 5. 文档和产出要求
echo -e "\n${YELLOW}[5/5] 产出要求${NC}"
check "P1 must_produce" "grep -A5 '^  P1:' $PROJECT_ROOT/.workflow/gates.yml | grep -q 'must_produce:'"
check "P4 must_produce" "grep -A5 '^  P4:' $PROJECT_ROOT/.workflow/gates.yml | grep -q 'must_produce:'"
check "P6 must_produce" "grep -A5 '^  P6:' $PROJECT_ROOT/.workflow/gates.yml | grep -q 'must_produce:'"

# 汇总
echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "   通过: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "   失败: ${RED}$CHECKS_FAILED${NC}"

TOTAL=$((CHECKS_PASSED + CHECKS_FAILED))
if [[ $TOTAL -gt 0 ]]; then
    RATE=$(awk "BEGIN {printf \"%.0f\", ($CHECKS_PASSED/$TOTAL)*100}")
    echo -e "   成功率: ${RATE}%"
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"

if [[ $CHECKS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}✅ 快速验证通过！CI工作流配置正常${NC}\n"
    exit 0
else
    echo -e "${RED}❌ 快速验证失败！发现 $CHECKS_FAILED 个问题${NC}\n"
    exit 1
fi
