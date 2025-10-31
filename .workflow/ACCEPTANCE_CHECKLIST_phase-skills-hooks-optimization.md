# Acceptance Checklist: Phase 1/6/7 Skills + Parallel Execution + Phase 7 Cleanup Fix

**Version**: 8.8.0
**Created**: 2025-10-31
**Feature**: 三合一系统优化（清理机制+并行执行+Skills指导）

---

## 功能需求验收（Functional Requirements）

### 需求1: Phase 7清理机制修复

- [ ] **F1.1**: main分支merge后，`.phase/current`文件不存在
  - 测试: merge PR到main后检查`test ! -f .phase/current`

- [ ] **F1.2**: main分支merge后，`.workflow/current`文件不存在
  - 测试: merge PR到main后检查`test ! -f .workflow/current`

- [ ] **F1.3**: main分支merge后，创建`.phase/completed`标记
  - 测试: merge PR后检查`test -f .phase/completed`

- [ ] **F1.4**: 新创建的feature分支继承干净状态（无Phase文件）
  - 测试: `git checkout -b test-branch && test ! -f .phase/current`

- [ ] **F1.5**: comprehensive_cleanup.sh包含Phase状态清理逻辑
  - 测试: `grep "phase/current" scripts/comprehensive_cleanup.sh`

- [ ] **F1.6**: phase_completion_validator.sh在Phase7完成时清理状态
  - 测试: 阅读代码确认逻辑存在

- [ ] **F1.7**: post-merge hook清理Phase状态（如果存在）
  - 测试: `test -f .git/hooks/post-merge && grep "phase/current" .git/hooks/post-merge`

### 需求2: 并行执行系统优化

- [ ] **F2.1**: executor.sh正确集成parallel_executor.sh
  - 测试: `grep -A10 "execute_parallel" .workflow/executor.sh`

- [ ] **F2.2**: is_parallel_enabled()函数读取manifest.yml配置
  - 测试: `source .workflow/executor.sh && is_parallel_enabled Phase3` 返回true

- [ ] **F2.3**: Phase 2并行执行被触发（高影响半径任务）
  - 测试: 创建Radius≥50的任务，检查`.workflow/logs/`中有parallel执行日志

- [ ] **F2.4**: Phase 3并行执行被触发
  - 测试: Phase 3时检查并行执行日志

- [ ] **F2.5**: Phase 4并行执行被触发（review组）
  - 测试: Phase 4时检查并行执行日志

- [ ] **F2.6**: Phase 7部分并行执行（cleanup组）
  - 测试: Phase 7时检查并行执行日志

- [ ] **F2.7**: 冲突检测基于实际修改文件，而非声明的conflict_paths
  - 测试: 阅读conflict_detector.sh代码，确认使用`git diff --name-only`

- [ ] **F2.8**: 冲突检测失败时自动降级为串行
  - 测试: 模拟冲突，验证降级日志

- [ ] **F2.9**: Phase 1 skill包含并行执行指导
  - 测试: `grep "并行执行" .claude/skills/phase1-discovery-planning/SKILL.md`

- [ ] **F2.10**: AI知道需要在单个消息中批量调用Task tool
  - 测试: Phase 1 skill中有明确说明和示例

### 需求3: Phase 1/6/7 Skills创建

- [ ] **F3.1**: phase1-discovery-planning skill文件存在
  - 测试: `test -f .claude/skills/phase1-discovery-planning/SKILL.md`

- [ ] **F3.2**: phase1 skill包含5个substages指导
  - 测试: `grep -E "Substage 1\.[1-5]" .claude/skills/phase1-discovery-planning/SKILL.md | wc -l` 返回5

- [ ] **F3.3**: phase1 skill包含Impact Assessment计算公式
  - 测试: `grep "Radius = " .claude/skills/phase1-discovery-planning/SKILL.md`

- [ ] **F3.4**: phase1 skill包含User confirmation要求
  - 测试: `grep "User confirmation" .claude/skills/phase1-discovery-planning/SKILL.md`

- [ ] **F3.5**: phase6-acceptance skill文件存在
  - 测试: `test -f .claude/skills/phase6-acceptance/SKILL.md`

- [ ] **F3.6**: phase6 skill包含checklist验证流程
  - 测试: `grep "Validate Each Item" .claude/skills/phase6-acceptance/SKILL.md`

- [ ] **F3.7**: phase6 skill包含ACCEPTANCE_REPORT.md模板
  - 测试: `grep "ACCEPTANCE_REPORT" .claude/skills/phase6-acceptance/SKILL.md`

- [ ] **F3.8**: phase7-closure skill文件存在
  - 测试: `test -f .claude/skills/phase7-closure/SKILL.md`

