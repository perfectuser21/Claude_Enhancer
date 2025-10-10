#!/usr/bin/env bash
set -euo pipefail

# Merge Lock Mechanism for Concurrent PR Merging
# Ensures FIFO serial merging when multiple PRs pass checks simultaneously

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
fail(){ echo -e "${RED}✗ $*${NC}"; exit 1; }
ok(){ echo -e "${GREEN}✓ $*${NC}"; }
warn(){ echo -e "${YELLOW}⚠ $*${NC}"; }
info(){ echo -e "${BLUE}ℹ $*${NC}"; }

# Configuration
LOCK_TIMEOUT=300  # 5 minutes max wait
RETRY_INTERVAL=10 # 10 seconds between retries
PROJECT_ROOT=$(git rev-parse --show-toplevel)
LOCK_DIR="${PROJECT_ROOT}/.workflow/locks"
LOCK_FILE="${LOCK_DIR}/merge.lock"

# Create locks directory
mkdir -p "${LOCK_DIR}"

# ============================================================================
# LOCK ACQUISITION
# ============================================================================

acquire_lock() {
    local pr_number="$1"
    local start_time=$(date +%s)
    local elapsed=0

    info "Attempting to acquire merge lock for PR #${pr_number}..."

    while [ $elapsed -lt $LOCK_TIMEOUT ]; do
        # Try to create lock file atomically
        if mkdir "${LOCK_FILE}" 2>/dev/null; then
            # Lock acquired successfully
            echo "${pr_number}" > "${LOCK_FILE}/pr_number"
            echo "$(date -Iseconds)" > "${LOCK_FILE}/timestamp"
            echo "$$" > "${LOCK_FILE}/pid"
            echo "$(whoami)" > "${LOCK_FILE}/user"

            ok "Merge lock acquired for PR #${pr_number}"
            return 0
        fi

        # Lock already exists, check if it's stale
        if [ -f "${LOCK_FILE}/timestamp" ]; then
            local lock_time=$(cat "${LOCK_FILE}/timestamp")
            local lock_pr=$(cat "${LOCK_FILE}/pr_number" 2>/dev/null || echo "unknown")
            local lock_age=$(( $(date +%s) - $(date -d "$lock_time" +%s 2>/dev/null || echo 0) ))

            if [ $lock_age -gt $LOCK_TIMEOUT ]; then
                warn "Stale lock detected (age: ${lock_age}s, PR: #${lock_pr})"
                warn "Removing stale lock and retrying..."
                release_lock_force
                continue
            fi

            warn "Lock held by PR #${lock_pr} (age: ${lock_age}s)"
        else
            warn "Lock exists but appears corrupted"
        fi

        # Wait and retry
        info "Waiting ${RETRY_INTERVAL}s before retry... (${elapsed}/${LOCK_TIMEOUT}s elapsed)"
        sleep $RETRY_INTERVAL

        elapsed=$(( $(date +%s) - start_time ))
    done

    fail "Failed to acquire merge lock after ${LOCK_TIMEOUT}s timeout"
}

# ============================================================================
# LOCK RELEASE
# ============================================================================

release_lock() {
    local pr_number="$1"

    if [ ! -d "${LOCK_FILE}" ]; then
        warn "Lock file does not exist (already released?)"
        return 0
    fi

    local lock_pr=$(cat "${LOCK_FILE}/pr_number" 2>/dev/null || echo "unknown")

    if [ "$lock_pr" != "$pr_number" ]; then
        warn "Lock is held by different PR (#${lock_pr} vs #${pr_number})"
        return 1
    fi

    rm -rf "${LOCK_FILE}"
    ok "Merge lock released for PR #${pr_number}"
}

release_lock_force() {
    rm -rf "${LOCK_FILE}"
    warn "Merge lock force-released"
}

# ============================================================================
# LOCK STATUS
# ============================================================================

