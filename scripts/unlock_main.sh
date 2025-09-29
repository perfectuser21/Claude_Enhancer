#!/bin/bash
# unlock_main.sh - 解除main分支的只读锁定
# 警告：仅在紧急维护时使用

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

# 检查锁定标记
LOCK_FILE=".workflow/.main_locked"
if [ ! -f "$LOCK_FILE" ]; then
    echo -e "${YELLOW}⚠️  主分支未锁定，无需解锁${NC}"
    exit 0
fi

echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}            ⚠️  警告：即将解锁主分支${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${RED}🚨 解锁主分支是高风险操作！${NC}"
echo ""
echo "解锁后将允许："
echo "  • 修改主分支文件"
echo "  • 直接在主分支提交"
echo "  • 可能破坏生产代码"
echo ""
echo -e "${YELLOW}建议的安全做法：${NC}"
echo "  1. 创建feature分支进行修改"
echo "  2. 通过PR合并到主分支"
echo "  3. 仅在紧急热修复时解锁"
echo ""

# 确认操作
read -p "$(echo -e ${RED}确定要解锁主分支吗？请输入 'UNLOCK' 确认: ${NC})" CONFIRM

if [ "$CONFIRM" != "UNLOCK" ]; then
    echo -e "${GREEN}✅ 已取消解锁操作${NC}"
    echo "主分支保持锁定状态"
    exit 0
fi

echo ""
echo -e "${YELLOW}🔓 正在解锁文件...${NC}"

# 统计文件数量
FILE_COUNT=$(find . -type f -not -path "./.git/*" -not -path "./node_modules/*" | wc -l)
echo -e "   将恢复 ${FILE_COUNT} 个文件的写权限"

# 恢复文件写权限
find . -type f \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -exec chmod u+w {} \; 2>/dev/null || true

# 恢复目录写权限
find . -type d \
    -not -path "./.git" \
    -not -path "./.git/*" \
    -not -path "./node_modules" \
    -not -path "./node_modules/*" \
    -exec chmod u+w {} \; 2>/dev/null || true

# 记录解锁信息
echo "$(date '+%Y-%m-%d %H:%M:%S') - Unlocked by $(whoami)" >> "$LOCK_FILE.history"
rm -f "$LOCK_FILE"

echo ""
echo -e "${GREEN}✅ 主分支已解锁！${NC}"
echo ""
echo -e "${YELLOW}⚠️  当前状态：${NC}"
echo "  • 文件可以修改"
echo "  • 可以创建新文件"
echo "  • 可以删除文件"
echo ""
echo -e "${RED}🚨 重要提醒：${NC}"
echo "  1. 完成紧急修复后，请立即重新锁定"
echo "  2. 运行: ./scripts/lock_main.sh"
echo "  3. 避免直接在主分支进行常规开发"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"