#!/bin/bash
# Performance Summary Functions
# Part of performance_monitor.sh modularization
# Version: 1.0.0

# Prevent multiple sourcing
if [[ -n "${_PERF_SUMMARY_LOADED:-}" ]]; then
    return 0
fi
_PERF_SUMMARY_LOADED=true

# Configuration (inherit from perf_timer if sourced)
PERF_LOG_DIR="${PERF_LOG_DIR:-${HOME}/.claude/performance}"
PERF_SUMMARY_FILE="${PERF_SUMMARY_FILE:-${PERF_LOG_DIR}/summary.json}"

# ═══════════════════════════════════════════════════════════════
# Summary Management
# ═══════════════════════════════════════════════════════════════

# Update performance summary
update_summary() {
    local operation="$1"
    local duration="$2"
    local status="$3"

    # Initialize summary if it doesn't exist
    if [[ ! -f "$PERF_SUMMARY_FILE" ]]; then
        echo '{}' > "$PERF_SUMMARY_FILE"
    fi

    # Update summary using jq if available, otherwise use python
    if command -v jq >/dev/null 2>&1; then
        jq --arg op "$operation" \
           --argjson dur "$duration" \
           --arg stat "$status" \
           '.[$op] |= (. // {count: 0, total_ms: 0, min_ms: null, max_ms: null, avg_ms: 0, last_ms: 0, last_status: ""}) |
            .[$op].count += 1 |
            .[$op].total_ms += $dur |
            .[$op].last_ms = $dur |
            .[$op].last_status = $stat |
            .[$op].min_ms = if .[$op].min_ms == null then $dur else [.[$op].min_ms, $dur] | min end |
            .[$op].max_ms = if .[$op].max_ms == null then $dur else [.[$op].max_ms, $dur] | max end |
            .[$op].avg_ms = (.[$op].total_ms / .[$op].count)' \
            "$PERF_SUMMARY_FILE" > "${PERF_SUMMARY_FILE}.tmp" && \
            mv "${PERF_SUMMARY_FILE}.tmp" "$PERF_SUMMARY_FILE"
    else
        python3 -c "
import json
import sys

with open('$PERF_SUMMARY_FILE', 'r') as f:
    data = json.load(f)

op = '$operation'
dur = $duration
stat = '$status'

if op not in data:
    data[op] = {'count': 0, 'total_ms': 0, 'min_ms': None, 'max_ms': None, 'avg_ms': 0, 'last_ms': 0, 'last_status': ''}

data[op]['count'] += 1
data[op]['total_ms'] += dur
data[op]['last_ms'] = dur
data[op]['last_status'] = stat
data[op]['min_ms'] = dur if data[op]['min_ms'] is None else min(data[op]['min_ms'], dur)
data[op]['max_ms'] = dur if data[op]['max_ms'] is None else max(data[op]['max_ms'], dur)
data[op]['avg_ms'] = data[op]['total_ms'] / data[op]['count']

with open('$PERF_SUMMARY_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
    fi
}

# Show performance summary
show_summary() {
    if [[ ! -f "$PERF_SUMMARY_FILE" ]]; then
        echo "No performance data available" >&2
        return 1
    fi

    echo "Performance Summary"
    echo "==================="
    echo ""

    if command -v jq >/dev/null 2>&1; then
        jq -r 'to_entries | sort_by(.value.avg_ms) | reverse[] |
            "\(.key): \(.value.avg_ms | floor)ms avg (\(.value.count) calls, \(.value.min_ms)-\(.value.max_ms)ms range)"
        ' "$PERF_SUMMARY_FILE"
    else
        cat "$PERF_SUMMARY_FILE"
    fi
}

# Export functions
export -f update_summary
export -f show_summary