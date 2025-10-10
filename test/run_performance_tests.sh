#!/usr/bin/env bash
# run_performance_tests.sh - Execute complete performance test suite
# Runs all performance tests and generates comprehensive report
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="${PROJECT_ROOT}/test/performance"
RESULTS_DIR="${TEST_DIR}/results"

# Create results directory
mkdir -p "${RESULTS_DIR}/history"

# Test suite options
RUN_BENCHMARKS=true
RUN_WORKFLOWS=true
RUN_LOAD_TESTS=true
RUN_CACHE_TESTS=true
RUN_STRESS_TESTS=false  # Disabled by default
RUN_MEMORY_PROFILING=true
RUN_REGRESSION_CHECK=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)
            RUN_STRESS_TESTS=true
            shift
            ;;
        --quick)
            RUN_LOAD_TESTS=false
            RUN_STRESS_TESTS=false
            RUN_MEMORY_PROFILING=false
            shift
            ;;
        --stress)
            RUN_STRESS_TESTS=true
            shift
            ;;
        --help)
            cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --all       Run all tests including stress tests
  --quick     Run only quick tests (benchmarks and workflows)
  --stress    Run stress tests
  --help      Show this help message

Default behavior: Run all tests except stress tests
EOF
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        CE CLI Performance Test Suite                        ║
║        Complete Performance Validation                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${BOLD}Test Configuration:${NC}"
echo "  Project: Claude Enhancer 5.0"
echo "  Test Directory: ${TEST_DIR}"
echo "  Results Directory: ${RESULTS_DIR}"
echo ""

# Test suite status
declare -A test_results

# Track overall time
SUITE_START=$(date +%s)

# ============================================================================
# Test execution wrapper
# ============================================================================

run_test() {
    local test_name="$1"
    local test_script="$2"
    local test_enabled="$3"

    if [[ "${test_enabled}" != "true" ]]; then
        echo -e "${YELLOW}⊘ Skipping: ${test_name}${NC}"
        echo ""
        return 0
    fi

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}Running: ${test_name}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local start_time
    start_time=$(date +%s)

    local test_output="${RESULTS_DIR}/${test_script%.sh}_output.log"

    # Run test
    if bash "${TEST_DIR}/${test_script}" > "${test_output}" 2>&1; then
        local end_time
        end_time=$(date +%s)
        local duration=$((end_time - start_time))

        echo -e "${GREEN}✓ ${test_name} completed in ${duration}s${NC}"
        test_results["${test_name}"]="PASSED"

        # Show summary from output
        tail -20 "${test_output}"
    else
        local end_time
        end_time=$(date +%s)
        local duration=$((end_time - start_time))

        echo -e "${RED}✗ ${test_name} failed after ${duration}s${NC}"
        test_results["${test_name}"]="FAILED"

        echo ""
        echo "Last 50 lines of output:"
        tail -50 "${test_output}"
    fi

    echo ""
}

# ============================================================================
# Run test suite
# ============================================================================

cd "${PROJECT_ROOT}"

echo -e "${CYAN}Starting performance test suite...${NC}"
echo ""

# 1. Command Benchmarks
run_test "Command Benchmarks" "benchmark_commands.sh" "${RUN_BENCHMARKS}"

# 2. Workflow Benchmarks
run_test "Workflow Benchmarks" "benchmark_workflows.sh" "${RUN_WORKFLOWS}"

# 3. Load Tests
run_test "Load Tests" "load_test.sh" "${RUN_LOAD_TESTS}"

# 4. Cache Performance
run_test "Cache Performance" "cache_performance.sh" "${RUN_CACHE_TESTS}"

# 5. Stress Tests (optional)
if [[ "${RUN_STRESS_TESTS}" == "true" ]]; then
    echo -e "${YELLOW}⚠️  WARNING: Stress tests will push your system to its limits${NC}"
    run_test "Stress Tests" "stress_test.sh" "${RUN_STRESS_TESTS}"
fi

# 6. Memory Profiling
run_test "Memory Profiling" "memory_profiling.sh" "${RUN_MEMORY_PROFILING}"

# 7. Regression Check
run_test "Regression Check" "regression_check.sh" "${RUN_REGRESSION_CHECK}"

# ============================================================================
# Generate comprehensive report
# ============================================================================

SUITE_END=$(date +%s)
SUITE_DURATION=$((SUITE_END - SUITE_START))

echo -e "${CYAN}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        Performance Test Suite Summary                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${BOLD}Test Results:${NC}"
echo ""

local total_tests=0
local passed_tests=0
local failed_tests=0

