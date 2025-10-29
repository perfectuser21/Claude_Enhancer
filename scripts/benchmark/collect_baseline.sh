#!/bin/bash
# =============================================================================
# Serial Baseline Collection Script
# =============================================================================
# Purpose: Collect serial execution baseline for speedup calculation
# Usage: bash scripts/benchmark/collect_baseline.sh
# Output: .workflow/metrics/serial_baseline.json
# =============================================================================

set -euo pipefail

# ==================== Configuration ====================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly METRICS_DIR="${PROJECT_ROOT}/.workflow/metrics"
readonly BASELINE_FILE="${METRICS_DIR}/serial_baseline.json"

# ==================== Logging ====================

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [BASELINE] INFO: $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [BASELINE] WARN: $*" >&2
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [BASELINE] ERROR: $*" >&2
}

# ==================== Baseline Data (from v8.2.1 measurements) ====================

# These are estimated serial execution times from PLAN.md
# In production, these would be collected from actual serial runs
declare -A PHASE_BASELINES=(
    ["Phase1"]="0"      # Serial only, no baseline needed
    ["Phase2"]="100"    # 100 minutes estimated
    ["Phase3"]="90"     # 90 minutes (current 4-group baseline)
    ["Phase4"]="120"    # 120 minutes estimated
    ["Phase5"]="60"     # 60 minutes estimated
    ["Phase6"]="40"     # 40 minutes estimated
    ["Phase7"]="0"      # Serial only, no baseline needed
)

# ==================== Baseline Collection ====================

collect_baseline() {
    log_info "Collecting serial baseline data..."

    mkdir -p "${METRICS_DIR}"

    # Generate baseline JSON
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "${BASELINE_FILE}" << EOF
{
  "version": "1.0",
  "collected_at": "${timestamp}",
  "method": "estimated",
  "note": "Baseline times from PLAN.md v8.3.0 estimates",
  "Phase1": {
    "avg_time_sec": 0,
    "note": "Serial only, no parallel capability"
  },
  "Phase2": {
    "avg_time_sec": 6000,
    "note": "Estimated 100 minutes serial"
  },
  "Phase3": {
    "avg_time_sec": 5400,
    "note": "Measured baseline from v8.2.1 (90 minutes)"
  },
  "Phase4": {
    "avg_time_sec": 7200,
    "note": "Estimated 120 minutes serial"
  },
  "Phase5": {
    "avg_time_sec": 3600,
    "note": "Estimated 60 minutes serial"
  },
  "Phase6": {
    "avg_time_sec": 2400,
    "note": "Estimated 40 minutes serial"
  },
  "Phase7": {
    "avg_time_sec": 0,
    "note": "Serial only, Git operations"
  }
}
EOF

    log_info "Baseline data written to ${BASELINE_FILE}"
}

# ==================== Main ====================

main() {
    log_info "Starting baseline collection..."

    collect_baseline

    log_info "Baseline collection complete"
    log_info "File: ${BASELINE_FILE}"

    # Display summary
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║  Serial Baseline Summary                             ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""

    if command -v jq >/dev/null 2>&1; then
        jq -r 'to_entries | map(select(.key | startswith("Phase"))) | .[] | "  \(.key): \(.value.avg_time_sec)s (\(.value.note))"' "${BASELINE_FILE}"
    else
        log_warn "jq not found, skipping summary display"
        cat "${BASELINE_FILE}"
    fi

    echo ""
    log_info "Next: Run parallel tests with 'bash scripts/benchmark/run_parallel_tests.sh'"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
