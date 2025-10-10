#!/usr/bin/env bash
# Merge Queue Manager for Claude Enhancer v5.4.0
# Purpose: FIFO queue management for multi-terminal merge coordination
# Used by: auto_pr.sh, auto_merge.sh, CI/CD pipeline

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"

# ============================================================================
# Configuration
# ============================================================================

QUEUE_DIR="/tmp/ce_locks"
QUEUE_FILE="${QUEUE_DIR}/merge_queue.fifo"
QUEUE_LOCK="${QUEUE_DIR}/merge_queue.lock"
QUEUE_BACKUP="${QUEUE_DIR}/merge_queue.backup"
STATUS_FILE="${QUEUE_DIR}/merge_queue_status.json"
CONFLICT_LOG="${QUEUE_DIR}/conflicts.log"

# Timeouts
readonly QUEUE_TIMEOUT=600        # 10 minutes max wait
readonly MERGE_TIMEOUT=300        # 5 minutes for merge operation
readonly LOCK_TIMEOUT=30          # 30 seconds for lock acquisition
readonly STALE_THRESHOLD=900      # 15 minutes for stale detection
readonly CONFLICT_CHECK_TIMEOUT=10 # 10 seconds for conflict check

# Retry configuration
readonly MAX_RETRIES=3
readonly RETRY_DELAY=5
readonly BACKOFF_MULTIPLIER=2

# State constants
readonly STATE_QUEUED="QUEUED"
readonly STATE_CONFLICT_CHECK="CONFLICT_CHECK"
readonly STATE_MERGING="MERGING"
readonly STATE_MERGED="MERGED"
readonly STATE_FAILED="FAILED"
readonly STATE_CONFLICT_DETECTED="CONFLICT_DETECTED"
readonly STATE_TIMEOUT="TIMEOUT"
readonly STATE_STALE="STALE"

# Queue entry format: timestamp:pr_number:branch:session_id:status:retry_count:started_at

# ============================================================================
# Utility Functions
# ============================================================================

ensure_queue_structure() {
    ensure_directory "$QUEUE_DIR"

    if [[ ! -f "$QUEUE_FILE" ]]; then
        touch "$QUEUE_FILE"
        log_debug "Created queue file: $QUEUE_FILE"
    fi

    if [[ ! -f "$STATUS_FILE" ]]; then
        echo "[]" > "$STATUS_FILE"
        log_debug "Created status file: $STATUS_FILE"
    fi
}

# Generate unique session ID
generate_session_id() {
    if command -v uuidgen &> /dev/null; then
        uuidgen | tr '[:upper:]' '[:lower:]'
    else
        echo "$(date +%s)-$$-${RANDOM}"
    fi
}

# Get current timestamp
get_timestamp() {
    date +%s
}

# Format timestamp for display
format_timestamp() {
    local ts="$1"
    if [[ -n "$ts" && "$ts" != "null" && "$ts" != "0" ]]; then
        date -d "@${ts}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -r "${ts}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "N/A"
    else
        echo "N/A"
    fi
}

# Calculate time difference in seconds
time_diff() {
    local start="$1"
    local end="${2:-$(get_timestamp)}"
    echo $((end - start))
}

# ============================================================================
# Lock Management
# ============================================================================

acquire_queue_lock() {
    local timeout="${1:-$LOCK_TIMEOUT}"
    local start_time=$(get_timestamp)
    local lock_acquired=0

    log_debug "Attempting to acquire queue lock (timeout: ${timeout}s)"

    while true; do
        # Try to create lock directory atomically
        if mkdir "$QUEUE_LOCK" 2>/dev/null; then
            # Set trap to clean up on exit
            trap 'release_queue_lock' EXIT INT TERM
            log_debug "Queue lock acquired"
            return 0
        fi

        # Check timeout
        local elapsed=$(time_diff "$start_time")
        if [[ $elapsed -gt $timeout ]]; then
            log_error "Failed to acquire queue lock after ${timeout}s"

            # Check if lock is stale
            if [[ -d "$QUEUE_LOCK" ]]; then
                local lock_age=$(file_age_minutes "$QUEUE_LOCK")
                if [[ $lock_age -gt 15 ]]; then
                    log_warning "Detected stale lock (${lock_age} minutes old), removing..."
                    cleanup_stale_lock
                    continue
                fi
            fi

            return 1
        fi

        # Short sleep before retry
        sleep 0.5
    done
}

