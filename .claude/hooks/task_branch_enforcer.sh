#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 任务-分支绑定强制执行器
# Claude Enhancer v6.5.0 - Task-Branch Binding System
# ═══════════════════════════════════════════════════════════════
# Hook类型：PreToolUse
# 触发时机：Write/Edit/MultiEdit前
# 功能：验证当前分支是否与任务绑定匹配，不匹配则硬阻止操作
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASK_MAP="$PROJECT_ROOT/.workflow/task_branch_map.json"
LOG_FILE="$PROJECT_ROOT/.workflow/logs/task_branch_enforcer.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') $*" >> "$LOG_FILE"
}

validate_json() {
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

show_binding_error() {
    local active_task="$1"
    local current_branch="$2"

    local task_id=$(echo "$active_task" | jq -r '.id')
    local description=$(echo "$active_task" | jq -r '.description')
    local bound_branch=$(echo "$active_task" | jq -r '.branch')

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

    log "BINDING_VIOLATION: Task=$task_id | Expected=$bound_branch | Actual=$current_branch | Blocked=true"
}

# ═══════════════════════════════════════════════════════════════
# 核心验证逻辑
# ═══════════════════════════════════════════════════════════════

enforce_binding() {
    # 如果JSON文件不存在或无效，不阻止操作（降级策略）
    if [[ ! -f "$TASK_MAP" ]] || ! validate_json "$TASK_MAP"; then
        log "NO_TASK_MAP: Allowing operation (no active task)"
        exit 0
    fi

    # 读取活动任务
    local active_task=""
    if command -v jq >/dev/null 2>&1; then
        active_task=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null || echo "")
    else
        # 降级：使用grep提取
        active_task=$(python3 -c "import json; data=json.load(open('$TASK_MAP')); print(json.dumps(data.get('active_task', {})) if data.get('active_task') else '')" 2>/dev/null || echo "")
    fi

    # 如果无活动任务，允许操作
    if [[ -z "$active_task" || "$active_task" == "null" || "$active_task" == "{}" ]]; then
        log "NO_ACTIVE_TASK: Allowing operation"
        exit 0
    fi

    # 提取绑定分支
    local bound_branch=""
    if command -v jq >/dev/null 2>&1; then
        bound_branch=$(echo "$active_task" | jq -r '.branch')
    else
        bound_branch=$(echo "$active_task" | python3 -c "import json,sys; print(json.load(sys.stdin).get('branch', ''))")
    fi

    # 获取当前分支
    local current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

    # 核心验证：当前分支必须等于绑定分支
    if [[ "$current_branch" != "$bound_branch" ]]; then
        show_binding_error "$active_task" "$current_branch"
        exit 1  # 硬阻止
    fi

    # 验证通过
    log "BINDING_OK: Task=$(echo "$active_task" | jq -r '.id') | Branch=$current_branch"
    exit 0
}

# ═══════════════════════════════════════════════════════════════
# 执行验证
# ═══════════════════════════════════════════════════════════════

enforce_binding
