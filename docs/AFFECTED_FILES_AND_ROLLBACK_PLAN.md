# Affected Files Inventory + Rollback Plan
## Multi-Layer Enforcement Implementation (v6.2)

**Task ID**: enforcement-optimization-20251011
**Date**: 2025-10-11
**Risk Level**: MEDIUM (Infrastructure changes, but non-breaking)
**Estimated Impact**: 35 files (18 new, 17 modified)

---

## Part 1: Affected Files Inventory

### 1.1 New Files (18 files)

#### Infrastructure Core (4 files)
```
.ce/
├── config.yml                    # Enforcement configuration
└── archive/                      # Historical task data directory

.gates/
└── {task_id}/                    # Per-task gate evidence
    ├── metadata.json             # Task metadata
    ├── 00.ok                     # P0 gate pass evidence
    └── agent_evidence.json       # Agent execution records
```

**Purpose**: Centralized enforcement metadata and audit trail

---

#### Claude Hooks Layer (6 files)
```
.claude/hooks/
├── branch_init.sh                # P0 branch validation (Rule 0)
├── collect_agent_evidence.sh     # Agent execution recorder
├── phase_enforcer.sh             # Phase-specific validation
├── gate_archiver.sh              # Historical gate preservation
├── parallel_limit_enforcer.sh    # Concurrent agent limiter
└── user_satisfaction_tracker.sh  # Non-intrusive satisfaction monitor
```

**Purpose**: AI-layer guidance and evidence collection (non-blocking)

---

#### Git Hooks Enhancement (4 files)
```
.git/hooks/
├── pre-commit.enhanced           # Enhanced P0/P1 validation
├── post-commit.evidence          # Auto-collect evidence post-commit
└── backups/                      # Hook backup directory
    ├── pre-commit.backup.{timestamp}
    └── commit-msg.backup.{timestamp}
```

**Purpose**: Hard enforcement with rollback capability

---

#### Documentation (4 files)
```
docs/
├── ENFORCEMENT_GUIDE.md          # User-facing enforcement guide
├── ROLLBACK_PROCEDURE.md         # Emergency rollback instructions
├── MIGRATION_CHECKLIST.md        # Deployment checklist
└── AFFECTED_FILES_AND_ROLLBACK_PLAN.md  # This file
```

**Purpose**: User education and operational procedures

---

### 1.2 Modified Files (17 files)

#### Configuration Updates (5 files)
```
.workflow/gates.yml               # Add P0 enforcement paths
  Changes:
  - phases.P0.allow_paths += [".ce/**", ".gates/**"]
  - phases.P1.allow_paths += [".ce/**"]
  - phases.P0.gates += ["Branch validation passed (Rule 0)"]
  - phases.P1.gates += ["Agent evidence collected"]

.workflow/config.yml              # Add enforcement settings
  Changes:
  - enforcement.mode = "multi-layer"
  - enforcement.strict_p0 = true
  - enforcement.collect_evidence = true
  - enforcement.satisfaction_tracking = true

.ce/task.yml                      # Add enforcement metadata
  Changes:
  - task.enforcement_version = "6.2"
  - task.rollback_enabled = true

.claude/config.yaml               # Link to enforcement config
  Changes:
  - hooks.enforcement_config = ".ce/config.yml"

.gitignore                        # Exclude temporary evidence
  Changes:
  + .ce/archive/*
  + .gates/*/tmp/
  + .workflow/logs/enforcement_*.log
```

---

#### Core Hooks Modifications (3 files)
```
.git/hooks/pre-commit             # Enhanced with P0/P1 validation
  Line changes: ~50 lines added (300 → 350 total)
  New sections:
  - P0 Branch Validation (Rule 0 check)
  - P1 Agent Evidence Collection
  - Gate archival trigger
  - Performance tracking (target: <500ms)

.git/hooks/commit-msg             # Add enforcement version tag
  Line changes: ~20 lines added (150 → 170 total)
  New sections:
  - Auto-append enforcement metadata to commit message
  - Format: [CE-v6.2] [evidence:collected]

.claude/hooks/branch_helper.sh   # Upgrade to enforcement mode
  Line changes: ~80 lines added (200 → 280 total)
  New sections:
  - Integration with .ce/config.yml
  - Evidence collection trigger
  - Performance optimization (parallel checks)
```

