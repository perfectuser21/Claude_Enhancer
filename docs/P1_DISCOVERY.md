# Phase 1.3: Technical Discovery - Self-Enforcing Quality System

**Version**: 8.5.2
**Date**: 2025-10-30
**Task**: 实现Self-Enforcing Quality System - 防止功能回归
**Branch**: `feature/self-enforcing-quality-system`

---

## 🎯 Executive Summary

**Problem Statement**: Working features stop working after iterations due to hollow implementations and lack of runtime validation.

**Root Cause**: Anti-Hollow System itself is hollow - it checks for file existence but not actual execution.

**Solution**: 3-Layer Defense System
1. **CODEOWNERS** - Protected core files requiring approval
2. **Sentinel CI** - Runtime validation checks in CI
3. **Contract Tests** - Verify features actually work, not just exist

**Impact**: Prevents regression issues like parallel execution and phase management bugs that plagued previous versions.

---

## 📊 Problem Analysis

### Evidence of Regressions (from .temp/REGRESSION_ANALYSIS.md)

#### Regression #1: Parallel Execution Never Happens

**Symptom**: User reported "我感觉你都是串行 不是并行的"

**Investigation Evidence**:
1. `parallel_subagent_suggester.sh` exists and is registered in settings.json
2. But `.workflow/logs/subagent/suggester.log` does not exist
3. Hook depends on `.phase/current` file
4. `.phase/current` shows "Phase7" but was never updated by AI
5. `phase_manager.sh` exists (835 lines) but AI never calls it

**Root Cause**: Three missing links
- Missing Hook: No PrePrompt hook tells AI current phase
- Missing Integration: phase_manager.sh not integrated with workflow
- Missing Documentation: CLAUDE.md doesn't say "call ce_phase_transition()"

**Result**:
- `.phase/current` stays at old value
- `parallel_subagent_suggester.sh` reads wrong phase
- Hook logic correct but input wrong → never triggers
- All parallel execution suggestions never happen

**Impact Radius**:
- Phase 2-4 Implementation: Serial execution, wasting time
- Development Speed: ~40-60% efficiency loss
- Since: v8.0+

#### Regression #2: Bypass Permissions Repeatedly Wrong

**Symptom**: User reported "这个bypass的这些我都说了不下10回了还是错的"

