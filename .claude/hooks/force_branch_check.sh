#!/bin/bash
# Claude Enhancer - PrePrompt Force Branch Check (Delegator)
# Version: 3.0 - Unified System
# Updated: 2025-10-25 - Delegates to unified_branch_protector.sh

# Load unified branch protector
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=.claude/hooks/unified_branch_protector.sh
source "${SCRIPT_DIR}/unified_branch_protector.sh"

# PrePrompt hook special handling: warn only, don't block
export CE_BRANCH_PROTECTION_MODE="warn"

# Get current branch with cache
current_branch=$(get_current_branch)

# Log activation
log_hook_event "force_branch_check" "PrePrompt triggered on branch: $current_branch"

# If on protected branch, show special PrePrompt warning
if is_protected_branch "$current_branch"; then
    # CRITICAL FIX: 清除旧Phase状态（merge后回到main时自动重置）
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
    PHASE_FILE="$PROJECT_ROOT/.phase/current"

    if [[ -f "$PHASE_FILE" ]]; then
        OLD_PHASE=$(cat "$PHASE_FILE" 2>/dev/null || echo "Unknown")
        rm -f "$PHASE_FILE"
        log_hook_event "force_branch_check" "清除旧Phase状态: $OLD_PHASE (在main分支上)"

        cat <<EOF >&2

╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  🔄 检测到旧Phase状态（$OLD_PHASE），已自动清除                         ║
║                                                                           ║
║  💡 这通常发生在merge完成后回到main分支                                ║
║                                                                           ║
║  📋 新任务请从Phase 1重新开始（创建feature分支）                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

EOF
    fi

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
    # Show additional guidance using unified functions
    show_branch_naming_guide
    echo "" >&2
    show_phase_workflow
fi

# PrePrompt always exits 0 (warning only)
exit 0
