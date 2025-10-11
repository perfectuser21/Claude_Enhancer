# P0 Discovery Decision Tree

> **Purpose**: Visual guide for navigating P0 decisions and choosing the right approach.

---

## 🌳 Main Decision Flow

```
START: New Development Task
         |
         v
    Is it a coding task?
         |
    +----+----+
    |         |
   NO        YES
    |         |
    v         v
 Skip P0   Continue to P0
           (Discovery)
              |
              v
      Run Technical Spikes
         (2-7 spikes)
              |
              v
      Assess Feasibility
              |
              v
      +------+-------+
      |      |       |
     GO   NO-GO   NEEDS-DECISION
      |      |       |
      v      v       v
     P1   Terminate  User Decision
              |       |
              v       v
       Alternative   Once decided
        Solution      → GO or NO-GO
```

---

## 🔬 Technical Spike Decision Tree

### How many spikes do I need?

```
What's the feature complexity?
         |
    +----+----+----------+
    |         |          |
  Simple   Standard   Complex
    |         |          |
    v         v          v
  2-3      3-5         5-7
 spikes   spikes     spikes
    |         |          |
    +----+----+----------+
              |
              v
      For each spike:
         Is it passing?
              |
         +----+----+
         |         |
        YES       NO
         |         |
         v         v
     Continue   Fix or
                 NO-GO
```

### Spike Selection Criteria

```
Start with critical unknowns
         |
         v
    Can we build core functionality?  ← Spike 1 (MUST)
         |
         v
    Does it integrate with existing? ← Spike 2 (MUST)
         |
         v
    +----+----+
    |         |
 Standard  Complex?
    |         |
    v         v
    |    Performance OK?    ← Spike 3
    |         |
    |         v
    |    Security safe?     ← Spike 4
    |         |
    |         v
    |    Scalability?       ← Spike 5
    |         |
    |         v
    |    Deployment OK?     ← Spike 6
    |         |
    |         v
    |    Backward compat?   ← Spike 7
    |         |
    +----+----+
         |
         v
    All critical spikes pass?
         |
    +----+----+
    |         |
   YES       NO
    |         |
    v         v
   GO      NO-GO or
            NEEDS-DECISION
```

---

## ⚠️ Risk Assessment Decision Tree

### How to categorize risks?

```
Identify potential risk
         |
         v
    What's the probability?
         |
    +----+----+----+
    |    |    |    |
   <10% 10-30% 30-60% >60%
    |    |    |    |
    v    v    v    v
   LOW  LOW  MED  HIGH
         |
         v
    What's the impact?
         |
    +----+----+----+
    |         |         |
  Minor    Moderate   Severe
  (LOW)    (MEDIUM)   (HIGH)
    |         |         |
    v         v         v
    |    Severity =     |
    |  P% × Impact     |
    +----+----+--------+
              |
              v
      Final Severity?
              |
    +----+----+----+
    |         |         |
   LOW     MEDIUM     HIGH
    |         |         |
    v         v         v
 Monitor  Mitigate   Must Fix
  Accept   During    Before GO
           P3
```

### Risk Response Strategy

```
Risk identified
       |
       v
   Can we mitigate?
       |
  +----+----+
  |         |
 YES       NO
  |         |
  v         v
Is it      Is impact
cost-      acceptable?
effective?    |
  |      +----+----+
  |     YES       NO
  v      |         |
Mitigate Accept   NO-GO
  |      |         |
  +------+---------+
         |
         v
    Document in
   Risk Register
```

---

## 📊 GO/NO-GO Decision Matrix

### Primary Decision Tree

```
All spikes passed?
         |
    +----+----+
    |         |
   YES       NO
    |         |
    v         |
Risks        |
mitigable?   |
    |         |
+---+---+     |
|       |     |
YES    NO     |
|       |     |
v       v     v
|       +-----+
|             |
v             v
Benefits    NO-GO
justify       |
cost?         v
|        Alternative
+---+---+ Solutions?
|       |     |
YES    NO  +--+--+
|       |  |     |
v       v YES   NO
|       | |     |
GO      | v     v
        |Defer  Terminate
        NO-GO
```

### Evaluation Matrix Decision

```
Calculate weighted score
    (see matrix formula)
         |
         v
    Score result?
         |
    +----+----+----+
    |    |    |    |
  <2.0 2.0-2.9 3.0-3.9 ≥4.0
    |    |    |    |
    v    v    v    v
  NO-GO NEEDS GO   GO
         DEC  (caution) (strong)
```

**Formula**: Σ(Score × Weight) for all dimensions

---

## 🎯 Implementation Strategy Selection

### Architecture Decision Tree

```
How many components affected?
         |
    +----+----+----+
    |         |         |
   1-2      3-5       6+
(Simple) (Standard) (Complex)
    |         |         |
    v         v         v
    |         |    Need distributed
    |         |    coordination?
    |         |         |
    |         |    +----+----+
    |         |   YES       NO
    |         |    |         |
    |         |    v         v
    |         | Phased   Direct
    |         | Rollout  Migration
    |         |
    +----+----+----+
              |
              v
    Breaking changes?
              |
         +----+----+
         |         |
        YES       NO
         |         |
         v         v
    Versioned  Direct
    Migration  Update
```

