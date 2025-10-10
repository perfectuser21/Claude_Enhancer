#!/usr/bin/env bash
# git_operations.sh - Git operations with retry and safety
# Provides robust git operations with error handling
set -euo pipefail

# Source common utilities if not already loaded
if ! command -v ce_log_info &>/dev/null; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    # shellcheck source=./common.sh
    source "${SCRIPT_DIR}/common.sh"
fi

# Git configuration
CE_GIT_RETRY_COUNT=${CE_GIT_RETRY_COUNT:-3}
CE_GIT_RETRY_DELAY=${CE_GIT_RETRY_DELAY:-2}

# ============================================================================
# Basic Git Operations
# ============================================================================

ce_git_is_repo() {
    # Check if current directory is a git repository
    # Returns: 0 if git repo, 1 otherwise
    git rev-parse --git-dir &>/dev/null
}

ce_git_get_root() {
    # Get git repository root directory
    # Returns: Absolute path to repo root
    # Usage: root=$(ce_git_get_root)
    if ! ce_git_is_repo; then
        ce_log_error "Not a git repository"
        return 1
    fi

    git rev-parse --show-toplevel
}

ce_git_get_current_branch() {
    # Get current branch name
    # Returns: Branch name or empty if detached HEAD
    if ! ce_git_is_repo; then
        return 1
    fi

    git symbolic-ref --short HEAD 2>/dev/null || echo ""
}

ce_git_branch_exists() {
    # Check if branch exists (local or remote)
    # Usage: ce_git_branch_exists "feat/auth" [--remote]
    # Returns: 0 if exists, 1 otherwise
    local branch="${1:?Branch name required}"
    local check_remote=false

    # Parse options
    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --remote)
                check_remote=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    if [[ "${check_remote}" == true ]]; then
        # Check remote branch
        git ls-remote --heads origin "${branch}" 2>/dev/null | grep -q "${branch}"
    else
        # Check local branch
        git show-ref --verify --quiet "refs/heads/${branch}"
    fi
}

# ============================================================================
# Branch Operations
# ============================================================================

ce_git_create_branch() {
    # Create new branch
    # Options:
    #   --from=<branch>: Create from specific branch (default: current HEAD)
    #   --checkout: Checkout immediately after creation
    # Usage: ce_git_create_branch "feat/new-feature" [--from=main] [--checkout]
    # Returns: 0 on success
    local branch="${1:?Branch name required}"
    local from_branch=""
    local do_checkout=false

    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --from=*)
                from_branch="${1#*=}"
                shift
                ;;
            --checkout)
                do_checkout=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    # Validate branch name
    if ! git check-ref-format --branch "${branch}" &>/dev/null; then
        ce_log_error "Invalid branch name: ${branch}"
        return 1
    fi

    # Check if branch already exists
    if ce_git_branch_exists "${branch}"; then
        ce_log_error "Branch '${branch}' already exists"
        return 1
    fi

    # Create branch
    if [[ -n "${from_branch}" ]]; then
        ce_log_info "Creating branch '${branch}' from '${from_branch}'"
        git branch "${branch}" "${from_branch}"
    else
        ce_log_info "Creating branch '${branch}'"
        git branch "${branch}"
    fi

    # Checkout if requested
    if [[ "${do_checkout}" == true ]]; then
        ce_git_switch_branch "${branch}"
    fi

    ce_log_success "Branch '${branch}' created"
}

ce_git_switch_branch() {
    # Switch to branch with safety checks
    # Options:
    #   --stash: Automatically stash changes if dirty
    # Usage: ce_git_switch_branch "feat/auth" [--stash]
    # Returns: 0 on success
    local branch="${1:?Branch name required}"
    local auto_stash=false

    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --stash)
                auto_stash=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    # Check if branch exists
    if ! ce_git_branch_exists "${branch}"; then
        ce_log_error "Branch '${branch}' does not exist"
        return 1
    fi

    # Check for uncommitted changes
    if ce_git_has_changes; then
        if [[ "${auto_stash}" == true ]]; then
            ce_log_info "Stashing uncommitted changes"
            ce_git_stash_save "Auto-stash before switching to ${branch}"
        else
            ce_log_error "You have uncommitted changes. Use --stash or commit them first."
            return 1
        fi
    fi

    ce_log_info "Switching to branch '${branch}'"
    git checkout "${branch}"
    ce_log_success "Switched to branch '${branch}'"
}

