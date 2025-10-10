#!/usr/bin/env bash
# Merge Queue Manager for Claude Enhancer v5.4.0
# Purpose: FIFO queue management for multi-terminal merge coordination
# Used by: auto_pr.sh, auto_merge.sh, CI/CD pipeline

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"

# Configuration
QUEUE_FILE="/tmp/ce_locks/merge_queue.fifo"
QUEUE_LOCK="/tmp/ce_locks/merge_queue.lock"
QUEUE_TIMEOUT=600  # 10 minutes
STATUS_FILE="/tmp/ce_locks/merge_queue_status.json"

# Ensure directories exist
ensure_directory "/tmp/ce_locks"

# Queue entry format: timestamp:pr_number:branch:session_id:status
# Status: QUEUED, CONFLICT_CHECK, MERGING, MERGED, FAILED

# Functions

acquire_queue_lock() {
    local timeout="${1:-$QUEUE_TIMEOUT}"
    local start_time=$(date +%s)

    while true; do
        if mkdir "$QUEUE_LOCK" 2>/dev/null; then
            trap 'rmdir "$QUEUE_LOCK" 2>/dev/null || true' EXIT
            return 0
        fi

        local elapsed=$(($(date +%s) - start_time))
        if [[ $elapsed -gt $timeout ]]; then
            log_error "Failed to acquire queue lock after ${timeout}s"
            return 1
        fi

        sleep 1
    done
}

release_queue_lock() {
    rmdir "$QUEUE_LOCK" 2>/dev/null || true
    trap - EXIT
}

enqueue_pr() {
    local pr_number="$1"
    local branch="${2:-$(get_current_branch)}"
    local session_id="${CE_SESSION_ID:-$(uuidgen || date +%s)}"

    acquire_queue_lock || return 1

    # Check if PR already in queue
    if [[ -f "$QUEUE_FILE" ]] && grep -q ":${pr_number}:" "$QUEUE_FILE"; then
        log_warning "PR #$pr_number already in queue"
        release_queue_lock
        return 0
    fi

    # Add to queue
    local timestamp=$(date +%s)
    local entry="${timestamp}:${pr_number}:${branch}:${session_id}:QUEUED"

    echo "$entry" >> "$QUEUE_FILE"
    log_success "Added PR #$pr_number to merge queue"

    # Show position
    local position=$(grep -n ":${pr_number}:" "$QUEUE_FILE" | cut -d: -f1)
    log_info "Queue position: $position"

    release_queue_lock

    # Trigger queue processing
    process_queue_async &
}

process_queue() {
    acquire_queue_lock || return 1

    if [[ ! -f "$QUEUE_FILE" ]]; then
        log_debug "Queue is empty"
        release_queue_lock
        return 0
    fi

    # Get first queued item
    local entry=$(grep ':QUEUED$' "$QUEUE_FILE" | head -n1)

    if [[ -z "$entry" ]]; then
        log_debug "No queued items to process"
        release_queue_lock
        return 0
    fi

    # Parse entry
    IFS=':' read -r timestamp pr_number branch session_id status <<< "$entry"

    log_info "Processing PR #$pr_number from queue"

    # Update status to CONFLICT_CHECK
    update_entry_status "$pr_number" "CONFLICT_CHECK"
    release_queue_lock

    # Check for conflicts
    if check_merge_conflicts "$pr_number" "$branch"; then
        acquire_queue_lock || return 1
        update_entry_status "$pr_number" "MERGING"
        release_queue_lock

        # Perform merge
        if perform_merge "$pr_number" "$branch"; then
            acquire_queue_lock || return 1
            update_entry_status "$pr_number" "MERGED"
            remove_from_queue "$pr_number"
            release_queue_lock

            log_success "PR #$pr_number merged successfully"

            # Process next item
            process_queue &
        else
            acquire_queue_lock || return 1
            update_entry_status "$pr_number" "FAILED"
            release_queue_lock

            log_error "Failed to merge PR #$pr_number"
        fi
    else
        acquire_queue_lock || return 1
        update_entry_status "$pr_number" "FAILED"
        release_queue_lock

        log_error "PR #$pr_number has merge conflicts"
    fi
}

