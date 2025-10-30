# Phase 1.3: Technical Discovery - Workflow Supervision Enforcement Fixes

**Version**: 8.5.1
**Date**: 2025-10-29
**Task**: 修复3个P0 Critical Workflow Supervision Bugs
**Branch**: `bugfix/workflow-supervision-enforcement`

---

## 🎯 Executive Summary

**问题严重性**: 🔴 P0 Critical - Workflow supervision机制完全失效

**影响范围**: 所有7个Phases的质量门禁和enforcement机制

**根本原因**:
1. File naming mismatch (`P2_DISCOVERY.md` vs `P1_DISCOVERY.md`)
2. Phase numbering inconsistency (`P0-P5` vs `Phase1-Phase7`)
3. Missing dependencies (`task_namespace.sh` not exist)

**修复策略**: 3个targeted fixes + 1个enhancement (per-phase impact assessment)

---

## 📊 Bug Analysis

### Bug #1: Impact Assessment Enforcer - File Name Mismatch

**严重性**: 🔴 P0 Critical
**文件**: `.claude/hooks/impact_assessment_enforcer.sh`
**问题行**: Line 24-26

**错误代码**:
```bash
is_phase2_completed() {
    [[ -f "$PROJECT_ROOT/docs/P2_DISCOVERY.md" ]] && \
    grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P2_DISCOVERY.md" 2>/dev/null
}
```

**问题分析**:
- Hook检查的文件名: `P2_DISCOVERY.md`
- 实际工作流创建的文件名: `P1_DISCOVERY.md` (Phase 1.3)
- 结果: 文件永远找不到 → Hook never triggers → Impact Assessment enforcement 完全失效

**影响**:
- PR #57中我跳过了Phase 1.4 Impact Assessment
- 没有被强制推荐Agent数量
- 导致高风险任务(Radius=67)没有使用推荐的6个agents

**修复方案**:
```bash
# 新代码 (Line 24-26):
is_phase1_3_completed() {
    [[ -f "$PROJECT_ROOT/docs/P1_DISCOVERY.md" ]] && \
    grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P1_DISCOVERY.md" 2>/dev/null
}

# 同时修改 Line 40:
# 旧: if [[ "$current_phase" == "P2" ]] && is_phase2_completed; then
# 新: if [[ "$current_phase" == "Phase1" ]] && is_phase1_3_completed; then
```

**验证方法**:
```bash
# 测试case 1: Phase 1.3完成时应该触发
mkdir -p docs
cat > docs/P1_DISCOVERY.md <<'EOF'
# Discovery

## Acceptance Checklist
- [ ] Test
EOF

# 模拟Phase转换
WORKFLOW_DIR=.workflow bash .claude/hooks/impact_assessment_enforcer.sh
# 预期: 应该触发Impact Assessment
```

---

### Bug #2: Phase Completion Validator - Phase Numbering Inconsistency

**严重性**: 🔴 P0 Critical
**文件**: `.claude/hooks/phase_completion_validator.sh`
**问题行**: Line 28-62 (entire case statement)

**错误代码**:
```bash
case "$phase" in
    "P0")  # ❌ 系统实际使用 Phase1，不是 P0
        [[ -f "$PROJECT_ROOT/docs/P0_DISCOVERY.md" ]] && \
        grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P0_DISCOVERY.md" 2>/dev/null
        ;;
    "P1")  # ❌ 应该是 Phase2
    "P2")  # ❌ 应该是 Phase2
    "P3")  # ❌ 应该是 Phase3
    # ...
esac
```

**问题分析**:
- Hook使用的Phase命名: `P0`, `P1`, `P2`, `P3`, `P4`, `P5` (6个Phases)
- 实际工作流Phase命名: `Phase1`, `Phase2`, `Phase3`, `Phase4`, `Phase5`, `Phase6`, `Phase7` (7个Phases)
- 结果: Phase名称永远不匹配 → Hook never triggers → 95步验证系统从未被调用

**影响**:
- PR #57中我完成了Phase 1-2就停止
- Anti-hollow gate没有阻止过早完成
- 导致workflow可以被不完整地执行