ce_git_delete_branch() {
    # Delete branch with safety checks
    # Options:
    #   --force: Force delete even if unmerged
    #   --remote: Also delete from remote
    # Usage: ce_git_delete_branch "feat/old" [--force] [--remote]
    # Returns: 0 on success
    local branch="${1:?Branch name required}"
    local force=false
    local delete_remote=false

    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force)
                force=true
                shift
                ;;
            --remote)
                delete_remote=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    # Check if currently on the branch
    local current_branch
    current_branch=$(ce_git_get_current_branch)
    if [[ "${current_branch}" == "${branch}" ]]; then
        ce_log_error "Cannot delete current branch. Switch to another branch first."
        return 1
    fi

    # Delete local branch
    if [[ "${force}" == true ]]; then
        ce_log_info "Force deleting branch '${branch}'"
        git branch -D "${branch}"
    else
        ce_log_info "Deleting merged branch '${branch}'"
        git branch -d "${branch}"
    fi

    # Delete remote branch if requested
    if [[ "${delete_remote}" == true ]]; then
        if ce_git_branch_exists "${branch}" --remote; then
            ce_log_info "Deleting remote branch '${branch}'"
            git push origin --delete "${branch}"
        fi
    fi

    ce_log_success "Branch '${branch}' deleted"
}

ce_git_list_branches() {
    # List branches with optional filtering
    # Options:
    #   --local: Show only local branches
    #   --remote: Show only remote branches
    #   --merged: Show only merged branches
    #   --unmerged: Show only unmerged branches
    # Usage: ce_git_list_branches [--local] [--merged]
    # Returns: List of branch names
    local show_local=true
    local show_remote=false
    local filter_merged=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --local)
                show_local=true
                show_remote=false
                shift
                ;;
            --remote)
                show_local=false
                show_remote=true
                shift
                ;;
            --merged)
                filter_merged="--merged"
                shift
                ;;
            --unmerged)
                filter_merged="--no-merged"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    if [[ "${show_local}" == true ]]; then
        git branch ${filter_merged} | sed 's/^[* ]*//'
    fi

    if [[ "${show_remote}" == true ]]; then
        git branch -r ${filter_merged} | sed 's/^[* ]*//' | grep -v 'HEAD'
    fi
}

# ============================================================================
# Commit Operations
# ============================================================================

ce_git_commit() {
    # Create commit with validation
    # Validates:
    #   - Message format (conventional commits)
    #   - Changes staged
    # Usage: ce_git_commit "feat: add new feature" [--allow-empty]
    # Returns: Commit SHA
    local message="${1:?Commit message required}"
    local allow_empty=false

    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --allow-empty)
                allow_empty=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    # Check for staged changes (unless --allow-empty)
    if [[ "${allow_empty}" == false ]] && ! ce_git_has_staged; then
        ce_log_error "No changes staged for commit"
        return 1
    fi

    # Validate commit message format
    if ! ce_git_validate_commit_message "${message}"; then
        ce_log_error "Invalid commit message format"
        return 1
    fi

    # Create commit
    local commit_opts=()
    [[ "${allow_empty}" == true ]] && commit_opts+=("--allow-empty")

    git commit "${commit_opts[@]}" -m "${message}"

    # Return commit SHA
    git rev-parse HEAD
}

ce_git_amend() {
    # Amend last commit
    # Safety check: Ensure not pushed to remote
    # Usage: ce_git_amend [--message="new message"]
    # Returns: New commit SHA
    local new_message=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --message=*)
                new_message="${1#*=}"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    # Check if last commit has been pushed
    local current_branch
    current_branch=$(ce_git_get_current_branch)

    if git branch -r --contains HEAD | grep -q "origin/${current_branch}"; then
        ce_log_warn "Last commit has been pushed. Amending will require force push."
        if ! ce_confirm "Continue with amend?"; then
            return 1
        fi
    fi

    # Amend commit
    if [[ -n "${new_message}" ]]; then
        git commit --amend -m "${new_message}"
    else
        git commit --amend --no-edit
    fi

    # Return new commit SHA
    git rev-parse HEAD
}

