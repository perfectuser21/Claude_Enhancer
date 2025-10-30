# Acceptance Checklist - Workflow Consistency Fixes
**Version**: 8.6.1 (target)
**Task**: 修复10个workflow一致性问题
**Branch**: feature/workflow-consistency-fixes
**Created**: 2025-10-30 16:15

---

## 用户版验收清单（User-Facing）

### 功能验收（What Changed）

#### ✅ 文档一致性修复
- [ ] SPEC.yaml、manifest.yml、CLAUDE.md三者完全一致
- [ ] 不再有自相矛盾的描述
- [ ] Phase 1产出文件名统一为P1_DISCOVERY.md
- [ ] 版本文件数量统一为6个

#### ✅ 代码清理
- [ ] TODO/FIXME从8个减至≤5个
- [ ] 所有保留的TODO都有明确理由
- [ ] 没有过期注释

#### ✅ 测试覆盖
- [ ] 新增契约测试验证一致性
- [ ] 契约测试通过
- [ ] 防止未来回归

### 质量验收（Quality Standards）

#### ✅ 自动化检查全部通过
- [ ] `bash scripts/static_checks.sh` ✅
- [ ] `bash scripts/pre_merge_audit.sh` ✅
- [ ] `bash scripts/check_version_consistency.sh` ✅
- [ ] `bash tests/contract/test_workflow_consistency.sh` ✅
- [ ] `bash tools/verify-core-structure.sh` ✅

#### ✅ 版本升级正确
- [ ] VERSION文件: 8.6.1
- [ ] settings.json: 8.6.1
- [ ] manifest.yml: 8.6.1
- [ ] package.json: 8.6.1
- [ ] CHANGELOG.md: 8.6.1
- [ ] SPEC.yaml: 8.6.1

#### ✅ 文档完整性
- [ ] CHANGELOG.md记录了本次修复
- [ ] README.md版本号已更新
- [ ] 所有Phase文档存在（P1_DISCOVERY, IMPACT_ASSESSMENT, PLAN, REVIEW, ACCEPTANCE_REPORT）

### 过程验收（Process Validation）

#### ✅ 工作流遵守情况
- [ ] 严格遵守7-Phase工作流（未跳过任何Phase）
- [ ] Phase 1包含所有5个子阶段
- [ ] Phase 3通过Quality Gate 1
- [ ] Phase 4通过Quality Gate 2

#### ✅ 多Subagent使用
- [ ] Impact Assessment自动计算了影响半径（Radius=63）
- [ ] 推荐使用6个Agent（高风险任务）
- [ ] 实际使用了6个并行Agent
- [ ] Agent分工明确（SPEC/manifest/LOCK/TODO/CLAUDE/Contract）

#### ✅ Bypass Permissions生效
- [ ] 整个过程没有弹窗询问用户权限
- [ ] AI自主完成所有技术决策
- [ ] 用户仅在Phase 6验收时参与

#### ✅ 工作记录完整
- [ ] 每个Phase有文档记录
- [ ] Git commit历史清晰
- [ ] Evidence收集完整
- [ ] 可追溯所有变更

---

## 技术版验收清单（Technical）

### Issue修复验证

#### Issue #1: SPEC.yaml产出文件名
- [ ] `.workflow/SPEC.yaml:135` 改为`P1_DISCOVERY.md`
- [ ] 搜索全文没有`P2_DISCOVERY.md`（除非在注释说明）

#### Issue #2: 版本文件数量
- [ ] `.workflow/SPEC.yaml:90` 说6个文件
- [ ] `.workflow/SPEC.yaml:170-178` 列出6个文件（包含SPEC.yaml自己）
- [ ] `scripts/check_version_consistency.sh` 检查6个文件
- [ ] `CLAUDE.md` 说6个文件

#### Issue #3: manifest.yml多余子阶段
- [ ] `.workflow/manifest.yml:18` 移除了"Dual-Language Checklist Generation"
- [ ] 子阶段数量=5（与SPEC.yaml对齐）
- [ ] settings.json的hook配置保持不变（仍然在phase1.3_complete触发）

#### Issue #4: TODO/FIXME清理
- [ ] 总数量≤5个
- [ ] 每个保留的TODO都有明确理由
- [ ] `bash scripts/pre_merge_audit.sh`不再报警

#### Issue #5: 在main分支
- [ ] ✅ 已解决（创建了feature/workflow-consistency-fixes分支）

#### Issue #6: 子阶段编号统一
- [ ] manifest.yml的substages使用编号（1.1, 1.2, ...）
- [ ] 与SPEC.yaml一致

#### Issue #7: 检查点编号示例
- [ ] SPEC.yaml的examples有清晰说明
- [ ] 或者移到单独文档说明

#### Issue #8: 契约测试
- [ ] `tests/contract/test_workflow_consistency.sh` 存在
- [ ] 可执行（chmod +x）
- [ ] 运行通过

