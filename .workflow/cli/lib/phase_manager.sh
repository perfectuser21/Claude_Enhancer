#!/usr/bin/env bash
# phase_manager.sh - Phase lifecycle and transition management
# Manages 8-phase workflow (P0-P7) with validation and gates
set -euo pipefail

# Phase definitions
CE_PHASES=(P0 P1 P2 P3 P4 P5 P6 P7)
CE_PHASE_NAMES=(
    "Discovery"
    "Planning"
    "Skeleton"
    "Implementation"
    "Testing"
    "Review"
    "Release"
    "Monitoring"
)

# Phase configuration files
CE_PHASES_CONFIG=".workflow/STAGES.yml"
CE_GATES_CONFIG=".workflow/gates.yml"
CE_PHASE_CURRENT=".phase/current"

# Load common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh" 2>/dev/null || true

# Check if yq is available
HAS_YQ=false
if command -v yq &>/dev/null; then
    HAS_YQ=true
fi

# ============================================================================
# Phase information
# ============================================================================

ce_phase_get_current() {
    # Get current phase from .phase/current
    # Returns: Phase code (P0-P7)
    # Fallback: P0 if not set

    if [[ -f "${CE_PHASE_CURRENT}" ]]; then
        local phase=$(cat "${CE_PHASE_CURRENT}" | tr -d '[:space:]')
        # Validate phase
        if [[ "$phase" =~ ^P[0-7]$ ]]; then
            echo "$phase"
        else
            echo "P0"
        fi
    else
        echo "P0"
    fi
}

ce_phase_get_name() {
    # Get human-readable phase name
    # Usage: name=$(ce_phase_get_name "P3")
    # Returns: "Implementation"

    local phase="$1"

    case "$phase" in
        P0) echo "Discovery" ;;
        P1) echo "Planning" ;;
        P2) echo "Skeleton" ;;
        P3) echo "Implementation" ;;
        P4) echo "Testing" ;;
        P5) echo "Review" ;;
        P6) echo "Release" ;;
        P7) echo "Monitoring" ;;
        *) echo "Unknown" ;;
    esac
}

ce_phase_get_description() {
    # Get phase description from STAGES.yml or gates.yml
    # Returns: Detailed description of phase purpose

    local phase="$1"

    if $HAS_YQ && [[ -f "${CE_GATES_CONFIG}" ]]; then
        yq eval ".phases.${phase}.name" "${CE_GATES_CONFIG}" 2>/dev/null || echo "No description available"
    else
        ce_phase_get_name "$phase"
    fi
}

ce_phase_get_info() {
    # Get comprehensive phase information
    # Returns JSON with: code, name, description, objectives, deliverables, gates

    local phase="${1:-$(ce_phase_get_current)}"
    local name=$(ce_phase_get_name "$phase")

    if $HAS_YQ && [[ -f "${CE_GATES_CONFIG}" ]]; then
        cat <<EOF
{
  "code": "$phase",
  "name": "$name",
  "description": "$(yq eval ".phases.${phase}.name" "${CE_GATES_CONFIG}" 2>/dev/null || echo "$name")",
  "objectives": $(yq eval -o=json ".phases.${phase}.must_produce" "${CE_GATES_CONFIG}" 2>/dev/null || echo "[]"),
  "gates": $(yq eval -o=json ".phases.${phase}.gates" "${CE_GATES_CONFIG}" 2>/dev/null || echo "[]"),
  "allow_paths": $(yq eval -o=json ".phases.${phase}.allow_paths" "${CE_GATES_CONFIG}" 2>/dev/null || echo "[]")
}
EOF
    else
        cat <<EOF
{
  "code": "$phase",
  "name": "$name",
  "description": "$name phase",
  "objectives": [],
  "gates": [],
  "allow_paths": []
}
EOF
    fi
}

