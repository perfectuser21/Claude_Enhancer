#!/usr/bin/env bash
# Rollback Script for Claude Enhancer v5.4.0
# Purpose: Automated rollback to previous stable version
# Used by: P6 deployment, emergency recovery

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"

# Configuration
ROLLBACK_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_RETRIES=5
HEALTH_CHECK_DELAY=10  # seconds

# Functions

get_previous_version() {
    # Get the tag before the current one
    local current_version=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

    if [[ -z "$current_version" ]]; then
        log_error "No tags found in repository"
        return 1
    fi

    local previous_version=$(git describe --tags --abbrev=0 "${current_version}^" 2>/dev/null || echo "")

    if [[ -z "$previous_version" ]]; then
        log_error "No previous version found before $current_version"
        return 1
    fi

    echo "$previous_version"
}

check_health() {
    local health_script="${1:-observability/probes/healthcheck.sh}"

    if [[ ! -f "$health_script" ]]; then
        log_warning "Health check script not found: $health_script"
        return 0  # Assume healthy if no script
    fi

    log_info "Running health check..."
    if bash "$health_script"; then
        log_success "Health check passed"
        return 0
    else
        log_error "Health check failed"
        return 1
    fi
}

perform_rollback() {
    local target_version="${1:-auto}"
    local reason="${2:-Manual rollback}"

    log_info "========================================="
    log_info "         ROLLBACK INITIATED"
    log_info "========================================="
    log_info "Reason: $reason"
    log_info "Time: $(date)"
    log_info ""

    # Determine target version
    if [[ "$target_version" == "auto" ]]; then
        target_version=$(get_previous_version)
        log_info "Auto-detected target version: $target_version"
    fi

    # Verify target version exists
    if ! git rev-parse "$target_version" &>/dev/null; then
        die "Target version not found: $target_version"
    fi

    # Get current branch
    local current_branch=$(get_current_branch)
    log_info "Current branch: $current_branch"

    # Ensure on main/master
    if ! is_main_branch "$current_branch"; then
        log_warning "Not on main/master branch"
        log_info "Switching to $(get_default_branch)..."
        git checkout "$(get_default_branch)"
    fi

    # Backup current state
    local backup_branch="rollback-backup-$(date +%Y%m%d-%H%M%S)"
    log_info "Creating backup branch: $backup_branch"
    git branch "$backup_branch"

    # Perform rollback
    log_info "Rolling back to $target_version..."

    # Option 1: Hard reset (destructive but clean)
    # git reset --hard "$target_version"

    # Option 2: Revert (non-destructive, creates new commit)
    if git revert --no-commit "${target_version}..HEAD"; then
        git commit -m "chore(rollback): Rollback to $target_version

Reason: $reason
Previous backup: $backup_branch
Timestamp: $(date --iso-8601=seconds)

This rollback was performed automatically by Claude Enhancer v5.4.0"
        log_success "Rollback commit created"
    else
        log_error "Rollback failed - conflicts detected"
        git revert --abort
        die "Manual intervention required"
    fi

    # Push rollback
    log_info "Pushing rollback to remote..."
    if git push origin "$(get_current_branch)"; then
        log_success "Rollback pushed successfully"
    else
        log_error "Failed to push rollback"
        return 1
    fi

    # Wait for deployment
    log_info "Waiting for deployment to stabilize..."
    sleep 30

    # Verify health
    log_info "Verifying system health..."
    local attempt=1
    while [[ $attempt -le $HEALTH_CHECK_RETRIES ]]; do
        if check_health; then
            log_success "System healthy after rollback"

            log_info ""
            log_info "========================================="
            log_info "    ROLLBACK COMPLETED SUCCESSFULLY"
            log_info "========================================="
            log_info "Target version: $target_version"
            log_info "Backup branch: $backup_branch"
            log_info "Duration: $SECONDS seconds"
            log_info ""

            return 0
        fi

        log_warning "Health check failed (attempt $attempt/$HEALTH_CHECK_RETRIES)"
        if [[ $attempt -lt $HEALTH_CHECK_RETRIES ]]; then
            log_info "Retrying in ${HEALTH_CHECK_DELAY}s..."
            sleep "$HEALTH_CHECK_DELAY"
        fi

        attempt=$((attempt + 1))
    done

    log_error "System unhealthy after rollback"
    log_error "Manual intervention required"
    log_info "Backup branch available: $backup_branch"

    return 1
}

show_rollback_plan() {
    local target_version="${1:-auto}"

    if [[ "$target_version" == "auto" ]]; then
        target_version=$(get_previous_version)
    fi

    local current_version=$(git describe --tags --abbrev=0 2>/dev/null || echo "unknown")

    echo "========================================="
    echo "         ROLLBACK PLAN"
    echo "========================================="
    echo ""
    echo "Current version: $current_version"
    echo "Target version:  $target_version"
    echo ""
    echo "Commits to be reverted:"
    git log --oneline --no-merges "${target_version}..HEAD" | head -20
    echo ""
    echo "Files affected:"
    git diff --name-only "${target_version}..HEAD" | wc -l | xargs echo
    echo ""
    echo "========================================="
}

# Main execution
main() {
    local action="${1:-plan}"
    shift || true

    case "$action" in
        execute)
            local target_version="${1:-auto}"
            local reason="${2:-Manual rollback}"
            perform_rollback "$target_version" "$reason"
            ;;
        plan)
            local target_version="${1:-auto}"
            show_rollback_plan "$target_version"
            ;;
        health)
            check_health
            ;;
        *)
            echo "Usage: $0 {execute|plan|health} [version] [reason]"
            echo ""
            echo "Actions:"
            echo "  execute [version] [reason]  - Perform rollback (default: auto-detect)"
            echo "  plan [version]              - Show rollback plan"
            echo "  health                      - Check system health"
            echo ""
            echo "Examples:"
            echo "  $0 plan                                    # Show plan for auto-rollback"
            echo "  $0 plan v5.3.5                            # Show plan for specific version"
            echo "  $0 execute                                # Execute auto-rollback"
            echo "  $0 execute v5.3.5 \"Critical bug found\"    # Rollback to specific version"
            exit 1
            ;;
    esac
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
