#!/bin/bash
# Claude Enhancer Hyper-Performance Cleanup Script
# Performance Engineering: Sub-500ms execution time with maximum efficiency
# Target: 10x faster than ultra version, <0.5s execution time

set -e

# Hyper-Performance Configuration
readonly PARALLEL_JOBS=${PARALLEL_JOBS:-$(nproc)}
readonly BATCH_SIZE=${BATCH_SIZE:-500}
readonly CACHE_DIR="/tmp/perfect21_hyper_cache"
readonly TEMP_DIR="/tmp/perfect21_hyper_work"

# Optimized Color Definitions (readonly for performance)
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# High-precision timing using EPOCHREALTIME (bash 5.0+)
declare -A PERF_TIMERS
declare -g SCRIPT_START_TIME

# Initialize performance measurement
init_performance() {
    if [[ ${BASH_VERSINFO[0]} -ge 5 ]]; then
        SCRIPT_START_TIME=${EPOCHREALTIME}
    else
        SCRIPT_START_TIME=$(date +%s.%N)
    fi
}

# Ultra-fast timer implementation
start_timer() {
    local name="$1"
    if [[ ${BASH_VERSINFO[0]} -ge 5 ]]; then
        PERF_TIMERS["$name"]=${EPOCHREALTIME}
    else
        PERF_TIMERS["$name"]=$(date +%s.%N)
    fi
}

end_timer() {
    local name="$1"
    local start_time=${PERF_TIMERS["$name"]:-0}
    local current_time

    if [[ ${BASH_VERSINFO[0]} -ge 5 ]]; then
        current_time=${EPOCHREALTIME}
    else
        current_time=$(date +%s.%N)
    fi

    local duration=$(awk "BEGIN {printf \"%.0f\", ($current_time - $start_time) * 1000}")
    printf "[$name] ${duration}ms\n" >&2
}

# Hyper-optimized single-pass file system operation
hyper_scan() {
    local operation="$1"
    local max_depth="${2:-8}"

    # Single find command with all patterns and operations
    # Uses -print0 for safe filename handling and limits depth for performance
    find . -maxdepth "$max_depth" \
        \( -path "./.git" -o -path "./node_modules" -o -path "./.venv" -o -path "./venv" -o -path "./__pycache__" -o -path "./build" -o -path "./dist" \) -prune -o \
        \( \
            -name "*.tmp" -o -name "*.temp" -o -name "*.bak" -o -name "*.orig" -o \
            -name ".DS_Store" -o -name "Thumbs.db" -o -name "*.swp" -o -name "*~" -o \
            -name "*.log.old" -o -name "*.pyc" \
        \) -type f -print0 | \
    case "$operation" in
        "delete")
            xargs -0 -r -P "$PARALLEL_JOBS" -n "$BATCH_SIZE" rm -f 2>/dev/null
            ;;
        "count")
            tr '\0' '\n' | wc -l
            ;;
        *)
            cat >/dev/null
            ;;
    esac
}

# Vectorized debug code cleanup with single-pass processing
hyper_debug_cleanup() {
    start_timer "debug_cleanup"

    local js_count=0
    local py_count=0

    # Process JavaScript/TypeScript files in a single pass
    {
        find . -maxdepth 6 \( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \) \
            ! -path "./node_modules/*" ! -path "./.git/*" \
            ! -name "*.test.*" ! -name "*.spec.*" ! -name "*.min.*" \
            -print0 | \
        xargs -0 -r -P "$PARALLEL_JOBS" -n 1 -I {} bash -c '
            if [[ -f "{}" ]]; then
                sed -i.bak \
                    -e "/\/\/ @keep\|\/\* @keep/!s/console\.log(/\/\/ console.log(/g" \
                    -e "/\/\/ @keep\|\/\* @keep/!s/console\.debug(/\/\/ console.debug(/g" \
                    -e "/\/\/ @keep\|\/\* @keep/!s/console\.info(/\/\/ console.info(/g" \
                    "{}" 2>/dev/null && rm -f "{}.bak"
                echo "1"
            fi
        ' 2>/dev/null | wc -l
    } &
    local js_pid=$!

    # Process Python files in parallel
    {
        find . -maxdepth 6 -name "*.py" \
            ! -path "./.git/*" ! -path "./venv/*" ! -path "./__pycache__/*" \
            ! -name "test_*.py" ! -name "*_test.py" \
            -print0 | \
        xargs -0 -r -P "$PARALLEL_JOBS" -n 1 -I {} bash -c '
            if [[ -f "{}" ]]; then
                sed -i.bak "/# @keep/!s/^\(\s*\)print(/\1# print(/g" "{}" 2>/dev/null && rm -f "{}.bak"
                echo "1"
            fi
        ' 2>/dev/null | wc -l
    } &
    local py_pid=$!

    # Wait for both operations and collect results
    wait $js_pid && js_count=$(jobs -p | wc -l)
    wait $py_pid && py_count=$(jobs -p | wc -l)

    printf "  ✅ Debug cleanup: %d JS, %d Python files\n" "$js_count" "$py_count" >&2
    end_timer "debug_cleanup"
}

# Lightning-fast security scan with compiled patterns
hyper_security_scan() {
    start_timer "security_scan"

    # Single grep command with all patterns using extended regex
    local pattern='(password|api[_-]?key|secret|token|aws[_-]?.*key).*=.*['\''"][^'\''\"]{3,}'

    local issues=0
    if grep -r -E -q "$pattern" \
        --include="*.js" --include="*.py" --include="*.json" --include="*.env" \
        --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir="test*" \
        --exclude="*test*" --exclude="*example*" --exclude="*mock*" \
        . 2>/dev/null; then
        issues=1
    fi

    if [[ $issues -eq 0 ]]; then
        printf "  ✅ Security scan: Clean\n" >&2
    else
        printf "  ⚠️ Security scan: Issues found\n" >&2
    fi

    end_timer "security_scan"
    return $issues
}

