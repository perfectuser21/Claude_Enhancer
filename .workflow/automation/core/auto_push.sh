#!/usr/bin/env bash
# Auto Push Script for Claude Enhancer v5.4.0
# Purpose: Automated git push with pre-push validation and safety checks
# Used by: Claude automation, P6 release workflow
# Tier: 2 (Medium Risk - Conditional automation)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"
# shellcheck source=../security/audit_log.sh
source "${SCRIPT_DIR}/../security/audit_log.sh"

# Configuration
FORCE_PUSH="${CE_FORCE_PUSH:-0}"
DRY_RUN="${CE_DRY_RUN:-0}"
AUTO_PUSH="${CE_AUTO_PUSH:-0}"
PUSH_TAGS="${CE_PUSH_TAGS:-0}"

# Protected branches (never allow force push)
declare -a PROTECTED_BRANCHES=("main" "master" "production" "staging")

# ============================================================
# SAFETY CHECK FUNCTIONS
# ============================================================

check_push_safety() {
    local branch="$1"
    local force="${2:-0}"

    log_debug "Checking push safety for branch: $branch (force=$force)"

    # Rule 1: Never force push to protected branches
    if is_protected_branch "$branch" && [[ "$force" == "1" ]]; then
        log_error "Force push to protected branch '$branch' is not allowed"
        audit_security_event "force_push_attempt_protected" "CRITICAL" "Attempted force push to $branch"
        return 1
    fi

    # Rule 2: Warn about force push to any branch
    if [[ "$force" == "1" ]]; then
        log_warning "Force push requested for branch: $branch"
        audit_git_operation "force_push_check" "$branch" "warning" "Force push enabled"
    fi

    # Rule 3: Check if branch has upstream
    if ! git rev-parse --abbrev-ref "@{upstream}" &> /dev/null; then
        log_info "No upstream configured, will set on first push"
        audit_git_operation "upstream_check" "$branch" "no_upstream" "Will set upstream on push"
    else
        # Rule 4: Check for diverged branches
        check_branch_divergence "$branch" || return 1
    fi

    # Rule 5: Check for unpushed commits
    local unpushed_count=$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo "0")
    if [[ "$unpushed_count" -eq 0 ]]; then
        log_warning "No unpushed commits detected"
        return 0
    fi

    log_info "Ready to push $unpushed_count new commit(s)"
    return 0
}

is_protected_branch() {
    local branch="$1"

    for protected in "${PROTECTED_BRANCHES[@]}"; do
        if [[ "$branch" == "$protected" ]]; then
            return 0
        fi
    done

    return 1
}

check_branch_divergence() {
    local branch="$1"

    # Check commits ahead and behind
    local ahead=$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo "0")
    local behind=$(git rev-list --count "HEAD..@{u}" 2>/dev/null || echo "0")

    log_debug "Branch divergence: ahead=$ahead, behind=$behind"

    # If behind remote, recommend pulling
    if [[ "$behind" -gt 0 ]]; then
        log_warning "Local branch is behind remote by $behind commit(s)"
        log_warning "Remote has changes that you don't have locally"

        # Show remote commits
        log_info "Remote commits:"
        git log --oneline HEAD..@{u} 2>/dev/null | head -5 | while read -r line; do
            log_info "  $line"
        done

        if [[ "$FORCE_PUSH" != "1" ]]; then
            log_error "Please pull or rebase before pushing"
            log_info "Commands:"
            log_info "  git pull --rebase  # Recommended"
            log_info "  git pull           # Alternative"
            audit_git_operation "divergence_check" "$branch" "failed" "Behind by $behind commits"
            return 1
        else
            log_warning "Force push will overwrite remote commits (--force-with-lease)"
        fi
    fi

    if [[ "$ahead" -gt 0 ]]; then
        log_info "Local branch is ahead of remote by $ahead commit(s)"

        # Show local commits to be pushed
        log_info "Commits to be pushed:"
        git log --oneline @{u}..HEAD 2>/dev/null | while read -r line; do
            log_info "  $line"
        done
    fi

    return 0
}

check_upstream_tracking() {
    local branch="$1"

    if git rev-parse --abbrev-ref "@{upstream}" &> /dev/null; then
        local upstream=$(git rev-parse --abbrev-ref "@{upstream}")
        log_debug "Upstream tracking: $upstream"
        return 0
    else
        log_debug "No upstream tracking configured"
        return 1
    fi
}

setup_upstream_tracking() {
    local branch="$1"
    local remote="${2:-origin}"

    log_info "Setting upstream to $remote/$branch"

    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would set upstream to $remote/$branch"
        return 0
    fi

    # Set upstream will be done during push with --set-upstream
    audit_git_operation "setup_upstream" "$branch" "pending" "Will set to $remote/$branch"
    return 0
}

# ============================================================
# PRE-PUSH VALIDATION
# ============================================================

