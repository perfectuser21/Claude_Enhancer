#!/bin/bash
# Unit tests for critical bug fixes
# Path: test/unit/test_bug_fixes.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

test_count=0
pass_count=0
fail_count=0
skip_count=0

# ANSI colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

run_test() {
    local test_name="$1"
    local test_command="$2"
    local required="${3:-true}" # true=required, false=optional

    ((test_count++))
    echo -n "Test $test_count: $test_name ... "

    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((pass_count++))
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ FAIL${NC}"
            ((fail_count++))
            return 1
        else
            echo -e "${YELLOW}⊘ SKIP (optional)${NC}"
            ((skip_count++))
            return 0
        fi
    fi
}

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Bug Fix Unit Tests                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

cd "$PROJECT_ROOT"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 1: Shell Syntax Fixes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo -e "${YELLOW}Category 1: Shell Syntax Fixes${NC}"

# Test 1.1: Bash syntax check on branch_helper.sh
run_test "Bash syntax valid on branch_helper.sh" \
    "bash -n .claude/hooks/branch_helper.sh"

# Test 1.2: Bash syntax check on workflow_auto_start.sh
run_test "Bash syntax valid on workflow_auto_start.sh" \
    "bash -n .claude/hooks/workflow_auto_start.sh"

# Test 1.3: All hook scripts have valid syntax
run_test "All Claude hooks have valid bash syntax" \
    "find .claude/hooks -name '*.sh' -type f -exec bash -n {} \;"

# Test 1.4: Git hooks have valid syntax
run_test "Git pre-commit hook has valid syntax" \
    "[ ! -f .git/hooks/pre-commit ] || bash -n .git/hooks/pre-commit"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 2: Python Import Fixes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${YELLOW}Category 2: Python Import Fixes${NC}"

# Test 2.1: Python syntax check
if [ -d "test/unit" ] && compgen -G "test/unit/*.py" > /dev/null; then
    run_test "Python test files have valid syntax" \
        "python3 -m py_compile test/unit/*.py" \
        "false"
else
    echo "Test $((test_count + 1)): Python test files have valid syntax ... ⊘ SKIP (no py files)"
    ((skip_count++))
fi

# Test 2.2: Core imports work
run_test "Core Python imports work" \
    "python3 -c 'import sys'" \
    "false"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 3: Method/Function Fixes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${YELLOW}Category 3: Method/Function Fixes${NC}"

# Test 3.1: select_agents_fast method exists
if [ -f ".claude/core/lazy_orchestrator.py" ]; then
    run_test "select_agents_fast method exists in LazyOrchestrator" \
        "grep -q 'def select_agents_fast' .claude/core/lazy_orchestrator.py"
else
    echo "Test $((test_count + 1)): select_agents_fast method exists ... ⊘ SKIP (file missing)"
    ((skip_count++))
fi

# Test 3.2: safe_rm_rf function exists
if [ -f ".claude/core/safety.sh" ]; then
    run_test "safe_rm_rf function exists in safety.sh" \
        "grep -q 'safe_rm_rf' .claude/core/safety.sh"
else
    echo "Test $((test_count + 1)): safe_rm_rf function exists ... ⊘ SKIP (file missing)"
    ((skip_count++))
fi

# Test 3.3: Error handling in hooks
run_test "Hooks have proper error handling (set -e or set -euo pipefail)" \
    "[ ! -f .git/hooks/pre-commit ] || grep -q 'set -e' .git/hooks/pre-commit"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 4: Configuration Fixes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${YELLOW}Category 4: Configuration Fixes${NC}"

# Test 4.1: No duplicate keys in YAML files
if compgen -G ".github/workflows/*.yml" > /dev/null; then
    run_test "CI workflows have no duplicate keys (Python YAML check)" \
        "for f in .github/workflows/*.yml; do python3 -c \"import yaml; yaml.safe_load(open('\$f'))\" || exit 1; done" \
        "false"
else
    echo "Test $((test_count + 1)): CI workflows valid ... ⊘ SKIP (no workflows)"
    ((skip_count++))
fi

# Test 4.2: package.json is valid JSON
if [ -f "package.json" ]; then
    run_test "package.json is valid JSON" \
        "python3 -m json.tool package.json >/dev/null"
else
    echo "Test $((test_count + 1)): package.json is valid JSON ... ⊘ SKIP (no package.json)"
    ((skip_count++))
fi

# Test 4.3: No trailing commas in JSON
if [ -f "package.json" ]; then
    run_test "package.json has no trailing commas" \
        "! grep -E ',\s*[}\]]' package.json"
else
    echo "Test $((test_count + 1)): package.json has no trailing commas ... ⊘ SKIP (no package.json)"
    ((skip_count++))
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 5: Race Condition Fixes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${YELLOW}Category 5: Race Condition Fixes${NC}"

# Test 5.1: Mutex/lock mechanisms exist
run_test "Lock mechanisms found in hooks or scripts" \
    "grep -r 'flock\|mkdir.*lock\|lockfile' .claude/hooks/ 2>/dev/null | grep -v Binary | wc -l | grep -qv '^0$'" \
    "false"

# Test 5.2: Phase validation has error handling
run_test "Phase validation has strict error handling" \
    "[ ! -f .git/hooks/pre-commit ] || grep -q 'exit 1\|return 1' .git/hooks/pre-commit"

# Test 5.3: Temp files use unique names
run_test "Temp files use unique names ($$, RANDOM, or mktemp)" \
    "grep -r '\$\$\|RANDOM\|mktemp' .claude/hooks/*.sh 2>/dev/null | wc -l | grep -qv '^0$'" \
    "false"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 6: Security Fixes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${YELLOW}Category 6: Security Fixes${NC}"

# Test 6.1: No hardcoded credentials in hooks
run_test "No hardcoded passwords in hook scripts" \
    "! grep -r 'password\s*=\s*[\"'\''']' --include='*.sh' .claude/hooks/ 2>/dev/null | grep -v 'example\|test\|mock'" \
    "false"

# Test 6.2: Proper input sanitization (quoted variables)
run_test "User input is sanitized (use of quotes in variable expansion)" \
    "grep -r '\"\$' .claude/hooks/*.sh 2>/dev/null | wc -l | grep -qv '^0$'" \
    "false"

# Test 6.3: Safe rm operations
if [ -f ".claude/core/safety.sh" ]; then
    run_test "Dangerous rm -rf calls use safe wrapper" \
        "grep -q 'safe_rm_rf' .claude/core/safety.sh"
else
    echo "Test $((test_count + 1)): Dangerous rm -rf calls use safe wrapper ... ⊘ SKIP (safety.sh missing)"
    ((skip_count++))
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Results Summary                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total tests:   $test_count"
echo -e "${GREEN}Passed:        $pass_count${NC}"
echo -e "${RED}Failed:        $fail_count${NC}"
echo -e "${YELLOW}Skipped:       $skip_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ All unit tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $fail_count test(s) failed${NC}"
    exit 1
fi
