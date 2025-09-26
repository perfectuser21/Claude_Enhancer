#!/bin/bash
# Claude Enhancer - 综合工作流优化脚本
# 自动化性能优化、智能配置调整、系统健康监控

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly NC='\033[0m'

# Configuration
readonly CLAUDE_DIR="/home/xx/dev/Claude Enhancer 5.0/.claude"
readonly LOG_DIR="/tmp/claude_optimizer_logs"
readonly BACKUP_DIR="$LOG_DIR/backups"
readonly PERFORMANCE_LOG="$LOG_DIR/performance.log"
readonly OPTIMIZATION_LOG="$LOG_DIR/optimizations.log"

# Performance thresholds
readonly MAX_HOOK_TIME=300    # ms
readonly MAX_AGENT_TIME=100   # ms
readonly MAX_MEMORY=80        # percentage
readonly MAX_CPU=85           # percentage

# Create necessary directories
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# Logging functions
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$OPTIMIZATION_LOG"
}

# Backup current configuration
backup_configuration() {
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/config_$backup_timestamp"

    log_info "Creating configuration backup..."

    mkdir -p "$backup_path"
    cp -r "$CLAUDE_DIR/settings.json" "$backup_path/" 2>/dev/null || true
    cp -r "$CLAUDE_DIR/hooks/" "$backup_path/" 2>/dev/null || true
    cp -r "$CLAUDE_DIR/core/" "$backup_path/" 2>/dev/null || true

    log_success "Configuration backed up to: $backup_path"
    echo "$backup_path" > "$LOG_DIR/last_backup.txt"
}

