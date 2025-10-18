#!/bin/bash
# Static Checks - Simplified
set -euo pipefail

echo "=== Static Checks ==="
echo ""

TOTAL=0
PASSED=0
FAILED=0

# Shell syntax
echo "Shell Syntax Check"
SCRIPTS=$(find scripts -name "*.sh" 2>/dev/null | head -10)
for script in $SCRIPTS; do
  if bash -n "$script" 2>/dev/null; then
    echo "  ✓ $script"
    PASSED=$((PASSED+1))
  else
    echo "  ✗ $script"
    FAILED=$((FAILED+1))
  fi
  TOTAL=$((TOTAL+1))
done

# Summary
echo ""
echo "=== Summary ==="
echo "Total:  $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
  echo ""
  echo "✅ ALL CHECKS PASSED"
  exit 0
else
  echo ""
  echo "❌ SOME CHECKS FAILED"
  exit 1
fi
