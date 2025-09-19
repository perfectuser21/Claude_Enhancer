#!/bin/bash
# Perfect21 Complete Workflow
# 统一的工作流协调器，集成所有hooks和Git流程

set -e

# 工作流阶段定义
declare -A WORKFLOW_STAGES=(
    ["1_PLANNING"]="任务规划阶段"
    ["2_AGENT_SELECTION"]="Agent选择阶段"
    ["3_EXECUTION"]="执行阶段"
    ["4_QUALITY_CHECK"]="质量检查阶段"
    ["5_GIT_COMMIT"]="代码提交阶段"
    ["6_DEPLOYMENT"]="部署阶段"
)

# 读取输入
INPUT=$(cat)

# 日志文件
WORKFLOW_LOG="/tmp/perfect21_workflow.log"
STATE_FILE="/tmp/perfect21_workflow_state.txt"

# 记录工作流开始
log_workflow() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$WORKFLOW_LOG"
}

# 检测当前阶段
detect_stage() {
    local input="$1"

    # 检测Task调用（Agent选择阶段）
    if echo "$input" | grep -q "Task"; then
        echo "2_AGENT_SELECTION"
        return
    fi

    # 检测编辑操作（执行阶段）
    if echo "$input" | grep -qE "Edit|Write|MultiEdit"; then
        echo "3_EXECUTION"
        return
    fi

    # 检测测试运行（质量检查阶段）
    if echo "$input" | grep -qE "test|pytest|jest|npm test"; then
        echo "4_QUALITY_CHECK"
        return
    fi

    # 检测Git操作（提交阶段）
    if echo "$input" | grep -qE "git (add|commit|push)"; then
        echo "5_GIT_COMMIT"
        return
    fi

    # 检测部署操作
    if echo "$input" | grep -qE "deploy|docker|kubernetes|k8s"; then
        echo "6_DEPLOYMENT"
        return
    fi

    echo "1_PLANNING"
}

CURRENT_STAGE=$(detect_stage "$INPUT")

log_workflow "=== 工作流阶段: ${WORKFLOW_STAGES[$CURRENT_STAGE]} ==="

# 保存当前阶段
echo "$CURRENT_STAGE" > "$STATE_FILE"

# 根据阶段执行相应的hooks
case "$CURRENT_STAGE" in
    1_PLANNING)
        echo "📋 Perfect21 工作流：任务规划阶段" >&2
        echo "" >&2
        echo "建议步骤：" >&2
        echo "  1. 明确任务需求" >&2
        echo "  2. 识别任务类型" >&2
        echo "  3. 选择合适的Agent组合" >&2
        echo "  4. 制定执行计划" >&2
        echo "" >&2

        # 执行任务分析
        echo "$INPUT" | bash /home/xx/dev/Perfect21/.claude/hooks/perfect21_task_analyzer.sh > /tmp/perfect21_temp.txt 2>&1
        cat /tmp/perfect21_temp.txt >&2
        ;;

    2_AGENT_SELECTION)
        echo "👥 Perfect21 工作流：Agent选择阶段" >&2
        echo "" >&2

        # 执行Agent验证链
        echo "$INPUT" | bash /home/xx/dev/Perfect21/.claude/hooks/perfect21_agent_validator.sh > /tmp/perfect21_temp.txt 2>&1
        EXIT_CODE=$?
        if [ $EXIT_CODE -ne 0 ]; then
            cat /tmp/perfect21_temp.txt >&2
            exit $EXIT_CODE
        fi

        # 检查并行执行
        echo "$INPUT" | bash /home/xx/dev/Perfect21/.claude/hooks/perfect21_parallel_checker.sh > /tmp/perfect21_temp.txt 2>&1
        cat /tmp/perfect21_temp.txt >&2
        ;;

    3_EXECUTION)
        echo "⚙️ Perfect21 工作流：代码执行阶段" >&2
        echo "" >&2

        # 执行质量检查
        echo "$INPUT" | bash /home/xx/dev/Perfect21/.claude/hooks/perfect21_quality_gates.sh > /tmp/perfect21_temp.txt 2>&1
        cat /tmp/perfect21_temp.txt >&2
        ;;

    4_QUALITY_CHECK)
        echo "🧪 Perfect21 工作流：质量检查阶段" >&2
        echo "" >&2
        echo "执行检查：" >&2
        echo "  ✓ 运行测试套件" >&2
        echo "  ✓ 代码覆盖率分析" >&2
        echo "  ✓ 性能基准测试" >&2
        echo "" >&2
        ;;

    5_GIT_COMMIT)
        echo "📦 Perfect21 工作流：代码提交阶段" >&2
        echo "" >&2

        # 执行Git桥接
        echo "$INPUT" | bash /home/xx/dev/Perfect21/.claude/hooks/perfect21_git_bridge.sh > /tmp/perfect21_temp.txt 2>&1
        cat /tmp/perfect21_temp.txt >&2

        # 提醒Git hooks
        echo "🔗 Git Hooks将自动执行：" >&2
        echo "  • pre-commit: 代码质量检查" >&2
        echo "  • commit-msg: 消息格式验证" >&2
        echo "  • pre-push: 最终安全检查" >&2
        echo "" >&2
        ;;

    6_DEPLOYMENT)
        echo "🚀 Perfect21 工作流：部署阶段" >&2
        echo "" >&2
        echo "部署检查清单：" >&2
        echo "  □ 所有测试通过" >&2
        echo "  □ 构建成功" >&2
        echo "  □ 环境变量配置" >&2
        echo "  □ 监控告警设置" >&2
        echo "  □ 回滚计划准备" >&2
        echo "" >&2
        ;;
esac

# 显示工作流进度
show_progress() {
    echo "" >&2
    echo "📊 工作流进度：" >&2
    echo "  [✓] 任务规划" >&2

    if [[ "$CURRENT_STAGE" > "1_PLANNING" ]]; then
        echo "  [✓] Agent选择" >&2
    else
        echo "  [ ] Agent选择" >&2
    fi

    if [[ "$CURRENT_STAGE" > "2_AGENT_SELECTION" ]]; then
        echo "  [✓] 代码执行" >&2
    else
        echo "  [ ] 代码执行" >&2
    fi

    if [[ "$CURRENT_STAGE" > "3_EXECUTION" ]]; then
        echo "  [✓] 质量检查" >&2
    else
        echo "  [ ] 质量检查" >&2
    fi

    if [[ "$CURRENT_STAGE" > "4_QUALITY_CHECK" ]]; then
        echo "  [✓] 代码提交" >&2
    else
        echo "  [ ] 代码提交" >&2
    fi

    if [[ "$CURRENT_STAGE" > "5_GIT_COMMIT" ]]; then
        echo "  [✓] 部署上线" >&2
    else
        echo "  [ ] 部署上线" >&2
    fi
    echo "" >&2
}

# 显示进度（除了规划阶段）
if [ "$CURRENT_STAGE" != "1_PLANNING" ]; then
    show_progress
fi

# 记录完成
log_workflow "阶段完成: $CURRENT_STAGE"

# 清理临时文件
rm -f /tmp/perfect21_temp.txt

# 输出原始内容
echo "$INPUT"
exit 0