ce_phase_list_all() {
    # List all phases with status
    # Output format:
    #   ✓ P0: Discovery (completed)
    #   ✓ P1: Planning (completed)
    #   → P3: Implementation (current)

    local current_phase=$(ce_phase_get_current)

    for i in {0..7}; do
        local phase="P${i}"
        local name=$(ce_phase_get_name "$phase")
        local marker="○"
        local status="pending"

        # Check if gate passed
        if [[ -f ".gates/0${i}.ok" ]]; then
            marker="✓"
            status="completed"
        fi

        # Mark current phase
        if [[ "$phase" == "$current_phase" ]]; then
            marker="→"
            status="current"
        fi

        printf "%s %s: %s (%s)\n" "$marker" "$phase" "$name" "$status"
    done
}

# ============================================================================
# Phase transitions
# ============================================================================

ce_phase_transition() {
    # Transition to new phase
    # Usage: ce_phase_transition "P4"
    # Returns: 0 on success, 1 on failure

    local target_phase="$1"
    local current_phase=$(ce_phase_get_current)

    [[ -z "$target_phase" ]] && {
        echo "ERROR: Target phase required" >&2
        return 1
    }

    # Validate phase code
    if [[ ! "$target_phase" =~ ^P[0-7]$ ]]; then
        echo "ERROR: Invalid phase code: $target_phase" >&2
        return 1
    fi

    # Check if already in target phase
    if [[ "$current_phase" == "$target_phase" ]]; then
        echo "Already in phase $target_phase"
        return 0
    fi

    # Validate transition
    ce_phase_validate_transition "$current_phase" "$target_phase" || {
        echo "ERROR: Transition validation failed" >&2
        return 1
    }

    # Run exit hook for current phase
    ce_phase_run_exit_hook "$current_phase" 2>/dev/null || true

    # Update phase file
    mkdir -p "$(dirname "${CE_PHASE_CURRENT}")"
    echo "$target_phase" > "${CE_PHASE_CURRENT}"

    # Run entry hook for new phase
    ce_phase_run_entry_hook "$target_phase" 2>/dev/null || true

    # Update session if state manager is available
    if declare -f ce_state_update_session &>/dev/null; then
        local session_id=$(ce_get_terminal_id 2>/dev/null || echo "default")
        ce_state_update_session "$session_id" "phase" "$target_phase" 2>/dev/null || true
    fi

    echo "Transitioned from $current_phase to $target_phase"
    return 0
}

ce_phase_validate_transition() {
    # Validate if transition is allowed
    # Usage: ce_phase_validate_transition "P3" "P4"
    # Returns: 0 if valid, 1 with reasons if not

    local from_phase="$1"
    local to_phase="$2"

    local from_num="${from_phase#P}"
    local to_num="${to_phase#P}"

    # Allow forward progression (with skip)
    if (( to_num > from_num )); then
        # Check gates for current phase
        if ! ce_phase_check_gates "$from_phase"; then
            echo "ERROR: Cannot transition - gates not passed for $from_phase" >&2
            return 1
        fi
        return 0
    fi

    # Allow backward progression (with warning)
    if (( to_num < from_num )); then
        echo "WARNING: Moving backward from $from_phase to $to_phase" >&2
        return 0
    fi

    # Same phase
    return 0
}

ce_phase_can_skip_to() {
    # Check if can skip to specific phase
    # Usage: ce_phase_can_skip_to "P2"
    # Returns: 0 if allowed, 1 if not

    local target_phase="$1"
    local current_phase=$(ce_phase_get_current)

    # For now, allow skipping if gates are passed
    # In future, add skip rules from configuration

    local target_num="${target_phase#P}"
    local current_num="${current_phase#P}"

    if (( target_num > current_num + 1 )); then
        echo "WARNING: Skipping phases - ensure dependencies are met" >&2
    fi

    return 0
}

ce_phase_next() {
    # Move to next sequential phase
    # Usage: ce_phase_next

    local current_phase=$(ce_phase_get_current)
    local current_num="${current_phase#P}"
    local next_num=$((current_num + 1))

    if (( next_num > 7 )); then
        echo "ERROR: Already at final phase (P7)" >&2
        return 1
    fi

    local next_phase="P${next_num}"
    ce_phase_transition "$next_phase"
}

