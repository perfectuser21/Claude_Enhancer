#!/bin/bash
# Performance tests for hooks and critical operations
# Path: test/performance/test_hook_performance.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMP_TEST_DIR="$PROJECT_ROOT/.temp/perf_tests"

# ANSI colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Performance thresholds (in milliseconds)
THRESHOLD_CRITICAL=1000   # Critical operations must complete within 1s
THRESHOLD_NORMAL=500      # Normal operations should complete within 500ms
THRESHOLD_FAST=100        # Fast operations should complete within 100ms

test_count=0
pass_count=0
warn_count=0
fail_count=0

# Cleanup
cleanup() {
    rm -rf "$TEMP_TEST_DIR"
    cd "$PROJECT_ROOT"
    git reset HEAD . 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "$TEMP_TEST_DIR"
cd "$PROJECT_ROOT"

# Get current time in milliseconds
get_time_ms() {
    date +%s%3N
}

# Run performance test
run_perf_test() {
    local test_name="$1"
    local test_command="$2"
    local threshold="$3"
    local category="${4:-normal}"  # fast/normal/critical

    ((test_count++))

    echo ""
    echo -e "${BLUE}Test $test_count: $test_name${NC}"
    echo -n "  "

    local start=$(get_time_ms)

    # Run the command and capture result
    local result=0
    eval "$test_command" >/dev/null 2>&1 || result=$?

    local end=$(get_time_ms)
    local duration=$((end - start))

    # Format duration for display
    if [ $duration -lt 1000 ]; then
        local duration_display="${duration}ms"
    else
        local duration_sec=$(echo "scale=2; $duration / 1000" | bc)
        local duration_display="${duration_sec}s"
    fi

    # Evaluate performance
    if [ $result -ne 0 ]; then
        echo -e "${RED}❌ FAILED (command error)${NC}"
        ((fail_count++))
    elif [ $duration -le $threshold ]; then
        echo -e "${GREEN}✅ PASS${NC} - ${duration_display} (threshold: ${threshold}ms)"
        ((pass_count++))
    elif [ "$category" = "fast" ] && [ $duration -le $THRESHOLD_NORMAL ]; then
        echo -e "${YELLOW}⚠ SLOW${NC} - ${duration_display} (expected: <${threshold}ms, acceptable: <${THRESHOLD_NORMAL}ms)"
        ((warn_count++))
    else
        echo -e "${RED}❌ TOO SLOW${NC} - ${duration_display} (threshold: ${threshold}ms)"
        ((fail_count++))
    fi

    return $result
}

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Hook Performance Tests                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Performance Thresholds:${NC}"
echo -e "  Fast operations:     <${THRESHOLD_FAST}ms"
echo -e "  Normal operations:   <${THRESHOLD_NORMAL}ms"
echo -e "  Critical operations: <${THRESHOLD_CRITICAL}ms"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 1: Git Operations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Category 1: Git Operations${NC}"

run_perf_test \
    "Git status execution time" \
    "git status" \
    $THRESHOLD_FAST \
    "fast"

run_perf_test \
    "Git branch listing time" \
    "git branch" \
    $THRESHOLD_FAST \
    "fast"

run_perf_test \
    "Git diff execution time" \
    "git diff --cached" \
    $THRESHOLD_NORMAL \
    "normal"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 2: Hook Execution
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Category 2: Hook Execution Performance${NC}"

# Create a test file for hook execution
TEST_FILE="$TEMP_TEST_DIR/test_file.js"
echo "console.log('test');" > "$TEST_FILE"
git add "$TEST_FILE" 2>/dev/null || true

if [ -x ".git/hooks/pre-commit" ]; then
    run_perf_test \
        "Pre-commit hook execution time" \
        ".git/hooks/pre-commit" \
        $THRESHOLD_CRITICAL \
        "critical"
else
    echo -e "  ${YELLOW}⊘ Pre-commit hook not executable - skipping${NC}"
fi

if [ -x ".git/hooks/commit-msg" ]; then
    echo "test: performance test" > "$TEMP_TEST_DIR/test_commit_msg"
    run_perf_test \
        "Commit-msg hook execution time" \
        ".git/hooks/commit-msg $TEMP_TEST_DIR/test_commit_msg" \
        $THRESHOLD_NORMAL \
        "normal"
else
    echo -e "  ${YELLOW}⊘ Commit-msg hook not found - skipping${NC}"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 3: Claude Hooks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Category 3: Claude Hook Performance${NC}"

if [ -f ".claude/hooks/branch_helper.sh" ]; then
    run_perf_test \
        "Branch helper hook execution" \
        "bash .claude/hooks/branch_helper.sh" \
        $THRESHOLD_NORMAL \
        "normal"
fi

if [ -f ".claude/hooks/quality_gate.sh" ]; then
    run_perf_test \
        "Quality gate hook execution" \
        "bash .claude/hooks/quality_gate.sh --dry-run 2>/dev/null || true" \
        $THRESHOLD_NORMAL \
        "normal"
fi

if [ -f ".claude/hooks/workflow_auto_start.sh" ]; then
    run_perf_test \
        "Workflow auto-start hook execution" \
        "bash .claude/hooks/workflow_auto_start.sh --check 2>/dev/null || true" \
        $THRESHOLD_NORMAL \
        "normal"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 4: Validation Operations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Category 4: Validation Performance${NC}"

# Shell syntax check
TEST_SHELL="$TEMP_TEST_DIR/test_shell.sh"
cat > "$TEST_SHELL" << 'EOF'
#!/bin/bash
set -euo pipefail
echo "test"
EOF

run_perf_test \
    "Shell syntax validation (bash -n)" \
    "bash -n $TEST_SHELL" \
    $THRESHOLD_FAST \
    "fast"

# JSON validation
if [ -f "package.json" ]; then
    run_perf_test \
        "JSON validation (package.json)" \
        "python3 -m json.tool package.json >/dev/null" \
        $THRESHOLD_FAST \
        "fast"
fi

# YAML validation
if compgen -G ".github/workflows/*.yml" > /dev/null; then
    FIRST_WORKFLOW=$(find .github/workflows -name "*.yml" -type f | head -1)
    if [ -n "$FIRST_WORKFLOW" ]; then
        run_perf_test \
            "YAML validation (workflow file)" \
            "python3 -c \"import yaml; yaml.safe_load(open('$FIRST_WORKFLOW'))\"" \
            $THRESHOLD_FAST \
            "fast"
    fi
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 5: File Operations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Category 5: File Operations${NC}"

run_perf_test \
    "Find all shell scripts" \
    "find .claude/hooks -name '*.sh' -type f" \
    $THRESHOLD_NORMAL \
    "normal"

run_perf_test \
    "Grep for pattern in hooks" \
    "grep -r 'set -e' .claude/hooks/ 2>/dev/null || true" \
    $THRESHOLD_NORMAL \
    "normal"

run_perf_test \
    "Count lines in all hooks" \
    "find .claude/hooks -name '*.sh' -exec wc -l {} + 2>/dev/null | tail -1" \
    $THRESHOLD_NORMAL \
    "normal"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Category 6: Concurrent Operations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Category 6: Concurrent Operation Overhead${NC}"

run_perf_test \
    "Multiple git status calls (sequential)" \
    "for i in {1..5}; do git status >/dev/null 2>&1; done" \
    $THRESHOLD_CRITICAL \
    "critical"

run_perf_test \
    "File lock creation/deletion" \
    "for i in {1..10}; do touch $TEMP_TEST_DIR/lock.\$i; rm $TEMP_TEST_DIR/lock.\$i; done" \
    $THRESHOLD_NORMAL \
    "normal"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Performance Summary & Metrics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Performance Test Summary              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total tests:   $test_count"
echo -e "${GREEN}Passed:        $pass_count${NC}"
echo -e "${YELLOW}Warnings:      $warn_count${NC}"
echo -e "${RED}Failed:        $fail_count${NC}"
echo ""

# Calculate pass rate
if [ $test_count -gt 0 ]; then
    pass_rate=$(( (pass_count + warn_count) * 100 / test_count ))
    echo -e "Pass rate:     ${pass_rate}% (including warnings as acceptable)"
fi

echo ""

if [ $fail_count -eq 0 ]; then
    if [ $warn_count -eq 0 ]; then
        echo -e "${GREEN}✅ All performance tests passed!${NC}"
        echo -e "${GREEN}   System performance is excellent.${NC}"
    else
        echo -e "${YELLOW}⚠ Performance tests passed with warnings${NC}"
        echo -e "${YELLOW}   Some operations are slower than optimal but acceptable.${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ $fail_count performance test(s) failed${NC}"
    echo -e "${RED}   Some operations are too slow and may impact user experience.${NC}"
    exit 1
fi