run_prepush_checks() {
    local branch="$1"

    log_info "Running pre-push validation checks..."

    # Check 1: Verify working directory is clean
    if ! git diff-index --quiet HEAD --; then
        log_warning "Working directory has uncommitted changes"
        log_warning "These changes will not be pushed"

        if [[ "${CE_STRICT_MODE:-0}" == "1" ]]; then
            log_error "Strict mode: commit all changes before pushing"
            return 1
        fi
    fi

    # Check 2: Run pre-push hook if exists
    if [[ -x ".git/hooks/pre-push" ]]; then
        log_info "Running pre-push hook..."

        # Set environment variable to indicate automation
        if CE_AUTO_PUSH=1 .git/hooks/pre-push origin "refs/heads/$branch" < /dev/null; then
            log_success "Pre-push hook passed"
            audit_git_operation "prepush_hook" "$branch" "success" "Hook validation passed"
        else
            log_error "Pre-push hook failed"
            audit_git_operation "prepush_hook" "$branch" "failed" "Hook validation failed"
            return 1
        fi
    else
        log_warning "pre-push hook not found, skipping validation"
    fi

    # Check 3: Verify no merge conflicts
    if git ls-files -u | grep -q .; then
        log_error "Unresolved merge conflicts detected"
        log_error "Resolve conflicts before pushing"
        return 1
    fi

    # Check 4: Check for TODO/FIXME in commits (optional)
    if [[ "${CE_BLOCK_TODO:-0}" == "1" ]]; then
        local todo_count=$(git diff @{u}..HEAD | grep -c "TODO\|FIXME" || true)
        if [[ "$todo_count" -gt 0 ]]; then
            log_warning "Found $todo_count TODO/FIXME comment(s) in new commits"

            if [[ "${CE_STRICT_MODE:-0}" == "1" ]]; then
                log_error "Strict mode: resolve TODOs before pushing"
                return 1
            fi
        fi
    fi

    log_success "All pre-push checks passed"
    return 0
}

# ============================================================
# PUSH OPERATIONS
# ============================================================

perform_push() {
    local branch="$1"
    local force="${2:-0}"
    local remote="${3:-origin}"

    log_info "Preparing to push branch '$branch' to '$remote'"

    # Safety checks
    check_push_safety "$branch" "$force" || return 1

    # Pre-push validation
    run_prepush_checks "$branch" || return 1

    # Build push command and flags
    local push_cmd="git push"
    local push_flags=()

    # Set upstream if not configured
    if ! check_upstream_tracking "$branch"; then
        push_flags+=("--set-upstream" "$remote" "$branch")
        log_info "Will set upstream to $remote/$branch"
    fi

    # Handle force push
    if [[ "$force" == "1" ]]; then
        if is_protected_branch "$branch"; then
            log_error "Cannot force push to protected branch: $branch"
            return 1
        fi

        # Use --force-with-lease for safety
        push_flags+=("--force-with-lease")
        log_warning "Using force push with lease protection"
        audit_security_event "force_push" "HIGH" "Force push to $branch with --force-with-lease"
    fi

    # Add tags if requested
    if [[ "$PUSH_TAGS" == "1" ]]; then
        push_flags+=("--follow-tags")
        log_info "Will push tags with commits"
    fi

    # Show push summary
    show_push_summary "$branch" "$remote"

    # Dry run mode
    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would execute:"
        log_info "  $push_cmd ${push_flags[*]}"
        audit_git_operation "push" "$branch" "dry_run" "Flags: ${push_flags[*]}"
        return 0
    fi

    # Perform the push
    log_info "Pushing to $remote/$branch..."
    audit_git_operation "push_attempt" "$branch" "started" "Remote: $remote, Force: $force"

    if git push "${push_flags[@]}"; then
        log_success "Push completed successfully"

        # Get push statistics
        local pushed_commits=$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo "0")

        # Show branch URL
        local branch_url=$(get_branch_url "$branch" "$remote")
        if [[ -n "$branch_url" ]]; then
            log_info "View on GitHub: $branch_url"
        fi

        # Audit successful push
        audit_git_operation "push" "$branch" "success" "Remote: $remote, Commits: $pushed_commits"

        # Show next steps
        show_next_steps "$branch"

        return 0
    else
        local exit_code=$?
        log_error "Push failed with exit code: $exit_code"

        # Provide troubleshooting guidance
        provide_push_failure_guidance "$exit_code" "$branch"

        audit_git_operation "push" "$branch" "failed" "Exit code: $exit_code"
        return 1
    fi
}

show_push_summary() {
    local branch="$1"
    local remote="$2"

    echo ""
    log_info "╔════════════════════════════════════════╗"
    log_info "║         Push Summary                   ║"
    log_info "╠════════════════════════════════════════╣"

    # Branch info
    log_info "  Branch:  $branch"
    log_info "  Remote:  $remote"

    # Commits to push
    if check_upstream_tracking "$branch"; then
        local ahead=$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo "0")
        log_info "  Commits: $ahead"

        if [[ "$ahead" -gt 0 ]]; then
            echo ""
            log_info "  Recent commits:"
            git log --oneline @{u}..HEAD | head -3 | while read -r line; do
                log_info "    $line"
            done
        fi
    else
        local total=$(git rev-list --count HEAD 2>/dev/null || echo "0")
        log_info "  Commits: $total (initial push)"
    fi

    log_info "╚════════════════════════════════════════╝"
    echo ""
}

