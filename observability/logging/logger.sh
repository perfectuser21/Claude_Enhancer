#!/usr/bin/env bash
# logger.sh - Structured logging system for Claude Enhancer
# Provides leveled logging with JSON/text output and log rotation
set -euo pipefail

# Logging configuration
CE_LOG_DIR="${CE_LOG_DIR:-.workflow/observability/logs}"
CE_LOG_LEVEL="${CE_LOG_LEVEL:-INFO}"  # DEBUG, INFO, WARN, ERROR, CRITICAL
CE_LOG_FORMAT="${CE_LOG_FORMAT:-json}"  # json or text
CE_LOG_ROTATION="${CE_LOG_ROTATION:-daily}"  # daily, size
CE_LOG_RETENTION="${CE_LOG_RETENTION:-7}"  # days
CE_LOG_MAX_SIZE="${CE_LOG_MAX_SIZE:-10485760}"  # 10MB in bytes

# Log level priorities
declare -A CE_LOG_LEVELS=(
    [DEBUG]=0
    [INFO]=1
    [WARN]=2
    [ERROR]=3
    [CRITICAL]=4
    [FATAL]=5
)

# ANSI color codes for text output
declare -A CE_LOG_COLORS=(
    [DEBUG]="\033[0;36m"     # Cyan
    [INFO]="\033[0;32m"      # Green
    [WARN]="\033[0;33m"      # Yellow
    [ERROR]="\033[0;31m"     # Red
    [CRITICAL]="\033[1;31m"  # Bold Red
    [FATAL]="\033[1;35m"     # Bold Magenta
    [RESET]="\033[0m"
)

# Initialize logging system
ce_log_init() {
    mkdir -p "${CE_LOG_DIR}"/{application,errors,audit,performance}

    # Create log metadata
    cat > "${CE_LOG_DIR}/.metadata" <<EOF
{
  "initialized_at": "$(date -Iseconds)",
  "log_level": "${CE_LOG_LEVEL}",
  "log_format": "${CE_LOG_FORMAT}",
  "retention_days": ${CE_LOG_RETENTION}
}
EOF

    # Initialize log files
    touch "${CE_LOG_DIR}/application/app.log"
    touch "${CE_LOG_DIR}/errors/errors.log"
    touch "${CE_LOG_DIR}/audit/audit.log"
    touch "${CE_LOG_DIR}/performance/perf.log"
}

# Get current log file based on rotation policy
ce_log_get_current_file() {
    local log_type="${1:-application}"  # application, errors, audit, performance
    local log_file="${CE_LOG_DIR}/${log_type}"

    if [[ "${CE_LOG_ROTATION}" == "daily" ]]; then
        log_file="${log_file}/$(date +%Y-%m-%d).log"
    else
        log_file="${log_file}/${log_type}.log"
    fi

    echo "$log_file"
}

# Check if log level should be logged
ce_log_should_log() {
    local level="$1"
    local current_priority="${CE_LOG_LEVELS[$CE_LOG_LEVEL]:-1}"
    local message_priority="${CE_LOG_LEVELS[$level]:-0}"

    [[ $message_priority -ge $current_priority ]]
}

# Core logging function
ce_log() {
    local level="${1^^}"  # Convert to uppercase
    local message="$2"
    local context="${3:-}"

    # Check if we should log this level
    if ! ce_log_should_log "$level"; then
        return 0
    fi

    local timestamp
    timestamp=$(date -Iseconds)

    local terminal_id="${CE_TERMINAL_ID:-unknown}"
    local phase="${CE_CURRENT_PHASE:-unknown}"
    local command="${CE_CURRENT_COMMAND:-unknown}"
    local branch
    branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "unknown")

    # Determine log file
    local log_file
    if [[ "$level" =~ ^(ERROR|CRITICAL|FATAL)$ ]]; then
        log_file=$(ce_log_get_current_file "errors")
    else
        log_file=$(ce_log_get_current_file "application")
    fi

    mkdir -p "$(dirname "$log_file")"

    # Format and write log entry
    if [[ "${CE_LOG_FORMAT}" == "json" ]]; then
        # JSON format
        local log_entry
        log_entry=$(cat <<EOF
{
  "timestamp": "${timestamp}",
  "level": "${level}",
  "message": ${message@Q},
  "terminal_id": "${terminal_id}",
  "phase": "${phase}",
  "command": "${command}",
  "branch": "${branch}",
  "pid": $$,
  "user": "${USER}",
  "context": ${context:-null}
}
EOF
)
        echo "$log_entry" >> "$log_file"
    else
        # Text format with colors (if terminal supports it)
        local color="${CE_LOG_COLORS[$level]:-}"
        local reset="${CE_LOG_COLORS[RESET]}"

        if [[ -t 1 ]]; then
            # Terminal supports colors
            echo -e "${color}${timestamp} [${level}]${reset} ${message} (terminal=${terminal_id}, phase=${phase})" | tee -a "$log_file"
        else
            # No colors
            echo "${timestamp} [${level}] ${message} (terminal=${terminal_id}, phase=${phase})" >> "$log_file"
        fi
    fi

    # Also write to audit log for important events
    if [[ "$level" =~ ^(WARN|ERROR|CRITICAL|FATAL)$ ]]; then
        local audit_file
        audit_file=$(ce_log_get_current_file "audit")
        echo "${timestamp} [${level}] ${message}" >> "$audit_file"
    fi
}

