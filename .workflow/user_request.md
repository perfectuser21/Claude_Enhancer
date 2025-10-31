# Phase 1/6/7 Skills + 并行执行系统 + Phase 7清理机制优化

**用户**: perfectuser21
**日期**: 2025-10-31
**分支**: feature/phase-skills-hooks-optimization

---

## 你需要得到什么（用人话说）

### 问题1：Phase 7清理机制有Bug
**现象**：你merge代码到main分支后，系统留下了"Phase7"标记文件，导致下次创建新分支时，系统以为还在Phase7，而不是从Phase1开始。

**你希望**：
- 每次merge完成后，系统自动清理Phase状态
- 创建新分支时，总是从Phase1开始
- 不用你手动删除文件

**就像**：租车归还后，工作人员会清理车内，下个客户拿到的是干净的车。你希望merge后系统自动"清理"，下个任务拿到的是干净状态。

### 问题2：并行执行没真正运行起来
**现象**：文档写了并行执行能加速3-5倍，但实际上AI还是一个一个串行执行任务，没变快。

**你希望**：
- Phase 3测试阶段，多个测试真正同时跑（不是一个跑完再跑下个）
- 能看到明显的速度提升（至少3倍快）
- 有日志证明确实并行执行了

**就像**：你买了多核CPU，但软件只用1个核心。你希望真正用上所有核心，把性能榨干。

### 问题3：AI在Phase 1/6/7不够规范
**现象**：AI在Phase 2-5有详细指导文档（知道该做什么），但Phase 1/6/7没有，容易偏离流程或漏步骤。

**你希望**：
- Phase 1：AI知道如何正确做需求分析、技术探索、架构规划
- Phase 6：AI知道如何验收，对照checklist逐项检查
- Phase 7：AI知道如何清理、如何正确创建PR（不是直接merge）
- 有完整的Hooks使用说明（20个hooks都是干什么的）

**就像**：给员工发了操作手册，Phase 2-5的手册很详细，但Phase 1/6/7的手册缺失，导致这几个阶段经常出错。你希望补全手册。

---

## 验收标准（怎么知道做好了）

### 1. Phase 7清理机制验收

**场景1**：merge代码后检查
- 你说"merge"
- AI执行merge
- 你检查main分支：`ls -la .phase/current`应该显示"文件不存在"
- ✅ 通过：文件不存在
- ❌ 失败：文件还在

**场景2**：创建新分支后检查
- 在main分支执行：`git checkout -b feature/test-cleanup`
- 你检查Phase状态：AI应该自动进入Phase1
- ✅ 通过：AI说"我们现在在Phase1"
- ❌ 失败：AI说"我们在Phase7"

**场景3**：三层清理都工作
- 第一层：comprehensive_cleanup.sh脚本清理
- 第二层：phase_completion_validator.sh在Phase7完成时清理
- 第三层：post-merge hook在merge后清理
- ✅ 通过：你随便测任何一层，都能清理
- ❌ 失败：某一层不工作

### 2. 并行执行验收

**场景1**：Phase 3测试加速
- 创建一个高复杂度任务（Impact Radius ≥50）
- 进入Phase 3测试阶段
- 记录测试开始时间和结束时间
- ✅ 通过：时间缩短至少3倍（例如：3小时→1小时）
- ❌ 失败：时间没明显变化

**场景2**：能看到并行执行证据
- Phase 3时查看日志：`ls .workflow/logs/*parallel*`
- ✅ 通过：有日志文件，内容显示多个agent同时执行
- ❌ 失败：无日志或日志显示串行执行

**场景3**：AI知道如何并行
- Phase 1结束时，AI说："我将使用6个agents并行执行Phase 2"
- Phase 2时，AI在单个消息中调用多个Task tool
- ✅ 通过：AI行为符合并行执行要求
- ❌ 失败：AI还是一个个串行执行

### 3. Skills和Hooks指导验收

**场景1**：Phase 1有详细指导
- 你给AI一个新需求
- AI进入Phase 1
- AI显示："参考 phase1-discovery-planning skill..."
- ✅ 通过：AI展示5个substages完整流程
- ❌ 失败：AI没有系统性指导，步骤混乱

**场景2**：Phase 6验收报告完整
- Phase 6时AI生成ACCEPTANCE_REPORT.md
- 报告包含：所有checklist项验证结果、证据、通过/失败统计
- ✅ 通过：报告详细，你能看懂每项是否通过
- ❌ 失败：报告简单或缺失

**场景3**：Phase 7有清理指导
- Phase 7时AI说："根据phase7-closure skill，我需要..."
- AI执行：清理、验证、创建PR（不是直接merge）
- ✅ 通过：AI按正确流程操作
- ❌ 失败：AI直接merge或漏步骤

**场景4**：Hooks文档完整
- 你打开docs/HOOKS_GUIDE.md
- 搜索任意一个hook名字（如：branch_helper.sh）
- 能找到：这个hook干什么、什么时候触发、如何配置
- ✅ 通过：20个hooks都有文档
- ❌ 失败：部分hooks无文档

**场景5**：Skills文档完整
- 你想创建一个新skill
- 打开docs/SKILLS_GUIDE.md
- 按照步骤操作能成功创建
- ✅ 通过：文档清晰可操作
- ❌ 失败：文档不清楚或缺步骤

### 4. 质量验收

**场景1**：所有脚本无语法错误
- 运行：`bash scripts/static_checks.sh`
- ✅ 通过：所有检查绿灯
- ❌ 失败：有红灯

**场景2**：版本号统一
- 检查6个文件：VERSION, settings.json, manifest.yml, package.json, CHANGELOG.md, SPEC.yaml
- ✅ 通过：6个文件版本号完全一致（如都是8.8.0）
- ❌ 失败：版本号不一致

**场景3**：验收项通过率
- 对照ACCEPTANCE_CHECKLIST.md逐项检查
- ✅ 通过：≥90%的项checked（至少116/129项）
- ❌ 失败：<90%

---

## 完成后你能做什么（最终效果）

1. **自动化清理**：你再也不用担心merge后的"脏"状态，系统自动清理

2. **真正的并行**：Phase 3测试从3小时缩短到1小时，真实可见的效率提升

3. **AI更规范**：
   - Phase 1：AI系统地做需求分析，不漏步骤
   - Phase 6：AI生成清晰的验收报告，你能看懂每项是否达标
   - Phase 7：AI正确清理和创建PR，不犯错

4. **完整文档**：
   - 20个hooks你都知道干什么用的
   - 想创建新skill时有完整指南可参考
   - 不再是"黑盒"

5. **质量保证**：
   - 所有代码通过质量检查
   - 版本号永远一致
   - 129项验收标准≥90%通过

**总结一句话**：系统更自动、更快、更规范、文档更完整，你用起来更放心。

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
