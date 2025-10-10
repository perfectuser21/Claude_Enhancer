#!/usr/bin/env bash
# security_validation.sh - Comprehensive security validation test suite
set -euo pipefail

echo "===================================================="
echo "  Claude Enhancer - Security Validation Suite"
echo "===================================================="
echo ""

PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Source required libraries
source "$PROJECT_ROOT/.workflow/cli/lib/common.sh"
source "$PROJECT_ROOT/.workflow/cli/lib/input_validator.sh"

passed=0
failed=0
total=0

# Test helper functions
test_pass() {
    local test_name="$1"
    echo -e "${GREEN}[PASS]${RESET} $test_name"
    ((passed++))
    ((total++))
}

test_fail() {
    local test_name="$1"
    local reason="${2:-}"
    echo -e "${RED}[FAIL]${RESET} $test_name"
    [[ -n "$reason" ]] && echo -e "       ${YELLOW}Reason: $reason${RESET}"
    ((failed++))
    ((total++))
}

# ============================================================================
# Test 1: Feature Name Validation
# ============================================================================
echo -e "${BLUE}[Test Suite 1]${RESET} Feature Name Validation"
echo ""

# Should PASS
if ce_validate_feature_name "user-auth" 2>/dev/null; then
    test_pass "Valid feature name: 'user-auth'"
else
    test_fail "Valid feature name: 'user-auth'" "Should have passed"
fi

if ce_validate_feature_name "api" 2>/dev/null; then
    test_pass "Short valid name: 'api'"
else
    test_fail "Short valid name: 'api'" "Should have passed"
fi

# Should FAIL
if ! ce_validate_feature_name "../etc/passwd" 2>/dev/null; then
    test_pass "Path traversal rejected: '../etc/passwd'"
else
    test_fail "Path traversal rejected: '../etc/passwd'" "Should have failed"
fi

if ! ce_validate_feature_name "test; rm -rf /" 2>/dev/null; then
    test_pass "Command injection rejected: 'test; rm -rf /'"
else
    test_fail "Command injection rejected: 'test; rm -rf /'" "Should have failed"
fi

if ! ce_validate_feature_name "a" 2>/dev/null; then
    test_pass "Too short rejected: 'a'"
else
    test_fail "Too short rejected: 'a'" "Should have failed"
fi

if ! ce_validate_feature_name "$(printf 'a%.0s' {1..60})" 2>/dev/null; then
    test_pass "Too long rejected (60 chars)"
else
    test_fail "Too long rejected (60 chars)" "Should have failed"
fi

echo ""

# ============================================================================
# Test 2: Terminal ID Validation
# ============================================================================
echo -e "${BLUE}[Test Suite 2]${RESET} Terminal ID Validation"
echo ""

# Should PASS
if ce_validate_terminal_id "t1" 2>/dev/null; then
    test_pass "Valid terminal ID: 't1'"
else
    test_fail "Valid terminal ID: 't1'" "Should have passed"
fi

if ce_validate_terminal_id "t999" 2>/dev/null; then
    test_pass "Valid terminal ID: 't999'"
else
    test_fail "Valid terminal ID: 't999'" "Should have passed"
fi

# Should FAIL
if ! ce_validate_terminal_id "../../../etc" 2>/dev/null; then
    test_pass "Path traversal rejected: '../../../etc'"
else
    test_fail "Path traversal rejected: '../../../etc'" "Should have failed"
fi

if ! ce_validate_terminal_id "t1; rm -rf /" 2>/dev/null; then
    test_pass "Invalid characters rejected: 't1; rm -rf /'"
else
    test_fail "Invalid characters rejected: 't1; rm -rf /'" "Should have failed"
fi

if ! ce_validate_terminal_id "terminal" 2>/dev/null; then
    test_pass "Invalid format rejected: 'terminal'"
else
    test_fail "Invalid format rejected: 'terminal'" "Should have failed"
fi

echo ""

# ============================================================================
# Test 3: Path Validation
# ============================================================================
echo -e "${BLUE}[Test Suite 3]${RESET} Path Traversal Prevention"
echo ""

# Create test directories
mkdir -p /tmp/ce-test-allowed/subdir
mkdir -p /tmp/ce-test-forbidden

# Should PASS
if ce_validate_path "/tmp/ce-test-allowed/subdir/file.txt" "/tmp/ce-test-allowed" >/dev/null 2>&1; then
    test_pass "Valid path within allowed directory"
else
    test_fail "Valid path within allowed directory" "Should have passed"
fi

# Should FAIL
if ! ce_validate_path "/tmp/ce-test-forbidden/file.txt" "/tmp/ce-test-allowed" >/dev/null 2>&1; then
    test_pass "Path outside allowed directory rejected"
else
    test_fail "Path outside allowed directory rejected" "Should have failed"
fi

if ! ce_validate_path "/tmp/ce-test-allowed/../ce-test-forbidden/file.txt" "/tmp/ce-test-allowed" >/dev/null 2>&1; then
    test_pass "Path traversal via .. rejected"
else
    test_fail "Path traversal via .. rejected" "Should have failed"
fi

# Cleanup
rm -rf /tmp/ce-test-allowed /tmp/ce-test-forbidden

