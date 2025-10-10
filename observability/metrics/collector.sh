#!/usr/bin/env bash
# collector.sh - Comprehensive metrics collection for Claude Enhancer
# Collects performance, usage, error, and resource metrics
set -euo pipefail

# Metrics configuration
CE_METRICS_DIR="${CE_METRICS_DIR:-.workflow/observability/metrics}"
CE_METRICS_INTERVAL="${CE_METRICS_INTERVAL:-60}"  # Collection interval in seconds
CE_METRICS_RETENTION="${CE_METRICS_RETENTION:-7}"  # Days to retain metrics
CE_METRICS_FORMAT="${CE_METRICS_FORMAT:-prometheus}"  # prometheus, json, or statsd

# Initialize metrics system
ce_metrics_init() {
    mkdir -p "${CE_METRICS_DIR}"/{performance,usage,errors,resources}

    # Create metrics metadata
    cat > "${CE_METRICS_DIR}/.metadata" <<EOF
{
  "initialized_at": "$(date -Iseconds)",
  "format": "${CE_METRICS_FORMAT}",
  "retention_days": ${CE_METRICS_RETENTION},
  "collection_interval": ${CE_METRICS_INTERVAL}
}
EOF
}

# Prometheus-style metric helpers
ce_metrics_counter() {
    local name="$1"
    local value="${2:-1}"
    local labels="${3:-}"
    local help="${4:-Counter metric}"

    local metric_file="${CE_METRICS_DIR}/performance/${name}.prom"

    # Write metric in Prometheus format
    cat >> "${metric_file}" <<EOF
# HELP ${name} ${help}
# TYPE ${name} counter
${name}${labels} ${value} $(date +%s)000
EOF
}

ce_metrics_gauge() {
    local name="$1"
    local value="$2"
    local labels="${3:-}"
    local help="${4:-Gauge metric}"

    local metric_file="${CE_METRICS_DIR}/performance/${name}.prom"

    cat > "${metric_file}" <<EOF
# HELP ${name} ${help}
# TYPE ${name} gauge
${name}${labels} ${value} $(date +%s)000
EOF
}

ce_metrics_histogram() {
    local name="$1"
    local value="$2"
    local labels="${3:-}"
    local help="${4:-Histogram metric}"

    local metric_file="${CE_METRICS_DIR}/performance/${name}.prom"

    # Calculate bucket values (simplified histogram)
    local buckets=(10 50 100 200 500 1000 2000 5000)

    cat >> "${metric_file}" <<EOF
# HELP ${name} ${help}
# TYPE ${name} histogram
EOF

    for bucket in "${buckets[@]}"; do
        if [[ $(echo "$value <= $bucket" | bc -l) -eq 1 ]]; then
            echo "${name}_bucket${labels}{le=\"${bucket}\"} 1 $(date +%s)000" >> "${metric_file}"
        else
            echo "${name}_bucket${labels}{le=\"${bucket}\"} 0 $(date +%s)000" >> "${metric_file}"
        fi
    done

    echo "${name}_bucket${labels}{le=\"+Inf\"} 1 $(date +%s)000" >> "${metric_file}"
    echo "${name}_sum${labels} ${value} $(date +%s)000" >> "${metric_file}"
    echo "${name}_count${labels} 1 $(date +%s)000" >> "${metric_file}"
}

