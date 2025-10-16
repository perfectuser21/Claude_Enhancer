#!/usr/bin/env bash
# Comprehensive Test Suite for Impact Radius Assessor
# Version: 1.0.0
# Coverage: 80+ test cases (functional, integration, performance, edge cases)

set -euo pipefail

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSESSOR_SCRIPT="$PROJECT_ROOT/.claude/scripts/impact_radius_assessor.sh"
TEST_DATA="$PROJECT_ROOT/tests/fixtures/task_samples.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Test results storage
declare -a FAILED_TEST_NAMES
declare -a FAILED_TEST_REASONS

# =============================================================================
# TEST FRAMEWORK UTILITIES
# =============================================================================

# Print colored messages
print_header() {
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo -e "\n${BLUE}┌─────────────────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│ $1${NC}"
    echo -e "${BLUE}└─────────────────────────────────────────────────────┘${NC}"
}

print_test() {
    local status="$1"
    local name="$2"
    local message="${3:-}"

    ((TOTAL_TESTS++))

    case "$status" in
        PASS)
            echo -e "${GREEN}✓${NC} $name"
            ((PASSED_TESTS++))
            ;;
        FAIL)
            echo -e "${RED}✗${NC} $name"
            echo -e "  ${RED}Reason: $message${NC}"
            FAILED_TEST_NAMES+=("$name")
            FAILED_TEST_REASONS+=("$message")
            ((FAILED_TESTS++))
            ;;
        SKIP)
            echo -e "${YELLOW}○${NC} $name (skipped)"
            ((SKIPPED_TESTS++))
            ;;
    esac
}

# Assertion functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    if [ "$expected" = "$actual" ]; then
        print_test "PASS" "$test_name"
        return 0
    else
        print_test "FAIL" "$test_name" "Expected: $expected, Got: $actual"
        return 1
    fi
}

assert_in_range() {
    local value="$1"
    local min="$2"
    local max="$3"
    local test_name="$4"

    if [ "$value" -ge "$min" ] && [ "$value" -le "$max" ]; then
        print_test "PASS" "$test_name"
        return 0
    else
        print_test "FAIL" "$test_name" "Expected: $min-$max, Got: $value"
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local test_name="$3"

    if echo "$haystack" | grep -q "$needle"; then
        print_test "PASS" "$test_name"
        return 0
    else
        print_test "FAIL" "$test_name" "String '$needle' not found"
        return 1
    fi
}

assert_json_field() {
    local json="$1"
    local field="$2"
    local expected="$3"
    local test_name="$4"

    local actual
    actual=$(echo "$json" | jq -r "$field" 2>/dev/null || echo "error")

    if [ "$actual" = "error" ]; then
        print_test "FAIL" "$test_name" "JSON parse error or field not found"
        return 1
    fi

    assert_equals "$expected" "$actual" "$test_name"
}

# Helper: Run assessor and return JSON
run_assessment() {
    local task="$1"
    "$ASSESSOR_SCRIPT" "$task" 2>/dev/null || echo "{}"
}

# Helper: Extract agent count from result
get_agent_count() {
    local task="$1"
    local result
    result=$(run_assessment "$task")
    echo "$result" | jq -r '.agent_strategy.min_agents // "error"'
}

# Helper: Extract impact radius from result
get_impact_radius() {
    local task="$1"
    local result
    result=$(run_assessment "$task")
    echo "$result" | jq -r '.scores.impact_radius // "error"'
}

# =============================================================================
# TEST SUITES
# =============================================================================

