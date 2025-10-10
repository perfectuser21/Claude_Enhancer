#!/usr/bin/env bats
# test_input_validator.bats - Unit tests for input_validator.sh library
# Tests input sanitization, validation, and security features

load '../helpers/test_helper'

setup() {
    setup_test_env
    source_lib "input_validator"
}

teardown() {
    teardown_test_env
}

# ============================================================================
# Sanitization Functions
# ============================================================================

@test "ce_sanitize_alphanum: removes non-alphanumeric characters" {
    run ce_sanitize_alphanum "hello@world#123"
    assert_success
    assert_output_equals "helloworld123"
}

@test "ce_sanitize_alphanum: preserves hyphens" {
    run ce_sanitize_alphanum "hello-world-123"
    assert_success
    assert_output_equals "hello-world-123"
}

@test "ce_sanitize_alphanum: truncates to max length" {
    run ce_sanitize_alphanum "abcdefghij" 5
    assert_success
    assert_output_equals "abcde"
}

@test "ce_sanitize_filename: replaces slashes with underscores" {
    run ce_sanitize_filename "path/to/file.txt"
    assert_success
    assert_output_equals "path_to_file.txt"
}

@test "ce_sanitize_filename: removes dangerous characters" {
    run ce_sanitize_filename "file\$name<>|.txt"
    assert_success
    assert_output_equals "filename.txt"
}

@test "ce_sanitize_filename: removes leading dots" {
    run ce_sanitize_filename ".hidden"
    assert_success
    assert_output_equals "hidden"
}

# ============================================================================
# Feature Name Validation
# ============================================================================

@test "ce_validate_feature_name: accepts valid lowercase name" {
    run ce_validate_feature_name "user-authentication"
    assert_success
}

@test "ce_validate_feature_name: accepts numbers in name" {
    run ce_validate_feature_name "feature-123"
    assert_success
}

@test "ce_validate_feature_name: rejects uppercase letters" {
    run ce_validate_feature_name "FeatureName"
    assert_failure
    assert_output_contains "lowercase"
}

@test "ce_validate_feature_name: rejects name too short" {
    run ce_validate_feature_name "a"
    assert_failure
    assert_output_contains "2-50 characters"
}

@test "ce_validate_feature_name: rejects name too long" {
    run ce_validate_feature_name "a-very-long-feature-name-that-exceeds-the-maximum-allowed-length-limit"
    assert_failure
    assert_output_contains "2-50 characters"
}

@test "ce_validate_feature_name: rejects consecutive hyphens" {
    run ce_validate_feature_name "feature--name"
    assert_failure
    assert_output_contains "consecutive hyphens"
}

@test "ce_validate_feature_name: rejects starting with hyphen" {
    run ce_validate_feature_name "-feature"
    assert_failure
}

@test "ce_validate_feature_name: rejects ending with hyphen" {
    run ce_validate_feature_name "feature-"
    assert_failure
}

@test "ce_validate_feature_name: rejects command injection characters" {
    run ce_validate_feature_name "feature;rm-rf"
    assert_failure
    assert_output_contains "prohibited characters"
}

@test "ce_validate_feature_name: rejects pipe characters" {
    run ce_validate_feature_name "feature|name"
    assert_failure
    assert_output_contains "prohibited characters"
}

@test "ce_validate_feature_name: rejects dollar signs" {
    run ce_validate_feature_name "feature\$name"
    assert_failure
    assert_output_contains "prohibited characters"
}

@test "ce_validate_feature_name: rejects backticks" {
    run ce_validate_feature_name "feature\`cmd\`"
    assert_failure
    assert_output_contains "prohibited characters"
}

# ============================================================================
# Terminal ID Validation
# ============================================================================

@test "ce_validate_terminal_id: accepts valid terminal ID" {
    run ce_validate_terminal_id "t1"
    assert_success
}

@test "ce_validate_terminal_id: accepts multi-digit terminal ID" {
    run ce_validate_terminal_id "t123"
    assert_success
}

@test "ce_validate_terminal_id: rejects missing t prefix" {
    run ce_validate_terminal_id "123"
    assert_failure
    assert_output_contains "t[0-9]+"
}

@test "ce_validate_terminal_id: rejects letters after t" {
    run ce_validate_terminal_id "tabc"
    assert_failure
    assert_output_contains "t[0-9]+"
}

@test "ce_validate_terminal_id: rejects path traversal attempts" {
    run ce_validate_terminal_id "t../../../etc"
    assert_failure
    assert_output_contains "invalid path characters"
}

