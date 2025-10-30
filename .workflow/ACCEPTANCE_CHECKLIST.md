# Acceptance Checklist - Self-Enforcing Quality System

**Version**: 8.5.2
**Task**: 实现Self-Enforcing Quality System - 防止功能回归
**Branch**: `feature/self-enforcing-quality-system`
**Date**: 2025-10-30

---

## ✅ Phase 1: Discovery & Planning

### 1.1 Branch Check
- [ ] 在main分支检查当前状态
- [ ] 创建feature分支 `feature/self-enforcing-quality-system`
- [ ] 确认分支clean（无未提交更改）

### 1.2 Requirements Discussion
- [ ] 理解regression问题（parallel execution, bypass permissions）
- [ ] 分析Anti-Hollow System自身是hollow的问题
- [ ] 确认3-Layer Defense解决方案

### 1.3 Technical Discovery
- [ ] 创建 `docs/P1_DISCOVERY.md` (>300行) ✅
- [ ] 分析Regression #1: Parallel Execution
- [ ] 分析Regression #2: Bypass Permissions
- [ ] 分析Systemic Issues (4 symptoms)
- [ ] 设计3-Layer Defense (CODEOWNERS + Sentinel CI + Contract Tests)

### 1.4 Impact Assessment
- [ ] 计算影响半径分数
- [ ] 确定推荐Agent数量
- [ ] 记录到 `.workflow/IMPACT_ASSESSMENT.md` ✅

### 1.5 Architecture Planning
- [ ] 创建 `docs/PLAN.md` (>500行) ✅
- [ ] 详细实现步骤（6 components）
- [ ] Test strategy (20 unit tests + 2 integration tests)
- [ ] Performance targets
- [ ] Rollback plan

---

## 🔧 Phase 2: Implementation

### 2.1 Component 1: CODEOWNERS File
- [ ] 创建 `.github/CODEOWNERS`
- [ ] 保护 `.claude/hooks/**` (15 entries)
- [ ] 保护 `.workflow/**` (SPEC.yaml, manifest.yml, gates.yml)
- [ ] 保护核心脚本 (pre_merge_audit.sh, static_checks.sh)
- [ ] 保护核心设置 (settings.json, CLAUDE.md, VERSION)
- [ ] 设置owner为 @perfectuser21
- [ ] 验证语法正确
- [ ] 测试：尝试修改protected file（应该需要approval）

### 2.2 Component 2: Guard Core CI Workflow
- [ ] 创建 `.github/workflows/guard-core.yml`
- [ ] Job 1: verify-critical-files (31 checks)
- [ ] Job 2: verify-critical-configs (10 checks)
- [ ] Job 3: verify-sentinel-strings (15 checks)
- [ ] Job 4: validate-runtime-behavior (5 checks)
- [ ] 配置触发条件 (push, pull_request)
- [ ] 测试本地执行成功
- [ ] 验证YAML语法

### 2.3 Component 3: Guard Scripts (4 scripts)

#### 2.3.1 check_critical_files.sh
- [ ] 创建 `scripts/guard/check_critical_files.sh`
- [ ] 检查31个critical files存在
  - [ ] 7 phase hooks
  - [ ] Core scripts (pre_merge_audit.sh, static_checks.sh, phase_manager.sh)
  - [ ] Core configs (settings.json, SPEC.yaml, manifest.yml)
  - [ ] Version files
- [ ] 添加clear error messages
- [ ] Exit code: 0=pass, 1=fail
- [ ] Test: All files exist → pass
- [ ] Test: One file missing → fail with clear message

#### 2.3.2 check_critical_configs.sh
- [ ] 创建 `scripts/guard/check_critical_configs.sh`
- [ ] Check 1: Bypass permissions configured
- [ ] Check 2: 7-Phase system intact
- [ ] Check 3: Required hooks registered
- [ ] Check 4: Version consistency (6 files)
- [ ] Check 5-10: Other critical configs
- [ ] Exit code: 0=pass, 1=fail
- [ ] Test: All configs valid → pass
- [ ] Test: Invalid config → fail

