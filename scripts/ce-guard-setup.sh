#!/bin/bash
# ce-guard-setup.sh - 设置工作流硬闸（快速版）
# 通过目录权限实现只读保护

set -euo pipefail

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT=$(git rev-parse --show-toplevel)
BRANCH=$(git branch --show-current)

# 操作模式
MODE=${1:-help}

case "$MODE" in
    lock)
        echo -e "${YELLOW}🔒 锁定工作目录（只读保护）...${NC}"

        # 检查是否在main分支
        if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
            # 锁定main分支
            echo "锁定主分支文件..."
            find "$PROJECT_ROOT" -type f -not -path "*/.git/*" -not -path "*/.workflow/*" \
                -exec chmod a-w {} \; 2>/dev/null || true

            # 创建锁定标记
            echo "$(date): Locked by $USER" > "$PROJECT_ROOT/.workflow/.locked"

            echo -e "${GREEN}✅ 主分支已锁定${NC}"
            echo -e "${YELLOW}现在必须运行 'ce start' 才能开始开发${NC}"
        else
            echo -e "${YELLOW}只在main分支执行锁定${NC}"
        fi
        ;;

    unlock)
        echo -e "${CYAN}🔓 解锁工作目录...${NC}"

        # 检查锁定标记
        if [ ! -f "$PROJECT_ROOT/.workflow/.locked" ]; then
            echo -e "${YELLOW}工作目录未锁定${NC}"
            exit 0
        fi

        # 恢复写权限
        find "$PROJECT_ROOT" -type f -not -path "*/.git/*" \
            -exec chmod u+w {} \; 2>/dev/null || true

        # 移除锁定标记
        rm -f "$PROJECT_ROOT/.workflow/.locked"

        echo -e "${GREEN}✅ 工作目录已解锁${NC}"
        ;;

    status)
        echo -e "${BLUE}📊 当前状态：${NC}"

        if [ -f "$PROJECT_ROOT/.workflow/.locked" ]; then
            echo "  🔒 工作目录: 已锁定"
            cat "$PROJECT_ROOT/.workflow/.locked"
        else
            echo "  🔓 工作目录: 未锁定"
        fi

        if [ -f "$PROJECT_ROOT/.workflow/ACTIVE" ]; then
            echo "  ✅ 工作流: 已激活"
            grep "^ticket=" "$PROJECT_ROOT/.workflow/ACTIVE" || true
        else
            echo "  ❌ 工作流: 未激活"
        fi

        echo "  🌿 当前分支: $BRANCH"
        ;;

    help|*)
        echo -e "${CYAN}用法：${NC}"
        echo "  $0 lock    - 锁定工作目录（只读）"
        echo "  $0 unlock  - 解锁工作目录"
        echo "  $0 status  - 查看当前状态"
        echo ""
        echo -e "${YELLOW}工作流程：${NC}"
        echo "  1. 在main分支: $0 lock"
        echo "  2. 开始开发: ce start \"任务\""
        echo "  3. 完成开发: ce stop"
        echo "  4. 紧急情况: $0 unlock"
        ;;
esac