#!/usr/bin/env bash
# Parallel Subagent Suggester Hook
# Version: 1.0.0
# Trigger: PrePrompt (在Phase2/3/4开始时)
# Purpose: 自动建议并行subagent调用方案，减少用户交互

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PHASE_FILE="${PROJECT_ROOT}/.phase/current"
GENERATOR="${PROJECT_ROOT}/scripts/subagent/parallel_task_generator.sh"
LOG_FILE="${PROJECT_ROOT}/.workflow/logs/subagent/suggester.log"

mkdir -p "$(dirname "${LOG_FILE}")"

# ========== 获取当前Phase ==========
get_current_phase() {
    if [[ -f "${PHASE_FILE}" ]]; then
        head -1 "${PHASE_FILE}"
    else
        echo "Unknown"
    fi
}

# ========== 提取任务描述 ==========
extract_task_from_context() {
    # 从git log或环境变量获取
    local task="${CLAUDE_TASK:-}"

    if [[ -z "${task}" ]]; then
        # 尝试从最近commit获取
        task=$(git log -1 --pretty=%s 2>/dev/null || echo "")
    fi

    if [[ -z "${task}" ]]; then
        # 从.workflow/user_request.md获取
        if [[ -f "${PROJECT_ROOT}/.workflow/user_request.md" ]]; then
            task=$(head -5 "${PROJECT_ROOT}/.workflow/user_request.md" | grep -v "^#" | tr '\n' ' ')
        fi
    fi

    echo "${task:-General development task}"
}

# ========== 主逻辑 ==========
main() {
    local phase=$(get_current_phase)

    # 只在Phase2/3/4触发
    case "${phase}" in
        Phase2|Phase3|Phase4)
            ;;
        *)
            exit 0  # 其他Phase不触发
            ;;
    esac

    # 提取任务
    local task=$(extract_task_from_context)

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Triggered for ${phase}: ${task}" >> "${LOG_FILE}"

    # 调用生成器
    if [[ -x "${GENERATOR}" ]]; then
        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "🤖 Parallel Subagent Suggestion (Auto-generated)"
        echo "═══════════════════════════════════════════════════════════"
        echo ""

        bash "${GENERATOR}" "${phase}" "${task}"

        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "💡 Tip: Copy the Task() calls above and execute in parallel"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
    fi

    # 不阻止执行
    exit 0
}

main "$@"
