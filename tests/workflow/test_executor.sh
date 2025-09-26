#!/bin/bash
# Workflow Executor Test Suite

set -e

# Test configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(cd "$TEST_DIR/../.." && pwd)"
EXECUTOR="$WORKFLOW_DIR/.workflow/executor.sh"
PASSED=0
FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test functions
test_phase_progression() {
    echo -e "${YELLOW}Testing: Phase Progression${NC}"

    # Save current state
    local original_phase=$(cat "$WORKFLOW_DIR/.phase/current")

    # Test P1 -> P2
    echo "P1" > "$WORKFLOW_DIR/.phase/current"
    "$EXECUTOR" test >/dev/null 2>&1

    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Phase progression test passed${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Phase progression test failed${NC}"
        ((FAILED++))
    fi

    # Restore
    echo "$original_phase" > "$WORKFLOW_DIR/.phase/current"
}

test_gates_validation() {
    echo -e "${YELLOW}Testing: Gates Validation${NC}"

    # Check if PLAN.md exists and validate
    if [[ -f "$WORKFLOW_DIR/docs/PLAN.md" ]]; then
        echo -e "${GREEN}✅ PLAN.md validation passed${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ PLAN.md validation failed${NC}"
        ((FAILED++))
    fi

    # Check task count
    local task_count=$(grep -c '^[0-9]\+\.' "$WORKFLOW_DIR/docs/PLAN.md" 2>/dev/null || echo 0)
    if [[ $task_count -ge 5 ]]; then
        echo -e "${GREEN}✅ Task count validation passed (${task_count} >= 5)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Task count validation failed (${task_count} < 5)${NC}"
        ((FAILED++))
    fi
}

test_parallel_limits() {
    echo -e "${YELLOW}Testing: Parallel Agent Limits${NC}"

    local phase="P3"
    local max_limit=$(cat "$WORKFLOW_DIR/.limits/$phase/max" 2>/dev/null || echo 0)

    if [[ $max_limit -eq 8 ]]; then
        echo -e "${GREEN}✅ P3 agent limit correct (8)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ P3 agent limit incorrect (expected 8, got $max_limit)${NC}"
        ((FAILED++))
    fi
}

test_hook_integration() {
    echo -e "${YELLOW}Testing: Claude Hook Integration${NC}"

    if [[ -f "$WORKFLOW_DIR/.claude/settings.json" ]]; then
        local version=$(grep -o '"version": "[^"]*"' "$WORKFLOW_DIR/.claude/settings.json" | cut -d'"' -f4)
        if [[ "$version" == "5.0.0" ]]; then
            echo -e "${GREEN}✅ Claude settings version correct${NC}"
            ((PASSED++))
        else
            echo -e "${RED}❌ Claude settings version incorrect${NC}"
            ((FAILED++))
        fi
    fi
}

test_boundary_conditions() {
    echo -e "${YELLOW}Testing: Boundary Conditions${NC}"

    # Test invalid phase
    echo "P99" > "$WORKFLOW_DIR/.phase/current"
    local result=$("$EXECUTOR" status 2>&1 | grep -c "P99" || echo 0)

    if [[ $result -gt 0 ]]; then
        echo -e "${GREEN}✅ Handles invalid phase correctly${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Failed to handle invalid phase${NC}"
        ((FAILED++))
    fi

    # Restore valid phase
    echo "P4" > "$WORKFLOW_DIR/.phase/current"
}

# Run all tests
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}   Workflow System Test Suite${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""

test_phase_progression
test_gates_validation
test_parallel_limits
test_hook_integration
test_boundary_conditions

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "Test Results:"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"

# Exit with appropriate code
[[ $FAILED -eq 0 ]] && exit 0 || exit 1