for test_name in "${!test_results[@]}"; do
    ((total_tests++))

    local result="${test_results[$test_name]}"

    if [[ "${result}" == "PASSED" ]]; then
        echo -e "  ${GREEN}✓ ${test_name}${NC}"
        ((passed_tests++))
    else
        echo -e "  ${RED}✗ ${test_name}${NC}"
        ((failed_tests++))
    fi
done

echo ""
echo -e "${BOLD}Summary:${NC}"
echo "  Total tests: ${total_tests}"
echo -e "  ${GREEN}Passed: ${passed_tests}${NC}"
echo -e "  ${RED}Failed: ${failed_tests}${NC}"
echo "  Duration: ${SUITE_DURATION}s"

echo ""

# ============================================================================
# Key metrics summary
# ============================================================================

echo -e "${BOLD}Key Metrics:${NC}"
echo ""

# Extract key metrics from result files
if [[ -f "${RESULTS_DIR}/workflow_benchmark_summary.json" ]]; then
    local cycle_time
    cycle_time=$(jq -r '.complete_cycle_ms' "${RESULTS_DIR}/workflow_benchmark_summary.json" 2>/dev/null || echo "N/A")

    local improvement
    improvement=$(jq -r '.improvement_percent' "${RESULTS_DIR}/workflow_benchmark_summary.json" 2>/dev/null || echo "N/A")

    echo "  Complete Cycle Time: ${cycle_time}ms"
    echo "  Improvement vs Baseline: ${improvement}%"
fi

if [[ -f "${RESULTS_DIR}/cache_performance_summary.json" ]]; then
    local speedup
    speedup=$(jq -r '.speedup_percent' "${RESULTS_DIR}/cache_performance_summary.json" 2>/dev/null || echo "N/A")

    echo "  Cache Speedup: ${speedup}%"
fi

if [[ -f "${RESULTS_DIR}/load_test_summary.json" ]]; then
    echo ""
    echo "Load Test Results:"

    local concurrent_5_time
    concurrent_5_time=$(jq -r '.concurrent_terminals."5".time_ms' "${RESULTS_DIR}/load_test_summary.json" 2>/dev/null || echo "N/A")

    local concurrent_20_time
    concurrent_20_time=$(jq -r '.concurrent_terminals."20".time_ms' "${RESULTS_DIR}/load_test_summary.json" 2>/dev/null || echo "N/A")

    echo "  5 concurrent terminals: ${concurrent_5_time}ms"
    echo "  20 concurrent terminals: ${concurrent_20_time}ms"
fi

echo ""

# ============================================================================
# Generate JSON report
# ============================================================================

cat > "${RESULTS_DIR}/test_suite_summary.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "duration_seconds": ${SUITE_DURATION},
  "tests": {
    "total": ${total_tests},
    "passed": ${passed_tests},
    "failed": ${failed_tests}
  },
  "test_results": {
$(for test_name in "${!test_results[@]}"; do
    echo "    \"${test_name}\": \"${test_results[$test_name]}\","
done | sed '$ s/,$//')
  },
  "configuration": {
    "benchmarks": ${RUN_BENCHMARKS},
    "workflows": ${RUN_WORKFLOWS},
    "load_tests": ${RUN_LOAD_TESTS},
    "cache_tests": ${RUN_CACHE_TESTS},
    "stress_tests": ${RUN_STRESS_TESTS},
    "memory_profiling": ${RUN_MEMORY_PROFILING},
    "regression_check": ${RUN_REGRESSION_CHECK}
  }
}
EOF

echo "JSON report saved to: ${RESULTS_DIR}/test_suite_summary.json"
echo ""

# ============================================================================
# Final status
# ============================================================================

if [[ ${failed_tests} -gt 0 ]]; then
    echo -e "${RED}❌ Performance test suite FAILED${NC}"
    echo ""
    echo "Review failed test logs in: ${RESULTS_DIR}/"
    exit 1
else
    echo -e "${GREEN}✅ Performance test suite PASSED${NC}"
    echo ""
    echo "All results saved to: ${RESULTS_DIR}/"

    # Check for performance improvements
    if [[ -f "${RESULTS_DIR}/workflow_benchmark_summary.json" ]]; then
        local improvement
        improvement=$(jq -r '.improvement_percent' "${RESULTS_DIR}/workflow_benchmark_summary.json" 2>/dev/null || echo "0")

        if [[ ${improvement} -ge 75 ]]; then
            echo ""
            echo -e "${GREEN}🎉 Meets 75% performance improvement target!${NC}"
        fi
    fi
fi

echo ""
echo "To generate visual reports, run:"
echo "  bash test/performance/generate_perf_report.sh"
