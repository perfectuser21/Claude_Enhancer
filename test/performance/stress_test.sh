#!/usr/bin/env bash
# stress_test.sh - Stress testing for CE CLI
# Push system to limits and identify breaking points
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
echo -e "${BLUE}  CE CLI Stress Testing${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# System monitoring
# ============================================================================

monitor_system() {
    local interval="${1:-5}"
    local duration="${2:-60}"
    local output_file="${3:-${RESULTS_DIR}/system_monitor.log}"

    echo "timestamp,cpu_percent,mem_percent,disk_io,load_avg" > "${output_file}"

    local end_time=$(($(date +%s) + duration))

    while [[ $(date +%s) -lt ${end_time} ]]; do
        local timestamp
        timestamp=$(date +%s)

        local cpu_percent
        cpu_percent=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

        local mem_percent
        mem_percent=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')

        local disk_io
        disk_io=$(iostat -d 1 1 | tail -1 | awk '{print $3+$4}' || echo "0")

        local load_avg
        load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')

        echo "${timestamp},${cpu_percent},${mem_percent},${disk_io},${load_avg}" >> "${output_file}"

        sleep "${interval}"
    done
}

# ============================================================================
# Stress Test 1: Maximum Concurrent Terminals
# ============================================================================

stress_test_max_terminals() {
    echo -e "${YELLOW}🔥 Stress Test 1: Maximum Concurrent Terminals${NC}"
    echo "  Finding breaking point for concurrent terminal operations"
    echo ""

    local max_tested=0
    local max_successful=0
    local breaking_point=0

    # Test with increasing numbers: 10, 20, 50, 100, 200
    local test_sizes=(10 20 50 100 200)

    for num_terminals in "${test_sizes[@]}"; do
        echo "  Testing ${num_terminals} concurrent terminals..."

        max_tested=${num_terminals}

        # Start system monitoring in background
        monitor_system 1 30 "${RESULTS_DIR}/stress_${num_terminals}_terminals_system.log" &
        local monitor_pid=$!

        local prefix="stress-max-${num_terminals}"
        local start_ns
        start_ns=$(date +%s%N)

        # Launch concurrent terminals
        local pids=()
        local failures=0

        for ((i=1; i<=num_terminals; i++)); do
            (
                export CE_TERMINAL_ID="stress-term-${i}"
                local branch="${prefix}-${i}-$$"

                if "${CE_BIN}" start "${branch}" &>/dev/null; then
                    "${CE_BIN}" status &>/dev/null || true
                    git checkout main &>/dev/null 2>&1 || true
                    git branch -D "${branch}" &>/dev/null 2>&1 || true
                    exit 0
                else
                    exit 1
                fi
            ) &
            pids+=($!)

            # Small delay to avoid overwhelming the system
            sleep 0.01
        done

        # Wait for all
        for pid in "${pids[@]}"; do
            if ! wait ${pid}; then
                ((failures++))
            fi
        done

        # Stop monitoring
        kill ${monitor_pid} 2>/dev/null || true
        wait ${monitor_pid} 2>/dev/null || true

        local end_ns
        end_ns=$(date +%s%N)
        local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

        local success_rate=$(( (num_terminals - failures) * 100 / num_terminals ))

        echo "    Duration: ${duration_ms}ms"
        echo "    Failures: ${failures}/${num_terminals}"
        echo "    Success rate: ${success_rate}%"

        if (( success_rate >= 90 )); then
            echo -e "${GREEN}    ✓ System stable at ${num_terminals} terminals${NC}"
            max_successful=${num_terminals}
        else
            echo -e "${RED}    ✗ System unstable at ${num_terminals} terminals${NC}"
            breaking_point=${num_terminals}
            break
        fi

        echo ""

        # Cleanup
        git checkout main &>/dev/null 2>&1 || true
        git branch | grep "${prefix}" | xargs -r git branch -D 2>/dev/null || true

        # Cool down period
        sleep 2
    done

    echo "  Maximum tested: ${max_tested} terminals"
    echo "  Maximum successful: ${max_successful} terminals"

    if [[ ${breaking_point} -gt 0 ]]; then
        echo -e "  ${RED}Breaking point: ${breaking_point} terminals${NC}"
    else
        echo -e "  ${GREEN}No breaking point found (stable up to ${max_tested})${NC}"
    fi

    echo ""
}

# ============================================================================
# Stress Test 2: Rapid Fire Commands
# ============================================================================

