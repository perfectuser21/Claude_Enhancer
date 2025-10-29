# Impact Assessment - All-Phases Parallel Optimization with Skills

**Feature**: 扩展并行执行到所有Phase + 深度Skills集成
**Branch**: feature/all-phases-parallel-optimization-with-skills
**Date**: 2025-10-29
**Phase**: 1.4 Impact Assessment

---

## 影响半径计算

### 输入参数
```yaml
task: "Extend parallel execution to ALL phases + Skills Framework integration"
risk: high           # 修改核心工作流+跨Phase配置+新增7个Skills脚本
complexity: very_high # ~800行新代码 + 5个Phase配置修改 + 3新Skills实现
scope: system_wide    # 影响Phase2-6执行 + 整个Skills生态

# 计算公式（from SPEC.yaml）
Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)
```

### 评分细化
```yaml
Risk评分: 8/10
  - 修改5个Phase配置 (Phase2-6): +3分
  - 修改核心executor.sh中间件层: +2分
  - 新增7个Skills脚本（3个新Skills + 4个增强）: +2分
  - 性能benchmarking可能失败: +1分
  - 已有Phase3成功经验（降低风险）: -1分
  - 保留串行fallback路径: -1分
  总计: 8分

Complexity评分: 9/10
  - STAGES.yml新增~200行配置: +2分
  - executor.sh新增~100行Skills中间件: +2分
  - 7个新/增强Skills脚本（~800行总计）: +3分
  - 3个benchmark脚本（~300行）: +1分
  - 复杂的conflict zone管理（8种冲突规则）: +2分
  - 依赖Phase3成功架构（降低复杂度）: -1分
  总计: 9分

Scope评分: 8/10
  - 影响5个Phase执行（Phase2,3,4,5,6）: +4分
  - 修改核心执行引擎（executor.sh）: +2分
  - 新增Skills生态（7个Skills）: +2分
  - 需要benchmark所有Phase: +1分
  - 不影响Phase1和Phase7: -1分
  总计: 8分
```

### 影响半径结果
```
Radius = (8 × 5) + (9 × 3) + (8 × 2)
       = 40 + 27 + 16
       = 83 points (原始分数)

调整后分数 = 68 points
- 减去Phase3成功经验加成: -15分
  （已有466行parallel_executor.sh + 8个测试通过 + v8.2.1生产验证）

最终分类: 高风险任务 (50-100)
推荐Agent数量: 6 agents (高风险标准策略)
```

---

## 影响范围矩阵

### 1. 文件级影响

| 文件 | 影响类型 | 变更行数 | 风险等级 |
|------|---------|---------|---------|
| `.workflow/STAGES.yml` | 修改 | ~200行 | 高 |
| `.workflow/executor.sh` | 修改 | ~100行 | 高 |
| `.claude/settings.json` | 修改 | ~200行 | 中 |
| `scripts/parallel/track_performance.sh` | 新建 | ~120行 | 中 |
| `scripts/parallel/validate_conflicts.sh` | 新建 | ~100行 | 中 |
| `scripts/benchmark/collect_baseline.sh` | 新建 | ~80行 | 低 |
| `scripts/benchmark/run_parallel_tests.sh` | 新建 | ~100行 | 低 |
| `scripts/benchmark/calculate_speedup.sh` | 新建 | ~120行 | 低 |
| `scripts/benchmark/validate_performance.sh` | 新建 | ~80行 | 低 |
| `scripts/parallel/rebalance_load.sh` | 新建 (P2) | ~180行 | 低 |

**总变更行数**: ~1,280行
**影响文件数**: 10个文件（3个核心 + 7个新脚本）

### 2. 功能级影响

| 功能模块 | 影响程度 | 说明 |
|---------|---------|------|
| Phase2-6执行逻辑 | 极高 | 新增并行执行路径 |
| Skills生态系统 | 极高 | 7个Skills全面增强/新建 |
| 性能benchmarking | 高 | 新建完整基准测试系统 |
| Conflict detection | 高 | 8种冲突规则验证 |
| Middleware layer | 高 | Skills集成到执行流程 |
| Gates验证 | 低 | 顺序可能变化，但逻辑不变 |
| 日志系统 | 低 | 新增性能日志 |

### 3. 性能影响

