# P0 Discovery Quick Reference Guide

> **Purpose**: Fast lookup for P0 document creation. Expand sections using the full template.

---

## ⚡ TL;DR: P0 in 5 Minutes

### What is P0?
**Discovery phase** that validates **feasibility** before detailed planning.

### Core Deliverable
A document answering: **"Should we build this? Can we build this?"**

### Minimum Viable P0
```markdown
1. ✅ Problem statement (2 paragraphs)
2. ✅ 2+ technical spikes with actual tests
3. ✅ Risk assessment (high/medium/low)
4. ✅ GO/NO-GO/NEEDS-DECISION conclusion
5. ✅ Next steps (transition to P1)
```

### Time Budget
- Simple feature: 1-2 hours
- Standard feature: 3-4 hours
- Complex feature: 4-6 hours

---

## 📋 P0 Document Outline (Copy-Paste)

```markdown
# P0 Discovery: [Feature Name]

**Phase**: P0 - Discovery
**Date**: 2025-MM-DD
**Target**: [One-line objective]

## 🎯 Executive Summary
- Problem: [2-3 sentences]
- Solution: [2-3 sentences]
- Feasibility: [GO/NO-GO/NEEDS-DECISION]

## 🔬 Technical Spike Verification

### Spike 1: [Core Question]
**Test**: `[command]`
**Result**: ✅/❌/⚠️
**Risk**: LOW/MEDIUM/HIGH

### Spike 2: [Second Question]
[Repeat structure]

## ⚠️ Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| TR-001 | 30% | HIGH | [plan] |

## 📊 Feasibility Conclusion

**Decision**: ✅ GO

**Rationale**:
1. [Reason 1]
2. [Reason 2]
3. [Reason 3]

**Expected Benefits**:
- [Metric 1]: X → Y (+Z%)

## 📋 Next Steps
- [ ] User approval
- [ ] Transition to P1
- [ ] Create PLAN.md
```

---

## 🔬 Technical Spike Template

### Essential Elements

```markdown
### Spike N: [Question to Answer]

**Hypothesis**: Can we [specific capability]?

**Verification**:
\```bash
# Actual command to test
command --with-flags
\```

**Expected**: [what success looks like]

**Actual Result**: [✅ PASS | ❌ FAIL | ⚠️ PARTIAL]

**Evidence**:
\```
[paste actual output]
\```

**Risk Assessment**:
- Probability: [%]
- Impact: [HIGH/MEDIUM/LOW]
- Mitigation: [specific action]
```

### Spike Quality Checklist
- [ ] Question is specific and testable
- [ ] Command is executable (someone can copy-paste)
- [ ] Output is included (not "it worked")
- [ ] Risk is quantified (not "might have issues")

---

## ⚠️ Risk Assessment Template

### Quick Risk Table

```markdown
| Risk ID | Description | P% | Impact | Severity | Mitigation |
|---------|-------------|-----|--------|----------|------------|
| TR-001 | [tech risk] | 30% | HIGH | 🔴 | [action] |
| BR-001 | [biz risk] | 20% | MED | 🟡 | [action] |
| TM-001 | [time risk] | 40% | LOW | 🟢 | [action] |
```

### Severity Calculation
- 🔴 HIGH: Probability × Impact ≥ HIGH
- 🟡 MEDIUM: Moderate probability or impact
- 🟢 LOW: Low probability and impact

### Mitigation Template
```markdown
**Mitigation for [Risk ID]**:
1. **Before P3**: [action]
2. **During P3**: [action]
3. **Rollback**: [command to undo]
```

---

## 📊 Feasibility Matrix (1-Minute Version)

| Dimension | Score | Weight | Calc |
|-----------|-------|--------|------|
| Tech Feasibility | 1-5 | 30% | S×W |
| Business Value | 1-5 | 25% | S×W |
| Complexity (inv) | 1-5 | 15% | S×W |
| Risk (inv) | 1-5 | 15% | S×W |
| Compatibility | 1-5 | 10% | S×W |
| ROI | 1-5 | 5% | S×W |
| **TOTAL** | - | 100% | **ΣSW** |

**Decision Rule**:
- ≥ 4.0 → Strong GO ✅
- 3.0-3.9 → GO with caution ⚠️
- 2.0-2.9 → NEEDS-DECISION 🤔
- < 2.0 → NO-GO ❌

---

## 🎯 GO/NO-GO Decision Template

### GO Decision ✅

