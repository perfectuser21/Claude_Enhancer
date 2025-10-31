# Acceptance Checklist - Parallel Strategy Documentation Restoration

**Feature**: 恢复并增强并行SubAgent策略文档，并建立防删除保护机制
**Branch**: feature/parallel-strategy-doc-restoration
**Phase**: Phase 1 (Planning)
**Date**: 2025-10-31
**Version**: 8.7.1

## 📋 定义"完成"的标准

本Checklist将在Phase 6 (Acceptance Testing)用于验证所有工作是否完整且符合质量要求。

---

## 1. 功能完整性验收标准

### 1.1 并行策略文档存在且完整

- [ ] **1.1.1** `docs/PARALLEL_SUBAGENT_STRATEGY.md`文件存在
  - **验证方法**: `test -f docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓ 文件存在" || echo "✗ 文件缺失"`
  - **期望结果**: 文件存在，返回✓

- [ ] **1.1.2** 文档大小≥2000行
  - **验证方法**: `wc -l < docs/PARALLEL_SUBAGENT_STRATEGY.md`
  - **期望结果**: 行数≥2000
  - **实际行数**: _________（Phase 6填写）

- [ ] **1.1.3** 文档包含8个必需section
  - **验证方法**: 逐个grep检查
  ```bash
  grep -q "理论基础：并行执行原理" docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓" || echo "✗"
  grep -q "当前系统架构 (v2.0.0)" docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓" || echo "✗"
  grep -q "Phase 2-7 并行策略详解" docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓" || echo "✗"
  grep -q "实战使用指南" docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓" || echo "✗"
  grep -q "性能与优化" docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓" || echo "✗"
  grep -q "Claude Code的批量调用" docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓" || echo "✗"
  grep -q "Impact Assessment" docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓" || echo "✗"
  grep -q "STAGES.yml" docs/PARALLEL_SUBAGENT_STRATEGY.md && echo "✓" || echo "✗"
  ```
  - **期望结果**: 8个section全部✓

- [ ] **1.1.4** 文档包含新旧内容融合
  - **旧理论内容**: 5种并行策略（Queen-Worker, Git Worktree等）
  - **新实现内容**: v2.0.0 STAGES.yml配置驱动
  - **验证方法**: 抽查关键词存在
  - **期望结果**: 两种内容均包含

- [ ] **1.1.5** 文档包含26个真实任务benchmark数据
  - **验证方法**: `grep -c "加速比" docs/PARALLEL_SUBAGENT_STRATEGY.md`
  - **期望结果**: 至少20个benchmark示例

---

### 1.2 保护机制完整实现

#### 1.2.1 Immutable Kernel保护

- [ ] **1.2.1.1** 文档已加入`.workflow/SPEC.yaml` kernel_files列表
  - **验证方法**: `grep "PARALLEL_SUBAGENT_STRATEGY.md" .workflow/SPEC.yaml`
  - **期望结果**: 找到该行

- [ ] **1.2.1.2** SPEC.yaml中kernel_files总数=10
  - **验证方法**: `yq '.immutable_kernel.kernel_files | length' .workflow/SPEC.yaml`
  - **期望结果**: 10

- [ ] **1.2.1.3** `.workflow/LOCK.json`已更新
  - **验证方法**: `bash tools/verify-core-structure.sh`
  - **期望结果**: 输出 `"ok":true`

#### 1.2.2 CI Sentinel实现

- [ ] **1.2.2.1** CI workflow文件存在
  - **验证方法**: `test -f .github/workflows/critical-docs-sentinel.yml`
  - **期望结果**: 文件存在

- [ ] **1.2.2.2** CI包含2个jobs
  - **验证方法**: 查看YAML文件
  - **期望结果**: `check-critical-docs` + `verify-parallel-strategy-content`

- [ ] **1.2.2.3** CI检查9个关键文档
  - **验证方法**: 查看CRITICAL_DOCS数组长度
  - **期望结果**: 9个文档（含PARALLEL_SUBAGENT_STRATEGY.md）

- [ ] **1.2.2.4** CI验证文档最小行数（2000行）
  - **验证方法**: 查看min_lines变量
  - **期望结果**: MIN_LINES=2000

- [ ] **1.2.2.5** CI验证8个必需section
  - **验证方法**: 查看REQUIRED_SECTIONS数组
  - **期望结果**: 8个section名称

- [ ] **1.2.2.6** CI能检测删除操作
  - **验证方法**: 查看"Check for Deleted Files in Commit" step
  - **期望结果**: 使用git diff检测deleted files

#### 1.2.3 防删除保护测试