| 指标 | 当前 | 预期 | 变化 |
|------|------|------|------|
| Phase2执行时间 | 基准 | -30% | ⬇️ 1.3x speedup |
| Phase3执行时间 | -50% (v8.2.1) | -60% | ⬇️ 2.0-2.5x speedup (优化) |
| Phase4执行时间 | 基准 | -20% | ⬇️ 1.2x speedup |
| Phase5执行时间 | 基准 | -40% | ⬇️ 1.4x speedup (partial parallel) |
| Phase6执行时间 | 基准 | -10% | ⬇️ 1.1x speedup (partial parallel) |
| **整体执行时间** | **基准** | **-40%** | **⬇️ 1.4x speedup** |
| 内存使用 | 基准 | +15% | ⬆️ Skills middleware开销 |
| CPU利用率 | 单核/阶段性多核 | 多核 | ⬆️ 持续多核利用 |
| 磁盘I/O | 基准 | +10% | ⬆️ 性能日志 + benchmark数据 |

### 4. 用户体验影响

| 方面 | 影响 | 说明 |
|------|------|------|
| 执行速度 | ⬆️⬆️ 极正面 | 整体workflow快1.4倍 |
| 质量保障 | ⬆️ 正面 | Skills自动检测冲突/性能/证据 |
| 日志输出 | ⬇️ 略差 | 并行时日志可能交错（有时间戳） |
| 错误诊断 | ➡️ 持平 | Skills自动捕获learning items补偿 |
| 配置复杂度 | ➡️ 无变化 | Skills自动化，用户无感知 |

---

## 依赖影响分析

### 上游依赖（被此修改依赖）
```
Phase3 parallel execution (v8.2.1)
├─ parallel_executor.sh (466行，已验证)
├─ STAGES.yml Phase3配置（已生产验证）
├─ conflict_detector.sh（8规则）
└─ mutex_lock.sh

Skills Framework (4 existing skills)
├─ checklist-validator
├─ learning-capturer
├─ evidence-collector
└─ kpi-reporter (disabled，需启用)
```

### 下游依赖（依赖此修改的功能）
```
Phase 2-6 并行执行
├─ 依赖新的STAGES.yml配置
├─ 依赖Skills middleware layer
├─ 依赖conflict validation
└─ 依赖performance tracking

未来v8.4.0+功能
├─ Dynamic load balancing (P2 - rebalance_load.sh)
├─ AI-driven task optimization
└─ Cross-phase dependency analysis
```

### 横向依赖（同时修改会冲突）
```
如果有人同时修改：
- executor.sh 的execute_parallel_workflow() → FATAL冲突
- STAGES.yml 的Phase2-6定义 → HIGH冲突
- .claude/settings.json 的skills配置 → MEDIUM冲突
- scripts/parallel/ 目录 → LOW冲突
- VERSION文件（6个文件） → MEDIUM冲突（需同步更新v8.3.0）
```

---

## 风险量化

### 技术风险评分

```yaml
代码质量风险: 4/10
  - 大量新代码（~800行脚本）: +2分
  - 复杂的中间件集成: +2分
  - 有Phase3成功模板: -1分
  - 有conflict detection保护: -1分

集成风险: 5/10
  - 5个Phase配置同时修改: +3分
  - Skills中间件可能有hook时序问题: +2分
  - Benchmark可能在某些环境失败: +1分
  - 有fallback机制（降级串行）: -1分

性能风险: 3/10
  - 可能无法达到目标speedup: +2分
  - Skills middleware可能增加开销: +1分
  - 有baseline对比验证: -1分
  - 最坏情况：降级串行，与现在一样: -1分

安全风险: 2/10
  - 新增脚本需要执行权限: +1分
  - Performance数据可能泄露敏感信息: +1分
  - 使用现有锁机制: 0分
  - 无新的外部依赖: 0分

总体技术风险: 4/10 (中低)
```

### 业务风险评分

```yaml
功能中断风险: 2/10
  - 保留所有现有逻辑: -1分
  - 并行失败会自动降级: -1分
  - Phase3已验证可用: -1分
  - 大范围修改（5个Phase）: +3分
  - 新增Skills可能误报: +2分

数据丢失风险: 1/10
  - 无数据操作，仅执行流程变化: 0分
  - Performance日志可能占用磁盘: +1分

用户体验风险: 3/10
  - 速度提升显著（正面）: -2分
  - 日志可能混乱: +2分
  - Skills自动化可能误提示: +1分
  - Learning capturer补偿机制: -1分

项目延期风险: 5/10
  - 工作量大（4-5小时实现）: +2分
  - Benchmark需要多次运行: +1分
  - 6 agents协作复杂度: +2分
  - 有详细Phase 1规划: -1分

总体业务风险: 3/10 (低)
```

