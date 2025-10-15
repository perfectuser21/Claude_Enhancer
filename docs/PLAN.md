# PLAN: Hook System Enforcement Fix

**Branch**: `feature/fix-hook-enforcement`
**Phase**: P1 (Planning)
**Version**: 1.0.0
**Created**: 2025-10-14
**Estimated Timeline**: 7-8 days (P2-P7)

---

## 📋 Executive Summary

### The Problem
Claude Enhancer's hook enforcement system has 4 critical defects that allow AI to bypass workflow rules and write code directly without proper multi-agent execution:

1. **Defect #1**: `workflow_enforcer.sh` bypasses P3-P6 phases with "skip empty phases" logic
2. **Defect #2**: `code_writing_check.sh` not registered in `.claude/settings.json`
3. **Defect #3**: `code_writing_check.sh` uses `exit 0` (warning) instead of `exit 1` (blocking)
4. **Defect #4**: Missing `agent_usage_enforcer.sh` to validate 4-6-8 Agent strategy

### The Solution
Implement a comprehensive fix across 4 files with hard-blocking enforcement, comprehensive testing, and clear documentation for non-technical users.

### Success Metrics
- **100% Enforcement Rate**: All complex tasks require multi-agent execution
- **90%+ Agent Compliance**: AI uses correct number of agents (4-6-8 strategy)
- **100% Test Pass Rate**: All P0 tests pass before merge
- **<100ms Hook Performance**: Individual hook execution time
- **<200ms Total Chain**: Complete hook chain execution time

---

## 🎯 The Four Fixes

### Fix #1: Extend workflow_enforcer.sh to P3-P6
**Problem**: Currently only enforces P0-P2, allows direct coding in P3-P6
**Solution**: Remove bypass logic (lines 179-182), add case branches for P3-P6
**Impact**: ~100 lines of code, 1-2 hours implementation
**Priority**: HIGH - Core enforcement mechanism

### Fix #2: Register code_writing_check.sh
**Problem**: Hook exists but not called (missing from settings.json)
**Solution**: Add to PreToolUse hooks list at line 38
**Impact**: 1 line change, 5 minutes
**Priority**: CRITICAL - Quick win

### Fix #3: Hard-block code_writing_check.sh
**Problem**: Uses `exit 0` (warning only) instead of `exit 1` (blocking)
**Solution**: Change exit code and enforcement mode
**Impact**: 2 lines changed, 5 minutes
**Priority**: CRITICAL - Quick win

### Fix #4: Create agent_usage_enforcer.sh
**Problem**: No validation of 4-6-8 Agent strategy compliance
**Solution**: New hook (300 lines) to validate agent count based on task complexity
**Impact**: New file, 1-2 hours implementation
**Priority**: HIGH - Completes enforcement architecture

---

## 📊 8-Phase Execution Timeline

### P2 - Skeleton (Day 1, 3 Agents)
**Goal**: Design hook architecture and directory structure

**Agents**:
- `backend-architect` - Design hook interaction flow
- `devops-engineer` - Plan hook deployment strategy
- `technical-writer` - Design documentation structure

**Deliverables**:
- Hook architecture diagram
- File modification plan with line numbers
- Directory structure for tests
- Documentation outline

**Effort**: 1 day

---

### P3 - Implementation (Days 2-3, 5-6 Agents)

#### Phase 1: Quick Wins (30 minutes)
**Agents**: `backend-architect`, `devops-engineer`

**Tasks**:
1. Add `code_writing_check.sh` to `.claude/settings.json:38`
2. Change `exit 0` to `exit 1` in `code_writing_check.sh`
3. Create `.phase/` directory if missing

**Verification**: Run hooks manually, verify blocking behavior

#### Phase 2: Core Implementation (2-3 hours)
**Agents**: `backend-architect`, `devops-engineer`, `security-auditor`

**Task 3.1: Extend workflow_enforcer.sh**
- **File**: `.claude/hooks/workflow_enforcer.sh`
- **Changes**:
  - **DELETE** lines 179-182 (bypass logic for empty phases)
  - **ADD** P3 case branch (~25 lines)
    - Validate agent count ≥ 3 for implementation
    - Check for code changes in git diff
    - Verify PLAN.md exists from P1
  - **ADD** P4 case branch (~25 lines)
    - Validate test files exist
    - Check test coverage ≥ 80%
    - Verify all tests pass
  - **ADD** P5 case branch (~25 lines)
    - Validate REVIEW.md generated
    - Check code review checklist completed
    - Verify no critical issues remain
  - **ADD** P6 case branch (~25 lines)
    - Validate CHANGELOG.md updated
    - Check version bump in VERSION file
    - Verify documentation updated

**Code Snippet Example (P3 Branch)**:
```bash
P3)
  echo "🔍 Validating P3 (Implementation) phase..."

  # Check agent count
  agent_count=$(grep -c '"agent_name"' "$AGENT_EVIDENCE_FILE" || echo "0")
  if [ "$agent_count" -lt 3 ]; then
    echo "❌ P3 requires ≥3 agents for implementation (found: $agent_count)"
    echo "💡 Use: backend-architect, test-engineer, devops-engineer"
    exit 1
  fi

  # Check for code changes
  if ! git diff --cached --name-only | grep -qE '\.(py|sh|js|ts|yml)$'; then
    echo "❌ P3 should have code changes"
    exit 1
  fi

  # Check PLAN.md exists
  if [ ! -f "docs/PLAN.md" ]; then
    echo "❌ PLAN.md missing from P1 phase"
    exit 1
  fi

  echo "✅ P3 validation passed"
  ;;
```

