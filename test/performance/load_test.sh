#!/usr/bin/env bash
# load_test.sh - Load testing for CE CLI system
# Simulates heavy concurrent usage and measures system behavior
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

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  CE CLI Load Testing${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# Helper functions
# ============================================================================

cleanup_test_branches() {
    local prefix="$1"

    git checkout main &>/dev/null || git checkout master &>/dev/null || true

    # Delete all test branches
    git branch | grep "${prefix}" | xargs -r git branch -D 2>/dev/null || true
}

get_system_metrics() {
    local cpu_usage
    local mem_usage
    local load_avg

    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')

    echo "CPU:${cpu_usage}% MEM:${mem_usage}% LOAD:${load_avg}"
}

# ============================================================================
# Load Test 1: Concurrent Terminal Operations
# ============================================================================

load_test_concurrent_terminals() {
    local num_terminals="$1"

    echo -e "${YELLOW}🔥 Load Test 1: ${num_terminals} Concurrent Terminals${NC}"
    echo ""

    local prefix="load-test-t${num_terminals}"
    local log_file="${RESULTS_DIR}/load_${num_terminals}_terminals.log"

    cleanup_test_branches "${prefix}"

    local start_metrics
    start_metrics=$(get_system_metrics)
    echo "  System metrics before: ${start_metrics}"

    local start_ns
    start_ns=$(date +%s%N)

    # Launch concurrent terminals
    local pids=()
    for ((i=1; i<=num_terminals; i++)); do
        (
            export CE_TERMINAL_ID="load-term-${i}"
            local branch="${prefix}-${i}-$$"

            "${CE_BIN}" start "${branch}" &>/dev/null || true
            "${CE_BIN}" status &>/dev/null || true
            "${CE_BIN}" validate &>/dev/null || true

            # Cleanup immediately
            git checkout main &>/dev/null 2>&1 || true
            git branch -D "${branch}" &>/dev/null 2>&1 || true
        ) &
        pids+=($!)
    done

    # Wait for all to complete
    local failures=0
    for pid in "${pids[@]}"; do
        if ! wait ${pid}; then
            ((failures++))
        fi
    done

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    local end_metrics
    end_metrics=$(get_system_metrics)
    echo "  System metrics after: ${end_metrics}"

    echo "  Duration: ${duration_ms}ms"
    echo "  Failures: ${failures}/${num_terminals}"
    echo "  Throughput: $((num_terminals * 1000 / duration_ms)) ops/sec"

    if (( failures == 0 )); then
        echo -e "${GREEN}  ✓ All terminals completed successfully${NC}"
    else
        echo -e "${YELLOW}  ⚠ ${failures} terminal(s) failed${NC}"
    fi

    cleanup_test_branches "${prefix}"

    echo ""
    echo "${duration_ms} ${failures}"
}

# ============================================================================
# Load Test 2: Rapid Command Execution
# ============================================================================

load_test_rapid_commands() {
    local num_commands="$1"

    echo -e "${YELLOW}🔥 Load Test 2: ${num_commands} Rapid Commands${NC}"
    echo ""

    local log_file="${RESULTS_DIR}/load_rapid_${num_commands}.log"

    local start_metrics
    start_metrics=$(get_system_metrics)
    echo "  System metrics before: ${start_metrics}"

    local start_ns
    start_ns=$(date +%s%N)

    # Execute rapid commands
    local failures=0
    for ((i=1; i<=num_commands; i++)); do
        if ! "${CE_BIN}" status &>/dev/null; then
            ((failures++))
        fi
    done

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    local end_metrics
    end_metrics=$(get_system_metrics)
    echo "  System metrics after: ${end_metrics}"

    echo "  Duration: ${duration_ms}ms"
    echo "  Failures: ${failures}/${num_commands}"
    echo "  Throughput: $((num_commands * 1000 / duration_ms)) ops/sec"
    echo "  Average: $((duration_ms / num_commands))ms per command"

    if (( failures == 0 )); then
        echo -e "${GREEN}  ✓ All commands completed successfully${NC}"
    else
        echo -e "${YELLOW}  ⚠ ${failures} command(s) failed${NC}"
    fi

    echo ""
    echo "${duration_ms} ${failures}"
}

# ============================================================================
# Load Test 3: State File Stress
# ============================================================================

load_test_state_stress() {
    local num_sessions="$1"

    echo -e "${YELLOW}🔥 Load Test 3: ${num_sessions} Session State Files${NC}"
    echo ""

    local state_dir=".workflow/cli/state/sessions"
    mkdir -p "${state_dir}"

    # Create session files
    echo "  Creating ${num_sessions} session files..."
    local start_create
    start_create=$(date +%s%N)

    for ((i=1; i<=num_sessions; i++)); do
        cat > "${state_dir}/stress-test-${i}.state" <<EOF
terminal_id: "stress-test-${i}"
branch: "stress-branch-${i}"
phase: "P$((RANDOM % 6 + 1))"
status: "active"
started_at: "$(date -Iseconds)"
last_activity: "$(date -Iseconds)"
gates_passed: []
files_modified: []
locks_held: []
metrics:
  commits: $((RANDOM % 100))
  lines_added: $((RANDOM % 1000))
  lines_deleted: $((RANDOM % 500))
EOF
    done

    local end_create
    end_create=$(date +%s%N)
    local create_time=$(( (end_create - start_create) / 1000000 ))

    echo "  Created ${num_sessions} files in ${create_time}ms"

    # Measure status operation with large state
    echo "  Testing operations with ${num_sessions} sessions..."

    local start_metrics
    start_metrics=$(get_system_metrics)
    echo "  System metrics before: ${start_metrics}"

    local start_op
    start_op=$(date +%s%N)

    "${CE_BIN}" status &>/dev/null || true

    local end_op
    end_op=$(date +%s%N)
    local op_time=$(( (end_op - start_op) / 1000000 ))

    local end_metrics
    end_metrics=$(get_system_metrics)
    echo "  System metrics after: ${end_metrics}"

    echo "  Status operation time: ${op_time}ms"

    # Check performance degradation
    local acceptable_time=$((num_sessions * 5))  # 5ms per session is acceptable
    if (( op_time <= acceptable_time )); then
        echo -e "${GREEN}  ✓ Performance acceptable: ${op_time}ms <= ${acceptable_time}ms${NC}"
    else
        echo -e "${YELLOW}  ⚠ Performance degraded: ${op_time}ms > ${acceptable_time}ms${NC}"
    fi

    # Cleanup
    echo "  Cleaning up ${num_sessions} session files..."
    for ((i=1; i<=num_sessions; i++)); do
        rm -f "${state_dir}/stress-test-${i}.state"
    done

    echo ""
    echo "${op_time}"
}

# ============================================================================
# Load Test 4: Lock Contention
# ============================================================================

load_test_lock_contention() {
    local num_concurrent="$1"

    echo -e "${YELLOW}🔥 Load Test 4: Lock Contention (${num_concurrent} concurrent)${NC}"
    echo ""

    local log_file="${RESULTS_DIR}/load_lock_contention.log"

    local start_metrics
    start_metrics=$(get_system_metrics)
    echo "  System metrics before: ${start_metrics}"

    local start_ns
    start_ns=$(date +%s%N)

    # Launch concurrent operations that require locks
    local pids=()
    local failures=0

    for ((i=1; i<=num_concurrent; i++)); do
        (
            # Try to acquire state lock
            if "${CE_BIN}" status &>/dev/null; then
                exit 0
            else
                exit 1
            fi
        ) &
        pids+=($!)
    done

    # Wait for all
    for pid in "${pids[@]}"; do
        if ! wait ${pid}; then
            ((failures++))
        fi
    done

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    local end_metrics
    end_metrics=$(get_system_metrics)
    echo "  System metrics after: ${end_metrics}"

    echo "  Duration: ${duration_ms}ms"
    echo "  Failures: ${failures}/${num_concurrent}"
    echo "  Lock contention detected: $((failures > 0))"

    if (( failures == 0 )); then
        echo -e "${GREEN}  ✓ No lock contention issues${NC}"
    else
        echo -e "${YELLOW}  ⚠ Lock contention caused ${failures} failures${NC}"
    fi

    echo ""
    echo "${duration_ms} ${failures}"
}

# ============================================================================
# Load Test 5: Memory Pressure
# ============================================================================

load_test_memory_pressure() {
    echo -e "${YELLOW}🔥 Load Test 5: Memory Pressure Test${NC}"
    echo ""

    local start_mem
    start_mem=$(free -m | grep Mem | awk '{print $3}')

    echo "  Initial memory usage: ${start_mem}MB"

    # Create large state to pressure memory
    local state_dir=".workflow/cli/state/sessions"
    mkdir -p "${state_dir}"

    echo "  Creating 1000 session files..."
    for ((i=1; i<=1000; i++)); do
        # Create larger state files with more data
        {
            echo "terminal_id: \"memory-test-${i}\""
            echo "branch: \"memory-branch-${i}\""
            echo "phase: \"P3\""
            echo "status: \"active\""
            echo "started_at: \"$(date -Iseconds)\""
            echo "last_activity: \"$(date -Iseconds)\""
            echo "gates_passed: []"
            echo "files_modified:"

            # Add many file entries
            for ((j=1; j<=50; j++)); do
                echo "  - \"file${j}.txt\""
            done

            echo "locks_held: []"
            echo "metrics:"
            echo "  commits: $((RANDOM % 1000))"
            echo "  lines_added: $((RANDOM % 10000))"
            echo "  lines_deleted: $((RANDOM % 5000))"
        } > "${state_dir}/memory-test-${i}.state"
    done

    local mid_mem
    mid_mem=$(free -m | grep Mem | awk '{print $3}')
    local mem_increase=$((mid_mem - start_mem))

    echo "  Memory after state creation: ${mid_mem}MB (+${mem_increase}MB)"

    # Test operations under memory pressure
    echo "  Testing operations under memory pressure..."

    local start_ns
    start_ns=$(date +%s%N)

    for ((i=1; i<=10; i++)); do
        "${CE_BIN}" status &>/dev/null || true
    done

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))
    local avg_time=$((duration_ms / 10))

    local end_mem
    end_mem=$(free -m | grep Mem | awk '{print $3}')

    echo "  Final memory usage: ${end_mem}MB"
    echo "  Average operation time: ${avg_time}ms"

    # Check for memory leaks
    local total_increase=$((end_mem - start_mem))
    echo "  Total memory increase: ${total_increase}MB"

    if (( total_increase > 100 )); then
        echo -e "${YELLOW}  ⚠ Significant memory increase detected${NC}"
    else
        echo -e "${GREEN}  ✓ Memory usage stable${NC}"
    fi

    # Cleanup
    echo "  Cleaning up 1000 session files..."
    for ((i=1; i<=1000; i++)); do
        rm -f "${state_dir}/memory-test-${i}.state"
    done

    echo ""
}

