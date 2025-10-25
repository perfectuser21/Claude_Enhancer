#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Branch Common Library
# Claude Enhancer v7.3.0 - Shared functions for branch hooks
# ═══════════════════════════════════════════════════════════════
# Purpose: Extract common code from branch-related hooks to reduce duplication
# Used by: force_branch_check.sh, task_branch_enforcer.sh, branch_helper.sh
# ═══════════════════════════════════════════════════════════════

# Prevent multiple sourcing
if [[ -n "${_BRANCH_COMMON_LOADED:-}" ]]; then
    return 0
fi
_BRANCH_COMMON_LOADED=true

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
# Color Definitions
# ═══════════════════════════════════════════════════════════════

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'  # No Color

# ═══════════════════════════════════════════════════════════════
# Core Branch Functions
# ═══════════════════════════════════════════════════════════════

# Get current git branch
# Returns: branch name or "unknown" if not in a git repo
get_current_branch() {
    git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

# Check if a branch is protected
# Args: $1 = branch name
# Returns: 0 if protected, 1 if not
is_protected_branch() {
    local branch="${1:-}"
    [[ "$branch" =~ ^(main|master|production)$ ]]
}

# Check if currently in a git repository
# Returns: 0 if in git repo, 1 if not
is_git_repo() {
    git rev-parse --git-dir >/dev/null 2>&1
}

# ═══════════════════════════════════════════════════════════════
# Logging Functions
# ═══════════════════════════════════════════════════════════════

# Log hook event to unified log file
# Args: $1 = hook name, $2 = event message
log_hook_event() {
    local hook_name="${1:-unknown}"
    local event="${2:-}"
    local timestamp
    timestamp=$(date +'%F %T')
    echo "$timestamp [$hook_name] $event" >> "$BRANCH_COMMON_LOG_FILE"
}

# ═══════════════════════════════════════════════════════════════
# Display Functions
# ═══════════════════════════════════════════════════════════════

# Show branch naming guidance
show_branch_naming_guide() {
    cat <<EOF >&2
${BOLD}📝 分支命名规范：${NC}
  ${GREEN}•${NC} feature/xxx    - 新功能开发
  ${GREEN}•${NC} bugfix/xxx     - Bug修复
  ${GREEN}•${NC} perf/xxx       - 性能优化
  ${GREEN}•${NC} docs/xxx       - 文档更新
  ${GREEN}•${NC} experiment/xxx - 实验性改动
EOF
}

# Show Phase workflow overview
show_phase_workflow() {
    cat <<EOF >&2
${BOLD}🚀 Claude Enhancer 7-Phase工作流：${NC}
  ${CYAN}Phase 1:${NC} Discovery & Planning  ${YELLOW}← 分支准备${NC}
  ${CYAN}Phase 2:${NC} Implementation
  ${CYAN}Phase 3:${NC} Testing (质量门禁1)
  ${CYAN}Phase 4:${NC} Review (质量门禁2)
  ${CYAN}Phase 5:${NC} Release
  ${CYAN}Phase 6:${NC} Acceptance
  ${CYAN}Phase 7:${NC} Closure
EOF
}

# Show protected branch warning box
# Args: $1 = current branch, $2 = hook name
show_protected_branch_warning() {
    local current_branch="${1:-main}"
    local hook_name="${2:-branch_common}"

    cat <<EOF >&2

${BOLD}╔═══════════════════════════════════════════════════════════╗${NC}
${BOLD}║  ${RED}⚠️  PROTECTED BRANCH DETECTED${NC}${BOLD}                            ║${NC}
${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}

${RED}${BOLD}📍 当前分支: $current_branch${NC}

${BOLD}🔴 规则0（Phase 1）强制要求：新任务 = 新分支${NC}

${BOLD}❌ 禁止操作：${NC}
  • 禁止在 main/master/production 分支上执行 Write/Edit 操作

${BOLD}✅ 解决方案：${NC}
  ${GREEN}git checkout -b feature/任务描述${NC}

EOF
    show_branch_naming_guide
    echo "" >&2
    show_phase_workflow
    echo "" >&2
    echo "${BOLD}💡 这是100%强制规则，不是建议！${NC}" >&2
    echo "${BOLD}═══════════════════════════════════════════════════════════${NC}" >&2
    echo "" >&2
}

# Show protected branch error box (for hard blocking)
# Args: $1 = current branch
show_protected_branch_error() {
    local current_branch="${1:-main}"

    cat <<EOF >&2

${BOLD}🚨 Claude Enhancer - 分支检查失败${NC}
${BOLD}═══════════════════════════════════════════════════════════${NC}

${RED}${BOLD}❌ 错误：禁止在 $current_branch 分支上修改文件${NC}

${BOLD}📋 规则0：新任务 = 新分支（100%强制执行）${NC}

${BOLD}🔧 解决方案：${NC}
  ${BOLD}1. AI必须先创建feature分支：${NC}
     ${GREEN}git checkout -b feature/任务描述${NC}

  ${BOLD}2. 或启用自动创建（推荐）：${NC}
     ${GREEN}export CE_AUTO_CREATE_BRANCH=true${NC}

EOF
    show_branch_naming_guide
    echo "" >&2
    echo "${BOLD}💡 这是100%强制规则，不是建议！${NC}" >&2
    echo "${BOLD}═══════════════════════════════════════════════════════════${NC}" >&2
    echo "" >&2
}

# ═══════════════════════════════════════════════════════════════
# Auto Branch Creation
# ═══════════════════════════════════════════════════════════════

# Automatically create a feature branch
# Returns: 0 if successful, 1 if failed
auto_create_branch() {
    local base_branch="${1:-main}"
    local silent_mode="${CE_SILENT_MODE:-false}"

    local date_str
    date_str=$(date +%Y%m%d-%H%M%S)
    local new_branch="feature/auto-${date_str}"

    if [[ "$silent_mode" != "true" ]]; then
        echo "" >&2
        echo "${BOLD}🤖 Claude Enhancer - 自动创建分支${NC}" >&2
        echo "${BOLD}═══════════════════════════════════════════════════════════${NC}" >&2
        echo "" >&2
        echo "${CYAN}📍 检测到在 $base_branch 分支${NC}" >&2
        echo "${GREEN}🚀 自动创建新分支: $new_branch${NC}" >&2
        echo "${YELLOW}💡 规则0: 新任务 = 新分支 (100%强制)${NC}" >&2
        echo "" >&2
    fi

    if git checkout -b "$new_branch" 2>/dev/null; then
        if [[ "$silent_mode" != "true" ]]; then
            echo "${GREEN}✅ 成功创建并切换到: $new_branch${NC}" >&2
            echo "${GREEN}✅ 现在可以安全开始Phase 2-7工作流${NC}" >&2
            echo "" >&2
        fi
        log_hook_event "auto_branch_creator" "Created: $new_branch from $base_branch"
        return 0
    else
        if [[ "$silent_mode" != "true" ]]; then
            echo "${RED}❌ 自动创建分支失败${NC}" >&2
        fi
        log_hook_event "auto_branch_creator" "FAILED: Could not create $new_branch"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# Validation Functions
# ═══════════════════════════════════════════════════════════════

# Validate JSON file exists and is valid
# Args: $1 = file path
# Returns: 0 if valid, 1 if not
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

# ═══════════════════════════════════════════════════════════════
# Environment Detection
# ═══════════════════════════════════════════════════════════════

# Detect if being called by Git hook
is_git_hook_context() {
    [[ -n "${CE_EXECUTION_MODE:-}" ]] || [[ -n "${GIT_DIR:-}" ]]
}

# Detect if being called by Claude hook
is_claude_hook_context() {
    [[ -z "${CE_EXECUTION_MODE:-}" ]] && [[ -z "${GIT_DIR:-}" ]]
}

# ═══════════════════════════════════════════════════════════════
# Initialization
# ═══════════════════════════════════════════════════════════════

# Auto-mode detection (if enabled)
if is_auto_mode; then
    export CE_SILENT_MODE=true
fi

# Library loaded successfully
log_hook_event "branch_common_lib" "Library loaded successfully"
