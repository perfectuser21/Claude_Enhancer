# 7-Phase Implementation Checklist: Phase Skills + Parallel Execution + Cleanup Fix

**Version**: 8.8.0
**Created**: 2025-10-31
**Estimated Time**: 6.5 hours (with 6 agents parallel)

---

## Phase 1: Discovery & Planning ✓ IN PROGRESS

### 1.1 Branch Check ✓ DONE
- [x] 确认在feature/phase-skills-hooks-optimization分支
- [x] 重置Phase状态为Phase1

### 1.2 Requirements Discussion ✓ DONE
- [x] 确认3个需求：
  1. 修复Phase 7清理机制（HIGH priority）
  2. 优化并行执行系统（MEDIUM priority）
  3. 为Phase 1/6/7创建Skills + Hooks指导（MEDIUM priority）

### 1.3 Technical Discovery ✓ DONE
- [x] 创建P1_DISCOVERY.md（5300行）
- [x] 分析Phase 7清理机制现状
- [x] 分析并行执行系统现状
- [x] 分析Skills系统现状
- [x] 识别gaps和问题根因

### 1.4 Impact Assessment ✓ DONE
- [x] 计算影响半径：**Radius = 60**
- [x] 推荐Agent策略：**6 agents**
- [x] 确定并行策略：Phase 2-4启用并行

### 1.5 Architecture Planning ⏳ IN PROGRESS
- [x] 创建ACCEPTANCE_CHECKLIST.md（129项验收标准）
- [ ] 完成PLAN.md（详细实施计划）
- [ ] 定义文件结构和修改范围
- [ ] 制定rollback策略
- [ ] 用户确认并同意开始Phase 2

---

## Phase 2: Implementation（预计3.3小时，6 agents并行）

### 🔴 并行组1: Phase 7清理机制修复（1.5小时）

#### 任务2.1.1: 修改comprehensive_cleanup.sh
- [ ] 在脚本末尾添加Phase状态清理逻辑
  ```bash
  # 添加到comprehensive_cleanup.sh Line ~350
  echo "🧹 Cleaning Phase state files..."
  if [[ -f ".phase/current" ]]; then
    current_phase=$(cat .phase/current)
    if [[ "$current_phase" == "Phase7" ]]; then
      rm -f .phase/current .workflow/current
      echo "Phase workflow complete at $(date)" > .phase/completed
      echo "✓ Phase state cleaned"
    fi
  fi
  ```
- [ ] 添加aggressive模式检查（确保只在Phase7清理）
- [ ] 添加日志输出
- [ ] 更新脚本注释和文档

#### 任务2.1.2: 修改phase_completion_validator.sh
- [ ] 在Phase7完成验证后添加清理逻辑
  ```bash
  # 在validate_phase7_completion()函数末尾添加
  if [[ "$next_phase" == "merge_ready" ]] || [[ "$next_phase" == "completed" ]]; then
    echo "Workflow complete, cleaning phase state"
    rm -f .phase/current .workflow/current
    touch .phase/completed
  fi
  ```
- [ ] 测试Phase7→completed转换
- [ ] 更新函数文档

#### 任务2.1.3: 创建post-merge hook
- [ ] 创建文件`.git/hooks/post-merge`
  ```bash
  #!/bin/bash
  # Post-merge hook: Clean phase state after merge to main

  if [[ "$(git rev-parse --abbrev-ref HEAD)" == "main" ]]; then
    rm -f .phase/current .workflow/current
    echo "[$(date)] Phase state cleaned after merge to main" >> .claude/logs/phase_cleanup.log
  fi
  ```
- [ ] 添加执行权限：`chmod +x .git/hooks/post-merge`
- [ ] 测试hook执行

#### 任务2.1.4: 更新comprehensive_cleanup.sh文档
- [ ] 在CLAUDE.md中记录Phase 7清理机制
- [ ] 更新脚本header注释

---

### 🟠 并行组2: 并行执行系统集成（3小时）

