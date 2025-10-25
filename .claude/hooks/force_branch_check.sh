#!/bin/bash
# Claude Enhancer - PrePrompt强制分支检查（规则0：Phase 1）
# 版本：2.0 - 使用公共库重构
# 创建日期：2025-10-15
# 更新日期：2025-10-25 - 提取公共代码到lib/branch_common.sh
# 目的：在AI思考之前注入强制警告，确保100%遵守Phase 1分支检查

# ============================================
# 这是PrePrompt Hook - 在AI开始思考之前运行
# 功能：
# 1. 检测当前分支
# 2. 如果在main/master，注入强制警告到AI上下文
# 3. 强制AI创建新分支后才能继续
# ============================================

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=.claude/hooks/lib/branch_common.sh
source "${SCRIPT_DIR}/lib/branch_common.sh"

# Hook metadata
readonly HOOK_NAME="force_branch_check.sh"
readonly HOOK_VERSION="2.0"

# ============================================
# Main Logic
# ============================================

# Check if in git repository
if ! is_git_repo; then
    exit 0
fi

# Get current branch (using common library)
current_branch=$(get_current_branch)

# Log activation
log_hook_event "$HOOK_NAME v$HOOK_VERSION" "PrePrompt triggered on branch: $current_branch"

# ============================================
# Core Logic: Check for protected branches
# ============================================

if is_protected_branch "$current_branch"; then
    # Protected branch detected - inject warning to AI context

    cat <<'EOF' >&2

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ⚠️ ⚠️ ⚠️  CRITICAL: 你正在 MAIN/MASTER 分支上！ ⚠️ ⚠️ ⚠️             ║
║                                                                           ║
║  🔴 规则0（Phase 1）强制要求：新任务 = 新分支                          ║
║                                                                           ║
║  ❌ 你**禁止**在main/master分支上执行任何Write/Edit操作                 ║
║                                                                           ║
║  ✅ 你**必须**先执行以下命令创建新分支：                                ║
║                                                                           ║
║     git checkout -b feature/任务描述                                     ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

EOF

    # Show guidance (using common library)
    show_branch_naming_guide
    echo "" >&2
    show_phase_workflow
    echo "" >&2
    echo "💡 这是100%强制规则，不是建议！" >&2
    echo "   违反将导致Hook硬阻止（exit 1）" >&2
    echo "" >&2

    log_hook_event "$HOOK_NAME v$HOOK_VERSION" "WARNING: AI on $current_branch, warning injected"

    # PrePrompt hook should NOT block (exit 0), just inject warning
    # Actual blocking is done by PreToolUse hooks (task_branch_enforcer, branch_helper)
    exit 0
else
    # On feature branch - silent pass
    log_hook_event "$HOOK_NAME v$HOOK_VERSION" "PASSED: on branch $current_branch"
    exit 0
fi
