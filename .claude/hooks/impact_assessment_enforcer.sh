#!/bin/bash
# Claude Hook: Impact Assessment强制执行器
# 触发时机：PrePrompt（Phase 2完成后，Phase 3开始前）
# 目的：强制执行Impact Radius评估

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
LOG_FILE="$WORKFLOW_DIR/logs/enforcement_violations.log"

mkdir -p "$(dirname "$LOG_FILE")"

# 检查当前Phase
get_current_phase() {
    if [[ -f "$WORKFLOW_DIR/current" ]]; then
        grep "^phase:" "$WORKFLOW_DIR/current" | awk '{print $2}' || echo "P1"
    else
        echo "P1"
    fi
}

# 检查Phase 2 (Discovery)是否完成
is_phase2_completed() {
    [[ -f "$PROJECT_ROOT/docs/P2_DISCOVERY.md" ]] && \
    grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P2_DISCOVERY.md" 2>/dev/null
}

# 检查Impact Assessment是否已执行
is_impact_assessed() {
    [[ -f "$WORKFLOW_DIR/impact_assessments/current.json" ]] && \
    grep -q "impact_radius_score" "$WORKFLOW_DIR/impact_assessments/current.json" 2>/dev/null
}

# 主函数
main() {
    local current_phase=$(get_current_phase)

    # 只在P2 (Discovery)完成后、P3 (Planning+Architecture)开始前触发
    if [[ "$current_phase" == "P2" ]] && is_phase2_completed; then
        # 检查是否已评估
        if ! is_impact_assessed; then
            echo "🚨 Phase 2 (Discovery)完成后必须进行Impact Radius评估！"
            echo "   这将自动计算任务的风险、复杂度和影响范围"
            echo "   并推荐最优的Agent数量（0/3/6 agents）"
            echo ""

            # 记录enforcement日志
            echo "[$(date +'%F %T')] [impact_assessment_enforcer.sh] [BLOCK] Impact Assessment not performed after Phase 2" >> "$LOG_FILE"

            # 尝试自动调用Impact Assessment
            if [[ -f "$PROJECT_ROOT/.claude/hooks/smart_agent_selector.sh" ]]; then
                echo "📊 正在自动执行Impact Assessment..."
                if bash "$PROJECT_ROOT/.claude/hooks/smart_agent_selector.sh"; then
                    echo "✅ Impact Assessment完成！"
                    echo "[$(date +'%F %T')] [impact_assessment_enforcer.sh] [AUTO_FIX] Impact Assessment auto-executed successfully (Phase 2)" >> "$LOG_FILE"
                    exit 0
                else
                    echo "❌ Impact Assessment自动执行失败"
                    echo "💡 请检查 smart_agent_selector.sh 脚本"
                    exit 1
                fi
            else
                # 脚本不存在，硬阻止
                echo "❌ smart_agent_selector.sh not found"
                echo "   请手动创建 .workflow/impact_assessments/current.json"
                echo "   或安装 smart_agent_selector.sh 脚本"
                exit 1
            fi
        fi
    fi

    # 其他情况放行
    exit 0
}

# 执行主函数
main "$@"
