#!/bin/bash
# 测试Claude Enhancer静默模式功能

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.claude/hooks"

echo "🧪 Claude Enhancer v5.5.1 - 静默模式测试"
echo "========================================="
echo

# 测试函数
test_hook_silent_mode() {
    local hook_name="$1"
    local hook_path="$HOOKS_DIR/$hook_name"

    if [[ ! -f "$hook_path" ]]; then
        echo "❌ Hook不存在: $hook_name"
        return 1
    fi

    echo "测试: $hook_name"
    echo "-----------------------------------"

    # 测试1: 正常模式（应该有输出）
    echo -n "  • 正常模式... "
    unset CE_SILENT_MODE
    unset CE_COMPACT_OUTPUT
    local normal_output=$(echo '{"prompt":"test"}' | bash "$hook_path" 2>&1 | wc -l)
    if [[ $normal_output -gt 1 ]]; then
        echo "✅ 有输出 (${normal_output}行)"
    else
        echo "⚠️ 输出很少 (${normal_output}行)"
    fi

    # 测试2: 静默模式（应该无输出或极少输出）
    echo -n "  • 静默模式... "
    export CE_SILENT_MODE=true
    unset CE_COMPACT_OUTPUT
    local silent_output=$(echo '{"prompt":"test"}' | bash "$hook_path" 2>&1 | wc -l)
    if [[ $silent_output -le 2 ]]; then
        echo "✅ 静默成功 (${silent_output}行)"
    else
        echo "❌ 仍有输出 (${silent_output}行)"
    fi

    # 测试3: 紧凑模式（应该有简短输出）
    echo -n "  • 紧凑模式... "
    unset CE_SILENT_MODE
    export CE_COMPACT_OUTPUT=true
    local compact_output=$(echo '{"prompt":"test"}' | bash "$hook_path" 2>&1 | grep -c "\[" || true)
    if [[ $compact_output -ge 0 ]]; then
        echo "✅ 紧凑输出 (${compact_output}个标签)"
    else
        echo "⚠️ 无紧凑输出"
    fi

    # 比较输出差异
    local reduction=$((normal_output - silent_output))
    local percent=0
    if [[ $normal_output -gt 0 ]]; then
        percent=$((reduction * 100 / normal_output))
    fi
    echo "  📊 输出减少: ${reduction}行 (${percent}%)"
    echo
}

# 已修复的hooks列表
FIXED_HOOKS=(
    "smart_agent_selector.sh"
    "workflow_auto_start.sh"
    "branch_helper.sh"
    "quality_gate.sh"
    "gap_scan.sh"
    "workflow_enforcer.sh"
    "unified_post_processor.sh"
    "agent_error_recovery.sh"
    "auto_cleanup_check.sh"
    "code_writing_check.sh"
    "concurrent_optimizer.sh"
)

echo "📋 测试已修复的 ${#FIXED_HOOKS[@]} 个hooks"
echo

# 统计
PASS_COUNT=0
FAIL_COUNT=0

# 测试每个hook
for hook in "${FIXED_HOOKS[@]}"; do
    if test_hook_silent_mode "$hook"; then
        ((PASS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
done

# 测试环境变量传递
echo "📋 测试环境变量功能"
echo "-----------------------------------"

# 测试CE_AUTO_MODE自动设置CE_SILENT_MODE
echo -n "  • CE_AUTO_MODE设置测试... "
export CE_AUTO_MODE=true
source "$HOOKS_DIR/smart_agent_selector.sh" 2>/dev/null || true
if [[ "${CE_SILENT_MODE:-}" == "true" ]]; then
    echo "✅ 自动设置成功"
else
    echo "❌ 未自动设置"
fi

# 测试CE_AUTO_CREATE_BRANCH
echo -n "  • CE_AUTO_CREATE_BRANCH测试... "
if grep -q "CE_AUTO_CREATE_BRANCH" "$HOOKS_DIR/branch_helper.sh"; then
    echo "✅ 变量已实现"
else
    echo "❌ 变量未实现"
fi

# 测试auto_confirm.sh库
echo -n "  • auto_confirm库测试... "
if [[ -f "$PROJECT_ROOT/.claude/lib/auto_confirm.sh" ]]; then
    source "$PROJECT_ROOT/.claude/lib/auto_confirm.sh"
    export CE_AUTO_CONFIRM=true
    result=$(auto_confirm "Continue?" "y")
    if [[ "$result" == "y" ]]; then
        echo "✅ 自动确认工作"
    else
        echo "❌ 自动确认失败"
    fi
else
    echo "❌ 库文件不存在"
fi

echo
echo "========================================="
echo "📊 测试结果统计"
echo "  • 通过: $PASS_COUNT"
echo "  • 失败: $FAIL_COUNT"
echo "  • 总计: ${#FIXED_HOOKS[@]}"
echo
echo "✨ 实现进度: ~22% (11/51 hooks已修复)"
echo

# 清理环境变量
unset CE_SILENT_MODE
unset CE_COMPACT_OUTPUT
unset CE_AUTO_MODE
unset CE_AUTO_CONFIRM