#### 2.3.3 check_sentinels.sh
- [ ] 创建 `scripts/guard/check_sentinels.sh`
- [ ] 添加sentinel strings到critical files
  - [ ] Add `# SENTINEL:PARALLEL_EXECUTION_CORE_LOGIC` to parallel_subagent_suggester.sh
  - [ ] Add `# SENTINEL:PHASE_MANAGEMENT_CORE` to phase_manager.sh
  - [ ] Add `# SENTINEL:EVIDENCE_COLLECTION_CORE` to evidence collection scripts
  - [ ] Add 12 more sentinels to other critical files
- [ ] Check all 15 sentinel strings present
- [ ] Exit code: 0=pass, 1=fail
- [ ] Test: All sentinels present → pass
- [ ] Test: One sentinel missing → fail (file was gutted!)

#### 2.3.4 validate_runtime_behavior.sh
- [ ] 创建 `scripts/guard/validate_runtime_behavior.sh`
- [ ] Check 1: parallel_subagent_suggester.sh has logs?
- [ ] Check 2: .phase/current updated in last 7 days?
- [ ] Check 3: Evidence files created in last 7 days?
- [ ] Check 4: Phase state maintained?
- [ ] Check 5: Git log shows phase transitions?
- [ ] Graceful degradation (warnings, not hard fails)
- [ ] Exit code: 0=all checks pass, 1=critical failure
- [ ] Test: All recent → pass
- [ ] Test: All stale (>7 days) → warnings

### 2.4 Component 4: Contract Tests (4 tests)

#### 2.4.1 test_parallel_execution.sh
- [ ] 创建 `tests/contract/test_parallel_execution.sh`
- [ ] Test: parallel_subagent_suggester.sh actually runs
- [ ] Test: suggester.log created
- [ ] Test: suggester.log updated recently (<7 days)
- [ ] Test: Log contains expected entries
- [ ] All tests pass

#### 2.4.2 test_phase_management.sh
- [ ] 创建 `tests/contract/test_phase_management.sh`
- [ ] Test: .phase/current exists
- [ ] Test: .phase/current maintained (<7 days old)
- [ ] Test: Git log shows phase transitions
- [ ] Test: Phase transitions follow sequence (Phase1→2→3...)
- [ ] All tests pass

#### 2.4.3 test_evidence_collection.sh
- [ ] 创建 `tests/contract/test_evidence_collection.sh`
- [ ] Test: .evidence/ directory exists
- [ ] Test: Recent evidence files (<7 days)
- [ ] Test: Evidence files are valid YAML
- [ ] Test: Evidence linked to checklist items
- [ ] All tests pass

#### 2.4.4 test_bypass_permissions.sh
- [ ] 创建 `tests/contract/test_bypass_permissions.sh`
- [ ] Test: settings.json has defaultMode=bypassPermissions
- [ ] Test: No "allow" rules override defaultMode
- [ ] Test: Configuration structure correct
- [ ] Note: Manual verification needed (Claude Code prompts)
- [ ] Document manual test procedure

### 2.5 Component 5: Pre-merge Audit Enhancement
- [ ] 打开 `scripts/pre_merge_audit.sh`
- [ ] 定位到最后一个check section
- [ ] 添加新section: "Check 7: Runtime Behavior Validation"
- [ ] Add Check 7.1: parallel_subagent_suggester.sh execution
- [ ] Add Check 7.2: phase_manager.sh usage
- [ ] Add Check 7.3: Evidence collection activity
- [ ] Add Check 7.4: .phase/current maintenance
- [ ] Use existing log_pass, log_warn, log_fail functions
- [ ] Test: Run pre_merge_audit.sh locally
- [ ] Verify new checks execute correctly

### 2.6 Component 6: Phase State Tracker Hook
- [ ] 创建 `.claude/hooks/phase_state_tracker.sh`
- [ ] Implement get_current_phase() function
- [ ] Implement is_phase_stale() function
- [ ] Display current phase on every prompt
- [ ] Warning if phase state stale (>7 days)
- [ ] Phase-specific transition reminders (Phase1-7)
- [ ] Make executable: `chmod +x phase_state_tracker.sh`
- [ ] Test: Run hook manually, verify output correct
- [ ] Test: Verify detects stale state

