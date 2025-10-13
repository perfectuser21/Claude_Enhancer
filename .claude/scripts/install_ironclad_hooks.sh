#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# IRONCLAD HOOKS INSTALLER
# Claude Enhancer 5.0 - Install unbypassable Git hooks
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo -e "${BOLD}🔒 Installing Ironclad Git Hooks${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Backup existing hooks
echo -e "\n${CYAN}[BACKUP]${NC}"

backup_dir="$HOOKS_DIR/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

for hook in pre-commit pre-push post-commit commit-msg; do
    if [ -f "$HOOKS_DIR/$hook" ]; then
        cp "$HOOKS_DIR/$hook" "$backup_dir/"
        echo -e "${GREEN}✓ Backed up: $hook${NC}"
    fi
done

echo -e "Backup location: $backup_dir"

# Install new hooks
echo -e "\n${CYAN}[INSTALLATION]${NC}"

installed=0

for hook in pre-commit pre-push post-commit; do
    if [ -f "$HOOKS_DIR/${hook}.new" ]; then
        mv "$HOOKS_DIR/${hook}.new" "$HOOKS_DIR/${hook}"
        chmod +x "$HOOKS_DIR/${hook}"
        echo -e "${GREEN}✓ Installed: $hook${NC}"
        ((installed++))
    else
        echo -e "${YELLOW}⚠️  Not found: ${hook}.new (skipping)${NC}"
    fi
done

# Verify installation
echo -e "\n${CYAN}[VERIFICATION]${NC}"

verified=0

for hook in pre-commit pre-push post-commit; do
    if [ -f "$HOOKS_DIR/$hook" ] && [ -x "$HOOKS_DIR/$hook" ]; then
        # Check for bypass detection
        if grep -q "SKIP_HOOKS" "$HOOKS_DIR/$hook" 2>/dev/null; then
            echo -e "${GREEN}✓ $hook: Installed with bypass detection${NC}"
            ((verified++))
        else
            echo -e "${YELLOW}⚠️  $hook: Missing bypass detection${NC}"
        fi
    else
        echo -e "${RED}❌ $hook: Not properly installed${NC}"
    fi
done

# Security hardening
echo -e "\n${CYAN}[HARDENING]${NC}"

# Prevent accidental deletion
for hook in pre-commit pre-push; do
    if [ -f "$HOOKS_DIR/$hook" ]; then
        # Make hooks harder to modify (but not impossible for legitimate updates)
        chmod 555 "$HOOKS_DIR/$hook"
        echo -e "${GREEN}✓ Hardened: $hook (read-only)${NC}"
    fi
done

# Create integrity marker
integrity_file="$HOOKS_DIR/.integrity"
{
    echo "# Git Hooks Integrity Marker"
    echo "installed_at=$(date -Iseconds)"
    echo "version=ironclad-v1.0"
    for hook in pre-commit pre-push post-commit; do
        if [ -f "$HOOKS_DIR/$hook" ]; then
            hash=$(sha256sum "$HOOKS_DIR/$hook" | cut -d' ' -f1)
            echo "${hook}_hash=$hash"
        fi
    done
} > "$integrity_file"

echo -e "${GREEN}✓ Created integrity marker${NC}"

# Summary
echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BOLD}${GREEN}✅ INSTALLATION COMPLETE${NC}"
echo -e "${CYAN}Installed hooks: $installed${NC}"
echo -e "${CYAN}Verified hooks: $verified${NC}"
echo ""
echo -e "${YELLOW}Security Features:${NC}"
echo "  ✓ Bypass attempt detection (env vars, --no-verify)"
echo "  ✓ Hook tampering detection (symlinks, redirects)"
echo "  ✓ Security scanning (secrets, keys, credentials)"
echo "  ✓ Syntax validation (shell, python, javascript)"
echo "  ✓ Branch protection (main/master/production)"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Test hooks: .claude/scripts/test_bypass_prevention.sh"
echo "  2. Review backup: $backup_dir"
echo "  3. Make a test commit to verify functionality"
echo ""

exit 0
