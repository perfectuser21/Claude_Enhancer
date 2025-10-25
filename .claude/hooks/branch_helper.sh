#!/bin/bash
# Claude Enhancer - Branch强制检查（规则0：Phase 1 - Branch Check）
# 版本：4.0 - 使用公共库重构
# 创建日期：2025-10-15
# 更新日期：2025-10-25 - 提取公共代码到lib/branch_common.sh
# 修复原因：之前的EXECUTION_MODE检测不可靠，导致50%违规率

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=.claude/hooks/lib/branch_common.sh
source "${SCRIPT_DIR}/lib/branch_common.sh"

# Hook metadata
readonly HOOK_NAME="branch_helper.sh"
readonly HOOK_VERSION="4.0"

# Auto-mode detection (before other checks)
if is_auto_mode; then
    export CE_SILENT_MODE=true
fi

# Log hook activation
log_hook_event "$HOOK_NAME v$HOOK_VERSION" "triggered by ${USER:-claude}"

# Check if in git repository
if ! is_git_repo; then
    echo "ℹ️  不在Git仓库中，跳过分支检查" >&2
    exit 0
fi

# Get current branch (using common library)
current_branch=$(get_current_branch)

# ============================================
# 版本4.0: 使用公共库函数，无条件硬阻止
# 删除不可靠的EXECUTION_MODE检测逻辑
# 任何对main/master分支的Write/Edit操作都被阻止
# ============================================

# Main logic: Check for protected branches
if is_protected_branch "$current_branch"; then
    # Protected branch detected - 无条件处理（不依赖EXECUTION_MODE）

    # 优先级1: 自动创建分支（如果启用，使用公共库函数）
    if is_auto_create_enabled; then
        if auto_create_branch "$current_branch"; then
            # 成功创建，继续执行
            exit 0
        else
            # 自动创建失败，继续到硬阻止逻辑
            if ! is_silent_mode; then
                echo "❌ 自动创建分支失败" >&2
            fi
        fi
    fi

    # 优先级2: 硬阻止（自动创建失败或被禁用，使用公共库函数）
    show_protected_branch_error "$current_branch"

    # 记录阻止日志
    log_hook_event "$HOOK_NAME v$HOOK_VERSION" "HARD-BLOCKED: attempt to modify on $current_branch"

    # 硬阻止 - exit 1
    exit 1
else
    # 在feature分支上 - 允许操作
    if ! is_silent_mode; then
        echo "✅ 分支检查通过: $current_branch" >&2
    fi
    log_hook_event "$HOOK_NAME v$HOOK_VERSION" "PASSED: on branch $current_branch"
fi

exit 0