**修复方案**:
```bash
# 新代码 (Line 28-78):
case "$phase" in
    "Phase1")
        # Phase 1完成标志：P1_DISCOVERY.md存在且完整
        [[ -f "$PROJECT_ROOT/docs/P1_DISCOVERY.md" ]] && \
        grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P1_DISCOVERY.md" 2>/dev/null
        ;;
    "Phase2")
        # Phase 2完成标志：实现代码已提交
        git log -1 --pretty=%B 2>/dev/null | grep -qE "(feat|fix|refactor):"
        ;;
    "Phase3")
        # Phase 3完成标志：静态检查通过
        [[ -f "$PROJECT_ROOT/scripts/static_checks.sh" ]] && \
        bash "$PROJECT_ROOT/scripts/static_checks.sh" >/dev/null 2>&1
        ;;
    "Phase4")
        # Phase 4完成标志：REVIEW.md存在且足够大
        [[ -f "$PROJECT_ROOT/.workflow/REVIEW.md" ]] && \
        [[ $(wc -c < "$PROJECT_ROOT/.workflow/REVIEW.md") -gt 3072 ]]
        ;;
    "Phase5")
        # Phase 5完成标志：CHANGELOG更新
        [[ -f "$PROJECT_ROOT/CHANGELOG.md" ]] && \
        grep -qE "## \[[0-9]+\.[0-9]+\.[0-9]+\]" "$PROJECT_ROOT/CHANGELOG.md" 2>/dev/null
        ;;
    "Phase6")
        # Phase 6完成标志：Acceptance Report存在
        [[ -f "$PROJECT_ROOT/.workflow/ACCEPTANCE_REPORT.md" ]] || \
        find "$PROJECT_ROOT/.workflow/" -name "ACCEPTANCE_REPORT_*.md" | grep -q .
        ;;
    "Phase7")
        # Phase 7完成标志：版本一致性检查通过
        [[ -f "$PROJECT_ROOT/scripts/check_version_consistency.sh" ]] && \
        bash "$PROJECT_ROOT/scripts/check_version_consistency.sh" >/dev/null 2>&1
        ;;
    *)
        return 1
        ;;
esac
```

**验证方法**:
```bash
# 测试case 1: Phase1完成应该触发验证
mkdir -p .workflow docs
echo "phase: Phase1" > .workflow/current
cat > docs/P1_DISCOVERY.md <<'EOF'
# Discovery

## Acceptance Checklist
- [ ] Test
EOF

TOOL_NAME=Write bash .claude/hooks/phase_completion_validator.sh
# 预期: 应该调用workflow_validator_v95.sh (如果存在)
```

---

### Bug #3: Agent Evidence Collector - Missing Dependencies

**严重性**: 🟡 P1 High
**文件**: `.claude/hooks/agent_evidence_collector.sh`
**问题行**: Line 16-22

**错误代码**:
```bash
if [ -f "${CLAUDE_CORE}/task_namespace.sh" ]; then
  source "${CLAUDE_CORE}/task_namespace.sh"
else
  echo "⚠️  Task namespace library not found, skipping evidence collection" >&2
  exit 0  # ❌ 静默失败，不报错
fi
```

**实际情况**:
```bash
$ test -f ".claude/core/task_namespace.sh"
MISSING

$ ls .claude/core/
loader.py
phase_definitions.yml
quality_thresholds.yml
task_templates.yaml
workflow_rules.yml
# ❌ task_namespace.sh 不存在
```

**问题分析**:
- Hook依赖 `.claude/core/task_namespace.sh` 提供的5个函数
- 但这个文件根本不存在
- Hook静默退出(exit 0) → Evidence collection完全不工作

**影响**:
- 所有Agent调用没有被记录
- 无法验证是否使用了推荐数量的Agents
- 导致multi-agent enforcement机制失效

