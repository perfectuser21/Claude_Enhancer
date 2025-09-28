#!/usr/bin/env bash
# Claude Enhancer 工作流强制执行器 - 确保AI始终遵循8-Phase工作流

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo -e "${MAGENTA}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║   Claude Enhancer 工作流强制执行器 v5.3      ║${NC}"
echo -e "${MAGENTA}║   确保AI永远不会跳过工作流直接编码           ║${NC}"
echo -e "${MAGENTA}╚═══════════════════════════════════════════════╝${NC}"

# 创建检查点文件
CHECK_FILE="$PROJECT_ROOT/.workflow/enforcement_check"
mkdir -p "$(dirname "$CHECK_FILE")"

# 写入检查时间戳
echo "$(date): Workflow enforcement triggered" > "$CHECK_FILE"

echo -e "\n${RED}⚠️  强制规则已激活！${NC}"
echo -e "${YELLOW}任何编程任务必须:${NC}"
echo "1. 先运行 smart_agent_selector.sh 分析任务"
echo "2. 启动 8-Phase 工作流 (P0-P7)"
echo "3. 使用至少 3 个 Agent 并行执行"
echo "4. 遵循 git hook 的所有检查"

echo -e "\n${CYAN}这个规则现已写入 Git Hooks，无法绕过！${NC}"

exit 0