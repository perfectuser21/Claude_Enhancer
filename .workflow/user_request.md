# User Request - Per-Phase Impact Assessment Architecture

**Date**: 2025-10-29
**Requested by**: User
**Branch**: feature/per-phase-impact-assessment
**Impact Radius**: 90/100 (very-high-risk)

---

## 📋 Request

将Impact Assessment系统从全局评估改造为per-phase架构，使每个Phase能够根据自己的特性独立评估任务风险和推荐agent数量。

---

## 🎯 Goals

### 核心目标
1. **Per-Phase评估**: 每个Phase（Phase2/3/4）独立评估任务复杂度
2. **Phase-Specific配置**: STAGES.yml包含每个Phase的风险模式和agent策略
3. **智能推荐**: Phase 2推荐2-4个agents，Phase 3推荐3-8个agents，Phase 4推荐2-5个agents
4. **向后兼容**: 保持现有全局评估模式可用

### 问题陈述

**当前问题**：
- Impact Assessment是全局的（评估整个任务）
- 不区分Phase特性（Phase 2实现 vs Phase 3测试 vs Phase 4审查）
- 推荐的agent数量固定（如：6个agents）
- 没有利用STAGES.yml已定义的per-phase并行组

**用户反馈**：
> "每个阶段应该根据需求不是有个评估吗，然后不同阶段应该多少个subagents并行工作。我不担心浪费token，我需要的是高效和准确性。"

---

## ✅ Acceptance Criteria

### 功能性验收
- [ ] Impact Assessment支持`--phase`参数（per-phase评估）
- [ ] STAGES.yml包含per-phase `impact_assessment`配置
  - [ ] Phase2配置（实现阶段风险模式）
  - [ ] Phase3配置（测试阶段风险模式）
  - [ ] Phase4配置（审查阶段风险模式）
- [ ] parallel_task_generator.sh使用per-phase评估
- [ ] Phase 2评估推荐agents数量符合Phase 2特性（2-4个）
- [ ] Phase 3评估推荐agents数量符合Phase 3特性（3-8个）
- [ ] Phase 4评估推荐agents数量符合Phase 4特性（2-5个）
- [ ] 向后兼容：`bash impact_radius_assessor.sh "task"`仍工作

### 性能验收
- [ ] Impact Assessment执行时间≤50ms（保持现有性能）
- [ ] parallel_task_generator执行时间≤1s
- [ ] STAGES.yml解析时间≤100ms

### 质量验收
- [ ] 通过所有静态检查（bash -n, shellcheck）
- [ ] 单元测试覆盖率≥70%
- [ ] 集成测试通过（Phase 2/3/4场景各1个）
- [ ] 文档完整（REVIEW.md >100行）
- [ ] 版本一致性100%（6个文件：VERSION, settings.json, manifest.yml, package.json, CHANGELOG.md, SPEC.yaml）

### 集成验收
- [ ] 不破坏现有7-Phase workflow
- [ ] 不破坏现有subagent调度系统
- [ ] Git hooks正常工作（pre-commit, pre-push）
- [ ] CI/CD通过（CE Unified Gates）

---

## 📊 Scope

### 修改文件（3个）
1. **`.workflow/STAGES.yml`**
   - 增加`impact_assessment`配置到Phase2/3/4
   - 定义per-phase风险模式（risk_patterns）
   - 定义per-phase agent策略（agent_strategy）

2. **`.claude/scripts/impact_radius_assessor.sh`**
   - 增加`--phase`参数支持
   - 读取STAGES.yml per-phase配置
   - 使用phase-specific patterns评估
   - 保持向后兼容（无`--phase`参数时使用全局模式）

3. **`scripts/subagent/parallel_task_generator.sh`**
   - 改造为per-phase评估调用
   - 读取STAGES.yml并行组配置
   - 生成phase-appropriate Task调用

### 新增文件（测试/文档）
1. **`test/unit/test_per_phase_impact_assessment.sh`**
   - 单元测试：Phase 2/3/4评估结果验证

