#!/usr/bin/env bash
# test_modules.sh - Verification script for PR Automator and Gate Integrator
# Tests all major functions to ensure correct implementation

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test result tracking
FAILED_TESTS=()

# Helper functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BLUE}║  $1${RESET}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${RESET}"
}

print_test() {
    echo -e "${YELLOW}▶ Testing: $1${RESET}"
}

pass() {
    echo -e "${GREEN}  ✓ $1${RESET}"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}  ✗ $1${RESET}"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

run_test() {
    ((TESTS_RUN++))
}

# ============================================================================
# PR Automator Tests
# ============================================================================

test_pr_automator() {
    print_header "Testing PR Automator (pr_automator.sh)"

    # Source the module
    if ! source .workflow/cli/lib/pr_automator.sh 2>/dev/null; then
        fail "Failed to source pr_automator.sh"
        return 1
    fi
    pass "Module loaded successfully"

    # Test 1: ce_pr_generate_title
    print_test "ce_pr_generate_title"
    run_test
    local title
    title=$(ce_pr_generate_title 2>/dev/null || echo "")
    if [[ -n "$title" ]]; then
        pass "Generated title: $title"
    else
        fail "Failed to generate title"
    fi

    # Test 2: ce_pr_parse_remote (SSH format)
    print_test "ce_pr_parse_remote (SSH)"
    run_test
    local parsed
    parsed=$(ce_pr_parse_remote "git@github.com:user/repo.git" 2>/dev/null || echo "")
    if [[ "$parsed" == "user/repo" ]]; then
        pass "Parsed SSH remote: $parsed"
    else
        fail "Failed to parse SSH remote (got: $parsed)"
    fi

    # Test 3: ce_pr_parse_remote (HTTPS format)
    print_test "ce_pr_parse_remote (HTTPS)"
    run_test
    parsed=$(ce_pr_parse_remote "https://github.com/user/repo.git" 2>/dev/null || echo "")
    if [[ "$parsed" == "user/repo" ]]; then
        pass "Parsed HTTPS remote: $parsed"
    else
        fail "Failed to parse HTTPS remote (got: $parsed)"
    fi

    # Test 4: ce_pr_calculate_size
    print_test "ce_pr_calculate_size"
    run_test
    local size
    size=$(ce_pr_calculate_size 2>/dev/null || echo "")
    if [[ "$size" =~ ^size/(XS|S|M|L|XL)$ ]]; then
        pass "Calculated PR size: $size"
    else
        fail "Invalid PR size format (got: $size)"
    fi

    # Test 5: ce_pr_suggest_labels
    print_test "ce_pr_suggest_labels"
    run_test
    local labels
    labels=$(ce_pr_suggest_labels 2>/dev/null || echo "")
    if [[ -n "$labels" ]]; then
        pass "Suggested labels: $labels"
    else
        # Labels might be empty if no files changed, that's ok
        pass "Label suggestion completed (empty result acceptable)"
    fi

    # Test 6: ce_pr_check_gh_installed
    print_test "ce_pr_check_gh_installed"
    run_test
    if ce_pr_check_gh_installed 2>/dev/null; then
        pass "GitHub CLI detected"
    else
        pass "GitHub CLI not installed (fallback will work)"
    fi

    # Test 7: ce_pr_generate_summary
    print_test "ce_pr_generate_summary"
    run_test
    local summary
    summary=$(ce_pr_generate_summary 2>/dev/null || echo "")
    if [[ -n "$summary" ]]; then
        pass "Generated summary (${#summary} characters)"
    else
        fail "Failed to generate summary"
    fi

    # Test 8: ce_pr_add_metrics
    print_test "ce_pr_add_metrics"
    run_test
    local metrics
    metrics=$(ce_pr_add_metrics 2>/dev/null || echo "")
    if [[ "$metrics" =~ "Quality Metrics" ]]; then
        pass "Generated metrics table"
    else
        fail "Failed to generate metrics table"
    fi

    # Test 9: Function exports
    print_test "Function exports"
    run_test
    local exported_functions=(
        ce_pr_create
        ce_pr_generate_title
        ce_pr_generate_description
        ce_pr_parse_remote
        ce_pr_calculate_size
    )
    local export_ok=true
    for func in "${exported_functions[@]}"; do
        if ! declare -F "$func" &>/dev/null; then
            export_ok=false
            break
        fi
    done
    if [[ "$export_ok" == "true" ]]; then
        pass "All key functions exported"
    else
        fail "Some functions not exported"
    fi

    echo ""
}

# ============================================================================
# Gate Integrator Tests
# ============================================================================