release_queue_lock() {
    if [[ -d "$QUEUE_LOCK" ]]; then
        rmdir "$QUEUE_LOCK" 2>/dev/null || true
        log_debug "Queue lock released"
    fi
    trap - EXIT INT TERM
}

cleanup_stale_lock() {
    log_warning "Cleaning up stale lock..."
    rmdir "$QUEUE_LOCK" 2>/dev/null || rm -rf "$QUEUE_LOCK" 2>/dev/null || true
}

# ============================================================================
# Queue Operations (Atomic with flock)
# ============================================================================

enqueue_pr() {
    local pr_number="$1"
    local branch="${2:-$(get_current_branch)}"
    local session_id="${CE_SESSION_ID:-$(generate_session_id)}"

    ensure_queue_structure

    # Validate inputs
    if [[ -z "$pr_number" || ! "$pr_number" =~ ^[0-9]+$ ]]; then
        die "Invalid PR number: $pr_number"
    fi

    if ! acquire_queue_lock; then
        die "Failed to acquire lock for enqueue operation"
    fi

    # Check if PR already in queue
    if [[ -f "$QUEUE_FILE" ]] && grep -q "^[^:]*:${pr_number}:" "$QUEUE_FILE" 2>/dev/null; then
        local existing_status=$(grep "^[^:]*:${pr_number}:" "$QUEUE_FILE" | tail -n1 | cut -d: -f5)
        if [[ "$existing_status" == "$STATE_QUEUED" || "$existing_status" == "$STATE_CONFLICT_CHECK" || "$existing_status" == "$STATE_MERGING" ]]; then
            log_warning "PR #$pr_number already in queue with status: $existing_status"
            release_queue_lock
            return 0
        fi
    fi

    # Create backup before modification
    if [[ -f "$QUEUE_FILE" ]]; then
        cp "$QUEUE_FILE" "$QUEUE_BACKUP" 2>/dev/null || true
    fi

    # Add to queue atomically
    local timestamp=$(get_timestamp)
    local entry="${timestamp}:${pr_number}:${branch}:${session_id}:${STATE_QUEUED}:0:0"

    echo "$entry" >> "$QUEUE_FILE"

    log_success "Added PR #$pr_number to merge queue"

    # Show position in queue
    local position=$(grep -n "^[^:]*:${pr_number}:.*:${STATE_QUEUED}$" "$QUEUE_FILE" 2>/dev/null | cut -d: -f1 | tail -n1)
    if [[ -n "$position" ]]; then
        log_info "Queue position: $position"

        # Estimate wait time (30 seconds per position)
        local estimated_wait=$((position * 30))
        log_info "Estimated wait time: ${estimated_wait}s"
    fi

    release_queue_lock

    # Trigger queue processing asynchronously
    trigger_queue_processor &

    return 0
}

dequeue_next() {
    if [[ ! -f "$QUEUE_FILE" ]]; then
        return 1
    fi

    # Get first QUEUED entry
    local entry
    entry=$(grep ":${STATE_QUEUED}:" "$QUEUE_FILE" 2>/dev/null | head -n1)

    if [[ -z "$entry" ]]; then
        return 1
    fi

    echo "$entry"
    return 0
}

update_entry_status() {
    local pr_number="$1"
    local new_status="$2"
    local started_at="${3:-0}"

    if [[ ! -f "$QUEUE_FILE" ]]; then
        return 0
    fi

    local temp_file="${QUEUE_FILE}.tmp.$$"
    local current_time=$(get_timestamp)

    # Update status while preserving other fields
    while IFS=: read -r timestamp pr branch session status retry_count old_started_at; do
        if [[ "$pr" == "$pr_number" ]]; then
            # Update the matching entry
            local updated_started_at="$old_started_at"
            if [[ "$started_at" != "0" ]]; then
                updated_started_at="$started_at"
            fi
            echo "${timestamp}:${pr}:${branch}:${session}:${new_status}:${retry_count}:${updated_started_at}"
        else
            # Keep other entries unchanged
            echo "${timestamp}:${pr}:${branch}:${session}:${status}:${retry_count}:${old_started_at}"
        fi
    done < "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"
    log_debug "Updated PR #$pr_number status to $new_status"
}

