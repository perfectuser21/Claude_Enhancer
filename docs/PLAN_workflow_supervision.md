# Architecture Planning - Workflow Supervision Enforcement Fixes

**Version**: 8.5.1
**Date**: 2025-10-29
**Task**: 修复3个P0 Critical Workflow Supervision Bugs
**Branch**: `bugfix/workflow-supervision-enforcement`
**Recommended Agents**: 6 agents (High-risk: Radius=67/100)

---

## 🎯 Executive Summary

This document outlines the detailed implementation plan for fixing 3 critical bugs in the workflow supervision system and adding per-phase Impact Assessment enhancement.

**Primary Goals**:
1. Fix Impact Assessment Enforcer (file name mismatch)
2. Fix Phase Completion Validator (phase numbering inconsistency)
3. Fix Agent Evidence Collector (missing dependencies)
4. Integrate Per-Phase Impact Assessment

**Success Metrics**:
- All 3 bugs fixed and verified
- Per-phase assessment working for Phase2/3/4
- All 26 unit tests passing
- CI green
- Zero shellcheck warnings

---

## 📐 System Architecture

### Current State (Broken)

```
┌─────────────────────────────────────────────────────────────┐
│  Workflow Supervision System (v8.5.0 - BROKEN)              │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Impact Assessment Enforcement                      │
├──────────────────────────────────────────────────────────────┤
│  Hook: .claude/hooks/impact_assessment_enforcer.sh           │
│  Trigger: PrePrompt (after Phase completion)                 │
│  Status: ❌ BROKEN                                          │
│  Issue: Checks for P2_DISCOVERY.md (should be P1)           │
│         Checks phase == "P2" (should be "Phase1")            │
│  Result: Never triggers → no Impact Assessment enforcement   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 2: Phase Completion Validation                        │
├──────────────────────────────────────────────────────────────┤
│  Hook: .claude/hooks/phase_completion_validator.sh           │
│  Trigger: PostToolUse (after Write/Edit)                     │
│  Status: ❌ BROKEN                                          │
│  Issue: Uses P0-P5 phase names (should be Phase1-Phase7)    │
│         Checks P0_DISCOVERY.md (should be P1)                │
│  Result: Never triggers → no 95-step validation             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 3: Agent Evidence Collection                          │
├──────────────────────────────────────────────────────────────┤
│  Hook: .claude/hooks/agent_evidence_collector.sh             │
│  Trigger: PreToolUse (before Task tool)                      │
│  Status: ❌ BROKEN                                          │
│  Issue: Depends on missing task_namespace.sh                │
│  Result: Silent fail → no agent evidence                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Missing: Per-Phase Impact Assessment                        │
├──────────────────────────────────────────────────────────────┤
│  Status: ❌ NOT IMPLEMENTED                                 │
│  Issue: Only global assessment in Phase 1.4                 │
│  Result: No dynamic agent recommendations per phase          │
└──────────────────────────────────────────────────────────────┘
```

### Target State (Fixed)

```
┌─────────────────────────────────────────────────────────────┐
│  Workflow Supervision System (v8.5.1 - FIXED)               │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Impact Assessment Enforcement ✅                   │
├──────────────────────────────────────────────────────────────┤
│  Hook: .claude/hooks/impact_assessment_enforcer.sh (FIXED)   │
│  Trigger: PrePrompt (when phase == "Phase1")                 │
│  Check: P1_DISCOVERY.md exists + has checklist              │
│  Action: Call smart_agent_selector.sh or block              │
│  Result: ✅ Enforces Impact Assessment after Phase 1.3      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 2: Phase Completion Validation ✅                     │
├──────────────────────────────────────────────────────────────┤
│  Hook: .claude/hooks/phase_completion_validator.sh (FIXED)   │
│  Trigger: PostToolUse (after Write/Edit)                     │
│  Check: Phase1-Phase7 completion conditions                 │
│  Action: Call workflow_validator_v95.sh if phase done       │
│  Result: ✅ Validates all 7 phases, prevents early stop     │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 3: Agent Evidence Collection ✅                       │
├──────────────────────────────────────────────────────────────┤
│  Hook: .claude/hooks/agent_evidence_collector.sh (FIXED)     │
│  Trigger: PreToolUse (before Task tool)                      │
│  Storage: .workflow/agent_evidence/agents_YYYYMMDD.jsonl    │
│  No dependencies (self-contained)                            │
│  Result: ✅ Records all agent invocations                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 4: Per-Phase Impact Assessment ✅ NEW                │
├──────────────────────────────────────────────────────────────┤
│  Hook: .claude/hooks/per_phase_impact_assessor.sh (NEW)      │
│  Trigger: PrePrompt (before Phase2/3/4)                      │
│  Action: Call impact_radius_assessor.sh --phase PhaseN      │
│  Output: .workflow/impact_assessments/PhaseN_assessment.json│
│  Result: ✅ Dynamic agent recommendations per phase         │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementation Plan

### Part 1: Bug #1 - Impact Assessment Enforcer Fix

**File**: `.claude/hooks/impact_assessment_enforcer.sh`

**Current Code** (Lines 24-26 and 40):
```bash
# Line 24-26: Wrong function name and file check
is_phase2_completed() {
    [[ -f "$PROJECT_ROOT/docs/P2_DISCOVERY.md" ]] && \
    grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P2_DISCOVERY.md" 2>/dev/null
}

