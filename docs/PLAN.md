# Architecture Planning - Self-Enforcing Quality System

**Version**: 8.6.0
**Date**: 2025-10-30
**Task**: 实现Self-Enforcing Quality System - 防止功能回归
**Branch**: `feature/self-enforcing-quality-system`
**Recommended Agents**: 6 agents (Very High-risk: Radius=77/100)

---

## 🎯 Executive Summary

This document outlines the detailed implementation plan for the Self-Enforcing Quality System - a 3-layer defense mechanism to prevent feature regressions through runtime validation and automated enforcement.

**Primary Goals**:
1. Protect critical files from accidental modification (CODEOWNERS)
2. Detect hollow implementations through CI (Sentinel CI)
3. Verify features actually work (Contract Tests)
4. Track phase state continuously (phase_state_tracker.sh)
5. Integrate runtime validation (pre_merge_audit.sh enhancement)

**Success Metrics**:
- 6 components implemented and tested
- 61 CI checks running automatically
- 4 contract tests detecting hollows
- Phase state tracked on every prompt
- 0 shellcheck warnings
- All tests pass
- CI green

---

## 📐 System Architecture

### Overview: 3-Layer Defense

```
┌─────────────────────────────────────────────────────────────┐
│  Self-Enforcing Quality System (v8.6.0)                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Protected Core Files (CODEOWNERS)                 │
├──────────────────────────────────────────────────────────────┤
│  File: .github/CODEOWNERS                                    │
│  Protected: 31 critical files                                │
│  Owner: @perfectuser21                                       │
│  Purpose: Prevent accidental AI modification                │
│  Enforcement: GitHub PR approval required                    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 2: Sentinel CI (Runtime Validation in CI)            │
├──────────────────────────────────────────────────────────────┤
│  File: .github/workflows/guard-core.yml                      │
│  Jobs: 4 (61 total checks)                                  │
│    1. verify-critical-files (31 checks)                     │
│    2. verify-critical-configs (10 checks)                   │
│    3. verify-sentinel-strings (15 checks)                   │
│    4. validate-runtime-behavior (5 checks)                  │
│  Trigger: Every push, every PR                               │
│  Purpose: Detect hollow implementations, missing files       │
│  Enforcement: PR blocked if checks fail                      │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Layer 3: Contract Tests (Verify Features Work)             │
├──────────────────────────────────────────────────────────────┤
│  Directory: tests/contract/                                  │
│  Tests: 4 contract test scripts                             │
│    1. test_parallel_execution.sh                            │
│    2. test_phase_management.sh                              │
│    3. test_evidence_collection.sh                           │
│    4. test_bypass_permissions.sh                            │
│  Purpose: Test actual behavior, not just file existence     │
│  Enforcement: Phase 3 requires tests pass                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Enhancement 1: Phase State Tracker                          │
├──────────────────────────────────────────────────────────────┤
│  File: .claude/hooks/phase_state_tracker.sh                 │
│  Trigger: PrePrompt (every AI interaction)                  │
│  Purpose: Display current phase, detect stale state         │
│  Output: 3-4 lines (phase, warnings, reminders)             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Enhancement 2: Pre-merge Audit Runtime Validation          │
├──────────────────────────────────────────────────────────────┤
│  File: scripts/pre_merge_audit.sh                           │
│  Addition: Check 7 (Runtime Behavior Validation)            │
│  Sub-checks: 4 (7.1-7.4)                                    │
│  Purpose: Verify features executed recently                 │
│  Enforcement: Part of Phase 4 quality gate                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Detailed Implementation Plan

### Component 1: CODEOWNERS File

**File**: `.github/CODEOWNERS`
**Line Count**: ~40 lines
**Dependencies**: None
**Estimated Time**: 30 minutes

#### Structure

```
# Self-Enforcing Quality System - Protected Core Files
# Owner: @perfectuser21
# Purpose: Prevent accidental AI modification of critical files
# Last Updated: 2025-10-30

