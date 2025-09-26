# Claude Enhancer 5.1 运维手册

## 🚀 快速启动

### 1. 安装依赖
```bash
# Python依赖
pip install rich pydantic orjson pyyaml inotify

# 系统依赖
sudo apt-get install inotify-tools  # Ubuntu/Debian
sudo yum install inotify-tools      # CentOS/RHEL
brew install fswatch                # macOS
```

### 2. 初始化项目
```bash
# 克隆仓库
git clone <your-repo>
cd <your-project>

# 复制Claude Enhancer配置
cp -r /path/to/claude-enhancer/.claude ./
cp -r /path/to/claude-enhancer/.workflow ./

# 安装Git Hooks
bash .claude/install_git_hooks.sh

# 验证安装
python .workflow/executor/executor.py status
```

### 3. 启动监听器
```bash
# 前台运行（调试）
python .workflow/executor/watcher.py

# 后台运行（生产）
nohup python .workflow/executor/watcher.py --daemon &
```

## 📝 日常操作

### 1. 开始新功能
```bash
# Phase 0: 创建分支
git checkout -b feature/your-feature

# 自动进入P1
echo "P1" > .phase/current

# 编写需求文档
vim docs/PLAN.md

# 验证P1
python .workflow/executor/executor.py validate --phase P1

# 推进到P2
python .workflow/executor/executor.py advance
```

### 2. 查看当前状态
```bash
# 工作流状态
python .workflow/executor/executor.py status

# 缓存统计
python .workflow/executor/executor.py cache-stats

# 事件监听状态
python .workflow/executor/watcher.py --status

# 查看指标
tail -f .workflow/metrics.jsonl | jq .
```

### 3. 手动验证Gate
```bash
# 验证当前阶段
python .workflow/executor/executor.py validate

# 验证指定阶段
python .workflow/executor/executor.py validate --phase P3

# 绕过缓存验证
python .workflow/executor/executor.py validate --no-cache
```

### 4. 管理工单
```bash
# 创建工单
touch .tickets/TASK-001.todo
echo "实现用户登录" > .tickets/TASK-001.todo

# 完成工单
mv .tickets/TASK-001.todo .tickets/TASK-001.done

# 查看活跃工单
ls .tickets/*.todo | wc -l
```

## 🔧 维护操作

### 1. 清理缓存
```bash
# 清理过期缓存
find .workflow/executor/cache -name "kv-*.json" -mtime +1 -delete

# 清理所有缓存
rm -rf .workflow/executor/cache/*

# 重建缓存
python -c "from executor import CacheManager; CacheManager().cleanup()"
```

### 2. 重置状态
```bash
# 重置到P1
echo "P1" > .phase/current
rm -f .gates/*.ok

# 清理所有工单
rm -f .tickets/*.todo
rm -f .tickets/*.done

# 重置指标
> .workflow/metrics.jsonl
> .workflow/events.jsonl
```

### 3. 备份和恢复
```bash
# 备份工作流状态
tar -czf workflow-backup-$(date +%Y%m%d).tar.gz \
  .phase/ .gates/ .tickets/ .workflow/

# 恢复工作流状态
tar -xzf workflow-backup-20250126.tar.gz
```

### 4. 升级系统
```bash
# 备份当前配置
cp -r .claude .claude.backup
cp -r .workflow .workflow.backup

# 拉取最新版本
git pull origin main

# 迁移配置
python .workflow/scripts/migrate_config.py

# 验证升级
python .workflow/executor/executor.py status
```

## 🐛 故障排查

### 1. 监听器不工作
```bash
# 检查进程
ps aux | grep watcher.py

# 查看日志
tail -f .workflow/watcher.log

# 检查inotify限制
cat /proc/sys/fs/inotify/max_user_watches
# 增加限制
echo 524288 | sudo tee /proc/sys/fs/inotify/max_user_watches

# 重启监听器
pkill -f watcher.py
python .workflow/executor/watcher.py --daemon
```

### 2. 验证失败
```bash
# 详细调试信息
PYTHON_DEBUG=1 python .workflow/executor/executor.py validate

# 检查Gate文件
ls -la .gates/

# 手动创建Gate
touch .gates/01.ok  # P1完成
touch .gates/02.ok  # P2完成

# 查看错误信息
grep ERROR .workflow/executor.log
```

### 3. 性能问题
```bash
# 分析慢查询
python -m cProfile .workflow/executor/executor.py validate

# 检查缓存命中率
python -c "
import json
with open('.workflow/metrics.jsonl') as f:
    lines = [json.loads(l) for l in f]
    hits = sum(1 for l in lines if l.get('cache_hit'))
    print(f'Cache hit rate: {hits/len(lines)*100:.1f}%')
"

# 优化缓存
python .workflow/scripts/optimize_cache.py
```

