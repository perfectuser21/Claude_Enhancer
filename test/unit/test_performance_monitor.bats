#!/usr/bin/env bats
# test_performance_monitor.bats - Unit tests for performance_monitor.sh
# Tests performance tracking, budgets, and reporting

load '../helpers/test_helper'

setup() {
    setup_test_env
    source_lib "common"  # Required dependency
    source_lib "performance_monitor"
    ce_perf_init
}

teardown() {
    teardown_test_env
}

# ============================================================================
# Performance Initialization
# ============================================================================

@test "ce_perf_init: creates performance log file" {
    ce_perf_init
    assert_file_exists "${CE_PERF_LOG_FILE}"
}

@test "ce_perf_init: skips when disabled" {
    export CE_PERF_ENABLED=false
    run ce_perf_init
    assert_success
}

# ============================================================================
# Performance Timing
# ============================================================================

@test "ce_perf_start: records start time" {
    run ce_perf_start "test_operation"
    assert_success
}

@test "ce_perf_stop: calculates duration" {
    ce_perf_start "test_operation"
    sleep 0.1
    run ce_perf_stop "test_operation"
    assert_success
    [[ "${output}" -gt 0 ]]
}

@test "ce_perf_stop: fails when no start time" {
    run ce_perf_stop "nonexistent_operation"
    assert_failure
}

@test "ce_perf_measure: times command execution" {
    run ce_perf_measure "test_op" echo "hello"
    assert_success
}

# ============================================================================
# Performance Budgets
# ============================================================================

@test "ce_perf_set_budget: sets custom budget" {
    run ce_perf_set_budget "my_operation" 500
    assert_success
}

@test "ce_perf_stop: warns when budget exceeded" {
    export CE_PERF_VERBOSE=true
    ce_perf_set_budget "slow_op" 10

    ce_perf_start "slow_op"
    sleep 0.05
    run ce_perf_stop "slow_op"

    assert_success
    # Budget exceeded warning should appear in log
}

# ============================================================================
# Performance Statistics
# ============================================================================

@test "ce_perf_stats: returns operation statistics" {
    ce_perf_start "test_op"
    ce_perf_stop "test_op"

    run ce_perf_stats "test_op"
    assert_success
    assert_output_contains "operation"
    assert_output_contains "count"
    assert_output_contains "average_ms"
}

@test "ce_perf_stats: returns all operations when no arg" {
    ce_perf_start "op1"
    ce_perf_stop "op1"

    run ce_perf_stats
    assert_success
    assert_output_contains "operations"
}

# ============================================================================
# Performance Reporting
# ============================================================================

@test "ce_perf_report: generates text report" {
    ce_perf_start "test_op"
    ce_perf_stop "test_op"

    run ce_perf_report "text"
    assert_success
    assert_output_contains "Performance Report"
}

@test "ce_perf_report: generates JSON report" {
    ce_perf_start "test_op"
    ce_perf_stop "test_op"

    run ce_perf_report "json"
    assert_success
    assert_output_contains "{"
}

# ============================================================================
# Performance Analysis
# ============================================================================

@test "ce_perf_analyze: analyzes specific operation" {
    # Log some operations
    for i in {1..5}; do
        ce_perf_start "test_op"
        sleep 0.01
        ce_perf_stop "test_op"
    done

    run ce_perf_analyze "test_op"
    assert_success
    assert_output_contains "Samples:"
    assert_output_contains "Min:"
    assert_output_contains "Max:"
}

# ============================================================================
# Utility Functions
# ============================================================================

@test "ce_perf_clear: clears performance data" {
    ce_perf_start "test_op"
    ce_perf_stop "test_op"

    run ce_perf_clear
    assert_success
    assert_output_contains "cleared"
}

@test "ce_perf_archive: archives performance log" {
    ce_perf_init

    run ce_perf_archive
    assert_success
    assert_output_contains "archived"
}

# Add more tests for performance_monitor functions...
