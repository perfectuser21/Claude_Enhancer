# PR和Branch Protection - 5分钟快速开始

> 最快的方式让你的仓库启用Claude Enhancer PR和Branch Protection系统

## 🚀 3步配置（管理员）

### Step 1: 运行自动配置脚本（2分钟）

```bash
# 进入项目目录
cd /home/xx/dev/Claude\ Enhancer\ 5.0

# 运行配置脚本
./scripts/setup_branch_protection.sh

# 脚本会自动：
# ✅ 检测仓库
# ✅ 验证权限
# ✅ 显示配置预览
# ✅ 配置Branch Protection
# ✅ 验证CODEOWNERS
# ✅ 生成配置报告
```

**期望输出**:
```
═══════════════════════════════════════════════════
  Claude Enhancer - Branch Protection配置
═══════════════════════════════════════════════════

ℹ 检测到仓库: your-org/your-repo
✅ 权限验证通过

═══════════════════════════════════════════════════
  配置预览
═══════════════════════════════════════════════════

ℹ 仓库: your-org/your-repo
ℹ 分支: main
ℹ 保护级别: claude-enhancer

将启用以下保护:
  - 需要 2 个approval
  - 需要Code Owner审查
  - 新提交时取消旧的approval
  - 要求线性历史
  - 管理员也需遵守规则
  - 需要解决所有对话
  - Required status checks:
      • validate-phase-gates
      • validate-must-produce
      • run-unit-tests
      • run-boundary-tests
      • run-smoke-tests
      • run-bdd-tests
      • check-security
      • validate-openapi
      • check-performance

⚠️  即将应用以上配置到 your-org/your-repo/main
ℹ 继续？(y/N) y

✅ Branch Protection配置成功！
✅ CODEOWNERS文件存在
✅ CODEOWNERS语法正确

═══════════════════════════════════════════════════
  配置完成
═══════════════════════════════════════════════════

✅ Branch Protection已成功配置！
```

### Step 2: 调整CODEOWNERS（1分钟）

```bash
# 编辑CODEOWNERS文件
vim .github/CODEOWNERS

# 替换示例用户名为你的团队成员
# 将 @team-lead 替换为 @your-team-lead
# 将 @senior-dev 替换为 @your-senior-dev
# 等等...

# 保存并提交
git add .github/CODEOWNERS
git commit -m "chore: configure CODEOWNERS for team"
git push origin main
```

### Step 3: 验证配置（1分钟）

```bash
# 方式1: Web界面验证
# 访问: https://github.com/your-org/your-repo/settings/branches
# 检查main分支的保护规则

# 方式2: CLI验证
gh api repos/your-org/your-repo/branches/main/protection

# 方式3: 创建测试PR
git checkout -b test/verify-config
echo "test" > test.txt
git add test.txt
git commit -m "test: verify configuration"
git push origin test/verify-config
gh pr create --draft

# 检查PR页面是否显示：
# ✅ Required status checks
# ✅ Required approvals (2)
# ✅ CODEOWNERS已自动添加
```

---

## 👨‍💻 3步使用（开发者）

### Step 1: 创建Feature分支（30秒）

```bash
# 克隆仓库（如果还没有）
git clone https://github.com/your-org/your-repo.git
cd your-repo

# 创建feature分支
git checkout -b feature/your-feature-name

# 确认当前Phase（如果使用Claude Enhancer）
cat .phase/current
# 输出: P3
```

### Step 2: 开发并提交（正常开发）

```bash
# 开发你的功能
# ... 编码 ...

# 提交代码（会触发pre-commit检查）
git add .
git commit -m "feat: implement your feature"

# 如果pre-commit通过：
# ✅ 分支检查通过
# ✅ Phase验证通过
# ✅ 路径白名单通过
# ✅ 安全检查通过
# ✅ Linting通过

# 推送到远程
git push origin feature/your-feature-name
```

### Step 3: 创建PR（1分钟）

```bash
# 创建PR（模板自动加载）
gh pr create

# 或者在Web界面创建
# 访问: https://github.com/your-org/your-repo/pulls
# 点击 "New pull request"

# 填写PR模板：
# 1. 确认Phase信息
# 2. 勾选must_produce清单
# 3. 填写测试证据
# 4. 提供回滚方案
# 5. 说明影响范围

# 提交PR
# GitHub会自动：
# ✅ 添加CODEOWNERS为reviewer
# ✅ 触发CI运行
# ✅ 检查Branch Protection规则
```

---

## 📋 每日使用清单

### 开发者日常

```bash
# 1. 每天开始
git checkout main
git pull origin main

# 2. 创建新分支
git checkout -b feature/task-name

# 3. 开发功能
# ... 编码 ...

# 4. 提交代码
git add .
git commit -m "feat: description"  # 会触发pre-commit
git push origin feature/task-name

# 5. 创建PR
gh pr create
# 填写PR模板

# 6. 等待Review
gh pr checks  # 查看CI状态
gh pr view    # 查看PR详情

# 7. 合并（review通过后）
# 在PR页面点击 "Squash and merge"
# 或使用CLI：
gh pr merge --squash

# 8. 清理
git checkout main
git pull origin main
git branch -d feature/task-name
```

### Reviewer日常

