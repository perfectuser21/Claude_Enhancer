#!/bin/bash
# Enforce Parallel Execution Rule
# 强制并行执行

set -e

# 读取输入
INPUT=$(cat)

# 检查是否包含Task调用
if ! echo "$INPUT" | grep -q '"name"\s*:\s*"Task"'; then
    # 不是Task调用，直接通过
    echo "$INPUT"
    exit 0
fi

# 检查是否在function_calls块中
if ! echo "$INPUT" | grep -q '<function_calls>'; then
    # 检查是否有多个独立的invoke
    INVOKE_COUNT=$(echo "$INPUT" | grep -c '<invoke' || echo 0)

    if [ $INVOKE_COUNT -gt 1 ]; then
        echo "❌ BLOCKED: 禁止顺序执行Agent！" >&2
        echo "" >&2
        echo "错误：检测到多个Agent分开调用（顺序执行）" >&2
        echo "所有Agent必须在同一个<function_calls>块中并行执行！" >&2
        echo "" >&2
        echo "❌ 错误方式（顺序）：" >&2
        echo "  <invoke>agent1</invoke>" >&2
        echo "  ...其他代码..." >&2
        echo "  <invoke>agent2</invoke>" >&2
        echo "" >&2
        echo "✅ 正确方式（并行）：" >&2
        echo "<function_calls>" >&2
        echo "  <invoke>agent1</invoke>" >&2
        echo "  <invoke>agent2</invoke>" >&2
        echo "  <invoke>agent3</invoke>" >&2
        echo "</function_calls>" >&2
        echo "" >&2
        echo "强制要求：所有Agent必须并行执行以提高效率！" >&2
        exit 2  # Exit code 2 强制阻止执行
    fi
fi

# 输出原始内容
echo "$INPUT"