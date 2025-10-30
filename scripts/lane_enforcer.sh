#!/bin/bash
# Lane Enforcer - Phase-Based Operation Restrictions
# Enforces that operations are only allowed in the appropriate Phase
#
# Usage:
#   source scripts/lane_enforcer.sh
#   lane_enforcer_check_operation "write_code"
#   lane_enforcer_set_lane "implementation"

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Lane Definitions
# ============================================

# Define allowed operations for each lane (Phase)
declare -A LANE_OPERATIONS

LANE_OPERATIONS[planning]="create_discovery create_checklist create_plan edit_docs read_files"
LANE_OPERATIONS[implementation]="write_code edit_code create_scripts create_hooks commit_code"
LANE_OPERATIONS[testing]="run_tests write_tests check_coverage run_static_checks"
LANE_OPERATIONS[review]="code_review create_review_doc audit_code"
LANE_OPERATIONS[release]="update_changelog bump_version create_tag update_docs"
LANE_OPERATIONS[acceptance]="run_acceptance_tests create_acceptance_report user_validation"
LANE_OPERATIONS[closure]="cleanup delete_temp_files verify_consistency create_pr"

# Phase to Lane mapping
declare -A PHASE_TO_LANE
PHASE_TO_LANE[Phase1]="planning"
PHASE_TO_LANE[Phase2]="implementation"
PHASE_TO_LANE[Phase3]="testing"
PHASE_TO_LANE[Phase4]="review"
PHASE_TO_LANE[Phase5]="release"
PHASE_TO_LANE[Phase6]="acceptance"
PHASE_TO_LANE[Phase7]="closure"

# ============================================
# Lane Management
# ============================================

# Get current lane from state
lane_enforcer_get_current_lane() {
    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        local current_phase
        current_phase=$(state_get "current_phase.phase")

        if [[ -n "$current_phase" ]] && [[ "$current_phase" != "null" ]]; then
            echo "${PHASE_TO_LANE[$current_phase]}"
            return 0
        fi
    fi

    # Default to planning if unknown
    echo "planning"
}

# Set current lane
lane_enforcer_set_lane() {
    local lane="$1"

    # Validate lane
    local valid_lanes="${!LANE_OPERATIONS[*]}"
    if [[ ! " $valid_lanes " =~ [[:space:]]${lane}[[:space:]] ]]; then
        echo -e "${RED}❌ ERROR: Invalid lane: ${lane}${NC}" >&2
        echo "Valid lanes: $valid_lanes" >&2
        return 1
    fi

    # Update state
    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        state_set "lane_enforcer.current_lane" "$lane"
        state_set "lane_enforcer.enabled" "true"
    fi

    echo -e "${GREEN}✓${NC} Lane set to: $lane"
}

# Check if Lane Enforcer is enabled
lane_enforcer_is_enabled() {
    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        local enabled
        enabled=$(state_get "lane_enforcer.enabled")
        [[ "$enabled" == "true" ]]
    else
        return 1  # Not enabled if state manager not found
    fi
}

# ============================================
# Operation Checking
# ============================================

# Check if an operation is allowed in the current lane
# Returns: 0 if allowed, 1 if not allowed
lane_enforcer_check_operation() {
    local operation="$1"

    if ! lane_enforcer_is_enabled; then
        # Lane enforcer not enabled, allow all
        return 0
    fi

    local current_lane
    current_lane=$(lane_enforcer_get_current_lane)

    # Get allowed operations for current lane
    local allowed_ops="${LANE_OPERATIONS[$current_lane]}"

    # Check if operation is in the allowed list
    if [[ " $allowed_ops " == *" $operation "* ]]; then
        return 0  # Allowed
    fi

    # Not allowed
    return 1
}

# Enforce operation (check and block if not allowed)
lane_enforcer_enforce() {
    local operation="$1"
    local description="${2:-$operation}"

    if ! lane_enforcer_is_enabled; then
        return 0  # Not enabled, allow
    fi

    if lane_enforcer_check_operation "$operation"; then
        return 0  # Allowed
    fi

    # Operation not allowed - block with error
    local current_lane
    current_lane=$(lane_enforcer_get_current_lane)

    echo ""
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}❌ ERROR: Lane Violation${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Operation:${NC} $description"
    echo -e "${YELLOW}Current Lane:${NC} $current_lane"
    echo ""
    echo -e "${BLUE}Allowed operations in '$current_lane' lane:${NC}"
    echo "${LANE_OPERATIONS[$current_lane]}" | tr ' ' '\n' | sed 's/^/  - /'
    echo ""
    echo -e "${BLUE}💡 This operation is allowed in these lanes:${NC}"
    for lane in "${!LANE_OPERATIONS[@]}"; do
        if [[ " ${LANE_OPERATIONS[$lane]} " == *" $operation "* ]]; then
            echo "  - $lane"
        fi
    done
    echo ""
    echo -e "${BLUE}To proceed:${NC}"
    echo "  1. Transition to the appropriate Phase/Lane"
    echo "  2. Or disable Lane Enforcer if not applicable"
    echo ""
    echo -e "${RED}🚨 This is a HARD BLOCK - operation cannot proceed${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Update state
    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        state_increment "lane_enforcer.violations"
    fi

    return 1
}

# ============================================
# Operation Wrappers
# ============================================

# These functions wrap common operations and enforce lane restrictions

