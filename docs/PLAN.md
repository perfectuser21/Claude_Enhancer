# Documentation Fix Plan - Critical Issues Resolution

> **任务**: 修复DECISION_TREE.md和BUTLER_MODE_IMPACT_ANALYSIS.md中的5个Critical Issues
> **分支**: docs/decision-tree-documentation
> **预计时间**: 8-12小时
> **Phase**: Phase 1 (Planning & Architecture)

---

## 📊 Executive Summary

### 问题根源
**Root Cause Pattern**: "Hub-Spoke Update Failure"

v6.3.0重构时（8-Phase → 6-Phase系统迁移）：
- ✅ 更新了Hub文档（CLAUDE.md）
- ❌ 未更新Spoke文档（WORKFLOW.md, DECISION_TREE.md）
- 结果：派生文档包含过时信息

### 5个Critical Issues概览

| Issue | 严重性 | 影响范围 | 修复时间 |
|-------|--------|---------|---------|
| 1. Agent数量错误 | Critical | 整个决策树 | 1小时 |
| 2. Hook数量错误 | Critical | 系统描述 | 1.5小时 |
| 3. Phase编号混乱 | Critical | 工作流逻辑 | 1小时 |
| 4. Butler Mode状态不清 | Critical | 用户误解 | 1.5小时 |
| 5. 不存在的脚本引用 | Critical | 可验证性 | 2小时 |
| **总计** | - | - | **7小时** |

---

## 🔥 Issue 1: Agent Count Inconsistency

### 问题描述
**文档声称**: 简单任务3个Agent，标准任务4个Agent，复杂任务4个Agent
**实际实现**: 简单任务4个，标准任务6个，复杂任务8个（4-6-8原则）
**Source of Truth**: `.claude/hooks/smart_agent_selector.sh` + `CLAUDE.md`

### 影响范围
```bash
# 错误出现位置
docs/DECISION_TREE.md:139-143     # Agent选择表格
docs/DECISION_TREE.md:2156        # Step 5决策树
docs/DECISION_TREE.md:3449        # Part 4总结
docs/diagrams/decision_flow.mermaid:45  # 流程图
```

### 修复方案

#### Step 1.1: 更新DECISION_TREE.md中的Agent数量
```bash
# 全局替换（注意：仅替换Agent数量相关描述）
sed -i 's/简单任务：3个Agent/简单任务：4个Agent/g' docs/DECISION_TREE.md
sed -i 's/标准任务：4个Agent/标准任务：6个Agent/g' docs/DECISION_TREE.md
sed -i 's/复杂任务：4个Agent/复杂任务：8个Agent/g' docs/DECISION_TREE.md

# 验证替换结果
grep -n "个Agent" docs/DECISION_TREE.md | grep -E "(简单|标准|复杂)"
```

#### Step 1.2: 更新Agent选择表格（Line 139-143）
**当前内容**:
```markdown
| 简单 | 3个Agent | 修复bug、小改动 |
| 标准 | 4个Agent | 新功能、重构 |
| 复杂 | 4个Agent | 架构设计、大型功能 |
```

**修复后**:
```markdown
| 简单 | 4个Agent | 修复bug、小改动 |
| 标准 | 6个Agent | 新功能、重构 |
| 复杂 | 8个Agent | 架构设计、大型功能 |
```

#### Step 1.3: 更新decision_flow.mermaid流程图
**位置**: `docs/diagrams/decision_flow.mermaid:45`

**当前**:
```mermaid
select_agents[Select 4-8 Agents]
```

**修复后**:
```mermaid
select_agents{Agent Selection}
select_agents -->|Simple| agents_4[4 Agents]
select_agents -->|Standard| agents_6[6 Agents]
select_agents -->|Complex| agents_8[8 Agents]
```

#### Step 1.4: 验证与代码一致性
```bash
# 验证smart_agent_selector.sh实现
grep -A 2 "simple)" .claude/hooks/smart_agent_selector.sh
grep -A 2 "standard)" .claude/hooks/smart_agent_selector.sh
grep -A 2 "complex)" .claude/hooks/smart_agent_selector.sh

# 验证CLAUDE.md描述
grep -A 5 "4-6-8原则" CLAUDE.md
```

### 验收标准
- [ ] `grep "简单任务：4个Agent" docs/DECISION_TREE.md` 有结果
- [ ] `grep "标准任务：6个Agent" docs/DECISION_TREE.md` 有结果
- [ ] `grep "复杂任务：8个Agent" docs/DECISION_TREE.md` 有结果
- [ ] `grep "3个Agent" docs/DECISION_TREE.md` 无结果（除了历史记录）
- [ ] Mermaid图显示明确的4/6/8分支

### 预计时间
**1小时** (文本替换30分钟 + 流程图更新20分钟 + 验证10分钟)

---

## 🔥 Issue 2: Hook Count Error

### 问题描述
**文档声称**: 系统有15个active hooks
**实际数量**: 17个active hooks
**Source of Truth**: `.claude/settings.json`

### 影响范围
```bash
# 错误出现位置
docs/DECISION_TREE.md:77          # Part 1总览
docs/DECISION_TREE.md:3449        # Part 3 Hook决策树标题
docs/DECISION_TREE.md:4705        # Part 4总结
docs/DECISION_TREE.md:4721        # 最终总结
```

### 实际Hook清单（17个）

#### UserPromptSubmit Hook (2个)
1. `requirement_clarification.sh` - 需求澄清
2. `workflow_auto_start.sh` - 工作流自动启动

#### PrePrompt Hook (5个)
3. `force_branch_check.sh` - 强制分支检查
4. `ai_behavior_monitor.sh` - AI行为监控
5. `workflow_enforcer.sh` - 工作流强制执行
6. `smart_agent_selector.sh` - 智能Agent选择
7. `gap_scan.sh` - 差距扫描

#### PreToolUse Hook (7个)
8. `task_branch_enforcer.sh` - 任务分支强制绑定
9. `branch_helper.sh` - 分支助手
10. `code_writing_check.sh` - 代码写入检查
11. `agent_usage_enforcer.sh` - Agent使用强制
12. `quality_gate.sh` - 质量门禁
13. `auto_cleanup_check.sh` - 自动清理检查
14. `concurrent_optimizer.sh` - 并发优化器