# Convenience logging functions
ce_log_debug() {
    ce_log "DEBUG" "$1" "${2:-}"
}

ce_log_info() {
    ce_log "INFO" "$1" "${2:-}"
}

ce_log_warn() {
    ce_log "WARN" "$1" "${2:-}"
}

ce_log_error() {
    ce_log "ERROR" "$1" "${2:-}"
}

ce_log_critical() {
    ce_log "CRITICAL" "$1" "${2:-}"
}

ce_log_fatal() {
    ce_log "FATAL" "$1" "${2:-}"
    exit 1
}

# Structured context logging
ce_log_with_context() {
    local level="$1"
    local message="$2"
    shift 2

    # Build context object from remaining key=value arguments
    local context="{"
    local first=true

    while [[ $# -gt 0 ]]; do
        local key="${1%%=*}"
        local value="${1#*=}"

        [[ "$first" == "true" ]] && first=false || context+=","
        context+="\"${key}\": \"${value}\""

        shift
    done

    context+="}"

    ce_log "$level" "$message" "$context"
}

# Performance logging
ce_log_performance() {
    local operation="$1"
    local duration_ms="$2"
    local status="${3:-success}"

    local perf_file
    perf_file=$(ce_log_get_current_file "performance")

    if [[ "${CE_LOG_FORMAT}" == "json" ]]; then
        cat >> "$perf_file" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "operation": "${operation}",
  "duration_ms": ${duration_ms},
  "status": "${status}",
  "terminal_id": "${CE_TERMINAL_ID:-unknown}",
  "phase": "${CE_CURRENT_PHASE:-unknown}"
}
EOF
    else
        echo "$(date -Iseconds) ${operation} ${duration_ms}ms ${status}" >> "$perf_file"
    fi
}

# Audit logging for security-relevant events
ce_log_audit() {
    local event="$1"
    local actor="${2:-${USER}}"
    local resource="${3:-}"
    local action="${4:-}"
    local result="${5:-success}"

    local audit_file
    audit_file=$(ce_log_get_current_file "audit")

    if [[ "${CE_LOG_FORMAT}" == "json" ]]; then
        cat >> "$audit_file" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "event": "${event}",
  "actor": "${actor}",
  "resource": "${resource}",
  "action": "${action}",
  "result": "${result}",
  "terminal_id": "${CE_TERMINAL_ID:-unknown}",
  "ip_address": "${SSH_CLIENT%% *}"
}
EOF
    else
        echo "$(date -Iseconds) [AUDIT] ${event} by ${actor} on ${resource}: ${result}" >> "$audit_file"
    fi
}

# Log rotation
ce_log_rotate() {
    local log_type="${1:-all}"  # application, errors, audit, performance, all

    if [[ "$log_type" == "all" ]]; then
        ce_log_rotate "application"
        ce_log_rotate "errors"
        ce_log_rotate "audit"
        ce_log_rotate "performance"
        return 0
    fi

    local log_dir="${CE_LOG_DIR}/${log_type}"
    [[ ! -d "$log_dir" ]] && return 0

    local log_file="${log_dir}/${log_type}.log"

    if [[ "${CE_LOG_ROTATION}" == "size" ]]; then
        # Rotate based on size
        if [[ -f "$log_file" ]]; then
            local file_size
            file_size=$(stat -c %s "$log_file" 2>/dev/null || stat -f %z "$log_file" 2>/dev/null || echo 0)

            if [[ $file_size -ge $CE_LOG_MAX_SIZE ]]; then
                local timestamp
                timestamp=$(date +%Y%m%d_%H%M%S)
                local archive_file="${log_file}.${timestamp}"

                mv "$log_file" "$archive_file"
                gzip "$archive_file" &

                ce_log_info "Rotated ${log_type} log: ${archive_file}.gz"
            fi
        fi
    fi

    # Daily rotation is handled automatically by filename
}

