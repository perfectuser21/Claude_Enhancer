#!/bin/bash
# Perfect21 Parallel Execution Checker
# 验证是否正确使用并行执行

set -e

# 读取输入
INPUT=$(cat)

# 检测是否包含多个Task调用
TASK_COUNT=$(echo "$INPUT" | grep -c '"Task"' || echo 0)

if [ "$TASK_COUNT" -le 1 ]; then
    # 单个或无Task调用，直接放行
    echo "$INPUT"
    exit 0
fi

# 检查是否在同一个function_calls块中
IN_SINGLE_BLOCK=false

# 检查是否有function_calls标签
if echo "$INPUT" | grep -q "<function_calls>" || echo "$INPUT" | grep -q "<function_calls>"; then
    # 计算function_calls块的数量
    BLOCK_COUNT=$(echo "$INPUT" | grep -c "<.*function_calls>" || echo 1)

    # 计算每个块中的Task数量
    if [ "$BLOCK_COUNT" -eq 1 ] && [ "$TASK_COUNT" -gt 1 ]; then
        IN_SINGLE_BLOCK=true
    fi
fi

# 分析Task调用模式
analyze_pattern() {
    local input="$1"

    # 提取Task调用的行号
    TASK_LINES=$(echo "$input" | grep -n "Task" | cut -d: -f1)

    if [ -z "$TASK_LINES" ]; then
        return
    fi

    # 计算最大和最小行号差
    MIN_LINE=$(echo "$TASK_LINES" | head -1)
    MAX_LINE=$(echo "$TASK_LINES" | tail -1)
    LINE_DIFF=$((MAX_LINE - MIN_LINE))

    # 如果Task调用相距超过100行，可能是顺序执行
    if [ "$LINE_DIFF" -gt 100 ] && [ "$TASK_COUNT" -gt 1 ]; then
        echo "sequential"
    else
        echo "parallel"
    fi
}

PATTERN=$(analyze_pattern "$INPUT")

# 如果检测到顺序执行模式
if [ "$PATTERN" = "sequential" ] && [ "$TASK_COUNT" -gt 1 ]; then
    echo "⚠️ Perfect21 规则违反：检测到顺序执行" >&2
    echo "" >&2
    echo "📊 检测结果：" >&2
    echo "  • 发现 $TASK_COUNT 个Task调用" >&2
    echo "  • 执行模式：顺序执行 ❌" >&2
    echo "" >&2
    echo "❌ 错误示例（当前做法）：" >&2
    echo "  调用Agent1..." >&2
    echo "  等待结果..." >&2
    echo "  调用Agent2..." >&2
    echo "  等待结果..." >&2
    echo "" >&2
    echo "✅ 正确做法（并行执行）：" >&2
    echo '  <function_calls>' >&2
    echo '    <invoke name="Task">agent1...</invoke>' >&2
    echo '    <invoke name="Task">agent2...</invoke>' >&2
    echo '    <invoke name="Task">agent3...</invoke>' >&2
    echo '  </function_calls>' >&2
    echo "" >&2
    echo "💡 优势：" >&2
    echo "  • 执行速度提升3-5倍" >&2
    echo "  • 获得多角度分析" >&2
    echo "  • 更全面的解决方案" >&2
    echo "" >&2
    echo "🔄 请重新组织：将所有Task调用放在同一个function_calls块中" >&2

    # 不强制阻止，但给出强烈警告
    # exit 1
fi

# 如果是并行执行，给予肯定
if [ "$IN_SINGLE_BLOCK" = true ] && [ "$TASK_COUNT" -gt 1 ]; then
    echo "✅ Perfect21: 检测到正确的并行执行模式 ($TASK_COUNT agents)" >&2
fi

# 记录执行模式
LOG_FILE="/tmp/perfect21_parallel_log.txt"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tasks: $TASK_COUNT, Pattern: $PATTERN, Block: $IN_SINGLE_BLOCK" >> "$LOG_FILE"

# 输出原始内容
echo "$INPUT"
exit 0