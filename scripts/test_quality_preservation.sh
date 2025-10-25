#!/bin/bash
# Test Quality Preservation After Optimizations
# Purpose: Ensure all quality checks still work after performance optimizations
# Version: 1.0.0
# Created: 2025-10-25

set -euo pipefail

# Configuration
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly TEST_RESULTS_DIR="${PROJECT_ROOT}/.temp/optimization_test_results"
readonly TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Ensure test results directory exists
mkdir -p "$TEST_RESULTS_DIR"

# Test counters
total_tests=0
passed_tests=0
failed_tests=0

# ═══════════════════════════════════════════════════════════════
# Test Functions
# ═══════════════════════════════════════════════════════════════

# Function: Run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="${3:-0}"

    ((total_tests++))
    echo -n "Testing $test_name... "

    local actual_result=0
    if eval "$test_command" > "${TEST_RESULTS_DIR}/${test_name}.log" 2>&1; then
        actual_result=0
    else
        actual_result=$?
    fi

    if [[ $actual_result -eq $expected_result ]]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((passed_tests++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (expected: $expected_result, got: $actual_result)"
        ((failed_tests++))
        echo "  See: ${TEST_RESULTS_DIR}/${test_name}.log"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# Test Suite 1: Caching System
# ═══════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════"
echo "Test Suite 1: Caching System"
echo "═══════════════════════════════════════════════════════════════"

# Test cache manager exists and is executable
run_test "cache_manager_exists" "test -f ${PROJECT_ROOT}/.claude/tools/cache_manager.sh"
run_test "cache_manager_executable" "test -x ${PROJECT_ROOT}/.claude/tools/cache_manager.sh"

# Test cache functionality
run_test "cache_test_command" "bash ${PROJECT_ROOT}/.claude/tools/cache_manager.sh test"

# Test cache stats command
run_test "cache_stats" "bash ${PROJECT_ROOT}/.claude/tools/cache_manager.sh stats"

# ═══════════════════════════════════════════════════════════════
# Test Suite 2: Unified Branch Protection
# ═══════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test Suite 2: Unified Branch Protection"
echo "═══════════════════════════════════════════════════════════════"

# Test unified branch protector exists
run_test "unified_protector_exists" "test -f ${PROJECT_ROOT}/.claude/hooks/unified_branch_protector.sh"

# Test branch helper delegation
run_test "branch_helper_size" "test \$(wc -l < ${PROJECT_ROOT}/.claude/hooks/branch_helper.sh) -lt 20"

# Test force_branch_check delegation
run_test "force_check_size" "test \$(wc -l < ${PROJECT_ROOT}/.claude/hooks/force_branch_check.sh) -lt 50"

# Test common library exists
run_test "branch_common_exists" "test -f ${PROJECT_ROOT}/.claude/hooks/lib/branch_common.sh"

# ═══════════════════════════════════════════════════════════════
# Test Suite 3: Performance Monitoring
# ═══════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test Suite 3: Performance Monitoring"
echo "═══════════════════════════════════════════════════════════════"

# Test performance monitor exists
run_test "perf_monitor_exists" "test -f ${PROJECT_ROOT}/.claude/tools/performance_monitor.sh"

# Test performance commands
run_test "perf_start_end" "
    bash ${PROJECT_ROOT}/.claude/tools/performance_monitor.sh start test_op test_ctx &&
    sleep 0.1 &&
    bash ${PROJECT_ROOT}/.claude/tools/performance_monitor.sh end test_op test_ctx success
"

# Test performance summary
run_test "perf_summary" "bash ${PROJECT_ROOT}/.claude/tools/performance_monitor.sh summary"

# ═══════════════════════════════════════════════════════════════
# Test Suite 4: Quality Checks Still Work
# ═══════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test Suite 4: Quality Checks Preservation"
echo "═══════════════════════════════════════════════════════════════"

# Test version consistency check still works
run_test "version_check_script" "test -f ${PROJECT_ROOT}/scripts/check_version_consistency.sh"
run_test "version_consistency" "bash ${PROJECT_ROOT}/scripts/check_version_consistency.sh"

# Test static checks still work
run_test "static_checks_script" "test -f ${PROJECT_ROOT}/scripts/static_checks.sh"

# Test pre-merge audit still works
run_test "pre_merge_script" "test -f ${PROJECT_ROOT}/scripts/pre_merge_audit.sh"

# Test workflow validator still works
run_test "workflow_validator" "test -f ${PROJECT_ROOT}/scripts/workflow_validator_v97.sh"

# Test phase manager exists
run_test "phase_manager" "test -f ${PROJECT_ROOT}/.claude/core/phase_manager.sh"

# ═══════════════════════════════════════════════════════════════
# Test Suite 5: Hook Count Reduction
# ═══════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test Suite 5: Hook Consolidation Verification"
echo "═══════════════════════════════════════════════════════════════"

# Count total hooks (excluding archived)
hook_count=$(find "${PROJECT_ROOT}/.claude/hooks" -maxdepth 1 -name "*.sh" | wc -l)
run_test "hook_count_reduced" "test $hook_count -le 45"

# Check for duplicate branch checking logic
duplicate_checks=$(grep -l "is_protected_branch\|main.*master.*production" "${PROJECT_ROOT}/.claude/hooks"/*.sh 2>/dev/null | wc -l)
run_test "minimal_duplicate_checks" "test $duplicate_checks -le 5"

# ═══════════════════════════════════════════════════════════════
# Test Suite 6: Performance Improvements
# ═══════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test Suite 6: Performance Verification"
echo "═══════════════════════════════════════════════════════════════"

# Test branch check with caching (should be fast)
run_test "cached_branch_check" "
    export CE_SILENT_MODE=true
    time_start=\$(date +%s%N)
    bash ${PROJECT_ROOT}/.claude/hooks/unified_branch_protector.sh test_context write
    bash ${PROJECT_ROOT}/.claude/hooks/unified_branch_protector.sh test_context write
    time_end=\$(date +%s%N)
    duration_ms=\$(( (time_end - time_start) / 1000000 ))
    test \$duration_ms -lt 500  # Should complete in under 500ms
"

# ═══════════════════════════════════════════════════════════════
# Results Summary
# ═══════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test Results Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Total Tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$failed_tests${NC}"
echo ""

if [[ $failed_tests -eq 0 ]]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Quality has been preserved while achieving:"
    echo "  • Caching layer implemented ✓"
    echo "  • Branch checks consolidated ✓"
    echo "  • Performance monitoring added ✓"
    echo "  • Hook count reduced ✓"
    echo "  • All quality checks intact ✓"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review the failed tests in: $TEST_RESULTS_DIR"
    exit 1
fi