#### PostToolUse Hook (3个)
15. `merge_confirmer.sh` - 合并确认
16. `unified_post_processor.sh` - 统一后处理
17. `agent_error_recovery.sh` - Agent错误恢复

### 修复方案

#### Step 2.1: 全局替换Hook数量
```bash
# 替换所有"15个active hooks"为"17个active hooks"
sed -i 's/15个active hooks/17个active hooks/g' docs/DECISION_TREE.md
sed -i 's/15个hooks/17个hooks/g' docs/DECISION_TREE.md
sed -i 's/共15个/共17个/g' docs/DECISION_TREE.md

# 验证
grep -n "17个" docs/DECISION_TREE.md
```

#### Step 2.2: 在Part 3添加完整Hook清单
**插入位置**: `docs/DECISION_TREE.md` Line 3450之后

**添加内容**:
```markdown
### 完整Hook清单（17个）

#### UserPromptSubmit Hook (2个)
1. **requirement_clarification.sh** - 需求澄清（讨论模式触发）
2. **workflow_auto_start.sh** - 工作流自动启动（执行模式触发）

#### PrePrompt Hook (5个)
3. **force_branch_check.sh** - 强制分支检查（Phase -1）
4. **ai_behavior_monitor.sh** - AI行为监控（防止违反规则）
5. **workflow_enforcer.sh** - 工作流强制执行（Phase 0-5验证）
6. **smart_agent_selector.sh** - 智能Agent选择（4-6-8原则）
7. **gap_scan.sh** - 差距扫描（Phase 0支持）

#### PreToolUse Hook (7个)
8. **task_branch_enforcer.sh** - 任务分支强制绑定（Write/Edit前）
9. **branch_helper.sh** - 分支助手（main/master保护）
10. **code_writing_check.sh** - 代码写入检查（讨论模式阻止）
11. **agent_usage_enforcer.sh** - Agent使用强制（最少3个）
12. **quality_gate.sh** - 质量门禁（Phase 3/4检查）
13. **auto_cleanup_check.sh** - 自动清理检查（.temp/清理）
14. **concurrent_optimizer.sh** - 并发优化器（并行执行检测）

#### PostToolUse Hook (3个)
15. **merge_confirmer.sh** - 合并确认（用户说"merge"后执行）
16. **unified_post_processor.sh** - 统一后处理（日志、记录）
17. **agent_error_recovery.sh** - Agent错误恢复（失败重试）

**验证命令**:
```bash
# 从settings.json统计
jq '.hooks | to_entries[] | .value[]' .claude/settings.json | wc -l
# 输出: 17
```
```

#### Step 2.3: 更新Butler Mode文档中的Hook引用
```bash
# BUTLER_MODE_IMPACT_ANALYSIS.md中也可能有Hook数量引用
grep -n "15个" docs/BUTLER_MODE_IMPACT_ANALYSIS.md
# 如果有，同样替换为17个
```

### 验收标准
- [ ] `grep "15个" docs/DECISION_TREE.md` 无结果
- [ ] `grep "17个active hooks" docs/DECISION_TREE.md` 有4处
- [ ] Part 3包含完整17个Hook清单
- [ ] 每个Hook有明确的功能描述
- [ ] 验证命令可执行且结果正确

### 预计时间
**1.5小时** (替换30分钟 + Hook清单整理40分钟 + 描述完善20分钟)

---

## 🔥 Issue 3: Phase Numbering Confusion

### 问题描述
**混淆点**: 文档中提到"Phase 6 (P9)"，但系统只有Phase 0-5（6个Phase）
**根源**: 混淆了"Steps"（10个）和"Phases"（6个）
**误导**: 用户可能寻找不存在的"Phase 6"

### 系统实际结构

#### 10 Steps（完整流程）
1. Step 1: Pre-Discussion（需求讨论）
2. Step 2: Phase -1 - Branch Check（分支检查）
3. Step 3: Phase 0 - Discovery（探索）
4. Step 4: Phase 1 - Planning & Architecture（规划+架构）
5. Step 5: Phase 2 - Implementation（实现）
6. Step 6: Phase 3 - Testing（测试）
7. Step 7: Phase 4 - Review（审查）
8. Step 8: Phase 5 - Release & Monitor（发布+监控）
9. Step 9: Acceptance Report（验收报告）
10. Step 10: Cleanup & Merge（收尾清理）

#### 6 Phases（开发阶段）
- Phase 0: Discovery
- Phase 1: Planning & Architecture
- Phase 2: Implementation
- Phase 3: Testing
- Phase 4: Review
- Phase 5: Release & Monitor

#### 关键区别
- **Steps 9-10不是Phases**，它们是工作流步骤
- **Phase -1是特殊前置Phase**，但不计入6-Phase系统
- **没有Phase 6**

### 影响范围
```bash
# 查找所有"Phase 6"引用
grep -n "Phase 6" docs/DECISION_TREE.md
grep -n "P6" docs/DECISION_TREE.md | grep -v "Phase"

# 查找"P9"引用
grep -n "P9" docs/DECISION_TREE.md
grep -n "P9" CLAUDE.md
```

### 修复方案

#### Step 3.1: 删除CLAUDE.md中的错误引用
**位置**: `CLAUDE.md` 中提到"Phase 6 (P9)"的地方

**查找**:
```bash
grep -n "Phase 6" CLAUDE.md
grep -n "P9" CLAUDE.md
```

**修复**:
```markdown
❌ 错误: "Step 10: Phase 6 (P9) - Cleanup & Merge"
✅ 正确: "Step 10: Cleanup & Merge（非Phase，是工作流步骤）"
```

#### Step 3.2: 在DECISION_TREE.md中添加术语澄清
**插入位置**: Part 1总览之后

