# Rollback Decision Flowchart
**Visual guide for rollback decisions and procedures**

---

## 🎯 Quick Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│                    Issue Detected                           │
│              (Manual or Automated Alert)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Is it CRITICAL?                                            │
│  ├─ Data loss detected                                      │
│  ├─ Security breach                                         │
│  ├─ Git corruption                                          │
│  └─ Hook failures >50%                                      │
└────────┬────────────────────────────────────────────────────┘
         │
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    ▼         ▼
┌─────────────────────┐  ┌─────────────────────────────────────┐
│ 🚨 IMMEDIATE        │  │  Is performance >2x target?         │
│    ROLLBACK         │  │  └─ Hook time >1000ms (p95)         │
│                     │  │  └─ Error rate >15%                 │
│ Execute NOW:        │  │  └─ System unresponsive             │
│ emergency_rollback  │  └────────┬────────────────────────────┘
│                     │           │
│ SLA: <30 minutes    │      ┌────┴────┐
└─────────────────────┘      │         │
                            YES       NO
                             │         │
                             ▼         ▼
                    ┌─────────────────────┐  ┌──────────────────┐
                    │ 🔴 URGENT           │  │ Is satisfaction  │
                    │    ROLLBACK         │  │ <3.0 for 3 days? │
                    │                     │  │                  │
                    │ Schedule within:    │  │ Or adoption      │
                    │ 4 hours             │  │ <40% (4 weeks)?  │
                    │                     │  └────────┬─────────┘
                    │ SLA: <4 hours       │           │
                    └─────────────────────┘      ┌────┴────┐
                                                 │         │
                                                YES       NO
                                                 │         │
                                                 ▼         ▼
                                        ┌─────────────────┐  ┌─────────┐
                                        │ 🟡 PLANNED      │  │ 🟢 OK   │
                                        │    ROLLBACK     │  │ MONITOR │
                                        │                 │  │         │
                                        │ Schedule within:│  │ Continue│
                                        │ 1 week          │  │ watching│
                                        │                 │  └─────────┘
                                        │ SLA: <1 week    │
                                        └─────────────────┘
```

---

## 📊 Monitoring Dashboard (Conceptual)

```
╔════════════════════════════════════════════════════════════════════╗
║                  Claude Enhancer v6.2 Health                       ║
╚════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────┐
│ Performance Metrics                                              │
├──────────────────────────────────────────────────────────────────┤
│ Hook Execution Time (p50):  234ms  [████████░░] 47% of target   │
│ Hook Execution Time (p95):  421ms  [████████░░] 84% of target   │
│ Cache Hit Ratio:            87%    [█████████░] GOOD            │
│                                                                  │
│ Status: 🟢 HEALTHY                                               │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ Quality Metrics                                                  │
├──────────────────────────────────────────────────────────────────┤
│ Error Rate:                 6%     [███░░░░░░░] GOOD            │
│ User Satisfaction:          4.1/5  [████████░░] EXCELLENT       │
│ Adoption Rate:              73%    [███████░░░] GOOD            │
│                                                                  │
│ Status: 🟢 HEALTHY                                               │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ Enforcement Activity                                             │
├──────────────────────────────────────────────────────────────────┤
│ Evidence Collection Rate:   95%    [█████████░] EXCELLENT       │
│ Gate Archival Count:        23     [Last 7 days]                │
│ Active Tasks:               5      [Current]                    │
│                                                                  │
│ Status: 🟢 OPERATIONAL                                           │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ Rollback Triggers                                                │
├──────────────────────────────────────────────────────────────────┤
│ ⚠️ Critical:     0 active   [No immediate action needed]        │
│ ⚠️ Urgent:       0 active   [No urgent action needed]           │
│ ⚠️ Planned:      0 active   [No planned rollback]               │
│                                                                  │
│ Decision: CONTINUE MONITORING ✅                                 │
└──────────────────────────────────────────────────────────────────┘
```

**When ANY metric enters red zone → Alert triggers**

---

## 🚦 Alert Thresholds

### 🔴 Critical (Auto-Rollback)
```yaml
triggers:
  - hook_failures_rate: >50%     # More than half of commits fail
  - data_loss: detected          # ANY data loss
  - security_breach: detected    # ANY security issue
  - git_corruption: detected     # Git fsck fails

action: IMMEDIATE ROLLBACK
sla: <30 minutes
automation: emergency_rollback.sh (auto-triggered)
```

---

### 🟠 Urgent (Escalation)
```yaml
triggers:
  - hook_time_p95: >1000ms       # 2x target exceeded
  - error_rate: >15%             # 15% of commits error
  - system_unresponsive: true    # Hang detected

action: URGENT ROLLBACK
sla: <4 hours
escalation: DevOps team notified
automation: emergency_rollback.sh (manual trigger)
```

---

### 🟡 Warning (Monitor)
```yaml
triggers:
  - user_satisfaction: <3.0 for 3 days
  - adoption_rate: <40% after 4 weeks
  - hook_time_p95: >500ms && <1000ms