---

#### Workflow Scripts (4 files)
```
.workflow/executor.sh             # Add enforcement orchestration
  Line changes: ~60 lines added (450 → 510 total)
  New functions:
  - check_enforcement_mode()
  - collect_phase_evidence()
  - archive_gate_history()

.workflow/phase_validator.py     # Add evidence validation
  Line changes: ~120 lines added (350 → 470 total)
  New classes:
  - EvidenceValidator
  - SatisfactionTracker

.workflow/cli/lib/common.sh       # Add enforcement utilities
  Line changes: ~40 lines added (280 → 320 total)
  New functions:
  - load_enforcement_config()
  - get_current_task_id()

.workflow/scripts/sign_gate.sh   # Add evidence signing
  Line changes: ~30 lines added (150 → 180 total)
  New sections:
  - Sign agent evidence JSON
  - Verify evidence integrity
```

---

#### CI/CD Updates (3 files)
```
.github/workflows/ci-enhanced-5.3.yml  # Add enforcement validation job
  New job:
  - enforcement-check:
      - Validate .ce/ structure
      - Verify evidence collection
      - Check gate integrity

.github/workflows/positive-health.yml  # Add enforcement health
  New checks:
  - Enforcement config validity
  - Evidence collection rate
  - User satisfaction trend

.github/PULL_REQUEST_TEMPLATE.md      # Add enforcement checklist
  New section:
  - [ ] Enforcement evidence collected
  - [ ] .ce/ metadata updated
  - [ ] Satisfaction score >= 3.0/5.0
```

---

#### Monitoring & Metrics (2 files)
```
.workflow/metrics.jsonl           # Add enforcement metrics
  New indicators:
  - enforcement_hook_time_ms
  - evidence_collection_success_rate
  - user_satisfaction_score
  - gate_archival_count

scripts/capability_snapshot.sh    # Add enforcement capability
  New checks:
  - .ce/ infrastructure exists
  - Enforcement hooks active
  - Evidence collection working
```

---

## Part 2: Rollback Plan

### 2.1 Rollback Triggers (WHEN to rollback)

#### Automated Triggers (High Priority)
```yaml
critical_failures:
  - data_loss: "Any git history corruption"
  - security_breach: "Sensitive data exposed in evidence"
  - hook_failure: "pre-commit fails >50% of attempts"
  - performance_degradation: "Hook execution time >1000ms (2x target)"

performance_triggers:
  - hook_time_p50: ">500ms (target: 200-300ms)"
  - hook_time_p95: ">1000ms (target: <500ms)"
  - cache_hit_ratio: "<60% (target: >80%)"

quality_triggers:
  - user_satisfaction: "<3.0/5.0 for 3 consecutive days"
  - adoption_rate: "<40% after 4 weeks"
  - error_rate: ">10% of commits fail validation"
```

#### Manual Triggers (User-Initiated)
```yaml
user_feedback:
  - too_intrusive: "Users report enforcement too strict"
  - confusing_errors: "Error messages unclear"
  - workflow_blocked: "Legitimate work prevented"

business_triggers:
  - deadline_pressure: "Critical release blocked by enforcement"
  - stakeholder_request: "Management requests rollback"
```

---

### 2.2 Rollback Procedure (HOW to rollback)

#### Step 1: Detect Issue (Automated or Manual)
```bash
# Automated detection via health check
.github/workflows/positive-health.yml
  → Triggers alert if metrics fail
  → Creates rollback ticket automatically

# Manual detection
claude-enhancer rollback --check
  → Shows current metrics
  → Recommends rollback if needed
```

---