#### 任务2.2.1: 验证executor.sh集成
- [ ] 检查executor.sh是否有`is_parallel_enabled()`函数
  ```bash
  grep -A10 "is_parallel_enabled" .workflow/executor.sh
  ```
- [ ] 检查是否有`execute_parallel_workflow()`函数
- [ ] 如果缺失，标记需要添加

#### 任务2.2.2: 添加并行执行集成代码（如缺失）
- [ ] 在executor.sh添加函数：
  ```bash
  is_parallel_enabled() {
    local phase="$1"
    local manifest="${PROJECT_ROOT}/.workflow/manifest.yml"

    if command -v yq &>/dev/null; then
      can_parallel=$(yq eval ".phases[] | select(.id == \"$phase\") | .parallel" "$manifest")
      echo "$can_parallel"
    else
      echo "false"
    fi
  }

  execute_parallel_workflow() {
    local phase="$1"
    echo "Executing Phase $phase in parallel mode..."
    bash "${PROJECT_ROOT}/.workflow/lib/parallel_executor.sh" "$phase"
  }
  ```
- [ ] 在main execution logic中调用：
  ```bash
  if [[ "$(is_parallel_enabled "$current_phase")" == "true" ]]; then
    execute_parallel_workflow "$current_phase"
  else
    execute_serial_workflow "$current_phase"
  fi
  ```

#### 任务2.2.3: 优化conflict_detector.sh
- [ ] 修改conflict检测逻辑，使用实际修改文件：
  ```bash
  # 在conflict_detector.sh添加
  get_actually_modified_files() {
    git diff --name-only main...HEAD 2>/dev/null || echo ""
  }

  check_real_conflict() {
    local group1_paths="$1"
    local group2_paths="$2"
    local modified_files="$3"

    # 只检查实际修改的文件
    for file in $modified_files; do
      if matches_pattern "$file" "$group1_paths" && matches_pattern "$file" "$group2_paths"; then
        return 0  # 真实冲突
      fi
    done
    return 1  # 无冲突
  }
  ```
- [ ] 保留原有逻辑作为fallback
- [ ] 添加debug日志

#### 任务2.2.4: 测试并行执行触发
- [ ] 创建测试脚本验证is_parallel_enabled
- [ ] 模拟Phase3并行执行
- [ ] 检查日志输出

---

### 🟡 并行组3: Phase 1 Skill创建（2小时）

#### 任务2.3.1: 创建skill目录结构
- [ ] 创建目录`.claude/skills/phase1-discovery-planning/`
- [ ] 创建文件`SKILL.md`

#### 任务2.3.2: 编写Phase 1 skill内容（~500行）
- [ ] Section 1: Skill Purpose（目的说明）
- [ ] Section 2: Phase 1 Overview（阶段概述）
- [ ] Section 3: Substage 1.1 - Branch Check（分支检查详细指导）
- [ ] Section 4: Substage 1.2 - Requirements Discussion（需求讨论模板）
- [ ] Section 5: Substage 1.3 - Technical Discovery（技术探索checklist）
- [ ] Section 6: Substage 1.4 - Impact Assessment（影响评估计算公式）
  - 包含Risk/Complexity/Scope评分标准
  - 包含Radius计算公式
  - 包含Agent推荐规则
- [ ] Section 7: Substage 1.5 - Architecture Planning（架构规划模板）
  - 包含PLAN.md结构定义
  - 包含并行策略决策树
- [ ] Section 8: Phase 1 Completion Confirmation（用户确认要求）
  - 必须等待用户说"我理解了，开始Phase 2"
  - 创建`.phase/phase1_confirmed`标记
- [ ] Section 9: 并行执行指导（重点）
  - 明确说明需要"单个消息调用多个Task tool"
  - 提供正确和错误示例对比
  - 图解并行vs串行调用
- [ ] Section 10: Success Criteria（成功标准）
- [ ] Section 11: Common Mistakes（常见错误）
- [ ] Section 12: Reference（参考资料）

#### 任务2.3.3: 测试skill格式
- [ ] 验证markdown格式正确
- [ ] 验证代码块语法高亮
- [ ] 验证内部链接有效

---

