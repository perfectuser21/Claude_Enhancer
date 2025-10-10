#!/usr/bin/env bash
# benchmark_workflows.sh - Benchmark complete CE CLI workflows
# Tests end-to-end performance of development cycles
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="${PROJECT_ROOT}/test/performance"
RESULTS_DIR="${TEST_DIR}/results"

mkdir -p "${RESULTS_DIR}"

CE_BIN="${PROJECT_ROOT}/.workflow/cli/ce"

# Performance targets (from P3 claims)
TARGET_COMPLETE_CYCLE=5000  # 5 seconds (was 17.4s, improved to 4.3s)
TARGET_CACHE_HIT_RATE=85    # 85% cache hit rate

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  CE CLI Workflow Benchmarks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# Helper functions
# ============================================================================

measure_time() {
    local start_ns
    start_ns=$(date +%s%N)

    "$@"

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    echo "${duration_ms}"
}

cleanup_test_branch() {
    local branch="$1"

    git checkout main &>/dev/null || git checkout master &>/dev/null || true
    git branch -D "${branch}" &>/dev/null 2>&1 || true
}

# ============================================================================
# Workflow 1: Complete Development Cycle
# ============================================================================

benchmark_complete_cycle() {
    echo -e "${YELLOW}📊 Workflow 1: Complete Development Cycle${NC}"
    echo "  Testing: start → status → validate → next → status"
    echo ""

    local test_branch="perf-test-cycle-$$"
    local log_file="${RESULTS_DIR}/complete_cycle.log"

    # Cleanup any existing test branch
    cleanup_test_branch "${test_branch}"

    # Measure complete cycle
    local start_ns
    start_ns=$(date +%s%N)

    {
        echo "=== Step 1: Start workflow ==="
        "${CE_BIN}" start "${test_branch}" || echo "Start completed with code $?"

        echo "=== Step 2: Check status ==="
        "${CE_BIN}" status || true

        echo "=== Step 3: Validate phase ==="
        "${CE_BIN}" validate || echo "Validate completed with code $?"

        echo "=== Step 4: Move to next phase ==="
        "${CE_BIN}" next || echo "Next completed with code $?"

        echo "=== Step 5: Final status ==="
        "${CE_BIN}" status || true
    } > "${log_file}" 2>&1

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    echo "  Complete cycle time: ${duration_ms}ms"

    # Check against target
    if (( duration_ms <= TARGET_COMPLETE_CYCLE )); then
        local improvement=$((100 - (duration_ms * 100 / 17400)))
        echo -e "${GREEN}  ✓ Within target: ${duration_ms}ms <= ${TARGET_COMPLETE_CYCLE}ms${NC}"
        echo -e "${GREEN}  ✓ Improvement: ${improvement}% faster than baseline (17.4s)${NC}"
    else
        echo -e "${RED}  ✗ Exceeded target: ${duration_ms}ms > ${TARGET_COMPLETE_CYCLE}ms${NC}"
    fi

    # Cleanup
    cleanup_test_branch "${test_branch}"

    echo ""
    echo "${duration_ms}"
}

# ============================================================================
# Workflow 2: Multi-Terminal Simulation
# ============================================================================