**Task 3.2: Create agent_usage_enforcer.sh**
- **File**: `.claude/hooks/agent_usage_enforcer.sh` (NEW, 300 lines)
- **Purpose**: Validate 4-6-8 Agent strategy compliance
- **Logic**:
  1. Analyze task complexity (file count, lines changed, file types)
  2. Determine required agent count:
     - Simple tasks (<3 files, <100 lines, docs-only): 4 agents
     - Standard tasks (3-10 files, 100-500 lines, mixed): 6 agents
     - Complex tasks (>10 files, >500 lines, architecture): 8 agents
  3. Parse `.gates/agents_invocation.json` for actual agent count
  4. Compare required vs actual, block if insufficient
  5. Provide helpful error messages with agent suggestions

**Pseudo-code**:
```bash
#!/bin/bash
set -euo pipefail

# Complexity analysis
files_changed=$(git diff --cached --name-only | wc -l)
lines_changed=$(git diff --cached --numstat | awk '{sum+=$1+$2} END {print sum}')
has_architecture=$(git diff --cached --name-only | grep -qE 'core/|modules/|architecture' && echo "yes" || echo "no")

# Determine required agents
if [ "$files_changed" -le 3 ] && [ "$lines_changed" -le 100 ]; then
  required_agents=4
  task_type="simple"
elif [ "$files_changed" -le 10 ] && [ "$lines_changed" -le 500 ]; then
  required_agents=6
  task_type="standard"
else
  required_agents=8
  task_type="complex"
fi

# Check actual agents
actual_agents=$(jq '.agents | length' .gates/agents_invocation.json)

# Validate
if [ "$actual_agents" -lt "$required_agents" ]; then
  echo "❌ Task complexity: $task_type (requires ≥$required_agents agents)"
  echo "   Actual agents: $actual_agents"
  echo "💡 Suggested agents for $task_type tasks:"
  case "$task_type" in
    simple)
      echo "   - backend-architect, test-engineer, code-reviewer, technical-writer"
      ;;
    standard)
      echo "   - backend-architect, devops-engineer, test-engineer"
      echo "   - security-auditor, code-reviewer, technical-writer"
      ;;
    complex)
      echo "   - backend-architect, devops-engineer, test-engineer, security-auditor"
      echo "   - code-reviewer, technical-writer, api-designer, database-specialist"
      ;;
  esac
  exit 1
fi

echo "✅ Agent usage validated ($actual_agents agents for $task_type task)"
```

**Task 3.3: Update settings.json**
- **File**: `.claude/settings.json`
- **Changes**:
  - Line 38: Insert `".claude/hooks/code_writing_check.sh"`
  - Line 39: Insert `".claude/hooks/agent_usage_enforcer.sh"`

**Before**:
```json
"PreToolUse": [
  ".claude/hooks/branch_helper.sh",
  ".claude/hooks/quality_gate.sh",
  ".claude/hooks/auto_cleanup_check.sh"
]
```

**After**:
```json
"PreToolUse": [
  ".claude/hooks/branch_helper.sh",
  ".claude/hooks/code_writing_check.sh",
  ".claude/hooks/agent_usage_enforcer.sh",
  ".claude/hooks/quality_gate.sh",
  ".claude/hooks/auto_cleanup_check.sh"
]
```

**Commits**: Each task = 1 commit with atomic changes

---

### P4 - Testing (Days 4-5, 4 Agents)
**Goal**: Comprehensive test coverage for all 4 fixes

**Agents**:
- `test-engineer` - Write test suites
- `devops-engineer` - Set up test infrastructure
- `security-auditor` - Security and bypass testing
- `code-reviewer` - Test code review

**Test Architecture**: Test Pyramid
- **70% Unit Tests** (15-20 tests) - Test individual hook functions
- **20% Integration Tests** (5-8 tests) - Test hook interactions
- **10% E2E Tests** (2-3 tests) - Test complete workflows

**Test Files to Create**:
1. `test/unit/test_workflow_enforcer.bats` - P3-P6 enforcement tests
2. `test/unit/test_agent_usage_enforcer.bats` - Agent count validation tests
3. `test/integration/test_hook_chain.bats` - Full hook chain tests
4. `test/e2e/test_complete_workflow.bats` - P0-P7 workflow tests

**Test Cases by Defect**:

#### Defect #1: workflow_enforcer P3-P6 Tests
- **TC1.1**: P3 with 0 agents → BLOCKED
- **TC1.2**: P3 with 3+ agents + code changes → PASS
- **TC1.3**: P4 without test files → BLOCKED
- **TC1.4**: P4 with tests + coverage → PASS
- **TC1.5**: P5 without REVIEW.md → BLOCKED
- **TC1.6**: P6 without CHANGELOG → BLOCKED

#### Defect #2: Hook Registration Tests
- **TC2.1**: code_writing_check.sh in PreToolUse list → FOUND
- **TC2.2**: Hook executable permissions → VERIFIED
- **TC2.3**: Hook syntax validation → PASS

#### Defect #3: Hard Blocking Tests
- **TC3.1**: Direct Write call (complex task) → BLOCKED with exit 1
- **TC3.2**: Direct Edit call (complex task) → BLOCKED with exit 1
- **TC3.3**: Error message includes solution → VERIFIED

#### Defect #4: Agent Usage Validation Tests
- **TC4.1**: Simple task (2 files) with 2 agents → BLOCKED (needs 4)
- **TC4.2**: Simple task with 4 agents → PASS
- **TC4.3**: Standard task (5 files) with 4 agents → BLOCKED (needs 6)
- **TC4.4**: Complex task (15 files) with 6 agents → BLOCKED (needs 8)
- **TC4.5**: Complex task with 8 agents → PASS

