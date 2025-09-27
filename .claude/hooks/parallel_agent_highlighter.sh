#!/bin/bash
# Claude Enhancer Parallel Agent Highlighter
# 高亮显示并行SubAgent调用

# 颜色定义
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 检查是否是Task工具调用
if [[ "$TOOL_NAME" == "Task" ]]; then
    # 检查是否有多个并行调用
    AGENT_COUNT=$(echo "$TOOL_PARAMS" | jq -r '.agents | length' 2>/dev/null || echo "1")

    if [[ "$AGENT_COUNT" -gt 1 ]]; then
        echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}${BOLD}⚡ 并行执行 ${AGENT_COUNT} 个 SubAgents${NC}"
        echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════════${NC}"

        # 获取当前Phase
        CURRENT_PHASE=$(cat .phase/current 2>/dev/null || echo "Unknown")
        echo -e "${BLUE}📍 当前Phase: ${BOLD}${CURRENT_PHASE}${NC}"

        # 显示agents列表
        echo -e "${GREEN}📋 Agents列表:${NC}"
        echo "$TOOL_PARAMS" | jq -r '.agents[]' 2>/dev/null | while read -r agent; do
            echo -e "   ${MAGENTA}▸${NC} ${BOLD}$agent${NC}"
        done

        echo -e "${CYAN}${BOLD}───────────────────────────────────────────────────────────────────${NC}"
        echo -e "${YELLOW}⏱️  开始并行执行...${NC}"
        echo ""
    fi
fi

# 如果是单个agent调用
if [[ "$AGENT_COUNT" == "1" ]]; then
    AGENT_NAME=$(echo "$TOOL_PARAMS" | jq -r '.subagent_type' 2>/dev/null || echo "unknown")
    if [[ "$AGENT_NAME" != "null" && "$AGENT_NAME" != "unknown" ]]; then
        echo -e "${GREEN}▶ 执行单个Agent: ${BOLD}${AGENT_NAME}${NC}"
    fi
fi