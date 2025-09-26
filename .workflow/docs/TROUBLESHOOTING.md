# Claude Enhancer 5.1 故障排查指南

## 🔴 常见问题快速解决

### 1. Workflow Enforcer阻断操作

**现象**：
```
⚠️ 检测到编程任务，但未按工作流执行！
🚫 操作已阻塞！请按工作流执行。
```

**原因**：直接跳到编码阶段，没有从P0开始

**解决**：
```bash
# 1. 创建feature分支（P0）
git checkout -b feature/your-feature

# 2. 设置初始阶段
echo "P1" > .phase/current

# 3. 按照正常流程执行
# P1 → 需求分析
# P2 → 设计规划
# P3 → 编码实现
```

### 2. Validate命令执行缓慢

**现象**：`validate`命令超过500ms

**原因**：
1. 缓存未命中
2. 文件变更导致缓存失效
3. 磁盘IO慢

**解决**：
```bash
# 1. 检查缓存状态
python .workflow/executor/executor.py cache-stats

# 2. 预热缓存
for phase in P1 P2 P3 P4 P5 P6; do
    python .workflow/executor/executor.py validate --phase $phase
done

# 3. 优化IO（使用SSD或内存盘）
mount -t tmpfs -o size=100M tmpfs .workflow/executor/cache
```

### 3. Agent调用失败

**现象**：
```
Error: SubAgent cannot call other SubAgents
```

**原因**：SubAgent尝试调用其他SubAgent

**解决**：
```xml
<!-- 错误：SubAgent A调用SubAgent B -->
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">backend-architect</parameter>
    <parameter name="prompt">
      请调用api-designer设计API  ❌
    </parameter>
  </invoke>
</function_calls>

<!-- 正确：Claude Code同时调用多个Agent -->
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">backend-architect</parameter>
    <parameter name="prompt">设计后端架构</parameter>
  </invoke>
  <invoke name="Task">
    <parameter name="subagent_type">api-designer</parameter>
    <parameter name="prompt">设计API接口</parameter>
  </invoke>
</function_calls>
```

### 4. Git Hooks未生效

**现象**：提交代码时没有触发检查

**原因**：Git Hooks未正确安装

**解决**：
```bash
# 1. 检查Hooks目录
ls -la .git/hooks/

# 2. 重新安装
bash .claude/install_git_hooks.sh

# 3. 手动复制（如果脚本失败）
cp .claude/git_hooks/pre-commit .git/hooks/
cp .claude/git_hooks/commit-msg .git/hooks/
cp .claude/git_hooks/pre-push .git/hooks/
chmod +x .git/hooks/*

# 4. 测试Hooks
git commit --dry-run -m "test"
```

### 5. 监听器不响应文件变化

**现象**：修改文件后没有自动触发验证

**原因**：
1. inotify限制达到上限
2. 监听器未启动
3. 文件在忽略列表中

**解决**：
```bash
# 1. 增加inotify限制
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl -p

# 2. 重启监听器
pkill -f watcher.py
python .workflow/executor/watcher.py --daemon

# 3. 检查监听状态
ps aux | grep watcher.py
tail -f .workflow/events.jsonl
```

### 6. Phase推进失败

**现象**：无法从P3推进到P4

**原因**：当前阶段Gate未通过

**解决**：
```bash
# 1. 查看具体失败原因
python .workflow/executor/executor.py validate --phase P3

# 2. 检查Gate文件
ls -la .gates/
# 应该看到: 01.ok, 02.ok, 03.ok

# 3. 手动修复（仅紧急情况）
touch .gates/03.ok

# 4. 重试推进
python .workflow/executor/executor.py advance
```

## 🔍 深度排查

### 1. 性能分析

```python
# performance_analysis.py
import json
import statistics
from pathlib import Path

def analyze_performance():
    metrics_file = Path(".workflow/metrics.jsonl")
    
    with open(metrics_file) as f:
        metrics = [json.loads(line) for line in f]
    
    # 分析validate性能
    validate_times = [m['validate_ms'] for m in metrics]
    
    print(f"⚡ Validate性能分析:")
    print(f"  平均: {statistics.mean(validate_times):.2f}ms")
    print(f"  中位数: {statistics.median(validate_times):.2f}ms")
    print(f"  P95: {statistics.quantiles(validate_times, n=20)[18]:.2f}ms")
    print(f"  P99: {statistics.quantiles(validate_times, n=100)[98]:.2f}ms")
    
    # 分析缓存命中率
    cache_hits = sum(1 for m in metrics if m['cache_hit'])
    hit_rate = cache_hits / len(metrics) * 100
    
    print(f"\n🎯 缓存命中率: {hit_rate:.1f}%")
    
    # 分析阶段分布
    phase_counts = {}
    for m in metrics:
        phase = m['phase']
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
    
    print(f"\n📈 阶段分布:")
    for phase, count in sorted(phase_counts.items()):
        print(f"  {phase}: {count} ({count/len(metrics)*100:.1f}%)")

if __name__ == "__main__":
    analyze_performance()
```

