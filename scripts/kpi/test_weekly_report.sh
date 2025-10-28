#!/usr/bin/env bash
# Test script for weekly_report.sh
# Verifies all 4 metrics with sample data

set -euo pipefail

CE_HOME="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="$CE_HOME/.kpi_test"
KPI_SCRIPT="$CE_HOME/scripts/kpi/weekly_report.sh"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  KPI Dashboard Test Suite                                ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Setup test environment
setup_test_env() {
  echo -e "${CYAN}[1/5] Setting up test environment...${NC}"

  # Clean up
  rm -rf "$TEST_DIR"
  mkdir -p "$TEST_DIR/.kpi"
  mkdir -p "$TEST_DIR/.learning"
  mkdir -p "$TEST_DIR/docs"

  # Create test Learning Items
  cat > "$TEST_DIR/.learning/item1.md" <<'EOF'
# Learning Item 1

## Problem
Test error

## Solution
Fixed the test error

## Prevention Strategy
Add test coverage
EOF

  cat > "$TEST_DIR/.learning/item2.yml" <<'EOF'
problem: Another test error
solution: Fixed it
prevention: Better validation
EOF

  # Create test rollback log
  echo "2025-10-28T10:00:00Z Rollback: Test failure" > "$TEST_DIR/.kpi/rollback.log"

  # Create test checklist
  cat > "$TEST_DIR/docs/TEST_CHECKLIST.md" <<'EOF'
# Test Checklist

- [x] 1.1 Test item with evidence
<!-- evidence: EVID-2025W44-001 -->

- [x] 1.2 Test item without evidence

- [ ] 1.3 Incomplete item
EOF

  echo -e "${GREEN}✓${NC} Test environment ready"
}

# Test: Run weekly_report with test data
test_all_metrics() {
  echo -e "\n${CYAN}[2/5] Testing all 4 metrics...${NC}"

  local result
  result=$(CE_HOME="$TEST_DIR" "$KPI_SCRIPT" --auto 2>&1)

  echo "     JSON Result: $result"

  # Parse JSON
  local autofix=$(echo "$result" | grep -o '"autofix":"[^"]*"' | cut -d'"' -f4)
  local mttr=$(echo "$result" | grep -o '"mttr":"[^"]*"' | cut -d'"' -f4)
  local reuse=$(echo "$result" | grep -o '"reuse":"[^"]*"' | cut -d'"' -f4)
  local evidence=$(echo "$result" | grep -o '"evidence":"[^"]*"' | cut -d'"' -f4)

  echo "     - Auto-Fix Success: $autofix"
  echo "     - MTTR: $mttr"
  echo "     - Learning Reuse: $reuse"
  echo "     - Evidence Compliance: $evidence"

  local failed=0

  # Test Auto-Fix (expect 50%)
  if [[ "$autofix" == "50%" ]] || [[ "$autofix" == "50.0%" ]]; then
    echo -e "${GREEN}✓${NC} Auto-Fix Success Rate correct"
  else
    echo -e "${RED}✗${NC} Auto-Fix: expected 50%, got $autofix"
    ((failed++))
  fi

  # Test MTTR (expect 0h or 0.0h)
  if [[ "$mttr" =~ ^[0-9]+(\.[0-9]+)?h$ ]] || [[ "$mttr" == "N/A (no resolved items)" ]]; then
    echo -e "${GREEN}✓${NC} MTTR calculation working"
  else
    echo -e "${RED}✗${NC} MTTR invalid format: $mttr"
    ((failed++))
  fi

  # Test Learning Reuse (expect 100%)
  if [[ "$reuse" == "100%" ]] || [[ "$reuse" == "100.0%" ]]; then
    echo -e "${GREEN}✓${NC} Learning Reuse Rate correct"
  else
    echo -e "${RED}✗${NC} Learning Reuse: expected 100%, got $reuse"
    ((failed++))
  fi

  # Test Evidence Compliance (expect 50%)
  if [[ "$evidence" == "50%" ]] || [[ "$evidence" == "50.0%" ]]; then
    echo -e "${GREEN}✓${NC} Evidence Compliance correct"
  else
    echo -e "${RED}✗${NC} Evidence: expected 50%, got $evidence"
    ((failed++))
  fi

  return $failed
}

# Cleanup
cleanup() {
  rm -rf "$TEST_DIR"
}

# Main
main() {
  local failed=0

  setup_test_env

  test_all_metrics || failed=$?

  cleanup

  echo ""
  echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

  if [[ $failed -eq 0 ]]; then
    echo -e "${GREEN}✓ All 4 metrics working correctly${NC}"
    return 0
  else
    echo -e "${RED}✗ $failed metric(s) failed${NC}"
    return 1
  fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