**添加内容**:
```markdown
### 🔍 重要术语澄清

#### Steps vs Phases
Claude Enhancer使用两套编号系统，容易混淆：

| 术语 | 数量 | 范围 | 说明 |
|-----|------|------|------|
| **Steps（步骤）** | 10个 | Step 1 - Step 10 | 完整工作流的所有步骤 |
| **Phases（阶段）** | 6个 | Phase 0 - Phase 5 | 开发周期的核心阶段 |
| **Special** | 1个 | Phase -1 | 前置检查，不计入6-Phase |

#### 映射关系
```
Step 1: Pre-Discussion          → （不是Phase，是准备）
Step 2: Phase -1                → （特殊前置Phase）
Step 3: Phase 0 - Discovery     → ✅ Phase 0
Step 4: Phase 1 - Planning      → ✅ Phase 1
Step 5: Phase 2 - Implementation→ ✅ Phase 2
Step 6: Phase 3 - Testing       → ✅ Phase 3
Step 7: Phase 4 - Review        → ✅ Phase 4
Step 8: Phase 5 - Release       → ✅ Phase 5
Step 9: Acceptance Report       → （不是Phase，是确认）
Step 10: Cleanup & Merge        → （不是Phase，是收尾）
```

#### 常见误解
- ❌ "Phase 6存在吗？" → 不存在，最高Phase 5
- ❌ "为什么有10步但只有6个Phase？" → Steps包含非Phase步骤
- ❌ "Phase -1算不算6-Phase之一？" → 不算，它是前置检查
- ✅ "6-Phase系统 = Phase 0到Phase 5" → 正确理解
```

#### Step 3.3: 添加版本演进说明
```markdown
### 📚 版本演进历史（Phase编号变化）

| 版本 | Phase系统 | 说明 |
|------|----------|------|
| v5.0-v6.2 | 8-Phase (P0-P7) | 原始设计：探索、规划、骨架、实现、测试、审查、发布、监控 |
| v6.3+ | 6-Phase (P0-P5) | **优化合并**: P1+P2=新P1, P6+P7=新P5，效率提升17% |

#### v6.3优化详情
- ✅ **合并P1规划+P2骨架** → 新Phase 1（规划与架构一次完成）
- ✅ **合并P6发布+P7监控** → 新Phase 5（发布和监控配置同步）
- ✅ **保持Phase 3/4质量门禁** → 零质量妥协
- ✅ **减少阶段切换开销** → 工作流更流畅

**迁移影响**:
- CLAUDE.md已更新 ✅
- WORKFLOW.md已更新 ✅
- DECISION_TREE.md需更新 ⚠️（本次修复）
```

### 验收标准
- [ ] `grep "Phase 6" CLAUDE.md` 无结果
- [ ] `grep "P9" CLAUDE.md` 无结果
- [ ] DECISION_TREE.md有术语澄清章节
- [ ] 版本演进表格清晰展示8→6的变化
- [ ] 所有Phase引用限于-1, 0-5范围

### 预计时间
**1小时** (CLAUDE.md修复20分钟 + 术语澄清编写30分钟 + 版本演进表格10分钟)

---

## 🔥 Issue 4: Butler Mode References Incomplete

### 问题描述
**文档**: `BUTLER_MODE_IMPACT_ANALYSIS.md` (2,400+ lines)
**问题**: 未明确标注"这是v6.6提案，当前未实现"
**风险**: 用户误以为Butler Mode已可用
**引用的不存在脚本**: butler_mode_detector.sh, butler_decision_recorder.sh, memory_recall.sh, context_manager.sh

### 当前状态
- Butler Mode: **提案阶段**，计划v6.6实现
- 当前版本: v6.5.0
- 文档创建时间: 2025-10-16（今天）
- 目的: 影响分析和实现规划

### 修复方案

#### Step 4.1: 重命名文件
```bash
# 明确标注为提案
git mv docs/BUTLER_MODE_IMPACT_ANALYSIS.md \
       docs/BUTLER_MODE_PROPOSAL_v6.6.md

# 更新所有引用此文件的链接
grep -r "BUTLER_MODE_IMPACT_ANALYSIS" docs/
# 逐一更新引用
```

#### Step 4.2: 添加文档顶部状态Banner
**插入位置**: 文件第1行

**Banner内容**:
```markdown
---
⚠️⚠️⚠️ **PROPOSAL DOCUMENT - NOT IMPLEMENTED** ⚠️⚠️⚠️

**Status**: 📋 Proposal for v6.6.0
**Current Version**: v6.5.0
**Implementation Status**: ❌ Not Started
**Purpose**: Impact Analysis & Implementation Planning
**Created**: 2025-10-16
**Target Release**: v6.6.0 (Q1 2026)

**Important**:
- Butler Mode功能**当前不可用**
- 本文档描述的hooks、脚本、配置均**未实现**
- 这是一份**设计规划文档**，不是用户指南
- 请勿尝试使用文中提到的Butler Mode功能

**Related Tracking**:
- Feature Request: #TBD
- Implementation Epic: #TBD
- Design Doc: This document

---
```

#### Step 4.3: 添加"已实现 vs 提案"对照表
**插入位置**: Executive Summary之后

**对照表**:
```markdown
### 🔍 v6.5 (Current) vs v6.6 (Proposed) Comparison

| 功能特性 | v6.5.0 (已实现) | v6.6.0 (提案) | 状态 |
|---------|----------------|---------------|------|
| **决策系统** | ||||
| 基础决策树 | ✅ 21+ decision points | ✅ 保持 | 已实现 |
| Butler决策增强 | ❌ 无 | 📋 +8 new points | 提案中 |
| 决策记录 | ❌ 无 | 📋 butler_decision_recorder.sh | 提案中 |
| **记忆系统** | ||||
| 静态配置 | ✅ CLAUDE.md | ✅ 保持 | 已实现 |
| 动态学习 | ❌ 无 | 📋 memory-cache.json | 提案中 |
| 上下文管理 | ❌ 无 | 📋 context_manager.sh | 提案中 |
| 记忆召回 | ❌ 无 | 📋 memory_recall.sh | 提案中 |
| **模式系统** | ||||
| 讨论模式 | ✅ 已实现 | ✅ 保持 | 已实现 |
| 执行模式 | ✅ 已实现 | ✅ 增强 | 部分提案 |
| Butler模式检测 | ❌ 无 | 📋 butler_mode_detector.sh | 提案中 |
| **Hooks** | ||||
| 当前Hooks | ✅ 17个hooks | ✅ 保持 | 已实现 |
| Butler专用Hooks | ❌ 无 | 📋 +4 new hooks | 提案中 |

**图例**:
- ✅ 已实现并可用
- ❌ 不存在/不可用
- 📋 提案中/计划实现
```

#### Step 4.4: 标注所有"提案功能"
在文档中每次提到未实现功能时，添加标记：

```markdown
❌ 错误写法:
"Butler Mode使用memory_recall.sh来召回历史决策"

✅ 正确写法:
"Butler Mode将使用memory_recall.sh来召回历史决策 📋[Proposed]"

或更明确:
"**[v6.6 Proposed]** Butler Mode将使用memory_recall.sh..."
```

