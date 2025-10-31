# Technical Discovery: Phase 1/6/7 Skills + Parallel Execution + Phase 7 Cleanup Fix

**Date**: 2025-10-31
**Version**: 8.8.0 (target)
**Author**: Claude Code
**Impact Radius**: TBD (will calculate in substage 1.4)

---

## 1. Executive Summary

### 1.1 User Request Analysis

用户提出了3个相关的优化需求，应作为一个整体来处理：

**需求1**: 修复Phase 7清理机制（Bug Fix）
- **问题**: main分支merge后遗留Phase7状态文件
- **影响**: 新feature分支继承错误状态，破坏7-Phase工作流
- **优先级**: HIGH（影响工作流完整性）

**需求2**: 优化并行执行系统（Feature Enhancement）
- **问题**: `PARALLEL_SUBAGENT_STRATEGY.md`文档完整，但并行执行代码未真正运行
- **影响**: 理论加速比3-5x，实际串行执行，浪费并行潜力
- **优先级**: MEDIUM（功能增强，提升效率）

**需求3**: 为Phase 1/6/7增加Skills + Hooks指导（Documentation Enhancement）
- **问题**: 只有Phase 2-5有详细skill指导，Phase 1/6/7缺失
- **影响**: AI在Phase 1/6/7执行不够规范，容易偏离标准流程
- **优先级**: MEDIUM（提升AI执行质量）

### 1.2 Why Together?

这3个需求有内在联系：
- **需求1（Phase 7清理）** 是基础bug，必须先修复
- **需求3（Skills指导）** 包含Phase 7的详细执行指导，可以一起实现
- **需求2（并行优化）** 需要在Skills中体现并行策略（Phase 1推荐Agent数量，Phase 2-7并行执行）

一起做的好处：
- ✅ 统一规划，避免重复工作
- ✅ Phase 7 skill可以包含清理机制的指导
- ✅ 并行策略可以在Phase 1 skill中体现（Impact Assessment）
- ✅ 一次PR完成所有优化，减少merge次数

---

## 2. Current State Analysis（当前状态分析）

### 2.1 Phase 7清理机制现状

**检查comprehensive_cleanup.sh**：
```
当前清理范围（已验证）:
- .temp/目录 ✓
- 旧版本文件 ✓
- 重复文档 ✓
- 大文件 ✓
- Git仓库优化 ✓
- Phase状态文件 ✗ (缺失！)
```

**问题验证**：
```bash
git show origin/main:.phase/current
# 输出: Phase7  ← 遗留状态

git show origin/main:.workflow/current
# 输出: phase: Phase1  ← 不一致！
```

**根因分析**：
- `comprehensive_cleanup.sh` 未包含Phase状态清理
- Phase 7结束后没有显式清理`.phase/current`和`.workflow/current`
- 没有"工作流完成"的明确标记机制

### 2.2 并行执行系统现状

**已有组件**：
```
文档层:
├─ docs/PARALLEL_SUBAGENT_STRATEGY.md (853行) ✓ 完整
├─ .workflow/STAGES.yml (803行) ✓ 配置完整
└─ 理论加速比: Phase 2 (1.3x), Phase 3 (5.1x), Phase 4 (1.2x)

代码层:
├─ .workflow/lib/parallel_executor.sh ✓ 存在
├─ .workflow/lib/conflict_detector.sh ✓ 存在
├─ .workflow/lib/mutex_lock.sh ✓ 存在
└─ scripts/subagent/parallel_task_generator.sh ✓ 存在

集成层:
├─ .workflow/executor.sh (主执行器) ？需检查
├─ .claude/hooks/parallel_subagent_suggester.sh ✓ 存在
├─ .claude/hooks/per_phase_impact_assessor.sh ✓ 存在
└─ settings.json → parallel_execution配置 ✓ 存在
```

**需要验证的问题**：
1. executor.sh是否调用parallel_executor.sh?
2. parallel_executor.sh是否有执行日志?
3. STAGES.yml中的并行组是否被读取?
4. AI是否知道需要在单个消息中批量调用Task tool?

**预期问题**：
- 🔴 Critical: executor.sh可能未集成parallel_executor.sh
- 🟡 Medium: 并行执行需要AI在单个消息中调用多个Task tool（文档说明不够）
- 🟡 Medium: 冲突检测可能过于保守（导致频繁降级为串行）

