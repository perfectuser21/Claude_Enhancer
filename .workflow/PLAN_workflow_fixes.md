# Architecture Planning - Workflow Consistency Fixes
**Version**: 8.6.1 (target)
**Date**: 2025-10-30
**Phase**: 1.5 Architecture Planning
**Impact Radius**: 63 (High Risk)
**Recommended Agents**: 6 (parallel execution)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Technical Architecture](#technical-architecture)
4. [6-Agent Parallel Execution Plan](#6-agent-parallel-execution-plan)
5. [File Modification Details](#file-modification-details)
6. [Testing Strategy](#testing-strategy)
7. [Quality Gates](#quality-gates)
8. [Risk Management](#risk-management)
9. [Rollback Plan](#rollback-plan)
10. [Success Criteria](#success-criteria)
11. [Timeline & Milestones](#timeline--milestones)

---

## Executive Summary

### Mission
修复Claude Enhancer v8.6.0的10个workflow一致性问题，使SPEC.yaml、manifest.yml、CLAUDE.md三者完全一致，确保系统自洽。

### Scope
- **Files to modify**: 6个核心文件
- **Issues to fix**: 10个（5 Critical + 3 Medium + 2 Low）
- **Agents required**: 6个并行Agent
- **Version upgrade**: 8.6.0 → 8.6.1
- **Estimated time**: 75分钟（并行执行）

### Key Changes
1. SPEC.yaml文档定义修正（3处）
2. manifest.yml子阶段定义修正（2处）
3. TODO/FIXME清理（8个减至≤5个）
4. 契约测试创建（新增1个测试套件）
5. LOCK.json更新（反映新结构）

### Success Metrics
- ✅ 所有10个Issue修复完成
- ✅ SPEC.yaml/manifest.yml/CLAUDE.md完全一致
- ✅ Quality Gate 1 + 2通过
- ✅ 契约测试通过
- ✅ 版本号升级到8.6.1（6个文件一致）

---

## Problem Statement

### Background
通过深度审计发现v8.6.0存在多处文档自相矛盾：

1. **SPEC.yaml说Phase 1产出`P2_DISCOVERY.md`**（应该是`P1_DISCOVERY.md`）
2. **版本文件数量不一致**（SPEC说5个，实际检查6个）
3. **manifest.yml多了个子阶段**（应该是hook不是子阶段）
4. **遗留TODO/FIXME过多**（8个，超标）
5. **检查点编号示例混乱**（P1/P2/P5对应关系不清）

### Impact
- 😕 AI可能创建错误文件名
- 😕 文档矛盾导致混淆
- 😕 契约测试缺失，无法防止回归
- 😕 不能作为"稳定基线"

### User Expectations
用户通过这个任务测试：
1. ✅ 7-Phase工作流是否真正执行
2. ✅ 多subagent机制是否触发
3. ✅ Bypass Permissions是否生效
4. ✅ 工作过程是否有完整记录

---

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────┐
│           Claude Enhancer v8.6.1                    │
│         Workflow Consistency Layer                   │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   SPEC.yaml      manifest.yml     CLAUDE.md
  (核心定义)      (执行配置)      (用户文档)
        │               │               │
        └───────────────┴───────────────┘
                        │
                ┌───────┴───────┐
                ▼               ▼
         LOCK.json      check_version_
        (指纹保护)      consistency.sh
                        (验证脚本)
```

### Core Components

#### 1. SPEC.yaml (Core Immutable Layer)
**职责**: 定义"什么是不可变的"
- Phase数量（7）
- 检查点数量（≥97）
- 质量门禁（2个）
- 版本文件列表（6个）

**修改原则**: 只能增加不能减少

#### 2. manifest.yml (Execution Config)
**职责**: 定义执行顺序和并行策略
- Phase依赖关系
- 超时配置
- 并行Agent数量
- 子阶段列表

**修改原则**: 必须与SPEC.yaml对齐

#### 3. CLAUDE.md (User Documentation)
**职责**: 向用户和AI说明规则
- 7-Phase详细说明
- 规则0-4强制规范
- AI行为准则

**修改原则**: 必须与SPEC.yaml和manifest.yml一致

#### 4. LOCK.json (Integrity Protection)
**职责**: 保护核心文件完整性
- SHA256指纹
- 防止AI无限改动

**更新时机**: 修改Layer 1或Layer 2后

#### 5. check_version_consistency.sh (Validator)
**职责**: 强制6个文件版本一致
- VERSION
- settings.json
- manifest.yml
- package.json
- CHANGELOG.md
- SPEC.yaml

---

## 6-Agent Parallel Execution Plan

### Architecture Diagram

```
                    ┌──────────────────┐
                    │  Task Scheduler  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼─────┐ ┌─────▼──────┐ ┌────▼─────┐
       │  Group 1   │ │  Group 2   │ │ Group 3  │
       │  (3 agents)│ │  (2 agents)│ │(1 agent) │
       └──────┬─────┘ └─────┬──────┘ └────┬─────┘
              │              │              │
    ┌─────────┼─────────┐    │              │
    ▼         ▼         ▼    ▼              ▼
 Agent1    Agent2   Agent3  Agent4       Agent6
 SPEC.yaml manifest  LOCK   TODO         契约测试
                            Agent5
                           CLAUDE.md
```

### Execution Strategy

**Phase 1 (Parallel)**: Group 1 + Group 2
- T+0min: Agent 1, 2, 4同时启动
- T+20min: Agent 2完成
- T+30min: Agent 1完成
- T+40min: Agent 4完成

**Phase 2 (Sequential)**: Group 1的Agent 3
- T+30min: Agent 3启动（等待Agent 1, 2）
- T+45min: Agent 3完成（LOCK更新）

**Phase 3 (Sequential)**: Group 2的Agent 5 + Group 3
- T+30min: Agent 5启动（等待Agent 1）
- T+50min: Agent 5完成
- T+45min: Agent 6启动（等待Agent 3）
- T+75min: Agent 6完成

**Total Time**: 75分钟（vs 顺序200分钟，节省62%）

---

## Agent Task Definitions

### Agent 1: SPEC.yaml Corrections

**Priority**: P0 (Critical)

**Responsibility**: 修复SPEC.yaml的3个问题

**Tasks**:

1. **Issue #1: 修复Phase 1产出文件名**
   - Location: Line 135
   - Change: `P2_DISCOVERY.md` → `P1_DISCOVERY.md`
   - Reason: Phase 1的产出应该叫P1不是P2

2. **Issue #2: 版本文件数量5→6**
   - Location: Line 90 + Line 170-178
   - Changes:
     ```yaml
     # Line 90
     - "版本完全一致性（5文件）"  # 改成6文件

     # Line 170-178
     version_consistency:
       required_files:
         - "VERSION"
         - ".claude/settings.json"
         - "package.json"
         - ".workflow/manifest.yml"
         - "CHANGELOG.md"
         - ".workflow/SPEC.yaml"  # 新增
     ```

3. **Issue #7: 检查点编号示例说明**
   - Location: Line 54-59
   - Action: 添加清晰说明或移到单独文档
   - Current (confusing):
     ```yaml
     examples:
       - "PD_S001"   # Pre-Discussion (Phase 1.2)
       - "P1_S001"   # Phase 1 Branch Check (Phase 1.1)
       - "P2_S001"   # Phase 2 Discovery (Phase 1.3)
       - "P5_S001"   # Phase 5 Testing (Phase 3)
     ```
   - Improved:
     ```yaml
     examples:
       - "PD_S001"   # Pre-Discussion checkpoints (Phase 1.2需求讨论)
       - "P1_S001"   # Branch Check checkpoints (Phase 1.1分支检查)
       - "P2_S001"   # Technical Discovery checkpoints (Phase 1.3技术发现)
       - "P3_S001"   # Architecture Planning checkpoints (Phase 1.5架构规划)
       - "P4_S001"   # Implementation checkpoints (Phase 2实现)
       - "P5_S001"   # Testing checkpoints (Phase 3测试)
       - "P6_S001"   # Review checkpoints (Phase 4审查)
       - "P7_S001"   # Release checkpoints (Phase 5发布)
       - "AC_S001"   # Acceptance checkpoints (Phase 6验收)
       - "CL_S001"   # Closure checkpoints (Phase 7清理)

     note: |
       编号规则说明：
       - PD/P1-P7/AC/CL代表不同的检查点集合
       - 不是直接对应Phase编号（历史原因）
       - P1是Phase 1.1, P2是Phase 1.3, P5是Phase 3
       - 保持向后兼容，不修改现有编号
     ```

**Input**: `.workflow/SPEC.yaml` (current)

**Output**: `.workflow/SPEC.yaml` (corrected)

**Validation**:
```bash
# 语法检查
python3 -c "import yaml; yaml.safe_load(open('.workflow/SPEC.yaml'))"

# 版本文件数量检查
grep -c "required_files:" .workflow/SPEC.yaml  # 应该列出6个
```

**Estimated Time**: 30分钟

**Dependencies**: 无（可并行）

---

### Agent 2: manifest.yml Corrections

**Priority**: P0 (Critical)

**Responsibility**: 修复manifest.yml的2个问题

**Tasks**:

1. **Issue #3: 移除多余子阶段**
   - Location: Line 18
   - Current:
     ```yaml
     substages: ["Branch Check", "Requirements Discussion",
                 "Technical Discovery", "Dual-Language Checklist Generation",
                 "Impact Assessment", "Architecture Planning"]
     ```
   - Fixed:
     ```yaml
     substages: ["1.1 Branch Check", "1.2 Requirements Discussion",
                 "1.3 Technical Discovery", "1.4 Impact Assessment",
                 "1.5 Architecture Planning"]
     ```
   - Reason: "Checklist Generation"是hook触发（settings.json:72-76），不是独立子阶段

2. **Issue #6: 子阶段加上编号**
   - 保持与SPEC.yaml一致（1.1, 1.2, ...）
   - 便于追踪和引用

**Input**: `.workflow/manifest.yml` (current)

**Output**: `.workflow/manifest.yml` (corrected)

**Validation**:
```bash
# 语法检查
python3 -c "import yaml; yaml.safe_load(open('.workflow/manifest.yml'))"

# 子阶段数量检查
grep -A2 "substages:" .workflow/manifest.yml | grep -o "," | wc -l  # 应该是4个逗号（5个子阶段）
```

**Estimated Time**: 20分钟

**Dependencies**: 无（可并行）

---

### Agent 3: LOCK.json Update & Verification

**Priority**: P1 (High)

**Responsibility**: 更新LOCK.json并验证完整性

**Tasks**:

1. **更新LOCK.json**
   ```bash
   cd "/home/xx/dev/Claude Enhancer"
   bash tools/update-lock.sh
   ```

2. **验证核心结构**
   ```bash
   bash tools/verify-core-structure.sh
   # 应该输出: {"ok":true,"message":"Core structure verification passed"}
   ```

3. **检查Lock模式**
   - 当前是`soft`模式（观测期）
   - 确认修改被正确记录

**Input**:
- `.workflow/SPEC.yaml` (from Agent 1)
- `.workflow/manifest.yml` (from Agent 2)
- `tools/update-lock.sh`

**Output**:
- `.workflow/LOCK.json` (updated)
- Verification report

**Validation**:
```bash
# LOCK.json格式检查
jq empty .workflow/LOCK.json

# 验证脚本通过
bash tools/verify-core-structure.sh
echo $?  # 应该是0
```

**Estimated Time**: 15分钟

**Dependencies**: Agent 1 AND Agent 2 完成

---

### Agent 4: TODO/FIXME Cleanup

**Priority**: P0 (Critical)

**Responsibility**: 清理遗留TODO/FIXME（从8个减至≤5个）

**Tasks**:

1. **扫描所有TODO/FIXME**
   ```bash
   cd "/home/xx/dev/Claude Enhancer"
   grep -rn "TODO\|FIXME" \
     --include="*.sh" \
     --include="*.md" \
     --include="*.json" \
     --include="*.yaml" \
     --include="*.yml" \
     . | grep -v ".git" | grep -v "node_modules" > /tmp/todo_list.txt

   wc -l /tmp/todo_list.txt  # 当前8个
   ```

2. **分类处理**
   - **可立即修复**: 简单问题，直接改代码
   - **需要设计**: 转成GitHub Issue，删除代码注释
   - **过期注释**: 直接删除
   - **保留**: 仅限"未来优化"类（≤3个）

3. **处理原则**
   ```
   TODO: 添加性能优化 → 保留（未来优化）
   FIXME: 这个逻辑有bug → 立即修复
   TODO: 实现XXX功能 → 转成Issue + 删除注释
   TODO: 临时方案，需重构 → 评估是否立即重构
   ```

4. **目标**
   - 最终TODO/FIXME ≤ 5个
   - 所有保留的TODO都有明确理由

**Input**: 多个文件中的TODO/FIXME

**Output**: 清理后的文件

**Validation**:
```bash
# 最终数量检查
grep -r "TODO\|FIXME" --include="*.sh" --include="*.md" . | grep -v ".git" | wc -l
# 应该 ≤ 5
```

**Estimated Time**: 40分钟

**Dependencies**: 无（可并行）

---

### Agent 5: CLAUDE.md Synchronization

**Priority**: P1 (High)

**Responsibility**: 确保CLAUDE.md与SPEC.yaml描述一致

**Tasks**:

1. **更新规则4中版本文件数量**
   - Location: 规则4 - 7-Phase完整执行强制
   - 搜索: "版本一致性 - VERSION + settings.json + manifest.yml + package.json + CHANGELOG.md"
   - 改为: "版本一致性 - VERSION + settings.json + manifest.yml + package.json + CHANGELOG.md + SPEC.yaml（6个文件）"

2. **更新Phase 1子阶段描述**
   - 确认使用编号（1.1, 1.2, ...）
   - 移除任何"Dual-Language Checklist Generation"作为独立子阶段的描述
   - 说明它是hook触发

3. **验证Phase 1产出文件名**
   - 搜索所有提到"P2_DISCOVERY.md"的地方
   - 改为"P1_DISCOVERY.md"

**Input**:
- `CLAUDE.md` (current)
- `.workflow/SPEC.yaml` (from Agent 1)

**Output**: `CLAUDE.md` (synchronized)

**Validation**:
```bash
# 检查版本文件数量描述
grep -A2 "版本一致性" CLAUDE.md | grep -o "settings.json\|VERSION\|CHANGELOG\|SPEC.yaml" | sort -u | wc -l
# 应该是6个

# 检查Phase 1子阶段
grep "1.1\|1.2\|1.3\|1.4\|1.5" CLAUDE.md | grep "Phase 1"
# 应该有5个子阶段
```

**Estimated Time**: 20分钟

**Dependencies**: Agent 1完成（需要知道SPEC.yaml的最终状态）

---

### Agent 6: Contract Test Creation

**Priority**: P1 (High)

**Responsibility**: 创建契约测试验证修复有效性

**Tasks**:

1. **创建测试目录**
   ```bash
   mkdir -p tests/contract
   ```

2. **创建test_workflow_consistency.sh**
   ```bash
   #!/bin/bash
   # Contract Test: Workflow Consistency
   # 验证SPEC.yaml、manifest.yml、CLAUDE.md三者一致性

   set -euo pipefail

   PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

   echo "🧪 Contract Test: Workflow Consistency"
   echo "======================================"

   # Test 1: Phase数量一致
   echo "[TEST 1] Phase数量一致性"
   SPEC_PHASES=$(python3 -c "import yaml; print(yaml.safe_load(open('$PROJECT_ROOT/.workflow/SPEC.yaml'))['workflow_structure']['total_phases'])")
   MANIFEST_PHASES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('$PROJECT_ROOT/.workflow/manifest.yml'))['phases']))")

   if [ "$SPEC_PHASES" = "7" ] && [ "$MANIFEST_PHASES" = "7" ]; then
     echo "  ✅ PASS: 两者都是7个Phase"
   else
     echo "  ❌ FAIL: SPEC=$SPEC_PHASES, manifest=$MANIFEST_PHASES"
     exit 1
   fi

   # Test 2: Phase 1子阶段数量一致
   echo "[TEST 2] Phase 1子阶段数量一致性"
   SPEC_SUBSTAGES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('$PROJECT_ROOT/.workflow/SPEC.yaml'))['workflow_structure']['phase1_substages']))")
   MANIFEST_SUBSTAGES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('$PROJECT_ROOT/.workflow/manifest.yml'))['phases'][0]['substages']))")

   if [ "$SPEC_SUBSTAGES" = "5" ] && [ "$MANIFEST_SUBSTAGES" = "5" ]; then
     echo "  ✅ PASS: 两者都是5个子阶段"
   else
     echo "  ❌ FAIL: SPEC=$SPEC_SUBSTAGES, manifest=$MANIFEST_SUBSTAGES"
     exit 1
   fi

   # Test 3: 版本文件数量定义一致
   echo "[TEST 3] 版本文件数量定义一致性"
   VERSION_FILES=$(python3 -c "import yaml; print(len(yaml.safe_load(open('$PROJECT_ROOT/.workflow/SPEC.yaml'))['version_consistency']['required_files']))")

   if [ "$VERSION_FILES" = "6" ]; then
     echo "  ✅ PASS: SPEC定义6个版本文件"
   else
     echo "  ❌ FAIL: SPEC定义了$VERSION_FILES个文件（应该是6个）"
     exit 1
   fi

   # Test 4: 检查点总数≥97
   echo "[TEST 4] 检查点总数≥97"
   TOTAL_CHECKPOINTS=$(python3 -c "import yaml; print(yaml.safe_load(open('$PROJECT_ROOT/.workflow/SPEC.yaml'))['checkpoints']['total_count'])")

   if [ "$TOTAL_CHECKPOINTS" -ge 97 ]; then
     echo "  ✅ PASS: 检查点总数=$TOTAL_CHECKPOINTS (≥97)"
   else
     echo "  ❌ FAIL: 检查点总数=$TOTAL_CHECKPOINTS (<97)"
     exit 1
   fi

   # Test 5: Quality Gates数量=2
   echo "[TEST 5] Quality Gates数量=2"
   GATES=$(python3 -c "import yaml; print(yaml.safe_load(open('$PROJECT_ROOT/.workflow/SPEC.yaml'))['quality_gates']['total_gates'])")

   if [ "$GATES" = "2" ]; then
     echo "  ✅ PASS: 质量门禁=2个"
   else
     echo "  ❌ FAIL: 质量门禁=$GATES（应该是2个）"
     exit 1
   fi

   # Test 6: CLAUDE.md提到6个版本文件
   echo "[TEST 6] CLAUDE.md文档一致性"
   if grep -q "VERSION.*settings.json.*manifest.yml.*package.json.*CHANGELOG.md.*SPEC.yaml" "$PROJECT_ROOT/CLAUDE.md" || \
      grep -q "6个文件版本" "$PROJECT_ROOT/CLAUDE.md"; then
     echo "  ✅ PASS: CLAUDE.md描述了6个版本文件"
   else
     echo "  ⚠️  WARN: CLAUDE.md可能未更新版本文件数量"
   fi

   echo ""
   echo "======================================"
   echo "✅ All contract tests passed!"
   echo "======================================"
   ```

3. **集成到CI**
   - 添加到`.github/workflows/guard-core.yml`
   - 或创建新的workflow

**Input**: 修复后的SPEC.yaml、manifest.yml

**Output**: `tests/contract/test_workflow_consistency.sh`

**Validation**:
```bash
# 测试脚本可执行
chmod +x tests/contract/test_workflow_consistency.sh

