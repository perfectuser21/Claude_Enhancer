#!/bin/bash
# Claude Enhancer v6.0 - GitHub Branch Protection 强化脚本
# 配置 Required Status Checks 和完整的保护规则

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
REPO="perfectuser21/Claude_Enhancer"
BRANCH="main"

echo -e "${BLUE}🚀 Claude Enhancer v6.0 - GitHub Protection Setup${NC}"
echo "================================================"

# 检查 gh 命令
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ 需要安装 GitHub CLI (gh)${NC}"
    echo "请运行: brew install gh 或访问 https://cli.github.com/"
    exit 1
fi

# 检查登录状态
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️ 需要登录 GitHub${NC}"
    gh auth login
fi

echo -e "\n${BLUE}📋 当前保护状态：${NC}"
gh api repos/${REPO}/branches/${BRANCH}/protection 2>/dev/null || echo "未配置保护"

# 创建保护配置
echo -e "\n${BLUE}🔧 配置 Branch Protection...${NC}"

# 完整的保护配置
PROTECTION_CONFIG='{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "ce-unified-gates",
      "security-scan",
      "test-suite"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "allow_fork_syncing": false
}'

# 应用保护规则
echo -e "${BLUE}📝 应用保护规则...${NC}"
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/${REPO}/branches/${BRANCH}/protection \
  --input - <<< "$PROTECTION_CONFIG"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Branch Protection 配置成功！${NC}"
else
    echo -e "${RED}❌ 配置失败，请检查权限${NC}"
    exit 1
fi

# 保存配置快照
echo -e "\n${BLUE}💾 保存配置快照...${NC}"
SNAPSHOT_DIR=".workflow/backups"
mkdir -p "$SNAPSHOT_DIR"
SNAPSHOT_FILE="$SNAPSHOT_DIR/bp_snapshot_v6_$(date +%Y%m%d_%H%M%S).json"

gh api repos/${REPO}/branches/${BRANCH}/protection > "$SNAPSHOT_FILE"
ln -sf "$(basename "$SNAPSHOT_FILE")" "$SNAPSHOT_DIR/bp_snapshot_latest.json"

echo -e "${GREEN}✅ 配置已保存到: $SNAPSHOT_FILE${NC}"

# 验证配置
echo -e "\n${BLUE}🔍 验证配置...${NC}"
echo "Required Status Checks:"
gh api repos/${REPO}/branches/${BRANCH}/protection | jq '.required_status_checks.contexts'

echo -e "\n${GREEN}✅ GitHub Protection v6.0 配置完成！${NC}"
echo "================================================"
echo "已配置："
echo "  ✅ Required Status Checks (3个)"
echo "  ✅ Linear History 强制"
echo "  ✅ 禁止 Force Push"
echo "  ✅ 禁止删除分支"
echo ""
echo "注意：CI workflows 需要更新为新的名称："
echo "  - ce-unified-gates"
echo "  - security-scan"
echo "  - test-suite"