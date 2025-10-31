# Implementation Plan - Phase 1/6/7 Skills + 并行执行系统 + Phase 7清理机制优化

**Branch**: feature/phase-skills-hooks-optimization
**Date**: 2025-10-31
**Phase**: 1.5 Architecture Planning
**Target Version**: 8.8.0
**Impact Radius**: 72/100 (very-high-risk)
**Agent Strategy**: 8 agents并行

---

## 📋 Executive Summary

### 任务概览

本次优化解决三个紧密关联的系统问题：
1. **Phase 7清理机制Bug修复**（HIGH优先级）- merge后Phase状态清理失败
2. **并行执行系统集成**（MEDIUM优先级）- 文档完整但代码未真正运行
3. **Phase 1/6/7 Skills指导**（MEDIUM优先级）- 缺少详细AI行为指导

### 核心目标

✅ **清理机制**：merge后自动清理Phase状态，新分支总是从Phase1开始  
✅ **并行执行**：Phase 3测试加速≥3x，有日志证明并行运行  
✅ **Skills指导**：Phase 1/6/7有详细substages指导，20个hooks有完整文档  
✅ **质量保证**：90%验收项通过（116/129），所有代码通过质量检查

### 战略决策

**Impact Assessment结果**：
- Risk: 8/10 (HIGH) - 修改workflow核心
- Complexity: 10/10 (VERY HIGH) - 架构级变更 + 多系统交互
- Scope: 1/10 (LOW) - 局限在workflow内部
- **Impact Radius: 72/100** → very-high-risk策略

**推荐Agent数量**：8 agents
**预计总时长**：6小时（串行） → 0.9小时（8 agents并行） = **6.7x加速**

### 时间估算

| Phase | 活动 | 时间（串行） | 时间（8 agents） | 累计 |
|-------|------|--------------|------------------|------|
| Phase 1 | Discovery + Planning（当前） | 2h | 2h | 2h |
| **Phase 2** | **Implementation (8 agents)** | **6h** | **0.9h** | **2.9h** |
| Phase 3 | Testing + Performance | 1.8h | 0.4h | 3.3h |
| Phase 4 | Review + Audit | 2h | 0.8h | 4.1h |
| Phase 5 | Release Preparation | 1h | 1h | 5.1h |
| Phase 6-7 | Acceptance + Closure | 0.5h | 0.5h | 5.6h |

**关键里程碑**：
- ⚡ Phase 2最大加速比：6h → 0.9h (6.7x)
- ⚡ Phase 3加速比：1.8h → 0.4h (4.5x)
- ⚡ 总加速比：13.3h → 5.6h (2.4x整体加速)

---

## 🏗️ Architecture Design（架构设计）

### 三大子系统设计

#### 子系统1：Phase 7清理机制（3-Layer Cleanup）

**目标**：merge后自动清理Phase状态，新分支总是从Phase1开始

**三层架构**：
```
Layer 1: comprehensive_cleanup.sh（脚本清理层）
  - 检测Phase7完成标记
  - 清理.phase/current, .workflow/current
  - 创建.phase/completed（记录完成时间）
  - 执行时机：Phase 7手动执行

Layer 2: phase_completion_validator.sh（Phase转换层）
  - 检测Phase 7 → "完成"转换
  - 自动触发清理逻辑
  - 创建.workflow/workflow_complete标记
  - 执行时机：PostToolUse hook触发

Layer 3: post-merge hook（Git merge层）
  - 检测merge到main分支
  - 强制清理所有Phase状态文件
  - 验证main分支无Phase标记
  - 执行时机：git merge完成后
```

**清理范围**：
- ✓ `.phase/current` - 当前Phase标记
- ✓ `.workflow/current` - workflow当前状态
- ✓ 创建`.phase/completed` - 工作流完成记录（时间戳）
- ✓ 创建`.workflow/workflow_complete` - 完成标记

**验证机制**：
- main分支检查：`ls -la .phase/current` 应该显示"文件不存在"
- 新分支检查：创建新分支后AI进入Phase1

#### 子系统2：并行执行系统集成（Activate Parallel Executor）

**目标**：从"文档完整"到"真正运行"，实现3-5x加速

**当前状态分析**：
```
已有组件 ✓:
├─ docs/PARALLEL_SUBAGENT_STRATEGY.md (完整文档)
├─ .workflow/STAGES.yml (配置定义)
├─ .workflow/lib/parallel_executor.sh (并行执行器)
├─ scripts/subagent/parallel_task_generator.sh (Task生成器)
└─ .claude/hooks/parallel_subagent_suggester.sh (AI提醒hook)

缺失部分 ✗:
├─ .workflow/executor.sh未调用parallel_executor.sh
├─ parallel_executor.sh无执行日志
└─ AI未在单个消息中调用多个Task tool
```

**集成方案**：
修改.workflow/executor.sh，添加并行检测和调用逻辑：
- 检测Phase是否支持并行（Phase 1和7不支持）
- 读取STAGES.yml获取并行组配置
- 调用parallel_executor.sh执行
- 生成执行日志证明并行运行

