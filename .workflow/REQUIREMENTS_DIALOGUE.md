# Requirements Dialogue - Activate Parallel Executor

**Feature**: 激活现有的并行执行系统
**Branch**: feature/activate-parallel-executor
**Date**: 2025-10-28

---

## 用户需求

用户发现通过深度压力测试，Claude Enhancer v8.2.0 有一个完善的并行执行系统（parallel_executor.sh, STAGES.yml），但从未被主工作流调用，导致：
- 预期的2.44x性能提升未实现
- 196分钟时间节省未兑现
- 8个并发Agent能力闲置

用户要求：
1. 用 Claude Enhancer 工作流来开发这个修复
2. 采用渐进式改进策略（先60分，不追求100分）
3. 聚焦核心问题：让并行执行器跑起来

---

## 核心问题

### 问题1: Phase命名不一致
- **现状**: STAGES.yml 使用 P1/P2/P3，manifest.yml 使用 Phase1/Phase2/Phase3
- **影响**: 需要映射层，容易出错
- **优先级**: P0

### 问题2: executor.sh 未集成 parallel_executor.sh
- **现状**: parallel_executor.sh (466行) 完整但从未被调用
- **影响**: 并行能力完全闲置
- **优先级**: P0

### 问题3: 缺少基本日志
- **现状**: .workflow/logs/parallel_execution.log 不存在
- **影响**: 无法验证并行执行效果
- **优先级**: P0

---

## 技术方案选择

### 方案A: 完整实现（ChatGPT建议）
包含：
- yq 替换 grep
- JSON Schema 校验
- 完整的信号处理
- JSONL 结构化日志
- --mode 4种模式
- dry-run 解释计划
- DAG 调度
- 额外的 Skills

**评估**: 过度设计，工作量巨大，违背"先跑起来"原则

### 方案B: 渐进式改进（推荐）✅
**Phase 1**: 核心问题修复（今天）
- 统一 Phase 命名
- 基本集成 parallel_executor
- 简单文本日志
- 基本错误处理

**Phase 2**: 验证效果（本周）
- 实际运行 Phase3
- 对比串行 vs 并行时间
- 收集真实数据

**Phase 3**: 针对性优化（下月）
- **只修复实际遇到的问题**
- 如果 grep 出错 → 引入 yq
- 如果需要调试 → 添加 --mode
- 如果日志难分析 → 改 JSONL

**评估**: 务实，可控，符合用户要求

---

## 范围界定

### 本次迭代包含（P0）
1. ✅ 统一 STAGES.yml 的 Phase 命名（P1→Phase1）
2. ✅ 在 executor.sh 集成 parallel_executor.sh
3. ✅ 创建基本日志目录
4. ✅ 添加基本错误处理（trap）
5. ✅ 简单测试验证

### 本次迭代不包含（延后）
- ❌ yq 替换 grep（除非必要）
- ❌ JSON Schema 校验（过度设计）
- ❌ 完整的 --mode 参数（只需 auto）
- ❌ JSONL 日志（普通文本够用）
- ❌ dry-run 模式（优先级低）
- ❌ DAG 调度（为时过早）
- ❌ 额外 Skills（现有的都没做完）
- ❌ ML/Autotune（明显过度）

---

## 验收标准

### 功能验收
- [ ] STAGES.yml 所有 P1-P7 改为 Phase1-Phase7
- [ ] executor.sh 能够检测 STAGES.yml 配置并调用 parallel_executor.sh
- [ ] Phase3 能够以并行模式执行（如果配置了并行组）
- [ ] 生成日志文件 .workflow/logs/parallel.log
- [ ] 子进程失败时主进程退出码非0

### 性能验收
- [ ] Phase3 并行执行时间 < 串行执行时间
- [ ] 理想目标：加速比 ≥ 1.5x
- [ ] 最低要求：能够并行运行不出错

### 质量验收
- [ ] 所有现有测试通过
- [ ] 无语法错误（bash -n）
- [ ] Shellcheck 无 warning
- [ ] 文档更新（CHANGELOG.md）

---

## 风险评估

### 高风险
无

### 中风险
1. **STAGES.yml 格式解析**
   - 风险: grep 可能解析错误
   - 缓解: 先用简单配置测试，复杂情况P2引入yq
   - 回退: 保留串行执行路径

2. **并行冲突**
   - 风险: 多个Agent写同一文件
   - 缓解: 依赖现有的8条冲突检测规则
   - 回退: 自动降级到串行

### 低风险
3. **性能未达预期**
   - 风险: 实际加速比 < 1.5x
   - 缓解: 这是优化问题，不影响功能
   - 回退: 可以禁用并行配置

---

## 依赖与约束

### 依赖
- ✅ parallel_executor.sh 已存在且完整
- ✅ STAGES.yml 配置完善
- ✅ manifest.yml 配置正确
- ✅ conflict_detector.sh 和 mutex_lock.sh 存在

### 约束
- ⛔ 不引入新的外部依赖（如 yq）
- ⛔ 不破坏现有串行执行路径
- ⛔ 不修改 parallel_executor.sh 核心逻辑（已验证）
- ⛔ 保持简单（KISS 原则）

---

## 时间估算

- Phase 1.1-1.2: 需求讨论 ✅ (30分钟)
- Phase 1.3: 技术发现 (30分钟)
- Phase 1.4: 影响评估 (15分钟)
- Phase 1.5: 架构规划 (45分钟)
- Phase 2: 实现 (1小时)
- Phase 3: 测试 (30分钟)
- Phase 4: 审查 (30分钟)
- Phase 5: 发布 (15分钟)

**总计**: ~4小时

---

## 用户确认

✅ 用户要求：用 Claude Enhancer 工作流开发
✅ 用户要求：渐进式改进，不追求完美
✅ 用户要求：聚焦核心问题

**下一步**: Phase 1.3 Technical Discovery
