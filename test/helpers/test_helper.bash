#!/usr/bin/env bash
# test_helper.bash - Common test utilities for BATS tests
# Provides setup, teardown, assertions, and mock helpers

# Test environment configuration
export CE_TEST_MODE=true
export CE_LOG_LEVEL=3  # ERROR level only
export CE_PERF_ENABLED=false
export CE_CACHE_ENABLED=false
export CE_NO_CACHE=true

# Test directories
export CE_TEST_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export CE_TEST_TMP_DIR="${CE_TEST_ROOT}/test/.tmp"
export CE_TEST_FIXTURES_DIR="${CE_TEST_ROOT}/test/fixtures"

# Setup test environment
setup_test_env() {
    # Create temporary test directory
    mkdir -p "${CE_TEST_TMP_DIR}"

    # Create isolated test workspace
    export CE_TEST_WORKSPACE="${CE_TEST_TMP_DIR}/workspace_$$"
    mkdir -p "${CE_TEST_WORKSPACE}"
    cd "${CE_TEST_WORKSPACE}"

    # Initialize minimal git repo
    git init --quiet
    git config user.name "Test User"
    git config user.email "test@example.com"

    # Create test directories
    mkdir -p .workflow/cli/{lib,state/sessions,state/cache}
    mkdir -p .phase .gates

    # Set phase
    echo "P0" > .phase/current
}

# Cleanup test environment
teardown_test_env() {
    # Return to original directory
    cd "${CE_TEST_ROOT}"

    # Remove test workspace
    if [[ -n "${CE_TEST_WORKSPACE}" ]] && [[ -d "${CE_TEST_WORKSPACE}" ]]; then
        rm -rf "${CE_TEST_WORKSPACE}"
    fi
}

# Assert command succeeds
assert_success() {
    if [[ $status -ne 0 ]]; then
        echo "Expected success but got status: $status"
        echo "Output: ${output}"
        return 1
    fi
}

# Assert command fails
assert_failure() {
    if [[ $status -eq 0 ]]; then
        echo "Expected failure but command succeeded"
        echo "Output: ${output}"
        return 1
    fi
}

# Assert output contains string
assert_output_contains() {
    local expected="$1"
    if [[ ! "${output}" =~ ${expected} ]]; then
        echo "Expected output to contain: '${expected}'"
        echo "Actual output: '${output}'"
        return 1
    fi
}

# Assert output equals string
assert_output_equals() {
    local expected="$1"
    if [[ "${output}" != "${expected}" ]]; then
        echo "Expected: '${expected}'"
        echo "Got: '${output}'"
        return 1
    fi
}

# Assert file exists
assert_file_exists() {
    local file="$1"
    if [[ ! -f "${file}" ]]; then
        echo "Expected file to exist: ${file}"
        return 1
    fi
}

# Assert directory exists
assert_dir_exists() {
    local dir="$1"
    if [[ ! -d "${dir}" ]]; then
        echo "Expected directory to exist: ${dir}"
        return 1
    fi
}

# Assert variable is set
assert_var_set() {
    local var_name="$1"
    if [[ -z "${!var_name}" ]]; then
        echo "Expected variable to be set: ${var_name}"
        return 1
    fi
}

# Assert variable equals value
assert_var_equals() {
    local var_name="$1"
    local expected="$2"
    if [[ "${!var_name}" != "${expected}" ]]; then
        echo "Expected ${var_name}='${expected}'"
        echo "Got ${var_name}='${!var_name}'"
        return 1
    fi
}

# Create test file with content
create_test_file() {
    local file="$1"
    local content="$2"
    mkdir -p "$(dirname "${file}")"
    echo "${content}" > "${file}"
}

# Create test git commit
create_test_commit() {
    local message="${1:-test commit}"
    git add -A
    git commit -m "${message}" --no-verify
}

# Mock command
mock_command() {
    local cmd="$1"
    local return_code="${2:-0}"
    local output="${3:-}"

    # Create mock function
    eval "${cmd}() {
        echo '${output}'
        return ${return_code}
    }"
    export -f "${cmd}"
}

# Unmock command
unmock_command() {
    local cmd="$1"
    unset -f "${cmd}"
}

# Source library under test
source_lib() {
    local lib_name="$1"
    local lib_path="${CE_TEST_ROOT}/.workflow/cli/lib/${lib_name}.sh"

    if [[ ! -f "${lib_path}" ]]; then
        echo "Library not found: ${lib_path}"
        return 1
    fi

    source "${lib_path}"
}

# Capture function output and status
run_function() {
    local func="$1"
    shift
    output="$("${func}" "$@" 2>&1)"
    status=$?
}

# Skip test with reason
skip_test() {
    local reason="$1"
    skip "${reason}"
}

# Export helper functions
export -f setup_test_env
export -f teardown_test_env
export -f assert_success
export -f assert_failure
export -f assert_output_contains
export -f assert_output_equals
export -f assert_file_exists
export -f assert_dir_exists
export -f assert_var_set
export -f assert_var_equals
export -f create_test_file
export -f create_test_commit
export -f mock_command
export -f unmock_command
export -f source_lib
export -f run_function
export -f skip_test
