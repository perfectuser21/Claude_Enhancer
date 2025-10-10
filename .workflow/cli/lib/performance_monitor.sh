#!/usr/bin/env bash
# performance_monitor.sh - Performance monitoring and instrumentation
# Tracks execution times, identifies bottlenecks, enforces performance budgets
set -euo pipefail

# Source common utilities
# shellcheck source=./common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Performance configuration
CE_PERF_ENABLED=${CE_PERF_ENABLED:-true}
CE_PERF_VERBOSE=${CE_PERF_VERBOSE:-false}
CE_PERF_BUDGET_FILE=".workflow/cli/config/performance_budgets.yml"
CE_PERF_LOG_FILE=".workflow/cli/state/performance.log"

# Performance budgets (milliseconds)
declare -A CE_PERF_BUDGETS=(
    ["git_status"]=100
    ["git_branch_list"]=200
    ["git_remote_check"]=500
    ["state_load"]=50
    ["state_save"]=100
    ["conflict_check"]=300
    ["gate_validate"]=1000
    ["yaml_parse"]=50
)

# Performance tracking
declare -g -A CE_PERF_TIMERS
declare -g -A CE_PERF_COUNTS
declare -g -A CE_PERF_TOTALS

# Initialize performance monitoring
ce_perf_init() {
    if [[ "${CE_PERF_ENABLED}" != "true" ]]; then
        return 0
    fi

    mkdir -p "$(dirname "${CE_PERF_LOG_FILE}")"

    # Create log header if new file
    if [[ ! -f "${CE_PERF_LOG_FILE}" ]]; then
        cat > "${CE_PERF_LOG_FILE}" <<EOF
# CE CLI Performance Log
# Format: timestamp,operation,duration_ms,exceeded_budget
# Generated: $(date -Iseconds)
EOF
    fi
}

# Start performance timer
ce_perf_start() {
    local operation="${1:?Operation name required}"

    if [[ "${CE_PERF_ENABLED}" != "true" ]]; then
        return 0
    fi

    # Store start time in nanoseconds
    CE_PERF_TIMERS["${operation}"]=$(date +%s%N)

    if [[ "${CE_PERF_VERBOSE}" == "true" ]]; then
        ce_log_debug "PERF: Started timing '${operation}'"
    fi
}

# Stop performance timer and record
ce_perf_stop() {
    local operation="${1:?Operation name required}"

    if [[ "${CE_PERF_ENABLED}" != "true" ]]; then
        return 0
    fi

    local start_time="${CE_PERF_TIMERS[${operation}]:-0}"

    if [[ ${start_time} -eq 0 ]]; then
        ce_log_warn "PERF: No start time found for '${operation}'"
        return 1
    fi

    # Calculate duration in milliseconds
    local end_time
    end_time=$(date +%s%N)
    local duration_ns=$((end_time - start_time))
    local duration_ms=$((duration_ns / 1000000))

    # Update statistics
    CE_PERF_COUNTS["${operation}"]=$((${CE_PERF_COUNTS[${operation}]:-0} + 1))
    CE_PERF_TOTALS["${operation}"]=$((${CE_PERF_TOTALS[${operation}]:-0} + duration_ms))

    # Check against budget
    local budget="${CE_PERF_BUDGETS[${operation}]:-0}"
    local exceeded=false

    if [[ ${budget} -gt 0 ]] && [[ ${duration_ms} -gt ${budget} ]]; then
        exceeded=true
        local overage=$((duration_ms - budget))
        local overage_pct=$((overage * 100 / budget))

        if [[ "${CE_PERF_VERBOSE}" == "true" ]]; then
            ce_log_warn "PERF: '${operation}' exceeded budget by ${overage}ms (${overage_pct}%) [${duration_ms}ms > ${budget}ms]"
        fi
    fi

    # Log to file
    echo "$(date -Iseconds),${operation},${duration_ms},${exceeded}" >> "${CE_PERF_LOG_FILE}"

    if [[ "${CE_PERF_VERBOSE}" == "true" ]]; then
        ce_log_debug "PERF: '${operation}' completed in ${duration_ms}ms"
    fi

    # Clean up timer
    unset "CE_PERF_TIMERS[${operation}]"

    echo "${duration_ms}"
}

# Measure execution time of a command
ce_perf_measure() {
    local operation="${1:?Operation name required}"
    shift
    local command=("$@")

    ce_perf_start "${operation}"

    # Execute command and capture result
    local result=0
    "${command[@]}" || result=$?

    ce_perf_stop "${operation}"

    return ${result}
}

