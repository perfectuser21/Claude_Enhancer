#!/usr/bin/env bash
# status.sh - Real-time status dashboard for Claude Enhancer
# Displays SLO compliance, metrics, errors, and resource usage
set -euo pipefail

# Dashboard configuration
CE_DASHBOARD_REFRESH="${CE_DASHBOARD_REFRESH:-5}"  # Refresh interval in seconds
CE_DASHBOARD_MODE="${CE_DASHBOARD_MODE:-full}"      # full, compact, minimal

# Source required libraries
if [[ -f .workflow/cli/lib/performance_monitor.sh ]]; then
    source .workflow/cli/lib/performance_monitor.sh
fi

if [[ -f .workflow/cli/lib/cache_manager.sh ]]; then
    source .workflow/cli/lib/cache_manager.sh
fi

# ANSI color codes
readonly COLOR_RESET="\033[0m"
readonly COLOR_BOLD="\033[1m"
readonly COLOR_RED="\033[0;31m"
readonly COLOR_GREEN="\033[0;32m"
readonly COLOR_YELLOW="\033[0;33m"
readonly COLOR_BLUE="\033[0;34m"
readonly COLOR_CYAN="\033[0;36m"
readonly COLOR_GRAY="\033[0;90m"

# Box drawing characters
readonly BOX_TL="╔"
readonly BOX_TR="╗"
readonly BOX_BL="╚"
readonly BOX_BR="╝"
readonly BOX_H="═"
readonly BOX_V="║"
readonly BOX_VL="╣"
readonly BOX_VR="╠"
readonly BOX_HT="╦"
readonly BOX_HB="╩"
readonly BOX_C="╬"

# Clear screen
ce_dashboard_clear() {
    clear
}

# Draw header
ce_dashboard_header() {
    local title="Claude Enhancer 5.0 - Production Monitoring Dashboard"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${COLOR_BOLD}${COLOR_CYAN}"
    echo "${BOX_TL}$(printf '%*s' 80 '' | tr ' ' "${BOX_H}")${BOX_TR}"
    printf "${BOX_V} %-78s ${BOX_V}\n" "$title"
    printf "${BOX_V} %-78s ${BOX_V}\n" "Last Updated: $timestamp"
    echo "${BOX_BL}$(printf '%*s' 80 '' | tr ' ' "${BOX_H}")${BOX_BR}"
    echo -e "${COLOR_RESET}"
}

# Draw SLO compliance section
ce_dashboard_slo_compliance() {
    echo -e "${COLOR_BOLD}${COLOR_BLUE}═══ SLO Compliance ═══${COLOR_RESET}"
    echo ""

    # Calculate SLO metrics
    local availability_slo=99.9
    local error_rate_slo=0.1
    local latency_p95_slo=500

    # Get current metrics
    local total_commands=0
    local failed_commands=0
    local total_errors=0
    local avg_latency=0

    if [[ -f .workflow/cli/state/performance.log ]]; then
        total_commands=$(grep -c "^" .workflow/cli/state/performance.log 2>/dev/null || echo 1)
        failed_commands=$(grep -c "exceeded=true" .workflow/cli/state/performance.log 2>/dev/null || echo 0)
    fi

    if [[ -f .workflow/observability/logs/errors/errors.log ]]; then
        total_errors=$(wc -l < .workflow/observability/logs/errors/errors.log 2>/dev/null || echo 0)
    fi

    # Calculate availability
    local availability=100
    if [[ $total_commands -gt 0 ]]; then
        availability=$(echo "scale=2; (($total_commands - $failed_commands) / $total_commands) * 100" | bc -l)
    fi

    # Calculate error rate
    local error_rate=0
    if [[ $total_commands -gt 0 ]]; then
        error_rate=$(echo "scale=2; ($total_errors / $total_commands) * 100" | bc -l)
    fi

    # Display SLOs
    printf "  %-30s %10s %10s %10s\n" "SLO" "Target" "Current" "Status"
    echo "  ────────────────────────────────────────────────────────────────────"

    ce_dashboard_slo_row "Availability" "${availability_slo}%" "${availability}%" "$availability" "$availability_slo"
    ce_dashboard_slo_row "Error Rate" "<${error_rate_slo}%" "${error_rate}%" "$error_rate" "$error_rate_slo"

    # Get P95 latency from performance log
    if [[ -f .workflow/cli/state/performance.log ]]; then
        local p95_latency
        p95_latency=$(grep -v "^#" .workflow/cli/state/performance.log | cut -d',' -f3 | sort -n | awk 'BEGIN{c=0} {a[c]=$1; c++} END{print a[int(c*0.95)]}' 2>/dev/null || echo 0)
        ce_dashboard_slo_row "P95 Latency" "<${latency_p95_slo}ms" "${p95_latency}ms" "$latency_p95_slo" "$p95_latency"
    fi

    echo ""
}

