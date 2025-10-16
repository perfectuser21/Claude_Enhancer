# P0 Acceptance Checklist - Documentation Fix

**Task**: Fix 5 Critical Documentation Issues in DECISION_TREE.md
**Version**: Claude Enhancer v6.5.0
**Created**: 2025-10-16
**Owner**: AI Assistant

---

## 📋 Executive Summary

This checklist defines the acceptance criteria for fixing 5 critical documentation issues discovered in the code review:

1. **Agent Count Inconsistency**: Documentation claims "3-4 agents" while code implements 4-6-8 principle
2. **Hook Count Error**: Documentation states "15 hooks" while actual count is 17 hooks
3. **Phase Numbering Confusion**: Mixed use of "P4 质量门禁" and "Phase 3 Testing" causing ambiguity
4. **Butler Mode References**: Incomplete implementation with placeholder in decision tree (line 4481, 4587)
5. **Non-existent Scripts**: References to `static_checks.sh` and `pre_merge_audit.sh` that don't exist

**Definition of "Done"**: All 5 issues resolved, verified through automated checks, and human validation confirms clarity and accuracy.

---

## ✅ Functional Acceptance Criteria

### Issue #1: Agent Count Inconsistency
- [ ] **AC-F1.1**: All references to "3-4 agents" changed to "4-6-8 agents"
  - **Verification**: `grep -r "3-4" docs/DECISION_TREE.md` returns 0 results
  - **Verification**: `grep -r "three-four" docs/DECISION_TREE.md` returns 0 results
  - **Locations**: Lines 243, 3698, 3795, 3798, 3799, 4497, 4679, 4706

- [ ] **AC-F1.2**: Section 4.1 "4-6-8原则详解" accurately reflects code implementation
  - **Verification**: Compare with `/home/xx/dev/Claude Enhancer 5.0/core/agents/selector.py`
  - **Verification**: Complexity scoring algorithm matches actual code (lines 3698-3875)
  - **Expected**: Simple tasks=4 agents, Standard=6 agents, Complex=8 agents

- [ ] **AC-F1.3**: Agent selection decision tree correctly maps complexity → agent count
  - **Verification**: Section 4.2 "复杂度评分算法" matches actual logic
  - **Verification**: Section 4.3 "Agent选择矩阵" shows 4/6/8 options, not 3/4

### Issue #2: Hook Count Error
- [ ] **AC-F2.1**: All references to "15 hooks" changed to "17 hooks"
  - **Verification**: `grep -r "15个active hooks" docs/DECISION_TREE.md` returns 0 results
  - **Verification**: `grep -r "15 hooks" docs/DECISION_TREE.md` returns 0 results
  - **Locations**: Line 77, 3449, 4721

- [ ] **AC-F2.2**: Hook count matches actual `.claude/settings.json` configuration
  - **Verification**: Count hooks in settings.json:
    - UserPromptSubmit: 2 hooks
    - PrePrompt: 5 hooks
    - PreToolUse: 7 hooks
    - PostToolUse: 3 hooks
    - **Total**: 17 hooks
  - **Expected**: Documentation states "17个active hooks"

- [ ] **AC-F2.3**: Hook distribution table reflects actual configuration
  - **Verification**: Part 3 "Hook决策逻辑" lists all 17 hooks by category
  - **Expected**: Each hook name matches exactly with settings.json

### Issue #3: Phase Numbering Confusion
- [ ] **AC-F3.1**: Consistent terminology: "Phase X" used throughout (not "PX")
  - **Verification**: `grep -r "P3 质量门禁" docs/DECISION_TREE.md` returns 0 results
  - **Verification**: `grep -r "P4 质量门禁" docs/DECISION_TREE.md` returns 0 results
  - **Expected**: Use "Phase 3 质量门禁" and "Phase 4 质量门禁"

- [ ] **AC-F3.2**: Phase mapping clearly documented in introduction
  - **Verification**: Section 1.1 includes a mapping table:
    ```
    Step 6 = Phase 3 (Testing)
    Step 7 = Phase 4 (Review)
    Step 8 = Phase 5 (Release)
    ```
  - **Expected**: No confusion between Step number and Phase number

