# Git自动化工作流使用指南

## 🎯 概述

Claude Enhancer 5.0现在支持完整的Git自动化工作流，让你专注于开发，Git操作自动执行。

## ✨ 核心特性

### 自动化操作
- **P3/P4/P5结束时** - 自动提交代码
- **P6结束时** - 自动打tag + 可选创建PR
- **分支管理** - 自动创建规范的feature分支
- **提交信息** - 自动生成规范的commit message

### 6-Phase标准流程
1. **P1 Requirements** - 需求分析 → 生成PLAN.md
2. **P2 Design** - 架构设计 → 生成DESIGN.md
3. **P3 Implementation** - 代码实现 → **自动git commit**
4. **P4 Testing** - 测试验证 → **自动git commit**
5. **P5 Review** - 代码审查 → **自动git commit**
6. **P6 Release** - 发布准备 → **自动git tag + 可选PR**

## 🚀 快速开始

### 1. 开始新任务（自动创建分支）
```bash
# Claude Code会自动检测并创建feature分支
# 格式: feature/PRD-XXX-description
```

### 2. 正常开发流程
```bash
# 你只需要专注于开发
# Phase会根据你的操作自动推进
# Git操作会在合适的时机自动触发
```

### 3. 查看当前状态
```bash
# 查看当前Phase
cat .phase/current

# 查看Git状态
git status

# 运行测试脚本
python test_git_automation.py
```

## ⚙️ 配置选项

在 `.workflow/config.yml` 中配置：

```yaml
git:
  auto_commit: true        # 自动提交(默认开启)
  auto_tag: true          # 自动打tag(默认开启)
  auto_pr: true           # 自动创建PR(需要gh CLI)
  auto_merge: false       # 自动合并到main(默认关闭)
  delete_branch_after_merge: true  # 合并后删除分支
```

## 📝 提交信息格式

自动生成的提交信息遵循以下格式：

```
[type]: [description] [Phase][Ticket]

Changes: X files changed, Y insertions(+), Z deletions(-)

Phase: PX completed
Branch: feature/PRD-XXX-description
Auto-commit by Claude Enhancer

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

## 🔄 工作流示例

### 完整开发流程
```bash
# 1. 开始任务 - 自动创建分支
# Claude Code检测到新任务，自动创建feature分支

# 2. P1: 需求分析
# 你: 分析需求，生成PLAN.md
# 系统: 自动进入P1

# 3. P2: 架构设计
# 你: 设计架构，生成DESIGN.md
# 系统: 自动进入P2

# 4. P3: 功能实现
# 你: 编写代码
# 系统: P3完成时自动commit ✅

# 5. P4: 测试验证
# 你: 运行测试
# 系统: P4完成时自动commit ✅

# 6. P5: 代码审查
# 你: 审查代码
# 系统: P5完成时自动commit ✅

# 7. P6: 发布准备
# 你: 准备发布
# 系统: 自动打tag + 可选创建PR ✅
```

## 🛠️ 手动控制

如果需要手动控制Git操作：

```bash
# 手动提交
python .claude/core/git_automation.py commit P3

# 手动打tag
python .claude/core/git_automation.py tag v1.0.0

# 手动创建PR
python .claude/core/git_automation.py pr

# 查看帮助
python .claude/core/git_automation.py
```

## ⚠️ 注意事项

1. **Git Hooks可能阻止提交** - 如果有安全检查失败，使用`--no-verify`
2. **需要gh CLI创建PR** - 安装：`brew install gh` 或 `apt install gh`
3. **自动合并默认关闭** - 需要手动在配置中启用
4. **Phase必须按顺序** - 不能跳过Phase

## 🎯 最佳实践

1. **让系统自动管理Git** - 不要手动commit，让Phase完成时自动处理
2. **保持Phase同步** - Phase状态和实际工作保持一致
3. **使用规范分支名** - feature/PRD-XXX-description格式
4. **定期查看状态** - 使用测试脚本验证系统状态

## 📊 状态检查

```bash
# 完整的状态检查
python test_git_automation.py

# 输出示例：
# Branch: feature/PRD-200-task-manager
# Phase: P3
# auto_commit: True
# auto_tag: True
```

## 🔍 故障排除

### 问题1：提交被Git Hooks阻止
```bash
# 解决：检查hooks输出，修复问题或使用--no-verify
```

### 问题2：Phase状态不正确
```bash
# 解决：手动更新
echo "P3" > .phase/current
```

### 问题3：自动化没有触发
```bash
# 解决：检查配置
cat .workflow/config.yml | grep -A5 "git:"
```

---

**提示**: Git自动化让你专注于编码，系统会处理所有Git操作！