```markdown
## 📊 Feasibility Conclusion

**Decision**: ✅ GO - Strong Approval

**Rationale**:
1. ✅ All technical spikes passed (5/5)
2. ✅ Risk level acceptable (2 LOW, 1 MEDIUM, 0 HIGH)
3. ✅ Clear business value (+40% efficiency)
4. ✅ Implementation time reasonable (~15 hours)
5. ✅ Backward compatible (no breaking changes)

**Conditions**:
- ✅ Complete P1 planning before P3
- ⚠️ Monitor performance during P4 testing

**Approval**: Ready to proceed to P1
```

### NO-GO Decision ❌

```markdown
## 📊 Feasibility Conclusion

**Decision**: ❌ NO-GO - Not Recommended

**Blocking Issues**:
1. ❌ Technical spike failed: [specific failure]
2. ❌ High risk with no mitigation: [risk]
3. ❌ Cost-benefit ratio unfavorable (20h for 5% gain)

**Alternative Recommendations**:
- Option A: [simpler approach]
- Option B: [different solution]
- Option C: Defer until [condition met]

**Termination Rationale**: [why stopping is best]
```

### NEEDS-DECISION 🤔

```markdown
## 📊 Feasibility Conclusion

**Decision**: ⚠️ NEEDS-DECISION - User Input Required

**Decision Points**:

1. **Architecture Choice**
   - Option A: [pros/cons]
   - Option B: [pros/cons]
   - **Recommended**: Option A because [reason]
   - **User Decision Required**: Yes/No + rationale

2. **Trade-off Resolution**
   - Trade-off: [description]
   - **Question**: [specific question for user]

**Timeline**: Awaiting decisions before P1
```

---

## 📋 P0→P1 Transition Checklist

### Before Marking P0 Complete

```bash
# 1. Validate P0 requirements met
grep -q "GO\|NO-GO\|NEEDS-DECISION" docs/P0_*.md
grep -q "Spike 1:" docs/P0_*.md
grep -q "Risk Assessment" docs/P0_*.md

# 2. Create gate marker (only if GO)
touch .gates/00.ok

# 3. Update phase
echo "P1" > .phase/current

# 4. Verify transition
cat .phase/current  # Should show: P1
```

### P0 Gate Requirements (.workflow/gates.yml)

```yaml
P0:
  must_produce:
    - "docs/P0_*_DISCOVERY.md"
    - "Feasibility conclusion (GO/NO-GO/NEEDS-DECISION)"
    - "≥ 2 technical spikes validated"
    - "Risk assessment complete"
  gates:
    - "P0 Discovery document exists"
    - "Clear feasibility conclusion"
    - "Technical spike count ≥ 2"
    - "Risk assessment complete (technical/business/time)"
```

---

## 🎨 Writing Style Quick Tips

### Do's ✅
- **Be Specific**: "Reduces time from 30min to 5min" not "faster"
- **Show Evidence**: Include actual command output
- **Quantify Risks**: "30% probability" not "might happen"
- **Be Honest**: Call out unknowns clearly

### Don'ts ❌
- **Avoid "Should Work"**: Prove it with spikes
- **No Vague Risks**: "Some issues" → "Query latency +15%"
- **Don't Skip Rollback**: Every change needs undo steps
- **No Analysis Paralysis**: Focus on critical unknowns

---

## 🔧 Common P0 Scenarios

### Scenario 1: New Feature
**Focus**: Technical feasibility + user value
**Spikes**: 3-5 (core tech + integration points)
**Risks**: Compatibility, complexity, time
**Time**: 3-4 hours

### Scenario 2: Bug Fix
**Focus**: Root cause + fix validation
**Spikes**: 2-3 (reproduction + fix verification)
**Risks**: Regression, side effects
**Time**: 1-2 hours

### Scenario 3: Performance Optimization
**Focus**: Current bottleneck + improvement potential
**Spikes**: 3-4 (profiling + optimization tests)
**Risks**: Breaking changes, diminishing returns
**Time**: 2-3 hours

### Scenario 4: Architecture Change
**Focus**: Migration path + backward compatibility
**Spikes**: 5-7 (new arch + migration + rollback)
**Risks**: High risk, breaking changes
**Time**: 4-6 hours

---

## 📏 P0 Quality Self-Check (30 Seconds)

