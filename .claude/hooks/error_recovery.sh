#!/bin/bash
# 错误恢复助手
echo "ℹ️ Error recovery helper activated"

# 错误恢复策略
echo "💡 错误恢复策略:"

# 检查最近的错误日志
if [ -f "watcher.log" ]; then
    errors=$(grep -c ERROR watcher.log 2>/dev/null || echo "0")
    if [ "$errors" -gt 0 ]; then
        echo "  ⚠️ 发现${errors}个错误，查看watcher.log"
    fi
fi

# 检查系统状态
echo "  系统状态检查:"

# Phase状态
if [ -f ".phase/current" ]; then
    phase=$(cat .phase/current)
    echo "    - 当前Phase: $phase"
else
    echo "    - ⚠️ Phase文件缺失"
fi

# Gates状态
gate_count=$(ls .gates/*.ok 2>/dev/null | wc -l)
echo "    - Gates通过: ${gate_count}/6"

# 建议的恢复操作
echo "  恢复建议:"
echo "    1. 检查.phase/current是否正确"
echo "    2. 验证.gates/*.ok文件完整"
echo "    3. 清理.tickets/*.todo僵尸任务"
echo "    4. 重启watcher进程"

# 提供快速修复命令
echo "  快速修复:"
echo "    - 重置到P1: echo 'P1' > .phase/current"
echo "    - 清理tickets: rm -f .tickets/*.todo"
echo "    - 重启watcher: pkill -f watcher.py && nohup python3 .workflow/executor/watcher.py &"