- [ ] **F3.9**: phase7 skill包含comprehensive_cleanup.sh使用指导
  - 测试: `grep "comprehensive_cleanup" .claude/skills/phase7-closure/SKILL.md`

- [ ] **F3.10**: phase7 skill包含20个hooks详解
  - 测试: `grep -c "### Hook:" .claude/skills/phase7-closure/SKILL.md` ≥20

- [ ] **F3.11**: phase7 skill包含Skills开发指南
  - 测试: `grep "Skills.*开发" .claude/skills/phase7-closure/SKILL.md`

- [ ] **F3.12**: phase7 skill包含PR创建正确流程（不是直接merge）
  - 测试: `grep "gh pr create" .claude/skills/phase7-closure/SKILL.md`

- [ ] **F3.13**: 3个skills在settings.json中注册
  - 测试: `jq '.skills | length' .claude/settings.json` 增加了3个

- [ ] **F3.14**: phase1 skill trigger配置正确（entering_phase1）
  - 测试: `jq '.skills[] | select(.name=="phase1-execution-guide") | .trigger' .claude/settings.json`

- [ ] **F3.15**: phase6 skill trigger配置正确（entering_phase6）
  - 测试: 同上

- [ ] **F3.16**: phase7 skill trigger配置正确（entering_phase7）
  - 测试: 同上

- [ ] **F3.17**: skills priority设置为P0（最高优先级）
  - 测试: `jq '.skills[] | select(.name | contains("phase")) | .priority' .claude/settings.json` 都是"P0"

### 需求4: Hooks和Skills开发指南

- [ ] **F4.1**: docs/HOOKS_GUIDE.md文件存在
  - 测试: `test -f docs/HOOKS_GUIDE.md`

- [ ] **F4.2**: HOOKS_GUIDE包含20个hooks文档
  - 测试: `grep -c "^### Hook:" docs/HOOKS_GUIDE.md` =20

- [ ] **F4.3**: HOOKS_GUIDE包含trigger时机说明
  - 测试: `grep "触发时机\|Trigger" docs/HOOKS_GUIDE.md`

- [ ] **F4.4**: HOOKS_GUIDE包含hook开发步骤
  - 测试: `grep "创建.*hook" docs/HOOKS_GUIDE.md`

- [ ] **F4.5**: HOOKS_GUIDE包含调试方法
  - 测试: `grep "调试\|Debug" docs/HOOKS_GUIDE.md`

- [ ] **F4.6**: docs/SKILLS_GUIDE.md文件存在
  - 测试: `test -f docs/SKILLS_GUIDE.md`

- [ ] **F4.7**: SKILLS_GUIDE包含trigger机制详解
  - 测试: `grep "Trigger机制" docs/SKILLS_GUIDE.md`

- [ ] **F4.8**: SKILLS_GUIDE包含action类型说明（reminder/script/blocking）
  - 测试: `grep -E "reminder|script|blocking" docs/SKILLS_GUIDE.md`

- [ ] **F4.9**: SKILLS_GUIDE包含创建skill步骤
  - 测试: `grep "创建.*skill" docs/SKILLS_GUIDE.md`

- [ ] **F4.10**: SKILLS_GUIDE包含Skills vs Hooks对比
  - 测试: `grep "Skills.*Hooks.*对比\|vs" docs/SKILLS_GUIDE.md`

---

## 质量需求验收（Quality Requirements）

### 代码质量

- [ ] **Q1**: 所有新增bash脚本通过shellcheck检查
  - 测试: `shellcheck scripts/comprehensive_cleanup.sh .git/hooks/post-merge`

- [ ] **Q1.2**: 所有新增bash脚本语法正确
  - 测试: `bash -n <script>`

- [ ] **Q1.3**: 所有脚本函数<150行
  - 测试: `bash scripts/check_function_length.sh`

- [ ] **Q1.4**: 所有脚本复杂度<15
  - 测试: 手动review或使用complexity工具

### 文档质量

- [ ] **Q2.1**: 3个skill文档总计1300-1500行
  - 测试: `wc -l .claude/skills/phase*/SKILL.md`

- [ ] **Q2.2**: HOOKS_GUIDE.md ≥500行
  - 测试: `wc -l docs/HOOKS_GUIDE.md`

- [ ] **Q2.3**: SKILLS_GUIDE.md ≥300行
  - 测试: `wc -l docs/SKILLS_GUIDE.md`

- [ ] **Q2.4**: 所有文档中的代码示例可运行
  - 测试: 手动复制运行关键示例

- [ ] **Q2.5**: 所有文档链接有效
  - 测试: `bash scripts/check_doc_links.sh`