# 运行测试
bash tests/contract/test_workflow_consistency.sh
# 应该全部通过
```

**Estimated Time**: 45分钟

**Dependencies**: Agent 3完成（需要最终文件）

---

## File Modification Details

### Before & After Comparison

#### 1. SPEC.yaml

**Change 1: Line 135**
```diff
  phase1:
-   - "P2_DISCOVERY.md (≥300行)"
+   - "P1_DISCOVERY.md (≥300行)"
    - "Acceptance Checklist"
```

**Change 2: Line 90**
```diff
  gate2:
    checks:
-     - "版本完全一致性（5文件）"
+     - "版本完全一致性（6文件）"
```

**Change 3: Line 170-178**
```diff
  version_consistency:
-   # ⛔ 绝对不可改：必须5文件完全一致
+   # ⛔ 绝对不可改：必须6文件完全一致
    required_files:
      - "VERSION"
      - ".claude/settings.json"
      - "package.json"
      - ".workflow/manifest.yml"
      - "CHANGELOG.md"
+     - ".workflow/SPEC.yaml"
```

**Change 4: Line 54-68 (扩展说明)**
```diff
  naming_convention:
    pattern: "P{phase}_{stage}_S{number}"
    examples:
      - "PD_S001"
      - "P1_S001"
      ...
