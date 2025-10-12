# Rollback Quick Reference Guide
**Claude Enhancer v6.2 Enforcement Implementation**

---

## 🚨 Emergency Rollback (One Command)

```bash
./.workflow/scripts/emergency_rollback.sh "performance issues"
```

**Duration**: ~30 seconds
**Effect**: Reverts to v6.1, preserves all data

---

## 📊 When to Rollback?

### ⚠️ Immediate Rollback (Critical)
```
├─ Data loss detected
├─ Security breach
├─ Git corruption
└─ Hook failures >50%
```
**Action**: Run `emergency_rollback.sh` NOW

---

### 🔴 Urgent Rollback (Performance)
```
├─ Hook time >1000ms (p95)
├─ Error rate >15%
└─ System unresponsive
```
**Action**: Rollback within 4 hours

---

### 🟡 Planned Rollback (Quality)
```
├─ User satisfaction <3.0/5.0 (3 days)
├─ Adoption rate <40% (4 weeks)
└─ Workflow complaints
```
**Action**: Rollback within 1 week

---

### 🟢 Monitor (No Action)
```
├─ Hook time <500ms
├─ User satisfaction >=3.0
└─ Error rate <10%
```
**Action**: Continue monitoring

---

## 🔧 Rollback Process (Automated)

```
emergency_rollback.sh
    ↓
[1/7] Create backup
    ├─ .ce/ → .workflow/backups/
    ├─ .gates/ → .workflow/backups/
    └─ Git hooks → backups/
    ↓
[2/7] Restore git hooks
    ├─ pre-commit (v6.1)
    └─ commit-msg (v6.1)
    ↓
[3/7] Archive infrastructure
    ├─ .ce/ → .workflow/archives/
    └─ .gates/ → .workflow/archives/
    ↓
[4/7] Remove new Claude hooks
    ├─ branch_init.sh (deleted)
    ├─ collect_agent_evidence.sh (deleted)
    └─ ... (6 files removed)
    ↓
[5/7] Revert configuration
    ├─ gates.yml (v6.1)
    ├─ config.yml (v6.1)
    └─ .gitignore (v6.1)
    ↓
[6/7] Verify rollback
    ├─ Test commit (should work)
    ├─ Git integrity check
    └─ Performance test (<500ms)
    ↓
[7/7] Create notice
    └─ ROLLBACK_NOTICE.md
```

---

## 📋 Verification Checklist

Run after rollback:
```bash
./.workflow/scripts/verify_rollback.sh
```

### Expected Results
```
✓ [1/4] Commits work without enforcement
✓ [2/4] Git integrity OK
✓ [3/4] Hook performance <500ms
✓ [4/4] Workflow scripts functional

Result: VERIFICATION SUCCESSFUL
```

---

## 🔍 What Gets Preserved?

### ✅ Permanent (Never Deleted)
```
.workflow/archives/enforcement_*/
├── ce/                    # All task metadata
└── gates/                 # All gate evidence

.workflow/backups/rollback_*/
├── Pre-rollback snapshots
└── Git hooks backup

.workflow/logs/
└── enforcement_*.log      # Execution logs
```

### 🗑️ Removed (Safe to Delete)
```
.ce/tmp/                   # Temporary files
.gates/*/tmp/              # Temporary evidence
.workflow/logs/*.pid       # Process IDs
```

---

## 📈 Gradual Rollout Plan

### Week 1: Canary (10% users)
```yaml
Target: Internal team (3-5 devs)
Success:
  - Hook time <500ms
  - Satisfaction >=4.0
  - Zero critical bugs
Decision: Continue or rollback
```

### Week 2-3: Beta (50% users)
```yaml
Target: Early adopters
Success:
  - Hook time <500ms
  - Satisfaction >=3.5
  - Error rate <8%
Decision: Continue or rollback
```