# Performance metrics collection
ce_metrics_collect_performance() {
    # Integrate with existing performance monitor
    if [[ -f ".workflow/cli/state/performance.log" ]]; then
        # Parse performance log
        local recent_data
        recent_data=$(tail -n 100 .workflow/cli/state/performance.log | grep -v "^#" || true)

        # Calculate statistics for each operation
        while IFS=',' read -r timestamp operation duration exceeded; do
            [[ -z "$operation" ]] && continue

            # Record command execution time
            ce_metrics_histogram "ce_command_duration_milliseconds" \
                "${duration}" \
                "{operation=\"${operation}\"}" \
                "Command execution duration"

            # Track budget violations
            if [[ "$exceeded" == "true" ]]; then
                ce_metrics_counter "ce_performance_budget_violations_total" \
                    1 \
                    "{operation=\"${operation}\"}" \
                    "Performance budget violations"
            fi
        done <<< "$recent_data"
    fi

    # Cache metrics (integrate with cache_manager.sh)
    if command -v ce_cache_stats &> /dev/null; then
        local cache_stats
        cache_stats=$(ce_cache_stats)

        local cache_hits
        local cache_misses
        local hit_rate

        cache_hits=$(echo "$cache_stats" | jq -r '.cache_hits // 0')
        cache_misses=$(echo "$cache_stats" | jq -r '.cache_misses // 0')
        hit_rate=$(echo "$cache_stats" | jq -r '.hit_rate_percent // 0')

        ce_metrics_counter "ce_cache_hits_total" "$cache_hits" "" "Cache hits"
        ce_metrics_counter "ce_cache_misses_total" "$cache_misses" "" "Cache misses"
        ce_metrics_gauge "ce_cache_hit_rate_percent" "$hit_rate" "" "Cache hit rate percentage"
    fi

    # Git operation duration
    if [[ -d .git ]]; then
        local start_time
        start_time=$(date +%s%N)
        git status --porcelain > /dev/null 2>&1 || true
        local end_time
        end_time=$(date +%s%N)
        local duration_ms=$(( (end_time - start_time) / 1000000 ))

        ce_metrics_histogram "ce_git_operation_duration_milliseconds" \
            "${duration_ms}" \
            "{operation=\"status\"}" \
            "Git operation duration"
    fi
}

