#!/bin/bash
# Phase Core Functions
# Part of phase_manager.sh modularization
# Version: 1.0.0

# Prevent multiple sourcing
if [[ -n "${_PHASE_CORE_LOADED:-}" ]]; then
    return 0
fi
_PHASE_CORE_LOADED=true

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
PHASE_FILE="$WORKFLOW_DIR/current"
LOG_DIR="$WORKFLOW_DIR/logs"

# Ensure directories exist
mkdir -p "$LOG_DIR"

# ═══════════════════════════════════════════════════════════════
# Core Phase Functions
# ═══════════════════════════════════════════════════════════════

# Get current phase
get_current_phase() {
    if [[ -f "$PHASE_FILE" ]]; then
        cat "$PHASE_FILE" | tr -d '[:space:]'
    else
        # Default Phase 7 (Closure)
        echo "Phase7"
    fi
}

# Validate phase name
is_valid_phase() {
    local phase="${1:-}"
    case "$phase" in
        Phase1|Phase2|Phase3|Phase4|Phase5|Phase6|Phase7)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Get phase description
get_phase_description() {
    local phase="${1:-}"
    case "$phase" in
        Phase1) echo "Discovery & Planning (33 checkpoints)" ;;
        Phase2) echo "Implementation (15 checkpoints)" ;;
        Phase3) echo "Testing - Quality Gate 1 (15 checkpoints)" ;;
        Phase4) echo "Review - Quality Gate 2 (10 checkpoints)" ;;
        Phase5) echo "Release (15 checkpoints)" ;;
        Phase6) echo "Acceptance (5 checkpoints)" ;;
        Phase7) echo "Closure (4 checkpoints)" ;;
        *) echo "Unknown Phase" ;;
    esac
}

# Get phase checkpoints count
get_phase_checkpoints() {
    local phase="${1:-}"
    case "$phase" in
        Phase1) echo "33" ;;
        Phase2) echo "15" ;;
        Phase3) echo "15" ;;
        Phase4) echo "10" ;;
        Phase5) echo "15" ;;
        Phase6) echo "5" ;;
        Phase7) echo "4" ;;
        *) echo "0" ;;
    esac
}

# Switch to a new phase
switch_to_phase() {
    local new_phase="${1:-}"

    if ! is_valid_phase "$new_phase"; then
        echo "Error: Invalid phase '$new_phase'" >&2
        return 1
    fi

    local current_phase=$(get_current_phase)

    # Save new phase
    echo "$new_phase" > "$PHASE_FILE"

    # Log transition
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Phase transition: $current_phase → $new_phase" >> "$LOG_DIR/phase_transitions.log"

    return 0
}

# Export functions
export -f get_current_phase
export -f is_valid_phase
export -f get_phase_description
export -f get_phase_checkpoints
export -f switch_to_phase