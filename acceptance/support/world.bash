#!/usr/bin/env bash
# BDD World - Shared test context and state

set -euo pipefail

# ============================================================================
# Global Test State
# ============================================================================

# Test execution context
export WORLD_TEST_RUN_ID="test-$(date +%s)"
export WORLD_TMPDIR="${BATS_TMPDIR:-/tmp}/ce-bdd-${WORLD_TEST_RUN_ID}"
export WORLD_LAST_OUTPUT_FILE="${WORLD_TMPDIR}/last_output"
export WORLD_LAST_EXIT_CODE_FILE="${WORLD_TMPDIR}/last_exit_code"

# Current execution state
export LAST_COMMAND=""
export LAST_OUTPUT=""
export LAST_EXIT_CODE=0

# Terminal sessions
declare -A TERMINAL_SESSIONS
declare -A TERMINAL_BRANCHES
declare -A TERMINAL_PHASES

# Feature context
export CURRENT_FEATURE=""
export CURRENT_SCENARIO=""
export CURRENT_STEP=""

# Test counters
export SCENARIOS_PASSED=0
export SCENARIOS_FAILED=0
export SCENARIOS_SKIPPED=0
export STEPS_PASSED=0
export STEPS_FAILED=0

# ============================================================================
# World Initialization
# ============================================================================

world_init() {
    mkdir -p "$WORLD_TMPDIR"
    touch "$WORLD_LAST_OUTPUT_FILE"
    touch "$WORLD_LAST_EXIT_CODE_FILE"

    # Initialize state files
    echo "{}" > "${WORLD_TMPDIR}/sessions.json"
    echo "[]" > "${WORLD_TMPDIR}/modified_files.json"
    echo "{}" > "${WORLD_TMPDIR}/gates.json"
}

world_cleanup() {
    if [[ -d "$WORLD_TMPDIR" ]]; then
        rm -rf "$WORLD_TMPDIR"
    fi
}

# ============================================================================
# State Persistence
# ============================================================================

save_last_output() {
    local output=$1
    local exit_code=$2

    echo "$output" > "$WORLD_LAST_OUTPUT_FILE"
    echo "$exit_code" > "$WORLD_LAST_EXIT_CODE_FILE"

    export LAST_OUTPUT="$output"
    export LAST_EXIT_CODE=$exit_code
}

load_last_output() {
    if [[ -f "$WORLD_LAST_OUTPUT_FILE" ]]; then
        LAST_OUTPUT=$(cat "$WORLD_LAST_OUTPUT_FILE")
    fi

    if [[ -f "$WORLD_LAST_EXIT_CODE_FILE" ]]; then
        LAST_EXIT_CODE=$(cat "$WORLD_LAST_EXIT_CODE_FILE")
    fi
}

# ============================================================================
# Session State Management
# ============================================================================

save_session_state() {
    local terminal=$1
    local session_id=$2
    local branch=$3
    local phase=$4

    TERMINAL_SESSIONS[$terminal]=$session_id
    TERMINAL_BRANCHES[$terminal]=$branch
    TERMINAL_PHASES[$terminal]=$phase

    # Persist to file
    cat > "${WORLD_TMPDIR}/session_${terminal}.state" << EOF
SESSION_ID=$session_id
BRANCH=$branch
PHASE=$phase
CREATED_AT=$(date -Iseconds)
EOF
}

load_session_state() {
    local terminal=$1
    local state_file="${WORLD_TMPDIR}/session_${terminal}.state"

    if [[ -f "$state_file" ]]; then
        source "$state_file"
        TERMINAL_SESSIONS[$terminal]=$SESSION_ID
        TERMINAL_BRANCHES[$terminal]=$BRANCH
        TERMINAL_PHASES[$terminal]=$PHASE
    fi
}

# ============================================================================
# Modified Files Tracking
# ============================================================================

track_modified_file() {
    local file=$1
    local terminal=${2:-"default"}

    echo "{\"file\": \"$file\", \"terminal\": \"$terminal\", \"timestamp\": \"$(date -Iseconds)\"}" \
        >> "${WORLD_TMPDIR}/modified_files.jsonl"
}

get_modified_files() {
    local terminal=${1:-""}

    if [[ -f "${WORLD_TMPDIR}/modified_files.jsonl" ]]; then
        if [[ -z "$terminal" ]]; then
            cat "${WORLD_TMPDIR}/modified_files.jsonl"
        else
            grep "\"terminal\": \"$terminal\"" "${WORLD_TMPDIR}/modified_files.jsonl"
        fi
    fi
}