```bash
# 1. 查看待审查的PR
gh pr list --assignee @me

# 2. 查看PR详情
gh pr view <pr-number>
gh pr diff <pr-number>

# 3. 在Web界面Review
# 访问PR页面
# 点击 "Files changed"
# 添加评论
# 点击 "Review changes" → "Approve"

# 4. 或使用CLI批准
gh pr review <pr-number> --approve --body "LGTM!"
```

---

## 🎯 重点记住

### 3个禁止

1. ❌ **禁止直接push到main** - 会被Branch Protection阻止
2. ❌ **禁止跳过PR模板** - 影响质量保证
3. ❌ **禁止绕过CI检查** - 所有checks必须通过

### 3个必须

1. ✅ **必须创建feature分支**
2. ✅ **必须完整填写PR模板**
3. ✅ **必须等待所有CI通过和Reviews批准**

### 3个建议

1. 💡 **小步提交** - 每个PR聚焦一个功能点
2. 💡 **提供回滚方案** - 确保可以快速回滚
3. 💡 **及时回复评论** - 加快合并速度

---

## 🆘 遇到问题？

### 问题1: pre-commit阻止提交

```bash
# 查看错误信息
# 常见原因：
# - 直接在main分支（应该在feature分支）
# - 修改了不允许的文件（检查当前Phase的allow_paths）
# - 代码有linting错误（运行npm run lint修复）
# - 包含敏感信息（移除密钥等）

# 解决：根据错误提示修复问题后重新commit
```

### 问题2: CI检查不通过

```bash
# 查看失败原因
gh pr checks <pr-number>

# 查看详细日志
gh run view <run-id> --log-failed

# 本地修复后推送
git add .
git commit -m "fix: resolve CI failures"
git push
```

### 问题3: PR无法合并

```bash
# 检查原因
gh pr view <pr-number>

# 常见原因：
# - CI未通过 → 等待CI或修复
# - Approvals不足 → 等待reviewers
# - 有未解决的对话 → 回复并resolve
# - Branch不是最新 → git pull origin main
```

---

## 📚 详细文档

需要更多信息？查看完整文档：

| 用途 | 文档 |
|------|------|
| **开始导航** | `docs/PR_AND_BRANCH_PROTECTION_README.md` |
| **配置Branch Protection** | `docs/BRANCH_PROTECTION_SETUP.md` |
| **使用PR模板** | `docs/PR_TEMPLATE_USAGE_GUIDE.md` |
| **快速参考** | `docs/PR_QUICK_REFERENCE.md` |
| **系统架构** | `docs/PR_SYSTEM_ARCHITECTURE.md` |

---

## 🎓 新手培训计划

### 第1周: 基础使用

- [ ] 阅读本快速开始指南（15分钟）
- [ ] 创建第一个feature分支（5分钟）
- [ ] 创建第一个PR（使用模板）（15分钟）
- [ ] 观察CI运行（10分钟）
- [ ] 学习如何回复Review评论（10分钟）

**练习**: 创建一个简单的文档更新PR

### 第2周: 深入理解

- [ ] 阅读`PR_TEMPLATE_USAGE_GUIDE.md`（30分钟）
- [ ] 了解8-Phase工作流（20分钟）
- [ ] 学习各Phase的must_produce要求（30分钟）
- [ ] 实践不同Phase的PR创建（1小时）

**练习**: 创建一个完整的功能PR（P1→P3→P4）

### 第3周: 最佳实践

- [ ] 阅读`BRANCH_PROTECTION_SETUP.md`（了解背后机制）（1小时）
- [ ] 学习Commit规范和最佳实践（30分钟）
- [ ] 了解回滚方案的编写（30分钟）
- [ ] 学习金丝雀发布流程（P7）（30分钟）

**练习**: 编写一个包含完整回滚方案的PR

---

## ✅ 验证清单

### 管理员验证

- [ ] `setup_branch_protection.sh`运行成功
- [ ] Branch Protection规则生效（Web界面可见）
- [ ] CODEOWNERS配置正确（无语法错误）
- [ ] 创建测试PR验证完整流程
- [ ] 团队成员已培训

### 开发者验证

- [ ] 能成功创建feature分支
- [ ] pre-commit检查正常工作
- [ ] PR模板自动加载
- [ ] CI自动运行
- [ ] CODEOWNERS自动添加reviewer
- [ ] 能成功合并PR

---

## 🎉 成功标志

当你看到以下情况，说明系统运行正常：

1. ✅ 开发者无法直接push到main
2. ✅ 每个PR都使用了模板
3. ✅ CI在每个PR上自动运行
4. ✅ CODEOWNERS自动分配reviewer
5. ✅ PR需要2+ approvals才能合并
6. ✅ 所有CI checks必须通过才能合并
7. ✅ Git历史保持线性（Squash merge）

---

## 📞 获取帮助

- **快速问题**: 查看`docs/PR_QUICK_REFERENCE.md`
- **详细指南**: 查看`docs/PR_TEMPLATE_USAGE_GUIDE.md`
- **配置问题**: 查看`docs/BRANCH_PROTECTION_SETUP.md`
- **提问**: 在GitHub Issues中提问

---

**恭喜！你已经完成了Claude Enhancer PR和Branch Protection系统的配置！**

**下一步**: 创建你的第一个PR试试吧！ 🚀

---

**文档版本**: 1.0
**最后更新**: 2025-01-15
**适用于**: Claude Enhancer 5.3+