# Helper to display SLO row
ce_dashboard_slo_row() {
    local name="$1"
    local target="$2"
    local current="$3"
    local current_val="${4:-0}"
    local target_val="${5:-100}"

    local status
    local color

    # Determine status based on comparison
    if (( $(echo "$current_val >= $target_val" | bc -l) )); then
        status="✓ OK"
        color="${COLOR_GREEN}"
    elif (( $(echo "$current_val >= $target_val * 0.95" | bc -l) )); then
        status="⚠ WARN"
        color="${COLOR_YELLOW}"
    else
        status="✗ FAIL"
        color="${COLOR_RED}"
    fi

    printf "  %-30s %10s %10s ${color}%10s${COLOR_RESET}\n" "$name" "$target" "$current" "$status"
}

# Draw performance metrics section
ce_dashboard_performance() {
    echo -e "${COLOR_BOLD}${COLOR_BLUE}═══ Performance Metrics ═══${COLOR_RESET}"
    echo ""

    # Cache statistics
    if command -v ce_cache_stats &>/dev/null; then
        local cache_stats
        cache_stats=$(ce_cache_stats 2>/dev/null || echo '{}')

        local cache_hits
        local cache_misses
        local hit_rate

        cache_hits=$(echo "$cache_stats" | jq -r '.cache_hits // 0')
        cache_misses=$(echo "$cache_stats" | jq -r '.cache_misses // 0')
        hit_rate=$(echo "$cache_stats" | jq -r '.hit_rate_percent // 0')

        printf "  %-30s %10s\n" "Cache Hit Rate:" "${hit_rate}%"
        printf "  %-30s %10s\n" "Cache Hits:" "$cache_hits"
        printf "  %-30s %10s\n" "Cache Misses:" "$cache_misses"
        echo ""
    fi

    # Recent command performance
    if [[ -f .workflow/cli/state/performance.log ]]; then
        echo "  Recent Command Performance (last 10):"
        echo "  ────────────────────────────────────────────────────────────────────"

        tail -n 10 .workflow/cli/state/performance.log | grep -v "^#" | while IFS=',' read -r timestamp operation duration exceeded; do
            local color="${COLOR_GREEN}"
            local marker="✓"

            if [[ "$exceeded" == "true" ]]; then
                color="${COLOR_RED}"
                marker="✗"
            fi

            printf "    ${color}${marker}${COLOR_RESET} %-30s %8sms\n" "${operation:0:30}" "$duration"
        done

        echo ""
    fi
}

# Draw resource usage section
ce_dashboard_resources() {
    echo -e "${COLOR_BOLD}${COLOR_BLUE}═══ Resource Usage ═══${COLOR_RESET}"
    echo ""

    # CPU usage
    if command -v top &>/dev/null; then
        local cpu_usage
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
        ce_dashboard_bar "CPU Usage" "$cpu_usage" 100 "%"
    fi

    # Memory usage
    if command -v free &>/dev/null; then
        local memory_total
        local memory_used
        local memory_percent

        memory_total=$(free -m | awk 'NR==2{print $2}')
        memory_used=$(free -m | awk 'NR==2{print $3}')
        memory_percent=$(echo "scale=1; $memory_used / $memory_total * 100" | bc -l)

        ce_dashboard_bar "Memory Usage" "$memory_percent" 100 "% (${memory_used}MB/${memory_total}MB)"
    fi

    # Disk usage
    local disk_usage
    disk_usage=$(df -h . | awk 'NR==2{print $5}' | sed 's/%//')
    ce_dashboard_bar "Disk Usage" "$disk_usage" 100 "%"

    echo ""
}

