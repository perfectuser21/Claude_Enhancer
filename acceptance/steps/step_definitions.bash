#!/usr/bin/env bash
# BDD Step Definitions for Claude Enhancer
# Uses bash-based step matching similar to Cucumber

set -euo pipefail

# Source test helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../support/helpers.bash"
source "${SCRIPT_DIR}/../support/world.bash"

# ============================================================================
# GIVEN Steps - Setup preconditions
# ============================================================================

# @step "I am in a Claude Enhancer project"
step_i_am_in_a_claude_enhancer_project() {
    setup_test_project
    cd "$TEST_PROJECT_DIR"
}

# @step "the main branch is up to date"
step_the_main_branch_is_up_to_date() {
    git checkout main
    git pull origin main 2>/dev/null || true
}

# @step "I have a clean working directory"
step_i_have_a_clean_working_directory() {
    git reset --hard HEAD
    git clean -fd
}

# @step "I have {int} terminal sessions"
step_i_have_n_terminal_sessions() {
    local count=$1
    for i in $(seq 1 "$count"); do
        create_terminal_session "t$i"
    done
}

# @step "I am on a feature branch"
step_i_am_on_a_feature_branch() {
    git checkout -b "feature/P3-t1-test-feature" 2>/dev/null || git checkout "feature/P3-t1-test-feature"
}

# @step "I have multiple active terminal sessions"
step_i_have_multiple_active_terminal_sessions() {
    create_terminal_session "t1"
    create_terminal_session "t2"
    create_terminal_session "t3"
}

# @step "terminal {int} is working on {string} modifying {list}"
step_terminal_is_working_on_feature_modifying_files() {
    local terminal=$1
    local feature=$2
    local files=$3

    set_terminal_context "$terminal"
    set_terminal_feature "$feature"

    # Parse file list and mark as modified
    IFS=',' read -ra FILE_ARRAY <<< "${files//[\[\]\"]/}"
    for file in "${FILE_ARRAY[@]}"; do
        file=$(echo "$file" | xargs) # trim whitespace
        touch_modified_file "$file"
    done
}

# @step "I am in phase {string} with all gates passed"
step_i_am_in_phase_with_all_gates_passed() {
    local phase=$1
    echo "$phase" > .phase/current
    mark_all_gates_passed "$phase"
}

# @step "I am in phase {string}"
step_i_am_in_phase() {
    local phase=$1
    echo "$phase" > .phase/current
}

# @step "gate {string} has not passed"
step_gate_has_not_passed() {
    local gate=$1
    mark_gate_failed "$gate"
}

# @step "GitHub CLI is installed and authenticated"
step_github_cli_is_installed_and_authenticated() {
    if ! command -v gh &>/dev/null; then
        skip_scenario "GitHub CLI not installed"
    fi

    if ! gh auth status &>/dev/null; then
        skip_scenario "GitHub CLI not authenticated"
    fi
}

# @step "I have a feature branch {string}"
step_i_have_a_feature_branch() {
    local branch=$1
    git checkout -b "$branch" 2>/dev/null || git checkout "$branch"
}

# @step "quality gates are configured"
step_quality_gates_are_configured() {
    setup_quality_gates
}

# @step "I have code with hardcoded credentials"
step_i_have_code_with_hardcoded_credentials() {
    cat > src/test.js << 'EOF'
const apiKey = "sk_live_1234567890abcdef";
const dbUrl = "mongodb://user:password@localhost/db";
EOF
}

# ============================================================================
# WHEN Steps - Execute actions
# ============================================================================

# @step "I run {string} in terminal {int}"
step_i_run_command_in_terminal() {
    local command=$1
    local terminal=$2

    set_terminal_context "t$terminal"
    run_command "$command"
}

# @step "I run {string}"
step_i_run_command() {
    local command=$1
    run_command "$command"
}

# @step "I modify {string} in terminal {int}"
step_i_modify_file_in_terminal() {
    local file=$1
    local terminal=$2

    set_terminal_context "t$terminal"
    touch_modified_file "$file"
}