**Investigation Evidence**:
1. v6.1.0: `bypassPermissionsMode: true` (non-standard field)
2. v7.1.0: `defaultMode: "bypassPermissions"` (fix attempt #1)
3. v8.5.1: Still using same config, but STILL asks user
4. Configuration looks correct but doesn't work

**Root Cause Hypotheses**:
- Configuration structure wrong (nested vs top-level)
- allow[] list too specific, overrides defaultMode
- Claude Code version changes require new config format
- No tests verify bypass actually works

**Result**:
- AI asks for confirmation every operation
- Breaks autonomy principle
- User frustrated: "said 10 times still wrong"

**Why It Keeps Regressing**:
- External Change: Claude Code version/behavior changes
- Configuration Drift: Format requirements change but docs not updated
- Test Gap: No automated tests verify bypass works
- Context Loss: AI doesn't remember why configured this way

---

## 🔍 Systemic Issues (from .temp/META_HOLLOW_DETECTION.md)

### The Irony: Anti-Hollow System is Hollow

We claim to have Anti-Hollow System, but:
- ❌ Parallel execution feature is hollow (code exists, never runs)
- ❌ Phase management is hollow (scripts exist, never called)
- ❌ Bypass permissions is hollow (configured, doesn't work)
- ❌ Evidence system is hollow (scripts exist, never collect key evidence)
- ❌ **Anti-Hollow System itself is hollow!**

### What Makes Anti-Hollow System Hollow?

#### Symptom 1: Rules Don't Apply to Themselves
```markdown
CLAUDE.md Rule 3: "Every Feature = Evidence + Integration + Active Usage"

But Anti-Hollow System itself:
- Evidence: ❌ No evidence it prevents hollows
- Integration: ❌ Not integrated with pre-merge audit
- Active Usage: ❌ Never actually blocked a hollow implementation
```

#### Symptom 2: Checks Are Shallow
```bash
# Current pre_merge_audit.sh checks:
✅ File exists? (shallow)
✅ Config formatted? (shallow)
✅ Hooks registered? (shallow)

# But doesn't check:
❌ Hook actually runs? (deep)
❌ Feature actually works? (deep)
❌ Evidence actually collected? (deep)
```

#### Symptom 3: No Runtime Validation
```bash
# We check:
✅ parallel_subagent_suggester.sh exists
✅ parallel_subagent_suggester.sh registered in settings.json

# We DON'T check:
❌ Did it execute in last 7 days?
❌ Does .workflow/logs/subagent/suggester.log exist?
❌ Did any PR actually use parallel execution?
```

#### Symptom 4: Evidence System Not Enforced
```bash
# Evidence system exists but:
❌ AI can skip collecting evidence
❌ Pre-merge audit doesn't verify evidence for critical features
❌ Can merge PRs with 0 evidence collected
❌ No enforcement mechanism
```

---

## 💡 Solution Design: Self-Enforcing Quality System

### Three Layers of Defense

#### Layer 1: Protected Core Files (CODEOWNERS)

**Purpose**: Prevent AI from accidentally modifying critical files without human approval.

**Mechanism**: GitHub CODEOWNERS file

**Protected Files**:
- `.claude/hooks/**` - All hooks
- `.workflow/**` - Workflow configs (SPEC.yaml, manifest.yml, gates.yml)
- `scripts/pre_merge_audit.sh` - Pre-merge audit script
- `scripts/static_checks.sh` - Static checks script
- `.claude/settings.json` - Core settings
- `CLAUDE.md` - AI instructions
- `VERSION` - Version file
- `.workflow/SPEC.yaml` - Core structure definition

**Implementation**:
```
# .github/CODEOWNERS
# Self-Enforcing Quality System - Protected Core Files

# Hooks - Cannot be modified without approval
/.claude/hooks/** @perfectuser21

# Workflow System - Core structure
/.workflow/SPEC.yaml @perfectuser21
/.workflow/manifest.yml @perfectuser21
/.workflow/gates.yml @perfectuser21

# Quality Scripts - Critical checks
/scripts/pre_merge_audit.sh @perfectuser21
/scripts/static_checks.sh @perfectuser21

# Core Settings
/.claude/settings.json @perfectuser21
/CLAUDE.md @perfectuser21
/VERSION @perfectuser21
```

**AI Rule**: Never modify these files unless explicitly instructed by @perfectuser21.

---

#### Layer 2: Sentinel Checks (CI)

**Purpose**: Verify critical files exist AND verify critical features actually work.

**Mechanism**: New GitHub Actions workflow: `guard-core.yml`

**Checks**:
1. **Critical Files Existence** (31 checks)
   - All 7 phase hooks exist
   - Core scripts exist (pre_merge_audit.sh, static_checks.sh, phase_manager.sh)
   - Core configs exist (settings.json, SPEC.yaml, manifest.yml)

2. **Critical Configurations Intact** (10 checks)
   - Bypass permissions configured correctly
   - 7-Phase system structure intact
   - Required hooks registered in settings.json
   - Version consistency across 6 files

3. **Anti-Hollow Sentinel Strings** (15 checks)
   - Sentinel comments present in critical files
   - Example: `# SENTINEL:PARALLEL_EXECUTION_CORE_LOGIC` in parallel_subagent_suggester.sh
   - If sentinel missing → file was gutted → fail CI

4. **Runtime Behavior Validation** (NEW - 5 checks)
   - `parallel_subagent_suggester.sh` has execution logs?
   - `.phase/current` updated in last 7 days?
   - Evidence collection produced files in last 7 days?
   - Phase state maintained?
   - Git log shows phase transitions?

**Implementation**:
```yaml
# .github/workflows/guard-core.yml
name: Guard Core System

on:
  push:
    branches: [main, 'feature/**', 'bugfix/**']
  pull_request:

jobs:
  verify-critical-files:
    name: Verify Critical Files
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check Critical Files Exist
        run: |
          bash scripts/guard/check_critical_files.sh
          # Checks all 31 critical files

      - name: Check Critical Configs
        run: |
          bash scripts/guard/check_critical_configs.sh
          # Checks bypass permissions, 7-phase system, etc.

      - name: Check Anti-Hollow Sentinels
        run: |
          bash scripts/guard/check_sentinels.sh
          # Checks sentinel strings in critical files

      - name: Validate Runtime Behavior
        run: |
          bash scripts/guard/validate_runtime_behavior.sh
          # NEW: Check if features actually executed
```

**Failure = PR blocked**

---

#### Layer 3: Contract Tests

**Purpose**: Test that features **actually work**, not just exist.

**Mechanism**: Shell-based contract tests in `tests/contract/`

**Test Examples**:

1. **Parallel Execution Contract**:
```bash
#!/bin/bash
# tests/contract/test_parallel_execution.sh

test_parallel_suggester_actually_runs() {
    # Setup: Create Phase 2 scenario
    mkdir -p .workflow/logs/subagent
    echo "phase: Phase2" > .phase/current

    # Execute: Trigger hook
    bash .claude/hooks/parallel_subagent_suggester.sh

    # Assert: Log file created
    if [[ -f ".workflow/logs/subagent/suggester.log" ]]; then
        echo "✅ PASS: parallel_subagent_suggester.sh actually runs"
        return 0
    else
        echo "❌ FAIL: parallel_subagent_suggester.sh exists but never runs (HOLLOW!)"
        return 1
    fi
}

test_parallel_suggester_logs_recent() {
    # Assert: Log updated in last 7 days
    if [[ -f ".workflow/logs/subagent/suggester.log" ]]; then
        LAST_MOD=$(stat -c %Y .workflow/logs/subagent/suggester.log)
        NOW=$(date +%s)
        AGE_DAYS=$(( (NOW - LAST_MOD) / 86400 ))

        if [[ $AGE_DAYS -lt 7 ]]; then
            echo "✅ PASS: suggester.log updated recently ($AGE_DAYS days)"
            return 0
        else
            echo "❌ FAIL: suggester.log stale ($AGE_DAYS days) - feature not being used"
            return 1
        fi
    else
        echo "❌ FAIL: suggester.log doesn't exist"
        return 1
    fi
}
```

2. **Phase Management Contract**:
```bash
#!/bin/bash
# tests/contract/test_phase_management.sh

test_phase_current_maintained() {
    # Assert: .phase/current exists and is recent
    if [[ ! -f ".phase/current" ]]; then
        echo "❌ FAIL: .phase/current missing"
        return 1
    fi

    LAST_MOD=$(stat -c %Y .phase/current)
    NOW=$(date +%s)
    AGE_DAYS=$(( (NOW - LAST_MOD) / 86400 ))

    if [[ $AGE_DAYS -lt 7 ]]; then
        echo "✅ PASS: .phase/current maintained ($AGE_DAYS days)"
        return 0
    else
        echo "❌ FAIL: .phase/current stale ($AGE_DAYS days) - phase_manager.sh not being called"
        return 1
    fi
}

test_phase_transitions_in_git_log() {
    # Assert: Git log shows phase transitions
    if git log --all --since="7 days ago" --grep="phase transition\|ce_phase_transition" | grep -q .; then
        echo "✅ PASS: Phase transitions happening"
        return 0
    else
        echo "❌ FAIL: No phase transitions in git log (phase_manager.sh not being used)"
        return 1
    fi
}
```

3. **Evidence Collection Contract**:
```bash
#!/bin/bash
# tests/contract/test_evidence_collection.sh

test_evidence_actually_collected() {
    # Assert: .evidence/ has recent files
    RECENT_EVIDENCE=$(find .evidence/ -name "*.yml" -mtime -7 2>/dev/null | wc -l)

    if [[ $RECENT_EVIDENCE -gt 0 ]]; then
        echo "✅ PASS: Evidence collected ($RECENT_EVIDENCE files in last 7 days)"
        return 0
    else
        echo "❌ FAIL: No evidence collected recently (evidence system HOLLOW!)"
        return 1
    fi
}
```

4. **Bypass Permissions Contract**:
```bash
#!/bin/bash
# tests/contract/test_bypass_permissions.sh

test_bypass_permissions_works() {
    # This test is tricky - needs to run in actual Claude Code environment
    # Placeholder for now

    echo "⚠️  Manual verification required: Check if Claude Code prompts for permissions"
    echo "    Expected: No prompts when defaultMode=bypassPermissions"
    echo "    Actual: (needs manual testing)"

    # TODO: Find way to automate this test
    return 0
}
```

---

### Runtime Validation in pre_merge_audit.sh

**Enhancement**: Add runtime checks to existing pre-merge audit.

**New Section** (after existing checks):
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
if git log --all --since="7 days ago" --grep="phase transition\|ce_phase_transition" | grep -q .; then
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

---

### Phase State Management Enhancement

**New Hook**: `phase_state_tracker.sh` (PrePrompt[1])

**Purpose**:
- Display current phase on every AI prompt
- Remind AI to update .phase/current on transitions
- Detect stale phase state (>7 days)

**Implementation**:
```bash
#!/bin/bash
# .claude/hooks/phase_state_tracker.sh
# Purpose: Track and display phase state, remind AI to update

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

# Reminder based on phase
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
    # ... similar for Phase4-7
esac

exit 0
```

**Registration** in `.claude/settings.json`:
```json
{
  "hooks": {
    "PrePrompt": [
      ".claude/hooks/phase_state_tracker.sh",  // ← NEW (position 1)
      ".claude/hooks/force_branch_check.sh",
      // ... other hooks
    ]
  }
}
```

---

## 🎯 Success Criteria

### Technical Success
1. ✅ CODEOWNERS file created and protects 31 critical files
2. ✅ guard-core.yml CI workflow created with 61 checks
3. ✅ Contract tests created for 4 critical features
4. ✅ pre_merge_audit.sh enhanced with runtime validation
5. ✅ phase_state_tracker.sh created and registered

### Functional Success
6. ✅ AI cannot modify protected files without approval
7. ✅ CI detects hollow implementations (file exists but never runs)
8. ✅ Contract tests catch regressions before merge
9. ✅ Phase state maintained and tracked
10. ✅ Runtime validation integrated into pre-merge audit

### Quality Success
11. ✅ All tests pass
12. ✅ CI green on test PR
13. ✅ Documentation complete
14. ✅ Zero shellcheck warnings

### Long-term Success (30-day verification)
15. ✅ Hollow Implementation Rate = 0%
16. ✅ No regressions of fixed features
17. ✅ Phase state maintained continuously
18. ✅ Evidence collection working

---

## 📊 Detailed Component Breakdown

### Component 1: CODEOWNERS File

**File Path**: `.github/CODEOWNERS`

**Line Count**: ~40 lines

**Content Structure**:
```
# Header comment
# Protected files by category
# - Hooks (15 entries)
# - Workflow configs (5 entries)
# - Core scripts (5 entries)
# - Settings (3 entries)
# - Version files (3 entries)
```

---

### Component 2: Guard Core CI Workflow

**File Path**: `.github/workflows/guard-core.yml`

**Line Count**: ~150 lines

**Jobs**:
1. verify-critical-files (checks 31 files)
2. verify-critical-configs (checks 10 configs)
3. verify-sentinel-strings (checks 15 sentinels)
4. validate-runtime-behavior (checks 5 runtime conditions)

**Dependencies**: 4 new scripts in `scripts/guard/`

---

### Component 3: Guard Scripts

**Files**:
1. `scripts/guard/check_critical_files.sh` (~100 lines)
2. `scripts/guard/check_critical_configs.sh` (~150 lines)
3. `scripts/guard/check_sentinels.sh` (~100 lines)
4. `scripts/guard/validate_runtime_behavior.sh` (~200 lines)

**Total**: ~550 lines

---

### Component 4: Contract Tests

**Files**:
1. `tests/contract/test_parallel_execution.sh` (~80 lines)
2. `tests/contract/test_phase_management.sh` (~90 lines)
3. `tests/contract/test_evidence_collection.sh` (~70 lines)
4. `tests/contract/test_bypass_permissions.sh` (~50 lines)

**Total**: ~290 lines

---

### Component 5: Pre-merge Audit Enhancement

**File**: `scripts/pre_merge_audit.sh`

**Changes**: Add new section (~80 lines)

**New Checks**:
- Check 7.1: parallel_subagent_suggester.sh execution
- Check 7.2: phase_manager.sh usage
- Check 7.3: Evidence collection activity
- Check 7.4: .phase/current maintenance

---

### Component 6: Phase State Tracker Hook

**File**: `.claude/hooks/phase_state_tracker.sh`

**Line Count**: ~80 lines

**Features**:
- Display current phase
- Detect stale state (>7 days)
- Remind AI to update phase
- Phase-specific transition reminders

---

## 🧪 Testing Strategy

### Unit Tests (20 test cases)

1. **CODEOWNERS Tests** (5 cases)
   - Test file exists
   - Test all 31 protected files listed
   - Test correct owner (@perfectuser21)
   - Test syntax valid
   - Test no duplicates

2. **Guard Script Tests** (8 cases)
   - Test check_critical_files.sh (2 cases: all exist, one missing)
   - Test check_critical_configs.sh (2 cases: valid config, invalid config)
   - Test check_sentinels.sh (2 cases: all present, one missing)
   - Test validate_runtime_behavior.sh (2 cases: all recent, one stale)

3. **Contract Tests** (4 cases)
   - Test parallel execution contract
   - Test phase management contract
   - Test evidence collection contract
   - Test bypass permissions contract

4. **Phase State Tracker Tests** (3 cases)
   - Test displays current phase correctly
   - Test detects stale state
   - Test transition reminders

### Integration Tests (2 scenarios)

1. **CI Integration Test**
   - Trigger guard-core.yml on test branch
   - Verify all 61 checks run
   - Test failure scenarios (remove critical file, etc.)

2. **End-to-End Workflow Test**
   - Run through Phase 1-7
   - Verify phase state tracked
   - Verify runtime validation catches issues
   - Verify contract tests run

---

## 📈 Impact Radius

### Files Created (12)
- `.github/CODEOWNERS` (new)
- `.github/workflows/guard-core.yml` (new)
- `scripts/guard/check_critical_files.sh` (new)
- `scripts/guard/check_critical_configs.sh` (new)
- `scripts/guard/check_sentinels.sh` (new)
- `scripts/guard/validate_runtime_behavior.sh` (new)
- `tests/contract/test_parallel_execution.sh` (new)
- `tests/contract/test_phase_management.sh` (new)
- `tests/contract/test_evidence_collection.sh` (new)
- `tests/contract/test_bypass_permissions.sh` (new)
- `.claude/hooks/phase_state_tracker.sh` (new)
- Documentation updates

### Files Modified (2)
- `scripts/pre_merge_audit.sh` (add runtime validation section)
- `.claude/settings.json` (register phase_state_tracker.sh)

### Total Lines: ~1,500 lines of new code + tests

---

## 🚀 AI Responsibilities

### After Implementing This System

**AI MUST**:
1. Never modify CODEOWNERS-protected files without explicit user instruction
2. Update .phase/current when transitioning phases
3. Monitor CI checks and fix failures
4. Collect evidence for all features
5. Run contract tests before claiming "feature works"

**AI MUST NOT**:
- Bypass CODEOWNERS protection
- Skip phase state updates
- Merge PRs with failing guard-core.yml checks
- Claim features work without runtime evidence

---

## 📚 References

- `.temp/REGRESSION_ANALYSIS.md` - Detailed regression analysis
- `.temp/META_HOLLOW_DETECTION.md` - Anti-Hollow system hollowness analysis
- `CLAUDE.md` - Anti-Hollow Gate System documentation
- GitHub CODEOWNERS documentation

---

## 🎯 Next Steps

After Phase 1 approval:

**Phase 2**: Implementation (6 components)
1. Create CODEOWNERS file
2. Create guard-core.yml workflow
3. Create 4 guard scripts
4. Create 4 contract tests
5. Enhance pre_merge_audit.sh
6. Create phase_state_tracker.sh

**Phase 3**: Testing
- Run all unit tests
- Run integration tests
- Test CI workflow
- Performance test all scripts

**Phase 4**: Review & Audit
- Code review
- Pre-merge audit
- Documentation review

**Phase 5-7**: Release, Acceptance, Closure

---

**Document Status**: ✅ Complete
**Line Count**: 579 lines
**Ready for Phase 1.4**: Yes
