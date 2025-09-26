#!/bin/bash
echo "=== Claude Enhancer 5.1 最小压力测试 ==="

echo "1. 基础测试"
for i in {1..10}; do
    echo -n "$i "
    cat .phase/current > /dev/null 2>&1 || echo "失败"
done
echo

echo "2. 并发测试(50个进程)"
for i in {1..50}; do
    (cat .phase/current > /dev/null 2>&1) &
done
wait
echo "✅ 并发完成"

echo "3. 批量测试(1000次)"
START=$(date +%s)
for i in {1..1000}; do
    [ -f .phase/current ] || true
done
END=$(date +%s)
echo "✅ 1000次查询用时: $((END-START))秒"

echo "4. Hook测试"
bash .claude/hooks/workflow_enforcer.sh 'test' 2>&1 | grep -q "工作流强制执行" && echo "✅ Hook正常工作" || echo "❌ Hook失败"

echo "=== 测试完成 ==="