**批量处理**:
```bash
# 查找所有提到未实现脚本的地方
grep -n "butler_mode_detector\|butler_decision_recorder\|memory_recall\|context_manager" \
     docs/BUTLER_MODE_PROPOSAL_v6.6.md

# 手动为每处添加 [Proposed] 或 [v6.6 Proposed] 标记
```

#### Step 4.5: 添加实现路线图章节
**添加位置**: 文档末尾

**路线图内容**:
```markdown
## 📅 Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] 创建memory-cache.json基础结构
- [ ] 实现context_manager.sh核心逻辑
- [ ] 添加butler_mode_detector.sh检测机制
- [ ] 单元测试覆盖率>80%

### Phase 2: Decision Enhancement (Week 3-4)
- [ ] 实现butler_decision_recorder.sh
- [ ] 集成8个新决策点
- [ ] 修改12个现有决策点
- [ ] BDD场景覆盖所有新决策

### Phase 3: Memory System (Week 5-6)
- [ ] 实现memory_recall.sh
- [ ] 动态学习算法实现
- [ ] 记忆衰减机制
- [ ] 性能基准测试

### Phase 4: Integration & Testing (Week 7)
- [ ] 集成测试
- [ ] 压力测试（100+ sessions）
- [ ] 文档完善
- [ ] 用户验收测试

### Phase 5: Release (Week 8)
- [ ] 发布v6.6.0-beta
- [ ] 收集反馈
- [ ] 修复bugs
- [ ] 正式发布v6.6.0

**Total Estimated Time**: 21-28 hours（文档中已评估）
**Target Release Date**: Q1 2026
```

### 验收标准
- [ ] 文件重命名为`BUTLER_MODE_PROPOSAL_v6.6.md`
- [ ] 顶部有明确的"NOT IMPLEMENTED"警告Banner
- [ ] 有完整的"已实现 vs 提案"对照表
- [ ] 所有未实现功能有`[Proposed]`或`📋`标记
- [ ] 有清晰的实现路线图
- [ ] 用户不会误以为Butler Mode可用

### 预计时间
**1.5小时** (重命名5分钟 + Banner编写10分钟 + 对照表30分钟 + 标记添加30分钟 + 路线图15分钟)

---

## 🔥 Issue 5: Non-existent Script References

### 问题描述
**文档引用但不存在的脚本**:
1. `scripts/static_checks.sh` - Phase 3质量门禁脚本
2. `scripts/pre_merge_audit.sh` - Phase 4合并前审计脚本
3. `scripts/memory_recall.sh` - Butler Mode记忆召回（v6.6提案）
4. `scripts/butler_mode_detector.sh` - Butler Mode检测（v6.6提案）
5. `scripts/butler_decision_recorder.sh` - 决策记录（v6.6提案）
6. `scripts/context_manager.sh` - 上下文管理（v6.6提案）

**影响**: 用户尝试运行文档中的命令时失败，降低文档可信度

### 分类处理策略

#### Category A: 立即创建（Critical，当前版本需要）
- `static_checks.sh` - Phase 3依赖
- `pre_merge_audit.sh` - Phase 4依赖

#### Category B: 标记为提案（v6.6才需要）
- `memory_recall.sh`
- `butler_mode_detector.sh`
- `butler_decision_recorder.sh`
- `context_manager.sh`

### 修复方案 - Category A

#### Step 5.1: 创建scripts/static_checks.sh
**功能**: Phase 3阶段的静态代码检查

**脚本内容**:
```bash
#!/usr/bin/env bash
# static_checks.sh - Phase 3 Static Quality Checks
# Version: 1.0.0
# Created: 2025-10-16

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔍 Phase 3: Static Quality Checks"
echo "=================================="

# 1. Shell语法检查
echo "📝 [1/5] Checking shell syntax..."
SHELL_ERRORS=0
while IFS= read -r -d '' script; do
    if ! bash -n "$script" 2>/dev/null; then
        echo "❌ Syntax error in: $script"
        ((SHELL_ERRORS++))
    fi
done < <(find "$PROJECT_ROOT/.claude/hooks" "$PROJECT_ROOT/scripts" -type f -name "*.sh" -print0 2>/dev/null)

if [ $SHELL_ERRORS -eq 0 ]; then
    echo "✅ All shell scripts have valid syntax"
else
    echo "❌ Found $SHELL_ERRORS script(s) with syntax errors"
    exit 1
fi

# 2. Shellcheck Linting
echo ""
echo "🔎 [2/5] Running shellcheck..."
if command -v shellcheck >/dev/null 2>&1; then
    SHELLCHECK_ERRORS=0
    while IFS= read -r -d '' script; do
        if ! shellcheck -x "$script" 2>/dev/null; then
            ((SHELLCHECK_ERRORS++))
        fi
    done < <(find "$PROJECT_ROOT/.claude/hooks" "$PROJECT_ROOT/scripts" -type f -name "*.sh" -print0 2>/dev/null)

    if [ $SHELLCHECK_ERRORS -eq 0 ]; then
        echo "✅ Shellcheck passed"
    else
        echo "⚠️  Found $SHELLCHECK_ERRORS shellcheck warning(s) (non-blocking)"
    fi
else
    echo "⚠️  Shellcheck not installed, skipping (non-blocking)"
fi

# 3. 代码复杂度检查
echo ""
echo "📊 [3/5] Checking code complexity..."
COMPLEX_FUNCTIONS=0
while IFS= read -r -d '' script; do
    # 查找超过150行的函数
    awk '/^[[:space:]]*function[[:space:]]+[a-zA-Z_]/ {start=NR; name=$2}
         /^}$/ && start {
             if (NR - start > 150) {
                 print FILENAME":"start": Function " name " is too long (" NR-start " lines)"
                 exit 1
             }
             start=0
         }' "$script" && continue
    ((COMPLEX_FUNCTIONS++))
done < <(find "$PROJECT_ROOT/.claude/hooks" "$PROJECT_ROOT/scripts" -type f -name "*.sh" -print0 2>/dev/null)

if [ $COMPLEX_FUNCTIONS -eq 0 ]; then
    echo "✅ No overly complex functions found"
else
    echo "❌ Found $COMPLEX_FUNCTIONS function(s) exceeding 150 lines"
    exit 1
fi

# 4. Hook性能测试
echo ""
echo "⚡ [4/5] Testing hook performance..."
SLOW_HOOKS=0
for hook in "$PROJECT_ROOT/.claude/hooks"/*.sh; do
    [ -f "$hook" ] || continue
    [ -x "$hook" ] || continue

    # 模拟执行（传入测试参数）
    start_time=$(date +%s%N)
    timeout 5s "$hook" "test" "test" >/dev/null 2>&1 || true
    end_time=$(date +%s%N)

    duration=$(( (end_time - start_time) / 1000000 )) # 转换为毫秒

    if [ $duration -gt 2000 ]; then
        echo "❌ Hook $(basename "$hook") too slow: ${duration}ms (limit: 2000ms)"
        ((SLOW_HOOKS++))
    fi
done

if [ $SLOW_HOOKS -eq 0 ]; then
    echo "✅ All hooks execute within performance budget"
else
    echo "❌ Found $SLOW_HOOKS slow hook(s)"
    exit 1
fi

# 5. 功能测试
echo ""
echo "🧪 [5/5] Running functional tests..."
if [ -f "$PROJECT_ROOT/test/run_tests.sh" ]; then
    if bash "$PROJECT_ROOT/test/run_tests.sh"; then
        echo "✅ Functional tests passed"
    else
        echo "❌ Functional tests failed"
        exit 1
    fi
else
    echo "⚠️  No test runner found, skipping (non-blocking)"
fi

# 最终结果
echo ""
echo "=================================="
echo "✅ Phase 3 Static Checks: PASSED"
echo "=================================="
exit 0
```