- [ ] **Q2.6**: 文档排版清晰，无格式错误
  - 测试: 手动阅读检查

### 测试覆盖

- [ ] **Q3.1**: Phase 7清理机制有单元测试
  - 测试: `test -f tests/unit/test_phase7_cleanup.sh`

- [ ] **Q3.2**: 并行执行集成有单元测试
  - 测试: `test -f tests/unit/test_parallel_executor.sh`

- [ ] **Q3.3**: Skills触发机制有集成测试
  - 测试: `test -f tests/integration/test_skills_trigger.sh`

- [ ] **Q3.4**: 完整工作流有端到端测试
  - 测试: `test -f tests/e2e/test_full_workflow.sh`

- [ ] **Q3.5**: 所有测试通过
  - 测试: `npm test && bash tests/run_all.sh`

### 性能要求

- [ ] **Q4.1**: Phase 3并行执行加速比≥3x
  - 测试: 对比并行vs串行执行时间

- [ ] **Q4.2**: Phase 2并行执行加速比≥1.5x
  - 测试: 对比并行vs串行执行时间

- [ ] **Q4.3**: Skills加载时间<500ms
  - 测试: `time bash -c "source .claude/skills/phase1-discovery-planning/SKILL.md"`

- [ ] **Q4.4**: Phase 7清理脚本执行时间<30秒
  - 测试: `time bash scripts/comprehensive_cleanup.sh aggressive`

- [ ] **Q4.5**: post-merge hook执行时间<2秒
  - 测试: `time bash .git/hooks/post-merge`

### 安全要求

- [ ] **Q5.1**: 清理脚本不误删重要文件
  - 测试: 代码review确认只删除`.phase/current`和`.workflow/current`

- [ ] **Q5.2**: post-merge hook只在main分支触发
  - 测试: 阅读代码确认分支检查逻辑

- [ ] **Q5.3**: 并行执行使用mutex锁避免竞态条件
  - 测试: `grep "mutex\|lock" .workflow/lib/parallel_executor.sh`

- [ ] **Q5.4**: 无硬编码敏感信息
  - 测试: `bash scripts/scan_secrets.sh`

---

## 集成需求验收（Integration Requirements）

### 与现有系统集成

- [ ] **I1.1**: comprehensive_cleanup.sh现有功能不受影响
  - 测试: 运行cleanup后验证.temp/清理、旧版本清理等

- [ ] **I1.2**: phase_completion_validator.sh现有验证逻辑不受影响
  - 测试: Phase转换验证仍然正常工作

- [ ] **I1.3**: executor.sh串行执行路径保留（fallback）
  - 测试: 禁用并行执行，验证串行仍可用

- [ ] **I1.4**: 新skills不与现有skills冲突
  - 测试: 检查settings.json中skills数组无重复name

- [ ] **I1.5**: parallel_executor.sh与STAGES.yml配置匹配
  - 测试: 验证executor读取的配置与STAGES.yml一致

### 向后兼容

- [ ] **I2.1**: 旧的feature分支（有Phase状态）仍可正常工作
  - 测试: 切换到旧分支，验证Phase不报错

- [ ] **I2.2**: 不依赖并行执行的任务仍可串行执行
  - 测试: 小任务（Radius<30）不启用并行

- [ ] **I2.3**: Phase 2-5 autonomous skill仍然有效
  - 测试: Phase 2-5时检查是否显示autonomous提醒

### 版本一致性

- [ ] **I3.1**: VERSION文件更新为8.8.0
  - 测试: `cat VERSION` = "8.8.0"

- [ ] **I3.2**: settings.json version更新为8.8.0
  - 测试: `jq '.version' .claude/settings.json` = "8.8.0"

- [ ] **I3.3**: manifest.yml version更新为8.8.0
  - 测试: `yq eval '.version' .workflow/manifest.yml` = "8.8.0"

- [ ] **I3.4**: package.json version更新为8.8.0
  - 测试: `jq '.version' package.json` = "8.8.0"

- [ ] **I3.5**: CHANGELOG.md version更新为8.8.0
  - 测试: `grep "8.8.0" CHANGELOG.md`

- [ ] **I3.6**: SPEC.yaml version更新为8.8.0
  - 测试: `yq eval '.version' .workflow/SPEC.yaml` = "8.8.0"

- [ ] **I3.7**: 版本一致性脚本通过
  - 测试: `bash scripts/check_version_consistency.sh` 返回0

---

## 用户验收标准（User Acceptance）

### 用户可见效果

- [ ] **U1.1**: 用户merge PR到main后，main分支干净（无Phase遗留）
  - 验证方式: 用户执行merge后检查main分支

- [ ] **U1.2**: 用户创建新feature分支时，从Phase1开始（无错误状态）
  - 验证方式: 用户创建新分支，AI自动进入Phase1

