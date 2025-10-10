#!/usr/bin/env bash
# System Health Check for Claude Enhancer v5.4.0
# Purpose: Verify all critical components are operational
# Usage: ./system_health_check.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Health check results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

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
# HEALTH CHECK FUNCTIONS
# ============================================================

check_file_exists() {
    local file="$1"
    local description="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ -f "$file" ]]; then
        log_success "$description: File exists"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$description: File missing ($file)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_dir_exists() {
    local dir="$1"
    local description="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ -d "$dir" ]]; then
        log_success "$description: Directory exists"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$description: Directory missing ($dir)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_executable() {
    local file="$1"
    local description="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ -x "$file" ]]; then
        log_success "$description: Executable"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_warning "$description: Not executable ($file)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        return 1
    fi
}

check_version_consistency() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    local version_file="${PROJECT_ROOT}/VERSION"
    if [[ ! -f "$version_file" ]]; then
        log_error "Version Consistency: VERSION file missing"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi

    local version=$(cat "$version_file")

    # Check README.md badge
    if grep -q "version-${version}-blue" "${PROJECT_ROOT}/README.md" 2>/dev/null; then
        log_success "Version Consistency: VERSION ($version) matches README.md"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "Version Consistency: VERSION ($version) doesn't match README.md"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

check_security_scripts() {
    log_info "Checking security scripts..."

    check_file_exists "${PROJECT_ROOT}/.workflow/automation/security/owner_operations_monitor.sh" \
        "Security Script: owner_operations_monitor.sh"

    check_file_exists "${PROJECT_ROOT}/.workflow/automation/security/enforce_permissions.sh" \
        "Security Script: enforce_permissions.sh"

    check_file_exists "${PROJECT_ROOT}/.workflow/automation/utils/rate_limiter.sh" \
        "Security Script: rate_limiter.sh"

    check_file_exists "${PROJECT_ROOT}/.workflow/automation/security/automation_permission_verifier.sh" \
        "Security Script: automation_permission_verifier.sh"
}

check_test_suite() {
    log_info "Checking test suite..."

    check_file_exists "${PROJECT_ROOT}/test/security/test_sql_injection_prevention.bats" \
        "Test Suite: SQL injection tests"

    check_file_exists "${PROJECT_ROOT}/test/security/test_file_permissions.bats" \
        "Test Suite: File permission tests"

    check_file_exists "${PROJECT_ROOT}/test/security/test_rate_limiting.bats" \
        "Test Suite: Rate limiting tests"

    check_file_exists "${PROJECT_ROOT}/test/security/test_permission_verification.bats" \
        "Test Suite: Permission verification tests"

    check_file_exists "${PROJECT_ROOT}/test/security/run_security_tests.sh" \
        "Test Suite: Test runner"
}

check_documentation() {
    log_info "Checking documentation..."

    check_file_exists "${PROJECT_ROOT}/docs/P3_SECURITY_FIXES_SUMMARY.md" \
        "Documentation: P3 security fixes summary"

    check_file_exists "${PROJECT_ROOT}/docs/P4_SECURITY_TESTING_SUMMARY.md" \
        "Documentation: P4 testing summary"

    check_file_exists "${PROJECT_ROOT}/docs/REVIEW.md" \
        "Documentation: P5 code review"

    check_file_exists "${PROJECT_ROOT}/docs/RELEASE_NOTES_v5.4.0.md" \
        "Documentation: v5.4.0 release notes"

    check_file_exists "${PROJECT_ROOT}/docs/P6_RELEASE_SUMMARY.md" \
        "Documentation: P6 release summary"
}

check_git_health() {
    log_info "Checking Git repository health..."

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if git -C "$PROJECT_ROOT" rev-parse --git-dir &>/dev/null; then
        log_success "Git Repository: Valid repository"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "Git Repository: Not a valid git repository"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if git -C "$PROJECT_ROOT" tag | grep -q "v5.4.0"; then
        log_success "Git Tags: v5.4.0 tag exists"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "Git Tags: v5.4.0 tag missing"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

check_dependencies() {
    log_info "Checking required dependencies..."

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if command -v bash &>/dev/null; then
        local bash_version=$(bash --version | head -1 | awk '{print $4}')
        log_success "Dependency: bash ($bash_version)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_error "Dependency: bash not found"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if command -v sqlite3 &>/dev/null; then
        local sqlite_version=$(sqlite3 --version | awk '{print $1}')
        log_success "Dependency: sqlite3 ($sqlite_version)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_warning "Dependency: sqlite3 not found (required for permission system)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    fi

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if command -v openssl &>/dev/null; then
        local openssl_version=$(openssl version | awk '{print $2}')
        log_success "Dependency: openssl ($openssl_version)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_warning "Dependency: openssl not found (required for HMAC)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    fi

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if command -v bats &>/dev/null; then
        local bats_version=$(bats --version)
        log_success "Dependency: bats ($bats_version)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_warning "Dependency: bats not found (required for testing)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
    fi
}

# ============================================================
# MAIN HEALTH CHECK
# ============================================================

main() {
    echo ""
    log_info "╔═══════════════════════════════════════════════╗"
    log_info "║   Claude Enhancer v5.4.0 Health Check        ║"
    log_info "╚═══════════════════════════════════════════════╝"
    echo ""

    # Run all health checks
    check_version_consistency
    echo ""

    check_security_scripts
    echo ""

    check_test_suite
    echo ""

    check_documentation
    echo ""

    check_git_health
    echo ""

    check_dependencies
    echo ""

    # Summary
    log_info "═══════════════════════════════════════════════"
    log_info "Health Check Summary"
    log_info "═══════════════════════════════════════════════"
    echo ""

    log_info "Total Checks: $TOTAL_CHECKS"
    log_success "Passed: $PASSED_CHECKS"

    if [[ $WARNING_CHECKS -gt 0 ]]; then
        log_warning "Warnings: $WARNING_CHECKS"
    fi

    if [[ $FAILED_CHECKS -gt 0 ]]; then
        log_error "Failed: $FAILED_CHECKS"
    fi

    echo ""

    # Calculate health percentage
    local health_percentage=$(awk "BEGIN {printf \"%.1f\", ($PASSED_CHECKS / $TOTAL_CHECKS) * 100}")

    log_info "Health Percentage: ${health_percentage}%"

    # Determine overall status
    if [[ $FAILED_CHECKS -eq 0 ]] && [[ $WARNING_CHECKS -eq 0 ]]; then
        log_success "Overall Status: HEALTHY ✅"
        echo ""
        return 0
    elif [[ $FAILED_CHECKS -eq 0 ]]; then
        log_warning "Overall Status: HEALTHY (with warnings) ⚠️"
        echo ""
        return 0
    else
        log_error "Overall Status: UNHEALTHY ❌"
        echo ""
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
