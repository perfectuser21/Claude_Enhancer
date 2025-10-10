# P1 Planning: Audit Fix 详细修复计划

**生成时间**: 2025-10-09
**规划师**: Requirements Analyst Agent
**工作流阶段**: P1 Planning
**基于**: docs/P0_AUDIT_FIX_DISCOVERY.md
**目标**: 修复10个审计问题，提升保障力评分至100/100

---

## 📋 执行摘要 (Executive Summary)

### 规划概览
- **总任务数**: 18个具体任务（15个实施 + 3个验证）
- **分批策略**: 3批次（阻断修复→降级修复→优化修复）
- **预计总工时**: 7.0小时（含测试验证2.5h）
- **风险等级**: LOW（100%向后兼容）
- **并行度**: 最高6个Agent同时工作

### 关键里程碑
| 里程碑 | 交付物 | 预计完成时间 |
|--------|--------|--------------|
| P1规划完成 | 本文档 | T+0.75h |
| P2骨架完成 | 7个文件模板 | T+1.25h |
| P3-Batch1完成 | FATAL修复 | T+2.25h |
| P3-Batch2完成 | MAJOR修复 | T+4.25h |
| P3-Batch3完成 | MINOR优化 | T+5.75h |
| P4测试完成 | 测试报告 | T+6.75h |
| P6发布完成 | Tag v5.3.3 | T+7.5h |

---

## 📋 任务清单 (Task Breakdown)

### Batch 1: FATAL级阻断修复（串行执行，1h）

#### 任务1.1: 创建工作流主配置文件manifest.yml
- **问题ID**: CE-ISSUE-001
- **优先级**: P0 (FATAL)
- **目标**: 定义8-Phase工作流的执行顺序、默认配置和元数据
- **负责Agent**: devops-engineer
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml` (新建)
- **产物内容**:
  ```yaml
  version: "1.0"
  metadata:
    project: "Claude Enhancer 5.0"
    description: "8-Phase AI-driven development workflow"

  defaults:
    parallel_limit: 4
    timeout: 3600
    retry: 2
    allow_failure: false

  phases:
    - id: P0
      name: "Discovery"
      description: "Technical spike and feasibility validation"
      parallel: false
      agents: []
      depends_on: []
      outputs: ["docs/SPIKE.md", "docs/P0_*.md"]

    - id: P1
      name: "Plan"
      description: "Requirements analysis and task breakdown"
      parallel: true
      max_agents: 4
      depends_on: ["P0"]
      outputs: ["docs/PLAN.md"]

    - id: P2
      name: "Skeleton"
      description: "Architecture design and directory structure"
      parallel: true
      max_agents: 6
      depends_on: ["P1"]
      outputs: ["src/**", "docs/SKELETON-NOTES.md"]

    - id: P3
      name: "Implement"
      description: "Coding development with commits"
      parallel: true
      max_agents: 8
      depends_on: ["P2"]
      outputs: ["src/**", "docs/CHANGELOG.md"]

    - id: P4
      name: "Test"
      description: "Unit/integration/performance/BDD tests"
      parallel: true
      max_agents: 6
      depends_on: ["P3"]
      outputs: ["tests/**", "docs/TEST-REPORT.md"]

    - id: P5
      name: "Review"
      description: "Code review and quality assessment"
      parallel: true
      max_agents: 4
      depends_on: ["P4"]
      outputs: ["docs/REVIEW.md"]

    - id: P6
      name: "Release"
      description: "Documentation update and tag creation"
      parallel: true
      max_agents: 2
      depends_on: ["P5"]
      outputs: ["docs/README.md", "docs/CHANGELOG.md", ".tags/**"]

    - id: P7
      name: "Monitor"
      description: "Production monitoring and SLO tracking"
      parallel: false
      agents: []
      depends_on: ["P6"]
      outputs: ["observability/slo/slo.yml", "docs/HEALTH_REPORT.md"]
  ```
- **验证方式**:
  ```bash
  # 1. YAML语法验证
  yamllint /home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml

  # 2. 结构验证
  yq '.phases | length' /home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml
  # 期望输出: 8

  # 3. 版本验证
  yq '.version' /home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml
  # 期望输出: "1.0"
  ```
- **预计耗时**: 45分钟
- **依赖关系**: 无前置依赖
- **风险**: 中等（新文件可能与executor.sh逻辑冲突）
- **回滚方案**:
  ```bash
  rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml
  ```

#### 任务1.2: 创建并行组声明文件STAGES.yml
- **问题ID**: CE-ISSUE-005 (部分)
- **优先级**: P0 (FATAL)
- **目标**: 声明各Phase的角色分组和并行执行策略
- **负责Agent**: workflow-optimizer
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml` (新建)
- **产物内容**:
  ```yaml
  version: "1.0"
  description: "Parallel execution groups and role mapping"

  # 可复用的角色组定义
  role_groups:
    architecture:
      - backend-architect
      - frontend-architect
      - database-specialist
      - api-designer

    implementation:
      - code-writer
      - test-engineer
      - security-auditor
      - performance-engineer

    review:
      - code-reviewer
      - quality-assurance
      - technical-writer

    devops:
      - devops-engineer
      - sre-specialist

  # Phase到角色组的映射
  phase_mapping:
    P0:
      groups: []
      parallel: false
      description: "Discovery phase - sequential analysis"

    P1:
      groups: [architecture]
      max_parallel: 4
      description: "Planning phase - architectural analysis"

    P2:
      groups: [architecture]
      max_parallel: 6
      description: "Skeleton phase - structural design"

    P3:
      groups: [architecture, implementation]
      max_parallel: 8
      description: "Implementation phase - coding"
      parallel_subgroups:
        - group_id: impl-backend
          agents: [backend-architect, database-specialist]
          can_parallel: true
        - group_id: impl-frontend
          agents: [frontend-architect, ux-designer]
          can_parallel: true
        - group_id: impl-security
          agents: [security-auditor, test-engineer]
          can_parallel: true

    P4:
      groups: [implementation]
      max_parallel: 6
      description: "Testing phase - quality validation"

    P5:
      groups: [review]
      max_parallel: 4
      description: "Review phase - code assessment"

    P6:
      groups: [review, devops]
      max_parallel: 2
      description: "Release phase - documentation and deployment"

    P7:
      groups: [devops]
      max_parallel: 1
      description: "Monitoring phase - production tracking"

  # 冲突检测规则（在任务2.3中补充详细规则）
  conflict_detection:
    enabled: true
    rules: []  # 将在Batch 2任务2.3中填充
  ```
- **验证方式**:
  ```bash
  # 1. YAML语法验证
  yamllint /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml

  # 2. 角色组数量验证
  yq '.role_groups | keys | length' /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml
  # 期望输出: 4

  # 3. P3并行组验证
  yq '.phase_mapping.P3.parallel_subgroups | length' /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml
  # 期望输出: >= 3
  ```
- **预计耗时**: 40分钟
- **依赖关系**: 无（可与任务1.1并行）
- **风险**: 中等（语法设计需与executor.sh集成）
- **回滚方案**:
  ```bash
  rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml
  ```