ce_git_get_last_commit() {
    # Get last commit information
    # Returns JSON-like output
    local sha
    local message
    local author
    local date

    sha=$(git rev-parse HEAD)
    message=$(git log -1 --pretty=%s)
    author=$(git log -1 --pretty=%an)
    date=$(git log -1 --pretty=%ai)

    cat <<EOF
{
  "sha": "${sha}",
  "message": "${message}",
  "author": "${author}",
  "date": "${date}"
}
EOF
}

ce_git_list_commits() {
    # List commits with formatting
    # Usage: ce_git_list_commits [--since="2 days ago"] [--count=10]
    # Returns: Formatted commit list
    local since=""
    local count=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --since=*)
                since="${1#*=}"
                shift
                ;;
            --count=*)
                count="${1#*=}"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local opts=()
    [[ -n "${since}" ]] && opts+=("--since=${since}")
    [[ -n "${count}" ]] && opts+=("-n" "${count}")

    git log "${opts[@]}" --pretty=format:"%h - %s (%an, %ar)"
}

# ============================================================================
# Push/Pull Operations
# ============================================================================

ce_git_push() {
    # Push with retry logic
    # Features:
    #   - Set upstream if needed
    #   - Force with lease option
    # Usage: ce_git_push [--force-with-lease] [--set-upstream]
    # Returns: 0 on success
    local force_lease=false
    local set_upstream=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force-with-lease)
                force_lease=true
                shift
                ;;
            --set-upstream|-u)
                set_upstream=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local current_branch
    current_branch=$(ce_git_get_current_branch)

    local push_opts=()
    [[ "${force_lease}" == true ]] && push_opts+=("--force-with-lease")
    [[ "${set_upstream}" == true ]] && push_opts+=("--set-upstream" "origin" "${current_branch}")

    ce_log_info "Pushing to origin/${current_branch}"
    git push "${push_opts[@]}" origin "${current_branch}"
    ce_log_success "Push completed"
}

ce_git_push_with_retry() {
    # Push with exponential backoff retry
    # Retries on network errors, not on auth failures
    # Usage: ce_git_push_with_retry [branch_name]
    # Returns: 0 on success, 1 after max retries
    local branch="${1:-$(ce_git_get_current_branch)}"
    local retry_count=0
    local delay="${CE_GIT_RETRY_DELAY}"

    while [[ ${retry_count} -lt ${CE_GIT_RETRY_COUNT} ]]; do
        ce_log_info "Attempting push (attempt $((retry_count + 1))/${CE_GIT_RETRY_COUNT})"

        if git push origin "${branch}" 2>&1; then
            ce_log_success "Push successful"
            return 0
        fi

        local exit_code=$?

        # Don't retry on authentication failures or rejected pushes
        if [[ ${exit_code} -eq 128 ]]; then
            ce_log_error "Authentication failed or push rejected"
            return 1
        fi

        ((retry_count++))

        if [[ ${retry_count} -lt ${CE_GIT_RETRY_COUNT} ]]; then
            ce_log_warn "Push failed, retrying in ${delay} seconds..."
            sleep "${delay}"
            # Exponential backoff
            delay=$((delay * 2))
        fi
    done

    ce_log_error "Push failed after ${CE_GIT_RETRY_COUNT} attempts"
    return 1
}

ce_git_pull() {
    # Pull with conflict detection
    # Options:
    #   --rebase: Use rebase instead of merge
    #   --autostash: Automatically stash/unstash local changes
    # Usage: ce_git_pull [--rebase] [--autostash]
    # Returns: 0 on success, 1 on conflicts
    local use_rebase=false
    local autostash=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --rebase)
                use_rebase=true
                shift
                ;;
            --autostash)
                autostash=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local pull_opts=()
    [[ "${use_rebase}" == true ]] && pull_opts+=("--rebase")
    [[ "${autostash}" == true ]] && pull_opts+=("--autostash")

    ce_log_info "Pulling from remote"
    if git pull "${pull_opts[@]}" 2>&1; then
        ce_log_success "Pull completed successfully"
        return 0
    else
        ce_log_error "Pull failed with conflicts"
        return 1
    fi
}

ce_git_fetch() {
    # Fetch from remote
    # Usage: ce_git_fetch [--all] [--prune]
    # Returns: 0 on success
    local fetch_all=false
    local prune=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --all)
                fetch_all=true
                shift
                ;;
            --prune)
                prune=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local fetch_opts=()
    [[ "${fetch_all}" == true ]] && fetch_opts+=("--all")
    [[ "${prune}" == true ]] && fetch_opts+=("--prune")

    ce_log_info "Fetching from remote"
    git fetch "${fetch_opts[@]}"
    ce_log_success "Fetch completed"
}