# Draw progress bar
ce_dashboard_bar() {
    local label="$1"
    local value="${2:-0}"
    local max="${3:-100}"
    local unit="${4:-}"

    local bar_width=40
    local filled
    filled=$(echo "scale=0; $value * $bar_width / $max" | bc -l 2>/dev/null || echo 0)
    [[ $filled -lt 0 ]] && filled=0
    [[ $filled -gt $bar_width ]] && filled=$bar_width

    local empty=$((bar_width - filled))

    # Color based on value
    local color="${COLOR_GREEN}"
    if (( $(echo "$value >= 80" | bc -l) )); then
        color="${COLOR_RED}"
    elif (( $(echo "$value >= 60" | bc -l) )); then
        color="${COLOR_YELLOW}"
    fi

    printf "  %-20s ${color}[" "$label"
    printf '%*s' "$filled" '' | tr ' ' '█'
    printf '%*s' "$empty" '' | tr ' ' '░'
    printf "]${COLOR_RESET} %6.1f${unit}\n" "$value"
}

# Draw active terminals section
ce_dashboard_terminals() {
    echo -e "${COLOR_BOLD}${COLOR_BLUE}═══ Active Terminals ═══${COLOR_RESET}"
    echo ""

    if [[ ! -d .workflow/cli/state/terminals ]]; then
        echo "  No active terminals"
        echo ""
        return
    fi

    local total_terminals
    total_terminals=$(find .workflow/cli/state/terminals -name "*.json" 2>/dev/null | wc -l)

    echo "  Total Active: $total_terminals"
    echo ""

    # Phase distribution
    echo "  Phase Distribution:"
    local phases=(P0 P1 P2 P3 P4 P5 P6 P7)
    for phase in "${phases[@]}"; do
        local count
        count=$(grep -l "\"phase\":\"${phase}\"" .workflow/cli/state/terminals/*.json 2>/dev/null | wc -l || echo 0)

        if [[ $count -gt 0 ]]; then
            printf "    %-5s " "$phase"
            ce_dashboard_mini_bar "$count" "$total_terminals"
        fi
    done

    echo ""
}

# Draw mini progress bar
ce_dashboard_mini_bar() {
    local value="$1"
    local max="${2:-1}"

    local bar_width=20
    local filled
    filled=$(echo "scale=0; $value * $bar_width / $max" | bc -l 2>/dev/null || echo 0)
    [[ $filled -lt 0 ]] && filled=0
    [[ $filled -gt $bar_width ]] && filled=$bar_width

    local empty=$((bar_width - filled))

    printf "${COLOR_CYAN}["
    printf '%*s' "$filled" '' | tr ' ' '█'
    printf '%*s' "$empty" '' | tr ' ' '░'
    printf "]${COLOR_RESET} %3d\n" "$value"
}

# Draw active alerts section
ce_dashboard_alerts() {
    echo -e "${COLOR_BOLD}${COLOR_BLUE}═══ Active Alerts ═══${COLOR_RESET}"
    echo ""

    if [[ ! -d .workflow/observability/alerts/fired ]] || \
       [[ $(find .workflow/observability/alerts/fired -name "*.json" 2>/dev/null | wc -l) -eq 0 ]]; then
        echo -e "  ${COLOR_GREEN}✓ No active alerts${COLOR_RESET}"
        echo ""
        return
    fi

    local critical_count warning_count info_count

    critical_count=$(find .workflow/observability/alerts/fired -name "*.json" -exec grep -l '"severity":"critical"' {} \; 2>/dev/null | wc -l || echo 0)
    warning_count=$(find .workflow/observability/alerts/fired -name "*.json" -exec grep -l '"severity":"warning"' {} \; 2>/dev/null | wc -l || echo 0)
    info_count=$(find .workflow/observability/alerts/fired -name "*.json" -exec grep -l '"severity":"info"' {} \; 2>/dev/null | wc -l || echo 0)

    [[ $critical_count -gt 0 ]] && printf "  ${COLOR_RED}✗ Critical: %d${COLOR_RESET}\n" "$critical_count"
    [[ $warning_count -gt 0 ]] && printf "  ${COLOR_YELLOW}⚠ Warning: %d${COLOR_RESET}\n" "$warning_count"
    [[ $info_count -gt 0 ]] && printf "  ${COLOR_CYAN}ℹ Info: %d${COLOR_RESET}\n" "$info_count"

    echo ""

    # Show recent alerts
    echo "  Recent Alerts:"
    find .workflow/observability/alerts/fired -name "*.json" 2>/dev/null | head -5 | while read -r alert_file; do
        local severity summary

        severity=$(jq -r '.severity' "$alert_file")
        summary=$(jq -r '.summary' "$alert_file" | cut -c1-60)

        local color="${COLOR_GRAY}"
        case "$severity" in
            critical) color="${COLOR_RED}" ;;
            warning) color="${COLOR_YELLOW}" ;;
            info) color="${COLOR_CYAN}" ;;
        esac

        printf "    ${color}%-10s${COLOR_RESET} %s\n" "[$severity]" "$summary"
    done

    echo ""
}

# Draw footer
ce_dashboard_footer() {
    echo -e "${COLOR_GRAY}$(printf '%*s' 80 '' | tr ' ' '─')${COLOR_RESET}"
    echo -e "${COLOR_GRAY}Press Ctrl+C to exit | Refresh every ${CE_DASHBOARD_REFRESH}s${COLOR_RESET}"
}

# Full dashboard
ce_dashboard_full() {
    ce_dashboard_clear
    ce_dashboard_header
    ce_dashboard_slo_compliance
    ce_dashboard_performance
    ce_dashboard_resources
    ce_dashboard_terminals
    ce_dashboard_alerts
    ce_dashboard_footer
}

# Compact dashboard
ce_dashboard_compact() {
    ce_dashboard_clear
    ce_dashboard_header
    ce_dashboard_slo_compliance
    ce_dashboard_resources
    ce_dashboard_alerts
    ce_dashboard_footer
}

# Minimal dashboard
ce_dashboard_minimal() {
    ce_dashboard_clear
    echo -e "${COLOR_BOLD}Claude Enhancer Status${COLOR_RESET} - $(date '+%H:%M:%S')"
    echo ""

    # Just SLO compliance
    ce_dashboard_slo_compliance

    # Resource summary
    if command -v free &>/dev/null; then
        local cpu_usage memory_usage disk_usage

        cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}' 2>/dev/null || echo 0)
        memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}' 2>/dev/null || echo 0)
        disk_usage=$(df -h . | awk 'NR==2{print $5}' | sed 's/%//' 2>/dev/null || echo 0)

        printf "Resources: CPU %.0f%% | Memory %.0f%% | Disk %s%%\n" "$cpu_usage" "$memory_usage" "$disk_usage"
    fi

    echo ""
}

# Live dashboard with auto-refresh
ce_dashboard_live() {
    local mode="${1:-$CE_DASHBOARD_MODE}"

    trap 'echo ""; echo "Dashboard stopped."; exit 0' INT TERM

    while true; do
        case "$mode" in
            compact)
                ce_dashboard_compact
                ;;
            minimal)
                ce_dashboard_minimal
                ;;
            *)
                ce_dashboard_full
                ;;
        esac

        sleep "$CE_DASHBOARD_REFRESH"
    done
}

# Export dashboard to file
ce_dashboard_export() {
    local output_file="${1:-.workflow/observability/status.txt}"

    {
        ce_dashboard_header
        ce_dashboard_slo_compliance
        ce_dashboard_performance
        ce_dashboard_resources
        ce_dashboard_terminals
        ce_dashboard_alerts
    } > "$output_file"

    echo "Dashboard exported to: $output_file"
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-live}" in
        live)
            ce_dashboard_live "${2:-full}"
            ;;
        once)
            ce_dashboard_full
            ;;
        compact)
            ce_dashboard_compact
            ;;
        minimal)
            ce_dashboard_minimal
            ;;
        export)
            ce_dashboard_export "${2:-}"
            ;;
        *)
            cat <<EOF
Usage: $0 {live|once|compact|minimal|export}

Commands:
  live [mode]           Start live dashboard (mode: full|compact|minimal)
  once                  Show dashboard once
  compact               Show compact dashboard
  minimal               Show minimal dashboard
  export [file]         Export dashboard to file

Examples:
  $0 live full
  $0 export status.txt
EOF
            ;;
    esac
fi

# Export functions
export -f ce_dashboard_full
export -f ce_dashboard_compact
export -f ce_dashboard_minimal
export -f ce_dashboard_live
export -f ce_dashboard_export
