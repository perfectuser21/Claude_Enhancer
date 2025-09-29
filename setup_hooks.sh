#!/bin/bash
# Setup hooks - 配置git使用本地hooks
# 可选参数: --global (全局安装) --uninstall (卸载)

set -euo pipefail

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOOKS_DIR="$SCRIPT_DIR/hooks"

# 检查参数
GLOBAL_INSTALL=false
UNINSTALL=false

for arg in "$@"; do
    case $arg in
        --global)
            GLOBAL_INSTALL=true
            ;;
        --uninstall)
            UNINSTALL=true
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --global    全局安装（影响所有git仓库）"
            echo "  --uninstall 卸载hooks配置"
            echo "  --help      显示帮助"
            echo ""
            echo "默认: 仅为当前仓库安装"
            exit 0
            ;;
    esac
done

# 卸载模式
if [ "$UNINSTALL" = true ]; then
    echo -e "${YELLOW}🔄 正在卸载hooks配置...${NC}"

    if [ "$GLOBAL_INSTALL" = true ]; then
        git config --global --unset core.hooksPath || true
        echo -e "${GREEN}✅ 已移除全局hooks配置${NC}"
    else
        git config --unset core.hooksPath || true
        echo -e "${GREEN}✅ 已移除本地hooks配置${NC}"
    fi

    echo ""
    echo -e "${GREEN}hooks配置已清除，git将使用默认的.git/hooks目录${NC}"
    exit 0
fi

# 检查hooks目录
if [ ! -d "$HOOKS_DIR" ]; then
    echo -e "${RED}❌ 错误：hooks目录不存在: $HOOKS_DIR${NC}"
    exit 1
fi

# 检查pre-push hook
if [ ! -f "$HOOKS_DIR/pre-push" ]; then
    echo -e "${RED}❌ 错误：pre-push hook不存在${NC}"
    exit 1
fi

# 确保hooks可执行
chmod +x "$HOOKS_DIR/pre-push"

# 安装hooks
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}       Claude Enhancer 工作流硬闸 - Hook安装器${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$GLOBAL_INSTALL" = true ]; then
    echo -e "${YELLOW}📦 正在进行全局安装...${NC}"
    git config --global core.hooksPath "$HOOKS_DIR"
    echo -e "${GREEN}✅ 全局hooks已配置！${NC}"
    echo -e "   路径: $HOOKS_DIR"
    echo -e "   影响: 所有git仓库"
else
    echo -e "${YELLOW}📦 正在为当前仓库安装...${NC}"
    git config core.hooksPath "$HOOKS_DIR"
    echo -e "${GREEN}✅ 本地hooks已配置！${NC}"
    echo -e "   路径: $HOOKS_DIR"
    echo -e "   影响: 仅当前仓库"
fi

echo ""
echo -e "${GREEN}🎯 已启用的守护功能：${NC}"
echo "  • pre-push: 推送前检查工作流激活状态"
echo "    - feature/* 分支必须激活工作流"
echo "    - hotfix/* 分支必须激活工作流"
echo "    - release/* 分支必须激活工作流"
echo ""
echo -e "${GREEN}📝 使用指南：${NC}"
echo "  1. 开始工作: ce start \"任务描述\""
echo "  2. 正常开发: git add/commit/push"
echo "  3. 结束工作: ce stop"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "  • 查看当前配置: git config core.hooksPath"
echo "  • 卸载hooks: $0 --uninstall"
echo "  • 切换到全局: $0 --global"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"