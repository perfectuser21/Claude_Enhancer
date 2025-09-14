#!/bin/bash
# VibePilot V2 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚁 VibePilot V2 启动脚本${NC}"
echo "============================================"

# 检查Python环境
echo -e "${YELLOW}📋 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"

# 检查Claude Code
echo -e "${YELLOW}📋 检查Claude Code...${NC}"
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✅ Claude Code 可用${NC}"
else
    echo -e "${YELLOW}⚠️ Claude Code 未找到，将在受限模式下运行${NC}"
fi

# 检查依赖
echo -e "${YELLOW}📋 检查Python依赖...${NC}"
MISSING_DEPS=()

# 检查必需的包
for package in "asyncio" "pathlib" "dataclasses" "enum"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        MISSING_DEPS+=("$package")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}❌ 缺少依赖: ${MISSING_DEPS[*]}${NC}"
    echo "请安装缺少的依赖包"
    exit 1
else
    echo -e "${GREEN}✅ 所有依赖已满足${NC}"
fi

# 检查目录结构
echo -e "${YELLOW}📋 检查目录结构...${NC}"
REQUIRED_DIRS=("core" "main" "modules" "features")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ 缺少目录: $dir${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ 目录结构完整${NC}"

# 创建工作空间目录
echo -e "${YELLOW}📋 准备工作空间...${NC}"
mkdir -p /tmp/vibepilot_workspaces
echo -e "${GREEN}✅ 工作空间目录已准备${NC}"

echo
echo -e "${BLUE}🚀 VibePilot V2 启动选项:${NC}"
echo "1) 🤖 聊天模式 (推荐)"
echo "2) 📊 系统状态"
echo "3) 📁 工作空间管理"
echo "4) 🎯 直接执行任务"
echo "5) ❓ 帮助信息"
echo "6) 🔧 调试模式"

echo
read -p "请选择启动模式 [1-6]: " choice

case $choice in
    1)
        echo -e "${GREEN}🤖 启动聊天模式...${NC}"
        python3 vp_v2.py chat
        ;;
    2)
        echo -e "${GREEN}📊 显示系统状态...${NC}"
        python3 vp_v2.py status
        ;;
    3)
        echo -e "${GREEN}📁 显示工作空间...${NC}"
        python3 vp_v2.py workspaces
        ;;
    4)
        echo -e "${GREEN}🎯 任务执行模式${NC}"
        read -p "请输入任务描述: " task_desc
        if [ -n "$task_desc" ]; then
            python3 vp_v2.py task "$task_desc"
        else
            echo -e "${RED}❌ 任务描述不能为空${NC}"
        fi
        ;;
    5)
        echo -e "${GREEN}❓ 显示帮助信息...${NC}"
        python3 vp_v2.py help
        ;;
    6)
        echo -e "${GREEN}🔧 启动调试模式...${NC}"
        export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
        python3 -c "
import sys
print('🔧 调试信息:')
print(f'Python路径: {sys.path[0]}')
print(f'工作目录: $(pwd)')
print('📦 导入测试:')
try:
    from main.vibepilot_v2 import VibePilotV2
    print('✅ VibePilotV2 导入成功')
except Exception as e:
    print(f'❌ VibePilotV2 导入失败: {e}')

try:
    from core.ai_pool import AIPool
    print('✅ AIPool 导入成功')
except Exception as e:
    print(f'❌ AIPool 导入失败: {e}')
"
        echo -e "${YELLOW}调试完成，使用 'python3 vp_v2.py' 手动启动${NC}"
        ;;
    *)
        echo -e "${RED}❌ 无效选择，启动默认聊天模式...${NC}"
        python3 vp_v2.py chat
        ;;
esac

echo
echo -e "${BLUE}👋 VibePilot V2 会话结束${NC}"