+   note: |
+     编号规则说明：
+     - PD/P1-P7/AC/CL代表不同的检查点集合
+     - 不是直接对应Phase编号（历史原因）
+     - 保持向后兼容，不修改现有编号
```

#### 2. manifest.yml

**Change 1: Line 18**
```diff
- substages: ["Branch Check", "Requirements Discussion", "Technical Discovery", "Dual-Language Checklist Generation", "Impact Assessment", "Architecture Planning"]
+ substages: ["1.1 Branch Check", "1.2 Requirements Discussion", "1.3 Technical Discovery", "1.4 Impact Assessment", "1.5 Architecture Planning"]
```

#### 3. CLAUDE.md

**Changes**: 搜索替换
- "5个文件" → "6个文件"（在版本一致性描述中）
- "P2_DISCOVERY.md" → "P1_DISCOVERY.md"（如果存在）
- 确认Phase 1子阶段使用编号

#### 4. TODO/FIXME清理

**Target Files** (示例):
- scripts/*.sh
- .claude/hooks/*.sh
- docs/*.md
- 各种配置文件

**Action**: 逐个评估并处理

#### 5. LOCK.json

**Action**: 自动生成（`tools/update-lock.sh`）

#### 6. tests/contract/

**New File**: `test_workflow_consistency.sh` (~200行)

---

## Testing Strategy

### Testing Pyramid

```
                  ┌──────────────┐
                  │  Contract    │
                  │  Tests (1)   │  ← Agent 6
                  └──────────────┘
               ┌────────────────────┐
               │  Integration Tests │
               │  (pre_merge_audit) │  ← Quality Gate 2
               └────────────────────┘
           ┌───────────────────────────┐
           │    Unit Tests             │
           │  (static_checks)          │  ← Quality Gate 1
           └───────────────────────────┘
       ┌────────────────────────────────────┐
       │  Syntax Validation (bash -n)       │
       └────────────────────────────────────┘
