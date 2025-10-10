# ADR-003: Git Automation Trade-offs and Control Boundaries

**Status**: Accepted
**Date**: 2025-10-10
**Deciders**: Claude Enhancer Team
**Context**: v5.4.0 Workflow Unification

---

## Context and Problem Statement

Claude Enhancer aims to automate the entire development lifecycle (P0-P7), including Git operations. However, full automation creates risks:
- Unintended commits to wrong branches
- Automatic merges of broken code
- Loss of developer control and oversight

**Core Tension**:
- **Automation Goal**: Claude handles all Git operations (commit, push, PR, merge)
- **Safety Requirement**: Critical operations need human confirmation
- **User Experience**: Minimize friction while maintaining control

**Key Question**: What Git operations should be automated, and what requires user confirmation?

---

## Decision Drivers

- **Safety First**: Never surprise the user with destructive operations
- **Velocity**: Automate routine operations to increase speed
- **Configurability**: Users can adjust automation levels
- **Transparency**: Always explain what will happen before doing it
- **Reversibility**: All automated operations can be rolled back
- **Audit Trail**: Every operation logged for compliance

---

## Automation Spectrum Analysis

### Full Spectrum of Git Operations

```
Low Risk ←──────────────────────────────────→ High Risk
│                                                      │
git add          git push         git merge      git push --force
git commit       gh pr create     gh pr merge    git reset --hard
git status       git tag          git rebase     git branch -D
```

---

## Considered Options

### Option 1: Full Automation (No Confirmations)
**Approach**: Claude executes all Git operations automatically

```bash
# User: "Implement authentication feature"
# Claude does automatically:
1. git checkout -b feature/auth
2. [Development work]
3. git add .
4. git commit -m "feat(P3): Implement auth"
5. git push -u origin feature/auth
6. gh pr create
7. [Wait for CI]
8. gh pr merge --auto
9. git tag v5.4.0
10. git push origin v5.4.0
```

**Pros**:
- Maximum velocity
- True "AI pair programmer" experience
- Zero human intervention

**Cons**:
- ❌ High risk of unintended merges
- ❌ No human review checkpoint
- ❌ Accidental tag creation
- ❌ Users feel loss of control
- ❌ Hard to explain what happened

**Verdict**: ❌ Rejected - Too risky

---

### Option 2: No Automation (Manual Control)
**Approach**: Claude only writes code, user handles all Git operations

```bash
# User: "Implement authentication feature"
# Claude does:
1. Writes code
2. Says "Ready for commit. Please run: git add . && git commit"

# User manually executes all Git commands
```

**Pros**:
- Maximum control
- No surprises
- Familiar workflow

**Cons**:
- ❌ Defeats purpose of automation
- ❌ Requires Git expertise
- ❌ Slows development significantly
- ❌ Breaks flow state

**Verdict**: ❌ Rejected - Insufficient automation

---

### Option 3: Tiered Automation with Environment Variables (Selected)
**Approach**: Progressive automation levels controlled by environment variables

**Automation Tiers**:
| Level | Operations | Risk | User Confirms |
|-------|-----------|------|---------------|
| **Tier 1: Safe** | add, commit, status | Low | Never |
| **Tier 2: Push** | push, branch creation | Medium | Optional |
| **Tier 3: PR** | gh pr create | Medium | Optional |
| **Tier 4: Merge** | gh pr merge | High | Default: Yes |
| **Tier 5: Release** | tag, release | Critical | Default: Yes |

**Environment Variables**:
```bash
CE_EXECUTION_MODE=1     # Enable automation
CE_AUTO_PUSH=1          # Auto push to remote
CE_AUTO_PR=1            # Auto create PRs
CE_AUTO_MERGE=1         # Auto merge PRs (risky)
CE_AUTO_RELEASE=1       # Auto create tags (critical)
```

**Default Behavior** (Conservative):
```bash
# Out of the box
CE_EXECUTION_MODE=0     # Manual mode
CE_AUTO_PUSH=0          # Ask before push
CE_AUTO_PR=0            # Ask before PR
CE_AUTO_MERGE=0         # Always ask
CE_AUTO_RELEASE=0       # Always ask
```

**Power User Setup**:
```bash
# ~/.bashrc or project-specific
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=1
export CE_AUTO_PR=1
export CE_AUTO_MERGE=1    # For solo dev
export CE_AUTO_RELEASE=0  # Still careful with releases
```

**Pros**:
- ✅ Flexible: User controls automation level
- ✅ Safe defaults: Conservative out-of-box
- ✅ Progressive: Enable as trust builds
- ✅ Transparent: Clear what each variable does
- ✅ Auditable: All operations logged

**Cons**:
- Requires configuration learning
- More complex than binary choice

**Verdict**: ✅ **Selected** - Best balance

---

## Decision Outcome

We adopt **Tiered Automation with Environment Variables**.

### Detailed Operation Matrix

