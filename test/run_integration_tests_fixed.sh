#!/bin/bash
# =============================================================================
# Integration Test Runner - Fixed Version
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

    # Run bats and capture exit code
    set +e
    bats --tap "${test_file}" > "${output_file}" 2>&1
    local exit_code=$?
    set -e

    # Count passed tests
    local passed_count=$(grep -c "^ok " "${output_file}" 2>/dev/null || echo "0")
    local failed_count=$(grep -c "^not ok " "${output_file}" 2>/dev/null || echo "0")

    # Clean count values (remove whitespace/newlines)
    passed_count=$(echo "${passed_count}" | tr -d '[:space:]')
    failed_count=$(echo "${failed_count}" | tr -d '[:space:]')

    # Update totals
    PASSED_TESTS=$((PASSED_TESTS + passed_count))
    FAILED_TESTS=$((FAILED_TESTS + failed_count))
    TOTAL_TESTS=$((TOTAL_TESTS + passed_count + failed_count))

    if [[ $exit_code -eq 0 ]]; then
        log_success "${test_name}: ${passed_count} tests passed"
        return 0
    else
        log_error "${test_name}: ${passed_count} passed, ${failed_count} failed"

        # Show failed test details
        echo ""
        grep "^not ok " "${output_file}" 2>/dev/null | head -5 || true
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

    local failed_count=0

    for suite in "${test_suites[@]}"; do
        local test_file="${TEST_DIR}/${suite}"

        if [[ -f "${test_file}" ]]; then
            if ! run_test_suite "${test_file}"; then
                failed_count=$((failed_count + 1))
            fi
        else
            log_warn "Test suite not found: ${suite}"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        fi
    done

    return ${failed_count}
}

# Generate simple summary
generate_summary() {
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
    echo -e "${CYAN}Reports saved to:${NC} ${REPORT_DIR}"
    echo ""
}

# Main execution
main() {
    log_header "Claude Enhancer 5.0 Integration Test Suite"

    check_dependencies

    local test_result=0
    if ! run_all_tests; then
        test_result=1
        log_error "Some test suites failed"
    else
        log_success "All test suites passed"
    fi

    generate_summary

    # Exit with appropriate code
    exit ${test_result}
}

# Run main function
main "$@"