echo ""

# ============================================================================
# Test 4: Secure File Creation
# ============================================================================
echo -e "${BLUE}[Test Suite 4]${RESET} Secure File Operations"
echo ""

# Test secure file creation
test_file="/tmp/ce-secure-test-$$"
if ce_create_secure_file "$test_file" "test content" 600 2>/dev/null; then
    perms=$(stat -c '%a' "$test_file" 2>/dev/null || stat -f '%Lp' "$test_file" 2>/dev/null)
    if [[ "$perms" == "600" ]]; then
        test_pass "Secure file created with correct permissions (600)"
    else
        test_fail "Secure file created with correct permissions (600)" "Got: $perms"
    fi
    rm -f "$test_file"
else
    test_fail "Secure file creation" "Failed to create file"
fi

# Test secure directory creation
test_dir="/tmp/ce-secure-dir-$$"
if ce_create_secure_dir "$test_dir" 700 2>/dev/null; then
    perms=$(stat -c '%a' "$test_dir" 2>/dev/null || stat -f '%Lp' "$test_dir" 2>/dev/null)
    if [[ "$perms" == "700" ]]; then
        test_pass "Secure directory created with correct permissions (700)"
    else
        test_fail "Secure directory created with correct permissions (700)" "Got: $perms"
    fi
    rm -rf "$test_dir"
else
    test_fail "Secure directory creation" "Failed to create directory"
fi

echo ""

# ============================================================================
# Test 5: Log Sanitization
# ============================================================================
echo -e "${BLUE}[Test Suite 5]${RESET} Log Sanitization"
echo ""

# Test password redaction
sanitized=$(ce_log_sanitize "password=secret123 token=abc123")
if [[ "$sanitized" == *"***REDACTED***"* ]] && [[ "$sanitized" != *"secret123"* ]]; then
    test_pass "Password redaction works"
else
    test_fail "Password redaction works" "Still contains secrets"
fi

# Test GitHub token redaction
sanitized=$(ce_log_sanitize "ghp_1234567890123456789012345678901234567890")
if [[ "$sanitized" == *"***GITHUB_TOKEN***"* ]] && [[ "$sanitized" != *"ghp_"* ]]; then
    test_pass "GitHub token redaction works"
else
    test_fail "GitHub token redaction works" "Still contains token"
fi

# Test Bearer token redaction
sanitized=$(ce_log_sanitize "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
if [[ "$sanitized" == *"***REDACTED***"* ]] && [[ "$sanitized" != *"eyJh"* ]]; then
    test_pass "Bearer token redaction works"
else
    test_fail "Bearer token redaction works" "Still contains token"
fi

echo ""

# ============================================================================
# Test 6: Phase Validation
# ============================================================================
echo -e "${BLUE}[Test Suite 6]${RESET} Phase Validation"
echo ""

# Should PASS
for phase in P0 P1 P2 P3 P4 P5 P6 P7; do
    if ce_validate_phase "$phase" 2>/dev/null; then
        test_pass "Valid phase: '$phase'"
    else
        test_fail "Valid phase: '$phase'" "Should have passed"
    fi
done

# Should FAIL
if ! ce_validate_phase "P8" 2>/dev/null; then
    test_pass "Invalid phase rejected: 'P8'"
else
    test_fail "Invalid phase rejected: 'P8'" "Should have failed"
fi

if ! ce_validate_phase "phase3" 2>/dev/null; then
    test_pass "Invalid phase rejected: 'phase3'"
else
    test_fail "Invalid phase rejected: 'phase3'" "Should have failed"
fi

echo ""

# ============================================================================
# Test 7: Branch Name Validation
# ============================================================================
echo -e "${BLUE}[Test Suite 7]${RESET} Branch Name Validation"
echo ""

# Should PASS
if ce_validate_branch_name "feature/user-auth" 2>/dev/null; then
    test_pass "Valid branch name: 'feature/user-auth'"
else
    test_fail "Valid branch name: 'feature/user-auth'" "Should have passed"
fi

if ce_validate_branch_name "fix/bug-123" 2>/dev/null; then
    test_pass "Valid branch name: 'fix/bug-123'"
else
    test_fail "Valid branch name: 'fix/bug-123'" "Should have passed"
fi

# Should FAIL
if ! ce_validate_branch_name "invalid/../path" 2>/dev/null; then
    test_pass "Path traversal in branch name rejected"
else
    test_fail "Path traversal in branch name rejected" "Should have failed"
fi

if ! ce_validate_branch_name "feature/test; rm -rf /" 2>/dev/null; then
    test_pass "Command injection in branch name rejected"
else
    test_fail "Command injection in branch name rejected" "Should have failed"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "===================================================="
echo "  Test Results Summary"
echo "===================================================="
echo ""
echo -e "Total Tests: ${BLUE}$total${RESET}"
echo -e "Passed: ${GREEN}$passed${RESET}"
echo -e "Failed: ${RED}$failed${RESET}"
echo ""

if [[ $failed -eq 0 ]]; then
    echo -e "${GREEN}✓ All security tests passed!${RESET}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some security tests failed${RESET}"
    echo ""
    exit 1
fi
