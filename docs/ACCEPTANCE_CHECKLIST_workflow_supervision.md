# Acceptance Checklist - Workflow Supervision Enforcement Fixes

**Version**: 8.5.1
**Task**: 修复3个P0 Critical Workflow Supervision Bugs
**Branch**: `bugfix/workflow-supervision-enforcement`
**Date**: 2025-10-29

---

## ✅ Phase 1: Discovery & Planning

### 1.1 Branch Check
- [x] 在main分支检查当前状态
- [x] 创建feature分支 `bugfix/workflow-supervision-enforcement`
- [x] 确认分支clean（无未提交更改）

### 1.2 Requirements Discussion
- [x] 理解用户需求（3个bugs）
- [x] 分析根本原因
- [x] 制定修复策略

### 1.3 Technical Discovery
- [x] 创建 `P1_DISCOVERY_workflow_supervision.md` (>300行)
- [x] 分析所有3个bugs的根因
- [x] 设计修复方案
- [x] 设计per-phase assessment enhancement

### 1.4 Impact Assessment
- [ ] 计算影响半径分数
- [ ] 确定推荐Agent数量
- [ ] 记录到 `.workflow/IMPACT_ASSESSMENT_workflow_supervision.md`

### 1.5 Architecture Planning
- [ ] 创建 `PLAN_workflow_supervision.md`
- [ ] 详细实现步骤
- [ ] Test strategy
- [ ] Rollback plan

---

## 🔧 Phase 2: Implementation

### 2.1 Bug #1: Impact Assessment Enforcer Fix
- [ ] 修改函数名 `is_phase2_completed` → `is_phase1_3_completed`
- [ ] 修改文件检查 `P2_DISCOVERY.md` → `P1_DISCOVERY.md`
- [ ] 修改Phase检查 `"P2"` → `"Phase1"`
- [ ] 添加debug logging
- [ ] 验证bash语法 (`bash -n`)

### 2.2 Bug #2: Phase Completion Validator Fix
- [ ] 重写case statement (P0-P5 → Phase1-Phase7)
- [ ] 实现Phase1检查逻辑
- [ ] 实现Phase2检查逻辑
- [ ] 实现Phase3检查逻辑
- [ ] 实现Phase4检查逻辑
- [ ] 实现Phase5检查逻辑
- [ ] 实现Phase6检查逻辑
- [ ] 实现Phase7检查逻辑
- [ ] 验证bash语法 (`bash -n`)

### 2.3 Bug #3: Agent Evidence Collector Simplification
- [ ] 移除task_namespace.sh依赖
- [ ] 实现简化版evidence recording
- [ ] 创建 `.workflow/agent_evidence/` 目录结构
- [ ] JSONL格式存储evidence
- [ ] 实现daily rotation
- [ ] 验证bash语法 (`bash -n`)

### 2.4 Enhancement: Per-Phase Impact Assessment
- [ ] 创建 `.claude/hooks/per_phase_impact_assessor.sh`
- [ ] 实现Phase detection逻辑
- [ ] 集成impact_radius_assessor.sh调用
- [ ] 输出到 `.workflow/impact_assessments/PhaseN_assessment.json`
- [ ] 验证bash语法 (`bash -n`)

### 2.5 Settings.json Update
- [ ] 添加per_phase_impact_assessor到PrePrompt hooks数组
- [ ] 验证JSON syntax (`jq . .claude/settings.json`)
- [ ] 确保enabled=true

### 2.6 Version Update
- [ ] 更新VERSION文件 → 8.5.1
- [ ] 更新.claude/settings.json version
- [ ] 更新.workflow/manifest.yml version
- [ ] 更新package.json version
- [ ] 更新CHANGELOG.md (添加8.5.1 section)
- [ ] 更新.workflow/SPEC.yaml version

---

## 🧪 Phase 3: Testing

### 3.1 Unit Tests - Impact Assessment Enforcer
- [ ] Test: Phase 1.3完成时触发
- [ ] Test: P1_DISCOVERY.md不存在时不触发
- [ ] Test: smart_agent_selector.sh缺失时报错
- [ ] Test: Impact Assessment成功后放行
- [ ] Test: Impact Assessment失败时阻止
- [ ] Test: 验证日志记录正确

### 3.2 Unit Tests - Phase Completion Validator
- [ ] Test: Phase1完成时调用validator
- [ ] Test: Phase2完成时调用validator
- [ ] Test: Phase3完成时调用validator
- [ ] Test: Phase4完成时调用validator
- [ ] Test: Phase5完成时调用validator
- [ ] Test: Phase6完成时调用validator
- [ ] Test: Phase7完成时调用validator
- [ ] Test: 验证失败时exit 1
- [ ] Test: 验证通过创建marker文件

### 3.3 Unit Tests - Agent Evidence Collector
- [ ] Test: Task tool触发记录
- [ ] Test: 非Task tool跳过
- [ ] Test: JSONL格式正确
- [ ] Test: Agent count统计正确
- [ ] Test: 无stdin时跳过
- [ ] Test: Daily rotation工作正常