increment_retry_count() {
    local pr_number="$1"

    if [[ ! -f "$QUEUE_FILE" ]]; then
        return 0
    fi

    local temp_file="${QUEUE_FILE}.tmp.$$"

    while IFS=: read -r timestamp pr branch session status retry_count started_at; do
        if [[ "$pr" == "$pr_number" ]]; then
            local new_retry_count=$((retry_count + 1))
            echo "${timestamp}:${pr}:${branch}:${session}:${status}:${new_retry_count}:${started_at}"
        else
            echo "${timestamp}:${pr}:${branch}:${session}:${status}:${retry_count}:${started_at}"
        fi
    done < "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"
    log_debug "Incremented retry count for PR #$pr_number"
}

remove_from_queue() {
    local pr_number="$1"

    if [[ ! -f "$QUEUE_FILE" ]]; then
        return 0
    fi

    local temp_file="${QUEUE_FILE}.tmp.$$"

    # Remove entry but keep for history (could be moved to separate log)
    grep -v "^[^:]*:${pr_number}:" "$QUEUE_FILE" > "$temp_file" || true
    mv "$temp_file" "$QUEUE_FILE"

    log_debug "Removed PR #$pr_number from queue"
}

# ============================================================================
# Conflict Detection
# ============================================================================

check_merge_conflicts() {
    local pr_number="$1"
    local branch="$2"
    local base_branch="${3:-$(get_default_branch)}"

    log_info "Checking for conflicts: $branch → $base_branch"

    # Fetch latest changes with timeout
    local fetch_start=$(get_timestamp)
    if ! timeout 30 git fetch origin "$base_branch" "$branch" 2>/dev/null; then
        log_error "Failed to fetch branches (timeout or network error)"
        return 1
    fi

    # Verify branches exist
    if ! git rev-parse --verify "origin/$base_branch" >/dev/null 2>&1; then
        log_error "Base branch origin/$base_branch does not exist"
        return 1
    fi

    if ! git rev-parse --verify "origin/$branch" >/dev/null 2>&1; then
        log_error "Branch origin/$branch does not exist"
        return 1
    fi

    # Use git merge-tree for zero side-effect conflict detection
    local merge_base
    merge_base=$(git merge-base "origin/$base_branch" "origin/$branch" 2>/dev/null)

    if [[ -z "$merge_base" ]]; then
        log_error "Could not find merge base between branches"
        return 1
    fi

    local merge_tree_output
    local merge_tree_exit=0

    # Run merge-tree with timeout
    merge_tree_output=$(timeout "$CONFLICT_CHECK_TIMEOUT" git merge-tree "$merge_base" "origin/$base_branch" "origin/$branch" 2>&1) || merge_tree_exit=$?

    if [[ $merge_tree_exit -eq 124 ]]; then
        log_error "Conflict check timed out after ${CONFLICT_CHECK_TIMEOUT}s"
        return 1
    fi

    # Check for conflict markers
    if echo "$merge_tree_output" | grep -q '<<<<<<<'; then
        log_warning "Conflicts detected in PR #$pr_number"

        # Extract and log conflict files
        local conflict_files
        conflict_files=$(echo "$merge_tree_output" | grep -E '^(changed in both|added in both|deleted by )' | awk '{print $NF}' | sort -u)

        if [[ -n "$conflict_files" ]]; then
            log_warning "Conflicting files:"
            echo "$conflict_files" | while read -r file; do
                log_warning "  - $file"
            done

            # Log to conflict log
            {
                echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] PR #$pr_number ($branch)"
                echo "Conflicts:"
                echo "$conflict_files" | sed 's/^/  /'
                echo "---"
            } >> "$CONFLICT_LOG"
        fi

        return 1
    else
        log_success "No conflicts detected for PR #$pr_number"
        return 0
    fi
}

# ============================================================================
# Merge Execution
# ============================================================================