stress_test_rapid_fire() {
    echo -e "${YELLOW}🔥 Stress Test 2: Rapid Fire Commands${NC}"
    echo "  Executing commands as fast as possible"
    echo ""

    # Start monitoring
    monitor_system 1 60 "${RESULTS_DIR}/stress_rapid_fire_system.log" &
    local monitor_pid=$!

    local target_commands=10000
    local batch_size=100

    echo "  Target: ${target_commands} commands"
    echo "  Batch size: ${batch_size}"
    echo ""

    local start_ns
    start_ns=$(date +%s%N)

    local completed=0
    local failures=0

    for ((batch=1; batch<=target_commands/batch_size; batch++)); do
        echo -n "  Batch ${batch}..."

        local batch_start
        batch_start=$(date +%s%N)

        for ((i=1; i<=batch_size; i++)); do
            if "${CE_BIN}" status &>/dev/null; then
                ((completed++))
            else
                ((failures++))
            fi
        done

        local batch_end
        batch_end=$(date +%s%N)
        local batch_time=$(( (batch_end - batch_start) / 1000000 ))

        echo " ${batch_time}ms (${failures} failures)"

        # Check if system is degrading
        if (( batch_time > 5000 )); then
            echo -e "${RED}  ✗ Performance severely degraded, stopping test${NC}"
            break
        fi
    done

    # Stop monitoring
    kill ${monitor_pid} 2>/dev/null || true
    wait ${monitor_pid} 2>/dev/null || true

    local end_ns
    end_ns=$(date +%s%N)
    local total_time=$(( (end_ns - start_ns) / 1000000 ))

    echo ""
    echo "  Completed: ${completed} commands"
    echo "  Failures: ${failures} commands"
    echo "  Total time: ${total_time}ms"

    if [[ ${completed} -gt 0 ]]; then
        local throughput=$((completed * 1000 / total_time))
        local avg_time=$((total_time / completed))
        local failure_rate=$((failures * 100 / (completed + failures)))

        echo "  Throughput: ${throughput} ops/sec"
        echo "  Average time: ${avg_time}ms per command"
        echo "  Failure rate: ${failure_rate}%"

        if (( failure_rate < 1 )); then
            echo -e "${GREEN}  ✓ System handled rapid fire well (< 1% failures)${NC}"
        else
            echo -e "${YELLOW}  ⚠ System struggled with rapid fire (${failure_rate}% failures)${NC}"
        fi
    fi

    echo ""
}

# ============================================================================
# Stress Test 3: Memory Exhaustion
# ============================================================================

stress_test_memory_exhaustion() {
    echo -e "${YELLOW}🔥 Stress Test 3: Memory Exhaustion${NC}"
    echo "  Creating massive state to test memory limits"
    echo ""

    local state_dir=".workflow/cli/state/sessions"
    mkdir -p "${state_dir}"

    local initial_mem
    initial_mem=$(free -m | grep Mem | awk '{print $3}')
    echo "  Initial memory: ${initial_mem}MB"

    # Create increasingly large state files
    local sizes=(1000 5000 10000)

    for num_sessions in "${sizes[@]}"; do
        echo "  Creating ${num_sessions} session files..."

        local create_start
        create_start=$(date +%s%N)

        for ((i=1; i<=num_sessions; i++)); do
            {
                echo "terminal_id: \"mem-stress-${i}\""
                echo "branch: \"mem-branch-${i}\""
                echo "phase: \"P3\""
                echo "status: \"active\""
                echo "started_at: \"$(date -Iseconds)\""
                echo "files_modified:"

                # Add 100 file entries per session
                for ((j=1; j<=100; j++)); do
                    echo "  - \"src/module${i}/file${j}.txt\""
                done

                echo "metrics:"
                echo "  commits: ${i}"
                echo "  lines_added: $((i * 100))"
            } > "${state_dir}/mem-stress-${i}.state"

            # Progress indicator every 1000 files
            if (( i % 1000 == 0 )); then
                echo -n "."
            fi
        done

        echo ""

        local create_end
        create_end=$(date +%s%N)
        local create_time=$(( (create_end - create_start) / 1000000 ))

        echo "    Created in: ${create_time}ms"

        local current_mem
        current_mem=$(free -m | grep Mem | awk '{print $3}')
        local mem_increase=$((current_mem - initial_mem))

        echo "    Current memory: ${current_mem}MB (+${mem_increase}MB)"

        # Test operations under memory pressure
        echo "    Testing operations..."

        local op_start
        op_start=$(date +%s%N)

        "${CE_BIN}" status &>/dev/null || true

        local op_end
        op_end=$(date +%s%N)
        local op_time=$(( (op_end - op_start) / 1000000 ))

        echo "    Operation time: ${op_time}ms"

        # Check if system is still responsive
        if (( op_time > 10000 )); then
            echo -e "${RED}    ✗ System severely degraded, stopping test${NC}"
            break
        elif (( op_time > 5000 )); then
            echo -e "${YELLOW}    ⚠ Significant performance degradation${NC}"
        else
            echo -e "${GREEN}    ✓ System still responsive${NC}"
        fi

        echo ""
    done

    # Cleanup
    echo "  Cleaning up session files..."
    rm -f "${state_dir}"/mem-stress-*.state

    local final_mem
    final_mem=$(free -m | grep Mem | awk '{print $3}')
    echo "  Final memory: ${final_mem}MB"

    echo ""
}

