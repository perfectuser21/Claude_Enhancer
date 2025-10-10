#!/usr/bin/env bash
# state_manager.sh - Session and state management
# Handles workflow state persistence and session lifecycle
set -euo pipefail

# State storage paths
CE_STATE_DIR=".workflow/cli/state"
CE_STATE_FILE="${CE_STATE_DIR}/global.state.yml"
CE_SESSION_DIR="${CE_STATE_DIR}/sessions"
CE_HISTORY_DIR="${CE_STATE_DIR}/history"
CE_BACKUP_DIR="${CE_STATE_DIR}/backups"
CE_LOCK_DIR="${CE_STATE_DIR}/locks"

# Load common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh" 2>/dev/null || true

# Check if yq is available for YAML operations
HAS_YQ=false
if command -v yq &>/dev/null; then
    HAS_YQ=true
fi

# ============================================================================
# State initialization
# ============================================================================

ce_state_init() {
    # Initialize state management system
    # Returns: 0 on success, 1 on error

    local base_dir="${1:-.}"
    cd "$base_dir" || return 1

    # Create state directories if missing
    mkdir -p "${CE_SESSION_DIR}" "${CE_HISTORY_DIR}" "${CE_BACKUP_DIR}" "${CE_LOCK_DIR}"

    # Initialize global state if new
    if [[ ! -f "${CE_STATE_FILE}" ]]; then
        cat > "${CE_STATE_FILE}" <<EOF
active_terminals: []
active_branches: []
resource_locks: {}
last_cleanup: null
statistics:
  total_sessions: 0
  total_branches: 0
  total_merges: 0
EOF
    fi

    # Validate state integrity
    ce_state_validate || {
        echo "ERROR: State validation failed" >&2
        return 1
    }

    # Load or create session for current terminal
    local term_id="${CE_TERMINAL_ID:-$(ce_get_terminal_id)}"
    local session_file="${CE_SESSION_DIR}/${term_id}.state"

    if [[ ! -f "$session_file" ]]; then
        ce_state_create_session "$term_id" || return 1
    fi

    return 0
}

ce_state_validate() {
    # Validate state file integrity
    # Returns: 0 if valid, 1 with errors

    [[ ! -f "${CE_STATE_FILE}" ]] && {
        echo "ERROR: State file not found: ${CE_STATE_FILE}" >&2
        return 1
    }

    # Validate YAML syntax
    if $HAS_YQ; then
        yq eval '.' "${CE_STATE_FILE}" &>/dev/null || {
            echo "ERROR: Invalid YAML syntax in ${CE_STATE_FILE}" >&2
            return 1
        }
    fi

    # Check required fields
    local required_fields=("active_terminals" "active_branches" "statistics")
    for field in "${required_fields[@]}"; do
        if $HAS_YQ; then
            yq eval ".${field}" "${CE_STATE_FILE}" &>/dev/null || {
                echo "ERROR: Missing required field: ${field}" >&2
                return 1
            }
        fi
    done

    # Clean up orphaned sessions (sessions without corresponding files)
    if $HAS_YQ; then
        local active_terminals
        active_terminals=$(yq eval '.active_terminals[]' "${CE_STATE_FILE}" 2>/dev/null || echo "")

        for term_id in $active_terminals; do
            if [[ ! -f "${CE_SESSION_DIR}/${term_id}.state" ]]; then
                echo "WARNING: Orphaned session detected: ${term_id}" >&2
                ce_state_remove_terminal "$term_id"
            fi
        done
    fi

    return 0
}

# ============================================================================
# State persistence
# ============================================================================

ce_state_save() {
    # Save current state to disk with atomic write
    # Usage: ce_state_save

    local temp_file="${CE_STATE_FILE}.tmp.$$"

    # Copy current state to temp file
    cp "${CE_STATE_FILE}" "$temp_file" 2>/dev/null || {
        echo "ERROR: Failed to create temp file" >&2
        return 1
    }

    # Validate YAML syntax
    if $HAS_YQ; then
        yq eval '.' "$temp_file" &>/dev/null || {
            echo "ERROR: Invalid YAML in temp file" >&2
            rm -f "$temp_file"
            return 1
        }
    fi

    # Atomic move
    mv -f "$temp_file" "${CE_STATE_FILE}" || {
        echo "ERROR: Failed to save state" >&2
        rm -f "$temp_file"
        return 1
    }

    return 0
}

