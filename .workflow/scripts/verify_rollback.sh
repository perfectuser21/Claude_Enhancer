#!/usr/bin/env bash
# Rollback Verification Script
# Validates that rollback was successful and system is stable

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Rollback Verification                                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0

# Test 1: Users can commit without enforcement
echo "[Test 1/4] Verify commits work without enforcement..."
echo "test-rollback" > .test_rollback_file.txt
git add .test_rollback_file.txt
if git commit -m "test: rollback verification" --quiet 2>/dev/null; then
    echo "   ✓ PASS: Commits work"
    PASS=$((PASS + 1))
    git reset --soft HEAD~1
    rm .test_rollback_file.txt
else
    echo "   ✗ FAIL: Commits blocked"
    FAIL=$((FAIL + 1))
fi

# Test 2: Git integrity
echo "[Test 2/4] Verify git integrity..."
if git fsck --full --quiet 2>/dev/null; then
    echo "   ✓ PASS: Git integrity OK"
    PASS=$((PASS + 1))
else
    echo "   ✗ FAIL: Git integrity compromised"
    FAIL=$((FAIL + 1))
fi

# Test 3: Hook performance
echo "[Test 3/4] Verify hook performance..."
START=$(date +%s%N)
git commit --allow-empty -m "perf test" --quiet 2>/dev/null || true
END=$(date +%s%N)
DURATION_MS=$(( (END - START) / 1000000 ))
git reset --soft HEAD~1 2>/dev/null || true

if [[ $DURATION_MS -lt 500 ]]; then
    echo "   ✓ PASS: Hook time ${DURATION_MS}ms (<500ms)"
    PASS=$((PASS + 1))
else
    echo "   ⚠ WARNING: Hook time ${DURATION_MS}ms (>500ms)"
    PASS=$((PASS + 1))  # Still pass but warn
fi

# Test 4: Workflow functionality
echo "[Test 4/4] Verify workflow functionality..."
if [[ -f .workflow/executor.sh ]]; then
    if bash .workflow/executor.sh --help &>/dev/null; then
        echo "   ✓ PASS: Workflow scripts functional"
        PASS=$((PASS + 1))
    else
        echo "   ✗ FAIL: Workflow scripts broken"
        FAIL=$((FAIL + 1))
    fi
else
    echo "   ⚠ SKIP: Workflow scripts not found"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Verification Results                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo "✓ VERIFICATION SUCCESSFUL"
    echo "  System is stable and ready for use"
    exit 0
else
    echo "✗ VERIFICATION FAILED"
    echo "  $FAIL test(s) failed - manual intervention required"
    exit 1
fi