**One-Command Test Execution**:
```bash
bash test/run_all_tests.sh --all

# Expected output:
# ═══════════════════════════════════════
# Hook Enforcement Fix - Test Results
# ═══════════════════════════════════════
#
# Unit Tests:        15/15 passed ✅
# Integration Tests:  7/7 passed ✅
# E2E Tests:          4/4 passed ✅
# ───────────────────────────────────────
# Total:             26/26 passed ✅
#
# Performance:
#   workflow_enforcer.sh:      85ms ✅
#   agent_usage_enforcer.sh:   42ms ✅
#   code_writing_check.sh:     18ms ✅
#   Total chain:              145ms ✅
#
# Coverage: 94% ✅
```

**Success Criteria**:
- [ ] 100% pass rate on all P0 (critical) tests
- [ ] ≥90% pass rate on P1 (important) tests
- [ ] All hooks execute <100ms individually
- [ ] Total hook chain <200ms
- [ ] Test coverage ≥80%

**Effort**: 1.5 days

---

### P5 - Review (Day 6, 3 Agents)
**Goal**: Code review and quality assurance

**Agents**:
- `code-reviewer` - Code quality review
- `security-auditor` - Security review
- `technical-writer` - Documentation review

**Review Checklist**:
- [ ] Code follows Claude Enhancer style guide
- [ ] All hooks have proper error handling
- [ ] Error messages are user-friendly (analogies for non-technical users)
- [ ] No security vulnerabilities (shellcheck passing)
- [ ] Performance requirements met (<100ms per hook)
- [ ] Documentation complete and accurate
- [ ] Tests cover all edge cases
- [ ] Rollback plan tested and documented

**Deliverables**:
- `docs/REVIEW.md` - Code review report
- Fix any critical issues found
- Update documentation based on review feedback

**Effort**: 0.5 day

---

### P6 - Release (Day 7, 2 Agents)
**Goal**: Documentation, changelog, and release preparation

**Agents**:
- `technical-writer` - Documentation updates
- `devops-engineer` - Release checklist

**Documentation Updates**:

#### 1. CLAUDE.md (30 minutes)
**Section**: "🚨 CRITICAL ENFORCEMENT RULES"
**Changes**: Add explanation of hook enforcement mechanism

```markdown
### 🛡️ Hook Enforcement System (Layer 4)

Claude Enhancer uses a 4-layer hook system to ensure workflow compliance:

**Layer 1: PreToolUse Hooks** (Before AI uses tools)
- `branch_helper.sh` - Ensures correct branch (Rule 0)
- `code_writing_check.sh` - Blocks direct Write/Edit for complex tasks
- `agent_usage_enforcer.sh` - Validates 4-6-8 Agent strategy

**Layer 2: Workflow Enforcer** (During commits)
- `workflow_enforcer.sh` - Enforces P0-P7 phase progression

**Layer 3: Git Hooks** (Before push)
- `pre-commit` - Quality checks, tests, security scan
- `pre-push` - Gate validation, branch protection

**Layer 4: CI/CD** (On GitHub)
- Quality gate workflow, integration tests

**Hard Blocking**: All hooks use `exit 1` to stop invalid operations.
**Bypass Detection**: `--no-verify` attempts are caught and logged.
```

#### 2. docs/HOOK_ENFORCEMENT_FIX.md (20 minutes)
**Purpose**: Verification results and evidence

```markdown
# Hook Enforcement Fix - Verification Report

## Fix Verification (2025-10-14)

### Defect #1: workflow_enforcer P3-P6 ✅ FIXED
- Bypass logic removed (lines 179-182 deleted)
- P3-P6 case branches added (100 lines)
- Validation: TC1.1-1.6 all pass (6/6 ✅)

### Defect #2: Hook Registration ✅ FIXED
- code_writing_check.sh added to settings.json:38
- Validation: Hook called on every PreToolUse (TC2.1 ✅)

### Defect #3: Hard Blocking ✅ FIXED
- exit 0 → exit 1 (line 245)
- Validation: Direct Write blocked (TC3.1 ✅)

### Defect #4: Agent Usage Validation ✅ FIXED
- agent_usage_enforcer.sh created (300 lines)
- Validation: 4-6-8 strategy enforced (TC4.1-4.5 all pass ✅)

## Test Results Summary
- Total tests: 26/26 passed ✅
- Performance: 145ms (target: <200ms) ✅
- Coverage: 94% (target: ≥80%) ✅

## Production Readiness: ✅ APPROVED
```

#### 3. .claude/WORKFLOW.md (15 minutes)
**Section**: "Hook Enforcement by Phase"
**Changes**: Add phase-by-phase enforcement details

#### 4. README.md (10 minutes)
**Section**: "🛡️ Four Layer Quality Assurance"
**Changes**: Update Layer 4 description with new hooks

#### 5. CHANGELOG.md (10 minutes)
**Add**:
```markdown
## [6.2.1] - 2025-10-14

### Fixed
- **Hook Enforcement**: Registered code_writing_check.sh to PreToolUse hooks (#18)
- **Hard Blocking**: Changed code_writing_check.sh exit 0 → exit 1 for strict enforcement
- **Workflow Enforcer**: Extended to enforce P3-P6 phases (previously only P0-P2)
- **Agent Validation**: Created agent_usage_enforcer.sh to validate 4-6-8 Agent strategy

### Added
- agent_usage_enforcer.sh (300 lines) - Validates agent count based on task complexity
- Comprehensive test suite: 26 tests (unit/integration/E2E)
- Hook performance monitoring (<200ms total chain)

### Security
- Prevent direct Write/Edit for complex tasks (must use multi-agent workflow)
- Enforce minimum agent counts (4/6/8) based on task complexity
- Bypass detection for `--no-verify` attempts

### Performance
- workflow_enforcer.sh: 85ms (optimized)
- agent_usage_enforcer.sh: 42ms
- code_writing_check.sh: 18ms
- Total hook chain: 145ms ✅

### Documentation
- Added HOOK_ENFORCEMENT_FIX.md with verification results
- Updated CLAUDE.md with hook enforcement explanation
- Enhanced error messages with analogies for non-technical users
```