@test "ce_validate_terminal_id: rejects forward slashes" {
    run ce_validate_terminal_id "t1/etc"
    assert_failure
    assert_output_contains "invalid path characters"
}

@test "ce_validate_terminal_id: rejects too long ID" {
    run ce_validate_terminal_id "t123456789012345678901"
    assert_failure
    assert_output_contains "too long"
}

# ============================================================================
# Path Validation
# ============================================================================

@test "ce_validate_path: accepts path within allowed prefix" {
    run ce_validate_path "${CE_TEST_WORKSPACE}/subdir" "${CE_TEST_WORKSPACE}"
    assert_success
    assert_output_contains "${CE_TEST_WORKSPACE}/subdir"
}

@test "ce_validate_path: rejects path outside allowed prefix" {
    run ce_validate_path "/tmp/outside" "${CE_TEST_WORKSPACE}"
    assert_failure
    assert_output_contains "path outside allowed directory"
}

@test "ce_validate_path: rejects path traversal with ../" {
    run ce_validate_path "${CE_TEST_WORKSPACE}/../../../etc/passwd" "${CE_TEST_WORKSPACE}"
    assert_failure
    assert_output_contains "path outside allowed directory"
}

@test "ce_validate_path: accepts exact match of prefix" {
    run ce_validate_path "${CE_TEST_WORKSPACE}" "${CE_TEST_WORKSPACE}"
    assert_success
}

@test "ce_validate_path: rejects empty path" {
    run ce_validate_path "" "${CE_TEST_WORKSPACE}"
    assert_failure
    assert_output_contains "cannot be empty"
}

@test "ce_validate_path: rejects empty prefix" {
    run ce_validate_path "/some/path" ""
    assert_failure
    assert_output_contains "must be specified"
}

# ============================================================================
# Phase Validation
# ============================================================================

@test "ce_validate_phase: accepts P0 through P7" {
    for phase in P0 P1 P2 P3 P4 P5 P6 P7; do
        run ce_validate_phase "${phase}"
        assert_success
    done
}

@test "ce_validate_phase: rejects P8" {
    run ce_validate_phase "P8"
    assert_failure
    assert_output_contains "Invalid phase"
}

@test "ce_validate_phase: rejects lowercase phase" {
    run ce_validate_phase "p3"
    assert_failure
    assert_output_contains "Invalid phase"
}

@test "ce_validate_phase: rejects phase without number" {
    run ce_validate_phase "P"
    assert_failure
    assert_output_contains "Invalid phase"
}

# ============================================================================
# Branch Name Validation
# ============================================================================

@test "ce_validate_branch_name: accepts feature branch" {
    run ce_validate_branch_name "feature/user-auth"
    assert_success
}

@test "ce_validate_branch_name: accepts fix branch" {
    run ce_validate_branch_name "fix/bug-123"
    assert_success
}

@test "ce_validate_branch_name: accepts all valid types" {
    local types=("feature" "feat" "fix" "docs" "test" "refactor" "chore" "hotfix" "release")
    for type in "${types[@]}"; do
        run ce_validate_branch_name "${type}/test-branch"
        assert_success
    done
}

@test "ce_validate_branch_name: rejects invalid type" {
    run ce_validate_branch_name "invalid/branch"
    assert_failure
    assert_output_contains "Invalid branch name format"
}

@test "ce_validate_branch_name: rejects missing slash separator" {
    run ce_validate_branch_name "feature-branch"
    assert_failure
}

@test "ce_validate_branch_name: rejects too short name" {
    run ce_validate_branch_name "f/x"
    assert_failure
    assert_output_contains "3-80 characters"
}

@test "ce_validate_branch_name: rejects too long name" {
    run ce_validate_branch_name "feature/this-is-an-extremely-long-branch-name-that-exceeds-the-maximum-allowed-length"
    assert_failure
    assert_output_contains "3-80 characters"
}

@test "ce_validate_branch_name: rejects path traversal patterns" {
    run ce_validate_branch_name "feature/../../../etc/passwd"
    assert_failure
    assert_output_contains "path traversal patterns"
}

@test "ce_validate_branch_name: rejects command injection" {
    run ce_validate_branch_name "feature/test;rm-rf"
    assert_failure
    assert_output_contains "prohibited characters"
}

# ============================================================================
# Description Validation
# ============================================================================

@test "ce_validate_description: accepts normal text" {
    run ce_validate_description "This is a valid description."
    assert_success
}

@test "ce_validate_description: accepts description with punctuation" {
    run ce_validate_description "Description with: punctuation, and symbols!"
    assert_success
}

