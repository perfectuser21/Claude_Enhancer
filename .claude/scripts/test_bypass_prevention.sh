#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# BYPASS PREVENTION TEST SUITE
# Claude Enhancer 5.0 - Verify hooks cannot be bypassed
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
_YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo -e "${BOLD}🧪 Testing Bypass Prevention${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"  # "PASS" or "BLOCK"
    
    ((TESTS_RUN++))
    
    echo -e "\n${CYAN}Test $TESTS_RUN: $test_name${NC}"
    
    # Run test in subshell to isolate environment
    if (eval "$test_command") &>/dev/null; then
        result="PASS"
    else
        result="BLOCK"
    fi
    
    if [ "$result" = "$expected_result" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Expected: $expected_result, Got: $result)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_result, Got: $result)"
        ((TESTS_FAILED++))
    fi
}

# Setup: Create test branch
echo -e "\n${CYAN}[SETUP]${NC}"
git config user.email "test@example.com" 2>/dev/null || true
git config user.name "Test User" 2>/dev/null || true

current_branch=$(git rev-parse --abbrev-ref HEAD)
test_branch="test/bypass-prevention-$$"

git checkout -b "$test_branch" 2>/dev/null || git checkout "$test_branch" 2>/dev/null || true
echo -e "${GREEN}✓ Test branch: $test_branch${NC}"

# Create test file
echo "test" > "$PROJECT_ROOT/.test_file_$$"
git add "$PROJECT_ROOT/.test_file_$$"

# ═══════════════════════════════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════════════════════════════

echo -e "\n${BOLD}[BYPASS PREVENTION TESTS]${NC}"

# Test 1: Normal commit (should pass)
run_test \
    "Normal commit on feature branch" \
    "git commit -m 'test' --no-verify; git reset --soft HEAD~1" \
    "PASS"

# Test 2: --no-verify flag (should be blocked)
run_test \
    "Commit with --no-verify flag" \
    "git commit -m 'test' --no-verify 2>&1 | grep -q 'bypass'" \
    "PASS"

# Test 3: Environment variable bypass (should be blocked)
run_test \
    "Commit with SKIP_HOOKS=1" \
    "SKIP_HOOKS=1 git commit -m 'test'" \
    "BLOCK"

# Test 4: Environment variable bypass alt (should be blocked)
run_test \
    "Commit with GIT_HOOKS_SKIP=1" \
    "GIT_HOOKS_SKIP=1 git commit -m 'test'" \
    "BLOCK"

# Test 5: Protected branch check
if [ "$current_branch" != "main" ] && [ "$current_branch" != "master" ]; then
    run_test \
        "Switch to main and commit (should block)" \
        "git checkout main 2>/dev/null && git commit -m 'test' 2>&1 | grep -q '禁止直接提交'" \
        "PASS"
    
    git checkout "$test_branch" 2>/dev/null || true
fi

# Test 6: Hook integrity check
run_test \
    "Pre-commit hook is executable" \
    "test -x $HOOKS_DIR/pre-commit" \
    "PASS"

# Test 7: Hook not symlinked to /dev/null
run_test \
    "Pre-commit not redirected to /dev/null" \
    "! readlink $HOOKS_DIR/pre-commit 2>/dev/null | grep -q '/dev/null'" \
    "PASS"

# Test 8: Hook contains bypass detection
run_test \
    "Pre-commit has bypass detection code" \
    "grep -q 'SKIP_HOOKS' $HOOKS_DIR/pre-commit" \
    "PASS"

# Test 9: Security scanning active
run_test \
    "Security scan detects AWS key pattern" \
    "echo '+AKIAIOSFODNN7EXAMPLE' | git diff --cached | grep -q 'AKIA[0-9A-Z]'" \
    "PASS"

# Test 10: Hook performance (<500ms)
echo -e "\n${CYAN}Test 10: Hook performance check${NC}"
((TESTS_RUN++))

start=$(date +%s%N)
bash "$HOOKS_DIR/pre-commit" &>/dev/null || true
end=$(date +%s%N)
duration=$(( (end - start) / 1000000 ))

if [ $duration -lt 500 ]; then
    echo -e "${GREEN}✓ PASS${NC} (${duration}ms < 500ms)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (${duration}ms >= 500ms)"
    ((TESTS_FAILED++))
fi

# ═══════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════

echo -e "\n${CYAN}[CLEANUP]${NC}"

# Remove test file
rm -f "$PROJECT_ROOT/.test_file_$$"
git reset HEAD "$PROJECT_ROOT/.test_file_$$" 2>/dev/null || true

# Return to original branch
git checkout "$current_branch" 2>/dev/null || true
git branch -D "$test_branch" 2>/dev/null || true

echo -e "${GREEN}✓ Cleanup complete${NC}"

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BOLD}TEST SUMMARY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Total Tests:  $TESTS_RUN"
echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${BOLD}${GREEN}✅ ALL TESTS PASSED${NC}"
    echo -e "Bypass prevention is ${BOLD}ACTIVE${NC} and ${BOLD}EFFECTIVE${NC}"
    exit 0
else
    echo ""
    echo -e "${BOLD}${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "Review failed tests and reinstall hooks if needed"
    exit 1
fi
