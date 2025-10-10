#!/usr/bin/env bash
# cache_performance.sh - Cache performance testing
# Validates cache hit rates and effectiveness
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
CACHE_DIR="${PROJECT_ROOT}/.workflow/cli/state/cache"

# Target cache hit rate from P3 claims
TARGET_CACHE_HIT_RATE=85

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  CE CLI Cache Performance Testing${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# Helper functions
# ============================================================================

measure_time() {
    local start_ns
    start_ns=$(date +%s%N)

    "$@" &>/dev/null

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    echo "${duration_ms}"
}

clear_cache() {
    rm -rf "${CACHE_DIR}" 2>/dev/null || true
    mkdir -p "${CACHE_DIR}"
}

count_cache_entries() {
    find "${CACHE_DIR}" -name "*.cache" 2>/dev/null | wc -l
}

get_cache_size() {
    du -sb "${CACHE_DIR}" 2>/dev/null | cut -f1 || echo "0"
}

# ============================================================================
# Cache Test 1: Cold vs Warm Performance
# ============================================================================

test_cold_vs_warm() {
    echo -e "${YELLOW}🧊 Test 1: Cold vs Warm Cache Performance${NC}"
    echo ""

    # Cold cache test
    echo "  Testing cold cache (no cache)..."
    clear_cache

    local cold_times=()
    local cold_runs=5

    for ((i=1; i<=cold_runs; i++)); do
        local time
        time=$(measure_time "${CE_BIN}" status --no-cache)
        cold_times+=("${time}")
        echo "    Run ${i}: ${time}ms"
    done

    # Calculate average cold time
    local cold_sum=0
    for time in "${cold_times[@]}"; do
        cold_sum=$((cold_sum + time))
    done
    local avg_cold=$((cold_sum / cold_runs))

    echo "  Average cold time: ${avg_cold}ms"
    echo ""

    # Warm cache test
    echo "  Warming cache..."
    "${CE_BIN}" status &>/dev/null

    local cache_entries
    cache_entries=$(count_cache_entries)
    echo "  Cache entries created: ${cache_entries}"
    echo ""

    echo "  Testing warm cache..."
    local warm_times=()
    local warm_runs=10

    for ((i=1; i<=warm_runs; i++)); do
        local time
        time=$(measure_time "${CE_BIN}" status)
        warm_times+=("${time}")
        echo "    Run ${i}: ${time}ms"
    done

    # Calculate average warm time
    local warm_sum=0
    for time in "${warm_times[@]}"; do
        warm_sum=$((warm_sum + time))
    done
    local avg_warm=$((warm_sum / warm_runs))

    echo "  Average warm time: ${avg_warm}ms"
    echo ""

    # Calculate speedup
    if [[ ${avg_cold} -gt 0 ]]; then
        local speedup=$((100 - (avg_warm * 100 / avg_cold)))
        echo -e "  ${GREEN}Cache speedup: ${speedup}%${NC}"

        if (( speedup >= TARGET_CACHE_HIT_RATE )); then
            echo -e "${GREEN}  ✓ Meets target: ${speedup}% >= ${TARGET_CACHE_HIT_RATE}%${NC}"
        else
            echo -e "${YELLOW}  ⚠ Below target: ${speedup}% < ${TARGET_CACHE_HIT_RATE}%${NC}"
        fi
    fi

    echo ""
    echo "${avg_cold} ${avg_warm}"
}

# ============================================================================
# Cache Test 2: Hit Rate Analysis
# ============================================================================

test_hit_rate() {
    echo -e "${YELLOW}📊 Test 2: Cache Hit Rate Analysis${NC}"
    echo ""

    # Clear cache and warm it up
    clear_cache
    "${CE_BIN}" status &>/dev/null

    echo "  Running 100 operations to measure hit rate..."

    # Enable performance logging
    export CE_PERF_ENABLED=true
    export CE_PERF_VERBOSE=false

    local total_ops=100
    for ((i=1; i<=total_ops; i++)); do
        "${CE_BIN}" status &>/dev/null || true
    done

    # Analyze cache statistics from performance log
    local perf_log=".workflow/cli/state/performance.log"

    if [[ -f "${perf_log}" ]]; then
        echo "  Analyzing cache statistics..."

        # Count cache hits vs misses (simplified analysis)
        local cache_entries_final
        cache_entries_final=$(count_cache_entries)

        local cache_size
        cache_size=$(get_cache_size)

        echo "  Total operations: ${total_ops}"
        echo "  Cache entries: ${cache_entries_final}"
        echo "  Cache size: $((cache_size / 1024))KB"

        # Estimate hit rate based on operation times
        # (operations that take < 50ms are likely cache hits)
        local fast_ops=0
        local recent_times
        recent_times=$(grep "git_status" "${perf_log}" 2>/dev/null | tail -${total_ops} | cut -d',' -f3 || echo "")

        if [[ -n "${recent_times}" ]]; then
            while IFS= read -r time; do
                if (( time < 50 )); then
                    ((fast_ops++))
                fi
            done <<< "${recent_times}"

            local hit_rate=$((fast_ops * 100 / total_ops))
            echo "  Estimated cache hit rate: ${hit_rate}%"

            if (( hit_rate >= TARGET_CACHE_HIT_RATE )); then
                echo -e "${GREEN}  ✓ Hit rate meets target: ${hit_rate}% >= ${TARGET_CACHE_HIT_RATE}%${NC}"
            else
                echo -e "${YELLOW}  ⚠ Hit rate below target: ${hit_rate}% < ${TARGET_CACHE_HIT_RATE}%${NC}"
            fi
        fi
    fi

    echo ""
}

# ============================================================================
# Cache Test 3: TTL and Invalidation
# ============================================================================

test_ttl_invalidation() {
    echo -e "${YELLOW}⏱️  Test 3: TTL and Cache Invalidation${NC}"
    echo ""

    # Clear cache
    clear_cache

    # Populate cache
    echo "  Populating cache..."
    "${CE_BIN}" status &>/dev/null

    local initial_entries
    initial_entries=$(count_cache_entries)
    echo "  Initial cache entries: ${initial_entries}"

    # Test immediate re-access (should be cached)
    echo "  Testing immediate re-access (should hit cache)..."
    local time_cached
    time_cached=$(measure_time "${CE_BIN}" status)
    echo "    Time: ${time_cached}ms"

    # Simulate state change (should invalidate cache)
    echo "  Simulating state change..."
    touch .workflow/cli/state/global.state.yml

    # Test after invalidation
    echo "  Testing after state change (should miss cache)..."
    local time_invalidated
    time_invalidated=$(measure_time "${CE_BIN}" status)
    echo "    Time: ${time_invalidated}ms"

    # Compare times
    if (( time_invalidated > time_cached )); then
        echo -e "${GREEN}  ✓ Cache properly invalidated on state change${NC}"
    else
        echo -e "${YELLOW}  ⚠ Cache invalidation may not be working${NC}"
    fi

    echo ""
}

# ============================================================================
# Cache Test 4: Memory Efficiency
# ============================================================================

test_memory_efficiency() {
    echo -e "${YELLOW}💾 Test 4: Cache Memory Efficiency${NC}"
    echo ""

    # Clear cache
    clear_cache

    # Populate cache with many operations
    echo "  Populating cache with 100 operations..."
    for ((i=1; i<=100; i++)); do
        "${CE_BIN}" status &>/dev/null || true
    done

    local cache_entries
    cache_entries=$(count_cache_entries)

    local cache_size
    cache_size=$(get_cache_size)

    echo "  Cache entries: ${cache_entries}"
    echo "  Cache size: $((cache_size / 1024))KB"

    if [[ ${cache_entries} -gt 0 ]]; then
        local avg_entry_size=$((cache_size / cache_entries))
        echo "  Average entry size: $((avg_entry_size / 1024))KB"

        # Check if cache size is reasonable (should be < 10MB for normal usage)
        if (( cache_size < 10485760 )); then
            echo -e "${GREEN}  ✓ Cache size is reasonable (< 10MB)${NC}"
        else
            echo -e "${YELLOW}  ⚠ Cache size is large (> 10MB)${NC}"
        fi
    fi

    echo ""
}

# ============================================================================
# Cache Test 5: Concurrent Access
# ============================================================================

test_concurrent_access() {
    echo -e "${YELLOW}🔀 Test 5: Concurrent Cache Access${NC}"
    echo ""

    # Clear and warm cache
    clear_cache
    "${CE_BIN}" status &>/dev/null

    echo "  Testing 10 concurrent cache accesses..."

    local start_ns
    start_ns=$(date +%s%N)

    # Launch concurrent operations
    local pids=()
    for ((i=1; i<=10; i++)); do
        "${CE_BIN}" status &>/dev/null &
        pids+=($!)
    done

    # Wait for all
    local failures=0
    for pid in "${pids[@]}"; do
        if ! wait ${pid}; then
            ((failures++))
        fi
    done

    local end_ns
    end_ns=$(date +%s%N)
    local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    echo "  Duration: ${duration_ms}ms"
    echo "  Failures: ${failures}/10"

    if (( failures == 0 )); then
        echo -e "${GREEN}  ✓ Cache handles concurrent access correctly${NC}"
    else
        echo -e "${YELLOW}  ⚠ ${failures} concurrent operations failed${NC}"
    fi

    echo ""
}

# ============================================================================
# Cache Test 6: Category-Specific Performance
# ============================================================================

test_category_performance() {
    echo -e "${YELLOW}🗂️  Test 6: Cache Category Performance${NC}"
    echo ""

    # Test different cache categories
    local categories=("git" "state" "validation" "gates")

    for category in "${categories[@]}"; do
        echo "  Testing ${category} cache..."

        # Clear specific category
        rm -rf "${CACHE_DIR}/${category}" 2>/dev/null || true
        mkdir -p "${CACHE_DIR}/${category}"

        # Measure performance
        local cold_time
        cold_time=$(measure_time "${CE_BIN}" status --no-cache)

        # Warm cache
        "${CE_BIN}" status &>/dev/null

        local warm_time
        warm_time=$(measure_time "${CE_BIN}" status)

        local entries
        entries=$(find "${CACHE_DIR}/${category}" -name "*.cache" 2>/dev/null | wc -l || echo "0")

        if [[ ${entries} -gt 0 ]]; then
            echo "    Entries: ${entries}"
            echo "    Cold: ${cold_time}ms, Warm: ${warm_time}ms"

            if [[ ${cold_time} -gt 0 ]]; then
                local speedup=$((100 - (warm_time * 100 / cold_time)))
                echo "    Speedup: ${speedup}%"
            fi
        else
            echo "    No cache entries for this category"
        fi
    done

    echo ""
}

# ============================================================================
# Run cache performance tests
# ============================================================================

cd "${PROJECT_ROOT}"

echo "Starting cache performance tests..."
echo ""

# Run tests
result=$(test_cold_vs_warm)
avg_cold=$(echo "${result}" | awk '{print $1}')
avg_warm=$(echo "${result}" | awk '{print $2}')

test_hit_rate
test_ttl_invalidation
test_memory_efficiency
test_concurrent_access
test_category_performance

# ============================================================================
# Generate summary report
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Cache Performance Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

printf "%-30s %15s\n" "Metric" "Value"
echo "────────────────────────────────────────────────"
printf "%-30s %15s\n" "Average Cold Time" "${avg_cold}ms"
printf "%-30s %15s\n" "Average Warm Time" "${avg_warm}ms"

if [[ ${avg_cold} -gt 0 ]]; then
    local speedup=$((100 - (avg_warm * 100 / avg_cold)))
    printf "%-30s %15s\n" "Cache Speedup" "${speedup}%"
    printf "%-30s %15s\n" "Target Hit Rate" "${TARGET_CACHE_HIT_RATE}%"

    if (( speedup >= TARGET_CACHE_HIT_RATE )); then
        echo -e "\n${GREEN}✓ Cache performance meets target${NC}"
    else
        echo -e "\n${YELLOW}⚠ Cache performance below target${NC}"
    fi
fi

echo ""

local final_entries
final_entries=$(count_cache_entries)

local final_size
final_size=$(get_cache_size)

printf "%-30s %15d\n" "Total Cache Entries" "${final_entries}"
printf "%-30s %15s\n" "Total Cache Size" "$((final_size / 1024))KB"

echo ""

# Save results
cat > "${RESULTS_DIR}/cache_performance_summary.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "cold_time_ms": ${avg_cold},
  "warm_time_ms": ${avg_warm},
  "speedup_percent": $((100 - (avg_warm * 100 / avg_cold))),
  "target_hit_rate": ${TARGET_CACHE_HIT_RATE},
  "cache_entries": ${final_entries},
  "cache_size_bytes": ${final_size}
}
EOF

echo "Results saved to: ${RESULTS_DIR}/cache_performance_summary.json"