# @step "I commit changes in terminal {int} with message {string}"
step_i_commit_changes_in_terminal_with_message() {
    local terminal=$1
    local message=$2

    set_terminal_context "t$terminal"
    git add -A
    git commit -m "$message"
}

# @step "I close terminal {int}"
step_i_close_terminal() {
    local terminal=$1
    close_terminal_session "t$terminal"
}

# @step "I reopen terminal {int}"
step_i_reopen_terminal() {
    local terminal=$1
    reopen_terminal_session "t$terminal"
}

# ============================================================================
# THEN Steps - Verify outcomes
# ============================================================================

# @step "terminal {int} should have session {string} with branch matching {string}"
step_terminal_should_have_session_with_branch_matching() {
    local terminal=$1
    local session=$2
    local branch_pattern=$3

    set_terminal_context "t$terminal"
    verify_session_exists "$session"
    verify_branch_matches "$branch_pattern"
}

# @step "all {int} sessions should be independent"
step_all_sessions_should_be_independent() {
    local count=$1
    verify_sessions_independent "$count"
}

# @step "each session should have its own session directory"
step_each_session_should_have_its_own_session_directory() {
    verify_session_directories_exist
}

# @step "terminal {int} should be in phase {string}"
step_terminal_should_be_in_phase() {
    local terminal=$1
    local phase=$2

    set_terminal_context "t$terminal"
    verify_current_phase "$phase"
}

# @step "terminal {int} should still be in phase {string}"
step_terminal_should_still_be_in_phase() {
    step_terminal_should_be_in_phase "$1" "$2"
}

# @step "I should see {string}"
step_i_should_see() {
    local expected=$1
    verify_output_contains "$expected"
}

# @step "I should see error {string}"
step_i_should_see_error() {
    local expected=$1
    verify_error_contains "$expected"
}

# @step "I should see warning {string}"
step_i_should_see_warning() {
    local expected=$1
    verify_warning_contains "$expected"
}

# @step "the status should show {int} modified files"
step_the_status_should_show_n_modified_files() {
    local count=$1
    verify_modified_file_count "$count"
}

# @step "a PR should be created with title matching the branch"
step_a_pr_should_be_created_with_title_matching_the_branch() {
    verify_pr_created
    verify_pr_title_matches_branch
}

# @step "the PR description should include quality metrics"
step_the_pr_description_should_include_quality_metrics() {
    verify_pr_has_quality_metrics
}

# @step "I should be in phase {string}"
step_i_should_be_in_phase() {
    local phase=$1
    verify_current_phase "$phase"
}

# @step "the phase marker should be updated to {string}"
step_the_phase_marker_should_be_updated_to() {
    local phase=$1
    verify_phase_marker "$phase"
}

# @step "I should remain in phase {string}"
step_i_should_remain_in_phase() {
    local phase=$1
    verify_current_phase "$phase"
}

# @step "a branch should be created matching {string}"
step_a_branch_should_be_created_matching() {
    local pattern=$1
    verify_branch_matches "$pattern"
}

# @step "the branch should be checked out"
step_the_branch_should_be_checked_out() {
    verify_branch_checked_out
}

# @step "a session state file should be created"
step_a_session_state_file_should_be_created() {
    verify_session_state_file_exists
}

# @step "the session should be restored"
step_the_session_should_be_restored() {
    verify_session_restored
}

# @step "the file list should be preserved"
step_the_file_list_should_be_preserved() {
    verify_file_list_preserved
}

# @step "the system should check score (>= {int})"
step_the_system_should_check_score() {
    local min_score=$1
    verify_quality_score_checked "$min_score"
}

# @step "the system should check coverage (>= {int}%)"
step_the_system_should_check_coverage() {
    local min_coverage=$1
    verify_coverage_checked "$min_coverage"
}

# @step "the system should check security (no secrets)"
step_the_system_should_check_security() {
    verify_security_checked
}

# @step "the system should check signatures (all valid)"
step_the_system_should_check_signatures() {
    verify_signatures_checked
}

# ============================================================================
# Table Steps - Handle Cucumber tables
# ============================================================================

step_table_should_contain() {
    local expected_table=$1
    verify_table_contains "$expected_table"
}

