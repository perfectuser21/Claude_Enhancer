#!/bin/bash
# Claude Enhancer Real-time Performance Monitor
# Continuous monitoring of cleanup script performance with live dashboard

set -e

# Monitor Configuration
readonly MONITOR_INTERVAL=1
readonly LOG_FILE="/tmp/perfect21_performance.log"
readonly DASHBOARD_FILE="/tmp/perfect21_dashboard.txt"
readonly MAX_LOG_ENTRIES=1000

# Color definitions
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Performance data storage
declare -A PERFORMANCE_DATA
declare -A EXECUTION_HISTORY
declare -g MONITORING_ACTIVE=true

# Initialize monitoring system
init_monitoring() {
    printf "${BLUE}🚀 Initializing Real-time Performance Monitor${NC}\n"

    # Create log file with header
    cat > "$LOG_FILE" << 'EOF'
timestamp,script,execution_time_ms,memory_kb,cpu_percent,files_processed,status
EOF

    # Initialize performance tracking
    PERFORMANCE_DATA["executions"]=0
    PERFORMANCE_DATA["total_time"]=0
    PERFORMANCE_DATA["min_time"]=999999
    PERFORMANCE_DATA["max_time"]=0
    PERFORMANCE_DATA["failures"]=0

    printf "  ✅ Monitor initialized\n"
    printf "  📊 Log file: %s\n" "$LOG_FILE"
    printf "  📺 Dashboard: %s\n" "$DASHBOARD_FILE"
}

# Get system resource usage
get_system_resources() {
    local cpu_usage
    local memory_usage_kb
    local load_avg

    # CPU usage (1-second average)
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')

    # Memory usage
    memory_usage_kb=$(awk '/MemAvailable/ {available=$2} /MemTotal/ {total=$2} END {used=total-available; print used}' /proc/meminfo)

    # Load average
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')

    echo "${cpu_usage:-0}:${memory_usage_kb:-0}:${load_avg:-0}"
}

# Monitor script execution
monitor_script_execution() {
    local script_path="$1"
    local script_name="$2"

    local start_time
    local end_time
    local execution_time_ms
    local memory_before
    local memory_after
    local memory_used
    local exit_code

    if [[ ${BASH_VERSINFO[0]} -ge 5 ]]; then
        start_time=${EPOCHREALTIME}
    else
        start_time=$(date +%s.%N)
    fi

    # Get memory before execution
    memory_before=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)

    # Execute script and capture exit code
    bash "$script_path" >/dev/null 2>&1
    exit_code=$?

    # Calculate execution time
    if [[ ${BASH_VERSINFO[0]} -ge 5 ]]; then
        end_time=${EPOCHREALTIME}
    else
        end_time=$(date +%s.%N)
    fi

    execution_time_ms=$(awk "BEGIN {printf \"%.0f\", ($end_time - $start_time) * 1000}")

    # Get memory after execution
    memory_after=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    memory_used=$((memory_before - memory_after))

    # Get system resources
    IFS=':' read -r cpu_percent memory_kb load_avg <<< "$(get_system_resources)"

    # Update performance statistics
    update_performance_stats "$script_name" "$execution_time_ms" "$exit_code"

    # Log execution data
    log_execution "$script_name" "$execution_time_ms" "$memory_used" "$cpu_percent" "0" "$exit_code"

    # Return execution time for caller
    echo "$execution_time_ms"
}

