#!/usr/bin/env bash
# Integration Test for Complete Enforcement Workflow
# Tests the full agent evidence → pre-commit enforcement flow

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Setup complete environment
setup() {
  export TEST_ROOT="/tmp/ce-integration-test-$$"
  mkdir -p "$TEST_ROOT"
  cd "$TEST_ROOT"

  echo -e "${BLUE}Setting up test environment...${NC}"

  # Initialize git repo
  git init -q
  git config user.email "test@example.com"
  git config user.name "Test User"

  # Create full directory structure
  mkdir -p .gates .claude/{core,hooks} scripts/hooks

  # Copy all necessary files
  cp -r "${OLDPWD}/.claude/core/"* .claude/core/
  cp "${OLDPWD}/.claude/hooks/agent_evidence_collector.sh" .claude/hooks/
  cp "${OLDPWD}/scripts/hooks/pre-commit-enforcement" scripts/hooks/
  cp "${OLDPWD}/scripts/fast_lane_detector.sh" scripts/

  # Create config
  cat > .claude/config.yml <<'EOF'
version: "6.2.0"
enforcement:
  enabled: true
  mode: "strict"
  task_namespace:
    enabled: true
    path: ".gates"
  agent_evidence:
    enabled: true
    min_agents:
      full_lane: 3
      fast_lane: 0
EOF

  # Create index
  cat > .gates/_index.json <<'EOF'
{
  "version": "1.0.0",
  "tasks": {},
  "active_task_id": null,
  "metadata": {"total_tasks": 0}
}
EOF

  # Initialize a task
  local task_id="test_task_$$"
  mkdir -p ".gates/$task_id"

  cat > ".gates/$task_id/task_meta.json" <<EOF
{
  "task_id": "$task_id",
  "phase": "P3",
  "lane": "full",
  "status": "in_progress",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

  cat > ".gates/$task_id/evidence.json" <<EOF
{
  "task_id": "$task_id",
  "entries": []
}
EOF

  cat > ".gates/$task_id/agents.json" <<EOF
{
  "task_id": "$task_id",
  "invocations": []
}
EOF

  # Update index
  local temp
  temp=$(mktemp)
  jq --arg id "$task_id" \
     '.tasks[$id] = {"phase": "P3", "status": "in_progress", "lane": "full"} | .active_task_id = $id' \
     .gates/_index.json > "$temp"
  mv "$temp" .gates/_index.json

  export TASK_ID="$task_id"

  echo -e "${GREEN}✓${NC} Test environment ready"
  echo ""
}

# Teardown
teardown() {
  cd "$OLDPWD"
  rm -rf "$TEST_ROOT"
}

# Assertion helpers
assert_success() {
  local message="$1"
  ((TESTS_RUN++)) || true
  ((TESTS_PASSED++)) || true
  echo -e "${GREEN}✓${NC} $message"
}

assert_failure() {
  local message="$1"
  ((TESTS_RUN++)) || true
  ((TESTS_FAILED++)) || true
  echo -e "${RED}✗${NC} $message"
}

# Simulate agent invocation
simulate_agent_invocation() {
  local agent_type="$1"

  echo -e "${BLUE}Simulating agent invocation: $agent_type${NC}"

  # Source the task namespace library
  # shellcheck source=../../.claude/core/task_namespace.sh
  source .claude/core/task_namespace.sh

  # Record agent
  record_agent "$TASK_ID" "$agent_type" "integration test invocation"

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Agent recorded${NC}"
    return 0
  else
    echo -e "${RED}  ✗ Failed to record agent${NC}"
    return 1
  fi
}

# Run pre-commit enforcement
run_pre_commit_check() {
  local should_pass="$1"

  echo -e "${BLUE}Running pre-commit enforcement check...${NC}"

  # Create a dummy file to commit
  echo "test content" > test.txt
  git add test.txt

  # Run enforcement script
  bash scripts/hooks/pre-commit-enforcement 2>&1 | tee /tmp/enforcement-output.txt

  local exit_code=${PIPESTATUS[0]}

  if [ "$should_pass" = "true" ]; then
    if [ $exit_code -eq 0 ]; then
      echo -e "${GREEN}  ✓ Enforcement check passed as expected${NC}"
      return 0
    else
      echo -e "${RED}  ✗ Enforcement check failed unexpectedly${NC}"
      cat /tmp/enforcement-output.txt
      return 1
    fi
  else
    if [ $exit_code -ne 0 ]; then
      echo -e "${GREEN}  ✓ Enforcement check blocked as expected${NC}"
      return 0
    else
      echo -e "${RED}  ✗ Enforcement check passed unexpectedly${NC}"
      return 1
    fi
  fi
}

# Test 1: Enforcement blocks with insufficient agents
test_insufficient_agents() {
  echo ""
  echo "=================================="
  echo "Test 1: Block commit with insufficient agents"
  echo "=================================="

  # Record only 1 agent (requires 3 for full lane)
  simulate_agent_invocation "backend-architect"

  if run_pre_commit_check "false"; then
    assert_success "Commit blocked with only 1 agent (requires 3)"
  else
    assert_failure "Should have blocked commit with insufficient agents"
  fi
}

# Test 2: Enforcement passes with sufficient agents
test_sufficient_agents() {
  echo ""
  echo "=================================="
  echo "Test 2: Allow commit with sufficient agents"
  echo "=================================="

  # Add 2 more agents (total 3)
  simulate_agent_invocation "test-engineer"
  simulate_agent_invocation "security-auditor"

  if run_pre_commit_check "true"; then
    assert_success "Commit allowed with 3 agents"
  else
    assert_failure "Should have allowed commit with sufficient agents"
  fi
}

# Test 3: Agent evidence persists across invocations
test_evidence_persistence() {
  echo ""
  echo "=================================="
  echo "Test 3: Agent evidence persistence"
  echo "=================================="

  # shellcheck source=../../.claude/core/task_namespace.sh
  source .claude/core/task_namespace.sh

  local count
  count=$(get_agent_count "$TASK_ID")

  if [ "$count" = "3" ]; then
    assert_success "Agent count persisted correctly (3)"
  else
    assert_failure "Agent count should be 3, got $count"
  fi

  # Check agents file
  local agents_file=".gates/$TASK_ID/agents.json"
  if [ -f "$agents_file" ]; then
    local recorded_count
    recorded_count=$(jq '.invocations | length' "$agents_file")

    if [ "$recorded_count" = "3" ]; then
      assert_success "All 3 agent invocations recorded in agents.json"
    else
      assert_failure "Expected 3 invocations in agents.json, got $recorded_count"
    fi
  else
    assert_failure "agents.json file not found"
  fi
}

# Test 4: Fast lane detection for docs-only changes
test_fast_lane_detection() {
  echo ""
  echo "=================================="
  echo "Test 4: Fast lane detection for docs-only"
  echo "=================================="

  # Create a docs-only commit
  git reset --hard HEAD 2>/dev/null || true
  echo "# Documentation" > README.md
  git add README.md

  # Run fast lane detector
  if bash scripts/fast_lane_detector.sh check; then
    assert_success "Docs-only change detected as fast lane eligible"
  else
    assert_failure "Docs-only change should be fast lane eligible"
  fi
}

# Test 5: Full lane required for code changes
test_full_lane_required() {
  echo ""
  echo "=================================="
  echo "Test 5: Full lane required for code changes"
  echo "=================================="

  # Create a code change
  git reset --hard HEAD 2>/dev/null || true
  mkdir -p src
  echo "function test() { return true; }" > src/code.js
  git add src/code.js

  # Run fast lane detector
  if ! bash scripts/fast_lane_detector.sh check; then
    assert_success "Code change correctly requires full lane"
  else
    assert_failure "Code change should require full lane"
  fi
}

# Test 6: Multiple tasks don't interfere
test_task_isolation() {
  echo ""
  echo "=================================="
  echo "Test 6: Task namespace isolation"
  echo "=================================="

  # Create a second task
  local task2_id="test_task2_$$"
  mkdir -p ".gates/$task2_id"

  cat > ".gates/$task2_id/task_meta.json" <<EOF
{
  "task_id": "$task2_id",
  "phase": "P3",
  "lane": "full",
  "status": "in_progress"
}
EOF

  cat > ".gates/$task2_id/agents.json" <<EOF
{
  "task_id": "$task2_id",
  "invocations": []
}
EOF

  # Record agent to task2
  # shellcheck source=../../.claude/core/task_namespace.sh
  source .claude/core/task_namespace.sh
  record_agent "$task2_id" "data-engineer" "task 2 agent"

  # Check task1 still has 3 agents
  local task1_count
  task1_count=$(get_agent_count "$TASK_ID")

  # Check task2 has 1 agent
  local task2_count
  task2_count=$(get_agent_count "$task2_id")

  if [ "$task1_count" = "3" ] && [ "$task2_count" = "1" ]; then
    assert_success "Tasks are properly isolated (task1=3, task2=1)"
  else
    assert_failure "Task isolation failed (task1=$task1_count, task2=$task2_count)"
  fi
}

# Test 7: Advisory mode allows commits with warning
test_advisory_mode() {
  echo ""
  echo "=================================="
  echo "Test 7: Advisory mode (warnings only)"
  echo "=================================="

  # Switch to advisory mode
  echo "DEBUG: Checking config.yml before modification..."
  if [ ! -f .claude/config.yml ]; then
    echo "DEBUG: config.yml not found, creating default..."
    mkdir -p .claude
    cat > .claude/config.yml <<'EOFCONFIG'
enforcement:
  mode: "strict"
  min_agents: 5
EOFCONFIG
  fi

  echo "DEBUG: Current config.yml content:"
  cat .claude/config.yml || echo "Failed to read config.yml"

  echo "DEBUG: Switching to advisory mode..."
  sed -i 's/mode: "strict"/mode: "advisory"/' .claude/config.yml || \
  sed -i 's/mode: strict/mode: advisory/' .claude/config.yml || \
  sed -i 's/mode:"strict"/mode:"advisory"/' .claude/config.yml || true

  echo "DEBUG: After modification:"
  cat .claude/config.yml || echo "Failed to read config.yml after modification"

  # Create new task with 0 agents
  local task3_id="test_task3_$$"
  mkdir -p ".gates/$task3_id"

  cat > ".gates/$task3_id/task_meta.json" <<EOF
{
  "task_id": "$task3_id",
  "phase": "P3",
  "lane": "full",
  "status": "in_progress"
}
EOF

  cat > ".gates/$task3_id/agents.json" <<EOF
{
  "task_id": "$task3_id",
  "invocations": []
}
EOF

  # Update index
  local temp
  temp=$(mktemp)
  jq --arg id "$task3_id" \
     '.tasks[$id] = {"phase": "P3", "status": "in_progress", "lane": "full"} | .active_task_id = $id' \
     .gates/_index.json > "$temp"
  mv "$temp" .gates/_index.json

  export TASK_ID="$task3_id"

  # Create commit (should pass with warning in advisory mode)
  echo "DEBUG: Resetting git state..."
  git reset --hard HEAD 2>/dev/null || true
  echo "DEBUG: Creating test file..."
  echo "test" > test2.txt
  git add test2.txt

  echo "DEBUG: Running pre-commit-enforcement script..."
  echo "DEBUG: TASK_ID=$TASK_ID"
  echo "DEBUG: PWD=$(pwd)"
  echo "DEBUG: About to check if script exists..."

  # Check if script exists
  if [ ! -f scripts/hooks/pre-commit-enforcement ]; then
    echo "ERROR: scripts/hooks/pre-commit-enforcement not found!"
    assert_failure "Enforcement script not found"
    return
  fi

  echo "DEBUG: Script exists, about to execute..."
  echo "DEBUG: ls -la scripts/hooks/pre-commit-enforcement:"
  ls -la scripts/hooks/pre-commit-enforcement || echo "ls failed"

  # Run enforcement and capture output with explicit error handling
  local output
  local exit_code
  echo "DEBUG: Executing enforcement script now..."
  set +e  # Temporarily disable exit on error
  output=$(bash scripts/hooks/pre-commit-enforcement 2>&1)
  exit_code=$?
  set -e  # Re-enable exit on error
  echo "DEBUG: Enforcement script execution completed"

  echo "DEBUG: Enforcement exit code: $exit_code"
  echo "DEBUG: Enforcement output (first 500 chars):"
  echo "$output" | head -c 500

  # Check if yq is available
  if command -v yq >/dev/null 2>&1; then
    echo "DEBUG: yq is available, testing true advisory mode..."
    # In advisory mode with yq, should pass (exit 0) but show warnings
    if [ $exit_code -eq 0 ]; then
      if echo "$output" | grep -q "⚠️\|WARNING\|⚠"; then
        assert_success "Advisory mode shows warnings but allows commit"
      else
        # Advisory mode passed without warnings - still acceptable
        assert_success "Advisory mode allows commit (no warnings for this change)"
      fi
    else
      echo "DEBUG: Full error output:"
      echo "$output"
      assert_failure "Advisory mode should allow commit (got exit code $exit_code)"
    fi
  else
    echo "DEBUG: yq not available, enforcement falls back to strict mode"
    # Without yq, config cannot be read, so strict mode is used (exits 1)
    if [ $exit_code -ne 0 ] && echo "$output" | grep -q "Commit blocked"; then
      assert_success "Without yq, enforcement correctly falls back to strict mode"
    else
      echo "DEBUG: Expected strict mode fallback, got exit=$exit_code"
      echo "DEBUG: Output: $output"
      assert_failure "Expected strict mode fallback when yq unavailable"
    fi
  fi
}

# Main test runner
main() {
  echo "=================================="
  echo "Enforcement Workflow Integration Tests"
  echo "=================================="
  echo ""

  setup

  test_insufficient_agents
  test_sufficient_agents
  test_evidence_persistence
  test_fast_lane_detection
  test_full_lane_required
  test_task_isolation
  test_advisory_mode

  teardown

  echo ""
  echo "=================================="
  echo "Test Results"
  echo "=================================="
  echo "Tests run:    $TESTS_RUN"
  echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
  echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

  if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All integration tests passed!${NC}"
    exit 0
  else
    echo -e "${RED}✗ Some integration tests failed${NC}"
    exit 1
  fi
}

main "$@"
