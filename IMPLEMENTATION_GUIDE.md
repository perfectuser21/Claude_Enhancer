# 🛡️ Claude Enhancer 工作流硬闸实施指南

## 📋 实施方案对比

### 方案选择建议

| 场景 | 推荐方案 | 复杂度 | 效果 |
|------|----------|--------|------|
| **快速体验** | 简单模式 + 目录锁定 | ⭐ | 🟨 中等 |
| **日常开发** | Git Worktree模式 | ⭐⭐ | 🟢 良好 |
| **严格管控** | OverlayFS模式 | ⭐⭐⭐ | 🟢 最强 |
| **生产环境** | 只读bind mount | ⭐⭐⭐⭐ | 🟢 最强 |

## 🚀 快速开始（推荐）

### Step 1: 一键安装

```bash
# 设置执行权限
chmod +x scripts/ce-*
chmod +x scripts/setup_enhanced_hooks.sh

# 安装增强hooks（入口层）
bash scripts/setup_enhanced_hooks.sh

# 验证安装
./test_three_layer_protection.sh
```

### Step 2: 选择工作模式

#### 🟢 模式A：简单模式（推荐新手）

最容易上手，适合日常开发：

```bash
# 1. 在main分支时，锁定目录（可选但推荐）
./scripts/ce-guard-setup.sh lock

# 2. 开始工作（自动创建分支）
./scripts/ce-start-enhanced "实现用户认证" --simple

# 3. 正常开发...

# 4. 完成工作
./scripts/ce-stop-enhanced
```

**优点**：
- ✅ 无需sudo权限
- ✅ 设置简单
- ✅ 易于恢复

**缺点**：
- ⚠️ 保护强度中等
- ⚠️ 可被chmod绕过

#### 🔵 模式B：Git Worktree（推荐日常）

每个任务独立工作树，完美隔离：

```bash
# 开始工作（创建独立worktree）
./scripts/ce-start-enhanced "重构API层" --worktree

# 会创建 /tmp/worktrees/T-xxx/ 独立工作目录
# VS Code会在新目录打开

# 完成后清理
./scripts/ce-stop-enhanced
```

**优点**：
- ✅ Git原生支持
- ✅ 完全隔离
- ✅ 易于管理

**缺点**：
- ⚠️ 占用额外空间
- ⚠️ 需要切换目录

#### 🟣 模式C：OverlayFS（最强保护）

使用Linux内核特性，变更在上层，底层只读：

```bash
# 需要sudo权限
sudo -v

# 开始工作（创建overlay）
./scripts/ce-start-enhanced "系统重构" --overlay

# 所有修改在upper层，原仓库保持只读

# 完成后清理（需要sudo）
./scripts/ce-stop-enhanced
```

**优点**：
- ✅ 最强保护
- ✅ 原仓库不变
- ✅ 可完全回滚

**缺点**：
- ⚠️ 需要sudo
- ⚠️ Linux特有
- ⚠️ 设置复杂

## 📊 效果验证

### 验证工作流硬闸

```bash
# 1. 尝试在未激活时提交（应该失败）
git add test.txt
git commit -m "test"
# ❌ pre-commit hook拒绝

# 2. 尝试推送（应该失败）
git push
# ❌ pre-push hook拒绝

# 3. 激活工作流后重试（应该成功）
./scripts/ce-start-enhanced "测试任务"
git add test.txt
git commit -m "test"
# ✅ 允许提交

git push
# ✅ 允许推送
```

## 🔧 高级配置

### 1. 只读Bind Mount（最强版）

用于生产服务器，需要root权限：

```bash
# 创建只读挂载
sudo mkdir -p /srv/repos/Claude_Enhancer
sudo rsync -a ~/Claude_Enhancer/ /srv/repos/Claude_Enhancer/
sudo mount --bind /srv/repos/Claude_Enhancer ~/Claude_Enhancer
sudo mount -o remount,ro,bind ~/Claude_Enhancer

# 解除挂载
sudo umount ~/Claude_Enhancer
```

### 2. 自动化脚本

创建别名简化操作：

