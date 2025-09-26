#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
# Claude Enhancer 5.0 - Dashboard Launcher
# 工作流监控面板启动器
# ═══════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m'

clear
echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${WHITE}                    Claude Enhancer 5.0 - Dashboard Launcher                        ${NC}"
echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BOLD}${WHITE}选择监控面板模式:${NC}"
echo ""
echo -e "${GREEN}1) ${BOLD}基础监控面板${NC} ${CYAN}- 标准工作流监控${NC}"
echo -e "   ${BLUE}●${NC} 实时阶段状态显示"
echo -e "   ${BLUE}●${NC} Gates验证结果"
echo -e "   ${BLUE}●${NC} 并行任务监控"
echo -e "   ${BLUE}●${NC} 实时日志显示"
echo ""

echo -e "${YELLOW}2) ${BOLD}增强监控面板${NC} ${CYAN}- 包含性能分析和统计图表${NC}"
echo -e "   ${BLUE}●${NC} 性能趋势分析"
echo -e "   ${BLUE}●${NC} 阶段时间统计"
echo -e "   ${BLUE}●${NC} Agent执行统计"
echo -e "   ${BLUE}●${NC} 系统资源监控"
echo -e "   ${BLUE}●${NC} 智能告警系统"
echo ""

echo -e "${CYAN}3) ${BOLD}帮助信息${NC} ${CYAN}- 查看使用说明${NC}"
echo ""
echo -e "${RED}0) ${BOLD}退出${NC}"
echo ""

echo -e "${WHITE}请选择 [1-3, 0]: ${NC}"
read -n 1 choice
echo ""

case "$choice" in
    1)
        echo -e "${GREEN}启动基础监控面板...${NC}"
        sleep 1
        exec "$SCRIPT_DIR/dashboard.sh"
        ;;
    2)
        echo -e "${YELLOW}启动增强监控面板...${NC}"
        sleep 1
        exec "$SCRIPT_DIR/dashboard-enhanced.sh"
        ;;
    3)
        clear
        echo -e "${BOLD}${CYAN}Claude Enhancer 5.0 - Dashboard 使用说明${NC}"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
        echo ""

        echo -e "${BOLD}系统概览:${NC}"
        echo -e "Claude Enhancer 5.0 使用8-Phase工作流系统："
        echo -e "  P0 - Branch Creation: 分支创建和环境准备"
        echo -e "  P1 - Plan: 需求分析和任务规划"
        echo -e "  P2 - Skeleton: 架构设计和骨架构建"
        echo -e "  P3 - Implement: 功能实现和代码开发"
        echo -e "  P4 - Test: 测试验证和质量保证"
        echo -e "  P5 - Review: 代码审查和质量评估"
        echo -e "  P6 - Docs & Release: 文档完善和发布部署"
        echo ""

        echo -e "${BOLD}监控功能:${NC}"
        echo -e "  ${GREEN}●${NC} 实时阶段进度显示"
        echo -e "  ${GREEN}●${NC} Gates验证状态监控"
        echo -e "  ${GREEN}●${NC} 并行Agent任务跟踪"
        echo -e "  ${GREEN}●${NC} 系统性能统计"
        echo -e "  ${GREEN}●${NC} 实时日志流显示"
        echo -e "  ${GREEN}●${NC} 错误和警告分析"
        echo ""

        echo -e "${BOLD}快捷键:${NC}"
        echo -e "  ${YELLOW}R${NC} - 手动刷新数据"
        echo -e "  ${YELLOW}L${NC} - 查看完整日志"
        echo -e "  ${YELLOW}H${NC} - 显示帮助信息"
        echo -e "  ${YELLOW}Q${NC} - 退出监控程序"
        echo -e "  ${YELLOW}Ctrl+C${NC} - 强制退出"
        echo ""

        echo -e "${BOLD}文件位置:${NC}"
        echo -e "  配置文件: $SCRIPT_DIR/dashboard-config.yaml"
        echo -e "  日志文件: .workflow/executor.log"
        echo -e "  阶段状态: .phase/current"
        echo -e "  Gates状态: .gates/"
        echo ""

        echo -e "${DIM}按任意键返回主菜单...${NC}"
        read -n 1
        exec "$0"
        ;;
    0)
        echo -e "${GREEN}感谢使用Claude Enhancer 5.0 Dashboard!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}无效选择，请重新选择${NC}"
        sleep 1
        exec "$0"
        ;;
esac