- [ ] **1.2.3.1** 模拟删除关键文档时CI失败
  - **测试步骤**:
    1. 创建测试分支: `git checkout -b test/delete-protection`
    2. 删除文档: `git rm docs/PARALLEL_SUBAGENT_STRATEGY.md`
    3. 提交: `git commit -m "test: delete critical doc"`
    4. 推送: `git push origin test/delete-protection`
    5. 创建PR并等待CI
  - **期望结果**: CI失败，显示"CRITICAL: Attempted to delete protected document"
  - **清理**: 删除测试分支
  - **实际结果**: _________（Phase 6验证）

- [ ] **1.2.3.2** 模拟简化文档时CI失败
  - **测试步骤**:
    1. 创建测试分支: `git checkout -b test/simplify-protection`
    2. 用500行内容替换文档: `head -500 docs/PARALLEL_SUBAGENT_STRATEGY.md > temp && mv temp docs/PARALLEL_SUBAGENT_STRATEGY.md`
    3. 提交推送
    4. 创建PR并等待CI
  - **期望结果**: CI失败，显示"Document too small"
  - **清理**: 删除测试分支
  - **实际结果**: _________（Phase 6验证）

---

### 1.3 集成验收标准

#### 1.3.1 CLAUDE.md引用

- [ ] **1.3.1.1** Phase 2章节包含并行策略引用
  - **验证方法**: `grep -A5 "Phase 2" CLAUDE.md | grep "PARALLEL_SUBAGENT_STRATEGY.md"`
  - **期望结果**: 找到引用

- [ ] **1.3.1.2** Phase 3章节包含并行策略引用
  - **验证方法**: `grep -A5 "Phase 3" CLAUDE.md | grep "PARALLEL_SUBAGENT_STRATEGY.md"`
  - **期望结果**: 找到引用

- [ ] **1.3.1.3** Phase 4章节包含并行策略引用
  - **验证方法**: `grep -A5 "Phase 4" CLAUDE.md | grep "PARALLEL_SUBAGENT_STRATEGY.md"`
  - **期望结果**: 找到引用

- [ ] **1.3.1.4** Phase 7章节包含并行策略引用
  - **验证方法**: `grep -A5 "Phase 7" CLAUDE.md | grep "PARALLEL_SUBAGENT_STRATEGY.md"`
  - **期望结果**: 找到引用

- [ ] **1.3.1.5** 所有引用包含完整说明（并行潜力+加速比+典型并行组）
  - **验证方法**: 人工检查每个引用的详细程度
  - **期望结果**: 不是简单链接，而是包含具体信息

#### 1.3.2 Git History可追溯

- [ ] **1.3.2.1** 能找到原始删除的commit
  - **验证方法**: `git log --all --oneline -- docs/PARALLEL_EXECUTION_SOLUTION.md | head -1`
  - **期望结果**: 显示commit be0f0161 (2025-09-19)

- [ ] **1.3.2.2** 能通过git show恢复旧内容
  - **验证方法**: `git show be0f0161^:docs/PARALLEL_EXECUTION_SOLUTION.md | wc -l`
  - **期望结果**: 257行

- [ ] **1.3.2.3** 新文档commit包含完整说明
  - **验证方法**: `git log --oneline docs/PARALLEL_SUBAGENT_STRATEGY.md | head -1`
  - **期望内容**: 包含"restore"或"parallel strategy"关键词

---

## 2. Bug修复验收标准

### 2.1 自动Phase重置功能

- [ ] **2.1.1** `force_branch_check.sh`包含Phase清除逻辑
  - **验证方法**: `grep -A10 "CRITICAL FIX" .claude/hooks/force_branch_check.sh`
  - **期望结果**: 找到清除.phase/current的代码

- [ ] **2.1.2** 在main分支时能检测到旧Phase状态
  - **测试步骤**:
    1. 创建假Phase状态: `echo "Phase7" > .phase/current`
    2. 切换到main分支: `git checkout main`
    3. 触发PrePrompt hook（发送消息给Claude）
  - **期望结果**: Hook显示"检测到旧Phase状态（Phase7），已自动清除"
  - **实际结果**: _________（Phase 6验证）

- [ ] **2.1.3** Phase清除后显示清晰提示消息
  - **验证方法**: 查看hook输出
  - **期望内容**:
    - ✓ 显示被清除的Phase名称
    - ✓ 说明这是merge后的正常行为
    - ✓ 提示新任务从Phase 1开始
    - ✓ 提示创建feature分支

- [ ] **2.1.4** Phase清除后`.phase/current`文件被删除
  - **验证方法**: 手动测试后检查文件
  - **期望结果**: `test ! -f .phase/current && echo "✓ 文件已删除" || echo "✗ 文件仍存在"`

