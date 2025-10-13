#!/bin/bash
# Master test runner for all quality validation tests
# Path: test/run_all_quality_tests.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/.temp/analysis"

# ANSI colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Test suite results
declare -A suite_results
declare -A suite_durations
total_suites=0
passed_suites=0
failed_suites=0

# Create results directory
mkdir -p "$RESULTS_DIR"

# Get current time in seconds
get_time() {
    date +%s
}

# Format duration
format_duration() {
    local duration=$1
    if [ $duration -lt 60 ]; then
        echo "${duration}s"
    else
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        echo "${minutes}m ${seconds}s"
    fi
}

# Run a test suite
run_suite() {
    local suite_name="$1"
    local suite_script="$2"
    local suite_category="$3"

    ((total_suites++))

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}▶ Running: ${suite_name}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}Category: ${suite_category}${NC}"
    echo -e "${MAGENTA}Script: ${suite_script}${NC}"
    echo ""

    local start=$(get_time)
    local result=0

    # Run the test suite and capture output
    local log_file="$RESULTS_DIR/${suite_name// /_}.log"

    if bash "$suite_script" 2>&1 | tee "$log_file"; then
        result=0
    else
        result=$?
    fi

    local end=$(get_time)
    local duration=$((end - start))

    suite_durations["$suite_name"]=$duration

    if [ $result -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ ${suite_name}: PASSED${NC} ($(format_duration $duration))"
        suite_results["$suite_name"]="PASSED"
        ((passed_suites++))
    else
        echo ""
        echo -e "${RED}❌ ${suite_name}: FAILED${NC} ($(format_duration $duration))"
        suite_results["$suite_name"]="FAILED"
        ((failed_suites++))
        echo -e "${YELLOW}   See log: $log_file${NC}"
    fi

    return $result
}

