# Phase 1 Discovery: Anti-Hollow Gate Full Integration

**Feature Branch**: `feature/anti-hollow-gate-full-integration`
**Date**: 2025-10-27
**Phase**: Phase 1 - Discovery & Planning

---

## 🎯 Problem Statement

### Current Situation (v8.0)
Claude Enhancer v8.0 implemented several advanced systems:
- Learning System (`.learning/`)
- Auto-fix mechanism (`scripts/learning/auto_fix.py`)
- Evidence collection infrastructure
- Skills framework (`.claude/settings.json`)

**Critical Issue**: All these features **exist but are not actively used** in the development workflow.

### Root Cause Analysis
Through detailed investigation, we discovered:

1. **Workflow Guardian Limitation**
   ```bash
   # scripts/workflow_guardian.sh only checks:
   check_phase1_docs() {
     p1_count=$(find docs/ -name "P1_*.md" | wc -l)
     # ✅ If file exists → PASS
     # ❌ Does NOT check if content is complete
     # ❌ Does NOT check if checklist has evidence
   }
   ```

2. **Acceptance Checklist Gap**
   - Checklists exist (e.g., `docs/ACCEPTANCE_CHECKLIST*.md`)
   - Items can be marked as `[x]` completed
   - **No validation that evidence was collected**
   - **No proof that implementation works**

3. **Learning System Unused**
   ```bash
   # Current state:
   $ ls .learning/items/
   # Only 8 test files with empty content:
   # - "测试Learning Item捕获功能"
   # - "测试性能优化Learning Item"
   # All have empty code_snippet, empty technical_details
   ```

4. **Skills Not Configured**
   ```json
   // .claude/settings.json
   {
     "skills": null  // ← Should have 4 skills configured
   }
   ```

### Real-World Impact
When I (Claude) implemented v8.0 features:
- ✅ Phase 1: Wrote comprehensive PLAN.md
- ✅ Phase 2: Implemented all code (auto_fix.py, directories, etc.)
- ✅ Phase 3: Created test data (8 learning items)
- ✅ Phase 4: Code review passed (files exist, syntax correct)
- ✅ Phase 5-7: Merged to main

**But**:
- ❌ No hook ever calls `auto_fix.py`
- ❌ No workflow step captures real learning items
- ❌ Skills never trigger automatically
- ❌ Evidence system exists but unused

**Result**: "Hollow Implementation" - code that passes all checks but never runs.

---

## 🎯 Proposed Solution

### Anti-Hollow Gate: 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    3-Layer Anti-Hollow Gate                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Pre-Write Hooks (Preventive)                         │
│  ────────────────────────────────────────                       │
│  Trigger: Before AI writes to checklist                         │
│  Action:  Prompt "Have you collected evidence?"                 │
│  Block:   Commits without evidence comments                     │
│                                                                  │
│  Layer 2: Phase Transition Hooks (Active)                      │
│  ─────────────────────────────────────────                      │
│  Trigger: Phase N → Phase N+1                                   │
│  Action:  Auto-capture Learning Items                           │
│           Validate checklist completion (≥90%)                  │
│  Block:   Transitions without learning captured                 │
│                                                                  │
│  Layer 3: Pre-Merge Audit (Final Gate)                        │
│  ───────────────────────────────────────                        │
│  Trigger: Before merge to main                                  │
│  Action:  Validate ALL [x] items have evidence                  │
│           Check Learning Items ≥1 per phase                     │
│           Verify Auto-fix rollback capability                   │
│  Block:   Merges with <90% completion or missing evidence      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Evidence System

**Format**: Evidence ID = `EVID-{YEAR}W{ISO_WEEK}-{SEQ}`
- Example: `EVID-2025W44-001`
- Storage: `.evidence/2025W44/EVID-2025W44-001.yml`

**Evidence Types**:
1. `test_result` - Test execution output
2. `code_review` - Manual review notes
3. `command_output` - Command execution proof
4. `artifact` - File artifacts (screenshots, logs)

**Usage in Checklist**:
```markdown
- [x] 1.1 Implement evidence collection script
<!-- evidence: EVID-2025W44-001 -->

- [x] 1.2 Create validation mechanism
<!-- evidence: EVID-2025W44-002 -->
```

**Validation**: `scripts/evidence/validate_checklist.sh` scans checklist and:
- ✅ Every `[x]` must have `<!-- evidence: EVID-... -->` within 5 lines
- ✅ Evidence ID must exist in `.evidence/index.json`
- ❌ Missing evidence → Block commit

---

## 🔧 Technical Implementation

### Component 1: Evidence System

