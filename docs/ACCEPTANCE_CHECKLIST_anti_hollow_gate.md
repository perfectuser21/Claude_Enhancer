# Acceptance Checklist: Anti-Hollow Gate Full Integration

**Feature**: Anti-Hollow Gate + Skills & Hooks Integration
**Branch**: `feature/anti-hollow-gate-full-integration`
**Date**: 2025-10-27

---

## 📋 Must-Have Criteria (P0)

### 1. Evidence System

- [x] 1.1 Evidence collection script works for all 3 types (test_result, code_review, command_output)
<!-- evidence: EVID-2025W44-001 -->

- [ ] 1.2 Evidence validation script correctly validates checklists

- [ ] 1.3 Evidence IDs follow ISO week format (EVID-2025W44-NNN)

- [ ] 1.4 Evidence storage structure created (.evidence/2025Wxx/)

- [ ] 1.5 Evidence index.json properly maintained

### 2. Anti-Hollow Gate Layer 1 (Pre-Tool-Use Hook)

- [ ] 2.1 Hook triggers before Write/Edit on checklist files

- [ ] 2.2 Hook checks for recent evidence collection (within 1 hour)

- [ ] 2.3 Hook prompts user if no evidence found

- [ ] 2.4 Hook supports CI/non-interactive mode (NONINTERACTIVE=1)

- [ ] 2.5 Hook works on both macOS and Linux

### 3. Anti-Hollow Gate Layer 2 (Phase Transition Hook)

- [ ] 3.1 Hook triggers on phase transitions (Phase N → Phase N+1)

- [ ] 3.2 Hook checks for recent Learning Items (within 1 hour)

- [ ] 3.3 Hook validates checklist completion before Phase 4+

- [ ] 3.4 Hook generates phase summary report

- [ ] 3.5 Hook supports CI/non-interactive mode

### 4. Anti-Hollow Gate Layer 3 (Enhanced Pre-Merge Audit)

- [ ] 4.1 Audit script calls legacy pre_merge_audit.sh first

- [ ] 4.2 Audit validates all [x] items have evidence comments

- [ ] 4.3 Audit checks checklist completion rate ≥90%

- [ ] 4.4 Audit verifies Learning Items exist (≥1 recommended)

- [ ] 4.5 Audit checks auto-fix rollback capability

- [ ] 4.6 Audit verifies KPI tools available (jq, bc)

- [ ] 4.7 Audit blocks if root documents >7

### 5. Auto-fix v2 with Rollback

- [ ] 5.1 Auto-fix creates git stash snapshot before fixes

- [ ] 5.2 Snapshot directory unified to $CE_HOME/.ce_snapshots

- [ ] 5.3 Rollback mechanism works on failure

- [ ] 5.4 Rollback events logged to .kpi/rollback.log

- [ ] 5.5 No-changes case handled gracefully

### 6. KPI Dashboard

- [ ] 6.1 KPI script generates 4 metrics (Auto-fix Success, MTTR, Learning Reuse, Evidence Compliance)

- [ ] 6.2 KPI calculations are cross-platform compatible (macOS + Linux)

- [ ] 6.3 KPI report includes weekly summary

- [ ] 6.4 KPI baseline established for first week

### 7. Integration with 7-Phase Workflow

- [ ] 7.1 CLAUDE.md updated with Anti-Hollow Gate requirements

- [ ] 7.2 Phase 1 requirements include ≥3 acceptance criteria

- [ ] 7.3 Phase 3 requires evidence collection for tests

- [ ] 7.4 Phase 4 requires evidence validation (hard block)

- [ ] 7.5 Phase 5 requires enhanced pre-merge audit (hard block)

- [ ] 7.6 Phase 6 requires evidence summary report

- [ ] 7.7 Phase 7 requires learning items archived

### 8. Hooks Registration

- [ ] 8.1 pre_tool_use.sh registered in .claude/settings.json

- [ ] 8.2 phase_transition.sh registered in .claude/settings.json

- [ ] 8.3 validate_checklist.sh called in pre-commit hook

- [ ] 8.4 pre_merge_audit_v2.sh integrated in CI workflow

### 9. Skills Configuration

- [ ] 9.1 checklist-validator skill configured

- [ ] 9.2 learning-capturer skill configured

- [ ] 9.3 evidence-collector skill configured

- [ ] 9.4 kpi-reporter skill configured

- [ ] 9.5 Skills auto-trigger on specified events

### 10. Documentation & Cleanup

- [ ] 10.1 P1_DISCOVERY document complete

- [ ] 10.2 ACCEPTANCE_CHECKLIST document complete (this file)

- [ ] 10.3 PLAN document complete

- [ ] 10.4 Empty Learning Items cleaned (8 test files)

- [ ] 10.5 README updated with Anti-Hollow Gate section

- [ ] 10.6 CHANGELOG.md updated with v8.1.0 changes

---

## 📋 Should-Have Criteria (P1)

### 11. Concurrent Safety

- [ ] 11.1 Evidence collection uses flock for concurrent writes