| Git Operation | Auto? | Condition | User Override |
|--------------|-------|-----------|---------------|
| `git add` | ✅ Yes | Always | No |
| `git commit` | ✅ Yes | Always | No |
| `git push` | ⚙️ Conditional | `CE_AUTO_PUSH=1` | Ask if unset |
| `gh pr create` | ⚙️ Conditional | `CE_AUTO_PR=1` | Ask if unset |
| `gh pr merge` | ⚙️ Conditional | `CE_AUTO_MERGE=1` | **Ask by default** |
| `git tag` | ⚙️ Conditional | `CE_AUTO_RELEASE=1` | **Ask by default** |
| `git push --force` | ❌ Never | N/A | **Must ask** |
| `git reset --hard` | ❌ Never | N/A | **Must ask** |
| `git branch -D` | ❌ Never | N/A | **Must ask** |

### Implementation Rules

#### Rule 1: Pre-Automation Check
```bash
before_git_operation() {
    local operation="$1"
    local risk_level="$2"

    # Check if execution mode enabled
    if [[ "${CE_EXECUTION_MODE:-0}" != "1" ]]; then
        log_info "Execution mode disabled. Please run manually:"
        log_info "  $operation"
        return 1
    fi

    # Check specific flag
    case "$risk_level" in
        low)
            return 0  # Always proceed
            ;;
        medium)
            # Check tier-specific flag
            ;;
        high)
            # Ask by default unless explicitly enabled
            ;;
        critical)
            # Always ask
            ;;
    esac
}
```

#### Rule 2: Explicit User Confirmation for High-Risk Ops
```bash
confirm_operation() {
    local operation="$1"
    local target="$2"

    echo "⚠️  About to: $operation"
    echo "   Target: $target"
    echo ""
    read -p "Proceed? (y/N): " confirm

    [[ "$confirm" =~ ^[Yy]$ ]]
}
```

#### Rule 3: Dry Run Mode
```bash
# Test automation without actual execution
export CE_DRY_RUN=1

# All scripts will show what they *would* do
# Example output:
# "DRY RUN: Would push to origin/feature/auth"
# "DRY RUN: Would create PR: feat: Add authentication"
```

---

## Consequences

### Positive

#### For Safety
- ✅ **Defense in Depth**: Multiple confirmation levels
- ✅ **No Surprises**: User controls what's automated
- ✅ **Rollback Ready**: All operations reversible
- ✅ **Audit Trail**: Every operation logged

#### For Velocity
- ✅ **Configurable Speed**: Trade safety for speed as needed
- ✅ **No Friction**: Routine ops (add/commit) never ask
- ✅ **Progressive Adoption**: Start conservative, increase as trust builds

#### For User Experience
- ✅ **User in Control**: Clear configuration model
- ✅ **Transparent**: Know what each flag does
- ✅ **Flexible**: Per-project or global settings
- ✅ **Discoverable**: Easy to understand hierarchy

### Negative

#### Complexity
- ⚠️ **More Configuration**: Users must learn variables
- ⚠️ **Context Switching**: Different projects may have different settings
- ⚠️ **Documentation Burden**: Need clear guides

#### Potential Confusion
- ⚠️ **Flag Interactions**: What if only CE_AUTO_MERGE=1 but not CE_AUTO_PR?
- ⚠️ **Defaults**: Users might not realize what's enabled

---

## Mitigation Strategies

### Strategy 1: Sensible Defaults
```bash
# Ship with safe defaults
# ~/.claude/default.env
CE_EXECUTION_MODE=0     # Explicitly disabled
CE_AUTO_PUSH=0
CE_AUTO_PR=0
CE_AUTO_MERGE=0
CE_AUTO_RELEASE=0
```

### Strategy 2: Progressive Enablement Guide
```markdown
# Quick Start (Safe)
export CE_EXECUTION_MODE=1

# After 10 successful commits
export CE_AUTO_PUSH=1

# After 5 successful PRs
export CE_AUTO_PR=1

# Solo developer comfort zone
export CE_AUTO_MERGE=1

# Production releases (still careful)
# Leave CE_AUTO_RELEASE=0
```

### Strategy 3: Pre-Flight Check Command
```bash
# Show current automation settings
$ claude-enhancer config show
╔════════════════════════════════════════╗
║   Claude Enhancer Configuration       ║
╠════════════════════════════════════════╣
║ Execution Mode:  ✅ ENABLED            ║
║ Auto Push:       ✅ ENABLED            ║
║ Auto PR:         ✅ ENABLED            ║
║ Auto Merge:      ⚠️  DISABLED (safe)   ║
║ Auto Release:    ⚠️  DISABLED (safe)   ║
╚════════════════════════════════════════╝

Automation Level: MEDIUM (recommended for solo)
```

### Strategy 4: Fail-Safe Mechanism
```bash
# Automatic downgrade on errors
if [[ $consecutive_failures -gt 3 ]]; then
    log_warning "3 automation failures detected"
    log_warning "Temporarily disabling auto-merge"
    export CE_AUTO_MERGE=0
fi
```

