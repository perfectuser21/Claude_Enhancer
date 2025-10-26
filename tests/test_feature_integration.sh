#!/bin/bash
# Test Suite for Feature Integration System
# Tests the complete feature registration and integration mechanism

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly PROJECT_ROOT
REGISTRY_CLI="${PROJECT_ROOT}/scripts/feature_registry_cli.sh"
readonly REGISTRY_CLI
VALIDATOR="${PROJECT_ROOT}/scripts/feature_integration_validator.sh"
readonly VALIDATOR
INTEGRATION="${PROJECT_ROOT}/scripts/feature_phase_integration.sh"
readonly INTEGRATION

# Test results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
GREEN='\033[0;32m'
readonly GREEN
RED='\033[0;31m'
readonly RED
YELLOW='\033[1;33m'
readonly YELLOW
NC='\033[0m'
readonly NC

# ============= Test Utilities =============

test_start() {
    echo -e "\n${YELLOW}TEST:${NC} $1"
    TESTS_RUN=$((TESTS_RUN + 1))
}

test_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-Assertion failed}"

    if [[ "$expected" == "$actual" ]]; then
        test_pass "$message"
    else
        test_fail "$message (expected: $expected, got: $actual)"
    fi
}

assert_file_exists() {
    local file="$1"
    local message="${2:-File should exist}"

    if [[ -f "$file" ]]; then
        test_pass "$message"
    else
        test_fail "$message: $file"
    fi
}

assert_command_succeeds() {
    local command="$1"
    local message="${2:-Command should succeed}"

    if eval "$command" >/dev/null 2>&1; then
        test_pass "$message"
    else
        test_fail "$message: $command"
    fi
}

# ============= Test Cases =============

# Test 1: Registry CLI exists and is executable
test_registry_cli_exists() {
    test_start "Registry CLI exists and is executable"

    assert_file_exists "$REGISTRY_CLI" "Registry CLI script exists"

    if [[ -x "$REGISTRY_CLI" ]]; then
        test_pass "Registry CLI is executable"
    else
        test_fail "Registry CLI is not executable"
    fi
}

# Test 2: Registry CLI help command
test_registry_cli_help() {
    test_start "Registry CLI help command"

    assert_command_succeeds "$REGISTRY_CLI help" "Registry CLI help works"
}

# Test 3: Registry CLI status command
test_registry_cli_status() {
    test_start "Registry CLI status command"

    local output
    output=$($REGISTRY_CLI status 2>&1)

    if echo "$output" | grep -q "Feature Integration System Status"; then
        test_pass "Status command shows system status"
    else
        test_fail "Status command output incorrect"
    fi
}

# Test 4: Registry CLI list command
test_registry_cli_list() {
    test_start "Registry CLI list features"

    local output
    output=$($REGISTRY_CLI list 2>&1)

    if echo "$output" | grep -q "cache_manager"; then
        test_pass "List shows registered features"
    else
        test_fail "List does not show expected features"
    fi
}

# Test 5: Validator exists and is executable
test_validator_exists() {
    test_start "Validator exists and is executable"

    assert_file_exists "$VALIDATOR" "Validator script exists"

    if [[ -x "$VALIDATOR" ]]; then
        test_pass "Validator is executable"
    else
        test_fail "Validator is not executable"
    fi
}

# Test 6: Phase Integration script exists
test_phase_integration_exists() {
    test_start "Phase Integration script exists"

    assert_file_exists "$INTEGRATION" "Phase integration script exists"

    if [[ -x "$INTEGRATION" ]]; then
        test_pass "Phase integration is executable"
    else
        test_fail "Phase integration is not executable"
    fi
}

# Test 7: Feature Registry YAML exists and is valid
test_registry_yaml_exists() {
    test_start "Feature Registry YAML exists and is valid"

    local registry="${PROJECT_ROOT}/.claude/FEATURE_REGISTRY.yaml"
    assert_file_exists "$registry" "Registry YAML exists"

    # Check YAML structure
    if grep -q "^features:" "$registry"; then
        test_pass "Registry has features section"
    else
        test_fail "Registry missing features section"
    fi

    if grep -q "^feature_types:" "$registry"; then
        test_pass "Registry has feature_types section"
    else
        test_fail "Registry missing feature_types section"
    fi
}

# Test 8: Validate a registered feature
test_validate_feature() {
    test_start "Validate registered feature (cache_manager)"

    if $REGISTRY_CLI validate cache_manager >/dev/null 2>&1; then
        test_pass "cache_manager validation succeeds"
    else
        test_fail "cache_manager validation fails"
    fi
}

# Test 9: Integration Template exists
test_integration_template() {
    test_start "Integration Template exists"

    local template="${PROJECT_ROOT}/.claude/FEATURE_INTEGRATION_TEMPLATE.md"
    assert_file_exists "$template" "Integration template exists"
}

# Test 10: Phase integration functions work
test_phase_integration_functions() {
    test_start "Phase integration functions are available"

    # Source the integration script
    # shellcheck source=/dev/null
    source "$INTEGRATION"

    # Check if functions are defined
    if type -t phase1_integration >/dev/null; then
        test_pass "phase1_integration function exists"
    else
        test_fail "phase1_integration function missing"
    fi

    if type -t all_phases_integration >/dev/null; then
        test_pass "all_phases_integration function exists"
    else
        test_fail "all_phases_integration function missing"
    fi
}

# Test 11: Get features for phase
test_get_features_for_phase() {
    test_start "Get features for specific phase"

    # Source the integration script
    # shellcheck source=/dev/null
    source "$INTEGRATION"

    local features
    features=$(get_features_for_phase "4" "replace_review")

    if echo "$features" | grep -q "parallel_review"; then
        test_pass "Found parallel_review for Phase 4"
    else
        test_fail "parallel_review not found for Phase 4"
    fi
}

# Test 12: Feature count matches expected
test_feature_count() {
    test_start "Feature count verification"

    local count
    count=$($REGISTRY_CLI list 2>/dev/null | grep -c "^[a-z_]" || echo 0)

    if [[ "$count" -ge 3 ]]; then
        test_pass "At least 3 features registered"
    else
        test_fail "Less than 3 features registered (found: $count)"
    fi
}

# ============= Test Runner =============

run_all_tests() {
    echo "╔════════════════════════════════════════════╗"
    echo "║  Feature Integration System Test Suite     ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    echo "Running tests..."

    # Core component tests
    test_registry_cli_exists
    test_registry_cli_help
    test_registry_cli_status
    test_registry_cli_list
    test_validator_exists
    test_phase_integration_exists
    test_registry_yaml_exists

    # Functionality tests
    test_validate_feature
    test_integration_template
    test_phase_integration_functions
    test_get_features_for_phase
    test_feature_count

    # Summary
    echo ""
    echo "════════════════════════════════════════════"
    echo "Test Results:"
    echo "  Tests run: $TESTS_RUN"
    echo -e "  Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "  Failed: ${RED}$TESTS_FAILED${NC}"

    local pass_rate
    pass_rate=$((TESTS_PASSED * 100 / TESTS_RUN))
    echo "  Pass rate: ${pass_rate}%"
    echo ""

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED${NC}"
        return 1
    fi
}

# Run tests
run_all_tests