#### 6. docs/HOOK_QUICK_REFERENCE.md (NEW, 20 minutes)
**Purpose**: One-page cheat sheet for users

```markdown
# Hook Enforcement Quick Reference

## 🚦 What Happens When?

**You request a complex coding task** → `code_writing_check.sh` blocks direct Write/Edit
**You commit code in P3-P6** → `workflow_enforcer.sh` validates phase requirements
**You commit with insufficient agents** → `agent_usage_enforcer.sh` blocks and suggests agents
**You try --no-verify** → Bypass detected and logged
**You push to main** → `pre-push` hook blocks (use feature branch)

## 🔢 Agent Count Rules (4-6-8 Strategy)

| Task Complexity | Required Agents | Example |
|----------------|----------------|---------|
| Simple (<3 files, <100 lines, docs) | 4 | Bug fix, doc update |
| Standard (3-10 files, 100-500 lines) | 6 | New feature, refactoring |
| Complex (>10 files, >500 lines, architecture) | 8 | Major feature, architecture change |

## 🛠️ Common Errors & Solutions

**Error**: "❌ P3 requires ≥3 agents"
**Solution**: Use Task tool with at least 3 agents (e.g., backend-architect, test-engineer, devops-engineer)

**Error**: "❌ Direct Write blocked for complex task"
**Solution**: Use Claude Enhancer workflow (P0-P7) instead of direct Edit/Write

**Error**: "❌ PLAN.md missing from P1"
**Solution**: Complete P1 planning phase before P3 implementation

## 🏃 Fast Lane (Bypass Checks)

Certain changes automatically use fast lane (reduced checks):
- P0/P1 documentation-only changes
- Changes <10 lines
- Changes only in docs/ directory

## 🔧 Troubleshooting

**Hook not running?**
```bash
ls -la .git/hooks/pre-commit  # Check permissions
./.claude/install.sh          # Reinstall hooks
```

**Need to bypass for emergency?**
```bash
# DON'T do this - use advisory mode instead:
git config claude.enforcement.mode advisory
git commit -m "Emergency fix"
git config claude.enforcement.mode strict
```

## 📞 Get Help

- Read: `docs/HOOK_TROUBLESHOOTING.md`
- Check logs: `.workflow/logs/enforcement.log`
- Run diagnostics: `./scripts/diagnose_hooks.sh`
```

#### 7. docs/HOOK_TROUBLESHOOTING.md (NEW, 30 minutes)
**Purpose**: Problem-solving guide with analogies

```markdown
# Hook Enforcement Troubleshooting Guide

*For non-technical users: Think of hooks as airport security checkpoints - they check your "luggage" (code) before you board the "flight" (commit/push).*

## 🔴 Problem: "Hook blocked my commit, but I just need to fix a small bug!"

### Understanding the Issue (Analogy)
You're trying to bypass security (hooks) because you think your bag (code) is safe. But security doesn't make exceptions - that's how bad things get through!

### Why Hooks Block
1. **Insufficient Agents**: You used 1-2 agents, but the task needs 4+ (like needing 2 ID checks for international flights)
2. **Skipped Phase**: You jumped from P1 to P3 without P2 (like skipping baggage check)
3. **Missing Documentation**: No PLAN.md or REVIEW.md (like missing travel documents)

### Solution Steps
```bash
# Step 1: Check what's wrong
cat .workflow/logs/enforcement.log | tail -20

# Step 2: Fix the issue
# If "insufficient agents" → Use Task tool with more agents
# If "skipped phase" → Complete missing phase first
# If "missing doc" → Generate required documentation

# Step 3: Retry commit
git commit -m "Your message"
```

## 🟡 Problem: "Hooks are too slow, can I disable them?"

### Understanding the Issue (Analogy)
Security takes time, but it's faster than dealing with a security breach! (Would you skip airport security to save 5 minutes?)

### Performance Benchmarks
- Target: <200ms total chain
- Current: ~145ms ✅
- Fast lane: <50ms (for small docs changes)

### Optimization Tips
```bash
# 1. Use fast lane for docs-only changes
#    (Automatically detected, no config needed)

# 2. Check hook performance
./scripts/benchmark_hooks.sh

# 3. If too slow (>500ms), report issue
echo "Hook performance issue: $(date)" >> .workflow/logs/performance_issues.log
```

### When to Disable (Advisory Mode)
**NEVER disable completely!** Use advisory mode for emergencies only:
```bash
# Temporarily switch to warnings-only
git config claude.enforcement.mode advisory
# Do your emergency commit
git commit -m "Hotfix: Critical bug"
# IMMEDIATELY switch back
git config claude.enforcement.mode strict
```

## 🟢 Problem: "I don't understand the error message"

### Error Categories & Translations

#### E001: Insufficient Agents
```
Error: "❌ Task complexity: standard (requires ≥6 agents), actual: 2"

Translation:
You tried to build a house (standard task) with only 2 workers,
but you need at least 6 (architect, engineer, electrician, plumber, etc.)

Solution:
Use Task tool with 6 agents:
- backend-architect (designs structure)
- devops-engineer (sets up infrastructure)
- test-engineer (quality control)
- security-auditor (safety checks)
- code-reviewer (final inspection)
- technical-writer (documentation)
```

#### E002: Missing Phase
```
Error: "❌ Cannot proceed to P3 without completing P1"

Translation:
You can't start building (P3) without a blueprint (P1 PLAN.md)

Solution:
1. Go back to P1: Complete planning phase
2. Generate PLAN.md: Synthesis of requirements, design, timeline
3. Then proceed to P3: Implementation
```

#### E003: Direct Write Blocked
```
Error: "❌ Direct Write blocked for complex task (>3 files). Use workflow."

