#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Workflow Executor Integration Hook
# 将workflow executor集成到Claude hooks系统
# =============================================================================

set -euo pipefail

# 配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly EXECUTOR="${PROJECT_ROOT}/.workflow/executor.sh"
readonly HOOK_CONFIG="${SCRIPT_DIR}/engine_config.json"

# 颜色输出
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# 日志函数
log_hook() {
    echo -e "${BLUE}[WORKFLOW-HOOK]${NC} $*" >&2
}

# 主要集成逻辑
main() {
    log_hook "Workflow Executor Integration Hook 触发"

    # 检查executor是否存在
    if [[ ! -f "${EXECUTOR}" ]]; then
        log_hook "${YELLOW}警告: Workflow Executor 未找到，跳过集成${NC}"
        exit 0
    fi

    # 获取当前上下文信息
    local current_phase="${WORKFLOW_PHASE:-unknown}"
    local context="${WORKFLOW_CONTEXT:-general}"

    log_hook "当前阶段: ${current_phase}, 上下文: ${context}"

    # 根据上下文决定执行的操作
    case "${context}" in
        *"Plan"*)
            log_hook "P1阶段 - 执行planning检查"
            "${EXECUTOR}" suggest >/dev/null 2>&1 || true
            ;;

        *"Implementation"*)
            log_hook "P3阶段 - 执行implementation检查"
            "${EXECUTOR}" hooks >/dev/null 2>&1 || true
            ;;

        *"Testing"*)
            log_hook "P4阶段 - 执行testing检查"
            "${EXECUTOR}" validate >/dev/null 2>&1 || true
            ;;

        *"Release"*)
            log_hook "P6阶段 - 执行release检查"
            "${EXECUTOR}" status >/dev/null 2>&1 || true
            ;;

        *)
            log_hook "通用上下文 - 执行状态检查"
            "${EXECUTOR}" status >/dev/null 2>&1 || true
            ;;
    esac

    log_hook "${GREEN}Workflow Executor Integration 完成${NC}"
}

# 错误处理
trap 'log_hook "Integration hook 意外终止"' ERR

# 超时保护 (30秒)
timeout 30s main "$@" || log_hook "${YELLOW}Integration hook 超时${NC}"

exit 0