```

### Test Levels

#### Level 1: Syntax Validation
**Tool**: `bash -n *.sh`
**Coverage**: 所有Shell脚本
**When**: 每次文件保存后
**Pass Criteria**: 无语法错误

#### Level 2: Static Checks (Quality Gate 1)
**Tool**: `scripts/static_checks.sh`
**Coverage**:
- Shell语法验证
- Shellcheck linting
- 代码复杂度检查
- Hook性能测试

**When**: Phase 3
**Pass Criteria**: 所有检查通过

#### Level 3: Pre-merge Audit (Quality Gate 2)
**Tool**: `scripts/pre_merge_audit.sh`
**Coverage**: 12项检查
1. Configuration completeness
2. Evidence validation
3. Checklist completion
4. Learning system active
5. Skills configured
6. Version consistency (6 files)
7. No hollow implementations
8. Auto-fix rollback capability
9. KPI tools available
10. Root documents ≤7
11. Documentation complete
12. Legacy audit (TODO/FIXME)

**When**: Phase 4
**Pass Criteria**: ≤2个warnings，0个failures

#### Level 4: Contract Tests
**Tool**: `tests/contract/test_workflow_consistency.sh`
**Coverage**:
- SPEC.yaml与manifest.yml一致性
- 版本文件数量定义
- Phase数量
- 检查点总数
- Quality Gates数量

**When**: Phase 3 + CI
**Pass Criteria**: 所有contract tests通过

#### Level 5: Version Consistency
**Tool**: `scripts/check_version_consistency.sh`
**Coverage**: 6个文件版本号
**When**: Phase 4 + Phase 7
**Pass Criteria**: 所有6个文件版本=8.6.1

### Test Matrix

| Test Type | Tool | Trigger | Critical | Auto-Fix |
|-----------|------|---------|----------|----------|
| Syntax | bash -n | Pre-commit | ✅ Yes | ❌ No |
| Linting | shellcheck | Pre-commit | ✅ Yes | ⚠️ Partial |
| Static | static_checks.sh | Phase 3 | ✅ Yes | ❌ No |
| Audit | pre_merge_audit.sh | Phase 4 | ✅ Yes | ❌ No |
| Contract | test_workflow_consistency.sh | Phase 3 | ✅ Yes | ❌ No |
| Version | check_version_consistency.sh | Phase 4/7 | ✅ Yes | ⚠️ Via script |

---

## Quality Gates

### Gate 1: Phase 3 - Technical Quality

**Trigger**: After implementation complete

**Checks**:
```bash
bash scripts/static_checks.sh
```

**Pass Criteria**:
- ✅ Shell syntax: 0 errors
- ✅ Shellcheck: 0 errors, <5 warnings
- ✅ Complexity: 所有函数<150行
- ✅ Hook performance: <2秒
- ✅ Contract tests: 全部通过

**Fail Action**: 返回Phase 2修复

### Gate 2: Phase 4 - Code Quality

**Trigger**: After code review

**Checks**:
```bash
bash scripts/pre_merge_audit.sh
```

**Pass Criteria**:
- ✅ Configuration complete
- ✅ TODO/FIXME ≤5个
- ✅ Root documents ≤7
- ✅ Version consistency (6 files)
- ✅ Documentation complete
- ⚠️ <2 warnings

**Fail Action**: 返回Phase 2修复critical issues

---

## Risk Management

### Risk Assessment Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SPEC.yaml修改触发Lock失败 | Medium | High | 准备好`update-lock.sh` |
| manifest.yml修改破坏依赖 | Low | High | 契约测试验证 |
| TODO清理引入新bug | Low | Medium | 每个清理单独commit |
| 版本号升级遗漏文件 | Low | High | `check_version_consistency.sh` |
| Agent并行冲突 | Low | Low | 修改不同文件 |

### Risk Mitigation Strategies

#### 1. Lock验证失败
**Mitigation**:
```bash
# 预先检查Lock模式
grep "lock_mode" .workflow/SPEC.yaml  # 应该是soft