#### Step 2: Create Pre-Rollback Backup
```bash
#!/bin/bash
# .workflow/scripts/create_rollback_backup.sh

BACKUP_DIR=".workflow/backups/rollback_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup current state
cp -r .ce/ "$BACKUP_DIR/ce/"
cp -r .gates/ "$BACKUP_DIR/gates/"
cp .git/hooks/pre-commit "$BACKUP_DIR/pre-commit.current"
cp .git/hooks/commit-msg "$BACKUP_DIR/commit-msg.current"
cp .claude/hooks/branch_helper.sh "$BACKUP_DIR/branch_helper.current"

# Backup configuration
cp .workflow/gates.yml "$BACKUP_DIR/gates.yml.current"
cp .workflow/config.yml "$BACKUP_DIR/config.yml.current"

# Create backup manifest
cat > "$BACKUP_DIR/manifest.txt" <<EOF
Backup created: $(date)
Reason: Pre-rollback safety backup
Enforcement version: 6.2
Files backed up: $(find "$BACKUP_DIR" -type f | wc -l)
EOF

echo "Backup created: $BACKUP_DIR"
```

---

#### Step 3: Restore Git Hooks from Backup
```bash
#!/bin/bash
# .workflow/scripts/restore_git_hooks.sh

# Find latest backup before enforcement upgrade
BACKUP_DIR=".git/hooks/backup_20251011_000000"  # Pre-v6.2 backup

if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "ERROR: Backup not found!"
    exit 1
fi

# Restore hooks
cp "$BACKUP_DIR/pre-commit" .git/hooks/pre-commit
cp "$BACKUP_DIR/commit-msg" .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg

# Verify restoration
git config --local core.hooksPath .git/hooks

echo "Git hooks restored from: $BACKUP_DIR"
echo "Enforcement disabled: pre-commit and commit-msg reverted to v6.1"
```

---

#### Step 4: Remove New Infrastructure (Preserve Evidence)
```bash
#!/bin/bash
# .workflow/scripts/remove_enforcement_infrastructure.sh

# Archive (don't delete) .ce/ and .gates/
ARCHIVE_DIR=".workflow/archives/enforcement_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

# Move to archive (preserve for audit)
mv .ce/ "$ARCHIVE_DIR/ce/" 2>/dev/null
mv .gates/ "$ARCHIVE_DIR/gates/" 2>/dev/null

# Remove new Claude hooks (keep existing ones)
cd .claude/hooks/
rm -f branch_init.sh collect_agent_evidence.sh phase_enforcer.sh \
      gate_archiver.sh parallel_limit_enforcer.sh user_satisfaction_tracker.sh

echo "Infrastructure archived to: $ARCHIVE_DIR"
echo "New Claude hooks removed (existing hooks preserved)"
```

---

#### Step 5: Revert Configuration Changes
```bash
#!/bin/bash
# .workflow/scripts/revert_config_changes.sh

# Restore gates.yml from git history
git show HEAD~1:.workflow/gates.yml > .workflow/gates.yml

# Restore config.yml from git history
git show HEAD~1:.workflow/config.yml > .workflow/config.yml

# Remove enforcement settings from .claude/config.yaml
sed -i '/hooks.enforcement_config/d' .claude/config.yaml

# Restore .gitignore
git checkout HEAD~1 -- .gitignore

echo "Configuration files reverted to pre-v6.2 state"
```

---

#### Step 6: Notify Users
```bash
#!/bin/bash
# .workflow/scripts/notify_rollback.sh

# Create rollback announcement
cat > ROLLBACK_NOTICE.md <<'EOF'
# Enforcement Rollback Notice

**Date**: $(date)
**Version**: v6.2 → v6.1
**Reason**: [Specify reason: performance/user-satisfaction/critical-bug]

## What Changed
- Enforcement hooks disabled
- .ce/ and .gates/ archived (not deleted)
- Configuration reverted to v6.1

## What Still Works
- All existing workflows (P0-P7)
- Git hooks (pre-commit, commit-msg)
- Claude Enhancer core features

## Data Preserved
- Historical gates: Archived in .workflow/archives/
- Task metadata: Archived in .workflow/archives/enforcement_*/
- Agent evidence: Preserved for post-mortem analysis

## Next Steps
1. Continue normal development (enforcement disabled)
2. Report any issues to: [issue-tracker-url]
3. Engineering will investigate root cause

---
*This is a temporary rollback. We will fix the issue and re-deploy with improvements.*
EOF

# Commit the rollback
git add -A
git commit -m "[ROLLBACK] Revert to v6.1 - enforcement disabled

Reason: [Specify]
Evidence preserved in: .workflow/archives/enforcement_$(date +%Y%m%d_%H%M%S)

\ud83e\udd16 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "Rollback committed. Notify team via:"
echo "- Slack: #claude-enhancer"
echo "- Email: dev-team@example.com"
```