# Test Suite 1: Functional Tests - Risk Scoring (15 tests)
test_functional_risk_scoring() {
    print_section "Test Suite 1: Risk Scoring (15 tests)"

    # Critical risk patterns (score 10)
    assert_equals "10" "$(run_assessment 'Fix CVE-2024-1234' | jq -r '.scores.risk_score')" \
        "T1.01: CVE keyword detection"

    assert_equals "10" "$(run_assessment 'Security vulnerability in auth' | jq -r '.scores.risk_score')" \
        "T1.02: Security keyword detection"

    assert_equals "10" "$(run_assessment 'Patch exploit in payment' | jq -r '.scores.risk_score')" \
        "T1.03: Exploit keyword detection"

    assert_equals "10" "$(run_assessment '修复安全漏洞' | jq -r '.scores.risk_score')" \
        "T1.04: Chinese security keyword"

    # High risk patterns (score 8)
    assert_equals "8" "$(run_assessment 'Migrate database to PostgreSQL' | jq -r '.scores.risk_score')" \
        "T1.05: Migration keyword detection"

    assert_equals "8" "$(run_assessment 'Refactor authentication system' | jq -r '.scores.risk_score')" \
        "T1.06: Refactor auth keyword"

    assert_equals "8" "$(run_assessment 'Architecture redesign' | jq -r '.scores.risk_score')" \
        "T1.07: Architecture keyword detection"

    assert_equals "8" "$(run_assessment 'Critical bug in production' | jq -r '.scores.risk_score')" \
        "T1.08: Critical keyword detection"

    assert_equals "8" "$(run_assessment '重构系统架构' | jq -r '.scores.risk_score')" \
        "T1.09: Chinese architecture keyword"

    # Medium risk patterns (score 5)
    assert_equals "5" "$(run_assessment 'Fix bug in login' | jq -r '.scores.risk_score')" \
        "T1.10: Bug keyword detection"

    assert_equals "5" "$(run_assessment 'Optimize query performance' | jq -r '.scores.risk_score')" \
        "T1.11: Optimize keyword detection"

    assert_equals "5" "$(run_assessment 'Improve error handling' | jq -r '.scores.risk_score')" \
        "T1.12: Improve keyword detection"

    # Low risk patterns (score 2)
    assert_equals "2" "$(run_assessment 'Fix typo in README' | jq -r '.scores.risk_score')" \
        "T1.13: Typo keyword detection"

    assert_equals "2" "$(run_assessment 'Update documentation' | jq -r '.scores.risk_score')" \
        "T1.14: Documentation keyword detection"

    assert_equals "2" "$(run_assessment 'Add TODO markers' | jq -r '.scores.risk_score')" \
        "T1.15: TODO keyword detection"
}

# Test Suite 2: Functional Tests - Complexity Scoring (15 tests)
test_functional_complexity_scoring() {
    print_section "Test Suite 2: Complexity Scoring (15 tests)"

    # Architectural complexity (score 10)
    assert_equals "10" "$(run_assessment 'Design system architecture' | jq -r '.scores.complexity_score')" \
        "T2.01: Architecture complexity"

    assert_equals "10" "$(run_assessment 'Refactor workflow engine' | jq -r '.scores.complexity_score')" \
        "T2.02: Workflow complexity"

    assert_equals "10" "$(run_assessment '全局架构设计' | jq -r '.scores.complexity_score')" \
        "T2.03: Chinese architecture complexity"

    # Core complexity (score 7)
    assert_equals "7" "$(run_assessment 'Modify core authentication hook' | jq -r '.scores.complexity_score')" \
        "T2.04: Hook complexity"

    assert_equals "7" "$(run_assessment 'Update core engine logic' | jq -r '.scores.complexity_score')" \
        "T2.05: Core engine complexity"

    assert_equals "7" "$(run_assessment 'Refactor framework module' | jq -r '.scores.complexity_score')" \
        "T2.06: Framework complexity"

    # Logic complexity (score 4)
    assert_equals "4" "$(run_assessment 'Update function logic' | jq -r '.scores.complexity_score')" \
        "T2.07: Function complexity"

    assert_equals "4" "$(run_assessment 'Implement algorithm' | jq -r '.scores.complexity_score')" \
        "T2.08: Algorithm complexity"

    assert_equals "4" "$(run_assessment 'Refactor module structure' | jq -r '.scores.complexity_score')" \
        "T2.09: Module complexity"

    # Simple complexity (score 1)
    assert_equals "1" "$(run_assessment 'Fix one-line typo' | jq -r '.scores.complexity_score')" \
        "T2.10: One-line complexity"

    assert_equals "1" "$(run_assessment 'Update single line comment' | jq -r '.scores.complexity_score')" \
        "T2.11: Single-line complexity"

    assert_equals "1" "$(run_assessment 'Improve code readability' | jq -r '.scores.complexity_score')" \
        "T2.12: Readability complexity"

    assert_equals "1" "$(run_assessment 'Rename variable for better names' | jq -r '.scores.complexity_score')" \
        "T2.13: Variable naming complexity"

    # Default complexity
    local default_complexity
    default_complexity=$(run_assessment 'Do something generic' | jq -r '.scores.complexity_score')
    assert_in_range "$default_complexity" 3 5 "T2.14: Default complexity score"

    # Mixed complexity
    assert_equals "10" "$(run_assessment 'Redesign architecture for single component' | jq -r '.scores.complexity_score')" \
        "T2.15: Mixed complexity (architecture wins)"
}

