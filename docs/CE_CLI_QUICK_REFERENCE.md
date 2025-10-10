# ce CLI 快速参考

## 一行命令速查

```bash
# 🚀 启动新功能
ce start <feature-name>

# 📊 查看状态
ce status

# ✅ 验证当前阶段
ce validate

# ⏭️ 进入下一阶段
ce next

# 📦 发布功能
ce publish

# 🔀 合并到主分支
ce merge main

# 🧹 清理已合并分支
ce clean
```

---

## 典型工作流

### 方式1: 自动推进（推荐）
```bash
ce start my-feature    # 启动
ce next                # P0 → P1
ce next                # P1 → P2
ce next                # P2 → P3
ce next                # P3 → P4
ce next                # P4 → P5
ce next                # P5 → P6
ce publish             # 推送+PR
ce merge main          # 合并
```

### 方式2: 验证为主
```bash
ce start my-feature
ce validate            # 检查P0
ce next
ce validate            # 检查P1
ce next
# ... 重复 ...
ce publish
```

### 方式3: 快速修复
```bash
ce start hotfix
ce goto P3             # 跳到实现
# ... 修复 ...
ce next                # → P4
ce next --force        # 快速过P5
ce publish --draft
ce merge main
```

---

## Phase要求速查

| Phase | 名称 | 必须产出 | 验证重点 |
|-------|------|----------|----------|
| P0 | Discovery | docs/P0_*_DISCOVERY.md | 可行性结论 |
| P1 | Plan | docs/PLAN.md | ≥5个任务 |
| P2 | Skeleton | 目录结构 | 符合PLAN |
| P3 | Implementation | 代码+CHANGELOG | 可构建 |
| P4 | Testing | 测试+报告 | ≥2个测试 |
| P5 | Review | docs/REVIEW.md | APPROVE |
| P6 | Release | README+tag | 版本号 |
| P7 | Monitor | 监控报告 | SLO达标 |

---

## 常见场景

### 检查当前在哪个阶段
```bash
ce status | grep "阶段:"
```

### 快速完成当前阶段
```bash
ce validate && ce next
```

### 看看还差什么
```bash
ce validate
# 查看 ❌ 标记的项
```

### 暂存当前进度
```bash
git stash
ce status  # 查看Phase状态
```

### 回到之前的阶段
```bash
ce goto P2
```

### 重新开始
```bash
ce reset
```

---

## 错误处理

### 验证失败
```bash
ce validate
# 看错误信息
# 修复问题
ce validate  # 重新验证
```

### 合并冲突
```bash
ce merge main
# 如果有冲突，手动解决
git merge main
# 解决冲突后
git commit
ce merge main  # 继续
```

### 健康检查失败
```bash
ce merge main
# 自动回滚
# 修复问题
ce publish     # 重新发布
ce merge main  # 再次尝试
```

---

## 高级选项

### 跳过某些检查
```bash
ce validate --skip-tests
ce next --skip-validate
ce publish --skip-pr
```

### 强制执行
```bash
ce next --force
ce merge --no-healthcheck
```

### 预览模式
```bash
ce clean --dry-run
ce merge --dry-run
```

### 详细输出
```bash
ce status --verbose
ce validate --verbose
```

### JSON输出（供脚本使用）
```bash
ce status --json | jq '.current_phase'
```

---

## 组合使用

### 一键完成P0-P2
```bash
ce validate && ce next && ce next && ce next
```

### 自动发布（如果验证通过）
```bash
ce validate && ce publish
```

### 条件合并
```bash
ce status --json | jq -r '.gates.passed | length' | \
  grep -q '^[6-7]$' && ce merge main
```

---

## 配置

### 查看配置
```bash
cat .workflow/config.yml | grep -A5 "git:"
```

### 启用自动合并
```bash
# 编辑 .workflow/config.yml
git:
  auto_merge: true
```

### 调整并行限制
```bash
# 编辑 .workflow/config.yml
parallel_limits:
  P3: 10  # 增加到10个Agent
```

---

## 性能对比

| 操作 | 手动 | ce CLI | 提升 |
|------|------|--------|------|
| 启动功能 | 5-10min | 30s | 10-20x |
| 验证 | 10-15min | 10s | 60-90x |
| 发布 | 15-20min | 1min | 15-20x |

---

## 常见问题

### Q: ce命令找不到？
```bash
# 确保安装了CLI
ls -la /usr/local/bin/ce
# 或检查符号链接
which ce
```

### Q: 卡在某个Phase？
```bash
ce status  # 查看当前要求
ce validate  # 看缺什么
```

### Q: 想跳过某个Phase？
```bash
ce goto P4  # 直接跳到P4
# 或
ce next --force  # 强制进入下一阶段
```

### Q: 搞砸了想重来？
```bash
ce reset  # 重置到P1
# 或
git checkout main
git branch -D feature/xxx
ce start xxx  # 重新开始
```

---

## 最佳实践

1. **频繁验证** - 随时运行 `ce validate`
2. **小步快跑** - 每个Phase做完立即 `ce next`
3. **自动化优先** - 让 `ce next` 自动提交
4. **定期清理** - 周末运行 `ce clean`
5. **保持更新** - 遵循Phase要求

---

## 快捷键建议

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc

alias ces='ce status'
alias cev='ce validate'
alias cen='ce next'
alias cep='ce publish'
alias cem='ce merge main'
alias cec='ce clean'

# 超级快捷
alias ceq='ce validate && ce next'  # Quick next
alias cea='ce publish && ce merge main'  # All the way
```

---

## 帮助资源

- 完整文档: `docs/CE_COMMAND_LINE_WORKFLOW.md`
- 命令帮助: `ce --help`
- 子命令帮助: `ce <command> --help`
- 示例: `docs/examples/`
- Wiki: https://github.com/user/repo/wiki

---

*记住: ce CLI 的目标是让你专注于创造，而不是流程*