process_queue_async() {
    nohup bash -c "$(declare -f process_queue check_merge_conflicts perform_merge update_entry_status remove_from_queue); process_queue" > /dev/null 2>&1 &
}

check_merge_conflicts() {
    local pr_number="$1"
    local branch="$2"
    local base_branch="${3:-$(get_default_branch)}"

    log_info "Checking for conflicts: $branch → $base_branch"

    # Fetch latest
    git fetch origin "$base_branch" "$branch" 2>/dev/null || true

    # Use merge-tree for zero side-effect conflict detection
    local merge_result
    if merge_result=$(git merge-tree "origin/$base_branch" "origin/$branch" 2>&1); then
        if echo "$merge_result" | grep -q "<<<<<<"; then
            log_warning "Conflicts detected in PR #$pr_number"
            return 1
        else
            log_success "No conflicts detected"
            return 0
        fi
    else
        log_error "Failed to check conflicts"
        return 1
    fi
}

perform_merge() {
    local pr_number="$1"
    local branch="$2"

    # Use GitHub CLI for merge
    if gh pr merge "$pr_number" --auto --squash --delete-branch; then
        log_success "PR #$pr_number merged"
        return 0
    else
        log_error "Failed to merge PR #$pr_number"
        return 1
    fi
}

update_entry_status() {
    local pr_number="$1"
    local new_status="$2"

    if [[ ! -f "$QUEUE_FILE" ]]; then
        return 0
    fi

    # Update status in place
    sed -i "s/:${pr_number}:[^:]*:[^:]*:[^:]*$/:${pr_number}:\0:${new_status}/" "$QUEUE_FILE" 2>/dev/null || {
        # macOS compatible
        sed -i '' "s/:${pr_number}:[^:]*:[^:]*:[^:]*$/:${pr_number}:\0:${new_status}/" "$QUEUE_FILE"
    }

    log_debug "Updated PR #$pr_number status to $new_status"
}

remove_from_queue() {
    local pr_number="$1"

    if [[ ! -f "$QUEUE_FILE" ]]; then
        return 0
    fi

    # Remove entry
    grep -v ":${pr_number}:" "$QUEUE_FILE" > "${QUEUE_FILE}.tmp" || true
    mv "${QUEUE_FILE}.tmp" "$QUEUE_FILE"

    log_debug "Removed PR #$pr_number from queue"
}

show_queue_status() {
    if [[ ! -f "$QUEUE_FILE" ]] || [[ ! -s "$QUEUE_FILE" ]]; then
        echo "Merge queue is empty"
        return 0
    fi

    echo "═══════════════════════════════════════"
    echo "         Merge Queue Status"
    echo "═══════════════════════════════════════"
    echo ""
    printf "%-4s %-10s %-30s %-15s\n" "Pos" "PR" "Branch" "Status"
    echo "───────────────────────────────────────"

    local pos=1
    while IFS=':' read -r timestamp pr_number branch session_id status; do
        printf "%-4s %-10s %-30s %-15s\n" "$pos" "#$pr_number" "$branch" "$status"
        pos=$((pos + 1))
    done < "$QUEUE_FILE"

    echo "═══════════════════════════════════════"
}

# Main execution
main() {
    local command="${1:-status}"
    shift || true

    case "$command" in
        enqueue)
            if [[ $# -lt 1 ]]; then
                die "Usage: $0 enqueue <pr_number> [branch]"
            fi
            enqueue_pr "$@"
            ;;
        process)
            process_queue
            ;;
        status)
            show_queue_status
            ;;
        clear)
            rm -f "$QUEUE_FILE"
            log_success "Queue cleared"
            ;;
        *)
            echo "Usage: $0 {enqueue|process|status|clear}"
            echo ""
            echo "Commands:"
            echo "  enqueue <pr_number> [branch]  - Add PR to queue"
            echo "  process                        - Process queue"
            echo "  status                         - Show queue status"
            echo "  clear                          - Clear queue"
            exit 1
            ;;
    esac
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
