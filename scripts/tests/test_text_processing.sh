#!/usr/bin/env bash
# Unit tests for text processing functions
set -uo pipefail  # Remove -e to allow tests to continue

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/text_processing.sh"

TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

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
    echo "  Expected: [$expected]"
    echo "  Actual: [$actual]"
    ((TESTS_FAILED++))
  fi
}

echo "════════════════════════════════════════"
echo "Text Processing Unit Tests"
echo "════════════════════════════════════════"

# Test code block filtering
echo ""
echo "Testing code block filtering..."

cat > /tmp/test_markdown.md <<'EOF'
Real requirement: Performance testing

Example code:
```bash
echo "Performance example"
```

Another requirement
EOF

filtered=$(strip_code_blocks < /tmp/test_markdown.md)
count=$(echo "$filtered" | grep -c "Performance" || echo "0")
assert_equals "1" "$count" "Code block filtered (only real requirement counted)"

# Test regex escaping
echo ""
echo "Testing regex escaping..."

test_str="Test (payment) \$99.99"
escaped=$(echo "$test_str" | re_escape)
# After escaping, special chars should be escaped
if echo "$escaped" | grep -q '\\\$'; then
  echo "✓ Dollar sign escaped"
  ((TESTS_PASSED++))
  ((TESTS_RUN++))
else
  echo "✗ Dollar sign not escaped"
  ((TESTS_FAILED++))
  ((TESTS_RUN++))
fi

# Test with various special characters
echo ""
echo "Testing special character escaping..."
special_chars='.*+?()[]{}|^\$'
escaped=$(echo "$special_chars" | re_escape)
if [[ "$escaped" == *'\\'* ]]; then
  echo "✓ Special characters escaped"
  ((TESTS_PASSED++))
  ((TESTS_RUN++))
else
  echo "✗ Special characters not escaped properly"
  ((TESTS_FAILED++))
  ((TESTS_RUN++))
fi

# Summary
echo ""
echo "════════════════════════════════════════"
echo "Test Summary"
echo "════════════════════════════════════════"
echo "Total: $TESTS_RUN"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"

rm -f /tmp/test_markdown.md

if [[ $TESTS_FAILED -eq 0 ]]; then
  echo "✅ All tests passed!"
  exit 0
else
  echo "❌ Some tests failed"
  exit 1
fi