# ============================================================================
# Run load tests
# ============================================================================

cd "${PROJECT_ROOT}"

echo "Starting load tests..."
echo ""

# Test with increasing load
echo "=== Progressive Load Testing ==="
echo ""

# 5 concurrent terminals
result_5=$(load_test_concurrent_terminals 5)
time_5=$(echo "${result_5}" | awk '{print $1}')
fail_5=$(echo "${result_5}" | awk '{print $2}')

# 10 concurrent terminals
result_10=$(load_test_concurrent_terminals 10)
time_10=$(echo "${result_10}" | awk '{print $1}')
fail_10=$(echo "${result_10}" | awk '{print $2}')

# 20 concurrent terminals
result_20=$(load_test_concurrent_terminals 20)
time_20=$(echo "${result_20}" | awk '{print $1}')
fail_20=$(echo "${result_20}" | awk '{print $2}')

echo "=== Rapid Command Testing ==="
echo ""

# 100 rapid commands
result_100=$(load_test_rapid_commands 100)
time_100=$(echo "${result_100}" | awk '{print $1}')
fail_100=$(echo "${result_100}" | awk '{print $2}')

# 1000 rapid commands
result_1000=$(load_test_rapid_commands 1000)
time_1000=$(echo "${result_1000}" | awk '{print $1}')
fail_1000=$(echo "${result_1000}" | awk '{print $2}')

