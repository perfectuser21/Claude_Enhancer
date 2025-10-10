#!/usr/bin/env bash
# Test script for merge_queue_manager.sh
# Purpose: Basic functional testing of merge queue operations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUEUE_MANAGER="${SCRIPT_DIR}/merge_queue_manager.sh"

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test helpers
test_start() {
    echo -e "\n${YELLOW}[TEST]${NC} $1"
    TESTS_RUN=$((TESTS_RUN + 1))
}

test_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-Assertion failed}"

    if [[ "$expected" == "$actual" ]]; then
        test_pass "$message"
        return 0
    else
        test_fail "$message (expected: '$expected', got: '$actual')"
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-Should contain}"

    if echo "$haystack" | grep -q "$needle"; then
        test_pass "$message"
        return 0
    else
        test_fail "$message (not found: '$needle')"
        return 1
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-Should not contain}"

    if echo "$haystack" | grep -q "$needle"; then
        test_fail "$message (found: '$needle')"
        return 1
    else
        test_pass "$message"
        return 0
    fi
}

assert_file_exists() {
    local file="$1"
    local message="${2:-File should exist}"

    if [[ -f "$file" ]]; then
        test_pass "$message"
        return 0
    else
        test_fail "$message (file: $file)"
        return 1
    fi
}

# Setup and cleanup
setup() {
    echo "=== Setting up test environment ==="

    # Clear queue
    "$QUEUE_MANAGER" clear --force 2>/dev/null || true

    # Remove lock if exists
    rm -rf /tmp/ce_locks/merge_queue.lock 2>/dev/null || true

    echo "Setup complete"
}

cleanup() {
    echo ""
    echo "=== Cleaning up test environment ==="

    # Clear queue
    "$QUEUE_MANAGER" clear --force 2>/dev/null || true

    # Remove test files
    rm -rf /tmp/ce_locks/merge_queue.lock 2>/dev/null || true

    echo "Cleanup complete"
}

# Test suite

test_empty_queue_status() {
    test_start "Empty queue should show EMPTY status"

    local output
    output=$("$QUEUE_MANAGER" status)

    assert_contains "$output" "EMPTY" "Status should indicate empty queue"
}

test_enqueue_basic() {
    test_start "Enqueue operation with valid PR number"

    "$QUEUE_MANAGER" enqueue 12345 "feature/test-branch" >/dev/null 2>&1

    assert_file_exists "/tmp/ce_locks/merge_queue.fifo" "Queue file should exist"

    local content
    content=$(cat /tmp/ce_locks/merge_queue.fifo)

    assert_contains "$content" ":12345:" "Queue should contain PR #12345"
    assert_contains "$content" "feature/test-branch" "Queue should contain branch name"
    assert_contains "$content" "QUEUED" "Initial status should be QUEUED"
}

test_enqueue_invalid_pr() {
    test_start "Enqueue should reject invalid PR number"

    local output
    local exit_code=0

    output=$("$QUEUE_MANAGER" enqueue "not-a-number" 2>&1) || exit_code=$?

    if [[ $exit_code -ne 0 ]]; then
        test_pass "Should exit with error for invalid PR"
    else
        test_fail "Should exit with error for invalid PR"
    fi

    assert_contains "$output" "Invalid PR number" "Error message should mention invalid PR"
}

test_duplicate_enqueue() {
    test_start "Duplicate enqueue should be detected"

    "$QUEUE_MANAGER" enqueue 99999 "feature/duplicate" >/dev/null 2>&1
    local output
    output=$("$QUEUE_MANAGER" enqueue 99999 "feature/duplicate" 2>&1)

    assert_contains "$output" "already in queue" "Should detect duplicate"

    local count
    count=$(grep -c ":99999:" /tmp/ce_locks/merge_queue.fifo)

    assert_equals "1" "$count" "Should have only one entry"
}

test_queue_status_display() {
    test_start "Queue status should display entries correctly"

    "$QUEUE_MANAGER" enqueue 111 "feature/test-1" >/dev/null 2>&1
    "$QUEUE_MANAGER" enqueue 222 "feature/test-2" >/dev/null 2>&1

    local output
    output=$("$QUEUE_MANAGER" status)

    assert_contains "$output" "#111" "Should show PR #111"
    assert_contains "$output" "#222" "Should show PR #222"
    assert_contains "$output" "feature/test-1" "Should show branch 1"
    assert_contains "$output" "feature/test-2" "Should show branch 2"
    assert_contains "$output" "Summary:" "Should show summary"
}

test_queue_status_detailed() {
    test_start "Detailed queue status should show additional info"

    "$QUEUE_MANAGER" enqueue 333 "feature/detailed" >/dev/null 2>&1

    local output
    output=$("$QUEUE_MANAGER" status --detailed)

    assert_contains "$output" "Wait(s)" "Should show wait time column"
    assert_contains "$output" "Retries" "Should show retries column"
    assert_contains "$output" "#333" "Should show PR #333"
}

