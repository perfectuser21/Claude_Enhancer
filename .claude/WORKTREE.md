# Git Worktree 智能管理

## 功能概述
Git Worktree允许你同时在多个分支上工作，无需频繁切换分支。Claude Enhancer提供智能化的worktree管理。

## 自动化场景

### 1. 并行开发
当需要同时处理多个功能时，自动创建worktree：
```bash
# 主仓库：feature/auth
# Worktree 1：feature/api → ../Claude Enhancer-api
# Worktree 2：feature/test → ../Claude Enhancer-test
```

### 2. 紧急修复
在开发功能时需要紧急修复bug：
```bash
# 自动创建hotfix worktree
git worktree add ../Claude Enhancer-hotfix hotfix/critical-bug
# 修复完成后自动清理
```

### 3. 代码审查
审查PR时不影响当前工作：
```bash
# 创建review worktree
git worktree add ../Claude Enhancer-review origin/pr/123
```

## 智能提示

Claude Enhancer会在以下情况提醒使用worktree：
- 检测到需要切换分支但有未提交更改
- 同时处理多个相关任务
- 需要对比不同分支的实现

## 自动清理

- 完成任务后自动提醒清理worktree
- 检测废弃的worktree并建议删除
- 维护worktree列表整洁

## 命令助手

```bash
# 列出所有worktree
git worktree list

# 添加新worktree
git worktree add ../Claude Enhancer-[branch-name] [branch]

# 删除worktree
git worktree remove ../Claude Enhancer-[branch-name]

# 清理废弃worktree
git worktree prune
```