- [ ] **U1.3**: 用户在Phase 3看到明显的速度提升（≥3x）
  - 验证方式: 用户对比Phase 3执行时间

- [ ] **U1.4**: 用户在Phase 1看到并行策略推荐（Impact Assessment）
  - 验证方式: Phase 1结束时显示"Recommended: 6 agents"

- [ ] **U1.5**: 用户在Phase 1/6/7看到详细的执行指导提醒
  - 验证方式: Phase转换时显示skill reminder

- [ ] **U1.6**: 用户能通过docs/HOOKS_GUIDE.md快速查找hook用法
  - 验证方式: 用户翻阅文档，5分钟内找到目标hook

- [ ] **U1.7**: 用户能通过docs/SKILLS_GUIDE.md理解如何创建新skill
  - 验证方式: 用户按照指南创建一个简单skill

### 用户操作便利性

- [ ] **U2.1**: 用户说"merge"后，AI不再直接在feature分支执行merge（正确创建PR）
  - 验证方式: 检查AI是否执行`gh pr create`而非`git merge`

- [ ] **U2.2**: 用户在Phase 7看到完整清理报告
  - 验证方式: Phase 7输出包含清理项目和统计

- [ ] **U2.3**: 用户在Phase 6看到清晰的验收报告
  - 验证方式: ACCEPTANCE_REPORT.md格式清晰，pass/fail明确

- [ ] **U2.4**: 用户无需手动干预，AI自动应用并行策略
  - 验证方式: 高影响半径任务自动并行执行

### 错误处理

- [ ] **U3.1**: 并行执行失败时，AI自动降级为串行并继续
  - 验证方式: 模拟并行失败，检查降级日志

- [ ] **U3.2**: Phase 7清理失败时，AI显示清晰错误信息
  - 验证方式: 模拟清理错误，检查错误提示

- [ ] **U3.3**: Skills加载失败时，AI fallback到默认行为
  - 验证方式: 删除skill文件，验证Phase仍可执行

---

## 回归测试（Regression Tests）

### 确保现有功能不受影响

- [ ] **R1.1**: 7-Phase工作流完整性不受影响
  - 测试: 执行完整Phase 1-7流程

- [ ] **R1.2**: Phase 2-5 autonomous模式正常工作
  - 测试: Phase 2-5不询问用户技术决策

- [ ] **R1.3**: Phase 1 completion确认机制正常工作
  - 测试: Phase 1完成后等待用户确认

- [ ] **R1.4**: 版本强制升级机制正常工作
  - 测试: 不升级版本无法commit

- [ ] **R1.5**: PR creation guard正常工作
  - 测试: Phase非7时无法创建PR

- [ ] **R1.6**: Branch protection hooks正常工作
  - 测试: 无法直接push到main

- [ ] **R1.7**: Evidence collection system正常工作
  - 测试: Phase 3-6 evidence正常收集

- [ ] **R1.8**: Impact Assessment自动触发
  - 测试: Phase 1.4自动计算影响半径

- [ ] **R1.9**: Checklist generation自动触发
  - 测试: Phase 1.3后自动生成ACCEPTANCE_CHECKLIST

- [ ] **R1.10**: Pre-merge audit正常工作
  - 测试: Phase 4执行pre_merge_audit.sh

---

## 文档更新验收（Documentation Updates）

- [ ] **D1**: CLAUDE.md更新Phase 7清理说明
  - 测试: `grep "Phase.*清理" CLAUDE.md`

- [ ] **D2**: CHANGELOG.md记录8.8.0所有改动
  - 测试: `grep -A20 "8.8.0" CHANGELOG.md`

- [ ] **D3**: README.md版本号更新为8.8.0
  - 测试: `grep "8.8.0" README.md`

- [ ] **D4**: PARALLEL_SUBAGENT_STRATEGY.md添加"使用方法"章节
  - 测试: `grep "使用方法\|How to Use" docs/PARALLEL_SUBAGENT_STRATEGY.md`

---

## 验收总结

**总计检查项**: 129项

**分类统计**:
- 功能需求: 54项
- 质量需求: 22项
- 集成需求: 15项
- 用户验收: 14项
- 回归测试: 10项
- 文档更新: 4项

**通过标准**: ≥90%项通过（116/129项）

**Critical项**: 20项（标记🔴）
- 所有Critical项必须100%通过才能验收

**验收流程**:
1. Phase 3: 运行自动化测试（Q开头）
2. Phase 4: 手动验证功能（F开头）
3. Phase 6: 用户确认用户验收项（U开头）
4. 最终: 生成ACCEPTANCE_REPORT.md
