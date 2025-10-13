#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Pre-Push 质量门禁演练脚本（中文）
# ═══════════════════════════════════════════════════════════════
#
# 用途：无副作用测试质量门禁，不修改仓库状态
# 用法：
#   MOCK_SCORE=84 bash scripts/演练_pre_push_gates.sh
#   MOCK_COVERAGE=79 bash scripts/演练_pre_push_gates.sh
#   BRANCH=main MOCK_SIG=invalid bash scripts/演练_pre_push_gates.sh
#
# 模拟环境变量：
#   MOCK_SCORE     - 覆盖质量分数（默认：真实分数）
#   MOCK_COVERAGE  - 覆盖覆盖率百分比（默认：真实覆盖率）
#   MOCK_SIG       - 设为 "invalid" 模拟签名失败
#   BRANCH         - 覆盖当前分支名
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# 颜色常量
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 获取项目根目录
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# 加载 final gate 库
if [[ ! -f "$PROJECT_ROOT/.workflow/lib/final_gate.sh" ]]; then
    echo -e "${RED}❌ 错误：找不到 final_gate.sh 库文件${NC}"
    echo "期望位置：$PROJECT_ROOT/.workflow/lib/final_gate.sh"
    exit 1
fi

source "$PROJECT_ROOT/.workflow/lib/final_gate.sh"

# ═══════════════════════════════════════════════════════════════
# 演练横幅
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║         PRE-PUSH 质量门禁演练（无副作用）           ║${NC}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# 显示当前配置
echo -e "${BLUE}📋 演练配置：${NC}"
echo -e "   项目：$(basename "$PROJECT_ROOT")"
echo -e "   真实分支：$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '不可用')"
echo -e "   测试分支：${BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '不可用')}"
echo ""

# 如果设置了模拟变量，显示出来
if [[ -n "${MOCK_SCORE:-}" || -n "${MOCK_COVERAGE:-}" || -n "${MOCK_SIG:-}" ]]; then
    echo -e "${YELLOW}🎭 模拟模式激活：${NC}"
    [[ -n "${MOCK_SCORE:-}" ]] && echo -e "   MOCK_SCORE=${MOCK_SCORE}"
    [[ -n "${MOCK_COVERAGE:-}" ]] && echo -e "   MOCK_COVERAGE=${MOCK_COVERAGE}"
    [[ -n "${MOCK_SIG:-}" ]] && echo -e "   MOCK_SIG=${MOCK_SIG}"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# 执行 Final Gate 检查（只读模式）
# ═══════════════════════════════════════════════════════════════

echo -e "${CYAN}🔍 执行质量门禁检查...${NC}"
echo ""

if final_gate_check; then
    echo ""
    echo -e "${BOLD}${GREEN}✅ 演练结果：门禁会通过${NC}"
    exit 0
else
    echo ""
    echo -e "${BOLD}${RED}❌ 演练结果：门禁会阻止${NC}"
    exit 1
fi