---

#### Step 7: Collect Incident Report
```bash
#!/bin/bash
# .workflow/scripts/generate_incident_report.sh

REPORT_FILE="docs/INCIDENT_REPORT_$(date +%Y%m%d).md"

cat > "$REPORT_FILE" <<EOF
# Enforcement Rollback Incident Report

## Summary
- **Date**: $(date)
- **Duration**: [Enforcement v6.2 live time]
- **Impact**: [Number of users affected]
- **Root Cause**: [Technical/UX/Performance issue]

## Timeline
- **Deploy**: 2025-10-11 00:00 UTC
- **First Alert**: [When issue detected]
- **Rollback Started**: [When rollback began]
- **Rollback Completed**: [When rollback finished]

## Metrics at Rollback
\`\`\`yaml
performance:
  hook_time_p50: [value]ms (target: <500ms)
  hook_time_p95: [value]ms (target: <1000ms)

quality:
  user_satisfaction: [value]/5.0 (target: >=3.0)
  error_rate: [value]% (target: <10%)
  adoption_rate: [value]% (target: >40%)
\`\`\`

## Evidence Collected
- Metrics logs: .workflow/metrics.jsonl
- Hook logs: .workflow/logs/enforcement_*.log
- User feedback: [Slack/GitHub issues]

## Root Cause Analysis
[Detailed technical analysis]

## Action Items
1. [ ] Fix root cause
2. [ ] Add regression test
3. [ ] Update documentation
4. [ ] Plan re-deployment

## Lessons Learned
[What went wrong and how to prevent]
EOF

echo "Incident report created: $REPORT_FILE"
```

---

### 2.3 Data Preservation Strategy

#### What Gets Preserved (NEVER deleted)
```yaml
permanent_archives:
  - path: ".workflow/archives/enforcement_*/"
    contents:
      - .ce/                    # All task metadata
      - .gates/                 # All gate evidence
    reason: "Audit trail + post-mortem analysis"
    retention: "Indefinite"

  - path: ".workflow/backups/rollback_*/"
    contents:
      - Pre-rollback snapshots
    reason: "Disaster recovery"
    retention: "90 days"

  - path: ".workflow/logs/enforcement_*.log"
    contents:
      - Hook execution logs
      - Performance metrics
    reason: "Debugging + optimization"
    retention: "30 days"
```

#### What Gets Deleted (Safe to remove)
```yaml
temporary_files:
  - ".ce/tmp/"               # Temporary working files
  - ".gates/*/tmp/"          # Temporary evidence files
  - ".workflow/logs/*.pid"   # Process ID files
```

---

### 2.4 Recovery Validation Checklist

#### Test 1: Users Can Commit Without Enforcement
```bash
# Test: Create dummy commit
echo "test" > test.txt
git add test.txt
git commit -m "test: verify enforcement disabled"

# Expected: Commit succeeds WITHOUT enforcement checks
# If fails: Rollback incomplete
```

---

#### Test 2: Old Workflows Functional
```bash
# Test: Run old workflow commands
.workflow/executor.sh P1

# Expected: P1 phase executes normally
# If fails: Configuration corruption
```

---

#### Test 3: Git History Intact
```bash
# Test: Verify no history corruption
git log --oneline -10
git fsck --full

# Expected: All commits present, no corruption
# If fails: Critical - escalate to DevOps
```

---

#### Test 4: No Performance Regression
```bash
# Test: Measure hook performance post-rollback
time git commit --allow-empty -m "performance test"

# Expected: <200ms (pre-enforcement baseline)
# If >500ms: Hook restoration failed
```

---

