# PR和Branch Protection快速参考

> 这是一张速查卡，包含最常用的命令和检查清单。详细信息请参考完整文档。

## 📝 创建PR速查

### 开发者快速流程

```bash
# 1. 创建feature分支
git checkout -b feature/your-feature

# 2. 确认当前Phase
cat .phase/current
# 输出: P3 (或其他Phase)

# 3. 开发功能...
# (编码、测试)

# 4. 提交（会触发pre-commit检查）
git add .
git commit -m "feat: implement feature"
# ✅ 自动检查: 分支、Phase、路径、安全、linting

# 5. 推送
git push origin feature/your-feature

# 6. 创建PR（模板自动加载）
gh pr create

# 7. 填写PR模板
# - 勾选当前Phase的must_produce清单
# - 填写测试证据
# - 提供回滚方案

# 8. 等待CI和Review
gh pr checks  # 查看CI状态

# 9. 合并（所有检查通过后）
gh pr merge --squash
```

---

## 🎯 各Phase必须产出速查

| Phase | Must Produce | 关键文件 |
|-------|-------------|----------|
| **P0** | SPIKE.md (GO/NO-GO) | docs/SPIKE.md |
| **P1** | PLAN.md (≥5任务) | docs/PLAN.md |
| **P2** | 目录骨架 | src/**, docs/SKELETON-NOTES.md |
| **P3** | 功能代码 + CHANGELOG | src/**, docs/CHANGELOG.md |
| **P4** | 测试(≥2) + TEST-REPORT | tests/**, docs/TEST-REPORT.md |
| **P5** | REVIEW.md + 结论 | docs/REVIEW.md |
| **P6** | README + 版本号 + tag | docs/README.md, CHANGELOG.md |
| **P7** | SLO + 告警 + MONITORING | observability/**, docs/MONITORING.md |

---

## ✅ PR检查清单

### 提交前（Local）

```
□ 代码已格式化 (npm run format / prettier)
□ Linting通过 (npm run lint)
□ 测试通过 (npm test) - P4阶段必须
□ .phase/current正确
□ 只修改了allow_paths内的文件
□ 无敏感信息（密钥、token等）
□ Commit消息符合规范 (feat/fix/docs: ...)
```

### PR创建后

```
□ PR模板完整填写
  □ Phase信息正确
  □ must_produce清单全部勾选
  □ 测试证据已提供
  □ 回滚方案可执行
  □ 影响范围已说明

□ CI检查全部通过
  □ validate-phase-gates ✅
  □ validate-must-produce ✅
  □ run-unit-tests ✅
  □ run-boundary-tests ✅
  □ run-smoke-tests ✅
  □ check-security ✅
  □ (其他检查...)

□ CODEOWNERS已自动添加

□ 等待2+ approvals

□ 所有对话已解决
```

### 合并前

```
□ 所有CI检查通过 ✅
□ 获得2+个approval ✅
□ 对话全部resolved ✅
□ Branch是最新的（基于main）
□ 选择Squash merge（保持历史清晰）
□ 合并后删除feature分支
```

---

## 🚨 常见问题快速解决

### Q: pre-commit阻止了我的提交

```bash
# 问题1: 禁止直接提交main
❌ ERROR: 禁止直接提交到 main 分支

# 解决:
git checkout -b feature/your-feature
git cherry-pick <commit-hash>

# 问题2: 路径白名单违规
❌ ERROR: src/api.ts 不在P1允许路径内

# 解决: 检查当前Phase是否正确
cat .phase/current
# 如果Phase错误，切换Phase
./.workflow/phase_switcher.sh P3

# 问题3: 安全检查失败
❌ ERROR: 检测到私钥

# 解决: 移除敏感信息，使用环境变量
git reset HEAD~1
# 编辑文件，移除敏感信息
git add .
git commit -m "fix: remove sensitive data"
```

### Q: CI一直不通过

```bash
# 1. 查看失败的具体原因
gh pr checks <pr-number>

# 2. 查看详细日志
gh run view <run-id> --log-failed

# 3. 本地重现并修复
npm run test  # 或其他失败的命令
npm run lint

# 4. 修复后推送
git add .
git commit -m "fix: resolve CI failures"
git push
```

### Q: PR无法合并

```bash
# 原因1: Status checks未通过
# 解决: 等待CI完成或修复失败的检查

# 原因2: Approvals不足
# 解决: 等待reviewers批准，或主动提醒

# 原因3: Branch不是最新
# 解决:
git checkout feature-branch
git pull origin main
git push

# 原因4: 有未解决的对话
# 解决: 在PR页面回复所有评论并点击Resolve
```

---

## 🔧 常用命令速查

### GitHub CLI (gh)

```bash
# PR相关
gh pr create                          # 创建PR（模板自动加载）
gh pr create --template p3.md        # 使用特定模板
gh pr list                            # 列出所有PR
gh pr view <pr-number>                # 查看PR详情
gh pr checks <pr-number>              # 查看CI状态
gh pr review <pr-number> --approve   # 批准PR
gh pr merge <pr-number> --squash     # 合并PR
gh pr close <pr-number>              # 关闭PR

# Branch Protection相关
gh api repos/{owner}/{repo}/branches/main/protection  # 查看保护规则
gh api repos/{owner}/{repo}/codeowners/errors         # 验证CODEOWNERS

# Workflow相关
gh run list                          # 列出workflow运行
gh run view <run-id>                 # 查看运行详情
gh run view <run-id> --log-failed   # 查看失败日志
gh workflow run <workflow-name>      # 手动触发workflow
```

### Git常用命令

```bash
# 分支管理
git checkout -b feature/name         # 创建并切换分支
git branch -d feature/name           # 删除本地分支
git push origin --delete feature/name # 删除远程分支

# 提交管理
git commit -m "type: message"        # 规范提交
git commit --amend                   # 修改最后一次提交
git revert <commit-hash>             # 回滚提交

# 同步
git pull origin main                 # 拉取main最新代码
git push origin feature-branch       # 推送分支
git push --force-with-lease          # 安全的强制推送（rebase后）

# 解决冲突
git pull origin main                 # 拉取最新代码
# 解决冲突文件
git add .
git commit -m "resolve: merge conflicts"
git push
```

### Phase管理

```bash
# 查看当前Phase
cat .phase/current

# 切换Phase
./.workflow/phase_switcher.sh P3

# 切换到下一个Phase
./.workflow/phase_switcher.sh next

# 验证Phase完成度
./.workflow/gate_validator.sh P3
```

### 测试和验证

```bash
# JavaScript/TypeScript
npm run lint                         # Linting
npm run format                       # 格式化
npm test                            # 运行测试
npm run test:coverage               # 测试覆盖率

# Python
flake8 .                            # Linting
pytest                              # 运行测试
pytest --cov                        # 测试覆盖率

# Shell脚本
shellcheck script.sh                # Shell脚本检查
```

---

## 📊 Phase到PR的快速映射

### P0 Discovery → PR重点

```markdown
☑ 核心产出:
  • docs/SPIKE.md (GO/NO-GO决策)

☑ 允许路径:
  • ** (所有文件)

☑ PR必填:
  • 可行性结论
  • 技术风险识别
  • 原型代码（可选）
```

### P1 Plan → PR重点

```markdown
☑ 核心产出:
  • docs/PLAN.md
  • 任务清单 ≥5条
  • 受影响文件清单

☑ 允许路径:
  • docs/PLAN.md

☑ PR必填:
  • 任务清单（每条含文件/模块名）
  • 回滚方案
```

### P3 Implementation → PR重点

```markdown
☑ 核心产出:
  • 功能代码（可构建）
  • docs/CHANGELOG.md更新

☑ 允许路径:
  • src/**
  • docs/CHANGELOG.md

☑ PR必填:
  • 构建验证通过
  • CHANGELOG Unreleased段更新
  • 变更点清单
  • 详细回滚方案
```

### P4 Testing → PR重点

```markdown
☑ 核心产出:
  • 测试用例 ≥2条（含边界测试）
  • docs/TEST-REPORT.md

☑ 允许路径:
  • tests/**
  • docs/TEST-REPORT.md

☑ PR必填:
  • 测试执行日志
  • 测试覆盖率
  • 所有测试通过证明

☑ 强制:
  • pre-push: npm test必须通过
```

### P6 Release → PR重点

```markdown
☑ 核心产出:
  • docs/README.md (安装、使用、注意事项)
  • docs/CHANGELOG.md (版本号递增)
  • Git tag

☑ 允许路径:
  • docs/**
  • .tags/**

☑ PR必填:
  • 版本号正确
  • Release notes完整
  • 升级指南
```

---

## 🎭 Hotfix紧急修复流程

```bash
# 1. 创建hotfix分支
git checkout -b hotfix/critical-fix

# 2. 快速修复
# (修改代码)

# 3. 简化验证
npm run build  # 确保能构建
npm run test:smoke  # 快速冒烟测试

# 4. 提交
git add .
git commit -m "fix: critical bug"

# 5. 创建PR（使用简化模板）
gh pr create --title "🔥 Hotfix: Critical Bug" --label hotfix,urgent

# 6. 填写简化版PR
# - 问题描述
# - 修复方案
# - 快速验证结果
# - 回滚方案

# 7. 快速review（1个approval即可，如配置）
# 8. 立即合并
gh pr merge --squash

# 9. 金丝雀部署
# 10% → 观察10分钟 → 50% → 100%

# 10. 事后补充
# - 完整测试
# - 文档更新
# - Root cause分析
```

---

## 🛡️ 安全检查清单

```
□ 无硬编码密钥
  ✗ const API_KEY = "sk-abc123"
  ✓ const API_KEY = process.env.API_KEY

□ 无私钥文件
  ✗ id_rsa, *.pem, *.key

□ 无敏感配置
  ✗ .env (应在.gitignore中)
  ✓ .env.example (模板可以commit)

□ 无云服务密钥
  ✗ AWS_SECRET_ACCESS_KEY=xxx
  ✗ GOOGLE_APPLICATION_CREDENTIALS=xxx

□ 无数据库密码
  ✗ DB_PASSWORD=password123

□ 无API token
  ✗ GITHUB_TOKEN=ghp_xxx

□ 敏感操作有权限检查
  ✓ if (!user.isAdmin()) throw new Error()

□ 输入验证充分
  ✓ validate(input) before use
```

---

## 📏 Commit消息规范

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

| Type | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(auth): add OAuth login |
| fix | Bug修复 | fix(api): handle null response |
| docs | 文档 | docs(readme): update install guide |
| style | 格式 | style: fix indentation |
| refactor | 重构 | refactor(db): optimize query |
| perf | 性能 | perf(cache): improve hit rate |
| test | 测试 | test(auth): add boundary tests |
| chore | 构建 | chore: update dependencies |

### 好的示例

```bash
# 简单提交
git commit -m "feat(session): implement Redis store"

# 包含body
git commit -m "feat(session): implement Redis store

Add Redis as session storage backend for distributed sessions.
Includes connection pool management and automatic failover."

# 包含breaking change
git commit -m "feat(api): redesign authentication

BREAKING CHANGE: API authentication now requires OAuth2.
Old API key method is no longer supported.
See MIGRATION.md for upgrade guide."
```

---

## 🔗 快速链接

| 资源 | 链接 |
|------|------|
| **文档导航** | docs/PR_AND_BRANCH_PROTECTION_README.md |
| **配置指南** | docs/BRANCH_PROTECTION_SETUP.md |
| **使用指南** | docs/PR_TEMPLATE_USAGE_GUIDE.md |
| **系统架构** | docs/PR_SYSTEM_ARCHITECTURE.md |
| **PR模板** | .github/PULL_REQUEST_TEMPLATE.md |
| **CODEOWNERS** | .github/CODEOWNERS |
| **配置脚本** | scripts/setup_branch_protection.sh |
| **8-Phase工作流** | .claude/WORKFLOW.md |
| **质量保障** | docs/WORKFLOW_QUALITY_ASSURANCE.md |

---

## 💡 提示和技巧

### 提高效率

```bash
# 1. 使用别名
alias pr='gh pr create'
alias prc='gh pr checks'
alias prv='gh pr view'
alias prm='gh pr merge --squash'

# 2. 保存常用命令
cat > ~/pr_commands.sh << 'EOF'
#!/bin/bash
# 创建PR并自动打开浏览器
pr() {
    gh pr create && gh pr view --web
}

# 查看PR状态
prs() {
    gh pr checks && gh pr view
}
EOF

source ~/pr_commands.sh

# 3. 使用Git模板
git config --global commit.template ~/.gitmessage
cat > ~/.gitmessage << 'EOF'
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>

# Type: feat|fix|docs|style|refactor|perf|test|chore
EOF
```

### 调试技巧

```bash
# 1. 查看pre-commit详细输出
GIT_TRACE=1 git commit -m "test"

# 2. 临时跳过hooks（仅调试，不推荐）
git commit --no-verify -m "debug"

# 3. 查看CI环境变量
gh run view <run-id> --log | grep "##\[set-output\]"

# 4. 本地模拟CI
docker run -v $(pwd):/app -w /app node:18 npm test

# 5. 验证CODEOWNERS匹配
# (没有官方工具，需要手动测试或使用第三方工具)
```

---

## 📱 移动端/Web界面操作

### GitHub Web界面

```
创建PR:
1. 访问仓库页面
2. 点击 "Pull requests" 标签
3. 点击 "New pull request"
4. 选择base(main) 和 compare(feature-branch)
5. 点击 "Create pull request"
6. 填写PR模板
7. 点击 "Create pull request"

查看CI状态:
1. 打开PR页面
2. 滚动到底部 "Checks" 区域
3. 点击任意check查看详情

Approve PR:
1. 打开PR页面
2. 点击 "Files changed" 标签
3. Review代码
4. 点击 "Review changes"
5. 选择 "Approve"
6. 点击 "Submit review"

Merge PR:
1. 确保所有checks通过
2. 确保有足够approvals
3. 滚动到底部
4. 选择 "Squash and merge"
5. 编辑commit消息（可选）
6. 点击 "Confirm squash and merge"
7. 勾选 "Delete branch"
```

---

## 🎯 记住这些关键点

1. **永远不要直接push到main** - 使用feature分支
2. **填写完整的PR模板** - 这是质量保证
3. **提供可执行的回滚方案** - 这是安全保障
4. **等待所有CI通过** - 不要催促合并
5. **遵循Phase工作流** - 每个Phase有明确产出
6. **Squash merge保持历史清晰** - 一个feature一个commit
7. **及时回复review评论** - 加快合并速度
8. **测试证据必须真实** - 不要复制粘贴假数据

---

**打印此页，贴在显示器旁边！**

**需要详细信息？查看**: `docs/PR_AND_BRANCH_PROTECTION_README.md`