perform_merge() {
    local pr_number="$1"
    local branch="$2"
    local merge_method="${3:-squash}"  # squash, merge, or rebase

    log_info "Performing merge for PR #$pr_number using method: $merge_method"

    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) not found. Please install it first."
        return 1
    fi

    # Verify gh authentication
    if ! gh auth status &> /dev/null; then
        log_error "Not authenticated with GitHub CLI. Run: gh auth login"
        return 1
    fi

    # Build merge command based on method
    local merge_cmd="gh pr merge ${pr_number} --auto --delete-branch"

    case "$merge_method" in
        squash)
            merge_cmd="$merge_cmd --squash"
            ;;
        merge)
            merge_cmd="$merge_cmd --merge"
            ;;
        rebase)
            merge_cmd="$merge_cmd --rebase"
            ;;
        *)
            log_warning "Unknown merge method: $merge_method, defaulting to squash"
            merge_cmd="$merge_cmd --squash"
            ;;
    esac

    # Execute merge with retry logic
    local attempt=1
    local delay=$RETRY_DELAY

    while [[ $attempt -le $MAX_RETRIES ]]; do
        log_info "Merge attempt $attempt/$MAX_RETRIES"

        if eval "$merge_cmd" 2>&1 | tee /tmp/merge_output_${pr_number}.log; then
            log_success "PR #$pr_number merged successfully"
            rm -f /tmp/merge_output_${pr_number}.log
            return 0
        fi

        local exit_code=${PIPESTATUS[0]}

        # Check if it's a recoverable error
        if grep -q "pull request is not mergeable" /tmp/merge_output_${pr_number}.log; then
            log_error "PR #$pr_number is not mergeable (likely conflicts or failed checks)"
            rm -f /tmp/merge_output_${pr_number}.log
            return 1
        fi

        if [[ $attempt -lt $MAX_RETRIES ]]; then
            log_warning "Merge failed (exit code: $exit_code), retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * BACKOFF_MULTIPLIER))
        fi

        attempt=$((attempt + 1))
    done

    log_error "Failed to merge PR #$pr_number after $MAX_RETRIES attempts"
    rm -f /tmp/merge_output_${pr_number}.log
    return 1
}

# ============================================================================
# Queue Processing
# ============================================================================

process_queue() {
    ensure_queue_structure

    if ! acquire_queue_lock "$LOCK_TIMEOUT"; then
        log_debug "Could not acquire lock, another processor may be running"
        return 0
    fi

    if [[ ! -f "$QUEUE_FILE" || ! -s "$QUEUE_FILE" ]]; then
        log_debug "Queue is empty"
        release_queue_lock
        return 0
    fi

    # Get first queued item
    local entry
    entry=$(dequeue_next)

    if [[ -z "$entry" ]]; then
        log_debug "No queued items to process"
        release_queue_lock
        return 0
    fi

    # Parse entry
    IFS=':' read -r timestamp pr_number branch session_id status retry_count started_at <<< "$entry"

    log_info "Processing PR #$pr_number from queue (branch: $branch)"

    # Check for timeout
    local queue_age=$(time_diff "$timestamp")
    if [[ $queue_age -gt $QUEUE_TIMEOUT ]]; then
        log_error "PR #$pr_number has exceeded timeout (${queue_age}s > ${QUEUE_TIMEOUT}s)"
        update_entry_status "$pr_number" "$STATE_TIMEOUT"
        release_queue_lock
        return 1
    fi

    # Update status to CONFLICT_CHECK
    local check_start=$(get_timestamp)
    update_entry_status "$pr_number" "$STATE_CONFLICT_CHECK" "$check_start"
    release_queue_lock

    # Check for conflicts (outside lock to allow parallel operations)
    local has_conflicts=0
    if ! check_merge_conflicts "$pr_number" "$branch"; then
        has_conflicts=1
    fi

    # Re-acquire lock for status update
    if ! acquire_queue_lock "$LOCK_TIMEOUT"; then
        log_error "Failed to re-acquire lock after conflict check"
        return 1
    fi

    if [[ $has_conflicts -eq 1 ]]; then
        log_error "PR #$pr_number has merge conflicts"
        update_entry_status "$pr_number" "$STATE_CONFLICT_DETECTED"

        # Check retry count
        if [[ $retry_count -lt $MAX_RETRIES ]]; then
            increment_retry_count "$pr_number"
            log_info "Will retry PR #$pr_number (retry $((retry_count + 1))/$MAX_RETRIES)"
            # Reset to QUEUED for retry
            update_entry_status "$pr_number" "$STATE_QUEUED"
        else
            log_error "PR #$pr_number exceeded max retries ($MAX_RETRIES)"
            update_entry_status "$pr_number" "$STATE_FAILED"
        fi

        release_queue_lock
        return 1
    fi

    # Update status to MERGING
    local merge_start=$(get_timestamp)
    update_entry_status "$pr_number" "$STATE_MERGING" "$merge_start"
    release_queue_lock

    # Perform merge (outside lock)
    local merge_success=0
    if perform_merge "$pr_number" "$branch"; then
        merge_success=1
    fi

    # Re-acquire lock for final status update
    if ! acquire_queue_lock "$LOCK_TIMEOUT"; then
        log_error "Failed to re-acquire lock after merge"
        return 1
    fi

    if [[ $merge_success -eq 1 ]]; then
        update_entry_status "$pr_number" "$STATE_MERGED"
        remove_from_queue "$pr_number"
        log_success "PR #$pr_number merged successfully and removed from queue"

        release_queue_lock

        # Process next item
        process_queue &
        return 0
    else
        update_entry_status "$pr_number" "$STATE_FAILED"
        log_error "Failed to merge PR #$pr_number"
        release_queue_lock
        return 1
    fi
}

