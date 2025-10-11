# Claude Enhancer 智能清理系统方案

## 🎯 问题诊断

### 当前状况
- **文件爆炸**：今天创建了1085个文件
- **缺乏管理**：虽有清理脚本但未融入工作流
- **垃圾堆积**：测试文件、临时文件、备份文件混杂

### 根本原因
1. Claude Code创建文件过多，缺乏节制
2. 清理系统与Claude Enhancer工作流脱节
3. 没有自动触发机制，需要手动执行

## 🏗️ 解决方案架构

### 1. 三层清理体系

```
┌─────────────────────────────────────────────┐
│          实时层 (Real-time)                 │
│   Claude Hooks - 文件创建时即时检查         │
├─────────────────────────────────────────────┤
│          批处理层 (Batch)                    │
│   Phase切换时自动清理 (P3/P5/P6)            │
├─────────────────────────────────────────────┤
│          定时层 (Scheduled)                  │
│   每天凌晨深度清理 (cron)                   │
└─────────────────────────────────────────────┘
```

### 2. 集成点设计

#### A. Hook级别集成
```bash
# .claude/hooks/file_guard.sh
# 在文件操作前后自动触发

- pre-write: 检查是否重复文件
- post-write: 统计新增文件
- threshold: 超过阈值触发清理
```

#### B. Phase级别集成
```python
# 工作流Phase与清理策略映射
phase_cleanup_map = {
    "P0": None,           # 探索阶段不清理
    "P1": "light",        # 轻度清理
    "P2": "light",        # 轻度清理
    "P3": "test_files",   # 清理测试垃圾
    "P4": "test_output",  # 清理测试输出
    "P5": "backup_files", # 清理备份文件
    "P6": "deep",         # 深度清理
    "P7": None            # 监控阶段不清理
}
```

#### C. Agent级别集成
```yaml
# Task完成后自动清理
agent_cleanup_rules:
  test-engineer:
    - pattern: "test_*.tmp"
    - pattern: "*_test_output.*"
  code-reviewer:
    - pattern: "*.review.tmp"
  backend-architect:
    - pattern: "*.diagram.tmp"
```

### 3. 清理规则分级

#### Level 1: 安全清理（无风险）
```
文件类型：*.pyc, *.pyo, *~, .DS_Store, Thumbs.db
触发时机：随时可执行
自动执行：是
```

#### Level 2: 临时文件（低风险）
```
文件类型：*.tmp, *.temp, *.swp, test_*.tmp
触发时机：Phase完成后
自动执行：是（需确认数量）
```

#### Level 3: 冗余文件（中风险）
```
文件类型：*_copy.*, *(1).*, *_backup.*
触发时机：P5审查后
自动执行：需要确认
```

#### Level 4: 深度清理（高风险）
```
文件类型：旧日志、大文件、重复代码
触发时机：P6发布前
自动执行：否（需人工确认）
```

## 💡 实施方案

### Step 1: 创建核心模块
```python
# .claude/core/smart_cleanup.py
class SmartCleanup:
    def __init__(self):
        self.phase_rules = {...}
        self.cleanup_levels = {...}

    def should_cleanup(self) -> bool
    def cleanup_by_phase(self, phase: str)
    def cleanup_by_level(self, level: int)
    def smart_cleanup(self, dry_run: bool)
```

### Step 2: 升级Hook系统
```bash
# .claude/hooks/auto_cleanup.sh
#!/bin/bash
# 监控文件创建，超阈值自动清理

NEW_FILES=$(find . -mmin -60 | wc -l)
if [ "$NEW_FILES" -gt 50 ]; then
    python3 .claude/core/smart_cleanup.py --level 1
fi
```

### Step 3: 修改工作流
```bash
# .workflow/ticket_manager.sh
# 在Phase切换时触发清理

switch_phase() {
    old_phase=$1
    new_phase=$2

    # Phase切换时清理
    if [[ "$old_phase" == "P3" ]] || \
       [[ "$old_phase" == "P5" ]] || \
       [[ "$old_phase" == "P6" ]]; then
        python3 .claude/core/smart_cleanup.py \
            --phase "$old_phase"
    fi
}
```

### Step 4: 添加质量门禁
```yaml
# .github/workflows/ci-enhanced.yml
- name: Check File Hygiene
  run: |
    python3 .claude/core/smart_cleanup.py --check
    if [ $? -ne 0 ]; then
      echo "Too many junk files detected!"
      exit 1
    fi
```

## 🚀 使用方式

### 1. 自动模式（推荐）
```bash
# 安装后自动运行，无需干预
./.claude/install.sh --enable-cleanup
```

### 2. 手动触发
```bash
# 检查是否需要清理
python3 .claude/core/smart_cleanup.py --check

# 预览清理（不实际删除）
python3 .claude/core/smart_cleanup.py --dry-run

# 执行清理
python3 .claude/core/smart_cleanup.py

# 激进清理（Level 3-4）
python3 .claude/core/smart_cleanup.py --aggressive
```

### 3. Phase触发
```bash
# 完成P3实现后
.workflow/ticket_manager.sh complete P3
# 自动清理测试文件

# 完成P5审查后
.workflow/ticket_manager.sh complete P5
# 自动清理备份文件
```

## 📊 预期效果

### 清理前
```
项目文件数：2500+
垃圾文件：500+
占用空间：200MB垃圾
```

### 清理后
```
项目文件数：1000-1500
垃圾文件：<50
释放空间：180MB+
```

### 效果指标
- **文件减少**：40-60%
- **空间释放**：90%垃圾空间
- **性能提升**：Git操作快30%
- **开发体验**：更清爽的项目结构

## 🔧 配置选项

### 环境变量
```bash
# 设置清理级别
export CLEANUP_LEVEL=2  # 1-4

# 设置自动清理阈值
export CLEANUP_THRESHOLD=100  # 文件数

# 禁用自动清理
export DISABLE_AUTO_CLEANUP=1
```

### 配置文件
```yaml
# .claude/cleanup.yml
auto_cleanup:
  enabled: true
  threshold: 100
  max_level: 2

protected_dirs:
  - .git
  - .claude
  - node_modules

custom_rules:
  - pattern: "*.custom"
    level: 1
```

## ⚡ 快速开始

```bash
# 1. 查看当前状态
find . -type f -mtime -1 | wc -l  # 今天创建的文件数

# 2. 运行清理检查
python3 .claude/core/smart_cleanup.py --check

# 3. 预览清理效果
python3 .claude/core/smart_cleanup.py --dry-run

# 4. 执行清理
python3 .claude/core/smart_cleanup.py

# 5. 设置自动清理
echo "export AUTO_CLEANUP=1" >> ~/.bashrc
```

## 🎯 核心优势

1. **融入工作流**：不是独立工具，是Claude Enhancer的有机组成
2. **智能分级**：4级清理策略，安全可控
3. **自动触发**：Phase切换、文件阈值、定时任务
4. **可追溯**：完整的清理日志，可回滚
5. **零配置**：开箱即用，智能判断

## 📝 注意事项

1. **首次运行**建议用`--dry-run`预览
2. **重要项目**请先备份
3. **保护目录**永远不会被清理
4. **清理日志**保存在`.cleanup_log`
5. **可以回滚**：清理的文件先移到`.trash`（可选）

---

这个方案完全融入Claude Enhancer体系，不是独立工具而是工作流的一部分。通过Hook、Phase、Agent三个层面的集成，实现自动化的文件管理。