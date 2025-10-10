#!/usr/bin/env bash
# usage_tracker.sh - Usage analytics and patterns for Claude Enhancer
# Tracks user behavior, feature adoption, and workflow patterns
set -euo pipefail

# Analytics configuration
CE_ANALYTICS_DIR="${CE_ANALYTICS_DIR:-.workflow/observability/analytics}"
CE_ANALYTICS_RETENTION="${CE_ANALYTICS_RETENTION:-30}"  # days

# Initialize analytics system
ce_analytics_init() {
    mkdir -p "${CE_ANALYTICS_DIR}"/{usage,patterns,adoption,sessions}

    cat > "${CE_ANALYTICS_DIR}/.metadata" <<EOF
{
  "initialized_at": "$(date -Iseconds)",
  "retention_days": ${CE_ANALYTICS_RETENTION},
  "tracking_enabled": true
}
EOF
}

# Track command usage
ce_analytics_track_command() {
    local command="$1"
    local terminal_id="${CE_TERMINAL_ID:-unknown}"
    local phase="${CE_CURRENT_PHASE:-unknown}"

    cat >> "${CE_ANALYTICS_DIR}/usage/commands.jsonl" <<EOF
{"timestamp":"$(date -Iseconds)","command":"${command}","terminal_id":"${terminal_id}","phase":"${phase}"}
EOF
}