- [ ] **AC-F3.3**: All cross-references use consistent naming
  - **Verification**: Search for mixed patterns like "Step 6 (P3)" or "Phase 3 (Step 6)"
  - **Expected**: Either "Step 6 (Phase 3)" or just "Phase 3" - consistent format

### Issue #4: Butler Mode References Incomplete
- [ ] **AC-F4.1**: Remove placeholder references to `butler_mode_detector.sh`
  - **Verification**: `grep -r "butler_mode" docs/DECISION_TREE.md` returns 0 results
  - **Locations**: Line 4481 (hook table), 4587 (checklist item)

- [ ] **AC-F4.2**: Add explanatory note about Butler Mode future implementation
  - **Verification**: Section 7.2 "未来功能" or similar includes:
    - "Butler Mode: Planned feature for automated task management"
    - "Status: Not yet implemented in v6.5.0"
  - **Expected**: Clear communication that this is planned, not current

- [ ] **AC-F4.3**: Hook count table does not include non-existent hooks
  - **Verification**: All 17 hooks in Part 3 tables exist in `.claude/hooks/` directory
  - **Verification**: `ls .claude/hooks/*.sh | wc -l` ≥ 17 (excluding archived)

### Issue #5: Non-existent Scripts Referenced
- [ ] **AC-F5.1**: Replace `static_checks.sh` references with actual implementation details
  - **Verification**: `grep -c "static_checks.sh" docs/DECISION_TREE.md` returns 0
  - **Locations**: Lines 170, 1307, 1386, 1387, 1389, 1455, 1459, 1634, 3786, 4093, 4247
  - **Solution Options**:
    - A) Document that checks are embedded in hooks (not separate script)
    - B) Create the script and document it
    - C) Reference actual hook that performs these checks

- [ ] **AC-F5.2**: Replace `pre_merge_audit.sh` references with actual implementation
  - **Verification**: `grep -c "pre_merge_audit.sh" docs/DECISION_TREE.md` returns 0
  - **Locations**: Lines 187, 1688, 1821, 1822, 1824, 1894, 1898, 2121, 2375, 2376, 3787, 4186
  - **Solution**: Same as AC-F5.1 (consistent approach)

- [ ] **AC-F5.3**: Decision tree accurately reflects actual quality gate implementation
  - **Verification**: Section 5.1 "Phase 3质量门禁" describes real process:
    - Which hook performs the check? (likely `quality_gate.sh`)
    - What specific checks are run?
    - Where is the exit code evaluated?
  - **Verification**: Section 5.2 "Phase 4质量门禁" similarly accurate

---

## 🔧 Technical Acceptance Criteria

### Code-Documentation Alignment
- [ ] **AC-T1**: Agent selection logic in docs matches `core/agents/selector.py`
  - **Verification**: Run diff comparison on pseudocode vs actual Python
  - **Metric**: 100% algorithm match

- [ ] **AC-T2**: Hook execution flow matches actual `.claude/settings.json` order
  - **Verification**: Part 3 hook sequence = settings.json sequence
  - **Metric**: All 17 hooks in correct order and category

- [ ] **AC-T3**: Phase transitions match workflow executor behavior
  - **Verification**: Compare decision tree transitions with `.workflow/executor.sh` or equivalent
  - **Metric**: No phantom states or missing transitions

### Verification Scripts
- [ ] **AC-T4**: Create verification script `scripts/verify_decision_tree.sh`
  - **Purpose**: Automated checking of all 5 issues
  - **Must check**:
    - Hook count = 17
    - Agent references = 4-6-8 (not 3-4)
    - No references to non-existent scripts
    - Phase numbering consistency
    - Butler Mode status clear
  - **Exit code**: 0 if all checks pass, 1 if any fail

- [ ] **AC-T5**: Verification script runs in CI/CD
  - **Verification**: `.github/workflows/` includes doc validation job
  - **Expected**: CI fails if decision tree drifts from reality

---

## 🎨 Consistency Acceptance Criteria

### Terminology Consistency
- [ ] **AC-C1**: "Phase" vs "Step" used correctly throughout
  - **Rule**: "Step X" = user-facing milestone (1-10)
  - **Rule**: "Phase Y" = technical stage (0-5)
  - **Verification**: No mixed usage like "Step Phase 3"

