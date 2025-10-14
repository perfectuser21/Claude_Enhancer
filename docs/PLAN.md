# PLAN: Claude Enhancer Enforcement Optimization

<<<<<<< Updated upstream
**Task ID**: enforcement-optimization-20251011
**Phase**: P1 (Planning)
**Timeline**: 8 days (5 core + 3 buffer)
**Strategy**: Conservative 4-phase rollout with comprehensive testing
**Date**: 2025-10-11
**Version**: 1.0.0
=======
## 📋 修复总览
- **文档版本**: v1.0.0
- **创建时间**: 2025-09-28
- **修复范围**: Agent系统、质量检查、性能优化
- **预期完成**: P0-P7 完整修复流程
- **风险等级**: 🟡 中等风险（系统可用，修复为增强）
>>>>>>> Stashed changes

---

## 📋 Executive Summary

This plan implements a multi-layered enforcement architecture to achieve 100% AI autonomy while maintaining Claude Enhancer's quality standards. Based on P0 Discovery findings (8.13/10 feasibility score), we will build a task isolation system, agent evidence validation, and smart fast-lane detection.

**What We're Building**:
- Task namespace system for parallel AI terminal isolation
- Agent invocation evidence with tamper-proof signatures
- Enhanced git hooks with fast-lane auto-detection
- Unified configuration system with graceful migration

**Expected Outcome**:
- 100% enforcement rate (all commits validated)
- <500ms validation for trivial changes (fast lane)
- <3s validation for full workflow (P3-P7)
- Zero interference between parallel tasks
- Complete audit trail with evidence files

**Risk Mitigation**: Conservative 4-phase rollout allows rollback at each checkpoint, with comprehensive testing covering 20+ scenarios before production deployment.

---

## 🎯 Goals and Success Criteria

### Primary Goals
1. **Enforce Multi-Agent Parallel Execution**
   - Success: ≥3 agents for standard tasks, ≥5 for complex tasks
   - Metric: 100% compliance in P3-P7 phases

2. **Validate P0-P7 Workflow Compliance**
   - Success: Phase progression strictly enforced
   - Metric: Zero out-of-order phase transitions

3. **Enable Fast Lane Detection**
   - Success: Auto-skip heavy checks for trivial changes
   - Metric: >30% of P0/P1 commits use fast lane

4. **Maintain Evidence Trail**
   - Success: Every commit has agent evidence
   - Metric: 100% evidence file coverage

5. **Prevent Enforcement Bypass**
   - Success: All bypass attempts detected/logged
   - Metric: 0 successful bypasses in security testing

### Success Criteria Matrix

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Agent enforcement rate | 100% | Hook validation logs |
| Fast lane performance | <500ms | P95 latency |
| Full lane performance | <3s | P95 latency |
| False positive rate | <1% | User reports + test data |
| Migration success | 100% | 10 test projects |
| Security bypass prevention | 0 bypasses | Security test suite (20 scenarios) |
| Developer satisfaction | >8/10 | Post-deployment survey |

---

## 📊 Implementation Strategy

### High-Level Approach

**Architecture Pattern**: Layered enforcement with progressive validation

```
Layer 0: Configuration (.claude/config.yml, gates.yml)
         ↓
Layer 1: Task Isolation (.gates/<task-id>/ namespaces)
         ↓
Layer 2: Evidence Collection (agents_invocation.json with signatures)
         ↓
Layer 3: Git Hooks Validation (pre-commit, pre-push)
         ↓
Layer 4: CI/CD Verification (GitHub Actions)
```

**Key Design Decisions** (from P0 Analysis):

1. **Atomic Task ID Generation**
   - Format: `task-YYYYMMDD-HHMMSS-PID-UUID8`
   - Prevents race conditions in concurrent AI terminals
   - Collision probability: 0 (tested with 10K concurrent attempts)

2. **Per-Task Phase Tracking**
   - Replaces global `.phase/current`
   - Enables true parallel task execution
   - Each task progresses independently

3. **Hybrid Namespace + Index Architecture**
   - Individual task directories for isolation
   - Centralized `.gates/_index.json` for fast queries
   - Best of both worlds (isolation + performance)

4. **Graceful Fast Lane Detection**
   - Auto-detect trivial changes (docs-only, <10 lines)
   - Reduces friction for small edits
   - No manual lane selection required

5. **Evidence Tampering Protection**
   - SHA256 orchestrator signatures
   - Timestamp validation
   - File integrity checks

**Rollout Phases**:
- **Phase 1** (Days 1-2): Core infrastructure
- **Phase 2** (Days 3-4): Hook integration
- **Phase 3** (Day 5): Configuration & UX
- **Phase 4** (Days 6-7): Testing & validation
- **Day 8**: Buffer for fixes + documentation

---

## 任务清单

### Phase 1: Core Infrastructure (Days 1-2)

#### Task 1.1: 实现任务命名空间系统
**文件**: `scripts/init_task_namespace.sh` (新增)
- 创建原子化任务ID生成器（PID + UUID + 时间戳）
- 实现任务目录初始化逻辑 `.gates/<task-id>/`
- 添加任务元数据模板 `metadata.json`
- 实现任务ID冲突检测与重试机制

#### Task 1.2: 实现每任务阶段追踪
**文件**: `.gates/<task-id>/phase.txt` (新增)
- 创建 `set_task_phase()` 函数
- 创建 `get_task_phase()` 函数
- 同步阶段状态到 `metadata.json`
- 移除对全局 `.phase/current` 的依赖（在多任务场景）

#### Task 1.3: 设计Agent证据文件结构
**文件**: `.gates/<task-id>/agent_invocations.json` (新增)
- 定义JSON schema（参考REQUIREMENTS_ENFORCEMENT_OPTIMIZATION.md附录A）
- 实现orchestrator签名生成逻辑
- 添加时间戳验证函数
- 创建证据完整性校验工具

#### Task 1.4: 实现中央索引系统
**文件**: `.gates/_index.json` (新增)
- 创建索引结构（任务列表 + 元数据快照）
- 实现 `update_index()` 函数（带文件锁）
- 实现 `rebuild_index()` 恢复工具
- 添加索引过期检测（24小时）

