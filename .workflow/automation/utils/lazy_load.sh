#!/usr/bin/env bash
# Lazy Loading Utilities for Claude Enhancer v5.4.0
# Purpose: Optimize script startup time by deferring expensive operations
# Used by: All automation scripts

# Lazy loading state
declare -A LAZY_LOADED=()
declare -A LAZY_CACHE=()

# Configuration
LAZY_LOAD_ENABLED="${CE_LAZY_LOAD:-1}"
CACHE_TTL="${CE_CACHE_TTL:-300}"  # 5 minutes

# Core lazy loading function
lazy_load() {
    local func_name="$1"
    local loader_cmd="$2"

    # Check if already loaded
    if [[ "${LAZY_LOADED[$func_name]:-0}" == "1" ]]; then
        return 0
    fi

    # Execute loader command
    eval "$loader_cmd"

    # Mark as loaded
    LAZY_LOADED["$func_name"]=1
}

# Lazy load git configuration
lazy_load_git_config() {
    if [[ "${LAZY_LOADED[git_config]:-0}" == "1" ]]; then
        return 0
    fi

    # These are expensive operations - only load when needed
    export GIT_USER_NAME="${GIT_USER_NAME:-$(git config user.name 2>/dev/null || echo 'unknown')}"
    export GIT_USER_EMAIL="${GIT_USER_EMAIL:-$(git config user.email 2>/dev/null || echo 'unknown@example.com')}"
    export GIT_DEFAULT_BRANCH="${GIT_DEFAULT_BRANCH:-$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo 'main')}"

    LAZY_LOADED[git_config]=1
}

# Lazy load GitHub CLI configuration
lazy_load_gh_config() {
    if [[ "${LAZY_LOADED[gh_config]:-0}" == "1" ]]; then
        return 0
    fi

    # Only check gh availability when needed
    if command -v gh &>/dev/null; then
        export GH_AVAILABLE=1
        export GH_VERSION="$(gh --version 2>/dev/null | head -n1 | cut -d' ' -f3 || echo 'unknown')"
    else
        export GH_AVAILABLE=0
    fi

    LAZY_LOADED[gh_config]=1
}

# Lazy load remote information
lazy_load_remote_info() {
    if [[ "${LAZY_LOADED[remote_info]:-0}" == "1" ]]; then
        return 0
    fi

    # Cache remote URL (expensive network operation)
    export GIT_REMOTE_URL="${GIT_REMOTE_URL:-$(git config --get remote.origin.url 2>/dev/null || echo '')}"

    # Extract repo info from URL
    if [[ -n "$GIT_REMOTE_URL" ]]; then
        if [[ "$GIT_REMOTE_URL" =~ github.com[:/]([^/]+)/([^/.]+) ]]; then
            export GITHUB_OWNER="${BASH_REMATCH[1]}"
            export GITHUB_REPO="${BASH_REMATCH[2]}"
        fi
    fi

    LAZY_LOADED[remote_info]=1
}

# Lazy load branch information
lazy_load_branch_info() {
    if [[ "${LAZY_LOADED[branch_info]:-0}" == "1" ]]; then
        return 0
    fi

    # Current branch (cheap operation, but still worth caching)
    export CURRENT_BRANCH="${CURRENT_BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')}"

    # Upstream branch (more expensive)
    export UPSTREAM_BRANCH="${UPSTREAM_BRANCH:-$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo '')}"

    LAZY_LOADED[branch_info]=1
}

# Lazy load commit information
lazy_load_commit_info() {
    if [[ "${LAZY_LOADED[commit_info]:-0}" == "1" ]]; then
        return 0
    fi

    # Latest commit (expensive for large repos)
    export LAST_COMMIT_HASH="${LAST_COMMIT_HASH:-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')}"
    export LAST_COMMIT_MESSAGE="${LAST_COMMIT_MESSAGE:-$(git log -1 --pretty=%s 2>/dev/null || echo 'unknown')}"

    LAZY_LOADED[commit_info]=1
}

# Lazy load repository status
lazy_load_repo_status() {
    if [[ "${LAZY_LOADED[repo_status]:-0}" == "1" ]]; then
        return 0
    fi

    # Check for changes (very expensive operation)
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        export REPO_HAS_CHANGES=0
    else
        export REPO_HAS_CHANGES=1
    fi

    # Count untracked files
    export UNTRACKED_FILES_COUNT=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)

    LAZY_LOADED[repo_status]=1
}

# Cached git operations
cached_git_status() {
    local cache_key="git_status"
    local cache_file="/tmp/ce_cache_${cache_key}_$$.cache"
    local cache_age=0

    if [[ -f "$cache_file" ]]; then
        cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null) ))
    fi

    if [[ $cache_age -lt $CACHE_TTL ]]; then
        cat "$cache_file"
    else
        git status --porcelain 2>/dev/null | tee "$cache_file"
    fi
}