- [ ] **AC-C2**: Agent count terminology standardized
  - **Old**: "3-4 agents", "three-four", "simple/standard"
  - **New**: "4-6-8 agents", "4/6/8", "simple/standard/complex"
  - **Verification**: Consistent phrasing across all 10+ references

- [ ] **AC-C3**: Script references use consistent format
  - **Format**: `` `script_name.sh` `` or `bash scripts/script_name.sh`
  - **Verification**: No broken scripts, all paths accurate

### Cross-Reference Integrity
- [ ] **AC-C4**: All internal links work (no broken anchors)
  - **Verification**: Test all `[text](#anchor)` links in Markdown
  - **Tool**: Use markdown link checker
  - **Metric**: 0 broken links

- [ ] **AC-C5**: Version numbers consistent across document
  - **Verification**: Header says "v6.5.0", all references match
  - **Verification**: No stale "v6.3", "v6.4" references

---

## 📖 Documentation Acceptance Criteria

### Clarity & Accuracy
- [ ] **AC-D1**: Decision tree is understandable by non-programmers
  - **Test**: Have user read Section 2.6 (Phase 3) and explain back
  - **Expected**: User can describe quality gate flow without confusion

- [ ] **AC-D2**: All code examples are syntactically correct
  - **Verification**: Extract all code blocks, run shellcheck/python linter
  - **Metric**: 0 syntax errors in examples

- [ ] **AC-D3**: Pseudocode accurately reflects actual code logic
  - **Verification**: Side-by-side comparison with real implementation
  - **Metric**: No algorithmic discrepancies

### Completeness
- [ ] **AC-D4**: All 17 hooks documented with decision logic
  - **Verification**: Part 3 has subsection for each of 17 hooks
  - **Content**: Each hook includes:
    - Purpose
    - Trigger condition
    - Decision logic (flowchart or pseudocode)
    - Exit codes
    - Example scenarios

- [ ] **AC-D5**: All quality gates fully explained
  - **Verification**: Phase 3 gate (Section 5.1) includes:
    - What is checked
    - How it's checked (which hook/script)
    - Pass/fail criteria
    - Failure handling
  - **Verification**: Phase 4 gate (Section 5.2) same level of detail

- [ ] **AC-D6**: Change impact analysis template usable
  - **Verification**: Section 7.1 provides clear instructions
  - **Test**: Hypothetically add a new feature, use template
  - **Expected**: Template guides to identify all affected decision points

### Maintainability
- [ ] **AC-D7**: Document metadata is current
  - **Verification**: Header includes:
    - Document version (v1.0 or higher)
    - System version (v6.5.0)
    - Last updated date (2025-10-16 or later)
    - Change log section at end

- [ ] **AC-D8**: Future maintenance guidance included
  - **Verification**: Section 7.2 explains:
    - When to update decision tree
    - How to validate changes
    - Who to notify (even if "yourself in 6 months")

---

## 🎯 Success Metrics

### Quantitative Metrics
| Metric | Target | Verification Method |
|--------|--------|---------------------|
| Hook count accuracy | 17/17 | `grep "17 hooks" docs/DECISION_TREE.md` |
| Agent reference consistency | 0 instances of "3-4" | `grep -c "3-4" docs/DECISION_TREE.md` = 0 |
| Non-existent script references | 0 | `grep -c "static_checks.sh\|pre_merge_audit.sh" docs/DECISION_TREE.md` = 0 |
| Phase numbering issues | 0 | Manual review of Part 2 section headers |
| Butler Mode clarity | 1 explanatory note | Search for "Butler Mode" finds future features section |
| Broken internal links | 0 | Markdown link checker passes |
| Code example errors | 0 | Shellcheck + Python lint passes |

### Qualitative Metrics
- [ ] **QM-1**: User can follow decision tree without asking clarifying questions
- [ ] **QM-2**: AI can use decision tree to self-correct behavior
- [ ] **QM-3**: Document serves as reliable reference for system behavior
- [ ] **QM-4**: No contradictions between decision tree and actual code

---

## 🔍 Verification Checklist