### 4. Git Hooks问题
```bash
# 检查Hook安装
ls -la .git/hooks/

# 重新安装Hooks
bash .claude/install_git_hooks.sh

# 绕过Hook提交（紧急情况）
git commit --no-verify -m "emergency fix"

# 检查Hook日志
tail -f .git/hooks/hook.log
```

## 📈 性能优化

### 1. 缓存预热
```bash
# 启动时预热缓存
python -c "
from executor import PhaseValidator
v = PhaseValidator()
for phase in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']:
    v.validate_phase(phase)
print('Cache warmed up')
"
```

### 2. 并行优化
```bash
# 调整并行限制
vim .workflow/config.yml
# 修改parallel_limits值

# 应用新配置
python .workflow/scripts/reload_config.py
```

### 3. 指标监控
```bash
# 实时监控
watch -n 1 'tail -n 20 .workflow/metrics.jsonl | jq .'

# Grafana集成（可选）
python .workflow/scripts/export_to_grafana.py
```

## 🎯 最佳实践

### 1. 每日开始
```bash
#!/bin/bash
# daily-start.sh

# 更新代码
git pull origin main

# 清理过期缓存
find .workflow/executor/cache -mtime +1 -delete

# 启动监听器
python .workflow/executor/watcher.py --daemon

# 显示状态
python .workflow/executor/executor.py status
```

### 2. 每周维护
```bash
#!/bin/bash
# weekly-maintenance.sh

# 备份状态
tar -czf workflow-weekly-$(date +%Y%W).tar.gz .workflow/

# 清理日志
find .workflow -name "*.log" -size +100M -exec truncate -s 0 {} \;

# 分析性能
python .workflow/scripts/weekly_report.py

# 优化数据库
sqlite3 .workflow/metrics.db "VACUUM;"
```

### 3. 紧急响应
```bash
#!/bin/bash
# emergency-response.sh

# 停止所有进程
pkill -f "workflow|watcher|executor"

# 重置状态
echo "P1" > .phase/current
rm -f .gates/*.ok
rm -f .tickets/*.todo

# 清理缓存
rm -rf .workflow/executor/cache/*

# 重启系统
python .workflow/executor/watcher.py --daemon
echo "系统已重置"
```

## 📊 监控指标

### 关键指标
| 指标 | 正常范围 | 报警阈值 | 处理方法 |
|-----|---------|---------|--------|
| validate耗时 | <250ms | >500ms | 检查缓存 |
| 缓存命中率 | >80% | <60% | 预热缓存 |
| 并发Agent | 4-8 | >10 | 调整限制 |
| 内存使用 | <500MB | >1GB | 重启服务 |
| CPU使用 | <30% | >70% | 优化算法 |

### 监控脚本
```python
# monitor.py
import json
import time
from pathlib import Path

def monitor():
    metrics_file = Path(".workflow/metrics.jsonl")
    
    while True:
        with open(metrics_file) as f:
            lines = f.readlines()[-100:]  # 最近100条
            
        metrics = [json.loads(l) for l in lines]
        
        # 计算指标
        avg_validate = sum(m['validate_ms'] for m in metrics) / len(metrics)
        cache_hits = sum(1 for m in metrics if m['cache_hit'])
        cache_rate = cache_hits / len(metrics) * 100
        
        # 报警
        if avg_validate > 500:
            print(f"⚠️ validate太慢: {avg_validate:.0f}ms")
        
        if cache_rate < 60:
            print(f"⚠️ 缓存命中率低: {cache_rate:.1f}%")
        
        time.sleep(60)  # 每分钟检查

if __name__ == "__main__":
    monitor()
```

## 🆘 帮助资源

### 文档
- [WORKFLOW_RULES.md](./WORKFLOW_RULES.md) - 工作流规则
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - 故障排查
- [PERF_BENCHMARK.md](./PERF_BENCHMARK.md) - 性能基准

### 命令速查
```bash
# 常用命令
alias ce-status='python .workflow/executor/executor.py status'
alias ce-validate='python .workflow/executor/executor.py validate'
alias ce-advance='python .workflow/executor/executor.py advance'
alias ce-cache='python .workflow/executor/executor.py cache-stats'
alias ce-watch='python .workflow/executor/watcher.py'
```

### 支持
- GitHub Issues: [your-repo/issues]
- 邮件: support@claude-enhancer.com
- 文档: https://docs.claude-enhancer.com