action: PLANNED ROLLBACK
sla: <1 week
decision: Team review + user feedback
automation: emergency_rollback.sh (scheduled)
```

---

### 🟢 Healthy (Continue)
```yaml
indicators:
  - hook_time_p95: <500ms
  - error_rate: <10%
  - user_satisfaction: >=3.0
  - adoption_rate: >=40%

action: CONTINUE MONITORING
automation: Daily health checks
```

---

## 🔧 Rollback Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Trigger Detection                                       │
│ ├─ Automated: Monitoring alerts                                 │
│ └─ Manual: User report                                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Execute Rollback Script                                 │
│                                                                  │
│   $ ./.workflow/scripts/emergency_rollback.sh "reason"          │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ [1/7] Create backup                            [✓ 5s]   │  │
│   │ [2/7] Restore git hooks                        [✓ 2s]   │  │
│   │ [3/7] Archive infrastructure                   [✓ 3s]   │  │
│   │ [4/7] Remove Claude hooks                      [✓ 1s]   │  │
│   │ [5/7] Revert configuration                     [✓ 2s]   │  │
│   │ [6/7] Verify rollback                          [✓ 10s]  │  │
│   │ [7/7] Create notice                            [✓ 5s]   │  │
│   │                                                          │  │
│   │ Total Duration: 28s                                      │  │
│   └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Verification                                             │
│                                                                  │
│   $ ./.workflow/scripts/verify_rollback.sh                      │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ ✓ [1/4] Commits work without enforcement               │  │
│   │ ✓ [2/4] Git integrity OK                               │  │
│   │ ✓ [3/4] Hook performance <500ms (187ms)                │  │
│   │ ✓ [4/4] Workflow scripts functional                    │  │
│   │                                                          │  │
│   │ Result: VERIFICATION SUCCESSFUL ✅                       │  │
│   └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Incident Report                                         │
│                                                                  │
│   $ ./.workflow/scripts/generate_incident_report.sh             │
│                                                                  │
│   Creates: docs/INCIDENT_REPORT_YYYYMMDD.md                     │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ ## Summary                                               │  │
│   │ - Date: 2025-10-11 14:23 UTC                            │  │
│   │ - Duration: 3 hours 15 minutes                          │  │
│   │ - Root Cause: [Performance degradation]                 │  │
│   │                                                          │  │
│   │ ## Metrics at Rollback                                  │  │
│   │ - Hook time p95: 1234ms (target: <500ms)               │  │
│   │ - Error rate: 18% (target: <10%)                       │  │
│   │                                                          │  │
│   │ ## Action Items                                         │  │
│   │ - [ ] Fix root cause                                    │  │
│   │ - [ ] Add regression test                               │  │
│   │ - [ ] Plan re-deployment                                │  │
│   └──────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Notification                                            │
│                                                                  │
│   Notify stakeholders:                                          │
│   ├─ Slack: #claude-enhancer                                    │
│   ├─ Email: dev-team@example.com                                │
│   └─ GitHub: Issue created                                      │
│                                                                  │
│   Message:                                                       │
│   "⚠️ Enforcement v6.2 has been rolled back to v6.1             │
│    due to [reason]. All data preserved. See                     │
│    ROLLBACK_NOTICE.md for details."                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📈 Gradual Rollout Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  WEEK 1: Canary (10%)                           │
│  Target: Internal team (3-5 developers)                         │
├─────────────────────────────────────────────────────────────────┤
│  Deploy → Monitor → Collect Feedback                            │
│                                                                  │
│  Success Criteria:                                              │
│  ✓ Hook time <500ms                                             │
│  ✓ Satisfaction >=4.0                                           │
│  ✓ Zero critical bugs                                           │
│                                                                  │
│  Decision Point: CONTINUE or ROLLBACK?                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ✅ PASS
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                WEEK 2-3: Beta (50%)                             │
│  Target: Early adopters + power users                           │
├─────────────────────────────────────────────────────────────────┤
│  Expand → Monitor → A/B Compare                                 │
│                                                                  │
│  Success Criteria:                                              │
│  ✓ Hook time <500ms                                             │
│  ✓ Satisfaction >=3.5                                           │
│  ✓ Error rate <8%                                               │
│  ✓ Adoption >60%                                                │
│                                                                  │
│  Decision Point: CONTINUE or ROLLBACK?                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ✅ PASS
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               WEEK 4+: Full (100%)                              │
│  Target: All users                                              │
├─────────────────────────────────────────────────────────────────┤
│  Deploy All → Stabilize → Continuous Monitor                    │
│                                                                  │
│  Success Criteria:                                              │
│  ✓ Hook time <500ms                                             │
│  ✓ Satisfaction >=3.0                                           │
│  ✓ Error rate <10%                                              │
│  ✓ Adoption >80%                                                │
│                                                                  │
│  Stabilization: 2 weeks                                         │
│  Rollback window: 30 days post-deployment                       │
└─────────────────────────────────────────────────────────────────┘
```