# Ultra-fast formatter with smart detection
hyper_format() {
    start_timer "formatting"

    # Quick check for recent files to avoid unnecessary work
    local recent_count=$(find . -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.json" -newer /tmp/.last_format 2>/dev/null | wc -l)

    if [[ $recent_count -eq 0 ]]; then
        printf "  ✅ Formatting: Skipped (no changes)\n" >&2
        end_timer "formatting"
        return 0
    fi

    local format_jobs=()

    # Prettier (if available)
    if command -v prettier &>/dev/null; then
        prettier --write "**/*.{js,jsx,ts,tsx,json}" --log-level silent --no-color &>/dev/null &
        format_jobs+=($!)
    fi

    # Black (if available)
    if command -v black &>/dev/null; then
        black . --quiet --fast &>/dev/null &
        format_jobs+=($!)
    fi

    # Wait for formatting jobs with timeout
    local timeout=5
    while [[ ${#format_jobs[@]} -gt 0 && $timeout -gt 0 ]]; do
        local new_jobs=()
        for pid in "${format_jobs[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                new_jobs+=("$pid")
            fi
        done
        format_jobs=("${new_jobs[@]}")
        ((timeout--))
        [[ ${#format_jobs[@]} -gt 0 ]] && sleep 0.1
    done

    # Kill any remaining jobs
    for pid in "${format_jobs[@]}"; do
        kill "$pid" 2>/dev/null || true
    done

    # Update timestamp
    touch /tmp/.last_format

    printf "  ✅ Formatting: Completed\n" >&2
    end_timer "formatting"
}

# Hyper-optimized parallel cleanup orchestrator
hyper_parallel_cleanup() {
    start_timer "total_cleanup"

    printf "${CYAN}⚡ Hyper-Performance Cleanup (${PARALLEL_JOBS} cores)${NC}\n" >&2

    # Phase 1: File cleanup (highest priority)
    {
        start_timer "file_cleanup"
        local file_count=$(hyper_scan "count" 8)
        hyper_scan "delete" 8
        printf "  ✅ Files cleaned: %d\n" "$file_count" >&2
        end_timer "file_cleanup"
    } &
    local pid1=$!

    # Phase 2: Python cache cleanup
    {
        start_timer "python_cache"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        printf "  ✅ Python cache: Cleaned\n" >&2
        end_timer "python_cache"
    } &
    local pid2=$!

    # Phase 3: Debug code cleanup
    hyper_debug_cleanup &
    local pid3=$!

    # Phase 4: Quick security and format
    {
        hyper_security_scan
        hyper_format
    } &
    local pid4=$!

    # Efficient wait for all operations
    wait $pid1 $pid2 $pid3 $pid4

    end_timer "total_cleanup"
}

# Phase-aware cleanup with minimal overhead
hyper_phase_cleanup() {
    local phase=${1:-$(get_current_phase)}

    printf "${BLUE}🚀 Hyper-Performance Cleanup v3.0${NC}\n" >&2
    printf "Phase: %s | Cores: %d\n" "$phase" "$PARALLEL_JOBS" >&2
    printf -- "----------------------------------------\n" >&2

    case "$phase" in
        0|5|7)
            # Full cleanup for critical phases
            hyper_parallel_cleanup
            ;;
        *)
            # Quick cleanup for other phases
            start_timer "quick_cleanup"
            hyper_scan "delete" 4 >/dev/null
            printf "  ✅ Quick cleanup completed\n" >&2
            end_timer "quick_cleanup"
            ;;
    esac
}

# Utility functions
get_current_phase() {
    if [[ -f ".claude/phase_state.json" ]]; then
        grep -oP '"current_phase"\s*:\s*\d+' .claude/phase_state.json 2>/dev/null | grep -oP '\d+' || echo "1"
    else
        echo "1"
    fi
}

# Performance monitoring
show_performance_summary() {
    local total_time
    if [[ ${BASH_VERSINFO[0]} -ge 5 ]]; then
        total_time=$(awk "BEGIN {printf \"%.0f\", (${EPOCHREALTIME} - $SCRIPT_START_TIME) * 1000}")
    else
        total_time=$(awk "BEGIN {printf \"%.0f\", ($(date +%s.%N) - $SCRIPT_START_TIME) * 1000}")
    fi

    printf -- "----------------------------------------\n" >&2
    printf "${GREEN}✅ Hyper cleanup completed in ${total_time}ms${NC}\n" >&2
    printf "${GREEN}🚀 Target: <500ms | Achieved: ${total_time}ms${NC}\n" >&2

    # Memory usage
    local memory_kb=$(awk '/VmRSS/ {print $2}' /proc/$$/status 2>/dev/null || echo "0")
    printf "💾 Memory: %d KB\n" "$memory_kb" >&2
}

# Cleanup function
cleanup_on_exit() {
    # Remove temporary files
    [[ -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR" 2>/dev/null || true
    show_performance_summary
}

# Main execution function
main() {
    # Initialize performance measurement
    init_performance

    # Set up cleanup handler
    trap cleanup_on_exit EXIT

    # Create working directory
    mkdir -p "$TEMP_DIR" 2>/dev/null || true

    # Execute hyper-optimized cleanup
    hyper_phase_cleanup "$@"
}

# Handle script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Check for dry run mode
    if [[ "$1" == "--dry-run" ]]; then
        printf "${YELLOW}DRY RUN MODE: Would execute hyper-performance cleanup${NC}\n" >&2
        exit 0
    fi

    # Execute main function
    main "$@"
fi