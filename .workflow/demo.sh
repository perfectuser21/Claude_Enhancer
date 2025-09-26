#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Workflow Executor演示脚本
# =============================================================================

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly EXECUTOR="${SCRIPT_DIR}/executor.sh"

# 颜色输出
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

echo -e "${CYAN}======================================${NC}"
echo -e "${BOLD}🚀 Claude Enhancer 5.0 工作流演示${NC}"
echo -e "${CYAN}======================================${NC}"

echo -e "\n${YELLOW}1. 显示工作流执行引擎帮助${NC}"
read -p "按Enter继续..."
"${EXECUTOR}" help

echo -e "\n${YELLOW}2. 查看当前工作流状态${NC}"
read -p "按Enter继续..."
"${EXECUTOR}" status

echo -e "\n${YELLOW}3. 跳转到P3阶段演示${NC}"
read -p "按Enter继续..."
"${EXECUTOR}" goto P3

echo -e "\n${YELLOW}4. 查看P3阶段的智能推荐${NC}"
read -p "按Enter继续..."
"${EXECUTOR}" suggest

echo -e "\n${YELLOW}5. 手动触发Claude Hooks集成${NC}"
read -p "按Enter继续..."
"${EXECUTOR}" hooks

echo -e "\n${YELLOW}6. 重置回P1阶段${NC}"
read -p "按Enter继续..."
"${EXECUTOR}" reset

echo -e "\n${GREEN}✅ 演示完成！${NC}"
echo -e "${BLUE}现在你可以使用以下命令：${NC}"
echo -e "  • ${EXECUTOR} status     - 查看状态"
echo -e "  • ${EXECUTOR} validate   - 验证当前阶段"
echo -e "  • ${EXECUTOR} next       - 进入下一阶段"
echo -e "  • ${EXECUTOR} suggest    - 获取智能建议"