# Write code (allowed in implementation lane)
lane_write_code() {
    lane_enforcer_enforce "write_code" "Writing code" || return 1
    # If allowed, execute the actual operation
    echo -e "${GREEN}✓${NC} Code writing allowed in current lane"
}

# Run tests (allowed in testing lane)
lane_run_tests() {
    lane_enforcer_enforce "run_tests" "Running tests" || return 1
    echo -e "${GREEN}✓${NC} Testing allowed in current lane"
}

# Code review (allowed in review lane)
lane_code_review() {
    lane_enforcer_enforce "code_review" "Code review" || return 1
    echo -e "${GREEN}✓${NC} Code review allowed in current lane"
}

# Bump version (allowed in release lane)
lane_bump_version() {
    lane_enforcer_enforce "bump_version" "Bumping version" || return 1
    echo -e "${GREEN}✓${NC} Version bump allowed in current lane"
}

# Create PR (allowed in closure lane)
lane_create_pr() {
    lane_enforcer_enforce "create_pr" "Creating PR" || return 1
    echo -e "${GREEN}✓${NC} PR creation allowed in current lane"
}

# ============================================
# Reporting
# ============================================

# Show current lane status
lane_enforcer_show() {
    local current_lane
    current_lane=$(lane_enforcer_get_current_lane)

    local enabled="false"
    if lane_enforcer_is_enabled; then
        enabled="true"
    fi

    echo "════════════════════════════════════════════"
    echo "  Lane Enforcer - Phase-Based Restrictions"
    echo "════════════════════════════════════════════"
    echo ""
    echo "Enabled: $enabled"
    echo "Current Lane: $current_lane"
    echo ""
    echo "Allowed operations:"
    echo "${LANE_OPERATIONS[$current_lane]}" | tr ' ' '\n' | sed 's/^/  - /'
    echo ""
    echo "All lanes:"
    for lane in planning implementation testing review release acceptance closure; do
        echo "  $lane: ${LANE_OPERATIONS[$lane]}"
    done
    echo "════════════════════════════════════════════"
}

# Show lane statistics
lane_enforcer_stats() {
    if ! lane_enforcer_is_enabled; then
        echo "Lane Enforcer: Disabled"
        return 0
    fi

    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        local violations
        violations=$(state_get "lane_enforcer.violations")
        local current_lane
        current_lane=$(lane_enforcer_get_current_lane)
        echo "Lane Enforcer: Enabled"
        echo "Current Lane: $current_lane"
        echo "Violations: $violations"
    else
        echo "Lane Enforcer: Enabled (stats unavailable)"
    fi
}

# ============================================
# Enable/Disable
# ============================================

# Enable Lane Enforcer
lane_enforcer_enable() {
    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        state_set "lane_enforcer.enabled" "true"

        # Set lane based on current phase
        local current_phase
        current_phase=$(state_get "current_phase.phase")
        if [[ -n "$current_phase" ]] && [[ "$current_phase" != "null" ]]; then
            local lane="${PHASE_TO_LANE[$current_phase]}"
            state_set "lane_enforcer.current_lane" "$lane"
            echo -e "${GREEN}✓${NC} Lane Enforcer enabled (lane: $lane)"
        else
            state_set "lane_enforcer.current_lane" "planning"
            echo -e "${GREEN}✓${NC} Lane Enforcer enabled (lane: planning)"
        fi
    else
        echo -e "${RED}❌ ERROR: state_manager.sh not found${NC}" >&2
        return 1
    fi
}

# Disable Lane Enforcer
lane_enforcer_disable() {
    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        state_set "lane_enforcer.enabled" "false"
        echo -e "${YELLOW}⚠️${NC}  Lane Enforcer disabled"
    fi
}

# ============================================
# Main (if run directly)
# ============================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being run directly, not sourced
    case "${1:-}" in
        enable)
            lane_enforcer_enable
            ;;
        disable)
            lane_enforcer_disable
            ;;
        check)
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 check <operation>"
                exit 1
            fi
            if lane_enforcer_check_operation "$2"; then
                echo "✓ Operation allowed: $2"
                exit 0
            else
                echo "✗ Operation not allowed: $2"
                exit 1
            fi
            ;;
        enforce)
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 enforce <operation> [description]"
                exit 1
            fi
            lane_enforcer_enforce "$2" "${3:-$2}"
            ;;
        set-lane)
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 set-lane <lane>"
                exit 1
            fi
            lane_enforcer_set_lane "$2"
            ;;
        show)
            lane_enforcer_show
            ;;
        stats)
            lane_enforcer_stats
            ;;
        *)
            echo "Lane Enforcer - Phase-Based Operation Restrictions"
            echo ""
            echo "Usage:"
            echo "  $0 enable                       - Enable Lane Enforcer"
            echo "  $0 disable                      - Disable Lane Enforcer"
            echo "  $0 check <operation>            - Check if operation allowed"
            echo "  $0 enforce <operation> [desc]   - Enforce operation (block if not allowed)"
            echo "  $0 set-lane <lane>              - Set current lane"
            echo "  $0 show                         - Show current lane status"
            echo "  $0 stats                        - Show statistics"
            echo ""
            echo "Lanes: planning, implementation, testing, review, release, acceptance, closure"
            echo ""
            echo "Or source this file:"
            echo "  source scripts/lane_enforcer.sh"
            echo "  lane_enforcer_enforce 'write_code'"
            exit 1
            ;;
    esac
fi
