#!/bin/bash
# workflow_guard_enforcer.sh - 集成工作流硬闸与Claude Hooks
# 在Claude操作前检查工作流激活状态

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 获取git仓库根目录
if ! GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
    # 不在git仓库，跳过检查
    exit 0
fi

# 获取当前分支
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

# 如果在main/master分支，不需要工作流
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ] || [ -z "$CURRENT_BRANCH" ]; then
    exit 0
fi

# 检查是否需要工作流（开发分支）
NEEDS_WORKFLOW=false
case "$CURRENT_BRANCH" in
    feature/*|hotfix/*|release/*|bugfix/*|develop)
        NEEDS_WORKFLOW=true
        ;;
esac

if [ "$NEEDS_WORKFLOW" = false ]; then
    exit 0
fi

# 检查ACTIVE文件
if [ ! -f "$GIT_ROOT/.workflow/ACTIVE" ]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" >&2
    echo -e "${YELLOW}⚠️  工作流未激活${NC}" >&2
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" >&2
    echo "" >&2
    echo -e "${YELLOW}当前分支: ${CURRENT_BRANCH}${NC}" >&2
    echo -e "${YELLOW}Claude Enhancer要求激活工作流才能进行开发${NC}" >&2
    echo "" >&2
    echo -e "${GREEN}请运行: ce start \"任务描述\"${NC}" >&2
    echo "" >&2

    # 非阻塞提醒（只是警告，不阻止操作）
    exit 0
fi

# 读取工作流信息
TICKET=$(grep "^ticket=" "$GIT_ROOT/.workflow/ACTIVE" | cut -d= -f2 || echo "unknown")
PHASE=$(grep "^phase=" "$GIT_ROOT/.workflow/ACTIVE" | cut -d= -f2 || echo "P1")

# 输出当前工作流状态（供其他hook使用）
echo "WORKFLOW_ACTIVE=true"
echo "WORKFLOW_TICKET=$TICKET"
echo "WORKFLOW_PHASE=$PHASE"

exit 0