**修复方案** (选择简化版):
```bash
# 方案A: 简化版 - 移除task_namespace.sh依赖，直接实现
# 优点: 快速修复，不依赖外部文件
# 缺点: 功能较简单

#!/usr/bin/env bash
# Agent Evidence Collector Hook (Simplified)
# Purpose: Record agent invocations for quality gate enforcement

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EVIDENCE_DIR="${ROOT}/.workflow/agent_evidence"
mkdir -p "$EVIDENCE_DIR"

# 简化版：直接从环境变量获取信息
TOOL_NAME="${1:-unknown}"
AGENT_TYPE="${2:-}"

# 只跟踪Task tool (agent launches)
if [ "$TOOL_NAME" != "Task" ]; then
  exit 0
fi

# Extract agent type from stdin if not provided
if [ -z "$AGENT_TYPE" ] && [ ! -t 0 ]; then
  JSON_INPUT=$(cat)
  AGENT_TYPE=$(echo "$JSON_INPUT" | jq -r '.subagent_type // empty' 2>/dev/null || echo "")
fi

if [ -z "$AGENT_TYPE" ]; then
  exit 0
fi

# Record agent invocation
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EVIDENCE_FILE="${EVIDENCE_DIR}/agents_$(date +%Y%m%d).jsonl"

# Append evidence
jq -n \
  --arg type "agent_invocation" \
  --arg agent "$AGENT_TYPE" \
  --arg ts "$TIMESTAMP" \
  '{
    "type": $type,
    "agent": $agent,
    "timestamp": $ts,
    "hook": "PreToolUse"
  }' >> "$EVIDENCE_FILE"

# Count today's agents
AGENT_COUNT=$(grep -c "agent_invocation" "$EVIDENCE_FILE" 2>/dev/null || echo "0")

echo "✅ Agent evidence recorded: $AGENT_TYPE (total today: $AGENT_COUNT)" >&2

exit 0
```

**验证方法**:
```bash
# 测试case 1: 记录agent调用
mkdir -p .workflow/agent_evidence

echo '{"subagent_type": "test-agent"}' | \
  bash .claude/hooks/agent_evidence_collector.sh Task

# 检查evidence文件
cat .workflow/agent_evidence/agents_$(date +%Y%m%d).jsonl
# 预期: 应该有一条记录，agent=test-agent
```

---

## 🚀 Enhancement: Per-Phase Impact Assessment

**优先级**: 🟢 P2 Enhancement
**目标**: 实现每个Phase动态评估Agent需求

**当前情况**:
- ✅ 全局Impact Assessment已实现 (Phase 1.4)
- ✅ Per-phase evaluation脚本已存在 (`impact_radius_assessor.sh` v1.4.0)
- ❌ 但未集成到workflow中

**实现方案**:
创建新的PrePrompt hook来在每个Phase开始前评估:

```bash
#!/bin/bash
# Per-Phase Impact Assessment Hook
# Triggers: PrePrompt (before each Phase starts)
# Purpose: Dynamically assess agent requirements per phase

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
ASSESSOR_SCRIPT="$PROJECT_ROOT/.claude/scripts/impact_radius_assessor.sh"

# 获取当前Phase
get_current_phase() {
    if [[ -f "$WORKFLOW_DIR/current" ]]; then
        grep "^phase:" "$WORKFLOW_DIR/current" | awk '{print $2}' || echo "Phase1"
    else
        echo "Phase1"
    fi
}

# 需要评估的Phases
CURRENT_PHASE=$(get_current_phase)

case "$CURRENT_PHASE" in
    "Phase2"|"Phase3"|"Phase4")
        echo "📊 Running per-phase Impact Assessment for $CURRENT_PHASE..."

        if [[ -f "$ASSESSOR_SCRIPT" ]]; then
            OUTPUT_FILE="$WORKFLOW_DIR/impact_assessments/${CURRENT_PHASE}_assessment.json"

            # 调用assessor脚本
            bash "$ASSESSOR_SCRIPT" \
                --phase "$CURRENT_PHASE" \
                --output "$OUTPUT_FILE"

            # 读取推荐Agent数量
            if [[ -f "$OUTPUT_FILE" ]]; then
                RECOMMENDED_AGENTS=$(jq -r '.recommended_agents // 0' "$OUTPUT_FILE")
                echo "💡 Recommended agents for $CURRENT_PHASE: $RECOMMENDED_AGENTS"
            fi
        fi
        ;;
    *)
        # 其他Phases不需要评估
        ;;
esac

exit 0
```

**集成点**:
- 注册到 `.claude/settings.json` 的 `PrePrompt` hooks数组
- 在Phase2/3/4开始前自动触发
- 生成Phase-specific的agent recommendations

