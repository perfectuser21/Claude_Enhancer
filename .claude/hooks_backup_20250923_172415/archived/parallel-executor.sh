#!/bin/bash
# 并行执行多个hooks

# 接收输入
INPUT=$(cat)

# 并行执行所有验证
{
    echo "$INPUT" | bash .claude/hooks/enforce-multi-agent.sh &
    PID1=$!

    echo "$INPUT" | bash .claude/hooks/context-manager.sh &
    PID2=$!

    # 等待所有进程
    wait $PID1 $PID2
} 2>&1

# 检查退出码
if [ $? -ne 0 ]; then
    exit 2
fi

echo "✅ All validations passed"