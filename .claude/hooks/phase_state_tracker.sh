#!/usr/bin/env bash
# phase_state_tracker.sh - PrePrompt hook for phase state awareness
# Maintains .phase/current and reminds AI about phase transitions
# Performance target: <50ms
set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

PHASE_CURRENT_FILE=".phase/current"
PHASE_MANAGER_SCRIPT=".workflow/cli/phase_manager.sh"
STALE_THRESHOLD_DAYS=7

# ============================================================================
# Helper Functions
# ============================================================================

# Get current phase from file
get_current_phase() {
    if [[ -f "${PHASE_CURRENT_FILE}" ]]; then
        local phase
        phase=$(tr -d '[:space:]' < "${PHASE_CURRENT_FILE}")
        # Validate phase format (Phase1-Phase7 only, matching 7-phase system)
        if [[ "$phase" =~ ^Phase[1-7]$ ]]; then
            echo "$phase"
        else
            echo "Phase1"  # Default fallback
        fi
    else
        # Create if missing with default Phase1
        mkdir -p "$(dirname "${PHASE_CURRENT_FILE}")"
        echo "Phase1" > "${PHASE_CURRENT_FILE}"
        echo "Phase1"
    fi
}

# Get human-readable phase name
get_phase_name() {
    local phase="$1"

    # Use phase_manager.sh if available
    if [[ -f "${PHASE_MANAGER_SCRIPT}" ]]; then
        # Source and call phase_manager function
        # shellcheck source=.workflow/cli/phase_manager.sh
        if source "${PHASE_MANAGER_SCRIPT}" 2>/dev/null; then
            local phase_num="${phase#Phase}"
            ce_phase_get_name "P${phase_num}" 2>/dev/null && return
        fi
    fi

    # Fallback to builtin mapping (7-phase system)
    case "$phase" in
        Phase1) echo "Discovery & Planning" ;;
        Phase2) echo "Implementation" ;;
        Phase3) echo "Testing" ;;
        Phase4) echo "Review" ;;
        Phase5) echo "Release" ;;
        Phase6) echo "Acceptance" ;;
        Phase7) echo "Closure" ;;
        *) echo "Unknown" ;;
    esac
}

# Calculate days since phase entered
get_phase_age_days() {
    if [[ ! -f "${PHASE_CURRENT_FILE}" ]]; then
        echo "0"
        return
    fi

    local current_time
    local file_time
    local age_seconds
    local age_days

    current_time=$(date +%s)
    file_time=$(stat -c %Y "${PHASE_CURRENT_FILE}" 2>/dev/null || stat -f %m "${PHASE_CURRENT_FILE}" 2>/dev/null || echo "$current_time")
    age_seconds=$((current_time - file_time))
    age_days=$((age_seconds / 86400))

    echo "$age_days"
}

# Get human-readable time ago
get_time_ago() {
    local days="$1"

    if [[ $days -eq 0 ]]; then
        echo "today"
    elif [[ $days -eq 1 ]]; then
        echo "1 day ago"
    elif [[ $days -lt 7 ]]; then
        echo "${days} days ago"
    elif [[ $days -lt 30 ]]; then
        local weeks=$((days / 7))
        if [[ $weeks -eq 1 ]]; then
            echo "1 week ago"
        else
            echo "${weeks} weeks ago"
        fi
    else
        local months=$((days / 30))
        if [[ $months -eq 1 ]]; then
            echo "1 month ago"
        else
            echo "${months} months ago"
        fi
    fi
}

# Check if phase is stale
is_phase_stale() {
    local days="$1"
    [[ $days -gt $STALE_THRESHOLD_DAYS ]]
}

# Get next suggested phase
get_next_phase() {
    local current_phase="$1"

    case "$current_phase" in
        Phase1) echo "Phase2" ;;
        Phase2) echo "Phase3" ;;
        Phase3) echo "Phase4" ;;
        Phase4) echo "Phase5" ;;
        Phase5) echo "Phase6" ;;
        Phase6) echo "Phase7" ;;
        Phase7) echo "" ;; # No next phase (final)
        *) echo "Phase2" ;;
    esac
}

# ============================================================================
# Main Display Function
# ============================================================================

display_phase_state() {
    local current_phase
    local phase_name
    local phase_age
    local time_ago

    current_phase=$(get_current_phase)
    phase_name=$(get_phase_name "$current_phase")
    phase_age=$(get_phase_age_days)
    time_ago=$(get_time_ago "$phase_age")

    # Output to stderr so AI sees it in system message
    cat >&2 <<EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Current Phase: ${current_phase}
   Phase Name: ${phase_name}
   Entered: ${time_ago}
EOF

    # Add stale warning if phase is old
    if is_phase_stale "$phase_age"; then
        cat >&2 <<EOF

⚠️  WARNING: Phase state is stale (${phase_age} days old, >${STALE_THRESHOLD_DAYS} day threshold)
   The current phase might be outdated. Please verify.
EOF
    fi

    # Reminder for phase transition
    local next_phase
    next_phase=$(get_next_phase "$current_phase")
    if [[ -n "$next_phase" ]]; then
        cat >&2 <<EOF

💡 Reminder: When completing this phase, update with:
   echo ${next_phase} > .phase/current
EOF
    else
        cat >&2 <<EOF

🎉 This is the final phase (Phase7)
EOF
    fi

    cat >&2 <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
}

# ============================================================================
# Performance Optimization: Quick Exit for Common Cases
# ============================================================================

# Main execution with performance optimization
main() {
    local start_time
    start_time=$(date +%s%3N 2>/dev/null || date +%s)

    # Check if in Claude Enhancer project (quick check)
    if [[ ! -f ".workflow/SPEC.yaml" ]] && [[ ! -f ".workflow/manifest.yml" ]]; then
        # Not in Claude Enhancer project, skip silently
        exit 0
    fi

    # Display phase state
    display_phase_state

    # Performance tracking (only if millisecond precision available)
    if command -v date >/dev/null 2>&1; then
        local end_time
        end_time=$(date +%s%3N 2>/dev/null || date +%s)
        local duration=$((end_time - start_time))

        # Only show performance warning if >50ms (updated target)
        if [[ $duration -gt 50 ]]; then
            echo "⚠️  Performance: ${duration}ms (target: <50ms)" >&2
        fi
    fi
}

# ============================================================================
# Execute
# ============================================================================

main "$@"