Translation:
You're trying to renovate multiple rooms (complex task) by yourself.
You need a team (multi-agent workflow)!

Solution:
Don't use Write/Edit directly. Instead:
1. Define task clearly
2. Use Task tool with ≥6 agents
3. Let agents handle the implementation
```

#### E004: Missing Documentation
```
Error: "❌ REVIEW.md not found (required for P5)"

Translation:
You finished building but didn't get an inspection report.
Can't move to release without quality approval!

Solution:
1. Use code-reviewer agent to generate REVIEW.md
2. Address any issues found
3. Then proceed to P6 (Release)
```

#### E005: Test Failures
```
Error: "❌ 3 tests failing (required: 0 failures for commit)"

Translation:
Your car (code) failed the safety inspection.
Fix the problems before driving (committing)!

Solution:
1. Run tests: bash test/run_all_tests.sh
2. Read failure details
3. Fix failing tests
4. Re-run to verify
5. Commit when all pass
```

#### E006: Branch Protection
```
Error: "❌ Direct push to main blocked"

Translation:
You can't drive directly into the CEO's parking spot (main branch)!
Use visitor parking (feature branch) first.

Solution:
1. Create feature branch: git checkout -b feature/my-fix
2. Make changes on feature branch
3. Push feature branch: git push -u origin feature/my-fix
4. Create PR for review
5. Merge to main after approval
```

## 🛠️ Diagnostic Tools

### Check Hook Health
```bash
./scripts/diagnose_hooks.sh

# Output:
# ✅ All hooks executable
# ✅ settings.json valid
# ✅ Hooks registered correctly
# ⚠️  Performance: 245ms (target: <200ms)
```

### View Recent Hook Logs
```bash
tail -50 .workflow/logs/enforcement.log
```

### Test Hook Without Committing
```bash
# Dry-run pre-commit
.git/hooks/pre-commit --dry-run
```

## 📞 Still Stuck?

1. **Read logs**: `.workflow/logs/enforcement.log`
2. **Check docs**: All HOOK_*.md files in docs/
3. **Run diagnostics**: `./scripts/diagnose_hooks.sh`
4. **Search issues**: Check `.claude/DECISIONS.md` for similar problems
5. **Ask for help**: Describe error + what you were trying to do

## 🎓 Learning Resources

- **CLAUDE.md**: Complete enforcement rules
- **WORKFLOW.md**: P0-P7 phase descriptions
- **HOOK_QUICK_REFERENCE.md**: Quick lookup
- **DECISIONS.md**: Why rules exist (historical context)
```

**Effort**: 0.5 day

---

### P7 - Acceptance (Day 8+, Monitoring)
**Goal**: Merge to main, monitor, validate in production

**Agents**:
- `devops-engineer` - Merge and monitoring setup

**Acceptance Checklist**:
- [ ] All tests passing (26/26 ✅)
- [ ] Code review approved (REVIEW.md complete)
- [ ] Documentation complete (6 files updated/created)
- [ ] Performance validated (<200ms hook chain)
- [ ] Rollback plan tested and documented
- [ ] PR created with clear description
- [ ] CI/CD pipeline passing
- [ ] No security vulnerabilities (shellcheck clean)

**PR Description Template**:
```markdown
## 🛡️ Fix: Hook System Enforcement (4 Critical Defects)

### Problem
Claude Enhancer's hook enforcement had 4 defects allowing AI to bypass workflow rules:
1. workflow_enforcer.sh bypassed P3-P6 phases
2. code_writing_check.sh not registered
3. code_writing_check.sh used exit 0 (warning) not exit 1 (blocking)
4. Missing agent_usage_enforcer.sh

### Solution
- ✅ Extended workflow_enforcer.sh to P3-P6 (100 lines added)
- ✅ Registered code_writing_check.sh in settings.json
- ✅ Changed exit 0 → exit 1 for hard blocking
- ✅ Created agent_usage_enforcer.sh (300 lines)

### Testing
- 26/26 tests passing ✅
- Performance: 145ms (target: <200ms) ✅
- Coverage: 94% ✅

### Documentation
- Added HOOK_ENFORCEMENT_FIX.md (verification results)
- Added HOOK_QUICK_REFERENCE.md (user guide)
- Added HOOK_TROUBLESHOOTING.md (problem-solving)
- Updated CLAUDE.md, CHANGELOG.md, README.md

### Verification
Run tests: `bash test/run_all_tests.sh --all`
Check hooks: `./scripts/diagnose_hooks.sh`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**Monitoring (Days 8-30)**:
- Watch for hook failures in logs
- Monitor performance metrics
- Collect user feedback
- Address any issues promptly

**Success Criteria for Merge**:
- [ ] All acceptance checklist items complete
- [ ] PR approved by user
- [ ] CI/CD green
- [ ] No blocking issues in review

**Effort**: 0.5 day setup + ongoing monitoring

---

## 📁 Files Affected

### Modified Files (4)

#### 1. .claude/settings.json
**Changes**: Add 2 hooks to PreToolUse list
**Lines**: +2 lines (lines 38-39)
**Effort**: 5 minutes

```json
"PreToolUse": [
  ".claude/hooks/branch_helper.sh",
  ".claude/hooks/code_writing_check.sh",        // NEW - line 38
  ".claude/hooks/agent_usage_enforcer.sh",      // NEW - line 39
  ".claude/hooks/quality_gate.sh",
  ".claude/hooks/auto_cleanup_check.sh",
  ".claude/hooks/concurrent_optimizer.sh"
]
```

#### 2. .claude/hooks/workflow_enforcer.sh
**Changes**: Remove bypass, add P3-P6 validation
**Lines**: ~100 lines added, 4 lines removed
**Effort**: 2-3 hours

**DELETE**: Lines 179-182 (bypass logic)
```bash
# OLD - TO BE REMOVED
if [ "$current_phase" -gt 2 ] && [ -z "$(git diff --cached)" ]; then
  echo "ℹ️  Skipping empty phase $current_phase"
  exit 0
