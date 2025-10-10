#!/usr/bin/env bash
# Auto Push Script for Claude Enhancer v5.4.0
# Purpose: Automated git push with pre-push validation
# Used by: Claude automation, P6 release workflow

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"

# Configuration
FORCE_PUSH="${CE_FORCE_PUSH:-0}"
DRY_RUN="${CE_DRY_RUN:-0}"

# Functions

check_push_safety() {
    local branch="$1"

    # Prevent force push to protected branches
    if is_main_branch "$branch" && [[ "$FORCE_PUSH" == "1" ]]; then
        log_error "Force push to main/master is not allowed"
        return 1
    fi

    # Check if branch has upstream
    if ! git rev-parse --abbrev-ref "@{upstream}" &> /dev/null; then
        log_info "No upstream configured, will set on first push"
    fi

    # Check for diverged branches
    if git rev-parse --abbrev-ref "@{upstream}" &> /dev/null; then
        local upstream_commits=$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo "0")
        local local_commits=$(git rev-list --count "HEAD..@{u}" 2>/dev/null || echo "0")

        if [[ "$local_commits" -gt 0 ]]; then
            log_warning "Local branch is behind remote by $local_commits commits"
            log_info "Consider pulling or rebasing first"
        fi

        log_info "Pushing $upstream_commits new commits"
    fi

    return 0
}

run_prepush_checks() {
    # Run pre-push hook if exists
    if [[ -x ".git/hooks/pre-push" ]]; then
        log_info "Running pre-push checks..."
        if CE_AUTO_PUSH=1 .git/hooks/pre-push; then
            log_success "Pre-push checks passed"
        else
            log_error "Pre-push checks failed"
            return 1
        fi
    else
        log_warning "pre-push hook not found, skipping validation"
    fi

    return 0
}

perform_push() {
    local branch="$1"
    local force="${2:-0}"

    # Check safety
    check_push_safety "$branch" || return 1

    # Run pre-push checks
    run_prepush_checks || return 1

    # Determine push flags
    local push_flags=()
    if ! git rev-parse --abbrev-ref "@{upstream}" &> /dev/null; then
        push_flags+=("--set-upstream" "origin" "$branch")
        log_info "Setting upstream to origin/$branch"
    fi

    if [[ "$force" == "1" ]] && ! is_main_branch "$branch"; then
        push_flags+=("--force-with-lease")
        log_warning "Force pushing with lease protection"
    fi

    # Dry run mode
    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would push to origin/$branch with flags: ${push_flags[*]}"
        return 0
    fi

    # Perform push
    log_info "Pushing to origin/$branch..."
    if git push "${push_flags[@]}"; then
        log_success "Push completed successfully"
        log_info "View on GitHub: $(get_branch_url "$branch")"
        return 0
    else
        log_error "Push failed"
        return 1
    fi
}

get_branch_url() {
    local branch="$1"
    local remote_url=$(git config --get remote.origin.url)

    # Convert git URL to https
    if [[ "$remote_url" =~ ^git@ ]]; then
        remote_url=$(echo "$remote_url" | sed 's|git@github.com:|https://github.com/|' | sed 's|\.git$||')
    fi

    echo "${remote_url}/tree/${branch}"
}

# Main execution
main() {
    local branch="${1:-$(get_current_branch)}"
    local force="${CE_FORCE_PUSH:-0}"

    log_info "Preparing to push branch: $branch"

    # Check environment
    check_environment

    # Perform push
    perform_push "$branch" "$force"
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
