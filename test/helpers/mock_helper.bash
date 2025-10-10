#!/usr/bin/env bash
# mock_helper.bash - General mocking framework for BATS tests
# Provides function mocking, stubbing, and verification

# Track mock calls
declare -A MOCK_CALL_COUNT
declare -A MOCK_CALL_ARGS

# Reset all mocks
mock_reset_all() {
    MOCK_CALL_COUNT=()
    MOCK_CALL_ARGS=()
}

# Create simple mock that returns success
mock_simple() {
    local func_name="$1"
    local return_value="${2:-0}"

    eval "${func_name}() {
        MOCK_CALL_COUNT[${func_name}]=\$((MOCK_CALL_COUNT[${func_name}] + 1))
        MOCK_CALL_ARGS[${func_name}]=\$*
        return ${return_value}
    }"
    export -f "${func_name}"
}

# Create mock with output
mock_with_output() {
    local func_name="$1"
    local output="$2"
    local return_value="${3:-0}"

    eval "${func_name}() {
        MOCK_CALL_COUNT[${func_name}]=\$((MOCK_CALL_COUNT[${func_name}] + 1))
        MOCK_CALL_ARGS[${func_name}]=\$*
        echo '${output}'
        return ${return_value}
    }"
    export -f "${func_name}"
}

# Create mock with custom behavior
mock_custom() {
    local func_name="$1"
    local behavior="$2"

    eval "${func_name}() {
        MOCK_CALL_COUNT[${func_name}]=\$((MOCK_CALL_COUNT[${func_name}] + 1))
        MOCK_CALL_ARGS[${func_name}]=\$*
        ${behavior}
    }"
    export -f "${func_name}"
}

# Assert mock was called
assert_mock_called() {
    local func_name="$1"
    local expected_times="${2:-1}"

    local actual_calls="${MOCK_CALL_COUNT[${func_name}]:-0}"

    if [[ ${actual_calls} -ne ${expected_times} ]]; then
        echo "Expected ${func_name} to be called ${expected_times} time(s)"
        echo "Was called ${actual_calls} time(s)"
        return 1
    fi
}

# Assert mock was never called
assert_mock_not_called() {
    local func_name="$1"

    local actual_calls="${MOCK_CALL_COUNT[${func_name}]:-0}"

    if [[ ${actual_calls} -ne 0 ]]; then
        echo "Expected ${func_name} to not be called"
        echo "Was called ${actual_calls} time(s)"
        return 1
    fi
}

# Assert mock called with args
assert_mock_called_with() {
    local func_name="$1"
    local expected_args="$2"

    local actual_args="${MOCK_CALL_ARGS[${func_name}]:-}"

    if [[ "${actual_args}" != "${expected_args}" ]]; then
        echo "Expected ${func_name} to be called with: '${expected_args}'"
        echo "Was called with: '${actual_args}'"
        return 1
    fi
}

# Get mock call count
get_mock_call_count() {
    local func_name="$1"
    echo "${MOCK_CALL_COUNT[${func_name}]:-0}"
}

# Get mock call args
get_mock_call_args() {
    local func_name="$1"
    echo "${MOCK_CALL_ARGS[${func_name}]:-}"
}

# Stub function (alias for mock)
stub() {
    mock_simple "$@"
}

# Spy on function (track calls but execute original)
spy_on() {
    local func_name="$1"

    # Save original function
    local original_func="${func_name}_original"
    eval "${original_func}=$(declare -f "${func_name}")"

    # Create spy wrapper
    eval "${func_name}() {
        MOCK_CALL_COUNT[${func_name}]=\$((MOCK_CALL_COUNT[${func_name}] + 1))
        MOCK_CALL_ARGS[${func_name}]=\$*
        ${original_func} \"\$@\"
    }"
    export -f "${func_name}"
}

# Restore spied function
restore_spy() {
    local func_name="$1"
    local original_func="${func_name}_original"

    if declare -f "${original_func}" &>/dev/null; then
        eval "$(declare -f "${original_func}" | sed "s/${original_func}/${func_name}/")"
        unset -f "${original_func}"
    fi
}

# Export mock helper functions
export -f mock_reset_all
export -f mock_simple
export -f mock_with_output
export -f mock_custom
export -f assert_mock_called
export -f assert_mock_not_called
export -f assert_mock_called_with
export -f get_mock_call_count
export -f get_mock_call_args
export -f stub
export -f spy_on
export -f restore_spy