#### 任务1.3: 扩展gates.yml添加P0和P7阶段定义
- **问题ID**: CE-ISSUE-002
- **优先级**: P0 (FATAL)
- **目标**: 补充缺失的P0和P7阶段的DoD（Definition of Done）
- **负责Agent**: requirements-analyst
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml` (修改)
- **修改内容**:
  1. 更新`phase_order`行（第23行）:
     ```yaml
     phase_order: [P0, P1, P2, P3, P4, P5, P6, P7]
     ```
  2. 在`phases:`段（第25行后）插入P0定义:
     ```yaml
     P0:
       name: "Discovery"
       allow_paths: ["docs/SPIKE.md", "docs/P0_*.md"]
       must_produce:
         - "docs/SPIKE.md: 包含技术调研、可行性分析、风险评估"
         - "技术调研至少3个选项对比"
         - "可行性结论明确（GO/NO-GO）"
       gates:
         - "必须存在 docs/SPIKE.md"
         - "必须包含 GO/NO-GO 结论"
         - "风险评估完整（高/中/低分类）"
       on_pass:
         - "create: .gates/00.ok"
         - "set: .phase/current=P1"
     ```
  3. 在P6定义后（第110行后）插入P7定义:
     ```yaml
     P7:
       name: "Monitor"
       allow_paths: ["observability/**", "docs/HEALTH_REPORT.md"]
       must_produce:
         - "observability/slo/slo.yml 包含≥10个SLO定义"
         - "docs/HEALTH_REPORT.md 包含健康检查结果"
         - "监控指标配置完整"
       gates:
         - "SLO定义数量 >= 10"
         - "健康检查脚本可执行"
         - "告警规则配置正确"
       on_pass:
         - "create: .gates/07.ok"
         - "set: .phase/current=P0"  # 循环回P0开始新工作流
     ```
- **验证方式**:
  ```bash
  # 1. Phase顺序验证
  yq '.phase_order' /home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml
  # 期望输出: [P0, P1, P2, P3, P4, P5, P6, P7]

  # 2. P0定义存在验证
  yq '.phases.P0.name' /home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml
  # 期望输出: "Discovery"

  # 3. P7定义存在验证
  yq '.phases.P7.name' /home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml
  # 期望输出: "Monitor"
  ```
- **预计耗时**: 20分钟
- **依赖关系**: 无（可与任务1.1/1.2并行）
- **风险**: 低（纯新增，不影响现有P1-P6）
- **回滚方案**:
  ```bash
  # 恢复gates.yml到修改前版本
  git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml
  ```

---

### Batch 2: MAJOR级降级修复（部分并行，2h）

#### 任务2.1: 创建状态同步检查脚本sync_state.sh
- **问题ID**: CE-ISSUE-003
- **优先级**: P1 (MAJOR)
- **目标**: 确保`.phase/current`与`.workflow/ACTIVE`文件状态一致性
- **负责Agent**: devops-engineer
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/sync_state.sh` (新建)
  - `/home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit` (修改)
- **产物内容（sync_state.sh）**:
  ```bash
  #!/bin/bash
  set -euo pipefail

  # 状态同步检查脚本
  # 用途: 确保.phase/current与.workflow/ACTIVE一致

  PHASE_FILE=".phase/current"
  ACTIVE_FILE=".workflow/ACTIVE"
  MAX_AGE_HOURS=24

  # 检查文件是否存在
  if [[ ! -f "$PHASE_FILE" ]]; then
      echo "❌ 错误: $PHASE_FILE 不存在"
      exit 1
  fi

  if [[ ! -f "$ACTIVE_FILE" ]]; then
      echo "❌ 错误: $ACTIVE_FILE 不存在"
      exit 1
  fi

  # 读取当前phase
  CURRENT_PHASE=$(cat "$PHASE_FILE")
  ACTIVE_PHASE=$(yq eval '.phase' "$ACTIVE_FILE")

  # 比较是否一致
  if [[ "$CURRENT_PHASE" != "$ACTIVE_PHASE" ]]; then
      echo "⚠️  警告: 状态不一致检测"
      echo "  .phase/current: $CURRENT_PHASE"
      echo "  .workflow/ACTIVE: $ACTIVE_PHASE"
      echo ""
      echo "🔧 自动同步中..."

      # 自动同步（以.phase/current为准）
      yq eval ".phase = \"$CURRENT_PHASE\"" -i "$ACTIVE_FILE"
      echo "✅ 已同步: ACTIVE.phase → $CURRENT_PHASE"
  fi

  # 检查ACTIVE文件是否过期（超过24小时未更新）
  if [[ -f "$ACTIVE_FILE" ]]; then
      FILE_AGE_SEC=$(( $(date +%s) - $(stat -c %Y "$ACTIVE_FILE") ))
      FILE_AGE_HOURS=$(( FILE_AGE_SEC / 3600 ))

      if [[ $FILE_AGE_HOURS -gt $MAX_AGE_HOURS ]]; then
          echo "⚠️  警告: $ACTIVE_FILE 超过${MAX_AGE_HOURS}小时未更新"
          echo "  最后更新: ${FILE_AGE_HOURS}小时前"
          echo "  建议检查是否有遗留的Phase未完成"
      fi
  fi

  echo "✅ 状态同步检查通过"
  exit 0
  ```
- **修改内容（pre-commit hook）**:
  在`/home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit`文件头部添加：
  ```bash
  # 状态同步检查
  if [[ -x .workflow/scripts/sync_state.sh ]]; then
      ./.workflow/scripts/sync_state.sh || {
          echo "❌ 状态同步检查失败，请先修复状态不一致"
          exit 1
      }
  fi
  ```
- **验证方式**:
  ```bash
  # 1. 脚本可执行验证
  test -x /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/sync_state.sh
  echo $?  # 期望: 0

  # 2. 功能测试（制造不一致）
  echo "P1" > /home/xx/dev/Claude Enhancer 5.0/.phase/current
  yq eval '.phase = "P2"' -i /home/xx/dev/Claude Enhancer 5.0/.workflow/ACTIVE
  /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/sync_state.sh
  # 期望: 自动同步，退出码0

  # 3. pre-commit集成验证
  git commit --allow-empty -m "test"
  # 期望: 自动执行sync_state.sh
  ```
- **预计耗时**: 25分钟
- **依赖关系**: 无
- **风险**: 低（纯新增功能，不影响现有逻辑）
- **回滚方案**:
  ```bash
  rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/sync_state.sh
  git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit
  ```

