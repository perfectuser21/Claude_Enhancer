#!/usr/bin/env bats
# test_common.bats - Unit tests for common.sh library
# Tests logging, color output, utility functions, and security features

load '../helpers/test_helper'
load '../helpers/mock_helper'

setup() {
    setup_test_env
    source_lib "common"
}

teardown() {
    teardown_test_env
    mock_reset_all
}

# ============================================================================
# Logging Functions
# ============================================================================

@test "ce_log_debug: logs debug message when debug level enabled" {
    export CE_CURRENT_LOG_LEVEL=${CE_LOG_LEVEL_DEBUG}
    run ce_log_debug "test debug message"
    assert_success
    assert_output_contains "DEBUG"
    assert_output_contains "test debug message"
}

@test "ce_log_debug: suppresses output when level too high" {
    export CE_CURRENT_LOG_LEVEL=${CE_LOG_LEVEL_ERROR}
    run ce_log_debug "should not appear"
    assert_success
    [[ -z "${output}" ]]
}

@test "ce_log_info: logs info message" {
    run ce_log_info "test info"
    assert_success
    assert_output_contains "INFO"
    assert_output_contains "test info"
}

@test "ce_log_warn: logs warning message to stderr" {
    run ce_log_warn "test warning"
    assert_success
    assert_output_contains "WARN"
    assert_output_contains "test warning"
}

@test "ce_log_error: logs error message to stderr" {
    run ce_log_error "test error"
    assert_success
    assert_output_contains "ERROR"
    assert_output_contains "test error"
}

@test "ce_log_success: logs success message" {
    run ce_log_success "operation completed"
    assert_success
    assert_output_contains "SUCCESS"
    assert_output_contains "operation completed"
}

# ============================================================================
# Security Functions
# ============================================================================

@test "ce_log_sanitize: redacts password patterns" {
    local input="user password=secret123 token=abc"
    run ce_log_sanitize "${input}"
    assert_success
    assert_output_contains "password=***REDACTED***"
    assert_output_contains "token=***REDACTED***"
    [[ ! "${output}" =~ secret123 ]]
}

@test "ce_log_sanitize: redacts GitHub tokens" {
    local input="ghp_1234567890123456789012345678901234ABCD"
    run ce_log_sanitize "${input}"
    assert_success
    assert_output_contains "***GITHUB_TOKEN***"
    [[ ! "${output}" =~ ghp_ ]]
}

@test "ce_log_sanitize: redacts SSH keys" {
    local input="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ user@host"
    run ce_log_sanitize "${input}"
    assert_success
    assert_output_contains "***REDACTED***"
    [[ ! "${output}" =~ AAAAB3 ]]
}

@test "ce_create_secure_file: creates file with correct permissions" {
    local test_file="${CE_TEST_WORKSPACE}/secure.txt"
    run ce_create_secure_file "${test_file}" "secret content" "600"
    assert_success
    assert_file_exists "${test_file}"

    # Check permissions (600)
    local perms=$(stat -c '%a' "${test_file}" 2>/dev/null || stat -f '%Lp' "${test_file}" 2>/dev/null)
    [[ "${perms}" == "600" ]]
}

@test "ce_create_secure_file: rejects invalid permission format" {
    run ce_create_secure_file "/tmp/test.txt" "content" "999"
    assert_failure
    assert_output_contains "Invalid permission format"
}

@test "ce_create_secure_dir: creates directory with secure permissions" {
    local test_dir="${CE_TEST_WORKSPACE}/secure_dir"
    run ce_create_secure_dir "${test_dir}" "700"
    assert_success
    assert_dir_exists "${test_dir}"

    local perms=$(stat -c '%a' "${test_dir}" 2>/dev/null || stat -f '%Lp' "${test_dir}" 2>/dev/null)
    [[ "${perms}" == "700" ]]
}

# ============================================================================
# Color Output Functions
# ============================================================================

@test "ce_color_text: outputs text with color codes" {
    run ce_color_text "${CE_COLOR_RED}" "red text"
    assert_success
    assert_output_contains "red text"
}

@test "ce_color_red: outputs red text" {
    run ce_color_red "error message"
    assert_success
    assert_output_contains "error message"
}

@test "ce_color_green: outputs green text" {
    run ce_color_green "success message"
    assert_success
    assert_output_contains "success message"
}

# ============================================================================
# Utility Functions
# ============================================================================

@test "ce_require_command: succeeds for existing command" {
    run ce_require_command "bash"
    assert_success
}

