#!/usr/bin/env bash
# Performance Profiler for Claude Enhancer v5.4.0
# Purpose: Profile script execution and identify bottlenecks
# Usage: source profiler.sh && profile_start && <your commands> && profile_end

set -euo pipefail

# Configuration
PROFILE_DIR="/tmp/ce_profile_$$"
PROFILE_ENABLED="${CE_PROFILE:-0}"
PROFILE_OUTPUT="${CE_PROFILE_OUTPUT:-${PROFILE_DIR}/profile.txt}"

# Profiling data
declare -A PROFILE_FUNCTION_TIMES=()
declare -A PROFILE_FUNCTION_CALLS=()
declare -A PROFILE_FUNCTION_START=()

# Create profile directory
mkdir -p "$PROFILE_DIR"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# ============================================================================
# Core Profiling Functions
# ============================================================================

profile_start() {
    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        return 0
    fi

    export PROFILE_START_TIME=$(date +%s%N)
    echo "Profiling started at $(date)"

    # Enable function tracing
    set -T
    trap 'profile_function_entry' DEBUG
}

profile_end() {
    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        return 0
    fi

    # Disable function tracing
    trap - DEBUG
    set +T

    local end_time=$(date +%s%N)
    local duration_ns=$((end_time - PROFILE_START_TIME))
    local duration_ms=$(echo "scale=2; $duration_ns / 1000000" | bc)

    echo "Profiling ended at $(date)"
    echo "Total duration: ${duration_ms}ms"

    # Generate report
    generate_profile_report
}

profile_function_entry() {
    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        return 0
    fi

    local func_name="${FUNCNAME[1]:-main}"
    local timestamp=$(date +%s%N)

    # Skip internal bash functions and profiler functions
    if [[ "$func_name" == "profile_"* ]] || [[ "$func_name" == "source" ]] || [[ "$func_name" == "main" ]]; then
        return 0
    fi

    # Record function call
    PROFILE_FUNCTION_CALLS["$func_name"]=$((${PROFILE_FUNCTION_CALLS[$func_name]:-0} + 1))

    # Record start time
    PROFILE_FUNCTION_START["$func_name"]=$timestamp
}

profile_function_exit() {
    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        return 0
    fi

    local func_name="${1:-unknown}"
    local end_time=$(date +%s%N)
    local start_time="${PROFILE_FUNCTION_START[$func_name]:-$end_time}"

    local duration_ns=$((end_time - start_time))

    # Accumulate time
    PROFILE_FUNCTION_TIMES["$func_name"]=$((${PROFILE_FUNCTION_TIMES[$func_name]:-0} + duration_ns))

    # Clear start time
    unset PROFILE_FUNCTION_START["$func_name"]
}

# ============================================================================
# Manual Profiling Markers
# ============================================================================

profile_section_start() {
    local section_name="$1"

    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        return 0
    fi

    PROFILE_FUNCTION_START["section:$section_name"]=$(date +%s%N)
    echo "Section started: $section_name"
}

profile_section_end() {
    local section_name="$1"

    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        return 0
    fi

    local end_time=$(date +%s%N)
    local start_time="${PROFILE_FUNCTION_START[section:$section_name]:-$end_time}"
    local duration_ns=$((end_time - start_time))
    local duration_ms=$(echo "scale=2; $duration_ns / 1000000" | bc)

    echo "Section ended: $section_name (${duration_ms}ms)"

    # Record section time
    PROFILE_FUNCTION_TIMES["section:$section_name"]=$duration_ns
    PROFILE_FUNCTION_CALLS["section:$section_name"]=1
}

profile_command() {
    local cmd_name="$1"
    shift
    local cmd=("$@")

    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        "${cmd[@]}"
        return $?
    fi

    local start_time=$(date +%s%N)
    "${cmd[@]}"
    local exit_code=$?
    local end_time=$(date +%s%N)

    local duration_ns=$((end_time - start_time))
    local duration_ms=$(echo "scale=2; $duration_ns / 1000000" | bc)

    echo "Command '$cmd_name' took ${duration_ms}ms"

    # Record command time
    PROFILE_FUNCTION_TIMES["cmd:$cmd_name"]=${duration_ns}
    PROFILE_FUNCTION_CALLS["cmd:$cmd_name"]=1

    return $exit_code
}

