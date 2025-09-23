#!/bin/bash
# 并行运行验证器 - 建议模式（不阻止执行）

INPUT=$(cat)

# 创建临时文件存储结果
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# 并行执行验证（忽略错误）
{
    echo "$INPUT" | bash .claude/hooks/agent_validator_advisory.sh > "$TMPDIR/validator.out" 2>&1 &
    PID1=$!

    # 其他验证器也可以添加（建议模式）

    # 等待所有进程
    wait $PID1
}

# 输出所有结果
cat "$TMPDIR"/*.out >&2

# 总是返回成功
echo "✅ Validation complete (advisory mode)" >&2
exit 0