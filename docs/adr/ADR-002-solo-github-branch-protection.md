# ADR-002: Solo-Adapted GitHub Branch Protection Strategy

**Status**: Accepted
**Date**: 2025-10-10
**Deciders**: Claude Enhancer Team
**Context**: v5.4.0 Workflow Unification

---

## Context and Problem Statement

Claude Enhancer is designed for solo developers who want production-grade quality without team overhead. Traditional GitHub Branch Protection requires human reviewers, which blocks automation and creates friction for solo workflows.

**Core Tension**:
- **Need**: Production-grade protection (quality, security, compliance)
- **Constraint**: Solo developer (no reviewers available)
- **Goal**: Enable full automation while maintaining quality gates

**Key Question**: How do we configure Branch Protection for solo use without sacrificing quality?

---

## Decision Drivers

- **Automation-Friendly**: Claude can auto-merge without waiting
- **Quality Assurance**: Same rigor as team workflows
- **Solo Optimization**: No unnecessary team features
- **CI/CD First**: Replace human review with automated checks
- **Rollback Safety**: Can revert quickly if needed
- **Compliance Ready**: Audit trail for future team growth

---

## Considered Options

### Option 1: Standard Team Configuration
**Approach**: Use GitHub's recommended team settings

```json
{
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  },
  "enforce_admins": false
}
```

**Pros**:
- Battle-tested settings
- Future-proof for team growth
- Industry best practice

**Cons**:
- ❌ Blocks automation completely
- ❌ Solo developer can't merge anything
- ❌ Creates fake PR approval workflows
- ❌ Slows development significantly

**Verdict**: ❌ Rejected - Incompatible with solo workflow

---

### Option 2: No Protection (Full Trust)
**Approach**: Disable all branch protection, rely on local git hooks

```bash
# No GitHub Branch Protection
# Only local .git/hooks enforcement
```

**Pros**:
- Maximum flexibility
- Zero GitHub overhead
- Fast iteration

**Cons**:
- ❌ No server-side enforcement
- ❌ Hooks can be bypassed
- ❌ No audit trail
- ❌ Risk of accidental direct commits
- ❌ Hard to enforce in future team

**Verdict**: ❌ Rejected - Insufficient protection

---

### Option 3: Solo-Adapted Protection with CI Gates (Selected)
**Approach**: 0 reviewers + comprehensive CI status checks