---

## 📋 Acceptance Checklist

### Bug Fix Verification

#### Bug #1: Impact Assessment Enforcer
- [ ] 1.1 修改 `is_phase2_completed()` → `is_phase1_3_completed()`
- [ ] 1.2 修改文件检查 `P2_DISCOVERY.md` → `P1_DISCOVERY.md`
- [ ] 1.3 修改Phase检查 `"P2"` → `"Phase1"`
- [ ] 1.4 测试：Phase 1.3完成时hook应该触发
- [ ] 1.5 测试：找不到smart_agent_selector.sh时应该报错
- [ ] 1.6 测试：Impact Assessment成功执行后应该放行

#### Bug #2: Phase Completion Validator
- [ ] 2.1 修改所有Phase case从 `P0-P5` → `Phase1-Phase7`
- [ ] 2.2 修改Phase1检查文件 `P0_DISCOVERY.md` → `P1_DISCOVERY.md`
- [ ] 2.3 增加Phase6和Phase7的completion检查逻辑
- [ ] 2.4 测试：每个Phase完成时应该触发验证
- [ ] 2.5 测试：调用workflow_validator_v95.sh（如果存在）
- [ ] 2.6 测试：验证失败应该硬阻止 (exit 1)
- [ ] 2.7 测试：验证通过应该创建marker文件

#### Bug #3: Agent Evidence Collector
- [ ] 3.1 简化hook，移除task_namespace.sh依赖
- [ ] 3.2 实现直接evidence记录功能
- [ ] 3.3 Evidence存储在 `.workflow/agent_evidence/agents_YYYYMMDD.jsonl`
- [ ] 3.4 测试：记录agent调用到JSONL文件
- [ ] 3.5 测试：统计每日agent调用次数
- [ ] 3.6 测试：非Task tool应该跳过 (exit 0)

### Enhancement Implementation

#### Per-Phase Impact Assessment
- [ ] 4.1 创建 `.claude/hooks/per_phase_impact_assessor.sh`
- [ ] 4.2 注册到 `.claude/settings.json` PrePrompt hooks
- [ ] 4.3 实现Phase2/3/4的评估逻辑
- [ ] 4.4 调用 `impact_radius_assessor.sh --phase PhaseN`
- [ ] 4.5 输出到 `.workflow/impact_assessments/PhaseN_assessment.json`
- [ ] 4.6 测试：Phase2开始前应该生成评估
- [ ] 4.7 测试：评估结果包含recommended_agents字段

### Integration Testing

#### End-to-End Workflow Test
- [ ] 5.1 创建测试分支模拟完整workflow
- [ ] 5.2 Phase 1.3完成 → 应该触发Impact Assessment enforcer
- [ ] 5.3 Phase 1完成 → 应该触发Phase completion validator
- [ ] 5.4 使用Task tool → 应该记录agent evidence
- [ ] 5.5 Phase2开始 → 应该触发per-phase assessment
- [ ] 5.6 所有Phases的completion都应该被正确检测

#### Regression Testing
- [ ] 6.1 确认修复后PR #57场景不会再发生
- [ ] 6.2 确认workflow不能在Phase1-2就停止
- [ ] 6.3 确认高风险任务会被推荐足够的agents
- [ ] 6.4 确认evidence collection正常工作

### Documentation

- [ ] 7.1 更新 `.claude/hooks/` 中所有修改的hook文件
- [ ] 7.2 添加注释说明Phase命名约定
- [ ] 7.3 更新CLAUDE.md中的anti-hollow gate文档
- [ ] 7.4 创建troubleshooting guide for hook debugging

### Quality Gates

- [ ] 8.1 所有shellcheck warnings修复
- [ ] 8.2 所有hook性能<2秒
- [ ] 8.3 Hook error handling完整（不静默失败）
- [ ] 8.4 Version consistency (8.5.1) across 6 files
- [ ] 8.5 CI所有checks通过

---

## 🔧 Technical Specifications

### Modified Files

1. `.claude/hooks/impact_assessment_enforcer.sh`
   - Lines changed: 24-26 (function rename), 40 (phase check)
   - Complexity: Low (2 changes)