**创建命令**:
```bash
cat > scripts/static_checks.sh << 'EOF'
[上述脚本内容]
EOF

chmod +x scripts/static_checks.sh
```

**验证**:
```bash
bash scripts/static_checks.sh
# 应该输出检查结果并返回0
```

#### Step 5.2: 创建scripts/pre_merge_audit.sh
**功能**: Phase 4阶段的合并前审计

**脚本内容**:
```bash
#!/usr/bin/env bash
# pre_merge_audit.sh - Phase 4 Pre-Merge Audit
# Version: 1.0.0
# Created: 2025-10-16

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔍 Phase 4: Pre-Merge Audit"
echo "==========================="

CRITICAL_ISSUES=0
MAJOR_ISSUES=0
MINOR_ISSUES=0

# 1. 配置完整性验证
echo "⚙️  [1/7] Checking configuration integrity..."

# 检查hooks注册
if [ ! -f "$PROJECT_ROOT/.claude/settings.json" ]; then
    echo "❌ CRITICAL: .claude/settings.json missing"
    ((CRITICAL_ISSUES++))
else
    HOOK_COUNT=$(jq '.hooks | to_entries[] | .value[]' "$PROJECT_ROOT/.claude/settings.json" 2>/dev/null | wc -l || echo "0")
    if [ "$HOOK_COUNT" -ne 17 ]; then
        echo "❌ CRITICAL: Expected 17 hooks, found $HOOK_COUNT"
        ((CRITICAL_ISSUES++))
    else
        echo "✅ Hook registration complete (17/17)"
    fi
fi

# 检查hook权限
UNEXECUTABLE_HOOKS=0
while IFS= read -r -d '' hook; do
    if [ ! -x "$hook" ]; then
        echo "❌ MAJOR: Hook not executable: $(basename "$hook")"
        ((MAJOR_ISSUES++))
        ((UNEXECUTABLE_HOOKS++))
    fi
done < <(find "$PROJECT_ROOT/.claude/hooks" -type f -name "*.sh" -print0 2>/dev/null)

if [ $UNEXECUTABLE_HOOKS -eq 0 ]; then
    echo "✅ All hooks are executable"
fi

# 2. 遗留问题扫描
echo ""
echo "🔎 [2/7] Scanning for unresolved issues..."

TODO_COUNT=$(grep -r "TODO" "$PROJECT_ROOT/.claude" "$PROJECT_ROOT/scripts" 2>/dev/null | wc -l || echo "0")
FIXME_COUNT=$(grep -r "FIXME" "$PROJECT_ROOT/.claude" "$PROJECT_ROOT/scripts" 2>/dev/null | wc -l || echo "0")

if [ "$TODO_COUNT" -gt 0 ]; then
    echo "⚠️  MINOR: Found $TODO_COUNT TODO comment(s)"
    ((MINOR_ISSUES++))
fi

if [ "$FIXME_COUNT" -gt 0 ]; then
    echo "❌ MAJOR: Found $FIXME_COUNT FIXME comment(s)"
    ((MAJOR_ISSUES++))
fi

# 3. 垃圾文档检测
echo ""
echo "📄 [3/7] Checking documentation cleanliness..."

ROOT_MD_COUNT=$(find "$PROJECT_ROOT" -maxdepth 1 -type f -name "*.md" | wc -l)
if [ "$ROOT_MD_COUNT" -gt 7 ]; then
    echo "❌ CRITICAL: Root directory has $ROOT_MD_COUNT .md files (limit: 7)"
    echo "   Allowed: README.md, CLAUDE.md, INSTALLATION.md, ARCHITECTURE.md,"
    echo "            CONTRIBUTING.md, CHANGELOG.md, LICENSE.md"
    ((CRITICAL_ISSUES++))
else
    echo "✅ Documentation structure clean ($ROOT_MD_COUNT/7 core docs)"
fi

# 4. 版本号一致性
echo ""
echo "🏷️  [4/7] Checking version consistency..."

if [ -f "$PROJECT_ROOT/VERSION" ]; then
    VERSION_FILE=$(cat "$PROJECT_ROOT/VERSION" | tr -d '\n')
else
    echo "⚠️  MINOR: VERSION file missing"
    VERSION_FILE="unknown"
    ((MINOR_ISSUES++))
fi

if [ -f "$PROJECT_ROOT/.claude/settings.json" ]; then
    SETTINGS_VERSION=$(jq -r '.version // "unknown"' "$PROJECT_ROOT/.claude/settings.json" 2>/dev/null)
else
    SETTINGS_VERSION="unknown"
fi

if [ "$VERSION_FILE" != "unknown" ] && [ "$SETTINGS_VERSION" != "unknown" ]; then
    if [ "$VERSION_FILE" != "$SETTINGS_VERSION" ]; then
        echo "❌ MAJOR: Version mismatch - VERSION: $VERSION_FILE, settings.json: $SETTINGS_VERSION"
        ((MAJOR_ISSUES++))
    else
        echo "✅ Version consistent: $VERSION_FILE"
    fi
fi

# 5. 代码模式一致性
echo ""
echo "🔄 [5/7] Checking code pattern consistency..."

# 检查所有hook是否使用set -euo pipefail
UNSAFE_SCRIPTS=0
while IFS= read -r -d '' script; do
    if ! grep -q "set -euo pipefail" "$script"; then
        echo "⚠️  MINOR: Missing 'set -euo pipefail' in $(basename "$script")"
        ((MINOR_ISSUES++))
        ((UNSAFE_SCRIPTS++))
    fi
done < <(find "$PROJECT_ROOT/.claude/hooks" "$PROJECT_ROOT/scripts" -type f -name "*.sh" -print0 2>/dev/null)

if [ $UNSAFE_SCRIPTS -eq 0 ]; then
    echo "✅ All scripts use safe error handling"
fi

# 6. 文档完整性
echo ""
echo "📚 [6/7] Checking documentation completeness..."

if [ ! -f "$PROJECT_ROOT/docs/REVIEW.md" ]; then
    echo "❌ CRITICAL: docs/REVIEW.md missing (required for Phase 4)"
    ((CRITICAL_ISSUES++))
else
    REVIEW_LINES=$(wc -l < "$PROJECT_ROOT/docs/REVIEW.md")
    if [ "$REVIEW_LINES" -lt 100 ]; then
        echo "❌ MAJOR: REVIEW.md too short ($REVIEW_LINES lines, minimum: 100)"
        ((MAJOR_ISSUES++))
    else
        echo "✅ REVIEW.md complete ($REVIEW_LINES lines)"
    fi
fi

# 7. Phase 0 Checklist验证
echo ""
echo "✅ [7/7] Verifying Phase 0 acceptance checklist..."

if [ -f "$PROJECT_ROOT/docs/P0_CHECKLIST.md" ]; then
    TOTAL_ITEMS=$(grep -c "^- \[" "$PROJECT_ROOT/docs/P0_CHECKLIST.md" || echo "0")
    CHECKED_ITEMS=$(grep -c "^- \[x\]" "$PROJECT_ROOT/docs/P0_CHECKLIST.md" || echo "0")

    if [ "$TOTAL_ITEMS" -eq 0 ]; then
        echo "⚠️  MINOR: P0 checklist is empty"
        ((MINOR_ISSUES++))
    elif [ "$CHECKED_ITEMS" -lt "$TOTAL_ITEMS" ]; then
        echo "❌ MAJOR: P0 checklist incomplete ($CHECKED_ITEMS/$TOTAL_ITEMS)"
        ((MAJOR_ISSUES++))
    else
        echo "✅ P0 checklist complete ($CHECKED_ITEMS/$TOTAL_ITEMS)"
    fi
else
    echo "⚠️  MINOR: P0_CHECKLIST.md not found"
    ((MINOR_ISSUES++))
fi

# 最终结果
echo ""
echo "==========================="
echo "📊 Audit Summary"
echo "==========================="
echo "🔴 Critical Issues: $CRITICAL_ISSUES"
echo "🟡 Major Issues: $MAJOR_ISSUES"
echo "⚪ Minor Issues: $MINOR_ISSUES"
echo ""

if [ $CRITICAL_ISSUES -gt 0 ]; then
    echo "❌ AUDIT FAILED: Critical issues must be resolved before merge"
    exit 1
elif [ $MAJOR_ISSUES -gt 0 ]; then
    echo "⚠️  AUDIT WARNING: Major issues found, review recommended"
    exit 1
else
    echo "✅ AUDIT PASSED: Ready for merge"
    exit 0
fi
```

