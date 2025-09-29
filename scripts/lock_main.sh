#!/bin/bash
# lock_main.sh - 将main分支设置为只读，防止误操作
# 这是一个物理级别的保护措施

set -euo pipefail

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取git仓库根目录
if ! GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
    echo -e "${RED}❌ 错误：不在git仓库内${NC}"
    exit 1
fi

cd "$GIT_ROOT"

# 获取当前分支
CURRENT_BRANCH=$(git branch --show-current)

# 检查是否在main/master分支
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo -e "${YELLOW}⚠️  警告：当前不在主分支${NC}"
    echo -e "   当前分支: ${CURRENT_BRANCH}"
    echo -e "   建议先切换到主分支: git checkout main"
    echo ""
    read -p "是否继续锁定当前目录？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}已取消操作${NC}"
        exit 0
    fi
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}            🔒 主分支物理锁定工具${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 创建锁定标记文件
LOCK_FILE=".workflow/.main_locked"
mkdir -p .workflow
echo "$(date '+%Y-%m-%d %H:%M:%S') - Locked by $(whoami)" > "$LOCK_FILE"

# 统计文件数量
FILE_COUNT=$(find . -type f -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./.workflow/*" | wc -l)

echo -e "${YELLOW}🔍 正在锁定文件...${NC}"
echo -e "   将设置 ${FILE_COUNT} 个文件为只读"
echo ""

# 设置文件为只读（排除.git和特定目录）
find . -type f \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -not -path "./.workflow/*" \
    -not -name "*.log" \
    -exec chmod a-w {} \; 2>/dev/null || true

# 设置目录为只读（不能创建新文件）
find . -type d \
    -not -path "./.git" \
    -not -path "./.git/*" \
    -not -path "./node_modules" \
    -not -path "./node_modules/*" \
    -not -path "./.workflow" \
    -not -path "./.workflow/*" \
    -exec chmod a-w {} \; 2>/dev/null || true

echo -e "${GREEN}✅ 主分支已锁定！${NC}"
echo ""
echo -e "${RED}⛔ 当前状态：${NC}"
echo "  • 所有文件已设为只读"
echo "  • 无法修改任何文件内容"
echo "  • 无法创建新文件"
echo "  • 无法删除文件"
echo ""
echo -e "${YELLOW}⚠️  重要提示：${NC}"
echo "  1. 这是物理级别的保护，即使切换分支也会保持"
echo "  2. 只在紧急维护时使用 unlock_main.sh 解锁"
echo "  3. 正常开发请在feature分支进行"
echo ""
echo -e "${GREEN}📝 解锁方法：${NC}"
echo "  运行: ${GREEN}./scripts/unlock_main.sh${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"