**Files to Create**:
```
.evidence/
├── schema.json              # JSON schema for evidence metadata
├── index.json               # Fast lookup index
└── 2025W44/                 # ISO week directories
    ├── EVID-2025W44-001.yml
    ├── EVID-2025W44-002.yml
    └── artifacts/           # Large files storage
        └── test_output_001.log

scripts/evidence/
├── collect.sh               # Collect evidence for checklist items
└── validate_checklist.sh    # Validate checklist has evidence
```

**Key Scripts**:

1. **collect.sh** (PATCHED v1.1)
   - Fixes: ISO week format, sequence generation, Python env export
   - Cross-platform: macOS + Linux sha256 support
   - Usage: `bash scripts/evidence/collect.sh --type test_result --checklist-item 1.1 ...`

2. **validate_checklist.sh** (PATCHED v1.1)
   - Fixes: Line-skipping bug (nested read issue)
   - Uses: `nl -ba` + `sed -n` for lookahead
   - Validation: 5-line window for evidence comments

### Component 2: Layer 1 Hook

**File**: `.claude/hooks/pre_tool_use.sh`

**Trigger**: Before `Write` or `Edit` tool on checklist files

**Logic**:
```bash
if [[ "$TOOL_NAME" =~ (Write|Edit) && "$TOOL_PARAMS" =~ ACCEPTANCE_CHECKLIST ]]; then
  # Check: Recent evidence collected (within 1 hour)?
  RECENT_EVIDENCE=$(find .evidence -name "*.yml" -mmin -60 | wc -l)

  if [[ $RECENT_EVIDENCE -eq 0 ]]; then
    echo "❌ No evidence collected recently"
    echo "Before marking [x], collect evidence first:"
    echo "  bash scripts/evidence/collect.sh ..."

    # CI-aware: Don't block in non-interactive mode
    if [[ -z "${CI:-}" ]]; then
      read -r RESPONSE
      [[ "$RESPONSE" =~ ^[Yy]$ ]] || exit 1
    fi
  fi
fi
```

**Features**:
- CI/non-interactive mode support (`NONINTERACTIVE=1`)
- Cross-platform file timestamp check (Python fallback)
- Non-blocking warning (allows override)

### Component 3: Layer 2 Hook

**File**: `.claude/hooks/phase_transition.sh`

**Trigger**: Phase transitions (e.g., `Phase3 → Phase4`)

**Logic**:
```bash
CURRENT_PHASE="$1"  # e.g., Phase3
TARGET_PHASE="$2"   # e.g., Phase4

# Step 1: Check Learning Items captured
RECENT_LEARNING=$(find .learning/items -name "*.yml" -mmin -60 | wc -l)

if [[ $RECENT_LEARNING -eq 0 ]]; then
  echo "⚠️  No Learning Items captured in last hour"
  echo "Recommendation: bash scripts/learning/capture.sh ..."
  # CI: Auto-proceed
fi

# Step 2: Validate checklist (if Phase 4+)
if [[ "$TARGET_PHASE" =~ Phase[4-7] ]]; then
  bash scripts/evidence/validate_checklist.sh "$CHECKLIST_FILE"
fi

# Step 3: Generate phase summary
echo "✅ Phase $CURRENT_PHASE completed"
echo "   Evidence: $PHASE_EVIDENCE items"
echo "   Learning: $RECENT_LEARNING items"
```

**Features**:
- Auto-captures learning context
- Validates checklist before Phase 4+
- Generates phase completion report

### Component 4: Layer 3 Audit

**File**: `scripts/pre_merge_audit_v2.sh`

**Trigger**: Before merge (Phase 5/7)

**Checks** (7 validations):
1. Legacy `pre_merge_audit.sh` (configuration)
2. Evidence validation (all [x] have proof)
3. Checklist completion rate (≥90%)
4. Learning Items count (≥1 per phase recommended)
5. Auto-fix rollback capability (snapshots exist)
6. KPI compliance (tools available)
7. Root documents limit (≤7 .md files)

**Hard Blocks**:
- ⛔ Evidence validation fails
- ⛔ Completion rate <90%
- ⛔ Root documents >7

### Component 5: Auto-fix v2 with Rollback

**File**: `scripts/learning/auto_fix_v2.py`

**Key Features**:
```python
# Before any auto-fix:
snapshot_name = create_snapshot("Before fix: XXX")
# → Creates git stash
# → Saves metadata to $CE_HOME/.ce_snapshots/

try:
    apply_auto_fix(command)
except Exception:
    # Auto-rollback on failure
    rollback_snapshot(snapshot_name)
    # → Logs to .kpi/rollback.log for KPI tracking
```

**Fixes Applied** (v1.1):
- Directory unified: `$CE_HOME/.ce_snapshots` (not `$HOME`)
- No-changes case handled gracefully
- Rollback events logged for KPI

### Component 6: KPI Dashboard

**File**: `scripts/kpi/weekly_report.sh`

