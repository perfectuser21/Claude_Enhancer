#!/usr/bin/env bash
# Unit tests for ID mapping functions
set -uo pipefail  # Remove -e to allow tests to continue after failures

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/id_mapping.sh"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper
assert_equals() {
  local expected="$1"
  local actual="$2"
  local test_name="$3"

  ((TESTS_RUN++))

  if [[ "$expected" == "$actual" ]]; then
    echo "✓ $test_name"
    ((TESTS_PASSED++))
  else
    echo "✗ $test_name"
    echo "  Expected: $expected"
    echo "  Actual: $actual"
    ((TESTS_FAILED++))
  fi
}

assert_true() {
  local command="$1"
  local test_name="$2"

  ((TESTS_RUN++))

  if eval "$command" >/dev/null 2>&1; then
    echo "✓ $test_name"
    ((TESTS_PASSED++))
  else
    echo "✗ $test_name"
    ((TESTS_FAILED++))
  fi
}

echo "════════════════════════════════════════"
echo "ID Mapping Unit Tests"
echo "════════════════════════════════════════"

# Test ID generation
echo ""
echo "Testing ID generation..."
result=$(generate_plan_id 4 1)
assert_equals "PLAN-W4-001" "$result" "generate_plan_id(4, 1)"

result=$(generate_checklist_id 4 5)
assert_equals "CL-W4-005" "$result" "generate_checklist_id(4, 5)"

result=$(generate_plan_id 12 99)
assert_equals "PLAN-W12-099" "$result" "generate_plan_id(12, 99)"

# Test ID format validation
echo ""
echo "Testing ID format validation..."
assert_true 'validate_id_format "PLAN-W4-001" "plan"' "Valid plan ID accepted"
assert_true 'validate_id_format "CL-W4-005" "checklist"' "Valid checklist ID accepted"
assert_true '! validate_id_format "INVALID-ID" "plan"' "Invalid ID rejected"
assert_true '! validate_id_format "PLAN-W4-1" "plan"' "Malformed plan ID rejected (missing padding)"
assert_true '! validate_id_format "CL-4-005" "checklist"' "Malformed checklist ID rejected (missing W)"

# Test comment parsing
echo ""
echo "Testing comment parsing..."
comment='<!-- id: CL-W4-005; evidence: EVID-2025W44-015 -->'
result=$(extract_checklist_id_from_comment "$comment")
assert_equals "CL-W4-005" "$result" "Extract checklist ID from comment"

result=$(extract_evidence_id_from_comment "$comment")
assert_equals "EVID-2025W44-015" "$result" "Extract evidence ID from comment"

# Test week number extraction
echo ""
echo "Testing week extraction..."
result=$(extract_week_number "## Week 4: KPI Dashboard")
assert_equals "4" "$result" "Extract week from section header"

result=$(extract_week_number "### Week 12: Final Testing")
assert_equals "12" "$result" "Extract week from subsection header"

# Summary
echo ""
echo "════════════════════════════════════════"
echo "Test Summary"
echo "════════════════════════════════════════"
echo "Total: $TESTS_RUN"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
  echo "✅ All tests passed!"
  exit 0
else
  echo "❌ Some tests failed"
  exit 1
fi