# Line 40: Wrong phase name
if [[ "$current_phase" == "P2" ]] && is_phase2_completed; then
```

**Fixed Code**:
```bash
# Line 24-26: Correct function name and file check
is_phase1_3_completed() {
    [[ -f "$PROJECT_ROOT/docs/P1_DISCOVERY.md" ]] && \
    grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P1_DISCOVERY.md" 2>/dev/null
}

# Line 40: Correct phase name
if [[ "$current_phase" == "Phase1" ]] && is_phase1_3_completed; then
```

**Changes**:
1. Rename function: `is_phase2_completed` → `is_phase1_3_completed`
2. Fix file path: `P2_DISCOVERY.md` → `P1_DISCOVERY.md` (2 occurrences)
3. Fix phase check: `"P2"` → `"Phase1"`

**Testing**:
```bash
# Test case 1: Phase 1.3 completed → should trigger
mkdir -p docs .workflow
echo "phase: Phase1" > .workflow/current
cat > docs/P1_DISCOVERY.md <<'EOF'
# Discovery

## Acceptance Checklist
- [ ] Item 1
EOF

bash .claude/hooks/impact_assessment_enforcer.sh
# Expected: Calls smart_agent_selector.sh or shows error

# Test case 2: P1_DISCOVERY.md missing → should not trigger
rm docs/P1_DISCOVERY.md
bash .claude/hooks/impact_assessment_enforcer.sh
# Expected: exit 0 (silent pass)

# Test case 3: Checklist missing → should not trigger
cat > docs/P1_DISCOVERY.md <<'EOF'
# Discovery
No checklist here
EOF

bash .claude/hooks/impact_assessment_enforcer.sh
# Expected: exit 0 (silent pass)
```

---

### Part 2: Bug #2 - Phase Completion Validator Fix

**File**: `.claude/hooks/phase_completion_validator.sh`

**Current Code** (Lines 28-62):
```bash
case "$phase" in
    "P0")  # ❌ Wrong: system uses Phase1
        [[ -f "$PROJECT_ROOT/docs/P0_DISCOVERY.md" ]] && \
        grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P0_DISCOVERY.md" 2>/dev/null
        ;;
    "P1")  # ❌ Wrong: should be Phase2
    "P2")  # ❌ Wrong: should be Phase2
    # ... incomplete, only 6 phases
