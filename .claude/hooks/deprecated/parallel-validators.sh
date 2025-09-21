#!/bin/bash
# 并行运行所有验证器

INPUT=$(cat)
FAILED=0

# 创建临时文件存储结果
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# 并行执行验证
{
    echo "$INPUT" | bash .claude/hooks/enforce-multi-agent.sh > "$TMPDIR/multi-agent.out" 2>&1 &
    PID1=$!

    echo "$INPUT" | bash .claude/hooks/agent_validator.sh > "$TMPDIR/validator.out" 2>&1 &
    PID2=$!

    echo "$INPUT" | bash .claude/hooks/context-manager.sh > "$TMPDIR/context.out" 2>&1 &
    PID3=$!

    # 等待所有进程完成
    wait $PID1 || FAILED=1
    wait $PID2 || FAILED=1
    wait $PID3 || FAILED=1
}

# 输出所有结果
cat "$TMPDIR"/*.out >&2

# 如果有任何失败，退出
if [ $FAILED -eq 1 ]; then
    echo "❌ Validation failed" >&2
    exit 2
fi

echo "✅ All validations passed in parallel!" >&2
exit 0