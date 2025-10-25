#!/bin/bash
# Performance Timer Functions
# Part of performance_monitor.sh modularization
# Version: 1.0.0

# Prevent multiple sourcing
if [[ -n "${_PERF_TIMER_LOADED:-}" ]]; then
    return 0
fi
_PERF_TIMER_LOADED=true

# Configuration
readonly PERF_LOG_DIR="${HOME}/.claude/performance"
readonly PERF_LOG_FILE="${PERF_LOG_DIR}/performance.log"
readonly PERF_SUMMARY_FILE="${PERF_LOG_DIR}/summary.json"

# Ensure performance directory exists
mkdir -p "$PERF_LOG_DIR"

# ═══════════════════════════════════════════════════════════════
# Timing Functions
# ═══════════════════════════════════════════════════════════════

# Start timing an operation
start_timer() {
    local operation="${1:-unknown}"
    local context="${2:-default}"

    # Store start time in nanoseconds
    local start_time
    start_time=$(date +%s%N)

    # Create timer file
    local timer_file="${PERF_LOG_DIR}/.timer_${operation}_${context}"
    echo "$start_time" > "$timer_file"

    # Log start
    echo "$(date -Iseconds) | START | $operation | $context" >> "$PERF_LOG_FILE"
}

# End timing and log results
end_timer() {
    local operation="${1:-unknown}"
    local context="${2:-default}"
    local status="${3:-success}"

    # Get end time in nanoseconds
    local end_time
    end_time=$(date +%s%N)

    # Read start time
    local timer_file="${PERF_LOG_DIR}/.timer_${operation}_${context}"
    if [[ ! -f "$timer_file" ]]; then
        echo "Error: Timer not started for $operation/$context" >&2
        return 1
    fi

    local start_time
    start_time=$(cat "$timer_file")
    rm -f "$timer_file"

    # Calculate duration in milliseconds
    local duration_ns=$((end_time - start_time))
    local duration_ms=$((duration_ns / 1000000))

    # Log result
    echo "$(date -Iseconds) | END | $operation | $context | $status | ${duration_ms}ms" >> "$PERF_LOG_FILE"

    # Update summary (delegate to perf_summary module)
    if [[ -f "$(dirname "${BASH_SOURCE[0]}")/perf_summary.sh" ]]; then
        # shellcheck source=/dev/null
        source "$(dirname "${BASH_SOURCE[0]}")/perf_summary.sh"
        update_summary "$operation" "$duration_ms" "$status"
    fi

    # Return duration
    echo "$duration_ms"
}

# Export functions
export -f start_timer
export -f end_timer