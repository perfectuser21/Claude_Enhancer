#!/usr/bin/env bash
# Anti-Hollow Contract Tests
# Purpose: Verify critical features actually WORK, not just exist
# Version: 1.0.0
# Created: 2025-10-30
#
# These are CONTRACT TESTS - they verify that advertised features
# actually function as promised, not just that files exist.

set -euo pipefail

# ============================================================================
# Setup and Configuration
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_TEMP="${PROJECT_ROOT}/.temp/contract_tests"
FAILED_CONTRACTS=0
PASSED_CONTRACTS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

assert_file_exists() {
    local file="$1"
    local description="${2:-File should exist}"

    if [[ -f "$file" ]]; then
        log_success "Assert: $description ($file exists)"
        return 0
    else
        log_failure "Assert: $description ($file NOT FOUND)"
        return 1
    fi
}

assert_file_contains() {
    local file="$1"
    local pattern="$2"
    local description="${3:-File should contain pattern}"

    if [[ ! -f "$file" ]]; then
        log_failure "Assert: $description (file $file not found)"
        return 1
    fi

    if grep -q "$pattern" "$file"; then
        log_success "Assert: $description (pattern found)"
        return 0
    else
        log_failure "Assert: $description (pattern '$pattern' NOT FOUND in $file)"
        return 1
    fi
}

assert_exit_code() {
    local actual="$1"
    local expected="$2"
    local description="${3:-Exit code should match}"

    if [[ "$actual" -eq "$expected" ]]; then
        log_success "Assert: $description (exit code $actual)"
        return 0
    else
        log_failure "Assert: $description (expected $expected, got $actual)"
        return 1
    fi
}

assert_json_equals() {
    local path="$1"
    local value="$2"
    local description="${3:-JSON value should match}"

    if ! command -v jq &>/dev/null; then
        log_warning "jq not available, skipping JSON assertion"
        return 0
    fi

    local actual
    actual=$(jq -r "$path" "${PROJECT_ROOT}/.claude/settings.json" 2>/dev/null || echo "")

    if [[ "$actual" == "$value" ]]; then
        log_success "Assert: $description (value='$value')"
        return 0
    else
        log_failure "Assert: $description (expected '$value', got '$actual')"
        return 1
    fi
}

# ============================================================================
# Test Setup
# ============================================================================

setup_test_environment() {
    log_info "Setting up test environment..."

    # Clean and create temp directory
    rm -rf "$TEST_TEMP"
    mkdir -p "$TEST_TEMP"

    # Backup current phase if exists
    if [[ -f "${PROJECT_ROOT}/.phase/current" ]]; then
        cp "${PROJECT_ROOT}/.phase/current" "${TEST_TEMP}/phase.backup"
    fi

    # Clear any existing suggester logs
    mkdir -p "${PROJECT_ROOT}/.workflow/logs/subagent"

    log_success "Test environment ready"
}

teardown_test_environment() {
    log_info "Tearing down test environment..."

    # Restore phase if backed up
    if [[ -f "${TEST_TEMP}/phase.backup" ]]; then
        mkdir -p "${PROJECT_ROOT}/.phase"
        cp "${TEST_TEMP}/phase.backup" "${PROJECT_ROOT}/.phase/current"
    fi

    # Clean up temp directory
    rm -rf "$TEST_TEMP"

    log_success "Test environment cleaned up"
}

# ============================================================================
# Contract Test 1: parallel_subagent_suggester.sh Execution
# ============================================================================

