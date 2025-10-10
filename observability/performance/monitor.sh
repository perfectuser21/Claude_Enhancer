#!/usr/bin/env bash
# monitor.sh - Enhanced performance monitoring for Claude Enhancer
# Real-time tracking, regression detection, and reporting
set -euo pipefail

# Performance monitoring configuration
CE_PERF_MONITOR_DIR="${CE_PERF_MONITOR_DIR:-.workflow/observability/performance}"
CE_PERF_BASELINE_FILE="${CE_PERF_BASELINE_FILE:-${CE_PERF_MONITOR_DIR}/baseline.json}"
CE_PERF_REGRESSION_THRESHOLD="${CE_PERF_REGRESSION_THRESHOLD:-0.2}"  # 20% degradation

# Initialize performance monitoring
ce_perf_monitor_init() {
    mkdir -p "${CE_PERF_MONITOR_DIR}"/{baselines,reports,trends}

    cat > "${CE_PERF_MONITOR_DIR}/.metadata" <<EOF
{
  "initialized_at": "$(date -Iseconds)",
  "regression_threshold": ${CE_PERF_REGRESSION_THRESHOLD},
  "monitoring_enabled": true
}
EOF
}

# Load performance budget
ce_perf_load_budget() {
    local budget_file="${1:-metrics/perf_budget.yml}"

    if [[ ! -f "$budget_file" ]]; then
        echo "{}" | jq '.'
        return
    fi

    # Convert YAML to JSON
    if command -v yq &>/dev/null; then
        yq eval -o=json "$budget_file" | jq '.performance_budgets'
    else
        echo "{}" | jq '.'
    fi
}

# Track command execution
ce_perf_track_command() {
    local command="$1"
    local duration_ms="$2"
    local status="${3:-success}"

    # Load budget
    local budgets
    budgets=$(ce_perf_load_budget)

    # Find budget for this command
    local budget_ms=0
    local threshold_ms=0

    if [[ "$budgets" != "{}" ]]; then
        budget_ms=$(echo "$budgets" | jq -r ".[] | select(.name == \"$command\") | .budget" 2>/dev/null || echo 0)
        threshold_ms=$(echo "$budgets" | jq -r ".[] | select(.name == \"$command\") | .threshold" 2>/dev/null || echo 0)

        # Parse time strings (e.g., "100ms" -> 100)
        budget_ms=$(echo "$budget_ms" | sed 's/[^0-9]//g')
        threshold_ms=$(echo "$threshold_ms" | sed 's/[^0-9]//g')
    fi

    # Determine performance status
    local perf_status="ok"
    if [[ $budget_ms -gt 0 ]] && [[ $duration_ms -gt $threshold_ms ]]; then
        perf_status="critical"
    elif [[ $budget_ms -gt 0 ]] && [[ $duration_ms -gt $budget_ms ]]; then
        perf_status="warning"
    fi

    # Record tracking data
    local tracking_file="${CE_PERF_MONITOR_DIR}/tracking.jsonl"

    cat >> "$tracking_file" <<EOF
{"timestamp":"$(date -Iseconds)","command":"${command}","duration_ms":${duration_ms},"budget_ms":${budget_ms},"threshold_ms":${threshold_ms},"status":"${status}","perf_status":"${perf_status}"}
EOF

    # Check for regression
    ce_perf_check_regression "$command" "$duration_ms"
}