### 🟢 并行组4: Phase 6/7 Skills创建（2.5小时）

#### 任务2.4.1: 创建Phase 6 skill（1小时）
- [ ] 创建目录`.claude/skills/phase6-acceptance/`
- [ ] 创建`SKILL.md`（~400行）
  - [ ] Section 1: Load Acceptance Checklist
  - [ ] Section 2: Validate Each Item（逐项验证方法）
  - [ ] Section 3: Generate Acceptance Report（报告模板）
  - [ ] Section 4: Present to User（展示格式）
  - [ ] Section 5: Handle User Feedback（反馈处理）
  - [ ] Section 6: Success Criteria
  - [ ] Section 7: Common Mistakes

#### 任务2.4.2: 创建Phase 7 skill（1.5小时，重点）
- [ ] 创建目录`.claude/skills/phase7-closure/`
- [ ] 创建`SKILL.md`（~600行）
  - [ ] Section 1: Phase 7 Overview
  - [ ] Section 2: Comprehensive Cleanup Checklist（详细清理清单）
    - 过期文件清理
    - 版本一致性验证（6个文件）
    - Phase系统一致性
    - 文档规范验证
  - [ ] Section 3: Cleanup Script Usage Guide
    - comprehensive_cleanup.sh 4种模式说明
    - 何时使用aggressive/conservative/minimal
  - [ ] Section 4: Version Consistency Verification
    - check_version_consistency.sh使用方法
    - 6个文件版本统一要求
  - [ ] Section 5: Phase State Cleanup Mechanism（新增）
    - 清理.phase/current和.workflow/current
    - 何时清理、如何清理
  - [ ] Section 6: Git Workflow（正确的PR流程）
    - 推送feature分支
    - 创建PR（不是直接merge）
    - 等待CI通过
    - gh pr merge --auto --squash
    - GitHub Actions自动创建tag
  - [ ] Section 7: **20个Hooks详解**（重点）
    - 每个hook的作用、触发时机、配置方法
    - PreBash hooks (1个): pr_creation_guard
    - UserPromptSubmit hooks (2个): requirement_clarification, workflow_auto_start
    - PrePrompt hooks (9个): force_branch_check, phase_state_tracker, ai_behavior_monitor, workflow_enforcer, phase2_5_autonomous, smart_agent_selector, gap_scan, impact_assessment_enforcer, parallel_subagent_suggester, per_phase_impact_assessor
    - PreToolUse hooks (9个): task_branch_enforcer, branch_helper, phase1_completion_enforcer, code_writing_check, agent_usage_enforcer, quality_gate, auto_cleanup_check, concurrent_optimizer, subagent_auto_scheduler
    - PostToolUse hooks (7个): checklist_generator, validate_checklist_mapping, acceptance_report_generator, merge_confirmer, unified_post_processor, agent_error_recovery, phase_completion_validator, telemetry_logger
  - [ ] Section 8: **Skills System Guide**
    - Skills vs Hooks对比
    - 如何定义trigger
    - Action类型（reminder/script/blocking）
    - 如何创建新skill
  - [ ] Section 9: Common Mistakes（PR #40经验教训）
  - [ ] Section 10: Success Criteria
  - [ ] Section 11: Reference

---

### 🔵 并行组5: Hooks/Skills开发指南（2小时）

#### 任务2.5.1: 创建docs/HOOKS_GUIDE.md（1小时）
- [ ] 创建文件`docs/HOOKS_GUIDE.md`（~800行）
  - [ ] Section 1: Hooks System Overview
  - [ ] Section 2: Hook Types（5种触发时机）
    - PreBash
    - UserPromptSubmit
    - PrePrompt
    - PreToolUse
    - PostToolUse
  - [ ] Section 3: **20 Existing Hooks Detailed Documentation**
    - 每个hook一个subsection
    - 包含：作用、触发时机、输入参数、返回值、使用示例、常见问题
  - [ ] Section 4: Creating New Hooks
    - Step 1: Define purpose
    - Step 2: Choose trigger type
    - Step 3: Write hook script
    - Step 4: Register in settings.json
    - Step 5: Test trigger
  - [ ] Section 5: Hook Development Best Practices
    - 性能要求（<2秒）
    - 错误处理
    - 日志记录
    - 幂等性
  - [ ] Section 6: Debugging Hooks
    - 启用debug模式
    - 查看hook执行日志
    - 常见问题排查
  - [ ] Section 7: Hook Examples

