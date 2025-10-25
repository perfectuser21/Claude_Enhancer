#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 任务-分支绑定强制执行器
# Claude Enhancer v7.3.0 - Task-Branch Binding System
# ═══════════════════════════════════════════════════════════════
# Hook类型：PreToolUse
# 触发时机：Write/Edit/MultiEdit前
# 功能：验证当前分支是否与任务绑定匹配，不匹配则硬阻止操作
# 版本：2.0 - 使用公共库重构
# 更新日期：2025-10-25 - 提取公共代码到lib/branch_common.sh
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=.claude/hooks/lib/branch_common.sh
source "${SCRIPT_DIR}/lib/branch_common.sh"

# Hook metadata
readonly HOOK_NAME="task_branch_enforcer.sh"
readonly HOOK_VERSION="2.0"

# Task binding file
readonly TASK_MAP="${BRANCH_COMMON_PROJECT_ROOT}/.workflow/task_branch_map.json"

# ═══════════════════════════════════════════════════════════════
# Task Binding Display Function
# ═══════════════════════════════════════════════════════════════

show_binding_error() {
    local active_task="$1"
    local current_branch="$2"

    local task_id
    local description
    local bound_branch

    if command -v jq >/dev/null 2>&1; then
        task_id=$(echo "$active_task" | jq -r '.id')
        description=$(echo "$active_task" | jq -r '.description')
        bound_branch=$(echo "$active_task" | jq -r '.branch')
    else
        task_id=$(echo "$active_task" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('id', 'unknown'))")
        description=$(echo "$active_task" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('description', ''))")
        bound_branch=$(echo "$active_task" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('branch', ''))")
    fi

    cat <<EOF >&2
${BOLD}╔═══════════════════════════════════════════════════════════╗${NC}
${BOLD}║  ${RED}❌ 任务-分支绑定冲突检测${NC}${BOLD}                               ║${NC}
${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}

${RED}${BOLD}🔴 错误：当前分支与任务绑定不符${NC}

${BOLD}任务信息：${NC}
  ${CYAN}ID:${NC}         $task_id
  ${CYAN}描述:${NC}       $description
  ${CYAN}绑定分支:${NC}   ${GREEN}$bound_branch${NC}

${BOLD}当前状态：${NC}
  ${CYAN}当前分支:${NC}   ${RED}$current_branch${NC}

${BOLD}🚫 禁止操作：${NC}Write/Edit/MultiEdit 操作已被阻止

${BOLD}✅ 解决方法（选择一项）：${NC}

  ${BOLD}1. 切回正确分支${NC} ${YELLOW}(推荐)${NC}
     ${GREEN}git checkout $bound_branch${NC}

  2. 完成当前任务
     ${GREEN}bash .claude/hooks/task_lifecycle.sh complete${NC}

  3. 紧急绕过 ${RED}(谨慎使用)${NC}
     ${YELLOW}bash .claude/hooks/task_lifecycle.sh cancel${NC}

${BOLD}═══════════════════════════════════════════════════════════${NC}

EOF

    log_hook_event "$HOOK_NAME v$HOOK_VERSION" "BINDING_VIOLATION: Task=$task_id | Expected=$bound_branch | Actual=$current_branch | Blocked=true"
}

# ═══════════════════════════════════════════════════════════════
# Core Validation Logic
# ═══════════════════════════════════════════════════════════════

enforce_binding() {
    # If JSON file doesn't exist or invalid, don't block (degradation strategy)
    if ! validate_json_file "$TASK_MAP"; then
        log_hook_event "$HOOK_NAME v$HOOK_VERSION" "NO_TASK_MAP: Allowing operation (no active task)"
        exit 0
    fi

    # Read active task
    local active_task=""
    if command -v jq >/dev/null 2>&1; then
        active_task=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null || echo "")
    else
        active_task=$(python3 -c "import json; data=json.load(open('$TASK_MAP')); print(json.dumps(data.get('active_task', {})) if data.get('active_task') else '')" 2>/dev/null || echo "")
    fi

    # If no active task, allow operation
    if [[ -z "$active_task" || "$active_task" == "null" || "$active_task" == "{}" ]]; then
        log_hook_event "$HOOK_NAME v$HOOK_VERSION" "NO_ACTIVE_TASK: Allowing operation"
        exit 0
    fi

    # Extract bound branch
    local bound_branch=""
    if command -v jq >/dev/null 2>&1; then
        bound_branch=$(echo "$active_task" | jq -r '.branch')
    else
        bound_branch=$(echo "$active_task" | python3 -c "import json,sys; print(json.load(sys.stdin).get('branch', ''))")
    fi

    # Get current branch (using common library)
    local current_branch
    current_branch=$(get_current_branch)

    # Core validation: current branch must equal bound branch
    if [[ "$current_branch" != "$bound_branch" ]]; then
        show_binding_error "$active_task" "$current_branch"
        exit 1  # Hard block
    fi

    # Validation passed
    local task_id
    if command -v jq >/dev/null 2>&1; then
        task_id=$(echo "$active_task" | jq -r '.id')
    else
        task_id=$(echo "$active_task" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id', 'unknown'))")
    fi
    log_hook_event "$HOOK_NAME v$HOOK_VERSION" "BINDING_OK: Task=$task_id | Branch=$current_branch"
    exit 0
}

# ═══════════════════════════════════════════════════════════════
# Execute Validation
# ═══════════════════════════════════════════════════════════════

enforce_binding
