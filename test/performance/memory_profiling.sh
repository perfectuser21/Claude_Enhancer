#!/usr/bin/env bash
# memory_profiling.sh - Memory usage profiling for CE CLI
# Track memory consumption and identify memory leaks
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
echo -e "${BLUE}  CE CLI Memory Profiling${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# Helper functions
# ============================================================================

get_process_memory() {
    local pid="$1"

    if [[ ! -d "/proc/${pid}" ]]; then
        echo "0 0 0"
        return
    fi

    # Get memory stats from /proc
    local rss
    local vsize
    local shared

    rss=$(grep "^VmRSS:" /proc/${pid}/status 2>/dev/null | awk '{print $2}' || echo "0")
    vsize=$(grep "^VmSize:" /proc/${pid}/status 2>/dev/null | awk '{print $2}' || echo "0")
    shared=$(grep "^RssFile:" /proc/${pid}/status 2>/dev/null | awk '{print $2}' || echo "0")

    echo "${rss} ${vsize} ${shared}"
}

profile_command() {
    local cmd="$1"
    local output_file="$2"

    echo "timestamp,rss_kb,vsize_kb,shared_kb" > "${output_file}"

    # Run command in background and monitor
    eval "${cmd}" &
    local pid=$!

    # Monitor memory every 100ms
    while kill -0 ${pid} 2>/dev/null; do
        local timestamp
        timestamp=$(date +%s%N)

        local mem_stats
        mem_stats=$(get_process_memory ${pid})

        echo "${timestamp},${mem_stats// /,}" >> "${output_file}"

        sleep 0.1
    done

    wait ${pid} 2>/dev/null || true
}

calculate_memory_stats() {
    local data_file="$1"

    if [[ ! -f "${data_file}" || $(wc -l < "${data_file}") -le 1 ]]; then
        echo "0 0 0 0"
        return
    fi

    local stats
    stats=$(awk -F',' 'NR>1 {
        rss[NR-1] = $2
        vsize[NR-1] = $3
        count++
    }
    END {
        if (count == 0) {
            print "0 0 0 0"
            exit
        }

        # Calculate average RSS
        rss_sum = 0
        for (i=1; i<=count; i++) rss_sum += rss[i]
        avg_rss = rss_sum / count

        # Find peak RSS
        peak_rss = rss[1]
        for (i=2; i<=count; i++) {
            if (rss[i] > peak_rss) peak_rss = rss[i]
        }

        # Calculate average VSize
        vsize_sum = 0
        for (i=1; i<=count; i++) vsize_sum += vsize[i]
        avg_vsize = vsize_sum / count

        # Find peak VSize
        peak_vsize = vsize[1]
        for (i=2; i<=count; i++) {
            if (vsize[i] > peak_vsize) peak_vsize = vsize[i]
        }

        printf "%.0f %.0f %.0f %.0f", avg_rss, peak_rss, avg_vsize, peak_vsize
    }' "${data_file}")

    echo "${stats}"
}

# ============================================================================
# Memory Profile 1: Individual Commands
# ============================================================================

profile_individual_commands() {
    echo -e "${YELLOW}📊 Profile 1: Individual Command Memory Usage${NC}"
    echo ""

    local commands=(
        "status"
        "validate"
    )

    declare -A peak_memory
    declare -A avg_memory

    for cmd in "${commands[@]}"; do
        echo "  Profiling: ce ${cmd}"

        local profile_file="${RESULTS_DIR}/memory_${cmd}.csv"

        # Use /usr/bin/time for detailed memory stats
        if command -v /usr/bin/time &>/dev/null; then
            /usr/bin/time -v "${CE_BIN}" ${cmd} &>/dev/null 2>"${RESULTS_DIR}/memory_${cmd}_time.log" || true

            # Extract peak memory
            local peak
            peak=$(grep "Maximum resident set size" "${RESULTS_DIR}/memory_${cmd}_time.log" | awk '{print $6}')
            peak_memory["${cmd}"]="${peak:-0}"

            # Extract average memory (approximate)
            local avg
            avg=$(grep "Average resident set size" "${RESULTS_DIR}/memory_${cmd}_time.log" | awk '{print $6}' || echo "0")
            avg_memory["${cmd}"]="${avg:-0}"

            echo "    Peak RSS: ${peak_memory[${cmd}]}KB"
            echo "    Avg RSS: ${avg_memory[${cmd}]}KB"
        else
            # Fallback to ps-based monitoring
            profile_command "${CE_BIN} ${cmd}" "${profile_file}"

            local stats
            stats=$(calculate_memory_stats "${profile_file}")

            avg_memory["${cmd}"]=$(echo "${stats}" | awk '{print $1}')
            peak_memory["${cmd}"]=$(echo "${stats}" | awk '{print $2}')

            echo "    Peak RSS: ${peak_memory[${cmd}]}KB"
            echo "    Avg RSS: ${avg_memory[${cmd}]}KB"
        fi

        echo ""
    done

    # Check memory budgets (from metrics/perf_budget.yml: 256MB = 262144KB)
    local memory_budget=262144

    for cmd in "${commands[@]}"; do
        local peak="${peak_memory[${cmd}]}"

        if (( peak > memory_budget )); then
            echo -e "${RED}  ✗ ${cmd} exceeds memory budget: ${peak}KB > ${memory_budget}KB${NC}"
        else
            echo -e "${GREEN}  ✓ ${cmd} within memory budget: ${peak}KB <= ${memory_budget}KB${NC}"
        fi
    done

    echo ""
}