ce_state_load() {
    # Load state from disk
    # Returns: State content

    if [[ ! -f "${CE_STATE_FILE}" ]]; then
        echo "ERROR: State file not found" >&2
        return 1
    fi

    cat "${CE_STATE_FILE}"
}

ce_state_get() {
    # Get specific state value using yq/grep
    # Usage: value=$(ce_state_get "statistics.total_sessions")

    local path="$1"

    [[ -z "$path" ]] && {
        echo "ERROR: Path required" >&2
        return 1
    }

    if $HAS_YQ; then
        yq eval ".${path}" "${CE_STATE_FILE}" 2>/dev/null || echo ""
    else
        # Fallback to grep for simple values
        grep "^${path}:" "${CE_STATE_FILE}" | cut -d':' -f2- | xargs || echo ""
    fi
}

ce_state_set() {
    # Set specific state value
    # Usage: ce_state_set "statistics.total_sessions" "5"

    local path="$1"
    local value="$2"

    [[ -z "$path" || -z "$value" ]] && {
        echo "ERROR: Path and value required" >&2
        return 1
    }

    if $HAS_YQ; then
        yq eval -i ".${path} = ${value}" "${CE_STATE_FILE}" || {
            echo "ERROR: Failed to set value" >&2
            return 1
        }
    else
        # Fallback: manual edit (limited)
        echo "WARNING: yq not available, manual state editing not fully supported" >&2
        return 1
    fi

    ce_state_save
}

ce_state_backup() {
    # Create backup of current state
    # Keeps last 10 backups

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${CE_BACKUP_DIR}/state_${timestamp}.yml"

    cp "${CE_STATE_FILE}" "$backup_file" || {
        echo "ERROR: Failed to create backup" >&2
        return 1
    }

    # Keep only last 10 backups
    local backup_count=$(ls -1 "${CE_BACKUP_DIR}"/state_*.yml 2>/dev/null | wc -l)
    if (( backup_count > 10 )); then
        ls -1t "${CE_BACKUP_DIR}"/state_*.yml | tail -n +11 | xargs rm -f
    fi

    echo "$backup_file"
}

ce_state_restore() {
    # Restore state from backup
    # Usage: ce_state_restore [backup_timestamp]

    local backup_timestamp="$1"

    if [[ -z "$backup_timestamp" ]]; then
        echo "Available backups:"
        ls -1t "${CE_BACKUP_DIR}"/state_*.yml 2>/dev/null | while read -r f; do
            local fname=$(basename "$f")
            local ts=$(echo "$fname" | sed 's/state_\(.*\)\.yml/\1/')
            echo "  - $ts"
        done
        return 0
    fi

    local backup_file="${CE_BACKUP_DIR}/state_${backup_timestamp}.yml"

    [[ ! -f "$backup_file" ]] && {
        echo "ERROR: Backup not found: $backup_file" >&2
        return 1
    }

    # Create backup of current state before restoring
    ce_state_backup >/dev/null

    # Restore
    cp "$backup_file" "${CE_STATE_FILE}" || {
        echo "ERROR: Failed to restore backup" >&2
        return 1
    }

    echo "State restored from backup: $backup_timestamp"
}

# ============================================================================
# Session management
# ============================================================================

ce_state_create_session() {
    # Create new workflow session
    # Usage: session_id=$(ce_state_create_session [terminal_id])

    local term_id="${1:-$(ce_get_terminal_id)}"
    local session_file="${CE_SESSION_DIR}/${term_id}.state"
    local timestamp=$(date -Iseconds)
    local current_phase=$(cat .phase/current 2>/dev/null || echo "P0")
    local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

    # Check if session already exists
    if [[ -f "$session_file" ]]; then
        echo "WARNING: Session already exists for terminal ${term_id}" >&2
        echo "$term_id"
        return 0
    fi

    # Create session from template
    cat > "$session_file" <<EOF
terminal_id: "${term_id}"
branch: "${current_branch}"
phase: "${current_phase}"
status: "active"
started_at: "${timestamp}"
last_activity: "${timestamp}"
gates_passed: []
files_modified: []
locks_held: []
metrics:
  commits: 0
  lines_added: 0
  lines_deleted: 0
  tests_added: 0
quality:
  coverage: 0.0
  lint_errors: 0
  test_pass_rate: 0.0
EOF

    # Register terminal in global state
    if $HAS_YQ; then
        yq eval -i ".active_terminals += [\"${term_id}\"]" "${CE_STATE_FILE}"
        yq eval -i ".statistics.total_sessions += 1" "${CE_STATE_FILE}"
    fi

    echo "$term_id"
}