**并行模式映射**（from STAGES.yml）：
- **Phase 2**: Implementation → 6 agents并行（修改hooks、scripts、docs）
- **Phase 3**: Testing → 5 agents并行（unit、integration、performance、security）
- **Phase 4**: Review → 3 agents并行（逻辑审查、文档审查、版本审查）
- **Phase 5**: Release → 2 agents并行（CHANGELOG、部署文档）
- **Phase 7**: Cleanup → 3 agents并行（temp清理、版本验证、Git优化）

**日志验证**：
- 创建`.workflow/logs/parallel_Phase2_*.log`
- 内容包含：agent启动时间、任务分配、完成时间、错误信息
- AI可引用日志证明并行执行

#### 子系统3：Skills + Hooks指导（AI Behavior Guidance）

**目标**：Phase 1/6/7有详细指导，20个hooks有完整文档

**Skills Framework**（3个新Skills）：

**phase1-discovery-planning.yml** - Phase 1完整流程指导：5个substages详细步骤
**phase6-acceptance.yml** - Phase 6验收流程：对照checklist逐项验证  
**phase7-closure.yml** - Phase 7收尾流程：清理+验证+PR准备

**Hooks Documentation**（2个新文档）：

**docs/HOOKS_GUIDE.md** - 完整的20个hooks说明文档（~800行）
**docs/SKILLS_GUIDE.md** - Skills创建和使用指南（~500行）

---

## 📐 Phase 2: Implementation Breakdown（8 agents并行）

### 并行组1：Phase 7清理机制修复（3 agents）

**Agent 1: comprehensive_cleanup.sh修改**
- 任务：在脚本末尾添加Phase状态清理逻辑
- 预计时间：30分钟
- 位置：scripts/comprehensive_cleanup.sh Line ~350

**Agent 2: phase_completion_validator.sh修改**
- 任务：Phase 7完成时自动清理
- 预计时间：30分钟
- 位置：.claude/hooks/phase_completion_validator.sh

**Agent 3: 创建post-merge hook**
- 任务：创建.git/hooks/post-merge（merge后强制清理）
- 预计时间：30分钟
- 注册：在.claude/install.sh中添加chmod +x

### 并行组2：并行执行系统集成（3 agents）

**Agent 4: 修改.workflow/executor.sh**
- 任务：启用并行模式，调用parallel_executor.sh
- 预计时间：45分钟

**Agent 5: 修改parallel_task_generator.sh**
- 任务：读取STAGES.yml生成Task调用
- 预计时间：45分钟

**Agent 6: 更新STAGES.yml**
- 任务：定义Phase 2-7并行组配置
- 预计时间：30分钟

### 并行组3：Skills+Hooks指导（2 agents）

**Agent 7: 创建phase1/6/7 skills文件**
- 任务：创建3个.yml skills文件
- 预计时间：1小时

**Agent 8: 创建SKILLS_GUIDE.md + HOOKS_GUIDE.md**
- 任务：编写完整文档
- 预计时间：1.5小时

---

## 🧪 Phase 3: Testing Strategy

### 3.1 单元测试（Unit Tests）

**清理机制测试**：
- test_comprehensive_cleanup_phase_state.sh
- test_phase_completion_validator_phase7.sh
- test_post_merge_hook.sh

**并行执行测试**：
- test_executor_parallel_detection.sh
- test_parallel_task_generator.sh
- test_stages_yml_parsing.sh

### 3.2 集成测试（Integration Tests）

**场景1：完整Phase 1-7流程**
- 从Phase1开始 → Phase7完成 → merge → 验证清理

**场景2：并行执行验证**
- Phase 2执行 → 检查日志 → 验证加速比

**场景3：Skills触发验证**
- Phase转换 → Skills提醒 → AI执行正确流程

### 3.3 性能测试（Performance Tests）

**清理机制性能**：
- comprehensive_cleanup.sh执行时间 <10s

**并行执行性能**：
- Phase 3测试加速比 ≥3x
- 日志文件大小 <1MB

**Hooks性能**：
- 所有hooks执行时间 <50ms

---

## 🛡️ 保障机制

### 5层质量防护

**Layer 1: Phase 3测试门禁（强制）**
- 静态检查（bash -n, shellcheck）
- 单元测试（hooks、scripts独立测试）
- 集成测试（完整Phase 1-7流程验证）
- 性能测试（清理机制 <10s，并行执行加速 ≥3x）

**Layer 2: Phase 4审查门禁（强制）**
- pre_merge_audit.sh（12项检查）
- 代码逻辑审查（Phase状态转换正确性）
- 版本一致性（6个文件统一）
- 文档完整性（REVIEW.md >100行）

**Layer 3: Phase 7清理验证**
- 三层清理机制全部工作
- 版本一致性最终验证
- Git status干净

**Layer 4: CI/CD验证**
- guard-core.yml（61项检查）
- Anti-Hollow Gate（防止空壳实现）
- Branch Protection（防止直推main）

**Layer 5: 回滚机制**
- Git feature分支隔离
- 所有变更可独立回滚
- 零影响主线稳定性

---

## 🎯 验收标准（90%通过率要求）

