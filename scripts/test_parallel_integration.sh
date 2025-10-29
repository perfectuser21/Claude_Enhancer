#!/bin/bash
# =============================================================================
# Parallel Execution Integration Test Suite
# =============================================================================
# Purpose: Integration tests for Phase2-6 parallel execution with Skills
# Coverage: Configuration, Skills, Executor integration, Benchmark system
# =============================================================================

set -euo pipefail

# ==================== Configuration ====================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ==================== Test Framework ====================

test_pass() {
    local test_name="$1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
    echo "  ✅ PASS: ${test_name}"
}

test_fail() {
    local test_name="$1"
    local reason="${2:-unknown}"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
    echo "  ❌ FAIL: ${test_name}"
    echo "     Reason: ${reason}"
}

test_section() {
    local section_name="$1"
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║  ${section_name}"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
}

# ==================== Test Suite 1: Configuration ====================

test_configuration() {
    test_section "Test Suite 1: Configuration Validation"

    # Test 1: STAGES.yml valid
    if python3 -c "import yaml; yaml.safe_load(open('${PROJECT_ROOT}/.workflow/STAGES.yml'))" 2>/dev/null; then
        test_pass "STAGES.yml is valid YAML"
    else
        test_fail "STAGES.yml YAML parsing" "Invalid YAML syntax"
    fi

    # Test 2: workflow_phase_parallel exists
    if python3 -c "import yaml; d=yaml.safe_load(open('${PROJECT_ROOT}/.workflow/STAGES.yml')); exit(0 if 'workflow_phase_parallel' in d else 1)" 2>/dev/null; then
        test_pass "workflow_phase_parallel section exists"
    else
        test_fail "workflow_phase_parallel section" "Section not found"
    fi

    # Test 3: Phase3 has 5 groups
    local phase3_groups=$(python3 -c "import yaml; d=yaml.safe_load(open('${PROJECT_ROOT}/.workflow/STAGES.yml')); print(len(d.get('workflow_phase_parallel',{}).get('Phase3',{}).get('parallel_groups',[])))" 2>/dev/null || echo 0)
    if [[ "${phase3_groups}" == "5" ]]; then
        test_pass "Phase3 upgraded to 5 parallel groups"
    else
        test_fail "Phase3 group count" "Expected 5, got ${phase3_groups}"
    fi
}

# ==================== Test Suite 2: Skills Framework ====================

test_skills_framework() {
    test_section "Test Suite 2: Skills Framework"

    # Test: New Skills exist
    if [[ -x "${PROJECT_ROOT}/scripts/parallel/track_performance.sh" ]] && \
       [[ -x "${PROJECT_ROOT}/scripts/parallel/validate_conflicts.sh" ]] && \
       [[ -x "${PROJECT_ROOT}/scripts/parallel/rebalance_load.sh" ]]; then
        test_pass "3 new Skills scripts exist and executable"
    else
        test_fail "New Skills scripts" "Missing or not executable"
    fi

    # Test: settings.json has 7 Skills
    local skill_count=$(jq '.skills | length' "${PROJECT_ROOT}/.claude/settings.json" 2>/dev/null || echo 0)
    if [[ "${skill_count}" == "7" ]]; then
        test_pass "settings.json configured with 7 Skills"
    else
        test_fail "settings.json Skills count" "Expected 7, got ${skill_count}"
    fi
}

# ==================== Test Suite 3: Executor Integration ====================

test_executor_integration() {
    test_section "Test Suite 3: Executor Integration"

    if grep -q "SKILLS MIDDLEWARE LAYER" "${PROJECT_ROOT}/.workflow/executor.sh"; then
        test_pass "executor.sh contains Skills Middleware Layer"
    else
        test_fail "Skills Middleware Layer" "Marker not found"
    fi

    if grep -q "track_performance.sh" "${PROJECT_ROOT}/.workflow/executor.sh"; then
        test_pass "Performance tracker integrated"
    else
        test_fail "Performance tracker" "Not integrated"
    fi
}

# ==================== Test Suite 4: Benchmark System ====================

test_benchmark_system() {
    test_section "Test Suite 4: Benchmark System"

    # Test: Scripts exist
    if [[ -x "${PROJECT_ROOT}/scripts/benchmark/collect_baseline.sh" ]] && \
       [[ -x "${PROJECT_ROOT}/scripts/benchmark/run_parallel_tests.sh" ]] && \
       [[ -x "${PROJECT_ROOT}/scripts/benchmark/calculate_speedup.sh" ]] && \
       [[ -x "${PROJECT_ROOT}/scripts/benchmark/validate_performance.sh" ]]; then
        test_pass "4 benchmark scripts exist and executable"
    else
        test_fail "Benchmark scripts" "Missing or not executable"
    fi

    # Test: Baseline collection
    if bash "${PROJECT_ROOT}/scripts/benchmark/collect_baseline.sh" >/dev/null 2>&1; then
        test_pass "Baseline collection works"
    else
        test_fail "Baseline collection" "Script failed"
    fi

    # Test: Parallel tests (1 iteration)
    if bash "${PROJECT_ROOT}/scripts/benchmark/run_parallel_tests.sh" 1 >/dev/null 2>&1; then
        test_pass "Parallel tests work"
    else
        test_fail "Parallel tests" "Script failed"
    fi

    # Test: Speedup calculation
    if bash "${PROJECT_ROOT}/scripts/benchmark/calculate_speedup.sh" >/dev/null 2>&1; then
        test_pass "Speedup calculation works"
    else
        test_fail "Speedup calculation" "Script failed"
    fi

    # Test: Overall speedup ≥1.4x
    local overall=$(jq -r '.overall_speedup' "${PROJECT_ROOT}/.workflow/metrics/speedup_report.json" 2>/dev/null || echo 0)
    if (( $(echo "${overall} >= 1.4" | bc -l 2>/dev/null || echo 0) )); then
        test_pass "Overall speedup ≥1.4x (${overall}x)"
    else
        test_fail "Overall speedup" "Got ${overall}x, expected ≥1.4x"
    fi
}

# ==================== Main ====================

main() {
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║  Parallel Execution Integration Test Suite           ║"
    echo "║  v8.3.0 - Phase2-6 Parallel + Skills                  ║"
    echo "╚═══════════════════════════════════════════════════════╝"

    test_configuration
    test_skills_framework
    test_executor_integration
    test_benchmark_system

    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║  Test Results Summary                                 ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo "  Total:   ${TOTAL_TESTS}"
    echo "  Passed:  ${PASSED_TESTS} ✅"
    echo "  Failed:  ${FAILED_TESTS} ❌"

    if [[ ${FAILED_TESTS} -eq 0 ]]; then
        echo "  Status: ✅ ALL TESTS PASSED"
        exit 0
    else
        echo "  Status: ❌ SOME TESTS FAILED"
        exit 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