echo "=== State Stress Testing ==="
echo ""

# Various state sizes
load_test_state_stress 100
load_test_state_stress 500
load_test_state_stress 1000

echo "=== Lock Contention Testing ==="
echo ""

load_test_lock_contention 5
load_test_lock_contention 10
load_test_lock_contention 20

echo "=== Memory Pressure Testing ==="
echo ""

load_test_memory_pressure

# ============================================================================
# Generate summary report
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Load Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Concurrent Terminals:"
printf "  %3d terminals: %6dms (%d failures)\n" 5 "${time_5}" "${fail_5}"
printf "  %3d terminals: %6dms (%d failures)\n" 10 "${time_10}" "${fail_10}"
printf "  %3d terminals: %6dms (%d failures)\n" 20 "${time_20}" "${fail_20}"

echo ""
echo "Rapid Commands:"
printf "  %4d commands: %7dms (%d failures)\n" 100 "${time_100}" "${fail_100}"
printf "  %4d commands: %7dms (%d failures)\n" 1000 "${time_1000}" "${fail_1000}"

echo ""

# Calculate throughput degradation
if (( time_5 > 0 )); then
    local throughput_5=$((5 * 1000 / time_5))
    local throughput_20=$((20 * 1000 / time_20))
    local degradation=$((100 - (throughput_20 * 100 / throughput_5)))

    echo "Throughput Analysis:"
    echo "  5 terminals: ${throughput_5} ops/sec"
    echo "  20 terminals: ${throughput_20} ops/sec"
    echo "  Degradation: ${degradation}%"

    if (( degradation < 20 )); then
        echo -e "${GREEN}  ✓ Excellent scalability (< 20% degradation)${NC}"
    elif (( degradation < 50 )); then
        echo -e "${YELLOW}  ⚠ Acceptable scalability (< 50% degradation)${NC}"
    else
        echo -e "${RED}  ✗ Poor scalability (>= 50% degradation)${NC}"
    fi
fi

echo ""

# Save results
cat > "${RESULTS_DIR}/load_test_summary.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "concurrent_terminals": {
    "5": {"time_ms": ${time_5}, "failures": ${fail_5}},
    "10": {"time_ms": ${time_10}, "failures": ${fail_10}},
    "20": {"time_ms": ${time_20}, "failures": ${fail_20}}
  },
  "rapid_commands": {
    "100": {"time_ms": ${time_100}, "failures": ${fail_100}},
    "1000": {"time_ms": ${time_1000}, "failures": ${fail_1000}}
  }
}
EOF

echo "Results saved to: ${RESULTS_DIR}/load_test_summary.json"
