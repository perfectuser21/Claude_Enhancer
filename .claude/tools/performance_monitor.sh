#!/bin/bash
# Performance Monitor for Claude Enhancer - Main Loader
# Purpose: Track execution times and identify bottlenecks
# Version: 1.0.1 (modularized)
# Created: 2025-10-25

set -euo pipefail

# Get library directory
PERF_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib"

# ═══════════════════════════════════════════════════════════════
# Load Modules
# ═══════════════════════════════════════════════════════════════

# 1. Load timer functions (required)
if [[ -f "$PERF_LIB_DIR/perf_timer.sh" ]]; then
    # shellcheck source=/dev/null
    source "$PERF_LIB_DIR/perf_timer.sh"
else
    echo "ERROR: perf_timer.sh not found!" >&2
    exit 1
fi

# 2. Load summary functions (required)
if [[ -f "$PERF_LIB_DIR/perf_summary.sh" ]]; then
    # shellcheck source=/dev/null
    source "$PERF_LIB_DIR/perf_summary.sh"
else
    echo "ERROR: perf_summary.sh not found!" >&2
    exit 1
fi

# 3. Load analysis functions (required)
if [[ -f "$PERF_LIB_DIR/perf_analysis.sh" ]]; then
    # shellcheck source=/dev/null
    source "$PERF_LIB_DIR/perf_analysis.sh"
else
    echo "ERROR: perf_analysis.sh not found!" >&2
    exit 1
fi

# ═══════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        start)
            start_timer "${2:-unknown}" "${3:-default}"
            ;;
        end)
            end_timer "${2:-unknown}" "${3:-default}" "${4:-success}"
            ;;
        summary)
            show_summary
            ;;
        compare)
            compare_with_baseline "${2:-all}"
            ;;
        baseline)
            establish_baseline
            ;;
        bottlenecks)
            identify_bottlenecks "${2:-1000}"
            ;;
        *)
            cat <<EOF
Usage: $(basename "$0") [command] [args]

Commands:
  start <operation> [context]     Start timing an operation
  end <operation> [context] [status]  End timing and log result
  summary                          Show performance summary
  compare [operation]              Compare with baseline
  baseline                         Establish baseline from current data
  bottlenecks [threshold_ms]       Identify performance bottlenecks

Example usage:
  # Time a hook execution
  $(basename "$0") start "branch_check" "pre-commit"
  # ... do work ...
  $(basename "$0") end "branch_check" "pre-commit" "success"

  # View summary
  $(basename "$0") summary

  # Compare with baseline
  $(basename "$0") baseline  # establish baseline
  # ... make optimizations ...
  $(basename "$0") compare

Module Information:
  - perf_timer.sh: Timing functions (77 lines)
  - perf_summary.sh: Summary management (90 lines)
  - perf_analysis.sh: Performance analysis (148 lines)
  - Total: 315 lines (was 329 lines)
EOF
            ;;
    esac
fi