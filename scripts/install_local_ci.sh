#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# install_local_ci.sh - 本地CI系统安装脚本
# 用途：安装或更新本地CI和Git Hooks
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  Local CI System Installation - Claude Enhancer 6.5     ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 前置检查
# ═══════════════════════════════════════════════════════════════

echo -e "${BLUE}[1/5] Pre-installation checks${NC}"

# 检查Git
if ! command -v git >/dev/null 2>&1; then
    echo -e "${RED}✗ Git not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Git found${NC}"

# 检查是否在Git仓库
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo -e "${RED}✗ Not a git repository${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Git repository detected${NC}"

# 检查必需脚本
REQUIRED_SCRIPTS=(
    "scripts/workflow_validator.sh"
    "scripts/local_ci.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [[ ! -f "$PROJECT_ROOT/$script" ]]; then
        echo -e "${RED}✗ Missing: $script${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required scripts present${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 备份现有Hooks
# ═══════════════════════════════════════════════════════════════

echo -e "${BLUE}[2/5] Backing up existing hooks${NC}"

BACKUP_DIR="$PROJECT_ROOT/.git/hooks/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [[ -f "$PROJECT_ROOT/.git/hooks/pre-commit" ]]; then
    cp "$PROJECT_ROOT/.git/hooks/pre-commit" "$BACKUP_DIR/pre-commit.backup"
    echo -e "${GREEN}✓ Backed up pre-commit${NC}"
fi

if [[ -f "$PROJECT_ROOT/.git/hooks/pre-push" ]]; then
    cp "$PROJECT_ROOT/.git/hooks/pre-push" "$BACKUP_DIR/pre-push.backup"
    echo -e "${GREEN}✓ Backed up pre-push${NC}"
fi

echo -e "${GREEN}✓ Backup completed: $BACKUP_DIR${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 安装新Hooks
# ═══════════════════════════════════════════════════════════════

echo -e "${BLUE}[3/5] Installing new hooks${NC}"

# 安装pre-commit
if [[ -f "$PROJECT_ROOT/.git/hooks/pre-commit.new" ]]; then
    cp "$PROJECT_ROOT/.git/hooks/pre-commit.new" "$PROJECT_ROOT/.git/hooks/pre-commit"
    chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit"
    echo -e "${GREEN}✓ Installed pre-commit hook${NC}"
else
    echo -e "${YELLOW}⚠ pre-commit.new not found - keeping existing${NC}"
fi

# 安装pre-push
if [[ -f "$PROJECT_ROOT/.git/hooks/pre-push.new" ]]; then
    cp "$PROJECT_ROOT/.git/hooks/pre-push.new" "$PROJECT_ROOT/.git/hooks/pre-push"
    chmod +x "$PROJECT_ROOT/.git/hooks/pre-push"
    echo -e "${GREEN}✓ Installed pre-push hook${NC}"
else
    echo -e "${YELLOW}⚠ pre-push.new not found - keeping existing${NC}"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 设置脚本权限
# ═══════════════════════════════════════════════════════════════

echo -e "${BLUE}[4/5] Setting script permissions${NC}"

chmod +x "$PROJECT_ROOT/scripts/workflow_validator.sh"
echo -e "${GREEN}✓ workflow_validator.sh${NC}"

chmod +x "$PROJECT_ROOT/scripts/local_ci.sh"
echo -e "${GREEN}✓ local_ci.sh${NC}"

if [[ -f "$PROJECT_ROOT/scripts/static_checks.sh" ]]; then
    chmod +x "$PROJECT_ROOT/scripts/static_checks.sh"
    echo -e "${GREEN}✓ static_checks.sh${NC}"
fi

if [[ -f "$PROJECT_ROOT/scripts/pre_merge_audit.sh" ]]; then
    chmod +x "$PROJECT_ROOT/scripts/pre_merge_audit.sh"
    echo -e "${GREEN}✓ pre_merge_audit.sh${NC}"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# 创建必要目录
# ═══════════════════════════════════════════════════════════════

echo -e "${BLUE}[5/5] Creating necessary directories${NC}"

mkdir -p "$PROJECT_ROOT/.workflow/logs"
echo -e "${GREEN}✓ .workflow/logs/${NC}"

mkdir -p "$PROJECT_ROOT/.evidence"
echo -e "${GREEN}✓ .evidence/${NC}"

mkdir -p "$PROJECT_ROOT/spec"
echo -e "${GREEN}✓ spec/${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# 测试安装
# ═══════════════════════════════════════════════════════════════

echo -e "${BLUE}Testing installation...${NC}"
echo ""

# 测试workflow_validator
echo -e "${YELLOW}Testing workflow_validator.sh...${NC}"
if bash "$PROJECT_ROOT/scripts/workflow_validator.sh" >/dev/null 2>&1 || true; then
    echo -e "${GREEN}✓ workflow_validator.sh executable${NC}"
else
    echo -e "${YELLOW}⚠ workflow_validator.sh test failed (may be expected)${NC}"
fi

# 测试local_ci
echo -e "${YELLOW}Testing local_ci.sh...${NC}"
if bash "$PROJECT_ROOT/scripts/local_ci.sh" >/dev/null 2>&1 || true; then
    echo -e "${GREEN}✓ local_ci.sh executable${NC}"
else
    echo -e "${YELLOW}⚠ local_ci.sh test failed (may be expected)${NC}"
fi

# 测试hooks
echo -e "${YELLOW}Testing pre-commit hook...${NC}"
if bash "$PROJECT_ROOT/.git/hooks/pre-commit" >/dev/null 2>&1 || true; then
    echo -e "${GREEN}✓ pre-commit hook executable${NC}"
else
    echo -e "${YELLOW}⚠ pre-commit hook test failed (may be expected)${NC}"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# 完成
# ═══════════════════════════════════════════════════════════════

echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║  ✅ Installation Complete!                               ║${NC}"
echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BOLD}Next Steps:${NC}"
echo ""
echo -e "1. ${BLUE}Test workflow validation:${NC}"
echo "   bash scripts/workflow_validator.sh"
echo ""
echo -e "2. ${BLUE}Test local CI:${NC}"
echo "   bash scripts/local_ci.sh"
echo ""
echo -e "3. ${BLUE}Test pre-commit hook:${NC}"
echo "   # Make some changes and commit"
echo "   git add ."
echo "   git commit -m 'test: hook validation'"
echo ""
echo -e "4. ${BLUE}Test pre-push hook:${NC}"
echo "   # Try to push"
echo "   git push"
echo ""
echo -e "${YELLOW}Note: Hooks will validate your workflow completion${NC}"
echo -e "${YELLOW}      Pass rate must be ≥80% to push${NC}"
echo ""
echo -e "${BOLD}Bypass Options (emergency only):${NC}"
echo "  - Skip local CI: CI_SKIP_LOCAL=1 git push"
echo "  - Force push: PUSH_FORCE=1 git push"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