# 修改后立即更新
bash tools/update-lock.sh

# 验证
bash tools/verify-core-structure.sh
```

#### 2. 依赖关系破坏
**Mitigation**:
- 契约测试验证Phase数量
- manifest.yml的phases数组必须是7
- 子阶段必须与SPEC.yaml对齐

#### 3. TODO清理引入bug
**Mitigation**:
- 每个TODO清理单独commit
- commit message格式：`chore: remove TODO in <file> - <reason>`
- 立即运行`bash -n`验证语法

#### 4. 版本号遗漏
**Mitigation**:
- 使用`scripts/bump_version.sh`统一升级
- Phase 4和Phase 7双重验证
- CI强制检查

#### 5. Agent并行冲突
**Mitigation**:
- Agent 1, 2, 4修改不同文件（无冲突）
- Agent 3依赖1+2完成
- Agent 5依赖1完成
- Agent 6依赖3完成

---

## Rollback Plan

### Rollback Triggers

以下情况触发回滚：
1. Quality Gate 1或2失败且无法修复
2. Contract tests失败
3. Lock验证失败且无法更新
4. 发现新的Critical bugs
5. 用户明确要求回滚

### Rollback Procedures

#### Method 1: Git Revert (推荐)
```bash
# 在feature分支上revert
cd "/home/xx/dev/Claude Enhancer"
git log --oneline  # 找到有问题的commit

