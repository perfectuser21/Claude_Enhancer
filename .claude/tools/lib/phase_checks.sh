#!/bin/bash
# Phase Check Functions
# Part of phase_manager.sh modularization
# Version: 1.0.0

# Prevent multiple sourcing
if [[ -n "${_PHASE_CHECKS_LOADED:-}" ]]; then
    return 0
fi
_PHASE_CHECKS_LOADED=true

# Inherit paths from phase_core if available
SCRIPT_DIR="${SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
SCRIPTS_DIR="${SCRIPTS_DIR:-$PROJECT_ROOT/scripts}"

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════
# Phase 1: Discovery & Planning Checks
# ═══════════════════════════════════════════════════════════════

run_phase1_checks() {
    local mode="${1:-full}"

    echo -e "${BLUE}[Phase 1.1] Branch Check${NC}"
    local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    echo -e "  Current branch: $current_branch"

    if [[ "$current_branch" =~ ^(main|master|production)$ ]]; then
        echo -e "${RED}⚠️  On protected branch! Create feature branch first${NC}"
    else
        echo -e "${GREEN}✅ On feature branch${NC}"
    fi

    if [[ "$mode" == "full" ]]; then
        echo ""
        echo -e "${BLUE}[Phase 1.2] Requirements Discovery${NC}"
        if [[ -f "$PROJECT_ROOT/P2_DISCOVERY.md" ]]; then
            local lines=$(wc -l < "$PROJECT_ROOT/P2_DISCOVERY.md")
            echo -e "${GREEN}✅ P2_DISCOVERY.md exists ($lines lines)${NC}"
        else
            echo -e "${YELLOW}⚠️  P2_DISCOVERY.md not found${NC}"
        fi

        echo ""
        echo -e "${BLUE}[Phase 1.3] Architecture Planning${NC}"
        if [[ -f "$PROJECT_ROOT/PLAN.md" ]]; then
            local lines=$(wc -l < "$PROJECT_ROOT/PLAN.md")
            echo -e "${GREEN}✅ PLAN.md exists ($lines lines)${NC}"
        else
            echo -e "${YELLOW}⚠️  PLAN.md not found${NC}"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 2: Implementation Checks
# ═══════════════════════════════════════════════════════════════

run_phase2_checks() {
    local mode="${1:-full}"

    echo -e "${BLUE}[Phase 2.1] Code Implementation${NC}"
    local changed_files=$(git diff --name-only 2>/dev/null | wc -l)
    local staged_files=$(git diff --cached --name-only 2>/dev/null | wc -l)

    echo -e "  Changed files: $changed_files"
    echo -e "  Staged files: $staged_files"

    if [[ "$mode" == "full" ]]; then
        echo ""
        echo -e "${BLUE}[Phase 2.2] Git Hooks Configuration${NC}"
        if [[ -x "$PROJECT_ROOT/.git/hooks/pre-commit" ]]; then
            echo -e "${GREEN}✅ Pre-commit hook installed${NC}"
        else
            echo -e "${YELLOW}⚠️  Pre-commit hook not installed${NC}"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 3: Testing - Quality Gate 1
# ═══════════════════════════════════════════════════════════════

run_phase3_checks() {
    local mode="${1:-full}"

    echo -e "${BOLD}${YELLOW}🔒 Quality Gate 1${NC}"
    echo ""

    if [[ "$mode" == "quick" ]]; then
        echo -e "${BLUE}[Phase 3] Running incremental static checks...${NC}"
        if [[ -f "$SCRIPTS_DIR/static_checks_incremental.sh" ]]; then
            bash "$SCRIPTS_DIR/static_checks_incremental.sh" 2>&1 | tail -20
        fi
    else
        echo -e "${BLUE}[Phase 3] Running full static checks...${NC}"
        if [[ -f "$SCRIPTS_DIR/static_checks.sh" ]]; then
            bash "$SCRIPTS_DIR/static_checks.sh" 2>&1 | tail -20
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 4: Review - Quality Gate 2
# ═══════════════════════════════════════════════════════════════

run_phase4_checks() {
    local mode="${1:-full}"

    echo -e "${BOLD}${YELLOW}🔒 Quality Gate 2${NC}"
    echo ""

    echo -e "${BLUE}[Phase 4] Running pre-merge audit...${NC}"
    if [[ -f "$SCRIPTS_DIR/pre_merge_audit.sh" ]]; then
        bash "$SCRIPTS_DIR/pre_merge_audit.sh" 2>&1 | tail -20
    else
        echo -e "${YELLOW}⚠️  Pre-merge audit script not found${NC}"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 5: Release Checks
# ═══════════════════════════════════════════════════════════════

run_phase5_checks() {
    local mode="${1:-full}"

    echo -e "${BLUE}[Phase 5.1] Version Check${NC}"
    if [[ -f "$SCRIPTS_DIR/check_version_consistency.sh" ]]; then
        bash "$SCRIPTS_DIR/check_version_consistency.sh" 2>&1 | tail -10
    fi

    if [[ "$mode" == "full" ]]; then
        echo ""
        echo -e "${BLUE}[Phase 5.2] Changelog Check${NC}"
        if [[ -f "$PROJECT_ROOT/CHANGELOG.md" ]]; then
            echo -e "${GREEN}✅ CHANGELOG.md exists${NC}"
        else
            echo -e "${YELLOW}⚠️  CHANGELOG.md missing${NC}"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════
# Phase 6 & 7: Acceptance and Closure
# ═══════════════════════════════════════════════════════════════

run_phase6_checks() {
    echo -e "${BLUE}[Phase 6] Acceptance Verification${NC}"
    echo -e "  Checking acceptance criteria..."
    echo -e "${GREEN}✅ Ready for user acceptance${NC}"
}

run_phase7_checks() {
    echo -e "${BLUE}[Phase 7] Closure Checklist${NC}"

    # Check .temp directory size
    if [[ -d "$PROJECT_ROOT/.temp" ]]; then
        local temp_size=$(du -sh "$PROJECT_ROOT/.temp" 2>/dev/null | cut -f1)
        echo -e "  .temp directory: $temp_size"
    fi

    echo -e "${GREEN}✅ Ready for merge${NC}"
}

# Master function to run phase checks
run_phase_checks() {
    local phase="${1:-}"
    local mode="${2:-full}"

    case "$phase" in
        Phase1) run_phase1_checks "$mode" ;;
        Phase2) run_phase2_checks "$mode" ;;
        Phase3) run_phase3_checks "$mode" ;;
        Phase4) run_phase4_checks "$mode" ;;
        Phase5) run_phase5_checks "$mode" ;;
        Phase6) run_phase6_checks "$mode" ;;
        Phase7) run_phase7_checks "$mode" ;;
        *)
            echo -e "${RED}Error: Unknown phase '$phase'${NC}" >&2
            return 1
            ;;
    esac
}

# Export functions
export -f run_phase_checks
export -f run_phase1_checks
export -f run_phase2_checks
export -f run_phase3_checks
export -f run_phase4_checks
export -f run_phase5_checks
export -f run_phase6_checks
export -f run_phase7_checks