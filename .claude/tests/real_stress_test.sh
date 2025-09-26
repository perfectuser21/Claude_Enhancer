#!/bin/bash
# 真实压力测试 - 找出系统问题

echo "=== 真实压力测试开始 ==="
echo "目标：找出实际问题和性能瓶颈"
echo

# 1. 测试workflow执行器的真实响应时间
echo "1. Workflow执行器真实性能测试"
echo "================================"
for i in {1..5}; do
    echo -n "  第$i次执行validate: "
    START=$(date +%s%3N)
    ./.workflow/executor.sh validate > /dev/null 2>&1
    END=$(date +%s%3N)
    echo "$((END-START))ms"
done

# 2. 测试并发极限
echo
echo "2. 并发极限测试"
echo "==============="
echo -n "  10并发: "
time (for i in {1..10}; do (./.workflow/executor.sh status > /dev/null 2>&1 &); done; wait)

echo -n "  20并发: "
time (for i in {1..20}; do (./.workflow/executor.sh status > /dev/null 2>&1 &); done; wait)

echo -n "  50并发: "
time (for i in {1..50}; do (./.workflow/executor.sh status > /dev/null 2>&1 &); done; wait)

# 3. Hook执行真实测试
echo
echo "3. Hook执行瓶颈测试"
echo "==================="
for hook in workflow_enforcer.sh unified_workflow_orchestrator.sh unified_post_processor.sh; do
    if [ -f ".claude/hooks/$hook" ]; then
        echo -n "  $hook: "
        START=$(date +%s%3N)
        bash ".claude/hooks/$hook" "test" 2>&1 > /dev/null || true
        END=$(date +%s%3N)
        echo "$((END-START))ms"
    fi
done

# 4. 文件I/O压力测试
echo
echo "4. 文件I/O压力测试"
echo "=================="
echo -n "  1000次Phase读取: "
time (for i in {1..1000}; do cat .phase/current > /dev/null; done)

echo -n "  100次workflow状态: "
time (for i in {1..100}; do ./.workflow/executor.sh status > /dev/null 2>&1; done)

# 5. 内存泄露测试
echo
echo "5. 内存监控"
echo "==========="
echo "  初始内存:"
ps aux | grep -E 'workflow|executor' | awk '{sum+=$6} END {print "    " sum/1024 " MB"}'

# 运行一些负载
for i in {1..20}; do
    ./.workflow/executor.sh status > /dev/null 2>&1 &
done
wait

echo "  负载后内存:"
ps aux | grep -E 'workflow|executor' | awk '{sum+=$6} END {print "    " sum/1024 " MB"}'

# 6. 找出最慢的操作
echo
echo "6. 性能瓶颈定位"
echo "==============="
echo "  执行strace跟踪系统调用..."
timeout 2 strace -c ./.workflow/executor.sh status 2>&1 | grep -E "calls|total" | head -5 || echo "    (strace需要权限)"

# 7. 错误处理测试
echo
echo "7. 错误处理和恢复"
echo "=================="
echo -n "  无效Phase处理: "
echo "INVALID" > .phase/current
./.workflow/executor.sh status > /dev/null 2>&1 && echo "未检测到错误!" || echo "正确处理错误"
echo "P3" > .phase/current  # 恢复

echo -n "  并发冲突测试: "
for i in {1..10}; do
    (echo "P$((i%7))" > .phase/current) &
done
wait
echo "完成"

# 8. 实际问题检查
echo
echo "8. 已知问题验证"
echo "==============="
echo -n "  auto_trigger重启问题: "
tail -5 .workflow/auto_trigger.log 2>/dev/null | grep -q "restarting" && echo "❌ 仍在重启" || echo "✅ 正常"

echo -n "  Hook并发警告: "
./.workflow/executor.sh validate 2>&1 | grep -q "Hook过多" && echo "❌ 存在警告" || echo "✅ 无警告"

echo
echo "=== 压力测试完成 ==="