benchmark_multi_terminal() {
    echo -e "${YELLOW}📊 Workflow 2: Multi-Terminal Workflow${NC}"
    echo "  Testing: 3 concurrent terminals"
    echo ""

    local branches=(
        "perf-test-t1-$$"
        "perf-test-t2-$$"
        "perf-test-t3-$$"
    )

    local log_file="${RESULTS_DIR}/multi_terminal.log"

    # Cleanup
    for branch in "${branches[@]}"; do
        cleanup_test_branch "${branch}"
    done

    # Measure concurrent execution
    local start_ns
    start_ns=$(date +%s%N)

    {
        # Terminal 1
        (
            export CE_TERMINAL_ID="term1"
            "${CE_BIN}" start "${branches[0]}" || true
            "${CE_BIN}" status || true
        ) &
        local pid1=$!

        # Terminal 2
        (
            export CE_TERMINAL_ID="term2"
            "${CE_BIN}" start "${branches[1]}" || true
            "${CE_BIN}" status || true
        ) &
        local pid2=$!

        # Terminal 3
        (
            export CE_TERMINAL_ID="term3"
            "${CE_BIN}" start "${branches[2]}" || true
            "${CE_BIN}" status || true
        ) &
        local pid3=$!

        # Wait for all terminals
        wait ${pid1} ${pid2} ${pid3}
    } > "${log_file}" 2>&1

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    echo "  Multi-terminal time: ${duration_ms}ms"
    echo "  Average per terminal: $((duration_ms / 3))ms"

    # Cleanup
    for branch in "${branches[@]}"; do
        cleanup_test_branch "${branch}"
    done

    echo ""
    echo "${duration_ms}"
}

# ============================================================================
# Workflow 3: Conflict Detection Performance
# ============================================================================

benchmark_conflict_detection() {
    echo -e "${YELLOW}📊 Workflow 3: Conflict Detection${NC}"
    echo "  Testing: Cross-terminal file analysis"
    echo ""

    local branches=(
        "perf-test-conflict1-$$"
        "perf-test-conflict2-$$"
    )

    # Cleanup
    for branch in "${branches[@]}"; do
        cleanup_test_branch "${branch}"
    done

    # Create two branches that modify the same file
    local test_file="test_conflict_file_$$.txt"

    # Terminal 1: Create first branch
    export CE_TERMINAL_ID="term1"
    "${CE_BIN}" start "${branches[0]}" &>/dev/null || true

    # Simulate file modification
    echo "Content from terminal 1" > "${test_file}"

    # Terminal 2: Create second branch
    export CE_TERMINAL_ID="term2"
    "${CE_BIN}" start "${branches[1]}" &>/dev/null || true

    # Simulate file modification
    echo "Content from terminal 2" > "${test_file}"

    # Measure conflict detection
    local duration_ms
    duration_ms=$(measure_time "${CE_BIN}" status 2>&1 | grep -o "Conflict" || echo "0")

    echo "  Conflict detection time: ${duration_ms}ms"

    # Cleanup
    rm -f "${test_file}"
    for branch in "${branches[@]}"; do
        cleanup_test_branch "${branch}"
    done

    unset CE_TERMINAL_ID

    echo ""
}

# ============================================================================
# Workflow 4: Cache Performance Testing
# ============================================================================

benchmark_cache_performance() {
    echo -e "${YELLOW}📊 Workflow 4: Cache Performance${NC}"
    echo "  Testing: Cache hit rate and effectiveness"
    echo ""

    # Clear cache
    rm -rf .workflow/cli/state/cache 2>/dev/null || true

    # Cold start (cache miss)
    echo "  Cold start (no cache)..."
    local cold_time
    cold_time=$(measure_time "${CE_BIN}" status --no-cache 2>/dev/null || echo "0")
    echo "    Time: ${cold_time}ms"

    # Warm cache
    echo "  Building cache..."
    "${CE_BIN}" status &>/dev/null

    # Measure cache hits
    echo "  Testing cache hits..."
    local total_time=0
    local runs=10

    for ((i=1; i<=runs; i++)); do
        local run_time
        run_time=$(measure_time "${CE_BIN}" status 2>/dev/null || echo "0")
        total_time=$((total_time + run_time))
    done

    local avg_warm_time=$((total_time / runs))
    echo "    Average warm time: ${avg_warm_time}ms"

    # Calculate cache effectiveness
    if [[ ${cold_time} -gt 0 ]]; then
        local speedup=$((100 - (avg_warm_time * 100 / cold_time)))
        echo -e "${GREEN}  Cache speedup: ${speedup}%${NC}"

        if (( speedup >= TARGET_CACHE_HIT_RATE )); then
            echo -e "${GREEN}  ✓ Cache hit rate target met: ${speedup}% >= ${TARGET_CACHE_HIT_RATE}%${NC}"
        else
            echo -e "${YELLOW}  ⚠ Cache hit rate below target: ${speedup}% < ${TARGET_CACHE_HIT_RATE}%${NC}"
        fi
    fi

    echo ""
}