# Set custom performance budget
ce_perf_set_budget() {
    local operation="${1:?Operation name required}"
    local budget_ms="${2:?Budget in milliseconds required}"

    CE_PERF_BUDGETS["${operation}"]="${budget_ms}"

    if [[ "${CE_PERF_VERBOSE}" == "true" ]]; then
        ce_log_debug "PERF: Set budget for '${operation}' to ${budget_ms}ms"
    fi
}

# Get performance statistics
ce_perf_stats() {
    local operation="${1:-}"

    if [[ -n "${operation}" ]]; then
        # Stats for specific operation
        local count="${CE_PERF_COUNTS[${operation}]:-0}"
        local total="${CE_PERF_TOTALS[${operation}]:-0}"
        local avg=0

        if [[ ${count} -gt 0 ]]; then
            avg=$((total / count))
        fi

        local budget="${CE_PERF_BUDGETS[${operation}]:-0}"

        cat <<EOF
{
  "operation": "${operation}",
  "count": ${count},
  "total_ms": ${total},
  "average_ms": ${avg},
  "budget_ms": ${budget},
  "within_budget": $(( avg <= budget ))
}
EOF
    else
        # Stats for all operations
        echo "{"
        echo '  "operations": {'

        local first=true
        for op in "${!CE_PERF_COUNTS[@]}"; do
            [[ "${first}" == "true" ]] && first=false || echo ","

            local count="${CE_PERF_COUNTS[${op}]}"
            local total="${CE_PERF_TOTALS[${op}]}"
            local avg=$((total / count))
            local budget="${CE_PERF_BUDGETS[${op}]:-0}"

            cat <<EOF2
    "${op}": {
      "count": ${count},
      "total_ms": ${total},
      "average_ms": ${avg},
      "budget_ms": ${budget},
      "within_budget": $(( budget == 0 || avg <= budget ))
    }
EOF2
        done

        echo "  }"
        echo "}"
    fi
}

# Get performance report
ce_perf_report() {
    local format="${1:-text}"  # text or json

    if [[ "${format}" == "json" ]]; then
        ce_perf_stats
        return 0
    fi

    # Text format report
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  CE CLI Performance Report"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    printf "%-25s %8s %10s %10s %10s %s\n" \
        "Operation" "Count" "Total (ms)" "Avg (ms)" "Budget" "Status"
    echo "────────────────────────────────────────────────────────────────────"

    local total_operations=0
    local total_time=0
    local budget_violations=0

    for op in $(echo "${!CE_PERF_COUNTS[@]}" | tr ' ' '\n' | sort); do
        local count="${CE_PERF_COUNTS[${op}]}"
        local total="${CE_PERF_TOTALS[${op}]}"
        local avg=$((total / count))
        local budget="${CE_PERF_BUDGETS[${op}]:-0}"

        local status="✓"
        local status_color="${CE_COLOR_GREEN}"

        if [[ ${budget} -gt 0 ]] && [[ ${avg} -gt ${budget} ]]; then
            status="✗"
            status_color="${CE_COLOR_RED}"
            ((budget_violations++))
        fi

        printf "%-25s %8d %10d %10d %10s " \
            "${op}" "${count}" "${total}" "${avg}" "${budget:-N/A}"
        echo -e "${status_color}${status}${CE_COLOR_RESET}"

        ((total_operations += count))
        ((total_time += total))
    done

    echo "────────────────────────────────────────────────────────────────────"
    printf "%-25s %8d %10d\n" "TOTAL" "${total_operations}" "${total_time}"
    echo ""

    if [[ ${budget_violations} -gt 0 ]]; then
        echo -e "${CE_COLOR_YELLOW}⚠ ${budget_violations} operation(s) exceeded budget${CE_COLOR_RESET}"
    else
        echo -e "${CE_COLOR_GREEN}✓ All operations within budget${CE_COLOR_RESET}"
    fi

    echo ""
}