count_modified_files() {
    local terminal=${1:-""}
    get_modified_files "$terminal" | wc -l
}

# ============================================================================
# Gate State Management
# ============================================================================

set_gate_status() {
    local gate=$1
    local status=$2
    local reason=${3:-""}

    cat >> "${WORLD_TMPDIR}/gates.jsonl" << EOF
{"gate": "$gate", "status": "$status", "reason": "$reason", "timestamp": "$(date -Iseconds)"}
EOF
}

get_gate_status() {
    local gate=$1

    if [[ -f "${WORLD_TMPDIR}/gates.jsonl" ]]; then
        grep "\"gate\": \"$gate\"" "${WORLD_TMPDIR}/gates.jsonl" | tail -1 | \
            grep -oP '"status": "\K[^"]+' || echo "unknown"
    else
        echo "unknown"
    fi
}

# ============================================================================
# Scenario Context
# ============================================================================

set_scenario_context() {
    local feature=$1
    local scenario=$2

    export CURRENT_FEATURE="$feature"
    export CURRENT_SCENARIO="$scenario"

    echo "=== Running: $feature > $scenario ===" >&2
}

set_step_context() {
    local step=$1
    export CURRENT_STEP="$step"
}

# ============================================================================
# Test Results Tracking
# ============================================================================

record_scenario_result() {
    local status=$1

    case "$status" in
        passed)
            ((SCENARIOS_PASSED++))
            ;;
        failed)
            ((SCENARIOS_FAILED++))
            ;;
        skipped)
            ((SCENARIOS_SKIPPED++))
            ;;
    esac
}

record_step_result() {
    local status=$1

    case "$status" in
        passed)
            ((STEPS_PASSED++))
            ;;
        failed)
            ((STEPS_FAILED++))
            ;;
    esac
}

print_test_summary() {
    local total_scenarios=$((SCENARIOS_PASSED + SCENARIOS_FAILED + SCENARIOS_SKIPPED))
    local total_steps=$((STEPS_PASSED + STEPS_FAILED))

    cat << EOF

========================================
BDD Test Summary
========================================
Scenarios: $total_scenarios total
  Passed:  $SCENARIOS_PASSED
  Failed:  $SCENARIOS_FAILED
  Skipped: $SCENARIOS_SKIPPED

Steps: $total_steps total
  Passed: $STEPS_PASSED
  Failed: $STEPS_FAILED

Test Run ID: $WORLD_TEST_RUN_ID
========================================

EOF
}

# ============================================================================
# Debugging Helpers
# ============================================================================

dump_world_state() {
    cat << EOF
=== World State Dump ===
Test Run ID: $WORLD_TEST_RUN_ID
Temp Directory: $WORLD_TMPDIR

Current Context:
  Feature: $CURRENT_FEATURE
  Scenario: $CURRENT_SCENARIO
  Step: $CURRENT_STEP

Last Execution:
  Command: $LAST_COMMAND
  Exit Code: $LAST_EXIT_CODE
  Output: $LAST_OUTPUT

Terminal Sessions:
$(for t in "${!TERMINAL_SESSIONS[@]}"; do
    echo "  $t: ${TERMINAL_SESSIONS[$t]} (${TERMINAL_BRANCHES[$t]}, ${TERMINAL_PHASES[$t]})"
done)

Modified Files: $(count_modified_files)

Test Results:
  Scenarios Passed: $SCENARIOS_PASSED
  Scenarios Failed: $SCENARIOS_FAILED
  Steps Passed: $STEPS_PASSED
  Steps Failed: $STEPS_FAILED
========================
EOF
}

# ============================================================================
# Hooks
# ============================================================================

before_all() {
    world_init
    echo "BDD Test Suite Starting..." >&2
}

after_all() {
    print_test_summary
    world_cleanup
    echo "BDD Test Suite Completed." >&2
}

before_scenario() {
    load_last_output
}

after_scenario() {
    # Cleanup scenario-specific state
    :
}

# ============================================================================
# Export Functions
# ============================================================================

export -f world_init
export -f world_cleanup
export -f save_last_output
export -f load_last_output
export -f save_session_state
export -f load_session_state
export -f track_modified_file
export -f get_modified_files
export -f count_modified_files
export -f set_gate_status
export -f get_gate_status
export -f set_scenario_context
export -f set_step_context
export -f record_scenario_result
export -f record_step_result
export -f print_test_summary
export -f dump_world_state
export -f before_all
export -f after_all
export -f before_scenario
export -f after_scenario