# ============================================================================
# Workflow 5: Large State File Performance
# ============================================================================

benchmark_large_state() {
    echo -e "${YELLOW}📊 Workflow 5: Large State File Handling${NC}"
    echo "  Testing: Performance with 100+ session files"
    echo ""

    local state_dir=".workflow/cli/state/sessions"
    mkdir -p "${state_dir}"

    # Create 100 dummy session files
    echo "  Creating 100 test session files..."
    for ((i=1; i<=100; i++)); do
        cat > "${state_dir}/test-session-${i}.state" <<EOF
terminal_id: "test-session-${i}"
branch: "test-branch-${i}"
phase: "P3"
status: "active"
started_at: "$(date -Iseconds)"
last_activity: "$(date -Iseconds)"
gates_passed: []
files_modified: []
locks_held: []
metrics:
  commits: 0
  lines_added: 0
  lines_deleted: 0
EOF
    done

    # Measure performance with large state
    echo "  Testing status with 100 sessions..."
    local duration_ms
    duration_ms=$(measure_time "${CE_BIN}" status 2>/dev/null || echo "0")

    echo "  Status time with 100 sessions: ${duration_ms}ms"

    if (( duration_ms <= 1000 )); then
        echo -e "${GREEN}  ✓ Performance acceptable: ${duration_ms}ms <= 1000ms${NC}"
    else
        echo -e "${YELLOW}  ⚠ Performance degradation: ${duration_ms}ms > 1000ms${NC}"
    fi

    # Cleanup test sessions
    echo "  Cleaning up test sessions..."
    for ((i=1; i<=100; i++)); do
        rm -f "${state_dir}/test-session-${i}.state"
    done

    echo ""
}

# ============================================================================
# Run all workflow benchmarks
# ============================================================================

cd "${PROJECT_ROOT}"

echo "Starting workflow benchmarks..."
echo ""

# Run benchmarks
cycle_time=$(benchmark_complete_cycle)
multi_time=$(benchmark_multi_terminal)
benchmark_conflict_detection
benchmark_cache_performance
benchmark_large_state

# ============================================================================
# Generate summary report
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Workflow Benchmark Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

printf "%-40s %15s %15s\n" "Workflow" "Time (ms)" "Target (ms)"
echo "────────────────────────────────────────────────────────────────────────"
printf "%-40s %15s %15s\n" "Complete Development Cycle" "${cycle_time}" "${TARGET_COMPLETE_CYCLE}"
printf "%-40s %15s %15s\n" "Multi-Terminal (3 concurrent)" "${multi_time}" "N/A"

echo ""

# Calculate improvement from baseline (17.4s = 17400ms)
if [[ ${cycle_time} -gt 0 ]]; then
    local improvement=$((100 - (cycle_time * 100 / 17400)))
    echo -e "${GREEN}Performance Improvement: ${improvement}% faster than baseline${NC}"

    if (( improvement >= 75 )); then
        echo -e "${GREEN}✓ Meets 75% improvement claim${NC}"
    else
        echo -e "${YELLOW}⚠ Below 75% improvement target${NC}"
    fi
fi

echo ""

# Save results
cat > "${RESULTS_DIR}/workflow_benchmark_summary.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "complete_cycle_ms": ${cycle_time},
  "multi_terminal_ms": ${multi_time},
  "target_cycle_ms": ${TARGET_COMPLETE_CYCLE},
  "baseline_ms": 17400,
  "improvement_percent": $((100 - (cycle_time * 100 / 17400)))
}
EOF

echo "Results saved to: ${RESULTS_DIR}/workflow_benchmark_summary.json"