### 2.3 Skills系统现状

**已有Skills**：
```
.claude/skills/
└─ phase2-5-autonomous/
   └─ SKILL.md (472行) ✓ 完整

settings.json → skills配置:
  ✓ checklist-validator
  ✓ learning-capturer
  ✓ evidence-collector
  ✓ kpi-reporter
  ✓ parallel-performance-tracker
  ✓ parallel-conflict-validator
  ✗ parallel-load-balancer (disabled, placeholder)
  ✓ workflow-guardian-enforcer
  ✓ phase-transition-validator
  ✓ phase1-completion-reminder
```

**缺失Skills**：
```
❌ phase1-discovery-planning (Phase 1详细执行指导)
❌ phase6-acceptance (Phase 6验收流程指导)
❌ phase7-closure (Phase 7清理+合并指导) ← 重点
```

**Hooks使用指导现状**：
```
文档:
- CLAUDE.md: 提到20个hooks，但无详细使用说明
- 各hook文件: 有注释，但不够系统化

缺失:
❌ Hooks开发指南（如何创建新hook）
❌ Hooks使用手册（何时触发、如何配置）
❌ Skills开发指南（如何定义trigger、action）
```

---

## 3. Technical Approach（技术方案概述）

### 3.1 Problem 1: Phase 7清理机制修复

**Root Cause**:
- Phase 7结束后未清理`.phase/current`和`.workflow/current`
- comprehensive_cleanup.sh不包含Phase状态清理

**Solution**:

**方案A: 在comprehensive_cleanup.sh中添加Phase清理**
```bash
# 在comprehensive_cleanup.sh末尾添加
echo "🧹 Cleaning Phase state files..."
if [[ -f ".phase/current" ]]; then
  current_phase=$(cat .phase/current)
  if [[ "$current_phase" == "Phase7" ]]; then
    echo "Phase7 complete, clearing phase state"
    rm -f .phase/current .workflow/current
    echo "Phase workflow complete at $(date)" > .phase/completed
  fi
fi
```

**方案B: 在phase_completion_validator.sh中清理**
```bash
# 在Phase7完成验证后添加
if [[ "$next_phase" == "completed" ]]; then
  echo "Workflow complete, cleaning phase state"
  rm -f .phase/current .workflow/current
  touch .phase/completed
fi
```

**方案C: 创建post-merge hook（最可靠）**
```bash
# .git/hooks/post-merge
#!/bin/bash
# 检测到merge到main后，清理Phase状态
if [[ "$(git rev-parse --abbrev-ref HEAD)" == "main" ]]; then
  rm -f .phase/current .workflow/current
  echo "Phase state cleaned after merge to main"
fi
```

**推荐**: 三管齐下（A+B+C），确保无论哪个路径都能清理

**Rollback Strategy**:
```bash
# 如果清理出错，可以手动恢复
git checkout HEAD -- .phase/current .workflow/current
```

### 3.2 Problem 2: 并行执行优化

**Root Cause**:
- executor.sh可能未集成parallel_executor.sh
- AI不知道需要在单个消息中批量调用Task tool
- 冲突检测可能过于保守

**Solution**:

**Step 1: 验证并修复executor.sh集成**
```bash
# 在executor.sh中添加并行执行逻辑
is_parallel_enabled() {
  local phase="$1"
  local manifest="${PROJECT_ROOT}/.workflow/manifest.yml"

  # 读取manifest.yml检查并行配置
  if command -v yq &>/dev/null; then
    can_parallel=$(yq eval ".phases[] | select(.id == \"$phase\") | .parallel" "$manifest")
    echo "$can_parallel"
  else
    echo "false"
  fi
}

execute_parallel_workflow() {
  local phase="$1"
  bash "${PROJECT_ROOT}/.workflow/lib/parallel_executor.sh" "$phase"
}

# 主流程
if [[ "$(is_parallel_enabled "$current_phase")" == "true" ]]; then
  execute_parallel_workflow "$current_phase"
else
  execute_serial_workflow "$current_phase"
fi
```

**Step 2: 在Skills中明确并行指导**