### Phase 7清理机制验收（场景1-3）

**场景1：merge代码后检查**
- 你说"merge"
- AI执行merge
- 你检查main分支：`ls -la .phase/current`应该显示"文件不存在"
- ✅ 通过：文件不存在
- ❌ 失败：文件还在

**场景2：创建新分支后检查**
- 在main分支执行：`git checkout -b feature/test-cleanup`
- 你检查Phase状态：AI应该自动进入Phase1
- ✅ 通过：AI说"我们现在在Phase1"
- ❌ 失败：AI说"我们在Phase7"

**场景3：三层清理都工作**
- 第一层：comprehensive_cleanup.sh脚本清理
- 第二层：phase_completion_validator.sh在Phase7完成时清理
- 第三层：post-merge hook在merge后清理
- ✅ 通过：你随便测任何一层，都能清理
- ❌ 失败：某一层不工作

### 并行执行验收（场景1-3）

**场景1：Phase 3测试加速**
- 创建一个高复杂度任务（Impact Radius ≥50）
- 进入Phase 3测试阶段
- 记录测试开始时间和结束时间
- ✅ 通过：时间缩短至少3倍（例如：3小时→1小时）
- ❌ 失败：时间没明显变化

**场景2：能看到并行执行证据**
- Phase 3时查看日志：`ls .workflow/logs/*parallel*`
- ✅ 通过：有日志文件，内容显示多个agent同时执行
- ❌ 失败：无日志或日志显示串行执行

**场景3：AI知道如何并行**
- Phase 1结束时，AI说："我将使用6个agents并行执行Phase 2"
- Phase 2时，AI在单个消息中调用多个Task tool
- ✅ 通过：AI行为符合并行执行要求
- ❌ 失败：AI还是一个个串行执行

### Skills指导验收（场景1-5）

**场景1：Phase 1有详细指导**
- 你给AI一个新需求
- AI进入Phase 1
- AI显示："参考 phase1-discovery-planning skill..."
- ✅ 通过：AI展示5个substages完整流程
- ❌ 失败：AI没有系统性指导，步骤混乱

**场景2：Phase 6验收报告完整**
- Phase 6时AI生成ACCEPTANCE_REPORT.md
- 报告包含：所有checklist项验证结果、证据、通过/失败统计
- ✅ 通过：报告详细，你能看懂每项是否通过
- ❌ 失败：报告简单或缺失

**场景3：Phase 7有清理指导**
- Phase 7时AI说："根据phase7-closure skill，我需要..."
- AI执行：清理、验证、创建PR（不是直接merge）
- ✅ 通过：AI按正确流程操作
- ❌ 失败：AI直接merge或漏步骤

**场景4：Hooks文档完整**
- 你打开docs/HOOKS_GUIDE.md
- 搜索任意一个hook名字（如：branch_helper.sh）
- 能找到：这个hook干什么、什么时候触发、如何配置
- ✅ 通过：20个hooks都有文档
- ❌ 失败：部分hooks无文档

**场景5：Skills文档完整**
- 你想创建一个新skill
- 打开docs/SKILLS_GUIDE.md
- 按照步骤操作能成功创建
- ✅ 通过：文档清晰可操作
- ❌ 失败：文档不清楚或缺步骤

### 质量验收（场景1-3）

**场景1：所有脚本无语法错误**
- 运行：`bash scripts/static_checks.sh`
- ✅ 通过：所有检查绿灯
- ❌ 失败：有红灯

**场景2：版本号统一**
- 检查6个文件：VERSION, settings.json, manifest.yml, package.json, CHANGELOG.md, SPEC.yaml
- ✅ 通过：6个文件版本号完全一致（如都是8.8.0）
- ❌ 失败：版本号不一致

**场景3：验收项通过率**
- 对照ACCEPTANCE_CHECKLIST.md逐项检查
- ✅ 通过：≥90%的项checked（至少116/129项）
- ❌ 失败：<90%

---

## 📈 成功指标

### 短期指标（Phase 6验收）
- Acceptance Checklist ≥90%完成
- 所有测试通过（单元+集成）
- 性能满足预算（清理≤10s，并行加速≥3x）
- 文档完整（REVIEW.md >100行）

### 中期指标（1周后）
- 实际使用并行执行≥5次
- 无regression bug报告
- 性能稳定（无下降）

### 长期指标（1个月后）
- Phase 7清理成功率100%
- 并行执行实际加速≥3x
- AI行为规范性提升（用户反馈）

---

## 🔄 回滚计划

### 回滚触发条件
- Phase 3测试失败率>20%
- Phase 4审查发现critical bugs
- Phase 6验收通过率<70%

### 回滚步骤
```bash
# Step 1: 切换到main分支
git checkout main

# Step 2: 删除feature分支
git branch -D feature/phase-skills-hooks-optimization

# Step 3: 验证main分支clean
git status

# Step 4: 如果已经merge，revert commit
git revert HEAD
```

### 回滚验证
- main分支无Phase状态遗留
- 所有hooks正常工作
- CI全部通过

---

**生成时间**：2025-10-31
**作者**：Claude Code
**版本**：v1.0