# Create performance baseline
ce_perf_create_baseline() {
    local baseline_name="${1:-default}"

    echo "Creating performance baseline: ${baseline_name}"

    # Analyze recent performance data
    if [[ ! -f .workflow/cli/state/performance.log ]]; then
        echo "No performance data available"
        return 1
    fi

    local baseline_data="{"

    # Calculate baselines for each operation
    local operations
    operations=$(grep -v "^#" .workflow/cli/state/performance.log | cut -d',' -f2 | sort -u)

    local first=true
    for operation in $operations; do
        [[ -z "$operation" ]] && continue

        # Get recent measurements for this operation
        local measurements
        measurements=$(grep ",${operation}," .workflow/cli/state/performance.log | tail -n 100 | cut -d',' -f3)

        [[ -z "$measurements" ]] && continue

        # Calculate statistics
        local count min max sum avg p50 p95 p99

        count=$(echo "$measurements" | wc -l)
        min=$(echo "$measurements" | sort -n | head -1)
        max=$(echo "$measurements" | sort -n | tail -1)
        sum=$(echo "$measurements" | awk '{s+=$1} END {print s}')
        avg=$((sum / count))

        p50=$(echo "$measurements" | sort -n | awk "NR==$((count/2)){print}")
        p95=$(echo "$measurements" | sort -n | awk "NR==$((count*95/100)){print}")
        p99=$(echo "$measurements" | sort -n | awk "NR==$((count*99/100)){print}")

        [[ "$first" == "true" ]] && first=false || baseline_data+=","

        baseline_data+="\"${operation}\":{\"count\":${count},\"min\":${min},\"max\":${max},\"avg\":${avg},\"p50\":${p50},\"p95\":${p95},\"p99\":${p99}}"
    done

    baseline_data+="}"

    # Save baseline
    local baseline_file="${CE_PERF_MONITOR_DIR}/baselines/${baseline_name}.json"

    cat > "$baseline_file" <<EOF
{
  "name": "${baseline_name}",
  "created_at": "$(date -Iseconds)",
  "operations": ${baseline_data}
}
EOF

    # Set as current baseline
    ln -sf "baselines/${baseline_name}.json" "${CE_PERF_BASELINE_FILE}"

    echo "Baseline created: $baseline_file"
}

# Check for performance regression
ce_perf_check_regression() {
    local operation="$1"
    local current_duration="$2"

    # Load baseline
    if [[ ! -f "$CE_PERF_BASELINE_FILE" ]]; then
        return 0  # No baseline to compare
    fi

    local baseline
    baseline=$(cat "$CE_PERF_BASELINE_FILE")

    local baseline_avg
    baseline_avg=$(echo "$baseline" | jq -r ".operations.\"${operation}\".avg // 0")

    [[ $baseline_avg -eq 0 ]] && return 0

    # Calculate regression percentage
    local regression_pct
    regression_pct=$(echo "scale=4; ($current_duration - $baseline_avg) / $baseline_avg" | bc -l)

    # Check if regression exceeds threshold
    if (( $(echo "$regression_pct > $CE_PERF_REGRESSION_THRESHOLD" | bc -l) )); then
        local regression_display
        regression_display=$(echo "scale=1; $regression_pct * 100" | bc -l)

        # Log regression
        echo "⚠️  Performance regression detected: ${operation}"
        echo "   Current: ${current_duration}ms | Baseline: ${baseline_avg}ms | Regression: ${regression_display}%"

        # Record regression
        local regression_file="${CE_PERF_MONITOR_DIR}/regressions.jsonl"

        cat >> "$regression_file" <<EOF
{"timestamp":"$(date -Iseconds)","operation":"${operation}","current_ms":${current_duration},"baseline_ms":${baseline_avg},"regression_pct":${regression_pct}}
EOF

        # Trigger alert if available
        if command -v ce_notify_send &>/dev/null; then
            ce_notify_send \
                "PerformanceRegression" \
                "warning" \
                "Performance regression detected for ${operation}" \
                "Current: ${current_duration}ms, Baseline: ${baseline_avg}ms, Regression: ${regression_display}%" \
                "docs/runbooks/performance-regression.md" \
                "Investigate performance degradation"
        fi
    fi
}