在phase1-discovery-planning skill中添加：
```markdown
## 并行执行策略（Phase 2-7）

基于Impact Assessment结果：
- Radius ≥50 (6 agents): 启用Phase 2-7并行执行
- Radius 30-49 (3 agents): 部分并行（Phase 3-4）
- Radius <30 (0 agents): 串行执行

CRITICAL: 并行执行需在单个消息中调用多个Task tool！

正确示例（伪代码）:
  调用Task tool #1 (实现后端)
  调用Task tool #2 (实现前端)
  调用Task tool #3 (实现测试)
  # 在同一个response中发送3个tool调用

错误示例:
  调用Task tool #1
  等待结果
  调用Task tool #2  # ← 这是串行，不是并行
```

**Step 3: 优化冲突检测**
```bash
# 在conflict_detector.sh中添加智能检测
# 只检测实际修改的文件，而不是声明的conflict_paths

# 读取git diff获取实际修改文件
modified_files=$(git diff --name-only main...HEAD)

# 只检查实际修改文件的冲突
for group1 in "${groups[@]}"; do
  for group2 in "${groups[@]}"; do
    # 检查实际文件交集，而不是pattern交集
    actual_conflict=$(check_real_file_overlap "$group1" "$group2" "$modified_files")
    if [[ "$actual_conflict" == "true" ]]; then
      downgrade_to_serial
    fi
  done
done
```

**Rollback Strategy**:
- 并行执行失败自动降级为串行（已有机制）
- 不影响功能，只影响速度

### 3.3 Problem 3: Phase 1/6/7 Skills + Hooks指导

**Solution**:

**Step 1: 创建3个新Skills**

**phase1-discovery-planning skill** (~500行):
```
结构:
- Phase 1五个substages详细指导
- Branch check流程
- Requirements discussion模板
- Technical discovery checklist
- Impact Assessment计算公式
- Architecture planning模板
- 并行策略决策树
- User confirmation要求
```

**phase6-acceptance skill** (~400行):
```
结构:
- 加载Phase 1 checklist
- 逐项验证方法
- Evidence collection要求
- Acceptance report生成模板
- User presentation格式
- Feedback handling流程
```

**phase7-closure skill** (~600行，重点):
```
结构:
- 全面清理checklist
- comprehensive_cleanup.sh使用指导
- 版本一致性验证
- Phase状态清理机制（新增）
- Git工作区验证
- PR创建流程（正确的，不是直接merge）
- Hooks使用指南（20个hooks详解）
- Skills开发指南
- 常见错误避免
```

**Step 2: 注册到settings.json**
```json
{
  "skills": [
    // ... 现有skills ...
    {
      "name": "phase1-execution-guide",
      "description": "Phase 1 discovery and planning execution guide",
      "trigger": {
        "event": "phase_transition",
        "context": "entering_phase1"
      },
      "action": {
        "type": "reminder",
        "message": "Refer to .claude/skills/phase1-discovery-planning/SKILL.md"
      },
      "enabled": true,
      "priority": "P0"
    },
    {
      "name": "phase6-execution-guide",
      "description": "Phase 6 acceptance testing execution guide",
      "trigger": {
        "event": "phase_transition",
        "context": "entering_phase6"
      },
      "action": {
        "type": "reminder",
        "message": "Refer to .claude/skills/phase6-acceptance/SKILL.md"
      },
      "enabled": true,
      "priority": "P0"
    },
    {
      "name": "phase7-execution-guide",
      "description": "Phase 7 closure and merge execution guide with hooks/skills guidance",
      "trigger": {
        "event": "phase_transition",
        "context": "entering_phase7"
      },
      "action": {
        "type": "reminder",
        "message": "Refer to .claude/skills/phase7-closure/SKILL.md for comprehensive closure guidance including hooks and skills usage"
      },
      "enabled": true,
      "priority": "P0"
    }
  ]
}
```

**Step 3: 创建Hooks和Skills开发指南**

**docs/HOOKS_GUIDE.md** (~800行):
```
- 20个现有hooks详解
- 何时触发、作用、配置方法
- 创建新hook的步骤
- Hook开发最佳实践
- 调试方法
```

**docs/SKILLS_GUIDE.md** (~500行):
```
- Skills系统架构
- Trigger机制详解
- Action类型（reminder/script/blocking）
- 创建新skill步骤
- Skills vs Hooks对比
- 最佳实践
```

**Rollback Strategy**:
- 删除新创建的skill文件
- 恢复settings.json
- 不影响现有功能