```bash
# 添加到 ~/.bashrc
alias ce-work='~/Claude_Enhancer/scripts/ce-start-enhanced'
alias ce-done='~/Claude_Enhancer/scripts/ce-stop-enhanced'
alias ce-lock='~/Claude_Enhancer/scripts/ce-guard-setup.sh lock'
alias ce-unlock='~/Claude_Enhancer/scripts/ce-guard-setup.sh unlock'

# 重载配置
source ~/.bashrc

# 使用
ce-work "新任务"
ce-done
```

## 🎯 Claude Code的执行模式

### 当Claude收到编程任务时

```python
def claude_programming_task_handler(task):
    """Claude Code必须遵循的执行流程"""

    # Step 1: 立即检查ACTIVE
    if not check_active_file():
        return """
        ❌ 工作流未激活

        请先运行：
        ./scripts/ce-start-enhanced "任务描述"

        可选模式：
        --simple   : 简单模式（默认）
        --worktree : Git Worktree隔离
        --overlay  : OverlayFS强隔离
        """

    # Step 2: 验证工作目录
    work_dir = get_active_work_dir()
    if not is_writable(work_dir):
        return "❌ 工作目录不可写，请检查权限"

    # Step 3: 使用Agent系统
    agents = select_agents_for_task(task, min_count=3)

    # Step 4: 并行执行
    execute_agents_parallel(agents)

    # Step 5: 验证结果
    verify_workflow_compliance()
```

### Claude的承诺

1. **永远先检查** - 不检查不写代码
2. **发现未激活立即停止** - 不尝试绕过
3. **提供明确指导** - 告诉你如何激活
4. **遵守工作目录** - 只在指定目录写

## 🚨 常见问题

### Q1: 忘记激活就写了代码怎么办？

```bash
# 补救方案
# 1. 暂存当前更改
git stash

# 2. 激活工作流
./scripts/ce-start-enhanced "补充任务"

# 3. 恢复更改
git stash pop

# 4. 正常提交
git add . && git commit
```

### Q2: 如何紧急绕过？

```bash
# 紧急情况（不推荐）
git commit --no-verify  # 绕过hooks
git push --no-verify    # 绕过hooks

# 但是：PR仍然无法合并（CI会失败）
```

### Q3: 如何完全清理？

```bash
# 清理所有worktree
git worktree prune
git worktree list

# 清理overlay（需要sudo）
sudo umount /tmp/overlays/*/merged
sudo rm -rf /tmp/overlays/*

# 解锁目录
./scripts/ce-guard-setup.sh unlock
```

## 📋 最佳实践

### 日常工作流程

```bash
# 早上开始
1. git pull origin main
2. ./scripts/ce-guard-setup.sh lock  # 锁定main
3. ./scripts/ce-start-enhanced "今日任务" --worktree

# 开发中
4. 在独立工作树开发
5. git add && git commit
6. git push origin feature/xxx

# 下班前
7. 创建PR
8. ./scripts/ce-stop-enhanced  # 清理工作区
```

### 团队协作

```bash
# 团队成员A
ce-start-enhanced "功能A" --worktree
# 工作目录: /tmp/worktrees/T-001/

# 团队成员B（同时）
ce-start-enhanced "功能B" --worktree
# 工作目录: /tmp/worktrees/T-002/

# 完全隔离，互不影响
```

## 🎖️ 效果保证

| 层级 | 机制 | Claude能绕过 | 人类能绕过 | 最终效果 |
|------|------|--------------|------------|----------|
| **入口** | 目录锁定 | 🟨 困难 | ⚠️ 可能 | 阻止直接写 |
| **入口** | Worktree隔离 | ❌ 不能 | ❌ 不能 | 完全隔离 |
| **过程** | pre-commit | ❌ 不能 | ⚠️ 可绕 | 阻止提交 |
| **过程** | pre-push | ❌ 不能 | ⚠️ 可绕 | 阻止推送 |
| **出口** | CI检查 | ❌ 不能 | ❌ 不能 | 阻止合并 |

## 🚀 立即开始

```bash
# 1. 选择你的模式
MODE="--simple"  # 或 --worktree 或 --overlay

# 2. 开始第一个任务
./scripts/ce-start-enhanced "我的第一个工作流任务" $MODE

# 3. 享受有保障的开发流程！
```

---

**Claude Enhancer v5.3.2** - 不仅是承诺，更是机制保障！