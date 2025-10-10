#!/bin/bash
# 修复所有hooks的日志记录 - 使用BASH_SOURCE替代$0

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "修复hooks日志记录..."

# 定义需要修复的hooks
hooks=(
    ".claude/hooks/workflow_auto_start.sh"
    ".claude/hooks/workflow_enforcer.sh"
    ".claude/hooks/smart_agent_selector.sh"
    ".claude/hooks/gap_scan.sh"
    ".claude/hooks/branch_helper.sh"
    ".claude/hooks/quality_gate.sh"
    ".claude/hooks/auto_cleanup_check.sh"
    ".claude/hooks/concurrent_optimizer.sh"
    ".claude/hooks/unified_post_processor.sh"
    ".claude/hooks/agent_error_recovery.sh"
)

fixed_count=0

for hook in "${hooks[@]}"; do
    hook_path="$PROJECT_ROOT/$hook"

    if [[ ! -f "$hook_path" ]]; then
        echo "跳过 $hook (文件不存在)"
        continue
    fi

    # 备份
    cp "$hook_path" "${hook_path}.bak"

    # 修复：将 $(basename $0) 替换为固定的脚本名
    hook_name=$(basename "$hook")

    # 使用sed替换
    sed -i "s/\$(basename \$0)/$hook_name/g" "$hook_path"

    echo "✓ 修复 $hook_name"
    ((fixed_count++))
done

echo
echo "修复完成：$fixed_count个hooks"
echo
echo "验证修复："
grep "triggered by" "$PROJECT_ROOT/.claude/hooks/workflow_auto_start.sh" | head -1
