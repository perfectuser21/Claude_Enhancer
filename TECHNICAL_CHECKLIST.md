# Technical Checklist: Fix Workflow Interference

**Task**: 修复AI工作流干扰问题 - 技术实现验证清单

**Generated**: 2025-10-22 (Phase 1.3: Technical Discovery)
**Branch**: feature/fix-workflow-interference

---

## 🔧 Technical Implementation Checks

### 1. File Modifications

#### 1.1 Global Config Backup
- [ ] Create backup: `cp /root/.claude/CLAUDE.md /root/.claude/CLAUDE.md.backup`
- [ ] Verify backup exists and is readable
- [ ] Backup file size matches original (404 lines)

#### 1.2 Remove Dual-Mode System (Lines 30-66)
- [ ] Section "🎭 双模式协作系统" completely removed
- [ ] Subsection "💭 讨论模式" removed
- [ ] Subsection "🚀 执行模式" removed
- [ ] Subsection "模式切换规则" removed
- [ ] Subsection "执行模式下的强制要求" removed

#### 1.3 Add CE-Specific Override Rule
- [ ] New section added: "🚀 Claude Enhancer 项目强制规则"
- [ ] Rule states: "当工作目录是 Claude Enhancer 时，立即进入7-Phase工作流"
- [ ] Explicit list: "任何编程任务 = Phase 1开始"
- [ ] Examples provided: "开发XXX"、"实现XXX"、"创建XXX"、"优化XXX"
- [ ] Exception clarified: 纯查询/分析不进工作流

#### 1.4 Update Phase System Reference
- [ ] All "8-Phase (P0-P7)" changed to "7-Phase (Phase 1-7)"
- [ ] Line 49: "激活完整8-Phase工作流" → "激活完整7-Phase工作流"
- [ ] Line 247: "P0-P7" → "Phase 1-7"
- [ ] Section at line 357: Updated phase list to Phase 1-7
- [ ] Removed "P0 探索" references
- [ ] Updated to match project CLAUDE.md version 7.1.0

### 2. Configuration Validation

#### 2.1 Syntax Checks
- [ ] YAML/Markdown syntax valid (no broken formatting)
- [ ] No duplicate section headers
- [ ] Code blocks properly closed
- [ ] Lists properly formatted

#### 2.2 Content Validation
- [ ] No contradictory rules (e.g., "wait for trigger" vs "immediately enter")
- [ ] Clear hierarchy: Project CLAUDE.md > Global CLAUDE.md for CE projects
- [ ] All phase numbers consistent (7, not 8)

#### 2.3 File Integrity
- [ ] Global config file size: ~380-400 lines (after removal)
- [ ] Project config unchanged: 1141 lines
- [ ] File permissions: readable by Claude Code
- [ ] No encoding issues (UTF-8)

### 3. Behavioral Testing

#### 3.1 Development Task Detection
- [ ] Input: "帮我开发XXX" → Expected: Enter Phase 1.2
- [ ] Input: "实现XXX功能" → Expected: Enter Phase 1.2
- [ ] Input: "创建XXX模块" → Expected: Enter Phase 1.2
- [ ] Input: "优化XXX性能" → Expected: Enter Phase 1.2
- [ ] Input: "重构XXX代码" → Expected: Enter Phase 1.2

#### 3.2 Non-Development Task Detection
- [ ] Input: "这是什么？" → Expected: Direct answer, no workflow
- [ ] Input: "为什么会这样？" → Expected: Direct analysis, no workflow
- [ ] Input: "这个文件在哪？" → Expected: Direct search, no workflow
- [ ] Input: "解释这段代码" → Expected: Direct explanation, no workflow

#### 3.3 Branch Check Behavior
- [ ] On main branch + development task → Create feature branch
- [ ] On feature branch + related task → Continue on branch
- [ ] On feature branch + unrelated task → Suggest new branch

### 4. Integration Testing

#### 4.1 Git Hooks Interaction
- [ ] Pre-commit hook not triggered during config change (only text)
- [ ] Pre-push hook allows pushing to feature branch
- [ ] Branch protection hook not blocking (on feature branch)

#### 4.2 Claude Hooks Interaction
- [ ] `.claude/hooks/branch_helper.sh` works correctly after change
- [ ] No conflicts with other hooks
- [ ] Hook execution time <2 seconds

#### 4.3 Workflow Validators
- [ ] `workflow_validator.sh` passes (if applicable)
- [ ] `pre_merge_audit.sh` passes (Phase 4)
- [ ] `static_checks.sh` passes (Phase 3)

### 5. Documentation Updates

#### 5.1 Changelog Entry
- [ ] Added to `CHANGELOG.md` under v7.1.1 or v7.2.0
- [ ] Format: `## [Version] - Date`
- [ ] Section: `### Fixed`
- [ ] Description: "修复全局配置干扰导致AI不进入工作流的问题"

#### 5.2 Evidence Documentation
- [ ] Test dialogue transcripts saved to `.temp/test_results/`
- [ ] Before/after comparison documented
- [ ] Error rate metrics: 4/day → 0/week

### 6. Rollback Plan

#### 6.1 Rollback Procedure
- [ ] Documented: `cp /root/.claude/CLAUDE.md.backup /root/.claude/CLAUDE.md`
- [ ] Tested: Rollback procedure works
- [ ] Recovery time: <1 minute

#### 6.2 Rollback Triggers
- [ ] Define: What constitutes failure requiring rollback?
  - AI still not entering workflow for development tasks
  - AI entering workflow for non-development tasks (false positive)
  - Syntax errors in global config
  - Breaking other projects using global config

---

## 🔍 Technical Debt & Future Improvements

### Known Limitations
- Global config affects ALL projects - need project-specific override mechanism
- No automated test for config changes (manual testing required)
- Backup is manual (not automated in CI)

### Future Enhancements
- [ ] Consider: Split global config into modules (base + CE-specific)
- [ ] Consider: Automated config validation in CI
- [ ] Consider: Per-project config inheritance mechanism

---

## ✅ Technical Sign-Off Criteria

**This technical checklist is complete when**:
1. All file modification checks ✓
2. All configuration validation checks ✓
3. All behavioral testing checks ✓ (minimum 3 test dialogues)
4. All integration testing checks ✓
5. All documentation update checks ✓
6. Rollback plan documented and tested ✓

**Technical reviewer should verify**:
- Config changes are minimal and focused
- No unintended side effects on other projects
- Test coverage is adequate (8+ test cases)
- Rollback is straightforward and safe

---

## 📝 Technical Notes

- **Complexity**: Low (text-only config change, no code)
- **Risk**: Medium (affects global config, but project override exists)
- **Testing**: Primarily behavioral (no unit tests for config)
- **Rollback**: Easy (simple file copy)
- **Dependencies**: None (standalone config change)