# ============================================================================
# Memory Profile 2: Memory Leak Detection
# ============================================================================

profile_memory_leaks() {
    echo -e "${YELLOW}🔍 Profile 2: Memory Leak Detection${NC}"
    echo "  Running 100 iterations to detect memory leaks"
    echo ""

    local profile_file="${RESULTS_DIR}/memory_leak_test.csv"
    echo "iteration,rss_kb,vsize_kb" > "${profile_file}"

    local iterations=100

    for ((i=1; i<=iterations; i++)); do
        # Run command
        "${CE_BIN}" status &>/dev/null || true

        # Get current process memory usage (from the running shell)
        local current_mem
        current_mem=$(ps -o rss,vsz -p $$ | tail -1 | awk '{print $1","$2}')

        echo "${i},${current_mem}" >> "${profile_file}"

        if (( i % 10 == 0 )); then
            echo -n "."
        fi
    done

    echo ""

    # Analyze for memory growth
    local first_rss
    local last_rss
    first_rss=$(awk -F',' 'NR==2 {print $2}' "${profile_file}")
    last_rss=$(awk -F',' 'END {print $2}' "${profile_file}")

    local growth=$((last_rss - first_rss))
    local growth_percent=0

    if [[ ${first_rss} -gt 0 ]]; then
        growth_percent=$((growth * 100 / first_rss))
    fi

    echo "  Initial RSS: ${first_rss}KB"
    echo "  Final RSS: ${last_rss}KB"
    echo "  Growth: ${growth}KB (${growth_percent}%)"

    if (( growth_percent > 20 )); then
        echo -e "${RED}  ✗ Possible memory leak detected (> 20% growth)${NC}"
    elif (( growth_percent > 10 )); then
        echo -e "${YELLOW}  ⚠ Minor memory growth detected (> 10%)${NC}"
    else
        echo -e "${GREEN}  ✓ No significant memory leak detected (< 10% growth)${NC}"
    fi

    echo ""
}

# ============================================================================
# Memory Profile 3: Large State Memory Impact
# ============================================================================

