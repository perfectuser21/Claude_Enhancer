#!/usr/bin/env bash
# verify_skeleton.sh - Verify P2 skeleton completeness
set -euo pipefail

echo "=================================================="
echo "  CE CLI P2 Skeleton Verification"
echo "=================================================="
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${YELLOW}ℹ${NC} $1"; }

ROOT="/home/xx/dev/Claude Enhancer 5.0"
ERRORS=0

# Check main entry
echo "Checking main entry point..."
if [[ -f "$ROOT/ce.sh" ]]; then
    if [[ -x "$ROOT/ce.sh" ]]; then
        pass "ce.sh exists and is executable"
    else
        fail "ce.sh exists but not executable"
        ((ERRORS++))
    fi
else
    fail "ce.sh not found"
    ((ERRORS++))
fi
echo

# Check libraries
echo "Checking library files..."
LIBS=(
    "common.sh"
    "branch_manager.sh"
    "state_manager.sh"
    "phase_manager.sh"
    "gate_integrator.sh"
    "pr_automator.sh"
    "git_operations.sh"
    "conflict_detector.sh"
)

for lib in "${LIBS[@]}"; do
    if [[ -f "$ROOT/.workflow/cli/lib/$lib" ]]; then
        pass "$lib exists"
    else
        fail "$lib not found"
        ((ERRORS++))
    fi
done
echo

# Count functions
echo "Counting functions..."
TOTAL_FUNCTIONS=0
for lib in "${LIBS[@]}"; do
    if [[ -f "$ROOT/.workflow/cli/lib/$lib" ]]; then
        COUNT=$(grep -c "^[a-z_]*() {" "$ROOT/.workflow/cli/lib/$lib" || echo 0)
        TOTAL_FUNCTIONS=$((TOTAL_FUNCTIONS + COUNT))
        info "$lib: $COUNT functions"
    fi
done

# Add ce.sh functions
CE_FUNCS=$(grep -c "^ce_[a-z_]*() {" "$ROOT/ce.sh" || echo 0)
TOTAL_FUNCTIONS=$((TOTAL_FUNCTIONS + CE_FUNCS))
info "ce.sh: $CE_FUNCS functions"
echo
pass "Total functions: $TOTAL_FUNCTIONS"
echo

# Check for set -euo pipefail
echo "Checking error handling..."
MISSING_STRICT=0
for file in "$ROOT/ce.sh" "$ROOT/.workflow/cli/lib"/*.sh; do
    if [[ -f "$file" ]]; then
        if grep -q "set -euo pipefail" "$file"; then
            : # OK
        else
            fail "$(basename "$file") missing 'set -euo pipefail'"
            ((MISSING_STRICT++))
            ((ERRORS++))
        fi
    fi
done
if [[ $MISSING_STRICT -eq 0 ]]; then
    pass "All files have error handling"
fi
echo

# Check for exports
echo "Checking exported functions..."
EXPORT_COUNT=0
for lib in "$ROOT/.workflow/cli/lib"/*.sh; do
    if [[ -f "$lib" ]]; then
        COUNT=$(grep -c "^export -f" "$lib" || echo 0)
        EXPORT_COUNT=$((EXPORT_COUNT + COUNT))
    fi
done
info "Exported functions: $EXPORT_COUNT"
echo

# Check TODO markers
echo "Checking TODO markers..."
TODO_COUNT=0
for file in "$ROOT/ce.sh" "$ROOT/.workflow/cli/lib"/*.sh; do
    if [[ -f "$file" ]]; then
        COUNT=$(grep -c "# TODO:" "$file" || echo 0)
        TODO_COUNT=$((TODO_COUNT + COUNT))
    fi
done
pass "TODO markers: $TODO_COUNT (ready for P3)"
echo

# Summary
echo "=================================================="
echo "  Verification Summary"
echo "=================================================="
echo
info "Files created: 9 (1 main + 8 libraries)"
info "Total functions: $TOTAL_FUNCTIONS"
info "Exported functions: $EXPORT_COUNT"
info "TODO markers: $TODO_COUNT"
echo

if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}✓ All checks passed! Ready for P3 implementation.${NC}"
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found. Please fix before proceeding.${NC}"
    exit 1
fi