@test "ce_require_command: fails for missing command" {
    run ce_require_command "nonexistent_command_xyz"
    assert_failure
    assert_output_contains "not found"
}

@test "ce_require_file: succeeds when file exists" {
    create_test_file "test.txt" "content"
    run ce_require_file "test.txt"
    assert_success
}

@test "ce_require_file: fails when file missing" {
    run ce_require_file "missing.txt"
    assert_failure
    assert_output_contains "not found"
}

@test "ce_get_project_root: finds .git directory" {
    run ce_get_project_root
    assert_success
    [[ -n "${output}" ]]
    [[ -d "${output}/.git" ]]
}

@test "ce_get_current_branch: returns current branch name" {
    git checkout -b test-branch --quiet
    run ce_get_current_branch
    assert_success
    assert_output_equals "test-branch"
}

@test "ce_get_timestamp: returns ISO 8601 timestamp" {
    run ce_get_timestamp
    assert_success
    [[ "${output}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]
}

@test "ce_trim: removes leading and trailing whitespace" {
    run ce_trim "  hello world  "
    assert_success
    assert_output_equals "hello world"
}

@test "ce_join: joins array elements with delimiter" {
    run ce_join "," "a" "b" "c"
    assert_success
    assert_output_equals "a,b,c"
}

@test "ce_is_git_repo: returns true in git repo" {
    run ce_is_git_repo
    assert_success
}

@test "ce_is_git_repo: returns false outside git repo" {
    cd /tmp
    run ce_is_git_repo
    assert_failure
}

@test "ce_is_ce_project: detects .workflow directory" {
    run ce_is_ce_project
    assert_success
}

@test "ce_format_duration: formats seconds to human readable" {
    run ce_format_duration 3665
    assert_success
    assert_output_contains "1h"
    assert_output_contains "1m"
    assert_output_contains "5s"
}

@test "ce_format_duration: handles zero seconds" {
    run ce_format_duration 0
    assert_success
    assert_output_equals "0s"
}

@test "ce_format_bytes: formats bytes to human readable" {
    run ce_format_bytes 1048576
    assert_success
    assert_output_contains "MB"
}

@test "ce_create_temp_file: creates temporary file" {
    run ce_create_temp_file
    assert_success
    local temp_file="${output}"
    assert_file_exists "${temp_file}"
}

@test "ce_create_temp_dir: creates temporary directory" {
    run ce_create_temp_dir
    assert_success
    local temp_dir="${output}"
    assert_dir_exists "${temp_dir}"
}

@test "ce_die: exits with error message" {
    run ce_die "fatal error" 42
    assert_failure
    [[ $status -eq 42 ]]
    assert_output_contains "fatal error"
}

@test "ce_debug_mode: returns success when debug enabled" {
    export CE_CURRENT_LOG_LEVEL=${CE_LOG_LEVEL_DEBUG}
    run ce_debug_mode
    assert_success
}

@test "ce_debug_mode: returns failure when debug disabled" {
    export CE_CURRENT_LOG_LEVEL=${CE_LOG_LEVEL_INFO}
    run ce_debug_mode
    assert_failure
}

@test "ce_enable_debug: enables debug logging" {
    ce_enable_debug
    [[ ${CE_CURRENT_LOG_LEVEL} -eq ${CE_LOG_LEVEL_DEBUG} ]]
}

@test "ce_disable_debug: disables debug logging" {
    ce_disable_debug
    [[ ${CE_CURRENT_LOG_LEVEL} -eq ${CE_LOG_LEVEL_INFO} ]]
}

# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@test "ce_trim: handles empty string" {
    run ce_trim ""
    assert_success
    assert_output_equals ""
}

@test "ce_join: handles empty array" {
    run ce_join ","
    assert_success
    assert_output_equals ""
}

@test "ce_join: handles single element" {
    run ce_join "," "only"
    assert_success
    assert_output_equals "only"
}

@test "ce_format_duration: handles large durations" {
    run ce_format_duration 86400  # 1 day
    assert_success
    assert_output_contains "24h"
}

@test "ce_log_sanitize: handles string with no secrets" {
    run ce_log_sanitize "normal text without secrets"
    assert_success
    assert_output_equals "normal text without secrets"
}

@test "ce_create_secure_file: handles file creation error" {
    # Try to create file in non-existent directory without parent creation
    run ce_create_secure_file "/nonexistent/path/file.txt" "content"
    assert_failure
}