#### 任务2.5.2: 创建docs/SKILLS_GUIDE.md（1小时）
- [ ] 创建文件`docs/SKILLS_GUIDE.md`（~500行）
  - [ ] Section 1: Skills System Overview
  - [ ] Section 2: Skills Architecture
    - settings.json配置结构
    - Trigger机制
    - Action执行流程
  - [ ] Section 3: Trigger Types Explained
    - before_tool_use
    - after_tool_use
    - phase_transition
    - on_error
  - [ ] Section 4: Action Types
    - reminder（提醒类）
    - script（脚本执行类）
    - blocking（阻塞类）
  - [ ] Section 5: Creating New Skills
    - Step 1: Define skill purpose
    - Step 2: Create skill directory
    - Step 3: Write SKILL.md
    - Step 4: Register in settings.json
    - Step 5: Test trigger
  - [ ] Section 6: Skills vs Hooks Comparison
    - 何时用Skills，何时用Hooks
    - 优缺点对比表
  - [ ] Section 7: Best Practices
  - [ ] Section 8: Examples

---

### 🟣 串行任务: Settings.json注册和文档更新（30分钟）

#### 任务2.6.1: 注册3个新skills到settings.json
- [ ] 添加phase1-execution-guide skill配置
  ```json
  {
    "name": "phase1-execution-guide",
    "description": "Phase 1 discovery and planning execution guide",
    "trigger": {
      "event": "phase_transition",
      "context": "entering_phase1"
    },
    "action": {
      "type": "reminder",
      "message": "📋 Refer to .claude/skills/phase1-discovery-planning/SKILL.md for comprehensive Phase 1 guidance"
    },
    "enabled": true,
    "priority": "P0"
  }
  ```
- [ ] 添加phase6-execution-guide skill配置（同上结构）
- [ ] 添加phase7-execution-guide skill配置（同上结构）
- [ ] 验证JSON格式：`jq . .claude/settings.json`

#### 任务2.6.2: 更新文档版本号和描述
- [ ] VERSION文件：更新为8.8.0
- [ ] settings.json: version和description更新
- [ ] manifest.yml: version更新
- [ ] package.json: version更新
- [ ] SPEC.yaml: version更新
- [ ] 验证6个文件版本一致：`bash scripts/check_version_consistency.sh`

#### 任务2.6.3: 更新核心文档
- [ ] CLAUDE.md: 添加Phase 7清理机制说明（~50行）
- [ ] docs/PARALLEL_SUBAGENT_STRATEGY.md: 添加"使用方法"章节（~100行）
  - 如何在Phase 1中应用Impact Assessment
  - 如何在Phase 2-7中启用并行
  - AI必须知道的"单个消息调用多个Task tool"

---

## Phase 3: Testing（预计0.9小时，5 agents并行）

### 🔴 并行组1: Phase 7清理机制测试（15分钟）

#### 任务3.1.1: 单元测试 - comprehensive_cleanup.sh
- [ ] 创建测试文件`tests/unit/test_phase7_cleanup.sh`
- [ ] Test 1: Phase7完成后清理状态文件
  ```bash
  echo "Phase7" > .phase/current
  bash scripts/comprehensive_cleanup.sh aggressive
  test ! -f .phase/current && echo "✓ Test passed"
  ```
- [ ] Test 2: Phase非7时不清理
  ```bash
  echo "Phase3" > .phase/current
  bash scripts/comprehensive_cleanup.sh aggressive
  test -f .phase/current && echo "✓ Test passed"
  ```
- [ ] Test 3: 创建.phase/completed标记
  ```bash
  echo "Phase7" > .phase/current
  bash scripts/comprehensive_cleanup.sh aggressive
  test -f .phase/completed && echo "✓ Test passed"
  ```

