#!/bin/bash
# Phase Display Functions
# Part of phase_manager.sh modularization
# Version: 1.0.0

# Prevent multiple sourcing
if [[ -n "${_PHASE_DISPLAY_LOADED:-}" ]]; then
    return 0
fi
_PHASE_DISPLAY_LOADED=true

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════
# Display Functions
# ═══════════════════════════════════════════════════════════════

# Show phase transition message
show_phase_transition() {
    local current_phase="$1"
    local new_phase="$2"

    # Load core functions if needed
    if ! type get_phase_description >/dev/null 2>&1; then
        if [[ -f "$(dirname "${BASH_SOURCE[0]}")/phase_core.sh" ]]; then
            # shellcheck source=/dev/null
            source "$(dirname "${BASH_SOURCE[0]}")/phase_core.sh"
        fi
    fi

    echo -e "${GREEN}✅ Switched to $new_phase${NC}"
    local desc=$(get_phase_description "$new_phase")
    echo -e "${CYAN}   $desc${NC}"
}

# Show current status
show_status() {
    # Load core functions if needed
    if ! type get_current_phase >/dev/null 2>&1; then
        if [[ -f "$(dirname "${BASH_SOURCE[0]}")/phase_core.sh" ]]; then
            # shellcheck source=/dev/null
            source "$(dirname "${BASH_SOURCE[0]}")/phase_core.sh"
        fi
    fi

    local current_phase=$(get_current_phase)
    local desc=$(get_phase_description "$current_phase")
    local checkpoints=$(get_phase_checkpoints "$current_phase")

    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}7-Phase Workflow Status${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BOLD}Current Phase:${NC} $current_phase"
    echo -e "${BOLD}Description:${NC} $desc"
    echo -e "${BOLD}Checkpoints:${NC} $checkpoints"
    echo ""
    echo -e "${BOLD}Phase Progress:${NC}"

    for phase in Phase1 Phase2 Phase3 Phase4 Phase5 Phase6 Phase7; do
        if [[ "$phase" == "$current_phase" ]]; then
            echo -e "  ${GREEN}▶${NC} $phase - $(get_phase_description $phase)"
        else
            echo -e "  ○ $phase - $(get_phase_description $phase)"
        fi
    done

    echo ""
    echo -e "${BOLD}Quality Gates:${NC}"
    echo -e "  🔒 Gate 1: Phase 3 → Phase 4 (Testing)"
    echo -e "  🔒 Gate 2: Phase 4 → Phase 5 (Review)"
}

# Show help message
show_help() {
    cat <<EOF
${BOLD}Phase Manager - 7-Phase Workflow Management${NC}

${BOLD}Commands:${NC}
  status|s              Show current phase and progress
  check|c [phase] [mode] Run checks for a phase (mode: full|quick)
  switch|sw <phase>     Switch to a specific phase
  next|n                Move to next phase
  help|h                Show this help message

${BOLD}Phases:${NC}
  Phase1 - Discovery & Planning (33 checkpoints)
  Phase2 - Implementation (15 checkpoints)
  Phase3 - Testing [Quality Gate 1] (15 checkpoints)
  Phase4 - Review [Quality Gate 2] (10 checkpoints)
  Phase5 - Release (15 checkpoints)
  Phase6 - Acceptance (5 checkpoints)
  Phase7 - Closure (4 checkpoints)

${BOLD}Examples:${NC}
  phase_manager status            # Show current status
  phase_manager check             # Run checks for current phase
  phase_manager check Phase3      # Run Phase 3 checks
  phase_manager check Phase3 quick # Run quick Phase 3 checks
  phase_manager switch Phase2     # Switch to Phase 2
  phase_manager next              # Move to next phase
EOF
}

# Export functions
export -f show_phase_transition
export -f show_status
export -f show_help