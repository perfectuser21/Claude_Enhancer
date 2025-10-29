# Requirements Dialogue - All-Phases Parallel Optimization with Skills

> Phase: Phase 1.2 - Requirements Discussion
> Date: 2025-10-29
> Branch: feature/all-phases-parallel-optimization-with-skills
> Version: 8.3.0 (target)

## 用户原始需求

> "我需要的时候完整 完善高质量的所有 phase 尽可能的提速"
> "你把 skills 融入 你刚才调研了"

### 解读

**核心需求**：
1. **所有Phases提速** - 不只Phase3，要Phase2, 3, 4, 5, 6全部并行优化
2. **完整完善** - 90分标准，不是60分的"能跑就行"
3. **高质量** - 完整配置 + 实际benchmark + 详细文档
4. **融入Skills** - 利用现有的4个Skills提升并行执行的质量和可靠性

### 背景

**v8.2.1完成的工作**（PR #51）：
- ✅ Phase3并行执行激活（"60分"快速方案）
- ✅ 70行集成代码 + 8个集成测试
- ✅ 预期1.5-2.0x加速（理论分析，未实测）

**当前限制**：
- ❌ 只有Phase3配置了并行
- ❌ Phase2, 4, 5, 6仍是串行
- ❌ 没有真实benchmark数据
- ❌ Skills未充分利用于并行执行

---

## 需求分析

### 功能需求

#### FR-1: 全Phase并行配置
**描述**：为所有可并行的Phases配置parallel_groups

**覆盖范围**：
- Phase2 (Implementation) - 代码编写任务可并行
- Phase3 (Testing) - 测试任务已配置，需优化
- Phase4 (Review) - 审查任务可并行
- Phase5 (Release) - 发布准备任务可并行
- Phase6 (Acceptance) - 验收任务可部分并行

**不包括**：
- Phase1 (Planning) - 必须串行（需求→发现→评估→规划有依赖）
- Phase7 (Closure) - 配置为serial-only（manifest.yml中parallel: false）

#### FR-2: Skills集成到并行执行
**描述**：利用现有4个Skills提升并行执行的质量

**Skills应用场景**：

1. **checklist-validator** (已有)
   - **并行场景应用**：并行任务完成后，验证每个任务的checklist有evidence
   - **增强**：支持并行任务的批量验证

2. **learning-capturer** (已有)
   - **并行场景应用**：并行执行失败时，自动捕获每个失败任务的原因
   - **增强**：并行上下文感知（记录哪个group、哪个task失败）

3. **evidence-collector** (已有)
   - **并行场景应用**：每个并行任务完成后，提醒收集evidence
   - **增强**：批量evidence收集（一次收集多个并行任务的结果）

4. **kpi-reporter** (已有，disabled)
   - **并行场景应用**：Phase转换时，报告并行执行的性能指标
   - **增强**：添加并行特定的KPI（并行度、加速比、任务分布）

#### FR-3: 新Skill - parallel-performance-tracker
**描述**：专门追踪并行执行性能的新Skill

**触发条件**：
```json
{
  "trigger": {
    "event": "after_parallel_execution",
    "phases": ["Phase2", "Phase3", "Phase4", "Phase5", "Phase6"]
  }
}
```

**功能**：
- 记录每次并行执行的时间
- 计算实际加速比（vs 串行基准）
- 检测性能退化
- 生成性能趋势报告

#### FR-4: 实际性能Benchmark
**描述**：真实运行测量，收集性能数据

**目标指标**：
- **Phase2加速比**: 目标 ≥1.3x
- **Phase3加速比**: 目标 ≥1.5x
- **Phase4加速比**: 目标 ≥1.2x
- **Phase5加速比**: 目标 ≥1.4x
- **Phase6加速比**: 目标 ≥1.1x（部分并行）
- **整体加速比**: 目标 ≥1.4x

**测量方法**：
```bash
# 串行基准
time bash .workflow/executor.sh --mode=serial Phase2-Phase6

# 并行测试
time bash .workflow/executor.sh --mode=parallel Phase2-Phase6

# 计算加速比
Speedup = T_serial / T_parallel
```

### 非功能需求

#### NFR-1: 质量标准
- **90分标准**: 完整配置 + 实测数据 + 详细文档
- **代码质量**: 保持97/100分标准
- **测试覆盖**: 每个Phase至少3个并行场景测试
- **文档完整性**: Phase 1文档 >2,000行

#### NFR-2: 性能目标
- **Phase2-6整体加速**: ≥1.4x
- **并行开销**: <5%（vs 理论最优）
- **启动延迟**: <100ms
- **内存占用**: 增加<50MB

#### NFR-3: 稳定性
- **零破坏性变更**: 串行模式完全不受影响
- **错误率**: 并行失败率 <5%
- **降级能力**: 任何Phase并行失败自动降级串行
- **Ctrl+C安全**: 所有并行任务可正确终止