ce_state_get_session() {
    # Get current active session ID
    # Returns: Session ID or empty if none

    local term_id="${CE_TERMINAL_ID:-$(ce_get_terminal_id)}"

    if [[ -f "${CE_SESSION_DIR}/${term_id}.state" ]]; then
        echo "$term_id"
    else
        echo ""
    fi
}

ce_state_load_session() {
    # Load session by ID
    # Returns: Session object as YAML
    # Usage: session=$(ce_state_load_session "t1")

    local session_id="${1:-$(ce_get_terminal_id)}"
    local session_file="${CE_SESSION_DIR}/${session_id}.state"

    [[ ! -f "$session_file" ]] && {
        echo "ERROR: Session not found: $session_id" >&2
        return 1
    }

    cat "$session_file"
}

ce_state_save_session() {
    # Save session data atomically
    # Usage: ce_state_save_session "session_id" "$session_data"

    local session_id="$1"
    local session_data="$2"

    [[ -z "$session_id" ]] && {
        echo "ERROR: Session ID required" >&2
        return 1
    }

    local session_file="${CE_SESSION_DIR}/${session_id}.state"
    local temp_file="${session_file}.tmp.$$"

    # Write to temp file
    echo "$session_data" > "$temp_file" || {
        echo "ERROR: Failed to write session" >&2
        return 1
    }

    # Validate YAML
    if $HAS_YQ; then
        yq eval '.' "$temp_file" &>/dev/null || {
            echo "ERROR: Invalid session YAML" >&2
            rm -f "$temp_file"
            return 1
        }
    fi

    # Atomic move
    mv -f "$temp_file" "$session_file"

    # Update last_activity
    ce_state_update_session "$session_id" "last_activity" "\"$(date -Iseconds)\""
}

