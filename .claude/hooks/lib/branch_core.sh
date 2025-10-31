#!/bin/bash
# Branch Core Functions
# Part of branch_common.sh modularization
# Version: 1.0.0

# Prevent multiple sourcing
if [[ -n "${_BRANCH_CORE_LOADED:-}" ]]; then
    return 0
fi
_BRANCH_CORE_LOADED=true

# Source cache manager if available (performance optimization)
CACHE_MANAGER_PATH="$(dirname "${BASH_SOURCE[0]}")/../../tools/cache_manager.sh"
if [[ -f "$CACHE_MANAGER_PATH" ]]; then
    # shellcheck source=/dev/null
    source "$CACHE_MANAGER_PATH"
    CACHE_ENABLED=true
else
    CACHE_ENABLED=false
fi

# ═══════════════════════════════════════════════════════════════
# Project Paths
# ═══════════════════════════════════════════════════════════════

get_project_root() {
    local script_path="${BASH_SOURCE[1]}"
    if [[ -z "$script_path" ]]; then
        script_path="${BASH_SOURCE[0]}"
    fi
    cd "$(dirname "$script_path")/../.." && pwd
}

readonly BRANCH_COMMON_PROJECT_ROOT="${PROJECT_ROOT:-$(get_project_root)}"
readonly BRANCH_COMMON_LOG_FILE="${BRANCH_COMMON_PROJECT_ROOT}/.workflow/logs/claude_hooks.log"

# Ensure log directory exists
mkdir -p "$(dirname "$BRANCH_COMMON_LOG_FILE")"

# ═══════════════════════════════════════════════════════════════
# Core Branch Functions
# ═══════════════════════════════════════════════════════════════

# Get current git branch (with caching)
get_current_branch() {
    if [[ "$CACHE_ENABLED" == "true" ]]; then
        # Use cache for branch check (TTL: 60 seconds)
        execute_with_cache "git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown'" "current-branch" 60
    else
        # Direct execution without cache
        git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
    fi
}

# Check if a branch is protected
is_protected_branch() {
    local branch="${1:-}"
    [[ "$branch" =~ ^(main|master|production)$ ]]
}

# Check if currently in a git repository (with caching)
is_git_repo() {
    if [[ "$CACHE_ENABLED" == "true" ]]; then
        # Use cache for git repo check (TTL: 300 seconds)
        local result
        result=$(execute_with_cache "git rev-parse --git-dir 2>&1 && echo 'YES' || echo 'NO'" "is-git-repo" 300)
        [[ "$result" == "YES" ]]
    else
        # Direct execution without cache
        git rev-parse --git-dir >/dev/null 2>&1
    fi
}

# ═══════════════════════════════════════════════════════════════
# Logging Functions
# ═══════════════════════════════════════════════════════════════

# Log hook event to unified log file
log_hook_event() {
    local hook_name="${1:-unknown}"
    local event="${2:-}"
    local timestamp
    timestamp=$(date +'%F %T')
    echo "$timestamp [$hook_name] $event" >> "$BRANCH_COMMON_LOG_FILE"
}

# ═══════════════════════════════════════════════════════════════
# Auto Branch Creation
# ═══════════════════════════════════════════════════════════════

# Automatically create a feature branch
auto_create_branch() {
    local base_branch="${1:-main}"
    local silent_mode="${CE_SILENT_MODE:-false}"

    local date_str
    date_str=$(date +%Y%m%d-%H%M%S)
    local new_branch="feature/auto-${date_str}"

    if [[ "$silent_mode" != "true" ]]; then
        # Source display functions for output
        if [[ -f "$(dirname "${BASH_SOURCE[0]}")/branch_display.sh" ]]; then
            # shellcheck source=/dev/null
            source "$(dirname "${BASH_SOURCE[0]}")/branch_display.sh"
        fi

        echo "" >&2
        echo "${BOLD:-}🤖 Claude Enhancer - 自动创建分支${NC:-}" >&2
        echo "${BOLD:-}═══════════════════════════════════════════════════════════${NC:-}" >&2
        echo "" >&2
        echo "${CYAN:-}📍 检测到在 $base_branch 分支${NC:-}" >&2
        echo "${GREEN:-}🚀 自动创建新分支: $new_branch${NC:-}" >&2
        echo "${YELLOW:-}💡 规则0: 新任务 = 新分支 (100%强制)${NC:-}" >&2
        echo "" >&2
    fi

    if git checkout -b "$new_branch" 2>/dev/null; then
        if [[ "$silent_mode" != "true" ]]; then
            echo "${GREEN:-}✅ 成功创建并切换到: $new_branch${NC:-}" >&2
            echo "${GREEN:-}✅ 现在可以安全开始Phase 2-7工作流${NC:-}" >&2
            echo "" >&2
        fi
        log_hook_event "auto_branch_creator" "Created: $new_branch from $base_branch"
        return 0
    else
        if [[ "$silent_mode" != "true" ]]; then
            echo "${RED:-}❌ 自动创建分支失败${NC:-}" >&2
        fi
        log_hook_event "auto_branch_creator" "FAILED: Could not create $new_branch"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════

# Check if running in silent mode
is_silent_mode() {
    [[ "${CE_SILENT_MODE:-false}" == "true" ]]
}

# Check if running in auto mode
is_auto_mode() {
    [[ "${CE_AUTO_MODE:-false}" == "true" ]]
}

# Check if auto branch creation is enabled
is_auto_create_enabled() {
    [[ "${CE_AUTO_CREATE_BRANCH:-true}" == "true" ]]
}

# Detect if being called by Git hook
is_git_hook_context() {
    [[ -n "${CE_EXECUTION_MODE:-}" ]] || [[ -n "${GIT_DIR:-}" ]]
}

# Detect if being called by Claude hook
is_claude_hook_context() {
    [[ -z "${CE_EXECUTION_MODE:-}" ]] && [[ -z "${GIT_DIR:-}" ]]
}

# Validate JSON file exists and is valid
validate_json_file() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        return 1
    fi

    if command -v jq >/dev/null 2>&1; then
        jq empty "$file" 2>/dev/null
    else
        python3 -c "import json; json.load(open('$file'))" 2>/dev/null
    fi
}

# ═══════════════════════════════════════════════════════════════
# Initialization
# ═══════════════════════════════════════════════════════════════

# Auto-mode detection (if enabled)
if is_auto_mode; then
    export CE_SILENT_MODE=true
fi

# Library loaded successfully
log_hook_event "branch_core_lib" "Library loaded successfully"