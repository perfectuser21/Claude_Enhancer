#!/bin/bash
# =============================================================================
# Integration Test Runner
# Executes all integration and e2e tests for Claude Enhancer
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEST_DIR="${SCRIPT_DIR}/integration"
REPORT_DIR="${SCRIPT_DIR}/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/integration_test_report_${TIMESTAMP}.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Statistics
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0
START_TIME=$(date +%s)

# Create report directory
mkdir -p "${REPORT_DIR}"

# Logging
log_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}\n"
}

log_info() {
    echo -e "${BLUE}→${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_header "Checking Dependencies"

    local missing_deps=()

    if ! command -v bats &> /dev/null; then
        missing_deps+=("bats")
    else
        log_success "BATS installed: $(bats --version)"
    fi

    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    else
        log_success "Git installed: $(git --version | head -n1)"
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        echo "Install instructions:"
        echo "  BATS: npm install -g bats"
        echo "  Git:  apt-get install git (or equivalent)"
        exit 1
    fi

    log_success "All dependencies satisfied"
}

# Run test suite
run_test_suite() {
    local test_file="$1"
    local test_name=$(basename "${test_file}" .bats)

    log_header "Running: ${test_name}"

    local output_file="${REPORT_DIR}/${test_name}_${TIMESTAMP}.tap"

    if bats --tap "${test_file}" > "${output_file}" 2>&1; then
        local test_count=$(grep -c "^ok" "${output_file}" || echo 0)
        PASSED_TESTS=$((PASSED_TESTS + test_count))
        TOTAL_TESTS=$((TOTAL_TESTS + test_count))

        log_success "${test_name}: ${test_count} tests passed"
        return 0
    else
        local passed=$(grep -c "^ok" "${output_file}" || echo 0)
        local failed=$(grep -c "^not ok" "${output_file}" || echo 0)

        PASSED_TESTS=$((PASSED_TESTS + passed))
        FAILED_TESTS=$((FAILED_TESTS + failed))
        TOTAL_TESTS=$((TOTAL_TESTS + passed + failed))

        log_error "${test_name}: ${passed} passed, ${failed} failed"

        # Show failed test details
        echo ""
        grep "^not ok" "${output_file}" | head -5 || true
        echo ""

        return 1
    fi
}