ce_phase_previous() {
    # Go back to previous phase
    # Usage: ce_phase_previous

    local current_phase=$(ce_phase_get_current)
    local current_num="${current_phase#P}"
    local prev_num=$((current_num - 1))

    if (( prev_num < 0 )); then
        echo "ERROR: Already at first phase (P0)" >&2
        return 1
    fi

    local prev_phase="P${prev_num}"

    echo "WARNING: Going back to $prev_phase - this may be destructive" >&2
    ce_phase_transition "$prev_phase"
}

# ============================================================================
# Phase gates
# ============================================================================

ce_phase_get_gates() {
    # Get quality gates for phase
    # Usage: gates=$(ce_phase_get_gates "P3")
    # Returns: Array of gate definitions

    local phase="${1:-$(ce_phase_get_current)}"

    if $HAS_YQ && [[ -f "${CE_GATES_CONFIG}" ]]; then
        yq eval -o=json ".phases.${phase}.gates" "${CE_GATES_CONFIG}" 2>/dev/null || echo "[]"
    else
        echo "[]"
    fi
}

ce_phase_validate_gates() {
    # Validate all gates for phase
    # Usage: results=$(ce_phase_validate_gates "P3")
    # Returns: Gate results as JSON

    local phase="${1:-$(ce_phase_get_current)}"
    local phase_num="${phase#P}"

    local gate_file=".gates/0${phase_num}.ok"

    if [[ -f "$gate_file" ]]; then
        echo '{"status": "passed", "file": "'$gate_file'"}'
    else
        echo '{"status": "failed", "file": "'$gate_file'", "reason": "Gate file not found"}'
    fi
}

ce_phase_get_gate_status() {
    # Get status of specific gate
    # Usage: status=$(ce_phase_get_gate_status "P3" "unit-tests")
    # Returns: passed/failed/pending/skipped

    local phase="${1:-$(ce_phase_get_current)}"
    local gate_name="$2"
    local phase_num="${phase#P}"

    if [[ -f ".gates/0${phase_num}.ok" ]]; then
        echo "passed"
    else
        echo "pending"
    fi
}

ce_phase_check_gates() {
    # Check if all required gates are passed
    # Usage: ce_phase_check_gates "P3"
    # Returns: 0 if all pass, 1 if any fail

    local phase="${1:-$(ce_phase_get_current)}"
    local phase_num="${phase#P}"

    # Check if gate file exists
    if [[ -f ".gates/0${phase_num}.ok" ]]; then
        return 0
    else
        return 1
    fi
}

ce_phase_check_gate_scores() {
    # Check if gate scores meet thresholds
    # Returns: 0 if all pass, 1 with details if fail

    local phase="${1:-$(ce_phase_get_current)}"

    # For now, just check if gate file exists
    # In future, parse gate file for scores

    ce_phase_check_gates "$phase"
}

# ============================================================================
# Phase deliverables
# ============================================================================

ce_phase_get_deliverables() {
    # Get required deliverables for phase
    # Returns: List of expected outputs/artifacts

    local phase="${1:-$(ce_phase_get_current)}"

    if $HAS_YQ && [[ -f "${CE_GATES_CONFIG}" ]]; then
        yq eval -o=json ".phases.${phase}.must_produce" "${CE_GATES_CONFIG}" 2>/dev/null || echo "[]"
    else
        echo "[]"
    fi
}