# Track session
ce_analytics_track_session() {
    local event="$1"  # start, end
    local terminal_id="${CE_TERMINAL_ID:-unknown}"

    local session_file="${CE_ANALYTICS_DIR}/sessions/${terminal_id}.json"

    if [[ "$event" == "start" ]]; then
        cat > "$session_file" <<EOF
{
  "terminal_id": "${terminal_id}",
  "started_at": "$(date -Iseconds)",
  "commands": [],
  "phases": []
}
EOF
    elif [[ "$event" == "end" ]] && [[ -f "$session_file" ]]; then
        local session
        session=$(cat "$session_file")

        local started_at
        started_at=$(echo "$session" | jq -r '.started_at')

        local duration_seconds
        duration_seconds=$(( $(date +%s) - $(date -d "$started_at" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$started_at" +%s 2>/dev/null || echo 0) ))

        # Update session
        echo "$session" | jq ". + {ended_at: \"$(date -Iseconds)\", duration_seconds: ${duration_seconds}}" > "${session_file}.complete"

        # Archive
        mv "${session_file}.complete" "${CE_ANALYTICS_DIR}/sessions/archive/$(date +%Y%m%d)_${terminal_id}.json"
        rm -f "$session_file"
    fi
}

# Track phase progression
ce_analytics_track_phase() {
    local from_phase="$1"
    local to_phase="$2"
    local terminal_id="${CE_TERMINAL_ID:-unknown}"

    cat >> "${CE_ANALYTICS_DIR}/patterns/phase_transitions.jsonl" <<EOF
{"timestamp":"$(date -Iseconds)","from":"${from_phase}","to":"${to_phase}","terminal_id":"${terminal_id}"}
EOF
}

# Track feature usage
ce_analytics_track_feature() {
    local feature="$1"
    local action="${2:-used}"  # created, used, completed, abandoned

    cat >> "${CE_ANALYTICS_DIR}/adoption/features.jsonl" <<EOF
{"timestamp":"$(date -Iseconds)","feature":"${feature}","action":"${action}","user":"${USER}"}
EOF
}

# Get most used commands
ce_analytics_most_used_commands() {
    local limit="${1:-10}"

    if [[ ! -f "${CE_ANALYTICS_DIR}/usage/commands.jsonl" ]]; then
        echo "No usage data available"
        return 1
    fi

    echo "Most Used Commands (Top ${limit}):"
    echo ""
    printf "%-5s %-30s %-10s\n" "Rank" "Command" "Count"
    echo "────────────────────────────────────────────────"

    jq -r '.command' "${CE_ANALYTICS_DIR}/usage/commands.jsonl" | \
        sort | uniq -c | sort -rn | head -n "$limit" | \
        awk '{printf "%-5d %-30s %-10s\n", NR, $2, $1}'
}

# Get average session duration
ce_analytics_session_stats() {
    local days="${1:-7}"

    local session_files
    session_files=$(find "${CE_ANALYTICS_DIR}/sessions/archive" -name "*.json" -mtime -${days} 2>/dev/null)

    [[ -z "$session_files" ]] && echo "No session data available" && return 1

    local total_sessions
    local total_duration
    local avg_duration

    total_sessions=$(echo "$session_files" | wc -l)
    total_duration=$(echo "$session_files" | xargs cat | jq -s '[.[].duration_seconds] | add' 2>/dev/null || echo 0)
    avg_duration=$((total_duration / total_sessions))

    cat <<EOF
Session Statistics (Last ${days} days):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Sessions:       ${total_sessions}
Total Duration:       $(printf '%dd %dh %dm' $((total_duration/86400)) $((total_duration%86400/3600)) $((total_duration%3600/60)))
Average Duration:     $(printf '%dh %dm' $((avg_duration/3600)) $((avg_duration%3600/60)))

EOF
}

# Analyze phase progression patterns
ce_analytics_phase_patterns() {
    if [[ ! -f "${CE_ANALYTICS_DIR}/patterns/phase_transitions.jsonl" ]]; then
        echo "No phase transition data available"
        return 1
    fi

    echo "Phase Progression Patterns:"
    echo ""

    # Most common transitions
    echo "Most Common Transitions:"
    jq -r '"\(.from) → \(.to)"' "${CE_ANALYTICS_DIR}/patterns/phase_transitions.jsonl" | \
        sort | uniq -c | sort -rn | head -10 | \
        awk '{printf "  %3d  %s\n", $1, substr($0, index($0,$2))}'

    echo ""

    # Average time in each phase (would need more tracking)
    echo "Phase Distribution:"
    jq -r '.to' "${CE_ANALYTICS_DIR}/patterns/phase_transitions.jsonl" | \
        sort | uniq -c | sort -rn | \
        awk '{printf "  %-5s %5d transitions\n", $2, $1}'

    echo ""
}

# Feature adoption metrics
ce_analytics_feature_adoption() {
    local days="${1:-30}"

    if [[ ! -f "${CE_ANALYTICS_DIR}/adoption/features.jsonl" ]]; then
        echo "No feature adoption data available"
        return 1
    fi

    local cutoff_date
    cutoff_date=$(date -d "${days} days ago" -Iseconds 2>/dev/null || date -v-${days}d -Iseconds 2>/dev/null)

    echo "Feature Adoption (Last ${days} days):"
    echo ""

    # Features created
    local created_count
    created_count=$(jq -s "map(select(.timestamp >= \"${cutoff_date}\" and .action == \"created\")) | length" "${CE_ANALYTICS_DIR}/adoption/features.jsonl")

    # Features completed
    local completed_count
    completed_count=$(jq -s "map(select(.timestamp >= \"${cutoff_date}\" and .action == \"completed\")) | length" "${CE_ANALYTICS_DIR}/adoption/features.jsonl")

    # Features abandoned
    local abandoned_count
    abandoned_count=$(jq -s "map(select(.timestamp >= \"${cutoff_date}\" and .action == \"abandoned\")) | length" "${CE_ANALYTICS_DIR}/adoption/features.jsonl")

    # Completion rate
    local completion_rate=0
    if [[ $created_count -gt 0 ]]; then
        completion_rate=$(echo "scale=1; $completed_count * 100 / $created_count" | bc -l)
    fi

    cat <<EOF
Features Created:     ${created_count}
Features Completed:   ${completed_count}
Features Abandoned:   ${abandoned_count}
Completion Rate:      ${completion_rate}%

Top Features:
EOF

    jq -r 'select(.action == "created") | .feature' "${CE_ANALYTICS_DIR}/adoption/features.jsonl" | \
        sort | uniq -c | sort -rn | head -10 | \
        awk '{printf "  %3d  %s\n", $1, $2}'

    echo ""
}

# Usage heatmap (by hour of day)
ce_analytics_usage_heatmap() {
    if [[ ! -f "${CE_ANALYTICS_DIR}/usage/commands.jsonl" ]]; then
        echo "No usage data available"
        return 1
    fi

    echo "Usage Heatmap (Commands by Hour):"
    echo ""

    # Count commands by hour
    for hour in {0..23}; do
        local count
        count=$(jq -r '.timestamp' "${CE_ANALYTICS_DIR}/usage/commands.jsonl" | \
                grep "T$(printf '%02d' $hour):" | wc -l)

        printf "%02d:00  " $hour

        # Draw bar
        local bar_length=$((count / 10))
        [[ $bar_length -gt 50 ]] && bar_length=50
        printf '%*s' $bar_length '' | tr ' ' '█'
        printf " %d\n" $count
    done

    echo ""
}

# Generate analytics report
ce_analytics_generate_report() {
    local report_name="${1:-$(date +%Y%m%d_%H%M%S)}"
    local report_file="${CE_ANALYTICS_DIR}/reports/${report_name}.md"

    mkdir -p "${CE_ANALYTICS_DIR}/reports"

    echo "Generating analytics report..."

    cat > "$report_file" <<EOF
# Usage Analytics Report

**Generated:** $(date -Iseconds)

## Overview

This report provides insights into Claude Enhancer usage patterns and feature adoption.

## Command Usage

$(ce_analytics_most_used_commands 10)

## Session Statistics

$(ce_analytics_session_stats 30)

## Phase Progression

$(ce_analytics_phase_patterns)

## Feature Adoption

$(ce_analytics_feature_adoption 30)

## Usage Patterns

$(ce_analytics_usage_heatmap)

## Recommendations

Based on usage patterns:

1. **Most active hours**: Focus documentation updates during peak usage times
2. **Feature adoption**: Promote underutilized features
3. **Phase transitions**: Optimize commonly used workflows
4. **Session duration**: Identify and reduce friction points

EOF

    echo "Report generated: $report_file"
}

# Export analytics data
ce_analytics_export() {
    local format="${1:-json}"  # json or csv
    local output_file="${2:-.workflow/observability/analytics/export/analytics_$(date +%Y%m%d).${format}}"

    mkdir -p "$(dirname "$output_file")"

    if [[ "$format" == "json" ]]; then
        # Export as JSON
        cat > "$output_file" <<EOF
{
  "exported_at": "$(date -Iseconds)",
  "commands": $(jq -s '.' "${CE_ANALYTICS_DIR}/usage/commands.jsonl" 2>/dev/null || echo '[]'),
  "sessions": $(find "${CE_ANALYTICS_DIR}/sessions/archive" -name "*.json" -exec cat {} \; 2>/dev/null | jq -s '.' || echo '[]'),
  "phase_transitions": $(jq -s '.' "${CE_ANALYTICS_DIR}/patterns/phase_transitions.jsonl" 2>/dev/null || echo '[]'),
  "features": $(jq -s '.' "${CE_ANALYTICS_DIR}/adoption/features.jsonl" 2>/dev/null || echo '[]')
}
EOF
    elif [[ "$format" == "csv" ]]; then
        # Export commands as CSV
        echo "timestamp,command,terminal_id,phase" > "$output_file"
        jq -r '[.timestamp, .command, .terminal_id, .phase] | @csv' "${CE_ANALYTICS_DIR}/usage/commands.jsonl" >> "$output_file" 2>/dev/null || true
    fi

    echo "Analytics exported to: $output_file"
}

# Cleanup old analytics data
ce_analytics_cleanup() {
    local retention_seconds=$((CE_ANALYTICS_RETENTION * 86400))
    local current_time
    current_time=$(date +%s)

    local cleaned=0

    # Clean old session archives
    find "${CE_ANALYTICS_DIR}/sessions/archive" -name "*.json" | while read -r file; do
        local file_time
        file_time=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo 0)
        local age=$((current_time - file_time))

        if [[ $age -gt $retention_seconds ]]; then
            rm -f "$file"
            ((cleaned++))
        fi
    done

    echo "Cleaned up ${cleaned} old analytics files"
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ce_analytics_init

    case "${1:-help}" in
        commands)
            ce_analytics_most_used_commands "${2:-10}"
            ;;
        sessions)
            ce_analytics_session_stats "${2:-7}"
            ;;
        phases)
            ce_analytics_phase_patterns
            ;;
        features)
            ce_analytics_feature_adoption "${2:-30}"
            ;;
        heatmap)
            ce_analytics_usage_heatmap
            ;;
        report)
            ce_analytics_generate_report "${2:-}"
            ;;
        export)
            ce_analytics_export "${2:-json}" "${3:-}"
            ;;
        cleanup)
            ce_analytics_cleanup
            ;;
        *)
            cat <<EOF
Usage: $0 {commands|sessions|phases|features|heatmap|report|export|cleanup}

Commands:
  commands [limit]      Show most used commands
  sessions [days]       Show session statistics
  phases                Analyze phase progression patterns
  features [days]       Show feature adoption metrics
  heatmap               Show usage heatmap by hour
  report [name]         Generate comprehensive report
  export [format] [file]
                        Export analytics data (json|csv)
  cleanup               Remove old analytics data

Examples:
  $0 commands 20
  $0 sessions 30
  $0 report monthly
  $0 export json analytics.json
EOF
            ;;
    esac
fi

# Export functions
export -f ce_analytics_init
export -f ce_analytics_track_command
export -f ce_analytics_track_session
export -f ce_analytics_track_phase
export -f ce_analytics_track_feature
export -f ce_analytics_most_used_commands
export -f ce_analytics_session_stats
export -f ce_analytics_phase_patterns
export -f ce_analytics_feature_adoption
export -f ce_analytics_generate_report
export -f ce_analytics_export
export -f ce_analytics_cleanup