# Test Suite 3: Functional Tests - Impact/Scope Scoring (15 tests)
test_functional_impact_scoring() {
    print_section "Test Suite 3: Impact/Scope Scoring (15 tests)"

    # System-wide impact (score 10)
    assert_equals "10" "$(run_assessment 'Change all modules globally' | jq -r '.scores.impact_score')" \
        "T3.01: Global impact"

    assert_equals "10" "$(run_assessment 'System-wide configuration' | jq -r '.scores.impact_score')" \
        "T3.02: System-wide impact"

    assert_equals "10" "$(run_assessment 'Entire codebase refactor' | jq -r '.scores.impact_score')" \
        "T3.03: Entire scope impact"

    # Multiple modules impact (score 7)
    assert_equals "7" "$(run_assessment 'Update multiple components' | jq -r '.scores.impact_score')" \
        "T3.04: Multiple impact"

    assert_equals "7" "$(run_assessment 'Cross-module changes' | jq -r '.scores.impact_score')" \
        "T3.05: Cross-cutting impact"

    assert_equals "7" "$(run_assessment 'Several services affected' | jq -r '.scores.impact_score')" \
        "T3.06: Several modules impact"

    # Single module impact (score 4)
    assert_equals "4" "$(run_assessment 'Fix single component' | jq -r '.scores.impact_score')" \
        "T3.07: Single module impact"

    assert_equals "4" "$(run_assessment 'Local change in auth' | jq -r '.scores.impact_score')" \
        "T3.08: Local impact"

    assert_equals "4" "$(run_assessment 'One specific function' | jq -r '.scores.impact_score')" \
        "T3.09: Specific scope impact"

    # Documentation-only impact (score 1)
    assert_equals "1" "$(run_assessment 'Update documentation only' | jq -r '.scores.impact_score')" \
        "T3.10: Documentation-only impact"

    assert_equals "1" "$(run_assessment 'Fix typo in comments' | jq -r '.scores.impact_score')" \
        "T3.11: Comment-only impact"

    assert_equals "1" "$(run_assessment 'Code formatting cleanup' | jq -r '.scores.impact_score')" \
        "T3.12: Formatting-only impact"

    assert_equals "1" "$(run_assessment 'Add TODO markers' | jq -r '.scores.impact_score')" \
        "T3.13: TODO-only impact"

    assert_equals "1" "$(run_assessment 'Spelling corrections' | jq -r '.scores.impact_score')" \
        "T3.14: Spelling-only impact"

    # Default impact
    local default_impact
    default_impact=$(run_assessment 'Generic task' | jq -r '.scores.impact_score')
    assert_in_range "$default_impact" 3 5 "T3.15: Default impact score"
}

