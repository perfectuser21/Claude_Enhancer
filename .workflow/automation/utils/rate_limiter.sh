#!/usr/bin/env bash
# Rate Limiter for Claude Enhancer v5.4.0
# Purpose: Prevent automation abuse through configurable rate limiting
# Method: Token bucket algorithm with file-based semaphore
# Usage: Source this file and call check_rate_limit before operations

set -euo pipefail

# Configuration
RATE_LIMIT_DIR="${CE_RATE_LIMIT_DIR:-/tmp/claude-enhancer/rate-limits}"
DEFAULT_MAX_OPERATIONS=10
DEFAULT_TIME_WINDOW=60  # seconds

# ============================================================
# INITIALIZATION
# ============================================================

init_rate_limiter() {
    # Create rate limit directory
    if [[ ! -d "$RATE_LIMIT_DIR" ]]; then
        mkdir -p "$RATE_LIMIT_DIR" 2>/dev/null || {
            RATE_LIMIT_DIR="/tmp/ce-rate-limits"
            mkdir -p "$RATE_LIMIT_DIR"
        }
        chmod 750 "$RATE_LIMIT_DIR"
    fi
}

# ============================================================
# TOKEN BUCKET IMPLEMENTATION
# ============================================================

# Check rate limit for an operation
# Args: $1 = operation_name, $2 = max_ops (optional), $3 = time_window_seconds (optional)
# Returns: 0 if allowed, 1 if rate limit exceeded
check_rate_limit() {
    local operation="$1"
    local max_ops="${2:-$DEFAULT_MAX_OPERATIONS}"
    local time_window="${3:-$DEFAULT_TIME_WINDOW}"

    init_rate_limiter

    local bucket_file="${RATE_LIMIT_DIR}/${operation}.bucket"
    local lock_file="${bucket_file}.lock"

    # Acquire lock (simple file-based lock with timeout)
    local lock_timeout=5
    local lock_attempts=0

    while [[ -f "$lock_file" ]] && [[ $lock_attempts -lt $lock_timeout ]]; do
        sleep 0.1
        lock_attempts=$((lock_attempts + 1))
    done

    # Create lock
    echo $$ > "$lock_file"

    # Read current bucket state
    local current_time=$(date +%s)
    local bucket_tokens=0
    local last_refill=0

    if [[ -f "$bucket_file" ]]; then
        IFS=':' read -r bucket_tokens last_refill < "$bucket_file"
    else
        # Initialize bucket (full)
        bucket_tokens=$max_ops
        last_refill=$current_time
    fi

    # Refill bucket based on time elapsed
    local time_elapsed=$((current_time - last_refill))
    if [[ $time_elapsed -gt 0 ]]; then
        # Refill rate: max_ops per time_window
        local refill_amount=$(( (time_elapsed * max_ops) / time_window ))

        bucket_tokens=$((bucket_tokens + refill_amount))

        # Cap at max
        if [[ $bucket_tokens -gt $max_ops ]]; then
            bucket_tokens=$max_ops
        fi

        last_refill=$current_time
    fi

    # Check if we can consume a token
    if [[ $bucket_tokens -gt 0 ]]; then
        # Consume token
        bucket_tokens=$((bucket_tokens - 1))

        # Save bucket state
        echo "${bucket_tokens}:${last_refill}" > "$bucket_file"

        # Release lock
        rm -f "$lock_file"

        return 0  # Allowed
    else
        # Rate limit exceeded
        # Calculate wait time
        local wait_time=$(( time_window / max_ops ))

        # Save bucket state
        echo "${bucket_tokens}:${last_refill}" > "$bucket_file"

        # Release lock
        rm -f "$lock_file"

        # Export wait time for caller
        export CE_RATE_LIMIT_WAIT=$wait_time

        return 1  # Rate limit exceeded
    fi
}

# Get current rate limit status
# Args: $1 = operation_name
# Returns: Available tokens count
get_rate_limit_status() {
    local operation="$1"

    init_rate_limiter

    local bucket_file="${RATE_LIMIT_DIR}/${operation}.bucket"

    if [[ -f "$bucket_file" ]]; then
        local bucket_tokens=0
        local last_refill=0

        IFS=':' read -r bucket_tokens last_refill < "$bucket_file"

        echo "$bucket_tokens"
    else
        echo "$DEFAULT_MAX_OPERATIONS"
    fi
}

# Reset rate limit for an operation
# Args: $1 = operation_name
reset_rate_limit() {
    local operation="$1"

    init_rate_limiter

    local bucket_file="${RATE_LIMIT_DIR}/${operation}.bucket"

    if [[ -f "$bucket_file" ]]; then
        rm -f "$bucket_file"
        return 0
    fi

    return 1
}