**创建命令**:
```bash
cat > scripts/pre_merge_audit.sh << 'EOF'
[上述脚本内容]
EOF

chmod +x scripts/pre_merge_audit.sh
```

**验证**:
```bash
bash scripts/pre_merge_audit.sh
# 应该输出审计结果
```

### 修复方案 - Category B

#### Step 5.3: 标记Butler Mode脚本为"Planned"
在 `docs/BUTLER_MODE_PROPOSAL_v6.6.md` 中添加脚本状态表：

```markdown
### 📦 Script Implementation Status

| Script | Status | Location | Purpose |
|--------|--------|----------|---------|
| static_checks.sh | ✅ Implemented | scripts/ | Phase 3 quality gate |
| pre_merge_audit.sh | ✅ Implemented | scripts/ | Phase 4 pre-merge audit |
| memory_recall.sh | 📋 Planned (v6.6) | scripts/ | Butler记忆召回 |
| butler_mode_detector.sh | 📋 Planned (v6.6) | .claude/hooks/ | Butler模式检测 |
| butler_decision_recorder.sh | 📋 Planned (v6.6) | scripts/ | 决策记录器 |
| context_manager.sh | 📋 Planned (v6.6) | scripts/ | 上下文管理 |

**Important**:
- ✅ 已实现的脚本可立即使用
- 📋 计划中的脚本将在v6.6实现
- 请勿尝试运行标记为"Planned"的脚本
```

#### Step 5.4: 更新CLAUDE.md中的脚本引用
在`CLAUDE.md` Phase 3和Phase 4描述中，确认脚本路径正确：

```markdown
❌ 错误: "运行 bash scripts/static_checks.sh（如果没有此脚本，跳过）"
✅ 正确: "**必须执行**: bash scripts/static_checks.sh"

❌ 错误: "运行 bash scripts/pre_merge_audit.sh（可选）"
✅ 正确: "**必须执行**: bash scripts/pre_merge_audit.sh"
```

### 验收标准
- [ ] `scripts/static_checks.sh` 存在且可执行
- [ ] `scripts/pre_merge_audit.sh` 存在且可执行
- [ ] 两个脚本运行成功（返回0或有清晰的错误提示）
- [ ] Butler Mode相关脚本标记为"Planned"
- [ ] CLAUDE.md中脚本路径正确
- [ ] 文档中所有脚本引用有状态标记（✅实现 or 📋计划）

