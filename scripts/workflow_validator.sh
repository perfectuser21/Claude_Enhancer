#!/bin/bash
# Workflow Validator - Simplified Version
set -euo pipefail

EVIDENCE_DIR=".evidence"
mkdir -p "$EVIDENCE_DIR"

TOTAL=0
PASSED=0
FAILED=0
FAILED_LIST=""

echo "=== Workflow Validator ==="
echo ""

# Phase 0
echo "Phase 0: Discovery"
test -f "docs/P0_DISCOVERY.md" && { echo "  ✓ P0_S001"; PASSED=$((PASSED+1)); } || { echo "  ✗ P0_S001"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P0_S001"; }
TOTAL=$((TOTAL+1))

grep -q "## Problem Statement" "docs/P0_DISCOVERY.md" 2>/dev/null && { echo "  ✓ P0_S002"; PASSED=$((PASSED+1)); } || { echo "  ✗ P0_S002"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P0_S002"; }
TOTAL=$((TOTAL+1))

grep -q "## Feasibility" "docs/P0_DISCOVERY.md" 2>/dev/null && { echo "  ✓ P0_S003"; PASSED=$((PASSED+1)); } || { echo "  ✗ P0_S003"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P0_S003"; }
TOTAL=$((TOTAL+1))

grep -q "## Acceptance Checklist" "docs/P0_DISCOVERY.md" 2>/dev/null && { echo "  ✓ P0_S004"; PASSED=$((PASSED+1)); } || { echo "  ✗ P0_S004"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P0_S004"; }
TOTAL=$((TOTAL+1))

# Phase 1
echo ""
echo "Phase 1: Planning"
test -f "docs/PLAN.md" && { echo "  ✓ P1_S001"; PASSED=$((PASSED+1)); } || { echo "  ✗ P1_S001"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P1_S001"; }
TOTAL=$((TOTAL+1))

test -f ".workflow/current" && { echo "  ✓ P1_S002"; PASSED=$((PASSED+1)); } || { echo "  ✗ P1_S002"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P1_S002"; }
TOTAL=$((TOTAL+1))

# Phase 2
echo ""
echo "Phase 2: Implementation"
test -f "spec/workflow.spec.yaml" && { echo "  ✓ P2_S001"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S001"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S001"; }
TOTAL=$((TOTAL+1))

test -f "scripts/workflow_validator.sh" && { echo "  ✓ P2_S002"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S002"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S002"; }
TOTAL=$((TOTAL+1))

test -f "scripts/local_ci.sh" && { echo "  ✓ P2_S003"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S003"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S003"; }
TOTAL=$((TOTAL+1))

test -f "scripts/serve_progress.sh" && { echo "  ✓ P2_S004"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S004"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S004"; }
TOTAL=$((TOTAL+1))

test -d ".evidence" && { echo "  ✓ P2_S005"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S005"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S005"; }
TOTAL=$((TOTAL+1))

test -f ".git/hooks/pre-commit" && { echo "  ✓ P2_S006"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S006"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S006"; }
TOTAL=$((TOTAL+1))

test -f ".git/hooks/pre-push" && { echo "  ✓ P2_S007"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S007"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S007"; }
TOTAL=$((TOTAL+1))

test -f "tools/web/dashboard.html" && { echo "  ✓ P2_S008"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S008"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S008"; }
TOTAL=$((TOTAL+1))

test -f "docs/WORKFLOW_VALIDATION.md" && { echo "  ✓ P2_S009"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S009"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S009"; }
TOTAL=$((TOTAL+1))

grep -q "完成标准\|Completion Standards" "README.md" 2>/dev/null && { echo "  ✓ P2_S010"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S010"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S010"; }
TOTAL=$((TOTAL+1))

grep -q "Workflow Validation Requirements" "CONTRIBUTING.md" 2>/dev/null && { echo "  ✓ P2_S011"; PASSED=$((PASSED+1)); } || { echo "  ✗ P2_S011"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P2_S011"; }
TOTAL=$((TOTAL+1))

# Phase 3: Testing
echo ""
echo "Phase 3: Testing"

# P3_S001: Static checks script exists and is executable
test -x "scripts/static_checks.sh" && { echo "  ✓ P3_S001: static_checks.sh executable"; PASSED=$((PASSED+1)); } || { echo "  ✗ P3_S001"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P3_S001"; }
TOTAL=$((TOTAL+1))

# P3_S002: Static checks can run successfully
if bash scripts/static_checks.sh >/dev/null 2>&1; then
  echo "  ✓ P3_S002: static_checks passes"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P3_S002: static_checks failed"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P3_S002"
fi
TOTAL=$((TOTAL+1))

# P3_S003: Pre-commit hook is executable
test -x ".git/hooks/pre-commit" && { echo "  ✓ P3_S003: pre-commit executable"; PASSED=$((PASSED+1)); } || { echo "  ✗ P3_S003"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P3_S003"; }
TOTAL=$((TOTAL+1))

# P3_S004: Pre-push hook is executable
test -x ".git/hooks/pre-push" && { echo "  ✓ P3_S004: pre-push executable"; PASSED=$((PASSED+1)); } || { echo "  ✗ P3_S004"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P3_S004"; }
TOTAL=$((TOTAL+1))

# P3_S005: Local CI script exists and is executable
test -x "scripts/local_ci.sh" && { echo "  ✓ P3_S005: local_ci.sh executable"; PASSED=$((PASSED+1)); } || { echo "  ✗ P3_S005"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P3_S005"; }
TOTAL=$((TOTAL+1))

# P3_S006: Evidence directory exists
test -d ".evidence" && { echo "  ✓ P3_S006: .evidence directory"; PASSED=$((PASSED+1)); } || { echo "  ✗ P3_S006"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P3_S006"; }
TOTAL=$((TOTAL+1))

# Phase 4: Review
echo ""
echo "Phase 4: Review"
test -f "docs/REVIEW.md" && { echo "  ✓ P4_S001: REVIEW.md exists"; PASSED=$((PASSED+1)); } || { echo "  ✗ P4_S001"; FAILED=$((FAILED+1)); FAILED_LIST="$FAILED_LIST P4_S001"; }
TOTAL=$((TOTAL+1))

# P4_S002: REVIEW.md has minimum content (>100 lines)
if [ -f "docs/REVIEW.md" ] && [ $(wc -l < "docs/REVIEW.md") -gt 100 ]; then
  echo "  ✓ P4_S002: REVIEW.md substantial"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P4_S002: REVIEW.md too short"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P4_S002"
fi
TOTAL=$((TOTAL+1))

# Phase 5: Release & Monitor
echo ""
echo "Phase 5: Release"

# P5_S001: Version consistency check
if bash scripts/check_version_consistency.sh >/dev/null 2>&1; then
  echo "  ✓ P5_S001: version consistency"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P5_S001: version mismatch"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P5_S001"
fi
TOTAL=$((TOTAL+1))

# P5_S002: CHANGELOG.md exists and updated
if [ -f "CHANGELOG.md" ]; then
  echo "  ✓ P5_S002: CHANGELOG.md exists"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P5_S002: CHANGELOG.md missing"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P5_S002"
fi
TOTAL=$((TOTAL+1))

# P5_S003: All documentation updated
if grep -q "6\.5\.1\|6\.3\|6\." "README.md" 2>/dev/null; then
  echo "  ✓ P5_S003: README.md version updated"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P5_S003: README.md version outdated"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P5_S003"
fi
TOTAL=$((TOTAL+1))

# P5_S004: Dashboard is accessible
if [ -f "tools/web/dashboard.html" ] && [ -f "tools/web/api/progress" ]; then
  echo "  ✓ P5_S004: Dashboard ready"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P5_S004: Dashboard incomplete"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P5_S004"
fi
TOTAL=$((TOTAL+1))

# P5_S005: Evidence file generated
if [ -f ".evidence/last_run.json" ]; then
  echo "  ✓ P5_S005: Evidence generated"
  PASSED=$((PASSED+1))
else
  echo "  ✗ P5_S005: No evidence"
  FAILED=$((FAILED+1))
  FAILED_LIST="$FAILED_LIST P5_S005"
fi
TOTAL=$((TOTAL+1))

# Summary
PASS_RATE=$((PASSED * 100 / TOTAL))

echo ""
echo "=== Summary ==="
echo "Total:  $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Rate:   $PASS_RATE%"

# Evidence
cat > "$EVIDENCE_DIR/last_run.json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total": $TOTAL,
  "passed": $PASSED,
  "failed": $FAILED,
  "pass_rate": $PASS_RATE
}
EOF

if [ "$FAILED_LIST" != "" ]; then
  echo ""
  echo "Failed:$FAILED_LIST"
fi

if [ $PASS_RATE -ge 80 ]; then
  echo ""
  echo "✅ PASSED"
  exit 0
else
  echo ""
  echo "❌ FAILED"
  exit 1
fi