**Metrics** (4 KPIs):
1. **Auto-fix Success Rate**: `(total - rollbacks) / total × 100%` (target: ≥80%)
2. **MTTR** (Mean Time To Repair): Average hours from error to fix (target: <24h)
3. **Learning Reuse Rate**: Learning items referenced in commits (target: ≥30%)
4. **Evidence Compliance**: `items_with_evidence / completed_items × 100%` (target: 100%)

**Fixes Applied** (v1.1):
- Cross-platform MTTR calculation (Python datetime)
- Evidence window = 5 lines (consistent with validator)
- Rollback log integration

---

## 📋 Integration with 7-Phase Workflow

### Phase 1: Discovery & Planning (Enhanced)

**Existing Requirements**:
- Branch check (Rule 0)
- Requirements discussion
- Technical discovery
- Impact assessment
- Architecture planning

**New Requirements** (Anti-Hollow Gate):
1. **Acceptance Checklist must define ≥3 verification items**
   ```markdown
   ## Acceptance Criteria
   - [ ] 1.1 Evidence collection works for all 3 types
   - [ ] 1.2 Validation script catches missing evidence
   - [ ] 1.3 Pre-commit hook blocks hollow commits
   ```

2. **Each criteria must be measurable** (no vague "implement X")
   - ✅ Good: "validate_checklist.sh exits 0 for valid checklist"
   - ❌ Bad: "checklist validation works"

### Phase 2: Implementation (Enhanced)

**Existing Requirements**:
- AI autonomous coding
- No user prompts for tech decisions

**New Requirements** (Anti-Hollow Gate):
1. **Hook Integration Points**
   - Register `.claude/hooks/pre_tool_use.sh` in settings.json
   - Register `.claude/hooks/phase_transition.sh` in settings.json

2. **Evidence Collection During Development**
   - After writing tests → `collect.sh --type test_result`
   - After code review → `collect.sh --type code_review`

### Phase 3: Testing (Enhanced)

**Existing Requirements**:
- Static checks (`scripts/static_checks.sh`)
- Performance tests (<2s for hooks)

**New Requirements** (Anti-Hollow Gate):
1. **Evidence Collection Mandatory**
   ```bash
   # Run tests
   pytest tests/ -v > /tmp/test_output.log

   # Collect evidence
   bash scripts/evidence/collect.sh \
     --type test_result \
     --checklist-item 1.1 \
     --description "Unit tests for evidence system" \
     --file /tmp/test_output.log
   ```

2. **Update Checklist with Evidence**
   ```markdown
   - [x] 1.1 Evidence collection works
   <!-- evidence: EVID-2025W44-001 -->
   ```

### Phase 4: Review (Enhanced)

**Existing Requirements**:
- `scripts/pre_merge_audit.sh`
- Manual code review

**New Requirements** (Anti-Hollow Gate):
1. **Evidence Validation Mandatory** ⛔
   ```bash
   bash scripts/evidence/validate_checklist.sh \
     docs/ACCEPTANCE_CHECKLIST_anti_hollow_gate.md

   # Must exit 0 to proceed
   ```

2. **Checklist Completion ≥90%** ⛔
   - If <90%, identify why items incomplete
   - Update PLAN.md if scope changed

### Phase 5: Release (Enhanced)

**Existing Requirements**:
- CHANGELOG.md update
- Version consistency (6 files)

**New Requirements** (Anti-Hollow Gate):
1. **Enhanced Pre-Merge Audit** ⛔
   ```bash
   bash scripts/pre_merge_audit_v2.sh

   # Checks:
   # 1. Legacy audit
   # 2. Evidence validation
   # 3. Completion rate ≥90%
   # 4. Learning Items ≥1/phase
   # 5. Auto-fix capability
   # 6. KPI tools available
   # 7. Root docs ≤7
   ```

2. **KPI Baseline Established**
   ```bash
   bash scripts/kpi/weekly_report.sh > .kpi/baseline_2025W44.md
   ```

### Phase 6: Acceptance (Enhanced)

**Existing Requirements**:
- User confirmation

**New Requirements** (Anti-Hollow Gate):
1. **Evidence Summary Report**
   ```bash
   # Generate summary
   find .evidence/2025W44 -name "*.yml" | wc -l
   # Output: "Collected 15 evidence items"
   ```

2. **Zero Hollow Implementations Verified**
   - All [x] items have evidence
   - All scripts have calling hooks/workflows

### Phase 7: Closure (Enhanced)

**Existing Requirements**:
- Cleanup temp files
- Version consistency check
- User says "merge"

**New Requirements** (Anti-Hollow Gate):
1. **Learning Items Archived**
   ```bash
   # Verify learning items exist
   find .learning/items -name "*anti_hollow_gate*.yml"
   # Should find ≥3 items
   ```

2. **Evidence Retention Policy Applied**
   ```bash
   # Evidence retention: 90 days
   # (Auto-cleanup script in future)
   ```