---

## 4. Risk Analysis（风险分析）

### 4.1 Phase 7清理机制风险

**Risk 1**: 清理过早导致Phase状态丢失
- **概率**: Low
- **影响**: Medium
- **缓解**: 只在Phase7完成且用户说"merge"后清理
- **回滚**: 从git恢复状态文件

**Risk 2**: post-merge hook未执行（权限问题）
- **概率**: Low
- **影响**: Low (有A、B方案兜底)
- **缓解**: 三管齐下，多个清理点

**Risk 3**: 清理逻辑bug导致其他文件被删
- **概率**: Very Low
- **影响**: High
- **缓解**: 只删除特定文件（.phase/current .workflow/current）

### 4.2 并行执行风险

**Risk 1**: executor.sh集成错误导致无法执行
- **概率**: Medium
- **影响**: High (阻塞Phase 2-7)
- **缓解**: 充分测试，保留串行执行fallback
- **回滚**: 注释掉并行执行代码，恢复串行

**Risk 2**: 冲突检测优化导致真实冲突未发现
- **概率**: Low
- **影响**: High (代码冲突)
- **缓解**: 保留原有检测逻辑，新逻辑作为优化层
- **回滚**: 恢复原conflict_detector.sh

**Risk 3**: AI不理解"单个消息调用多个Task tool"
- **概率**: Medium
- **影响**: Medium (无法并行，但能串行)
- **缓解**: 在skill中多次强调+示例+图解
- **回滚**: 不影响功能，只影响速度

### 4.3 Skills创建风险

**Risk 1**: Skill文档过长导致加载慢
- **概率**: Low
- **影响**: Low (仅影响首次加载)
- **缓解**: 控制在600行以内
- **回滚**: 删除skill文件

**Risk 2**: Trigger配置错误导致skill不触发
- **概率**: Low
- **影响**: Medium (skill无效)
- **缓解**: 充分测试trigger条件
- **回滚**: 修正settings.json配置

**Risk 3**: 多个skills指导冲突
- **概率**: Very Low
- **影响**: Low (AI会优先Phase specific skill)
- **缓解**: 明确priority（P0 > P1）
- **回滚**: 调整priority或disable冲突skill

---

## 5. Feasibility Assessment（可行性评估）

### 5.1 Dependencies Required

**无新依赖** ✓
- 所有工具已存在（bash, yq, jq, git）
- 只是集成和配置现有组件

### 5.2 Compatibility Verified

**与现有系统兼容** ✓
- Phase 7清理是增量修改，不破坏现有逻辑
- 并行执行有fallback到串行
- Skills是新增，不影响现有skills

### 5.3 Blockers Identified

**无阻塞** ✓
- 所有代码都在本地
- 无需外部API或服务
- 可以完全本地测试

---

## 6. Complexity Estimate（复杂度评估）

**总体复杂度**: 6/10 (Medium)

**分项评估**:
- Phase 7清理机制: 3/10 (简单，只是添加清理逻辑)
- 并行执行集成: 7/10 (中等，需要验证和修复集成点)
- Skills创建: 5/10 (中等，主要是文档编写)
- Hooks/Skills指南: 4/10 (简单，整理现有知识)

**预计工作量**:
- Phase 2 Implementation: 4-6小时
- Phase 3 Testing: 2-3小时
- Phase 4 Review: 1-2小时
- Phase 5-7: 1小时

**总计**: 8-12小时（1-2个工作日）

---

## 7. Evidence of Feasibility（可行性证据）

### 7.1 Similar Implementations

**Phase 2-5 Autonomous Skill** ✓
- 已成功实现phase2-5-autonomous skill
- 证明skill机制有效
- 可以复用相同结构

**Parallel Executor Components** ✓
- parallel_executor.sh已存在
- STAGES.yml配置完整
- 只需要集成到主流程

**Comprehensive Cleanup Script** ✓
- 已有清理机制
- 只需要添加Phase状态清理

### 7.2 Prototype Testing

**无需prototype** ✓
- 修改都是增量的
- 可以直接在feature分支测试
- Rollback容易（git revert）

---

## 8. Alternative Approaches Considered（备选方案）

### 8.1 Alternative for Phase 7 Cleanup