2. **`test/integration/test_parallel_generator_per_phase.sh`**
   - 集成测试：完整workflow验证

3. **`.workflow/P1_DISCOVERY.md`**
   - 技术探索文档（>300行）

4. **`.workflow/PLAN.md`**
   - 详细设计文档（>1000行）

5. **`.workflow/REVIEW.md`**
   - 代码审查报告（Phase 4产出，>100行）

---

## 🎯 Success Metrics

### 短期指标（Phase 6验收）
- Acceptance Checklist ≥90%完成
- 所有测试通过（单元+集成）
- 性能满足预算（≤50ms）
- 文档完整（REVIEW.md >100行）

### 中期指标（1周后）
- 实际使用per-phase评估≥5次
- 无regression bug报告
- 性能稳定（无下降）

### 长期指标（1个月后）
- Per-phase评估准确率≥86%（保持现有水平）
- 用户反馈正面
- 无版本冲突/回滚

---

## ⚠️ Risk Assessment

**Impact Assessment自评**（2025-10-29）：
```json
{
  "impact_radius": 90,
  "strategy": "very-high-risk",
  "min_agents": 8,
  "risk_level": "HIGH",
  "complexity_level": "HIGH",
  "impact_level": "WIDE"
}
```

**风险等级**: 超高风险（架构变更 + 多组件 + 系统级影响）

**需要保障**:
- ✅ 完整7-Phase workflow执行
- ✅ 2个质量门禁（Phase 3 + Phase 4）
- ✅ 8个agents验证（如可用）
- ✅ 5层防护机制（Workflow + Hooks + Anti-Hollow + Lockdown + CI/CD）

---

## 📚 Related Documents

- **可行性评估**: `.temp/PER_PHASE_IMPACT_ASSESSMENT_FEASIBILITY.md`
- **概念澄清**: `.temp/CLARIFICATION_AGENTS_VS_STEPS.md`
- **系统总结**: `.workflow/WORKFLOW_COMPLETION_SUMMARY.md`
- **代码审查**: `.workflow/REVIEW_subagent_optimization.md`

---

## 🚀 Implementation Plan

### Phase 1: Discovery & Planning（当前阶段）
- [x] 1.1 Branch Check - 创建feature/per-phase-impact-assessment ✅
- [x] 1.2 Requirements Discussion - 本文档 ✅
- [ ] 1.3 Technical Discovery - P1_DISCOVERY.md（>300行）
- [x] 1.4 Impact Assessment - 90分，very-high-risk ✅
- [ ] 1.5 Architecture Planning - PLAN.md（>1000行）

### Phase 2: Implementation
- [ ] 修改STAGES.yml（增加per-phase配置）
- [ ] 修改impact_radius_assessor.sh（增加--phase参数）
- [ ] 修改parallel_task_generator.sh（per-phase调用）
- [ ] 编写单元测试
- [ ] 编写集成测试

### Phase 3: Testing（🔒 质量门禁1）
- [ ] 静态检查（bash -n, shellcheck）
- [ ] 单元测试（≥70%覆盖率）
- [ ] 集成测试（3个场景）
- [ ] 性能测试（≤50ms）

### Phase 4: Review（🔒 质量门禁2）
- [ ] 代码逻辑审查
- [ ] 版本一致性验证（6个文件）
- [ ] 文档完整性（REVIEW.md >100行）
- [ ] Pre-merge audit（12项检查）

### Phase 5: Release
- [ ] 更新CHANGELOG.md
- [ ] 更新README.md（如有必要）
- [ ] 更新VERSION（如有必要）

### Phase 6: Acceptance
- [ ] AI生成验收报告
- [ ] 用户确认"没问题"

### Phase 7: Closure
- [ ] 全面清理（bash scripts/comprehensive_cleanup.sh aggressive）
- [ ] 版本一致性最终验证
- [ ] 等待用户说"merge"

---

**User Request完成时间**: 2025-10-29
**下一步**: Phase 1.3 - 技术探索（P1_DISCOVERY.md）