### Week 4+: Full (100% users)
```yaml
Target: All users
Success:
  - Hook time <500ms
  - Satisfaction >=3.0
  - Adoption >80%
Decision: Stabilize or rollback
```

---

## 🎯 Affected Files (35 total)

### New Infrastructure (18 files)
```
.ce/
├── config.yml
└── archive/

.gates/{task_id}/
├── metadata.json
├── 00.ok
└── agent_evidence.json

.claude/hooks/
├── branch_init.sh
├── collect_agent_evidence.sh
├── phase_enforcer.sh
├── gate_archiver.sh
├── parallel_limit_enforcer.sh
└── user_satisfaction_tracker.sh

.git/hooks/
├── pre-commit.enhanced
└── post-commit.evidence

docs/
├── ENFORCEMENT_GUIDE.md
├── ROLLBACK_PROCEDURE.md
├── MIGRATION_CHECKLIST.md
└── AFFECTED_FILES_AND_ROLLBACK_PLAN.md
```

### Modified Files (17 files)
```
Configuration (5):
├── .workflow/gates.yml
├── .workflow/config.yml
├── .ce/task.yml
├── .claude/config.yaml
└── .gitignore

Hooks (3):
├── .git/hooks/pre-commit
├── .git/hooks/commit-msg
└── .claude/hooks/branch_helper.sh

Workflow (4):
├── .workflow/executor.sh
├── .workflow/phase_validator.py
├── .workflow/cli/lib/common.sh
└── .workflow/scripts/sign_gate.sh

CI/CD (3):
├── .github/workflows/ci-enhanced-5.3.yml
├── .github/workflows/positive-health.yml
└── .github/PULL_REQUEST_TEMPLATE.md

Monitoring (2):
├── .workflow/metrics.jsonl
└── scripts/capability_snapshot.sh
```

---

## 📞 Emergency Contacts

### Self-Service (Level 1)
```bash
# Emergency rollback
./emergency_rollback.sh "reason"

# Verify success
./verify_rollback.sh

# Generate report
./generate_incident_report.sh
```
**Duration**: <30 minutes

---

### Team Support (Level 2)
```
Contact: @devops-team
Channel: #claude-enhancer
SLA: <2 hours
```

---

### Management (Level 3+)
```
Engineering Manager: @eng-manager
VP Engineering: @vp-eng
SLA: <4 hours (L3), <24h (L4)
```

---

## 🧪 Post-Rollback Testing

### Manual Tests
```bash
# Test 1: Basic commit
echo "test" > test.txt
git add test.txt
git commit -m "test"
# Expected: SUCCESS (no enforcement)

# Test 2: Performance
time git commit --allow-empty -m "perf test"
# Expected: <200ms

# Test 3: Workflow
.workflow/executor.sh P1
# Expected: P1 executes normally
```

---

## 📝 Incident Report

After rollback, generate report:
```bash
./.workflow/scripts/generate_incident_report.sh
```

Creates: `docs/INCIDENT_REPORT_YYYYMMDD.md`

Fill in:
- Root cause analysis
- User impact assessment
- Corrective actions
- Re-deployment plan

---

## ✅ Re-Deployment Criteria

Before re-deploying v6.2:

### Must Fix
- [ ] Root cause resolved
- [ ] Regression tests added
- [ ] Performance optimized (<500ms p95)
- [ ] Documentation updated

### Must Verify
- [ ] All tests pass
- [ ] Peer review approved
- [ ] Canary deployment successful (10% users, 1 week)

### Must Communicate
- [ ] Release notes published
- [ ] Training materials ready
- [ ] Support team briefed

---

## 🎓 Learn More

- **Full Plan**: `docs/AFFECTED_FILES_AND_ROLLBACK_PLAN.md`
- **User Guide**: `docs/ENFORCEMENT_GUIDE.md`
- **Migration**: `docs/MIGRATION_CHECKLIST.md`

---

*Last Updated: 2025-10-11*
*Version: 1.0*
