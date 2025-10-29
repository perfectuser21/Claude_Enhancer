#!/bin/bash
# =============================================================================
# Performance Validation Script
# =============================================================================
# Purpose: Validate that speedup targets are met for CI/CD
# Usage: bash scripts/benchmark/validate_performance.sh
# Exit: 0 if targets met, 1 if below targets
# =============================================================================

set -euo pipefail

# ==================== Configuration ====================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly METRICS_DIR="${PROJECT_ROOT}/.workflow/metrics"
readonly REPORT_FILE="${METRICS_DIR}/speedup_report.json"

# Performance targets from PLAN.md
readonly TARGET_OVERALL=1.4
readonly TARGET_PHASE2=1.3
readonly TARGET_PHASE3=2.0
readonly TARGET_PHASE4=1.2
readonly TARGET_PHASE5=1.4
readonly TARGET_PHASE6=1.1

# ==================== Logging ====================

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [VALIDATE] INFO: $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [VALIDATE] WARN: $*" >&2
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [VALIDATE] ERROR: $*" >&2
}

# ==================== Validation ====================

validate_report_exists() {
    if [[ ! -f "${REPORT_FILE}" ]]; then
        log_error "Speedup report not found: ${REPORT_FILE}"
        log_error "Run: bash scripts/benchmark/calculate_speedup.sh"
        exit 1
    fi

    log_info "Report file found: ${REPORT_FILE}"
}

validate_targets() {
    log_info "Validating performance targets..."

    python3 <<EOF
import json
import sys

report_file = "${REPORT_FILE}"
target_overall = float("${TARGET_OVERALL}")
targets = {
    "Phase2": float("${TARGET_PHASE2}"),
    "Phase3": float("${TARGET_PHASE3}"),
    "Phase4": float("${TARGET_PHASE4}"),
    "Phase5": float("${TARGET_PHASE5}"),
    "Phase6": float("${TARGET_PHASE6}")
}

try:
    with open(report_file, 'r') as f:
        report = json.load(f)

    print("\n" + "="*70)
    print("  Performance Validation Report")
    print("="*70 + "\n")

    failures = []

    # Validate each phase
    for phase, target in sorted(targets.items()):
        if phase not in report.get("phases", {}):
            print(f"⚠️  {phase}: No data available")
            failures.append(f"{phase} (no data)")
            continue

        actual = report["phases"][phase]["speedup"]

        if actual >= target:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            failures.append(f"{phase} ({actual:.2f}x < {target}x)")

        print(f"{phase}:")
        print(f"  Target: {target}x")
        print(f"  Actual: {actual}x")
        print(f"  Status: {status}")
        print()

    # Validate overall
    overall_actual = report.get("overall_speedup", 0.0)

    print("-"*70)
    print("\nOverall Speedup:")
    print(f"  Target: ≥{target_overall}x")
    print(f"  Actual: {overall_actual}x")

    if overall_actual >= target_overall:
        print(f"  Status: ✅ PASS")
    else:
        print(f"  Status: ❌ FAIL")
        failures.append(f"Overall ({overall_actual:.2f}x < {target_overall}x)")

    print("\n" + "="*70)

    # Summary
    if failures:
        print("\n❌ VALIDATION FAILED")
        print(f"   {len(failures)} target(s) not met:\n")
        for f in failures:
            print(f"   - {f}")
        print()
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        print("   All performance targets met!")
        print()
        sys.exit(0)

except Exception as e:
    print(f"\nError validating performance: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
}

# ==================== Main ====================

main() {
    log_info "Performance Validation Script"

    validate_report_exists
    validate_targets

    # If we reach here, validation passed
    log_info "Performance validation complete"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