# Analyze performance log for trends
ce_perf_analyze() {
    local operation="${1:-}"
    local limit="${2:-100}"

    if [[ ! -f "${CE_PERF_LOG_FILE}" ]]; then
        echo "No performance log found"
        return 1
    fi

    if [[ -n "${operation}" ]]; then
        # Analyze specific operation
        echo "Performance analysis for: ${operation}"
        echo ""

        local data
        data=$(grep ",${operation}," "${CE_PERF_LOG_FILE}" | tail -n "${limit}")

        if [[ -z "${data}" ]]; then
            echo "No data found for operation: ${operation}"
            return 1
        fi

        # Calculate statistics
        local count
        count=$(echo "${data}" | wc -l)

        local durations
        durations=$(echo "${data}" | cut -d',' -f3)

        local min max sum
        min=$(echo "${durations}" | sort -n | head -1)
        max=$(echo "${durations}" | sort -n | tail -1)
        sum=$(echo "${durations}" | awk '{s+=$1} END {print s}')
        local avg=$((sum / count))

        # Calculate median (p50)
        local median
        median=$(echo "${durations}" | sort -n | awk '{a[NR]=$1} END {print (NR%2==1)?a[(NR+1)/2]:(a[NR/2]+a[NR/2+1])/2}')

        # Calculate p95 and p99
        local p95_idx=$((count * 95 / 100))
        local p99_idx=$((count * 99 / 100))
        local p95
        local p99
        p95=$(echo "${durations}" | sort -n | sed -n "${p95_idx}p")
        p99=$(echo "${durations}" | sort -n | sed -n "${p99_idx}p")

        # Budget violations
        local violations
        violations=$(echo "${data}" | grep ",true$" | wc -l)
        local violation_rate=$((violations * 100 / count))

        echo "Samples: ${count}"
        echo "Min: ${min}ms"
        echo "Max: ${max}ms"
        echo "Avg: ${avg}ms"
        echo "Median (p50): ${median}ms"
        echo "p95: ${p95}ms"
        echo "p99: ${p99}ms"
        echo "Budget violations: ${violations} (${violation_rate}%)"

    else
        # Show summary of all operations
        echo "Performance analysis summary (last ${limit} entries per operation)"
        echo ""

        # Get unique operations
        local operations
        operations=$(grep -v "^#" "${CE_PERF_LOG_FILE}" | cut -d',' -f2 | sort -u)

        printf "%-25s %8s %10s %10s %10s\n" \
            "Operation" "Samples" "Avg (ms)" "p95 (ms)" "Violations"
        echo "────────────────────────────────────────────────────────────────────"

        for op in ${operations}; do
            local data
            data=$(grep ",${op}," "${CE_PERF_LOG_FILE}" | tail -n "${limit}")

            local count
            count=$(echo "${data}" | wc -l)

            if [[ ${count} -eq 0 ]]; then
                continue
            fi

            local durations
            durations=$(echo "${data}" | cut -d',' -f3)

            local sum
            sum=$(echo "${durations}" | awk '{s+=$1} END {print s}')
            local avg=$((sum / count))

            local p95_idx=$((count * 95 / 100))
            local p95
            p95=$(echo "${durations}" | sort -n | sed -n "${p95_idx}p")

            local violations
            violations=$(echo "${data}" | grep ",true$" | wc -l)

            printf "%-25s %8d %10d %10s %10d\n" \
                "${op}" "${count}" "${avg}" "${p95:-N/A}" "${violations}"
        done
    fi
}

# Clear performance data
ce_perf_clear() {
    # Clear in-memory stats
    for op in "${!CE_PERF_COUNTS[@]}"; do
        unset "CE_PERF_COUNTS[${op}]"
        unset "CE_PERF_TOTALS[${op}]"
    done

    # Clear active timers
    for op in "${!CE_PERF_TIMERS[@]}"; do
        unset "CE_PERF_TIMERS[${op}]"
    done

    echo "Performance data cleared"
}

# Archive old performance log
ce_perf_archive() {
    if [[ ! -f "${CE_PERF_LOG_FILE}" ]]; then
        return 0
    fi

    local archive_dir
    archive_dir="$(dirname "${CE_PERF_LOG_FILE}")/archive"
    mkdir -p "${archive_dir}"

    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local archive_file="${archive_dir}/performance_${timestamp}.log"

    mv "${CE_PERF_LOG_FILE}" "${archive_file}"

    echo "Performance log archived to: ${archive_file}"
}

# Performance-wrapped git operations
ce_perf_git_status() {
    ce_perf_start "git_status"
    local result
    result=$(git status --porcelain 2>/dev/null || echo "")
    ce_perf_stop "git_status" >/dev/null
    echo "${result}"
}

ce_perf_git_branches() {
    ce_perf_start "git_branch_list"
    local result
    result=$(git branch --list 2>/dev/null || echo "")
    ce_perf_stop "git_branch_list" >/dev/null
    echo "${result}"
}

# Export functions
export -f ce_perf_init
export -f ce_perf_start
export -f ce_perf_stop
export -f ce_perf_measure
export -f ce_perf_set_budget
export -f ce_perf_stats
export -f ce_perf_report
export -f ce_perf_analyze
export -f ce_perf_clear
export -f ce_perf_archive
export -f ce_perf_git_status
export -f ce_perf_git_branches
