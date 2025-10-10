#!/usr/bin/env bash
# Security Test Runner for Claude Enhancer v5.4.0
# Purpose: Run all security tests and generate report
# Usage: ./run_security_tests.sh [options]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
VERBOSE="${VERBOSE:-0}"
REPORT_FILE="${PROJECT_ROOT}/test/security/security_test_report.txt"

# Test files
SECURITY_TESTS=(
    "test_sql_injection_prevention.bats"
    "test_file_permissions.bats"
    "test_rate_limiting.bats"
    "test_permission_verification.bats"
)

# ============================================================
# LOGGING
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*"
}

# ============================================================
# PREREQUISITES
# ============================================================

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check bats is installed
    if ! command -v bats &>/dev/null; then
        log_error "bats not installed"
        log_info "Install: npm install -g bats"
        return 1
    fi

    log_success "bats found: $(bats --version)"

    # Check sqlite3
    if ! command -v sqlite3 &>/dev/null; then
        log_warning "sqlite3 not found (some tests may fail)"
    fi

    # Check required scripts exist
    local missing=0
    for script in \
        "${PROJECT_ROOT}/.workflow/automation/security/owner_operations_monitor.sh" \
        "${PROJECT_ROOT}/.workflow/automation/security/enforce_permissions.sh" \
        "${PROJECT_ROOT}/.workflow/automation/utils/rate_limiter.sh" \
        "${PROJECT_ROOT}/.workflow/automation/security/automation_permission_verifier.sh"; do

        if [[ ! -f "$script" ]]; then
            log_error "Missing: $script"
            missing=$((missing + 1))
        fi
    done

    if [[ $missing -gt 0 ]]; then
        log_error "Missing $missing required script(s)"
        return 1
    fi

    log_success "All required scripts found"
    return 0
}

# ============================================================
# TEST EXECUTION
# ============================================================

run_test_file() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .bats)

    log_info "Running: $test_name"

    local output
    local exit_code=0

    # Run bats with TAP output
    if [[ "$VERBOSE" == "1" ]]; then
        bats "$test_file" || exit_code=$?
    else
        output=$(bats --tap "$test_file" 2>&1) || exit_code=$?
    fi

    if [[ $exit_code -eq 0 ]]; then
        log_success "$test_name: ALL PASSED"
        return 0
    else
        log_error "$test_name: SOME FAILED"
        if [[ "$VERBOSE" != "1" ]]; then
            echo "$output" | grep -E "^(not ok|# )" || true
        fi
        return 1
    fi
}

run_all_tests() {
    local total_files=${#SECURITY_TESTS[@]}
    local passed=0
    local failed=0

    log_info "═══════════════════════════════════════════════"
    log_info "  Security Test Suite - Claude Enhancer v5.4.0"
    log_info "═══════════════════════════════════════════════"
    echo ""

    for test_file in "${SECURITY_TESTS[@]}"; do
        local test_path="${SCRIPT_DIR}/${test_file}"

        if [[ ! -f "$test_path" ]]; then
            log_warning "Test file not found: $test_file"
            continue
        fi

        if run_test_file "$test_path"; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi

        echo ""
    done

    # Summary
    log_info "═══════════════════════════════════════════════"
    log_info "  Test Summary"
    log_info "═══════════════════════════════════════════════"
    echo ""
    log_info "Total test files: $total_files"
    log_success "Passed: $passed"

    if [[ $failed -gt 0 ]]; then
        log_error "Failed: $failed"
        return 1
    else
        log_success "All security tests passed!"
        return 0
    fi
}

# ============================================================
# REPORT GENERATION
# ============================================================

generate_report() {
    log_info "Generating test report..."

    cat > "$REPORT_FILE" <<REPORT
========================================
Security Test Report
========================================
Date: $(date)
Project: Claude Enhancer v5.4.0

Test Suite Overview:
-------------------
Total Test Files: ${#SECURITY_TESTS[@]}
1. SQL Injection Prevention (30 tests)
2. File Permissions (10 tests)
3. Rate Limiting (15 tests)
4. Permission Verification (20 tests)

Total: 75 security test cases

Test Execution Results:
----------------------
REPORT

    # Run tests and capture results
    for test_file in "${SECURITY_TESTS[@]}"; do
        local test_path="${SCRIPT_DIR}/${test_file}"

        if [[ -f "$test_path" ]]; then
            echo "" >> "$REPORT_FILE"
            echo "Test File: $test_file" >> "$REPORT_FILE"
            echo "---" >> "$REPORT_FILE"

            # Run bats and append output
            bats --tap "$test_path" >> "$REPORT_FILE" 2>&1 || true
        fi
    done

    echo "" >> "$REPORT_FILE"
    echo "Report Generated: $(date)" >> "$REPORT_FILE"

    log_success "Report saved: $REPORT_FILE"
}

# ============================================================
# MAIN
# ============================================================

main() {
    local action="${1:-run}"

    case "$action" in
        run)
            check_prerequisites || exit 1
            echo ""
            run_all_tests
            ;;

        report)
            check_prerequisites || exit 1
            generate_report
            ;;

        check)
            check_prerequisites
            ;;

        help|*)
            cat <<HELP
Security Test Runner - Claude Enhancer v5.4.0

Usage: $0 [command]

Commands:
  run       Run all security tests (default)
  report    Generate detailed test report
  check     Check prerequisites only

Environment Variables:
  VERBOSE=1    Show detailed test output

Examples:
  # Run all tests
  $0

  # Run with verbose output
  VERBOSE=1 $0 run

  # Generate report
  $0 report

Test Files:
  - test_sql_injection_prevention.bats (30 tests)
  - test_file_permissions.bats (10 tests)
  - test_rate_limiting.bats (15 tests)
  - test_permission_verification.bats (20 tests)

Total: 75 security test cases

Coverage:
  ✓ SQL injection vulnerabilities
  ✓ File permission enforcement
  ✓ Rate limiting mechanism
  ✓ Authorization system
HELP
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