test_parallel_subagent_suggester_execution() {
    echo ""
    echo "======================================================================"
    echo "CONTRACT TEST 1: parallel_subagent_suggester.sh Actually Executes"
    echo "======================================================================"
    echo ""

    local test_passed=true
    local hook_script="${PROJECT_ROOT}/.claude/hooks/parallel_subagent_suggester.sh"
    local log_file="${PROJECT_ROOT}/.workflow/logs/subagent/suggester.log"

    # Setup: Create Phase2 marker
    log_info "Setup: Setting current phase to Phase2"
    mkdir -p "${PROJECT_ROOT}/.phase"
    echo "Phase2" > "${PROJECT_ROOT}/.phase/current"

    # Clear existing log
    rm -f "$log_file"

    # Run: Execute the hook
    log_info "Running: bash $hook_script"

    local exit_code=0
    bash "$hook_script" > "${TEST_TEMP}/suggester_output.txt" 2>&1 || exit_code=$?

    # Assert 1: Hook executed successfully (exit 0)
    if ! assert_exit_code "$exit_code" 0 "Hook should exit successfully"; then
        test_passed=false
    fi

    # Assert 2: Log file was created
    if ! assert_file_exists "$log_file" "Suggester log should be created"; then
        test_passed=false
    fi

    # Assert 3: Log contains Phase2
    if ! assert_file_contains "$log_file" "Phase2" "Log should mention Phase2"; then
        test_passed=false
    fi

    # Assert 4: Log contains timestamp (indicates it actually ran)
    if ! assert_file_contains "$log_file" "Triggered for Phase2" "Log should show trigger message"; then
        test_passed=false
    fi

    # Assert 5: Output contains suggestion markers
    if grep -q "Parallel Subagent Suggestion" "${TEST_TEMP}/suggester_output.txt"; then
        log_success "Assert: Output contains suggestion markers"
    else
        log_failure "Assert: Output should contain suggestion markers"
        test_passed=false
    fi

    # Report result
    echo ""
    if $test_passed; then
        log_success "CONTRACT TEST 1: PASSED"
        ((PASSED_CONTRACTS++))
    else
        log_failure "CONTRACT TEST 1: FAILED"
        ((FAILED_CONTRACTS++))
    fi

    if [ "$test_passed" = true ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Contract Test 2: phase_manager.sh Transitions Work
# ============================================================================

test_phase_manager_transitions() {
    echo ""
    echo "======================================================================"
    echo "CONTRACT TEST 2: phase_manager.sh Transitions Work"
    echo "======================================================================"
    echo ""

    local test_passed=true
    local phase_manager="${PROJECT_ROOT}/.workflow/cli/phase_manager.sh"
    local phase_file="${PROJECT_ROOT}/.phase/current"

    # Setup: Source the phase manager
    log_info "Setup: Sourcing phase_manager.sh"

    # shellcheck disable=SC1090
    if ! source "$phase_manager" 2>/dev/null; then
        log_failure "Failed to source phase_manager.sh"
        log_failure "CONTRACT TEST 2: FAILED"
        ((FAILED_CONTRACTS++))
        return 1
    fi

    # Setup: Set initial phase to P2
    log_info "Setup: Setting initial phase to P2"
    mkdir -p "$(dirname "$phase_file")"
    echo "P2" > "$phase_file"

    # Run: Transition to P3
    log_info "Running: ce_phase_transition P3"

    local exit_code=0
    local output
    output=$(ce_phase_transition "P3" 2>&1) || exit_code=$?

    # Assert 1: Function returned success
    if ! assert_exit_code "$exit_code" 0 "Transition should succeed"; then
        test_passed=false
    fi

    # Assert 2: Phase file contains P3
    if [[ -f "$phase_file" ]]; then
        local current_phase
        current_phase=$(tr -d '[:space:]' < "$phase_file")
        if [[ "$current_phase" == "P3" ]]; then
            log_success "Assert: Phase file contains P3"
        else
            log_failure "Assert: Phase file should contain P3 (got: $current_phase)"
            test_passed=false
        fi
    else
        log_failure "Assert: Phase file should exist after transition"
        test_passed=false
    fi

    # Assert 3: Output confirms transition
    if echo "$output" | grep -q "Transitioned.*P2.*P3"; then
        log_success "Assert: Output confirms transition from P2 to P3"
    else
        log_failure "Assert: Output should confirm transition"
        test_passed=false
    fi

    # Additional test: Try invalid phase
    log_info "Testing: Invalid phase code (should fail)"
    exit_code=0
    ce_phase_transition "P99" &>/dev/null || exit_code=$?

    if [[ "$exit_code" -ne 0 ]]; then
        log_success "Assert: Invalid phase code rejected correctly"
    else
        log_failure "Assert: Invalid phase code should be rejected"
        test_passed=false
    fi

    # Report result
    echo ""
    if $test_passed; then
        log_success "CONTRACT TEST 2: PASSED"
        ((PASSED_CONTRACTS++))
    else
        log_failure "CONTRACT TEST 2: FAILED"
        ((FAILED_CONTRACTS++))
    fi

    if [ "$test_passed" = true ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Contract Test 3: Bypass Permissions Configured
# ============================================================================

test_bypass_permissions_configured() {
    echo ""
    echo "======================================================================"
    echo "CONTRACT TEST 3: Bypass Permissions Configured Correctly"
    echo "======================================================================"
    echo ""

    local test_passed=true
    local settings_file="${PROJECT_ROOT}/.claude/settings.json"

    # Assert 1: settings.json exists
    if ! assert_file_exists "$settings_file" "Settings file should exist"; then
        log_failure "CONTRACT TEST 3: FAILED (settings.json not found)"
        ((FAILED_CONTRACTS++))
        return 1
    fi

    # Assert 2: defaultMode is bypassPermissions
    if ! assert_json_equals '.permissions.defaultMode' 'bypassPermissions' \
        "defaultMode should be bypassPermissions"; then
        log_error "Bypass permissions not configured - this will cause permission prompts!"
        log_info "User reported: 'bypass 的这些我都说了不下 10 回了还是错的'"
        log_info "Fix: Ensure .permissions.defaultMode = 'bypassPermissions' (not top-level)"
        test_passed=false
    fi

    # Assert 2.5: Verify it's under .permissions, not top-level (common mistake)
    if jq -e '.defaultMode' "$settings_file" >/dev/null 2>&1; then
        log_failure "defaultMode found at top-level - WRONG LOCATION"
        log_info "Should be: .permissions.defaultMode"
        log_info "Not: .defaultMode"
        test_passed=false
    fi

    # Assert 3: Bash is in allow list
    if jq -e '.permissions.allow[] | select(. == "Bash")' "$settings_file" &>/dev/null; then
        log_success "Assert: Bash is in allow list"
    else
        log_failure "Assert: Bash should be in allow list"
        test_passed=false
    fi

    # Assert 4: Read/Write/Edit are allowed
    local tools=("Read" "Write" "Edit" "Glob" "Grep")
    for tool in "${tools[@]}"; do
        if jq -e ".permissions.allow[] | select(. == \"$tool\")" "$settings_file" &>/dev/null; then
            log_success "Assert: $tool is in allow list"
        else
            log_failure "Assert: $tool should be in allow list"
            test_passed=false
        fi
    done

    # Report result
    echo ""
    if $test_passed; then
        log_success "CONTRACT TEST 3: PASSED"
        ((PASSED_CONTRACTS++))
    else
        log_failure "CONTRACT TEST 3: FAILED"
        ((FAILED_CONTRACTS++))
    fi

    if [ "$test_passed" = true ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Contract Test 4: Critical Hooks Registered
# ============================================================================

test_critical_hooks_registered() {
    echo ""
    echo "======================================================================"
    echo "CONTRACT TEST 4: All Critical Hooks Are Registered"
    echo "======================================================================"
    echo ""

    local test_passed=true
    local settings_file="${PROJECT_ROOT}/.claude/settings.json"

    # Define P0 (critical) hooks
    # PrePrompt hooks
    local preprompt_hooks=(
        "force_branch_check.sh"
        "workflow_enforcer.sh"
        "parallel_subagent_suggester.sh"
    )

    # PreToolUse hooks
    local pretooluse_hooks=(
        "task_branch_enforcer.sh"
        "code_writing_check.sh"
        "quality_gate.sh"
    )

    # Check PrePrompt hooks
    log_info "Checking PrePrompt hooks..."
    for hook in "${preprompt_hooks[@]}"; do
        if jq -e ".hooks.PrePrompt[] | select(endswith(\"$hook\"))" "$settings_file" &>/dev/null; then
            log_success "Assert: PrePrompt hook $hook is registered"
        else
            log_failure "Assert: PrePrompt hook $hook should be registered"
            test_passed=false
        fi
    done

    # Check PreToolUse hooks
    log_info "Checking PreToolUse hooks..."
    for hook in "${pretooluse_hooks[@]}"; do
        if jq -e ".hooks.PreToolUse[] | select(endswith(\"$hook\"))" "$settings_file" &>/dev/null; then
            log_success "Assert: PreToolUse hook $hook is registered"
        else
            log_failure "Assert: PreToolUse hook $hook should be registered"
            test_passed=false
        fi
    done

    # Check that hooks are executable
    log_info "Checking hook executability..."
    local all_hooks=(
        ".claude/hooks/parallel_subagent_suggester.sh"
        ".claude/hooks/workflow_enforcer.sh"
        ".claude/hooks/quality_gate.sh"
    )

    for hook_path in "${all_hooks[@]}"; do
        local full_path="${PROJECT_ROOT}/${hook_path}"
        if [[ -f "$full_path" ]]; then
            if [[ -x "$full_path" ]]; then
                log_success "Assert: Hook $hook_path is executable"
            else
                log_warning "Hook $hook_path exists but is not executable"
                # Not failing the test for this, but warning
            fi
        fi
    done

    # Report result
    echo ""
    if $test_passed; then
        log_success "CONTRACT TEST 4: PASSED"
        ((PASSED_CONTRACTS++))
    else
        log_failure "CONTRACT TEST 4: FAILED"
        ((FAILED_CONTRACTS++))
    fi

    if [ "$test_passed" = true ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Main Test Runner
# ============================================================================

run_all_contract_tests() {
    echo ""
    echo "***********************************************************************"
    echo "*                    ANTI-HOLLOW CONTRACT TESTS                      *"
    echo "*                                                                     *"
    echo "*  Purpose: Verify critical features WORK, not just exist            *"
    echo "*  Version: 1.0.0                                                    *"
    echo "*  Date: 2025-10-30                                                  *"
    echo "***********************************************************************"
    echo ""

    setup_test_environment

    # Run all contract tests
    test_parallel_subagent_suggester_execution
    test_phase_manager_transitions
    test_bypass_permissions_configured
    test_critical_hooks_registered

    teardown_test_environment

    # Print summary
    echo ""
    echo "======================================================================"
    echo "                        TEST SUMMARY                                  "
    echo "======================================================================"
    echo ""
    echo -e "Total Tests:  $(( PASSED_CONTRACTS + FAILED_CONTRACTS ))"
    echo -e "${GREEN}Passed:       $PASSED_CONTRACTS${NC}"
    echo -e "${RED}Failed:       $FAILED_CONTRACTS${NC}"
    echo ""

    if [[ "$FAILED_CONTRACTS" -eq 0 ]]; then
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  ALL CONTRACT TESTS PASSED!${NC}"
        echo -e "${GREEN}  Features are ACTUALLY working!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}  SOME CONTRACT TESTS FAILED!${NC}"
        echo -e "${RED}  $FAILED_CONTRACTS feature(s) not working!${NC}"
        echo -e "${RED}========================================${NC}"
        echo ""
        return 1
    fi
}

# ============================================================================
# Entry Point
# ============================================================================

main() {
    # Check if running from correct directory
    if [[ ! -f "${PROJECT_ROOT}/.claude/settings.json" ]]; then
        log_failure "This script must be run from Claude Enhancer project root"
        log_failure "Current PROJECT_ROOT: $PROJECT_ROOT"
        exit 1
    fi

    # Run all tests
    run_all_contract_tests
    exit $?
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
