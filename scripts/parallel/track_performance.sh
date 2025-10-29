#!/bin/bash
# =============================================================================
# Parallel Performance Tracker - Skills Framework
# =============================================================================
# Purpose: Track and report parallel execution performance metrics
# Usage: bash scripts/parallel/track_performance.sh <phase> <exec_time_sec> <group_count>
# Output: JSON metrics to .workflow/metrics/parallel_performance.jsonl
# =============================================================================

set -euo pipefail

# ==================== Configuration ====================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly METRICS_DIR="${PROJECT_ROOT}/.workflow/metrics"
readonly METRICS_FILE="${METRICS_DIR}/parallel_performance.jsonl"
readonly BASELINE_FILE="${METRICS_DIR}/serial_baseline.json"

# ==================== Logging ====================

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [PERF-TRACKER] INFO: $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [PERF-TRACKER] WARN: $*" >&2
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [PERF-TRACKER] ERROR: $*" >&2
}

# ==================== Initialization ====================

init_metrics_system() {
    mkdir -p "${METRICS_DIR}"

    # Create metrics file if not exists
    if [[ ! -f "${METRICS_FILE}" ]]; then
        log_info "Initializing metrics file: ${METRICS_FILE}"
        touch "${METRICS_FILE}"
    fi

    # Create baseline file if not exists
    if [[ ! -f "${BASELINE_FILE}" ]]; then
        log_warn "Baseline file not found: ${BASELINE_FILE}"
        log_warn "Run 'bash scripts/benchmark/collect_baseline.sh' to establish baseline"
        echo '{}' > "${BASELINE_FILE}"
    fi
}

# ==================== Baseline Management ====================

get_serial_baseline() {
    local phase="$1"

    if [[ ! -f "${BASELINE_FILE}" ]]; then
        echo "0"
        return 1
    fi

    # Extract baseline time for phase
    local baseline_time=$(python3 << EOF
import json
import sys
try:
    with open("${BASELINE_FILE}", 'r') as f:
        data = json.load(f)
    print(data.get("${phase}", {}).get("avg_time_sec", 0))
except:
    print(0)
EOF
)

    echo "${baseline_time}"
}

# ==================== Performance Calculation ====================

calculate_speedup() {
    local serial_time="$1"
    local parallel_time="$2"

    if [[ "${serial_time}" == "0" ]] || [[ -z "${serial_time}" ]]; then
        echo "0.00"
        return 1
    fi

    python3 << EOF
serial = float("${serial_time}")
parallel = float("${parallel_time}")
speedup = serial / parallel if parallel > 0 else 0.0
print(f"{speedup:.2f}")
EOF
}

calculate_efficiency() {
    local speedup="$1"
    local group_count="$2"

    if [[ "${group_count}" == "0" ]] || [[ -z "${group_count}" ]]; then
        echo "0.00"
        return 1
    fi

    python3 << EOF
speedup = float("${speedup}")
groups = int("${group_count}")
efficiency = (speedup / groups) * 100 if groups > 0 else 0.0
print(f"{efficiency:.2f}")
EOF
}

# ==================== Metrics Collection ====================

collect_metrics() {
    local phase="$1"
    local exec_time_sec="$2"
    local group_count="$3"

    log_info "Collecting metrics for ${phase}..."
    log_info "  Execution time: ${exec_time_sec}s"
    log_info "  Group count: ${group_count}"

    # Get serial baseline
    local serial_baseline=$(get_serial_baseline "${phase}")

    if [[ "${serial_baseline}" == "0" ]]; then
        log_warn "No baseline for ${phase}, speedup calculation skipped"
        local speedup="0.00"
        local efficiency="0.00"
    else
        log_info "  Serial baseline: ${serial_baseline}s"

        # Calculate speedup and efficiency
        speedup=$(calculate_speedup "${serial_baseline}" "${exec_time_sec}")
        efficiency=$(calculate_efficiency "${speedup}" "${group_count}")

        log_info "  Speedup: ${speedup}x"
        log_info "  Efficiency: ${efficiency}%"
    fi

    # Generate JSON metrics
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local metric_entry=$(cat <<EOF
{
  "timestamp": "${timestamp}",
  "phase": "${phase}",
  "execution_time_sec": ${exec_time_sec},
  "group_count": ${group_count},
  "serial_baseline_sec": ${serial_baseline},
  "speedup": ${speedup},
  "efficiency_percent": ${efficiency},
  "event_type": "parallel_execution"
}
EOF
)

    # Append to metrics file
    echo "${metric_entry}" >> "${METRICS_FILE}"
    log_info "Metrics recorded to ${METRICS_FILE}"
}

# ==================== Reporting ====================

generate_summary() {
    log_info "Generating performance summary..."

    if [[ ! -f "${METRICS_FILE}" ]] || [[ ! -s "${METRICS_FILE}" ]]; then
        log_warn "No metrics data available"
        return 0
    fi

    # Generate summary using Python
    python3 << 'EOF'
import json
import sys
from collections import defaultdict

metrics_file = "${METRICS_FILE}"

try:
    with open(metrics_file, 'r') as f:
        metrics = [json.loads(line) for line in f if line.strip()]

    if not metrics:
        print("No metrics found", file=sys.stderr)
        sys.exit(0)

    # Group by phase
    by_phase = defaultdict(list)
    for m in metrics:
        phase = m.get('phase', 'Unknown')
        by_phase[phase].append(m)

    print("\n" + "="*60)
    print("  Parallel Performance Summary")
    print("="*60)

    for phase, phase_metrics in sorted(by_phase.items()):
        speedups = [m['speedup'] for m in phase_metrics if m['speedup'] > 0]
        efficiencies = [m['efficiency_percent'] for m in phase_metrics if m['efficiency_percent'] > 0]

        if speedups:
            avg_speedup = sum(speedups) / len(speedups)
            max_speedup = max(speedups)
            print(f"\n{phase}:")
            print(f"  Executions: {len(phase_metrics)}")
            print(f"  Avg Speedup: {avg_speedup:.2f}x")
            print(f"  Max Speedup: {max_speedup:.2f}x")
            if efficiencies:
                avg_efficiency = sum(efficiencies) / len(efficiencies)
                print(f"  Avg Efficiency: {avg_efficiency:.1f}%")

    print("\n" + "="*60)

except Exception as e:
    print(f"Error generating summary: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# ==================== Main ====================

main() {
    if [[ $# -lt 3 ]]; then
        log_error "Usage: $0 <phase> <exec_time_sec> <group_count>"
        log_error "Example: $0 Phase3 45 4"
        exit 1
    fi

    local phase="$1"
    local exec_time_sec="$2"
    local group_count="$3"

    init_metrics_system
    collect_metrics "${phase}" "${exec_time_sec}" "${group_count}"
    generate_summary

    log_info "Performance tracking complete"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