# ============================================================================
# Report Generation
# ============================================================================

generate_profile_report() {
    local report_file="$PROFILE_OUTPUT"

    echo "Generating profile report: $report_file"

    cat > "$report_file" <<EOF
Performance Profile Report
==========================

Generated: $(date)
Total Duration: $(echo "scale=2; ($(($(date +%s%N) - PROFILE_START_TIME))) / 1000000" | bc)ms

Function Call Statistics:
-------------------------

EOF

    # Sort functions by total time
    {
        for func in "${!PROFILE_FUNCTION_TIMES[@]}"; do
            local total_ns="${PROFILE_FUNCTION_TIMES[$func]}"
            local calls="${PROFILE_FUNCTION_CALLS[$func]:-1}"
            local avg_ns=$((total_ns / calls))

            local total_ms=$(echo "scale=2; $total_ns / 1000000" | bc)
            local avg_ms=$(echo "scale=2; $avg_ns / 1000000" | bc)

            echo "$func|$total_ms|$avg_ms|$calls"
        done
    } | sort -t'|' -k2 -rn | while IFS='|' read -r func total avg calls; do
        printf "%-40s %10s ms (avg: %8s ms, calls: %5s)\n" "$func" "$total" "$avg" "$calls"
    done >> "$report_file"

    cat >> "$report_file" <<EOF

Top 10 Slowest Functions:
-------------------------

EOF

    {
        for func in "${!PROFILE_FUNCTION_TIMES[@]}"; do
            local total_ns="${PROFILE_FUNCTION_TIMES[$func]}"
            local total_ms=$(echo "scale=2; $total_ns / 1000000" | bc)
            echo "$func|$total_ms"
        done
    } | sort -t'|' -k2 -rn | head -n 10 | while IFS='|' read -r func time; do
        printf "  %-40s %10s ms\n" "$func" "$time"
    done >> "$report_file"

    cat >> "$report_file" <<EOF

Top 10 Most Called Functions:
------------------------------

EOF

    {
        for func in "${!PROFILE_FUNCTION_CALLS[@]}"; do
            local calls="${PROFILE_FUNCTION_CALLS[$func]}"
            echo "$func|$calls"
        done
    } | sort -t'|' -k2 -rn | head -n 10 | while IFS='|' read -r func calls; do
        printf "  %-40s %10s calls\n" "$func" "$calls"
    done >> "$report_file"

    echo ""
    echo "Profile report saved to: $report_file"

    # Display summary
    display_profile_summary
}

display_profile_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "         Performance Profile Summary"
    echo "═══════════════════════════════════════════════════════"
    echo ""

    # Top 5 slowest functions
    echo "Top 5 Slowest Functions:"
    {
        for func in "${!PROFILE_FUNCTION_TIMES[@]}"; do
            local total_ns="${PROFILE_FUNCTION_TIMES[$func]}"
            local total_ms=$(echo "scale=2; $total_ns / 1000000" | bc)
            echo "$func|$total_ms"
        done
    } | sort -t'|' -k2 -rn | head -n 5 | while IFS='|' read -r func time; do
        printf "  %-40s %10s ms\n" "$func" "$time"
    done

    echo ""

    # Total functions profiled
    echo "Total Functions: ${#PROFILE_FUNCTION_TIMES[@]}"
    echo "Total Calls: $(( $(IFS=+; echo "$((${PROFILE_FUNCTION_CALLS[*]:-0}))") ))"

    echo ""
    echo "═══════════════════════════════════════════════════════"
}

# ============================================================================
# Flame Graph Generation (if available)
# ============================================================================

generate_flame_graph() {
    local output_file="${1:-${PROFILE_DIR}/flamegraph.svg}"

    if ! command -v flamegraph.pl &>/dev/null; then
        echo "flamegraph.pl not found. Install from: https://github.com/brendangregg/FlameGraph"
        return 1
    fi

    # Convert profile data to flame graph format
    local stacks_file="${PROFILE_DIR}/stacks.txt"

    {
        for func in "${!PROFILE_FUNCTION_TIMES[@]}"; do
            local total_ns="${PROFILE_FUNCTION_TIMES[$func]}"
            local calls="${PROFILE_FUNCTION_CALLS[$func]:-1}"
            echo "$func $total_ns"
        done
    } > "$stacks_file"

    # Generate flame graph
    flamegraph.pl "$stacks_file" > "$output_file"

    echo "Flame graph generated: $output_file"
}

