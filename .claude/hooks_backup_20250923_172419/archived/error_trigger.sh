#!/bin/bash
# Claude Enhancer 错误触发器
# 如果不满足要求，触发各种错误尝试中断执行

INPUT=$(cat)
AGENT_COUNT=$(echo "$INPUT" | grep -c '"subagent_type"' 2>/dev/null || echo 0)
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 | head -1 || echo "")

MIN_REQUIRED=3
if echo "$TASK_DESC" | grep -qiE "login|auth|认证|登录"; then
    MIN_REQUIRED=5
elif echo "$TASK_DESC" | grep -qiE "api|接口"; then
    MIN_REQUIRED=4
fi

if [ "$AGENT_COUNT" -lt "$MIN_REQUIRED" ]; then
    echo "💣 TRIGGERING ERRORS - Need $MIN_REQUIRED agents" >&2

    # 策略1: 填满stderr
    for i in {1..1000}; do
        echo "ERROR ERROR ERROR ERROR ERROR ERROR ERROR ERROR" >&2
    done

    # 策略2: 返回巨大输出尝试造成问题
    perl -e 'print "X" x 1000000'

    # 策略3: 触发除零错误
    echo $((1/0)) 2>/dev/null || true

    # 策略4: 使用不存在的命令
    nonexistent_command_to_trigger_error 2>/dev/null || true

    # 策略5: 返回特殊字符可能破坏解析
    echo $'\x00\x01\x02\x03\x04\x05\x06\x07\x08'

    # 最后返回错误
    exit 127  # 命令未找到
else
    echo "✅ OK: $AGENT_COUNT agents" >&2
    echo "$INPUT"
    exit 0
fi