# ============================================
# Hooks - Cannot be modified without approval
# ============================================
/.claude/hooks/** @perfectuser21

# ============================================
# Workflow System - Core structure
# ============================================
/.workflow/SPEC.yaml @perfectuser21
/.workflow/manifest.yml @perfectuser21
/.workflow/gates.yml @perfectuser21

# ============================================
# Quality Scripts - Critical checks
# ============================================
/scripts/pre_merge_audit.sh @perfectuser21
/scripts/static_checks.sh @perfectuser21
/scripts/workflow_validator_v97.sh @perfectuser21

# ============================================
# Core Settings
# ============================================
/.claude/settings.json @perfectuser21
/CLAUDE.md @perfectuser21
/VERSION @perfectuser21

# ============================================
# Phase Management
# ============================================
/.workflow/cli/phase_manager.sh @perfectuser21

# ============================================
# CI/CD Workflows
# ============================================
/.github/workflows/ce-unified-gates.yml @perfectuser21
/.github/workflows/guard-core.yml @perfectuser21
```

#### Protected Files List (31 files)

**Hooks** (15 files):
- `.claude/hooks/force_branch_check.sh`
- `.claude/hooks/ai_behavior_monitor.sh`
- `.claude/hooks/workflow_enforcer.sh`
- `.claude/hooks/phase2_5_autonomous.sh`
- `.claude/hooks/smart_agent_selector.sh`
- `.claude/hooks/gap_scan.sh`
- `.claude/hooks/impact_assessment_enforcer.sh`
- `.claude/hooks/parallel_subagent_suggester.sh`
- `.claude/hooks/phase_state_tracker.sh` (new)
- `.claude/hooks/pre_tool_use.sh`
- `.claude/hooks/phase_transition.sh`
- `.claude/hooks/pre_write_document.sh`
- `.claude/hooks/branch_helper.sh`
- `.claude/hooks/quality_gate.sh`
- All other hooks in `.claude/hooks/`

**Workflow Configs** (5 files):
- `.workflow/SPEC.yaml`
- `.workflow/manifest.yml`
- `.workflow/gates.yml`
- `.workflow/current`
- `.phase/current`

**Quality Scripts** (5 files):
- `scripts/pre_merge_audit.sh`
- `scripts/static_checks.sh`
- `scripts/workflow_validator_v97.sh`
- `.workflow/cli/phase_manager.sh`
- `scripts/comprehensive_cleanup.sh`

**Core Settings** (3 files):
- `.claude/settings.json`
- `CLAUDE.md`
- `VERSION`

**CI Workflows** (3 files):
- `.github/workflows/ce-unified-gates.yml`
- `.github/workflows/guard-core.yml` (new)
- `.github/workflows/positive-health.yml`

#### Implementation Steps

1. Create `.github/CODEOWNERS` file
2. Add header comment
3. Add all 31 protected files (grouped by category)
4. Set owner to @perfectuser21 for all entries
5. Verify syntax (GitHub CODEOWNERS validator)
6. Test: Try to create PR modifying protected file (should require approval)

#### Testing

```bash
# Test 1: CODEOWNERS file exists
test -f .github/CODEOWNERS && echo "PASS" || echo "FAIL"

# Test 2: All 31 protected files listed
grep -c "@perfectuser21" .github/CODEOWNERS
# Expected: 31

# Test 3: Syntax valid
gh repo edit --enable-wiki=false  # Ensures CODEOWNERS is validated
# If CODEOWNERS has syntax errors, this will fail

# Test 4: Protection works (manual)
# 1. Create test branch
# 2. Modify protected file (e.g., .claude/settings.json)
# 3. Create PR
# 4. Verify "Review required from @perfectuser21" message
```

---

### Component 2: Guard Core CI Workflow

**File**: `.github/workflows/guard-core.yml`
**Line Count**: ~150 lines
**Dependencies**: 4 guard scripts (in scripts/guard/)
**Estimated Time**: 2 hours

#### Workflow Structure

```yaml
name: Guard Core System

on:
  push:
    branches:
      - main
      - 'feature/**'
      - 'bugfix/**'
  pull_request:
    branches:
      - main

jobs:
  verify-critical-files:
    name: "Verify Critical Files (31 checks)"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check Critical Files Exist
        run: |
          bash scripts/guard/check_critical_files.sh
          if [ $? -ne 0 ]; then
            echo "❌ Critical files check failed"
            exit 1
          fi

  verify-critical-configs:
    name: "Verify Critical Configs (10 checks)"
    runs-on: ubuntu-latest
    needs: verify-critical-files
    steps:
      - uses: actions/checkout@v3

      - name: Check Critical Configurations
        run: |
          bash scripts/guard/check_critical_configs.sh
          if [ $? -ne 0 ]; then
            echo "❌ Critical configs check failed"
            exit 1
          fi

  verify-sentinel-strings:
    name: "Verify Sentinel Strings (15 checks)"
    runs-on: ubuntu-latest
    needs: verify-critical-files
    steps:
      - uses: actions/checkout@v3

      - name: Check Sentinel Strings Present
        run: |
          bash scripts/guard/check_sentinels.sh
          if [ $? -ne 0 ]; then
            echo "❌ Sentinel strings check failed"
            exit 1
          fi

  validate-runtime-behavior:
    name: "Validate Runtime Behavior (5 checks)"
    runs-on: ubuntu-latest
    needs: verify-critical-files
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Need full history for git log checks

      - name: Check Runtime Behaviors
        run: |
          bash scripts/guard/validate_runtime_behavior.sh
          if [ $? -ne 0 ]; then
            echo "⚠️  Runtime validation warnings detected"
            # Don't fail CI, just warn
          fi
```

#### Implementation Steps

1. Create `.github/workflows/guard-core.yml`
2. Define trigger conditions (push, pull_request)
3. Create job 1: verify-critical-files
4. Create job 2: verify-critical-configs (depends on job 1)
5. Create job 3: verify-sentinel-strings (depends on job 1)
6. Create job 4: validate-runtime-behavior (depends on job 1)
7. Test workflow locally using `act` (if available)
8. Push to test branch and verify workflow runs
9. Check CI logs for any issues

#### Testing

```bash
# Test 1: YAML syntax valid
yamllint .github/workflows/guard-core.yml

# Test 2: Workflow can be triggered locally (if act available)
act -W .github/workflows/guard-core.yml

# Test 3: Push to test branch and verify workflow runs
git checkout -b test/guard-core-ci
git push -u origin test/guard-core-ci
# Check GitHub Actions tab

# Test 4: Verify all 4 jobs run
gh run list --workflow=guard-core.yml
```

---

### Component 3: Guard Scripts (4 scripts)

**Directory**: `scripts/guard/`
**Total Lines**: ~550 lines across 4 scripts
**Dependencies**: None (self-contained)
**Estimated Time**: 3 hours (1.5 hours each for Agent 3a and 3b)

#### Script 1: check_critical_files.sh

**Purpose**: Verify all 31 critical files exist
**Line Count**: ~100 lines
**Exit Code**: 0=pass, 1=fail

**Implementation**:

```bash
#!/bin/bash
# check_critical_files.sh
# Purpose: Verify all 31 critical files exist
# Exit: 0=pass, 1=fail

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Checking Critical Files Existence..."
echo "========================================"

FAILURES=0

# Function to check file exists
check_file() {
    local file="$1"
    local category="$2"

    if [[ -f "$file" ]] || [[ -d "$file" ]]; then
        echo "✅ $category: $file"
        return 0
    else
        echo "❌ $category: $file MISSING"
        ((FAILURES++))
        return 1
    fi
}

# Hooks (15 checks)
echo ""
echo "📌 Category: Hooks"
check_file ".claude/hooks/force_branch_check.sh" "Hook"
check_file ".claude/hooks/ai_behavior_monitor.sh" "Hook"
check_file ".claude/hooks/workflow_enforcer.sh" "Hook"
check_file ".claude/hooks/phase2_5_autonomous.sh" "Hook"
check_file ".claude/hooks/smart_agent_selector.sh" "Hook"
check_file ".claude/hooks/gap_scan.sh" "Hook"
check_file ".claude/hooks/impact_assessment_enforcer.sh" "Hook"
check_file ".claude/hooks/parallel_subagent_suggester.sh" "Hook"
check_file ".claude/hooks/phase_state_tracker.sh" "Hook"
check_file ".claude/hooks/pre_tool_use.sh" "Hook"
check_file ".claude/hooks/phase_transition.sh" "Hook"
check_file ".claude/hooks/pre_write_document.sh" "Hook"
check_file ".claude/hooks/branch_helper.sh" "Hook"
check_file ".claude/hooks/quality_gate.sh" "Hook"
check_file ".claude/hooks/" "Hook Directory"

# Workflow Configs (5 checks)
echo ""
echo "📌 Category: Workflow Configs"
check_file ".workflow/SPEC.yaml" "Config"
check_file ".workflow/manifest.yml" "Config"
check_file ".workflow/gates.yml" "Config"
check_file ".workflow/current" "Config"
check_file ".phase/current" "Config"

# Quality Scripts (5 checks)
echo ""
echo "📌 Category: Quality Scripts"
check_file "scripts/pre_merge_audit.sh" "Script"
check_file "scripts/static_checks.sh" "Script"
check_file "scripts/workflow_validator_v97.sh" "Script"
check_file ".workflow/cli/phase_manager.sh" "Script"
check_file "scripts/comprehensive_cleanup.sh" "Script"

# Core Settings (3 checks)
echo ""
echo "📌 Category: Core Settings"
check_file ".claude/settings.json" "Setting"
check_file "CLAUDE.md" "Setting"
check_file "VERSION" "Setting"

# CI Workflows (3 checks)
echo ""
echo "📌 Category: CI Workflows"
check_file ".github/workflows/ce-unified-gates.yml" "CI"
check_file ".github/workflows/guard-core.yml" "CI"
check_file ".github/workflows/positive-health.yml" "CI"

# Summary
echo ""
echo "========================================"
if [[ $FAILURES -eq 0 ]]; then
    echo "✅ All 31 critical files exist"
    exit 0
else
    echo "❌ $FAILURES critical files missing"
    echo ""
    echo "💡 Tip: These files are protected by CODEOWNERS"
    echo "    If deleted accidentally, restore from git history"
    exit 1
fi
```

**Testing**:

```bash
# Test 1: All files exist → pass
bash scripts/guard/check_critical_files.sh
echo $?  # Expected: 0

# Test 2: One file missing → fail
mv .claude/hooks/force_branch_check.sh /tmp/backup.sh
bash scripts/guard/check_critical_files.sh
echo $?  # Expected: 1
mv /tmp/backup.sh .claude/hooks/force_branch_check.sh
```

#### Script 2: check_critical_configs.sh

**Purpose**: Verify critical configurations are intact
**Line Count**: ~150 lines
**Exit Code**: 0=pass, 1=fail

**Checks** (10):
1. Bypass permissions configured (`defaultMode: "bypassPermissions"`)
2. 7-Phase system intact (SPEC.yaml: `total_phases: 7`)
3. Required hooks registered in settings.json
4. Version consistency (6 files match)
5. Phase naming consistent (Phase1-Phase7, not P0-P7)
6. CODEOWNERS exists and has 31 entries
7. guard-core.yml workflow exists
8. pre_merge_audit.sh executable
9. phase_state_tracker.sh registered in PrePrompt[0]
10. .phase/current file valid format

**Implementation**: (Abbreviated - full script ~150 lines)

```bash
#!/bin/bash
# check_critical_configs.sh
# Purpose: Verify critical configurations intact
# Exit: 0=pass, 1=fail

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Checking Critical Configurations..."
FAILURES=0

# Check 1: Bypass permissions
if grep -q '"defaultMode".*"bypassPermissions"' .claude/settings.json; then
    echo "✅ Check 1: Bypass permissions configured"
else
    echo "❌ Check 1: Bypass permissions NOT configured"
    ((FAILURES++))
fi

# Check 2: 7-Phase system
if grep -q 'total_phases: 7' .workflow/SPEC.yaml; then
    echo "✅ Check 2: 7-Phase system intact"
else
    echo "❌ Check 2: 7-Phase system BROKEN"
    ((FAILURES++))
fi

# ... (8 more checks)

# Summary
if [[ $FAILURES -eq 0 ]]; then
    echo "✅ All 10 critical configs intact"
    exit 0
else
    echo "❌ $FAILURES critical configs invalid"
    exit 1
fi
```

#### Script 3: check_sentinels.sh

**Purpose**: Verify sentinel strings present in critical files
**Line Count**: ~100 lines
**Exit Code**: 0=pass, 1=fail

**Sentinel Strings** (15):
1. `# SENTINEL:PARALLEL_EXECUTION_CORE_LOGIC` in parallel_subagent_suggester.sh
2. `# SENTINEL:PHASE_MANAGEMENT_CORE` in phase_manager.sh
3. `# SENTINEL:EVIDENCE_COLLECTION_CORE` in evidence collection scripts
4. `# SENTINEL:WORKFLOW_ENFORCER_CORE` in workflow_enforcer.sh
5-15. (Additional sentinels in other critical files)

**Implementation**:

```bash
#!/bin/bash
# check_sentinels.sh
# Purpose: Verify sentinel strings present (detects file gutting)
# Exit: 0=pass, 1=fail

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Checking Sentinel Strings..."
FAILURES=0

check_sentinel() {
    local file="$1"
    local sentinel="$2"

    if grep -q "$sentinel" "$file" 2>/dev/null; then
        echo "✅ Sentinel found: $file"
        return 0
    else
        echo "❌ Sentinel MISSING: $file"
        echo "   Expected: $sentinel"
        echo "   ⚠️  File may have been gutted!"
        ((FAILURES++))
        return 1
    fi
}

# Check all 15 sentinels
check_sentinel ".claude/hooks/parallel_subagent_suggester.sh" "# SENTINEL:PARALLEL_EXECUTION_CORE_LOGIC"
check_sentinel ".workflow/cli/phase_manager.sh" "# SENTINEL:PHASE_MANAGEMENT_CORE"
check_sentinel "scripts/evidence/collect.sh" "# SENTINEL:EVIDENCE_COLLECTION_CORE"
# ... (12 more)

if [[ $FAILURES -eq 0 ]]; then
    echo "✅ All 15 sentinels present"
    exit 0
else
    echo "❌ $FAILURES sentinels missing"
    exit 1
fi
```

**Note**: Need to add sentinel strings to files first (during implementation)

#### Script 4: validate_runtime_behavior.sh

**Purpose**: Verify features actually executed recently
**Line Count**: ~200 lines
**Exit Code**: 0=pass, 1=warnings (don't fail CI)

**Checks** (5):
1. parallel_subagent_suggester.sh has execution logs?
2. .phase/current updated in last 7 days?
3. Evidence files created in last 7 days?
4. Phase state maintained?
5. Git log shows phase transitions?

**Implementation**:

```bash
#!/bin/bash
# validate_runtime_behavior.sh
# Purpose: Verify features actually executed (detect hollows)
# Exit: 0=pass, 1=warnings (graceful degradation)

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "🔍 Validating Runtime Behavior..."
WARNINGS=0

# Check 1: parallel_subagent_suggester.sh logs
if [[ -f ".workflow/logs/subagent/suggester.log" ]]; then
    LAST_RUN=$(stat -c %Y ".workflow/logs/subagent/suggester.log")
    NOW=$(date +%s)
    AGE_DAYS=$(( (NOW - LAST_RUN) / 86400 ))

    if [[ $AGE_DAYS -lt 7 ]]; then
        echo "✅ Check 1: parallel_subagent_suggester.sh executed recently ($AGE_DAYS days)"
    else
        echo "⚠️  Check 1: parallel_subagent_suggester.sh stale ($AGE_DAYS days)"
        ((WARNINGS++))
    fi
else
    echo "⚠️  Check 1: parallel_subagent_suggester.sh NEVER executed (HOLLOW!)"
    ((WARNINGS++))
fi

# Check 2-5: Similar structure...

# Summary
if [[ $WARNINGS -eq 0 ]]; then
    echo "✅ All runtime behaviors healthy"
    exit 0
else
    echo "⚠️  $WARNINGS runtime behavior warnings"
    echo "💡 Tip: This is not a CI failure, but indicates potential hollow implementations"
    exit 0  # Don't fail CI, just warn
fi
```

---

### Component 4: Contract Tests (4 tests)

**Directory**: `tests/contract/`
**Total Lines**: ~290 lines across 4 scripts
**Dependencies**: None (self-contained)
**Estimated Time**: 2 hours

#### Test 1: test_parallel_execution.sh

**Purpose**: Test that parallel_subagent_suggester.sh actually runs
**Line Count**: ~80 lines

**Implementation**:

```bash
#!/bin/bash
# tests/contract/test_parallel_execution.sh
# Contract Test: Parallel Execution Feature

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo "🧪 Contract Test: Parallel Execution"
echo "===================================="

PASS=0
FAIL=0

# Test 1: Hook script exists
test_hook_exists() {
    if [[ -f ".claude/hooks/parallel_subagent_suggester.sh" ]]; then
        echo "✅ Test 1: Hook script exists"
        ((PASS++))
        return 0
    else
        echo "❌ Test 1: Hook script MISSING"
        ((FAIL++))
        return 1
    fi
}

# Test 2: Hook is executable
test_hook_executable() {
    if [[ -x ".claude/hooks/parallel_subagent_suggester.sh" ]]; then
        echo "✅ Test 2: Hook is executable"
        ((PASS++))
        return 0
    else
        echo "❌ Test 2: Hook is NOT executable"
        ((FAIL++))
        return 1
    fi
}

# Test 3: Hook registered in settings.json
test_hook_registered() {
    if grep -q "parallel_subagent_suggester.sh" .claude/settings.json; then
        echo "✅ Test 3: Hook registered in settings.json"
        ((PASS++))
        return 0
    else
        echo "❌ Test 3: Hook NOT registered"
        ((FAIL++))
        return 1
    fi
}

# Test 4: Hook has execution logs (critical!)
test_hook_actually_runs() {
    if [[ -f ".workflow/logs/subagent/suggester.log" ]]; then
        LAST_RUN=$(stat -c %Y ".workflow/logs/subagent/suggester.log")
        NOW=$(date +%s)
        AGE_DAYS=$(( (NOW - LAST_RUN) / 86400 ))

        if [[ $AGE_DAYS -lt 7 ]]; then
            echo "✅ Test 4: Hook actually runs (last run: $AGE_DAYS days ago)"
            ((PASS++))
            return 0
        else
            echo "⚠️  Test 4: Hook logs stale ($AGE_DAYS days old)"
            echo "    WARNING: Feature may not be working"
            ((FAIL++))
            return 1
        fi
    else
        echo "❌ Test 4: Hook has NEVER run (HOLLOW IMPLEMENTATION!)"
        echo "    CRITICAL: Feature exists but never executes"
        ((FAIL++))
        return 1
    fi
}

# Run all tests
test_hook_exists
test_hook_executable
test_hook_registered
test_hook_actually_runs

# Summary
echo ""
echo "===================================="
echo "Results: $PASS pass, $FAIL fail"

if [[ $FAIL -eq 0 ]]; then
    echo "✅ Contract: Parallel Execution feature VERIFIED"
    exit 0
else
    echo "❌ Contract: Parallel Execution feature BROKEN"
    exit 1
fi
```

#### Test 2: test_phase_management.sh

**Purpose**: Test that phase_manager.sh is actually called
**Line Count**: ~90 lines

**Tests**:
1. phase_manager.sh exists
2. .phase/current exists
3. .phase/current maintained (<7 days old)
4. Git log shows phase transitions
5. Phase transitions follow sequence (Phase1→2→3...)

#### Test 3: test_evidence_collection.sh

**Purpose**: Test that evidence is actually collected
**Line Count**: ~70 lines

**Tests**:
1. .evidence/ directory exists
2. .evidence/schema.json exists
3. Recent evidence files (<7 days)
4. Evidence files are valid YAML
5. Evidence linked to checklist items

#### Test 4: test_bypass_permissions.sh

**Purpose**: Test that bypass permissions config is correct
**Line Count**: ~50 lines

**Tests**:
1. settings.json has defaultMode=bypassPermissions
2. No "allow" rules override defaultMode
3. Configuration structure correct
4. **Manual verification needed**: Check if Claude Code actually prompts

**Note**: This test cannot be fully automated (requires Claude Code environment).
Document manual test procedure.

---

### Component 5: Pre-merge Audit Enhancement

**File**: `scripts/pre_merge_audit.sh`
**Changes**: Add new section (~80 lines)
**Dependencies**: None (uses existing functions)
**Estimated Time**: 1.5 hours

#### Implementation

**Location**: After existing checks (around line 800+)

```bash
# ============================================
# Check 7: Runtime Behavior Validation (NEW)
# ============================================
log_check "Runtime Behavior Validation"

# Check 7.1: parallel_subagent_suggester.sh actually executed?
if [ -f ".workflow/logs/subagent/suggester.log" ]; then
    LAST_RUN=$(stat -c %Y ".workflow/logs/subagent/suggester.log" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    AGE_DAYS=$(( (NOW - LAST_RUN) / 86400 ))

    if [ $AGE_DAYS -lt 7 ]; then
        log_pass "parallel_subagent_suggester.sh executed in last 7 days"
    else
        log_warn "parallel_subagent_suggester.sh not executed in $AGE_DAYS days"
        log_manual "Verify: Is parallel execution actually working?"
    fi
else
    log_fail "parallel_subagent_suggester.sh has NEVER executed (hollow implementation!)"
    ((config_issues++))
fi

# Check 7.2: phase_manager.sh actually called?
if git log --all --since="7 days ago" --grep="phase transition\|ce_phase_transition" 2>/dev/null | grep -q .; then
    log_pass "Phase transitions happening"
else
    log_warn "No phase transitions in git log (phase_manager.sh not being used?)"
    log_manual "Verify: Is .phase/current being maintained?"
fi

# Check 7.3: Evidence collected for last PR?
LAST_PR_NUM=$(gh pr list --state merged --limit 1 --json number --jq '.[0].number' 2>/dev/null || echo "0")
if [ "$LAST_PR_NUM" != "0" ]; then
    EVIDENCE_COUNT=$(find .evidence/ -name "*.yml" -newer ".evidence/index.json" 2>/dev/null | wc -l)
    if [ $EVIDENCE_COUNT -gt 0 ]; then
        log_pass "Evidence collected for recent changes ($EVIDENCE_COUNT files)"
    else
        log_warn "No evidence collected for PR #$LAST_PR_NUM"
        log_manual "Verify: Was evidence collection skipped?"
    fi
fi

# Check 7.4: .phase/current maintained?
if [ -f ".phase/current" ]; then
    LAST_MOD=$(stat -c %Y .phase/current 2>/dev/null || echo 0)
    NOW=$(date +%s)
    AGE_DAYS=$(( (NOW - LAST_MOD) / 86400 ))

    if [ $AGE_DAYS -lt 7 ]; then
        log_pass ".phase/current maintained ($AGE_DAYS days old)"
    else
        log_warn ".phase/current stale ($AGE_DAYS days old)"
        log_manual "Verify: Is phase state being updated?"
    fi
else
    log_fail ".phase/current missing"
    ((config_issues++))
fi
```

#### Testing

```bash
# Test 1: Run pre_merge_audit.sh locally
bash scripts/pre_merge_audit.sh

# Test 2: Verify Check 7 section executes
bash scripts/pre_merge_audit.sh 2>&1 | grep "Check 7:"

# Test 3: Verify Check 7.1-7.4 all execute
bash scripts/pre_merge_audit.sh 2>&1 | grep "Check 7\.[1-4]"

# Test 4: Test with stale state (>.7 days)
touch -d "8 days ago" .phase/current
bash scripts/pre_merge_audit.sh 2>&1 | grep "stale"
```

---

### Component 6: Phase State Tracker Hook

**File**: `.claude/hooks/phase_state_tracker.sh`
**Line Count**: ~80 lines
**Dependencies**: None (self-contained)
**Estimated Time**: 1 hour

#### Implementation

```bash
#!/bin/bash
# phase_state_tracker.sh
# Purpose: Track and display phase state, remind AI to update
# Trigger: PrePrompt (every AI interaction)

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PHASE_FILE="$PROJECT_ROOT/.phase/current"

# Get current phase
get_current_phase() {
    if [[ -f "$PHASE_FILE" ]]; then
        grep "^phase:" "$PHASE_FILE" | awk '{print $2}' || echo "Unknown"
    else
        echo "Unknown"
    fi
}

# Check if phase state is stale
is_phase_stale() {
    if [[ -f "$PHASE_FILE" ]]; then
        LAST_MOD=$(stat -c %Y "$PHASE_FILE" 2>/dev/null || echo 0)
        NOW=$(date +%s)
        AGE_DAYS=$(( (NOW - LAST_MOD) / 86400 ))

        if [[ $AGE_DAYS -gt 7 ]]; then
            return 0  # Stale
        fi
    fi
    return 1  # Not stale
}

# Main logic
CURRENT_PHASE=$(get_current_phase)

echo "📍 Current Phase: $CURRENT_PHASE"

if is_phase_stale; then
    echo "⚠️  Warning: Phase state is stale (>7 days old)"
    echo "💡 Reminder: Update .phase/current when transitioning phases:"
    echo "   echo 'phase: Phase2' > .phase/current"
fi

# Phase-specific transition reminders
case "$CURRENT_PHASE" in
    "Phase1")
        if [[ -f "$PROJECT_ROOT/docs/P1_DISCOVERY.md" ]] &&
           [[ -f "$PROJECT_ROOT/docs/PLAN.md" ]]; then
            echo "💡 Phase 1 complete? Remember to transition to Phase 2:"
            echo "   echo 'phase: Phase2' > .phase/current"
        fi
        ;;
    "Phase2")
        echo "💡 After implementing core features, transition to Phase 3:"
        echo "   echo 'phase: Phase3' > .phase/current"
        ;;
    "Phase3")
        echo "💡 After all tests pass, transition to Phase 4:"
        echo "   echo 'phase: Phase4' > .phase/current"
        ;;
    "Phase4")
        echo "💡 After code review approved, transition to Phase 5:"
        echo "   echo 'phase: Phase5' > .phase/current"
        ;;
    "Phase5")
        echo "💡 After release notes complete, transition to Phase 6:"
        echo "   echo 'phase: Phase6' > .phase/current"
        ;;
    "Phase6")
        echo "💡 After user acceptance, transition to Phase 7:"
        echo "   echo 'phase: Phase7' > .phase/current"
        ;;
    "Phase7")
        echo "💡 Closure phase - remember to clean up and prepare for merge"
        ;;
    *)
        # Unknown phase
        ;;
esac

exit 0
```

#### Settings.json Update

```json
{
  "hooks": {
    "PrePrompt": [
      ".claude/hooks/phase_state_tracker.sh",  // ← NEW (position 0)
      ".claude/hooks/force_branch_check.sh",
      ".claude/hooks/ai_behavior_monitor.sh",
      ".claude/hooks/workflow_enforcer.sh",
      ".claude/hooks/phase2_5_autonomous.sh",
      ".claude/hooks/smart_agent_selector.sh",
      ".claude/hooks/gap_scan.sh",
      ".claude/hooks/impact_assessment_enforcer.sh",
      ".claude/hooks/parallel_subagent_suggester.sh"
    ]
  }
}
```

#### Testing

```bash
# Test 1: Hook script exists and executable
test -x .claude/hooks/phase_state_tracker.sh && echo "PASS" || echo "FAIL"

# Test 2: Run hook manually
bash .claude/hooks/phase_state_tracker.sh

# Test 3: Test with Phase1
echo "phase: Phase1" > .phase/current
bash .claude/hooks/phase_state_tracker.sh
# Expected: "Current Phase: Phase1" + reminder to transition

# Test 4: Test with stale state
touch -d "8 days ago" .phase/current
bash .claude/hooks/phase_state_tracker.sh
# Expected: Warning about stale state

# Test 5: Verify registered in settings.json
grep -q "phase_state_tracker.sh" .claude/settings.json && echo "PASS" || echo "FAIL"
```

---

## 🧪 Testing Strategy

### Unit Tests (20 test cases)

**Test Suite 1: CODEOWNERS (5 tests)**
- Test 1: CODEOWNERS file exists
- Test 2: All 31 protected files listed
- Test 3: Correct owner (@perfectuser21)
- Test 4: Syntax valid
- Test 5: No duplicate entries

**Test Suite 2: Guard Scripts (8 tests)**
- Test 1: check_critical_files.sh passes when all exist
- Test 2: check_critical_files.sh fails when one missing
- Test 3: check_critical_configs.sh passes when valid
- Test 4: check_critical_configs.sh fails when invalid
- Test 5: check_sentinels.sh passes when all present
- Test 6: check_sentinels.sh fails when one missing
- Test 7: validate_runtime_behavior.sh passes when recent
- Test 8: validate_runtime_behavior.sh warns when stale

**Test Suite 3: Contract Tests (4 tests)**
- Test 1: test_parallel_execution.sh
- Test 2: test_phase_management.sh
- Test 3: test_evidence_collection.sh
- Test 4: test_bypass_permissions.sh

**Test Suite 4: Phase State Tracker (3 tests)**
- Test 1: Displays current phase correctly
- Test 2: Detects stale state (>7 days)
- Test 3: Shows transition reminders

### Integration Tests (2 scenarios)

**Integration Test 1: CI Workflow**
- Trigger guard-core.yml on test branch
- Verify all 4 jobs run successfully
- Verify 61 total checks executed
- Test failure scenarios (remove critical file, etc.)

**Integration Test 2: End-to-End Workflow**
- Simulate Phase 1-7 workflow
- Verify phase_state_tracker.sh shows correct phase at each step
- Verify runtime validation catches stale state
- Verify contract tests detect hollow implementations
- Verify pre_merge_audit.sh includes new checks

---

## 📦 Deployment Plan

### Phase 2: Implementation (Parallel - 6 agents)

**Agent 1: CODEOWNERS & Documentation** (1 hour)
- Create .github/CODEOWNERS
- List all 31 protected files
- Update CLAUDE.md with new AI responsibilities
- Update README.md with quality enforcement section

**Agent 2: Guard Core CI Workflow** (2 hours)
- Create .github/workflows/guard-core.yml
- Define 4 jobs with 61 total checks
- Test workflow locally (if possible)
- Push to test branch and verify

**Agent 3a: Guard Scripts (Part 1)** (1.5 hours)
- Create scripts/guard/check_critical_files.sh
- Create scripts/guard/check_critical_configs.sh
- Test both scripts locally

**Agent 3b: Guard Scripts (Part 2)** (1.5 hours)
- Add sentinel strings to 15 critical files
- Create scripts/guard/check_sentinels.sh
- Create scripts/guard/validate_runtime_behavior.sh
- Test both scripts locally

**Agent 4: Contract Tests** (2 hours)
- Create tests/contract/test_parallel_execution.sh
- Create tests/contract/test_phase_management.sh
- Create tests/contract/test_evidence_collection.sh
- Create tests/contract/test_bypass_permissions.sh
- Run all contract tests

**Agent 5: Pre-merge Audit Enhancement** (1.5 hours)
- Open scripts/pre_merge_audit.sh
- Add Check 7 section (Runtime Behavior Validation)
- Add Check 7.1-7.4 sub-checks
- Test locally

**Agent 6: Phase State Tracker & Integration** (2 hours)
- Create .claude/hooks/phase_state_tracker.sh
- Update .claude/settings.json (add to PrePrompt[0])
- Make hook executable
- Test hook manually
- Run integration tests
- Verify all components work together

**Estimated Wall Time**: 2-3 hours (with 6 agents in parallel)

---

### Phase 3: Testing (Sequential - 3-4 hours)

1. Run all unit tests (20 tests) - 1 hour
2. Run all contract tests (4 tests) - 30 minutes
3. Run integration tests (2 tests) - 1 hour
4. Fix any issues found - 1-1.5 hours
5. Re-run failed tests - 30 minutes

---

### Phase 4: Review (Sequential - 2 hours)

1. Code review (all 6 components) - 1 hour
2. Documentation review (4 Phase 1 docs) - 30 minutes
3. Pre-merge audit - 30 minutes

---

### Phase 5-7: Release, Acceptance, Closure (Sequential - 2 hours)

1. Version updates (6 files) - 15 minutes
2. CHANGELOG updates - 15 minutes
3. User acceptance testing - 1 hour
4. PR creation and merge - 30 minutes

---

## 🔒 Rollback Plan

### Quick Rollback (< 5 minutes)

If critical issues discovered after merge:

```bash
# Option 1: Git revert
git revert <commit-hash>
git push origin main

# Option 2: Disable CODEOWNERS
mv .github/CODEOWNERS .github/CODEOWNERS.disabled
git commit -m "fix: disable CODEOWNERS temporarily"
git push origin main

# Option 3: Disable guard-core.yml
mv .github/workflows/guard-core.yml .github/workflows/guard-core.yml.disabled
git commit -m "fix: disable guard-core.yml temporarily"
git push origin main
```

### Gradual Rollback (if issues are non-critical)

```bash
# Disable specific checks in guard-core.yml
# Edit .github/workflows/guard-core.yml
# Comment out problematic job

# Or disable phase_state_tracker.sh
jq '.hooks.PrePrompt = (.hooks.PrePrompt | map(select(. != ".claude/hooks/phase_state_tracker.sh")))' \
  .claude/settings.json > .claude/settings.json.tmp
mv .claude/settings.json.tmp .claude/settings.json
git commit -m "fix: disable phase_state_tracker temporarily"
```

---

## 🎯 Success Criteria

### Technical Success
1. ✅ CODEOWNERS file created and protects 31 critical files
2. ✅ guard-core.yml CI workflow created with 61 checks
3. ✅ 4 guard scripts created and tested
4. ✅ 4 contract tests created and pass
5. ✅ pre_merge_audit.sh enhanced with Check 7
6. ✅ phase_state_tracker.sh created and registered
7. ✅ All scripts <2s execution time
8. ✅ 0 shellcheck warnings
9. ✅ All tests pass
10. ✅ CI green

### Functional Success
11. ✅ AI cannot modify protected files without approval
12. ✅ CI detects hollow implementations
13. ✅ Contract tests catch regressions
14. ✅ Phase state tracked on every prompt
15. ✅ Runtime validation integrated into pre-merge audit

### Quality Success
16. ✅ Code review approved
17. ✅ Documentation complete (4 Phase 1 docs)
18. ✅ Version consistency (6/6 files)
19. ✅ User acceptance confirmed

### Long-term Success (30-day verification)
20. ✅ Hollow Implementation Rate = 0%
21. ✅ No regressions of parallel execution
22. ✅ No regressions of phase management
23. ✅ Phase state maintained continuously
24. ✅ Evidence collection working

---

## 📊 Performance Targets

### Hook Performance
- phase_state_tracker.sh: <500ms ✅
- All PrePrompt hooks combined: <2s ✅

### Guard Script Performance
- check_critical_files.sh: <1s ✅
- check_critical_configs.sh: <1.5s ✅
- check_sentinels.sh: <1s ✅
- validate_runtime_behavior.sh: <2s ✅

### Contract Test Performance
- test_parallel_execution.sh: <5s ✅
- test_phase_management.sh: <5s ✅
- test_evidence_collection.sh: <3s ✅
- test_bypass_permissions.sh: <2s ✅

### CI Performance
- guard-core.yml total time: <5 minutes ✅
- All 4 jobs run in parallel: <2 minutes each ✅

---

## 📚 References

- `.temp/REGRESSION_ANALYSIS.md` - Detailed regression analysis
- `.temp/META_HOLLOW_DETECTION.md` - Anti-Hollow system hollowness analysis
- `CLAUDE.md` - Anti-Hollow Gate System documentation
- GitHub CODEOWNERS documentation
- GitHub Actions workflow syntax
- Bash scripting best practices

---

## 🤝 Agent Coordination Strategy

### Parallel Work (Phase 2)

**No Dependencies** (can work simultaneously):
- Agent 1 (CODEOWNERS) ← independent
- Agent 2 (guard-core.yml) ← independent
- Agent 3a (guard scripts part 1) ← independent
- Agent 3b (guard scripts part 2) ← depends on Agent 3a for sentinel placement
- Agent 4 (contract tests) ← independent
- Agent 5 (pre_merge_audit enhancement) ← independent
- Agent 6 (phase_state_tracker) ← independent

**Coordination Points**:
1. Agent 3b waits for Agent 3a to identify files needing sentinels
2. Agent 6 waits for all others to finish before running integration tests

### Communication Protocol

**Status Updates** (every 30 minutes):
- Progress percentage (e.g., "Agent 1: 75% complete")
- Blockers encountered
- ETA to completion

**Blockers Resolution**:
- If Agent X blocked by missing dependency → notify Agent Y
- If syntax error discovered → fix immediately, notify all agents
- If test fails → investigate, fix, re-test

---

**Document Status**: ✅ Complete
**Line Count**: 1,257 lines
**Ready for Phase 2**: Awaiting user approval
**Estimated Total Time**: 9-11 hours (AI time), 2-3 hours (wall time with 6 agents)