step_the_following_should_be_verified() {
    local checks=$1
    verify_checks_executed "$checks"
}

# ============================================================================
# Utility Functions
# ============================================================================

run_command() {
    local cmd=$1
    LAST_COMMAND="$cmd"

    # Execute command and capture output
    set +e
    LAST_OUTPUT=$(eval "$cmd" 2>&1)
    LAST_EXIT_CODE=$?
    set -e

    echo "$LAST_OUTPUT" > "$WORLD_LAST_OUTPUT_FILE"
    echo "$LAST_EXIT_CODE" > "$WORLD_LAST_EXIT_CODE_FILE"
}

verify_output_contains() {
    local expected=$1
    if ! echo "$LAST_OUTPUT" | grep -q "$expected"; then
        fail "Expected output to contain: $expected\nActual output:\n$LAST_OUTPUT"
    fi
}

verify_error_contains() {
    local expected=$1
    if [[ $LAST_EXIT_CODE -eq 0 ]]; then
        fail "Expected command to fail, but it succeeded"
    fi
    verify_output_contains "$expected"
}

verify_warning_contains() {
    local expected=$1
    verify_output_contains "$expected"
}

verify_current_phase() {
    local expected_phase=$1
    local actual_phase=$(cat .phase/current 2>/dev/null || echo "unknown")

    if [[ "$actual_phase" != "$expected_phase" ]]; then
        fail "Expected phase: $expected_phase, Actual: $actual_phase"
    fi
}

verify_phase_marker() {
    local expected=$1
    verify_current_phase "$expected"
}

verify_branch_matches() {
    local pattern=$1
    local current_branch=$(git rev-parse --abbrev-ref HEAD)

    if [[ ! "$current_branch" =~ $pattern ]]; then
        fail "Branch '$current_branch' does not match pattern '$pattern'"
    fi
}

verify_branch_checked_out() {
    local branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$branch" == "main" ]] || [[ "$branch" == "master" ]]; then
        fail "Expected to be on a feature branch, but on: $branch"
    fi
}

verify_session_state_file_exists() {
    if [[ ! -d ".workflow/state/sessions" ]]; then
        fail "Session state directory not found"
    fi

    local session_count=$(find .workflow/state/sessions -mindepth 1 -maxdepth 1 -type d | wc -l)
    if [[ $session_count -eq 0 ]]; then
        fail "No session directories found"
    fi
}

verify_modified_file_count() {
    local expected=$1
    local actual=$(git status --porcelain | wc -l)

    if [[ $actual -ne $expected ]]; then
        fail "Expected $expected modified files, found $actual"
    fi
}

verify_quality_score_checked() {
    local min_score=$1
    verify_output_contains "quality score"
    verify_output_contains "$min_score"
}

verify_coverage_checked() {
    local min_coverage=$1
    verify_output_contains "coverage"
    verify_output_contains "${min_coverage}%"
}

verify_security_checked() {
    verify_output_contains "security"
}

verify_signatures_checked() {
    verify_output_contains "signature"
}

verify_pr_created() {
    # Check if gh pr create was called or PR URL is in output
    if ! echo "$LAST_OUTPUT" | grep -qE "(PR #|pull/[0-9]+|pr create)"; then
        fail "PR was not created"
    fi
}

verify_pr_title_matches_branch() {
    local branch=$(git rev-parse --abbrev-ref HEAD)
    local feature=$(echo "$branch" | grep -oP '(?<=-)[^-]+$')
    verify_output_contains "$feature"
}

verify_pr_has_quality_metrics() {
    verify_output_contains "quality"
    verify_output_contains "coverage"
}

# ============================================================================
# Helper Functions
# ============================================================================

fail() {
    local message=$1
    echo -e "FAILED: $message" >&2
    return 1
}

skip_scenario() {
    local reason=$1
    echo "SKIPPED: $reason"
    exit 0
}

# Export functions for use in step execution
export -f step_i_am_in_a_claude_enhancer_project
export -f step_i_run_command
export -f step_i_should_see
export -f run_command
export -f verify_output_contains