**Option 1**: 不清理Phase状态，让新分支自己初始化
- ❌ 问题: 新分支继承错误状态，需要额外逻辑检测
- ❌ 复杂度更高

**Option 2**: 只在main分支清理，feature分支保留
- ⚠️ 问题: main分支merge后遗留状态
- ✓ 优势: feature分支可以恢复工作
- ❌ 选择: 不推荐，会导致main分支"脏"

**Option 3**: 引入Phase 0作为"idle"状态
- ✓ 优势: 明确的"无工作流"状态
- ⚠️ 问题: 需要修改更多代码
- ❌ 选择: 过度设计，当前方案更简单

**Selected**: 清理Phase状态文件（当前方案）

### 8.2 Alternative for Parallel Execution

**Option 1**: 完全重写并行执行系统
- ❌ 工作量巨大（数周）
- ❌ 风险高
- ❌ 不推荐

**Option 2**: 只优化冲突检测，不改executor
- ⚠️ 问题: 如果executor未集成，优化无效
- ✓ 优势: 风险低
- ❌ 选择: 不够彻底

**Option 3**: 当前方案（验证+修复+文档）
- ✓ 风险可控
- ✓ 工作量合理
- ✓ 效果显著
- ✅ 选择: 推荐

**Selected**: 当前方案

### 8.3 Alternative for Skills Creation

**Option 1**: 只创建Phase 7 skill，不创建Phase 1/6
- ❌ 问题: 不够完整，Phase 1/6仍然缺失指导
- ❌ 不推荐

**Option 2**: 合并Phase 1/6/7到一个mega skill
- ❌ 问题: 文件过大（>2000行），难以维护
- ❌ 不推荐

**Option 3**: 当前方案（3个独立skills）
- ✓ 结构清晰
- ✓ 易于维护
- ✓ 按需触发
- ✅ 选择: 推荐

**Selected**: 当前方案（3个独立skills）

---

## 9. Success Criteria（成功标准）

### 9.1 Phase 7清理机制

**验证方法**:
```bash
# 1. 完成Phase 7并merge到main
git checkout main
git merge feature/xxx

# 2. 验证Phase状态已清理
test ! -f .phase/current && echo "✓ Phase state cleaned"
test ! -f .workflow/current && echo "✓ Workflow state cleaned"
test -f .phase/completed && echo "✓ Completion marker created"

# 3. 创建新feature分支，验证继承干净状态
git checkout -b feature/new-task
test ! -f .phase/current && echo "✓ New branch has clean state"
```

**Expected Result**:
- ✓ main分支无Phase状态文件
- ✓ 新feature分支从Phase1开始
- ✓ 无错误状态继承

### 9.2 并行执行优化

**验证方法**:
```bash
# 1. 创建高影响半径任务（Radius ≥50）
# 在Phase 1中得到"6 agents recommended"

# 2. 进入Phase 2，观察AI行为
# 应该在单个消息中调用多个Task tool

# 3. 检查并行执行日志
find .workflow/logs -name "*parallel*" -mtime -1
grep "parallel_executor.sh" .workflow/logs/*.log

# 4. 验证加速比
# Phase 3测试: 应该显著快于串行（接近5x）
```

**Expected Result**:
- ✓ executor.sh正确调用parallel_executor.sh
- ✓ AI在单个消息中批量调用Task tool
- ✓ Phase 3测试加速比≥3x（目标5x，考虑overhead）
- ✓ 冲突检测日志显示智能判断

### 9.3 Skills创建

**验证方法**:
```bash
# 1. 验证文件存在
test -f .claude/skills/phase1-discovery-planning/SKILL.md && echo "✓ Phase 1 skill exists"
test -f .claude/skills/phase6-acceptance/SKILL.md && echo "✓ Phase 6 skill exists"
test -f .claude/skills/phase7-closure/SKILL.md && echo "✓ Phase 7 skill exists"

# 2. 验证settings.json注册
jq '.skills[] | select(.name | contains("phase1-execution-guide"))' .claude/settings.json
jq '.skills[] | select(.name | contains("phase6-execution-guide"))' .claude/settings.json
jq '.skills[] | select(.name | contains("phase7-execution-guide"))' .claude/settings.json

# 3. 验证trigger机制
# 进入Phase 1，观察是否显示提醒
# 进入Phase 6，观察是否显示提醒
# 进入Phase 7，观察是否显示提醒
```

