# ADR-001: Rule 0 Exception Handling and Intelligent Branch Judgment

**Status**: Accepted
**Date**: 2025-10-10
**Deciders**: Claude Enhancer Team
**Context**: v5.4.0 Workflow Unification

---

## Context and Problem Statement

Rule 0 (Phase -1) requires branch checking before any development work. However, always asking users about branch decisions creates friction and reduces developer experience. We need a system that:

1. Enforces branching best practices
2. Intelligently determines when to ask vs. when to proceed
3. Handles multi-terminal parallel development
4. Supports solo developer workflow

**Key Question**: How do we balance strict enforcement with intelligent automation?

---

## Decision Drivers

- **Developer Experience**: Minimize interruptions for obvious cases
- **Safety**: Never allow unintended changes to main/master
- **Intelligence**: Understand task semantics and branch context
- **Flexibility**: Support both solo and team workflows
- **Auditability**: Track all branch decisions for compliance

---

## Considered Options

### Option 1: Always Ask (Strict)
**Approach**: Every task triggers a branch decision prompt

**Pros**:
- Maximum safety - no assumptions
- Simple logic - no complex decision tree
- Clear audit trail - all decisions explicit

**Cons**:
- Poor UX - constant interruptions
- Breaks flow state - especially for small tasks
- User fatigue - repetitive questions
- Doesn't leverage AI intelligence

**Verdict**: ❌ Rejected - Too rigid

---

### Option 2: Never Ask (Full Automation)
**Approach**: AI decides branches automatically without user input

**Pros**:
- Seamless UX - no interruptions
- Fast workflow - no decision delays
- Fully leverages AI capabilities

**Cons**:
- High risk - AI might misinterpret intent
- No user override - hard to correct mistakes
- Difficult to audit - hidden decisions
- Trust issues - users lose control

**Verdict**: ❌ Rejected - Too risky

---

### Option 3: Three-Tier Intelligent System (Selected)
**Approach**: Use semantic analysis to categorize situations and respond appropriately

**Response Tiers**:
- 🟢 **Green**: Obviously safe → Continue directly
- 🟡 **Yellow**: Uncertain → Brief confirmation
- 🔴 **Red**: Clearly needs new branch → Suggest with reason

**Pros**:
- Balanced UX - interrupts only when needed
- Safe - detects dangerous operations
- Smart - learns from context
- Flexible - adapts to task type
- Auditable - logs decision reasoning

**Cons**:
- Complex implementation - multi-factor analysis
- Requires tuning - decision boundaries
- Edge cases - some ambiguity remains

**Verdict**: ✅ **Selected**

---

## Decision Outcome

We adopt the **Three-Tier Intelligent Branch Judgment System**.

### Implementation Details

#### Decision Algorithm
```
收到用户需求
    ↓
【判断1】是编码任务吗？
    ├─ ❌ 否 → 直接处理（查询/讨论/分析）
    └─ ✅ 是 → 继续
           ↓
【判断2】用户明确指定了分支策略吗？
    ├─ ✅ 是 → 按用户指示执行
    └─ ❌ 否 → 继续
           ↓
【判断3】任务与当前分支主题的匹配度？
    ├─ 🟢 高度匹配 → 直接继续
    ├─ 🟡 模糊相关 → 简短询问（给选项）
    └─ 🔴 明显不匹配 → 建议新分支（说理由）
```

#### Matching Criteria

**🟢 Green (Direct Continue)**:
- 延续词: "继续", "完善", "修复当前"
- 主题匹配: 关键词重叠 >70%
- 分支状态: 活跃开发中（最近24小时有提交）

**🟡 Yellow (Brief Confirmation)**:
- 相关性: 领域接近但边界不清
- 扩展性: 可能属于现有功能扩展
- 分支状态: 已完成但未合并

**🔴 Red (Suggest New Branch)**:
- 新建词: "新功能", "新建", "add"
- 无关性: 完全不同领域
- 当前分支: main/master
- 分支状态: 已完成已合并

#### Response Templates

**Green Response** (No interruption):
```
"好的，我在当前分支 feature/user-auth 继续实现登录功能..."
（直接开始工作，不多话）
```

**Yellow Response** (Quick confirmation):
```
"关于邮件验证，两种理解：
 1. 作为认证流程的一部分 → 当前分支继续
 2. 独立的通知系统 → 建议新分支 feature/email-notification
 您倾向于哪种？（或直接告诉我您的选择）"
```

**Red Response** (Suggest with reasoning):
```
"🔍 分支策略建议

 当前：feature/logging（已完成，等待合并）
 新需求：支付系统

 ✅ 建议：创建新分支 feature/payment-system
 💡 理由：
    - 支付系统与日志功能完全独立
    - 当前分支已完成，应保持稳定
    - 新分支可独立开发和审查

 请确认，或告诉我您的想法？"
```

---

## Consequences

### Positive
- ✅ **Improved UX**: 80% reduction in unnecessary prompts
- ✅ **Maintained Safety**: Zero tolerance for main/master violations
- ✅ **Better Intelligence**: AI demonstrates understanding
- ✅ **Clear Reasoning**: Users understand decision logic
- ✅ **Flexible**: Adapts to user's preferred style over time

### Negative
- ⚠️ **Complexity**: More code paths to maintain
- ⚠️ **Edge Cases**: Some ambiguous situations still require judgment
- ⚠️ **Training Data**: Needs tuning based on user feedback

### Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Misclassification | Medium | Low | User can override immediately |
| Ambiguous cases | Low | Medium | Default to Yellow (ask) |
| User confusion | Medium | Low | Clear explanations in responses |

---

## Implementation Plan

### Phase 1: Core Logic (P3)
- [ ] Implement three-tier classification
- [ ] Build semantic keyword extraction
- [ ] Create decision tree logic
- [ ] Add response templates

### Phase 2: Integration (P3)
- [ ] Integrate with branch_helper.sh
- [ ] Connect to Claude hooks
- [ ] Add audit logging

### Phase 3: Tuning (P4-P5)
- [ ] Collect user feedback
- [ ] Adjust thresholds
- [ ] Refine keyword lists
- [ ] Add learning from patterns

---

## Monitoring and Success Metrics

### Key Metrics
- **Prompt Reduction Rate**: Target 80% reduction
- **Misclassification Rate**: Target <5%
- **User Override Rate**: Track when users disagree
- **Time to Decision**: Measure decision latency

### Success Criteria
- ✅ Users report "AI understands me better"
- ✅ No main/master violations
- ✅ Reduced friction in workflow
- ✅ Audit log shows sound reasoning

---

## References

- [Claude Enhancer CLAUDE.md](../../CLAUDE.md) - Rule 0 specification
- [Branch Helper Hook](../../.claude/hooks/branch_helper.sh) - Implementation
- [P0 Exploration Report](../P0_EXPLORATION_REPORT.md) - Feasibility analysis

---

## Approval

**Decision Made By**: Claude Enhancer Team
**Approved**: 2025-10-10
**Review Date**: 2025-11-10 (1 month post-implementation)