# ============================================================================
# Bottleneck Detection
# ============================================================================

detect_bottlenecks() {
    local threshold_ms="${1:-100}"  # Functions taking >100ms are considered bottlenecks

    echo "Detecting bottlenecks (threshold: ${threshold_ms}ms)..."
    echo ""

    local found_bottlenecks=0

    for func in "${!PROFILE_FUNCTION_TIMES[@]}"; do
        local total_ns="${PROFILE_FUNCTION_TIMES[$func]}"
        local total_ms=$(echo "scale=2; $total_ns / 1000000" | bc)

        if (( $(echo "$total_ms > $threshold_ms" | bc -l) )); then
            local calls="${PROFILE_FUNCTION_CALLS[$func]:-1}"
            local avg_ms=$(echo "scale=2; $total_ms / $calls" | bc)

            echo -e "${RED}[BOTTLENECK]${NC} $func"
            echo "  Total time: ${total_ms}ms"
            echo "  Average time: ${avg_ms}ms"
            echo "  Calls: $calls"
            echo ""

            found_bottlenecks=$((found_bottlenecks + 1))
        fi
    done

    if [[ $found_bottlenecks -eq 0 ]]; then
        echo -e "${GREEN}No bottlenecks detected${NC}"
    else
        echo -e "${YELLOW}Found $found_bottlenecks bottleneck(s)${NC}"
    fi
}

# ============================================================================
# Memory Profiling
# ============================================================================

profile_memory_start() {
    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        return 0
    fi

    PROFILE_MEMORY_START=$(ps -o rss= -p $$ | xargs)
    echo "Initial memory: ${PROFILE_MEMORY_START}KB"
}

profile_memory_end() {
    if [[ "$PROFILE_ENABLED" != "1" ]]; then
        return 0
    fi

    local memory_end=$(ps -o rss= -p $$ | xargs)
    local memory_diff=$((memory_end - PROFILE_MEMORY_START))
    local memory_diff_mb=$(echo "scale=2; $memory_diff / 1024" | bc)

    echo "Final memory: ${memory_end}KB"
    echo "Memory increase: ${memory_diff_mb}MB"

    # Add to report
    {
        echo ""
        echo "Memory Profile:"
        echo "  Start: ${PROFILE_MEMORY_START}KB"
        echo "  End: ${memory_end}KB"
        echo "  Increase: ${memory_diff_mb}MB"
    } >> "$PROFILE_OUTPUT"
}

# ============================================================================
# CPU Profiling
# ============================================================================

profile_cpu_usage() {
    local duration="${1:-10}"
    local interval="${2:-1}"

    echo "Profiling CPU usage for ${duration}s..."

    local samples=()
    local count=0

    while [[ $count -lt $duration ]]; do
        local cpu=$(ps -p $$ -o %cpu= | xargs)
        samples+=("$cpu")
        count=$((count + interval))
        sleep "$interval"
    done

    # Calculate statistics
    local total=0
    local max=0

    for sample in "${samples[@]}"; do
        total=$(echo "$total + $sample" | bc)
        if (( $(echo "$sample > $max" | bc -l) )); then
            max=$sample
        fi
    done

    local avg=$(echo "scale=2; $total / ${#samples[@]}" | bc)

    echo "CPU Usage:"
    echo "  Average: ${avg}%"
    echo "  Peak: ${max}%"
    echo "  Samples: ${#samples[@]}"

    # Add to report
    {
        echo ""
        echo "CPU Profile:"
        echo "  Average: ${avg}%"
        echo "  Peak: ${max}%"
    } >> "$PROFILE_OUTPUT"
}

# ============================================================================
# Export Functions
# ============================================================================

export -f profile_start
export -f profile_end
export -f profile_section_start
export -f profile_section_end
export -f profile_command
export -f detect_bottlenecks
export -f profile_memory_start
export -f profile_memory_end
export -f profile_cpu_usage

# Auto-setup if sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    if [[ "$PROFILE_ENABLED" == "1" ]]; then
        echo "Profiler loaded and enabled"
    fi
fi