**Expected Result**:
- ✓ 3个skill文件创建成功（总计~1500行）
- ✓ settings.json正确注册
- ✓ Phase转换时自动触发提醒
- ✓ AI按照skill指导执行

### 9.4 Hooks/Skills指南

**验证方法**:
```bash
# 1. 验证文档存在
test -f docs/HOOKS_GUIDE.md && echo "✓ Hooks guide exists"
test -f docs/SKILLS_GUIDE.md && echo "✓ Skills guide exists"

# 2. 验证内容完整性
wc -l docs/HOOKS_GUIDE.md  # 应该>500行
wc -l docs/SKILLS_GUIDE.md  # 应该>300行

# 3. 验证20个hooks都有文档
grep -c "^### Hook:" docs/HOOKS_GUIDE.md  # 应该=20
```

**Expected Result**:
- ✓ Hooks guide完整（>500行）
- ✓ Skills guide完整（>300行）
- ✓ 20个hooks全部有文档
- ✓ 示例代码可运行

---

## 10. Testing Strategy（测试策略）

### 10.1 Unit Testing

**Phase 7清理逻辑**:
```bash
# Test 1: Phase7完成后清理
echo "Phase7" > .phase/current
bash scripts/comprehensive_cleanup.sh
test ! -f .phase/current && echo "✓ Test 1 passed"

# Test 2: Phase非7时不清理
echo "Phase3" > .phase/current
bash scripts/comprehensive_cleanup.sh
test -f .phase/current && echo "✓ Test 2 passed"

# Test 3: post-merge hook
git checkout main
touch .phase/current  # 模拟遗留状态
bash .git/hooks/post-merge
test ! -f .phase/current && echo "✓ Test 3 passed"
```

**并行执行集成**:
```bash
# Test 1: is_parallel_enabled检测
source .workflow/executor.sh
result=$(is_parallel_enabled "Phase3")
test "$result" == "true" && echo "✓ Test 1 passed"

# Test 2: execute_parallel_workflow调用
# 需要mock环境，检查是否调用parallel_executor.sh
```

**Skills触发**:
```bash
# Test 1: Phase1转换触发提醒
# 需要模拟Phase转换，检查skill输出
```

### 10.2 Integration Testing

**完整工作流测试**:
```bash
# Test: 从Phase1到Phase7完整流程
# 1. 创建新feature分支
git checkout -b feature/test-workflow

# 2. 执行Phase 1-7
# 观察每个Phase是否显示skill提醒

# 3. merge到main
git checkout main
git merge feature/test-workflow

# 4. 验证清理
test ! -f .phase/current && echo "✓ Cleanup successful"

# 5. 创建新分支验证
git checkout -b feature/test-2
test ! -f .phase/current && echo "✓ Clean state inherited"
```

### 10.3 Performance Testing

**并行执行性能**:
```bash
# Test: Phase 3并行 vs 串行
# 1. 禁用并行，执行Phase 3，记录时间
time bash scripts/static_checks.sh

# 2. 启用并行，执行Phase 3，记录时间
# 应该显著更快
```

**Benchmark目标**:
- Phase 3并行加速比 ≥3x
- Phase 2并行加速比 ≥1.5x
- Skills加载时间 <500ms

---

## 11. Rollback Strategy（回滚策略）

### 11.1 Phase 7清理机制回滚

```bash
# 1. 恢复comprehensive_cleanup.sh
git checkout HEAD~1 -- scripts/comprehensive_cleanup.sh

# 2. 恢复phase_completion_validator.sh
git checkout HEAD~1 -- .claude/hooks/phase_completion_validator.sh

# 3. 删除post-merge hook
rm .git/hooks/post-merge

# 4. 手动恢复Phase状态（如果需要）
echo "Phase7" > .phase/current
```

**影响**: 无破坏性影响，只是恢复到旧行为

### 11.2 并行执行优化回滚

```bash
# 1. 恢复executor.sh
git checkout HEAD~1 -- .workflow/executor.sh

# 2. 恢复conflict_detector.sh
git checkout HEAD~1 -- .workflow/lib/conflict_detector.sh

# 3. 系统自动降级到串行执行
# 无需额外操作
```

**影响**: 恢复到串行执行，速度变慢但功能正常