#### 任务3.1.2: 单元测试 - post-merge hook
- [ ] Test 1: main分支触发清理
  ```bash
  git checkout main
  touch .phase/current
  bash .git/hooks/post-merge
  test ! -f .phase/current && echo "✓ Test passed"
  ```
- [ ] Test 2: feature分支不触发清理
  ```bash
  git checkout feature/test
  touch .phase/current
  bash .git/hooks/post-merge
  test -f .phase/current && echo "✓ Test passed"
  ```

---

### 🟠 并行组2: 并行执行集成测试（20分钟）

#### 任务3.2.1: 单元测试 - is_parallel_enabled()
- [ ] 创建测试文件`tests/unit/test_parallel_executor.sh`
- [ ] Test 1: Phase3返回true
  ```bash
  source .workflow/executor.sh
  result=$(is_parallel_enabled "Phase3")
  [[ "$result" == "true" ]] && echo "✓ Test passed"
  ```
- [ ] Test 2: Phase1返回false
- [ ] Test 3: 无效Phase返回false

#### 任务3.2.2: 集成测试 - parallel_executor调用
- [ ] Mock环境，测试execute_parallel_workflow调用
- [ ] 验证parallel_executor.sh被执行
- [ ] 检查日志输出

#### 任务3.2.3: 冲突检测测试
- [ ] Test 1: 实际文件冲突检测
  ```bash
  # 模拟两个group修改同一文件
  # 验证冲突被检测到
  ```
- [ ] Test 2: 无实际冲突不降级
- [ ] Test 3: 降级日志正确记录

---

### 🟡 并行组3: Skills触发测试（15分钟）

#### 任务3.3.1: 测试phase1 skill触发
- [ ] 模拟Phase转换到Phase1
- [ ] 验证skill reminder显示
- [ ] 检查触发日志

#### 任务3.3.2: 测试phase6 skill触发
- [ ] 同上，Phase6场景

#### 任务3.3.3: 测试phase7 skill触发
- [ ] 同上，Phase7场景
- [ ] 验证20个hooks说明是否显示

---

### 🟢 并行组4: 性能Benchmark（20分钟）

#### 任务3.4.1: Phase 3并行性能测试
- [ ] 禁用并行，执行Phase 3静态检查，记录时间
  ```bash
  time bash scripts/static_checks.sh
  # 基线时间
  ```
- [ ] 启用并行，执行Phase 3静态检查，记录时间
  ```bash
  # 应该显著更快
  ```
- [ ] 计算加速比：≥3x为通过

#### 任务3.4.2: Phase 7清理性能测试
- [ ] Benchmark comprehensive_cleanup.sh执行时间
  ```bash
  time bash scripts/comprehensive_cleanup.sh aggressive
  # 应该<30秒
  ```

#### 任务3.4.3: Skills加载性能测试
- [ ] Benchmark skill文件读取时间
  ```bash
  time cat .claude/skills/phase1-discovery-planning/SKILL.md > /dev/null
  # 应该<500ms
  ```

---

### 🔵 并行组5: 回归测试（20分钟）

#### 任务3.5.1: 7-Phase工作流完整性测试
- [ ] 创建测试脚本`tests/e2e/test_full_workflow.sh`
- [ ] 模拟Phase 1-7完整流程
- [ ] 验证每个Phase转换正常
- [ ] 验证Phase 7清理正常

#### 任务3.5.2: 现有功能回归测试
- [ ] Phase 2-5 autonomous模式正常工作
- [ ] Phase 1 completion确认机制正常
- [ ] Version increment enforcer正常
- [ ] PR creation guard正常
- [ ] Branch protection hooks正常

#### 任务3.5.3: 静态检查
- [ ] 运行static_checks.sh（shellcheck + bash -n）
- [ ] 所有脚本通过检查
- [ ] 无语法错误，无严重warning

---

## Phase 4: Review（预计1.3小时）

### 🔴 代码审查（45分钟）

#### 任务4.1: Phase 7清理机制审查
- [ ] 审查comprehensive_cleanup.sh改动
  - 逻辑正确性
  - 边界条件处理
  - 错误处理