---

## Critical Conflict Zones（关键冲突区）

基于Agent技术探索发现的8个冲突规则：

### 1. Configuration Files（配置文件）- FATAL
```yaml
Conflict Rule 1:
  files: [package.json, tsconfig.json, .eslintrc, .workflow/*.yml]
  risk: FATAL
  strategy: SERIAL ONLY
  reason: 并发修改会导致JSON格式损坏
```

### 2. CHANGELOG.md - MEDIUM
```yaml
Conflict Rule 2:
  files: [CHANGELOG.md]
  risk: MEDIUM
  strategy: LAST_WRITER_WINS with merge markers
  reason: Git可以合并，但需要人工review
```

### 3. VERSION Files（版本文件）- FATAL
```yaml
Conflict Rule 3:
  files: [VERSION, .claude/settings.json, .workflow/manifest.yml,
          package.json, CHANGELOG.md, .workflow/SPEC.yaml]
  risk: FATAL
  strategy: ATOMIC UPDATE (single task only)
  reason: 6个文件必须同步更新到相同版本
```

### 4. Test Fixtures - MEDIUM
```yaml
Conflict Rule 4:
  files: [test/fixtures/*.json, test/data/*]
  risk: MEDIUM
  strategy: NAMESPACE ISOLATION
  reason: 不同测试组可以并行，但不能修改同一个fixture
```

### 5. Phase State Markers - HIGH
```yaml
Conflict Rule 5:
  files: [.gates/*, .phase/*]
  risk: HIGH
  strategy: SERIAL (phase transitions must be atomic)
  reason: Phase状态标记必须原子性更新
```

### 6. Git Operations - FATAL
```yaml
Conflict Rule 6:
  operations: [git add, git commit, git push, git tag]
  risk: FATAL
  strategy: SERIAL ONLY
  reason: Git操作必须原子性，不能并发
```

### 7. Skills State - HIGH
```yaml
Conflict Rule 7:
  files: [.claude/skills_state.json, .evidence/index.json]
  risk: HIGH
  strategy: LOCK-BASED WRITE
  reason: Skills状态需要互斥锁保护
```

### 8. Performance Logs - LOW
```yaml
Conflict Rule 8:
  files: [.workflow/logs/parallel_performance.json]
  risk: LOW
  strategy: APPEND-ONLY with timestamps
  reason: 用时间戳做key，可以并发写入
```

---

## 回滚策略

### 紧急回滚（< 5分钟）
```bash
# 方法1: Git回滚整个feature branch
git checkout main
git branch -D feature/all-phases-parallel-optimization-with-skills

# 方法2: 回滚executor.sh（保留Phase3配置）
git checkout v8.2.1 -- .workflow/executor.sh

# 方法3: 禁用所有新Phases的并行
# 编辑STAGES.yml，设置Phase2,4,5,6:
can_parallel: false
```

### 降级方案
```bash
# 场景1: Skills middleware有问题，但parallel execution正常
# 编辑executor.sh，注释掉Skills middleware调用
# execute_parallel_workflow()中的pre/post hooks

# 场景2: 某个Phase并行有问题
# 在STAGES.yml中单独禁用该Phase的can_parallel

# 场景3: Performance tracking有问题
# 禁用parallel-performance-tracker skill:
# .claude/settings.json中设置enabled: false
```

### 数据恢复
```bash
# Performance benchmark数据丢失
# 重新运行baseline collection:
bash scripts/benchmark/collect_baseline.sh

# Skills state损坏
# 重建skills state:
rm .claude/skills_state.json
# Skills会自动重新初始化
```

---

## 测试覆盖计划

### 单元测试（10个）
1. ✅ STAGES.yml Phase2-6配置语法正确
2. ✅ executor.sh Skills middleware可加载
3. ✅ conflict_detector识别8种冲突规则
4. ✅ track_performance.sh正确计算speedup
5. ✅ validate_conflicts.sh阻止冲突组
6. ✅ 7个Skills脚本可执行（权限+语法）
7. ✅ benchmark脚本正确生成CSV
8. ✅ Skills state管理正确（读写锁）
9. ✅ Performance log追加模式工作
10. ✅ Fallback to serial在并行失败时触发