# Usage metrics collection
ce_metrics_collect_usage() {
    # Count active terminals (state files)
    local active_terminals=0
    if [[ -d .workflow/cli/state/terminals ]]; then
        active_terminals=$(find .workflow/cli/state/terminals -name "*.json" 2>/dev/null | wc -l)
    fi

    ce_metrics_gauge "ce_active_terminals" \
        "${active_terminals}" \
        "" \
        "Number of active terminal sessions"

    # Count commands executed today
    local commands_today=0
    if [[ -f .workflow/cli/state/performance.log ]]; then
        local today
        today=$(date +%Y-%m-%d)
        commands_today=$(grep -c "^${today}" .workflow/cli/state/performance.log || echo 0)
    fi

    ce_metrics_counter "ce_commands_executed_total" \
        "${commands_today}" \
        "" \
        "Total commands executed"

    # Phase distribution
    local phases=(P0 P1 P2 P3 P4 P5 P6 P7)
    for phase in "${phases[@]}"; do
        local phase_count=0
        if [[ -d .workflow/cli/state/terminals ]]; then
            phase_count=$(grep -l "\"phase\":\"${phase}\"" .workflow/cli/state/terminals/*.json 2>/dev/null | wc -l || echo 0)
        fi

        ce_metrics_gauge "ce_terminals_by_phase" \
            "${phase_count}" \
            "{phase=\"${phase}\"}" \
            "Terminals in each phase"
    done

    # Feature development count
    local features_count=0
    if [[ -d .workflow/cli/state/features ]]; then
        features_count=$(find .workflow/cli/state/features -type f 2>/dev/null | wc -l)
    fi

    ce_metrics_gauge "ce_features_total" \
        "${features_count}" \
        "" \
        "Total features in development"

    # PR creation count
    local pr_count=0
    if [[ -f .workflow/cli/state/pr_stats.json ]]; then
        pr_count=$(jq -r '.total_prs // 0' .workflow/cli/state/pr_stats.json 2>/dev/null || echo 0)
    fi

    ce_metrics_counter "ce_pull_requests_total" \
        "${pr_count}" \
        "" \
        "Total pull requests created"
}

# Error metrics collection
ce_metrics_collect_errors() {
    # Parse error logs
    local error_log=".workflow/observability/logs/errors.log"

    if [[ -f "$error_log" ]]; then
        local today
        today=$(date +%Y-%m-%d)

        # Count errors by level
        local error_levels=(ERROR CRITICAL FATAL)
        for level in "${error_levels[@]}"; do
            local error_count
            error_count=$(grep -c "${today}.*${level}" "$error_log" 2>/dev/null || echo 0)

            ce_metrics_counter "ce_errors_total" \
                "${error_count}" \
                "{level=\"${level}\"}" \
                "Errors by severity level"
        done

        # Count errors by type
        local git_errors
        local validation_errors
        local state_errors

        git_errors=$(grep -c "${today}.*git.*error" "$error_log" 2>/dev/null || echo 0)
        validation_errors=$(grep -c "${today}.*validation.*failed" "$error_log" 2>/dev/null || echo 0)
        state_errors=$(grep -c "${today}.*state.*error" "$error_log" 2>/dev/null || echo 0)

        ce_metrics_counter "ce_git_errors_total" "$git_errors" "" "Git operation errors"
        ce_metrics_counter "ce_validation_errors_total" "$validation_errors" "" "Validation failures"
        ce_metrics_counter "ce_state_errors_total" "$state_errors" "" "State operation errors"
    fi

    # Failed commands
    if [[ -f .workflow/cli/state/command_history.log ]]; then
        local failed_commands
        failed_commands=$(grep -c "status=failed" .workflow/cli/state/command_history.log 2>/dev/null || echo 0)

        ce_metrics_counter "ce_failed_commands_total" \
            "${failed_commands}" \
            "" \
            "Failed command executions"
    fi

    # Calculate error rate
    local total_commands
    local total_errors
    total_commands=$(ce_metrics_counter "ce_commands_executed_total" || echo 1)
    total_errors=$(ce_metrics_counter "ce_errors_total" || echo 0)

    local error_rate=0
    if [[ $total_commands -gt 0 ]]; then
        error_rate=$(echo "scale=4; $total_errors / $total_commands * 100" | bc -l)
    fi

    ce_metrics_gauge "ce_error_rate_percent" \
        "${error_rate}" \
        "" \
        "Overall error rate percentage"
}

# Resource metrics collection
ce_metrics_collect_resources() {
    # CPU usage
    local cpu_usage
    if command -v top &> /dev/null; then
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    else
        cpu_usage=0
    fi

    ce_metrics_gauge "ce_cpu_usage_percent" \
        "${cpu_usage}" \
        "" \
        "CPU usage percentage"

    # Memory usage
    local memory_total
    local memory_used
    local memory_percent

    if command -v free &> /dev/null; then
        memory_total=$(free -m | awk 'NR==2{print $2}')
        memory_used=$(free -m | awk 'NR==2{print $3}')
        memory_percent=$(echo "scale=2; $memory_used / $memory_total * 100" | bc -l)
    else
        memory_percent=0
    fi

    ce_metrics_gauge "ce_memory_usage_percent" \
        "${memory_percent}" \
        "" \
        "Memory usage percentage"

    ce_metrics_gauge "ce_memory_used_megabytes" \
        "${memory_used:-0}" \
        "" \
        "Memory used in megabytes"

    # Disk usage
    local disk_usage
    disk_usage=$(df -h . | awk 'NR==2{print $5}' | sed 's/%//')

    ce_metrics_gauge "ce_disk_usage_percent" \
        "${disk_usage}" \
        "" \
        "Disk usage percentage"

    # Disk I/O
    if command -v iostat &> /dev/null; then
        local disk_io
        disk_io=$(iostat -dx 1 2 | tail -n +4 | awk '{print $4}' | tail -1)

        ce_metrics_gauge "ce_disk_io_operations_per_second" \
            "${disk_io}" \
            "" \
            "Disk I/O operations per second"
    fi

    # Network I/O (for git operations)
    if [[ -f /proc/net/dev ]]; then
        local rx_bytes
        local tx_bytes

        rx_bytes=$(cat /proc/net/dev | grep -E "eth0|wlan0|enp" | head -1 | awk '{print $2}')
        tx_bytes=$(cat /proc/net/dev | grep -E "eth0|wlan0|enp" | head -1 | awk '{print $10}')

        ce_metrics_counter "ce_network_received_bytes_total" \
            "${rx_bytes:-0}" \
            "" \
            "Network bytes received"

        ce_metrics_counter "ce_network_transmitted_bytes_total" \
            "${tx_bytes:-0}" \
            "" \
            "Network bytes transmitted"
    fi

    # State directory size
    local state_dir_size=0
    if [[ -d .workflow/cli/state ]]; then
        state_dir_size=$(du -sb .workflow/cli/state 2>/dev/null | cut -f1)
    fi

    ce_metrics_gauge "ce_state_directory_bytes" \
        "${state_dir_size}" \
        "" \
        "State directory size in bytes"

    # Cache directory size
    local cache_dir_size=0
    if [[ -d .workflow/cli/state/cache ]]; then
        cache_dir_size=$(du -sb .workflow/cli/state/cache 2>/dev/null | cut -f1)
    fi

    ce_metrics_gauge "ce_cache_directory_bytes" \
        "${cache_dir_size}" \
        "" \
        "Cache directory size in bytes"
}

# Collect all metrics
ce_metrics_collect_all() {
    echo "$(date -Iseconds) [INFO] Starting metrics collection..."

    ce_metrics_collect_performance
    ce_metrics_collect_usage
    ce_metrics_collect_errors
    ce_metrics_collect_resources

    echo "$(date -Iseconds) [INFO] Metrics collection complete"
}

# Export metrics in Prometheus format
ce_metrics_export_prometheus() {
    local output_file="${1:-.workflow/observability/metrics/metrics.prom}"

    mkdir -p "$(dirname "$output_file")"

    # Combine all .prom files
    cat "${CE_METRICS_DIR}"/performance/*.prom > "$output_file" 2>/dev/null || true

    echo "Metrics exported to: $output_file"
}

# Export metrics in JSON format
ce_metrics_export_json() {
    local output_file="${1:-.workflow/observability/metrics/metrics.json}"

    mkdir -p "$(dirname "$output_file")"

    cat > "$output_file" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "metrics": {
EOF

    # Parse all .prom files and convert to JSON
    local first=true
    for prom_file in "${CE_METRICS_DIR}"/performance/*.prom; do
        [[ ! -f "$prom_file" ]] && continue

        while IFS= read -r line; do
            [[ "$line" =~ ^# ]] && continue
            [[ -z "$line" ]] && continue

            local metric_name
            local metric_value

            metric_name=$(echo "$line" | awk '{print $1}')
            metric_value=$(echo "$line" | awk '{print $2}')

            [[ "$first" == "true" ]] && first=false || echo ","
            echo "    \"${metric_name}\": ${metric_value}"
        done < "$prom_file"
    done

    cat >> "$output_file" <<EOF
  }
}
EOF

    echo "Metrics exported to: $output_file"
}

# Cleanup old metrics
ce_metrics_cleanup() {
    local retention_seconds=$((CE_METRICS_RETENTION * 86400))
    local current_time
    current_time=$(date +%s)

    find "${CE_METRICS_DIR}" -name "*.prom" -o -name "*.json" | while read -r file; do
        local file_time
        file_time=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo 0)
        local age=$((current_time - file_time))

        if [[ $age -gt $retention_seconds ]]; then
            rm -f "$file"
            echo "Removed old metric file: $file"
        fi
    done
}

# Background metrics collector daemon
ce_metrics_daemon() {
    echo "Starting metrics collection daemon (interval: ${CE_METRICS_INTERVAL}s)..."

    while true; do
        ce_metrics_collect_all
        ce_metrics_export_prometheus
        ce_metrics_cleanup

        sleep "${CE_METRICS_INTERVAL}"
    done
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ce_metrics_init

    case "${1:-collect}" in
        collect)
            ce_metrics_collect_all
            ;;
        export-prometheus)
            ce_metrics_export_prometheus "${2:-}"
            ;;
        export-json)
            ce_metrics_export_json "${2:-}"
            ;;
        daemon)
            ce_metrics_daemon
            ;;
        cleanup)
            ce_metrics_cleanup
            ;;
        *)
            echo "Usage: $0 {collect|export-prometheus|export-json|daemon|cleanup}"
            exit 1
            ;;
    esac
fi

# Export functions
export -f ce_metrics_init
export -f ce_metrics_counter
export -f ce_metrics_gauge
export -f ce_metrics_histogram
export -f ce_metrics_collect_performance
export -f ce_metrics_collect_usage
export -f ce_metrics_collect_errors
export -f ce_metrics_collect_resources
export -f ce_metrics_collect_all
export -f ce_metrics_export_prometheus
export -f ce_metrics_export_json
export -f ce_metrics_cleanup
