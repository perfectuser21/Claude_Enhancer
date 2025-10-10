#!/usr/bin/env bash
# benchmark_commands.sh - Benchmark individual CE CLI commands
# Tests each command for performance and compares against budgets
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="${PROJECT_ROOT}/test/performance"
RESULTS_DIR="${TEST_DIR}/results"
BASELINE_FILE="${TEST_DIR}/baseline.json"
BUDGET_FILE="${PROJECT_ROOT}/metrics/perf_budget.yml"

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Load CE CLI
CE_BIN="${PROJECT_ROOT}/.workflow/cli/ce"
if [[ ! -f "${CE_BIN}" ]]; then
    echo -e "${RED}ERROR: CE CLI not found at ${CE_BIN}${NC}"
    exit 1
fi

# Performance budgets (ms) from metrics/perf_budget.yml
declare -A BUDGETS=(
    ["status"]=500
    ["validate"]=2000
    ["start"]=200
    ["next"]=500
    ["publish"]=1000
    ["merge"]=1000
    ["clean"]=300
)

# Track results
declare -A RESULTS
declare -A VIOLATIONS

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  CE CLI Command Benchmarks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# Benchmark individual commands
# ============================================================================

benchmark_command() {
    local cmd="$1"
    local budget="${2:-0}"
    local runs="${3:-10}"
    local warmup="${4:-3}"

    echo -e "${YELLOW}📊 Benchmarking: ${cmd}${NC}"

    # Prepare test command
    local test_cmd="${CE_BIN} ${cmd}"

    # Run benchmark with hyperfine
    local result_file="${RESULTS_DIR}/${cmd//[: ]/_}_benchmark.json"

    if command -v hyperfine &>/dev/null; then
        hyperfine \
            --warmup ${warmup} \
            --runs ${runs} \
            --export-json "${result_file}" \
            --show-output \
            "${test_cmd}" 2>&1 | tee "${RESULTS_DIR}/${cmd//[: ]/_}_output.log"

        # Extract mean time in ms
        local mean_ms
        mean_ms=$(jq -r '.results[0].mean * 1000' "${result_file}" 2>/dev/null || echo "0")
        RESULTS["${cmd}"]="${mean_ms}"

        # Check budget
        if [[ ${budget} -gt 0 ]]; then
            local mean_int=${mean_ms%.*}
            if (( mean_int > budget )); then
                VIOLATIONS["${cmd}"]=$((mean_int - budget))
                echo -e "${RED}  ✗ Budget exceeded: ${mean_int}ms > ${budget}ms${NC}"
            else
                echo -e "${GREEN}  ✓ Within budget: ${mean_int}ms <= ${budget}ms${NC}"
            fi
        fi

    else
        # Fallback to time command
        echo "  hyperfine not available, using time command..."

        local total_time=0
        for ((i=1; i<=runs; i++)); do
            local start_ns
            start_ns=$(date +%s%N)

            eval "${test_cmd}" &>/dev/null || true

            local end_ns
            end_ns=$(date +%s%N)
            local duration_ms=$(( (end_ns - start_ns) / 1000000 ))

            total_time=$((total_time + duration_ms))
        done

        local mean_ms=$((total_time / runs))
        RESULTS["${cmd}"]="${mean_ms}"

        echo "  Mean time: ${mean_ms}ms"

        # Check budget
        if [[ ${budget} -gt 0 ]]; then
            if (( mean_ms > budget )); then
                VIOLATIONS["${cmd}"]=$((mean_ms - budget))
                echo -e "${RED}  ✗ Budget exceeded: ${mean_ms}ms > ${budget}ms${NC}"
            else
                echo -e "${GREEN}  ✓ Within budget: ${mean_ms}ms <= ${budget}ms${NC}"
            fi
        fi
    fi

    echo ""
}

# ============================================================================
# Run benchmarks for all commands
# ============================================================================

echo "Starting command benchmarks..."
echo ""

# Setup test environment
cd "${PROJECT_ROOT}"

# Initialize CE if needed
if [[ ! -d ".workflow/cli/state" ]]; then
    echo "Initializing CE CLI..."
    "${CE_BIN}" status &>/dev/null || true
fi

# Benchmark each command
benchmark_command "status" "${BUDGETS[status]}" 10 3
benchmark_command "validate" "${BUDGETS[validate]}" 5 2

# Note: Some commands require specific state, so we test them conditionally
if git branch | grep -q "feature/"; then
    benchmark_command "next" "${BUDGETS[next]}" 5 2
fi

# ============================================================================
# Benchmark cache performance
# ============================================================================

echo -e "${YELLOW}📊 Benchmarking: Cache performance${NC}"

# Cold cache test
rm -rf .workflow/cli/state/cache 2>/dev/null || true
echo "  Cold cache (no cache)..."
benchmark_command "status --no-cache" 0 5 1

# Warm cache test
echo "  Warming cache..."
"${CE_BIN}" status &>/dev/null
echo "  Warm cache (with cache)..."
benchmark_command "status" 0 10 1

# Calculate cache speedup
if [[ -n "${RESULTS[status --no-cache]}" && -n "${RESULTS[status]}" ]]; then
    local cold_time=${RESULTS[status --no-cache]%.*}
    local warm_time=${RESULTS[status]%.*}

    if (( cold_time > 0 )); then
        local speedup=$((100 - (warm_time * 100 / cold_time)))
        echo -e "${GREEN}  Cache speedup: ${speedup}%${NC}"
    fi
fi

echo ""

# ============================================================================
# Generate report
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Benchmark Results${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

printf "%-30s %15s %15s %10s\n" "Command" "Time (ms)" "Budget (ms)" "Status"
echo "────────────────────────────────────────────────────────────────────────"

for cmd in "${!RESULTS[@]}"; do
    local time=${RESULTS[$cmd]%.*}
    local budget="${BUDGETS[$cmd]:-N/A}"
    local status="✓"

    if [[ -n "${VIOLATIONS[$cmd]:-}" ]]; then
        status="✗"
    fi

    printf "%-30s %15d %15s %10s\n" "${cmd}" "${time}" "${budget}" "${status}"
done

echo ""

# Summary
total_violations=${#VIOLATIONS[@]}
total_tests=${#RESULTS[@]}

if [[ ${total_violations} -gt 0 ]]; then
    echo -e "${YELLOW}⚠ ${total_violations}/${total_tests} commands exceeded budget${NC}"
    exit 1
else
    echo -e "${GREEN}✓ All ${total_tests} commands within budget${NC}"
fi

echo ""

# Save results to baseline
echo "Saving results to baseline..."
{
    echo "{"
    echo '  "timestamp": "'$(date -Iseconds)'",'
    echo '  "results": {'

    local first=true
    for cmd in "${!RESULTS[@]}"; do
        [[ "${first}" == "true" ]] && first=false || echo ","
        echo -n "    \"${cmd}\": ${RESULTS[$cmd]}"
    done

    echo ""
    echo "  }"
    echo "}"
} > "${BASELINE_FILE}"

echo "Baseline saved to: ${BASELINE_FILE}"