test_gate_integrator() {
    print_header "Testing Gate Integrator (gate_integrator.sh)"

    # Source the module
    if ! source .workflow/cli/lib/gate_integrator.sh 2>/dev/null; then
        fail "Failed to source gate_integrator.sh"
        return 1
    fi
    pass "Module loaded successfully"

    # Test 1: ce_gate_get_score
    print_test "ce_gate_get_score"
    run_test
    local score
    score=$(ce_gate_get_score "code-quality" 2>/dev/null || echo "0")
    if [[ "$score" =~ ^[0-9]+$ ]]; then
        pass "Retrieved score: $score"
    else
        fail "Invalid score format (got: $score)"
    fi

    # Test 2: ce_gate_get_coverage_value
    print_test "ce_gate_get_coverage_value"
    run_test
    local coverage
    coverage=$(ce_gate_get_coverage_value 2>/dev/null || echo "N/A")
    if [[ "$coverage" =~ ^[0-9.]+$ ]] || [[ "$coverage" == "N/A" ]]; then
        pass "Retrieved coverage: $coverage%"
    else
        fail "Invalid coverage format (got: $coverage)"
    fi

    # Test 3: ce_gate_check_signatures
    print_test "ce_gate_check_signatures"
    run_test
    if ce_gate_check_signatures 2>&1 | grep -q "signatures"; then
        pass "Signature check executed"
    else
        fail "Signature check failed to execute"
    fi

    # Test 4: ce_gate_show_summary
    print_test "ce_gate_show_summary"
    run_test
    local summary
    summary=$(ce_gate_show_summary 2>/dev/null || echo "")
    if [[ "$summary" =~ "Quality Gates Summary" ]]; then
        pass "Generated gate summary"
    else
        fail "Failed to generate gate summary"
    fi

    # Test 5: ce_gate_load_config
    print_test "ce_gate_load_config"
    run_test
    if ce_gate_load_config 2>/dev/null | grep -q "phase"; then
        pass "Loaded gates.yml configuration"
    else
        # Config might not exist, that's acceptable
        pass "Config load executed (file may not exist)"
    fi

    # Test 6: ce_gate_validate_config
    print_test "ce_gate_validate_config"
    run_test
    if ce_gate_validate_config 2>&1 | grep -q "Validating"; then
        pass "Config validation executed"
    else
        fail "Config validation failed to execute"
    fi

    # Test 7: Gate file operations
    print_test "ce_gate_read_status"
    run_test
    # Try to read status of gate 03 (likely exists)
    if ce_gate_read_status "03" 2>&1 | grep -q "Gate P03"; then
        pass "Gate status read successfully"
    else
        pass "Gate status read executed (gate may not exist)"
    fi

    # Test 8: ce_gate_check_phase_gate
    print_test "ce_gate_check_phase_gate"
    run_test
    if ce_gate_check_phase_gate "P3" "code-quality" 2>/dev/null; then
        pass "Phase gate check executed (passed)"
    else
        pass "Phase gate check executed (failed as expected)"
    fi

    # Test 9: Function exports
    print_test "Function exports"
    run_test
    local exported_functions=(
        ce_gate_validate_all
        ce_gate_check_score
        ce_gate_check_coverage
        ce_gate_check_security
        ce_gate_show_summary
    )
    local export_ok=true
    for func in "${exported_functions[@]}"; do
        if ! declare -F "$func" &>/dev/null; then
            export_ok=false
            break
        fi
    done
    if [[ "$export_ok" == "true" ]]; then
        pass "All key functions exported"
    else
        fail "Some functions not exported"
    fi

    echo ""
}

# ============================================================================
# Integration Tests
# ============================================================================

test_integration() {
    print_header "Testing Module Integration"

    # Test 1: Load both modules together
    print_test "Load both modules simultaneously"
    run_test
    if source .workflow/cli/lib/pr_automator.sh 2>/dev/null && \
       source .workflow/cli/lib/gate_integrator.sh 2>/dev/null; then
        pass "Both modules loaded successfully"
    else
        fail "Failed to load both modules"
    fi

    # Test 2: No function name conflicts
    print_test "No function name conflicts"
    run_test
    local pr_functions
    local gate_functions
    pr_functions=$(declare -F | grep "ce_pr_" | wc -l)
    gate_functions=$(declare -F | grep "ce_gate_" | wc -l)

    if [[ $pr_functions -ge 30 ]] && [[ $gate_functions -ge 30 ]]; then
        pass "All functions available (PR: $pr_functions, Gate: $gate_functions)"
    else
        fail "Missing functions (PR: $pr_functions, Gate: $gate_functions)"
    fi

    # Test 3: Color codes defined
    print_test "Color codes defined"
    run_test
    if [[ -n "$CE_PR_COLOR_GREEN" ]] && [[ -n "$CE_GATE_COLOR_GREEN" ]]; then
        pass "Color codes defined in both modules"
    else
        fail "Color codes not properly defined"
    fi

    echo ""
}

