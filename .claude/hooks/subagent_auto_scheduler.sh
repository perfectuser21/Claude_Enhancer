#!/usr/bin/env bash
# Subagent Auto Scheduler Hook
# Version: 1.0.0
# Purpose: 在合适时机自动调用subagent并行调度器，无需用户手动干预
# Trigger: PreToolUse (before Write/Edit operations)
# Priority: P1 (after branch check, before actual writing)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ORCHESTRATOR="${PROJECT_ROOT}/scripts/subagent/parallel_orchestrator.sh"
PHASE_FILE="${PROJECT_ROOT}/.phase/current"
LOG_FILE="${PROJECT_ROOT}/.workflow/logs/subagent/auto_scheduler.log"

# 确保日志目录存在
mkdir -p "$(dirname "${LOG_FILE}")"

# ========== 日志函数 ==========
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "${LOG_FILE}"
}

# ========== 获取当前Phase ==========
get_current_phase() {
    if [[ -f "${PHASE_FILE}" ]]; then
        cat "${PHASE_FILE}"
    else
        echo "Unknown"
    fi
}

# ========== 判断是否需要自动调度 ==========
should_auto_schedule() {
    local phase="$1"
    local tool_name="$2"
    local file_path="${3:-}"

    # 只在Phase2-4自动调度（实现、测试、审查阶段）
    case "${phase}" in
        Phase2|Phase3|Phase4)
            # 只在写代码/配置时触发
            if [[ "${tool_name}" == "Write" || "${tool_name}" == "Edit" ]]; then
                # 排除文档文件（避免频繁触发）
                if [[ "${file_path}" =~ \.(md|txt)$ ]]; then
                    return 1
                fi
                return 0
            fi
            ;;
    esac
    return 1
}

# ========== 提取任务描述（从上下文） ==========
extract_task_description() {
    # 从环境变量或git log获取任务描述
    local task="${CLAUDE_TASK:-}"

    if [[ -z "${task}" ]]; then
        # 尝试从最近的commit message获取
        task=$(git log -1 --pretty=%s 2>/dev/null || echo "General development task")
    fi

    echo "${task}"
}

# ========== 主逻辑 ==========
main() {
    # Hook参数（由Claude Code传入）
    local tool_name="${CLAUDE_TOOL_NAME:-Unknown}"
    local file_path="${CLAUDE_FILE_PATH:-}"

    log "Hook triggered: tool=${tool_name}, file=${file_path}"

    # 1. 获取当前Phase
    local current_phase=$(get_current_phase)
    log "Current phase: ${current_phase}"

    # 2. 判断是否需要自动调度
    if ! should_auto_schedule "${current_phase}" "${tool_name}" "${file_path}"; then
        log "Auto-scheduling not needed for this context"
        exit 0
    fi

    # 3. 提取任务描述
    local task_desc=$(extract_task_description)
    log "Task description: ${task_desc}"

    # 4. 调用调度器
    log "Calling orchestrator..."
    if bash "${ORCHESTRATOR}" "${current_phase}" "${task_desc}" >> "${LOG_FILE}" 2>&1; then
        log "Orchestrator completed successfully"
    else
        log "Orchestrator failed or no parallel needed"
    fi

    # 5. 不阻止工具执行（hook返回0）
    exit 0
}

# 只在支持的环境下执行
if [[ -x "${ORCHESTRATOR}" ]]; then
    main "$@"
else
    # 调度器不存在，跳过
    exit 0
fi
