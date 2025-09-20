#!/bin/bash
# Enforce Multi-Agent Rule
# 强制使用至少3个Agent

set -e

# 读取输入
INPUT=$(cat)

# 检查是否是Task调用
if ! echo "$INPUT" | grep -q '"name"\s*:\s*"Task"'; then
    # 不是Task调用，直接通过
    echo "$INPUT"
    exit 0
fi

# 提取所有agent types
AGENTS=$(echo "$INPUT" | grep -oP '"subagent_type"\s*:\s*"[^"]+' | cut -d'"' -f4 | sort -u)
AGENT_COUNT=$(echo "$AGENTS" | grep -c . || echo 0)

# 最少Agent数量要求
MIN_AGENTS=3

# 检查Agent数量
if [ $AGENT_COUNT -lt $MIN_AGENTS ]; then
    echo "❌ BLOCKED: 违反多Agent并行规则！" >&2
    echo "" >&2
    echo "当前只有 $AGENT_COUNT 个Agent，必须至少使用 $MIN_AGENTS 个Agent！" >&2
    echo "" >&2
    echo "正确示例：" >&2
    echo "<function_calls>" >&2
    echo "  <invoke name=\"Task\">" >&2
    echo "    <parameter name=\"subagent_type\">backend-architect</parameter>" >&2
    echo "  </invoke>" >&2
    echo "  <invoke name=\"Task\">" >&2
    echo "    <parameter name=\"subagent_type\">frontend-specialist</parameter>" >&2
    echo "  </invoke>" >&2
    echo "  <invoke name=\"Task\">" >&2
    echo "    <parameter name=\"subagent_type\">test-engineer</parameter>" >&2
    echo "  </invoke>" >&2
    echo "</function_calls>" >&2
    echo "" >&2
    echo "强制要求：必须在同一个function_calls块中调用多个Agent！" >&2
    exit 2  # Exit code 2 会阻止执行
fi

# 通过检查，输出原始内容
echo "$INPUT"