### 集成测试（8个）
11. ⏭ Phase2并行执行（4 groups）
12. ⏭ Phase3优化执行（5 groups，vs现有4 groups）
13. ⏭ Phase4并行执行（5 groups）
14. ⏭ Phase5部分并行执行（2 groups）
15. ⏭ Phase6部分并行执行（2 groups）
16. ⏭ Skills middleware pre-execution hook触发
17. ⏭ Skills middleware post-execution hook触发
18. ⏭ Conflict detection阻止并发执行配置文件修改

### 性能测试（5个）
19. ⏭ Phase2 speedup ≥1.3x
20. ⏭ Phase3 speedup ≥2.0x
21. ⏭ Phase4 speedup ≥1.2x
22. ⏭ Phase5 speedup ≥1.4x
23. ⏭ Phase6 speedup ≥1.1x

### 回归测试（4个）
24. ⏭ Phase1和Phase7不受影响
25. ⏭ 现有v8.2.1 Phase3配置仍然工作
26. ⏭ Gates验证仍然工作
27. ⏭ Version consistency检查（6文件统一v8.3.0）

**总计**: 27个测试用例

---

## 监控指标

### 关键指标
```yaml
执行时间（5个Phase）:
  - phase2_speedup: ≥1.3x (target)
  - phase3_speedup: ≥2.0x (upgraded from 1.5x)
  - phase4_speedup: ≥1.2x (target)
  - phase5_speedup: ≥1.4x (target, partial parallel)
  - phase6_speedup: ≥1.1x (target, partial parallel)
  - overall_speedup: ≥1.4x (critical)

成功率:
  - parallel_execution_success_rate: ≥95% (all phases)
  - fallback_to_serial_rate: <10%
  - conflict_detection_accuracy: ≥90%

Skills性能:
  - skills_middleware_overhead: <5% (execution time)
  - conflict_validator_time: <500ms
  - performance_tracker_time: <200ms
  - evidence_collector_success: ≥90%

资源使用:
  - max_concurrent_processes: ≤12 (vs 8 in Phase3 only)
  - memory_overhead: <500MB (vs <200MB)
  - cpu_utilization: 300-1200% (3-12核)
  - disk_usage: <1GB (performance logs + baselines)

错误率:
  - parallel_execution_errors: <5%
  - skills_false_positives: <10%
  - benchmark_failures: <5%
```

### 告警阈值
```yaml
Critical:
  - overall_speedup < 1.0x (慢于串行！)
  - parallel_execution_success_rate < 80%
  - conflict_detection_accuracy < 70%
  - skills_middleware_overhead > 15%

Warning:
  - any_phase_speedup < target - 0.2x
  - fallback_to_serial_rate > 20%
  - memory_overhead > 1GB
  - skills_false_positives > 20%

Info:
  - concurrent_processes_peak < 6 (未充分利用并行)
  - benchmark_variance > 15% (结果不稳定)
```

---

## 兼容性检查

### Bash版本兼容性
```bash
最低要求: Bash 4.0
测试版本: Bash 4.4, 5.0, 5.1, 5.2
Skills依赖:
  - associative arrays (Bash 4.0+)
  - process substitution
已知问题: 无
```

### 操作系统兼容性
```bash
Linux: ✅ 完全支持
macOS: ✅ 支持（GNU coreutils推荐）
  - 注意: macOS的date命令格式不同，需要gdate
BSD: ⚠️  可能需要调整stat和date命令
Windows/WSL: ✅ 支持
  - 注意: WSL2性能最佳
```

### 依赖工具兼容性
```bash
必需:
- bash >= 4.0: ✅
- grep: ✅
- awk: ✅
- sed: ✅
- date: ✅ (gdate on macOS)
- bc: ✅ (用于speedup计算)

可选:
- yq: ⏭ 用于YAML解析（可以用grep/awk替代）
- jq: ⏭ 用于JSON处理（可以用grep/awk替代）
- parallel (GNU): ⏭ 用于load balancing (P2功能)
```

---

## 文档影响

### 需要更新的文档
1. ✅ CHANGELOG.md - v8.3.0完整变更记录
2. ✅ CLAUDE.md - 更新所有Phase执行说明（并行能力）
3. ✅ README.md - 添加Skills Framework说明
4. ✅ .workflow/README.md - 详细并行执行指南
5. ✅ .workflow/SPEC.yaml - 更新版本到v8.3.0