---

## Special Cases

### Case 1: Force Push
**Policy**: Never automate, always require explicit user command

```bash
git_force_push() {
    die "Force push must be done manually. This is intentional."
}
```

**Rationale**: Force push can destroy history. User must type it themselves.

### Case 2: Merge Conflicts
**Policy**: Abort automation, guide user to resolve manually

```bash
if git_merge_has_conflicts; then
    log_error "Merge conflicts detected"
    log_info "Automated merge aborted"
    log_info "Please resolve manually: git status"
    return 1
fi
```

### Case 3: Failed CI Checks
**Policy**: Abort auto-merge, inform user

```bash
if ! ci_checks_passed; then
    log_error "CI checks failed"
    log_info "Auto-merge blocked"
    log_info "Fix issues and CI will retry"
    return 1
fi
```

### Case 4: Emergency Rollback
**Policy**: Always require confirmation, even with CE_AUTO_RELEASE=1

```bash
rollback_to_version() {
    local version="$1"

    # Critical operation - ignore CE_AUTO_RELEASE
    confirm_operation "Rollback to $version" "Production" || return 1

    # Proceed with rollback
}
```

---

## Implementation Plan

### Phase 1: Environment Variable System (P3)
- [ ] Define all environment variables
- [ ] Create configuration loader
- [ ] Implement pre-flight checks
- [ ] Add audit logging

### Phase 2: Tiered Automation Scripts (P3)
- [ ] Implement auto_commit.sh (Tier 1)
- [ ] Implement auto_push.sh (Tier 2)
- [ ] Implement auto_pr.sh (Tier 3)
- [ ] Implement merge automation (Tier 4)
- [ ] Implement auto_release.sh (Tier 5)

### Phase 3: Safety Mechanisms (P3)
- [ ] Add dry-run mode
- [ ] Implement confirmation prompts
- [ ] Add fail-safe downgrades
- [ ] Create rollback procedures

### Phase 4: User Interface (P6)
- [ ] Create config show command
- [ ] Add setup wizard
- [ ] Write documentation
- [ ] Create video tutorial

---

## Monitoring and Success Metrics

### Key Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Automation Adoption Rate** | 70% | Users enable Tier 2+ |
| **False Automation Rate** | <5% | Unintended operations |
| **User Override Rate** | <10% | Manual intervention needed |
| **Rollback Frequency** | <1/month | Automated ops requiring revert |
| **User Satisfaction** | >8/10 | Survey score |

### Success Criteria
- ✅ Users report "feels safe and fast"
- ✅ No accidental data loss
- ✅ Clear understanding of what's automated
- ✅ Easy to enable/disable per project

---

## Future Enhancements

### Enhancement 1: Machine Learning Thresholds
Learn from user behavior to auto-adjust automation levels

```python
# If user never intervenes in 50 PRs
if auto_merge_success_rate > 0.98:
    suggest_enable(CE_AUTO_MERGE)
```

### Enhancement 2: Context-Aware Automation
Different settings for different branches

```yaml
# .claude/automation.yml
branches:
  main:
    auto_merge: false   # Always careful with main
  develop:
    auto_merge: true    # More relaxed for develop
  feature/*:
    auto_merge: true    # Full automation for features
```

### Enhancement 3: Rollback Window
Automatic rollback if health checks fail

```bash
# If deployed version fails health checks within 10 minutes
if health_check_failed_within 600s; then
    auto_rollback_to_previous_version
fi
```

---

## References

- [auto_commit.sh](../../.workflow/automation/core/auto_commit.sh)
- [auto_push.sh](../../.workflow/automation/core/auto_push.sh)
- [auto_pr.sh](../../.workflow/automation/core/auto_pr.sh)
- [auto_release.sh](../../.workflow/automation/core/auto_release.sh)
- [P0 Exploration Report](../P0_EXPLORATION_REPORT.md) - Section 2

---

## Decision Matrix Summary

| Operation | Default | Solo Dev | Team | CI/CD |
|-----------|---------|----------|------|-------|
| **commit** | ✅ Auto | ✅ Auto | ✅ Auto | ✅ Auto |
| **push** | ❌ Ask | ✅ Auto | ❌ Ask | ✅ Auto |
| **PR create** | ❌ Ask | ✅ Auto | ❌ Ask | ✅ Auto |
| **PR merge** | ❌ Ask | ⚙️ Config | ❌ Ask | ⚙️ After approval |
| **tag** | ❌ Ask | ❌ Ask | ❌ Ask | ⚙️ After approval |
| **force push** | ❌ Never | ❌ Never | ❌ Never | ❌ Never |

---

## Approval

**Decision Made By**: Claude Enhancer Team
**Approved**: 2025-10-10
**Effective Date**: v5.4.0
**Review Date**: 2026-01-10 (3 months post-implementation)

**Signature**: _Tiered automation provides the best balance of safety and velocity_