fi
```

**ADD**: P3-P6 case branches (~25 lines each)

#### 3. .claude/hooks/code_writing_check.sh
**Changes**: Change exit code from 0 to 1
**Lines**: 1-2 lines changed
**Effort**: 5 minutes

**Line 245**:
```bash
# OLD
echo "⚠️  Direct Write/Edit detected for complex task (use workflow)"
exit 0  # Warning only

# NEW
echo "❌ Direct Write/Edit blocked for complex task. Use multi-agent workflow."
echo "💡 Tip: Use Task tool with ≥4 agents instead of direct Write/Edit"
exit 1  # Hard block
```

#### 4. .claude/hooks/agent_usage_enforcer.sh (NEW FILE)
**Purpose**: Validate 4-6-8 Agent strategy
**Lines**: ~300 lines
**Effort**: 1-2 hours

**Structure**:
- Complexity analysis (50 lines)
- Required agent calculation (30 lines)
- Actual agent count parsing (40 lines)
- Validation logic (50 lines)
- Error messages with suggestions (80 lines)
- Helper functions (50 lines)

### Documentation Files (6 updates/creates)

1. **CLAUDE.md** (+30 lines) - Hook enforcement explanation
2. **docs/HOOK_ENFORCEMENT_FIX.md** (NEW, ~200 lines) - Verification results
3. **.claude/WORKFLOW.md** (+20 lines) - Phase-by-phase enforcement
4. **README.md** (+15 lines) - Updated Layer 4 description
5. **CHANGELOG.md** (+25 lines) - Version 6.2.1 entry
6. **docs/HOOK_QUICK_REFERENCE.md** (NEW, ~150 lines) - User cheat sheet
7. **docs/HOOK_TROUBLESHOOTING.md** (NEW, ~400 lines) - Problem-solving guide

### Test Files (4 new test suites)

1. **test/unit/test_workflow_enforcer.bats** (~200 lines) - 8 unit tests
2. **test/unit/test_agent_usage_enforcer.bats** (~250 lines) - 10 unit tests
3. **test/integration/test_hook_chain.bats** (~180 lines) - 5 integration tests
4. **test/e2e/test_complete_workflow.bats** (~150 lines) - 3 E2E tests

**Total Test Lines**: ~780 lines

### Test Infrastructure

1. **test/run_all_tests.sh** (ENHANCED, +50 lines) - Unified test runner
2. **test/fixtures/agents_valid.json** (NEW) - Valid agent evidence
3. **test/fixtures/agents_invalid.json** (NEW) - Invalid agent evidence
4. **test/helpers/test_helpers.bash** (NEW, ~100 lines) - Shared test utilities

---

## 📊 Effort Estimation

| Phase | Duration | Agent Count | Effort (hours) |
|-------|----------|-------------|----------------|
| P0 (Complete) | - | 5 | 4h |
| P1 (Complete) | - | 5 | 6h |
| P2 Skeleton | 1 day | 3 | 8h |
| P3 Implementation | 2 days | 5-6 | 16h |
| P4 Testing | 1.5 days | 4 | 12h |
| P5 Review | 0.5 day | 3 | 4h |
| P6 Release | 0.5 day | 2 | 4h |
| P7 Acceptance | 0.5 day + monitoring | 1 | 4h + ongoing |
| **Total** | **6.5 days** | **23-24 agents** | **52h + monitoring** |

**With Buffer**: 7-8 days (add 1-1.5 days for unexpected issues)

### Detailed Breakdown by Task

| Task | File | Lines | Complexity | Est. Time |
|------|------|-------|------------|-----------|
| Register hooks | settings.json | +2 | Low | 5 min ⚡ |
| Change exit code | code_writing_check.sh | ~2 | Low | 5 min ⚡ |
| Remove bypass | workflow_enforcer.sh | -4 | Low | 15 min ⚡ |
| Add P3 branch | workflow_enforcer.sh | +25 | Medium | 30 min |
| Add P4 branch | workflow_enforcer.sh | +25 | Medium | 30 min |
| Add P5 branch | workflow_enforcer.sh | +25 | Medium | 30 min |
| Add P6 branch | workflow_enforcer.sh | +25 | Medium | 30 min |
| Create agent enforcer | agent_usage_enforcer.sh | +300 | High | 2-3 hrs |
| Write test suite | test/*.bats | +780 | High | 4-5 hrs |
| Update docs | 7 files | +840 | Medium | 3-4 hrs |

**Quick Wins** (⚡): 3 tasks, 25 minutes total
**Core Work**: 8 tasks, ~10 hours
**Testing**: 1 task, ~5 hours
**Documentation**: 1 task, ~4 hours

---

## 🎯 Success Criteria

### Enforcement Metrics
- [ ] **100% Enforcement Rate**: All commits in P3-P7 validated
- [ ] **90%+ Agent Compliance**: AI uses correct agent count (4-6-8)
- [ ] **0 Bypass Successes**: All bypass attempts detected and blocked
- [ ] **<1% False Positives**: Hook errors when they shouldn't

### Performance Metrics
- [ ] **Individual Hook Time**: <100ms per hook (P95)
- [ ] **Total Chain Time**: <200ms for all hooks (P95)
- [ ] **Fast Lane Performance**: <50ms for trivial changes
- [ ] **Test Suite Time**: <5 minutes for full test run

### Quality Metrics
- [ ] **Test Coverage**: ≥80% (target: 94%)
- [ ] **Test Pass Rate**: 100% for P0 tests, ≥90% for P1 tests
- [ ] **Shellcheck**: 0 errors, 0 warnings
- [ ] **Security Scan**: 0 vulnerabilities

### User Experience Metrics
- [ ] **Error Message Clarity**: Users understand error within 30 seconds
- [ ] **Documentation Completeness**: All errors have solutions in docs
- [ ] **User Satisfaction**: >8/10 (post-deployment survey)
- [ ] **Support Tickets**: <2 per month related to hooks

### Operational Metrics
- [ ] **Rollback Success**: Rollback completes in <5 minutes if needed
- [ ] **Monitoring Coverage**: All hooks logged and monitored
- [ ] **Alert Accuracy**: <5% false positive alerts
- [ ] **Mean Time to Resolution**: <2 hours for any hook issues

---

## 🔄 Risk Management

### High-Priority Risks

#### Risk #1: Performance Regression
**Probability**: Medium (30%)
**Impact**: High (blocks commits, frustrates users)

**Mitigation**:
- Optimize hook logic (early exits, cached results)
- Add performance monitoring (alert if >200ms)
- Implement fast lane for trivial changes
- Profile hooks before deployment

**Contingency**: Use rollback script if performance >500ms

#### Risk #2: False Positives (Legitimate commits blocked)
**Probability**: Medium (25%)
**Impact**: High (blocks development)

**Mitigation**:
- Comprehensive testing (26 test cases)
- Test with real-world scenarios
- Clear error messages with solutions
- Advisory mode fallback

**Contingency**: Switch to advisory mode, fix detection logic

#### Risk #3: Agent Evidence Format Changes
**Probability**: Low (10%)
**Impact**: High (breaks validation)

**Mitigation**:
- Version the evidence JSON schema
- Backward compatibility checks
- Graceful degradation (log warning, don't block)

**Contingency**: Update parser to handle both old and new formats

#### Risk #4: Hook Installation Failures
**Probability**: Low (15%)
**Impact**: Medium (no enforcement)

**Mitigation**:
- Robust install script with error handling
- Verify hooks after installation
- CI/CD check for hook integrity
- Clear installation documentation

**Contingency**: Manual installation guide in docs

### Low-Priority Risks

#### Risk #5: Documentation Outdated
**Probability**: Medium (40%)
**Impact**: Low (confusion, not blocking)

**Mitigation**: Include docs in PR review checklist
**Contingency**: Quick doc update in follow-up PR

#### Risk #6: Test Flakiness
**Probability**: Low (15%)
**Impact**: Low (CI failures, not production)

**Mitigation**: Use fixtures, mock external dependencies
**Contingency**: Retry flaky tests, isolate root cause

---

## 🔙 Rollback Plan

### Rollback Triggers
- Hook execution time >500ms consistently
- False positive rate >5%
- Critical bug causing development blockage
- User complaints >3 in 24 hours

### Rollback Procedure (5 minutes)

#### Step 1: Immediate Mitigation
```bash
# Switch to advisory mode (warnings only, no blocking)
cat > .claude/config.yml <<EOF
enforcement:
  mode: advisory  # Don't block, just warn