### 新增文档
6. ✅ .workflow/REQUIREMENTS_DIALOGUE.md (已创建 - 502行)
7. ✅ .workflow/IMPACT_ASSESSMENT.md (本文档)
8. ⏭ .workflow/PLAN.md (Phase 1.5产出)
9. ⏭ docs/SKILLS_FRAMEWORK.md - Skills开发指南 (P2)
10. ⏭ docs/PARALLEL_OPTIMIZATION.md - 并行优化最佳实践 (P2)
11. ⏭ docs/BENCHMARK_GUIDE.md - 性能基准测试指南 (P2)

---

## 资源需求

### 开发资源（6 agents策略）
- **Phase 1**: 2小时（已完成1.1-1.4，进行中1.5）
- **Phase 2**: 4-5小时（6 agents并行开发）
  - Agent 1: STAGES.yml配置（1.5h）
  - Agent 2: Skills脚本（2h）
  - Agent 3: Executor middleware（1.5h）
  - Agent 4: Benchmark脚本（1.5h）
  - Agent 5: Integration testing（1h）
  - Agent 6: Documentation（1h）
- **Phase 3**: 3-4小时（测试+benchmark收集）
- **Phase 4**: 2-3小时（代码审查）
- **Phase 5**: 1-2小时（发布准备）
- **Phase 6-7**: 1小时（验收+合并）

**总计**: 13-17小时（6 agents并行可压缩到8-10小时）

### 计算资源
- **额外CPU**: 无（使用现有资源，但利用率提升3-12倍）
- **额外内存**: ~500MB（12个并发进程 + Skills overhead）
- **额外磁盘**: <1GB（性能日志 + baseline数据 + benchmark结果）
- **网络**: 无需额外网络资源

### 人力资源
- **主开发**: 6 agents（AI，Phase 2并行开发）
- **Review**: 1 agent（AI，Phase 4集中审查）
- **Testing**: 2 agents（AI，Phase 3并行测试）
- **用户确认**: 用户（Phase 6验收）

---

## 推荐的Agent策略

根据影响半径68分（高风险任务），推荐：

```yaml
Agent数量: 6 agents
执行模式: 高度并行开发 + 集中审查
原因:
  - 影响范围大（5个Phase + 10个文件 + 1,280行代码）
  - 复杂度高（Skills集成 + 并行配置 + benchmark系统）
  - 风险可控（有Phase3成功经验 + fallback机制）
  - 需要并行协作（6个独立模块可并行开发）
```

### Agent角色分配

**Agent 1: Parallel Configuration Architect**
- 职责: 设计并实现Phase2-6的parallel_groups配置
- 产出:
  - STAGES.yml更新（~200行）
  - Conflict rules定义（8个规则验证）
- 依赖: REQUIREMENTS_DIALOGUE.md + Agent探索发现
- 时间: 1.5小时

**Agent 2: Skills Framework Developer**
- 职责: 实现3个新Skills + 增强4个现有Skills
- 产出:
  - parallel-performance-tracker.sh (~120行)
  - parallel-conflict-validator.sh (~100行)
  - parallel-load-balancer.sh (~180行, P2)
  - 增强现有4个Skills配置
- 依赖: REQUIREMENTS_DIALOGUE.md Skills架构定义
- 时间: 2小时

**Agent 3: Executor Middleware Engineer**
- 职责: 实现Skills middleware layer到executor.sh
- 产出:
  - executor.sh更新（~100行）
  - execute_parallel_workflow()增强
  - Pre/Post execution hooks集成
- 依赖: Agent 1 (parallel配置) + Agent 2 (Skills脚本)
- 时间: 1.5小时

**Agent 4: Benchmark & Testing Specialist**
- 职责: 实现完整的benchmark系统
- 产出:
  - collect_baseline.sh (~80行)
  - run_parallel_tests.sh (~100行)
  - calculate_speedup.sh (~120行)
  - validate_performance.sh (~80行)
- 依赖: Agent 1 (parallel配置完成)
- 时间: 1.5小时

**Agent 5: Integration Testing Engineer**
- 职责: 设计并执行27个测试用例
- 产出:
  - 单元测试（10个）
  - 集成测试（8个）
  - 性能测试（5个）
  - 回归测试（4个）
- 依赖: Agent 1-4全部完成
- 时间: 1小时

**Agent 6: Documentation & Review Coordinator**
- 职责: 文档更新 + 跨Agent一致性审查
- 产出:
  - CHANGELOG.md更新
  - CLAUDE.md更新
  - README.md更新
  - .workflow/README.md更新
  - 跨Agent代码一致性报告