# Generate performance report
ce_perf_generate_report() {
    local report_name="${1:-$(date +%Y%m%d_%H%M%S)}"
    local report_file="${CE_PERF_MONITOR_DIR}/reports/${report_name}.md"

    echo "Generating performance report..."

    cat > "$report_file" <<'EOF'
# Performance Monitoring Report

**Generated:** $(date -Iseconds)

## Executive Summary

EOF

    # Calculate summary metrics
    if [[ -f .workflow/cli/state/performance.log ]]; then
        local total_operations
        local total_violations
        local avg_duration

        total_operations=$(grep -c "^" .workflow/cli/state/performance.log 2>/dev/null || echo 0)
        total_violations=$(grep -c "exceeded=true" .workflow/cli/state/performance.log 2>/dev/null || echo 0)

        cat >> "$report_file" <<EOF

- **Total Operations Tracked:** ${total_operations}
- **Budget Violations:** ${total_violations}
- **Violation Rate:** $(echo "scale=2; $total_violations * 100 / $total_operations" | bc -l)%

## Performance by Operation

EOF

        # Analyze each operation
        local operations
        operations=$(grep -v "^#" .workflow/cli/state/performance.log | cut -d',' -f2 | sort -u)

        for operation in $operations; do
            [[ -z "$operation" ]] && continue

            local measurements
            measurements=$(grep ",${operation}," .workflow/cli/state/performance.log | tail -n 100 | cut -d',' -f3)

            [[ -z "$measurements" ]] && continue

            local count min max sum avg p95

            count=$(echo "$measurements" | wc -l)
            min=$(echo "$measurements" | sort -n | head -1)
            max=$(echo "$measurements" | sort -n | tail -1)
            sum=$(echo "$measurements" | awk '{s+=$1} END {print s}')
            avg=$((sum / count))
            p95=$(echo "$measurements" | sort -n | awk "NR==$((count*95/100)){print}")

            cat >> "$report_file" <<EOF

### ${operation}

- **Count:** ${count}
- **Min:** ${min}ms
- **Max:** ${max}ms
- **Average:** ${avg}ms
- **P95:** ${p95}ms

EOF
        done
    fi

    # Performance budgets
    cat >> "$report_file" <<EOF

## Performance Budget Compliance

EOF

    local budgets
    budgets=$(ce_perf_load_budget)

    if [[ "$budgets" != "{}" ]]; then
        echo "$budgets" | jq -r '.[] | "- **\(.name)**: Budget \(.budget), Threshold \(.threshold)"' >> "$report_file"
    else
        echo "No performance budgets configured." >> "$report_file"
    fi

    # Regressions
    if [[ -f "${CE_PERF_MONITOR_DIR}/regressions.jsonl" ]]; then
        local regression_count
        regression_count=$(wc -l < "${CE_PERF_MONITOR_DIR}/regressions.jsonl")

        cat >> "$report_file" <<EOF

## Performance Regressions

**Total Regressions Detected:** ${regression_count}

Recent regressions:

EOF

        tail -n 10 "${CE_PERF_MONITOR_DIR}/regressions.jsonl" | while read -r line; do
            local operation current baseline regression

            operation=$(echo "$line" | jq -r '.operation')
            current=$(echo "$line" | jq -r '.current_ms')
            baseline=$(echo "$line" | jq -r '.baseline_ms')
            regression=$(echo "$line" | jq -r '.regression_pct * 100' | xargs printf "%.1f")

            echo "- **${operation}**: ${current}ms (baseline: ${baseline}ms, +${regression}%)" >> "$report_file"
        done
    fi

    # Recommendations
    cat >> "$report_file" <<EOF

## Recommendations

1. Review operations with budget violations
2. Investigate performance regressions
3. Update baselines if new improvements are stable
4. Consider caching for frequently executed operations
5. Monitor resource usage trends

EOF

    echo "Report generated: $report_file"
}