test_queue_clear() {
    test_start "Queue clear should remove all entries"

    "$QUEUE_MANAGER" enqueue 444 "feature/clear-test" >/dev/null 2>&1

    # Verify entry exists
    local before
    before=$(cat /tmp/ce_locks/merge_queue.fifo)
    assert_contains "$before" ":444:" "Entry should exist before clear"

    # Clear queue
    "$QUEUE_MANAGER" clear --force >/dev/null 2>&1

    # Verify empty
    if [[ -s /tmp/ce_locks/merge_queue.fifo ]]; then
        test_fail "Queue file should be empty after clear"
    else
        test_pass "Queue file is empty after clear"
    fi
}

test_session_id_generation() {
    test_start "Session ID should be generated if not provided"

    "$QUEUE_MANAGER" enqueue 555 "feature/session-test" >/dev/null 2>&1

    local content
    content=$(cat /tmp/ce_locks/merge_queue.fifo)

    # Session ID should be in field 4
    local session_id
    session_id=$(echo "$content" | grep ":555:" | cut -d: -f4)

    if [[ -n "$session_id" && "$session_id" != "null" ]]; then
        test_pass "Session ID generated: $session_id"
    else
        test_fail "Session ID should be generated"
    fi
}

test_custom_session_id() {
    test_start "Custom session ID should be used when provided"

    CE_SESSION_ID="custom-session-123" "$QUEUE_MANAGER" enqueue 666 "feature/custom-session" >/dev/null 2>&1

    local content
    content=$(cat /tmp/ce_locks/merge_queue.fifo)

    assert_contains "$content" "custom-session-123" "Should use custom session ID"
}

test_multiple_concurrent_enqueues() {
    test_start "Multiple concurrent enqueues should not corrupt queue"

    # Enqueue 10 PRs in parallel
    for i in {1..10}; do
        "$QUEUE_MANAGER" enqueue "$((700 + i))" "feature/concurrent-$i" >/dev/null 2>&1 &
    done
    wait

    local count
    count=$(wc -l < /tmp/ce_locks/merge_queue.fifo)

    assert_equals "10" "$count" "Should have exactly 10 entries"

    # Verify no corruption (each line should be parseable)
    local valid=true
    while IFS=: read -r ts pr branch session status retry started; do
        if [[ -z "$ts" || -z "$pr" || -z "$status" ]]; then
            valid=false
            break
        fi
    done < /tmp/ce_locks/merge_queue.fifo

    if $valid; then
        test_pass "Queue file is valid after concurrent operations"
    else
        test_fail "Queue file corrupted after concurrent operations"
    fi
}

test_cleanup_old_entries() {
    test_start "Cleanup should remove old entries"

    # Add old entry (timestamp from 2000 seconds ago)
    local old_timestamp=$(($(date +%s) - 2000))
    echo "${old_timestamp}:888:feature/old:old-session:QUEUED:0:0" >> /tmp/ce_locks/merge_queue.fifo

    # Add recent entry
    "$QUEUE_MANAGER" enqueue 889 "feature/recent" >/dev/null 2>&1

    # Verify both exist
    local before_count
    before_count=$(wc -l < /tmp/ce_locks/merge_queue.fifo)
    assert_equals "2" "$before_count" "Should have 2 entries before cleanup"

    # Cleanup with 1000 second threshold
    "$QUEUE_MANAGER" cleanup 1000 >/dev/null 2>&1

    # Verify old entry removed
    local after_count
    after_count=$(wc -l < /tmp/ce_locks/merge_queue.fifo)
    assert_equals "1" "$after_count" "Should have 1 entry after cleanup"

    local content
    content=$(cat /tmp/ce_locks/merge_queue.fifo)
    assert_not_contains "$content" ":888:" "Old entry should be removed"
    assert_contains "$content" ":889:" "Recent entry should remain"
}

test_help_command() {
    test_start "Help command should display usage"

    local output
    output=$("$QUEUE_MANAGER" help)

    assert_contains "$output" "Usage:" "Should show usage"
    assert_contains "$output" "Commands:" "Should show commands"
    assert_contains "$output" "enqueue" "Should mention enqueue"
    assert_contains "$output" "status" "Should mention status"
    assert_contains "$output" "cleanup" "Should mention cleanup"
}

test_queue_position_display() {
    test_start "Enqueue should display queue position"

    "$QUEUE_MANAGER" enqueue 991 "feature/first" >/dev/null 2>&1

    local output
    output=$("$QUEUE_MANAGER" enqueue 992 "feature/second" 2>&1)

    assert_contains "$output" "Queue position:" "Should show position"
    assert_contains "$output" "Estimated wait time:" "Should show wait time"
}

# Main test runner
main() {
    echo "========================================"
    echo "  Merge Queue Manager - Test Suite"
    echo "========================================"
    echo ""
    echo "Script: $QUEUE_MANAGER"
    echo ""

    # Setup
    setup

    # Run tests
    test_empty_queue_status
    test_enqueue_basic
    test_enqueue_invalid_pr
    test_duplicate_enqueue
    test_queue_status_display
    test_queue_status_detailed
    test_queue_clear
    test_session_id_generation
    test_custom_session_id
    test_multiple_concurrent_enqueues
    test_cleanup_old_entries
    test_help_command
    test_queue_position_display

    # Cleanup
    cleanup

    # Summary
    echo ""
    echo "========================================"
    echo "           Test Summary"
    echo "========================================"
    echo "Tests run:    $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    echo "========================================"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

# Run tests
main "$@"