# Run all integration tests
run_all_tests() {
    log_header "Claude Enhancer Integration Tests"

    local test_suites=(
        "test_complete_workflow.bats"
        "test_multi_terminal.bats"
        "test_conflict_detection.bats"
        "test_phase_transitions.bats"
        "test_quality_gates.bats"
    )

    local failed_suites=()

    for suite in "${test_suites[@]}"; do
        local test_file="${TEST_DIR}/${suite}"

        if [[ -f "${test_file}" ]]; then
            if ! run_test_suite "${test_file}"; then
                failed_suites+=("${suite}")
            fi
        else
            log_warn "Test suite not found: ${suite}"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        fi
    done

    return ${#failed_suites[@]}
}

# Generate report
generate_report() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    local pass_rate=0

    if [[ ${TOTAL_TESTS} -gt 0 ]]; then
        pass_rate=$(awk "BEGIN {printf \"%.1f\", (${PASSED_TESTS}/${TOTAL_TESTS})*100}")
    fi

    log_header "Generating Report"

    cat > "${REPORT_FILE}" << EOF
# Integration Test Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**Duration:** ${duration}s
**Project:** Claude Enhancer 5.0

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | ${TOTAL_TESTS} |
| Passed | ${PASSED_TESTS} |
| Failed | ${FAILED_TESTS} |
| Skipped | ${SKIPPED_TESTS} |
| Pass Rate | ${pass_rate}% |
| Execution Time | ${duration}s |

## Test Suites

### 1. Complete Workflow Tests
Tests the full feature development lifecycle from P1 through P6.

**Coverage:**
- Complete P1 workflow (Plan phase)
- P1→P2 progression (Plan to Skeleton)
- P1→P2→P3 cycle (Full implementation)
- P1→P2→P3→P4 cycle (Add testing)
- P1→P2→P3→P4→P5 cycle (Code review)
- P1→P2→P3→P4→P5→P6 cycle (Release)
- Full P1→P6 lifecycle in single test
- Workflow rollback scenarios
- State checkpoint and restoration

### 2. Multi-Terminal Tests
Tests concurrent development workflows across multiple terminals.

**Coverage:**
- Independent feature development (2 terminals)
- Parallel development (3 terminals)
- Phase progression in parallel
- Session isolation
- Concurrent PLAN.md edits
- Sequential merging of parallel work
- Performance with 10 concurrent branches
- Branch cleanup after merge

### 3. Conflict Detection Tests
Tests conflict detection and resolution mechanisms.

**Coverage:**
- Same file modifications
- Same line conflicts
- Multi-file conflict scenarios
- Manual merge resolution
- Deletion vs modification conflicts
- Directory structure conflicts
- Binary file conflicts
- File locking simulation
- Complex three-way merges

### 4. Phase Transition Tests
Tests phase progression, validation, and transition logic.

**Coverage:**
- P0→P1 (Discovery to Planning)
- P1→P2 (Planning to Skeleton)
- P2→P3 (Skeleton to Implementation)
- P3→P4 (Implementation to Testing)
- P4→P5 (Testing to Review)
- P5→P6 (Review to Release)
- P6→P7 (Release to Monitoring)
- Complete P0→P7 lifecycle
- Phase skip detection
- Backward transitions (rollback)
- Multiple forward-backward cycles
- Rapid sequential transitions
- Invalid phase handling

### 5. Quality Gates Tests
Tests quality gate validation and enforcement.

**Coverage:**
- P0 discovery validation
- P1 plan validation (task count, sections)
- P3 changelog validation
- P4 test coverage validation
- P4 test report validation
- P5 review validation (three sections)
- P5 REWORK scenario handling
- P6 README validation
- P6 version tag validation
- P7 monitoring validation
- Security scan validation
- Build validation
- Comprehensive all-phase validation

## Test Results by Suite

EOF

    # Add individual suite results
    for tap_file in "${REPORT_DIR}"/*.tap; do
        if [[ -f "${tap_file}" ]]; then
            local suite_name=$(basename "${tap_file}" .tap | sed "s/_${TIMESTAMP}//")
            local passed=$(grep -c "^ok" "${tap_file}" || echo 0)
            local failed=$(grep -c "^not ok" "${tap_file}" || echo 0)
            local total=$((passed + failed))

            cat >> "${REPORT_FILE}" << EOF
### ${suite_name}
- Total: ${total}
- Passed: ${passed}
- Failed: ${failed}

EOF
        fi
    done

    cat >> "${REPORT_FILE}" << EOF

## Environment

- **OS:** $(uname -s)
- **Kernel:** $(uname -r)
- **Git:** $(git --version | head -n1)
- **BATS:** $(bats --version)
- **Shell:** ${SHELL}
- **Working Directory:** ${PROJECT_ROOT}

## Test Artifacts

All test outputs saved to: \`${REPORT_DIR}\`

EOF

    if [[ ${FAILED_TESTS} -eq 0 ]]; then
        cat >> "${REPORT_FILE}" << EOF
## Conclusion

✅ **ALL TESTS PASSED** (${pass_rate}%)

The Claude Enhancer integration test suite has successfully validated all workflows, phase transitions, quality gates, and multi-terminal scenarios. The system is ready for production use.

EOF
    else
        cat >> "${REPORT_FILE}" << EOF
## Conclusion

⚠️ **SOME TESTS FAILED** (${pass_rate}% pass rate)

${FAILED_TESTS} out of ${TOTAL_TESTS} tests failed. Review the failed test details above and check the TAP output files for more information.

EOF
    fi

    cat >> "${REPORT_FILE}" << EOF
---
*Integration Test Suite - Claude Enhancer 5.0*
EOF

    log_success "Report saved: ${REPORT_FILE}"
}

# Display summary
display_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    log_header "Test Execution Summary"

    echo -e "${BOLD}Total Tests:${NC}    ${TOTAL_TESTS}"
    echo -e "${GREEN}${BOLD}Passed:${NC}         ${PASSED_TESTS}"
    echo -e "${RED}${BOLD}Failed:${NC}         ${FAILED_TESTS}"
    echo -e "${YELLOW}${BOLD}Skipped:${NC}        ${SKIPPED_TESTS}"
    echo -e "${BOLD}Duration:${NC}       ${duration}s"
    echo ""

    if [[ ${TOTAL_TESTS} -gt 0 ]]; then
        local pass_rate=$(awk "BEGIN {printf \"%.1f\", (${PASSED_TESTS}/${TOTAL_TESTS})*100}")
        echo -e "${BOLD}Pass Rate:${NC}      ${pass_rate}%"
    fi

    echo ""
    echo -e "${CYAN}Report:${NC}         ${REPORT_FILE}"
    echo ""

    if [[ ${FAILED_TESTS} -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}${BOLD}   ✓ ALL INTEGRATION TESTS PASSED ✓              ${NC}"
        echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════${NC}"
    else
        echo -e "${YELLOW}${BOLD}════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}${BOLD}   ⚠ SOME TESTS FAILED - REVIEW REQUIRED         ${NC}"
        echo -e "${YELLOW}${BOLD}════════════════════════════════════════════════════${NC}"
    fi

    echo ""
}

# Main execution
main() {
    log_header "Claude Enhancer 5.0 Integration Test Suite"

    check_dependencies

    if run_all_tests; then
        log_success "All test suites passed"
    else
        log_error "Some test suites failed"
    fi

    generate_report
    display_summary

    # Exit with appropriate code
    if [[ ${FAILED_TESTS} -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