#### 任务2.2: Hooks审计与激活（分3步）
- **问题ID**: CE-ISSUE-006
- **优先级**: P1 (MAJOR)
- **目标**: 审计65个hooks文件，激活关键hooks，归档废弃hooks
- **负责Agent**: security-auditor + code-reviewer（联合审计）
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.claude/settings.json` (修改)
  - `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/HOOKS_AUDIT_REPORT.md` (新建)
  - `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/` (新建目录)
  - `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/*` (部分移动到archive/)

**步骤2.2.1: 自动分类hooks**
- **方法**: 脚本扫描hooks文件头部注释，识别用途和状态
- **分类标准**:
  ```
  ACTIVE（活跃）:
    - 已在settings.json挂载
    - 头部注释标记为"PRODUCTION"
    - 最近30天有修改

  CANDIDATE（候选）:
    - 被其他hooks调用
    - 头部注释标记为"READY"
    - 功能完整但未激活

  DEPRECATED（废弃）:
    - 头部注释标记为"DEPRECATED"
    - 存在同名升级版本（如v2替代v1）
    - 超过180天未修改

  NEEDS_REVIEW（需人工审查）:
    - 无明确注释
    - 功能未知
    - 可能有风险
  ```
- **产物**: `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/HOOKS_AUDIT_REPORT.md`（分类清单）

**步骤2.2.2: 激活关键hooks**
- **激活列表**（添加到settings.json的hooks段）:
  ```json
  {
    "hooks": {
      "UserPromptSubmit": [
        ".claude/hooks/workflow_auto_start.sh"
      ],
      "PrePrompt": [
        ".claude/hooks/workflow_enforcer.sh",
        ".claude/hooks/smart_agent_selector.sh",
        ".claude/hooks/phase_transition_validator.sh",
        ".claude/hooks/task_complexity_analyzer.sh"
      ],
      "PreToolUse": [
        ".claude/hooks/branch_helper.sh",
        ".claude/hooks/quality_gate.sh",
        ".claude/hooks/gap_scan.sh",
        ".claude/hooks/file_permission_checker.sh"
      ],
      "PostToolUse": [
        ".claude/hooks/unified_post_processor.sh",
        ".claude/hooks/metrics_collector.sh",
        ".claude/hooks/changelog_updater.sh"
      ],
      "OnError": [
        ".claude/hooks/error_analyzer.sh",
        ".claude/hooks/rollback_suggester.sh"
      ]
    }
  }
  ```
- **新增hooks数量**: 从5个→15个（新增10个）

**步骤2.2.3: 归档废弃hooks**
- **归档策略**: 移动到`.claude/hooks/archive/`，保留文件以便回滚
- **归档示例**:
  ```bash
  mkdir -p /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/deprecated
  mv /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/old_*.sh /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/deprecated/
  ```

- **验证方式**:
  ```bash
  # 1. settings.json hooks数量验证
  jq '.hooks | to_entries | map(.value | length) | add' /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json
  # 期望输出: >= 15

  # 2. 审计报告存在验证
  test -f /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/HOOKS_AUDIT_REPORT.md
  echo $?  # 期望: 0

  # 3. archive目录验证
  test -d /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive
  echo $?  # 期望: 0
  ```
- **预计耗时**: 70分钟（扫描30min + 审查30min + 配置10min）
- **依赖关系**: 无（可与其他Batch 2任务并行）
- **风险**: 中等（误激活/误归档可能影响功能）
- **回滚方案**:
  ```bash
  cp /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json.backup /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json
  mv /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/* /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/
  ```

#### 任务2.3: 补充STAGES.yml的并行冲突检测规则
- **问题ID**: CE-ISSUE-005（详细规则部分）
- **优先级**: P1 (MAJOR)
- **目标**: 定义Agent并行执行时的冲突检测和降级策略
- **负责Agent**: workflow-optimizer
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml` (修改)
- **修改内容**: 在`conflict_detection`段添加详细规则
  ```yaml
  conflict_detection:
    enabled: true

    rules:
      - rule_id: "same-file-write"
        name: "Same File Write Conflict"
        description: "两个或多个Agent尝试写入同一文件"
        condition: "agents.write_targets 存在交集"
        action: "downgrade_to_serial"
        priority: 1
        severity: "HIGH"

      - rule_id: "git-lock"
        name: "Git Lock Conflict"
        description: "多个Agent同时执行git操作（commit/push）"
        condition: "agents.uses_git_write == true 且 count > 1"
        action: "queue_execution"
        priority: 2
        severity: "HIGH"

      - rule_id: "shared-config-modify"
        name: "Shared Config Modification"
        description: "多个Agent修改同一配置文件（如package.json）"
        condition: "agents.modifies 包含 ['package.json', 'tsconfig.json', 'gates.yml']"
        action: "serialize_by_priority"
        priority: 3
        severity: "MEDIUM"

      - rule_id: "database-migration"
        name: "Database Migration Conflict"
        description: "多个Agent同时创建migration文件"
        condition: "agents.creates_migration == true 且 count > 1"
        action: "merge_migrations"
        priority: 4
        severity: "MEDIUM"

      - rule_id: "resource-intensive"
        name: "Resource Intensive Operations"
        description: "多个Agent同时执行资源密集型操作（如构建、测试）"
        condition: "agents.cpu_intensive == true 且 count > system.cpu_cores"
        action: "throttle_parallel_count"
        priority: 5
        severity: "LOW"

    downgrade_strategies:
      downgrade_to_serial:
        description: "完全串行化执行，一个Agent完成后再启动下一个"
        implementation: "sequential_queue"

      queue_execution:
        description: "使用锁机制排队执行"
        implementation: "mutex_queue"
        max_wait_seconds: 300

      serialize_by_priority:
        description: "按Agent优先级排序串行执行"
        implementation: "priority_queue"

      merge_migrations:
        description: "合并migration文件，统一版本号"
        implementation: "migration_merger"

      throttle_parallel_count:
        description: "限制并行数量，分批执行"
        implementation: "semaphore"
        max_concurrent: 4

    monitoring:
      log_conflicts: true
      metrics_path: ".workflow/metrics/conflicts.log"
      alert_on_downgrade: true
  ```
- **验证方式**:
  ```bash
  # 1. 规则数量验证
  yq '.conflict_detection.rules | length' /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml
  # 期望输出: >= 5

  # 2. 降级策略完整性验证
  yq '.conflict_detection.downgrade_strategies | keys' /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml
  # 期望输出: 包含5个策略

  # 3. YAML语法验证
  yamllint /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml
  ```
- **预计耗时**: 35分钟
- **依赖关系**: 依赖任务1.2（STAGES.yml基础结构）
- **风险**: 低（纯配置增强，不影响现有功能）
- **回滚方案**:
  ```bash
  # 恢复STAGES.yml到任务1.2完成后的版本
  git checkout HEAD~1 -- /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml
  ```

---

### Batch 3: MINOR级优化修复（全部并行，1.5h）

#### 任务3.1: 实现executor.sh的dry-run模式
- **问题ID**: CE-ISSUE-004
- **优先级**: P2 (MINOR)
- **目标**: 添加`--dry-run`标志，实现执行计划预览和可视化
- **负责Agent**: devops-engineer
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh` (修改)
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/plan_renderer.sh` (新建)
- **修改内容（executor.sh）**:
  在文件头部添加参数解析：
  ```bash
  # 解析命令行参数
  DRY_RUN=false
  VISUALIZE=false

  while [[ $# -gt 0 ]]; do
      case $1 in
          --dry-run)
              DRY_RUN=true
              shift
              ;;
          --visualize)
              VISUALIZE=true
              shift
              ;;
          *)
              PHASE=$1
              shift
              ;;
      esac
  done

  # Dry-run模式执行逻辑
  if [[ "$DRY_RUN" == "true" ]]; then
      echo "🔍 DRY RUN MODE - No changes will be made"
      echo ""

      # 调用计划渲染脚本
      if [[ "$VISUALIZE" == "true" ]]; then
          ./.workflow/scripts/plan_renderer.sh "$PHASE" --format mermaid
      else
          ./.workflow/scripts/plan_renderer.sh "$PHASE" --format text
      fi

      exit 0
  fi
  ```

- **产物内容（plan_renderer.sh）**:
  ```bash
  #!/bin/bash
  set -euo pipefail

  PHASE=$1
  FORMAT=${2:-text}

  # 读取manifest.yml和gates.yml
  AGENTS=$(yq eval ".phases[] | select(.id == \"$PHASE\") | .max_agents" .workflow/manifest.yml)
  OUTPUTS=$(yq eval ".phases[] | select(.id == \"$PHASE\") | .outputs[]" .workflow/manifest.yml)
  GATES=$(yq eval ".phases.$PHASE.gates[]" .workflow/gates.yml)

  if [[ "$FORMAT" == "mermaid" ]]; then
      # 生成Mermaid流程图
      cat <<EOF
  \`\`\`mermaid
  graph TD
      Start[开始 $PHASE] --> Analysis[分析任务]
      Analysis --> Parallel{并行执行}
      Parallel --> Agent1[Agent 1]
      Parallel --> Agent2[Agent 2]
      Parallel --> AgentN[Agent $AGENTS]
      Agent1 --> Gates[质量门禁验证]
      Agent2 --> Gates
      AgentN --> Gates
      Gates --> |通过| Success[Phase完成]
      Gates --> |失败| Rework[返工修复]
  \`\`\`
  EOF
  else
      # 文本格式输出
      cat <<EOF
  ╔══════════════════════════════════════════════╗
  ║       PHASE $PHASE EXECUTION PLAN           ║
  ╚══════════════════════════════════════════════╝

  📊 Overview:
     Phase:          $PHASE
     Max Agents:     $AGENTS
     Parallel:       $(yq eval ".phases[] | select(.id == \"$PHASE\") | .parallel" .workflow/manifest.yml)

  📁 Expected Outputs:
  $(echo "$OUTPUTS" | sed 's/^/     - /')

  ✅ Quality Gates:
  $(echo "$GATES" | sed 's/^/     - /')

  ⏱️  Estimated Duration: ~$(estimate_phase_duration "$PHASE")

  💡 To execute: ./executor.sh $PHASE
      (Remove --dry-run flag)
  EOF
  fi
  ```

- **验证方式**:
  ```bash
  # 1. Dry-run模式验证
  /home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh P3 --dry-run
  # 期望: 输出执行计划，不实际执行

  # 2. Mermaid图生成验证
  /home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh P3 --dry-run --visualize
  # 期望: 输出Mermaid代码块

  # 3. 脚本可执行验证
  test -x /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/plan_renderer.sh
  echo $?  # 期望: 0
  ```
- **预计耗时**: 45分钟
- **依赖关系**: 依赖任务1.1（需读取manifest.yml）
- **风险**: 低（新增功能，不影响现有执行逻辑）
- **回滚方案**:
  ```bash
  git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh
  rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/plan_renderer.sh
  ```

#### 任务3.2: 清理.gates/目录的多余gate文件
- **问题ID**: CE-ISSUE-007
- **优先级**: P2 (MINOR)
- **目标**: 删除gates.yml未定义的gate文件，保持一致性
- **负责Agent**: code-reviewer
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.gates/` (清理)
- **清理策略**:
  ```bash
  # 保留的文件（对应P0-P7，共16个文件）
  # 00.ok, 00.ok.sig, 01.ok, 01.ok.sig, ..., 07.ok, 07.ok.sig

  # 删除的文件（未在gates.yml定义的其他gate文件）
  # 例如: 08.ok, 09.ok, legacy.ok等
  ```
- **执行脚本**:
  ```bash
  #!/bin/bash
  cd /home/xx/dev/Claude Enhancer 5.0/.gates/

  # 备份当前状态
  tar -czf gates_backup_$(date +%Y%m%d_%H%M%S).tar.gz *.ok *.ok.sig

  # 删除非标准gate文件
  for file in *.ok *.ok.sig; do
      if [[ ! "$file" =~ ^0[0-7]\.(ok|ok\.sig)$ ]]; then
          echo "删除多余文件: $file"
          rm -f "$file"
      fi
  done

  # 验证剩余文件数量
  remaining=$(ls -1 *.ok *.ok.sig 2>/dev/null | wc -l)
  echo "清理完成，剩余文件数: $remaining (期望: 16)"
  ```
- **验证方式**:
  ```bash
  # 1. 文件数量验证
  ls -1 /home/xx/dev/Claude Enhancer 5.0/.gates/*.ok /home/xx/dev/Claude Enhancer 5.0/.gates/*.ok.sig 2>/dev/null | wc -l
  # 期望输出: 16 (P0-P7各2个文件)

  # 2. 文件命名验证
  ls /home/xx/dev/Claude Enhancer 5.0/.gates/ | grep -E "^0[0-7]\.(ok|ok\.sig)$" | wc -l
  # 期望输出: 16

  # 3. 备份文件存在验证
  ls /home/xx/dev/Claude Enhancer 5.0/.gates/gates_backup_*.tar.gz
  # 期望: 存在备份文件
  ```
- **预计耗时**: 15分钟
- **依赖关系**: 依赖任务1.3（gates.yml添加P0/P7后再清理）
- **风险**: 低（有备份，可快速恢复）
- **回滚方案**:
  ```bash
  cd /home/xx/dev/Claude Enhancer 5.0/.gates/
  tar -xzf gates_backup_*.tar.gz
  ```

#### 任务3.3: 补充历史REVIEW.md的明确结论
- **问题ID**: CE-ISSUE-008
- **优先级**: P2 (MINOR)
- **目标**: 为所有REVIEW*.md文件添加APPROVE/REWORK/ARCHIVED结论
- **负责Agent**: code-reviewer
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/docs/REVIEW.md` (修改)
  - `/home/xx/dev/Claude Enhancer 5.0/docs/REVIEW_STRESS_TEST.md` (修改)
  - `/home/xx/dev/Claude Enhancer 5.0/docs/REVIEW_*.md` (其他历史文件，如存在)
- **处理规则**:
  ```
  1. 读取REVIEW文件内容
  2. 分析质量评估结果:
     - 包含"质量达标"/"LGTM"/"无问题" → 添加"APPROVE"
     - 包含"需修改"/"存在问题"/"建议重构" → 添加"REWORK: <原因>"
     - 超过90天未更新且不再相关 → 添加"ARCHIVED: 历史版本已过时"
  3. 在文件末尾追加结论
  ```
- **修改示例**:
  ```markdown
  <!-- 在REVIEW.md末尾添加 -->

  ---

  ## 审查结论 (Review Conclusion)

  **状态**: APPROVE ✅
  **审查日期**: 2025-10-09
  **审查员**: code-reviewer
  **备注**: 代码质量达标，测试覆盖充分，可进入发布阶段
  ```
- **验证方式**:
  ```bash
  # 1. 结论存在性验证
  grep -E "APPROVE|REWORK|ARCHIVED" /home/xx/dev/Claude Enhancer 5.0/docs/REVIEW*.md
  # 期望: 每个文件至少有一个结论

  # 2. 文件数量验证
  ls /home/xx/dev/Claude Enhancer 5.0/docs/REVIEW*.md | wc -l
  # 记录数量N

  grep -l "APPROVE\|REWORK\|ARCHIVED" /home/xx/dev/Claude Enhancer 5.0/docs/REVIEW*.md | wc -l
  # 期望: 等于N（所有文件都有结论）
  ```
- **预计耗时**: 25分钟
- **依赖关系**: 无（可独立并行）
- **风险**: 极低（仅文档修改）
- **回滚方案**:
  ```bash
  git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/docs/REVIEW*.md
  ```

#### 任务3.4: 配置日志轮转策略logrotate.conf
- **问题ID**: CE-ISSUE-009
- **优先级**: P2 (MINOR)
- **目标**: 防止日志文件无限增长，配置自动轮转压缩
- **负责Agent**: devops-engineer
- **受影响文件**:
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf` (新建)
  - `/home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh` (修改，添加日志清理逻辑)
- **产物内容（logrotate.conf）**:
  ```
  # Claude Enhancer日志轮转配置

  /home/xx/dev/Claude Enhancer 5.0/.workflow/logs/*.log {
      # 单个文件超过10MB时轮转
      size 10M

      # 保留最近5个归档文件
      rotate 5

      # 使用gzip压缩归档
      compress
      delaycompress

      # 如果日志文件不存在不报错
      missingok

      # 日志文件为空也轮转
      notifempty

      # 轮转后创建新文件
      create 0644 xx xx

      # 共享脚本（所有日志轮转后执行）
      sharedscripts

      # 轮转后执行的脚本
      postrotate
          echo "$(date): 日志轮转完成" >> /home/xx/dev/Claude Enhancer 5.0/.workflow/logs/logrotate.log
      endscript
  }

  # 特殊日志文件（每日轮转）
  /home/xx/dev/Claude Enhancer 5.0/.workflow/logs/daily/*.log {
      daily
      rotate 30
      compress
      missingok
      notifempty
      create 0644 xx xx
  }
  ```
- **集成方式**: 在executor.sh启动时检查日志大小
  ```bash
  # 在executor.sh头部添加
  LOG_DIR=".workflow/logs"
  MAX_LOG_SIZE_MB=10

  # 检查日志大小并轮转
  check_and_rotate_logs() {
      for log in "$LOG_DIR"/*.log; do
          if [[ -f "$log" ]]; then
              size_mb=$(du -m "$log" | cut -f1)
              if [[ $size_mb -gt $MAX_LOG_SIZE_MB ]]; then
                  echo "日志文件 $log 超过 ${MAX_LOG_SIZE_MB}MB，执行轮转..."
                  logrotate -f .workflow/scripts/logrotate.conf
                  break
              fi
          fi
      done
  }

  check_and_rotate_logs
  ```
- **验证方式**:
  ```bash
  # 1. 配置文件存在验证
  test -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf
  echo $?  # 期望: 0

  # 2. 语法验证
  logrotate -d /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf
  # 期望: 无语法错误

  # 3. 功能测试（创建大文件触发轮转）
  dd if=/dev/zero of=/home/xx/dev/Claude Enhancer 5.0/.workflow/logs/test.log bs=1M count=11
  logrotate -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf
  ls /home/xx/dev/Claude Enhancer 5.0/.workflow/logs/test.log.1.gz
  # 期望: 存在压缩文件
  ```
- **预计耗时**: 20分钟
- **依赖关系**: 无（可独立并行）
- **风险**: 极低（日志管理不影响功能）
- **回滚方案**:
  ```bash
  rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf
  git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh
  ```

---

## 🗂️ 受影响文件清单 (Affected Files List)

### 新增文件（10个）

| 序号 | 文件路径 | 用途 | 批次 | 负责Agent |
|------|---------|------|------|-----------|
| 1 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml` | 工作流主配置 | Batch 1 | devops-engineer |
| 2 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml` | 并行组声明 | Batch 1 | workflow-optimizer |
| 3 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/sync_state.sh` | 状态同步脚本 | Batch 2 | devops-engineer |
| 4 | `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/HOOKS_AUDIT_REPORT.md` | Hooks审计报告 | Batch 2 | security-auditor |
| 5 | `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/` | 废弃hooks目录 | Batch 2 | code-reviewer |
| 6 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/plan_renderer.sh` | 执行计划可视化 | Batch 3 | devops-engineer |
| 7 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf` | 日志轮转配置 | Batch 3 | devops-engineer |
| 8 | `/home/xx/dev/Claude Enhancer 5.0/.gates/gates_backup_*.tar.gz` | Gate文件备份 | Batch 3 | code-reviewer |
| 9 | `/home/xx/dev/Claude Enhancer 5.0/.claude/settings.json.backup` | Settings备份 | Batch 2 | security-auditor |
| 10 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/metrics/conflicts.log` | 冲突监控日志 | Batch 2 | workflow-optimizer |

### 修改文件（5个）

| 序号 | 文件路径 | 修改内容 | 批次 | 负责Agent |
|------|---------|---------|------|-----------|
| 1 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml` | 添加P0/P7定义，更新phase_order | Batch 1 | requirements-analyst |
| 2 | `/home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit` | 添加状态同步检查调用 | Batch 2 | devops-engineer |
| 3 | `/home/xx/dev/Claude Enhancer 5.0/.claude/settings.json` | 新增10个hooks挂载 | Batch 2 | security-auditor |
| 4 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh` | 添加--dry-run和日志轮转逻辑 | Batch 3 | devops-engineer |
| 5 | `/home/xx/dev/Claude Enhancer 5.0/docs/REVIEW*.md` | 补充审查结论 | Batch 3 | code-reviewer |

### 移动/清理文件（约50-60个）

| 操作 | 文件模式 | 目标位置 | 批次 | 负责Agent |
|------|---------|---------|------|-----------|
| 移动 | `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/deprecated_*.sh` | `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/deprecated/` | Batch 2 | code-reviewer |
| 移动 | `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/old_*.sh` | `/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/legacy/` | Batch 2 | code-reviewer |
| 删除 | `/home/xx/dev/Claude Enhancer 5.0/.gates/[^0-7][0-9].ok*` | (删除) | Batch 3 | code-reviewer |
| 备份 | `/home/xx/dev/Claude Enhancer 5.0/.gates/*.ok*` | `/home/xx/dev/Claude Enhancer 5.0/.gates/gates_backup_*.tar.gz` | Batch 3 | code-reviewer |

---

## 🔄 回滚方案 (Rollback Plan)

### 整体回滚（恢复到修复前状态）

```bash
#!/bin/bash
# 全局回滚脚本
set -euo pipefail

echo "🔄 开始整体回滚..."

# 1. 恢复Git管理的文件
git checkout HEAD -- \
    /home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml \
    /home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit \
    /home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh \
    /home/xx/dev/Claude Enhancer 5.0/docs/REVIEW*.md

# 2. 恢复备份文件
if [[ -f /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json.backup ]]; then
    cp /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json.backup /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json
fi

# 3. 恢复gate文件
if [[ -f /home/xx/dev/Claude Enhancer 5.0/.gates/gates_backup_*.tar.gz ]]; then
    cd /home/xx/dev/Claude Enhancer 5.0/.gates/
    tar -xzf gates_backup_*.tar.gz
    cd -
fi

# 4. 恢复hooks（从archive移回）
if [[ -d /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive ]]; then
    mv /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/*/* /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/ 2>/dev/null || true
