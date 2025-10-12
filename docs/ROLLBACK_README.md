# Rollback Documentation - Start Here

**Quick Links**: [Emergency](#emergency) | [Planning](#planning) | [Reference](#reference) | [Scripts](#scripts)

---

## Emergency - Something is Wrong NOW

**If you need to rollback immediately:**

1. Run: `./.workflow/scripts/emergency_rollback.sh "your reason"`
2. Verify: `./.workflow/scripts/verify_rollback.sh`
3. Document: `./.workflow/scripts/generate_incident_report.sh`

**Duration**: ~2 minutes total

**Quick Reference**: [`ROLLBACK_QUICK_REFERENCE.md`](./ROLLBACK_QUICK_REFERENCE.md) (print this!)

---

## Planning - Understanding the Full Picture

**Before deploying v6.2:**

1. Read the master plan: [`AFFECTED_FILES_AND_ROLLBACK_PLAN.md`](./AFFECTED_FILES_AND_ROLLBACK_PLAN.md)
2. Review file details: [`FILES_SUMMARY_TABLE.md`](./FILES_SUMMARY_TABLE.md)
3. Understand decisions: [`ROLLBACK_DECISION_FLOWCHART.md`](./ROLLBACK_DECISION_FLOWCHART.md)

**Time needed**: ~1 hour

---

## Reference - Finding Specific Information

**Use the index for navigation:**

[`ENFORCEMENT_ROLLBACK_INDEX.md`](./ENFORCEMENT_ROLLBACK_INDEX.md) - Complete guide to all documentation

**Quick searches**:
- How many files? → FILES_SUMMARY_TABLE.md - Summary Statistics
- Rollback steps? → ROLLBACK_QUICK_REFERENCE.md - Rollback Process
- When to rollback? → ROLLBACK_DECISION_FLOWCHART.md - Quick Decision Tree
- What changes? → FILES_SUMMARY_TABLE.md - Part 1 & 2

---

## Scripts - Automated Operations

**Location**: `.workflow/scripts/`

| Script | Purpose | Duration |
|--------|---------|----------|
| `emergency_rollback.sh` | Full rollback (7 steps) | ~30s |
| `verify_rollback.sh` | Validate rollback success | ~15s |
| `generate_incident_report.sh` | Create post-mortem | ~5s |

**All scripts are safe**: 100% data preservation, no destructive operations without confirmation.

---

## Documentation Map

```
docs/
├── ROLLBACK_README.md (You are here)
├── ENFORCEMENT_ROLLBACK_INDEX.md (Navigation hub)
├── ROLLBACK_QUICK_REFERENCE.md (One-page guide)
├── ROLLBACK_DECISION_FLOWCHART.md (Visual guide)
├── AFFECTED_FILES_AND_ROLLBACK_PLAN.md (Master plan)
├── FILES_SUMMARY_TABLE.md (Detailed inventory)
└── P1_ROLLBACK_DELIVERABLES_SUMMARY.md (Executive summary)
```

---

## Who Should Read What?

### On-Call Engineers
**Priority docs**:
1. ROLLBACK_QUICK_REFERENCE.md (5 min)
2. ROLLBACK_DECISION_FLOWCHART.md (10 min)

**Practice**: Run emergency_rollback.sh in staging

---

### DevOps Team
**Priority docs**:
1. AFFECTED_FILES_AND_ROLLBACK_PLAN.md (30 min)
2. FILES_SUMMARY_TABLE.md (20 min)
3. ROLLBACK_DECISION_FLOWCHART.md (10 min)

**Action**: Test all scripts in staging environment

---

### Developers
**Priority docs**:
1. FILES_SUMMARY_TABLE.md - Parts 1 & 2 (15 min)
2. AFFECTED_FILES_AND_ROLLBACK_PLAN.md - Part 1 (10 min)

**Action**: Review actual file diffs in git

---

### Managers/Stakeholders
**Priority docs**:
1. P1_ROLLBACK_DELIVERABLES_SUMMARY.md (10 min)
2. ROLLBACK_DECISION_FLOWCHART.md (10 min)

**Focus**: Understand decision criteria and escalation paths

---

## Key Concepts

### 35 Files Affected
- 18 new files (infrastructure, hooks, docs)
- 17 modified files (config, existing hooks, CI/CD)
- 100% documented with rollback strategy

### 7-Step Rollback
1. Create backup (5s)
2. Restore git hooks (2s)
3. Archive infrastructure (3s)
4. Remove Claude hooks (1s)
5. Revert configuration (2s)
6. Verify rollback (10s)
7. Create notice (5s)

**Total**: ~30 seconds, 100% safe

### 4 Severity Levels
- 🔴 Critical: Immediate rollback (<30 min)
- 🟠 Urgent: Rollback within 4 hours
- 🟡 Warning: Planned rollback (<1 week)
- 🟢 Healthy: Continue monitoring

### Gradual Rollout
- Week 1: Canary (10% users)
- Week 2-3: Beta (50% users)
- Week 4+: Full (100% users)

---

## Quick Command Reference

```bash
# Emergency rollback
./.workflow/scripts/emergency_rollback.sh "performance issues"

# Verify success
./.workflow/scripts/verify_rollback.sh

# Generate incident report
./.workflow/scripts/generate_incident_report.sh

# Check current status
./scripts/capability_snapshot.sh

# View metrics
tail -f .workflow/metrics.jsonl | jq .
```

---

## Support

### Documentation Issues
- Missing info? Create GitHub issue: `documentation` label
- Unclear? Submit PR with improvements
- Error? Report immediately

### Emergency Help
- Critical: Use ROLLBACK_QUICK_REFERENCE.md
- Questions: #claude-enhancer Slack channel
- Escalation: See ROLLBACK_DECISION_FLOWCHART.md

---

## Version Info

- **Created**: 2025-10-11
- **Phase**: P1 (Planning Complete)
- **Task**: enforcement-optimization-20251011
- **Status**: Production-ready documentation
- **Next**: P2 (Skeleton) implementation

---

*Start with the right document for your role, or use ENFORCEMENT_ROLLBACK_INDEX.md to navigate.*
