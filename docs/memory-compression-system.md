# Memory Compression System

## 问题背景

`memory-cache.json` 是AI的"长期记忆"，记录历史决策防止自我矛盾。但随时间增长会导致：

- **Token膨胀**：45K tokens/年（每次会话加载浪费）
- **性能下降**：文件过大导致读取缓慢
- **信息过载**：旧决策干扰新决策

## 解决方案：三层存储架构

```
Hot Storage (memory-cache.json)
└─ 最近30天决策 (~5KB, 1200 tokens)
   ├─ Critical → 永久保留
   ├─ Warning → 90天后归档
   └─ Info → 30天后归档

Cold Storage (.claude/memory-archive/)
└─ 历史归档（按月）
   ├─ 2025-10.json
   ├─ 2025-09.json
   └─ ...

Quick Index (decision-index.json)
└─ 快速索引（每月摘要）
   └─ AI需要时再加载详细归档
```

## 核心特性

### 1. 智能分级压缩

根据决策重要性和年龄自动处理：

| 重要性 | 保留时间 | 处理方式 |
|--------|---------|---------|
| Critical | 永久 | 保留在hot storage |
| Warning | 90天 | 超期归档到cold storage |
| Info | 30天 | 超期归档到cold storage |

### 2. 自动重要性推断

如果决策未显式标记重要性：

```python
if decision["do_not_revert"] or decision["do_not_delete"]:
    → importance = "critical"

elif len(affected_files) >= 5:
    → importance = "warning"

else:
    → importance = "info"
```

### 3. 向后兼容

- 压缩后的JSON仍可被旧系统读取
- 归档文件保留完整信息，无损压缩

### 4. 自动备份

每次压缩前自动创建 `memory-cache.json.backup`

## 使用方法

### 基础命令

```bash
# 查看统计信息
python3 scripts/memory-compressor.py --stats

# 干运行（分析但不修改）
python3 scripts/memory-compressor.py --dry-run

# 执行压缩
python3 scripts/memory-compressor.py

# 强制压缩（忽略大小检查）
python3 scripts/memory-compressor.py --force

# 自定义保留期
python3 scripts/memory-compressor.py --retention-days 60
```

### 自动化集成

#### 方式1：Git Hook（推荐）

每次commit后自动检查：

```bash
# .git/hooks/post-commit
#!/bin/bash
python3 scripts/memory-compressor.py --force >/dev/null 2>&1 || true
```

#### 方式2：Cron定时任务

每周自动压缩：

```bash
# 添加到crontab
0 2 * * 0 cd /path/to/project && python3 scripts/memory-compressor.py
```

#### 方式3：CI/CD集成

```yaml
# .github/workflows/memory-maintenance.yml
name: Memory Maintenance
on:
  schedule:
    - cron: '0 0 * * 0'  # 每周日

jobs:
  compress:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: python3 scripts/memory-compressor.py --force
      - run: git add .claude/
      - run: git commit -m "chore: compress memory cache [skip ci]"
      - run: git push
```

## 配置说明

在 `memory-cache.json` 中添加：

```json
{
  "_auto_cleanup": {
    "enabled": true,
    "retention_days": 30,
    "max_size_kb": 5,
    "archive_path": ".claude/memory-archive/",
    "compression_rules": {
      "critical": "永久保留",
      "warning": "90天后归档",
      "info": "30天后归档"
    }
  }
}
```

## 工作流程详解

### Step 1: 分析阶段

```
读取 memory-cache.json
    ↓
提取每个决策的元数据
    ├─ importance（显式或推断）
    ├─ age_days（距今天数）
    └─ size（字节数）
    ↓
应用保留规则
    ├─ Critical → 保留
    ├─ Warning + >90天 → 归档
    └─ Info + >30天 → 归档
```

### Step 2: 归档阶段

```
决策 "2025-08-15_old_feature"
    ↓
移动到 .claude/memory-archive/2025-08.json
    ↓
从 memory-cache.json 删除
    ↓
更新 decision-index.json
```

### Step 3: 验证阶段

```
压缩前: 5.12 KB (1310 tokens)
压缩后: 4.71 KB (1204 tokens)
    ↓
节省: 106 tokens
    ↓
创建备份: memory-cache.json.backup
```

## 监控指标

### 健康标准

| 指标 | 目标 | 警告阈值 |
|-----|------|---------|
| memory-cache.json大小 | <5KB | >5KB |
| Token数量 | <1200 | >1500 |
| 决策数量 | <10个 | >15个 |
| 归档文件 | 按月增长 | - |