```markdown
Quick validation before submitting P0:

Structure:
[ ] Title + metadata complete
[ ] Executive summary ≤ 1 page
[ ] ≥ 2 technical spikes
[ ] Risk assessment present
[ ] Clear GO/NO-GO/NEEDS-DECISION
[ ] Next steps defined

Content Quality:
[ ] Spikes have actual commands + output
[ ] Risks are quantified (not vague)
[ ] Decision is justified by data
[ ] Benefits are measurable
[ ] Rollback plan exists for high risks

Gate Compliance:
[ ] Matches .workflow/gates.yml requirements
[ ] Can create .gates/00.ok
[ ] Ready to transition to P1
```

---

## 🚀 Fast P0 Workflows

### Workflow 1: Express P0 (1 hour)
**Use when**: Small, well-understood feature

```markdown
1. Problem statement (5 min)
2. 2 quick spikes (30 min)
3. Risk table (10 min)
4. GO decision (5 min)
5. Next steps (5 min)
6. Formatting cleanup (5 min)
```

### Workflow 2: Standard P0 (3-4 hours)
**Use when**: Normal feature development

```markdown
1. Executive summary (20 min)
2. 3-4 detailed spikes (90 min)
3. Comprehensive risk assessment (45 min)
4. Feasibility matrix (30 min)
5. Implementation strategy (20 min)
6. Documentation polish (15 min)
```

### Workflow 3: Deep P0 (4-6 hours)
**Use when**: High-risk architectural change

```markdown
1. Problem analysis (30 min)
2. 5-7 thorough spikes (120 min)
3. Multi-dimensional risk analysis (60 min)
4. Alternative approaches (30 min)
5. Detailed evaluation matrix (30 min)
6. Implementation roadmap (30 min)
7. Review and refinement (30 min)
```

---

## 📚 Quick References

### Related Documents
- **Full Template**: [P0_enforcement_optimization_DISCOVERY_TEMPLATE.md](./P0_enforcement_optimization_DISCOVERY_TEMPLATE.md)
- **Gates Definition**: [.workflow/gates.yml](../.workflow/gates.yml)
- **Workflow Guide**: [CLAUDE.md](../CLAUDE.md)

### Example P0 Documents
- [P0_FULL_AUTOMATION_DISCOVERY.md](./P0_FULL_AUTOMATION_DISCOVERY.md) - Automation example
- [P0_AI_PARALLEL_DEV_DISCOVERY.md](./P0_AI_PARALLEL_DEV_DISCOVERY.md) - Complex architecture
- [P0_AUDIT_FIX_DISCOVERY.md](./P0_AUDIT_FIX_DISCOVERY.md) - Bug fix example

### Tools and Commands

```bash
# Start P0
echo "P0" > .phase/current

# Validate P0 document structure
grep -E "^##\s+(Executive Summary|Technical Spike|Risk|Feasibility|Next Steps)" docs/P0_*.md

# Check spike count
grep -c "^### Spike" docs/P0_*.md  # Should be ≥ 2

# Verify decision present
grep -E "(GO|NO-GO|NEEDS-DECISION)" docs/P0_*.md

# Complete P0
touch .gates/00.ok
echo "P1" > .phase/current
```

---

## 🎓 P0 Best Practices

### The "3 Spikes Rule"
Always validate at least 3 technical aspects:
1. **Core capability**: Can we build the main feature?
2. **Integration**: Does it work with existing systems?
3. **Performance**: Will it meet performance requirements?

### The "RICE" Risk Framework
- **Reach**: How many users/components affected?
- **Impact**: How severe if it goes wrong?
- **Confidence**: How sure are we of the approach?
- **Effort**: How much work is required?

### The "10-80-10 Rule"
- 10% of time: Executive summary
- 80% of time: Technical spikes + risk assessment
- 10% of time: Conclusion + next steps

### The "Explain to CEO" Test
Can you explain the GO/NO-GO decision to a non-technical person in 1 minute?
If not, your conclusion isn't clear enough.

---

## 🆘 Troubleshooting P0 Issues

### Issue: "I don't know what to test"
**Solution**: Ask "What's the biggest unknown that could block P3?"

### Issue: "Spikes are taking too long"
**Solution**: Limit each spike to 15-20 minutes. If longer, split into multiple spikes.

### Issue: "Too many risks to document"
**Solution**: Focus on HIGH risks only in P0. Document MEDIUM/LOW in P1.

### Issue: "Can't decide GO/NO-GO"
**Solution**: Use the evaluation matrix. Score < 3.0 = needs more spikes or is NO-GO.

### Issue: "User can't make decision"
**Solution**: Use NEEDS-DECISION. Present 2-3 options with clear pros/cons and recommendation.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-11
**Quick Reference Owner**: Technical Writer Agent

*Print this for desk reference or bookmark for quick access during P0 work.*