#### NFR-4: 可维护性
- **配置清晰**: parallel_groups易于理解和修改
- **调试友好**: 详细的并行日志
- **监控完善**: Skills自动收集性能和错误数据

---

## Skills Framework深度集成方案

### 架构概览

```
并行执行引擎 (parallel_executor.sh)
    ↓
Skills Middleware Layer (新增)
    ├─ Pre-execution Skills
    │   ├─ parallel-conflict-validator (检查冲突)
    │   └─ parallel-resource-allocator (分配资源)
    ↓
    ├─ During-execution Skills
    │   ├─ parallel-progress-monitor (监控进度)
    │   └─ parallel-load-balancer (动态负载均衡)
    ↓
    └─ Post-execution Skills
        ├─ parallel-performance-tracker (性能追踪)
        ├─ evidence-collector (批量收集)
        ├─ learning-capturer (失败分析)
        └─ kpi-reporter (性能报告)
```

### 新Skills设计

#### Skill 5: parallel-performance-tracker
```json
{
  "name": "parallel-performance-tracker",
  "description": "Track parallel execution performance and generate metrics",
  "trigger": {
    "event": "after_parallel_execution",
    "phases": ["Phase2", "Phase3", "Phase4", "Phase5", "Phase6"]
  },
  "action": {
    "script": "scripts/parallel/track_performance.sh",
    "args": [
      "{{phase}}",
      "{{execution_time}}",
      "{{group_count}}",
      "{{task_count}}"
    ]
  },
  "output": {
    "file": ".workflow/logs/parallel_performance.json",
    "format": "json"
  },
  "enabled": true
}
```

#### Skill 6: parallel-conflict-validator
```json
{
  "name": "parallel-conflict-validator",
  "description": "Validate no conflicts before parallel execution",
  "trigger": {
    "event": "before_parallel_execution"
  },
  "action": {
    "script": "scripts/parallel/validate_conflicts.sh",
    "args": ["{{phase}}", "{{groups}}"]
  },
  "enabled": true
}
```

#### Skill 7: parallel-load-balancer
```json
{
  "name": "parallel-load-balancer",
  "description": "Dynamically balance load across parallel groups",
  "trigger": {
    "event": "during_parallel_execution",
    "condition": "task_count_imbalance > 30%"
  },
  "action": {
    "script": "scripts/parallel/rebalance_load.sh",
    "args": ["{{phase}}", "{{current_distribution}}"]
  },
  "enabled": false
}
```

### 现有Skills增强

#### 增强1: checklist-validator (批量模式)
**新增参数**：
```bash
scripts/evidence/validate_checklist.sh --parallel-mode --batch \
  --tasks "task1,task2,task3"
```

**输出格式**：
```json
{
  "total_tasks": 3,
  "validated": 3,
  "missing_evidence": [],
  "validation_time": "0.5s"
}
```

#### 增强2: evidence-collector (并行收集)
**新增功能**：
```bash
# 自动检测并行执行的输出文件
scripts/evidence/collect.sh --auto-detect-parallel \
  --phase Phase3 \
  --group-id unit_tests
```

#### 增强3: kpi-reporter (并行KPI)
**新增指标**：
- `parallel_degree`: 实际并行任务数
- `speedup_ratio`: 加速比
- `parallel_efficiency`: 并行效率（实际加速/理论加速）
- `load_balance_score`: 负载均衡评分

---

## 技术可行性分析

### 可行性评估

#### 1. Phase2并行可行性 ✅ HIGH
**任务类型**：代码编写、脚本创建、配置文件修改

**可并行场景**：
- Group 1: 核心功能实现
- Group 2: 测试脚本编写
- Group 3: 配置文件更新
- Group 4: 文档初稿

**冲突风险**: 🟡 MEDIUM
- 可能冲突：同一文件的不同部分
- 缓解：细粒度的conflict rules

**预期加速**: 1.3-1.5x

#### 2. Phase3并行可行性 ✅ VERY HIGH
**当前状态**：已配置，运行良好

**优化空间**：
- 当前3个groups可扩展到5个
- 添加更细粒度的任务分组
- 优化conflict rules

**预期加速**: 1.5-2.0x（当前） → 2.0-2.5x（优化后）

#### 3. Phase4并行可行性 ✅ MEDIUM-HIGH
**任务类型**：代码审查、文档验证、性能分析

**可并行场景**：
- Group 1: 代码逻辑审查
- Group 2: 代码一致性检查
- Group 3: 文档完整性验证
- Group 4: Pre-merge audit

**冲突风险**: 🟢 LOW
- 大部分是只读操作
- REVIEW.md写入需要互斥

**预期加速**: 1.2-1.4x

#### 4. Phase5并行可行性 ✅ HIGH
**任务类型**：文档更新、版本标记、监控配置

**可并行场景**：
- Group 1: CHANGELOG更新
- Group 2: README/文档更新
- Group 3: 版本号统一
- Group 4: 监控配置

**冲突风险**: 🟡 MEDIUM
- 版本号需要协调
- 多个文档可能引用相同版本