trigger_queue_processor() {
    # Check if processor is already running
    if [[ -d "$QUEUE_LOCK" ]]; then
        log_debug "Queue processor already running"
        return 0
    fi

    # Start processor in background
    nohup bash -c "
        source '${SCRIPT_DIR}/../utils/common.sh'
        source '${BASH_SOURCE[0]}'
        process_queue
    " > /dev/null 2>&1 &

    log_debug "Triggered queue processor (PID: $!)"
}

# ============================================================================
# Queue Status and Monitoring
# ============================================================================

show_queue_status() {
    local detailed="${1:-false}"

    if [[ ! -f "$QUEUE_FILE" ]] || [[ ! -s "$QUEUE_FILE" ]]; then
        echo ""
        echo "═══════════════════════════════════════"
        echo "       Merge Queue Status: EMPTY"
        echo "═══════════════════════════════════════"
        return 0
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "                       Merge Queue Status"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""

    if [[ "$detailed" == "true" ]]; then
        printf "%-4s %-8s %-25s %-20s %-10s %-8s\n" "Pos" "PR" "Branch" "Status" "Wait(s)" "Retries"
    else
        printf "%-4s %-8s %-25s %-20s\n" "Pos" "PR" "Branch" "Status"
    fi
    echo "───────────────────────────────────────────────────────────────────"

    local pos=1
    local current_time=$(get_timestamp)

    while IFS=: read -r timestamp pr_number branch session_id status retry_count started_at; do
        local wait_time=$(time_diff "$timestamp" "$current_time")

        # Add color to status
        local colored_status="$status"
        case "$status" in
            "$STATE_MERGED")
                colored_status="${GREEN}${status}${NC}"
                ;;
            "$STATE_FAILED"|"$STATE_TIMEOUT")
                colored_status="${RED}${status}${NC}"
                ;;
            "$STATE_MERGING")
                colored_status="${BLUE}${status}${NC}"
                ;;
            "$STATE_CONFLICT_DETECTED")
                colored_status="${YELLOW}${status}${NC}"
                ;;
        esac

        if [[ "$detailed" == "true" ]]; then
            printf "%-4s %-8s %-25s %-30s %-10s %-8s\n" \
                "$pos" "#$pr_number" "${branch:0:25}" "$colored_status" "$wait_time" "$retry_count"
        else
            printf "%-4s %-8s %-25s %-30s\n" \
                "$pos" "#$pr_number" "${branch:0:25}" "$colored_status"
        fi

        pos=$((pos + 1))
    done < "$QUEUE_FILE"

    echo "═══════════════════════════════════════════════════════════════════"

    # Show summary
    local total=$(wc -l < "$QUEUE_FILE")
    local queued=$(grep -c ":${STATE_QUEUED}:" "$QUEUE_FILE" 2>/dev/null || echo 0)
    local processing=$(grep -c ":${STATE_MERGING}:" "$QUEUE_FILE" 2>/dev/null || echo 0)
    local merged=$(grep -c ":${STATE_MERGED}:" "$QUEUE_FILE" 2>/dev/null || echo 0)
    local failed=$(grep -c ":${STATE_FAILED}:" "$QUEUE_FILE" 2>/dev/null || echo 0)

    echo "Summary: Total=$total | Queued=$queued | Processing=$processing | Merged=$merged | Failed=$failed"
    echo ""
}

