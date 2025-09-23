#!/bin/bash
# 并行运行任务分析器

INPUT=$(cat)
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# 并行分析任务
{
    echo "$INPUT" | bash .claude/hooks/task-type-detector.sh > "$TMPDIR/type.out" 2>&1 &
    PID1=$!

    echo "$INPUT" | bash .claude/hooks/task_analyzer.sh > "$TMPDIR/analyzer.out" 2>&1 &
    PID2=$!

    wait $PID1 $PID2
}

# 合并输出
echo "📊 Task Analysis Results:" >&2
cat "$TMPDIR"/*.out >&2

exit 0