#!/bin/bash
# Claude Hook: Phase完成验证器
# 触发时机：PostToolUse（工具使用后）
# 目的：Phase完成时自动调用75步验证系统

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
LOG_FILE="$WORKFLOW_DIR/logs/enforcement_violations.log"

mkdir -p "$(dirname "$LOG_FILE")"

# 获取当前Phase
get_current_phase() {
    if [[ -f "$WORKFLOW_DIR/current" ]]; then
        grep "^phase:" "$WORKFLOW_DIR/current" | awk '{print $2}' || echo "P0"
    else
        echo "P0"
    fi
}

# 判断Phase是否完成
is_phase_completed() {
    local phase="$1"

    # 检查Phase完成标记
    case "$phase" in
        "P0")
            # P0完成标志：P0_DISCOVERY.md存在且完整
            [[ -f "$PROJECT_ROOT/docs/P0_DISCOVERY.md" ]] && \
            grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P0_DISCOVERY.md" 2>/dev/null
            ;;
        "P1")
            # P1完成标志：PLAN.md存在且完整
            [[ -f "$PROJECT_ROOT/docs/PLAN.md" ]] && \
            [[ $(wc -l < "$PROJECT_ROOT/docs/PLAN.md") -gt 500 ]]
            ;;
        "P2")
            # P2完成标志：实现代码已提交
            git log -1 --pretty=%B 2>/dev/null | grep -qE "(feat|fix|refactor):"
            ;;
        "P3")
            # P3完成标志：静态检查通过
            [[ -f "$PROJECT_ROOT/scripts/static_checks.sh" ]] && \
            bash "$PROJECT_ROOT/scripts/static_checks.sh" >/dev/null 2>&1
            ;;
        "P4")
            # P4完成标志：REVIEW.md存在
            [[ -f "$PROJECT_ROOT/docs/REVIEW.md" ]] && \
            [[ $(wc -c < "$PROJECT_ROOT/docs/REVIEW.md") -gt 3072 ]]
            ;;
        "P5")
            # P5完成标志：CHANGELOG更新
            [[ -f "$PROJECT_ROOT/CHANGELOG.md" ]] && \
            grep -qE "## \[[0-9]+\.[0-9]+\.[0-9]+\]" "$PROJECT_ROOT/CHANGELOG.md" 2>/dev/null
            ;;
        *)
            return 1
            ;;
    esac
}

# 主函数
main() {
    local tool_name="${TOOL_NAME:-unknown}"

    # 只在Write/Edit工具后触发（表示产出了内容）
    if [[ "$tool_name" != "Write" && "$tool_name" != "Edit" ]]; then
        exit 0
    fi

    # 获取当前Phase
    local current_phase=$(get_current_phase)

    # 检查Phase是否刚刚完成
    if is_phase_completed "$current_phase"; then
        # 检查是否已经验证过（避免重复验证）
        local validation_marker="$WORKFLOW_DIR/validated_${current_phase}"
        if [[ -f "$validation_marker" ]]; then
            exit 0  # 已验证，跳过
        fi

        echo "[phase_completion_validator] Phase $current_phase completed, running 95-step validation..."

        # 调用95步验证系统（升级到v95）
        if [[ -f "$PROJECT_ROOT/scripts/workflow_validator_v95.sh" ]]; then
            if ! bash "$PROJECT_ROOT/scripts/workflow_validator_v95.sh"; then
                # 验证失败，记录日志并阻止
                echo "[$(date +'%F %T')] [phase_completion_validator.sh] [BLOCK] Phase $current_phase validation failed (<80% pass rate)" >> "$LOG_FILE"

                echo "🚨 Phase $current_phase 验证失败！"
                echo "   75步验证系统检测到质量问题"
                echo "   请修复后重试"
                echo ""
                echo "   查看详情: cat .evidence/last_run.json"

                exit 1  # 硬阻止
            fi

            # 验证通过，标记已验证
            touch "$validation_marker"
            echo "[$(date +'%F %T')] [phase_completion_validator.sh] [PASS] Phase $current_phase validation passed" >> "$LOG_FILE"
            echo "✅ Phase $current_phase 验证通过！"
        else
            # 验证脚本不存在，仅警告
            echo "⚠️  Warning: workflow_validator_v95.sh not found"
        fi
    fi

    exit 0
}

# 执行主函数
main "$@"