ce_state_update_session() {
    # Update specific session field
    # Usage: ce_state_update_session "session_id" "phase" "P3"

    local session_id="$1"
    local field="$2"
    local value="$3"

    [[ -z "$session_id" || -z "$field" ]] && {
        echo "ERROR: Session ID and field required" >&2
        return 1
    }

    local session_file="${CE_SESSION_DIR}/${session_id}.state"

    [[ ! -f "$session_file" ]] && {
        echo "ERROR: Session not found: $session_id" >&2
        return 1
    }

    if $HAS_YQ; then
        # Quote value if it's a string and not already quoted
        if [[ ! "$value" =~ ^[0-9]+$ && ! "$value" =~ ^\".+\"$ ]]; then
            value="\"$value\""
        fi
        yq eval -i ".${field} = ${value}" "$session_file"
    else
        echo "WARNING: yq not available, session update not fully supported" >&2
        return 1
    fi
}

ce_state_list_sessions() {
    # List all sessions
    # Output format:
    #   * t1 (active) - P3: Implementation - 2h ago
    #     t2 (paused) - P2: Skeleton - 1d ago

    [[ ! -d "${CE_SESSION_DIR}" ]] && return 0

    local current_term="${CE_TERMINAL_ID:-$(ce_get_terminal_id)}"

    for session_file in "${CE_SESSION_DIR}"/*.state; do
        [[ ! -f "$session_file" ]] && continue

        local term_id=$(basename "$session_file" .state)
        local status phase branch last_activity

        if $HAS_YQ; then
            status=$(yq eval '.status' "$session_file")
            phase=$(yq eval '.phase' "$session_file")
            branch=$(yq eval '.branch' "$session_file")
            last_activity=$(yq eval '.last_activity' "$session_file")
        else
            status=$(grep '^status:' "$session_file" | cut -d':' -f2 | xargs)
            phase=$(grep '^phase:' "$session_file" | cut -d':' -f2 | xargs)
            branch=$(grep '^branch:' "$session_file" | cut -d':' -f2 | xargs)
            last_activity=$(grep '^last_activity:' "$session_file" | cut -d':' -f2- | xargs)
        fi

        local marker=" "
        [[ "$term_id" == "$current_term" ]] && marker="*"

        # Calculate time ago (simplified)
        local time_ago="recently"
        if [[ -n "$last_activity" ]]; then
            local last_ts=$(date -d "$last_activity" +%s 2>/dev/null || echo "0")
            local now_ts=$(date +%s)
            local diff=$((now_ts - last_ts))

            if (( diff < 3600 )); then
                time_ago="$((diff / 60))m ago"
            elif (( diff < 86400 )); then
                time_ago="$((diff / 3600))h ago"
            else
                time_ago="$((diff / 86400))d ago"
            fi
        fi

        printf "%s %s (%s) - %s - %s - %s\n" "$marker" "$term_id" "$status" "$phase" "$branch" "$time_ago"
    done
}

ce_state_activate_session() {
    # Activate a session (make it current)
    # Usage: ce_state_activate_session "session_id"

    local session_id="$1"

    [[ -z "$session_id" ]] && {
        echo "ERROR: Session ID required" >&2
        return 1
    }

    # Deactivate previous session (current terminal)
    local current_term="${CE_TERMINAL_ID:-$(ce_get_terminal_id)}"
    if [[ -f "${CE_SESSION_DIR}/${current_term}.state" ]]; then
        ce_state_update_session "$current_term" "status" "paused"
    fi

    # Activate target session
    ce_state_update_session "$session_id" "status" "active" || return 1

    # Update environment
    export CE_TERMINAL_ID="$session_id"

    echo "Session activated: $session_id"
}

ce_state_pause_session() {
    # Pause current session
    # Usage: ce_state_pause_session

    local term_id="${CE_TERMINAL_ID:-$(ce_get_terminal_id)}"

    ce_state_update_session "$term_id" "status" "paused" || return 1

    echo "Session paused: $term_id"
}

ce_state_resume_session() {
    # Resume paused session
    # Usage: ce_state_resume_session "session_id"

    local session_id="${1:-$(ce_get_terminal_id)}"

    ce_state_update_session "$session_id" "status" "active" || return 1

    echo "Session resumed: $session_id"
}

ce_state_close_session() {
    # Close session (mark as completed)
    # Usage: ce_state_close_session "session_id"

    local session_id="${1:-$(ce_get_terminal_id)}"
    local session_file="${CE_SESSION_DIR}/${session_id}.state"

    [[ ! -f "$session_file" ]] && {
        echo "ERROR: Session not found: $session_id" >&2
        return 1
    }

    # Mark as closed
    ce_state_update_session "$session_id" "status" "closed"

    # Archive session
    ce_state_archive_session "$session_id"

    # Remove from active terminals
    ce_state_remove_terminal "$session_id"

    echo "Session closed: $session_id"
}

# ============================================================================
# Session metadata
# ============================================================================

ce_state_get_metadata() {
    # Get session metadata
    # Usage: metadata=$(ce_state_get_metadata [session_id])

    local session_id="${1:-$(ce_get_terminal_id)}"

    ce_state_load_session "$session_id"
}

ce_state_set_metadata() {
    # Update session metadata field
    # Usage: ce_state_set_metadata "session_id" "field" "value"

    ce_state_update_session "$@"
}

ce_state_add_commit() {
    # Record commit in session
    # Usage: ce_state_add_commit "session_id" "commit_hash" "commit_message"

    local session_id="$1"
    local commit_hash="$2"
    local commit_msg="$3"

    local session_file="${CE_SESSION_DIR}/${session_id}.state"

    # Increment commit counter
    if $HAS_YQ; then
        local current_commits=$(yq eval '.metrics.commits' "$session_file")
        yq eval -i ".metrics.commits = $((current_commits + 1))" "$session_file"
    fi

    echo "Commit recorded: $commit_hash"
}

ce_state_get_commits() {
    # Get all commits for session
    # Usage: commits=$(ce_state_get_commits "session_id")

    local session_id="${1:-$(ce_get_terminal_id)}"
    local session_file="${CE_SESSION_DIR}/${session_id}.state"

    if $HAS_YQ; then
        yq eval '.metrics.commits' "$session_file"
    else
        grep -A1 'metrics:' "$session_file" | grep 'commits:' | cut -d':' -f2 | xargs
    fi
}

# ============================================================================
# Session analytics
# ============================================================================

ce_state_get_duration() {
    # Calculate session duration in seconds
    # Usage: duration=$(ce_state_get_duration "session_id")

    local session_id="${1:-$(ce_get_terminal_id)}"
    local session_file="${CE_SESSION_DIR}/${session_id}.state"

    if $HAS_YQ; then
        local started_at=$(yq eval '.started_at' "$session_file")
        local start_ts=$(date -d "$started_at" +%s 2>/dev/null || echo "0")
        local now_ts=$(date +%s)
        echo $((now_ts - start_ts))
    else
        echo "0"
    fi
}

ce_state_get_stats() {
    # Get session statistics
    # Returns: Statistics as YAML

    local session_id="${1:-$(ce_get_terminal_id)}"
    local session_file="${CE_SESSION_DIR}/${session_id}.state"

    local duration=$(ce_state_get_duration "$session_id")

    if $HAS_YQ; then
        cat <<EOF
duration: ${duration}
commits: $(yq eval '.metrics.commits' "$session_file")
lines_added: $(yq eval '.metrics.lines_added' "$session_file")
lines_deleted: $(yq eval '.metrics.lines_deleted' "$session_file")
tests_added: $(yq eval '.metrics.tests_added' "$session_file")
coverage: $(yq eval '.quality.coverage' "$session_file")
EOF
    fi
}

# ============================================================================
# Cleanup operations
# ============================================================================

ce_state_cleanup_stale() {
    # Cleanup stale sessions
    # Usage: ce_state_cleanup_stale [--days=7] [--dry-run]

    local days=7
    local dry_run=false

    # Parse arguments
    for arg in "$@"; do
        case "$arg" in
            --days=*)
                days="${arg#*=}"
                ;;
            --dry-run)
                dry_run=true
                ;;
        esac
    done

    local cutoff_ts=$(($(date +%s) - days * 86400))

    echo "Cleaning up sessions inactive for more than ${days} days..."

    for session_file in "${CE_SESSION_DIR}"/*.state; do
        [[ ! -f "$session_file" ]] && continue

        local term_id=$(basename "$session_file" .state)
        local last_activity status

        if $HAS_YQ; then
            last_activity=$(yq eval '.last_activity' "$session_file")
            status=$(yq eval '.status' "$session_file")
        else
            continue
        fi

        local last_ts=$(date -d "$last_activity" +%s 2>/dev/null || echo "0")

        # Check if stale
        if (( last_ts < cutoff_ts )) && [[ "$status" == "paused" ]]; then
            echo "  - Stale session: $term_id (last activity: $last_activity)"

            if ! $dry_run; then
                ce_state_archive_session "$term_id"
                rm -f "$session_file"
                ce_state_remove_terminal "$term_id"
            fi
        fi
    done
}

ce_state_archive_session() {
    # Archive session to history
    # Usage: ce_state_archive_session "session_id"

    local session_id="$1"
    local session_file="${CE_SESSION_DIR}/${session_id}.state"

    [[ ! -f "$session_file" ]] && return 1

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local archive_file="${CE_HISTORY_DIR}/${session_id}_${timestamp}.state"

    cp "$session_file" "$archive_file" || {
        echo "ERROR: Failed to archive session" >&2
        return 1
    }

    # Compress if old (>30 days)
    local file_age=$(($(date +%s) - $(stat -c %Y "$session_file" 2>/dev/null || echo "0")))
    if (( file_age > 2592000 )); then
        gzip "$archive_file" 2>/dev/null || true
    fi

    echo "Session archived: $archive_file"
}

# ============================================================================
# State history
# ============================================================================

ce_state_get_history() {
    # Get state change history
    # Returns: List of archived sessions

    ls -1t "${CE_HISTORY_DIR}"/*.state* 2>/dev/null | head -20 | while read -r f; do
        local fname=$(basename "$f")
        echo "$fname"
    done
}

ce_state_rollback() {
    # Rollback state to previous version
    # Usage: ce_state_rollback [--steps=1]

    local steps=1

    for arg in "$@"; do
        case "$arg" in
            --steps=*)
                steps="${arg#*=}"
                ;;
        esac
    done

    local backup=$(ls -1t "${CE_BACKUP_DIR}"/state_*.yml 2>/dev/null | sed -n "${steps}p")

    [[ -z "$backup" ]] && {
        echo "ERROR: No backup found at step ${steps}" >&2
        return 1
    }

    local backup_ts=$(basename "$backup" | sed 's/state_\(.*\)\.yml/\1/')
    ce_state_restore "$backup_ts"
}

# ============================================================================
# Context management
# ============================================================================

ce_context_save() {
    # Save current working context
    # Usage: ce_context_save "context_name"

    local context_name="$1"
    local context_dir="${CE_STATE_DIR}/contexts"

    mkdir -p "$context_dir"

    local context_file="${context_dir}/${context_name}.ctx"

    cat > "$context_file" <<EOF
branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
phase: $(cat .phase/current 2>/dev/null || echo "P0")
modified_files:
$(git status --porcelain 2>/dev/null | awk '{print "  - " $2}')
timestamp: $(date -Iseconds)
EOF

    echo "Context saved: $context_name"
}

ce_context_restore() {
    # Restore saved context
    # Usage: ce_context_restore "context_name"

    local context_name="$1"
    local context_file="${CE_STATE_DIR}/contexts/${context_name}.ctx"

    [[ ! -f "$context_file" ]] && {
        echo "ERROR: Context not found: $context_name" >&2
        return 1
    }

    echo "Context from $context_file:"
    cat "$context_file"

    # Note: Actual restoration would require git operations
    echo "INFO: Manual restoration required based on context above"
}

# ============================================================================
# Helper functions
# ============================================================================

ce_get_terminal_id() {
    # Generate or retrieve terminal ID
    # Uses tty device or creates a unique ID

    if [[ -n "${CE_TERMINAL_ID:-}" ]]; then
        echo "$CE_TERMINAL_ID"
        return 0
    fi

    # Use tty device name
    local tty_name=$(tty 2>/dev/null | sed 's|/dev/||g' | tr '/' '-')

    if [[ -n "$tty_name" && "$tty_name" != "not a tty" ]]; then
        echo "$tty_name"
    else
        # Fallback to process-based ID
        echo "term-$$"
    fi
}

ce_state_remove_terminal() {
    # Remove terminal from active list
    # Usage: ce_state_remove_terminal "terminal_id"

    local term_id="$1"

    if $HAS_YQ; then
        yq eval -i "del(.active_terminals[] | select(. == \"${term_id}\"))" "${CE_STATE_FILE}"
    fi
}

# ============================================================================
# Lock management
# ============================================================================

ce_state_acquire_lock() {
    # Acquire file lock to prevent race conditions
    # Usage: ce_state_acquire_lock "lock_name" [timeout_seconds]

    local lock_name="$1"
    local timeout="${2:-30}"
    local lock_file="${CE_LOCK_DIR}/${lock_name}.lock"
    local start_time=$(date +%s)

    while true; do
        # Try to create lock file atomically
        if mkdir "$lock_file" 2>/dev/null; then
            echo $$ > "${lock_file}/pid"
            echo "$(date -Iseconds)" > "${lock_file}/timestamp"
            return 0
        fi

        # Check timeout
        local current_time=$(date +%s)
        if (( current_time - start_time >= timeout )); then
            echo "ERROR: Lock timeout for ${lock_name}" >&2
            return 1
        fi

        # Check if lock is stale (older than 5 minutes)
        if [[ -f "${lock_file}/timestamp" ]]; then
            local lock_ts=$(cat "${lock_file}/timestamp")
            local lock_age=$((current_time - $(date -d "$lock_ts" +%s 2>/dev/null || echo "$current_time")))

            if (( lock_age > 300 )); then
                echo "WARNING: Removing stale lock for ${lock_name}" >&2
                rm -rf "$lock_file"
                continue
            fi
        fi

        sleep 0.5
    done
}

ce_state_release_lock() {
    # Release file lock
    # Usage: ce_state_release_lock "lock_name"

    local lock_name="$1"
    local lock_file="${CE_LOCK_DIR}/${lock_name}.lock"

    if [[ -d "$lock_file" ]]; then
        rm -rf "$lock_file"
    fi
}

# ============================================================================
# Export functions
# ============================================================================

export -f ce_state_init
export -f ce_state_validate
export -f ce_state_save
export -f ce_state_load
export -f ce_state_get
export -f ce_state_set
export -f ce_state_backup
export -f ce_state_restore
export -f ce_state_create_session
export -f ce_state_get_session
export -f ce_state_load_session
export -f ce_state_save_session
export -f ce_state_update_session
export -f ce_state_list_sessions
export -f ce_state_activate_session
export -f ce_state_pause_session
export -f ce_state_resume_session
export -f ce_state_close_session
export -f ce_state_get_metadata
export -f ce_state_set_metadata
export -f ce_state_add_commit
export -f ce_state_get_commits
export -f ce_state_get_duration
export -f ce_state_get_stats
export -f ce_state_cleanup_stale
export -f ce_state_archive_session
export -f ce_state_get_history
export -f ce_state_rollback
export -f ce_context_save
export -f ce_context_restore
export -f ce_get_terminal_id
export -f ce_state_acquire_lock
export -f ce_state_release_lock