# ============================================================================
# Cleanup and Maintenance
# ============================================================================

cleanup_stale_entries() {
    local threshold="${1:-$STALE_THRESHOLD}"

    log_info "Cleaning up stale entries (threshold: ${threshold}s)"

    if [[ ! -f "$QUEUE_FILE" ]]; then
        return 0
    fi

    if ! acquire_queue_lock "$LOCK_TIMEOUT"; then
        log_error "Could not acquire lock for cleanup"
        return 1
    fi

    local temp_file="${QUEUE_FILE}.tmp.$$"
    local current_time=$(get_timestamp)
    local removed_count=0

    while IFS=: read -r timestamp pr_number branch session_id status retry_count started_at; do
        local age=$(time_diff "$timestamp" "$current_time")

        # Remove stale entries in non-terminal states
        if [[ $age -gt $threshold ]]; then
            case "$status" in
                "$STATE_QUEUED"|"$STATE_CONFLICT_CHECK"|"$STATE_MERGING")
                    log_warning "Removing stale entry: PR #$pr_number (age: ${age}s, status: $status)"
                    removed_count=$((removed_count + 1))
                    continue
                    ;;
            esac
        fi

        # Keep entry
        echo "${timestamp}:${pr_number}:${branch}:${session_id}:${status}:${retry_count}:${started_at}"
    done < "$QUEUE_FILE" > "$temp_file"

    mv "$temp_file" "$QUEUE_FILE"
    release_queue_lock

    log_success "Cleanup complete: removed $removed_count stale entries"
    return 0
}

clear_queue() {
    local force="${1:-false}"

    if [[ "$force" != "true" ]]; then
        echo "This will clear all queue entries. Are you sure? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Aborted"
            return 0
        fi
    fi

    if ! acquire_queue_lock "$LOCK_TIMEOUT"; then
        log_error "Could not acquire lock to clear queue"
        return 1
    fi

    # Backup before clearing
    if [[ -f "$QUEUE_FILE" ]]; then
        cp "$QUEUE_FILE" "${QUEUE_BACKUP}.$(date +%s)" 2>/dev/null || true
    fi

    > "$QUEUE_FILE"
    release_queue_lock

    log_success "Queue cleared"
    return 0
}

# ============================================================================
# Main CLI
# ============================================================================

show_usage() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
  enqueue <pr_number> [branch]    Add PR to merge queue
  process                          Process queue (usually automatic)
  status [--detailed]              Show queue status
  cleanup [threshold_seconds]      Remove stale entries
  clear [--force]                  Clear entire queue
  help                             Show this help message

Examples:
  $0 enqueue 123 feature/new-feature
  $0 status --detailed
  $0 cleanup 900
  $0 clear --force

Environment Variables:
  CE_SESSION_ID    Custom session identifier
  CE_DEBUG         Enable debug logging (set to 1)

EOF
}

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
            local detailed=false
            if [[ "${1:-}" == "--detailed" || "${1:-}" == "-d" ]]; then
                detailed=true
            fi
            show_queue_status "$detailed"
            ;;
        cleanup)
            local threshold="${1:-$STALE_THRESHOLD}"
            cleanup_stale_entries "$threshold"
            ;;
        clear)
            local force=false
            if [[ "${1:-}" == "--force" || "${1:-}" == "-f" ]]; then
                force=true
            fi
            clear_queue "$force"
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# ============================================================================
# Entry Point
# ============================================================================

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