```json
{
  "required_pull_request_reviews": null,  // No human reviewers
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "ShellCheck Analysis",
      "Python Linting",
      "Unit Tests",
      "Security Scanning",
      "Quality Gate",
      "Performance Benchmarks",
      "Documentation Validation",
      "Git Workflow Validation",
      "Overall Quality Gate"
    ]
  },
  "enforce_admins": true,  // Even owner must pass checks
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

**Pros**:
- ✅ Automation-friendly (0 reviewers)
- ✅ Quality enforced by CI (9 checks)
- ✅ Owner accountability (enforce_admins)
- ✅ Clean history (linear, no force push)
- ✅ Audit trail (GitHub API logs)
- ✅ Easy to add team later

**Cons**:
- Requires robust CI/CD setup
- CI failures block merging
- Initial setup complexity

**Verdict**: ✅ **Selected** - Best balance

---

## Decision Outcome

We adopt **Solo-Adapted Branch Protection** with the following configuration:

### Complete Configuration

```json
{
  "protection": {
    "enabled": true,
    "required_status_checks": {
      "strict": true,
      "checks": [
        {
          "context": "ShellCheck Analysis",
          "app_id": -1
        },
        {
          "context": "Python Linting",
          "app_id": -1
        },
        {
          "context": "Unit Tests",
          "app_id": -1
        },
        {
          "context": "Integration Tests",
          "app_id": -1
        },
        {
          "context": "Security Scanning",
          "app_id": -1
        },
        {
          "context": "Performance Benchmarks",
          "app_id": -1
        },
        {
          "context": "Documentation Validation",
          "app_id": -1
        },
        {
          "context": "Git Workflow Validation",
          "app_id": -1
        },
        {
          "context": "Overall Quality Gate",
          "app_id": -1
        }
      ]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": null,
    "restrictions": null,
    "required_linear_history": true,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "block_creations": false,
    "required_conversation_resolution": false,
    "lock_branch": false,
    "allow_fork_syncing": false
  }
}
```

### Key Design Principles

#### 1. Replace Human Review with CI
**Traditional**:
- 2 human reviewers
- Manual code inspection
- Subjective quality judgment

**Solo-Adapted**:
- 9 automated CI checks
- Objective quality metrics (≥8.0/10)
- Deterministic pass/fail

#### 2. Owner Accountability
```json
"enforce_admins": true
```

**Rationale**: Even the repository owner (solo developer) must pass all checks. This prevents "emergency bypasses" that compromise quality.

**Trade-off**: Slightly longer fix time for critical bugs, but maintains discipline.

#### 3. Linear History Enforcement
```json
"required_linear_history": true
```

**Benefit**: Clean, reviewable history without merge commits
**Process**: Always squash or rebase before merge

#### 4. No Force Push
```json
"allow_force_pushes": false
```

**Protection**: Prevents accidental history rewriting on main
**Alternative**: Use rollback scripts for reverts

---

## Consequences

### Positive

#### For Solo Developer
- ✅ **Full Automation**: Claude can merge PRs automatically
- ✅ **No Fake Approvals**: No need to click "Approve" yourself
- ✅ **Faster Iteration**: Pass CI → Merged
- ✅ **Peace of Mind**: Can't accidentally break main

#### For Quality
- ✅ **Objective Standards**: 9 automated checks
- ✅ **Consistent Enforcement**: Same rules every time
- ✅ **Audit Trail**: All decisions logged in GitHub
- ✅ **Rollback Safety**: Clean history makes reverts easy

#### For Future
- ✅ **Team Ready**: Easy to add reviewers later
- ✅ **Compliance**: Audit trail already exists
- ✅ **Scalable**: Can handle multiple developers

### Negative

#### Challenges
- ⚠️ **CI Dependency**: GitHub Actions must be reliable
- ⚠️ **Setup Cost**: Initial CI configuration effort
- ⚠️ **Debug Time**: Failed checks require investigation

#### Risks
- ⚠️ **CI Outage**: Blocks merging during GitHub outages
- ⚠️ **False Positives**: Overly strict checks might block valid changes
- ⚠️ **Learning Curve**: Understanding why checks fail

---

## Mitigation Strategies

### Risk 1: CI Outage
**Problem**: GitHub Actions down = Cannot merge

**Mitigation**:
1. **Emergency Override**: Document procedure to temporarily disable protection
2. **Local Testing**: All checks can run locally before pushing
3. **Graceful Degradation**: Non-critical checks are optional
4. **Status Page**: Monitor GitHub status proactively

### Risk 2: False Positives
**Problem**: Valid changes blocked by overly strict rules

**Mitigation**:
1. **Configurable Thresholds**: Quality gate at 7.0 (not 9.0)
2. **Override Mechanism**: Document when/how to adjust rules
3. **Continuous Tuning**: Review failed checks monthly
4. **Escape Hatches**: Allow specific file exemptions

### Risk 3: Learning Curve
**Problem**: Developer confused by check failures

**Mitigation**:
1. **Clear Error Messages**: CI outputs actionable guidance
2. **Documentation**: Each check has troubleshooting guide
3. **Local Validation**: Run checks before pushing
4. **Progressive Rollout**: Start with warnings, then errors

---

## Implementation Plan

### Phase 1: CI Setup (P3)
- [ ] Create `.github/workflows/ci-workflow-v5.4.yml`
- [ ] Implement all 9 status check jobs
- [ ] Test locally and in feature branch
- [ ] Verify status checks appear in GitHub

### Phase 2: Protection Configuration (P6)
- [ ] Generate JSON config from template
- [ ] Apply via GitHub API (gh api)
- [ ] Verify protection rules in GitHub UI
- [ ] Test with sample PR

### Phase 3: Validation (P6)
- [ ] Attempt direct push to main (should fail)
- [ ] Create PR with failing checks (should block)
- [ ] Create PR with passing checks (should allow auto-merge)
- [ ] Test rollback procedure

### Phase 4: Documentation (P6)
- [ ] Document emergency override procedure
- [ ] Create troubleshooting guide for common failures
- [ ] Add runbook for CI maintenance
- [ ] Update CLAUDE.md with new workflow

---

## Monitoring and Success Metrics

### Metrics to Track

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Auto-Merge Success Rate** | >95% | PRs merged without manual intervention |
| **CI Failure Rate** | <10% | False positive rate |
| **Time to Merge** | <10min | From PR creation to merge |
| **Protection Bypasses** | 0 | Owner overrides per month |
| **Rollback Frequency** | <1/month | Reverts due to bad merges |

### Success Criteria
- ✅ Claude can merge PRs automatically
- ✅ No quality degradation vs. manual review
- ✅ Developer velocity maintained or improved
- ✅ Audit trail passes compliance review

---

## Future Considerations

### When to Revisit

**Trigger 1: Adding Team Members**
- Action: Add `required_approving_review_count: 1`
- Reason: Team needs human oversight

**Trigger 2: Compliance Requirements**
- Action: Add CODEOWNERS, increase checks
- Reason: Regulatory demands

**Trigger 3: CI Reliability Issues**
- Action: Reduce check count, add fallbacks
- Reason: Unblock development

### Potential Enhancements
- **Merge Queue**: For multiple concurrent PRs
- **Auto-rebase**: Keep PRs up-to-date automatically
- **Conditional Checks**: Different rules per file type
- **Performance Budgets**: Block PRs that slow down system

---

## References

- [GitHub Branch Protection API](https://docs.github.com/en/rest/branches/branch-protection)
- [Claude Enhancer CI Workflow](../../.github/workflows/ci-workflow-v5.4.yml)
- [P0 Exploration Report](../P0_EXPLORATION_REPORT.md) - Section 3
- [scripts/setup_branch_protection.sh](../../scripts/setup_branch_protection.sh)

---

## Appendix: Configuration Script

```bash
#!/usr/bin/env bash
# Apply Solo-Adapted Branch Protection
# Usage: ./setup_branch_protection.sh [branch_name]

BRANCH="${1:-main}"
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO}/branches/${BRANCH}/protection" \
  --input branch-protection.json

echo "✅ Branch protection applied to $BRANCH"
```

---

## Approval

**Decision Made By**: Claude Enhancer Team
**Approved**: 2025-10-10
**Effective Date**: Immediate (v5.4.0)
**Review Date**: 2025-11-10 (1 month post-implementation)
