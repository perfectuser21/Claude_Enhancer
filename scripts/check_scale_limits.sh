#!/bin/bash
# Scale Limits Checker - 规模限制检查
# 防止hooks、scripts、docs数量失控
#
# Usage:
#   bash scripts/check_scale_limits.sh
#   bash scripts/check_scale_limits.sh --strict  # Exit 1 if exceeded

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
GATES_FILE="$PROJECT_ROOT/.workflow/gates.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

STRICT_MODE=false
if [[ "${1:-}" == "--strict" ]]; then
    STRICT_MODE=true
fi

# ============================================
# Read limits from gates.yml
# ============================================

if [[ ! -f "$GATES_FILE" ]]; then
    echo -e "${RED}❌ ERROR: gates.yml not found${NC}" >&2
    exit 1
fi

# Extract limits using grep (jq-free for portability)
HOOKS_MAX=$(grep "hooks_max:" "$GATES_FILE" | awk '{print $2}' | head -1)
SCRIPTS_MAX=$(grep "scripts_max:" "$GATES_FILE" | awk '{print $2}' | head -1)
DOCS_MAX=$(grep "docs_max:" "$GATES_FILE" | awk '{print $2}' | head -1)
TEMP_SIZE_MAX=$(grep "temp_size_mb_max:" "$GATES_FILE" | awk '{print $2}' | head -1)

# Defaults if not found
HOOKS_MAX=${HOOKS_MAX:-50}
SCRIPTS_MAX=${SCRIPTS_MAX:-90}
DOCS_MAX=${DOCS_MAX:-7}
TEMP_SIZE_MAX=${TEMP_SIZE_MAX:-10}

# ============================================
# Count current files
# ============================================

HOOKS_COUNT=$(find "$PROJECT_ROOT/.claude/hooks" -type f -name "*.sh" 2>/dev/null | wc -l || echo 0)
SCRIPTS_COUNT=$(find "$PROJECT_ROOT/scripts" -type f -name "*.sh" 2>/dev/null | wc -l || echo 0)
DOCS_COUNT=$(find "$PROJECT_ROOT" -maxdepth 1 -type f -name "*.md" 2>/dev/null | wc -l || echo 0)

# Calculate .temp size
if [[ -d "$PROJECT_ROOT/.temp" ]]; then
    TEMP_SIZE_MB=$(du -sm "$PROJECT_ROOT/.temp" 2>/dev/null | cut -f1 || echo 0)
else
    TEMP_SIZE_MB=0
fi

# ============================================
# Check limits
# ============================================

VIOLATIONS=0

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Scale Limits Check - 规模限制检查"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check hooks
echo -n "Hooks:   $HOOKS_COUNT / $HOOKS_MAX ... "
if [ "$HOOKS_COUNT" -le "$HOOKS_MAX" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL (exceeded by $((HOOKS_COUNT - HOOKS_MAX)))${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Check scripts
echo -n "Scripts: $SCRIPTS_COUNT / $SCRIPTS_MAX ... "
if [ "$SCRIPTS_COUNT" -le "$SCRIPTS_MAX" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL (exceeded by $((SCRIPTS_COUNT - SCRIPTS_MAX)))${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Check docs
echo -n "Docs:    $DOCS_COUNT / $DOCS_MAX ... "
if [ "$DOCS_COUNT" -le "$DOCS_MAX" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL (exceeded by $((DOCS_COUNT - DOCS_MAX)))${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Check .temp size
echo -n ".temp/:  ${TEMP_SIZE_MB}MB / ${TEMP_SIZE_MAX}MB ... "
if [ "$TEMP_SIZE_MB" -le "$TEMP_SIZE_MAX" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL (exceeded by $((TEMP_SIZE_MB - TEMP_SIZE_MAX))MB)${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════"

# ============================================
# Summary
# ============================================

if [ $VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✅ All scale limits are within bounds${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $VIOLATIONS scale limit(s) exceeded${NC}"
    echo ""

    if [ $VIOLATIONS -gt 0 ]; then
        echo -e "${YELLOW}Recommended actions:${NC}"
        echo ""

        if [ "$HOOKS_COUNT" -gt "$HOOKS_MAX" ]; then
            echo "Hooks exceeded:"
            echo "  1. Review .claude/hooks/ for duplicates or obsolete files"
            echo "  2. Move deprecated hooks to archive/"
            echo "  3. Consolidate similar functionality"
            echo ""
        fi

        if [ "$SCRIPTS_COUNT" -gt "$SCRIPTS_MAX" ]; then
            echo "Scripts exceeded:"
            echo "  1. Review scripts/ for one-time migration/fix scripts"
            echo "  2. Delete benchmark/test scripts if not actively used"
            echo "  3. Consolidate utility scripts"
            echo ""
        fi

        if [ "$DOCS_COUNT" -gt "$DOCS_MAX" ]; then
            echo "Root docs exceeded:"
            echo "  1. Move detailed docs to docs/ subdirectory"
            echo "  2. Only keep 7 core docs in root: README, CLAUDE, INSTALLATION,"
            echo "     ARCHITECTURE, CONTRIBUTING, CHANGELOG, LICENSE"
            echo "  3. Move analysis/reports to .temp/"
            echo ""
        fi

        if [ "$TEMP_SIZE_MB" -gt "$TEMP_SIZE_MAX" ]; then
            echo ".temp/ size exceeded:"
            echo "  1. Run: bash scripts/comprehensive_cleanup.sh"
            echo "  2. Delete old logs and reports (>7 days)"
            echo "  3. Clear test artifacts"
            echo ""
        fi
    fi

    if [ "$STRICT_MODE" = true ]; then
        echo -e "${RED}🚨 STRICT MODE: Blocking due to scale limit violations${NC}"
        echo ""
        exit 1
    else
        echo -e "${YELLOW}⚠️  WARNING MODE: Please address violations before Phase 4/7${NC}"
        echo ""
        exit 0  # Don't block in warning mode
    fi
fi
