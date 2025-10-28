#!/usr/bin/env bash
# Run all Anti-Hollow Gate tests
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Anti-Hollow Gate v8.2 - Test Suite                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

TOTAL_PASSED=0
TOTAL_FAILED=0

# Run each test suite
for test_script in "$SCRIPT_DIR"/test_*.sh; do
  if [[ -f "$test_script" ]]; then
    echo "Running $(basename "$test_script")..."
    if bash "$test_script"; then
      ((TOTAL_PASSED++))
    else
      ((TOTAL_FAILED++))
    fi
    echo ""
  fi
done

# Summary
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Overall Test Summary                                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo "Test suites passed: $TOTAL_PASSED"
echo "Test suites failed: $TOTAL_FAILED"

if [[ $TOTAL_FAILED -eq 0 ]]; then
  echo "✅ All test suites passed!"
  exit 0
else
  echo "❌ Some test suites failed"
  exit 1
fi
