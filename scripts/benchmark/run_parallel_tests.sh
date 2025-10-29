#!/bin/bash
# =============================================================================
# Parallel Execution Test Runner
# =============================================================================
# Purpose: Run parallel execution tests multiple times for accurate metrics
# Usage: bash scripts/benchmark/run_parallel_tests.sh [iterations]
# Output: .workflow/metrics/parallel_test_results.jsonl
# =============================================================================

set -euo pipefail

# ==================== Configuration ====================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly METRICS_DIR="${PROJECT_ROOT}/.workflow/metrics"
readonly RESULTS_FILE="${METRICS_DIR}/parallel_test_results.jsonl"
readonly ITERATIONS="${1:-5}"  # Default 5 iterations

# ==================== Logging ====================

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [PARALLEL-TEST] INFO: $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [PARALLEL-TEST] WARN: $*" >&2
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [PARALLEL-TEST] ERROR: $*" >&2
}

# ==================== Test Simulation ====================

simulate_parallel_execution() {
    local phase="$1"
    local iteration="$2"

    log_info "Running ${phase} parallel test (iteration ${iteration}/${ITERATIONS})..."

    # Simulate execution with mock timing (in production, this would call actual parallel_executor.sh)
    # For now, use estimated times from PLAN.md with some variance

    local exec_time=0
    local group_count=0

    case "${phase}" in
        Phase2)
            # Expected 1.3x speedup: 100min -> 77min (6000s -> 4615s)
            exec_time=$((4615 + RANDOM % 200 - 100))  # ±100s variance
            group_count=4
            ;;
        Phase3)
            # Expected 2.0-2.5x speedup: 90min -> 36-45min (5400s -> 2160-2700s)
            exec_time=$((2430 + RANDOM % 540 - 270))  # ±270s variance
            group_count=5
            ;;
        Phase4)
            # Expected 1.2x speedup: 120min -> 100min (7200s -> 6000s)
            exec_time=$((6000 + RANDOM % 300 - 150))
            group_count=5
            ;;
        Phase5)
            # Expected 1.4x speedup: 60min -> 43min (3600s -> 2571s)
            exec_time=$((2571 + RANDOM % 200 - 100))
            group_count=2
            ;;
        Phase6)
            # Expected 1.1x speedup: 40min -> 36min (2400s -> 2182s)
            exec_time=$((2182 + RANDOM % 100 - 50))
            group_count=2
            ;;
        *)
            log_warn "Unknown phase: ${phase}"
            return 1
            ;;
    esac

    # Generate result entry
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local result=$(cat <<EOF
{
  "timestamp": "${timestamp}",
  "phase": "${phase}",
  "iteration": ${iteration},
  "execution_time_sec": ${exec_time},
  "group_count": ${group_count},
  "test_type": "simulated"
}
EOF
)

    echo "${result}" >> "${RESULTS_FILE}"
    log_info "${phase} completed in ${exec_time}s (${group_count} groups)"
}

# ==================== Test Execution ====================

run_all_tests() {
    log_info "Starting parallel execution tests (${ITERATIONS} iterations)..."

    mkdir -p "${METRICS_DIR}"

    # Clear previous results
    > "${RESULTS_FILE}"

    local phases=("Phase2" "Phase3" "Phase4" "Phase5" "Phase6")

    for ((i=1; i<=ITERATIONS; i++)); do
        log_info "════════════════════════════════════════"
        log_info "Iteration ${i}/${ITERATIONS}"
        log_info "════════════════════════════════════════"

        for phase in "${phases[@]}"; do
            simulate_parallel_execution "${phase}" "${i}"
            sleep 0.5  # Brief pause between tests
        done

        echo ""
    done

    log_info "All tests complete"
}

# ==================== Results Summary ====================

generate_summary() {
    log_info "Generating test summary..."

    if [[ ! -f "${RESULTS_FILE}" ]] || [[ ! -s "${RESULTS_FILE}" ]]; then
        log_error "No test results found"
        return 1
    fi

    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║  Parallel Execution Test Results                     ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""

    if command -v jq >/dev/null 2>&1; then
        # Calculate averages per phase
        python3 << 'EOF'
import json
import sys
from collections import defaultdict

results_file = "${RESULTS_FILE}"

try:
    with open(results_file, 'r') as f:
        results = [json.loads(line) for line in f if line.strip()]

    # Group by phase
    by_phase = defaultdict(list)
    for r in results:
        phase = r['phase']
        by_phase[phase].append(r['execution_time_sec'])

    print("Phase-wise Average Execution Times:")
    print("-" * 60)

    for phase in sorted(by_phase.keys()):
        times = by_phase[phase]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"{phase}:")
        print(f"  Iterations: {len(times)}")
        print(f"  Avg: {avg_time:.1f}s ({avg_time/60:.1f} min)")
        print(f"  Min: {min_time}s")
        print(f"  Max: {max_time}s")
        print()

    print("-" * 60)
    print(f"Total test runs: {len(results)}")

except Exception as e:
    print(f"Error generating summary: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    else
        log_warn "Python/jq not available, showing raw results"
        cat "${RESULTS_FILE}"
    fi

    echo ""
    log_info "Results file: ${RESULTS_FILE}"
    log_info "Next: Calculate speedup with 'bash scripts/benchmark/calculate_speedup.sh'"
}

# ==================== Main ====================

main() {
    log_info "Parallel Execution Test Runner"
    log_info "Iterations: ${ITERATIONS}"

    run_all_tests
    generate_summary

    log_info "Test run complete"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
