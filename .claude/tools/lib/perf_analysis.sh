#!/bin/bash
# Performance Analysis Functions
# Part of performance_monitor.sh modularization
# Version: 1.0.0

# Prevent multiple sourcing
if [[ -n "${_PERF_ANALYSIS_LOADED:-}" ]]; then
    return 0
fi
_PERF_ANALYSIS_LOADED=true

# Configuration
PERF_LOG_DIR="${PERF_LOG_DIR:-${HOME}/.claude/performance}"
PERF_SUMMARY_FILE="${PERF_SUMMARY_FILE:-${PERF_LOG_DIR}/summary.json}"
BASELINE_FILE="${BASELINE_FILE:-${PERF_LOG_DIR}/baseline.json}"

# ═══════════════════════════════════════════════════════════════
# Performance Analysis
# ═══════════════════════════════════════════════════════════════

# Compare with baseline
compare_with_baseline() {
    local operation="${1:-all}"

    if [[ ! -f "$BASELINE_FILE" ]]; then
        echo "No baseline found. Run 'establish_baseline' first." >&2
        return 1
    fi

    if [[ ! -f "$PERF_SUMMARY_FILE" ]]; then
        echo "No performance data found." >&2
        return 1
    fi

    echo "Performance Comparison Report"
    echo "=============================="
    echo ""

    if command -v jq >/dev/null 2>&1; then
        if [[ "$operation" == "all" ]]; then
            jq -r --slurpfile baseline "$BASELINE_FILE" '
                to_entries[] |
                .key as $op |
                .value as $current |
                ($baseline[0][$op] // {avg_ms: 0}) as $base |
                "\($op):\n" +
                "  Current: \($current.avg_ms | floor)ms (min: \($current.min_ms)ms, max: \($current.max_ms)ms)\n" +
                "  Baseline: \($base.avg_ms | floor)ms\n" +
                "  Change: \((($current.avg_ms - $base.avg_ms) / $base.avg_ms * 100) | floor)%\n" +
                "  Status: " + (if $current.avg_ms < $base.avg_ms then "✅ IMPROVED" else "⚠️ DEGRADED" end) + "\n"
            ' "$PERF_SUMMARY_FILE"
        else
            jq -r --slurpfile baseline "$BASELINE_FILE" --arg op "$operation" '
                .[$op] as $current |
                ($baseline[0][$op] // {avg_ms: 0}) as $base |
                "\($op):\n" +
                "  Current: \($current.avg_ms | floor)ms (min: \($current.min_ms)ms, max: \($current.max_ms)ms)\n" +
                "  Baseline: \($base.avg_ms | floor)ms\n" +
                "  Change: \((($current.avg_ms - $base.avg_ms) / $base.avg_ms * 100) | floor)%\n" +
                "  Status: " + (if $current.avg_ms < $base.avg_ms then "✅ IMPROVED" else "⚠️ DEGRADED" end)
            ' "$PERF_SUMMARY_FILE"
        fi
    else
        python3 -c "
import json

with open('$PERF_SUMMARY_FILE', 'r') as f:
    current = json.load(f)

with open('$BASELINE_FILE', 'r') as f:
    baseline = json.load(f)

op = '$operation'

if op == 'all':
    for key in current:
        curr = current[key]
        base = baseline.get(key, {'avg_ms': 0})
        change = ((curr['avg_ms'] - base['avg_ms']) / base['avg_ms'] * 100) if base['avg_ms'] > 0 else 0
        status = '✅ IMPROVED' if curr['avg_ms'] < base['avg_ms'] else '⚠️ DEGRADED'
        print(f'{key}:')
        print(f\"  Current: {curr['avg_ms']:.0f}ms (min: {curr['min_ms']}ms, max: {curr['max_ms']}ms)\")
        print(f\"  Baseline: {base['avg_ms']:.0f}ms\")
        print(f\"  Change: {change:.0f}%\")
        print(f\"  Status: {status}\")
        print()
else:
    if op in current:
        curr = current[op]
        base = baseline.get(op, {'avg_ms': 0})
        change = ((curr['avg_ms'] - base['avg_ms']) / base['avg_ms'] * 100) if base['avg_ms'] > 0 else 0
        status = '✅ IMPROVED' if curr['avg_ms'] < base['avg_ms'] else '⚠️ DEGRADED'
        print(f'{op}:')
        print(f\"  Current: {curr['avg_ms']:.0f}ms (min: {curr['min_ms']}ms, max: {curr['max_ms']}ms)\")
        print(f\"  Baseline: {base['avg_ms']:.0f}ms\")
        print(f\"  Change: {change:.0f}%\")
        print(f\"  Status: {status}\")
"
    fi
}

# Establish baseline
establish_baseline() {
    if [[ -f "$PERF_SUMMARY_FILE" ]]; then
        cp "$PERF_SUMMARY_FILE" "$BASELINE_FILE"
        echo "Baseline established from current performance data" >&2
    else
        echo "No performance data to establish baseline" >&2
        return 1
    fi
}

# Identify bottlenecks
identify_bottlenecks() {
    local threshold="${1:-1000}"  # Default: operations over 1000ms

    echo "Performance Bottlenecks (>${threshold}ms avg)"
    echo "========================================"
    echo ""

    if command -v jq >/dev/null 2>&1; then
        jq -r --argjson threshold "$threshold" '
            to_entries |
            map(select(.value.avg_ms > $threshold)) |
            sort_by(.value.avg_ms) |
            reverse[] |
            "⚠️ \(.key): \(.value.avg_ms | floor)ms avg (\(.value.count) calls)"
        ' "$PERF_SUMMARY_FILE"
    else
        python3 -c "
import json

with open('$PERF_SUMMARY_FILE', 'r') as f:
    data = json.load(f)

threshold = $threshold
bottlenecks = [(k, v) for k, v in data.items() if v['avg_ms'] > threshold]
bottlenecks.sort(key=lambda x: x[1]['avg_ms'], reverse=True)

for op, stats in bottlenecks:
    print(f\"⚠️ {op}: {stats['avg_ms']:.0f}ms avg ({stats['count']} calls)\")
"
    fi
}

# Export functions
export -f compare_with_baseline
export -f establish_baseline
export -f identify_bottlenecks