# ============================================================================
# Remote Operations
# ============================================================================

ce_git_check_remote() {
    # Check if remote exists and is accessible
    # Usage: ce_git_check_remote [remote_name]
    # Returns: 0 if accessible, 1 otherwise
    local remote="${1:-origin}"

    # Check if remote is configured
    if ! git remote get-url "${remote}" &>/dev/null; then
        ce_log_error "Remote '${remote}' not configured"
        return 1
    fi

    # Check if remote is reachable
    ce_log_info "Checking connectivity to '${remote}'"
    if git ls-remote --exit-code "${remote}" &>/dev/null; then
        ce_log_success "Remote '${remote}' is accessible"
        return 0
    else
        ce_log_error "Cannot reach remote '${remote}'"
        return 1
    fi
}

ce_git_get_remote_url() {
    # Get remote URL
    # Usage: url=$(ce_git_get_remote_url [remote_name])
    # Returns: Remote URL
    local remote="${1:-origin}"

    git remote get-url "${remote}" 2>/dev/null || {
        ce_log_error "Remote '${remote}' not found"
        return 1
    }
}

ce_git_set_remote() {
    # Set or update remote URL
    # Usage: ce_git_set_remote "origin" "https://github.com/user/repo.git"
    # Returns: 0 on success
    local remote="${1:?Remote name required}"
    local url="${2:?Remote URL required}"

    if git remote get-url "${remote}" &>/dev/null; then
        ce_log_info "Updating remote '${remote}' to ${url}"
        git remote set-url "${remote}" "${url}"
    else
        ce_log_info "Adding remote '${remote}' as ${url}"
        git remote add "${remote}" "${url}"
    fi

    ce_log_success "Remote '${remote}' configured"
}

# ============================================================================
# Merge Operations
# ============================================================================

ce_git_merge() {
    # Merge branch with conflict handling
    # Usage: ce_git_merge "feat/branch" [--no-ff] [--squash]
    # Returns: 0 on success, 1 on conflicts
    local branch="${1:?Branch name required}"
    local no_ff=false
    local squash=false

    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-ff)
                no_ff=true
                shift
                ;;
            --squash)
                squash=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local merge_opts=()
    [[ "${no_ff}" == true ]] && merge_opts+=("--no-ff")
    [[ "${squash}" == true ]] && merge_opts+=("--squash")

    ce_log_info "Merging branch '${branch}'"
    if git merge "${merge_opts[@]}" "${branch}" 2>&1; then
        ce_log_success "Merge completed successfully"
        return 0
    else
        ce_log_error "Merge conflicts detected. Resolve conflicts and commit."
        return 1
    fi
}

ce_git_merge_base() {
    # Find merge base between branches
    # Usage: base=$(ce_git_merge_base "feat/branch" "main")
    # Returns: Commit SHA of merge base
    local branch1="${1:?First branch required}"
    local branch2="${2:?Second branch required}"

    git merge-base "${branch1}" "${branch2}"
}

ce_git_check_merge_conflicts() {
    # Check for potential merge conflicts
    # Simulates merge without modifying working tree
    # Usage: ce_git_check_merge_conflicts "feat/branch" "main"
    # Returns: 0 if clean, 1 with conflict files
    local source_branch="${1:?Source branch required}"
    local target_branch="${2:?Target branch required}"

    ce_log_info "Checking for merge conflicts between '${source_branch}' and '${target_branch}'"

    # Use merge tree to simulate merge
    if git merge-tree "$(ce_git_merge_base "${source_branch}" "${target_branch}")" \
        "${source_branch}" "${target_branch}" | grep -q "^changed in both"; then
        ce_log_warn "Potential merge conflicts detected"
        return 1
    else
        ce_log_success "No merge conflicts detected"
        return 0
    fi
}

ce_git_abort_merge() {
    # Abort in-progress merge
    # Restores to pre-merge state
    # Usage: ce_git_abort_merge
    if [[ -f .git/MERGE_HEAD ]]; then
        ce_log_info "Aborting merge"
        git merge --abort
        ce_log_success "Merge aborted"
    else
        ce_log_warn "No merge in progress"
    fi
}