2. `.claude/hooks/phase_completion_validator.sh`
   - Lines changed: 28-78 (case statement rewrite)
   - Complexity: Medium (7 phases × 3 lines each)

3. `.claude/hooks/agent_evidence_collector.sh`
   - Lines changed: 1-128 (complete rewrite)
   - Complexity: Medium (simplification)

### New Files

4. `.claude/hooks/per_phase_impact_assessor.sh`
   - Lines: ~80
   - Complexity: Medium (phase detection + assessor call)

5. `.claude/settings.json`
   - Changes: Add per_phase_impact_assessor to PrePrompt hooks array
   - Complexity: Low (JSON array modification)

### Test Files

6. `tests/hooks/test_impact_assessment_enforcer.sh`
   - Test cases: 6

7. `tests/hooks/test_phase_completion_validator.sh`
   - Test cases: 7

8. `tests/hooks/test_agent_evidence_collector.sh`
   - Test cases: 6

9. `tests/hooks/test_per_phase_assessor.sh`
   - Test cases: 7

---

## 📊 Impact Assessment (Self-Assessment)

**Risk**: 6/10
- 修改3个核心workflow hooks
- 影响所有Phases的enforcement机制
- 但changes are targeted and well-understood

**Complexity**: 7/10
- 需要理解Phase命名约定
- 需要测试7个Phases的completion logic
- 需要集成per-phase assessment

**Scope**: 8/10
- 影响所有7个Phases
- 影响所有使用agent的场景
- 影响workflow enforcement机制

**Impact Radius**: (6 × 5) + (7 × 3) + (8 × 2) = 30 + 21 + 16 = **67/100**

**Recommended Agents**: 🔴 **6 agents** (High-risk: 50-69分)

**Rationale**:
- Score 67落在High-risk区间(50-69)
- 修改核心enforcement hooks需要仔细review
- 需要多个agents验证不同Phases的逻辑
- 需要agents测试regression scenarios

---

## 🎯 Success Criteria

### Must Have (P0)
1. ✅ Bug #1修复：Impact Assessment Enforcer正确检测P1_DISCOVERY.md
2. ✅ Bug #2修复：Phase Completion Validator使用Phase1-Phase7命名
3. ✅ Bug #3修复：Agent Evidence Collector不依赖task_namespace.sh

### Should Have (P1)
4. ✅ Per-phase Impact Assessment集成到workflow
5. ✅ 所有hooks有完整测试覆盖
6. ✅ Error handling不静默失败

### Nice to Have (P2)
7. ⚪ Evidence visualization dashboard
8. ⚪ Hook performance monitoring
9. ⚪ Automated rollback on hook failure

---

## 📅 Implementation Timeline

**Estimated Total Time**: 2-3 hours (AI time)

- Phase 1 (Discovery & Planning): 30min ✅ (current)
- Phase 2 (Implementation): 60min
  - Fix 3 bugs: 20min each
  - Per-phase assessment: 30min
  - Settings.json update: 10min
- Phase 3 (Testing): 45min
  - Unit tests: 20min
  - Integration tests: 15min
  - Regression tests: 10min
- Phase 4 (Review): 20min
- Phase 5-7 (Release, Acceptance, Closure): 25min

---

## 🔍 Risks and Mitigation

### Risk 1: Hook Changes Break Existing Workflow
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Comprehensive testing before merge
- Gradual rollout with monitoring
- Keep old hooks as backup (.bak files)

### Risk 2: Per-Phase Assessment Performance Impact
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Assessor script already optimized (<50ms)
- Only runs 3 times (Phase2/3/4)
- Can disable via config if needed

### Risk 3: Evidence Collection Fills Disk
**Probability**: Low
**Impact**: Low
**Mitigation**:
- JSONL format is compact
- Daily rotation (one file per day)
- Auto-cleanup after 30 days

---

## 📚 References

- PR #57: Performance optimization (exposed these bugs)
- `.claude/scripts/impact_radius_assessor.sh` v1.4.0
- `.claude/ARCHITECTURE/` - Workflow system design
- `CLAUDE.md` - Anti-hollow gate documentation

---

**Document Status**: ✅ Complete
**Next Phase**: Phase 1.5 - Architecture Planning
**Estimated Start**: 2025-10-29 23:30 UTC