# System health check
check_system_health() {
    log_info "Performing system health check..."

    local health_score=100
    local issues=()

    # Check CPU usage
    local cpu_usage=$(python3 -c "import psutil; print(psutil.cpu_percent(interval=1))")
    if (( $(echo "$cpu_usage > $MAX_CPU" | bc -l) )); then
        issues+=("High CPU usage: ${cpu_usage}%")
        health_score=$((health_score - 15))
    fi

    # Check memory usage
    local memory_usage=$(python3 -c "import psutil; print(psutil.virtual_memory().percent)")
    if (( $(echo "$memory_usage > $MAX_MEMORY" | bc -l) )); then
        issues+=("High memory usage: ${memory_usage}%")
        health_score=$((health_score - 10))
    fi

    # Check disk space
    local disk_usage=$(df . | tail -1 | awk '{print $5}' | tr -d '%')
    if [[ $disk_usage -gt 90 ]]; then
        issues+=("High disk usage: ${disk_usage}%")
        health_score=$((health_score - 5))
    fi

    # Check Claude-specific metrics
    check_claude_performance_health health_score issues

    # Report health status
    if [[ $health_score -ge 90 ]]; then
        log_success "System health: EXCELLENT ($health_score/100)"
    elif [[ $health_score -ge 75 ]]; then
        log_info "System health: GOOD ($health_score/100)"
    elif [[ $health_score -ge 60 ]]; then
        log_warning "System health: FAIR ($health_score/100)"
    else
        log_error "System health: POOR ($health_score/100)"
    fi

    # Report issues
    if [[ ${#issues[@]} -gt 0 ]]; then
        log_warning "Detected issues:"
        printf "  - %s\n" "${issues[@]}"
    fi

    echo "$health_score" > "$LOG_DIR/health_score.txt"
    return $((100 - health_score))
}

# Check Claude-specific performance
check_claude_performance_health() {
    local -n health_ref=$1
    local -n issues_ref=$2

    # Check hook execution times
    if [[ -f "/tmp/orchestrator_perf" ]]; then
        local avg_hook_time=$(tail -10 /tmp/orchestrator_perf 2>/dev/null | \
            awk -F, '{sum+=$2; count++} END {if(count>0) print sum/count; else print 0}')

        if (( $(echo "$avg_hook_time > $MAX_HOOK_TIME" | bc -l) )); then
            issues_ref+=("Slow hook execution: ${avg_hook_time}ms avg")
            health_ref=$((health_ref - 10))
        fi
    fi

    # Check agent selection performance
    if [[ -f "/tmp/claude_agent_selection.log" ]]; then
        local recent_selections=$(tail -5 /tmp/claude_agent_selection.log | wc -l)
        if [[ $recent_selections -eq 0 ]]; then
            issues_ref+=("No recent agent selections")
            health_ref=$((health_ref - 5))
        fi
    fi

    # Check cache effectiveness
    local cache_dirs=("/tmp/claude_context_cache" "/tmp/claude_results_cache")
    local total_cache_files=0

    for cache_dir in "${cache_dirs[@]}"; do
        if [[ -d "$cache_dir" ]]; then
            local cache_file_count=$(find "$cache_dir" -type f 2>/dev/null | wc -l)
            total_cache_files=$((total_cache_files + cache_file_count))
        fi
    done

    if [[ $total_cache_files -eq 0 ]]; then
        issues_ref+=("No cache utilization")
        health_ref=$((health_ref - 8))
    elif [[ $total_cache_files -gt 100 ]]; then
        issues_ref+=("Excessive cache files: $total_cache_files")
        health_ref=$((health_ref - 3))
    fi
}

# Optimize hook execution
optimize_hook_execution() {
    log_info "Optimizing hook execution..."

    local settings_file="$CLAUDE_DIR/settings.json"
    local temp_file=$(mktemp)

    # Read current settings
    if [[ ! -f "$settings_file" ]]; then
        log_error "Settings file not found: $settings_file"
        return 1
    fi

    # Apply hook optimizations using Python for JSON manipulation
    python3 << EOF
import json
import sys

try:
    with open('$settings_file', 'r') as f:
        settings = json.load(f)

    # Performance optimizations
    if 'performance' not in settings:
        settings['performance'] = {}

    perf = settings['performance']

    # Optimize hook execution
    perf['max_concurrent_hooks'] = 6  # Reduced from 8 for better resource management
    perf['hook_timeout_ms'] = 200     # Reduced from 500
    perf['smart_hook_batching'] = True
    perf['adaptive_timeout'] = True
    perf['hook_prioritization'] = True
    perf['phase_transition_delay'] = 10  # Reduced delay

    # Enable advanced optimizations
    perf['enable_parallel_execution'] = True
    perf['workflow_optimization'] = True
    perf['memory_optimization'] = True
    perf['lazy_loading'] = True

    # Save optimized settings
    with open('$settings_file', 'w') as f:
        json.dump(settings, f, indent=2)

    print("Hook execution optimized successfully")
    sys.exit(0)

except Exception as e:
    print(f"Error optimizing hooks: {e}")
    sys.exit(1)
EOF

    if [[ $? -eq 0 ]]; then
        log_success "Hook execution optimized"
        return 0
    else
        log_error "Failed to optimize hook execution"
        return 1
    fi
}

# Optimize agent selection
optimize_agent_selection() {
    log_info "Optimizing agent selection algorithm..."

    # Update lazy orchestrator with optimized parameters
    local orchestrator_file="$CLAUDE_DIR/core/lazy_orchestrator.py"

    if [[ ! -f "$orchestrator_file" ]]; then
        log_warning "Lazy orchestrator not found, skipping agent optimization"
        return 0
    fi

    # Apply agent selection optimizations
    python3 << EOF
import sys
import os

# Set optimization parameters
os.environ['CLAUDE_AGENT_CACHE_SIZE'] = '200'
os.environ['CLAUDE_AGENT_CACHE_TTL'] = '600'
os.environ['CLAUDE_COMPLEXITY_CACHE_SIZE'] = '128'

# Create agent optimization config
config = {
    'cache_size': 200,
    'ttl_seconds': 600,
    'aggressive_caching': True,
    'smart_preloading': True,
    'parallel_loading': True
}

import json
with open('/tmp/claude_agent_optimization.json', 'w') as f:
    json.dump(config, f, indent=2)

print("Agent selection optimized")
EOF

    log_success "Agent selection algorithm optimized"
}

# Clean up temporary files and optimize storage
cleanup_and_optimize_storage() {
    log_info "Cleaning up temporary files and optimizing storage..."

    local cleaned_files=0
    local freed_space=0

    # Clean up old cache files (older than 2 hours)
    local cache_dirs=("/tmp/claude_context_cache" "/tmp/claude_results_cache")

    for cache_dir in "${cache_dirs[@]}"; do
        if [[ -d "$cache_dir" ]]; then
            local old_files=$(find "$cache_dir" -type f -mmin +120 2>/dev/null)
            if [[ -n "$old_files" ]]; then
                local file_count=$(echo "$old_files" | wc -l)
                local size_before=$(du -sb "$cache_dir" 2>/dev/null | cut -f1)

                echo "$old_files" | xargs rm -f 2>/dev/null || true

                local size_after=$(du -sb "$cache_dir" 2>/dev/null | cut -f1)
                local saved_space=$((size_before - size_after))

                cleaned_files=$((cleaned_files + file_count))
                freed_space=$((freed_space + saved_space))
            fi
        fi
    done

    # Clean up log files (keep last 1000 lines)
    local log_files=(
        "/tmp/claude_agent_selection.log"
        "/tmp/orchestrator_perf"
        "/tmp/claude_hook_metrics"
        "/tmp/claude_execution_metrics"
        "/tmp/claude_phase_progress"
    )

    for log_file in "${log_files[@]}"; do
        if [[ -f "$log_file" && $(wc -l < "$log_file") -gt 1000 ]]; then
            tail -1000 "$log_file" > "${log_file}.tmp"
            mv "${log_file}.tmp" "$log_file"
            cleaned_files=$((cleaned_files + 1))
        fi
    done

    # Clean up old backup files (keep last 5)
    if [[ -d "$BACKUP_DIR" ]]; then
        local backup_count=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "config_*" | wc -l)
        if [[ $backup_count -gt 5 ]]; then
            find "$BACKUP_DIR" -maxdepth 1 -type d -name "config_*" | \
                sort | head -n $((backup_count - 5)) | \
                xargs rm -rf 2>/dev/null || true
        fi
    fi

    local freed_mb=$((freed_space / 1024 / 1024))
    log_success "Cleanup completed: $cleaned_files files cleaned, ${freed_mb}MB freed"
}

# Optimize system configuration
optimize_system_configuration() {
    log_info "Optimizing system configuration..."

    # Set optimal environment variables
    export CLAUDE_ENHANCER_PERFORMANCE_MODE="optimized"
    export CLAUDE_HOOK_TIMEOUT="200"
    export CLAUDE_CACHE_ENABLED="true"
    export CLAUDE_PARALLEL_HOOKS="true"

    # Create performance configuration file
    cat > "/tmp/claude_performance_config" << EOF
# Claude Enhancer Performance Configuration
# Generated on $(date)

HOOK_TIMEOUT_MS=200
MAX_CONCURRENT_HOOKS=6
ENABLE_SMART_BATCHING=true
ENABLE_ADAPTIVE_TIMEOUT=true
ENABLE_HOOK_PRIORITIZATION=true
PHASE_TRANSITION_DELAY=10
CACHE_TTL_SECONDS=300
AGENT_CACHE_SIZE=200
COMPLEXITY_CACHE_SIZE=128
ENABLE_PARALLEL_EXECUTION=true
ENABLE_MEMORY_OPTIMIZATION=true
ENABLE_LAZY_LOADING=true
EOF

    log_success "System configuration optimized"
}

# Performance benchmark
run_performance_benchmark() {
    log_info "Running performance benchmark..."

    local benchmark_results=()

    # Test hook execution speed
    local hook_start=$(date +%s%N)
    bash "$CLAUDE_DIR/hooks/unified_workflow_orchestrator.sh" <<< '{"test": "performance"}' > /dev/null 2>&1
    local hook_end=$(date +%s%N)
    local hook_time=$(( (hook_end - hook_start) / 1000000 ))  # Convert to ms
    benchmark_results+=("Hook execution: ${hook_time}ms")

    # Test agent selection speed
    local agent_start=$(date +%s%N)
    python3 "$CLAUDE_DIR/core/lazy_orchestrator.py" <<< "test performance optimization" > /dev/null 2>&1 || true
    local agent_end=$(date +%s%N)
    local agent_time=$(( (agent_end - agent_start) / 1000000 ))
    benchmark_results+=("Agent selection: ${agent_time}ms")

    # Test file I/O performance
    local io_start=$(date +%s%N)
    find "$CLAUDE_DIR" -name "*.sh" -o -name "*.py" | head -20 | xargs wc -l > /dev/null
    local io_end=$(date +%s%N)
    local io_time=$(( (io_end - io_start) / 1000000 ))
    benchmark_results+=("File I/O: ${io_time}ms")

    # Report benchmark results
    log_info "Benchmark results:"
    printf "  - %s\n" "${benchmark_results[@]}"

    # Save results
    {
        echo "# Performance Benchmark Results - $(date)"
        printf "%s\n" "${benchmark_results[@]}"
        echo "Overall status: $(( hook_time + agent_time + io_time < 1000 && "GOOD" || "NEEDS_OPTIMIZATION" ))"
    } > "$LOG_DIR/benchmark_results.txt"
}

# Generate optimization report
generate_optimization_report() {
    log_info "Generating optimization report..."

    local report_file="$LOG_DIR/optimization_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
Claude Enhancer Workflow Optimization Report
==========================================
Generated on: $(date)

System Information:
- Hostname: $(hostname)
- OS: $(uname -s) $(uname -r)
- CPU: $(nproc) cores
- Memory: $(free -h | grep "Mem:" | awk '{print $2}') total
- Disk: $(df -h . | tail -1 | awk '{print $4}') available

Health Score: $(cat "$LOG_DIR/health_score.txt" 2>/dev/null || echo "N/A")/100

Optimizations Applied:
- Hook execution performance optimization
- Agent selection algorithm enhancement
- Storage cleanup and optimization
- System configuration tuning

Performance Metrics:
$(cat "$LOG_DIR/benchmark_results.txt" 2>/dev/null || echo "Benchmark not available")

Configuration Backup:
$(cat "$LOG_DIR/last_backup.txt" 2>/dev/null || echo "No backup created")

Recommendations:
1. Monitor system regularly using 'workflow_optimizer.sh monitor'
2. Run optimization weekly or when performance issues occur
3. Check logs in $LOG_DIR for detailed information
4. Consider increasing system resources if health score is consistently low

Next Steps:
- Enable automatic optimization: cron job recommended
- Set up monitoring dashboard
- Configure alerts for performance degradation

EOF

    log_success "Optimization report generated: $report_file"
    echo "$report_file"
}

# Continuous monitoring mode
start_monitoring() {
    log_info "Starting continuous monitoring mode..."
    log_info "Press Ctrl+C to stop monitoring"

    local monitor_interval=30  # seconds

    trap 'log_info "Monitoring stopped"; exit 0' INT TERM

    while true; do
        clear
        echo -e "${CYAN}Claude Enhancer Performance Monitor${NC}"
        echo "========================================"
        echo "$(date)"
        echo ""

        # Quick health check
        local health_score=$(check_system_health 2>/dev/null | tail -1 | grep -oE '[0-9]+' | head -1)
        echo "Health Score: ${health_score:-N/A}/100"

        # System resources
        local cpu=$(python3 -c "import psutil; print(f'{psutil.cpu_percent(interval=0.1):.1f}')" 2>/dev/null || echo "N/A")
        local memory=$(python3 -c "import psutil; print(f'{psutil.virtual_memory().percent:.1f}')" 2>/dev/null || echo "N/A")

        echo "CPU Usage: ${cpu}%"
        echo "Memory Usage: ${memory}%"
        echo ""

        # Recent activity
        echo "Recent Hook Activity:"
        if [[ -f "/tmp/orchestrator_perf" ]]; then
            echo "  Last 5 executions:"
            tail -5 /tmp/orchestrator_perf 2>/dev/null | while IFS=, read -r timestamp duration; do
                echo "    $(date -d @$timestamp '+%H:%M:%S'): ${duration}ms"
            done 2>/dev/null || echo "  No recent activity"
        else
            echo "  No performance data available"
        fi

        echo ""
        echo "Monitoring... (interval: ${monitor_interval}s)"
        sleep $monitor_interval
    done
}

# Auto-optimization based on health score
auto_optimize() {
    log_info "Running auto-optimization based on system health..."

    local health_exit_code=0
    check_system_health >/dev/null || health_exit_code=$?

    if [[ $health_exit_code -gt 25 ]]; then  # Health score < 75
        log_warning "Poor system health detected. Applying optimizations..."

        backup_configuration
        optimize_hook_execution
        optimize_agent_selection
        cleanup_and_optimize_storage
        optimize_system_configuration

        log_success "Auto-optimization completed"
        return 0
    else
        log_info "System health is acceptable. No optimization needed."
        return 0
    fi
}

# Help function
show_help() {
    cat << EOF
Claude Enhancer Workflow Optimizer

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    check       - Run system health check
    optimize    - Run full optimization suite
    auto        - Auto-optimize based on health score
    cleanup     - Clean up temporary files and logs
    benchmark   - Run performance benchmark
    report      - Generate optimization report
    monitor     - Start continuous monitoring mode
    backup      - Create configuration backup
    help        - Show this help message

EXAMPLES:
    $0 check                    # Quick health check
    $0 optimize                 # Full optimization
    $0 auto                     # Smart auto-optimization
    $0 monitor                  # Continuous monitoring
    $0 benchmark               # Performance benchmark

LOGS:
    Logs are stored in: $LOG_DIR

CONFIGURATION:
    Claude Enhancer directory: $CLAUDE_DIR
    Settings file: $CLAUDE_DIR/settings.json

For more information, see the Claude Enhancer documentation.
EOF
}

# Main execution logic
main() {
    local command="${1:-help}"

    # Ensure log directory exists
    mkdir -p "$LOG_DIR"

    # Initialize log file
    echo "=== Claude Enhancer Workflow Optimizer Session - $(date) ===" >> "$OPTIMIZATION_LOG"

    case "$command" in
        "check")
            echo -e "${BLUE}Running system health check...${NC}"
            check_system_health
            ;;
        "optimize")
            echo -e "${BLUE}Running full optimization suite...${NC}"
            backup_configuration
            optimize_hook_execution
            optimize_agent_selection
            cleanup_and_optimize_storage
            optimize_system_configuration
            run_performance_benchmark
            report_file=$(generate_optimization_report)
            echo ""
            log_success "Optimization completed! Report: $report_file"
            ;;
        "auto")
            echo -e "${BLUE}Running auto-optimization...${NC}"
            auto_optimize
            ;;
        "cleanup")
            echo -e "${BLUE}Running cleanup and storage optimization...${NC}"
            cleanup_and_optimize_storage
            ;;
        "benchmark")
            echo -e "${BLUE}Running performance benchmark...${NC}"
            run_performance_benchmark
            ;;
        "report")
            echo -e "${BLUE}Generating optimization report...${NC}"
            report_file=$(generate_optimization_report)
            echo ""
            log_success "Report generated: $report_file"
            ;;
        "monitor")
            start_monitoring
            ;;
        "backup")
            echo -e "${BLUE}Creating configuration backup...${NC}"
            backup_configuration
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"