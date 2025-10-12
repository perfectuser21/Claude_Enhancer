#!/usr/bin/env bash
# Unit Tests for task_namespace.sh
# Tests all core functions with assertions

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Setup test environment
setup() {
  export TEST_ROOT="/tmp/ce-test-$$"
  mkdir -p "$TEST_ROOT"
  cd "$TEST_ROOT"

  # Initialize git repo
  git init -q
  git config user.email "test@example.com"
  git config user.name "Test User"

  # Create minimal structure
  mkdir -p .gates .claude/core

  # Copy libraries
  cp "${OLDPWD}/.claude/core/atomic_ops.sh" .claude/core/
  cp "${OLDPWD}/.claude/core/task_namespace.sh" .claude/core/

  # Create index
  cat > .gates/_index.json <<'EOF'
{
  "version": "1.0.0",
  "tasks": {},
  "active_task_id": null,
  "metadata": {"total_tasks": 0}
}
EOF

  # Source the library
  # shellcheck source=../../.claude/core/task_namespace.sh
  source .claude/core/task_namespace.sh
}

# Teardown
teardown() {
  cd "$OLDPWD"
  rm -rf "$TEST_ROOT"
}

# Assertion helpers
assert_equals() {
  local expected="$1"
  local actual="$2"
  local message="${3:-Assertion failed}"

  ((TESTS_RUN++)) || true

  if [ "$expected" = "$actual" ]; then
    ((TESTS_PASSED++)) || true
    echo -e "${GREEN}✓${NC} $message"
    return 0
  else
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} $message"
    echo "  Expected: $expected"
    echo "  Actual:   $actual"
    return 1
  fi
}

assert_file_exists() {
  local file="$1"
  local message="${2:-File should exist: $file}"

  ((TESTS_RUN++)) || true

  if [ -f "$file" ]; then
    ((TESTS_PASSED++)) || true
    echo -e "${GREEN}✓${NC} $message"
    return 0
  else
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} $message"
    return 1
  fi
}

assert_dir_exists() {
  local dir="$1"
  local message="${2:-Directory should exist: $dir}"

  ((TESTS_RUN++)) || true

  if [ -d "$dir" ]; then
    ((TESTS_PASSED++)) || true
    echo -e "${GREEN}✓${NC} $message"
    return 0
  else
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} $message"
    return 1
  fi
}

assert_json_value() {
  local file="$1"
  local jq_filter="$2"
  local expected="$3"
  local message="${4:-JSON value mismatch}"

  ((TESTS_RUN++)) || true

  local actual
  actual=$(jq -r "$jq_filter" "$file" 2>/dev/null || echo "ERROR")

  if [ "$expected" = "$actual" ]; then
    ((TESTS_PASSED++)) || true
    echo -e "${GREEN}✓${NC} $message"
    return 0
  else
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} $message"
    echo "  Expected: $expected"
    echo "  Actual:   $actual"
    return 1
  fi
}

# Test: get_current_task when no task exists
test_get_current_task_empty() {
  echo ""
  echo "Test: get_current_task with no active task"

  local result
  result=$(get_current_task || echo "")

  assert_equals "" "$result" "Should return empty when no active task"
}

# Test: get_task_dir with no task
test_get_task_dir_empty() {
  echo ""
  echo "Test: get_task_dir with no task"

  get_task_dir && {
    ((TESTS_RUN++)) || true
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} Should fail when no task"
    return 1
  }

  ((TESTS_RUN++)) || true
  ((TESTS_PASSED++)) || true
  echo -e "${GREEN}✓${NC} Correctly fails when no task"
}

# Test: Create task namespace
test_create_task_namespace() {
  echo ""
  echo "Test: Create task namespace"

  # Create a task manually
  local task_id="P0_test_12345_abc123"
  local task_dir=".gates/$task_id"

  mkdir -p "$task_dir"

  cat > "$task_dir/task_meta.json" <<EOF
{
  "task_id": "$task_id",
  "phase": "P0",
  "lane": "full",
  "status": "in_progress"
}
EOF

  cat > "$task_dir/evidence.json" <<EOF
{
  "task_id": "$task_id",
  "entries": []
}
EOF

  cat > "$task_dir/agents.json" <<EOF
{
  "task_id": "$task_id",
  "invocations": []
}
EOF

  # Update index
  local temp
  temp=$(mktemp)
  jq --arg id "$task_id" \
     '.tasks[$id] = {"phase": "P0", "status": "in_progress"} | .active_task_id = $id' \
     .gates/_index.json > "$temp"
  mv "$temp" .gates/_index.json

  assert_dir_exists "$task_dir" "Task directory created"
  assert_file_exists "$task_dir/task_meta.json" "Task metadata exists"
  assert_file_exists "$task_dir/evidence.json" "Evidence file exists"
  assert_file_exists "$task_dir/agents.json" "Agents file exists"
}

# Test: get_current_task with active task
test_get_current_task_active() {
  echo ""
  echo "Test: get_current_task with active task"

  local result
  result=$(get_current_task)

  assert_equals "P0_test_12345_abc123" "$result" "Should return active task ID"
}