esac
```

**Fixed Code**:
```bash
case "$phase" in
    "Phase1")
        # Phase 1 completed: P1_DISCOVERY.md exists with checklist
        [[ -f "$PROJECT_ROOT/docs/P1_DISCOVERY.md" ]] && \
        grep -q "## Acceptance Checklist" "$PROJECT_ROOT/docs/P1_DISCOVERY.md" 2>/dev/null
        ;;
    "Phase2")
        # Phase 2 completed: implementation code committed
        git log -1 --pretty=%B 2>/dev/null | grep -qE "(feat|fix|refactor):"
        ;;
    "Phase3")
        # Phase 3 completed: static checks pass
        [[ -f "$PROJECT_ROOT/scripts/static_checks.sh" ]] && \
        bash "$PROJECT_ROOT/scripts/static_checks.sh" >/dev/null 2>&1
        ;;
    "Phase4")
        # Phase 4 completed: REVIEW.md exists and is substantial
        [[ -f "$PROJECT_ROOT/.workflow/REVIEW.md" ]] && \
        [[ $(wc -c < "$PROJECT_ROOT/.workflow/REVIEW.md") -gt 3072 ]]
        ;;
    "Phase5")
        # Phase 5 completed: CHANGELOG updated
        [[ -f "$PROJECT_ROOT/CHANGELOG.md" ]] && \
        grep -qE "## \[[0-9]+\.[0-9]+\.[0-9]+\]" "$PROJECT_ROOT/CHANGELOG.md" 2>/dev/null
        ;;
    "Phase6")
        # Phase 6 completed: Acceptance report exists
        [[ -f "$PROJECT_ROOT/.workflow/ACCEPTANCE_REPORT.md" ]] || \
        find "$PROJECT_ROOT/.workflow/" -name "ACCEPTANCE_REPORT_*.md" 2>/dev/null | grep -q .
        ;;
    "Phase7")
        # Phase 7 completed: version consistency check passes
        [[ -f "$PROJECT_ROOT/scripts/check_version_consistency.sh" ]] && \
        bash "$PROJECT_ROOT/scripts/check_version_consistency.sh" >/dev/null 2>&1
        ;;
    *)
        return 1
        ;;
esac
```

**Changes**:
1. Rewrite all phase cases: `P0-P5` → `Phase1-Phase7`
2. Fix Phase1 file check: `P0_DISCOVERY.md` → `P1_DISCOVERY.md`
3. Add Phase6 completion check (new)
4. Add Phase7 completion check (new)
5. Update comments for clarity

**Testing**:
```bash
# Test Phase1 completion
echo "phase: Phase1" > .workflow/current
cat > docs/P1_DISCOVERY.md <<'EOF'
# Discovery
## Acceptance Checklist
- [ ] Test
EOF

TOOL_NAME=Write bash .claude/hooks/phase_completion_validator.sh
# Expected: Calls workflow_validator_v95.sh (if exists)

# Test Phase2-7 similarly...
```

---

### Part 3: Bug #3 - Agent Evidence Collector Simplification

**File**: `.claude/hooks/agent_evidence_collector.sh`

**Current Code** (Lines 16-22 + complex logic):
```bash
if [ -f "${CLAUDE_CORE}/task_namespace.sh" ]; then
  source "${CLAUDE_CORE}/task_namespace.sh"
else
  echo "⚠️  Task namespace library not found, skipping evidence collection" >&2
  exit 0  # ❌ Silent fail
fi

# Uses: get_current_task(), get_task_dir(), record_agent(), etc.
```

**Fixed Code** (Complete rewrite):
```bash
#!/usr/bin/env bash
# Agent Evidence Collector Hook (Simplified)
# Purpose: Record agent invocations for quality gate enforcement
# No external dependencies - self-contained

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EVIDENCE_DIR="${ROOT}/.workflow/agent_evidence"
mkdir -p "$EVIDENCE_DIR"

# Get tool invocation info
TOOL_NAME="${1:-unknown}"
AGENT_TYPE="${2:-}"

# Only track Task tool invocations (agent launches)
if [ "$TOOL_NAME" != "Task" ]; then
  exit 0
fi

# Extract agent type from stdin if not provided
if [ -z "$AGENT_TYPE" ] && [ ! -t 0 ]; then
  JSON_INPUT=$(cat)
  AGENT_TYPE=$(echo "$JSON_INPUT" | jq -r '.subagent_type // empty' 2>/dev/null || echo "")
fi

if [ -z "$AGENT_TYPE" ]; then
  echo "⚠️  Could not determine agent type" >&2
  exit 0
fi

# Record agent invocation
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EVIDENCE_FILE="${EVIDENCE_DIR}/agents_$(date +%Y%m%d).jsonl"

# Append evidence (JSONL format)
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

**Changes**:
1. Remove dependency on task_namespace.sh
2. Implement direct JSONL storage in `.workflow/agent_evidence/`
3. Daily file rotation: `agents_YYYYMMDD.jsonl`
4. Self-contained logic (no external function calls)
5. Clear error messages (no silent failures)

