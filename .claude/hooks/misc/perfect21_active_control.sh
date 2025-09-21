#!/bin/bash
# Perfect21/Claude Enhancer 主动控制Hook
# 不再被动等待，而是主动控制执行流程

set -e

INPUT=$(cat)

# 使用Python控制器分析和纠正
RESULT=$(echo "$INPUT" | python3 /home/xx/dev/Perfect21/perfect21_controller.py 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    # 违规且无法纠正
    echo "🚨 Perfect21 Control: Execution Blocked" >&2
    echo "$RESULT" >&2

    # 返回一个空的但有效的JSON，阻止原始执行
    echo '{"perfect21_blocked": true}'
    exit 2
else
    # 返回纠正后的请求或原始请求
    echo "$RESULT"
    exit 0
fi