check_lock_status() {
    if [ ! -d "${LOCK_FILE}" ]; then
        echo "Status: 🟢 No active merge lock"
        return 0
    fi

    local lock_pr=$(cat "${LOCK_FILE}/pr_number" 2>/dev/null || echo "unknown")
    local lock_time=$(cat "${LOCK_FILE}/timestamp" 2>/dev/null || echo "unknown")
    local lock_pid=$(cat "${LOCK_FILE}/pid" 2>/dev/null || echo "unknown")
    local lock_user=$(cat "${LOCK_FILE}/user" 2>/dev/null || echo "unknown")

    echo "Status: 🔴 Merge lock ACTIVE"
    echo "  • PR: #${lock_pr}"
    echo "  • Acquired: ${lock_time}"
    echo "  • PID: ${lock_pid}"
    echo "  • User: ${lock_user}"

    if [ "$lock_time" != "unknown" ]; then
        local lock_age=$(( $(date +%s) - $(date -d "$lock_time" +%s 2>/dev/null || echo 0) ))
        echo "  • Age: ${lock_age}s"

        if [ $lock_age -gt $LOCK_TIMEOUT ]; then
            warn "Lock appears stale (age: ${lock_age}s > timeout: ${LOCK_TIMEOUT}s)"
            echo "  • Recommendation: Run 'merge_lock.sh force-release' to clear stale lock"
        fi
    fi

    return 1
}

# ============================================================================
# MERGE EXECUTION WITH LOCK
# ============================================================================

merge_with_lock() {
    local pr_number="$1"
    local merge_method="${2:-squash}"  # squash, merge, or rebase

    info "Starting locked merge for PR #${pr_number} (method: ${merge_method})"

    # Acquire lock (with retry)
    acquire_lock "$pr_number" || fail "Failed to acquire lock"

    # Ensure lock is released on exit
    trap "release_lock $pr_number" EXIT INT TERM

    # Perform merge
    info "Executing merge..."
    if gh pr merge "$pr_number" --"${merge_method}" --auto; then
        ok "Merge initiated successfully"
    else
        fail "Merge command failed"
    fi

    # Lock will be automatically released by trap
    ok "Merge operation complete for PR #${pr_number}"
}

# ============================================================================
# USAGE AND MAIN
# ============================================================================

usage() {
    cat <<EOF
Usage: $0 <command> [arguments]

Commands:
    acquire <pr_number>           Acquire merge lock
    release <pr_number>           Release merge lock
    force-release                 Force release lock (use for stale locks)
    status                        Check lock status
    merge <pr_number> [method]    Merge PR with lock (method: squash|merge|rebase)

Examples:
    # Acquire lock manually
    $0 acquire 123

    # Release lock manually
    $0 release 123

    # Check lock status
    $0 status

    # Merge PR with automatic lock management
    $0 merge 123 squash

    # Force release stale lock
    $0 force-release

Environment Variables:
    LOCK_TIMEOUT      Lock timeout in seconds (default: 300)
    RETRY_INTERVAL    Retry interval in seconds (default: 10)

Notes:
    - Locks automatically expire after LOCK_TIMEOUT seconds
    - Stale locks are detected and can be force-released
    - Use 'merge' command for automatic lock management
    - Lock directory: .workflow/locks/
EOF
    exit 0
}

main() {
    local command="${1:-}"

    if [ -z "$command" ]; then
        usage
    fi

    case "$command" in
        acquire)
            local pr_number="${2:-}"
            [ -z "$pr_number" ] && fail "PR number required"
            acquire_lock "$pr_number"
            ;;
        release)
            local pr_number="${2:-}"
            [ -z "$pr_number" ] && fail "PR number required"
            release_lock "$pr_number"
            ;;
        force-release)
            release_lock_force
            ;;
        status)
            check_lock_status
            ;;
        merge)
            local pr_number="${2:-}"
            local merge_method="${3:-squash}"
            [ -z "$pr_number" ] && fail "PR number required"
            merge_with_lock "$pr_number" "$merge_method"
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            fail "Unknown command: $command (use --help for usage)"
            ;;
    esac
}

main "$@"