# Test: get_task_dir with active task
test_get_task_dir_active() {
  echo ""
  echo "Test: get_task_dir with active task"

  local result
  result=$(get_task_dir)

  # get_task_dir returns absolute path, extract relative part
  local expected=".gates/P0_test_12345_abc123"
  if [[ "$result" == *"$expected" ]]; then
    ((TESTS_RUN++)) || true
    ((TESTS_PASSED++)) || true
    echo -e "${GREEN}✓${NC} Should return correct task directory"
  else
    ((TESTS_RUN++)) || true
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} Should return correct task directory"
    echo "  Expected (ends with): $expected"
    echo "  Actual:   $result"
  fi
}

# Test: record_agent
test_record_agent() {
  echo ""
  echo "Test: record_agent"

  local task_id
  task_id=$(get_current_task)

  record_agent "$task_id" "backend-architect" "test context"

  local agents_file=".gates/$task_id/agents.json"
  assert_file_exists "$agents_file" "Agents file exists after recording"

  local count
  count=$(jq '.invocations | length' "$agents_file")
  assert_equals "1" "$count" "Should have 1 agent invocation"

  local agent_name
  agent_name=$(jq -r '.invocations[0].agent' "$agents_file")
  assert_equals "backend-architect" "$agent_name" "Agent name recorded correctly"
}

# Test: get_agent_count
test_get_agent_count() {
  echo ""
  echo "Test: get_agent_count"

  local task_id
  task_id=$(get_current_task)

  # Add more agents
  record_agent "$task_id" "test-engineer" "test 2"
  record_agent "$task_id" "security-auditor" "test 3"

  local count
  count=$(get_agent_count "$task_id")

  assert_equals "3" "$count" "Should have 3 agent invocations"
}

# Test: record_evidence
test_record_evidence() {
  echo ""
  echo "Test: record_evidence"

  local task_id
  task_id=$(get_current_task)

  local entry
  entry=$(jq -n --arg type "test_event" '{"type": $type, "data": "test"}')

  record_evidence "$task_id" "$entry"

  local evidence_file=".gates/$task_id/evidence.json"
  local count
  count=$(jq '.entries | length' "$evidence_file")

  assert_equals "1" "$count" "Should have 1 evidence entry"

  local entry_type
  entry_type=$(jq -r '.entries[0].type' "$evidence_file")
  assert_equals "test_event" "$entry_type" "Evidence type recorded correctly"
}

# Test: update_task_phase
test_update_task_phase() {
  echo ""
  echo "Test: update_task_phase"

  local task_id
  task_id=$(get_current_task)

  update_task_phase "$task_id" "P1"

  local meta_file=".gates/$task_id/task_meta.json"
  assert_json_value "$meta_file" ".phase" "P1" "Phase updated in task metadata"

  assert_json_value ".gates/_index.json" ".tasks[\"$task_id\"].phase" "P1" "Phase updated in index"
}

# Test: complete_phase
test_complete_phase() {
  echo ""
  echo "Test: complete_phase"

  local task_id
  task_id=$(get_current_task)

  complete_phase "$task_id" "P1"

  local gate_file=".gates/$task_id/1.ok"
  assert_file_exists "$gate_file" "Phase gate marker created"

  grep -q "Phase P1 completed successfully" "$gate_file" || {
    ((TESTS_RUN++)) || true
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} Gate marker should contain completion message"
    return 1
  }

  ((TESTS_RUN++)) || true
  ((TESTS_PASSED++)) || true
  echo -e "${GREEN}✓${NC} Gate marker contains completion message"
}

# Test: is_phase_complete
test_is_phase_complete() {
  echo ""
  echo "Test: is_phase_complete"

  local task_id
  task_id=$(get_current_task)

  if is_phase_complete "$task_id" "P1"; then
    ((TESTS_RUN++)) || true
    ((TESTS_PASSED++)) || true
    echo -e "${GREEN}✓${NC} P1 detected as complete"
  else
    ((TESTS_RUN++)) || true
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} P1 should be detected as complete"
  fi

  if is_phase_complete "$task_id" "P2"; then
    ((TESTS_RUN++)) || true
    ((TESTS_FAILED++)) || true
    echo -e "${RED}✗${NC} P2 should not be complete"
  else
    ((TESTS_RUN++)) || true
    ((TESTS_PASSED++)) || true
    echo -e "${GREEN}✓${NC} P2 correctly detected as incomplete"
  fi
}

# Main test runner
main() {
  echo "=================================="
  echo "Task Namespace Unit Tests"
  echo "=================================="

  setup

  test_get_current_task_empty
  test_get_task_dir_empty
  test_create_task_namespace
  test_get_current_task_active
  test_get_task_dir_active
  test_record_agent
  test_get_agent_count
  test_record_evidence
  test_update_task_phase
  test_complete_phase
  test_is_phase_complete

  teardown

  echo ""
  echo "=================================="
  echo "Test Results"
  echo "=================================="
  echo "Tests run:    $TESTS_RUN"
  echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
  echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

  if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
  else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
  fi
}

main "$@"
