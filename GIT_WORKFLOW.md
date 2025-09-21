# Claude Enhancer 完整Git工作流
## 从分支创建到最终合并的6步流程

```
┌──────────────┐
│ 1. 创建分支  │
└──────┬───────┘
       ↓
┌──────────────┐
│ 2. 开发阶段  │ ← Claude Code主动约束（5-10 agents）
└──────┬───────┘
       ↓
┌──────────────┐
│ 3. 测试验证  │ ← 自动化测试 + 代码审查
└──────┬───────┘
       ↓
┌──────────────┐
│ 4. 提交代码  │ ← Git Hooks质量检查
└──────┬───────┘
       ↓
┌──────────────┐
│ 5. 推送&PR   │ ← CI/CD pipeline
└──────┬───────┘
       ↓
┌──────────────┐
│ 6. 合并主分支│ ← 最终验证
└──────────────┘
```

## 详细步骤

### 步骤 1️⃣：创建功能分支
```bash
# 从主分支创建新分支
git checkout main
git pull origin main
git checkout -b feature/user-authentication

# 或者使用Git Flow
git flow feature start user-authentication
```

**Claude Code行为**：
- 识别任务类型
- 准备相应的agents组合

### 步骤 2️⃣：开发实现（Claude Code主动约束）

**自动触发Max 20X模式**：
```
用户："实现用户认证功能"
    ↓
Claude Code自检（RULES.md）
    ↓
主动使用7个agents：
- backend-architect（架构设计）
- security-auditor（安全审计）
- api-designer（API设计）
- database-specialist（数据库设计）
- test-engineer（测试方案）
- frontend-specialist（前端实现）
- devops-engineer（部署配置）
    ↓
并行执行，生成高质量代码
```

**产出**：
- 完整的功能代码
- 单元测试
- API文档
- 部署配置

### 步骤 3️⃣：测试验证

```bash
# 运行测试套件
npm test
# 或
python -m pytest

# 代码覆盖率检查
npm run coverage
# 或
pytest --cov

# 安全扫描
npm audit
# 或
bandit -r .

# 代码质量检查
npm run lint
# 或
pylint **/*.py
```

**质量标准**：
- ✅ 测试覆盖率 > 80%
- ✅ 0个安全漏洞
- ✅ 代码规范通过

### 步骤 4️⃣：提交代码（Git Hooks介入）

```bash
# 添加更改
git add .

# 提交（触发pre-commit hook）
git commit -m "feat(auth): implement user authentication system

- Added JWT-based authentication
- Implemented password reset flow
- Created user registration API
- Added comprehensive test suite
- Security hardening with rate limiting

Used 7 specialized agents for implementation"
```

**Pre-commit Hook检查**：
```bash
🔍 Claude Enhancer Pre-commit Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ✅ Test files found
2. ✅ Documentation found
3. ✅ Code formatted
4. ✅ No security issues
5. ✅ Commit size OK
6. ✅ Multi-agent collaboration detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All checks passed!
```

**Commit-msg Hook验证**：
```bash
🔍 Commit Message Check
━━━━━━━━━━━━━━━━━━━━━
✅ Format: feat(auth): ...
✅ Agent collaboration mentioned
✅ Message length OK
━━━━━━━━━━━━━━━━━━━━━
```

### 步骤 5️⃣：推送和创建PR

```bash
# 推送到远程
git push origin feature/user-authentication

# 创建Pull Request（使用GitHub CLI）
gh pr create \
  --title "feat(auth): User Authentication System" \
  --body "## Summary
- Implemented complete authentication system
- JWT tokens with refresh mechanism
- Password reset flow
- Rate limiting and security measures

## Agents Used (7)
- backend-architect
- security-auditor
- api-designer
- database-specialist
- test-engineer
- frontend-specialist
- devops-engineer

## Checklist
- [x] Tests passing (95% coverage)
- [x] Documentation updated
- [x] Security review completed
- [x] Performance tested
- [x] Deployment ready

## Screenshots
[Add if applicable]

🤖 Generated with Claude Enhancer Max Quality Mode"
```

**CI/CD Pipeline自动运行**：
```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on: [pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: npm test
      - name: Check coverage
        run: npm run coverage
      - name: Security scan
        run: npm audit
      - name: Build
        run: npm run build
```

### 步骤 6️⃣：代码审查和合并

**PR审查清单**：
```markdown
## Code Review Checklist
- [ ] 架构设计合理
- [ ] 安全措施到位
- [ ] 测试覆盖完整
- [ ] 文档清晰完整
- [ ] 性能优化适当
- [ ] 遵循项目规范
- [ ] 无明显技术债
```

**合并策略**：
```bash
# 方式1: Squash and merge（推荐）
gh pr merge --squash

# 方式2: Merge commit
gh pr merge --merge

# 方式3: Rebase and merge
gh pr merge --rebase

# 合并后删除分支
git branch -d feature/user-authentication
git push origin --delete feature/user-authentication
```

## 完整示例脚本

```bash
#!/bin/bash
# complete_workflow.sh

# 1. 创建分支
git checkout -b feature/new-feature

# 2. 开发（Claude Code使用7个agents）
echo "Developing with 7 agents..."

# 3. 测试
npm test
npm run coverage

# 4. 提交
git add .
git commit -m "feat: implement new feature with 7 agents"

# 5. 推送
git push origin feature/new-feature

# 6. 创建PR
gh pr create --fill

echo "Workflow complete! Ready for review."
```

## 时间线示例

| 步骤 | 活动 | 时间 | 质量检查点 |
|------|------|------|-----------|
| 1 | 创建分支 | 5分钟 | 分支命名规范 |
| 2 | 开发实现 | 2-4小时 | 7个agents并行 |
| 3 | 测试验证 | 30分钟 | 覆盖率>80% |
| 4 | 代码提交 | 10分钟 | Git Hooks通过 |
| 5 | 推送&PR | 15分钟 | CI/CD通过 |
| 6 | 审查&合并 | 1-2小时 | PR审查通过 |

**总计：4-7小时完成一个高质量功能**

## 关键质量保证点

### 每个步骤的质量门槛：

1. **分支创建**：命名规范（feature/、bugfix/、hotfix/）
2. **开发阶段**：最少5个agents，最好7-10个
3. **测试阶段**：覆盖率80%+，0个严重bug
4. **提交阶段**：Pre-commit检查全部通过
5. **推送阶段**：CI/CD pipeline绿色
6. **合并阶段**：至少1人审查通过

## 自动化脚本集成

将这些步骤集成到项目中：
```bash
# 添加到package.json
"scripts": {
  "workflow:start": "git checkout -b feature/$1",
  "workflow:test": "npm test && npm run coverage",
  "workflow:commit": "git add . && git commit",
  "workflow:push": "git push origin HEAD",
  "workflow:pr": "gh pr create --fill",
  "workflow:complete": "npm run workflow:test && npm run workflow:commit && npm run workflow:push && npm run workflow:pr"
}
```

---

这就是完整的6步工作流，从创建分支到最终合并，每一步都有质量保证！