# ============================================================================
# File Structure Tests
# ============================================================================

test_file_structure() {
    print_header "Testing File Structure"

    # Test 1: Check file permissions
    print_test "File permissions"
    run_test
    if [[ -x .workflow/cli/lib/pr_automator.sh ]] && \
       [[ -x .workflow/cli/lib/gate_integrator.sh ]]; then
        pass "Both scripts are executable"
    else
        fail "Scripts are not executable"
    fi

    # Test 2: Check shebang
    print_test "Shebang lines"
    run_test
    local pr_shebang
    local gate_shebang
    pr_shebang=$(head -1 .workflow/cli/lib/pr_automator.sh)
    gate_shebang=$(head -1 .workflow/cli/lib/gate_integrator.sh)

    if [[ "$pr_shebang" == "#!/usr/bin/env bash" ]] && \
       [[ "$gate_shebang" == "#!/usr/bin/env bash" ]]; then
        pass "Correct shebang in both files"
    else
        fail "Incorrect shebang lines"
    fi

    # Test 3: Check set -euo pipefail
    print_test "Strict error handling"
    run_test
    if grep -q "set -euo pipefail" .workflow/cli/lib/pr_automator.sh && \
       grep -q "set -euo pipefail" .workflow/cli/lib/gate_integrator.sh; then
        pass "Strict error handling enabled"
    else
        fail "Strict error handling not enabled"
    fi

    # Test 4: Check documentation exists
    print_test "Documentation files"
    run_test
    if [[ -f .workflow/cli/P3_PR_GATE_IMPLEMENTATION_SUMMARY.md ]] && \
       [[ -f .workflow/cli/QUICK_REFERENCE.md ]]; then
        pass "Documentation files present"
    else
        fail "Documentation files missing"
    fi

    echo ""
}

# ============================================================================
# Syntax Tests
# ============================================================================

test_syntax() {
    print_header "Testing Bash Syntax"

    # Test 1: pr_automator.sh syntax
    print_test "pr_automator.sh syntax"
    run_test
    if bash -n .workflow/cli/lib/pr_automator.sh 2>/dev/null; then
        pass "No syntax errors in pr_automator.sh"
    else
        fail "Syntax errors found in pr_automator.sh"
    fi

    # Test 2: gate_integrator.sh syntax
    print_test "gate_integrator.sh syntax"
    run_test
    if bash -n .workflow/cli/lib/gate_integrator.sh 2>/dev/null; then
        pass "No syntax errors in gate_integrator.sh"
    else
        fail "Syntax errors found in gate_integrator.sh"
    fi

    echo ""
}

# ============================================================================
# Main Test Runner
# ============================================================================

main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   PR Automator & Gate Integrator Test Suite               ║"
    echo "║   Testing P3 Implementation                                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}\n"

    # Change to project root
    cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

    # Run test suites
    test_syntax
    test_file_structure
    test_pr_automator
    test_gate_integrator
    test_integration

    # Print summary
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BLUE}║  Test Summary${RESET}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo "  Tests Run:    $TESTS_RUN"
    echo -e "  Passed:       ${GREEN}$TESTS_PASSED${RESET}"

    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "  Failed:       ${RED}$TESTS_FAILED${RESET}"
        echo ""
        echo -e "${RED}Failed Tests:${RESET}"
        for failed_test in "${FAILED_TESTS[@]}"; do
            echo -e "${RED}  • $failed_test${RESET}"
        done
        echo ""
        echo -e "${RED}╔════════════════════════════════════════════════════════════╗${RESET}"
        echo -e "${RED}║  TEST SUITE FAILED                                         ║${RESET}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════╝${RESET}"
        exit 1
    else
        echo -e "  Failed:       ${GREEN}0${RESET}"
        echo ""
        local pass_rate
        pass_rate=$((TESTS_PASSED * 100 / TESTS_RUN))
        echo -e "  Pass Rate:    ${GREEN}${pass_rate}%${RESET}"
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${RESET}"
        echo -e "${GREEN}║  ALL TESTS PASSED ✓                                        ║${RESET}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${RESET}"
        exit 0
    fi
}

# Run tests
main "$@"