# Clean up old rate limit files (older than 24 hours)
cleanup_rate_limits() {
    init_rate_limiter

    find "$RATE_LIMIT_DIR" -type f -mtime +1 -delete 2>/dev/null || true
}

# ============================================================
# OPERATION-SPECIFIC RATE LIMITS
# ============================================================

# Rate limit for git operations
check_git_rate_limit() {
    local operation="${1:-git_operation}"
    local max_ops="${CE_GIT_MAX_OPS:-20}"
    local time_window="${CE_GIT_TIME_WINDOW:-60}"

    check_rate_limit "git_${operation}" "$max_ops" "$time_window"
}

# Rate limit for API calls
check_api_rate_limit() {
    local api_name="${1:-github_api}"
    local max_ops="${CE_API_MAX_OPS:-60}"
    local time_window="${CE_API_TIME_WINDOW:-60}"

    check_rate_limit "api_${api_name}" "$max_ops" "$time_window"
}

# Rate limit for automation operations
check_automation_rate_limit() {
    local automation_type="${1:-auto_commit}"
    local max_ops="${CE_AUTO_MAX_OPS:-10}"
    local time_window="${CE_AUTO_TIME_WINDOW:-60}"

    check_rate_limit "automation_${automation_type}" "$max_ops" "$time_window"
}

# Rate limit for owner operations monitoring
check_owner_ops_rate_limit() {
    local max_ops="${CE_OWNER_OPS_MAX:-5}"
    local time_window="${CE_OWNER_OPS_WINDOW:-300}"  # 5 minutes

    check_rate_limit "owner_operations" "$max_ops" "$time_window"
}

# ============================================================
# LOGGING & AUDIT
# ============================================================

