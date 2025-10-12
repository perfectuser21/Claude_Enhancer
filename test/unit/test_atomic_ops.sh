#!/usr/bin/env bash
# Unit Tests for atomic_ops.sh
# Tests atomic operations and concurrent safety

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Setup
setup() {
  export TEST_ROOT="/tmp/ce-atomic-test-$$"
  mkdir -p "$TEST_ROOT"
  cd "$TEST_ROOT"

  # Copy library
  mkdir -p .claude/core
  cp "${OLDPWD}/.claude/core/atomic_ops.sh" .claude/core/

  # Source the library
  # shellcheck source=../../.claude/core/atomic_ops.sh
  source .claude/core/atomic_ops.sh
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

assert_json_valid() {
  local file="$1"
  local message="${2:-JSON should be valid}"

  ((TESTS_RUN++)) || true

  if jq empty "$file" 2>/dev/null; then
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

# Test: atomic_write basic functionality
test_atomic_write() {
  echo ""
  echo "Test: atomic_write basic functionality"

  local file="test.txt"
  local content="Hello, World!"

  atomic_write "$file" "$content"

  assert_file_exists "$file" "File created by atomic_write"

  local actual
  actual=$(cat "$file")

  if [ "$content" = "$actual" ]; then
    assert_success "Content written correctly"
  else
    assert_failure "Content mismatch"
  fi
}

# Test: atomic_json_update creates file if not exists
test_atomic_json_update_create() {
  echo ""
  echo "Test: atomic_json_update creates file if not exists"

  local file="new.json"

  atomic_json_update "$file" ".test" '"value"'

  assert_file_exists "$file" "File created"
  assert_json_valid "$file" "Valid JSON created"
  assert_json_value "$file" ".test" "value" "Value set correctly"
}

# Test: atomic_json_update modifies existing value
test_atomic_json_update_modify() {
  echo ""
  echo "Test: atomic_json_update modifies existing value"

  local file="modify.json"

  # Create initial file
  echo '{"test": "old", "keep": "value"}' > "$file"

  atomic_json_update "$file" ".test" '"new"'

  assert_json_value "$file" ".test" "new" "Value updated"
  assert_json_value "$file" ".keep" "value" "Other values preserved"
}

# Test: atomic_json_append
test_atomic_json_append() {
  echo ""
  echo "Test: atomic_json_append"

  local file="append.json"

  # Create initial file with empty array
  echo '{"items": []}' > "$file"

  atomic_json_append "$file" ".items" '"item1"'
  atomic_json_append "$file" ".items" '"item2"'
  atomic_json_append "$file" ".items" '"item3"'

  local count
  count=$(jq '.items | length' "$file")

  if [ "$count" = "3" ]; then
    assert_success "Array has 3 items"
  else
    assert_failure "Array should have 3 items, has $count"
  fi

  assert_json_value "$file" ".items[0]" "item1" "First item correct"
  assert_json_value "$file" ".items[2]" "item3" "Last item correct"
}

# Test: Concurrent writes don't corrupt data
test_concurrent_writes() {
  echo ""
  echo "Test: Concurrent writes (10 parallel processes)"

  local file="concurrent.json"
  echo '{"counter": 0}' > "$file"

  # Launch 10 parallel processes to increment counter
  local pids=()
  for _ in {1..10}; do
    (
      for _ in {1..5}; do
        # Use jq's += operator for atomic read-modify-write
        atomic_json_update "$file" ".counter" "(.counter + 1)"
      done
    ) &
    pids+=($!)
  done

  # Wait for all processes
  for pid in "${pids[@]}"; do
    wait "$pid" 2>/dev/null || true
  done

  # Check result
  local final
  final=$(jq '.counter' "$file")

  # Should be 50 (10 processes * 5 increments each)
  if [ "$final" = "50" ]; then
    assert_success "Concurrent writes completed successfully (counter = 50)"
  else
    assert_failure "Concurrent writes may have lost updates (counter = $final, expected 50)"
  fi

  assert_json_valid "$file" "JSON still valid after concurrent writes"
}

# Test: Retry mechanism on lock timeout
test_retry_mechanism() {
  echo ""
  echo "Test: Retry mechanism on lock contention"

  local file="retry.json"
  echo '{"value": 0}' > "$file"

  # Hold a lock and try to update
  (
    flock -x 200
    # Hold lock for 2 seconds
    sleep 2
  ) 200>"${file}.lock" &

  local lock_pid=$!

  # Try to update while lock is held (should retry)
  local start
  start=$(date +%s)

  atomic_json_update "$file" ".value" "1" || {
    assert_failure "Update failed (should have retried)"
    kill $lock_pid 2>/dev/null || true
    return 1
  }

  local end
  end=$(date +%s)
  local duration=$((end - start))

  wait $lock_pid 2>/dev/null || true
  rm -f "${file}.lock"

  if [ "$duration" -ge 2 ]; then
    assert_success "Retry mechanism waited for lock release (${duration}s)"
  else
    assert_failure "Update completed too quickly (${duration}s, expected >=2s)"
  fi

  assert_json_value "$file" ".value" "1" "Value updated after retry"
}

# Test: JSON validation catches corrupt data
test_json_validation() {
  echo ""
  echo "Test: JSON validation rejects corrupt data"

  local file="validate.json"
  echo '{"valid": true}' > "$file"

  # Try to write invalid JSON (this should fail)
  atomic_json_update "$file" ".broken" 'not-valid-json' 2>/dev/null && {
    assert_failure "Should reject invalid JSON"
    return 1
  }

  # Original file should be unchanged
  assert_json_valid "$file" "Original file still valid after failed update"
  assert_json_value "$file" ".valid" "true" "Original value preserved"
  assert_success "Invalid JSON rejected, original file preserved"
}

# Test: Cleanup temp files
test_cleanup_temp_files() {
  echo ""
  echo "Test: cleanup_temp_files"

  # Create some old temp files
  touch "file1.tmp.123"
  touch "file2.tmp.456"

  # Make them old (61 minutes ago)
  touch -d "61 minutes ago" "file1.tmp.123"
  touch -d "61 minutes ago" "file2.tmp.456"

  # Create a recent temp file (should not be deleted)
  touch "file3.tmp.789"

  cleanup_temp_files "."

  if [ ! -f "file1.tmp.123" ] && [ ! -f "file2.tmp.456" ]; then
    assert_success "Old temp files cleaned up"
  else
    assert_failure "Old temp files should be deleted"
  fi

  if [ -f "file3.tmp.789" ]; then
    assert_success "Recent temp file preserved"
  else
    assert_failure "Recent temp file should be preserved"
  fi
}

# Test: Backup and recovery
test_backup_recovery() {
  echo ""
  echo "Test: Backup and recovery"

  local file="backup-test.json"
  echo '{"important": "data"}' > "$file"

  create_backup "$file"

  assert_file_exists "${file}.backup" "Backup created"

  # Simulate file loss
  rm "$file"

  recover_from_crash "$file"

  assert_file_exists "$file" "File recovered from backup"
  assert_json_value "$file" ".important" "data" "Data restored correctly"
}

# Main test runner
main() {
  echo "=================================="
  echo "Atomic Operations Unit Tests"
  echo "=================================="

  setup

  test_atomic_write
  test_atomic_json_update_create
  test_atomic_json_update_modify
  test_atomic_json_append
  test_concurrent_writes
  test_retry_mechanism
  test_json_validation
  test_cleanup_temp_files
  test_backup_recovery

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