### 2.2 防止Workflow绕过

- [ ] **2.2.1** Merge后回到main分支时，自动阻止直接编码
  - **测试场景**: 用户merge PR后，立即在main分支发起新任务
  - **期望行为**: PrePrompt hook显示警告，强制创建新分支
  - **实际结果**: _________（Phase 6验证）

- [ ] **2.2.2** 在main分支尝试Write/Edit时被阻止
  - **测试步骤**:
    1. 确保在main分支: `git checkout main`
    2. 尝试创建文件: `echo "test" > test.md`
    3. 检查hook响应
  - **期望结果**: 没有hook阻止（Write/Edit由PrePrompt警告处理）
  - **说明**: PrePrompt是warn模式，不硬阻止，但AI应遵守警告

---

## 3. 文档质量验收标准

### 3.1 Phase 1文档完整性

- [ ] **3.1.1** `P1_DISCOVERY_parallel-strategy.md`存在且≥300行
  - **验证方法**: `wc -l < .workflow/P1_DISCOVERY_parallel-strategy.md`
  - **期望结果**: ≥300行
  - **实际行数**: 328行 ✓

- [ ] **3.1.2** P1_DISCOVERY包含11个必需section
  - **必需section**:
    1. Technical Investigation（技术调查）
    2. Impact Assessment（影响评估）
    3. Root Cause Analysis（根因分析）
    4. Solution Exploration（方案探索）
    5. Technical Feasibility（技术可行性）
    6. Risk Assessment（风险评估）
    7. Performance Impact（性能影响）
    8. Dependencies（依赖关系）
    9. Timeline（时间线）
    10. Success Criteria（成功标准）
    11. Next Actions（下一步行动）
  - **验证方法**: 人工检查或grep
  - **期望结果**: 11/11存在

- [ ] **3.1.3** `ACCEPTANCE_CHECKLIST_parallel-strategy.md`存在
  - **验证方法**: `test -f .workflow/ACCEPTANCE_CHECKLIST_parallel-strategy.md`
  - **期望结果**: 文件存在（本文件）

- [ ] **3.1.4** Acceptance Checklist包含≥40个验收项
  - **验证方法**: `grep -c "^\- \[ \]" .workflow/ACCEPTANCE_CHECKLIST_parallel-strategy.md`
  - **期望结果**: ≥40项

- [ ] **3.1.5** `PLAN_parallel-strategy.md`存在且≥500行
  - **验证方法**: `wc -l < .workflow/PLAN_parallel-strategy.md`
  - **期望结果**: ≥500行
  - **实际行数**: _________（待完成）

### 3.2 文档语言和格式

- [ ] **3.2.1** 所有文档使用正确的Markdown格式
  - **验证方法**: 运行markdown linter（如有）
  - **期望结果**: 无格式错误

- [ ] **3.2.2** 代码示例使用正确的语法高亮
  - **验证方法**: 人工检查代码块标记
  - **期望结果**: 所有代码块有语言标记（```bash, ```yaml等）

- [ ] **3.2.3** 所有内部链接有效
  - **验证方法**: 检查文档间引用
  - **期望结果**: 引用的文件都存在

---

## 4. 版本和配置验收标准

### 4.1 版本一致性

- [ ] **4.1.1** 6个版本文件完全一致
  - **验证方法**: `bash scripts/check_version_consistency.sh`
  - **期望结果**: 输出"All version files are consistent"
  - **6个文件**:
    1. VERSION
    2. .claude/settings.json
    3. .workflow/manifest.yml
    4. package.json
    5. CHANGELOG.md
    6. .workflow/SPEC.yaml

- [ ] **4.1.2** 版本号正确升级（从8.7.0 → 8.7.1）
  - **验证方法**: `cat VERSION`
  - **期望结果**: 8.7.1

### 4.2 CHANGELOG更新

- [ ] **4.2.1** CHANGELOG.md包含本次功能的条目
  - **验证方法**: `grep "8.7.1" CHANGELOG.md`
  - **期望内容**:
    - 标题: `## [8.7.1] - 2025-10-31`
    - 说明并行策略文档恢复
    - 说明防删除保护机制
    - 说明Phase自动重置bug修复

- [ ] **4.2.2** CHANGELOG条目格式正确
  - **期望格式**:
    ```markdown
    ## [8.7.1] - 2025-10-31

    ### Added
    - 恢复并增强并行SubAgent策略文档（2753行）
    - 三层防删除保护（Immutable Kernel + CI Sentinel + CLAUDE.md引用）

    ### Fixed
    - Merge后回到main分支时自动清除旧Phase状态
    - 防止workflow绕过导致直接在main分支编码
    ```

---