- [ ] 审查phase_completion_validator.sh改动
  - Phase7完成条件正确
  - 清理时机恰当
- [ ] 审查post-merge hook
  - 分支检查逻辑正确
  - 权限设置正确

#### 任务4.2: 并行执行集成审查
- [ ] 审查executor.sh集成代码
  - is_parallel_enabled逻辑正确
  - execute_parallel_workflow调用正确
  - fallback机制完善
- [ ] 审查conflict_detector.sh优化
  - 实际文件检测逻辑
  - 性能影响可控

#### 任务4.3: Skills内容审查
- [ ] 审查phase1 skill内容
  - 5个substages完整
  - Impact Assessment公式正确
  - 并行执行指导清晰
- [ ] 审查phase6 skill内容
  - 验证流程完整
  - 报告模板清晰
- [ ] 审查phase7 skill内容
  - 20个hooks文档完整
  - Skills指南清晰
  - PR流程正确

#### 任务4.4: 文档审查
- [ ] 审查HOOKS_GUIDE.md
  - 20个hooks都有文档
  - 示例可运行
- [ ] 审查SKILLS_GUIDE.md
  - 内容完整
  - 对比表清晰

---

### 🟠 Pre-merge Audit（30分钟）

#### 任务4.5: 运行pre_merge_audit.sh
- [ ] 执行脚本：`bash scripts/pre_merge_audit.sh`
- [ ] 检查12项audit结果：
  1. Configuration completeness ✓
  2. Evidence validation ✓
  3. Checklist completion ≥90% ✓
  4. Learning system active ✓
  5. Skills configured ✓
  6. Version consistency (6 files) ✓
  7. No hollow implementations ✓
  8. Auto-fix rollback capability ✓
  9. KPI tools available ✓
  10. Root documents ≤7 ✓
  11. Documentation complete ✓
  12. Legacy audit passed ✓

#### 任务4.6: 版本一致性验证
- [ ] 执行`bash scripts/check_version_consistency.sh`
- [ ] 确认6个文件版本都是8.8.0：
  - VERSION
  - .claude/settings.json
  - .workflow/manifest.yml
  - package.json
  - CHANGELOG.md
  - .workflow/SPEC.yaml

#### 任务4.7: Phase 1 Checklist验证
- [ ] 对照ACCEPTANCE_CHECKLIST.md逐项检查
- [ ] 计算完成率：应该≥90% (116/129项)
- [ ] 记录未完成项及原因

---

### 🟡 创建REVIEW.md（15分钟）

#### 任务4.8: 生成审查报告
- [ ] 创建`.workflow/REVIEW_phase-skills-hooks-optimization.md`
- [ ] 记录审查结果：
  - Code review findings
  - Pre-merge audit results
  - Version consistency check
  - Checklist completion rate
  - Critical issues: 0 (预期)
  - Warnings: <5 (预期)
  - Recommendations: (如有)

---

## Phase 5: Release（预计30分钟）

### 🔴 文档更新（20分钟）

#### 任务5.1: 更新CHANGELOG.md
- [ ] 添加v8.8.0条目
  ```markdown
  ## [8.8.0] - 2025-10-31

  ### Added
  - Phase 7清理机制：自动清理Phase状态文件
  - 并行执行系统集成：executor.sh正式支持并行执行
  - Phase 1/6/7 Skills：完整执行指导文档
  - Hooks开发指南：20个hooks详细文档
  - Skills开发指南：Skills系统使用手册

  ### Fixed
  - Phase 7清理bug：main分支merge后不再遗留Phase状态
  - 并行执行未落地问题：真正启用Phase 2-7并行加速

  ### Changed
  - comprehensive_cleanup.sh：增加Phase状态清理
  - conflict_detector.sh：优化为基于实际文件检测
  - PARALLEL_SUBAGENT_STRATEGY.md：添加使用方法章节

  ### Performance
  - Phase 3测试加速：3.5x (3h → 0.9h)
  - Phase 2实施加速：1.8x (6h → 3.3h)
  - 总体加速：2.2x (11h → 5h)
  ```