### 3.4 Unit Tests - Per-Phase Assessor
- [ ] Test: Phase2开始前触发
- [ ] Test: Phase3开始前触发
- [ ] Test: Phase4开始前触发
- [ ] Test: 其他Phases不触发
- [ ] Test: JSON输出格式正确
- [ ] Test: Recommended agents字段存在

### 3.5 Integration Tests
- [ ] End-to-end workflow test (Phase1-7)
- [ ] Regression test: PR #57场景不再发生
- [ ] Performance test: 所有hooks <2秒
- [ ] Error handling test: 所有failure paths测试

### 3.6 Static Checks
- [ ] Shellcheck所有修改的hooks (0 warnings)
- [ ] bash -n所有scripts
- [ ] JSON syntax validation (jq)
- [ ] File permissions正确 (hooks executable)

---

## 📝 Phase 4: Review

### 4.1 Code Quality Review
- [ ] 所有函数<150行
- [ ] 复杂度<15
- [ ] 代码一致性检查
- [ ] Error handling完整

### 4.2 Documentation Review
- [ ] 所有修改有注释说明
- [ ] Phase命名约定documented
- [ ] Troubleshooting guide创建
- [ ] CLAUDE.md更新

### 4.3 Pre-merge Audit
- [ ] 运行 `bash scripts/pre_merge_audit.sh`
- [ ] 配置完整性检查通过
- [ ] 版本一致性检查通过 (6/6文件)
- [ ] 文档规范检查通过 (≤7个)

### 4.4 Review Document
- [ ] 创建 `.workflow/REVIEW.md` (>100行)
- [ ] 记录所有修改
- [ ] 记录所有测试结果
- [ ] Final verdict: APPROVED

---

## 🚀 Phase 5: Release

### 5.1 Documentation Updates
- [ ] CHANGELOG.md添加8.5.1条目
- [ ] README.md更新（如需要）
- [ ] CLAUDE.md更新anti-hollow gate文档

### 5.2 Git Tagging
- [ ] 创建tag v8.5.1
- [ ] Tag推送到GitHub
- [ ] Release notes生成

### 5.3 Monitoring Setup
- [ ] Verify hooks registered correctly
- [ ] Verify evidence collection working
- [ ] Verify per-phase assessment working

---

## ✅ Phase 6: Acceptance

### 6.1 Verification
- [ ] 所有checklist items完成 (≥90%)
- [ ] 所有tests通过
- [ ] CI所有checks通过
- [ ] 用户确认修复有效

### 6.2 Acceptance Report
- [ ] 创建 `.workflow/ACCEPTANCE_REPORT_workflow_supervision.md`
- [ ] 对照checklist验证
- [ ] 记录所有evidence
- [ ] 最终sign-off

---

## 🏁 Phase 7: Closure

### 7.1 Cleanup
- [ ] 运行 `bash scripts/comprehensive_cleanup.sh aggressive`
- [ ] .temp/目录清空
- [ ] 旧版本文件删除
- [ ] 临时报告文件删除

### 7.2 Final Verification
- [ ] 版本一致性 (6/6文件=8.5.1)
- [ ] 根目录文档≤7个
- [ ] Git工作区clean
- [ ] 所有commits使用规范格式

### 7.3 Pull Request
- [ ] Push分支到GitHub
- [ ] 创建PR with detailed description
- [ ] 等待CI通过
- [ ] 用户说"merge"后合并

---

## 📊 Quality Metrics

### Code Quality
- [ ] Shellcheck warnings: 0
- [ ] Function length: <150行
- [ ] Cyclomatic complexity: <15
- [ ] Test coverage: ≥80%

### Performance
- [ ] impact_assessment_enforcer.sh: <500ms
- [ ] phase_completion_validator.sh: <1s
- [ ] agent_evidence_collector.sh: <200ms
- [ ] per_phase_impact_assessor.sh: <500ms

### Documentation
- [ ] P1_DISCOVERY: >300行 ✅
- [ ] PLAN: >100行
- [ ] REVIEW: >100行
- [ ] ACCEPTANCE_REPORT: >50行

---

## 🎯 Success Criteria Summary

**Must Have (P0) - All 3 bugs fixed**:
1. ✅ Impact Assessment Enforcer检测P1_DISCOVERY.md
2. ✅ Phase Completion Validator使用Phase1-Phase7
3. ✅ Agent Evidence Collector不依赖task_namespace.sh

**Should Have (P1)**:
4. ✅ Per-phase Impact Assessment集成
5. ✅ 完整测试覆盖
6. ✅ Error handling不静默失败

**Quality Gates**:
7. ✅ CI所有checks通过
8. ✅ Version consistency (6/6 files)
9. ✅ Shellcheck 0 warnings
10. ✅ 所有Phases完成 (1-7)

---

**Total Items**: 126
**Current Progress**: 8/126 (6%) - Phase 1.3 completed
**Target Completion**: ≥113/126 (90%)

**Document Status**: ✅ Complete
**Next Action**: Phase 1.4 - Impact Assessment