cached_git_branch_list() {
    local cache_key="git_branches"
    local cache_file="/tmp/ce_cache_${cache_key}_$$.cache"
    local cache_age=0

    if [[ -f "$cache_file" ]]; then
        cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null) ))
    fi

    if [[ $cache_age -lt $CACHE_TTL ]]; then
        cat "$cache_file"
    else
        git branch -a 2>/dev/null | tee "$cache_file"
    fi
}

cached_git_remote_list() {
    local cache_key="git_remotes"
    local cache_file="/tmp/ce_cache_${cache_key}_$$.cache"
    local cache_age=0

    if [[ -f "$cache_file" ]]; then
        cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null) ))
    fi

    if [[ $cache_age -lt $CACHE_TTL ]]; then
        cat "$cache_file"
    else
        git remote -v 2>/dev/null | tee "$cache_file"
    fi
}

# Deferred initialization
defer_initialization() {
    local func_name="$1"

    # Create a wrapper function that loads on first use
    eval "
    $func_name() {
        # Load the real function
        lazy_load_${func_name}

        # Call the real function
        ${func_name}_real \"\$@\"
    }
    "
}

# Optimize shell options for performance
optimize_shell_options() {
    # Disable command hashing (small performance gain)
    set +h 2>/dev/null || true

    # Disable mail checking
    unset MAILCHECK

    # Set minimal PS1 for non-interactive shells
    if [[ ! -t 1 ]]; then
        PS1=""
    fi
}

# Reduce subprocess spawning
use_builtin_alternatives() {
    # Use bash built-ins instead of external commands where possible

    # Instead of: echo "$(cat file)"
    # Use: echo "$(<file)"

    # Instead of: count=$(wc -l < file)
    # Use: count=0; while read; do ((count++)); done < file

    # Instead of: basename "$path"
    # Use: path="${path##*/}"

    # Instead of: dirname "$path"
    # Use: path="${path%/*}"

    return 0
}

# Cache expensive external command results
cache_command_result() {
    local cache_key="$1"
    shift
    local cmd=("$@")

    local cache_file="/tmp/ce_cache_${cache_key}_$$.cache"
    local cache_age=0

    if [[ -f "$cache_file" ]]; then
        cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null) ))
    fi

    if [[ $cache_age -lt $CACHE_TTL ]]; then
        cat "$cache_file"
    else
        "${cmd[@]}" | tee "$cache_file"
    fi
}

# Preload commonly used data
preload_common_data() {
    # Only preload if explicitly requested
    if [[ "${CE_PRELOAD:-0}" != "1" ]]; then
        return 0
    fi

    # Preload in background to not block startup
    (
        lazy_load_git_config
        lazy_load_branch_info
    ) &
}

# Clear lazy load cache
clear_lazy_cache() {
    LAZY_LOADED=()
    LAZY_CACHE=()

    # Clear cache files
    rm -f /tmp/ce_cache_*_$$.cache 2>/dev/null || true

    # Unset cached environment variables
    unset GIT_USER_NAME GIT_USER_EMAIL GIT_DEFAULT_BRANCH
    unset GH_AVAILABLE GH_VERSION
    unset GIT_REMOTE_URL GITHUB_OWNER GITHUB_REPO
    unset CURRENT_BRANCH UPSTREAM_BRANCH
    unset LAST_COMMIT_HASH LAST_COMMIT_MESSAGE
    unset REPO_HAS_CHANGES UNTRACKED_FILES_COUNT
}

# Show lazy load statistics
show_lazy_load_stats() {
    echo "Lazy Load Statistics:"
    echo "  Loaded modules: ${#LAZY_LOADED[@]}"
    echo "  Cached items: ${#LAZY_CACHE[@]}"
    echo ""
    echo "Loaded modules:"
    for key in "${!LAZY_LOADED[@]}"; do
        echo "  - $key"
    done
}

# Initialize lazy loading
init_lazy_load() {
    if [[ "$LAZY_LOAD_ENABLED" != "1" ]]; then
        # If lazy loading is disabled, load everything immediately
        lazy_load_git_config
        lazy_load_gh_config
        lazy_load_remote_info
        lazy_load_branch_info
        return 0
    fi

    # Optimize shell environment
    optimize_shell_options

    # Optionally preload common data
    preload_common_data
}

# Auto-initialize if sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    init_lazy_load
fi

# Export functions
export -f lazy_load
export -f lazy_load_git_config
export -f lazy_load_gh_config
export -f lazy_load_remote_info
export -f lazy_load_branch_info
export -f lazy_load_commit_info
export -f lazy_load_repo_status
export -f cached_git_status
export -f cached_git_branch_list
export -f cached_git_remote_list
export -f cache_command_result
export -f clear_lazy_cache
export -f show_lazy_load_stats