ce_phase_check_deliverables() {
    # Check if all deliverables are present
    # Returns: 0 if complete, 1 with missing items

    local phase="${1:-$(ce_phase_get_current)}"

    case "$phase" in
        P0)
            [[ -f "docs/P0_"*"_DISCOVERY.md" ]] || {
                echo "Missing: P0 discovery document" >&2
                return 1
            }
            ;;
        P1)
            [[ -f "docs/PLAN.md" ]] || {
                echo "Missing: PLAN.md" >&2
                return 1
            }
            ;;
        P2)
            [[ -f "docs/SKELETON-NOTES.md" ]] || {
                echo "Missing: SKELETON-NOTES.md" >&2
                return 1
            }
            ;;
        P3)
            [[ -f "docs/CHANGELOG.md" ]] || {
                echo "Missing: CHANGELOG.md" >&2
                return 1
            }
            ;;
        P4)
            [[ -f "docs/TEST-REPORT.md" ]] || {
                echo "Missing: TEST-REPORT.md" >&2
                return 1
            }
            ;;
        P5)
            [[ -f "docs/REVIEW.md" ]] || {
                echo "Missing: REVIEW.md" >&2
                return 1
            }
            ;;
        P6)
            [[ -f "docs/README.md" ]] || {
                echo "Missing: README.md" >&2
                return 1
            }
            ;;
        P7)
            [[ -f "observability/"*"_MONITOR_REPORT.md" ]] || {
                echo "Missing: Monitor report" >&2
                return 1
            }
            ;;
    esac

    return 0
}

ce_phase_generate_checklist() {
    # Generate phase completion checklist
    # Output: Interactive checklist

    local phase="${1:-$(ce_phase_get_current)}"
    local name=$(ce_phase_get_name "$phase")

    echo "Phase $phase: $name"
    echo "===================="

    if $HAS_YQ && [[ -f "${CE_GATES_CONFIG}" ]]; then
        local deliverables=$(yq eval ".phases.${phase}.must_produce[]" "${CE_GATES_CONFIG}" 2>/dev/null)

        echo "Deliverables:"
        while IFS= read -r item; do
            if [[ -n "$item" ]]; then
                echo "☐ $item"
            fi
        done <<< "$deliverables"

        echo ""
        echo "Gates:"
        local gates=$(yq eval ".phases.${phase}.gates[]" "${CE_GATES_CONFIG}" 2>/dev/null)

        while IFS= read -r gate; do
            if [[ -n "$gate" ]]; then
                local marker="☐"
                if ce_phase_check_gates "$phase" 2>/dev/null; then
                    marker="☑"
                fi
                echo "$marker $gate"
            fi
        done <<< "$gates"
    fi
}

# ============================================================================
# Phase metrics
# ============================================================================