### 预计时间
**2小时** (static_checks.sh编写40分钟 + pre_merge_audit.sh编写50分钟 + 测试20分钟 + 文档更新10分钟)

---

## 📅 Phase 2-5 Execution Plan

### Phase 2: Implementation（预计7小时）
**时间安排**:
- Hour 1: Issue 1 修复（Agent数量）
- Hour 2-3.5: Issue 2 修复（Hook数量）
- Hour 4: Issue 3 修复（Phase编号）
- Hour 5-6: Issue 4 修复（Butler Mode）
- Hour 7-9: Issue 5 修复（Scripts创建）

**并行策略**:
- Issue 1, 3可并行（文本替换）
- Issue 2需要单独处理（Hook清单整理）
- Issue 4, 5可部分并行（文件重命名 vs 脚本创建）

**Commits策略**:
```bash
git commit -m "fix(docs): correct agent count to 4-6-8 principle

- Update DECISION_TREE.md agent selection table
- Fix all 3-agent references to 4-agent
- Update decision_flow.mermaid with explicit branches
- Verify consistency with smart_agent_selector.sh

Issue: #1 Agent Count Inconsistency
Phase: Phase 2 (Implementation)"

git commit -m "fix(docs): update hook count from 15 to 17

- Add complete 17-hook inventory to Part 3
- Update all references in DECISION_TREE.md
- Verify with settings.json
- Add functional descriptions for each hook

Issue: #2 Hook Count Error
Phase: Phase 2 (Implementation)"

# ... 类似地为Issue 3, 4, 5创建commits
```

### Phase 3: Testing（预计2小时）
**测试类型**:
1. **验证测试** (30分钟)
   - 运行所有验收标准中的grep命令
   - 检查脚本可执行性
   - 验证文件重命名成功

2. **交叉引用测试** (30分钟)
   - 检查DECISION_TREE.md与CLAUDE.md一致性
   - 验证所有内部链接有效
   - 确认术语使用统一

3. **脚本功能测试** (45分钟)
   - 运行`bash scripts/static_checks.sh`
   - 运行`bash scripts/pre_merge_audit.sh`
   - 修复发现的任何问题

4. **文档可读性测试** (15分钟)
   - 快速通读所有修改部分
   - 确认语句通顺
   - 检查markdown格式正确

**测试命令集**:
```bash
# Issue 1验证
grep -c "简单任务：4个Agent" docs/DECISION_TREE.md  # 应该>0
grep -c "3个Agent" docs/DECISION_TREE.md | grep "^0$"  # 应该是0（除了可能的历史记录）

# Issue 2验证
grep -c "17个active hooks" docs/DECISION_TREE.md  # 应该>=4
jq '.hooks | to_entries[] | .value[]' .claude/settings.json | wc -l  # 应该=17

# Issue 3验证
grep "Phase 6" CLAUDE.md | grep -v "Phase 0-5"  # 应该无结果
grep "P9" CLAUDE.md  # 应该无结果

# Issue 4验证
test -f docs/BUTLER_MODE_PROPOSAL_v6.6.md && echo "✅ File renamed"
head -5 docs/BUTLER_MODE_PROPOSAL_v6.6.md | grep "NOT IMPLEMENTED"  # 应该有结果

# Issue 5验证
test -x scripts/static_checks.sh && echo "✅ static_checks.sh exists"
test -x scripts/pre_merge_audit.sh && echo "✅ pre_merge_audit.sh exists"
bash scripts/static_checks.sh
bash scripts/pre_merge_audit.sh
```

### Phase 4: Review（预计1.5小时）
**人工审查要点**:
1. **逻辑正确性** (30分钟)
   - 4-6-8原则描述逻辑清晰
   - Hook功能描述准确
   - Phase vs Steps区分清楚
   - Butler Mode提案vs实现明确分离

2. **代码一致性** (30分钟)
   - DECISION_TREE.md与CLAUDE.md术语一致
   - 所有Agent数量引用统一为4-6-8
   - Hook数量统一为17
   - 脚本实现符合CLAUDE.md描述

3. **文档完整性** (30分钟)
   - 生成完整的REVIEW.md（>100行）
   - 包含所有5个Issue的修复确认
   - 列出所有修改的文件
   - 记录测试结果

**REVIEW.md模板**:
```markdown
# Code Review Report - Documentation Fix

## Review Summary
- **Branch**: docs/decision-tree-documentation
- **Reviewer**: Claude Code (code-reviewer agent)
- **Date**: 2025-10-16
- **Scope**: 5 Critical Issues in documentation
- **Verdict**: ✅ APPROVED / ⚠️ APPROVED WITH COMMENTS / ❌ CHANGES REQUESTED

## Issues Reviewed

### Issue 1: Agent Count Inconsistency ✅
- [x] All "3-agent" references updated to "4-agent"
- [x] Agent selection table corrected
- [x] decision_flow.mermaid updated with explicit branches
- [x] Consistency verified with smart_agent_selector.sh
- **Verdict**: ✅ Resolved

### Issue 2: Hook Count Error ✅
- [x] All "15 hooks" updated to "17 hooks"
- [x] Complete 17-hook inventory added
- [x] Each hook has functional description
- [x] Verified with settings.json
- **Verdict**: ✅ Resolved

### Issue 3: Phase Numbering Confusion ✅
- [x] "Phase 6" references removed
- [x] Terminology clarification added
- [x] Version evolution table added
- [x] Steps vs Phases clearly distinguished
- **Verdict**: ✅ Resolved

### Issue 4: Butler Mode References ✅
- [x] File renamed to BUTLER_MODE_PROPOSAL_v6.6.md
- [x] "NOT IMPLEMENTED" banner added
- [x] Current vs Proposed comparison table added
- [x] All未实现功能标记为[Proposed]
- **Verdict**: ✅ Resolved

### Issue 5: Non-existent Scripts ✅
- [x] static_checks.sh created and tested
- [x] pre_merge_audit.sh created and tested
- [x] Butler Mode scripts marked as "Planned"
- [x] Script status table added
- **Verdict**: ✅ Resolved

## Files Modified
1. docs/DECISION_TREE.md - 修复Issues 1, 2, 3
2. docs/BUTLER_MODE_IMPACT_ANALYSIS.md → docs/BUTLER_MODE_PROPOSAL_v6.6.md - 修复Issue 4
3. docs/diagrams/decision_flow.mermaid - 修复Issue 1
4. CLAUDE.md - 修复Issue 3
5. scripts/static_checks.sh - 新建（Issue 5）
6. scripts/pre_merge_audit.sh - 新建（Issue 5）

## Test Results
- ✅ All verification commands passed
- ✅ Scripts executable and functional
- ✅ Cross-reference consistency verified
- ✅ Markdown formatting valid

## Recommendations
- Consider adding automated doc consistency checker (long-term)
- Update .github/workflows to run static_checks.sh in CI
- Add pre_merge_audit.sh to PR template checklist

## Approval
**Status**: ✅ APPROVED
**Ready for Phase 5**: Yes
**Blockers**: None
```