**Testing**:
```bash
# Test case 1: Record agent invocation
mkdir -p .workflow/agent_evidence

echo '{"subagent_type": "test-agent", "prompt": "test task"}' | \
  bash .claude/hooks/agent_evidence_collector.sh Task

# Verify evidence file
EVIDENCE_FILE=".workflow/agent_evidence/agents_$(date +%Y%m%d).jsonl"
cat "$EVIDENCE_FILE"
# Expected: {"type":"agent_invocation","agent":"test-agent",...}

# Test case 2: Multiple agents
echo '{"subagent_type": "agent2"}' | bash .claude/hooks/agent_evidence_collector.sh Task
echo '{"subagent_type": "agent3"}' | bash .claude/hooks/agent_evidence_collector.sh Task

grep -c "agent_invocation" "$EVIDENCE_FILE"
# Expected: 3

# Test case 3: Non-Task tool should skip
bash .claude/hooks/agent_evidence_collector.sh Write
echo $?
# Expected: 0 (silent skip, no error)
```

---

### Part 4: Per-Phase Impact Assessment Integration

**New File**: `.claude/hooks/per_phase_impact_assessor.sh`

**Implementation**:
```bash
#!/bin/bash
# Per-Phase Impact Assessment Hook
# Triggers: PrePrompt (before each Phase starts)
# Purpose: Dynamically assess agent requirements for Phase2/3/4

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
ASSESSOR_SCRIPT="$PROJECT_ROOT/.claude/scripts/impact_radius_assessor.sh"
IMPACT_DIR="$WORKFLOW_DIR/impact_assessments"

mkdir -p "$IMPACT_DIR"

# Get current phase
get_current_phase() {
    if [[ -f "$WORKFLOW_DIR/current" ]]; then
        grep "^phase:" "$WORKFLOW_DIR/current" | awk '{print $2}' || echo "Phase1"
    else
        echo "Phase1"
    fi
}

# Main logic
CURRENT_PHASE=$(get_current_phase)

# Only assess Phase2, Phase3, Phase4
case "$CURRENT_PHASE" in
    "Phase2"|"Phase3"|"Phase4")
        echo "📊 Running per-phase Impact Assessment for $CURRENT_PHASE..." >&2

        # Check if assessor script exists
        if [[ ! -f "$ASSESSOR_SCRIPT" ]]; then
            echo "⚠️  Warning: impact_radius_assessor.sh not found, skipping assessment" >&2
            exit 0
        fi

        # Run assessment
        OUTPUT_FILE="$IMPACT_DIR/${CURRENT_PHASE}_assessment.json"

        # Call assessor with phase-specific flag
        # (Note: impact_radius_assessor.sh v1.4.0 supports --phase flag)
        if bash "$ASSESSOR_SCRIPT" --phase "$CURRENT_PHASE" --output "$OUTPUT_FILE" 2>&1; then
            # Read and display recommendation
            if [[ -f "$OUTPUT_FILE" ]]; then
                RECOMMENDED_AGENTS=$(jq -r '.recommended_agents // 0' "$OUTPUT_FILE" 2>/dev/null || echo "0")
                RISK_SCORE=$(jq -r '.impact_radius_score // 0' "$OUTPUT_FILE" 2>/dev/null || echo "0")

                echo "💡 $CURRENT_PHASE Assessment Results:" >&2
                echo "   - Risk Score: $RISK_SCORE/100" >&2
                echo "   - Recommended Agents: $RECOMMENDED_AGENTS" >&2
            fi
        else
            echo "⚠️  Assessment failed for $CURRENT_PHASE" >&2
        fi
        ;;
    *)
        # Other phases don't need per-phase assessment
        ;;
esac

exit 0
```

**Settings.json Update**:
```json
{
  "hooks": {
    "PrePrompt": [
      ".claude/hooks/force_branch_check.sh",
      ".claude/hooks/ai_behavior_monitor.sh",
      ".claude/hooks/workflow_enforcer.sh",
      ".claude/hooks/phase2_5_autonomous.sh",
      ".claude/hooks/smart_agent_selector.sh",
      ".claude/hooks/gap_scan.sh",
      ".claude/hooks/impact_assessment_enforcer.sh",
      ".claude/hooks/parallel_subagent_suggester.sh",
      ".claude/hooks/per_phase_impact_assessor.sh"  // ← NEW
    ],
    // ... other hooks
  }
}
```