### Rollout Strategy Decision

```
Risk level?
     |
+----+----+----+
|    |    |    |
LOW MED HIGH CRIT
|    |    |    |
v    v    v    v
|    |    |    Phase by phase
|    |    |    with rollback
|    |    Feature flag
|    |    + monitoring
|    Staged rollout
|    (10→50→100%)
Direct deployment
+ basic monitoring
```

---

## 🔄 NEEDS-DECISION Resolution Tree

### When to use NEEDS-DECISION?

```
Technical feasibility validated?
         |
    +----+----+
    |         |
   YES       NO
    |         |
    v         v
Multiple     More
viable      spikes
options?    needed
    |         |
+---+---+     v
|       |   NO-GO
YES    NO    (for now)
|       |
v       v
|      GO
|    (clear
v     path)
NEEDS-
DECISION
    |
    v
Present options
    |
    v
Get user input
    |
    v
+---+---+
|       |
GO    NO-GO
```

### Decision Point Template

```
For each decision point:
         |
         v
    Option count?
         |
    +----+----+----+
    |         |         |
    2        3        4+
    |         |         |
    v         v         v
Binary    Multi-   Needs
Choice   Choice   Breakdown
    |         |         |
    v         v         v
Pros/Cons for each option
         |
         v
    Recommend one
         |
         v
    User decides
```

---

## 📏 Time Estimation Decision Tree

### P0 Time Budget

```
Feature type?
     |
+----+----+----+----+
|         |         |
Bug     Feature   Arch
Fix              Change
|         |         |
v         v         v
1-2h    3-4h     4-6h
|         |         |
v         v         v
What's the complexity factor?
         |
    +----+----+----+
    |         |         |
  Well-    Some     High
  known   unknown  unknown
  (1.0x)  (1.2x)   (1.5x)
    |         |         |
    v         v         v
Base × Factor = P0 Time
         |
         v
    Add buffer (20%)
         |
         v
    Final estimate
```

### Spike Time Budget

```
Per spike:
     |
     v
Type of validation?
     |
+----+----+----+
|         |         |
Quick   Standard  Deep
Test    Test    Research
|         |         |
v         v         v
5-10min 15-20min 30-45min
     |
     v
Total spike time =
Σ(individual spikes)
     |
     v
Should be ≤ 60%
of total P0 time
```

---

## 🚦 Quality Gate Decision Tree

### Is P0 ready for approval?

```
Check structure
     |
     v
All sections present?
     |
+----+----+
|         |
YES       NO → Add missing sections
|
v
Check spikes
|
v
≥ 2 spikes with results?
|
+----+----+
|         |
YES       NO → Run more spikes
|
v
Check risks
|
v
Risks assessed & mitigated?
|
+----+----+
|         |
YES       NO → Complete risk analysis
|
v
Check decision
|
v
Clear GO/NO-GO/NEEDS-DEC?
|
+----+----+
|         |
YES       NO → Make decision
|
v
Check next steps
|
v
P1 transition defined?
|
+----+----+
|         |
YES       NO → Add next steps
|
v
✅ P0 READY
|
v
Create .gates/00.ok
```

---

## 🔀 Alternative Solution Decision Tree

### When NO-GO is chosen

```
Why NO-GO?
     |
+----+----+----+
|         |         |
Tech    Business   Time
Issue    Issue   Constraint
|         |         |
v         v         v
|         |    Can we defer?
|         |         |
|         |    +----+----+
|         |   YES       NO
|         |    |         |
|         |    v         v
|         | Defer    Terminate
|         | until X    |
|    ROI too low?     |
|         |            |
|    +----+----+       |
|   YES       NO       |
|    |         |       |
|    v         v       |
| Terminate  Revise    |
|            scope     |
|                      |
Alternative           |
tech exists?          |
|                     |
+---+---+             |
|       |             |
YES    NO             |
|       |             |
v       v             v
Try    Terminate   Document
new                rationale
approach
```

---

## 📊 Example Decision Walkthroughs

### Example 1: Simple Bug Fix

```
Task: Fix login button spacing
     ↓
Is it coding? YES
     ↓
P0 needed? YES (always for coding)
     ↓
Spikes:
  1. Can replicate bug? ✅
  2. CSS fix works? ✅
     ↓
Risks: LOW (visual only)
     ↓
Score: 4.2/5
     ↓
Decision: ✅ GO
     ↓
Time: 1 hour P0, 2 hours total
```

### Example 2: New Feature