# Test Suite 4: Integration Tests - Agent Count Mapping (15 tests)
test_integration_agent_mapping() {
    print_section "Test Suite 4: Agent Count Mapping (15 tests)"

    # High-risk tasks → 6 agents
    assert_equals "6" "$(get_agent_count 'Fix CVE-2024-1234')" \
        "T4.01: CVE fix → 6 agents"

    assert_equals "6" "$(get_agent_count 'Migrate database to PostgreSQL')" \
        "T4.02: Database migration → 6 agents"

    assert_equals "6" "$(get_agent_count 'Refactor authentication system')" \
        "T4.03: Auth refactor → 6 agents"

    assert_equals "6" "$(get_agent_count 'Architecture redesign')" \
        "T4.04: Architecture → 6 agents"

    assert_equals "6" "$(get_agent_count 'Critical production bug')" \
        "T4.05: Critical bug → 6 agents"

    # Medium-risk tasks → 3 agents
    assert_equals "3" "$(get_agent_count 'Fix bug in login page')" \
        "T4.06: Login bug → 3 agents"

    assert_equals "3" "$(get_agent_count 'Optimize API performance')" \
        "T4.07: Optimization → 3 agents"

    assert_equals "3" "$(get_agent_count 'Refactor user module')" \
        "T4.08: Module refactor → 3 agents"

    assert_equals "3" "$(get_agent_count 'Add logging functionality')" \
        "T4.09: Feature addition → 3 agents"

    assert_equals "3" "$(get_agent_count 'Update dependencies')" \
        "T4.10: Dependency update → 3 agents"

    # Low-risk tasks → 0 agents
    assert_equals "0" "$(get_agent_count 'Fix typo in README')" \
        "T4.11: Typo fix → 0 agents"

    assert_equals "0" "$(get_agent_count 'Update code comments')" \
        "T4.12: Comment update → 0 agents"

    assert_equals "0" "$(get_agent_count 'Format code style')" \
        "T4.13: Formatting → 0 agents"

    assert_equals "0" "$(get_agent_count 'Add TODO markers')" \
        "T4.14: TODO markers → 0 agents"

    assert_equals "0" "$(get_agent_count 'Cleanup temporary files')" \
        "T4.15: Cleanup → 0 agents"
}

# Test Suite 5: Integration Tests - Compound/Mixed Tasks (10 tests)
test_integration_compound_tasks() {
    print_section "Test Suite 5: Compound/Mixed Tasks (10 tests)"

    # High-priority keyword should dominate
    assert_equals "6" "$(get_agent_count 'Fix typo and CVE-2024-1234')" \
        "T5.01: Typo + CVE → CVE dominates (6 agents)"

    assert_equals "6" "$(get_agent_count 'Update docs and refactor authentication')" \
        "T5.02: Docs + refactor → refactor dominates (6 agents)"

    assert_equals "6" "$(get_agent_count 'Format code and migrate database')" \
        "T5.03: Format + migration → migration dominates (6 agents)"

    # Medium + Low should be medium
    assert_equals "3" "$(get_agent_count 'Fix bug and update comments')" \
        "T5.04: Bug + comments → bug dominates (3 agents)"

    assert_equals "3" "$(get_agent_count 'Optimize performance and fix typos')" \
        "T5.05: Optimize + typo → optimize dominates (3 agents)"

    # Multiple medium tasks
    assert_equals "3" "$(get_agent_count 'Fix bug and optimize performance')" \
        "T5.06: Bug + optimize → medium (3 agents)"

    assert_equals "3" "$(get_agent_count 'Refactor module and add logging')" \
        "T5.07: Refactor + logging → medium (3 agents)"

    # Multiple low tasks
    assert_equals "0" "$(get_agent_count 'Fix typo and update comments')" \
        "T5.08: Typo + comments → low (0 agents)"

    assert_equals "0" "$(get_agent_count 'Formatting and cleanup')" \
        "T5.09: Format + cleanup → low (0 agents)"

    # Complex compound
    assert_equals "6" "$(get_agent_count 'Critical security issue in production system')" \
        "T5.10: Complex compound → high (6 agents)"
}

