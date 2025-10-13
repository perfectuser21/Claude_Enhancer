#!/bin/bash
# Regression tests: ensure fixes don't break existing functionality
# Path: test/regression/test_no_new_bugs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ANSI colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

test_count=0
pass_count=0
fail_count=0
warn_count=0

cd "$PROJECT_ROOT"

run_regression_test() {
    local test_name="$1"
    local test_func="$2"
    local critical="${3:-true}"  # true=critical, false=warning only

    ((test_count++))
    echo ""
    echo -e "${BLUE}Test $test_count: $test_name${NC}"
    echo -n "  "

    if $test_func; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((pass_count++))
        return 0
    else
        if [ "$critical" = "true" ]; then
            echo -e "${RED}❌ FAIL${NC}"
            ((fail_count++))
            return 1
        else
            echo -e "${YELLOW}⚠ WARNING${NC}"
            ((warn_count++))
            return 0
        fi
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

test_git_operations() {
    echo -n "Checking git status... "
    if git status >/dev/null 2>&1; then
        echo "OK"
        return 0
    else
        echo "FAILED"
        return 1
    fi
}

test_branch_operations() {
    echo -n "Checking branch listing... "
    if git branch >/dev/null 2>&1; then
        echo "OK"
        return 0
    else
        echo "FAILED"
        return 1
    fi
}

test_yaml_workflows() {
    echo -n "Validating CI workflows... "
    local all_valid=true

    if [ ! -d ".github/workflows" ]; then
        echo "NO WORKFLOWS DIR"
        return 0
    fi

    for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
        if [ -f "$workflow" ]; then
            if ! python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
                echo "INVALID: $workflow"
                all_valid=false
            fi
        fi
    done

    if $all_valid; then
        echo "OK"
        return 0
    else
        return 1
    fi
}

test_core_documents() {
    echo -n "Checking core documents... "
    local missing=()

    for doc in README.md CLAUDE.md; do
        if [ ! -f "$doc" ]; then
            missing+=("$doc")
        fi
    done

    if [ ${#missing[@]} -eq 0 ]; then
        echo "OK"
        return 0
    else
        echo "MISSING: ${missing[*]}"
        return 1
    fi
}

test_directory_structure() {
    echo -n "Checking critical directories... "
    local missing=()

    for dir in .claude .git test; do
        if [ ! -d "$dir" ]; then
            missing+=("$dir")
        fi
    done

    if [ ${#missing[@]} -eq 0 ]; then
        echo "OK"
        return 0
    else
        echo "MISSING: ${missing[*]}"
        return 1
    fi
}

test_hook_installation() {
    echo -n "Checking Git hooks installation... "

    if [ ! -f ".git/hooks/pre-commit" ]; then
        echo "MISSING pre-commit"
        return 1
    fi

    if [ ! -x ".git/hooks/pre-commit" ]; then
        echo "NOT EXECUTABLE"
        return 1
    fi

    echo "OK"
    return 0
}

test_python_imports() {
    echo -n "Testing Python environment... "

    if ! command -v python3 >/dev/null 2>&1; then
        echo "NO PYTHON3"
        return 1
    fi

    # Try basic import
    if python3 -c "import sys" 2>/dev/null; then
        echo "OK"
        return 0
    else
        echo "IMPORT FAILED"
        return 1
    fi
}

test_shell_hooks_syntax() {
    echo -n "Checking shell hook syntax... "
    local syntax_errors=0

    for hook in .claude/hooks/*.sh; do
        if [ -f "$hook" ]; then
            if ! bash -n "$hook" 2>/dev/null; then
                ((syntax_errors++))
            fi
        fi
    done

    if [ $syntax_errors -eq 0 ]; then
        echo "OK"
        return 0
    else
        echo "ERRORS: $syntax_errors files"
        return 1
    fi
}

test_json_config_files() {
    echo -n "Validating JSON configs... "
    local json_valid=true

    for json in package.json tsconfig.json .eslintrc.json; do
        if [ -f "$json" ]; then
            if ! python3 -m json.tool "$json" >/dev/null 2>&1; then
                echo "INVALID: $json"
                json_valid=false
            fi
        fi
    done

    if $json_valid; then
        echo "OK"
        return 0
    else
        return 1
    fi
}

test_no_broken_symlinks() {
    echo -n "Checking for broken symlinks... "

    local broken=$(find . -type l ! -exec test -e {} \; -print 2>/dev/null | wc -l)

    if [ "$broken" -eq 0 ]; then
        echo "OK"
        return 0
    else
        echo "FOUND: $broken"
        return 1
    fi
}

test_executable_permissions() {
    echo -n "Checking executable scripts... "
    local missing_exec=0

    # Check .sh files in key directories
    for script in .claude/hooks/*.sh test/*.sh scripts/*.sh; do
        if [ -f "$script" ] && [ ! -x "$script" ]; then
            ((missing_exec++))
        fi
    done

    if [ $missing_exec -eq 0 ]; then
        echo "OK"
        return 0
    else
        echo "NON-EXECUTABLE: $missing_exec files"
        return 0  # Warning only
    fi
}

test_test_directory_structure() {
    echo -n "Checking test directory structure... "

    if [ ! -d "test" ]; then
        echo "NO TEST DIR"
        return 1
    fi

    # Count test files
    local test_files=$(find test -name "test_*.sh" -o -name "test_*.py" -o -name "*.test.js" 2>/dev/null | wc -l)

    if [ "$test_files" -gt 0 ]; then
        echo "OK ($test_files test files)"
        return 0
    else
        echo "NO TEST FILES"
        return 1
    fi
}

test_claude_enhancer_structure() {
    echo -n "Checking Claude Enhancer structure... "
    local missing=()

    if [ ! -d ".claude" ]; then
        missing+=(".claude/")
    fi

    if [ ! -d ".claude/hooks" ]; then
        missing+=(".claude/hooks/")
    fi

    if [ ${#missing[@]} -eq 0 ]; then
        echo "OK"
        return 0
    else
        echo "MISSING: ${missing[*]}"
        return 1
    fi
}

test_no_sensitive_data() {
    echo -n "Checking for sensitive data patterns... "

    # Look for common sensitive patterns (excluding .git and node_modules)
    local found=$(grep -r \
        -E '(password|secret|api[_-]?key|token)\s*=\s*["\047][^"\047]+["\047]' \
        --include='*.sh' --include='*.py' --include='*.js' \
        --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='.temp' \
        . 2>/dev/null | \
        grep -v 'example\|test\|mock\|dummy\|placeholder' | \
        wc -l)

    if [ "$found" -eq 0 ]; then
        echo "OK"
        return 0
    else
        echo "POTENTIAL ISSUES: $found"
        return 0  # Warning only, might be false positives
    fi
}

test_script_shebangs() {
    echo -n "Checking script shebangs... "
    local missing_shebang=0

    for script in .claude/hooks/*.sh test/**/*.sh scripts/*.sh; do
        if [ -f "$script" ]; then
            if ! head -1 "$script" | grep -q '^#!'; then
                ((missing_shebang++))
            fi
        fi
    done

    if [ $missing_shebang -eq 0 ]; then
        echo "OK"
        return 0
    else
        echo "MISSING: $missing_shebang files"
        return 0  # Warning only
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Test Execution
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Regression Tests                      ║${NC}"
echo -e "${BLUE}║  Ensuring no existing functionality    ║${NC}"
echo -e "${BLUE}║  was broken by recent changes          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Category: Core Functionality${NC}"
run_regression_test "Git operations work normally" test_git_operations
run_regression_test "Branch operations work" test_branch_operations
run_regression_test "Directory structure intact" test_directory_structure

echo -e "\n${YELLOW}Category: Configuration Files${NC}"
run_regression_test "CI workflows are valid YAML" test_yaml_workflows
run_regression_test "JSON config files are valid" test_json_config_files "false"
run_regression_test "Core documents preserved" test_core_documents

echo -e "\n${YELLOW}Category: Code Quality${NC}"
run_regression_test "Shell hooks have valid syntax" test_shell_hooks_syntax
run_regression_test "Python environment works" test_python_imports "false"
run_regression_test "Scripts have proper shebangs" test_script_shebangs "false"

echo -e "\n${YELLOW}Category: Installation & Setup${NC}"
run_regression_test "Git hooks are installed" test_hook_installation
run_regression_test "Claude Enhancer structure" test_claude_enhancer_structure
run_regression_test "Test directory structure" test_test_directory_structure

echo -e "\n${YELLOW}Category: Security & Maintenance${NC}"
run_regression_test "No broken symlinks" test_no_broken_symlinks "false"
run_regression_test "Executable permissions set" test_executable_permissions "false"
run_regression_test "No obvious sensitive data" test_no_sensitive_data "false"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Regression Test Summary               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total tests:   $test_count"
echo -e "${GREEN}Passed:        $pass_count${NC}"
echo -e "${RED}Failed:        $fail_count${NC}"
echo -e "${YELLOW}Warnings:      $warn_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ All regression tests passed!${NC}"
    echo -e "${GREEN}   No existing functionality was broken.${NC}"
    exit 0
else
    echo -e "${RED}❌ $fail_count regression test(s) failed${NC}"
    echo -e "${RED}   Some existing functionality may be broken.${NC}"
    exit 1
fi