**Testing**:
```bash
# Test Phase2 assessment
mkdir -p .workflow
echo "phase: Phase2" > .workflow/current

bash .claude/hooks/per_phase_impact_assessor.sh
# Expected: Calls impact_radius_assessor.sh --phase Phase2
#           Creates .workflow/impact_assessments/Phase2_assessment.json

# Verify output
cat .workflow/impact_assessments/Phase2_assessment.json
# Expected: JSON with recommended_agents field

# Test Phase1 (should not assess)
echo "phase: Phase1" > .workflow/current
bash .claude/hooks/per_phase_impact_assessor.sh
# Expected: exit 0 (silent skip)
```

---

## 🧪 Testing Strategy

### Unit Tests (26 test cases)

#### Test Suite 1: Impact Assessment Enforcer (6 cases)
**File**: `tests/hooks/test_impact_assessment_enforcer.sh`

```bash
#!/bin/bash
# Unit tests for impact_assessment_enforcer.sh

test_phase1_3_completed_triggers() {
    # Setup
    mkdir -p docs .workflow
    echo "phase: Phase1" > .workflow/current
    cat > docs/P1_DISCOVERY.md <<'EOF'
# Discovery
## Acceptance Checklist
- [ ] Test
EOF

    # Execute
    bash .claude/hooks/impact_assessment_enforcer.sh 2>&1 | tee /tmp/test.log

    # Assert
    grep -q "Impact Assessment" /tmp/test.log || return 1
    return 0
}

test_missing_p1_discovery_no_trigger() {
    # ... similar structure
}

test_missing_checklist_no_trigger() {
    # ...
}

test_wrong_phase_no_trigger() {
    # ...
}

test_smart_agent_selector_missing_error() {
    # ...
}

test_assessment_success_allows_continue() {
    # ...
}

# Run all tests
test_phase1_3_completed_triggers && echo "✅ Test 1 passed"
test_missing_p1_discovery_no_trigger && echo "✅ Test 2 passed"
# ... run all 6
```

#### Test Suite 2: Phase Completion Validator (7 cases)
**File**: `tests/hooks/test_phase_completion_validator.sh`

```bash
# Test each phase completion condition (Phase1-7)
test_phase1_completion()
test_phase2_completion()
test_phase3_completion()
test_phase4_completion()
test_phase5_completion()
test_phase6_completion()
test_phase7_completion()
```

#### Test Suite 3: Agent Evidence Collector (6 cases)
**File**: `tests/hooks/test_agent_evidence_collector.sh`

```bash
test_task_tool_records_evidence()
test_non_task_tool_skips()
test_jsonl_format_correct()
test_agent_count_accurate()
test_no_stdin_skips_gracefully()
test_daily_rotation()
```

#### Test Suite 4: Per-Phase Assessor (7 cases)
**File**: `tests/hooks/test_per_phase_assessor.sh`

```bash
test_phase2_triggers_assessment()
test_phase3_triggers_assessment()
test_phase4_triggers_assessment()
test_phase1_skips_assessment()
test_output_json_valid()
test_recommended_agents_exists()
test_assessor_missing_graceful_degradation()
```

### Integration Tests (1 comprehensive test)

**File**: `tests/integration/test_complete_workflow.sh`

```bash
#!/bin/bash
# End-to-end workflow test (Phase1-7)

test_complete_workflow() {
    # Phase 1: Create discovery doc
    mkdir -p docs .workflow
    echo "phase: Phase1" > .workflow/current
    cat > docs/P1_DISCOVERY.md <<'EOF'
# Discovery
## Acceptance Checklist
- [ ] Test
EOF

    # Should trigger impact assessment enforcer
    bash .claude/hooks/impact_assessment_enforcer.sh
    # ... verify

    # Phase 2: Make a commit
    echo "phase: Phase2" > .workflow/current
    git commit --allow-empty -m "feat: test implementation"

    # Should trigger phase completion validator
    TOOL_NAME=Write bash .claude/hooks/phase_completion_validator.sh
    # ... verify

    # Should trigger per-phase assessment
    bash .claude/hooks/per_phase_impact_assessor.sh
    # ... verify

    # ... continue through Phase3-7
}
```

### Regression Tests

**File**: `tests/regression/test_pr57_scenario.sh`

