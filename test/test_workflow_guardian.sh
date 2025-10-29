#!/usr/bin/env bash
# Test script for workflow_guardian.sh zero-exception policy
# Verifies that all branches require Phase 1 documents

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Test: Workflow Guardian - Zero Exception Policy         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: docs branch without Phase 1 docs → should be BLOCKED
test_docs_branch_without_phase1() {
  echo "[Test 1] docs branch without Phase 1 → should BLOCK"

  # Save current branch
  ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)

  # Create test branch
  git checkout -b docs/test-exemption-removal 2>/dev/null || git checkout docs/test-exemption-removal

  # Make a change
  echo "test change" >> README.md
  git add README.md

  # Run workflow_guardian (capture output, allow it to fail)
  set +e
  OUTPUT=$(bash scripts/workflow_guardian.sh 2>&1)
  EXIT_CODE=$?
  set -e

  if [[ $EXIT_CODE -ne 0 ]] && echo "$OUTPUT" | grep -q "Phase 1 文档缺失"; then
    echo "✅ PASS: docs branch correctly BLOCKED without Phase 1"
    ((TESTS_PASSED++))
  else
    echo "❌ FAIL: docs branch was NOT blocked!"
    echo "Exit code: $EXIT_CODE"
    echo "Output snippet: $(echo "$OUTPUT" | grep -i "phase 1" | head -1)"
    ((TESTS_FAILED++))
  fi

  # Cleanup
  git reset HEAD README.md
  git checkout .
  git checkout "$ORIGINAL_BRANCH"
  git branch -D docs/test-exemption-removal 2>/dev/null || true

  echo ""
}

# Test 2: feature branch without Phase 1 docs → should be BLOCKED
test_feature_branch_without_phase1() {
  echo "[Test 2] feature branch without Phase 1 → should BLOCK"

  ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)

  git checkout -b feature/test-enforcement 2>/dev/null || git checkout feature/test-enforcement

  echo "test" >> scripts/test_dummy.sh
  git add scripts/test_dummy.sh

  set +e
  OUTPUT=$(bash scripts/workflow_guardian.sh 2>&1)
  EXIT_CODE=$?
  set -e

  if [[ $EXIT_CODE -ne 0 ]] && echo "$OUTPUT" | grep -q "Phase 1 文档缺失"; then
    echo "✅ PASS: feature branch correctly BLOCKED without Phase 1"
    ((TESTS_PASSED++))
  else
    echo "❌ FAIL: feature branch was NOT blocked!"
    echo "Exit code: $EXIT_CODE"
    ((TESTS_FAILED++))
  fi

  # Cleanup
  git reset HEAD scripts/test_dummy.sh
  rm -f scripts/test_dummy.sh
  git checkout "$ORIGINAL_BRANCH"
  git branch -D feature/test-enforcement 2>/dev/null || true

  echo ""
}

# Test 3: With Phase 1 docs → should be ALLOWED
test_with_phase1_docs() {
  echo "[Test 3] With complete Phase 1 docs → should ALLOW"

  ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)

  git checkout -b feature/test-with-docs 2>/dev/null || git checkout feature/test-with-docs

  # Create Phase 1 docs
  mkdir -p docs .workflow
  touch docs/P1_DISCOVERY.md
  touch docs/PLAN.md
  touch .workflow/ACCEPTANCE_CHECKLIST.md
  touch .workflow/IMPACT_ASSESSMENT.md

  echo "test" >> scripts/test_dummy.sh
  git add .

  set +e
  OUTPUT=$(bash scripts/workflow_guardian.sh 2>&1)
  EXIT_CODE=$?
  set -e

  if [[ $EXIT_CODE -eq 0 ]] && echo "$OUTPUT" | grep -q "Phase 1文档齐全"; then
    echo "✅ PASS: With Phase 1 docs correctly ALLOWED"
    ((TESTS_PASSED++))
  else
    echo "❌ FAIL: With Phase 1 docs was BLOCKED!"
    echo "Exit code: $EXIT_CODE"
    ((TESTS_FAILED++))
  fi

  # Cleanup
  git reset HEAD .
  rm -f docs/P1_DISCOVERY.md docs/PLAN.md
  rm -f .workflow/ACCEPTANCE_CHECKLIST.md .workflow/IMPACT_ASSESSMENT.md
  rm -f scripts/test_dummy.sh
  git checkout "$ORIGINAL_BRANCH"
  git branch -D feature/test-with-docs 2>/dev/null || true

  echo ""
}

# Run all tests
test_docs_branch_without_phase1
test_feature_branch_without_phase1
test_with_phase1_docs

# Summary
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Test Summary                                             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
  echo "✅ All tests passed! Zero-exception policy verified."
  exit 0
else
  echo "❌ Some tests failed. Policy not enforced correctly."
  exit 1
fi