# ============================================================================
# Rebase Operations
# ============================================================================

ce_git_rebase() {
    # Rebase current branch
    # Usage: ce_git_rebase "main" [--interactive]
    # Returns: 0 on success, 1 on conflicts
    local base_branch="${1:?Base branch required}"
    local interactive=false

    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --interactive|-i)
                interactive=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local rebase_opts=()
    [[ "${interactive}" == true ]] && rebase_opts+=("-i")

    ce_log_info "Rebasing onto '${base_branch}'"
    if git rebase "${rebase_opts[@]}" "${base_branch}" 2>&1; then
        ce_log_success "Rebase completed"
        return 0
    else
        ce_log_error "Rebase conflicts detected"
        return 1
    fi
}

ce_git_rebase_interactive() {
    # Start interactive rebase
    # Usage: ce_git_rebase_interactive [commit_count]
    local commit_count="${1:-5}"

    ce_log_info "Starting interactive rebase for last ${commit_count} commits"
    git rebase -i "HEAD~${commit_count}"
}

ce_git_abort_rebase() {
    # Abort in-progress rebase
    # Usage: ce_git_abort_rebase
    if [[ -d .git/rebase-merge ]] || [[ -d .git/rebase-apply ]]; then
        ce_log_info "Aborting rebase"
        git rebase --abort
        ce_log_success "Rebase aborted"
    else
        ce_log_warn "No rebase in progress"
    fi
}

# ============================================================================
# Status and Diff
# ============================================================================

ce_git_status() {
    # Get git status in structured format
    # Returns formatted status information
    local branch
    local ahead
    local behind

    branch=$(ce_git_get_current_branch)

    # Get ahead/behind info
    ahead=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
    behind=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo "0")

    # Get file status
    local staged=()
    local modified=()
    local untracked=()

    while IFS= read -r line; do
        [[ -z "${line}" ]] && continue
        local status="${line:0:2}"
        local file="${line:3}"

        case "${status}" in
            "A "*)
                staged+=("${file}")
                ;;
            "M "*)
                staged+=("${file}")
                ;;
            " M"*)
                modified+=("${file}")
                ;;
            "??"*)
                untracked+=("${file}")
                ;;
        esac
    done < <(git status --porcelain 2>/dev/null)

    # Output structured information
    cat <<EOF
{
  "branch": "${branch}",
  "ahead": ${ahead},
  "behind": ${behind},
  "staged": [$(ce_join ", " "${staged[@]+"${staged[@]}"}}")],
  "modified": [$(ce_join ", " "${modified[@]+"${modified[@]}"}}")],
  "untracked": [$(ce_join ", " "${untracked[@]+"${untracked[@]}"}"})]
}
EOF
}

ce_git_has_changes() {
    # Check if there are uncommitted changes
    # Returns: 0 if dirty, 1 if clean
    ! git diff-index --quiet HEAD -- 2>/dev/null
}

ce_git_has_staged() {
    # Check if there are staged changes
    # Returns: 0 if staged changes exist, 1 otherwise
    ! git diff-index --quiet --cached HEAD -- 2>/dev/null
}

ce_git_diff() {
    # Get diff output
    # Options:
    #   --staged: Show staged changes
    #   --branch=<name>: Compare against branch
    #   [files...]: Specific files to diff
    # Usage: ce_git_diff [--staged] [--branch=main] [file...]
    # Returns: Diff output
    local staged=false
    local compare_branch=""
    local files=()

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --staged)
                staged=true
                shift
                ;;
            --branch=*)
                compare_branch="${1#*=}"
                shift
                ;;
            *)
                files+=("$1")
                shift
                ;;
        esac
    done

    local diff_opts=()
    [[ "${staged}" == true ]] && diff_opts+=("--cached")

    if [[ -n "${compare_branch}" ]]; then
        git diff "${diff_opts[@]}" "${compare_branch}" "${files[@]+"${files[@]}"}"
    else
        git diff "${diff_opts[@]}" "${files[@]+"${files[@]}"}"
    fi
}

ce_git_diff_stat() {
    # Get diff statistics
    # Returns files changed, lines added/removed
    # Usage: ce_git_diff_stat "main"
    local compare_ref="${1:-HEAD}"

    git diff --stat "${compare_ref}"
}

# ============================================================================
# Stash Operations
# ============================================================================

