#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Unified Branch Protector
# Claude Enhancer v7.3.0 - Single source of truth for branch protection
# ═══════════════════════════════════════════════════════════════
# Purpose: Consolidate all branch checking into one optimized hook
# Replaces: Multiple redundant branch checks across various hooks
# Performance: Uses caching to avoid duplicate git operations
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# Load common library with caching support
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=.claude/hooks/lib/branch_common.sh
source "${SCRIPT_DIR}/lib/branch_common.sh"

# Load performance monitor if available
if [[ -f "${SCRIPT_DIR}/../core/performance_monitor.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SCRIPT_DIR}/../core/performance_monitor.sh"
    PERF_MONITORING=true
else
    PERF_MONITORING=false
fi

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

readonly HOOK_NAME="unified_branch_protector"
readonly HOOK_VERSION="1.0.0"
readonly PROTECTION_MODE="${CE_BRANCH_PROTECTION_MODE:-strict}"
readonly CACHE_KEY="branch-protection-check"
readonly CACHE_TTL=60  # Cache for 1 minute

# ═══════════════════════════════════════════════════════════════
# Main Protection Logic
# ═══════════════════════════════════════════════════════════════

# Function: Perform unified branch protection check
perform_branch_check() {
    local context="${1:-default}"
    local operation="${2:-write}"

    # Start performance timer if enabled
    [[ "$PERF_MONITORING" == "true" ]] && start_timer "branch_check" "$context"

    # Check if in git repository (with caching)
    if ! is_git_repo; then
        [[ "${CE_SILENT_MODE:-false}" != "true" ]] && echo "ℹ️  Not in a git repository, skipping branch check" >&2
        [[ "$PERF_MONITORING" == "true" ]] && end_timer "branch_check" "$context" "skip"
        return 0
    fi

    # Get current branch (with caching)
    local current_branch
    current_branch=$(get_current_branch)

    # Log the check
    log_hook_event "$HOOK_NAME" "Checking branch: $current_branch (context: $context, operation: $operation)"

    # Check if branch is protected
    if is_protected_branch "$current_branch"; then
        # Branch is protected - handle based on mode and options

        # Check if auto-create is enabled
        if is_auto_create_enabled; then
            if auto_create_branch "$current_branch"; then
                log_hook_event "$HOOK_NAME" "Auto-created branch from $current_branch"
                [[ "$PERF_MONITORING" == "true" ]] && end_timer "branch_check" "$context" "auto-created"
                return 0
            fi
        fi

        # Check protection mode
        case "$PROTECTION_MODE" in
            strict)
                # Strict mode - always block
                show_protected_branch_error "$current_branch"
                log_hook_event "$HOOK_NAME" "BLOCKED: Operation on $current_branch (strict mode)"
                [[ "$PERF_MONITORING" == "true" ]] && end_timer "branch_check" "$context" "blocked"
                return 1
                ;;

            warn)
                # Warning mode - warn but allow
                show_protected_branch_warning "$current_branch" "$HOOK_NAME"
                log_hook_event "$HOOK_NAME" "WARNED: Operation on $current_branch (warn mode)"
                [[ "$PERF_MONITORING" == "true" ]] && end_timer "branch_check" "$context" "warned"
                return 0
                ;;

            bypass)
                # Bypass mode - allow silently
                log_hook_event "$HOOK_NAME" "BYPASSED: Operation on $current_branch (bypass mode)"
                [[ "$PERF_MONITORING" == "true" ]] && end_timer "branch_check" "$context" "bypassed"
                return 0
                ;;

            *)
                # Default to strict
                show_protected_branch_error "$current_branch"
                log_hook_event "$HOOK_NAME" "BLOCKED: Operation on $current_branch (default strict)"
                [[ "$PERF_MONITORING" == "true" ]] && end_timer "branch_check" "$context" "blocked"
                return 1
                ;;
        esac
    else
        # Not a protected branch - allow
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "✅ Branch check passed: $current_branch" >&2
        fi
        log_hook_event "$HOOK_NAME" "ALLOWED: Operation on $current_branch"
        [[ "$PERF_MONITORING" == "true" ]] && end_timer "branch_check" "$context" "allowed"
        return 0
    fi
}

# ═══════════════════════════════════════════════════════════════
# Caching Wrapper
# ═══════════════════════════════════════════════════════════════

# Function: Cached branch check
cached_branch_check() {
    local context="${1:-default}"
    local operation="${2:-write}"

    if [[ "$CACHE_ENABLED" == "true" ]]; then
        # Use cached result if available
        local cache_context="${context}-${operation}"
        local cached_result

        if cached_result=$(read_cache "branch-check" "$cache_context" "$CACHE_TTL" 2>/dev/null); then
            # Cache hit - use cached result
            echo "[CACHE HIT] Using cached branch check result" >&2
            return "$cached_result"
        else
            # Cache miss - perform check and cache result
            local exit_code=0
            perform_branch_check "$context" "$operation" || exit_code=$?
            write_cache "branch-check" "$cache_context" "$exit_code"
            return $exit_code
        fi
    else
        # No cache - perform check directly
        perform_branch_check "$context" "$operation"
    fi
}

# ═══════════════════════════════════════════════════════════════
# API Functions for Other Hooks
# ═══════════════════════════════════════════════════════════════

# Function: Check if operation is allowed on current branch
is_operation_allowed() {
    local operation="${1:-write}"
    cached_branch_check "api-check" "$operation"
}

# Function: Ensure we're on a feature branch
ensure_feature_branch() {
    local current_branch
    current_branch=$(get_current_branch)

    if is_protected_branch "$current_branch"; then
        if is_auto_create_enabled; then
            auto_create_branch "$current_branch"
        else
            show_protected_branch_error "$current_branch"
            return 1
        fi
    fi
    return 0
}

# ═══════════════════════════════════════════════════════════════
# Export Functions for Other Hooks
# ═══════════════════════════════════════════════════════════════

export -f is_operation_allowed
export -f ensure_feature_branch
export -f cached_branch_check

# ═══════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════

# If sourced, don't execute main logic
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Direct execution - perform check
    context="${1:-direct}"
    operation="${2:-write}"

    # Auto-mode detection
    if is_auto_mode; then
        export CE_SILENT_MODE=true
    fi

    # Perform the check with caching
    if cached_branch_check "$context" "$operation"; then
        exit 0
    else
        exit 1
    fi
fi