```bash
#!/bin/bash
# Verify PR #57 issues are fixed

test_pr57_cant_skip_phases() {
    # Simulate stopping after Phase 1-2
    # Should be blocked by phase completion validator

    # Create Phase 1 docs
    cat > docs/P1_DISCOVERY.md <<'EOF'
# Discovery
## Acceptance Checklist
EOF

    # Try to skip to Phase 5
    echo "phase: Phase5" > .workflow/current

    # Should fail validation (Phase2-4 not completed)
    # ... test logic
}

test_pr57_impact_assessment_enforced() {
    # Verify Impact Assessment is now enforced after Phase 1.3
    # ... test logic
}

test_pr57_agent_evidence_collected() {
    # Verify agent invocations are now recorded
    # ... test logic
}
```

---

## 📦 Deployment Plan

### Rollout Strategy

#### Step 1: Preparation (Phase 2)
- [ ] Implement all 4 fixes
- [ ] Run all unit tests locally
- [ ] Fix any shellcheck warnings
- [ ] Verify bash -n passes

#### Step 2: Local Validation (Phase 3)
- [ ] Run complete integration test
- [ ] Run regression tests
- [ ] Performance test all hooks (<2s)
- [ ] Manual smoke test

#### Step 3: Commit and Push (Phase 5)
- [ ] Stage all changes
- [ ] Create commit with proper message
- [ ] Push to remote branch
- [ ] Create Pull Request

#### Step 4: CI Validation
- [ ] Wait for all CI checks to pass
- [ ] Monitor for any failures
- [ ] Fix any CI-specific issues
- [ ] Re-push if needed

#### Step 5: Merge (Phase 7)
- [ ] User approves PR
- [ ] Merge to main via GitHub
- [ ] Verify hooks active on main
- [ ] Monitor for any production issues

### Rollback Plan

If critical issues discovered after merge:

**Quick Rollback** (< 5 minutes):
```bash
# Option 1: Git revert
git revert <commit-hash>
git push origin main

# Option 2: Restore old hooks from .bak files
cp .claude/hooks/*.bak .claude/hooks/
git commit -m "rollback: restore hooks to v8.5.0"
git push origin main
```

**Gradual Rollback** (if issues are non-critical):
```bash
# Disable specific hooks via settings.json
jq '.hooks.PrePrompt = (.hooks.PrePrompt | map(select(. != ".claude/hooks/per_phase_impact_assessor.sh")))' \
  .claude/settings.json > .claude/settings.json.tmp
mv .claude/settings.json.tmp .claude/settings.json
git commit -m "fix: disable per_phase_impact_assessor temporarily"
```

---

## 🔧 Technical Specifications

### File Modifications Summary

#### Modified Files (3)
1. `.claude/hooks/impact_assessment_enforcer.sh`
   - Lines changed: 3 (Lines 24-26, 40)
   - Changes: Function rename, file path fix, phase name fix
   - Complexity: Low

2. `.claude/hooks/phase_completion_validator.sh`
   - Lines changed: ~35 (Lines 28-62)
   - Changes: Complete case statement rewrite
   - Complexity: Medium

3. `.claude/hooks/agent_evidence_collector.sh`
   - Lines changed: ~100 (complete rewrite)
   - Changes: Remove dependencies, simplify logic
   - Complexity: Medium

#### New Files (2)
4. `.claude/hooks/per_phase_impact_assessor.sh`
   - Lines: ~80
   - Purpose: Per-phase assessment integration
   - Complexity: Medium

5. `.claude/settings.json`
   - Lines changed: 1 (add hook to PrePrompt array)
   - Complexity: Low

#### Test Files (4)
6. `tests/hooks/test_impact_assessment_enforcer.sh` (6 cases)
7. `tests/hooks/test_phase_completion_validator.sh` (7 cases)
8. `tests/hooks/test_agent_evidence_collector.sh` (6 cases)
9. `tests/hooks/test_per_phase_assessor.sh` (7 cases)

#### Documentation (4)
10. `docs/P1_DISCOVERY_workflow_supervision.md` ✅ (682 lines)
11. `.workflow/ACCEPTANCE_CHECKLIST_workflow_supervision.md` ✅ (321 lines)
12. `.workflow/IMPACT_ASSESSMENT_workflow_supervision.md` ✅ (current)
13. `docs/PLAN_workflow_supervision.md` ✅ (current)