ce_git_stash_save() {
    # Stash current changes
    # Usage: ce_git_stash_save ["message"]
    # Returns: Stash reference
    local message="${1:-WIP on $(ce_git_get_current_branch)}"

    ce_log_info "Stashing changes: ${message}"
    git stash push -m "${message}"

    # Return stash reference
    git stash list -1 --format="%gd"
}

ce_git_stash_pop() {
    # Pop most recent stash
    # Usage: ce_git_stash_pop
    # Returns: 0 on success, 1 on conflicts
    if ! git stash list | grep -q "stash@"; then
        ce_log_warn "No stashes found"
        return 1
    fi

    ce_log_info "Popping stash"
    if git stash pop; then
        ce_log_success "Stash applied successfully"
        return 0
    else
        ce_log_error "Conflicts while applying stash"
        return 1
    fi
}

ce_git_stash_list() {
    # List all stashes
    # Returns: Formatted stash list
    git stash list --format="%gd: %s"
}

ce_git_stash_clear() {
    # Clear all stashes
    # Usage: ce_git_stash_clear [--confirm]
    local need_confirm=true

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-confirm)
                need_confirm=false
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    if [[ "${need_confirm}" == true ]]; then
        if ! ce_confirm "Clear all stashes?"; then
            return 1
        fi
    fi

    ce_log_info "Clearing all stashes"
    git stash clear
    ce_log_success "Stashes cleared"
}

# ============================================================================
# Tag Operations
# ============================================================================

ce_git_create_tag() {
    # Create annotated tag
    # Usage: ce_git_create_tag "v1.0.0" "Release message" [--sign]
    # Returns: 0 on success
    local tag="${1:?Tag name required}"
    local message="${2:?Tag message required}"
    local sign=false

    shift 2 || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --sign|-s)
                sign=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local tag_opts=("-a" "-m" "${message}")
    [[ "${sign}" == true ]] && tag_opts+=("-s")

    ce_log_info "Creating tag '${tag}'"
    git tag "${tag_opts[@]}" "${tag}"
    ce_log_success "Tag '${tag}' created"
}

ce_git_list_tags() {
    # List tags with optional filtering
    # Usage: ce_git_list_tags [--pattern="v*"]
    # Returns: List of tags
    local pattern=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pattern=*)
                pattern="${1#*=}"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    if [[ -n "${pattern}" ]]; then
        git tag -l "${pattern}"
    else
        git tag
    fi
}

ce_git_delete_tag() {
    # Delete tag locally and remotely
    # Usage: ce_git_delete_tag "v1.0.0" [--remote]
    local tag="${1:?Tag name required}"
    local delete_remote=false

    shift || true
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --remote)
                delete_remote=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    ce_log_info "Deleting local tag '${tag}'"
    git tag -d "${tag}"

    if [[ "${delete_remote}" == true ]]; then
        ce_log_info "Deleting remote tag '${tag}'"
        git push origin --delete "refs/tags/${tag}"
    fi

    ce_log_success "Tag '${tag}' deleted"
}

# ============================================================================
# History Operations
# ============================================================================

ce_git_log() {
    # Get formatted git log
    # Usage: ce_git_log [--count=10] [--since="2 days ago"]
    # Returns: Formatted log
    local count=""
    local since=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --count=*)
                count="${1#*=}"
                shift
                ;;
            --since=*)
                since="${1#*=}"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local log_opts=("--pretty=format:%h - %s (%an, %ar)")
    [[ -n "${count}" ]] && log_opts+=("-n" "${count}")
    [[ -n "${since}" ]] && log_opts+=("--since=${since}")

    git log "${log_opts[@]}"
}

ce_git_log_since_branch_point() {
    # Get commits since branching from base
    # Usage: ce_git_log_since_branch_point "main"
    # Returns: Commits unique to current branch
    local base_branch="${1:-main}"
    local current_branch
    current_branch=$(ce_git_get_current_branch)

    git log "${base_branch}..${current_branch}" --pretty=format:"%h - %s"
}

ce_git_blame() {
    # Get blame for file
    # Usage: ce_git_blame "path/to/file"
    # Returns: Line-by-line blame info
    local file="${1:?File path required}"

    if [[ ! -f "${file}" ]]; then
        ce_log_error "File not found: ${file}"
        return 1
    fi

    git blame "${file}"
}