### Phase 5: Release & Monitor（预计30分钟）
**发布清单**:
1. **文档更新** (10分钟)
   - [ ] 更新CHANGELOG.md记录本次修复
   - [ ] 确认DECISION_TREE.md版本号
   - [ ] 添加修复说明到commit message

2. **最终提交** (10分钟)
   ```bash
   git add docs/DECISION_TREE.md \
           docs/BUTLER_MODE_PROPOSAL_v6.6.md \
           docs/diagrams/decision_flow.mermaid \
           CLAUDE.md \
           scripts/static_checks.sh \
           scripts/pre_merge_audit.sh \
           docs/REVIEW.md

   git commit -m "$(cat <<'EOF'
   docs: fix 5 critical issues in decision tree documentation

   ## Issues Fixed
   1. Agent count corrected to 4-6-8 principle
   2. Hook count updated to 17 (was 15)
   3. Phase numbering clarified (Steps vs Phases)
   4. Butler Mode marked as v6.6 proposal
   5. Created missing static_checks.sh and pre_merge_audit.sh

   ## Root Cause
   Hub-Spoke Update Failure: v6.3 refactoring updated CLAUDE.md
   but didn't propagate to DECISION_TREE.md

   ## Verification
   - All acceptance criteria passed
   - Scripts tested and functional
   - REVIEW.md generated
   - Cross-reference consistency verified

   Phase: Phase 5 (Release)
   Branch: docs/decision-tree-documentation

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

3. **Phase 0 Checklist Final Verification** (10分钟)
   - [ ] 逐项对照P0_CHECKLIST.md验证
   - [ ] 所有33个验收标准全部✅
   - [ ] 生成验收报告

**CHANGELOG.md条目**:
```markdown
## [6.5.0] - 2025-10-16

### Fixed
- **Documentation Accuracy** (Critical Issues #1-5)
  - Corrected agent count from 3-4 to 4-6-8 principle (#1)
  - Updated hook count from 15 to 17 with complete inventory (#2)
  - Clarified Phase numbering (removed "Phase 6" confusion) (#3)
  - Marked Butler Mode as v6.6 proposal (added NOT IMPLEMENTED banner) (#4)
  - Created missing scripts: static_checks.sh, pre_merge_audit.sh (#5)
- **Root Cause**: Hub-Spoke Update Failure pattern identified and fixed
- **Impact**: DECISION_TREE.md now 100% consistent with CLAUDE.md and code

### Added
- scripts/static_checks.sh - Phase 3 quality gate automation
- scripts/pre_merge_audit.sh - Phase 4 pre-merge auditing
- Complete 17-hook inventory in DECISION_TREE.md
- Terminology clarification: Steps vs Phases
- Version evolution table (v6.3: 8-Phase → 6-Phase)

### Changed
- docs/BUTLER_MODE_IMPACT_ANALYSIS.md → docs/BUTLER_MODE_PROPOSAL_v6.6.md
- Updated all agent selection references to 4-6-8
- Enhanced decision_flow.mermaid with explicit agent branches
```

---

## 🎯 Overall Success Criteria

### Documentation Quality
- [ ] ✅ No factual errors (agent counts, hook counts, phase numbers)
- [ ] ✅ All scripts referenced in docs exist and are executable
- [ ] ✅ Proposed features clearly distinguished from implemented features
- [ ] ✅ Cross-document consistency (DECISION_TREE ↔ CLAUDE.md ↔ Code)
- [ ] ✅ Version evolution clearly documented

### Usability
- [ ] ✅ User can follow decision tree without confusion
- [ ] ✅ All verification commands work as documented
- [ ] ✅ No broken links or missing files
- [ ] ✅ Terminology used consistently throughout

### Maintainability
- [ ] ✅ Future updates to CLAUDE.md will trigger doc review
- [ ] ✅ Scripts have clear purpose and are well-commented
- [ ] ✅ Changes logged in CHANGELOG.md
- [ ] ✅ REVIEW.md provides clear audit trail

### Alignment with Phase 0 Checklist
- [ ] ✅ All 33 acceptance criteria from P0_CHECKLIST.md satisfied
- [ ] ✅ No scope creep (only fixing 5 Critical Issues)
- [ ] ✅ Time budget respected (8-12 hours target)

---

## 📊 Time Tracking

| Phase | Planned | Actual | Status |
|-------|---------|--------|--------|
| Phase -1 | 5 min | - | ✅ Completed |
| Phase 0 | 30 min | - | ✅ Completed |
| Phase 1 | 1 hour | - | ⏳ In Progress |
| Phase 2 | 7 hours | - | ⏸️ Pending |
| Phase 3 | 2 hours | - | ⏸️ Pending |
| Phase 4 | 1.5 hours | - | ⏸️ Pending |
| Phase 5 | 30 min | - | ⏸️ Pending |
| **Total** | **12 hours** | - | |

---

## 🔗 References

### Source of Truth Documents
- `.claude/settings.json` - Hook registration (17 hooks)
- `.claude/hooks/smart_agent_selector.sh` - Agent selection logic (4-6-8)
- `CLAUDE.md` - System configuration and rules
- `WORKFLOW.md` - 6-Phase system definition

### Issue Tracking
- Code Review Report: `code_review_results_*.md` (in .temp/analysis/)
- P0 Acceptance Checklist: `P0_CHECKLIST.md`
- Root Cause Analysis: Phase 0 error-detective report

### Related PRs
- (This will be the PR for this fix)
- Previous: PR #XX (v6.3 refactoring - source of inconsistency)

---

**Plan Status**: ✅ Complete
**Next Step**: Execute Phase 2 - Implementation
**Created**: 2025-10-16
**Author**: Claude Code (Phase 1)