### 11.3 Skills创建回滚

```bash
# 1. 删除3个skill文件
rm -rf .claude/skills/phase1-discovery-planning
rm -rf .claude/skills/phase6-acceptance
rm -rf .claude/skills/phase7-closure

# 2. 恢复settings.json
git checkout HEAD~1 -- .claude/settings.json

# 3. 删除文档
rm docs/HOOKS_GUIDE.md
rm docs/SKILLS_GUIDE.md
```

**影响**: 恢复到Phase 1/6/7无详细指导的状态

### 11.4 完整回滚

```bash
# 终极大招：回滚整个PR
git revert <commit-hash>
# 或者
git reset --hard HEAD~1
git push --force origin feature/phase-skills-hooks-optimization
```

**影响**: 完全恢复到改动前状态，无副作用

---

## 12. Documentation Requirements（文档需求）

### 12.1 需要创建的文档

**Skills文档** (3个):
- `.claude/skills/phase1-discovery-planning/SKILL.md` (~500行)
- `.claude/skills/phase6-acceptance/SKILL.md` (~400行)
- `.claude/skills/phase7-closure/SKILL.md` (~600行)

**开发指南** (2个):
- `docs/HOOKS_GUIDE.md` (~800行)
- `docs/SKILLS_GUIDE.md` (~500行)

**更新文档** (4个):
- `CLAUDE.md` → 添加Phase 7清理说明
- `CHANGELOG.md` → 记录v8.8.0改动
- `README.md` → 更新版本号
- `docs/PARALLEL_SUBAGENT_STRATEGY.md` → 添加"如何使用"章节

### 12.2 文档标准

**每个文档必须包含**:
- 目的说明
- 使用示例
- 常见错误
- 故障排查
- 相关文件引用

**质量要求**:
- 代码示例可运行
- 链接有效
- 排版清晰
- 中英双语关键部分

---

## 13. Known Limitations（已知限制）

### 13.1 并行执行限制

**无法并行的Phase**:
- Phase 1: 规划阶段，必须串行
- Phase 5: Git操作，必须串行（部分可并行）
- Phase 6: 用户确认，必须串行
- Phase 7: 清理和merge，必须串行

**冲突检测限制**:
- 无法检测运行时冲突（如数据库锁）
- 无法检测语义冲突（如API契约不一致）
- 需要开发者手动定义conflict_paths

**AI并行限制**:
- AI必须主动在单个消息中调用多个Task tool
- 如果AI不理解指导，会退化为串行
- SubAgents无法互相调用（架构限制）

### 13.2 Skills系统限制

**Trigger限制**:
- 只能基于event、tool、context触发
- 无法基于复杂逻辑（如"Phase3且测试失败时"）
- Trigger匹配是字符串匹配，不是语义理解

**Action限制**:
- Reminder类型只能提示，不能强制
- Script类型需要bash支持
- 无法在skill中调用其他skill

**Priority限制**:
- P0 > P1，但同级skill可能冲突
- 无法动态调整priority

### 13.3 Phase 7清理限制

**时机限制**:
- 只能在Phase7完成后清理
- 如果Phase6→Phase7失败，状态可能遗留
- 如果用户强制退出，状态可能遗留

**范围限制**:
- 只清理`.phase/current`和`.workflow/current`
- 不清理`.workflow/`下的其他文件（P1_DISCOVERY.md等）
- 需要手动清理或通过comprehensive_cleanup.sh

---

## 14. Dependencies on External Systems（外部依赖）

**无外部依赖** ✓

所有依赖都是本地工具：
- bash 4.0+
- git 2.0+
- yq (optional, for YAML parsing)
- jq (optional, for JSON parsing)

如果yq/jq不存在，系统会fallback到简单模式。

---

## 15. Stakeholder Impact（相关方影响）

### 15.1 AI（Claude Code）

**Impact**: HIGH（直接受益者）
- ✅ Phase 1/6/7有详细执行指导
- ✅ 并行执行更高效
- ✅ 错误状态继承被修复
- ⚠️ 需要学习"单个消息调用多个Task tool"

**Action Required**: 无（自动应用）

### 15.2 用户（perfectuser21）

**Impact**: MEDIUM（间接受益者）
- ✅ 工作流更可靠（无Phase状态错误）
- ✅ Phase 2-7执行更快（并行加速）
- ✅ AI执行质量更高（有详细指导）
- ⚠️ 需要熟悉新的hooks/skills指南