ce_phase_get_duration() {
    # Get time spent in current phase
    # Returns: Duration in seconds since phase entry

    local phase="${1:-$(ce_phase_get_current)}"

    # Try to get from session state
    if declare -f ce_state_get_duration &>/dev/null; then
        ce_state_get_duration 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

ce_phase_get_history() {
    # Get phase transition history
    # Returns: Timeline of all phase changes

    echo "Phase transition history:"

    # Check git log for phase changes
    if git rev-parse --git-dir &>/dev/null; then
        git log --all --grep="phase" --oneline 2>/dev/null | head -10 || echo "No phase history found"
    fi
}

ce_phase_get_stats() {
    # Get statistics for phase
    # Returns: Various metrics

    local phase="${1:-$(ce_phase_get_current)}"

    cat <<EOF
Phase: $phase ($(ce_phase_get_name "$phase"))
Gates passed: $(ce_phase_check_gates "$phase" && echo "Yes" || echo "No")
Deliverables: $(ce_phase_check_deliverables "$phase" &>/dev/null && echo "Complete" || echo "Incomplete")
Duration: $(ce_phase_get_duration "$phase")s
EOF
}

# ============================================================================
# Phase hooks
# ============================================================================

ce_phase_run_entry_hook() {
    # Run hook when entering phase
    # Usage: ce_phase_run_entry_hook "P3"

    local phase="$1"
    local hook_file=".workflow/hooks/phase_entry_${phase}.sh"

    if [[ -x "$hook_file" ]]; then
        echo "Running entry hook for $phase..."
        bash "$hook_file" || true
    fi
}

ce_phase_run_exit_hook() {
    # Run hook when exiting phase
    # Usage: ce_phase_run_exit_hook "P3"

    local phase="$1"
    local hook_file=".workflow/hooks/phase_exit_${phase}.sh"

    if [[ -x "$hook_file" ]]; then
        echo "Running exit hook for $phase..."
        bash "$hook_file" || true
    fi
}

# ============================================================================
# Phase recommendations
# ============================================================================

ce_phase_suggest_next_actions() {
    # Suggest next actions for current phase
    # Returns: Prioritized list of recommendations

    local phase=$(ce_phase_get_current)
    local name=$(ce_phase_get_name "$phase")

    echo "Suggested actions for $phase ($name):"

    case "$phase" in
        P0)
            echo "1. Create technical spike document"
            echo "2. Validate feasibility"
            echo "3. Document risks"
            ;;
        P1)
            echo "1. Create PLAN.md with tasks"
            echo "2. List affected files"
            echo "3. Define rollback plan"
            ;;
        P2)
            echo "1. Create directory structure"
            echo "2. Add interface skeletons"
            echo "3. Document in SKELETON-NOTES.md"
            ;;
        P3)
            echo "1. Implement functionality"
            echo "2. Update CHANGELOG.md"
            echo "3. Ensure code builds"
            ;;
        P4)
            echo "1. Write unit tests"
            echo "2. Add integration tests"
            echo "3. Generate TEST-REPORT.md"
            ;;
        P5)
            echo "1. Review code quality"
            echo "2. Check for risks"
            echo "3. Create REVIEW.md with approval"
            ;;
        P6)
            echo "1. Update README.md"
            echo "2. Finalize CHANGELOG.md"
            echo "3. Tag release"
            ;;
        P7)
            echo "1. Run health checks"
            echo "2. Verify SLOs"
            echo "3. Generate monitoring report"
            ;;
    esac
}

ce_phase_estimate_completion() {
    # Estimate time to complete phase
    # Returns: Estimated time in human-readable format

    local phase=$(ce_phase_get_current)

    # Simple estimation based on phase type
    case "$phase" in
        P0) echo "1-2 hours" ;;
        P1) echo "30-60 minutes" ;;
        P2) echo "30 minutes" ;;
        P3) echo "2-4 hours" ;;
        P4) echo "1-2 hours" ;;
        P5) echo "30-60 minutes" ;;
        P6) echo "30 minutes" ;;
        P7) echo "15-30 minutes" ;;
        *) echo "Unknown" ;;
    esac
}

# ============================================================================
# Phase configuration
# ============================================================================

ce_phase_load_config() {
    # Load phase configuration from STAGES.yml or gates.yml
    # Returns: Config content

    if [[ -f "${CE_GATES_CONFIG}" ]]; then
        cat "${CE_GATES_CONFIG}"
    elif [[ -f "${CE_PHASES_CONFIG}" ]]; then
        cat "${CE_PHASES_CONFIG}"
    else
        echo "ERROR: No phase configuration found" >&2
        return 1
    fi
}

ce_phase_validate_config() {
    # Validate phase configuration file
    # Returns: 0 if valid, 1 with errors

    local config_file="${CE_GATES_CONFIG}"

    [[ ! -f "$config_file" ]] && {
        echo "ERROR: Config file not found: $config_file" >&2
        return 1
    }

    # Validate YAML syntax
    if $HAS_YQ; then
        yq eval '.' "$config_file" &>/dev/null || {
            echo "ERROR: Invalid YAML syntax" >&2
            return 1
        }
    fi

    # Check required fields
    for phase in P0 P1 P2 P3 P4 P5 P6 P7; do
        if $HAS_YQ; then
            yq eval ".phases.${phase}" "$config_file" &>/dev/null || {
                echo "ERROR: Missing phase definition: $phase" >&2
                return 1
            }
        fi
    done

    return 0
}

# ============================================================================
# Progress tracking
# ============================================================================