# Update performance statistics
update_performance_stats() {
    local script_name="$1"
    local execution_time_ms="$2"
    local exit_code="$3"

    # Update global counters
    ((PERFORMANCE_DATA["executions"]++))
    PERFORMANCE_DATA["total_time"]=$((PERFORMANCE_DATA["total_time"] + execution_time_ms))

    # Update min/max times
    if [[ $execution_time_ms -lt ${PERFORMANCE_DATA["min_time"]} ]]; then
        PERFORMANCE_DATA["min_time"]=$execution_time_ms
    fi

    if [[ $execution_time_ms -gt ${PERFORMANCE_DATA["max_time"]} ]]; then
        PERFORMANCE_DATA["max_time"]=$execution_time_ms
    fi

    # Track failures
    if [[ $exit_code -ne 0 ]]; then
        ((PERFORMANCE_DATA["failures"]++))
    fi

    # Store in execution history (last 10 executions)
    local history_key="${script_name}_history"
    local current_history="${EXECUTION_HISTORY[$history_key]:-}"
    EXECUTION_HISTORY[$history_key]="${current_history} ${execution_time_ms}"

    # Keep only last 10 entries
    local history_array=($current_history $execution_time_ms)
    if [[ ${#history_array[@]} -gt 10 ]]; then
        EXECUTION_HISTORY[$history_key]="${history_array[@]: -10}"
    fi
}

# Log execution to file
log_execution() {
    local script_name="$1"
    local execution_time_ms="$2"
    local memory_kb="$3"
    local cpu_percent="$4"
    local files_processed="$5"
    local exit_code="$6"

    local timestamp=$(date -Iseconds)
    local status=$([[ $exit_code -eq 0 ]] && echo "SUCCESS" || echo "FAILURE")

    # Append to log file
    echo "${timestamp},${script_name},${execution_time_ms},${memory_kb},${cpu_percent},${files_processed},${status}" >> "$LOG_FILE"

    # Rotate log if too large
    local line_count=$(wc -l < "$LOG_FILE")
    if [[ $line_count -gt $MAX_LOG_ENTRIES ]]; then
        tail -n $((MAX_LOG_ENTRIES - 1)) "$LOG_FILE" > "${LOG_FILE}.tmp"
        mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi
}

# Generate real-time dashboard
generate_dashboard() {
    local current_time=$(date '+%Y-%m-%d %H:%M:%S')
    local avg_time=0

    if [[ ${PERFORMANCE_DATA["executions"]} -gt 0 ]]; then
        avg_time=$((PERFORMANCE_DATA["total_time"] / PERFORMANCE_DATA["executions"]))
    fi

    local success_rate=100
    if [[ ${PERFORMANCE_DATA["executions"]} -gt 0 ]]; then
        local successful=$((PERFORMANCE_DATA["executions"] - PERFORMANCE_DATA["failures"]))
        success_rate=$(( (successful * 100) / PERFORMANCE_DATA["executions"] ))
    fi

    # Get current system resources
    IFS=':' read -r cpu_percent memory_kb load_avg <<< "$(get_system_resources)"

    cat > "$DASHBOARD_FILE" << EOF
╔════════════════════════════════════════════════════════════════════════════════╗
║                     Claude Enhancer Performance Dashboard                      ║
║                              Updated: ${current_time}                          ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ 📊 EXECUTION STATISTICS                                                        ║
║    Total Executions: ${PERFORMANCE_DATA["executions"]}                                                      ║
║    Success Rate:     ${success_rate}%                                                       ║
║    Failures:         ${PERFORMANCE_DATA["failures"]}                                                       ║
║                                                                                ║
║ ⚡ PERFORMANCE METRICS                                                         ║
║    Average Time:     ${avg_time} ms                                            ║
║    Best Time:        ${PERFORMANCE_DATA["min_time"]} ms                                             ║
║    Worst Time:       ${PERFORMANCE_DATA["max_time"]} ms                                            ║
║    Target:           <500 ms                                                   ║
║                                                                                ║
║ 💾 SYSTEM RESOURCES                                                           ║
║    CPU Usage:        ${cpu_percent}%                                                       ║
║    Memory Used:      ${memory_kb} KB                                              ║
║    Load Average:     ${load_avg}                                                       ║
║                                                                                ║
║ 🎯 PERFORMANCE STATUS                                                         ║
EOF

    # Add performance status indicator
    if [[ $avg_time -le 500 && $avg_time -gt 0 ]]; then
        echo "║    Status:           ✅ TARGET ACHIEVED                                       ║" >> "$DASHBOARD_FILE"
    elif [[ $avg_time -gt 500 ]]; then
        echo "║    Status:           ❌ TARGET MISSED                                         ║" >> "$DASHBOARD_FILE"
    else
        echo "║    Status:           ⏳ WAITING FOR DATA                                      ║" >> "$DASHBOARD_FILE"
    fi

    cat >> "$DASHBOARD_FILE" << 'EOF'
║                                                                                ║
║ 📈 RECENT EXECUTIONS (Last 10)                                                ║
EOF

    # Add recent execution times
    local recent_executions=()
    for key in "${!EXECUTION_HISTORY[@]}"; do
        if [[ $key == *"_history" ]]; then
            local script_name=${key%_history}
            local history=(${EXECUTION_HISTORY[$key]})
            if [[ ${#history[@]} -gt 0 ]]; then
                recent_executions+=("${script_name}: ${history[@]: -5}")
            fi
        fi
    done

    if [[ ${#recent_executions[@]} -eq 0 ]]; then
        echo "║    No recent executions                                                    ║" >> "$DASHBOARD_FILE"
    else
        for execution in "${recent_executions[@]}"; do
            printf "║    %-70s ║\n" "$execution" >> "$DASHBOARD_FILE"
        done
    fi

    cat >> "$DASHBOARD_FILE" << 'EOF'
║                                                                                ║
║ 🔧 MONITORING CONTROLS                                                        ║
║    [Ctrl+C] Stop monitoring                                                    ║
║    [Enter]  Refresh display                                                    ║
╚════════════════════════════════════════════════════════════════════════════════╝
EOF
}

# Display dashboard in terminal
display_dashboard() {
    clear
    if [[ -f "$DASHBOARD_FILE" ]]; then
        cat "$DASHBOARD_FILE"
    else
        printf "${RED}❌ Dashboard file not found${NC}\n"
    fi
}

# Run continuous monitoring
start_continuous_monitoring() {
    local scripts_to_monitor=(
        "/home/xx/dev/Perfect21/.claude/scripts/cleanup.sh:Original"
        "/home/xx/dev/Perfect21/.claude/scripts/ultra_optimized_cleanup.sh:Ultra"
        "/home/xx/dev/Perfect21/.claude/scripts/hyper_performance_cleanup.sh:Hyper"
    )

    printf "${CYAN}🔄 Starting continuous monitoring...${NC}\n"
    printf "Press Ctrl+C to stop monitoring\n\n"

    # Set up signal handler
    trap 'MONITORING_ACTIVE=false; cleanup_monitoring' INT TERM

    local iteration=0
    while [[ $MONITORING_ACTIVE == true ]]; do
        ((iteration++))

        # Monitor each script
        for script_info in "${scripts_to_monitor[@]}"; do
            IFS=':' read -r script_path script_name <<< "$script_info"

            if [[ -f "$script_path" ]]; then
                printf "${BLUE}[%s] Testing %s...${NC}\r" "$(date '+%H:%M:%S')" "$script_name"
                monitor_script_execution "$script_path" "$script_name" >/dev/null
            fi
        done

        # Update dashboard
        generate_dashboard
        display_dashboard

        # Show current iteration
        printf "\n${YELLOW}Monitoring iteration: %d${NC}\n" "$iteration"

        # Wait before next iteration
        sleep "$MONITOR_INTERVAL"
    done
}

# Run single performance test
run_single_test() {
    local script_path="$1"
    local script_name="${2:-$(basename "$script_path")}"

    printf "${CYAN}🧪 Single Test: %s${NC}\n" "$script_name"

    if [[ ! -f "$script_path" ]]; then
        printf "${RED}❌ Script not found: %s${NC}\n" "$script_path"
        return 1
    fi

    local execution_time_ms
    execution_time_ms=$(monitor_script_execution "$script_path" "$script_name")

    printf "  ⏱️ Execution Time: %d ms\n" "$execution_time_ms"

    if [[ $execution_time_ms -le 500 ]]; then
        printf "  ${GREEN}✅ Target achieved (<500ms)${NC}\n"
    else
        printf "  ${RED}❌ Target missed (>500ms)${NC}\n"
    fi

    # Generate single test dashboard
    generate_dashboard
    printf "\n"
    cat "$DASHBOARD_FILE"
}

# Cleanup monitoring
cleanup_monitoring() {
    printf "\n${YELLOW}🧹 Stopping performance monitoring...${NC}\n"

    # Generate final summary
    if [[ ${PERFORMANCE_DATA["executions"]} -gt 0 ]]; then
        local avg_time=$((PERFORMANCE_DATA["total_time"] / PERFORMANCE_DATA["executions"]))
        printf "\n${BOLD}📊 Final Summary:${NC}\n"
        printf "  Total Executions: %d\n" "${PERFORMANCE_DATA["executions"]}"
        printf "  Average Time: %d ms\n" "$avg_time"
        printf "  Best Time: %d ms\n" "${PERFORMANCE_DATA["min_time"]}"
        printf "  Worst Time: %d ms\n" "${PERFORMANCE_DATA["max_time"]}"
        printf "  Success Rate: %d%%\n" "$(( (PERFORMANCE_DATA["executions"] - PERFORMANCE_DATA["failures"]) * 100 / PERFORMANCE_DATA["executions"] ))"
    fi

    printf "  📊 Performance log: %s\n" "$LOG_FILE"
    printf "${GREEN}✅ Monitoring stopped${NC}\n"
}

# Display help
show_help() {
    cat << 'EOF'
Claude Enhancer Real-time Performance Monitor

Usage:
    ./realtime_performance_monitor.sh [OPTIONS] [SCRIPT_PATH]

Options:
    --continuous, -c     Start continuous monitoring of all scripts
    --single, -s         Run single test on specified script
    --dashboard, -d      Show current dashboard only
    --help, -h           Show this help message

Examples:
    # Continuous monitoring
    ./realtime_performance_monitor.sh --continuous

    # Single test
    ./realtime_performance_monitor.sh --single cleanup.sh

    # Show dashboard
    ./realtime_performance_monitor.sh --dashboard

Features:
    - Real-time performance tracking
    - Live dashboard with metrics
    - Automatic logging to CSV
    - System resource monitoring
    - Success/failure tracking
    - Performance trend analysis
EOF
}

# Main execution function
main() {
    case "${1:-}" in
        --continuous|-c)
            init_monitoring
            start_continuous_monitoring
            ;;
        --single|-s)
            if [[ -z "${2:-}" ]]; then
                printf "${RED}❌ Error: Script path required for single test${NC}\n"
                show_help
                exit 1
            fi
            init_monitoring
            run_single_test "$2" "${3:-}"
            ;;
        --dashboard|-d)
            if [[ -f "$DASHBOARD_FILE" ]]; then
                display_dashboard
            else
                printf "${YELLOW}⚠️ No dashboard data available${NC}\n"
                printf "Run monitoring first to generate dashboard data.\n"
            fi
            ;;
        --help|-h)
            show_help
            ;;
        "")
            printf "${BLUE}🚀 Claude Enhancer Performance Monitor${NC}\n"
            printf "Use --help for usage information\n"
            show_help
            ;;
        *)
            printf "${RED}❌ Unknown option: %s${NC}\n" "$1"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi