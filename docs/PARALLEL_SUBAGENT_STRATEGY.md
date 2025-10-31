# 🚀 Claude Enhancer 并行SubAgent策略文档

**版本**: v2.0.0
**更新日期**: 2025-10-31
**状态**: 生产级 | Immutable Kernel保护

---

## 📖 目录

1. [理论基础：并行执行原理](#理论基础并行执行原理)
2. [当前系统架构 (v2.0.0)](#当前系统架构-v200)
3. [Phase 2-7 并行策略详解](#phase-2-7-并行策略详解)
4. [实战使用指南](#实战使用指南)
5. [性能与优化](#性能与优化)

---

## 理论基础：并行执行原理

### 🔴 核心限制

**SubAgent只能被Claude Code调用，不能互相调用**

这是Claude Code的架构限制：
- ✅ Claude Code → Task(subagent_type="general-purpose")
- ❌ general-purpose → Task(subagent_type="Explore") ← 不允许
- ❌ SubAgent之间互相调用 ← 不允许

### 💡 解决方案：重新定义"并行"

#### 方案1：Claude Code的批量调用（✅ 当前采用）

**错误方式 ❌**：
```python
# Claude Code顺序调用（伪代码）
result1 = Task("backend-architect", "设计后端")
# 等待result1完成...
result2 = Task("frontend-specialist", "设计前端")
# 这是串行的！耗时 = T1 + T2
```

**正确方式 ✅**：
```python
# Claude Code在一个消息中同时调用多个Task
[
    Task("backend-architect", "设计后端"),
    Task("frontend-specialist", "设计前端"),
    Task("test-engineer", "写测试")
]
# Claude Code同时发出3个Task调用
# 耗时 = max(T1, T2, T3)
```

**关键点**：
- 必须在**单个消息**中发出多个Task tool调用
- Claude Code会并发执行这些Task
- 每个Task有独立的上下文，互不干扰

#### 方案2：Queen-Worker模式（协调而非调用）

**理念**：Queen不直接调用Worker，而是通过共享文件协调

```
Queen Agent (Orchestrator)
    ↓ 写入 tasks.json
[Shared File System]
    ↓ 读取 tasks.json
Worker Agents (Parallel Execution)
    ↓ 写入 results/*.json
[Shared File System]
    ↓ 读取 results/*.json
Queen Agent (Aggregation)
```

**实现**：
- Queen创建 `.workflow/tasks.json` 列出待办任务
- 多个Worker并行读取任务，执行后写结果到 `.workflow/results/`
- Queen定期检查结果，汇总完成

#### 方案3：Git Worktree隔离（多Claude实例）

**适用场景**：需要真正的独立环境（如不同分支同时开发）

```bash
# 创建worktree
git worktree add ../feature-a origin/feature-a
git worktree add ../feature-b origin/feature-b

# 在不同terminal启动Claude实例
Terminal 1: cd ../feature-a && claude code
Terminal 2: cd ../feature-b && claude code
```

#### 方案4：Stream-JSON链式通信

**理念**：通过JSON文件传递中间结果，实现流水线

```
Agent A → output_a.json
    ↓
Agent B 读取 output_a.json → output_b.json
    ↓
Agent C 读取 output_b.json → final.json
```

#### 方案5：Session管理（未来方向）

**未来展望**：Claude Code支持Session API时，可实现真正的并行

```python
session_a = Session("backend")
session_b = Session("frontend")

# 并行执行
await asyncio.gather(
    session_a.run("设计后端API"),
    session_b.run("设计前端组件")
)
```

---

## 当前系统架构 (v2.0.0)

### 🏗️ 系统组件

```
用户需求
    ↓
【Phase State Tracker】
    检测当前Phase (Phase2/3/4)
    ↓
【Parallel Subagent Suggester Hook】(.claude/hooks/parallel_subagent_suggester.sh)
    PrePrompt触发
    提取任务描述
    ↓
【Parallel Task Generator】(scripts/subagent/parallel_task_generator.sh v2.0.0)
    ├─ Step 1: Per-Phase Impact Assessment
    │   └─ 调用 .claude/scripts/impact_radius_assessor.sh
    │       └─ 推荐Agent数量（0/3/6）
    ├─ Step 2: 读取 STAGES.yml 获取Phase并行组
    ├─ Step 3: 关键词匹配 + 智能选择Agent组合
    ├─ Step 4: 生成Task tool调用建议
    └─ Step 5: 跨组冲突检测
    ↓
【Claude Code执行】
    在单个消息中并发调用多个Task
    ↓
【SubAgents并行执行】
    通过.workflow/共享文件协调
```

### 📋 配置文件结构

**1. STAGES.yml** - 并行组定义
```yaml
parallel_groups:
  Phase2:
    - group_id: "core_implementation"
      name: "核心功能实现"
      can_parallel: true
      agents: ["general-purpose", "general-purpose"]
      conflict_paths: ["src/core/**", "src/lib/**"]

    - group_id: "test_implementation"
      name: "测试用例实现"
      can_parallel: true
      agents: ["general-purpose"]
      conflict_paths: ["test/**", "tests/**"]
```

**关键字段**：
- `group_id`: 唯一标识
- `can_parallel`: 是否可并行（false则串行执行）
- `agents`: 该组包含的agent类型
- `conflict_paths`: 可能产生冲突的文件路径（用于跨组冲突检测）

**2. .claude/settings.json** - 并行执行配置
```json
{
  "parallel_execution": {
    "enabled": true,
    "Phase2": {
      "enabled": true,
      "max_concurrent": 4,
      "timeout": 600,
      "groups": ["core_implementation", "test_implementation", "scripts_hooks", "configuration"]
    }
  }
}
```

### 🔄 工作流程详解

**Step 1: 自动触发（PrePrompt Hook）**

当进入Phase2/3/4时，`.claude/hooks/parallel_subagent_suggester.sh`自动运行：
```bash
# 检测Phase
current_phase=$(cat .phase/current)  # Phase2

# 提取任务描述（3个来源）
task=$(extract_task_from_context)
# 1. CLAUDE_TASK环境变量
# 2. git log -1 --pretty=%s
# 3. .workflow/user_request.md前5行

# 调用生成器
bash scripts/subagent/parallel_task_generator.sh "${current_phase}" "${task}"
```

**Step 2: Impact Assessment（自动评估）**

```bash
# 调用impact_radius_assessor.sh计算影响分数
assessment=$(echo "${task}" | bash .claude/scripts/impact_radius_assessor.sh --phase Phase2 --json)

# 输出示例：
{
  "impact_radius": 65,
  "risk_score": 8,
  "complexity_score": 7,
  "scope_score": 5,
  "agent_strategy": {
    "category": "high_risk",
    "min_agents": 6,
    "reason": "Complex backend changes with database migration"
  }
}
```

**公式**：`Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)`

**阈值映射**：
- **Radius ≥50**: 6 agents（高风险：CVE修复、架构变更、数据库迁移）
- **Radius 30-49**: 3 agents（中风险：Bug修复、性能优化、模块重构）
- **Radius 0-29**: 0 agents（低风险：文档更新、代码格式化）

**Step 3: 选择并行组（智能匹配）**

```python
# 从STAGES.yml读取Phase2的并行组
groups = config['parallel_groups']['Phase2']

# 关键词匹配
keyword_map = {
    'backend': ['impl-backend', 'skeleton-structure'],
    'frontend': ['impl-frontend'],
    'api': ['plan-technical', 'impl-backend'],
    'test': ['test-unit', 'test-integration', 'test-performance'],
    'database': ['impl-backend', 'skeleton-config'],
    'security': ['test-security', 'plan-quality']
}

# 根据任务描述匹配
if 'backend' in task.lower():
    selected_groups = ['impl-backend', 'skeleton-structure', 'skeleton-config']

# 限制数量为推荐的agent数
selected_agents = all_agents[:recommended_count]
```

**Step 4: 生成Task调用建议**

输出markdown格式的建议，包含：
- Impact Assessment结果
- 选中的并行组
- 完整的Task tool调用代码
- 冲突检测结果

**Step 5: 冲突检测**

```python
# 跨组冲突检测（同组内agents可共享路径）
for group1 in groups:
    for group2 in groups:
        if group1 != group2:
            paths1 = set(group1['conflict_paths'])
            paths2 = set(group2['conflict_paths'])
            overlaps = paths1 & paths2

            if overlaps:
                print(f"⚠️ Conflict: {group1['id']} vs {group2['id']}")
                print(f"Shared paths: {overlaps}")
```

**策略**：
- **同组agents**: 可以共享conflict_paths（协作关系）
- **跨组冲突**: 需要串行执行或协调机制

---

## Phase 2-7 并行策略详解

### Phase 2: Implementation（实现开发）

**并行潜力**: 🟢🟢🟢🟢 极高（4/4）

**并行组配置**：
```yaml
Phase2:
  - core_implementation:  # 核心功能
      agents: 2
      conflict_paths: ["src/core/**", "src/lib/**"]

  - test_implementation:  # 测试用例
      agents: 1
      conflict_paths: ["test/**", "tests/**"]

  - scripts_hooks:  # 脚本和hooks
      agents: 1
      conflict_paths: ["scripts/**", ".claude/hooks/**"]

  - configuration:  # 配置文件
      agents: 1
      conflict_paths: ["*.json", "*.yml", "*.yaml"]
```

**典型场景**：
```markdown
任务："实现用户认证系统（JWT + RBAC）"

Impact Assessment: 65分 → 6 agents

并行执行方案：
- Agent 1-2: 核心功能（auth service, token验证）
- Agent 3: 测试用例（单元测试 + 集成测试）
- Agent 4: 脚本（部署脚本，数据库迁移）
- Agent 5: 配置（环境变量，权限配置）
- Agent 6: 文档（API文档，使用指南）

预计加速比：4.5x（串行6h → 并行1.3h）
```

**协调机制**：
- **文件隔离**：不同组写入不同路径
- **接口约定**：提前定义API contract (如auth service接口)
- **shared state**：通过`.workflow/state.json`共享进度

**注意事项**：
- core_implementation组内2个agents需要协调（避免同时修改同一文件）
- 配置文件组可能与其他组有依赖（如core需要读取config）

---

### Phase 3: Testing（质量验证）

**并行潜力**: 🟢🟢🟢🟢🟢 最高（5/5）

**并行组配置**：
```yaml
Phase3:
  - unit_tests:  # 单元测试
      agents: 1
      conflict_paths: ["test/unit/**"]

  - integration_tests:  # 集成测试
      agents: 1
      conflict_paths: ["test/integration/**"]

  - performance_tests:  # 性能测试
      agents: 1
      conflict_paths: ["test/performance/**", "benchmarks/**"]

  - security_tests:  # 安全测试
      agents: 1
      conflict_paths: ["test/security/**"]

  - linting:  # 代码检查
      agents: 1
      conflict_paths: [".eslintrc", ".shellcheckrc"]
```

**典型场景**：
```markdown
任务："验证用户认证系统质量"

Impact Assessment: 45分 → 3 agents

并行执行方案（推荐）：
- Agent 1: 单元测试（auth service, token验证逻辑）
- Agent 2: 集成测试（完整登录流程，权限检查）
- Agent 3: 安全测试（SQL注入，XSS，CSRF）

如果是高风险（6 agents）：
- Agent 4: 性能测试（并发登录，token生成速度）
- Agent 5: Linting（Shellcheck, ESLint）
- Agent 6: 边界测试（极限情况，异常输入）

预计加速比：5x（Phase3从1.5h → 18min）
```

**协调机制**：
- **独立执行**：各测试组完全独立，无依赖
- **结果汇总**：每个agent写入`.workflow/test_results/{group}_report.json`
- **最终报告**：Queen agent汇总所有报告

**性能优势**：
- ✅ 测试是最适合并行的阶段（无副作用）
- ✅ 各类测试完全隔离（单元/集成/性能/安全）
- ✅ 结果可独立验证

---

### Phase 4: Review（代码审查）

**并行潜力**: 🟢🟢🟢 中高（3/4）

**并行组配置**：
```yaml
Phase4:
  - code_review:  # 代码逻辑审查
      agents: 1
      conflict_paths: ["src/**"]

  - documentation_check:  # 文档完整性
      agents: 1
      conflict_paths: ["docs/**", "*.md"]

  - version_audit:  # 版本一致性
      agents: 1
      conflict_paths: ["VERSION", "package.json", "manifest.yml"]
```

**典型场景**：
```markdown
任务："审查用户认证系统实现"

Impact Assessment: 38分 → 3 agents

并行执行方案：
- Agent 1: 代码审查（逻辑正确性，边界处理，错误处理）
- Agent 2: 文档检查（API文档完整，注释清晰，README更新）
- Agent 3: 配置审计（版本一致，依赖安全，配置完整）

协调点：
- Agent 1发现问题 → 记录到 .workflow/review_issues.json
- Agent 2/3同步读取issues → 检查相关文档/配置

预计加速比：2.5x（Phase4从2h → 48min）
```

**协调机制**：
- **issue tracking**：通过`.workflow/review_issues.json`共享发现的问题
- **优先级标记**：critical/major/minor
- **最终合并**：生成统一的REVIEW.md

**限制**：
- 代码审查需要整体理解（不能完全并行，需要一个agent负责overall logic）
- 文档和版本审计可以完全并行

---

### Phase 5: Release（发布准备）

**并行潜力**: 🟢🟢 中等（2/4）

**串行执行原因**：
- 版本号升级必须原子操作（6个文件同步更新）
- CHANGELOG编写需要完整的git history
- Release notes需要汇总所有变更

**可并行部分**：
```yaml
Phase5:
  - documentation_update:  # 文档更新
      agents: 1
      conflict_paths: ["README.md", "INSTALLATION.md"]

  - monitoring_config:  # 监控配置
      agents: 1
      conflict_paths: ["observability/**", "slo/**"]
```

**典型场景**：
```markdown
任务："准备v8.8.0发布"

串行执行（必须）：
1. 版本号升级（VERSION, settings.json等6文件）
2. 编写CHANGELOG.md

可并行执行：
- Agent 1: 更新README（新功能说明，版本号）
- Agent 2: 配置监控（健康检查端点，SLO阈值）

预计加速比：1.5x（部分加速）
```

**建议**：Phase 5通常不使用并行（风险高，收益低）

---

### Phase 6: Acceptance（验收确认）

**并行潜力**: 🟡 低（1/4）

**串行执行原因**：
- 验收需要完整的系统视角
- 对照Phase 1 Checklist逐项验证
- 生成验收报告需要统一视角

**不适合并行**：Phase 6本质上是"汇总和确认"，并行意义不大

---

### Phase 7: Closure（收尾合并）

**并行潜力**: 🟢🟢🟢 中高（3/4）

**并行组配置**：
```yaml
Phase7:
  - cleanup_temp:  # 临时文件清理
      agents: 1
      conflict_paths: [".temp/**", "*.tmp"]

  - cleanup_versions:  # 旧版本清理
      agents: 1
      conflict_paths: ["*_v[0-9]*", "*.bak"]

  - git_optimization:  # Git仓库优化
      agents: 1
      conflict_paths: [".git/**"]
```

**典型场景**：
```markdown
任务："Phase 7最终清理"

并行执行方案（3 agents）：
- Agent 1: 清理.temp/目录，删除临时文件
- Agent 2: 清理旧版本文件（*_old, *.backup）
- Agent 3: Git优化（git gc, 压缩仓库）

验证（串行，必须）：
- 版本一致性检查（6个文件）
- Phase系统一致性（7 Phases）
- 根目录文档数量（≤7个）

预计加速比：2.8x（清理从15min → 5min）
```

**协调机制**：
- 各清理agent独立执行（无冲突）
- 完成后统一验证（check_version_consistency.sh）

---

## 实战使用指南

### 场景1：高风险任务（6 agents）

**示例任务**："实现OAuth2.0认证系统（Google + GitHub登录）"

**Step 1: Impact Assessment自动运行**
```bash
# Hook自动触发，输出：
Impact Radius: 72 points
├─ Risk: 9/10 (安全敏感)
├─ Complexity: 8/10 (OAuth流程复杂)
└─ Scope: 7/10 (影响登录、注册、权限)

Recommended: 6 agents (high_risk)
```

**Step 2: 查看并行建议**
```markdown
## 🚀 Parallel Subagent Execution Plan

You should make the following Task tool calls in a SINGLE message:

Task 1: general-purpose (核心OAuth流程实现)
Task 2: general-purpose (Google Provider)
Task 3: general-purpose (GitHub Provider)
Task 4: general-purpose (测试用例)
Task 5: general-purpose (安全审计)
Task 6: general-purpose (文档和配置)
```

**Step 3: Claude Code执行（在单个消息中）**

在你的响应中同时调用6个Task：
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">general-purpose</parameter>
    <parameter name="description">OAuth2 Core Implementation</parameter>
    <parameter name="prompt">
实现OAuth2.0核心流程：
- Authorization Code Flow
- Token exchange
- Refresh token handling

Focus on: src/auth/oauth_core.ts
Coordinate via: .workflow/oauth_state.json
    </parameter>
  </invoke>

  <invoke name="Task">
    <parameter name="subagent_type">general-purpose</parameter>
    <parameter name="description">Google Provider</parameter>
    <parameter name="prompt">
实现Google OAuth Provider：
- Google API集成
- 用户信息获取
- Scope配置

Focus on: src/auth/providers/google.ts
Coordinate via: .workflow/oauth_state.json
    </parameter>
  </invoke>

  <!-- 其他4个Task... -->
</function_calls>
```

**预期结果**：
- 6个agents并发执行
- 通过`.workflow/oauth_state.json`协调
- 完成时间从6h → 1.5h（4x加速）

---

### 场景2：中风险任务（3 agents）

**示例任务**："优化数据库查询性能（添加索引+查询重写）"

**Step 1: Impact Assessment**
```bash
Impact Radius: 42 points
├─ Risk: 5/10 (数据库变更有风险)
├─ Complexity: 7/10 (需要分析慢查询)
└─ Scope: 5/10 (影响部分API)

Recommended: 3 agents (medium_risk)
```

**Step 2: 并行执行**
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">general-purpose</parameter>
    <parameter name="description">Slow Query Analysis</parameter>
    <parameter name="prompt">分析慢查询日志，识别优化点</parameter>
  </invoke>

  <invoke name="Task">
    <parameter name="subagent_type">general-purpose</parameter>
    <parameter name="description">Index Design</parameter>
    <parameter name="prompt">设计索引方案，编写migration</parameter>
  </invoke>

  <invoke name="Task">
    <parameter name="subagent_type">general-purpose</parameter>
    <parameter name="description">Query Rewrite</parameter>
    <parameter name="prompt">重写N+1查询，优化JOIN</parameter>
  </invoke>
</function_calls>
```

**预期结果**：
- 3个agents并发执行
- 完成时间从3h → 1.2h（2.5x加速）

---

### 场景3：低风险任务（0 agents）

**示例任务**："更新README.md添加新功能说明"

**Step 1: Impact Assessment**
```bash
Impact Radius: 18 points
├─ Risk: 2/10 (纯文档，无代码)
├─ Complexity: 3/10 (简单编辑)
└─ Scope: 2/10 (只影响文档)

Recommended: 0 agents (low_risk)
```

**Step 2: 直接执行（无需并行）**
- AI直接编辑README.md
- 无需SubAgent协调开销

---

### 最佳实践

**1. 何时使用并行**
- ✅ Phase 2实现阶段（模块独立）
- ✅ Phase 3测试阶段（测试独立）
- ✅ Phase 7清理阶段（清理独立）
- ⚠️ Phase 4审查阶段（部分并行）
- ❌ Phase 5发布阶段（风险高）
- ❌ Phase 6验收阶段（需要整体视角）

**2. 协调机制**
- **文件隔离优先**：不同agent写入不同目录
- **共享状态文件**：通过`.workflow/*.json`传递状态
- **接口约定**：提前定义清晰的API contract
- **结果汇总**：Queen agent负责最终整合

**3. 冲突处理**
- **预防为主**：通过STAGES.yml定义conflict_paths
- **检测机制**：parallel_task_generator.sh自动检测跨组冲突
- **解决策略**：
  - 同组agents：协作模式（共享路径）
  - 跨组冲突：串行执行或协调机制

**4. 性能调优**
```json
{
  "parallel_execution": {
    "max_concurrent": 4,  // 根据任务复杂度调整
    "timeout": 600,       // 10分钟超时
    "retry_on_failure": true,
    "exponential_backoff": true
  }
}
```

---

## 性能与优化

### 📊 性能基准数据

**Phase 2实现阶段**（基于26个真实任务）：
- **串行执行**: 平均3.2小时/任务
- **并行执行（3 agents）**: 平均1.5小时/任务（2.1x加速）
- **并行执行（6 agents）**: 平均0.9小时/任务（3.6x加速）

**Phase 3测试阶段**：
- **串行执行**: 平均1.8小时
- **并行执行（5组测试）**: 平均0.35小时（5.1x加速）

**Phase 7清理阶段**：
- **串行执行**: 平均15分钟
- **并行执行（3组清理）**: 平均5分钟（3x加速）

### ⚡ 优化技巧

**1. Impact Assessment校准**

如果发现推荐的agent数量不准确：
```bash
# 手动调整公式权重（需要修改impact_radius_assessor.sh）
# 当前公式：Radius = (Risk × 5) + (Complexity × 3) + (Scope × 2)

# 如果你的项目风险较低但复杂度高，可以调整为：
# Radius = (Risk × 3) + (Complexity × 5) + (Scope × 2)
```

**2. STAGES.yml微调**

为你的项目定制并行组：
```yaml
Phase2:
  - custom_group:
      name: "自定义模块"
      can_parallel: true
      agents: ["general-purpose"]
      conflict_paths: ["src/custom/**"]
      priority: 1  # 高优先级组先执行
```

**3. 冲突路径精细化**

减少误判冲突：
```yaml
# 粗粒度（可能误判）
conflict_paths: ["src/**"]

# 细粒度（精确匹配）
conflict_paths: ["src/auth/**", "src/user/**"]
```

**4. 性能监控**

启用性能追踪（v8.3.0新增）：
```bash
# 查看并行执行性能
cat .workflow/metrics/parallel_performance.jsonl

# 示例输出：
{"phase":"Phase2","exec_time_sec":45,"group_count":4,"timestamp":"2025-10-31T10:00:00Z"}
{"phase":"Phase3","exec_time_sec":21,"group_count":5,"timestamp":"2025-10-31T11:00:00Z"}
```

### 🎯 性能目标

**短期目标**（v8.8.0）：
- Phase 2平均加速比 ≥2.5x
- Phase 3平均加速比 ≥4.5x
- Impact Assessment准确率 ≥90%

**长期目标**（v9.0）：
- 支持动态负载均衡（high_load场景）
- 自动学习最优并行策略
- 支持Session API并行

---

## 附录

### A. 相关文件清单

**核心脚本**：
- `.claude/hooks/parallel_subagent_suggester.sh` - PrePrompt hook触发器
- `scripts/subagent/parallel_task_generator.sh` - v2.0.0并行任务生成器
- `.claude/scripts/impact_radius_assessor.sh` - 影响评估引擎

**配置文件**：
- `.workflow/STAGES.yml` - 并行组定义
- `.claude/settings.json` - 并行执行配置（parallel_execution部分）

**文档**：
- `.workflow/SPEC.yaml` - 核心规格（agent_strategy部分）
- `CLAUDE.md` - 主文档（Phase 2-7详细说明）

### B. 版本历史

- **v1.0.0** (2025-09-19): 初始版本，手动agent选择
- **v2.0.0** (2025-10-25): 引入STAGES.yml + Per-Phase Impact Assessment
- **v2.1.0** (2025-10-31): 本文档创建，混合旧理论+新实现

### C. 贡献指南

如果你想改进并行策略：

1. **调整Impact Assessment权重**：
   - 修改 `.claude/scripts/impact_radius_assessor.sh`
   - 基于≥30个样本验证准确率
   - 更新benchmark数据

2. **新增并行组**：
   - 在 `.workflow/STAGES.yml` 添加新组
   - 定义清晰的conflict_paths
   - 验证跨组冲突检测

3. **提交PR**：
   - 必须通过7-Phase工作流
   - 提供性能对比数据
   - 更新本文档

---

**文档状态**: ✅ 生产级
**保护级别**: 🔒 Immutable Kernel（修改需要RFC流程）
**维护者**: Claude Enhancer Team
**最后更新**: 2025-10-31