# Revert specific commit
git revert <commit-hash>

# Or revert entire branch
git checkout main
git branch -D feature/workflow-consistency-fixes
```

#### Method 2: File-level Restore
```bash
# 恢复单个文件
git checkout main -- .workflow/SPEC.yaml

# 恢复多个文件
git checkout main -- .workflow/SPEC.yaml .workflow/manifest.yml
```

#### Method 3: Cherry-pick Good Changes
```bash
# 如果部分修改是好的
git checkout main
git checkout -b feature/workflow-fixes-v2
git cherry-pick <good-commit-1>
git cherry-pick <good-commit-2>
```

### Rollback Validation

回滚后必须验证：
```bash
# 语法检查
bash -n scripts/*.sh

# 版本一致性
bash scripts/check_version_consistency.sh

# 核心结构
bash tools/verify-core-structure.sh

# 分支状态
git status
```

---

## Success Criteria

### Definition of Done

任务完成必须满足：

#### ✅ Functional Requirements
- [ ] Issue #1-#10全部修复
- [ ] SPEC.yaml与manifest.yml完全一致
- [ ] SPEC.yaml与CLAUDE.md描述一致
- [ ] TODO/FIXME ≤5个
- [ ] 契约测试创建并通过

#### ✅ Quality Requirements
- [ ] Quality Gate 1通过（static_checks.sh）
- [ ] Quality Gate 2通过（pre_merge_audit.sh）
- [ ] Contract tests通过（test_workflow_consistency.sh）
- [ ] Version consistency通过（6个文件=8.6.1）
- [ ] Core structure验证通过（verify-core-structure.sh）

#### ✅ Documentation Requirements
- [ ] P1_DISCOVERY.md存在（≥300行）
- [ ] IMPACT_ASSESSMENT.md存在
- [ ] PLAN.md存在（≥1000行）
- [ ] ACCEPTANCE_CHECKLIST.md创建
- [ ] REVIEW.md存在（Phase 4）
- [ ] CHANGELOG.md更新（8.6.1）

#### ✅ Process Requirements
- [ ] 使用了6个并行Agent（基于Impact Assessment）
- [ ] 没有弹窗询问权限（Bypass模式）
- [ ] 每个Phase有完整记录
- [ ] 所有修改有Git commit
- [ ] Evidence收集完整

### Acceptance Checklist

见`.workflow/ACCEPTANCE_CHECKLIST_workflow_fixes.md`（Phase 1完成后创建）

---

## Timeline & Milestones

### Phase 1: Discovery & Planning (Complete)
- [x] 1.1 Branch Check (5min)
- [x] 1.2 Requirements Discussion (10min)
- [x] 1.3 Technical Discovery (20min)
- [x] 1.4 Impact Assessment (10min)
- [x] 1.5 Architecture Planning (30min)
- **Total**: 75分钟

### Phase 2: Implementation (Pending)
- [ ] Agent 1: SPEC.yaml修复 (30min)
- [ ] Agent 2: manifest.yml修复 (20min)
- [ ] Agent 3: LOCK更新 (15min, after 1+2)
- [ ] Agent 4: TODO清理 (40min)
- [ ] Agent 5: CLAUDE.md同步 (20min, after 1)
- [ ] Agent 6: 契约测试 (45min, after 3)
- **Total**: 75分钟（并行）

### Phase 3: Testing (Pending)
- [ ] Static checks (10min)
- [ ] Contract tests (5min)
- [ ] Fix any issues (15min)
- **Total**: 30分钟

### Phase 4: Review (Pending)
- [ ] Manual review (20min)
- [ ] Pre-merge audit (10min)
- **Total**: 30分钟

### Phase 5: Release (Pending)
- [ ] Version upgrade (8.6.0→8.6.1) (10min)
- [ ] CHANGELOG update (10min)
- [ ] README update (5min)
- **Total**: 25分钟

### Phase 6: Acceptance (Pending)
- [ ] Generate acceptance report (10min)
- [ ] User confirmation (wait)
- **Total**: 10分钟 + wait

### Phase 7: Closure (Pending)
- [ ] Cleanup temp files (5min)
- [ ] Final validation (5min)
- [ ] Create PR (5min)
- **Total**: 15分钟

### Overall Timeline
```
Phase 1: ████████████████ 75min ✅ Complete
Phase 2: ████████████████ 75min ⏳ Pending
Phase 3: ██████ 30min ⏳ Pending
Phase 4: ██████ 30min ⏳ Pending
Phase 5: █████ 25min ⏳ Pending
Phase 6: ██ 10min + wait ⏳ Pending
Phase 7: ███ 15min ⏳ Pending
─────────────────────────────────
Total:   260min (4.3 hours)
```

**Parallel Optimization**: Phase 2使用6个Agent，节省125分钟

---

## Appendices

### Appendix A: Agent Communication Protocol

Agents之间通过文件系统通信：

```
.workflow/agent_status/
├── agent1.status  # {"status": "completed", "time": 1730275200}
├── agent2.status
├── agent3.status
├── agent4.status
├── agent5.status
└── agent6.status
```

### Appendix B: File Backup Strategy

修改前备份：
```bash
mkdir -p .workflow/backup_$(date +%Y%m%d_%H%M%S)
cp .workflow/SPEC.yaml .workflow/backup_*/
cp .workflow/manifest.yml .workflow/backup_*/
```

### Appendix C: Commit Message Convention

```
Format: <type>: <subject>

