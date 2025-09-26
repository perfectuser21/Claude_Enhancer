#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
# Claude Enhancer 5.0 - Dashboard Test Script
# 工作流监控面板功能演示和测试
# ═══════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${CYAN}Claude Enhancer 5.0 - Dashboard Test & Demo${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BOLD}测试内容：${NC}"
echo -e "${GREEN}1.${NC} 验证dashboard文件完整性"
echo -e "${GREEN}2.${NC} 测试基础监控面板功能"
echo -e "${GREEN}3.${NC} 验证配置文件格式"
echo -e "${GREEN}4.${NC} 检查项目目录结构"
echo ""

# 1. 验证文件完整性
echo -e "${YELLOW}[1/4] 验证dashboard文件完整性...${NC}"

files=(
    "$SCRIPT_DIR/dashboard.sh"
    "$SCRIPT_DIR/dashboard-enhanced.sh"
    "$SCRIPT_DIR/dashboard-launcher.sh"
    "$SCRIPT_DIR/dashboard-config.yaml"
)

for file in "${files[@]}"; do
    if [[ -f "$file" ]] && [[ -x "$file" || "$file" == *.yaml ]]; then
        echo -e "${GREEN}✓${NC} $(basename "$file") - 存在且可执行"
    else
        echo -e "${RED}✗${NC} $(basename "$file") - 缺失或不可执行"
    fi
done
echo ""

# 2. 测试基础功能
echo -e "${YELLOW}[2/4] 测试基础监控面板功能...${NC}"

# 检查当前阶段
if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
    current_phase=$(cat "$PROJECT_ROOT/.phase/current" | tr -d '\n')
    echo -e "${GREEN}✓${NC} 当前阶段: $current_phase"
else
    echo -e "${YELLOW}!${NC} 阶段文件不存在，将使用默认值P0"
fi

# 检查Gates状态
gates_count=$(ls "$PROJECT_ROOT/.gates/"*.ok 2>/dev/null | wc -l)
echo -e "${GREEN}✓${NC} Gates状态: ${gates_count}/6 已通过"

# 检查日志文件
if [[ -f "$PROJECT_ROOT/.workflow/executor.log" ]]; then
    log_lines=$(wc -l < "$PROJECT_ROOT/.workflow/executor.log")
    echo -e "${GREEN}✓${NC} 日志文件: ${log_lines} 行"
else
    echo -e "${YELLOW}!${NC} 日志文件不存在"
fi
echo ""

# 3. 验证配置文件
echo -e "${YELLOW}[3/4] 验证配置文件格式...${NC}"

if [[ -f "$SCRIPT_DIR/dashboard-config.yaml" ]]; then
    echo -e "${GREEN}✓${NC} 配置文件存在"

    # 简单的YAML格式检查
    if grep -q "display:" "$SCRIPT_DIR/dashboard-config.yaml" && \
       grep -q "phases:" "$SCRIPT_DIR/dashboard-config.yaml" && \
       grep -q "gates:" "$SCRIPT_DIR/dashboard-config.yaml"; then
        echo -e "${GREEN}✓${NC} 配置文件格式正确"
    else
        echo -e "${YELLOW}!${NC} 配置文件格式可能有问题"
    fi
else
    echo -e "${YELLOW}!${NC} 配置文件不存在"
fi
echo ""

# 4. 检查目录结构
echo -e "${YELLOW}[4/4] 检查项目目录结构...${NC}"

required_dirs=(
    "$PROJECT_ROOT/.phase"
    "$PROJECT_ROOT/.gates"
    "$PROJECT_ROOT/.workflow"
    "$PROJECT_ROOT/src/workflow"
)

for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        echo -e "${GREEN}✓${NC} $(basename "$dir") 目录存在"
    else
        echo -e "${YELLOW}!${NC} 创建目录: $(basename "$dir")"
        mkdir -p "$dir"
    fi
done
echo ""

# 演示功能
echo -e "${BOLD}${BLUE}演示模式（可选）：${NC}"
echo -e "${CYAN}A)${NC} 启动基础监控面板 (5秒预览)"
echo -e "${CYAN}B)${NC} 启动增强监控面板 (5秒预览)"
echo -e "${CYAN}C)${NC} 显示配置信息"
echo -e "${CYAN}L)${NC} 启动选择器"
echo -e "${CYAN}Q)${NC} 退出测试"
echo ""

echo -e "${WHITE}选择演示模式 [A/B/C/L/Q]: ${NC}"
read -n 1 demo_choice
echo ""

case "$demo_choice" in
    'A'|'a')
        echo -e "${GREEN}启动基础监控面板预览...${NC}"
        echo -e "${YELLOW}(将在5秒后自动退出)${NC}"
        sleep 2
        timeout 5 "$SCRIPT_DIR/dashboard.sh" || echo -e "\n${GREEN}预览完成${NC}"
        ;;
    'B'|'b')
        echo -e "${GREEN}启动增强监控面板预览...${NC}"
        echo -e "${YELLOW}(将在5秒后自动退出)${NC}"
        sleep 2
        timeout 5 "$SCRIPT_DIR/dashboard-enhanced.sh" || echo -e "\n${GREEN}预览完成${NC}"
        ;;
    'C'|'c')
        echo -e "${GREEN}显示配置信息...${NC}"
        echo ""
        echo -e "${BOLD}当前配置：${NC}"
        echo -e "项目路径: $PROJECT_ROOT"
        echo -e "脚本路径: $SCRIPT_DIR"
        echo -e "当前阶段: $(cat "$PROJECT_ROOT/.phase/current" 2>/dev/null || echo "P0")"
        echo -e "Gates状态: $(ls "$PROJECT_ROOT/.gates/"*.ok 2>/dev/null | wc -l)/6"
        echo ""
        ;;
    'L'|'l')
        echo -e "${GREEN}启动Dashboard Launcher...${NC}"
        sleep 1
        exec "$SCRIPT_DIR/dashboard-launcher.sh"
        ;;
    'Q'|'q')
        echo -e "${GREEN}退出测试程序${NC}"
        ;;
    *)
        echo -e "${YELLOW}跳过演示模式${NC}"
        ;;
esac

echo ""
echo -e "${BOLD}${GREEN}测试完成！${NC}"
echo ""
echo -e "${BOLD}使用说明：${NC}"
echo -e "${CYAN}●${NC} 运行基础面板: ${YELLOW}./dashboard.sh${NC}"
echo -e "${CYAN}●${NC} 运行增强面板: ${YELLOW}./dashboard-enhanced.sh${NC}"
echo -e "${CYAN}●${NC} 运行启动器: ${YELLOW}./dashboard-launcher.sh${NC}"
echo -e "${CYAN}●${NC} 编辑配置: ${YELLOW}./dashboard-config.yaml${NC}"
echo ""
echo -e "${BOLD}注意事项：${NC}"
echo -e "• 监控面板会实时显示工作流状态"
echo -e "• 使用Ctrl+C可以随时退出面板"
echo -e "• 配置文件可以自定义显示选项"
echo -e "• 增强面板包含更多统计和分析功能"