# Cleanup old logs
ce_log_cleanup() {
    local retention_seconds=$((CE_LOG_RETENTION * 86400))
    local current_time
    current_time=$(date +%s)

    find "${CE_LOG_DIR}" -name "*.log" -o -name "*.log.*.gz" | while read -r file; do
        local file_time
        file_time=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null || echo 0)
        local age=$((current_time - file_time))

        if [[ $age -gt $retention_seconds ]]; then
            rm -f "$file"
            ce_log_info "Removed old log file: $file"
        fi
    done
}

# Search logs
ce_log_search() {
    local query="$1"
    local log_type="${2:-application}"
    local max_results="${3:-100}"

    local log_dir="${CE_LOG_DIR}/${log_type}"

    if [[ "${CE_LOG_FORMAT}" == "json" ]]; then
        # Search JSON logs with jq
        find "$log_dir" -name "*.log" -type f | \
            xargs grep -h "$query" | \
            head -n "$max_results" | \
            jq -s '.'
    else
        # Search text logs
        find "$log_dir" -name "*.log" -type f | \
            xargs grep -h "$query" | \
            head -n "$max_results"
    fi
}

# Get log statistics
ce_log_stats() {
    local log_type="${1:-application}"

    local log_dir="${CE_LOG_DIR}/${log_type}"
    [[ ! -d "$log_dir" ]] && return 0

    local total_files
    local total_size
    local total_lines

    total_files=$(find "$log_dir" -name "*.log" -type f | wc -l)
    total_size=$(du -sh "$log_dir" 2>/dev/null | cut -f1)
    total_lines=$(find "$log_dir" -name "*.log" -type f -exec wc -l {} + | tail -1 | awk '{print $1}')

    # Count by level
    local debug_count info_count warn_count error_count critical_count

    debug_count=$(find "$log_dir" -name "*.log" -type f -exec grep -c "DEBUG" {} + 2>/dev/null | awk '{s+=$1} END {print s}' || echo 0)
    info_count=$(find "$log_dir" -name "*.log" -type f -exec grep -c "INFO" {} + 2>/dev/null | awk '{s+=$1} END {print s}' || echo 0)
    warn_count=$(find "$log_dir" -name "*.log" -type f -exec grep -c "WARN" {} + 2>/dev/null | awk '{s+=$1} END {print s}' || echo 0)
    error_count=$(find "$log_dir" -name "*.log" -type f -exec grep -c "ERROR" {} + 2>/dev/null | awk '{s+=$1} END {print s}' || echo 0)
    critical_count=$(find "$log_dir" -name "*.log" -type f -exec grep -c "CRITICAL" {} + 2>/dev/null | awk '{s+=$1} END {print s}' || echo 0)

    cat <<EOF
{
  "log_type": "${log_type}",
  "total_files": ${total_files},
  "total_size": "${total_size}",
  "total_lines": ${total_lines},
  "counts_by_level": {
    "DEBUG": ${debug_count},
    "INFO": ${info_count},
    "WARN": ${warn_count},
    "ERROR": ${error_count},
    "CRITICAL": ${critical_count}
  }
}
EOF
}

# Tail logs in real-time
ce_log_tail() {
    local log_type="${1:-application}"
    local lines="${2:-50}"

    local log_file
    log_file=$(ce_log_get_current_file "$log_type")

    if [[ -f "$log_file" ]]; then
        tail -f -n "$lines" "$log_file"
    else
        echo "Log file not found: $log_file"
        return 1
    fi
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ce_log_init

    case "${1:-help}" in
        init)
            ce_log_init
            ;;
        rotate)
            ce_log_rotate "${2:-all}"
            ;;
        cleanup)
            ce_log_cleanup
            ;;
        search)
            ce_log_search "${2:-}" "${3:-application}" "${4:-100}"
            ;;
        stats)
            ce_log_stats "${2:-application}"
            ;;
        tail)
            ce_log_tail "${2:-application}" "${3:-50}"
            ;;
        *)
            cat <<EOF
Usage: $0 {init|rotate|cleanup|search|stats|tail}

Commands:
  init                  Initialize logging system
  rotate [type]         Rotate logs (application, errors, audit, performance, all)
  cleanup               Remove old logs based on retention policy
  search <query> [type] [limit]  Search logs
  stats [type]          Get log statistics
  tail [type] [lines]   Tail logs in real-time

Examples:
  $0 search "ERROR" errors 20
  $0 stats application
  $0 tail performance 100
EOF
            ;;
    esac
fi

# Export functions
export -f ce_log_init
export -f ce_log
export -f ce_log_debug
export -f ce_log_info
export -f ce_log_warn
export -f ce_log_error
export -f ce_log_critical
export -f ce_log_fatal
export -f ce_log_with_context
export -f ce_log_performance
export -f ce_log_audit
export -f ce_log_rotate
export -f ce_log_cleanup
export -f ce_log_search
export -f ce_log_stats
export -f ce_log_tail
