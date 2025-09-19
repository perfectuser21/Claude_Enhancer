#!/bin/bash
# Perfect21 Master Hook
# 主控制器，协调所有Perfect21 hooks

set -e

# 读取输入
INPUT=$(cat)

# Hook文件路径
HOOKS_DIR="/home/xx/dev/Perfect21/.claude/hooks"

# 定义hook执行顺序和条件
declare -a HOOKS_SEQUENCE=(
    "perfect21_workflow.sh"            # 0. 工作流协调器
    "perfect21_task_analyzer.sh"       # 1. 分析任务类型
    "perfect21_agent_validator.sh"     # 2. 验证Agent选择
    "perfect21_parallel_checker.sh"    # 3. 检查并行执行
    "perfect21_quality_gates.sh"       # 4. 质量门检查
    "perfect21_git_bridge.sh"          # 5. Git集成桥接
)

# 日志文件
LOG_FILE="/tmp/perfect21_master.log"
ERROR_LOG="/tmp/perfect21_errors.log"

# 记录开始
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Perfect21 Hook执行开始 ===" >> "$LOG_FILE"

# 执行状态
EXECUTION_STATUS="SUCCESS"
BLOCKED=false
WARNINGS=""

# 临时文件存储中间结果
TEMP_INPUT="/tmp/perfect21_input_$$"
echo "$INPUT" > "$TEMP_INPUT"

# 执行hook链
for hook in "${HOOKS_SEQUENCE[@]}"; do
    HOOK_PATH="$HOOKS_DIR/$hook"

    if [ ! -f "$HOOK_PATH" ]; then
        echo "⚠️ Hook文件不存在: $hook" >&2
        continue
    fi

    if [ ! -x "$HOOK_PATH" ]; then
        chmod +x "$HOOK_PATH"
    fi

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行: $hook" >> "$LOG_FILE"

    # 执行hook并捕获输出
    if cat "$TEMP_INPUT" | bash "$HOOK_PATH" > "${TEMP_INPUT}.out" 2>"${TEMP_INPUT}.err"; then
        # Hook执行成功
        mv "${TEMP_INPUT}.out" "$TEMP_INPUT"

        # 收集stderr中的警告信息
        if [ -s "${TEMP_INPUT}.err" ]; then
            WARNINGS="${WARNINGS}$(cat ${TEMP_INPUT}.err)\n"
        fi
    else
        # Hook执行失败（阻止执行）
        EXIT_CODE=$?
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Hook阻止: $hook (exit code: $EXIT_CODE)" >> "$LOG_FILE"

        # 输出错误信息
        if [ -s "${TEMP_INPUT}.err" ]; then
            cat "${TEMP_INPUT}.err" >&2
        fi

        # 记录错误
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hook: $hook" >> "$ERROR_LOG"
        [ -s "${TEMP_INPUT}.err" ] && cat "${TEMP_INPUT}.err" >> "$ERROR_LOG"

        BLOCKED=true
        EXECUTION_STATUS="BLOCKED by $hook"

        # 清理临时文件
        rm -f "$TEMP_INPUT" "${TEMP_INPUT}.out" "${TEMP_INPUT}.err"

        # 如果被阻止，停止执行链
        exit $EXIT_CODE
    fi

    # 清理错误文件
    rm -f "${TEMP_INPUT}.err"
done

# 输出所有警告信息
if [ -n "$WARNINGS" ]; then
    echo -e "$WARNINGS" >&2
fi

# 输出最终结果
cat "$TEMP_INPUT"

# 清理临时文件
rm -f "$TEMP_INPUT" "${TEMP_INPUT}.out" "${TEMP_INPUT}.err"

# 记录完成
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 执行完成: $EXECUTION_STATUS ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit 0