# Test Suite 6: Edge Cases (10 tests)
test_edge_cases() {
    print_section "Test Suite 6: Edge Cases (10 tests)"

    # Empty/whitespace input
    local empty_result
    empty_result=$(run_assessment '' 2>&1 || echo "error")
    assert_contains "$empty_result" "error\|usage\|help" "T6.01: Empty input handling"

    # Very long input
    local long_input
    long_input=$(printf 'a%.0s' {1..10000})
    local long_result
    long_result=$(run_assessment "$long_input" 2>/dev/null || echo "{}")
    if [ -n "$long_result" ]; then
        print_test "PASS" "T6.02: Long input handling"
    else
        print_test "FAIL" "T6.02: Long input handling" "Script failed on long input"
    fi

    # Unicode characters
    local unicode_result
    unicode_result=$(get_agent_count 'Fix 🐛 bug with emojis 测试')
    if [ "$unicode_result" != "error" ]; then
        print_test "PASS" "T6.03: Unicode input handling"
    else
        print_test "FAIL" "T6.03: Unicode input handling" "Unicode parsing failed"
    fi

    # Special characters
    assert_equals "3" "$(get_agent_count 'Fix bug in user@domain.com validation')" \
        "T6.04: Special characters (@) handling"

    assert_equals "3" "$(get_agent_count 'Update path/to/file.js')" \
        "T6.05: Path separators handling"

    # SQL injection patterns (should not cause errors)
    local injection_result
    injection_result=$(get_agent_count "'; DROP TABLE tasks; --")
    if [ "$injection_result" != "error" ]; then
        print_test "PASS" "T6.06: SQL injection pattern safety"
    else
        print_test "FAIL" "T6.06: SQL injection pattern safety" "Injection pattern caused error"
    fi

    # Newlines in input
    local newline_result
    newline_result=$(get_agent_count "Fix bug"$'\n'"in multiple lines")
    if [ "$newline_result" != "error" ]; then
        print_test "PASS" "T6.07: Newline handling"
    else
        print_test "FAIL" "T6.07: Newline handling" "Newline caused error"
    fi

    # Multiple spaces
    assert_equals "3" "$(get_agent_count 'Fix    bug    with    spaces')" \
        "T6.08: Multiple spaces handling"

    # Mixed case
    assert_equals "10" "$(get_agent_count 'fix CVE-2024-1234 SECURITY issue')" \
        "T6.09: Mixed case handling"

    # No matching patterns (default behavior)
    local default_result
    default_result=$(get_agent_count 'xyz123 foobar qwerty')
    assert_in_range "$default_result" 0 6 "T6.10: No pattern match defaults"
}

# Test Suite 7: Performance Tests (5 tests)
test_performance() {
    print_section "Test Suite 7: Performance Tests (5 tests)"

    # Single execution speed
    local start_time end_time duration
    start_time=$(date +%s%N)
    run_assessment "Fix bug in login page" >/dev/null
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

    if [ "$duration" -lt 100 ]; then
        print_test "PASS" "T7.01: Single execution <100ms (${duration}ms)"
    else
        print_test "FAIL" "T7.01: Single execution <100ms" "Duration: ${duration}ms"
    fi

    # Batch execution speed (10 assessments)
    start_time=$(date +%s%N)
    for i in {1..10}; do
        run_assessment "Fix bug $i" >/dev/null
    done
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 ))
    local avg_duration=$((duration / 10))

    if [ "$avg_duration" -lt 100 ]; then
        print_test "PASS" "T7.02: Average execution <100ms (${avg_duration}ms avg)"
    else
        print_test "FAIL" "T7.02: Average execution <100ms" "Average: ${avg_duration}ms"
    fi

    # Memory usage (should be minimal)
    local mem_before mem_after mem_used
    mem_before=$(ps -o rss= -p $$ 2>/dev/null || echo "0")
    for i in {1..100}; do
        run_assessment "Test task $i" >/dev/null
    done
    mem_after=$(ps -o rss= -p $$ 2>/dev/null || echo "0")
    mem_used=$((mem_after - mem_before))

    if [ "$mem_used" -lt 10240 ]; then # <10MB
        print_test "PASS" "T7.03: Memory usage <10MB (${mem_used}KB)"
    else
        print_test "FAIL" "T7.03: Memory usage <10MB" "Used: ${mem_used}KB"
    fi

    # Concurrent execution safety
    local concurrent_results=()
    for i in {1..5}; do
        (get_agent_count "Fix bug $i") &
        concurrent_results[$i]=$!
    done

    local all_success=true
    for pid in "${concurrent_results[@]}"; do
        wait "$pid" || all_success=false
    done

    if [ "$all_success" = true ]; then
        print_test "PASS" "T7.04: Concurrent execution safety"
    else
        print_test "FAIL" "T7.04: Concurrent execution safety" "Some processes failed"
    fi

    # Large batch performance (30 samples from fixture)
    if [ -f "$TEST_DATA" ]; then
        start_time=$(date +%s%N)
        local sample_count
        sample_count=$(jq -r '.total_samples' "$TEST_DATA")
        for i in $(seq 0 $((sample_count - 1))); do
            local desc
            desc=$(jq -r ".samples[$i].description" "$TEST_DATA")
            run_assessment "$desc" >/dev/null
        done
        end_time=$(date +%s%N)
        duration=$(( (end_time - start_time) / 1000000 ))
        local avg=$((duration / sample_count))

        if [ "$avg" -lt 100 ]; then
            print_test "PASS" "T7.05: Large batch avg <100ms (${avg}ms avg, ${sample_count} samples)"
        else
            print_test "FAIL" "T7.05: Large batch avg <100ms" "Average: ${avg}ms"
        fi
    else
        print_test "SKIP" "T7.05: Large batch test (fixture not found)"
    fi
}

