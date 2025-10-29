#!/bin/bash
# =============================================================================
# Speedup Calculation Script
# =============================================================================
# Purpose: Calculate speedup ratios from baseline and parallel test results
# Usage: bash scripts/benchmark/calculate_speedup.sh
# Output: .workflow/metrics/speedup_report.json
# =============================================================================

set -euo pipefail

# ==================== Configuration ====================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly METRICS_DIR="${PROJECT_ROOT}/.workflow/metrics"
readonly BASELINE_FILE="${METRICS_DIR}/serial_baseline.json"
readonly RESULTS_FILE="${METRICS_DIR}/parallel_test_results.jsonl"
readonly REPORT_FILE="${METRICS_DIR}/speedup_report.json"

# ==================== Logging ====================

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SPEEDUP] INFO: $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SPEEDUP] WARN: $*" >&2
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SPEEDUP] ERROR: $*" >&2
}

# ==================== Validation ====================

validate_inputs() {
    if [[ ! -f "${BASELINE_FILE}" ]]; then
        log_error "Baseline file not found: ${BASELINE_FILE}"
        log_error "Run: bash scripts/benchmark/collect_baseline.sh"
        exit 1
    fi

    if [[ ! -f "${RESULTS_FILE}" ]] || [[ ! -s "${RESULTS_FILE}" ]]; then
        log_error "Test results not found: ${RESULTS_FILE}"
        log_error "Run: bash scripts/benchmark/run_parallel_tests.sh"
        exit 1
    fi

    log_info "Input files validated"
}

# ==================== Speedup Calculation ====================

calculate_speedup() {
    log_info "Calculating speedup ratios..."

    python3 << 'EOF'
import json
import sys
from collections import defaultdict

baseline_file = "${BASELINE_FILE}"
results_file = "${RESULTS_FILE}"
report_file = "${REPORT_FILE}"

try:
    # Load baseline
    with open(baseline_file, 'r') as f:
        baseline = json.load(f)

    # Load test results
    with open(results_file, 'r') as f:
        results = [json.loads(line) for line in f if line.strip()]

    # Group results by phase
    by_phase = defaultdict(list)
    for r in results:
        phase = r['phase']
        by_phase[phase].append(r['execution_time_sec'])

    # Calculate speedup for each phase
    speedup_data = {
        "version": "1.0",
        "calculated_at": None,
        "overall_speedup": 0.0,
        "phases": {}
    }

    from datetime import datetime
    speedup_data["calculated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    total_serial_time = 0
    total_parallel_time = 0

    for phase in sorted(by_phase.keys()):
        times = by_phase[phase]
        avg_parallel_time = sum(times) / len(times)

        # Get serial baseline
        serial_time = baseline.get(phase, {}).get("avg_time_sec", 0)

        if serial_time > 0:
            speedup = serial_time / avg_parallel_time
            efficiency = (speedup / by_phase[phase][0]) * 100 if by_phase[phase] else 0

            # For overall calculation
            total_serial_time += serial_time
            total_parallel_time += avg_parallel_time

            speedup_data["phases"][phase] = {
                "serial_time_sec": serial_time,
                "parallel_avg_time_sec": round(avg_parallel_time, 1),
                "parallel_min_time_sec": min(times),
                "parallel_max_time_sec": max(times),
                "speedup": round(speedup, 2),
                "efficiency_percent": round(efficiency, 1),
                "iterations": len(times),
                "target_speedup": get_target_speedup(phase)
            }

    # Calculate overall speedup
    if total_parallel_time > 0:
        speedup_data["overall_speedup"] = round(total_serial_time / total_parallel_time, 2)

    # Write report
    with open(report_file, 'w') as f:
        json.dump(speedup_data, f, indent=2)

    print(f"Speedup report written to {report_file}", file=sys.stderr)

    # Display summary
    print("\n" + "="*70)
    print("  Speedup Calculation Results")
    print("="*70 + "\n")

    for phase in sorted(speedup_data["phases"].keys()):
        data = speedup_data["phases"][phase]
        target = data["target_speedup"]
        actual = data["speedup"]

        status = "✅" if actual >= target else "⚠️"

        print(f"{phase}:")
        print(f"  Serial: {data['serial_time_sec']}s ({data['serial_time_sec']/60:.1f} min)")
        print(f"  Parallel Avg: {data['parallel_avg_time_sec']}s ({data['parallel_avg_time_sec']/60:.1f} min)")
        print(f"  Speedup: {actual}x (target: {target}x) {status}")
        print(f"  Efficiency: {data['efficiency_percent']}%")
        print()

    print("-"*70)
    print(f"Overall Speedup: {speedup_data['overall_speedup']}x")
    print(f"Target: ≥1.4x")

    if speedup_data['overall_speedup'] >= 1.4:
        print("Status: ✅ TARGET MET")
    else:
        print("Status: ⚠️  BELOW TARGET")

    print("="*70 + "\n")

except Exception as e:
    print(f"Error calculating speedup: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

def get_target_speedup(phase):
    targets = {
        "Phase2": 1.3,
        "Phase3": 2.0,
        "Phase4": 1.2,
        "Phase5": 1.4,
        "Phase6": 1.1
    }
    return targets.get(phase, 1.0)

EOF

    log_info "Speedup calculation complete"
}

# ==================== Main ====================

main() {
    log_info "Speedup Calculation Script"

    validate_inputs
    calculate_speedup

    log_info "Report file: ${REPORT_FILE}"
    log_info "Next: Validate performance with 'bash scripts/benchmark/validate_performance.sh'"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