ce_phase_get_progress() {
    # Calculate phase completion percentage
    # Returns: 0-100 percentage

    local phase=$(ce_phase_get_current)

    # Simple calculation based on gates and deliverables
    local total=2
    local completed=0

    if ce_phase_check_gates "$phase" 2>/dev/null; then
        completed=$((completed + 1))
    fi

    if ce_phase_check_deliverables "$phase" 2>/dev/null; then
        completed=$((completed + 1))
    fi

    echo $(( completed * 100 / total ))
}

ce_phase_show_progress() {
    # Display visual progress for phase
    # Output: Progress bar and statistics

    local phase=$(ce_phase_get_current)
    local name=$(ce_phase_get_name "$phase")
    local progress=$(ce_phase_get_progress)

    echo "Phase $phase: $name"

    # Progress bar
    local filled=$((progress / 10))
    local empty=$((10 - filled))

    printf "Progress: ["
    for ((i=0; i<filled; i++)); do printf "█"; done
    for ((i=0; i<empty; i++)); do printf "░"; done
    printf "] %d%%\n" "$progress"

    # Status
    local gates_status="pending"
    if ce_phase_check_gates "$phase" 2>/dev/null; then
        gates_status="passed"
    fi

    local deliverables_status="incomplete"
    if ce_phase_check_deliverables "$phase" 2>/dev/null; then
        deliverables_status="complete"
    fi

    echo "Gates: $gates_status"
    echo "Deliverables: $deliverables_status"
}

# ============================================================================
# Helper functions
# ============================================================================

ce_phase_get_allowed_next() {
    # Get list of allowed next phases
    # Returns: Array of phase codes

    local current_phase=$(ce_phase_get_current)
    local current_num="${current_phase#P}"

    # Can always go forward or backward
    local next_num=$((current_num + 1))
    local prev_num=$((current_num - 1))

    local allowed=()

    if (( prev_num >= 0 )); then
        allowed+=("P${prev_num}")
    fi

    if (( next_num <= 7 )); then
        allowed+=("P${next_num}")
    fi

    printf "%s\n" "${allowed[@]}"
}

ce_phase_verify_gates_passed() {
    # Verify all gates passed for phase progression
    # Usage: ce_phase_verify_gates_passed "P3"

    local phase="${1:-$(ce_phase_get_current)}"

    if ce_phase_check_gates "$phase"; then
        echo "All gates passed for $phase"
        return 0
    else
        echo "Gates not passed for $phase"
        return 1
    fi
}

ce_phase_rollback() {
    # Rollback to previous phase (with safety checks)
    # Usage: ce_phase_rollback

    local current_phase=$(ce_phase_get_current)

    echo "WARNING: Rolling back from $current_phase" >&2
    echo "This may require manual cleanup of changes" >&2

    ce_phase_previous
}

# ============================================================================
# Export functions
# ============================================================================

export -f ce_phase_get_current
export -f ce_phase_get_name
export -f ce_phase_get_description
export -f ce_phase_get_info
export -f ce_phase_list_all
export -f ce_phase_transition
export -f ce_phase_validate_transition
export -f ce_phase_can_skip_to
export -f ce_phase_next
export -f ce_phase_previous
export -f ce_phase_get_gates
export -f ce_phase_validate_gates
export -f ce_phase_get_gate_status
export -f ce_phase_check_gates
export -f ce_phase_check_gate_scores
export -f ce_phase_get_deliverables
export -f ce_phase_check_deliverables
export -f ce_phase_generate_checklist
export -f ce_phase_get_duration
export -f ce_phase_get_history
export -f ce_phase_get_stats
export -f ce_phase_run_entry_hook
export -f ce_phase_run_exit_hook
export -f ce_phase_suggest_next_actions
export -f ce_phase_estimate_completion
export -f ce_phase_load_config
export -f ce_phase_validate_config
export -f ce_phase_get_progress
export -f ce_phase_show_progress