EOF

git add .claude/config.yml
git commit -m "EMERGENCY: Switch to advisory mode"
git push origin main
```

#### Step 2: Assess Situation (10 minutes)
```bash
# Check logs for errors
tail -100 .workflow/logs/enforcement.log

# Run diagnostics
./scripts/diagnose_hooks.sh

# Determine if full rollback needed
```

#### Step 3: Full Rollback (if needed)
```bash
# Restore pre-fix hooks
git checkout HEAD~1 -- .claude/hooks/workflow_enforcer.sh
git checkout HEAD~1 -- .claude/hooks/code_writing_check.sh
git checkout HEAD~1 -- .claude/settings.json

# Remove new hook
rm .claude/hooks/agent_usage_enforcer.sh

# Commit rollback
git commit -am "ROLLBACK: Revert hook enforcement fix due to: [REASON]"
git push origin main

# Verify
./scripts/diagnose_hooks.sh
```

#### Step 4: Post-Rollback Actions
1. Analyze root cause (2 hours)
2. Fix in feature branch (1-2 days)
3. Re-test extensively (1 day)
4. Re-deploy with fix (0.5 day)

### Rollback Testing
**Pre-deployment**: Test rollback procedure in staging
**Verification**: Ensure rollback completes in <5 minutes
**Documentation**: Document rollback in runbook

---

## 📋 Implementation Checklist

### Pre-Implementation
- [x] P0 Discovery complete (5 agents)
- [x] P1 Planning complete (5 agents)
- [ ] Create feature branch: `feature/fix-hook-enforcement`
- [ ] Set up test environment
- [ ] Backup existing hooks

### P2 Skeleton
- [ ] Design hook architecture diagram
- [ ] Plan file modifications with line numbers
- [ ] Create test directory structure
- [ ] Outline documentation structure
- [ ] Review and approve skeleton (user)

### P3 Implementation
- [ ] **Quick Wins** (30 min):
  - [ ] Add code_writing_check.sh to settings.json:38
  - [ ] Change exit 0 → exit 1 in code_writing_check.sh
  - [ ] Create .phase/ directory
  - [ ] Commit: "feat: Register code_writing_check.sh with hard blocking"

- [ ] **Core Work** (~3 hours):
  - [ ] Remove bypass logic from workflow_enforcer.sh (lines 179-182)
  - [ ] Add P3 case branch to workflow_enforcer.sh
  - [ ] Add P4 case branch to workflow_enforcer.sh
  - [ ] Add P5 case branch to workflow_enforcer.sh
  - [ ] Add P6 case branch to workflow_enforcer.sh
  - [ ] Commit: "feat: Extend workflow_enforcer.sh to P3-P6"
  - [ ] Create agent_usage_enforcer.sh (300 lines)
  - [ ] Commit: "feat: Create agent_usage_enforcer.sh for 4-6-8 validation"

### P4 Testing
- [ ] Create test infrastructure (helpers, fixtures)
- [ ] Write unit tests (test_workflow_enforcer.bats)
- [ ] Write unit tests (test_agent_usage_enforcer.bats)
- [ ] Write integration tests (test_hook_chain.bats)
- [ ] Write E2E tests (test_complete_workflow.bats)
- [ ] Run full test suite: `bash test/run_all_tests.sh --all`
- [ ] Verify 26/26 tests passing
- [ ] Verify performance <200ms
- [ ] Commit: "test: Add comprehensive test suite for hook enforcement"

### P5 Review
- [ ] Code review by code-reviewer agent
- [ ] Security review by security-auditor agent
- [ ] Documentation review by technical-writer agent
- [ ] Generate REVIEW.md
- [ ] Fix any critical issues found
- [ ] Re-run tests after fixes
- [ ] Commit: "review: Address code review findings"

### P6 Release
- [ ] Update CLAUDE.md (hook enforcement explanation)
- [ ] Create HOOK_ENFORCEMENT_FIX.md (verification results)
- [ ] Update .claude/WORKFLOW.md (phase enforcement)
- [ ] Update README.md (Layer 4 description)
- [ ] Update CHANGELOG.md (v6.2.1 entry)
- [ ] Create HOOK_QUICK_REFERENCE.md (user cheat sheet)
- [ ] Create HOOK_TROUBLESHOOTING.md (problem-solving guide)
- [ ] Commit: "docs: Complete documentation for hook enforcement fix"
- [ ] Create PR with detailed description
- [ ] Run CI/CD pipeline

### P7 Acceptance
- [ ] All tests passing in CI ✅
- [ ] Code review approved ✅
- [ ] Documentation complete ✅
- [ ] Performance validated ✅
- [ ] Rollback plan tested ✅
- [ ] User approval for merge
- [ ] Merge PR to main
- [ ] Monitor logs for 24 hours
- [ ] Verify no false positives
- [ ] Collect user feedback
- [ ] Address any issues promptly

---

## 📈 Expected Outcomes

### Immediate Benefits (Week 1)
- **100% workflow compliance**: All commits follow P0-P7 phases
- **Multi-agent enforcement**: No more single-agent complex tasks
- **Clear error messages**: Users understand what to fix
- **Fast performance**: <200ms hook validation

### Medium-Term Benefits (Month 1)
- **Quality improvement**: Higher code quality from proper workflow
- **Reduced errors**: Fewer bugs from rushed single-agent coding
- **Better documentation**: Forced documentation at each phase
- **Team alignment**: Everyone follows same workflow

### Long-Term Benefits (Month 3+)
- **Cultural shift**: Multi-agent workflow becomes default mindset
- **Knowledge sharing**: Multiple agents = better code understanding
- **Maintainability**: Well-documented, well-tested code
- **Scalability**: Workflow scales to larger projects

### Metrics to Track
1. **Enforcement Rate**: % of commits that pass hook validation (target: 100%)
2. **Agent Compliance**: % of tasks using correct agent count (target: 90%+)
3. **False Positive Rate**: % of legitimate commits blocked (target: <1%)
4. **User Satisfaction**: Survey score (target: >8/10)
5. **Performance**: P95 hook execution time (target: <200ms)
6. **Code Quality**: Bugs per commit (target: reduce by 30%)

---

## 🎓 Key Learnings for Future

### What Worked Well in P0-P1
1. **Multi-agent discovery**: 5 agents in P0 provided comprehensive analysis
2. **Parallel planning**: 5 agents in P1 produced detailed plans quickly
3. **Structured approach**: 8-phase workflow kept planning organized
4. **Clear documentation**: Easy to synthesize agent outputs

### What to Improve
1. **Earlier user involvement**: Validate approach in P0 before P1
2. **Simpler error messages**: More analogies for non-technical users
3. **Performance profiling**: Profile hooks before deployment
4. **Rollback testing**: Test rollback procedure as part of P4

### Recommendations for Similar Fixes
1. **Start with quick wins**: Build momentum with easy fixes
2. **Comprehensive testing**: 70% unit, 20% integration, 10% E2E
3. **User-centric docs**: Write for non-technical users first
4. **Monitor everything**: Log all enforcement actions for analysis

---

## 📞 Support & Resources

### Documentation
- **This Plan**: Complete implementation guide
- **CLAUDE.md**: Global rules and enforcement explanation
- **WORKFLOW.md**: Detailed P0-P7 phase descriptions
- **HOOK_QUICK_REFERENCE.md**: One-page cheat sheet (to be created in P6)
- **HOOK_TROUBLESHOOTING.md**: Problem-solving guide (to be created in P6)

### Tools & Scripts
- **Test Runner**: `bash test/run_all_tests.sh --all`
- **Diagnostics**: `./scripts/diagnose_hooks.sh`
- **Performance**: `./scripts/benchmark_hooks.sh`
- **Rollback**: `./scripts/rollback_v6.2.1.sh`

### Monitoring
- **Enforcement Log**: `.workflow/logs/enforcement.log`
- **Performance Log**: `.workflow/logs/performance.log`
- **Error Log**: `.workflow/logs/errors.log`

### Decision Context
- **DECISIONS.md**: Historical decisions and rationale
- **Memory Cache**: `.claude/memory-cache.json`

---

**Document Version**: 1.0.0
**Created**: 2025-10-14
**Status**: ✅ P1 PLAN Complete - Ready for P2
**Next Phase**: P2 (Skeleton) - Design hook architecture
**Approval**: Pending user confirmation

---

**END OF PLAN DOCUMENT**
