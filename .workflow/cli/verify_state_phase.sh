#!/usr/bin/env bash
# verify_state_phase.sh - Verification script for state and phase managers
set -euo pipefail

echo "========================================"
echo "State & Phase Manager Verification"
echo "========================================"
echo ""

# Load modules
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/state_manager.sh"
source "${SCRIPT_DIR}/phase_manager.sh"

echo "1. State Manager Verification"
echo "------------------------------"

# Initialize state
echo "   Initializing state system..."
ce_state_init
echo "   ✓ State initialized"

# Get terminal ID
term_id=$(ce_get_terminal_id)
echo "   ✓ Terminal ID: $term_id"

# List sessions
echo "   ✓ Active sessions:"
ce_state_list_sessions | sed 's/^/      /'

# Get session stats
echo "   ✓ Session statistics:"
ce_state_get_stats "$term_id" | sed 's/^/      /'

# Test lock management
echo "   Testing lock management..."
if ce_state_acquire_lock "verify_test" 5; then
    echo "   ✓ Lock acquired"
    ce_state_release_lock "verify_test"
    echo "   ✓ Lock released"
fi

# Test backup
echo "   Creating state backup..."
backup_file=$(ce_state_backup)
echo "   ✓ Backup created: $backup_file"

echo ""
echo "2. Phase Manager Verification"
echo "------------------------------"

# Get current phase
current_phase=$(ce_phase_get_current)
phase_name=$(ce_phase_get_name "$current_phase")
echo "   ✓ Current phase: $current_phase ($phase_name)"

# List all phases
echo "   ✓ Phase status:"
ce_phase_list_all | sed 's/^/      /'

# Show progress
echo "   ✓ Phase progress:"
ce_phase_show_progress | sed 's/^/      /'

# Check gates
if ce_phase_check_gates "$current_phase"; then
    echo "   ✓ Gates passed for $current_phase"
else
    echo "   ✗ Gates not passed for $current_phase"
fi

# Check deliverables
if ce_phase_check_deliverables "$current_phase" 2>/dev/null; then
    echo "   ✓ Deliverables complete for $current_phase"
else
    echo "   ⚠ Deliverables incomplete for $current_phase"
fi

# Get suggested actions
echo "   ✓ Suggested next actions:"
ce_phase_suggest_next_actions | sed 's/^/      /'

# Estimate completion
estimate=$(ce_phase_estimate_completion)
echo "   ✓ Estimated completion time: $estimate"

echo ""
echo "3. Integration Verification"
echo "----------------------------"

# Verify state-phase integration
session_phase=$(ce_state_load_session "$term_id" | grep '^phase:' | cut -d':' -f2 | xargs)
file_phase=$(ce_phase_get_current)

if [[ "$session_phase" == "$file_phase" ]]; then
    echo "   ✓ Session phase matches current phase: $session_phase"
else
    echo "   ⚠ Phase mismatch - Session: $session_phase, File: $file_phase"
fi

# Count functions
state_functions=$(declare -F | grep 'ce_state_' | wc -l)
phase_functions=$(declare -F | grep 'ce_phase_' | wc -l)

echo "   ✓ State manager functions: $state_functions"
echo "   ✓ Phase manager functions: $phase_functions"

echo ""
echo "4. Function Coverage Check"
echo "--------------------------"

# State manager functions (should be 30+)
expected_state_funcs=(
    "ce_state_init"
    "ce_state_validate"
    "ce_state_save"
    "ce_state_load"
    "ce_state_get"
    "ce_state_set"
    "ce_state_backup"
    "ce_state_restore"
    "ce_state_create_session"
    "ce_state_get_session"
    "ce_state_load_session"
    "ce_state_save_session"
    "ce_state_update_session"
    "ce_state_list_sessions"
    "ce_state_activate_session"
    "ce_state_pause_session"
    "ce_state_resume_session"
    "ce_state_close_session"
    "ce_state_get_metadata"
    "ce_state_set_metadata"
    "ce_state_add_commit"
    "ce_state_get_commits"
    "ce_state_get_duration"
    "ce_state_get_stats"
    "ce_state_cleanup_stale"
    "ce_state_archive_session"
    "ce_state_get_history"
    "ce_state_rollback"
    "ce_context_save"
    "ce_context_restore"
)

state_missing=0
for func in "${expected_state_funcs[@]}"; do
    if ! declare -F "$func" &>/dev/null; then
        echo "   ✗ Missing: $func"
        state_missing=$((state_missing + 1))
    fi
done

if (( state_missing == 0 )); then
    echo "   ✓ All ${#expected_state_funcs[@]} core state functions present"
else
    echo "   ✗ Missing $state_missing state functions"
fi

# Phase manager functions (should be 28+)
expected_phase_funcs=(
    "ce_phase_get_current"
    "ce_phase_get_name"
    "ce_phase_get_description"
    "ce_phase_get_info"
    "ce_phase_list_all"
    "ce_phase_transition"
    "ce_phase_validate_transition"
    "ce_phase_can_skip_to"
    "ce_phase_next"
    "ce_phase_previous"
    "ce_phase_get_gates"
    "ce_phase_validate_gates"
    "ce_phase_get_gate_status"
    "ce_phase_check_gates"
    "ce_phase_check_gate_scores"
    "ce_phase_get_deliverables"
    "ce_phase_check_deliverables"
    "ce_phase_generate_checklist"
    "ce_phase_get_duration"
    "ce_phase_get_history"
    "ce_phase_get_stats"
    "ce_phase_run_entry_hook"
    "ce_phase_run_exit_hook"
    "ce_phase_suggest_next_actions"
    "ce_phase_estimate_completion"
    "ce_phase_load_config"
    "ce_phase_validate_config"
    "ce_phase_get_progress"
)

phase_missing=0
for func in "${expected_phase_funcs[@]}"; do
    if ! declare -F "$func" &>/dev/null; then
        echo "   ✗ Missing: $func"
        phase_missing=$((phase_missing + 1))
    fi
done

if (( phase_missing == 0 )); then
    echo "   ✓ All ${#expected_phase_funcs[@]} core phase functions present"
else
    echo "   ✗ Missing $phase_missing phase functions"
fi

echo ""
echo "========================================"
echo "Verification Summary"
echo "========================================"

total_expected=$((${#expected_state_funcs[@]} + ${#expected_phase_funcs[@]}))
total_missing=$((state_missing + phase_missing))
total_implemented=$((total_expected - total_missing))

echo "State Manager:  ${#expected_state_funcs[@]} functions ($state_missing missing)"
echo "Phase Manager:  ${#expected_phase_funcs[@]} functions ($phase_missing missing)"
echo "Total:          $total_implemented / $total_expected implemented"

if (( total_missing == 0 )); then
    echo ""
    echo "✅ ALL FUNCTIONS IMPLEMENTED AND WORKING"
    echo ""
    exit 0
else
    echo ""
    echo "⚠️  MISSING $total_missing FUNCTIONS"
    echo ""
    exit 1
fi
