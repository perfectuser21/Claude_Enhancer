#!/bin/bash
# Unit Tests for phase1_completion_enforcer.sh
# Tests the Phase 1 completion enforcement hook

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOK_SCRIPT="$PROJECT_ROOT/.claude/hooks/phase1_completion_enforcer.sh"

# Test utilities
TESTS_PASSED=0
TESTS_FAILED=0

pass() {
    echo "✓ $1"
    ((TESTS_PASSED++))
}

fail() {
    echo "✗ $1"
    ((TESTS_FAILED++))
}

# Setup test environment
setup() {
    # Backup current state
    if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
        cp "$PROJECT_ROOT/.phase/current" "$PROJECT_ROOT/.phase/current.backup"
    fi
    if [[ -f "$PROJECT_ROOT/.phase/phase1_confirmed" ]]; then
        cp "$PROJECT_ROOT/.phase/phase1_confirmed" "$PROJECT_ROOT/.phase/phase1_confirmed.backup"
    fi
}

# Teardown test environment
teardown() {
    # Restore state
    if [[ -f "$PROJECT_ROOT/.phase/current.backup" ]]; then
        mv "$PROJECT_ROOT/.phase/current.backup" "$PROJECT_ROOT/.phase/current"
    fi
    if [[ -f "$PROJECT_ROOT/.phase/phase1_confirmed.backup" ]]; then
        mv "$PROJECT_ROOT/.phase/phase1_confirmed.backup" "$PROJECT_ROOT/.phase/phase1_confirmed"
    fi
}

# Test 1: Non-coding tools should pass
test_non_coding_tools() {
    echo "Phase1" > "$PROJECT_ROOT/.phase/current"

    for tool in "Read" "Grep" "Glob"; do
        if TOOL_NAME="$tool" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
            pass "Test 1: $tool tool allowed"
        else
            fail "Test 1: $tool tool should be allowed"
        fi
    done
}

# Test 2: Phase1 complete without confirmation should block
test_phase1_complete_without_confirmation() {
    echo "Phase1" > "$PROJECT_ROOT/.phase/current"
    rm -f "$PROJECT_ROOT/.phase/phase1_confirmed"

    # Ensure Phase 1 docs exist
    touch "$PROJECT_ROOT/docs/P1_DISCOVERY.md"
    touch "$PROJECT_ROOT/.workflow/ACCEPTANCE_CHECKLIST.md"
    touch "$PROJECT_ROOT/docs/PLAN.md"

    if TOOL_NAME="Write" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        fail "Test 2: Should block Write when Phase1 complete but unconfirmed"
    else
        pass "Test 2: Correctly blocks Write when Phase1 complete but unconfirmed"
    fi

    if TOOL_NAME="Edit" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        fail "Test 2: Should block Edit when Phase1 complete but unconfirmed"
    else
        pass "Test 2: Correctly blocks Edit when Phase1 complete but unconfirmed"
    fi

    if TOOL_NAME="Bash" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        fail "Test 2: Should block Bash when Phase1 complete but unconfirmed"
    else
        pass "Test 2: Correctly blocks Bash when Phase1 complete but unconfirmed"
    fi
}

# Test 3: Phase1 with confirmation should pass
test_phase1_with_confirmation() {
    echo "Phase1" > "$PROJECT_ROOT/.phase/current"
    touch "$PROJECT_ROOT/.phase/phase1_confirmed"

    if TOOL_NAME="Write" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        pass "Test 3: Write allowed when Phase1 confirmed"
    else
        fail "Test 3: Write should be allowed when Phase1 confirmed"
    fi

    if TOOL_NAME="Edit" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        pass "Test 3: Edit allowed when Phase1 confirmed"
    else
        fail "Test 3: Edit should be allowed when Phase1 confirmed"
    fi
}

# Test 4: Phase2 status should pass
test_phase2_status() {
    echo "Phase2" > "$PROJECT_ROOT/.phase/current"
    rm -f "$PROJECT_ROOT/.phase/phase1_confirmed"

    if TOOL_NAME="Write" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        pass "Test 4: Write allowed in Phase2"
    else
        fail "Test 4: Write should be allowed in Phase2"
    fi

    if TOOL_NAME="Edit" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        pass "Test 4: Edit allowed in Phase2"
    else
        fail "Test 4: Edit should be allowed in Phase2"
    fi
}

# Test 5: Missing Phase 1 docs should pass (Phase incomplete)
test_missing_phase1_docs() {
    echo "Phase1" > "$PROJECT_ROOT/.phase/current"
    rm -f "$PROJECT_ROOT/.phase/phase1_confirmed"

    # Remove one Phase 1 doc to make it incomplete
    rm -f "$PROJECT_ROOT/docs/PLAN.md.test"
    touch "$PROJECT_ROOT/docs/PLAN.md.test"

    # Should pass because Phase 1 is not complete yet
    if TOOL_NAME="Write" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        pass "Test 5: Write allowed when Phase1 incomplete"
    else
        fail "Test 5: Write should be allowed when Phase1 incomplete"
    fi

    rm -f "$PROJECT_ROOT/docs/PLAN.md.test"
}

# Test 6: No .phase/current file should pass
test_no_phase_file() {
    rm -f "$PROJECT_ROOT/.phase/current"

    if TOOL_NAME="Write" bash "$HOOK_SCRIPT" >/dev/null 2>&1; then
        pass "Test 6: Write allowed when no .phase/current"
    else
        fail "Test 6: Write should be allowed when no .phase/current"
    fi
}

# Test 7: Performance test - should complete in <50ms
test_performance() {
    echo "Phase1" > "$PROJECT_ROOT/.phase/current"
    touch "$PROJECT_ROOT/.phase/phase1_confirmed"

    local start=$(date +%s%N)
    TOOL_NAME="Write" bash "$HOOK_SCRIPT" >/dev/null 2>&1
    local end=$(date +%s%N)

    local duration_ms=$(( (end - start) / 1000000 ))

    if [[ $duration_ms -lt 50 ]]; then
        pass "Test 7: Performance ${duration_ms}ms < 50ms"
    else
        fail "Test 7: Performance ${duration_ms}ms >= 50ms (too slow)"
    fi
}

# Main test runner
main() {
    echo "════════════════════════════════════════════════════════════"
    echo "Unit Tests: phase1_completion_enforcer.sh"
    echo "════════════════════════════════════════════════════════════"
    echo ""

    setup

    test_non_coding_tools
    test_phase1_complete_without_confirmation
    test_phase1_with_confirmation
    test_phase2_status
    test_missing_phase1_docs
    test_no_phase_file
    test_performance

    teardown

    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Test Results"
    echo "════════════════════════════════════════════════════════════"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo ""
        echo "✅ All tests passed!"
        exit 0
    else
        echo ""
        echo "❌ Some tests failed"
        exit 1
    fi
}

main "$@"