# ============================================================================
# Cleanup Operations
# ============================================================================

ce_git_clean() {
    # Clean untracked files
    # Safety: Requires confirmation unless --force
    # Usage: ce_git_clean [--dry-run] [--force]
    local dry_run=false
    local force=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                dry_run=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    if [[ "${dry_run}" == true ]]; then
        ce_log_info "Dry run - files that would be removed:"
        git clean -nfd
        return 0
    fi

    if [[ "${force}" == false ]]; then
        if ! ce_confirm "Remove all untracked files?"; then
            return 1
        fi
    fi

    ce_log_info "Cleaning untracked files"
    git clean -fd
    ce_log_success "Clean completed"
}

ce_git_gc() {
    # Run git garbage collection
    # Optimizes repository
    # Usage: ce_git_gc
    ce_log_info "Running garbage collection"
    git gc --auto
    ce_log_success "Garbage collection completed"
}

ce_git_prune() {
    # Prune remote tracking branches
    # Removes stale remote branches
    # Usage: ce_git_prune [remote_name]
    local remote="${1:-origin}"

    ce_log_info "Pruning stale remote branches from '${remote}'"
    git remote prune "${remote}"
    ce_log_success "Prune completed"
}

# ============================================================================
# Validation Operations
# ============================================================================

ce_git_validate_commit_message() {
    # Validate commit message format
    # Checks against conventional commits format
    # Usage: ce_git_validate_commit_message "feat: add feature"
    # Returns: 0 if valid, 1 with errors
    local message="${1:?Commit message required}"

    # Conventional commits pattern: type(scope): description
    local pattern="^(feat|fix|docs|style|refactor|perf|test|chore|build|ci)(\(.+\))?: .{1,}"

    if [[ "${message}" =~ ${pattern} ]]; then
        return 0
    else
        ce_log_error "Commit message does not follow conventional commits format"
        ce_log_error "Expected: type(scope): description"
        ce_log_error "Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci"
        return 1
    fi
}

ce_git_check_signed() {
    # Check if commits are signed
    # Usage: ce_git_check_signed [commit_range]
    # Returns: List of unsigned commits
    local commit_range="${1:-HEAD~10..HEAD}"

    ce_log_info "Checking for unsigned commits in ${commit_range}"

    local unsigned_commits=()
    while IFS= read -r commit; do
        if ! git verify-commit "${commit}" &>/dev/null; then
            unsigned_commits+=("${commit}")
        fi
    done < <(git rev-list "${commit_range}")

    if [[ ${#unsigned_commits[@]} -gt 0 ]]; then
        ce_log_warn "Found ${#unsigned_commits[@]} unsigned commits:"
        printf '%s\n' "${unsigned_commits[@]}"
        return 1
    else
        ce_log_success "All commits are signed"
        return 0
    fi
}

# ============================================================================
# Export Functions
# ============================================================================

export -f ce_git_is_repo
export -f ce_git_get_root
export -f ce_git_get_current_branch
export -f ce_git_branch_exists
export -f ce_git_create_branch
export -f ce_git_switch_branch
export -f ce_git_delete_branch
export -f ce_git_list_branches
export -f ce_git_commit
export -f ce_git_amend
export -f ce_git_get_last_commit
export -f ce_git_list_commits
export -f ce_git_push
export -f ce_git_push_with_retry
export -f ce_git_pull
export -f ce_git_fetch
export -f ce_git_check_remote
export -f ce_git_get_remote_url
export -f ce_git_set_remote
export -f ce_git_merge
export -f ce_git_merge_base
export -f ce_git_check_merge_conflicts
export -f ce_git_abort_merge
export -f ce_git_rebase
export -f ce_git_rebase_interactive
export -f ce_git_abort_rebase
export -f ce_git_status
export -f ce_git_has_changes
export -f ce_git_has_staged
export -f ce_git_diff
export -f ce_git_diff_stat
export -f ce_git_stash_save
export -f ce_git_stash_pop
export -f ce_git_stash_list
export -f ce_git_stash_clear
export -f ce_git_create_tag
export -f ce_git_list_tags
export -f ce_git_delete_tag
export -f ce_git_log
export -f ce_git_log_since_branch_point
export -f ce_git_blame
export -f ce_git_clean
export -f ce_git_gc
export -f ce_git_prune
export -f ce_git_validate_commit_message
export -f ce_git_check_signed