---

## 🎯 Success Criteria

### Functional Requirements

1. **Evidence System**
   - ✅ Can collect 3 types of evidence (test_result, code_review, command_output)
   - ✅ Evidence IDs follow format `EVID-2025W44-{SEQ}`
   - ✅ Validation script detects missing evidence
   - ✅ Works on macOS + Linux

2. **Anti-Hollow Gate**
   - ✅ Layer 1: Prompts for evidence before checklist edits
   - ✅ Layer 2: Validates checklist at phase transitions
   - ✅ Layer 3: Blocks merge if evidence missing or <90% complete

3. **Integration**
   - ✅ Hooks registered in `.claude/settings.json`
   - ✅ Pre-commit calls `validate_checklist.sh`
   - ✅ CI runs `pre_merge_audit_v2.sh`

4. **Learning System**
   - ✅ Auto-captures learning on phase transitions
   - ✅ Empty test data cleaned up (8 files)
   - ✅ Real usage data starts accumulating

5. **KPI Dashboard**
   - ✅ Generates 4 metrics weekly
   - ✅ Cross-platform compatible
   - ✅ Baseline established

### Non-Functional Requirements

1. **Performance**
   - Pre-commit hook: <500ms for evidence validation
   - Phase transition hook: <2s total execution
   - KPI report: <10s generation time

2. **Usability**
   - Clear error messages with fix instructions
   - CI/non-interactive mode support
   - Documentation complete

3. **Reliability**
   - Cross-platform (macOS + Linux)
   - Handles edge cases (no evidence, no checklist, etc.)
   - Auto-fix has rollback safety

### Verification Methods

1. **Unit Tests**
   ```bash
   # Test evidence collection
   bash tests/test_evidence_collection.sh

   # Test validation
   bash tests/test_checklist_validation.sh
   ```

2. **Integration Tests**
   ```bash
   # Test full workflow
   bash tests/test_anti_hollow_gate_integration.sh
   ```

3. **Manual Verification**
   - Try to commit without evidence → Should block
   - Try to transition phases without learning → Should warn
   - Try to merge with <90% checklist → Should block

---

## 📊 Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Hooks don't trigger in Claude Code | HIGH | Also integrate in git hooks (pre-commit) |
| CI environment differences | MEDIUM | Use NONINTERACTIVE=1 mode |
| Cross-platform script failures | MEDIUM | Python fallbacks for date/hash operations |
| Evidence index corruption | LOW | Atomic writes + backup before changes |

### Process Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Too strict validation blocks development | MEDIUM | Allow override with confirmation |
| Learning capture overhead | LOW | Auto-capture in background |
| KPI calculation errors | LOW | Manual verification for first month |

---

## 📅 Implementation Timeline

### Week 1: Foundation
- Day 1-2: Evidence system (collect.sh, validate_checklist.sh)
- Day 3-4: Layer 1 hook (pre_tool_use.sh)
- Day 5-6: Integration testing
- Day 7: Bug fixes

### Week 2: Enforcement
- Day 8-9: Layer 2 hook (phase_transition.sh)
- Day 10-12: Layer 3 audit (pre_merge_audit_v2.sh)
- Day 13-14: CI integration + testing

### Week 3: Intelligence
- Day 15-16: Auto-fix v2 with rollback
- Day 17-18: Skills configuration
- Day 19-20: Learning auto-capture
- Day 21: End-to-end testing

### Week 4: Metrics & Polish
- Day 22-24: KPI dashboard
- Day 25-26: Documentation
- Day 27: UAT
- Day 28: Production deployment

---

## 🔗 Dependencies

### Internal Dependencies
- Existing 7-Phase workflow (CLAUDE.md)
- Workflow Guardian (scripts/workflow_guardian.sh)
- Static checks (scripts/static_checks.sh)
- Git hooks infrastructure

### External Dependencies
- git ≥2.20
- python3 ≥3.7
- jq ≥1.6
- bc (for KPI calculations)

### Optional Dependencies
- flock (for concurrent evidence collection)
- shellcheck (for script validation)

---

## 📚 References

### Documentation
- Original Plan: `docs/ANTI_HOLLOW_GATE_COMPLETE_IMPLEMENTATION_PLAN.md`
- Patched Plan: `docs/ANTI_HOLLOW_GATE_IMPLEMENTATION_V1.1_PATCHED.md`
- ChatGPT Review: (external document shared by user)

### Related Issues
- Issue: "v8.0 Learning System not used in actual development"
- Issue: "Workflow Guardian allows hollow implementations"
- Issue: "Skills configured but never trigger"

---

**Status**: ✅ Phase 1 Discovery Complete
**Next Phase**: Phase 2 - Implementation
**Estimated Completion**: 4 weeks from start date