log_rate_limit_exceeded() {
    local operation="$1"
    local wait_time="${CE_RATE_LIMIT_WAIT:-0}"

    if command -v log_warning &>/dev/null; then
        log_warning "Rate limit exceeded for: $operation"
        log_warning "Please wait ${wait_time}s before retrying"
    else
        echo "⚠ Rate limit exceeded for: $operation" >&2
        echo "⚠ Please wait ${wait_time}s before retrying" >&2
    fi

    # Audit rate limit violation if audit_log.sh is available
    if command -v audit_security_event &>/dev/null; then
        audit_security_event "rate_limit_exceeded" "MEDIUM" "Operation: $operation, Wait: ${wait_time}s"
    fi
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

# Wait for rate limit to allow operation (blocking)
# Args: $1 = operation_name, $2 = max_attempts (default: 3)
wait_for_rate_limit() {
    local operation="$1"
    local max_attempts="${2:-3}"
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if check_rate_limit "$operation"; then
            return 0  # Allowed
        fi

        # Rate limit exceeded, wait and retry
        local wait_time="${CE_RATE_LIMIT_WAIT:-5}"

        if [[ $attempt -eq 0 ]]; then
            log_rate_limit_exceeded "$operation"
        fi

        sleep "$wait_time"
        attempt=$((attempt + 1))
    done

    # Max attempts exceeded
    if command -v log_error &>/dev/null; then
        log_error "Rate limit exceeded after $max_attempts attempts: $operation"
    else
        echo "✗ Rate limit exceeded after $max_attempts attempts: $operation" >&2
    fi

    return 1
}

# Get rate limit statistics
get_rate_limit_stats() {
    init_rate_limiter

    echo "Rate Limit Statistics:"
    echo "======================"

    local total_operations=0
    local active_limits=0

    for bucket_file in "${RATE_LIMIT_DIR}"/*.bucket; do
        if [[ -f "$bucket_file" ]]; then
            local operation=$(basename "$bucket_file" .bucket)
            local tokens=0
            local last_refill=0

            IFS=':' read -r tokens last_refill < "$bucket_file"

            local age=$(($(date +%s) - last_refill))

            echo "  $operation:"
            echo "    Available tokens: $tokens"
            echo "    Last refill: ${age}s ago"

            active_limits=$((active_limits + 1))
            total_operations=$((total_operations + 1))
        fi
    done

    if [[ $active_limits -eq 0 ]]; then
        echo "  No active rate limits"
    fi

    echo ""
    echo "Total operations tracked: $total_operations"
}

# ============================================================
# CONFIGURATION PRESETS
# ============================================================

# Development mode (relaxed limits)
enable_dev_mode() {
    export CE_GIT_MAX_OPS=50
    export CE_GIT_TIME_WINDOW=60
    export CE_API_MAX_OPS=100
    export CE_API_TIME_WINDOW=60
    export CE_AUTO_MAX_OPS=30
    export CE_AUTO_TIME_WINDOW=60

    if command -v log_info &>/dev/null; then
        log_info "Rate limiter: Development mode enabled (relaxed limits)"
    fi
}

# Production mode (strict limits)
enable_prod_mode() {
    export CE_GIT_MAX_OPS=10
    export CE_GIT_TIME_WINDOW=60
    export CE_API_MAX_OPS=30
    export CE_API_TIME_WINDOW=60
    export CE_AUTO_MAX_OPS=5
    export CE_AUTO_TIME_WINDOW=60

    if command -v log_info &>/dev/null; then
        log_info "Rate limiter: Production mode enabled (strict limits)"
    fi
}

# CI/CD mode (moderate limits)
enable_ci_mode() {
    export CE_GIT_MAX_OPS=20
    export CE_GIT_TIME_WINDOW=60
    export CE_API_MAX_OPS=60
    export CE_API_TIME_WINDOW=60
    export CE_AUTO_MAX_OPS=15
    export CE_AUTO_TIME_WINDOW=60

    if command -v log_info &>/dev/null; then
        log_info "Rate limiter: CI/CD mode enabled (moderate limits)"
    fi
}

# ============================================================
# MAIN (for testing/CLI)
# ============================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Direct execution - CLI mode

    case "${1:-help}" in
        check)
            if check_rate_limit "${2:-test_operation}" "${3:-10}" "${4:-60}"; then
                echo "✓ Operation allowed"
                exit 0
            else
                echo "✗ Rate limit exceeded (wait: ${CE_RATE_LIMIT_WAIT}s)"
                exit 1
            fi
            ;;

        status)
            get_rate_limit_stats
            ;;

        reset)
            if [[ -n "${2:-}" ]]; then
                reset_rate_limit "$2"
                echo "✓ Rate limit reset for: $2"
            else
                rm -rf "$RATE_LIMIT_DIR"
                mkdir -p "$RATE_LIMIT_DIR"
                echo "✓ All rate limits reset"
            fi
            ;;

        cleanup)
            cleanup_rate_limits
            echo "✓ Old rate limit files cleaned up"
            ;;

        help|*)
            cat <<HELP
Rate Limiter - Claude Enhancer v5.4.0

Usage:
  source rate_limiter.sh        # Source for library use
  ./rate_limiter.sh <command>   # Direct CLI execution

Commands:
  check <operation> [max_ops] [time_window]
      Check if operation is rate-limited
      Example: ./rate_limiter.sh check git_push 10 60

  status
      Show current rate limit statistics

  reset [operation]
      Reset rate limit for operation (or all if omitted)

  cleanup
      Remove old rate limit files (>24 hours)

Library Functions:
  check_rate_limit <operation> [max_ops] [time_window]
      Returns 0 if allowed, 1 if rate limited

  check_git_rate_limit <operation>
      Specialized for git operations

  check_api_rate_limit <api_name>
      Specialized for API calls

  check_automation_rate_limit <type>
      Specialized for automation operations

  wait_for_rate_limit <operation> [max_attempts]
      Block until rate limit allows operation

Environment Variables:
  CE_GIT_MAX_OPS         Max git operations per window (default: 20)
  CE_GIT_TIME_WINDOW     Git rate limit window in seconds (default: 60)
  CE_API_MAX_OPS         Max API calls per window (default: 60)
  CE_API_TIME_WINDOW     API rate limit window in seconds (default: 60)
  CE_AUTO_MAX_OPS        Max automation ops per window (default: 10)
  CE_AUTO_TIME_WINDOW    Automation rate limit window (default: 60)

Configuration Modes:
  enable_dev_mode        Relaxed limits for development
  enable_prod_mode       Strict limits for production
  enable_ci_mode         Moderate limits for CI/CD

Example Usage in Scripts:
  source .workflow/automation/utils/rate_limiter.sh

  if check_git_rate_limit "commit"; then
      git commit -m "message"
  else
      log_rate_limit_exceeded "git_commit"
      exit 1
  fi

Algorithm: Token Bucket
  - Tokens refill over time at constant rate
  - Each operation consumes 1 token
  - If no tokens available, operation is rate-limited
  - Thread-safe with file-based locking

Benefits:
  ✓ Prevents automation abuse
  ✓ Protects external APIs from overuse
  ✓ Mitigates DoS risks
  ✓ Enforces fair resource usage
HELP
            ;;
    esac
fi