### 2.7 Settings.json Update
- [ ] 打开 `.claude/settings.json`
- [ ] 定位 `hooks.PrePrompt` array
- [ ] Add `.claude/hooks/phase_state_tracker.sh` at position 1
- [ ] Verify JSON syntax valid
- [ ] Test: Verify hook runs on next AI prompt

### 2.8 Quality Checks
- [ ] All bash scripts pass `bash -n` syntax check
- [ ] All scripts pass shellcheck (0 warnings)
- [ ] All scripts have proper shebang (#!/bin/bash)
- [ ] All scripts have set -euo pipefail
- [ ] All scripts have clear comments
- [ ] All file paths use absolute paths (no relative paths)

---

## 🧪 Phase 3: Testing

### 3.1 Unit Tests - CODEOWNERS (5 tests)
- [ ] Test: CODEOWNERS file exists
- [ ] Test: All 31 protected files listed
- [ ] Test: Correct owner (@perfectuser21)
- [ ] Test: Syntax valid (no errors when parsed)
- [ ] Test: No duplicate entries

### 3.2 Unit Tests - Guard Scripts (8 tests)
- [ ] Test: check_critical_files.sh passes when all exist
- [ ] Test: check_critical_files.sh fails when one missing
- [ ] Test: check_critical_configs.sh passes when valid
- [ ] Test: check_critical_configs.sh fails when invalid
- [ ] Test: check_sentinels.sh passes when all present
- [ ] Test: check_sentinels.sh fails when one missing
- [ ] Test: validate_runtime_behavior.sh passes when recent
- [ ] Test: validate_runtime_behavior.sh warns when stale

### 3.3 Contract Tests (4 tests)
- [ ] Run test_parallel_execution.sh → all pass
- [ ] Run test_phase_management.sh → all pass
- [ ] Run test_evidence_collection.sh → all pass
- [ ] Run test_bypass_permissions.sh → manual verification

### 3.4 Phase State Tracker Tests (3 tests)
- [ ] Test: Displays current phase correctly
- [ ] Test: Detects stale state (>7 days)
- [ ] Test: Shows transition reminders

### 3.5 Integration Test - CI Workflow
- [ ] Push test commit to trigger guard-core.yml
- [ ] Wait for CI to complete
- [ ] Verify all 4 jobs run successfully
- [ ] Verify 61 total checks executed (31+10+15+5)
- [ ] Check CI logs for any issues

### 3.6 Integration Test - End-to-End Workflow
- [ ] Simulate Phase 1-7 workflow
- [ ] Verify phase_state_tracker.sh shows correct phase at each step
- [ ] Verify runtime validation catches stale state
- [ ] Verify contract tests detect hollow implementations
- [ ] Verify pre_merge_audit.sh includes new checks

### 3.7 Performance Tests
- [ ] Measure phase_state_tracker.sh execution time (<500ms)
- [ ] Measure guard scripts execution time (<2s each)
- [ ] Measure contract tests execution time (<10s total)
- [ ] Measure pre_merge_audit.sh total time (should not increase >20%)

### 3.8 Static Analysis
- [ ] Run shellcheck on all new scripts (0 warnings)
- [ ] Run bash -n on all new scripts (no syntax errors)
- [ ] Verify all scripts use set -euo pipefail
- [ ] Check for hardcoded paths (should use PROJECT_ROOT)

---

## 🔍 Phase 4: Review

### 4.1 Code Review
- [ ] Review CODEOWNERS for completeness
- [ ] Review guard-core.yml workflow structure
- [ ] Review all 4 guard scripts for correctness
- [ ] Review all 4 contract tests for coverage
- [ ] Review pre_merge_audit.sh enhancement
- [ ] Review phase_state_tracker.sh implementation
- [ ] Check for consistent error handling
- [ ] Check for consistent code style

### 4.2 Documentation Review
- [ ] Verify P1_DISCOVERY.md complete (>300 lines) ✅
- [ ] Verify PLAN.md complete (>500 lines) ✅
- [ ] Verify ACCEPTANCE_CHECKLIST.md complete (this file) ✅
- [ ] Verify IMPACT_ASSESSMENT.md complete ✅
- [ ] Create REVIEW.md (>100 lines)
  - [ ] Summary of changes
  - [ ] Code quality assessment
  - [ ] Test coverage analysis
  - [ ] Potential risks identified

### 4.3 Pre-merge Audit
- [ ] Run `bash scripts/pre_merge_audit.sh`
- [ ] Verify all checks pass (including new Check 7)
- [ ] Address any warnings
- [ ] Confirm 0 configuration issues

### 4.4 Checklist Verification
- [ ] Phase 1 checklist: 100% complete ✅
- [ ] Phase 2 checklist: ≥95% complete
- [ ] Phase 3 checklist: ≥95% complete
- [ ] Phase 4 checklist: Current phase

---

## 📦 Phase 5: Release

### 5.1 Documentation Updates
- [ ] Update CHANGELOG.md with v8.5.2 entry
  - [ ] Add "Self-Enforcing Quality System" section
  - [ ] List all 6 components
  - [ ] Mention 3-layer defense
- [ ] Update README.md if needed
  - [ ] Add section on quality enforcement
  - [ ] Explain CODEOWNERS protection
- [ ] Update CLAUDE.md if needed
  - [ ] Document phase_state_tracker.sh behavior
  - [ ] Update AI responsibilities section

### 5.2 Version Management
- [ ] Update VERSION file to 8.5.2
- [ ] Update .claude/settings.json version to 8.5.2
- [ ] Update .workflow/manifest.yml version to 8.5.2
- [ ] Update package.json version to 8.5.2
- [ ] Update CHANGELOG.md version to 8.5.2
- [ ] Update .workflow/SPEC.yaml version to 8.5.2
- [ ] Verify all 6 files have identical version
- [ ] Run `bash scripts/check_version_consistency.sh` → pass

### 5.3 Git Tagging
- [ ] Create git tag v8.5.2
- [ ] Format: `git tag -a v8.5.2 -m "feat: Self-Enforcing Quality System"`
- [ ] Push tag: `git push origin v8.5.2`

### 5.4 Deployment Preparation
- [ ] No deployment needed (development workflow enhancement)
- [ ] Verify all files committed
- [ ] Verify no uncommitted changes
- [ ] Branch ready for PR

---

## ✔️ Phase 6: Acceptance

### 6.1 Acceptance Testing
- [ ] CODEOWNERS protects critical files (test: try to modify protected file)
- [ ] guard-core.yml CI runs on every push/PR
- [ ] All 61 checks execute successfully
- [ ] Contract tests detect hollow implementations
- [ ] Phase state tracker displays phase correctly
- [ ] Runtime validation integrated into pre-merge audit

### 6.2 User Acceptance Criteria

#### Criterion 1: CODEOWNERS Protection Works
- [ ] AI cannot modify protected files without approval
- [ ] Attempting to modify protected file shows "needs approval" message
- [ ] User @perfectuser21 can approve changes

#### Criterion 2: Sentinel CI Detects Hollows
- [ ] CI fails if critical file missing
- [ ] CI fails if critical config invalid
- [ ] CI fails if sentinel string removed (file gutted)
- [ ] CI warns if runtime validation shows stale state

#### Criterion 3: Contract Tests Catch Regressions
- [ ] Parallel execution contract detects if hook never runs
- [ ] Phase management contract detects if state not maintained
- [ ] Evidence collection contract detects if no evidence collected
- [ ] All contract tests pass in current codebase

#### Criterion 4: Phase State Tracked
- [ ] phase_state_tracker.sh displays current phase on every prompt
- [ ] AI reminded to update .phase/current when transitioning
- [ ] Warning shown if phase state stale (>7 days)

#### Criterion 5: Runtime Validation Integrated
- [ ] pre_merge_audit.sh includes Check 7 (Runtime Behavior Validation)
- [ ] Check 7.1-7.4 execute correctly
- [ ] Warnings generated for stale state
- [ ] Failures generated for critical issues (never executed)

### 6.3 Acceptance Report
- [ ] Create `.workflow/ACCEPTANCE_REPORT.md`
- [ ] Document all acceptance tests performed
- [ ] Document results (pass/fail for each criterion)
- [ ] Document any issues found and resolved
- [ ] User sign-off: @perfectuser21 confirms acceptance

---

## 🧹 Phase 7: Closure

### 7.1 Final Verification
- [ ] Run `bash scripts/comprehensive_cleanup.sh aggressive`
- [ ] Verify .temp/ directory clean
- [ ] Verify no duplicate documents (*.md count ≤7 in root)
- [ ] Run `bash scripts/check_version_consistency.sh` → pass
- [ ] Run `bash scripts/verify-phase-consistency.sh` → pass
- [ ] Run `bash tools/verify-core-structure.sh` → pass

### 7.2 Git Status
- [ ] All changes committed
- [ ] No uncommitted files
- [ ] No untracked files (except .workflow/, .temp/)
- [ ] Branch up-to-date with main (if needed)

### 7.3 PR Preparation
- [ ] Feature branch pushed to remote
- [ ] PR created with proper title:
  - "feat: Self-Enforcing Quality System - 3-Layer Defense Against Regressions"
- [ ] PR description includes:
  - [ ] Summary of 3-layer defense
  - [ ] List of 6 components
  - [ ] Test results
  - [ ] Documentation links
  - [ ] Claude Code attribution

### 7.4 CI Validation
- [ ] Wait for guard-core.yml to complete
- [ ] Verify all 61 checks pass
- [ ] Wait for other CI workflows to complete
- [ ] All CI checks green ✅

### 7.5 User Approval
- [ ] Wait for user to review PR
- [ ] Address any feedback
- [ ] User says "merge" or approves PR

### 7.6 Merge
- [ ] Execute: `gh pr merge --auto --squash`
- [ ] Wait for GitHub to merge
- [ ] Verify merge successful
- [ ] Verify tag v8.5.2 created automatically (by release workflow)

### 7.7 Post-Merge Verification
- [ ] Switch to main branch: `git checkout main`
- [ ] Pull latest: `git pull`
- [ ] Verify CODEOWNERS active
- [ ] Verify guard-core.yml running on main
- [ ] Verify phase_state_tracker.sh hook active
- [ ] Run one test: Try to modify protected file (should need approval)

---

## 📊 Success Metrics Summary

### Technical Metrics
- [ ] 6 components implemented: CODEOWNERS, guard-core.yml, 4 guard scripts, 4 contract tests, pre_merge_audit enhancement, phase_state_tracker.sh
- [ ] 12 new files created
- [ ] 2 files modified
- [ ] ~1,500 lines of new code + tests
- [ ] 20 unit tests pass
- [ ] 2 integration tests pass
- [ ] 0 shellcheck warnings
- [ ] All scripts <2s execution time

### Functional Metrics
- [ ] CODEOWNERS protects 31 critical files
- [ ] guard-core.yml runs 61 checks
- [ ] Contract tests detect 4 types of hollow implementations
- [ ] Phase state tracked continuously
- [ ] Runtime validation integrated

### Quality Metrics
- [ ] Code review approved
- [ ] All tests pass
- [ ] CI green
- [ ] Documentation complete (4 Phase 1 docs)
- [ ] Version consistency (6/6 files)
- [ ] User acceptance confirmed

### Long-term Metrics (30-day follow-up)
- [ ] Hollow Implementation Rate = 0%
- [ ] No regressions of parallel execution
- [ ] No regressions of phase management
- [ ] Phase state maintained continuously (no stale >7 days)
- [ ] Evidence collection working (files created weekly)

---

**Checklist Status**: ✅ Complete
**Total Items**: 196
**Phase 1 Complete**: Yes
**Ready for Phase 2**: Awaiting user approval