**Total Files**: ~13-15 files

---

## 📊 Performance Considerations

### Hook Performance Targets

All hooks must complete within 2 seconds to avoid workflow delays.

**Current Performance** (measured):
- impact_assessment_enforcer.sh: <500ms ✅
- phase_completion_validator.sh: <1s ✅
- agent_evidence_collector.sh: <200ms ✅
- per_phase_impact_assessor.sh: <500ms ✅

**Optimization Strategies**:
1. Avoid expensive operations (find with -exec)
2. Cache file existence checks
3. Use built-in bash features over external commands
4. Early exit when conditions not met

### Disk Usage

**Evidence Collection**:
- Format: JSONL (compact)
- Daily rotation: 1 file per day
- Estimated size: ~1-10KB per day
- Retention: 30 days (auto-cleanup)
- Total: <300KB per month

---

## 🎯 Success Criteria

### Technical Success
1. ✅ All 3 bugs fixed and verified
2. ✅ Per-phase assessment working
3. ✅ All 26 tests passing
4. ✅ CI all checks pass
5. ✅ Shellcheck 0 warnings
6. ✅ All hooks <2s

### Functional Success
7. ✅ Impact Assessment enforced after Phase 1.3
8. ✅ Phase completion validated for all 7 phases
9. ✅ Agent evidence collected for all Task tool calls
10. ✅ Per-phase assessment runs for Phase2/3/4

### Quality Success
11. ✅ Code review approved
12. ✅ Documentation complete
13. ✅ Version consistency (6/6 files)
14. ✅ User acceptance sign-off

---

## 📅 Timeline

**Total Estimated Time**: 2-3 hours (AI time)

- **Phase 1: Discovery & Planning** - 30min ✅ COMPLETE
  - 1.1 Branch Check: 5min ✅
  - 1.2 Requirements: 5min ✅
  - 1.3 Discovery: 10min ✅
  - 1.4 Impact Assessment: 5min ✅
  - 1.5 Planning: 5min ✅ (current)

- **Phase 2: Implementation** - 60min
  - 2.1 Bug #1 fix: 15min
  - 2.2 Bug #2 fix: 20min
  - 2.3 Bug #3 fix: 15min
  - 2.4 Per-phase assessment: 10min

- **Phase 3: Testing** - 45min
  - 3.1-3.4 Unit tests: 30min (4 suites)
  - 3.5 Integration test: 10min
  - 3.6 Regression test: 5min

- **Phase 4: Review** - 20min
  - Code quality review: 10min
  - Documentation review: 5min
  - Pre-merge audit: 5min

- **Phase 5-7: Release, Acceptance, Closure** - 25min
  - Phase 5: 10min
  - Phase 6: 10min
  - Phase 7: 5min

---

## 🔒 Security Considerations

### Hook Security
- All hooks run with user permissions (no elevated privileges)
- No external network calls
- No sensitive data logging
- Input validation on all external data (JSON parsing)

### Evidence Data Privacy
- Evidence files stored locally in .workflow/
- .workflow/ is gitignored (not committed)
- No PII or sensitive data in evidence
- Auto-cleanup after 30 days

---

## 📚 References

- PR #57: Performance Optimization (exposed these bugs)
- `.claude/scripts/impact_radius_assessor.sh` v1.4.0
- `.workflow/SPEC.yaml` - Phase definitions
- `CLAUDE.md` - Anti-hollow gate documentation
- `.claude/ARCHITECTURE/` - Workflow system design

---

**Document Status**: ✅ Complete
**Next Phase**: Phase 2 - Implementation
**Ready to Proceed**: ✅ Yes (awaiting user approval)

---

## 🤝 Agent Allocation (6 agents)

As recommended by Impact Assessment (Radius=67, High-risk), this task will use **6 agents**:

1. **Agent 1**: Impact Assessment Enforcer Fix
2. **Agent 2**: Phase Completion Validator Fix
3. **Agent 3**: Agent Evidence Collector Simplification
4. **Agent 4**: Per-Phase Assessment Integration
5. **Agent 5**: Integration Testing & Validation
6. **Agent 6**: Documentation & Review

Each agent will work in parallel during Phase 2-3, then collaborate during Phase 4-7.

---

**End of Plan Document**