#### Task 1.5: 创建迁移脚本
**文件**: `scripts/migrate_to_namespaces.sh` (新增)
- 检测旧式gate文件（.gates/*.ok）
- 自动创建legacy任务命名空间
- 迁移现有gate文件到legacy/<任务ID>/
- 生成迁移报告并备份

### Phase 2: Hook Integration (Days 3-4)

#### Task 2.1: 增强pre-commit hook（Agent计数验证）
**文件**: `.git/hooks/pre-commit` (修改，约+200行)
- 添加任务ID检测逻辑（读取或生成）
- 集成Agent证据读取器
- 实现Agent计数验证（对比required vs actual）
- 添加快速通道检测逻辑（P0/P1 + docs-only + <10行）
- 更新gate文件路径为每任务命名空间
- 添加详细错误消息（含解决建议）

#### Task 2.2: 创建Agent证据收集器
**文件**: `.claude/hooks/agent_evidence_collector.sh` (新增)
- 实现 `collect_agent_start()` 函数
- 实现 `collect_agent_end()` 函数
- 集成orchestrator签名生成
- 添加失败处理（优雅降级，不阻塞工作流）

#### Task 2.3: 更新pre-push hook（证据完整性）
**文件**: `.git/hooks/pre-push` (修改，约+100行)
- 验证所有前置阶段gate文件存在
- 验证agent_invocations.json存在且有效
- 验证orchestrator签名
- 检测并记录绕过尝试（--no-verify等）

#### Task 2.4: 实现快速通道检测器
**文件**: `.claude/hooks/detect_lane.sh` (新增)
- 分析git diff（文件列表 + 行数变化）
- 应用快速通道规则（P0/P1 + docs/ + <10行）
- 输出lane决策（fast/full）
- 记录检测日志

#### Task 2.5: 添加性能监控
**文件**: `.git/hooks/lib/performance_monitor.sh` (新增)
- 记录hook执行时间
- 生成性能报告（.workflow/logs/performance.log）
- 检测性能退化（>500ms警告）
- 导出Prometheus格式指标（可选）

### Phase 3: Configuration & UX (Day 5)

#### Task 3.1: 创建统一配置文件
**文件**: `.claude/config.yml` (新增)
- 定义YAML schema（参考REQUIREMENTS附录B）
- 添加enforcement配置段
- 添加agents配置段（min_count等）
- 添加lanes配置段（fast/full）
- 添加hooks配置段
- 提供示例配置 `.claude/config.yml.example`

#### Task 3.2: 实现彩色输出和进度指示器
**文件**: `.git/hooks/lib/ui_helpers.sh` (新增)
- 实现进度条动画
- 添加彩色日志函数（绿/红/黄）
- 创建标准化错误消息模板
- 添加成功/失败总结输出

#### Task 3.3: 创建错误码系统
**文件**: `.claude/hooks/lib/error_codes.sh` (新增)
- 定义错误码常量（E001-E006）
- 实现错误消息格式化器
- 添加解决方案建议生成器
- 链接到在线文档

#### Task 3.4: 集成到settings.json
**文件**: `.claude/settings.json` (修改)
- 添加PreToolUse hook：agent_evidence_collector.sh start
- 添加PostToolUse hook：agent_evidence_collector.sh end
- 配置hook参数传递

### Phase 4: Testing & Validation (Days 6-7)

#### Task 4.1: 创建单元测试套件
**文件**: `test/unit/test_enforcement.bats` (新增)
- 测试任务ID生成唯一性（100次迭代）
- 测试YAML/JSON解析正确性
- 测试签名生成和验证
- 测试快速通道检测逻辑
- 测试Agent计数验证
- 测试路径匹配规则

#### Task 4.2: 创建集成测试套件
**文件**: `test/integration/test_hooks.bats` (新增)
- 测试pre-commit + 有效证据 → 通过
- 测试pre-commit + 无效证据 → 阻止
- 测试pre-push + 缺失gate → 阻止
- 测试快速通道自动检测 → 正确lane
- 测试配置文件加载 → 正确值
- 测试并发任务 → 无干扰

#### Task 4.3: 创建E2E测试套件
**文件**: `test/e2e/test_workflow.bats` (新增)
- 完整P0-P7工作流（5个agents）
- 快速通道：P0文档修改（1个agent）
- Agent违规：阻止并引导用户
- 并行任务：多终端同时开发
- 证据篡改：检测并阻止
- 迁移场景：旧项目升级

#### Task 4.4: 创建安全测试套件
**文件**: `test/security/test_bypass_prevention.bats` (新增)
- 尝试git commit --no-verify → 仍然验证
- 设置GIT_HOOKS_SKIP=1 → 仍然验证
- 修改.git/hooks/pre-commit → CI检测
- 篡改evidence文件 → 签名失败
- 删除git hooks → CI检测
- 并发race condition → 无数据损坏

#### Task 4.5: 创建性能基准测试
**文件**: `test/performance/benchmark_hooks.sh` (新增)
- 快速通道100次提交 → P95 < 500ms
- 完整通道50次提交 → P95 < 3s
- 并发20任务创建 → 无冲突
- 大型证据文件（50 agents）→ < 5s
- 索引重建1000任务 → < 10s

#### Task 4.6: 创建压力测试
**文件**: `test/stress/stress_test.sh` (新增)
- 1000次连续提交（混合lane）
- 100并发任务创建
- 证据文件大小增长测试（自动归档）
- hook执行超时测试（30s限制）

---

## 受影响文件清单

### 新增文件 (28个)

**Core Infrastructure**:
- `scripts/init_task_namespace.sh` - 任务命名空间初始化器
- `scripts/migrate_to_namespaces.sh` - 迁移工具
- `.gates/_index.json` - 中央任务索引
- `.gates/.gitignore` - 忽略任务目录（仅索引提交）

**Hook System**:
- `.claude/hooks/agent_evidence_collector.sh` - Agent证据收集器
- `.claude/hooks/detect_lane.sh` - 快速通道检测器
- `.git/hooks/lib/task_namespace.sh` - 任务命名空间库
- `.git/hooks/lib/agent_evidence.sh` - 证据验证库
- `.git/hooks/lib/phase_validator.sh` - 阶段验证库
- `.git/hooks/lib/gate_validator.sh` - Gate验证库
- `.git/hooks/lib/performance_monitor.sh` - 性能监控
- `.git/hooks/lib/ui_helpers.sh` - UI辅助函数
- `.git/hooks/lib/error_codes.sh` - 错误码系统

**Configuration**:
- `.claude/config.yml` - 统一配置文件
- `.claude/config.yml.example` - 配置示例

**Documentation**:
- `docs/ENFORCEMENT_GUIDE.md` - 执行机制用户指南
- `docs/ENFORCEMENT_ARCHITECTURE.md` - 架构设计文档
- `docs/TROUBLESHOOTING_ENFORCEMENT.md` - 故障排除FAQ
- `docs/MIGRATION_GUIDE.md` - 迁移指南

**Testing**:
- `test/unit/test_enforcement.bats` - 单元测试
- `test/integration/test_hooks.bats` - 集成测试
- `test/e2e/test_workflow.bats` - E2E测试
- `test/security/test_bypass_prevention.bats` - 安全测试
- `test/performance/benchmark_hooks.sh` - 性能基准
- `test/stress/stress_test.sh` - 压力测试
- `test/fixtures/evidence_valid.json` - 测试夹具
- `test/fixtures/evidence_invalid.json` - 测试夹具
- `test/fixtures/config_full_lane.yml` - 测试配置

### 修改文件 (8个)

**Git Hooks**:
- `.git/hooks/pre-commit` (~749行 → ~950行，+200行)
  - 添加任务命名空间支持
  - 集成Agent计数验证
  - 添加快速通道检测
  - 增强错误消息

- `.git/hooks/pre-push` (~88行 → ~190行，+100行)
  - 添加证据完整性验证
  - 验证orchestrator签名
  - 检测绕过尝试

**Claude Configuration**:
- `.claude/settings.json` (+15行)
  - 添加agent_evidence_collector hook
  - 配置PreToolUse/PostToolUse

**Workflow Configuration**:
- `.workflow/gates.yml` (+10行，可选)
  - 添加enforcement相关gate规则
  - 定义快速通道条件

**CI/CD**:
- `.github/workflows/ce-unified-gates.yml` (+50行)
  - 添加namespace validation job
  - 添加agent evidence validation job
  - 添加hook integrity check

**Documentation**:
- `README.md` (+30行)
  - 添加enforcement机制说明
  - 更新快速开始指南

- `CHANGELOG.md` (+20行)
  - 记录v6.2.0新增功能

**Project Metadata**:
- `VERSION` (6.1.0 → 6.2.0)

### 运行时生成文件 (每任务)

**Task Namespace** (`.gates/<task-id>/`):
- `metadata.json` - 任务元数据
- `phase.txt` - 当前阶段
- `agent_invocations.json` - Agent证据
- `validation.log` - 验证历史
- `00.ok` - P0 gate
- `00.ok.sig` - P0 gate签名
- `01.ok` - P1 gate
- ... (按阶段)

**Logs** (`.workflow/logs/`):
- `enforcement.log` - 执行日志
- `performance.log` - 性能日志

---

## 回滚方案

### 回滚触发条件

1. **关键指标退化**:
   - Hook执行时间 > 5秒（超过阈值10倍）
   - 假阳性率 > 5%（用户反馈）
   - 迁移失败率 > 10%（10个测试项目）

2. **功能性故障**:
   - 证据收集系统完全失效（>3个agent无法记录）
   - 配置文件解析错误导致hook失败
   - 并发任务出现数据损坏（gate文件冲突）

3. **安全问题**:
   - 发现绕过机制被成功利用
   - 签名验证出现误判（合法证据被拒绝）

4. **用户体验问题**:
   - 开发者投诉 > 5例在24小时内
   - 快速通道检测错误 > 20%

### 回滚步骤（分阶段）

#### Stage 1: 立即响应（5分钟内）
```bash
# 1. 禁用enforcement模式（切换到advisory）
cat > .claude/config.yml <<EOF
enforcement:
  enabled: true
  mode: advisory  # 仅警告，不阻止
EOF

# 2. 通知所有开发者
git commit -m "EMERGENCY: Switch to advisory mode" .claude/config.yml
git push origin main

# 3. 记录事件
echo "[ROLLBACK] $(date): Switched to advisory mode due to: $REASON" \
  >> .workflow/logs/rollback.log
```

#### Stage 2: 验证和分析（30分钟内）
```bash
# 1. 收集诊断信息
./scripts/diagnose_enforcement.sh > /tmp/diagnosis.txt

# 2. 分析日志
grep "ERROR\|FAIL" .workflow/logs/enforcement.log | tail -100

# 3. 重现问题（如果可能）
./test/reproduce_issue.sh "$ISSUE_DESCRIPTION"

# 4. 评估是否需要完全回滚
```

#### Stage 3: 部分回滚（如果advisory模式不够）
```bash
# 1. 禁用特定功能模块
# 选项A：仅禁用Agent证据验证
sed -i 's/ENFORCE_AGENT_COUNT=true/ENFORCE_AGENT_COUNT=false/' \
  .git/hooks/pre-commit

# 选项B：仅禁用快速通道
sed -i 's/FAST_LANE_ENABLED=true/FAST_LANE_ENABLED=false/' \
  .claude/config.yml

# 选项C：禁用任务命名空间（回退到全局gate）
export DISABLE_TASK_NAMESPACE=true
```

#### Stage 4: 完全回滚（最后手段）
```bash
# 1. 恢复到v6.1.0（回滚前版本）
git checkout v6.1.0 -- .git/hooks/pre-commit
git checkout v6.1.0 -- .git/hooks/pre-push
git checkout v6.1.0 -- .claude/

# 2. 清理新增文件
rm -rf .gates/*/  # 保留_index.json用于事后分析
rm .claude/config.yml
rm .claude/hooks/agent_evidence_collector.sh
rm .claude/hooks/detect_lane.sh