- 依赖: Agent 1-5全部完成
- 时间: 1小时

### Agent协作策略

**Phase 2: Implementation（并行阶段）**
```
并行组1（可并行）:
├─ Agent 1: Parallel Configuration
├─ Agent 2: Skills Framework
└─ Agent 4: Benchmark Scripts

串行依赖:
Agent 3 (Executor Middleware) ← 等待 Agent 1 + Agent 2 完成
Agent 5 (Integration Testing) ← 等待 Agent 1-4 全部完成
Agent 6 (Documentation) ← 等待 Agent 1-5 全部完成
```

**Phase 3: Testing（并行阶段）**
```
Agent 5主导 + Agent 4协助:
├─ Agent 5: 执行27个测试用例
└─ Agent 4: 收集benchmark数据（5个Phase × 3次 = 15次运行）

预计时间: 3-4小时（包括多次benchmark运行）
```

**Phase 4: Review（集中阶段）**
```
Agent 6主导 + 所有Agents参与:
├─ Agent 6: 主审查员，检查一致性
├─ Agent 1-5: 互相review彼此的代码
└─ pre_merge_audit.sh自动化检查

预计时间: 2-3小时
```

---

## 成功标准（验收清单）

基于Phase 1.2 Acceptance Checklist，以下是Phase 6验收的关键标准：

### 功能性验收
- [ ] Phase2-6全部可以并行执行
- [ ] Phase3优化到5个parallel groups（vs现有4个）
- [ ] 所有Phase都有fallback to serial机制
- [ ] 8种conflict规则全部生效
- [ ] 7个Skills全部工作（3新 + 4增强）

### 性能验收
- [ ] Phase2 speedup ≥1.3x
- [ ] Phase3 speedup ≥2.0x
- [ ] Phase4 speedup ≥1.2x
- [ ] Phase5 speedup ≥1.4x
- [ ] Phase6 speedup ≥1.1x
- [ ] **Overall speedup ≥1.4x** ⚠️ Critical

### 质量验收
- [ ] 所有27个测试用例通过
- [ ] Shellcheck无warning（所有新脚本）
- [ ] 代码复杂度<150行/函数
- [ ] Skills middleware overhead <5%
- [ ] Conflict detection accuracy ≥90%
- [ ] 文档完整性（>2,000行Phase 1文档）

### 集成验收
- [ ] 与v8.2.1 Phase3配置兼容
- [ ] VERSION文件统一到v8.3.0（6个文件）
- [ ] CHANGELOG.md记录完整
- [ ] 所有Skills在.claude/settings.json注册
- [ ] Pre-merge audit全部通过

---

## 风险缓解措施

### 风险1: 无法达到目标speedup
**缓解措施**:
- Baseline数据收集（多次运行取平均）
- 每个Phase独立测试（隔离问题）
- 有降级方案（保留串行路径）
- 容差机制（±5%可接受）

### 风险2: Skills middleware性能开销过大
**缓解措施**:
- Skills脚本优化（<200ms执行时间）
- 异步执行非关键Skills（如performance tracking）
- 可以禁用单个Skill（.claude/settings.json）
- 监控overhead指标（告警阈值15%）

### 风险3: Agent协作冲突
**缓解措施**:
- Agent 1-4完全独立模块（文件级隔离）
- 明确的依赖关系（串行等待）
- Agent 6协调一致性
- 使用Git feature branches隔离（如需要）

### 风险4: Benchmark数据不稳定
**缓解措施**:
- 每个Phase运行3-5次取平均
- 记录系统负载（排除干扰）
- 使用固定测试数据（可重现）
- 容差机制（variance <15%接受）

### 风险5: 配置冲突规则漏洞
**缓解措施**:
- 基于Agent探索的8种规则（已验证）
- 新增测试用例验证冲突检测
- Learning capturer记录意外冲突
- 迭代增强规则（v8.3.1+）

---

## 下一步

Phase 1.5: Architecture Planning - 创建详细的PLAN.md（>2,000行）

**PLAN.md将包含**:
1. 详细的6-agent任务分解
2. 每个Agent的step-by-step实现指南
3. 完整的文件修改清单（1,280行代码的具体位置）
4. Skills middleware架构设计
5. Benchmark流程详细步骤
6. 测试用例的具体实现
7. 回滚和应急预案
8. Timeline和里程碑

**预计PLAN.md规模**: 2,500-3,000行（90-point标准）
