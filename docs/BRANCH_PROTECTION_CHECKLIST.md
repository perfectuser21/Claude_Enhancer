# GitHub Branch Protection配置检查清单

**仓库**: perfectuser21/Claude_Enhancer
**配置日期**: 2025-10-10
**配置人**: [您的名字]

---

## 🎯 配置步骤

### Step 1: 访问Branch Protection设置页面

**直接链接**:
```
https://github.com/perfectuser21/Claude_Enhancer/settings/branches
```

或手动导航:
1. 访问 https://github.com/perfectuser21/Claude_Enhancer
2. 点击 "Settings" 标签
3. 左侧菜单选择 "Branches"

### Step 2: 添加Main分支保护规则

1. 点击 **"Add branch protection rule"** 按钮

2. **Branch name pattern**: 输入 `main`

### Step 3: 配置保护规则

请按照以下清单逐项配置：

#### ✅ Protect matching branches

**Require a pull request before merging**
- [x] ✅ 勾选此项
- **Required approvals**: 选择 `2`
- [x] ✅ Dismiss stale pull request approvals when new commits are pushed
- [x] ✅ Require review from Code Owners (如果有CODEOWNERS文件)
- [ ] ☐ Require approval of the most recent reviewable push (可选)

**Require status checks to pass before merging**
- [x] ✅ 勾选此项
- [x] ✅ Require branches to be up to date before merging

**Required status checks** (添加以下9项):
```
1. validate-phase-gates
2. validate-must-produce
3. run-unit-tests
4. run-boundary-tests
5. run-smoke-tests
6. run-bdd-tests
7. check-security
8. validate-openapi
9. check-performance
```

**注意**:
- 这些status checks需要至少运行一次才会出现在列表中
- 如果看不到，需要先触发一次CI运行（创建PR即可触发）
- 或者先配置其他规则，status checks稍后添加

**Require conversation resolution before merging**
- [x] ✅ 勾选此项

**Require signed commits**
- [ ] ☐ 可选（如果团队使用GPG签名）

**Require linear history**
- [x] ✅ 勾选此项

**Require deployments to succeed before merging**
- [ ] ☐ 通常不需要

**Lock branch**
- [ ] ☐ 暂不锁定（会禁止所有push，包括merge）

**Do not allow bypassing the above settings**
- [x] ✅ Include administrators
  - 即使管理员也需要遵守规则
  - 这是最佳实践，确保代码质量

**Restrict who can push to matching branches**
- [ ] ☐ 通常不需要（PR机制已足够）

**Allow force pushes**
- [ ] ❌ 不要勾选（禁止force push）
  - Everyone: 禁止
  - Specify who can force push: 也禁止

**Allow deletions**
- [ ] ❌ 不要勾选（禁止删除main分支）

### Step 4: 保存配置

点击页面底部的 **"Create"** 按钮保存配置

---

## ✅ 验证清单

配置完成后，请验证以下内容：

### 验证1: 查看保护规则
- [ ] 访问 https://github.com/perfectuser21/Claude_Enhancer/settings/branch_protection_rules
- [ ] 看到 "main" 分支的保护规则
- [ ] 规则摘要显示正确

### 验证2: 尝试直接Push（应该被阻止）
```bash
cd "/home/xx/dev/Claude Enhancer 5.0"
git checkout main
git pull
echo "# Test" >> README.md
git commit -am "test: direct push to main"
git push origin main
```

**预期结果**:
```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: error: Cannot force-push to this branch
```

如果被阻止，说明配置成功！记得还原测试改动：
```bash
git reset --hard HEAD~1
```

### 验证3: 创建测试PR
```bash
git checkout -b test/branch-protection
echo "# Branch Protection Test" >> README.md
git commit -am "test: verify branch protection"
git push origin test/branch-protection
```

然后访问GitHub创建PR:
- [ ] PR页面显示需要2个approvals
- [ ] 显示9个required status checks（如果CI已配置）
- [ ] 显示需要resolve conversations
- [ ] 无法直接merge（按钮是灰色的）

### 验证4: Status Checks（如果已配置CI）

如果你的仓库有GitHub Actions配置（`.github/workflows/`），PR创建后会触发CI：
- [ ] 检查PR页面是否显示CI运行状态
- [ ] 等待所有checks完成
- [ ] 确认required checks都在列表中

**注意**: 如果CI尚未配置或首次运行，你需要：
1. 等待CI至少运行一次
2. 然后回到Branch Protection设置
3. 在"Required status checks"中搜索并添加这9个checks

---

## 🔧 常见问题

### Q1: 看不到Required status checks选项

**原因**: CI还没有运行过，GitHub不知道有哪些checks

**解决**:
1. 先保存当前配置（不包含status checks）
2. 创建一个测试PR触发CI
3. CI运行后，回来编辑规则添加status checks

### Q2: 配置后无法合并自己的PR

**原因**: 设置了2个approvals，但只有你一个人

**解决**:
- 暂时将approvals改为1
- 或者邀请协作者帮忙approve
- 或者使用admin override（不推荐）

### Q3: Force push被阻止了，但我需要rebase

**原因**: "Require linear history"禁止了某些操作

**解决**:
- 使用 `git merge` 而不是 `git rebase`
- 或者在PR分支上rebase（不影响main）
- 或者临时禁用"Allow force pushes"后再恢复

### Q4: Status checks一直pending

**原因**: CI配置有问题或未触发

**解决**:
1. 检查 `.github/workflows/` 中的workflow文件
2. 确认workflow的 `on:` 配置包含 `pull_request`
3. 查看Actions tab的运行日志
4. 临时去掉status checks要求，待修复后再加回

---

## 📊 配置摘要

配置完成后，你的main分支将受到以下保护：

| 保护项 | 状态 | 说明 |
|-------|------|------|
| 需要PR | ✅ | 无法直接push到main |
| Approvals | ✅ | 需要2个reviewer批准 |
| Status Checks | ✅ | 9个CI checks必须通过 |
| Conversation Resolution | ✅ | 所有讨论必须resolved |
| Linear History | ✅ | 禁止merge commits |
| Force Push | ❌ | 禁止force push |
| Delete Branch | ❌ | 禁止删除main分支 |
| Admin Bypass | ❌ | 管理员也需遵守规则 |

---

## 🎯 下一步

配置完成后：

1. **团队培训**
   - 通知团队成员新的工作流程
   - 解释为什么需要PR和review
   - 培训如何创建和review PR

2. **文档更新**
   - 更新项目README
   - 添加贡献指南（CONTRIBUTING.md）
   - 说明PR流程

3. **持续改进**
   - 收集团队反馈
   - 根据实际情况调整规则
   - 定期review保护设置

4. **配置其他分支**（可选）
   - develop分支: 较宽松的保护
   - release/* 分支: 更严格的保护

---

## 📝 配置记录

| 项目 | 值 |
|-----|---|
| 配置人 | [填写] |
| 配置时间 | [填写] |
| 保护级别 | Claude Enhancer Standard |
| Required Approvals | 2 |
| Required Checks | 9 |
| 验证状态 | [填写：已验证/待验证] |
| 备注 | [填写] |

---

**配置完成后请在此签名**: _________________ 日期: _________

---

*此检查清单是Claude Enhancer v5.4.0 Branch Protection配置的一部分*

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