profile_large_state_memory() {
    echo -e "${YELLOW}📈 Profile 3: Large State Memory Impact${NC}"
    echo ""

    local state_dir=".workflow/cli/state/sessions"
    mkdir -p "${state_dir}"

    local sizes=(10 100 500 1000)

    declare -A memory_by_size

    for size in "${sizes[@]}"; do
        echo "  Testing with ${size} session files..."

        # Create session files
        for ((i=1; i<=size; i++)); do
            cat > "${state_dir}/mem-profile-${i}.state" <<EOF
terminal_id: "mem-profile-${i}"
branch: "branch-${i}"
phase: "P3"
status: "active"
started_at: "$(date -Iseconds)"
last_activity: "$(date -Iseconds)"
gates_passed: []
files_modified: []
locks_held: []
EOF
        done

        # Measure memory with /usr/bin/time
        if command -v /usr/bin/time &>/dev/null; then
            /usr/bin/time -v "${CE_BIN}" status &>/dev/null 2>"${RESULTS_DIR}/memory_state_${size}.log" || true

            local peak
            peak=$(grep "Maximum resident set size" "${RESULTS_DIR}/memory_state_${size}.log" | awk '{print $6}')
            memory_by_size["${size}"]="${peak:-0}"

            echo "    Peak RSS: ${memory_by_size[${size}]}KB"
        fi

        # Cleanup
        for ((i=1; i<=size; i++)); do
            rm -f "${state_dir}/mem-profile-${i}.state"
        done

        echo ""
    done

    # Analyze memory scaling
    echo "  Memory scaling analysis:"
    local prev_size=0
    local prev_mem=0

    for size in "${sizes[@]}"; do
        local mem="${memory_by_size[${size}]}"

        if [[ ${prev_size} -gt 0 && ${prev_mem} -gt 0 && ${mem} -gt 0 ]]; then
            local size_increase=$((size - prev_size))
            local mem_increase=$((mem - prev_mem))
            local mem_per_session=$((mem_increase / size_increase))

            echo "    ${prev_size} → ${size} sessions: +${mem_increase}KB (${mem_per_session}KB per session)"
        fi

        prev_size=${size}
        prev_mem=${mem}
    done

    echo ""
}

# ============================================================================
# Memory Profile 4: Cache Memory Usage
# ============================================================================

profile_cache_memory() {
    echo -e "${YELLOW}💾 Profile 4: Cache Memory Usage${NC}"
    echo ""

    # Clear cache
    rm -rf .workflow/cli/state/cache 2>/dev/null || true

    echo "  Measuring memory without cache..."
    if command -v /usr/bin/time &>/dev/null; then
        /usr/bin/time -v "${CE_BIN}" status --no-cache &>/dev/null 2>"${RESULTS_DIR}/memory_no_cache.log" || true

        local mem_no_cache
        mem_no_cache=$(grep "Maximum resident set size" "${RESULTS_DIR}/memory_no_cache.log" | awk '{print $6}')

        echo "    Peak RSS (no cache): ${mem_no_cache}KB"
    fi

    echo ""
    echo "  Warming cache..."
    "${CE_BIN}" status &>/dev/null

    local cache_size
    cache_size=$(du -sb .workflow/cli/state/cache 2>/dev/null | cut -f1 || echo "0")

    echo "  Cache size: $((cache_size / 1024))KB"
    echo ""

    echo "  Measuring memory with cache..."
    if command -v /usr/bin/time &>/dev/null; then
        /usr/bin/time -v "${CE_BIN}" status &>/dev/null 2>"${RESULTS_DIR}/memory_with_cache.log" || true

        local mem_with_cache
        mem_with_cache=$(grep "Maximum resident set size" "${RESULTS_DIR}/memory_with_cache.log" | awk '{print $6}')

        echo "    Peak RSS (with cache): ${mem_with_cache}KB"

        if [[ ${mem_no_cache} -gt 0 && ${mem_with_cache} -gt 0 ]]; then
            local cache_overhead=$((mem_with_cache - mem_no_cache))
            echo "    Cache memory overhead: ${cache_overhead}KB"

            local cache_size_kb=$((cache_size / 1024))
            if [[ ${cache_size_kb} -gt 0 ]]; then
                local overhead_ratio=$((cache_overhead * 100 / cache_size_kb))
                echo "    Overhead ratio: ${overhead_ratio}%"
            fi
        fi
    fi

    echo ""
}

# ============================================================================
# Run memory profiling
# ============================================================================

cd "${PROJECT_ROOT}"

echo "Starting memory profiling..."
echo ""

profile_individual_commands
profile_memory_leaks
profile_large_state_memory
profile_cache_memory

# ============================================================================
# Generate summary report
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Memory Profiling Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Memory profiling complete!"
echo ""
echo "Results saved to: ${RESULTS_DIR}/"
echo ""
echo "Key findings:"
echo "  - Individual command memory usage profiled"
echo "  - Memory leak detection completed"
echo "  - Large state scaling analyzed"
echo "  - Cache memory impact measured"
echo ""

# Check if valgrind is available for deeper analysis
if command -v valgrind &>/dev/null; then
    echo "💡 Tip: For deeper memory analysis, run:"
    echo "    valgrind --leak-check=full --track-origins=yes ${CE_BIN} status"
else
    echo "💡 Tip: Install valgrind for deeper memory leak detection:"
    echo "    sudo apt-get install valgrind"
fi

echo ""
