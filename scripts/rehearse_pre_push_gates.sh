#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Pre-Push Quality Gates Rehearsal Script (English)
# ═══════════════════════════════════════════════════════════════
#
# Purpose: Test quality gates without modifying repository state
# Usage:
#   MOCK_SCORE=84 bash scripts/rehearse_pre_push_gates.sh
#   MOCK_COVERAGE=79 bash scripts/rehearse_pre_push_gates.sh
#   BRANCH=main MOCK_SIG=invalid bash scripts/rehearse_pre_push_gates.sh
#
# Mock Environment Variables:
#   MOCK_SCORE     - Override quality score (default: real score)
#   MOCK_COVERAGE  - Override coverage percentage (default: real coverage)
#   MOCK_SIG       - Set to "invalid" to simulate signature failure
#   BRANCH         - Override current branch name
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# Color constants
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Get project root
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Source the final gate library
if [[ ! -f "$PROJECT_ROOT/.workflow/lib/final_gate.sh" ]]; then
    echo -e "${RED}❌ ERROR: final_gate.sh library not found${NC}"
    echo "Expected location: $PROJECT_ROOT/.workflow/lib/final_gate.sh"
    exit 1
fi

source "$PROJECT_ROOT/.workflow/lib/final_gate.sh"

# ═══════════════════════════════════════════════════════════════
# Rehearsal Banner
# ═══════════════════════════════════════════════════════════════

echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║     PRE-PUSH QUALITY GATES REHEARSAL (No Changes)    ║${NC}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Show current configuration
echo -e "${BLUE}📋 Rehearsal Configuration:${NC}"
echo -e "   Project: $(basename "$PROJECT_ROOT")"
echo -e "   Real Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')"
echo -e "   Test Branch: ${BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')}"
echo ""

# Show mock variables if set
if [[ -n "${MOCK_SCORE:-}" || -n "${MOCK_COVERAGE:-}" || -n "${MOCK_SIG:-}" ]]; then
    echo -e "${YELLOW}🎭 Mock Mode Active:${NC}"
    [[ -n "${MOCK_SCORE:-}" ]] && echo -e "   MOCK_SCORE=${MOCK_SCORE}"
    [[ -n "${MOCK_COVERAGE:-}" ]] && echo -e "   MOCK_COVERAGE=${MOCK_COVERAGE}"
    [[ -n "${MOCK_SIG:-}" ]] && echo -e "   MOCK_SIG=${MOCK_SIG}"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# Run Final Gate Check (Read-Only)
# ═══════════════════════════════════════════════════════════════

echo -e "${CYAN}🔍 Running quality gate checks...${NC}"
echo ""

if final_gate_check; then
    echo ""
    echo -e "${BOLD}${GREEN}✅ REHEARSAL RESULT: Gates would PASS${NC}"
    exit 0
else
    echo ""
    echo -e "${BOLD}${RED}❌ REHEARSAL RESULT: Gates would BLOCK${NC}"
    exit 1
fi