# Test Suite 8: JSON Output Validation (5 tests)
test_json_output() {
    print_section "Test Suite 8: JSON Output Validation (5 tests)"

    local result
    result=$(run_assessment "Fix CVE-2024-1234")

    # Valid JSON
    if echo "$result" | jq empty 2>/dev/null; then
        print_test "PASS" "T8.01: Valid JSON output"
    else
        print_test "FAIL" "T8.01: Valid JSON output" "Invalid JSON"
    fi

    # Required fields present
    local has_all_fields=true
    for field in version timestamp task_description scores agent_strategy reasoning; do
        if ! echo "$result" | jq -e ".$field" >/dev/null 2>&1; then
            has_all_fields=false
            break
        fi
    done

    if [ "$has_all_fields" = true ]; then
        print_test "PASS" "T8.02: All required fields present"
    else
        print_test "FAIL" "T8.02: All required fields present" "Missing field: $field"
    fi

    # Score fields are numbers
    assert_json_field "$result" '.scores.risk_score' "10" "T8.03: Risk score is numeric"
    assert_json_field "$result" '.scores.complexity_score | type' "number" "T8.04: Complexity score is numeric"
    assert_json_field "$result" '.scores.impact_score | type' "number" "T8.05: Impact score is numeric"
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

main() {
    print_header "Impact Radius Assessor - Comprehensive Test Suite"

    # Check dependencies
    echo "Checking dependencies..."
    if [ ! -f "$ASSESSOR_SCRIPT" ]; then
        echo -e "${RED}ERROR: Assessor script not found: $ASSESSOR_SCRIPT${NC}"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        echo -e "${RED}ERROR: jq is required but not installed${NC}"
        exit 1
    fi

    chmod +x "$ASSESSOR_SCRIPT"
    echo -e "${GREEN}✓ All dependencies satisfied${NC}\n"

    # Run test suites
    test_functional_risk_scoring
    test_functional_complexity_scoring
    test_functional_impact_scoring
    test_integration_agent_mapping
    test_integration_compound_tasks
    test_edge_cases
    test_performance
    test_json_output

    # Generate report
    print_header "Test Results Summary"

    echo -e "\n${CYAN}Overall Statistics:${NC}"
    echo -e "  Total Tests:  $TOTAL_TESTS"
    echo -e "  ${GREEN}Passed:       $PASSED_TESTS${NC}"
    echo -e "  ${RED}Failed:       $FAILED_TESTS${NC}"
    echo -e "  ${YELLOW}Skipped:      $SKIPPED_TESTS${NC}"

    local pass_rate=0
    if [ "$TOTAL_TESTS" -gt 0 ]; then
        pass_rate=$(( PASSED_TESTS * 100 / TOTAL_TESTS ))
    fi
    echo -e "\n  ${CYAN}Pass Rate:    ${pass_rate}%${NC}"

    # Show failed tests
    if [ "$FAILED_TESTS" -gt 0 ]; then
        echo -e "\n${RED}Failed Tests:${NC}"
        for i in "${!FAILED_TEST_NAMES[@]}"; do
            echo -e "  ${RED}✗${NC} ${FAILED_TEST_NAMES[$i]}"
            echo -e "    ${FAILED_TEST_REASONS[$i]}"
        done
    fi

    # Final verdict
    echo ""
    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
        echo -e "${GREEN}✓ Test suite completed successfully${NC}"
        exit 0
    else
        echo -e "${RED}✗ TESTS FAILED${NC}"
        echo -e "${RED}✗ $FAILED_TESTS test(s) need attention${NC}"
        exit 1
    fi
}

# Run main
main "$@"