#### Issue #9 & #10: Low priority
- [ ] （可选）暂不处理

### 文件完整性验证

#### Core Files Modified
- [ ] `.workflow/SPEC.yaml` - 4处修改
- [ ] `.workflow/manifest.yml` - 2处修改
- [ ] `.workflow/LOCK.json` - 自动更新
- [ ] `CLAUDE.md` - 版本文件数量更新
- [ ] 多个文件 - TODO/FIXME清理

#### New Files Created
- [ ] `.workflow/P1_DISCOVERY_workflow_fixes.md`
- [ ] `.workflow/IMPACT_ASSESSMENT_workflow_fixes.md`
- [ ] `.workflow/PLAN_workflow_fixes.md`
- [ ] `.workflow/ACCEPTANCE_CHECKLIST_workflow_fixes.md` (本文件)
- [ ] `tests/contract/test_workflow_consistency.sh`
- [ ] `.workflow/REVIEW_workflow_fixes.md` (Phase 4)
- [ ] `.workflow/ACCEPTANCE_REPORT_workflow_fixes.md` (Phase 6)

#### Backup Files
- [ ] `.workflow/backup_<timestamp>/SPEC.yaml`
- [ ] `.workflow/backup_<timestamp>/manifest.yml`

### Git提交验证

#### Commit History
- [ ] 每个Issue修复有独立commit
- [ ] Commit message遵守规范（fix/chore/test/docs）
- [ ] 没有`fixup`或`wip` commit

#### Branch Status
- [ ] 分支名: `feature/workflow-consistency-fixes`
- [ ] 基于main分支
- [ ] 没有merge冲突
- [ ] 可以快速合并（fast-forward或squash）

---

## 最终用户验收（Phase 6）

### 用户需要确认的事项

#### 1. 功能正确性
**验证方法**: 阅读ACCEPTANCE_REPORT_workflow_fixes.md

**问题**:
- SPEC.yaml、manifest.yml、CLAUDE.md是否一致了？
- 是否理解为什么版本文件是6个不是5个？
- TODO/FIXME清理是否合理？

**确认**: [ ] 功能符合预期

#### 2. 质量标准
**验证方法**: 查看Quality Gate输出

```bash
# 运行这些命令，都应该通过
bash scripts/static_checks.sh
bash scripts/pre_merge_audit.sh
bash scripts/check_version_consistency.sh
bash tests/contract/test_workflow_consistency.sh
```

**确认**: [ ] 所有检查通过

#### 3. 过程合规
**验证方法**: 查看Phase文档和todo list

**问题**:
- 是否严格遵守了7-Phase工作流？
- 是否使用了6个并行Agent？
- 是否整个过程没有弹窗询问权限？
- 是否有完整的工作记录？

**确认**: [ ] 过程符合Claude Enhancer规范

#### 4. 文档完整
**验证方法**: 检查.workflow/目录

```bash
ls -la .workflow/ | grep workflow_fixes
```

**应该看到**:
- P1_DISCOVERY_workflow_fixes.md
- IMPACT_ASSESSMENT_workflow_fixes.md
- PLAN_workflow_fixes.md
- ACCEPTANCE_CHECKLIST_workflow_fixes.md (本文件)
- REVIEW_workflow_fixes.md
- ACCEPTANCE_REPORT_workflow_fixes.md

**确认**: [ ] 文档完整

---

## 验收通过标准

**所有以下条件必须满足**:

### ✅ Blocker（必须全部通过）
- [ ] 10个Issue全部修复
- [ ] Quality Gate 1通过
- [ ] Quality Gate 2通过
- [ ] Contract tests通过
- [ ] Version consistency通过
- [ ] 版本号升级到8.6.1

### ✅ Critical（必须全部通过）
- [ ] 7-Phase工作流完整执行
- [ ] 使用了6个并行Agent
- [ ] Bypass Permissions生效
- [ ] 工作记录完整

### ⚠️ Major（允许≤2个不通过）
- [ ] TODO/FIXME ≤5个
- [ ] Commit message规范
- [ ] 文档可读性
- [ ] Code review无major issue

### 💡 Minor（允许不通过）
- [ ] Issue #9（SPEC.yaml精简）
- [ ] Issue #10（Phase超时配置）
- [ ] 性能优化

---

## 用户最终确认

**当所有Blocker和Critical都通过后，用户说以下任一句话即表示验收通过**:

- "没问题"
- "通过"
- "可以merge"
- "OK"
- "验收通过"

**用户说以下任一句话表示需要修改**:

- "有问题"
- "需要修改XXX"
- "重新做XXX"

---

**Checklist创建时间**: 2025-10-30 16:20
**Phase**: 1.5 Architecture Planning Complete
**下一步**: 等待用户确认"我理解了，开始Phase 2"