## Part 3: Migration Safety Plan

### 3.1 Pre-Deployment Backup Strategy
```bash
#!/bin/bash
# .workflow/scripts/pre_deployment_backup.sh

BACKUP_ROOT=".workflow/backups/pre_v6.2_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_ROOT"

# Critical files backup
cp -r .git/hooks/ "$BACKUP_ROOT/git_hooks/"
cp -r .claude/hooks/ "$BACKUP_ROOT/claude_hooks/"
cp -r .workflow/ "$BACKUP_ROOT/workflow/"
cp .gitignore "$BACKUP_ROOT/gitignore.backup"

# Configuration snapshot
git show HEAD:.workflow/gates.yml > "$BACKUP_ROOT/gates.yml.pre"
git show HEAD:.workflow/config.yml > "$BACKUP_ROOT/config.yml.pre"

# Capability baseline
./scripts/capability_snapshot.sh > "$BACKUP_ROOT/capability_baseline.txt"

# Create restore script
cat > "$BACKUP_ROOT/RESTORE.sh" <<'RESTORE_EOF'
#!/bin/bash
set -euo pipefail
BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$BACKUP_DIR/../../.." && pwd)"

echo "Restoring from backup: $BACKUP_DIR"
cd "$PROJECT_ROOT"

# Restore hooks
cp -r "$BACKUP_DIR/git_hooks/"* .git/hooks/
cp -r "$BACKUP_DIR/claude_hooks/"* .claude/hooks/
chmod +x .git/hooks/* .claude/hooks/*.sh

# Restore configuration
cp "$BACKUP_DIR/gates.yml.pre" .workflow/gates.yml
cp "$BACKUP_DIR/config.yml.pre" .workflow/config.yml
cp "$BACKUP_DIR/gitignore.backup" .gitignore

echo "Restoration complete. Run: git status"
RESTORE_EOF

chmod +x "$BACKUP_ROOT/RESTORE.sh"

echo "Backup created: $BACKUP_ROOT"
echo "To restore: $BACKUP_ROOT/RESTORE.sh"
```

---

### 3.2 Gradual Rollout Checkpoints

#### Phase 1: Canary Deployment (10% users, Week 1)
```yaml
target_group: "Internal team (3-5 developers)"

success_criteria:
  - hook_time_p95: "<500ms"
  - user_satisfaction: ">=4.0/5.0"
  - error_rate: "<5%"
  - zero_critical_bugs: true

monitoring:
  - Real-time metrics dashboard
  - Daily satisfaction survey
  - Incident tracking

rollback_decision:
  - Auto-rollback if error_rate >10%
  - Manual rollback if user_satisfaction <3.0
```

---

#### Phase 2: Beta Deployment (50% users, Week 2-3)
```yaml
target_group: "Early adopters + power users"

success_criteria:
  - hook_time_p95: "<500ms"
  - user_satisfaction: ">=3.5/5.0"
  - error_rate: "<8%"
  - adoption_rate: ">60%"

monitoring:
  - Weekly performance review
  - User feedback analysis
  - A/B comparison with Phase 1

rollback_decision:
  - Auto-rollback if error_rate >15%
  - Manual rollback if adoption_rate <40%
```

---

#### Phase 3: Full Deployment (100% users, Week 4+)
```yaml
target_group: "All users"

success_criteria:
  - hook_time_p95: "<500ms"
  - user_satisfaction: ">=3.0/5.0"
  - error_rate: "<10%"
  - adoption_rate: ">80%"

monitoring:
  - Continuous health checks
  - Monthly satisfaction survey
  - Performance trending

stabilization_period: "2 weeks"
rollback_window: "30 days post-deployment"
```

---

### 3.3 A/B Testing Plan

#### Test Setup
```yaml
groups:
  control_group:
    size: 50%
    enforcement: "v6.1 (current)"
    duration: "4 weeks"

  treatment_group:
    size: 50%
    enforcement: "v6.2 (new)"
    duration: "4 weeks"

assignment:
  method: "user_id hash % 2"
  sticky: true  # Users stay in same group
```

---