**Action Required**:
- 阅读docs/HOOKS_GUIDE.md和docs/SKILLS_GUIDE.md
- 可选：调整并行执行配置（如果需要）

### 15.3 系统（Claude Enhancer）

**Impact**: LOW（系统更健壮）
- ✅ Phase 7清理机制完善
- ✅ 并行执行真正可用
- ✅ 文档更完整
- ⚠️ 代码复杂度略有增加（可控）

**Action Required**: 无（向后兼容）

---

## 16. Timeline Estimate（时间线估算）

### 16.1 Phase 2: Implementation (4-6小时)

**并行组1: Phase 7清理机制** (1.5小时)
- 修改comprehensive_cleanup.sh (30min)
- 修改phase_completion_validator.sh (30min)
- 创建post-merge hook (30min)

**并行组2: 并行执行集成** (3小时)
- 验证executor.sh集成 (1h)
- 修复集成代码（如需要） (1h)
- 优化conflict_detector.sh (1h)

**并行组3: Phase 1 skill创建** (2小时)
- 编写SKILL.md内容 (1.5h)
- 测试trigger和格式 (0.5h)

**并行组4: Phase 6/7 skills创建** (2.5小时)
- Phase 6 SKILL.md (1h)
- Phase 7 SKILL.md (重点，1.5h)

**并行组5: Hooks/Skills指南** (2小时)
- docs/HOOKS_GUIDE.md (1h)
- docs/SKILLS_GUIDE.md (1h)

**串行任务: settings.json注册** (0.5小时)
- 添加3个skill配置
- 验证JSON格式

**Parallel Estimate**: 3小时（最长并行组）
**Serial Estimate**: 6小时
**Speedup**: 2x

### 16.2 Phase 3: Testing (2-3小时)

**Unit tests** (1小时)
**Integration tests** (1小时)
**Performance tests** (1小时)
**修复发现的问题** (预留buffer)

### 16.3 Phase 4: Review (1-2小时)

**Code review** (1小时)
**Pre-merge audit** (30min)
**Documentation review** (30min)

### 16.4 Phase 5-7 (1小时)

**Phase 5: Release** (30min)
- 更新CHANGELOG.md
- 更新README.md
- 版本号升级到8.8.0

**Phase 6: Acceptance** (15min)
- 用户验收

**Phase 7: Closure** (15min)
- 运行新的清理机制
- 创建PR

**Total Estimate**: 8-12小时（含buffer）
**Best Case**: 1工作日（8小时）
**Realistic**: 1.5工作日（12小时）

---

## 17. Conclusion（结论）

### 17.1 Summary

这个优化方案解决3个相关问题：
1. ✅ 修复Phase 7清理机制bug（HIGH priority）
2. ✅ 优化并行执行系统，让理论变成实践（MEDIUM priority）
3. ✅ 为Phase 1/6/7创建Skills + 完整Hooks/Skills指南（MEDIUM priority）

### 17.2 Why This Approach

**一起做的理由**：
- 逻辑相关：Phase 7 skill包含清理机制指导
- 效率最高：避免多次merge
- 风险可控：有完整rollback策略
- 影响可见：用户能直接感受到改进

### 17.3 Expected Outcome

**Phase 7清理**：
- ✓ main分支始终干净
- ✓ 新feature分支从Phase1开始
- ✓ 无错误状态继承

**并行执行**：
- ✓ Phase 2-7真正并行执行
- ✓ Phase 3测试加速3-5x
- ✓ 整体开发效率提升40%+

**Skills + 指南**：
- ✓ Phase 1/6/7有详细执行指导
- ✓ 20个hooks有完整文档
- ✓ Skills开发指南完整
- ✓ AI执行质量显著提升

### 17.4 Next Steps

等待用户确认此方案，然后：
1. 创建ACCEPTANCE_CHECKLIST.md（定义验收标准）
2. 创建PLAN.md（详细实施计划）
3. 等待用户说"我理解了，开始Phase 2"
4. 进入Phase 2实施

---

**Status**: Phase 1.3 (Technical Discovery) Complete ✓
**Next**: Phase 1.4 (Impact Assessment) + Phase 1.5 (Architecture Planning)
