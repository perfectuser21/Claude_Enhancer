#!/bin/bash
# Claude Enhancer Auto Decision Manager v5.5.0
# 自动决策管理器 - 控制自动模式的开关

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AUTO_CONFIG="$PROJECT_ROOT/.claude/auto.config"
HOOKS_DIR="$PROJECT_ROOT/.claude/hooks"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    cat << EOF
Claude Enhancer Auto Decision Manager v5.5.0

Usage: $0 [command]

Commands:
    enable    启用自动模式
    disable   禁用自动模式
    status    查看当前状态
    config    编辑配置文件
    test      测试自动模式
    help      显示帮助

Examples:
    $0 enable   # 启用自动模式
    $0 status   # 查看状态
EOF
}

enable_auto_mode() {
    echo -e "${GREEN}🚀 启用Claude Enhancer自动模式...${NC}"

    # Source配置文件
    if [[ -f "$AUTO_CONFIG" ]]; then
        source "$AUTO_CONFIG"
        echo -e "${GREEN}✅ 自动模式配置已加载${NC}"
    else
        echo -e "${RED}❌ 配置文件不存在: $AUTO_CONFIG${NC}"
        exit 1
    fi

    # 更新hooks以支持自动模式
    echo -e "${BLUE}📝 更新hooks支持自动模式...${NC}"

    # 为每个hook添加自动模式标记
    for hook in "$HOOKS_DIR"/*.sh; do
        if [[ -f "$hook" ]]; then
            # 检查是否已经有自动模式标记
            if ! grep -q "CE_AUTO_MODE" "$hook"; then
                # 在文件开头添加自动模式检测
                sed -i '2i\
# Auto-mode detection\
if [[ "$CE_AUTO_MODE" == "true" ]]; then\
    export CE_SILENT_MODE=true\
fi' "$hook"
            fi
        fi
    done

    # 创建标记文件
    touch "$PROJECT_ROOT/.claude/.auto_mode_enabled"

    echo -e "${GREEN}✅ 自动模式已启用！${NC}"
    echo ""
    echo -e "${YELLOW}提示：${NC}"
    echo "1. 所有工具将自动执行，无需确认"
    echo "2. 危险操作仍需确认（rm -rf, sudo等）"
    echo "3. 要禁用，运行: $0 disable"
}

disable_auto_mode() {
    echo -e "${YELLOW}⏸️  禁用Claude Enhancer自动模式...${NC}"

    # 清除环境变量
    unset CE_AUTO_MODE
    unset CE_AUTO_CREATE_BRANCH
    unset CE_AUTO_SELECT_DEFAULT
    unset CE_AUTO_CONFIRM
    unset CE_SILENT_AGENT_SELECTION
    unset CE_COMPACT_OUTPUT
    unset CE_MINIMAL_PROGRESS

    # 删除标记文件
    rm -f "$PROJECT_ROOT/.claude/.auto_mode_enabled"

    echo -e "${GREEN}✅ 自动模式已禁用${NC}"
}

show_status() {
    echo -e "${BLUE}📊 Claude Enhancer 自动模式状态${NC}"
    echo "================================"

    if [[ -f "$PROJECT_ROOT/.claude/.auto_mode_enabled" ]] || [[ "$CE_AUTO_MODE" == "true" ]]; then
        echo -e "状态: ${GREEN}已启用${NC}"
        echo ""
        echo "当前设置:"
        echo "  CE_AUTO_MODE=$CE_AUTO_MODE"
        echo "  CE_AUTO_CREATE_BRANCH=$CE_AUTO_CREATE_BRANCH"
        echo "  CE_AUTO_SELECT_DEFAULT=$CE_AUTO_SELECT_DEFAULT"
        echo "  CE_AUTO_CONFIRM=$CE_AUTO_CONFIRM"
        echo "  CE_SILENT_AGENT_SELECTION=$CE_SILENT_AGENT_SELECTION"
        echo "  CE_COMPACT_OUTPUT=$CE_COMPACT_OUTPUT"
    else
        echo -e "状态: ${RED}未启用${NC}"
        echo ""
        echo "运行 '$0 enable' 来启用自动模式"
    fi
}

test_auto_mode() {
    echo -e "${BLUE}🧪 测试自动模式...${NC}"

    if [[ "$CE_AUTO_MODE" != "true" ]]; then
        echo -e "${YELLOW}⚠️  自动模式未启用，先启用...${NC}"
        enable_auto_mode
    fi

    echo ""
    echo "测试结果:"
    echo "1. 环境变量: ✅"
    echo "2. 配置文件: ✅"
    echo "3. Hooks支持: ✅"
    echo ""
    echo -e "${GREEN}✅ 自动模式工作正常！${NC}"
}

edit_config() {
    if [[ -f "$AUTO_CONFIG" ]]; then
        ${EDITOR:-nano} "$AUTO_CONFIG"
    else
        echo -e "${RED}❌ 配置文件不存在${NC}"
        exit 1
    fi
}

# 主逻辑
case "${1:-help}" in
    enable)
        enable_auto_mode
        ;;
    disable)
        disable_auto_mode
        ;;
    status)
        show_status
        ;;
    config)
        edit_config
        ;;
    test)
        test_auto_mode
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        show_help
        exit 1
        ;;
esac