# ============================================================================
# Stress Test 4: Cache Thrashing
# ============================================================================

stress_test_cache_thrashing() {
    echo -e "${YELLOW}🔥 Stress Test 4: Cache Thrashing${NC}"
    echo "  Rapid cache invalidation and rebuild"
    echo ""

    local cache_dir=".workflow/cli/state/cache"
    local state_file=".workflow/cli/state/global.state.yml"

    echo "  Running 100 cycles of cache build/invalidate..."

    local start_ns
    start_ns=$(date +%s%N)

    for ((i=1; i<=100; i++)); do
        # Build cache
        "${CE_BIN}" status &>/dev/null || true

        # Invalidate by touching state file
        touch "${state_file}"

        # Progress indicator
        if (( i % 10 == 0 )); then
            echo -n "."
        fi
    done

    echo ""

    local end_ns
    end_ns=$(date +%s%N)
    local total_time=$(( (end_ns - start_ns) / 1000000 ))

    echo "  Total time: ${total_time}ms"
    echo "  Average per cycle: $((total_time / 100))ms"

    # Check cache health
    local cache_entries
    cache_entries=$(find "${cache_dir}" -name "*.cache" 2>/dev/null | wc -l)

    echo "  Final cache entries: ${cache_entries}"

    if (( total_time / 100 < 1000 )); then
        echo -e "${GREEN}  ✓ Cache handles thrashing well${NC}"
    else
        echo -e "${YELLOW}  ⚠ Cache thrashing causes performance issues${NC}"
    fi

    echo ""
}

# ============================================================================
# Stress Test 5: Disk I/O Saturation
# ============================================================================

stress_test_disk_io() {
    echo -e "${YELLOW}🔥 Stress Test 5: Disk I/O Saturation${NC}"
    echo "  Heavy concurrent file operations"
    echo ""

    local test_dir="${RESULTS_DIR}/disk_stress"
    mkdir -p "${test_dir}"

    # Start monitoring
    monitor_system 1 30 "${RESULTS_DIR}/stress_disk_io_system.log" &
    local monitor_pid=$!

    echo "  Creating 1000 concurrent file operations..."

    local start_ns
    start_ns=$(date +%s%N)

    # Launch concurrent file operations
    local pids=()

    for ((i=1; i<=1000; i++)); do
        (
            # Write
            echo "Test data ${i}" > "${test_dir}/file_${i}.txt"

            # Read
            cat "${test_dir}/file_${i}.txt" >/dev/null

            # Modify
            echo "Modified ${i}" >> "${test_dir}/file_${i}.txt"

            # Delete
            rm -f "${test_dir}/file_${i}.txt"
        ) &
        pids+=($!)

        # Batch launch to avoid fork bomb
        if (( i % 100 == 0 )); then
            wait
            pids=()
        fi
    done

    wait

    # Stop monitoring
    kill ${monitor_pid} 2>/dev/null || true
    wait ${monitor_pid} 2>/dev/null || true

    local end_ns
    end_ns=$(date +%s%N)
    local total_time=$(( (end_ns - start_ns) / 1000000 ))

    echo "  Total time: ${total_time}ms"
    echo "  I/O operations: 4000 (write, read, modify, delete)"
    echo "  Throughput: $((4000 * 1000 / total_time)) ops/sec"

    # Cleanup
    rm -rf "${test_dir}"

    echo ""
}

# ============================================================================
# Run stress tests
# ============================================================================

cd "${PROJECT_ROOT}"

echo "Starting stress tests..."
echo "⚠️  WARNING: These tests will push your system to its limits"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Stress tests cancelled"
    exit 0
fi

echo ""

stress_test_max_terminals
stress_test_rapid_fire
stress_test_memory_exhaustion
stress_test_cache_thrashing
stress_test_disk_io

# ============================================================================
# Generate summary report
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Stress Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "All stress tests completed!"
echo ""
echo "Results saved to: ${RESULTS_DIR}/"
echo ""
echo "Review the following files for detailed analysis:"
echo "  - stress_*_terminals_system.log  (system metrics during terminal stress)"
echo "  - stress_rapid_fire_system.log   (system metrics during rapid fire)"
echo "  - stress_disk_io_system.log      (system metrics during I/O stress)"
echo ""

# Generate analysis
if command -v gnuplot &>/dev/null; then
    echo "Generating charts with gnuplot..."
    # TODO: Create gnuplot scripts for visualization
fi

echo -e "${GREEN}Stress testing complete!${NC}"