# Real-time performance monitoring
ce_perf_monitor_live() {
    echo "Starting real-time performance monitoring..."
    echo "Watching: .workflow/cli/state/performance.log"
    echo ""

    # Load budgets
    local budgets
    budgets=$(ce_perf_load_budget)

    # Watch performance log
    tail -f .workflow/cli/state/performance.log 2>/dev/null | while IFS=',' read -r timestamp operation duration exceeded; do
        [[ "$timestamp" =~ ^# ]] && continue
        [[ -z "$operation" ]] && continue

        # Get budget for this operation
        local budget_ms=0
        if [[ "$budgets" != "{}" ]]; then
            budget_ms=$(echo "$budgets" | jq -r ".[] | select(.name == \"$operation\") | .budget" 2>/dev/null | sed 's/[^0-9]//g' || echo 0)
        fi

        # Display with color coding
        local color="\033[0;32m"  # Green
        local status="✓"

        if [[ "$exceeded" == "true" ]]; then
            color="\033[0;31m"  # Red
            status="✗"
        elif [[ $budget_ms -gt 0 ]] && [[ $duration -gt $((budget_ms * 90 / 100)) ]]; then
            color="\033[0;33m"  # Yellow
            status="⚠"
        fi

        printf "${color}${status} %-30s %8sms" "${operation:0:30}" "$duration"
        [[ $budget_ms -gt 0 ]] && printf " (budget: %sms)" "$budget_ms"
        printf "\033[0m\n"

        # Track
        ce_perf_track_command "$operation" "$duration" "success"
    done
}

# Performance trend analysis
ce_perf_analyze_trends() {
    local operation="${1:-all}"
    local days="${2:-7}"

    echo "Analyzing performance trends for: ${operation} (last ${days} days)"

    if [[ ! -f "${CE_PERF_MONITOR_DIR}/tracking.jsonl" ]]; then
        echo "No tracking data available"
        return 1
    fi

    local cutoff_date
    cutoff_date=$(date -d "${days} days ago" -Iseconds 2>/dev/null || date -v-${days}d -Iseconds 2>/dev/null)

    # Filter data
    local data
    if [[ "$operation" == "all" ]]; then
        data=$(jq -s "map(select(.timestamp >= \"${cutoff_date}\"))" "${CE_PERF_MONITOR_DIR}/tracking.jsonl")
    else
        data=$(jq -s "map(select(.timestamp >= \"${cutoff_date}\" and .command == \"${operation}\"))" "${CE_PERF_MONITOR_DIR}/tracking.jsonl")
    fi

    # Calculate trend statistics
    local total_measurements
    local avg_duration
    local degradation_count

    total_measurements=$(echo "$data" | jq 'length')
    avg_duration=$(echo "$data" | jq '[.[].duration_ms] | add / length')
    degradation_count=$(echo "$data" | jq '[.[] | select(.perf_status == "warning" or .perf_status == "critical")] | length')

    cat <<EOF

Trend Analysis Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Measurements:    ${total_measurements}
Average Duration:      ${avg_duration}ms
Degradations:          ${degradation_count}

Performance Status Distribution:
EOF

    echo "$data" | jq -r 'group_by(.perf_status) | .[] | "  \(.[0].perf_status): \(length)"'

    # Save trend report
    local trend_file="${CE_PERF_MONITOR_DIR}/trends/trend_${operation}_$(date +%Y%m%d).json"

    cat > "$trend_file" <<EOF
{
  "operation": "${operation}",
  "period_days": ${days},
  "total_measurements": ${total_measurements},
  "avg_duration_ms": ${avg_duration},
  "degradation_count": ${degradation_count},
  "analyzed_at": "$(date -Iseconds)",
  "data": ${data}
}
EOF

    echo ""
    echo "Trend report saved: $trend_file"
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ce_perf_monitor_init

    case "${1:-help}" in
        track)
            ce_perf_track_command "${2:-}" "${3:-0}" "${4:-success}"
            ;;
        baseline)
            ce_perf_create_baseline "${2:-default}"
            ;;
        report)
            ce_perf_generate_report "${2:-}"
            ;;
        live)
            ce_perf_monitor_live
            ;;
        trends)
            ce_perf_analyze_trends "${2:-all}" "${3:-7}"
            ;;
        *)
            cat <<EOF
Usage: $0 {track|baseline|report|live|trends}

Commands:
  track <cmd> <duration> [status]
                        Track command execution
  baseline [name]       Create performance baseline
  report [name]         Generate performance report
  live                  Real-time performance monitoring
  trends [operation] [days]
                        Analyze performance trends

Examples:
  $0 track git_status 45 success
  $0 baseline production
  $0 report weekly
  $0 trends git_status 7
EOF
            ;;
    esac
fi

# Export functions
export -f ce_perf_monitor_init
export -f ce_perf_track_command
export -f ce_perf_create_baseline
export -f ce_perf_check_regression
export -f ce_perf_generate_report
export -f ce_perf_monitor_live
export -f ce_perf_analyze_trends
