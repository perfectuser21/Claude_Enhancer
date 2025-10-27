# Implementation Plan - Workflow Enforcement Mechanism

## Phase 2: Implementation

### 2.1 创建Pre-commit Hook (核心)

**文件**: `.git/hooks/pre-commit` (追加到现有hook)

**功能模块**:
```bash
# Module 1: 检测分支类型
detect_branch_type() {
  # 返回: "coding" | "non-coding" | "unknown"
}

# Module 2: 检测代码改动
has_code_changes() {
  # 检查staged files是否包含代码文件
}

# Module 3: 检查Phase 1文档
check_phase1_docs() {
  # 检查docs/目录下的P1, CHECKLIST, PLAN文件
}

# Module 4: Bypass检查
check_bypass() {
  # 检查.workflow/BYPASS_WORKFLOW文件
}

# Module 5: 主逻辑
enforce_workflow() {
  if coding_branch && has_code && no_p1_docs && no_bypass; then
    echo "ERROR: Missing Phase 1 documents"
    exit 1
  fi
}
```

### 2.2 创建AI层提醒Hook

**文件**: `.claude/hooks/workflow_guardian.sh` (新文件)

**功能**: PreToolUse时检查，软提醒

### 2.3 创建CI验证

**文件**: `.github/workflows/workflow-validation.yml` (新文件)

**触发**: PR创建/更新时

**检查**:
```yaml
jobs:
  validate-workflow:
    runs-on: ubuntu-latest
    steps:
      - name: Check Phase 1 Docs
        run: |
          if [[ "${{ github.head_ref }}" =~ ^(feature|bugfix)/ ]]; then
            if ! ls docs/P1_*.md 1> /dev/null 2>&1; then
              echo "ERROR: Missing P1_DISCOVERY.md"
              exit 1
            fi
          fi
```

### 2.4 更新文档

**文件**: `CLAUDE.md`

**内容**: 在规则0后添加"Workflow Enforcement Mechanism"说明

## Phase 3: Testing

### 3.1 单元测试

**文件**: `tests/test_workflow_enforcement.sh`

```bash
# Test 1: Feature branch without P1 docs
test_feature_no_docs() {
  git checkout -b feature/test
  echo "change" >> test.sh
  git add test.sh
  git commit -m "test" && fail || pass
}

# Test 2: Feature branch with P1 docs
test_feature_with_docs() {
  touch docs/P1_TEST.md docs/CHECKLIST.md docs/PLAN.md
  git add docs/
  git commit -m "test" && pass || fail
}

# Test 3: Bypass mechanism
test_bypass() {
  echo '{"reason":"test"}' > .workflow/BYPASS_WORKFLOW
  git add .workflow/BYPASS_WORKFLOW
  git commit -m "test" && pass || fail
}
```

### 3.2 集成测试

完整workflow验证：
1. 创建feature分支
2. 尝试commit without P1 → 应该被阻止
3. 创建P1文档
4. Commit → 应该成功
5. 创建PR → CI应该通过

## Phase 4: Review

### 4.1 代码审查

- [ ] Hook逻辑正确
- [ ] 错误信息清晰
- [ ] 无误判
- [ ] 性能可接受

### 4.2 文档审查

- [ ] CLAUDE.md说明清楚
- [ ] Troubleshooting完整
- [ ] 示例准确

## Phase 5: Release

### 5.1 更新CHANGELOG

```markdown
## [8.0.2] - 2025-10-27

### Added
- **Workflow Enforcement Mechanism**: Automatic detection and prevention of workflow violations
  - Pre-commit hook checks for Phase 1 documents
  - AI layer reminder in PreToolUse
  - CI validation for PRs
  - Bypass mechanism for emergencies
```

### 5.2 版本更新

- VERSION: 8.0.2
- settings.json: 8.0.2
- manifest.yml: 8.0.2
- package.json: 8.0.2
- SPEC.yaml: 8.0.2
- CHANGELOG.md: 8.0.2

## Phase 6: Acceptance

用户验收：
1. 创建测试任务
2. 尝试跳过workflow → 被阻止
3. 完成Phase 1 → 允许继续
4. 确认机制有效

## Phase 7: Closure

1. 清理测试文件
2. 确保所有文档到位
3. 准备PR
4. 等待用户说"merge"

## Timeline

| Phase | 预计时间 | 说明 |
|-------|---------|------|
| Phase 2 | 2小时 | Hook实现 + CI配置 |
| Phase 3 | 1小时 | 测试 |
| Phase 4 | 30分钟 | Review |
| Phase 5 | 30分钟 | Release准备 |
| Phase 6 | 用户确认 | 等待 |
| Phase 7 | 15分钟 | Cleanup |
| **Total** | **~4小时** | Solo work |