- [ ] 11.2 Index updates are atomic

### 12. Evidence Retention

- [ ] 12.1 Evidence retention policy script created

- [ ] 12.2 Auto-cleanup cron job configured (90 days)

### 13. Skills Advanced Features

- [ ] 13.1 Skills log execution to .skills/execution.log

- [ ] 13.2 Skills have error recovery mechanisms

### 14. KPI Visualization

- [ ] 14.1 KPI trend analysis over multiple weeks

- [ ] 14.2 KPI alert on regression

---

## 📋 Could-Have Criteria (P2)

### 15. Evidence Search

- [ ] 15.1 Full-text search across evidence files

- [ ] 15.2 Evidence by type filtering

### 16. Phase Parallelization

- [ ] 16.1 Phase dependency graph defined

- [ ] 16.2 Parallel phase execution support

### 17. Notion Integration

- [ ] 17.1 KPI sync to Notion dashboard

- [ ] 17.2 Evidence export to Notion

---

## 🧪 Testing Criteria

### 18. Unit Tests

- [ ] 18.1 Test evidence collection for all 3 types

- [ ] 18.2 Test evidence validation with valid/invalid checklists

- [ ] 18.3 Test ISO week ID generation

- [ ] 18.4 Test cross-platform compatibility (macOS + Linux)

### 19. Integration Tests

- [ ] 19.1 Test full workflow: collect → validate → audit

- [ ] 19.2 Test phase transition with learning capture

- [ ] 19.3 Test auto-fix with rollback on failure

- [ ] 19.4 Test KPI generation with mock data

### 20. Manual Verification

- [ ] 20.1 Try commit without evidence → Should block

- [ ] 20.2 Try phase transition without learning → Should warn

- [ ] 20.3 Try merge with <90% checklist → Should block

- [ ] 20.4 Try merge with missing evidence → Should block

---

## 🎯 Performance Criteria

### 21. Performance Targets

- [ ] 21.1 Pre-commit hook executes in <500ms

- [ ] 21.2 Phase transition hook executes in <2s

- [ ] 21.3 Pre-merge audit executes in <10s

- [ ] 21.4 KPI report generates in <10s

---

## 📊 Success Metrics

### 22. Quantitative Metrics

- [ ] 22.1 Hollow Implementation Rate = 0% (no features without integration)

- [ ] 22.2 Evidence Compliance = 100% (all [x] have evidence)

- [ ] 22.3 Learning System Usage > 0 items/week

- [ ] 22.4 Auto-fix Success Rate ≥80% (baseline TBD)

- [ ] 22.5 MTTR <24h (baseline TBD)

### 23. Qualitative Metrics

- [ ] 23.1 Code quality: No hollow implementations pass review

- [ ] 23.2 Developer experience: CI works without hanging

- [ ] 23.3 Cross-platform: Works on macOS + Linux

- [ ] 23.4 Documentation: Complete and actionable

---

## ✅ Acceptance Sign-off

### Criteria Met
- Must-Have (P0): [ ] 10/10 sections complete
- Should-Have (P1): [ ] 4/4 sections complete
- Could-Have (P2): [ ] 3/3 sections complete (optional)

### Verification
- Unit Tests: [ ] Pass
- Integration Tests: [ ] Pass
- Manual Tests: [ ] Pass
- Performance Tests: [ ] Pass

### Stakeholder Approval
- [ ] Technical Review Complete
- [ ] Documentation Review Complete
- [ ] User Acceptance Testing Complete

### Ready for Production
- [ ] All Must-Have criteria met (P0)
- [ ] All Should-Have criteria met (P1)
- [ ] Zero critical bugs
- [ ] Documentation complete

---

**Completion Rate**: 0% (0/77 items)
**Status**: 🟡 In Progress - Phase 1
**Target Completion**: Week 4 (Day 28)

---

## 📝 Notes

### Evidence Collection Examples

After implementing a feature:
```bash
# Run tests
pytest tests/test_evidence.py -v > /tmp/test_output.log

# Collect evidence
bash scripts/evidence/collect.sh \
  --type test_result \
  --checklist-item 1.1 \
  --description "Unit tests for evidence collection" \
  --file /tmp/test_output.log

# Output: EVID-2025W44-001
```

Update checklist:
```markdown
- [x] 1.1 Evidence collection script works
<!-- evidence: EVID-2025W44-001 -->
```

### Validation

Before commit:
```bash
bash scripts/evidence/validate_checklist.sh \
  docs/ACCEPTANCE_CHECKLIST_anti_hollow_gate.md

# Expected: Exit 0 if all [x] have evidence
# Expected: Exit 1 if any [x] missing evidence
```

### Phase Transition

When moving from Phase 3 to Phase 4:
```bash
bash .claude/hooks/phase_transition.sh Phase3 Phase4

# Expected: Validates checklist completion
# Expected: Checks for learning items
# Expected: Generates phase summary
```

---

*This checklist will be updated as items are completed with evidence references.*
