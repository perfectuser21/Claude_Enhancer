# Phase 1.3: Technical Discovery - Workflow Consistency Fixes

## 任务背景
通过深度审计发现Claude Enhancer v8.6.0存在10个workflow一致性问题，需要系统性修复。

## 用户原始需求
> "是我的 我希望你用Claude enhaner 去完成 我刚好看看你的工作情况 是否用了多subagent 以及是否再次问我要权限 你现在有意识的记录记录 方便以后修改"

**用户意图**：
1. 测试7-Phase工作流是否真正执行
2. 测试多subagent机制是否触发
3. 测试Bypass Permissions是否生效
4. 验证工作过程是否有完整记录

## 问题分析（基于审计报告）

### 🔴 Critical Issues（必须修复）

#### Issue #1: SPEC.yaml产出文件名错误
**位置**: `.workflow/SPEC.yaml:135`
```yaml
core_deliverables:
  phase1:
    - "P2_DISCOVERY.md (≥300行)"  # ❌ 错误
```
**修复**: 改为`P1_DISCOVERY.md`或统一为`user_request.md`

#### Issue #2: 版本文件数量自相矛盾
**位置**:
- `.workflow/SPEC.yaml:90` → 说5个文件
- `.workflow/SPEC.yaml:170-177` → 列出5个文件
- `scripts/check_version_consistency.sh` → 实际检查6个
- `CLAUDE.md` → 说6个文件

**修复**: SPEC.yaml改成6个，加上`SPEC.yaml`自己

#### Issue #3: manifest.yml多余子阶段
**位置**: `.workflow/manifest.yml:18`
```yaml
substages: [..., "Dual-Language Checklist Generation", ...]  # ❌ 多余
```
**分析**: Checklist Generation是hook触发（settings.json:72-76），不是独立子阶段

**修复**: 移除这个子阶段

#### Issue #4: TODO/FIXME过多
**当前**: 8个（超标，允许≤5个）
**需要**: 逐个排查并处理

#### Issue #5: 在main分支
**状态**: ✅ 已解决（已创建feature/workflow-consistency-fixes分支）

### 🟡 Medium Issues（应该修复）

#### Issue #6: 子阶段编号不统一
**SPEC.yaml**: 使用编号（1.1, 1.2, ...）
**manifest.yml**: 不使用编号
**建议**: manifest.yml也加上编号

#### Issue #7: 检查点编号示例混乱
**位置**: `.workflow/SPEC.yaml:54-59`
```yaml
examples:
  - "PD_S001"   # Pre-Discussion (Phase 1.2)  ❌ 含义不清
  - "P1_S001"   # Phase 1 Branch Check (Phase 1.1)  ❌
  - "P2_S001"   # Phase 2 Discovery (Phase 1.3)  ❌ 逻辑混乱
  - "P5_S001"   # Phase 5 Testing (Phase 3)  ❌ 更混乱
```
**需要**: 重新整理或补充说明

#### Issue #8: 缺少契约测试
**缺失**: `tests/contract/test_workflow_consistency.sh`
**需要**: 验证修复后的一致性

### 🟢 Low Priority（可选）

#### Issue #9: SPEC.yaml过于冗长
#### Issue #10: Phase超时配置（需数据支撑）

## 技术方案

### 修复策略

**原则**:
1. 优先修复Critical issues（#1-#4）
2. 同时修复Medium issues（#6-#8）
3. Low priority暂不处理

**文件修改清单**:
- `.workflow/SPEC.yaml` → Issue #1, #2, #6, #7
- `.workflow/manifest.yml` → Issue #3, #6
- 多个文件 → Issue #4（TODO/FIXME清理）
- `tests/contract/` → Issue #8（新增测试）

### 风险分析

**高风险**:
- 修改SPEC.yaml触及"核心不变层"
- 可能触发Lock验证（verify-core-structure.sh）
- 需要更新LOCK.json

**中风险**:
- manifest.yml被CODEOWNERS保护
- 可能需要审批

**低风险**:
- 清理TODO/FIXME
- 添加契约测试

### 依赖关系

```
Issue #1, #2, #3, #6, #7 (文档修复)
    ↓
bash tools/update-lock.sh (更新LOCK.json)
    ↓
Issue #4 (清理TODO)
    ↓
Issue #8 (契约测试)
    ↓
Quality Gate 1 + 2
    ↓
版本升级 (8.6.0 → 8.6.1)
```

## 多Subagent策略分析（Phase 1.4 Impact Assessment）

### 任务特征
- **风险**: Medium-High（触及核心文档）
- **复杂度**: Medium（逻辑清晰但文件多）
- **影响范围**: 核心定义文件（SPEC.yaml, manifest.yml）

### Impact Radius计算
```
Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)
       = (7 × 5) + (6 × 3) + (5 × 2)
       = 35 + 18 + 10
       = 63
```

### Agent推荐
- **Radius = 63** → **高风险任务** (≥50)
- **推荐**: **6 agents**

### Parallel Groups设计

**Group 1: 文档一致性修复** (3 agents)
- Agent 1: 修复SPEC.yaml (Issue #1, #2, #7)
- Agent 2: 修复manifest.yml (Issue #3, #6)
- Agent 3: 更新LOCK.json + 验证

**Group 2: 代码清理** (2 agents)
- Agent 4: 清理TODO/FIXME (Issue #4)
- Agent 5: 更新相关文档（CLAUDE.md保持一致）

**Group 3: 测试验证** (1 agent)
- Agent 6: 创建契约测试 (Issue #8)

**并行策略**:
- Group 1和Group 2可并行
- Group 3依赖Group 1完成

## 验收清单

- [ ] SPEC.yaml: P2_DISCOVERY.md → P1_DISCOVERY.md
- [ ] SPEC.yaml: 版本文件5个 → 6个
- [ ] manifest.yml: 移除多余子阶段
- [ ] manifest.yml: 子阶段加上编号
- [ ] SPEC.yaml: 检查点编号示例清晰
- [ ] TODO/FIXME ≤ 5个
- [ ] 契约测试存在且通过
- [ ] tools/verify-core-structure.sh通过
- [ ] scripts/static_checks.sh通过
- [ ] scripts/pre_merge_audit.sh通过
- [ ] 版本号升级到8.6.1
- [ ] 6个文件版本一致

## 下一步：Phase 1.5 Architecture Planning

需要创建详细的PLAN.md（≥1000行），包含：
1. 完整修改方案
2. Agent任务分配
3. 测试策略
4. 回滚方案

---

**文档创建时间**: 2025-10-30 15:55
**Phase**: 1.3 Technical Discovery
**下一Phase**: 1.4 Impact Assessment（自动化）