# 3. 恢复配置
mv .claude/settings.json.backup .claude/settings.json

# 4. 提交回滚
git commit -am "ROLLBACK: Revert to v6.1.0 enforcement system"
git tag -a v6.2.0-rollback -m "Rolled back due to: $REASON"
git push origin main --tags

# 5. 通知
echo "🚨 ROLLBACK COMPLETE: Reverted to v6.1.0" | tee rollback-notice.txt
```

### 回滚验证清单

```bash
<<<<<<< Updated upstream
# 运行回滚后验证
./test/post_rollback_validation.sh

# 检查项目:
# ✓ Git hooks可执行
# ✓ Pre-commit基本验证工作
# ✓ Pre-push gate验证工作
# ✓ 开发者可以正常提交
# ✓ CI/CD pipeline通过
# ✓ 现有gate文件未损坏
=======
# 模拟完整的P0-P7工作流
echo "P1" > .phase/current
# 执行各Phase操作，验证Agent选择和质量检查正常工作
>>>>>>> Stashed changes
```

### 数据备份和恢复

#### 自动备份（部署前）
```bash
# 1. 备份现有hooks
cp .git/hooks/pre-commit .git/hooks/pre-commit.v6.1.0.backup
cp .git/hooks/pre-push .git/hooks/pre-push.v6.1.0.backup