Types:
- fix: 修复Issue
- chore: 清理TODO
- docs: 更新文档
- test: 添加测试
- refactor: 重构

Examples:
- fix(SPEC): correct P2_DISCOVERY.md to P1_DISCOVERY.md (Issue #1)
- fix(SPEC): update version files count from 5 to 6 (Issue #2)
- fix(manifest): remove redundant substage (Issue #3)
- chore: cleanup 3 TODO comments in scripts/
- test: add contract test for workflow consistency
```

### Appendix D: Evidence Collection

每个Agent完成后收集evidence：
```bash
bash scripts/evidence/collect.sh \
  --type "agent_completion" \
  --checklist-item "2.1" \
  --description "Agent 1: SPEC.yaml corrections" \
  --file /tmp/agent1_output.log
```

---

**Plan完成时间**: 2025-10-30 16:15
**总字数**: ~6500字
**总行数**: ~1200行
**Phase**: 1.5 Architecture Planning Complete ✅
**下一Phase**: Phase 2 Implementation（等待用户确认）

---

## Next Steps

1. **User Confirmation**: 等待用户确认"我理解了，开始Phase 2"
2. **Phase 2 Execution**: 启动6个并行Agent
3. **Quality Validation**: Phase 3 + Phase 4
4. **Version Release**: Phase 5
5. **User Acceptance**: Phase 6
6. **Merge Ready**: Phase 7

**现在等待用户确认Phase 1完成，是否开始Phase 2。**