# Main execution
main() {
    cd "$PROJECT_ROOT"

    # Print header
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                        ║${NC}"
    echo -e "${BLUE}║       Claude Enhancer Quality Test Suite              ║${NC}"
    echo -e "${BLUE}║       Complete Validation Framework                   ║${NC}"
    echo -e "${BLUE}║                                                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}This comprehensive test suite validates:${NC}"
    echo -e "  • Bug fixes work correctly"
    echo -e "  • Prevention mechanisms cannot be bypassed"
    echo -e "  • No regressions in existing functionality"
    echo -e "  • End-to-end workflows function properly"
    echo -e "  • System performance meets requirements"
    echo ""
    echo -e "${YELLOW}Starting test execution...${NC}"
    echo ""

    local overall_start=$(get_time)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Suite 1: Unit Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_suite \
        "Unit Tests - Bug Fixes" \
        "$SCRIPT_DIR/unit/test_bug_fixes.sh" \
        "Validation"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Suite 2: Integration Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_suite \
        "Integration Tests - Quality Gates" \
        "$SCRIPT_DIR/integration/test_quality_gates.sh" \
        "Prevention"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Suite 3: Regression Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_suite \
        "Regression Tests - No New Bugs" \
        "$SCRIPT_DIR/regression/test_no_new_bugs.sh" \
        "Stability"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Suite 4: E2E Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_suite \
        "E2E Tests - Full Workflow" \
        "$SCRIPT_DIR/e2e/test_full_workflow.sh" \
        "Workflow"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Suite 5: Performance Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_suite \
        "Performance Tests - Hook Performance" \
        "$SCRIPT_DIR/performance/test_hook_performance.sh" \
        "Performance"

    local overall_end=$(get_time)
    local overall_duration=$((overall_end - overall_start))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Generate Summary Report
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    echo ""
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                        ║${NC}"
    echo -e "${BLUE}║                  Test Execution Summary                ║${NC}"
    echo -e "${BLUE}║                                                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Detailed results table
    echo -e "${CYAN}Test Suite Results:${NC}"
    echo ""
    printf "%-40s %-10s %-10s\n" "Suite" "Status" "Duration"
    echo "────────────────────────────────────────────────────────────"

    for suite in "${!suite_results[@]}"; do
        local status="${suite_results[$suite]}"
        local duration="${suite_durations[$suite]}"
        local duration_fmt=$(format_duration $duration)

        if [ "$status" = "PASSED" ]; then
            printf "%-40s ${GREEN}%-10s${NC} %-10s\n" "$suite" "✅ PASSED" "$duration_fmt"
        else
            printf "%-40s ${RED}%-10s${NC} %-10s\n" "$suite" "❌ FAILED" "$duration_fmt"
        fi
    done

    echo ""
    echo -e "${CYAN}Overall Statistics:${NC}"
    echo "────────────────────────────────────────────────────────────"
    echo -e "Total test suites:    $total_suites"
    echo -e "${GREEN}Passed suites:        $passed_suites${NC}"
    echo -e "${RED}Failed suites:        $failed_suites${NC}"
    echo -e "Total execution time: $(format_duration $overall_duration)"
    echo ""

    # Calculate success rate
    if [ $total_suites -gt 0 ]; then
        local success_rate=$(( passed_suites * 100 / total_suites ))
        echo -e "Success rate:         ${success_rate}%"
        echo ""
    fi

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Generate Coverage Report
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    local coverage_report="$RESULTS_DIR/test_coverage_report.md"

    cat > "$coverage_report" << EOF
# Quality Test Suite - Coverage Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')

## Test Execution Summary

| Metric | Value |
|--------|-------|
| Total Test Suites | $total_suites |
| Passed Suites | $passed_suites |
| Failed Suites | $failed_suites |
| Success Rate | $(( passed_suites * 100 / total_suites ))% |
| Total Duration | $(format_duration $overall_duration) |

## Suite Results

| Suite Name | Status | Duration |
|------------|--------|----------|
EOF

    for suite in "${!suite_results[@]}"; do
        local status="${suite_results[$suite]}"
        local duration="${suite_durations[$suite]}"
        local duration_fmt=$(format_duration $duration)
        local status_icon="✅"
        [ "$status" != "PASSED" ] && status_icon="❌"

        echo "| $suite | $status_icon $status | $duration_fmt |" >> "$coverage_report"
    done

    cat >> "$coverage_report" << EOF

## Test Categories Covered

### 1. Bug Fixes Validation
- Shell syntax errors
- Python import issues
- Undefined methods
- Configuration errors
- Race conditions
- Security vulnerabilities

### 2. Prevention Mechanisms
- Git hook activation
- Bypass prevention
- Document creation control
- Coverage thresholds
- Phase validation
- Safe operation wrappers

### 3. Regression Protection
- Core functionality preservation
- Configuration file integrity
- Code quality standards
- Installation and setup
- Security measures

### 4. Workflow Testing
- Branch management
- File operations
- Git integration
- Hook execution
- Commit workflow

### 5. Performance Validation
- Hook execution speed
- Git operations
- Validation overhead
- File operations
- Concurrent operations

## Logs

Individual test logs are available in:
\`\`.temp/analysis/\`\`

EOF

    echo -e "${CYAN}Coverage report saved to:${NC}"
    echo -e "  $coverage_report"
    echo ""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Generate Performance Metrics
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    local metrics_file="$RESULTS_DIR/performance_metrics.json"

    cat > "$metrics_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "overall": {
    "total_suites": $total_suites,
    "passed_suites": $passed_suites,
    "failed_suites": $failed_suites,
    "success_rate": $(( passed_suites * 100 / total_suites )),
    "total_duration_seconds": $overall_duration
  },
  "suites": {
EOF

    local first=true
    for suite in "${!suite_results[@]}"; do
        [ "$first" = false ] && echo "," >> "$metrics_file"
        first=false

        local status="${suite_results[$suite]}"
        local duration="${suite_durations[$suite]}"
        local suite_key="${suite// /_}"

        cat >> "$metrics_file" << EOF
    "$suite_key": {
      "status": "$status",
      "duration_seconds": $duration
    }
EOF
    done

    cat >> "$metrics_file" << EOF

  }
}
EOF

    echo -e "${CYAN}Performance metrics saved to:${NC}"
    echo -e "  $metrics_file"
    echo ""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Final Status
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    if [ $failed_suites -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                        ║${NC}"
        echo -e "${GREEN}║               ✅ ALL TESTS PASSED! ✅                  ║${NC}"
        echo -e "${GREEN}║                                                        ║${NC}"
        echo -e "${GREEN}║  All bug fixes validated                               ║${NC}"
        echo -e "${GREEN}║  All prevention mechanisms verified                    ║${NC}"
        echo -e "${GREEN}║  No regressions detected                               ║${NC}"
        echo -e "${GREEN}║                                                        ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                        ║${NC}"
        echo -e "${RED}║              ❌ TESTS FAILED ❌                        ║${NC}"
        echo -e "${RED}║                                                        ║${NC}"
        echo -e "${RED}║  $failed_suites out of $total_suites test suite(s) failed               ║${NC}"
        echo -e "${RED}║                                                        ║${NC}"
        echo -e "${RED}║  Please review the logs in .temp/analysis/             ║${NC}"
        echo -e "${RED}║                                                        ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
        echo ""
        return 1
    fi
}

# Run main and exit with its status
if main "$@"; then
    exit 0
else
    exit 1
fi