### 2. 日志分析

```bash
# 查找错误
grep -r "ERROR\|FAIL\|Exception" .workflow/ --include="*.log"

# 查看最近的事件
tail -n 50 .workflow/events.jsonl | jq '.'

# 统计事件类型
jq -r '.event_type' .workflow/events.jsonl | sort | uniq -c

# 找出慢查询
jq 'select(.validate_ms > 500)' .workflow/metrics.jsonl
```

### 3. 系统资源检查

```bash
#!/bin/bash
# system_check.sh

echo "📊 系统资源检查"
echo "=================="

# CPU使用
echo -n "CPU使用: "
top -bn1 | grep "Cpu(s)" | awk '{print $2}'

# 内存使用
echo -n "内存使用: "
free -h | awk '/^Mem:/ {print $3 "/" $2}'

# 磁盘使用
echo -n "磁盘使用: "
df -h . | awk 'NR==2 {print $3 "/" $2}'

# Python进程
echo -e "\nPython进程:"
ps aux | grep python | grep -E "executor|watcher" | awk '{print $2, $11}'

# inotify watches
echo -e "\ninotify watches:"
find .workflow -type f -name "*.py" | wc -l
echo -n "当前/上限: "
cat /proc/sys/fs/inotify/max_user_watches
```

### 4. 网络连接检查

```bash
# 检查端口占用
netstat -tlnp | grep python

# 检查连接数
ss -s

# 检查网络延迟
ping -c 10 localhost | tail -1
```

## 💊 恢复方案

### 1. 紧急重置

```bash
#!/bin/bash
# emergency_reset.sh

echo "🆘 执行紧急重置..."

# 停止所有进程
echo "1. 停止进程"
pkill -f "executor|watcher"
sleep 2

# 备份当前状态
echo "2. 备份状态"
tar -czf emergency-backup-$(date +%Y%m%d-%H%M%S).tar.gz \
    .phase/ .gates/ .tickets/ .workflow/

# 重置状态
echo "3. 重置状态"
rm -rf .workflow/executor/cache/*
rm -f .gates/*.ok
rm -f .tickets/*.todo
echo "P1" > .phase/current

# 清理日志
echo "4. 清理日志"
> .workflow/metrics.jsonl
> .workflow/events.jsonl
find .workflow -name "*.log" -exec truncate -s 0 {} \;

# 重启服务
echo "5. 重启服务"
python .workflow/executor/watcher.py --daemon

echo "✅ 重置完成"
```

### 2. 数据恢复

```bash
#!/bin/bash
# data_recovery.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 恢复数据中..."

# 停止服务
pkill -f "executor|watcher"

# 解压备份
tar -xzf "$BACKUP_FILE"

# 验证恢复
python .workflow/executor/executor.py status

# 重启服务
python .workflow/executor/watcher.py --daemon

echo "✅ 数据恢复完成"
```

### 3. 版本回滚

```bash
#!/bin/bash
# version_rollback.sh

PREVIOUS_VERSION="5.0"

echo "⚠️ 回滚到版本 $PREVIOUS_VERSION"

# 备份当前版本
cp -r .claude .claude.current
cp -r .workflow .workflow.current

# 回滚到之前版本
git checkout tags/v$PREVIOUS_VERSION -- .claude/
git checkout tags/v$PREVIOUS_VERSION -- .workflow/

# 重新安装依赖
pip install -r .workflow/requirements.txt

# 重启服务
pkill -f "executor|watcher"
python .workflow/executor/watcher.py --daemon

echo "✅ 已回滚到版本 $PREVIOUS_VERSION"
```

## 📋 检查清单

### 日常检查
- [ ] 监听器进程存活
- [ ] 缓存命中率 > 80%
- [ ] validate响应 < 250ms
- [ ] 磁盘空间 > 20%
- [ ] 内存使用 < 1GB

### 周检查
- [ ] 清理过期缓存
- [ ] 压缩日志文件
- [ ] 备份工作流状态
- [ ] 更新依赖包
- [ ] 分析性能报告

### 月检查
- [ ] 系统安全扫描
- [ ] 依赖漏洞检查
- [ ] 性能基准测试
- [ ] 恢复流程演练
- [ ] 文档更新

## 🆘 获取帮助

### 调试模式
```bash
# 开启调试
export PYTHON_DEBUG=1
export LOG_LEVEL=DEBUG

# 运行命令
python -v .workflow/executor/executor.py validate
```

### 日志级别
```python
# 修改.workflow/config.yml
environment:
  LOG_LEVEL: "DEBUG"  # INFO, WARNING, ERROR
```

### 联系支持
- 查看[RUNBOOK.md](./RUNBOOK.md)获取操作指南
- 查看[WORKFLOW_RULES.md](./WORKFLOW_RULES.md)了解规则
- GitHub Issues: [your-repo/issues]
- 邮件: support@claude-enhancer.com