## 5. 性能和稳定性验收标准

### 5.1 Hook性能

- [ ] **5.1.1** `force_branch_check.sh`执行时间<500ms
  - **验证方法**: `time bash .claude/hooks/force_branch_check.sh`
  - **期望结果**: real time <0.5s
  - **实际时间**: _________ms（Phase 6测量）

### 5.2 CI性能

- [ ] **5.2.1** `critical-docs-sentinel.yml` workflow完成时间<5min
  - **验证方法**: 查看GitHub Actions运行记录
  - **期望结果**: Total time <5min
  - **实际时间**: _________（Phase 6测量）

- [ ] **5.2.2** CI检查job成功率100%（无flaky tests）
  - **验证方法**: 运行CI 5次，全部通过
  - **期望结果**: 5/5成功
  - **实际结果**: _________（Phase 6验证）

---

## 6. 用户体验验收标准

### 6.1 错误消息清晰度

- [ ] **6.1.1** Phase清除消息易于理解（非技术用户也能看懂）
  - **验证方法**: 请非技术人员阅读消息
  - **期望反馈**: 能理解发生了什么、为什么、下一步该做什么

- [ ] **6.1.2** CI失败消息包含明确的修复指导
  - **验证方法**: 查看CI失败输出
  - **期望内容**:
    - ✓ 说明失败原因
    - ✓ 说明为什么这是critical
    - ✓ 提供修复步骤（numbered list）
    - ✓ 提供RFC流程说明（如果是intentional deletion）

### 6.2 分支命名一致性

- [ ] **6.2.1** 功能分支名称符合约定
  - **验证方法**: `git rev-parse --abbrev-ref HEAD`
  - **期望格式**: `feature/parallel-strategy-doc-restoration`
  - **实际名称**: _________（Phase 6检查）

---

## 7. 回滚和恢复验收标准

### 7.1 回滚能力

- [ ] **7.1.1** 能通过git revert回滚所有更改
  - **测试方法（在测试分支）**:
    1. 记录当前commit: `git rev-parse HEAD`
    2. Revert所有更改: `git revert <commit1> <commit2> ...`
    3. 验证系统恢复到原状态
  - **期望结果**: 系统能正常运行，无残留
  - **实际结果**: _________（Phase 6验证，非破坏性测试）

- [ ] **7.1.2** README/CLAUDE.md包含问题排查指南
  - **验证方法**: 搜索"troubleshooting"或"问题排查"
  - **期望内容**: 至少包含3个常见问题的解决方案

---

## 8. 最终验收清单

### 8.1 所有自动化检查通过

- [ ] **8.1.1** `bash scripts/static_checks.sh` 通过 ✅
- [ ] **8.1.2** `bash scripts/pre_merge_audit.sh` 通过 ✅
- [ ] **8.1.3** `bash tools/verify-core-structure.sh` 通过 ✅
- [ ] **8.1.4** `bash scripts/check_version_consistency.sh` 通过 ✅
- [ ] **8.1.5** GitHub CI全部通过 ✅

### 8.2 手动验收完成

- [ ] **8.2.1** AI已逐项检查本Checklist（Phase 6）
- [ ] **8.2.2** AI生成`ACCEPTANCE_REPORT_parallel-strategy.md`
- [ ] **8.2.3** 用户审查并确认"没问题"

### 8.3 准备Merge

- [ ] **8.3.1** Git工作区干净（无未提交更改）
- [ ] **8.3.2** 所有commits消息符合规范
- [ ] **8.3.3** PR已创建并等待review
- [ ] **8.3.4** 用户说"merge"

---

## 📊 验收统计

**总验收项**: 74项

**完成情况**（Phase 6填写）:
- ✅ 已通过: ___/74
- ⏳ 进行中: ___/74
- ❌ 未通过: ___/74
- 🔄 需修复: ___/74

**完成率**: ___%

**是否达到验收标准**: ☐ 是 / ☐ 否

**用户最终确认**: ☐ 通过 / ☐ 需修改

**备注**: _________________________________________

---

## 📝 使用说明

**在Phase 1 (当前阶段)**:
- 定义验收标准，但不执行验收

**在Phase 2-5**:
- 实现功能时参考本Checklist，确保覆盖所有要求

**在Phase 6 (Acceptance Testing)**:
- AI逐项验证本Checklist
- 执行所有测试步骤
- 填写"实际结果"
- 生成ACCEPTANCE_REPORT

**在Phase 7 (Final Cleanup)**:
- 确保本Checklist≥90%完成
- 处理未完成项或记录为已知限制

---

*Generated in Phase 1 - Planning Stage*
*This checklist defines the "Definition of Done" for the parallel strategy restoration feature*