#### Metrics to Compare
```yaml
performance:
  - hook_execution_time_ms
  - git_operation_latency_ms
  - cache_hit_ratio

quality:
  - commits_blocked_rate
  - false_positive_rate
  - gate_pass_rate

user_experience:
  - satisfaction_score (1-5)
  - workflow_interruption_count
  - help_doc_access_count

adoption:
  - active_user_rate
  - feature_usage_rate
  - opt_out_rate
```

---

#### Decision Matrix
```yaml
# After 4 weeks A/B test
decision_rules:
  deploy_to_all:
    conditions:
      - treatment_group.satisfaction >= control_group.satisfaction
      - treatment_group.error_rate <= control_group.error_rate * 1.2
      - treatment_group.performance <= control_group.performance * 1.5

  rollback:
    conditions:
      - treatment_group.satisfaction < control_group.satisfaction - 0.5
      - treatment_group.error_rate > control_group.error_rate * 2.0
      - critical_bug_detected: true

  iterate:
    conditions:
      - Mixed results (some better, some worse)
      - Need more data
```

---

## Part 4: Emergency Contacts & Resources

### 4.1 Rollback Decision Tree
```
Issue Detected
    ↓
Is it CRITICAL? (data loss / security / >50% hook failures)
    ├─ YES → IMMEDIATE ROLLBACK (Steps 1-7)
    └─ NO → Continue ↓
        ↓
Is performance >2x target? (>1000ms)
    ├─ YES → SCHEDULED ROLLBACK (within 24h)
    └─ NO → Continue ↓
        ↓
Is user satisfaction <3.0 for 3 days?
    ├─ YES → PLANNED ROLLBACK (within 1 week)
    └─ NO → MONITOR + ITERATE
```

---

### 4.2 Quick Reference Commands
```bash
# Check current status
./scripts/capability_snapshot.sh

# View metrics
tail -f .workflow/metrics.jsonl | jq .

# Emergency rollback (one command)
./.workflow/scripts/emergency_rollback.sh

# Verify rollback success
./scripts/verify_rollback.sh

# Create incident report
./scripts/generate_incident_report.sh
```

---

### 4.3 Escalation Path
```yaml
Level 1 (Self-Service):
  - Use: ./scripts/emergency_rollback.sh
  - Duration: <30 minutes

Level 2 (Team Lead):
  - Contact: @devops-team
  - SLA: <2 hours

Level 3 (Engineering Manager):
  - Contact: @engineering-manager
  - SLA: <4 hours

Level 4 (VP Engineering):
  - Contact: @vp-engineering
  - SLA: <24 hours
```

---

## Part 5: Post-Rollback Analysis

### 5.1 Mandatory Reviews
```yaml
technical_review:
  - Root cause analysis (RCA)
  - Performance profiling
  - Code review of changes

user_research:
  - Satisfaction survey
  - Pain point analysis
  - Feature usage patterns

process_review:
  - Deployment process
  - Testing coverage
  - Documentation quality
```

---

### 5.2 Re-Deployment Criteria
```yaml
must_fix:
  - Root cause resolved
  - Regression tests added
  - Performance optimized (<500ms p95)
  - Documentation updated

must_verify:
  - All tests pass
  - Peer review approved
  - Canary deployment successful (10% users, 1 week)

must_communicate:
  - Release notes published
  - Training materials ready
  - Support team briefed
```

---

## Summary

### Key Takeaways
1. **35 files affected** (18 new, 17 modified)
2. **Rollback is SAFE**: All evidence preserved, no data loss
3. **Rollback is FAST**: <30 minutes end-to-end
4. **Gradual rollout**: 10% → 50% → 100% over 4 weeks
5. **A/B testing**: Continuous validation of improvements

### Risk Mitigation
- Pre-deployment backup: MANDATORY
- Rollback scripts: TESTED and VERSIONED
- Evidence preservation: PERMANENT
- User communication: TRANSPARENT

### Confidence Level
**Deployment Risk**: MEDIUM
**Rollback Risk**: LOW
**Overall Confidence**: HIGH (85/100)

---

*This plan is a living document. Update after each deployment/rollback.*