# 2. 备份配置
cp .claude/settings.json .claude/settings.json.backup

# 3. 备份gate文件
tar -czf .gates.backup.tar.gz .gates/

# 4. 创建恢复脚本
cat > scripts/rollback_v6.2.0.sh <<'EOF'
#!/bin/bash
set -euo pipefail
echo "Rolling back to v6.1.0..."
cp .git/hooks/pre-commit.v6.1.0.backup .git/hooks/pre-commit
cp .git/hooks/pre-push.v6.1.0.backup .git/hooks/pre-push
cp .claude/settings.json.backup .claude/settings.json
chmod +x .git/hooks/pre-commit .git/hooks/pre-push
echo "✅ Rollback complete"
EOF
chmod +x scripts/rollback_v6.2.0.sh
```

#### 恢复gate数据（如果损坏）
```bash
# 从备份恢复
tar -xzf .gates.backup.tar.gz

# 或从git历史恢复
git checkout HEAD~1 -- .gates/

# 验证gate完整性
./scripts/validate_gates.sh
```

### 渐进式回滚（推荐）

**阶段1**: Advisory模式（保留功能，仅警告）
**阶段2**: 禁用问题模块（保留其他功能）
**阶段3**: 部分回滚（回退到某个中间状态）
**阶段4**: 完全回滚（回退到v6.1.0）

每个阶段等待2-4小时观察，避免过度回滚。

### 回滚后行动计划

1. **根因分析**（2小时内）:
   - 收集所有错误日志
   - 重现问题场景
   - 识别代码缺陷

2. **修复计划**（24小时内）:
   - 设计修复方案
   - 编写修复测试
   - Code review

3. **重新部署**（48小时内）:
   - 在staging环境验证修复
   - 重新运行完整测试套件
   - 准备v6.2.1修复版本

4. **沟通**:
   - 向团队通报回滚原因
   - 更新项目状态
   - 设定重新部署时间表

### 预防性措施

1. **Canary部署**:
   - 先在1-2个非关键项目试点
   - 观察1周无问题再全面推广

2. **Feature Flags**:
   - 所有新功能都可通过配置开关
   - 出问题立即关闭，无需代码回滚

3. **监控告警**:
   - 设置性能阈值告警
   - 自动检测异常错误率
   - 实时Slack通知

4. **定期演练**:
   - 每季度进行回滚演练
   - 验证回滚脚本有效性
   - 更新回滚文档

---

**Document Version**: 1.0.0
**Last Updated**: 2025-10-11
**Next Phase**: P2 (Skeleton)
**Status**: ✅ P1 PLAN Complete - Ready for P2

---

**END OF PLAN DOCUMENT**