```
Task: Add user authentication
     ↓
Is it coding? YES
     ↓
P0 needed? YES
     ↓
Spikes:
  1. OAuth integration? ✅
  2. Session management? ✅
  3. Security audit pass? ✅
  4. Performance OK? ⚠️ (needs optimization)
     ↓
Risks: MEDIUM (security implications)
     ↓
Score: 3.5/5
     ↓
Decision: ✅ GO (with caution)
     ↓
Conditions:
  - Security review in P5
  - Performance test in P4
     ↓
Time: 4 hours P0, 20 hours total
```

### Example 3: Architecture Change

```
Task: Migrate to microservices
     ↓
Is it coding? YES
     ↓
P0 needed? YES (high complexity)
     ↓
Spikes:
  1. Service isolation? ✅
  2. Inter-service comm? ✅
  3. Data consistency? ⚠️ (eventual consistency)
  4. Migration path? ✅
  5. Rollback plan? ✅
  6. Performance impact? ❌ (25% latency increase)
     ↓
Risks: HIGH (breaking changes, perf)
     ↓
Score: 2.8/5
     ↓
Decision: ⚠️ NEEDS-DECISION
     ↓
Options:
  A: Full migration (risky)
  B: Phased approach (slower)
  C: Defer until v2.0
     ↓
User chooses: Option B
     ↓
Decision: ✅ GO (phased approach)
     ↓
Time: 6 hours P0, 80+ hours total
```

---

## 🎨 Visual Decision Symbols

### Status Indicators
- ✅ **GO** - Proceed to next phase
- ❌ **NO-GO** - Stop or redirect
- ⚠️ **NEEDS-DECISION** - User input required
- 🔄 **IN-PROGRESS** - Still evaluating
- ⏸️ **DEFERRED** - Wait for condition

### Risk Levels
- 🟢 **LOW** - Minimal concern
- 🟡 **MEDIUM** - Manageable with mitigation
- 🔴 **HIGH** - Must address before GO
- ⚫ **CRITICAL** - Blocking issue

### Complexity
- 🔵 **SIMPLE** - 1-2 hours
- 🟣 **STANDARD** - 3-4 hours
- 🔶 **COMPLEX** - 4-6 hours
- 🔺 **CRITICAL** - 6+ hours

---

## 🧭 Navigation Guide

### Where am I in the process?

```
┌─────────────────────────────────────┐
│  P0 Discovery Phase                 │
├─────────────────────────────────────┤
│                                     │
│  ☐ Problem defined                  │
│  ☐ Spikes completed (≥2)            │
│  ☐ Risks assessed                   │
│  ☐ Decision made                    │
│  ☐ Next steps defined               │
│                                     │
├─────────────────────────────────────┤
│  Current step: _____________        │
│  Blockers: _________________        │
│  Next action: ______________        │
└─────────────────────────────────────┘
```

### Quick Self-Check

```
Am I stuck? Use this diagnostic:

Can't define problem?
  → Read user requirements again
  → Interview stakeholders

Can't design spikes?
  → Ask: "What's the biggest unknown?"
  → Start with simplest validation

Spikes failing?
  → Is the approach fundamentally wrong?
  → Try alternative technical solution

Can't assess risks?
  → Use RICE framework
  → Review similar past projects

Can't decide GO/NO-GO?
  → Calculate evaluation matrix
  → If score < 3.0, likely NO-GO
  → If score ≥ 4.0, likely GO
  → If 3.0-3.9, review risks again
```

---

## 📋 Quick Reference Checklist

Use this at each decision point:

### Before Starting P0
- [ ] Task is a coding task (not just discussion)
- [ ] Clear problem statement available
- [ ] Access to testing environment
- [ ] Time budget allocated (1-6 hours)

### During Technical Spikes
- [ ] Each spike tests one specific thing
- [ ] Commands are executable
- [ ] Results are documented
- [ ] Failures are explained

### During Risk Assessment
- [ ] Risks are specific (not generic)
- [ ] Probability quantified (%)
- [ ] Impact quantified (HIGH/MED/LOW)
- [ ] Mitigation plans actionable

### Before Making Decision
- [ ] All critical spikes completed
- [ ] Risk severity calculated
- [ ] Evaluation matrix filled out
- [ ] Benefits quantified
- [ ] Alternative solutions considered

### Before Submitting P0
- [ ] Structure matches template
- [ ] Decision is clear (GO/NO-GO/NEEDS-DECISION)
- [ ] Next steps defined
- [ ] Ready to create .gates/00.ok

---

## 🆘 Decision Tree Troubleshooting

### "I can't decide how many spikes"
→ Follow this tree: Simple (2-3) → Standard (3-5) → Complex (5-7)

### "Spikes contradict each other"
→ Re-examine assumptions. May need NEEDS-DECISION.

### "All spikes pass but it feels risky"
→ Check risk assessment. May have missed a risk category.

### "Evaluation score is borderline (3.0)"
→ Run 1-2 more spikes to increase confidence.

### "User won't decide (NEEDS-DECISION)"
→ Provide clearer pros/cons. Add recommendation.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-11
**Owner**: Technical Writer Agent

*Use this decision tree alongside the P0 template and quick reference for complete guidance.*