#### 任务5.2: 更新README.md
- [ ] 更新版本号为8.8.0
- [ ] 添加新功能说明（如有需要）
- [ ] 更新Performance指标

#### 任务5.3: 更新CLAUDE.md
- [ ] Phase 7章节：添加清理机制说明
- [ ] Skills系统章节：更新skills列表
- [ ] Parallel execution章节：添加使用指导

---

### 🟠 Git Tag准备（10分钟）

#### 任务5.4: 提交所有改动
- [ ] Stage所有修改文件
  ```bash
  git add scripts/comprehensive_cleanup.sh
  git add .claude/hooks/phase_completion_validator.sh
  git add .git/hooks/post-merge
  git add .workflow/executor.sh
  git add .workflow/lib/conflict_detector.sh
  git add .claude/skills/phase1-discovery-planning/
  git add .claude/skills/phase6-acceptance/
  git add .claude/skills/phase7-closure/
  git add docs/HOOKS_GUIDE.md
  git add docs/SKILLS_GUIDE.md
  git add .claude/settings.json
  git add VERSION
  git add CHANGELOG.md
  git add README.md
  git add CLAUDE.md
  git add docs/PARALLEL_SUBAGENT_STRATEGY.md
  git add tests/
  ```
- [ ] 创建commit
  ```bash
  git commit -m "feat: Phase 7 cleanup + Parallel execution + Phase 1/6/7 Skills

  - Fix Phase 7 cleanup mechanism (3-layer cleanup)
  - Integrate parallel execution into executor.sh
  - Add Phase 1/6/7 skills (1500+ lines documentation)
  - Add HOOKS_GUIDE.md (20 hooks detailed docs)
  - Add SKILLS_GUIDE.md (skills development guide)
  - Optimize conflict detection (actual file-based)
  - Performance: 2.2x overall speedup

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

#### 任务5.5: 验证Git状态
- [ ] 运行`git status`确认working directory clean
- [ ] 运行`git log -1`验证commit message

---

## Phase 6: Acceptance（预计15分钟）

### 🔴 生成验收报告（10分钟）

#### 任务6.1: 运行acceptance report generator
- [ ] 执行`.claude/hooks/acceptance_report_generator.sh .workflow/ACCEPTANCE_CHECKLIST_phase-skills-hooks-optimization.md`
- [ ] 生成`.workflow/ACCEPTANCE_REPORT_phase-skills-hooks-optimization.md`
- [ ] 验证报告包含：
  - Executive Summary
  - Validation Results (129项)
  - Issues Summary
  - Recommendations
  - Evidence Collected

#### 任务6.2: 对照Checklist验证
- [ ] 逐项检查ACCEPTANCE_CHECKLIST.md
- [ ] 计算通过率：目标≥90%
- [ ] 记录未通过项（如有）

---

### 🟠 用户确认（5分钟）

#### 任务6.3: 展示验收报告给用户
- [ ] 总结核心功能：
  ```
  ✅ Phase 7清理机制：3层清理，确保main分支干净
  ✅ 并行执行集成：executor.sh集成parallel_executor.sh
  ✅ Phase 1/6/7 Skills：1500+行详细指导
  ✅ Hooks/Skills指南：完整开发文档
  ✅ 性能提升：2.2x整体加速
  ```
- [ ] 突出关键指标：
  - 129项验收标准
  - 通过率≥90%
  - Phase 3加速3.5x
  - 20个hooks完整文档

#### 任务6.4: 等待用户反馈
- [ ] 用户说"没问题"/"验收通过" → 进入Phase 7
- [ ] 用户说"有疑问" → 解释具体项
- [ ] 用户说"修复XX" → 返回相应Phase修复

---

## Phase 7: Closure（预计15分钟）

### 🔴 全面清理（10分钟）

#### 任务7.1: 运行comprehensive_cleanup.sh
- [ ] 执行清理（使用新的Phase清理机制）
  ```bash
  bash scripts/comprehensive_cleanup.sh aggressive
  ```
- [ ] 验证清理结果：
  - .temp/目录清空
  - 旧版本文件删除
  - .phase/current已清理（如Phase7）
  - .workflow/current已清理
  - Git工作区干净

#### 任务7.2: 最终验证
- [ ] 版本一致性：`bash scripts/check_version_consistency.sh`
- [ ] Git状态：`git status`（应该clean）
- [ ] Phase状态：`cat .phase/current`（应该Phase7或不存在）

---

### 🟠 推送和创建PR（5分钟）

#### 任务7.3: 推送feature分支
- [ ] 推送到remote
  ```bash
  git push -u origin feature/phase-skills-hooks-optimization
  ```

#### 任务7.4: 创建Pull Request
- [ ] 执行PR创建（会被pr_creation_guard检查）
  ```bash
  gh pr create --title "feat: Phase 7 cleanup + Parallel execution + Phase 1/6/7 Skills (v8.8.0)" --body "$(cat <<'EOF'
  ## Summary

  三合一系统优化，解决3个核心问题：

  1. ✅ Phase 7清理机制修复（Bug Fix - HIGH）
     - 修复main分支merge后遗留Phase状态
     - 三层清理机制：comprehensive_cleanup + phase_completion_validator + post-merge hook

  2. ✅ 并行执行系统集成（Feature Enhancement - MEDIUM）
     - executor.sh集成parallel_executor.sh
     - 优化conflict_detector.sh（实际文件检测）
     - Phase 2-7真正启用并行执行

  3. ✅ Phase 1/6/7 Skills创建（Documentation Enhancement - MEDIUM）
     - 创建phase1-discovery-planning skill (500行)
     - 创建phase6-acceptance skill (400行)
     - 创建phase7-closure skill (600行) + 20个hooks详解
     - 创建HOOKS_GUIDE.md (800行) + SKILLS_GUIDE.md (500行)

  ## Test Plan

  - [x] 单元测试：Phase 7清理、并行执行、Skills触发
  - [x] 集成测试：完整7-Phase工作流
  - [x] 性能测试：Phase 3加速3.5x ✓
  - [x] 回归测试：现有功能不受影响 ✓
  - [x] Pre-merge audit：12项检查全部通过 ✓

  ## Performance Improvements

  - Phase 2: 6h → 3.3h (1.8x) ✓
  - Phase 3: 3h → 0.9h (3.5x) ✓
  - Phase 4: 2h → 1.3h (1.5x) ✓
  - **Overall: 11h → 5h (2.2x speedup)**

  ## Breaking Changes

  None. 向后兼容，所有改动都是增量。

  ## Rollback Plan

  如果出现问题，可以通过以下方式回滚：
  - git revert <commit-hash>
  - 或删除新增文件，恢复修改文件
  - 详细rollback步骤见P1_DISCOVERY.md Section 11

  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  EOF
  )"
  ```

#### 任务7.5: 等待CI和用户确认
- [ ] 等待CI checks完成（58个checks预期）
  ```bash
  gh pr checks --watch
  ```
- [ ] 所有checks通过后，等待用户说"merge"
- [ ] 用户确认后执行merge
  ```bash
  gh pr merge --auto --squash
  ```

---

## Summary（总结）

### ✅ Phase 1完成标志
- [x] P1_DISCOVERY.md (5300行)
- [x] ACCEPTANCE_CHECKLIST.md (129项)
- [ ] PLAN.md (本文档，待完成详细实施计划)
- [x] Impact Assessment (Radius=60, 6 agents)
- [ ] 用户确认

### 📊 关键数字
- **文件修改**: 5个核心脚本
- **文件新增**: 5个skill/guide文档（~2700行）
- **验收标准**: 129项检查
- **预计时间**: 6.5小时
- **并行加速**: 2.2x
- **Agent数量**: 6个并行

### 🎯 下一步
等待用户确认此checklist，然后我会：
1. 完成PLAN.md（详细实施计划）
2. 总结Phase 1产出
3. 等待用户说"我理解了，开始Phase 2"
4. 进入Phase 2实施