### Automated Verification (Required)
```bash
# Run before marking task complete
cd /home/xx/dev/Claude\ Enhancer\ 5.0

# Check 1: Hook count
grep -c "17 hooks" docs/DECISION_TREE.md
# Expected: ≥ 3 (should find 3 occurrences)

# Check 2: Agent count (no old references)
grep -c "3-4 agents\|three-four" docs/DECISION_TREE.md
# Expected: 0

# Check 3: Non-existent scripts
grep -c "static_checks.sh\|pre_merge_audit.sh" docs/DECISION_TREE.md
# Expected: 0

# Check 4: Phase numbering
grep -c "P3 质量门禁\|P4 质量门禁" docs/DECISION_TREE.md
# Expected: 0

# Check 5: Butler Mode cleanup
grep -c "butler_mode_detector.sh" docs/DECISION_TREE.md
# Expected: 0

# Check 6: Code examples syntax
# Extract all shell code blocks and validate
awk '/```bash/,/```/' docs/DECISION_TREE.md > /tmp/decision_tree_code.sh
shellcheck /tmp/decision_tree_code.sh
# Expected: No errors
```

### Manual Verification (Required)
- [ ] **MV-1**: Read Section 1.1 - Does hook count say 17? ✓
- [ ] **MV-2**: Read Section 4.1 - Does it explain 4-6-8 principle clearly? ✓
- [ ] **MV-3**: Read Section 2.6 - Are quality gate steps clear and accurate? ✓
- [ ] **MV-4**: Search for "Butler" - Is future status explained? ✓
- [ ] **MV-5**: Check Part 3 - Do all 17 hooks have documentation? ✓
- [ ] **MV-6**: Spot check 5 random code examples - Syntax correct? ✓

---

## 🚦 Definition of Done

**This task is considered 100% complete when:**

1. ✅ **All 33 Acceptance Criteria** (AC-F1.1 through AC-D8) are checked ✓
2. ✅ **All 7 Success Metrics** meet target values
3. ✅ **Automated Verification** script exits with code 0
4. ✅ **Manual Verification** checklist (MV-1 through MV-6) all checked ✓
5. ✅ **Code Review** by AI confirms no regressions introduced
6. ✅ **User Confirmation** states "No more confusion, documentation is clear"

**Failure Conditions** (task NOT done if any true):
- ❌ Any automated check returns non-zero exit code
- ❌ User reports: "I'm still confused about [any of the 5 issues]"
- ❌ New discrepancies introduced while fixing old ones
- ❌ Decision tree contradicts actual code behavior

---

## 📝 Notes for AI Executor

### Implementation Strategy
1. **Priority**: Fix high-impact issues first (Hook count, Agent count)
2. **Approach**: Search-and-replace for consistency issues
3. **Validation**: Run verification script after each fix
4. **Iteration**: If verification fails, analyze and retry

### Risk Mitigation
- **Risk**: Introducing new errors while fixing old ones
  - **Mitigation**: Make one change at a time, verify immediately
- **Risk**: Over-correcting and losing useful information
  - **Mitigation**: Preserve original meaning, only fix inaccuracies
- **Risk**: Breaking internal document links
  - **Mitigation**: Run markdown link checker after section header changes

### Reference Files
- **Hook count source**: `/home/xx/dev/Claude Enhancer 5.0/.claude/settings.json`
- **Agent logic source**: `/home/xx/dev/Claude Enhancer 5.0/core/agents/selector.py`
- **Phase definitions**: `/home/xx/dev/Claude Enhancer 5.0/CLAUDE.md` (lines 200-250)
- **Workflow logic**: `/home/xx/dev/Claude Enhancer 5.0/.workflow/executor.sh`

---

## 📊 Progress Tracking

**Issue Resolution Status**:
- [ ] Issue #1: Agent Count Inconsistency (0/3 criteria met)
- [ ] Issue #2: Hook Count Error (0/3 criteria met)
- [ ] Issue #3: Phase Numbering Confusion (0/3 criteria met)
- [ ] Issue #4: Butler Mode Incomplete (0/3 criteria met)
- [ ] Issue #5: Non-existent Scripts (0/3 criteria met)

**Overall Completion**: 0/33 acceptance criteria met (0%)

**Target Completion Date**: [To be filled during Phase 1]
**Actual Completion Date**: [To be filled during Phase 5]

---

*This checklist is the authoritative definition of "done" for the documentation fix task. Any changes to scope must update this document first.*