### 查看当前状态

```bash
python3 scripts/memory-compressor.py --stats
```

输出示例：

```
📊 Memory System Statistics
============================================================
Memory Cache:
  Size: 4.71 KB (~1204 tokens)
  Decisions: 4
  Status: ✅ Healthy

Archives:
  Count: 1 months
  Total size: 0.74 KB
  Location: /home/xx/dev/Claude Enhancer 5.0/.claude/memory-archive

Decision Index:
  Months indexed: 2
  Last updated: 2025-10-14T07:33:25.064681
============================================================
```

## 测试验证

运行完整测试套件：

```bash
bash test/memory-compression-test.sh
```

测试覆盖：
- ✅ 统计功能
- ✅ 干运行模式
- ✅ 备份创建
- ✅ 归档结构
- ✅ 索引完整性
- ✅ Token节省计算

## 故障排除

### 问题1：压缩后size反而变大

**原因**：Python写入时添加了metadata（`_last_compressed`, `_compression_stats`）

**解决**：正常现象，下次归档更多决策后会明显减小

### 问题2：找不到归档文件

**原因**：所有决策都是Critical或时间未超期

**解决**：
```bash
# 检查决策年龄
python3 scripts/memory-compressor.py --dry-run

# 手动添加importance标记
# 在memory-cache.json中为旧决策添加 "importance": "info"
```

### 问题3：归档后AI找不到历史决策

**原因**：AI只读hot storage，未检查archives

**解决**：AI应该先查看 `decision-index.json`，再按需加载具体归档文件

## 最佳实践

### 1. 标记重要性

创建决策时显式标记：

```json
{
  "2025-10-14_important_change": {
    "date": "2025-10-14",
    "decision": "...",
    "importance": "critical",  // 显式标记
    "do_not_revert": true
  }
}
```

### 2. 定期审查

每月检查决策是否仍然相关：

```bash
# 查看即将归档的决策
python3 scripts/memory-compressor.py --dry-run

# 如果仍然重要，修改importance为critical
```

### 3. 监控Token增长

```bash
# 添加到日常健康检查
python3 scripts/memory-compressor.py --stats | grep "tokens"
```

### 4. 渐进式迁移

不要一次性归档所有历史：

```bash
# 第一次：只归档90天前的
python3 scripts/memory-compressor.py --retention-days 90

# 观察几周后
python3 scripts/memory-compressor.py --retention-days 60

# 最终目标
python3 scripts/memory-compressor.py --retention-days 30
```

## 性能影响

### Token节省预估

| 时间 | 无压缩 | 压缩后 | 节省 |
|-----|-------|--------|------|
| 1个月 | 2000 tokens | 1200 tokens | 40% |
| 6个月 | 12000 tokens | 1200 tokens | 90% |
| 1年 | 45000 tokens | 1200 tokens | 97.3% |

### 性能开销

- **压缩时间**：<1秒（100个决策）
- **备份空间**：~5KB/次
- **归档增长**：~1KB/月

## 架构优势

### 1. 可扩展性

- 支持无限历史（cold storage按月分片）
- Hot storage始终保持轻量（<5KB）

### 2. 可靠性

- 自动备份机制
- 无损归档（完整保留原始数据）

### 3. 可维护性

- 清晰的三层架构
- 独立的索引系统
- 人类可读的JSON格式

### 4. AI友好

- 快速索引查询
- 按需加载详细内容
- 向后兼容旧系统

## 未来扩展

### 计划中的功能

- [ ] **语义压缩**：使用LLM自动总结旧决策
- [ ] **智能提醒**：归档前提醒重要决策
- [ ] **交互式审查**：命令行界面选择归档内容
- [ ] **云端同步**：将归档备份到云存储
- [ ] **统计报告**：生成月度决策报告

## 相关文档

- [Self-Healing System](./self-healing-system.md) - 自愈系统总览
- [Memory Cache Schema](../.claude/memory-cache.json) - 数据结构定义
- [Decision Index](../.claude/decision-index.json) - 快速索引

## 总结

Memory Compression System通过三层存储架构：

- ✅ 防止token无限膨胀（<5KB上限）
- ✅ 保持AI响应速度（只加载hot storage）
- ✅ 完整保留历史（cold storage归档）
- ✅ 智能管理决策生命周期（自动分级）

**核心理念**：Hot for speed, Cold for history, Index for discovery.
