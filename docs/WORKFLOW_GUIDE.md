# Claude Enhancer v6.0 工作流指南

## 📋 目录

1. [8-Phase 工作流详解](#8-phase-工作流详解)
2. [环境变量配置](#环境变量配置)
3. [Git Hooks 集成](#git-hooks-集成)
4. [CI/CD 流程](#cicd-流程)
5. [常见场景](#常见场景)

---

## 🔄 8-Phase 工作流详解

### Phase 0: Discovery（探索）

**触发条件**:
- 新任务开始
- 技术选型需要
- 可行性验证

**必须产出**:
- 技术评估报告
- 可行性结论

**自动化支持**:
```bash
# 自动创建探索分支
export CE_AUTO_CREATE_BRANCH=true
git checkout -b discovery/feature-name
```

**质量门控**:
- 必须有明确的技术结论
- 风险评估完成

---

### Phase 1: Planning（规划）

**触发条件**:
- P0 完成
- 需求明确

**必须产出**:
- `docs/PLAN.md`

**Gates 规则**:
```yaml
P1:
  allow_paths: ["docs/**", "*.md"]
  must_produce: ["docs/PLAN.md"]
```

**自动化支持**:
- `requirements_validator.sh` 自动检查

---

### Phase 2: Skeleton（骨架）

**触发条件**:
- P1 完成
- 架构设计就绪

**必须产出**:
- 目录结构
- 配置文件框架

**Gates 规则**:
```yaml
P2:
  allow_paths: ["**"]
  must_produce: ["src/", "test/"]
```

---

### Phase 3: Implementation（实现）

**触发条件**:
- P2 完成
- 开发环境就绪

**必须产出**:
- 源代码
- 单元测试

**自动化支持**:
```bash
# Smart Agent 选择
.claude/hooks/smart_agent_selector.sh
# 建议: 使用6个Agent并行开发
```

**质量门控**:
- 代码覆盖率 > 80%
- 无严重安全问题

---

### Phase 4: Testing（测试）

**触发条件**:
- P3 代码完成

**必须产出**:
- 测试报告
- 覆盖率报告

**CI 集成**:
```yaml
name: test-suite
jobs:
  - unit-tests
  - integration-tests
  - performance-tests
```

---

### Phase 5: Review（审查）

**触发条件**:
- P4 测试通过

**必须产出**:
- `docs/REVIEW.md`
- 审查意见

**自动化**:
- `review_preparation.sh` 准备审查

---

### Phase 6: Release（发布）

**触发条件**:
- P5 审查通过
- 版本准备就绪

**必须产出**:
- Git tag
- Release notes

**命令**:
```bash
git tag -a v6.0.0 -m "Release v6.0.0"
git push origin v6.0.0
```

---

### Phase 7: Monitor（监控）

**触发条件**:
- P6 发布完成

**必须产出**:
- 监控配置
- 告警规则

---

## 🔧 环境变量配置

### 完全自动模式

```bash
# 启用所有自动化
export CE_AUTO_MODE=true
export CE_SILENT_MODE=false  # 保留输出用于调试
export CE_COMPACT_OUTPUT=false
export CE_AUTO_CREATE_BRANCH=true
export CE_AUTO_CONFIRM=true
export CE_AUTO_SELECT_DEFAULT=true
```

### 静默生产模式

```bash
# 生产环境静默运行
export CE_AUTO_MODE=true
export CE_SILENT_MODE=true  # 完全静默
export CE_COMPACT_OUTPUT=false
export CE_AUTO_CREATE_BRANCH=true
export CE_AUTO_CONFIRM=true
export CE_AUTO_SELECT_DEFAULT=true
```

### 交互开发模式

```bash
# 开发时交互确认
export CE_AUTO_MODE=false
export CE_SILENT_MODE=false
export CE_COMPACT_OUTPUT=true  # 紧凑输出
export CE_AUTO_CREATE_BRANCH=false
export CE_AUTO_CONFIRM=false
export CE_AUTO_SELECT_DEFAULT=false
```

---

## 🪝 Git Hooks 集成

### pre-commit

**功能**:
- Phase 路径验证
- Must-produce 检查
- 代码格式化

**跳过方法**:
```bash
git commit --no-verify  # 紧急情况使用
```

### commit-msg

**格式要求**:
```
type(scope): description

- type: feat/fix/docs/style/refactor/test/chore
- scope: 影响范围
- description: 简短描述
```

### pre-push

**检查项**:
- Phase 完成度
- 测试通过
- 安全扫描

---

## 🚀 CI/CD 流程

### Required Status Checks（必须通过）

1. **ce-unified-gates**
   - Phase 验证
   - Gates 规则检查
   - 版本一致性

2. **test-suite**
   - 单元测试
   - 集成测试
   - 性能测试

3. **security-scan**
   - 密钥检测
   - 依赖安全
   - 代码安全模式

### 可选 Checks

4. **bp-guard**（每周一运行）
   - Branch Protection 验证
   - 配置漂移检测

5. **release**（手动触发）
   - 版本发布
   - Tag 创建
   - Release notes

---

## 📚 常见场景

### 场景1: 新功能开发

```bash
# 1. 设置自动模式
export CE_AUTO_MODE=true

# 2. 开始任务（自动创建分支）
# 系统自动: git checkout -b feature/xxx

# 3. 执行 P0-P7
# P0: 技术探索
# P1: 创建 PLAN.md
# P2: 搭建目录结构
# P3: 编写代码
# P4: 运行测试
# P5: 代码审查
# P6: 发布准备
# P7: 配置监控

# 4. 合并到主分支
gh pr create --base main
gh pr merge --squash
```

### 场景2: Bug 修复

```bash
# 1. 创建修复分支
git checkout -b bugfix/issue-123

# 2. 快速修复（跳到 P3）
echo "P3" > .phase/current

# 3. 修复代码
# ... 编辑文件 ...

# 4. 测试验证（P4）
npm test

# 5. 提交
git commit -m "fix: 修复XXX问题"
git push
```

### 场景3: 紧急热修复

```bash
# 1. 从main创建hotfix
git checkout main
git checkout -b hotfix/critical-issue

# 2. 快速修复
# 编辑...

# 3. 跳过部分检查
git commit --no-verify -m "hotfix: 紧急修复"
git push

# 4. 快速合并
gh pr create --base main --title "HOTFIX"
gh pr merge --admin  # 需要admin权限
```

---

## 🔍 故障排除

### 问题1: Phase 验证失败

```bash
错误: "Not allowed to modify files in current phase"

解决:
1. 检查当前 phase: cat .phase/current
2. 查看允许路径: grep "allow_paths" .workflow/gates.yml
3. 切换到正确 phase: echo "P3" > .phase/current
```

### 问题2: Required Checks 失败

```bash
错误: "Required status check 'ce-unified-gates' failed"

解决:
1. 查看CI日志: gh run view
2. 本地运行检查: ./.github/workflows/ce-unified-gates.yml
3. 修复问题后重新推送
```

### 问题3: Hooks 执行太慢

```bash
症状: Git操作卡顿

解决:
1. 启用静默模式: export CE_SILENT_MODE=true
2. 检查性能: time .claude/hooks/performance_monitor.sh
3. 临时禁用: git commit --no-verify
```

---

## 📞 获取帮助

- 查看系统状态: `./scripts/verify_v6.sh`
- 查看当前 Phase: `cat .phase/current`
- 查看 Gates 规则: `cat .workflow/gates.yml`
- 查看版本: `cat VERSION`

---

*Claude Enhancer v6.0 Workflow Guide - 让工作流自动化*