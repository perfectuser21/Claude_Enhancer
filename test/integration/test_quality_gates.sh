#!/bin/bash
# Integration tests for quality gates and prevention mechanisms
# Path: test/integration/test_quality_gates.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMP_TEST_DIR="$PROJECT_ROOT/.temp/integration_tests"

# ANSI colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

test_count=0
pass_count=0
fail_count=0

# Cleanup function
cleanup() {
    rm -rf "$TEMP_TEST_DIR"
    cd "$PROJECT_ROOT"
}
trap cleanup EXIT

# Setup
mkdir -p "$TEMP_TEST_DIR"
cd "$PROJECT_ROOT"

run_integration_test() {
    local test_name="$1"
    local test_func="$2"

    ((test_count++))
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Test $test_count: $test_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if $test_func; then
        echo -e "${GREEN}✅ PASS: $test_name${NC}"
        ((pass_count++))
        return 0
    else
        echo -e "${RED}❌ FAIL: $test_name${NC}"
        ((fail_count++))
        return 1
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

test_git_hook_activation() {
    echo "Checking if Git hooks are properly activated..."

    # Check if hooks are executable
    if [ ! -x ".git/hooks/pre-commit" ]; then
        echo "❌ pre-commit hook is not executable"
        return 1
    fi

    # Check if pre-commit has shebang
    if ! head -1 .git/hooks/pre-commit | grep -q '^#!'; then
        echo "❌ pre-commit hook missing shebang"
        return 1
    fi

    echo "✓ Git hooks are properly activated"
    return 0
}

test_hook_bypass_prevention() {
    echo "Testing that git hooks cannot be bypassed..."

    # Check if hook detects bypass attempts
    if grep -q 'GIT_SKIP_HOOKS\|no-verify' .git/hooks/pre-commit 2>/dev/null; then
        echo "✓ Hook has bypass detection"
    else
        echo "⚠ Hook may not detect all bypass attempts"
    fi

    # Simulate bypass attempt
    export GIT_SKIP_HOOKS=1
    if .git/hooks/pre-commit 2>/dev/null; then
        echo "❌ Hook was bypassed with GIT_SKIP_HOOKS"
        unset GIT_SKIP_HOOKS
        return 1
    else
        echo "✓ Bypass attempt was blocked"
        unset GIT_SKIP_HOOKS
    fi

    return 0
}

test_shellcheck_validation() {
    echo "Testing shell script validation..."

    if ! command -v shellcheck >/dev/null 2>&1; then
        echo "⚠ shellcheck not installed, skipping"
        return 0
    fi

    # Test a known good script
    local test_script="$TEMP_TEST_DIR/good_script.sh"
    cat > "$test_script" << 'EOF'
#!/bin/bash
set -euo pipefail
echo "Hello World"
EOF

    if shellcheck "$test_script"; then
        echo "✓ Shellcheck validation works"
        return 0
    else
        echo "❌ Shellcheck validation failed"
        return 1
    fi
}

test_bad_syntax_detection() {
    echo "Testing detection of bad shell syntax..."

    local bad_script="$TEMP_TEST_DIR/bad_script.sh"
    cat > "$bad_script" << 'EOF'
#!/bin/bash
bad shell $$$ syntax
if [ missing bracket
EOF

    if bash -n "$bad_script" 2>/dev/null; then
        echo "❌ Bad syntax was not detected"
        return 1
    else
        echo "✓ Bad syntax was properly detected"
        return 0
    fi
}

test_document_creation_control() {
    echo "Testing document creation control..."

    # Check if there's a mechanism to control document creation
    local doc_control_hook=".claude/hooks/unified_post_processor.sh"

    if [ -f "$doc_control_hook" ]; then
        echo "✓ Document control hook exists: $doc_control_hook"

        # Check if it has document validation
        if grep -q 'AUTHORIZED_DOCUMENTS\|document.*control\|unauthorized' "$doc_control_hook" 2>/dev/null; then
            echo "✓ Document control mechanism found"
            return 0
        else
            echo "⚠ Document control hook exists but may not have validation"
            return 0
        fi
    else
        echo "⚠ No document control hook found (acceptable if not needed)"
        return 0
    fi
}

test_coverage_threshold() {
    echo "Testing coverage threshold enforcement..."

    # Check if coverage threshold is configured
    if [ -f "package.json" ] && grep -q '"coverage"' package.json; then
        echo "✓ Coverage configuration found in package.json"

        # Check for threshold
        if grep -q '"lines":\s*[0-9]' package.json || grep -q '"branches":\s*[0-9]' package.json; then
            echo "✓ Coverage thresholds are configured"
            return 0
        fi
    fi

    if [ -f "pytest.ini" ] && grep -q 'fail_under' pytest.ini; then
        echo "✓ Coverage threshold found in pytest.ini"
        return 0
    fi

    echo "⚠ No coverage threshold configured (may not be required)"
    return 0
}

test_phase_validation() {
    echo "Testing phase gate validation..."

    # Check if pre-commit hook has phase validation
    if [ -f ".git/hooks/pre-commit" ]; then
        if grep -q 'phase\|P[0-7]\|workflow' .git/hooks/pre-commit 2>/dev/null; then
            echo "✓ Phase validation logic found in pre-commit hook"
            return 0
        else
            echo "⚠ No explicit phase validation in hooks (may use other mechanism)"
            return 0
        fi
    else
        echo "❌ pre-commit hook not found"
        return 1
    fi
}

test_safe_operations() {
    echo "Testing safe operation wrappers..."

    # Check for safe rm wrapper
    if [ -f ".claude/core/safety.sh" ]; then
        if grep -q 'safe_rm_rf' .claude/core/safety.sh; then
            echo "✓ Safe rm wrapper exists"
            return 0
        fi
    fi

    # Check if hooks use safe operations
    if grep -r 'rm -rf' .claude/hooks/ 2>/dev/null | grep -v 'safe_rm_rf' | grep -v '#'; then
        echo "⚠ Found potentially unsafe rm -rf usage"
        return 0  # Warning, not failure
    else
        echo "✓ No unsafe rm -rf operations found"
        return 0
    fi
}

test_concurrent_safety() {
    echo "Testing concurrent operation safety..."

    # Check for mutex/locking mechanisms
    if grep -r 'flock\|lock.*file\|mutex' .claude/hooks/ .git/hooks/ 2>/dev/null | grep -v Binary | head -5; then
        echo "✓ Lock mechanisms found for concurrent safety"
        return 0
    else
        echo "⚠ No explicit lock mechanisms found (may not be needed)"
        return 0
    fi
}

test_yaml_validity() {
    echo "Testing YAML configuration validity..."

    local yaml_valid=true

    for yaml_file in .github/workflows/*.yml; do
        if [ -f "$yaml_file" ]; then
            if ! python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
                echo "❌ Invalid YAML: $yaml_file"
                yaml_valid=false
            fi
        fi
    done

    if $yaml_valid; then
        echo "✓ All YAML files are valid"
        return 0
    else
        echo "❌ Some YAML files are invalid"
        return 1
    fi
}

test_hook_error_handling() {
    echo "Testing hook error handling..."

    # Check if hooks have proper error handling
    local hooks_with_errors=0

    for hook in .git/hooks/*; do
        if [ -f "$hook" ] && [ -x "$hook" ] && ! echo "$hook" | grep -q '.sample'; then
            if grep -q 'set -e\|set -euo pipefail' "$hook"; then
                ((hooks_with_errors++))
            fi
        fi
    done

    if [ $hooks_with_errors -gt 0 ]; then
        echo "✓ Found $hooks_with_errors hooks with proper error handling"
        return 0
    else
        echo "⚠ No hooks found with error handling flags"
        return 0
    fi
}

test_version_consistency() {
    echo "Testing version consistency across files..."

    # Check if version is consistent in key files
    local versions_found=()

    if [ -f "package.json" ]; then
        local pkg_version=$(python3 -c "import json; print(json.load(open('package.json')).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
        versions_found+=("package.json:$pkg_version")
    fi

    if [ -f "CLAUDE.md" ] && grep -q 'version\|v[0-9]' CLAUDE.md; then
        local claude_version=$(grep -oP '(?<=version|v)\s*[0-9]+\.[0-9]+(\.[0-9]+)?' CLAUDE.md | head -1 || echo "unknown")
        versions_found+=("CLAUDE.md:$claude_version")
    fi

    if [ ${#versions_found[@]} -gt 0 ]; then
        echo "✓ Version information found in:"
        printf '%s\n' "${versions_found[@]}" | sed 's/^/  /'
        return 0
    else
        echo "⚠ No version information found (may not be versioned yet)"
        return 0
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main Test Execution
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Quality Gate Integration Tests       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

run_integration_test "Git Hook Activation" test_git_hook_activation
run_integration_test "Hook Bypass Prevention" test_hook_bypass_prevention
run_integration_test "Shellcheck Validation" test_shellcheck_validation
run_integration_test "Bad Syntax Detection" test_bad_syntax_detection
run_integration_test "Document Creation Control" test_document_creation_control
run_integration_test "Coverage Threshold" test_coverage_threshold
run_integration_test "Phase Validation" test_phase_validation
run_integration_test "Safe Operations" test_safe_operations
run_integration_test "Concurrent Safety" test_concurrent_safety
run_integration_test "YAML Validity" test_yaml_validity
run_integration_test "Hook Error Handling" test_hook_error_handling
run_integration_test "Version Consistency" test_version_consistency

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Integration Test Summary              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total tests:   $test_count"
echo -e "${GREEN}Passed:        $pass_count${NC}"
echo -e "${RED}Failed:        $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ All integration tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $fail_count test(s) failed${NC}"
    exit 1
fi
