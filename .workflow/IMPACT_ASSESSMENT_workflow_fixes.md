# Phase 1.4: Impact Assessment - Workflow Consistency Fixes

## 自动化影响评估

### 任务特征量化

#### 风险等级 (Risk): 7/10
- ✅ 触及核心文档（SPEC.yaml, manifest.yml）
- ✅ 可能触发Lock验证
- ✅ 需要CODEOWNERS审批
- ⚠️ 但修改逻辑清晰，不是架构重构
- ⚠️ 有完整测试覆盖

**风险点**:
1. SPEC.yaml是"核心不变层"定义
2. manifest.yml被CODEOWNERS保护
3. 修改后需要更新LOCK.json
4. 多文件修改可能引入新矛盾

#### 复杂度 (Complexity): 6/10
- ⚠️ 涉及10个独立问题
- ⚠️ 需要理解SPEC/manifest/CLAUDE.md的关系
- ✅ 但每个问题修复逻辑简单
- ✅ 有明确的审计报告指导
- ✅ 不涉及算法或复杂逻辑

**复杂度来源**:
1. 需要保持3个文档一致
2. 检查点编号规则需要理清
3. TODO/FIXME分散在多个文件
4. 契约测试需要设计

#### 影响范围 (Scope): 5/10
- ⚠️ 修改2个核心配置文件
- ⚠️ 清理可能涉及10+个文件
- ✅ 不影响业务逻辑
- ✅ 不影响hooks执行
- ✅ 主要是文档层面

**影响的文件**:
- `.workflow/SPEC.yaml`
- `.workflow/manifest.yml`
- `.workflow/LOCK.json`
- `CLAUDE.md` (可能)
- 多个文件的TODO/FIXME
- `tests/contract/` (新增)

### Impact Radius计算

```
公式: Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)

计算:
  Risk      = 7 × 5 = 35
  Complexity = 6 × 3 = 18
  Scope     = 5 × 2 = 10
  ─────────────────────
  Total Radius = 63
```

### Agent推荐策略

#### 阈值映射
- **Radius ≥ 50**: 高风险 → **6 agents**
- Radius 30-49: 中风险 → 3 agents
- Radius 0-29: 低风险 → 0 agents

#### 结论
**Radius = 63 → 高风险任务**

**推荐配置**: **6 agents**

---

## 6-Agent并行执行方案

### Parallel Group 1: 核心文档修复（3 agents）

#### Agent 1: SPEC.yaml修复
**任务**:
- Issue #1: P2_DISCOVERY.md → P1_DISCOVERY.md
- Issue #2: 版本文件5个 → 6个
- Issue #7: 检查点编号示例整理

**文件**: `.workflow/SPEC.yaml`

**预计时间**: 30分钟

**依赖**: 无

#### Agent 2: manifest.yml修复
**任务**:
- Issue #3: 移除"Dual-Language Checklist Generation"
- Issue #6: 子阶段加上编号

**文件**: `.workflow/manifest.yml`

**预计时间**: 20分钟

**依赖**: 无

#### Agent 3: Lock文件更新与验证
**任务**:
- 运行`bash tools/update-lock.sh`
- 验证`bash tools/verify-core-structure.sh`
- 确保Lock验证通过

**文件**: `.workflow/LOCK.json`

**预计时间**: 15分钟

**依赖**: Agent 1和Agent 2完成后

---

### Parallel Group 2: 代码清理（2 agents）

#### Agent 4: TODO/FIXME清理
**任务**:
- 找出所有8个TODO/FIXME
- 分类处理：
  - 可立即修复 → 修复
  - 需要设计 → 转成Issue
  - 过期注释 → 删除
- 目标：≤5个TODO

**预计时间**: 40分钟

**依赖**: 无（可与Group 1并行）

#### Agent 5: CLAUDE.md同步更新
**任务**:
- 确保CLAUDE.md与SPEC.yaml描述一致
- 更新规则4中版本文件数量（5→6）
- 更新Phase 1子阶段描述

**文件**: `CLAUDE.md`

**预计时间**: 20分钟

**依赖**: Agent 1完成后

---

### Parallel Group 3: 测试验证（1 agent）

#### Agent 6: 契约测试创建
**任务**:
- 创建`tests/contract/test_workflow_consistency.sh`
- 验证项：
  1. SPEC.yaml与manifest.yml Phase数量一致
  2. SPEC.yaml与manifest.yml子阶段一致
  3. 版本文件数量定义一致
  4. 检查点编号规则有效
- 集成到CI

**预计时间**: 45分钟

**依赖**: Group 1完成后

---

## 并行执行时序图

```
T+0min
  ├─ Agent 1: SPEC.yaml修复 ───────────────────────→ T+30min ✓
  ├─ Agent 2: manifest.yml修复 ──────────────→ T+20min ✓
  └─ Agent 4: TODO清理 ────────────────────────────────→ T+40min ✓

T+30min（Group 1完成）
  ├─ Agent 3: Lock更新验证 ─────────→ T+45min ✓
  ├─ Agent 5: CLAUDE.md同步 ─────────→ T+50min ✓
  └─ Agent 6: 契约测试创建 ───────────────────→ T+75min ✓

T+75min: 所有Agent完成
```

**总并行时间**: ~75分钟（vs 顺序执行~200分钟）
**效率提升**: 62%

---

## 资源需求评估

### 计算资源
- 6个并行Agent
- 每个Agent独立执行环境
- 无文件冲突（修改不同文件或不同部分）

### 人力投入
- AI自主执行（Bypass Permissions模式）
- 用户仅需Phase 6验收确认

### 风险缓解
1. **冲突检测**: parallel_conflict_validator.sh自动检查
2. **回滚机制**: Git feature分支，任何问题都可revert
3. **增量验证**: 每个Agent完成后运行子集测试

---

## 下一步：Phase 1.5 Architecture Planning

将基于这个Impact Assessment创建详细的PLAN.md，包含：
1. 6个Agent的详细任务定义
2. 文件修改的diff预览
3. 测试策略
4. 回滚方案

---

**评估完成时间**: 2025-10-30 16:00
**Phase**: 1.4 Impact Assessment
**推荐配置**: 6 agents (高风险任务)
**预计总时间**: 75分钟（并行执行）
**下一Phase**: 1.5 Architecture Planning