**At ANY stage**: If metrics fail → Rollback to previous stage

---

## 🔄 A/B Testing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              USER ASSIGNMENT (Hash-based)                       │
│                                                                  │
│   user_id hash % 2 == 0 → Control Group (v6.1)                 │
│   user_id hash % 2 == 1 → Treatment Group (v6.2)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────┐  ┌──────────────────────────┐
│     Control Group (50%)          │  │   Treatment Group (50%)  │
│     Enforcement v6.1             │  │   Enforcement v6.2       │
├──────────────────────────────────┤  ├──────────────────────────┤
│ Hook time: 187ms (p95)           │  │ Hook time: 421ms (p95)   │
│ Error rate: 4%                   │  │ Error rate: 6%           │
│ Satisfaction: 4.0                │  │ Satisfaction: 4.1        │
└────────────────┬─────────────────┘  └────────┬─────────────────┘
                 │                             │
                 └──────────┬──────────────────┘
                            │
                            ▼
                ┌───────────────────────────┐
                │  AFTER 4 WEEKS           │
                │  Compare Metrics          │
                └───────────┬───────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
           BETTER                   WORSE
                │                       │
                ▼                       ▼
    ┌─────────────────────┐  ┌─────────────────────┐
    │ Deploy to 100%      │  │ Rollback treatment  │
    │ (Success!)          │  │ (Keep v6.1)         │
    └─────────────────────┘  └─────────────────────┘
```

**Decision Criteria**:
- Treatment satisfaction >= Control
- Treatment error rate <= Control × 1.2
- Treatment performance <= Control × 1.5

---

## 📞 Escalation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Issue Severity                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    CRITICAL          URGENT          WARNING
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Level 1      │  │ Level 2      │  │ Level 3      │
│ Self-Service │  │ Team Lead    │  │ Eng Manager  │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ Action:      │  │ Contact:     │  │ Contact:     │
│ emergency_   │  │ @devops-team │  │ @eng-manager │
│ rollback.sh  │  │              │  │              │
│              │  │ Channel:     │  │ SLA:         │
│ SLA:         │  │ #ce-support  │  │ <4 hours     │
│ <30 minutes  │  │              │  │              │
│              │  │ SLA:         │  │ Decision:    │
│ Auto-trigger │  │ <2 hours     │  │ Plan fix or  │
│ if possible  │  │              │  │ defer        │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Escalation Path**:
1. **Self-service** (Level 1): Run emergency_rollback.sh
2. **Team support** (Level 2): Contact @devops-team if script fails
3. **Management** (Level 3): Escalate if business impact
4. **Executive** (Level 4): VP Engineering (only if strategic)

---

## ✅ Post-Rollback Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                  Rollback Complete                              │
│                  Now What?                                      │
└─────────────────────────────────────────────────────────────────┘

Immediate (Done by script):
  ✓ Git hooks restored
  ✓ Infrastructure archived
  ✓ Configuration reverted
  ✓ Verification passed
  ✓ Notice created

Within 1 hour:
  ⬜ Notify team (Slack + Email)
  ⬜ Create GitHub issue
  ⬜ Update status page

Within 4 hours:
  ⬜ Complete incident report
  ⬜ Schedule post-mortem meeting
  ⬜ Begin root cause analysis

Within 1 week:
  ⬜ Fix identified issues
  ⬜ Add regression tests
  ⬜ Update documentation
  ⬜ Plan re-deployment

Before re-deployment:
  ⬜ All tests pass
  ⬜ Peer review approved
  ⬜ Canary deployment plan ready
  ⬜ Team trained
```

---

## 📚 Related Documentation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| `AFFECTED_FILES_AND_ROLLBACK_PLAN.md` | Complete rollback strategy | Planning/Reference |
| `ROLLBACK_QUICK_REFERENCE.md` | One-page emergency guide | During incident |
| `ROLLBACK_DECISION_FLOWCHART.md` | Visual decision guide | Decision making |
| `FILES_SUMMARY_TABLE.md` | Detailed file inventory | Impact analysis |
| `ENFORCEMENT_GUIDE.md` | User-facing guide | User training |

---

## 🎓 Training Resources

### For Users
- **Document**: `docs/ENFORCEMENT_GUIDE.md`
- **Training**: [TBD: Video walkthrough]
- **Support**: #claude-enhancer Slack channel

### For DevOps
- **Rollback drill**: Run `emergency_rollback.sh` in staging
- **Incident response**: Review `INCIDENT_REPORT_*.md` examples
- **Monitoring**: Dashboard training session

### For Management
- **Metrics review**: Weekly dashboard review
- **Decision making**: Use this flowchart
- **Escalation**: Know when to escalate

---

*Last Updated: 2025-10-11*
*Version: 1.0*
*Part of Claude Enhancer v6.2 Enforcement Implementation*