show_next_steps() {
    local branch="$1"

    if ! is_protected_branch "$branch"; then
        echo ""
        log_info "Next steps:"
        log_info "  1. Create a pull request:"
        log_info "     ${SCRIPT_DIR}/auto_pr.sh"
        log_info ""
        log_info "  2. Or merge directly (if allowed):"
        log_info "     git checkout main && git merge $branch"
    fi
}

provide_push_failure_guidance() {
    local exit_code="$1"
    local branch="$2"

    echo ""
    log_info "Troubleshooting:"

    case "$exit_code" in
        1)
            log_info "  - Check network connectivity"
            log_info "  - Verify remote repository access"
            log_info "  - Check if branch is protected"
            ;;
        128)
            log_info "  - Remote may have rejected the push"
            log_info "  - Check branch protection rules"
            log_info "  - Verify you have write access"
            ;;
        *)
            log_info "  - Run: git push --verbose for more details"
            log_info "  - Check: git remote -v"
            log_info "  - Verify: git status"
            ;;
    esac

    echo ""
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

get_branch_url() {
    local branch="$1"
    local remote="${2:-origin}"

    # Get remote URL
    local remote_url=$(git config --get "remote.${remote}.url" 2>/dev/null)

    if [[ -z "$remote_url" ]]; then
        return 1
    fi

    # Convert git URL to https
    if [[ "$remote_url" =~ ^git@github\.com:(.+)\.git$ ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/tree/${branch}"
    elif [[ "$remote_url" =~ ^https://github\.com/(.+)\.git$ ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/tree/${branch}"
    elif [[ "$remote_url" =~ ^https://github\.com/(.+)$ ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/tree/${branch}"
    else
        echo ""
    fi
}

check_remote_exists() {
    local remote="${1:-origin}"

    if git remote | grep -q "^${remote}$"; then
        return 0
    else
        log_error "Remote '$remote' does not exist"
        log_info "Available remotes:"
        git remote -v
        return 1
    fi
}

# ============================================================
# AUTOMATION MODE
# ============================================================

check_automation_mode() {
    # Check if automation is enabled
    if [[ "${CE_EXECUTION_MODE:-0}" != "1" ]]; then
        log_warning "Execution mode disabled"
        log_info "To enable automation: export CE_EXECUTION_MODE=1"
        return 1
    fi

    # Check if auto-push is enabled
    if [[ "$AUTO_PUSH" != "1" ]]; then
        log_info "Auto-push not enabled"
        log_info "To enable: export CE_AUTO_PUSH=1"
        return 1
    fi

    return 0
}

# ============================================================
# MAIN EXECUTION
# ============================================================

main() {
    local branch="${1:-$(get_current_branch)}"
    local force="${CE_FORCE_PUSH:-0}"
    local remote="${2:-origin}"

    log_info "Auto Push - Claude Enhancer v5.4.0"
    log_info "Branch: $branch"

    # Check environment
    check_environment || exit 1

    # Check if remote exists
    check_remote_exists "$remote" || exit 1

    # Perform push
    perform_push "$branch" "$force" "$remote"
}

# Show help
show_help() {
    cat <<EOF
Usage: $0 [branch] [remote]

Automated git push with comprehensive safety checks and validation.

Arguments:
  branch    Branch to push (default: current branch)
  remote    Remote to push to (default: origin)

Environment Variables:
  CE_EXECUTION_MODE=1    Enable automation mode
  CE_AUTO_PUSH=1         Enable automatic push (Tier 2)
  CE_FORCE_PUSH=1        Enable force push with --force-with-lease
  CE_PUSH_TAGS=1         Push tags along with commits
  CE_DRY_RUN=1           Dry run mode (show what would be done)
  CE_STRICT_MODE=1       Enable strict validation
  CE_BLOCK_TODO=1        Block push if TODOs found in commits

Examples:
  # Push current branch
  $0

  # Push specific branch
  $0 feature/authentication

  # Push to different remote
  $0 feature/auth upstream

  # Dry run to see what would happen
  CE_DRY_RUN=1 $0

  # Force push (feature branches only)
  CE_FORCE_PUSH=1 $0 feature/experimental

Safety Features:
  ✓ Branch divergence detection
  ✓ Protected branch checks
  ✓ Pre-push hook validation
  ✓ Force-with-lease for safety
  ✓ Audit logging
  ✓ Automatic upstream tracking

Protected Branches (no force push):
  - main
  - master
  - production
  - staging

Tier: 2 (Medium Risk - Requires CE_AUTO_PUSH=1)
EOF
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        show_help
        exit 0
    fi

    main "$@"
fi