@test "ce_validate_description: rejects too long description" {
    local long_desc=$(printf 'a%.0s' {1..600})
    run ce_validate_description "${long_desc}" 500
    assert_failure
    assert_output_contains "exceeds maximum length"
}

@test "ce_validate_description: rejects control characters" {
    local desc_with_ctrl="text with $(printf '\x00') null byte"
    run ce_validate_description "${desc_with_ctrl}"
    assert_failure
    assert_output_contains "control characters"
}

# ============================================================================
# Session ID Validation
# ============================================================================

@test "ce_validate_session_id: accepts valid session ID" {
    run ce_validate_session_id "t1-20241009-123456"
    assert_success
}

@test "ce_validate_session_id: accepts alphanumeric with hyphens" {
    run ce_validate_session_id "session-123-abc"
    assert_success
}

@test "ce_validate_session_id: rejects special characters" {
    run ce_validate_session_id "session@#$"
    assert_failure
    assert_output_contains "invalid characters"
}

@test "ce_validate_session_id: rejects path traversal" {
    run ce_validate_session_id "../../etc/passwd"
    assert_failure
    assert_output_contains "path traversal patterns"
}

@test "ce_validate_session_id: rejects slashes" {
    run ce_validate_session_id "session/id"
    assert_failure
    assert_output_contains "path traversal patterns"
}

@test "ce_validate_session_id: rejects too short ID" {
    run ce_validate_session_id "ab"
    assert_failure
    assert_output_contains "3-100 characters"
}

# ============================================================================
# Commit Message Validation
# ============================================================================

@test "ce_validate_commit_message: accepts valid commit message" {
    run ce_validate_commit_message "feat: add user authentication"
    assert_success
}

@test "ce_validate_commit_message: rejects too short message" {
    run ce_validate_commit_message "fix bug" 10
    assert_failure
    assert_output_contains "too short"
}

@test "ce_validate_commit_message: rejects too long message" {
    local long_msg=$(printf 'a%.0s' {1..600})
    run ce_validate_commit_message "${long_msg}" 10 500
    assert_failure
    assert_output_contains "too long"
}

@test "ce_validate_commit_message: rejects whitespace-only message" {
    run ce_validate_commit_message "   "
    assert_failure
    assert_output_contains "empty or only whitespace"
}

# ============================================================================
# Combined Validation Functions
# ============================================================================

@test "ce_validate_feature_input: validates all components" {
    run ce_validate_feature_input "auth-system" "User authentication" "P3"
    assert_success
}

@test "ce_validate_feature_input: fails on invalid feature name" {
    run ce_validate_feature_input "Invalid-Name" "Description" "P3"
    assert_failure
}

@test "ce_validate_feature_input: fails on invalid phase" {
    run ce_validate_feature_input "valid-name" "Description" "P9"
    assert_failure
}

@test "ce_validate_feature_input: works with empty description" {
    run ce_validate_feature_input "valid-name" "" "P3"
    assert_success
}

@test "ce_validate_session_path: validates terminal ID and constructs path" {
    run ce_validate_session_path "t1" "${CE_TEST_WORKSPACE}"
    assert_success
    assert_output_contains "${CE_TEST_WORKSPACE}/t1"
}

@test "ce_validate_session_path: rejects invalid terminal ID" {
    run ce_validate_session_path "invalid" "${CE_TEST_WORKSPACE}"
    assert_failure
}

# ============================================================================
# Security Attack Scenarios
# ============================================================================

@test "security: rejects command injection in feature name" {
    run ce_validate_feature_name "test\$(whoami)"
    assert_failure
}

@test "security: rejects SQL injection patterns" {
    run ce_validate_feature_name "test'; DROP TABLE--"
    assert_failure
}

@test "security: rejects shell expansion in path" {
    run ce_validate_path "\${HOME}/.ssh/id_rsa" "${CE_TEST_WORKSPACE}"
    assert_failure
}

@test "security: rejects symlink path traversal" {
    # Create symlink pointing outside workspace
    ln -s /etc "${CE_TEST_WORKSPACE}/symlink"
    run ce_validate_path "${CE_TEST_WORKSPACE}/symlink/passwd" "${CE_TEST_WORKSPACE}"
    # This should fail as the canonical path resolves to /etc/passwd
    assert_failure
}

@test "security: sanitizes filename with null byte" {
    run ce_sanitize_filename "file$(printf '\x00')name.txt"
    assert_success
    [[ ! "${output}" =~ $'\x00' ]]
}