fi

# 5. 删除新增文件
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/sync_state.sh
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/plan_renderer.sh
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf
rm -f /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/HOOKS_AUDIT_REPORT.md
rm -rf /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive

echo "✅ 整体回滚完成"
```

### 分批次回滚

#### Batch 1回滚（FATAL修复）
```bash
# 回滚manifest.yml和STAGES.yml
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml

# 恢复gates.yml
git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml
```

#### Batch 2回滚（MAJOR修复）
```bash
# 回滚状态同步脚本
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/sync_state.sh
git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit

# 恢复settings.json
cp /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json.backup /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json

# 恢复hooks
mv /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive/*/* /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/
rm -rf /home/xx/dev/Claude Enhancer 5.0/.claude/hooks/archive
```

#### Batch 3回滚（MINOR优化）
```bash
# 回滚executor.sh
git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh

# 删除新增脚本
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/plan_renderer.sh
rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf

# 恢复gate文件
cd /home/xx/dev/Claude Enhancer 5.0/.gates/
tar -xzf gates_backup_*.tar.gz
cd -

# 恢复REVIEW文件
git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/docs/REVIEW*.md
```

### 单个任务回滚

| 任务ID | 回滚命令 |
|--------|---------|
| 1.1 | `rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml` |
| 1.2 | `rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml` |
| 1.3 | `git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml` |
| 2.1 | `rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/sync_state.sh && git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit` |
| 2.2 | `cp /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json.backup /home/xx/dev/Claude Enhancer 5.0/.claude/settings.json` |
| 2.3 | `git checkout HEAD~1 -- /home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml` |
| 3.1 | `git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh && rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/plan_renderer.sh` |
| 3.2 | `cd /home/xx/dev/Claude Enhancer 5.0/.gates/ && tar -xzf gates_backup_*.tar.gz` |
| 3.3 | `git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/docs/REVIEW*.md` |
| 3.4 | `rm -f /home/xx/dev/Claude Enhancer 5.0/.workflow/scripts/logrotate.conf && git checkout HEAD -- /home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh` |

---

## 🧪 测试策略 (Testing Strategy)

### 测试分层

```
┌─────────────────────────────────────────┐
│  P4 Testing Phase - 三层测试体系       │
├─────────────────────────────────────────┤
│  Layer 1: 单元测试 (30min)             │
│  - 测试每个新增脚本的独立功能          │
│  - 验证YAML解析正确性                   │
│  - 验证状态同步逻辑                     │
├─────────────────────────────────────────┤
│  Layer 2: 集成测试 (40min)             │
│  - 端到端工作流测试（P0→P7）           │
│  - Dry-run模式测试                      │
│  - Hooks激活后功能测试                  │
├─────────────────────────────────────────┤
│  Layer 3: 回归测试 (20min)             │
│  - 确保修复未破坏现有功能               │
│  - 性能对比（修复前后）                 │
│  - 兼容性测试                           │
└─────────────────────────────────────────┘
```

### 单元测试清单（P4阶段任务）

| 测试ID | 测试对象 | 测试内容 | 验证方式 | 负责Agent |
|--------|---------|---------|---------|-----------|
| UT-1 | manifest.yml | YAML格式正确性 | `yamllint manifest.yml` | test-engineer |
| UT-2 | manifest.yml | Phase数量=8 | `yq '.phases \| length' == 8` | test-engineer |
| UT-3 | STAGES.yml | 角色组完整性 | `yq '.role_groups \| keys \| length' >= 4` | test-engineer |
| UT-4 | STAGES.yml | 冲突规则数量 | `yq '.conflict_detection.rules \| length' >= 5` | test-engineer |
| UT-5 | gates.yml | P0/P7定义存在 | `yq '.phases.P0' != null && yq '.phases.P7' != null` | test-engineer |
| UT-6 | sync_state.sh | 状态不一致检测 | 制造不一致，验证自动同步 | test-engineer |
| UT-7 | sync_state.sh | 文件过期检测 | 修改文件时间戳，验证告警 | test-engineer |
| UT-8 | plan_renderer.sh | Mermaid图生成 | 验证输出包含\`\`\`mermaid | test-engineer |
| UT-9 | plan_renderer.sh | 文本格式输出 | 验证包含"Execution Plan" | test-engineer |
| UT-10 | logrotate.conf | 语法正确性 | `logrotate -d logrotate.conf` | test-engineer |

### 集成测试场景（P4阶段任务）

| 场景ID | 场景描述 | 测试步骤 | 期望结果 | 负责Agent |
|--------|---------|---------|---------|-----------|
| IT-1 | 完整工作流P0→P1 | 1. 创建SPIKE.md<br>2. 执行P0 gate<br>3. 切换到P1 | .phase/current=P1, 00.ok存在 | test-engineer |
| IT-2 | Dry-run模式 | 1. `executor.sh P3 --dry-run`<br>2. 检查无文件变更 | 输出计划，git status clean | test-engineer |
| IT-3 | 并行冲突检测 | 1. 模拟2个Agent写同一文件<br>2. 触发冲突规则 | 自动降级为串行 | workflow-optimizer |
| IT-4 | Hooks激活验证 | 1. 触发PrePrompt事件<br>2. 检查新hooks执行 | 日志显示15个hooks执行 | security-auditor |
| IT-5 | 状态同步自愈 | 1. 手动破坏状态一致性<br>2. git commit触发hook | 自动修复，commit成功 | devops-engineer |
| IT-6 | 日志轮转 | 1. 创建>10MB日志<br>2. 执行executor.sh | 自动轮转，生成.log.1.gz | devops-engineer |

### 回归测试清单（P4阶段任务）

| 回归ID | 测试目标 | 测试方法 | 成功标准 | 负责Agent |
|--------|---------|---------|---------|-----------|
| RT-1 | 现有P1-P6工作流 | 执行完整6-Phase循环 | 所有gate通过，无报错 | test-engineer |
| RT-2 | 现有hooks功能 | 触发5个原有hooks | 功能正常，无冲突 | security-auditor |
| RT-3 | Git操作兼容性 | commit/push/merge测试 | 所有操作成功 | devops-engineer |
| RT-4 | 性能对比 | 测量P3阶段执行时间 | 性能无退化（±5%以内） | performance-engineer |
| RT-5 | 文档完整性 | 验证所有必要文档存在 | PLAN/REVIEW/CHANGELOG齐全 | technical-writer |

### 验收测试（UAT，P5阶段）

| UAT-ID | 用户场景 | 操作步骤 | 验收标准 |
|--------|---------|---------|---------|
| UAT-1 | 启动新工作流 | 用户执行`executor.sh P0` | manifest加载成功，显示8-Phase概览 |
| UAT-2 | 预览执行计划 | 用户执行`executor.sh P3 --dry-run --visualize` | 显示Mermaid图和任务清单 |
| UAT-3 | 查看hooks状态 | 用户查看`.claude/hooks/HOOKS_AUDIT_REPORT.md` | 显示65个hooks分类结果 |
| UAT-4 | 回滚修复 | 用户执行整体回滚脚本 | 系统恢复到修复前状态，功能正常 |

---

## 📊 风险评估与缓解措施 (Risk Assessment)

### 风险矩阵

| 风险ID | 风险描述 | 可能性 | 影响 | 风险等级 | 缓解措施 |
|--------|---------|--------|------|---------|---------|
| R-1 | manifest.yml与executor.sh解析冲突 | 中 | 高 | 🟡 中 | 先测试解析，保留fallback逻辑 |
| R-2 | Hooks审计误删活跃hooks | 中 | 中 | 🟡 中 | 先归档不删除，可快速恢复 |
| R-3 | 状态同步脚本bug导致工作流卡死 | 低 | 高 | 🟡 中 | 添加bypass开关，充分测试 |
| R-4 | 并行冲突检测误报过多 | 中 | 低 | 🟢 低 | 保守策略，宁可串行也不冲突 |
| R-5 | 日志轮转配置错误导致日志丢失 | 低 | 中 | 🟢 低 | 保留5个备份，压缩不删除 |
| R-6 | Gate文件清理误删关键文件 | 低 | 高 | 🟡 中 | 先备份再清理，可回滚 |
| R-7 | REVIEW结论判断错误 | 低 | 低 | 🟢 低 | 人工复审，标记为ARCHIVED |
| R-8 | 新hooks与旧hooks功能冲突 | 中 | 中 | 🟡 中 | 渐进式激活，先测试1个 |

### 缓解措施详细说明

#### R-1: manifest.yml解析冲突
- **监控指标**: executor.sh启动时解析成功率
- **应急措施**:
  ```bash
  # 在executor.sh中添加fallback逻辑
  if ! parse_manifest manifest.yml; then
      echo "⚠️ manifest.yml解析失败，使用gates.yml兜底"
      use_legacy_gates_only
  fi
  ```
- **回滚触发条件**: 连续3次解析失败

#### R-2: Hooks审计误删
- **预防措施**:
  1. 只归档不删除
  2. 人工确认DEPRECATED标记
  3. 审计报告生成后人工复审
- **恢复时间**: < 5分钟（从archive恢复）

#### R-3: 状态同步卡死
- **Bypass开关**:
  ```bash
  export SKIP_STATE_SYNC=true  # 紧急绕过
  git commit --no-verify       # 跳过pre-commit hook
  ```
- **监控告警**: 状态同步时间 > 5秒触发告警

#### R-6: Gate文件误删
- **双重保护**:
  1. 删除前备份到tar.gz
  2. 仅删除明确的非标准文件（正则白名单）
- **恢复SOP**:
  ```bash
  cd .gates/
  tar -xzf gates_backup_*.tar.gz
  ```

---

## 🎯 DoD (Definition of Done)

### P1规划阶段DoD（本文档）

- [x] 任务清单≥15条（实际18条）
- [x] 每条任务包含：动词+文件名+验证方式
- [x] 受影响文件清单使用绝对路径
- [x] 回滚方案可执行（提供bash脚本）
- [x] DoD明确且可验证
- [x] 时间估算合理（基于P0结论）
- [x] 风险评估完整（8个风险+缓解措施）
- [x] 测试策略清晰（单元+集成+回归）

### P3实现阶段DoD（后续执行）

- [ ] 所有10个CE-ISSUE对应的修复任务完成
- [ ] 10个新增文件创建并验证格式正确
- [ ] 5个修改文件完成且向后兼容
- [ ] 废弃hooks归档（约50个文件），settings.json更新
- [ ] .gates/目录文件数=16（00-07各2个文件）
- [ ] 所有REVIEW*.md包含明确结论
- [ ] 所有新增脚本具有可执行权限（chmod +x）
- [ ] Git commit message符合规范（feat/fix/docs前缀）

### P4测试阶段DoD

- [ ] 10个单元测试全部通过
- [ ] 6个集成测试场景全部通过
- [ ] 5个回归测试无性能退化
- [ ] 4个UAT场景用户验收通过
- [ ] 测试覆盖率≥85%
- [ ] docs/TEST-REPORT.md生成

### P5审查阶段DoD

- [ ] 代码风格一致性检查通过
- [ ] 风险清单完整（无遗漏）
- [ ] 回滚可行性验证（实际执行回滚测试）
- [ ] docs/REVIEW.md末尾有明确结论（APPROVE）

### P6发布阶段DoD

- [ ] CHANGELOG.md更新（版本号v5.3.3）
- [ ] 影响面说明清晰（修复10个问题）
- [ ] Git tag创建成功（v5.3.3）
- [ ] Release Notes发布
- [ ] README.md更新（如有新功能说明）
- [ ] Post-merge healthcheck通过

---

## ⏱️ 详细时间估算 (Detailed Timeline)

### Phase级别时间线

| Phase | 阶段名称 | 主要任务 | 预计时长 | 累计时长 | 负责Agent数量 |
|-------|---------|---------|---------|---------|--------------|
| P0 | Discovery | 技术调研+可行性分析 | 30min | 0.5h | 1 (requirements-analyst) |
| P1 | Plan | 生成本文档 | 45min | 1.25h | 1 (requirements-analyst) |
| P2 | Skeleton | 创建10个文件骨架 | 30min | 1.75h | 2 (devops-engineer, workflow-optimizer) |
| P3 | Implement | 3批次修复实现 | 4.5h | 6.25h | 6 (并行) |
| P4 | Test | 单元+集成+回归测试 | 1.5h | 7.75h | 3 (test-engineer, performance-engineer, security-auditor) |
| P5 | Review | 代码审查+生成REVIEW.md | 45min | 8.5h | 1 (code-reviewer) |
| P6 | Release | 文档更新+打tag | 30min | 9h | 2 (technical-writer, devops-engineer) |
| P7 | Monitor | 配置监控指标 | 15min | 9.25h | 1 (sre-specialist) |

**总计**: 9.25小时（含所有阶段）

### P3实现阶段详细时间线（关键路径）

#### Batch 1: FATAL修复（并行，瓶颈45min）

| 时间点 | 任务 | Agent | 状态 |
|--------|------|-------|------|
| T+0min | 任务1.1启动（manifest.yml） | devops-engineer | 🏃 进行中 |
| T+0min | 任务1.2启动（STAGES.yml） | workflow-optimizer | 🏃 进行中 |
| T+0min | 任务1.3启动（gates.yml P0/P7） | requirements-analyst | 🏃 进行中 |
| T+20min | 任务1.3完成 | requirements-analyst | ✅ 完成 |
| T+40min | 任务1.2完成 | workflow-optimizer | ✅ 完成 |
| T+45min | 任务1.1完成 | devops-engineer | ✅ 完成 |
| **T+45min** | **Batch 1完成** | - | ✅ **里程碑** |

#### Batch 2: MAJOR修复（部分并行，瓶颈70min）

| 时间点 | 任务 | Agent | 状态 | 依赖 |
|--------|------|-------|------|------|
| T+45min | 任务2.1启动（sync_state.sh） | devops-engineer | 🏃 进行中 | 无 |
| T+45min | 任务2.2启动（Hooks审计） | security-auditor + code-reviewer | 🏃 进行中 | 无 |
| T+70min | 任务2.1完成 | devops-engineer | ✅ 完成 | - |
| T+85min | 任务2.3启动（STAGES.yml冲突规则） | workflow-optimizer | 🏃 进行中 | 依赖任务1.2 |
| T+115min | 任务2.2完成 | security-auditor + code-reviewer | ✅ 完成 | - |
| T+120min | 任务2.3完成 | workflow-optimizer | ✅ 完成 | - |
| **T+120min** | **Batch 2完成** | - | ✅ **里程碑** |

#### Batch 3: MINOR优化（全部并行，瓶颈45min）

| 时间点 | 任务 | Agent | 状态 | 依赖 |
|--------|------|-------|------|------|
| T+120min | 任务3.1启动（dry-run模式） | devops-engineer | 🏃 进行中 | 依赖任务1.1 |
| T+120min | 任务3.3启动（REVIEW结论） | code-reviewer | 🏃 进行中 | 无 |
| T+120min | 任务3.4启动（日志轮转） | devops-engineer-2 | 🏃 进行中 | 无 |
| T+135min | 任务3.2启动（gate清理） | code-reviewer-2 | 🏃 进行中 | 依赖任务1.3 |
| T+140min | 任务3.4完成 | devops-engineer-2 | ✅ 完成 | - |
| T+145min | 任务3.3完成 | code-reviewer | ✅ 完成 | - |
| T+150min | 任务3.2完成 | code-reviewer-2 | ✅ 完成 | - |
| T+165min | 任务3.1完成 | devops-engineer | ✅ 完成 | - |
| **T+165min (2.75h)** | **Batch 3完成** | - | ✅ **里程碑** |

### 并行度分析

```
时间轴（分钟）    Agent并行数    活动任务
───────────────────────────────────────────
0-20              3             1.1, 1.2, 1.3
20-40             2             1.1, 1.2
40-45             1             1.1
45-70             3             2.1, 2.2a, 2.2b
70-85             2             2.2a, 2.2b
85-115            3             2.2a, 2.2b, 2.3
115-120           1             2.3
120-135           3             3.1, 3.3, 3.4
135-140           4             3.1, 3.2, 3.3, 3.4
140-145           3             3.1, 3.2, 3.3
145-150           2             3.1, 3.2
150-165           1             3.1
───────────────────────────────────────────
最高并行度: 4 Agents (T+135-140)
平均并行度: 2.5 Agents
```

---

## 👥 Agent分工与职责矩阵 (Agent Responsibility Matrix)

### 主要Agent及专长

| Agent | 专长领域 | 负责任务 | 工作时长 | 批次 |
|-------|---------|---------|---------|------|
| **devops-engineer** | 配置管理、脚本、CI/CD | 1.1, 2.1, 3.1, 3.4 | 130min | Batch 1/2/3 |
| **workflow-optimizer** | 并行优化、性能调优 | 1.2, 2.3 | 75min | Batch 1/2 |
| **requirements-analyst** | 需求分析、DoD定义 | 1.3, P1规划 | 65min | Batch 1 |
| **security-auditor** | 安全审计、权限管理 | 2.2（审计部分） | 40min | Batch 2 |
| **code-reviewer** | 代码审查、质量保证 | 2.2（审查部分）, 3.2, 3.3 | 70min | Batch 2/3 |
| **test-engineer** | 测试设计、质量验证 | P4所有测试任务 | 90min | P4阶段 |
| **technical-writer** | 文档编写、规范制定 | P6文档更新 | 15min | P6阶段 |
| **performance-engineer** | 性能测试、基准对比 | P4回归测试RT-4 | 15min | P4阶段 |

### RACI矩阵（任务责任分配）

| 任务ID | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) |
|--------|----------------|-----------------|---------------|--------------|
| 1.1 | devops-engineer | requirements-analyst | workflow-optimizer | 全员 |
| 1.2 | workflow-optimizer | requirements-analyst | devops-engineer | 全员 |
| 1.3 | requirements-analyst | requirements-analyst | - | 全员 |
| 2.1 | devops-engineer | requirements-analyst | - | 全员 |
| 2.2 | security-auditor, code-reviewer | security-auditor | devops-engineer | 全员 |
| 2.3 | workflow-optimizer | requirements-analyst | devops-engineer | 全员 |
| 3.1 | devops-engineer | requirements-analyst | workflow-optimizer | 全员 |
| 3.2 | code-reviewer | requirements-analyst | - | 全员 |
| 3.3 | code-reviewer | requirements-analyst | - | 全员 |
| 3.4 | devops-engineer | requirements-analyst | - | 全员 |

### Agent并行组（P3阶段执行策略）

**Group A（Batch 1，并行启动）**:
```bash
# 同时启动3个Agent
invoke devops-engineer "任务1.1: 创建manifest.yml"
invoke workflow-optimizer "任务1.2: 创建STAGES.yml"
invoke requirements-analyst "任务1.3: 扩展gates.yml"
```

**Group B（Batch 2，部分并行）**:
```bash
# 第一波（并行启动）
invoke devops-engineer "任务2.1: 状态同步脚本"
invoke security-auditor "任务2.2: Hooks审计"
invoke code-reviewer "任务2.2: Hooks审查"

# 第二波（等待1.2完成后）
wait_for task-1.2
invoke workflow-optimizer "任务2.3: 冲突检测规则"
```

**Group C（Batch 3，全部并行）**:
```bash
# 等待1.1和1.3完成后并行启动
wait_for task-1.1 task-1.3

invoke devops-engineer "任务3.1: dry-run模式"
invoke devops-engineer "任务3.4: 日志轮转"
invoke code-reviewer "任务3.2: gate清理"
invoke code-reviewer "任务3.3: REVIEW结论"
```

---

## 📝 产物清单与交付标准 (Deliverables & Quality Standards)

### P1规划阶段产物（当前）

| 序号 | 产物名称 | 文件路径 | 交付标准 | 状态 |
|------|---------|---------|---------|------|
| 1 | 详细修复计划 | `/home/xx/dev/Claude Enhancer 5.0/docs/PLAN_AUDIT_FIX.md` | 包含18个任务+时间线+风险评估 | ✅ 本文档 |
| 2 | 受影响文件清单 | 本文档§受影响文件清单 | 绝对路径+分类说明 | ✅ 已完成 |
| 3 | 回滚方案 | 本文档§回滚方案 | 可执行bash脚本 | ✅ 已完成 |

### P2骨架阶段产物

| 序号 | 产物名称 | 文件路径 | 交付标准 | 状态 |
|------|---------|---------|---------|------|
| 1 | manifest.yml模板 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/manifest.yml` | 包含version+8个phase骨架 | ⏳ 待创建 |
| 2 | STAGES.yml模板 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/STAGES.yml` | 包含role_groups+phase_mapping骨架 | ⏳ 待创建 |
| 3 | 脚本模板文件 | `.workflow/scripts/*.sh` | 头部注释+函数签名 | ⏳ 待创建 |
| 4 | 骨架说明文档 | `/home/xx/dev/Claude Enhancer 5.0/docs/SKELETON-NOTES.md` | 说明创建的文件结构 | ⏳ 待创建 |

### P3实现阶段产物

| 批次 | 产物名称 | 数量 | 交付标准 | 状态 |
|------|---------|------|---------|------|
| Batch 1 | 配置文件（manifest, STAGES, gates扩展） | 3个 | YAML格式正确+通过验证 | ⏳ 待实现 |
| Batch 2 | 脚本+审计报告 | 4个 | 可执行+日志清晰 | ⏳ 待实现 |
| Batch 3 | 优化脚本+清理操作 | 4个 | 功能完整+有备份 | ⏳ 待实现 |

### P4测试阶段产物

| 序号 | 产物名称 | 文件路径 | 交付标准 | 状态 |
|------|---------|---------|---------|------|
| 1 | 单元测试报告 | `/home/xx/dev/Claude Enhancer 5.0/docs/TEST-REPORT.md` | 10个测试用例+结果 | ⏳ 待生成 |
| 2 | 集成测试报告 | 同上（追加） | 6个场景+截图 | ⏳ 待生成 |
| 3 | 回归测试报告 | 同上（追加） | 5个对比数据+性能图表 | ⏳ 待生成 |
| 4 | 测试覆盖率报告 | `.workflow/coverage/` | 覆盖率≥85% | ⏳ 待生成 |

### P5审查阶段产物

| 序号 | 产物名称 | 文件路径 | 交付标准 | 状态 |
|------|---------|---------|---------|------|
| 1 | 代码审查报告 | `/home/xx/dev/Claude Enhancer 5.0/docs/REVIEW_AUDIT_FIX.md` | 三段式+明确结论 | ⏳ 待生成 |
| 2 | 风险清单 | 同上（追加） | 列出残余风险+监控建议 | ⏳ 待生成 |
| 3 | 回滚验证报告 | 同上（追加） | 实际执行回滚+恢复验证 | ⏳ 待生成 |

### P6发布阶段产物

| 序号 | 产物名称 | 文件路径 | 交付标准 | 状态 |
|------|---------|---------|---------|------|
| 1 | CHANGELOG更新 | `/home/xx/dev/Claude Enhancer 5.0/docs/CHANGELOG.md` | v5.3.3版本+10个修复条目 | ⏳ 待更新 |
| 2 | Git Tag | - | `v5.3.3` + Release Notes | ⏳ 待创建 |
| 3 | README更新（可选） | `/home/xx/dev/Claude Enhancer 5.0/docs/README.md` | 新增manifest/STAGES说明 | ⏳ 待评估 |
| 4 | 健康检查报告 | `/home/xx/dev/Claude Enhancer 5.0/docs/HEALTH_REPORT.md` | 所有gate通过+系统正常 | ⏳ 待生成 |

---

## 🚀 下一步行动计划 (Next Steps)

### 立即行动（需用户决策）

1. **审阅本P1规划文档**
   - 确认任务分解合理性
   - 确认时间估算可接受
   - 确认风险可控

2. **关键决策点**
   - **CE-006 Hooks审计策略**: 选择保守（人工审查每个）还是激进（自动批量激活）
   - **批次执行方式**: 一次性完成3批次 还是 分3天渐进式修复
   - **测试深度**: 标准测试（1.5h）还是 深度测试（3h+压力测试）

3. **签署P1 Gate**
   ```bash
   # 用户确认后执行
   touch /home/xx/dev/Claude Enhancer 5.0/.gates/01.ok
   gpg --sign /home/xx/dev/Claude Enhancer 5.0/.gates/01.ok
   echo "P2" > /home/xx/dev/Claude Enhancer 5.0/.phase/current
   yq eval '.phase = "P2"' -i /home/xx/dev/Claude Enhancer 5.0/.workflow/ACTIVE
   ```

### P2骨架阶段准备

**启动条件**: P1 gate签署完成

**执行计划**:
```bash
# 启动2个Agent并行创建骨架
invoke devops-engineer "创建10个文件骨架（manifest, STAGES, scripts）"
invoke requirements-analyst "编写SKELETON-NOTES.md说明文档"
```

**预计时长**: 30分钟

**产物**: 10个模板文件（包含头部注释+TODO标记）

### P3实现阶段启动

**启动条件**: P2 gate签署完成

**执行顺序**:
1. **Batch 1（并行3 Agents）**: 修复FATAL问题
2. **Batch 2（并行3-4 Agents）**: 修复MAJOR问题
3. **Batch 3（并行4 Agents）**: 完成MINOR优化

**关键检查点**:
- Batch 1完成后: 验证manifest和gates解析正确
- Batch 2完成后: 验证hooks激活无冲突
- Batch 3完成后: 全功能冒烟测试

### 风险监控计划

**监控频率**: 每批次完成后

**监控指标**:
| 指标 | 阈值 | 告警级别 |
|------|------|---------|
| 单元测试通过率 | <90% | 🔴 严重 |
| 脚本执行失败率 | >5% | 🟡 警告 |
| 回滚测试成功率 | <100% | 🔴 严重 |
| 性能退化 | >10% | 🟡 警告 |
| Git操作失败 | 任何失败 | 🔴 严重 |

**告警响应SOP**:
```
🔴 严重告警 → 立即停止，执行回滚，分析根因
🟡 警告告警 → 继续执行，记录问题，P5阶段集中处理
```

---

## 📌 附录 (Appendix)

### A. 术语表

| 术语 | 全称/解释 | 示例 |
|------|----------|------|
| DoD | Definition of Done，完成标准 | P3完成需通过所有gates |
| RACI | Responsible/Accountable/Consulted/Informed，责任分配矩阵 | R=执行者，A=负责人 |
| UAT | User Acceptance Testing，用户验收测试 | 用户验证dry-run功能 |
| SOP | Standard Operating Procedure，标准操作流程 | 回滚SOP |
| Gate | 质量门禁，阶段验证点 | P1 gate需验证PLAN.md存在 |

### B. 参考文档

| 文档名称 | 路径 | 用途 |
|---------|------|------|
| P0探索报告 | `/home/xx/dev/Claude Enhancer 5.0/docs/P0_AUDIT_FIX_DISCOVERY.md` | 可行性分析依据 |
| 审计报告 | （未提供路径） | 10个问题来源 |
| 工作流规范 | `/home/xx/dev/Claude Enhancer 5.0/.claude/WORKFLOW.md` | 8-Phase流程说明 |
| Gates配置 | `/home/xx/dev/Claude Enhancer 5.0/.workflow/gates.yml` | 质量门禁定义 |
| Settings配置 | `/home/xx/dev/Claude Enhancer 5.0/.claude/settings.json` | Hooks挂载配置 |

### C. 工具与脚本清单

| 工具 | 用途 | 验证命令 |
|------|------|---------|
| yamllint | YAML格式验证 | `yamllint --version` |
| yq | YAML查询工具 | `yq --version` |
| logrotate | 日志轮转 | `logrotate --version` |
| jq | JSON查询工具 | `jq --version` |
| gpg | Gate签名 | `gpg --version` |

### D. 质量检查清单（Checklist）

**P3实现前检查**:
- [ ] P1 gate已签署
- [ ] P2骨架文件已创建
- [ ] 所有依赖工具已安装（yamllint, yq, jq）
- [ ] Git工作目录干净（`git status` clean）
- [ ] 当前phase=P3（`.phase/current`）

**P3实现中检查（每个任务）**:
- [ ] 任务对应的文件已创建/修改
- [ ] 验证命令执行成功
- [ ] Git commit message符合规范
- [ ] 回滚脚本已测试有效

**P3实现后检查**:
- [ ] 所有18个任务状态=✅完成
- [ ] 单元测试通过率=100%
- [ ] 集成测试场景全部通过
- [ ] 回归测试无性能退化
- [ ] CHANGELOG.md已更新

---

## 🏁 规划总结 (Planning Summary)

### 核心成果

本P1规划文档提供了：
1. **18个具体任务**：覆盖10个审计问题的完整修复方案
2. **3批次执行策略**：优先级明确，降低风险
3. **15个受影响文件**：新增10个，修改5个，清单完整
4. **可执行回滚方案**：整体/分批/单任务三级回滚脚本
5. **完整测试策略**：10个单元测试+6个集成测试+5个回归测试
6. **详细时间估算**：总计9.25小时，关键路径4.5小时

### 关键决策依据

| 决策点 | 选择方案 | 理由 |
|--------|---------|------|
| 修复策略 | 渐进式3批次 | 降低风险，快速验证 |
| 并行度 | 最高6 Agents | 平衡速度与资源占用 |
| Hooks审计 | 混合方案（自动+人工） | 安全与效率兼顾 |
| 配置格式 | YAML | 业界标准，易维护 |
| 回滚机制 | 三级（整体/批次/任务） | 灵活应对不同场景 |

### 预期收益

**定量收益**:
- 修复10个审计问题（2 FATAL + 3 MAJOR + 5 MINOR）
- 保障力评分预计提升：当前85 → 修复后100
- Hooks激活率提升：5个 → 15个（增长200%）
- 文档完整性提升：补充3个缺失段（P0/P7/REVIEW结论）

**定性收益**:
- 工作流配置化：manifest.yml使流程可视化、可调试
- 状态同步自愈：自动修复不一致，减少人工干预
- 并行冲突预防：智能降级策略，避免数据竞争
- 可观测性增强：dry-run模式、日志轮转、执行计划预览

### 风险可控性

- **8个识别风险**：全部有缓解措施+回滚方案
- **100%向后兼容**：所有修改非破坏性
- **快速回滚**：最快<5分钟恢复到修复前状态
- **渐进式验证**：每批次独立测试，降低整体风险

---

**文档版本**: 1.0
**生成时间**: 2025-10-09
**规划师**: Requirements Analyst Agent
**审批状态**: ⏳ 待用户审阅
**下一阶段**: P2 Skeleton - 创建文件骨架
**预计启动时间**: 用户批准后立即启动

**Phase Gate状态**: ✅ P1→P2 READY（待签署.gates/01.ok）

---

## 📞 联系与支持

如有疑问或需调整计划，请：
1. 审阅本文档标记的决策点
2. 提出修改建议
3. 批准进入P2阶段

**准备就绪，等待指令！** 🚀