**预期加速**: 1.4-1.6x

#### 5. Phase6并行可行性 🟡 LOW-MEDIUM
**任务类型**：验收测试、报告生成

**部分并行**：
- 多个验收标准可并行检查
- 但最终报告生成串行

**预期加速**: 1.1-1.2x（有限提升）

### Skills Framework可行性 ✅ HIGH

**现有基础**：
- 4个Skills已实现并稳定运行
- Hook系统成熟（PreToolUse, PostToolUse）
- Event trigger机制完善

**需要开发**：
- 3个新Skills（performance-tracker, conflict-validator, load-balancer）
- 现有3个Skills增强（批量模式、并行感知）
- Skills middleware layer

**风险评估**: 🟢 LOW
- Skills系统架构清晰
- 增量开发，不破坏现有功能
- 可独立测试和验证

---

## 成功标准

### 必须达成 (Must Have)

1. **全Phase配置完整** ✅
   - Phase2, 3, 4, 5, 6都有parallel_groups定义
   - 每个Phase至少2个groups
   - conflict rules完整

2. **Skills深度集成** ✅
   - 3个新Skills实现
   - 3个现有Skills增强
   - Skills middleware layer工作

3. **实测性能数据** ✅
   - 每个Phase的实际加速比
   - 整体加速比 ≥1.4x
   - 性能报告完整

4. **90分质量标准** ✅
   - Phase 1文档 >2,000行
   - 代码质量 ≥95/100
   - 测试覆盖 100%（所有并行场景）

### 期望达成 (Should Have)

1. **Phase3加速优化** 🎯
   - 从1.5-2.0x提升到2.0-2.5x
   - 细粒度任务分组

2. **动态负载均衡** 🎯
   - parallel-load-balancer Skill
   - 实时任务重分配

3. **性能可视化** 🎯
   - Web dashboard显示并行性能
   - 趋势图和对比分析

### 额外收益 (Nice to Have)

1. **自适应并行度** 🏆
   - 根据系统负载自动调整
   - CPU/内存感知

2. **预测性调度** 🏆
   - 基于历史数据预测任务耗时
   - 智能分组优化

---

## 风险评估

### 高风险项

#### R1: 配置复杂度爆炸
**风险**: 5个Phases × 平均4个groups = 20个并行配置，维护困难

**缓解**：
- 配置模板化
- 自动化验证工具
- 详细文档和示例

**Fallback**: 减少groups数量，保持简洁

#### R2: Skills性能开销
**风险**: 7个Skills运行可能增加显著延迟

**缓解**：
- Skills异步执行（不阻塞主流程）
- 性能预算：每个Skill <50ms
- 可配置enable/disable

**Fallback**: 默认只启用关键Skills

### 中风险项

#### R3: 真实性能不达预期
**风险**: 实测加速比远低于理论值

**缓解**：
- 保守估计（理论值 × 0.7）
- 逐步优化，而非一次性
- 详细性能分析工具

**Fallback**: 降低目标（1.4x → 1.3x）

#### R4: Skill开发时间超预期
**风险**: 3个新Skills开发可能需要额外时间

**缓解**：
- 分阶段实现（P0: performance-tracker, P1: conflict-validator, P2: load-balancer）
- 复用现有代码模式
- 充分测试

**Fallback**: P2 (load-balancer) 可延后

---

## 依赖和约束

### 技术依赖
- ✅ parallel_executor.sh (466 lines, 已有)
- ✅ conflict_detector.sh (已有)
- ✅ mutex_lock.sh (已有)
- ✅ Skills framework (已有)
- ✅ STAGES.yml (已有)

### 时间约束
- **Phase 1**: 3-4小时（详细规划）
- **Phase 2**: 4-5小时（实现）
- **Phase 3**: 3-4小时（测试 + benchmark）
- **Phase 4**: 2-3小时（审查）
- **Phase 5-7**: 2-3小时（发布 + 验收 + 清理）
- **总计**: 14-19小时

### 资源约束
- **单开发者**: 您和AI协作
- **测试环境**: 需要实际运行环境（不能纯理论）
- **性能基准**: 需要串行执行的基准数据

---

## 下一步

### Phase 1.3: Technical Discovery
需要调研：
1. 每个Phase当前的任务分解
2. 任务之间的依赖关系
3. 文件访问模式（conflict分析）
4. Skills集成点识别

### Phase 1.4: Impact Assessment
评估：
1. 影响半径（修改范围）
2. Agent数量推荐
3. 风险评分

### Phase 1.5: Architecture Planning
设计：
1. 详细的parallel_groups配置
2. Skills middleware架构
3. 性能测试方案
4. 实施步骤

---

**创建时间**: 2025-10-29
**作者**: Claude Code (Sonnet 4.5)
**用户需求**: 完整、完善、高质量的全Phase提速 + Skills深度集成
**质量标准**: 90分（完整配置 + 实测benchmark + 详细文档）
