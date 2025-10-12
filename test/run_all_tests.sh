#!/usr/bin/env bash
# Master Test Runner
# Runs all test suites and generates comprehensive report

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_FILE="$ROOT/docs/TEST-REPORT.md"
LOG_DIR="/tmp/ce-test-logs-$$"

# Test results
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

# Create log directory
mkdir -p "$LOG_DIR"

# Header
print_header() {
  echo ""
  echo -e "${CYAN}╔═════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║                                                         ║${NC}"
  echo -e "${CYAN}║     ${BOLD}Claude Enhancer v6.2 Test Suite${NC}${CYAN}                ║${NC}"
  echo -e "${CYAN}║     ${BOLD}Enforcement Optimization Testing${NC}${CYAN}                ║${NC}"
  echo -e "${CYAN}║                                                         ║${NC}"
  echo -e "${CYAN}╚═════════════════════════════════════════════════════════╝${NC}"
  echo ""
}

# Run a test suite
run_test_suite() {
  local name="$1"
  local script="$2"
  local log_file
  log_file="$LOG_DIR/$(basename "$script" .sh).log"

  ((TOTAL_SUITES++)) || true

  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}Running: $name${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""

  local start_time
  start_time=$(date +%s)

  if bash "$script" 2>&1 | tee "$log_file"; then
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    ((PASSED_SUITES++)) || true
    echo ""
    echo -e "${GREEN}✓ $name PASSED${NC} (${duration}s)"
    echo "$name|PASS|${duration}s" >> "$LOG_DIR/results.txt"
    return 0
  else
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    ((FAILED_SUITES++)) || true
    echo ""
    echo -e "${RED}✗ $name FAILED${NC} (${duration}s)"
    echo "$name|FAIL|${duration}s" >> "$LOG_DIR/results.txt"
    return 1
  fi
}

# Generate report (simplified version)
generate_report() {
  echo ""
  echo -e "${BLUE}Generating test report...${NC}"

  {
    echo "# Test Report - Enforcement Optimization v6.2"
    echo ""
    echo "**Generated**: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    echo ""
    echo "## Summary"
    echo ""
    echo "| Metric | Value |"
    echo "|--------|-------|"
    echo "| Total Test Suites | $TOTAL_SUITES |"
    echo "| Passed | $PASSED_SUITES ✅ |"
    echo "| Failed | $FAILED_SUITES ❌ |"
    echo ""
    echo "## Coverage"
    echo ""
    echo "- Task Namespace (11 test cases)"
    echo "- Atomic Operations (9 test cases)"
    echo "- Integration Workflow (7 scenarios)"
    echo "- Stress Test (20 parallel tasks, 50 concurrent operations)"
    echo ""
  } > "$REPORT_FILE"

  echo -e "${GREEN}✓${NC} Test report: $REPORT_FILE"
}

# Main
main() {
  cd "$ROOT"
  print_header

  run_test_suite "Task Namespace Unit Tests" "test/unit/test_task_namespace.sh"
  run_test_suite "Atomic Operations Unit Tests" "test/unit/test_atomic_ops.sh"
  run_test_suite "Integration Tests" "test/integration/test_enforcement_workflow.sh"
  run_test_suite "Stress Tests" "test/stress/test_concurrent_operations.sh"

  generate_report

  echo ""
  echo "Total: $TOTAL_SUITES | Passed: $PASSED_SUITES | Failed: $FAILED_SUITES"

  [ "$FAILED_SUITES" -eq 0 ] && exit 0 || exit 1
}

main "$@"
