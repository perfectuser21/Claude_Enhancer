# Automation Guide - Claude Enhancer v5.4.0

**Last Updated**: 2025-10-10
**Version**: 5.4.0
**Automation Level**: Tiered (5 levels)

---

## Table of Contents

- [Introduction](#introduction)
- [Automation Philosophy](#automation-philosophy)
- [Environment Variables Reference](#environment-variables-reference)
- [Tiered Automation Levels](#tiered-automation-levels)
- [Core Automation Scripts](#core-automation-scripts)
- [Safety Features](#safety-features)
- [Real-World Examples](#real-world-examples)
- [Troubleshooting](#troubleshooting)

---

## Introduction

Claude Enhancer v5.4.0 includes **complete Git automation**, from commit to release. This guide explains how to configure, use, and trust the automation system.

### What's Automated

```
Git Workflow Automation
├─ Tier 1: commit, add (always safe)
├─ Tier 2: push (configurable)
├─ Tier 3: PR creation (configurable)
├─ Tier 4: PR merge (default: manual)
└─ Tier 5: tag, release (default: manual)
```

### Design Principles

1. **Safe by Default** - Conservative defaults, progressive enablement
2. **Transparent** - Always show what will happen
3. **Reversible** - All operations can be undone
4. **Audited** - Every action logged with HMAC integrity

---

## Automation Philosophy

### Trade-offs: Safety vs Velocity

```
Safety ←────────────────────────→ Velocity
│                                        │
Manual                              Full Auto
(Slow but safe)                (Fast but risky)
        │
        └─ Claude Enhancer
           (Configurable balance)
```

**The Claude Enhancer Approach**:
- Start conservative (high safety)
- Enable progressively (gain confidence)
- Override when needed (maintain control)
- Audit everything (accountability)

### Control Boundaries

| Operation | Risk Level | Default | Override |
|-----------|-----------|---------|----------|
| **git add** | Low | Auto | Never ask |
| **git commit** | Low | Auto | Never ask |
| **git push** | Medium | Ask | `CE_AUTO_PUSH=1` |
| **PR create** | Medium | Ask | `CE_AUTO_PR=1` |
| **PR merge** | High | Ask | `CE_AUTO_MERGE=1` |
| **git tag** | Critical | Ask | `CE_AUTO_RELEASE=1` |
| **force push** | Critical | Never | No override |

---

## Environment Variables Reference

### Core Execution Control

#### `CE_EXECUTION_MODE`
```bash
export CE_EXECUTION_MODE=1  # 0=manual, 1=automated
```

**Purpose**: Master switch for all automation
**Default**: `0` (manual mode)
**When to Enable**: After reading documentation

**Effects**:
- `0`: All automation disabled, scripts show instructions only
- `1`: Automation enabled based on tier configuration

**Example**:
```bash
# Check current mode
echo "Mode: $CE_EXECUTION_MODE"

# Enable automation
export CE_EXECUTION_MODE=1
```

---

### Tier-Specific Controls

#### `CE_AUTO_PUSH` (Tier 2)
```bash
export CE_AUTO_PUSH=1  # 0=ask, 1=auto
```

**Purpose**: Control automatic push to remote
**Default**: `0` (ask before push)
**Risk**: Medium (can't easily undo after push)

**When to Enable**:
- After 10+ successful commits
- Solo developer on feature branch
- CI/CD pipeline

**Safety**:
- Blocks force push to protected branches
- Checks upstream tracking branch
- Verifies no diverged commits

**Example**:
```bash
# Manual mode
export CE_AUTO_PUSH=0
bash auto_commit.sh "feat: Add feature"
bash auto_push.sh  # Will ask for confirmation

# Auto mode
export CE_AUTO_PUSH=1
bash auto_commit.sh "feat: Add feature"
bash auto_push.sh  # Pushes automatically
```

#### `CE_AUTO_PR` (Tier 3)
```bash
export CE_AUTO_PR=1  # 0=ask, 1=auto
```

**Purpose**: Automatic PR creation after push
**Default**: `0` (ask before PR)
**Risk**: Medium (creates public PR)

**When to Enable**:
- After 5+ successful PRs
- Standard workflow established
- PR template configured

**Safety**:
- Validates branch name
- Generates smart PR description
- Adds to merge queue automatically

**Example**:
```bash
# Manual mode
export CE_AUTO_PR=0
bash auto_pr.sh "Add feature" "Description"  # Asks confirmation

# Auto mode
export CE_AUTO_PR=1
bash auto_pr.sh "Add feature" "Description"  # Creates immediately
```

#### `CE_AUTO_MERGE` (Tier 4)
```bash
export CE_AUTO_MERGE=1  # 0=ask, 1=auto (DANGEROUS!)
```

**Purpose**: Automatic PR merge after CI passes
**Default**: `0` (always ask)
**Risk**: High (affects main branch)

**When to Enable**:
- Solo developer only
- High confidence in CI
- Rollback procedure tested

**Safety**:
- Checks CI status (must be green)
- Verifies branch protection rules
- Runs conflict detection first
- Logs to audit trail

**⚠️ Warning**: Only enable if you're comfortable with auto-merge consequences.

**Example**:
```bash
# Conservative (recommended)
export CE_AUTO_MERGE=0

# Aggressive (solo developer)
export CE_AUTO_MERGE=1
```

#### `CE_AUTO_RELEASE` (Tier 5)
```bash
export CE_AUTO_RELEASE=1  # 0=ask, 1=auto (VERY DANGEROUS!)
```

**Purpose**: Automatic tagging and release creation
**Default**: `0` (always ask)
**Risk**: Critical (affects production)

**When to Enable**:
- Never recommended for production
- Only for testing/staging environments
- With human review in production pipeline

**Safety**:
- Validates semver format
- Generates release notes
- Requires signed commits
- Triggers deployment hooks

**🔴 Recommendation**: Always keep disabled (`CE_AUTO_RELEASE=0`)

---

### Utility Controls

#### `CE_DRY_RUN`
```bash
export CE_DRY_RUN=1  # 0=execute, 1=show only
```

**Purpose**: Preview what would happen without execution
**Default**: `0` (normal execution)

**Use Cases**:
- Testing new configurations
- Debugging workflows
- Training new team members

**Example**:
```bash
# See what would happen
export CE_DRY_RUN=1
bash auto_commit.sh "feat: Test"
# Output: "DRY RUN: Would commit with message: feat: Test"
```

#### `CE_DEBUG`
```bash
export CE_DEBUG=1  # 0=normal, 1=verbose
```

**Purpose**: Enable detailed logging
**Default**: `0` (normal logging)

**Output Level**:
- `0`: INFO, SUCCESS, WARNING, ERROR
- `1`: Above + DEBUG messages

**Example**:
```bash
export CE_DEBUG=1
bash auto_commit.sh "feat: Debug test"
# Shows detailed execution steps
```

#### `CE_STRICT_MODE`
```bash
export CE_STRICT_MODE=1  # 0=relaxed, 1=strict
```

**Purpose**: Enable strict validation rules
**Default**: `0` (relaxed)

**Effects**:
- Enforces conventional commit format
- Blocks WIP commits
- Requires phase markers
- Fails on large files (>10MB)

**Example**:
```bash
# Relaxed (warnings only)
export CE_STRICT_MODE=0
bash auto_commit.sh "Add stuff"  # Works with warning

# Strict (errors fail)
export CE_STRICT_MODE=1
bash auto_commit.sh "Add stuff"  # Fails (not conventional)
```

#### `CE_SESSION_ID`
```bash
export CE_SESSION_ID="$(uuidgen)"
```

**Purpose**: Track operations across terminals
**Default**: Auto-generated if unset

**Use Cases**:
- Multi-terminal debugging
- Audit log correlation
- Session replay

#### `CE_AUDIT_SECRET`
```bash
export CE_AUDIT_SECRET="$(openssl rand -hex 32)"
```

**Purpose**: HMAC key for audit log integrity
**Default**: None (must be set)
**Security**: Store in secure location, never commit

**Required For**: All audit logging operations

**Setup**:
```bash
# Generate once and store securely
openssl rand -hex 32 > ~/.claude-enhancer-secret
chmod 600 ~/.claude-enhancer-secret

# Load in shell profile
export CE_AUDIT_SECRET="$(cat ~/.claude-enhancer-secret)"
```

---

## Tiered Automation Levels

### Level 1: Beginner (Week 1)
**Safe for learning**

```bash
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=0
export CE_AUTO_PR=0
export CE_AUTO_MERGE=0
export CE_AUTO_RELEASE=0
```

**What happens**:
- Auto commit ✅
- Manual push ✋
- Manual PR ✋
- Manual merge ✋

**Best for**: First week, learning workflow

---

### Level 2: Comfortable (Week 2-3)
**Confident with commits**

```bash
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=1      # ← Enabled
export CE_AUTO_PR=0
export CE_AUTO_MERGE=0
export CE_AUTO_RELEASE=0
```

**What happens**:
- Auto commit ✅
- Auto push ✅
- Manual PR ✋
- Manual merge ✋

**Best for**: Daily feature development

---

### Level 3: Productive (Week 4+)
**Established workflow**

```bash
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=1
export CE_AUTO_PR=1        # ← Enabled
export CE_AUTO_MERGE=0
export CE_AUTO_RELEASE=0
```

**What happens**:
- Auto commit ✅
- Auto push ✅
- Auto PR ✅
- Manual merge ✋

**Best for**: Standard development cycles

---

### Level 4: Solo Developer (Advanced)
**High trust, solo work**

```bash
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=1
export CE_AUTO_PR=1
export CE_AUTO_MERGE=1     # ← Enabled (RISKY)
export CE_AUTO_RELEASE=0
```

**What happens**:
- Auto commit ✅
- Auto push ✅
- Auto PR ✅
- Auto merge ✅ (if CI passes)
- Manual release ✋

**⚠️ Requirements**:
- Solo developer only
- Comprehensive CI coverage
- Tested rollback procedure

**Best for**: Personal projects, prototypes

---

### Level 5: Full Automation (NOT RECOMMENDED)
**Maximum velocity, maximum risk**

```bash
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=1
export CE_AUTO_PR=1
export CE_AUTO_MERGE=1
export CE_AUTO_RELEASE=1   # ← Enabled (VERY RISKY)
```

**🔴 WARNING**: This is extremely dangerous for production systems!

**Only acceptable for**:
- Staging environments
- Test repositories
- Demo systems

**Never use for**: Production code

---

## Core Automation Scripts

### 1. auto_commit.sh

**Purpose**: Automated git commit with validation
**Tier**: 1 (Always safe)
**Location**: `.workflow/automation/core/auto_commit.sh`

#### Usage

```bash
bash auto_commit.sh <message> [files...]
```

#### Arguments

- `message`: Commit message (required, ≥10 chars)
- `files`: Specific files to commit (optional, default: all)

#### Features

- ✅ Commit message validation (length, format, phase)
- ✅ Automatic phase marker injection
- ✅ Large file detection (warns >10MB)
- ✅ Sensitive file blocking (*.env, *.pem, etc)
- ✅ Conventional commit support
- ✅ Audit logging

#### Examples

```bash
# Commit all changes
bash auto_commit.sh "feat(P3): Add user authentication"

# Commit specific files
bash auto_commit.sh "fix(P3): Resolve bug" src/auth.js tests/auth.test.js

# With phase auto-injection
export CE_CURRENT_PHASE=3
bash auto_commit.sh "feat: Add feature"  # Becomes "feat: [P3] Add feature"

# Strict mode
export CE_STRICT_MODE=1
bash auto_commit.sh "feat(auth): Add login"  # Must be conventional

# Dry run
export CE_DRY_RUN=1
bash auto_commit.sh "feat: Test"  # Shows what would happen
```

#### Exit Codes

- `0`: Success
- `1`: Validation failed or commit failed

---

### 2. auto_push.sh

**Purpose**: Automated push to remote with safety checks
**Tier**: 2 (Configurable via `CE_AUTO_PUSH`)
**Location**: `.workflow/automation/core/auto_push.sh`

#### Usage

```bash
bash auto_push.sh [remote] [branch]
```

#### Arguments

- `remote`: Remote name (optional, default: origin)
- `branch`: Branch name (optional, default: current)

#### Safety Checks

- ✅ Blocks force push to protected branches (main/master)
- ✅ Verifies upstream tracking branch
- ✅ Checks for unpushed commits
- ✅ Runs pre-push hooks
- ✅ Audit logging

#### Examples

```bash
# Push current branch to origin
bash auto_push.sh

# Push specific branch
bash auto_push.sh origin feature/auth

# With confirmation (CE_AUTO_PUSH=0)
bash auto_push.sh  # Asks: "Push to origin/feature-auth? (y/N)"

# Auto push (CE_AUTO_PUSH=1)
export CE_AUTO_PUSH=1
bash auto_push.sh  # Pushes immediately

# Dry run
export CE_DRY_RUN=1
bash auto_push.sh  # Shows: "DRY RUN: Would push to origin/feature-auth"
```

#### Exit Codes

- `0`: Success or skipped
- `1`: Safety check failed or push failed

---

### 3. auto_pr.sh

**Purpose**: Automated PR creation with smart defaults
**Tier**: 3 (Configurable via `CE_AUTO_PR`)
**Location**: `.workflow/automation/core/auto_pr.sh`

#### Usage

```bash
bash auto_pr.sh <title> <description> [options]
```

#### Arguments

- `title`: PR title (required)
- `description`: PR description (required)
- `--draft`: Create as draft PR (optional)
- `--base <branch>`: Base branch (optional, default: main)

#### Features

- ✅ Auto-generates PR description from commits
- ✅ Detects Phase from branch name or commits
- ✅ Calculates change statistics
- ✅ Adds to merge queue automatically
- ✅ Supports draft PRs
- ✅ Audit logging

#### Examples

```bash
# Create PR with description
bash auto_pr.sh \
  "Add user authentication" \
  "Implements JWT-based auth with refresh tokens"

# Create draft PR
bash auto_pr.sh \
  "WIP: Add feature" \
  "Work in progress" \
  --draft

# Custom base branch
bash auto_pr.sh \
  "Hotfix: Critical bug" \
  "Fixes production issue" \
  --base master

# Auto-generate description
bash auto_pr.sh \
  "Add authentication" \
  "$(git log origin/main..HEAD --oneline)"

# With confirmation (CE_AUTO_PR=0)
bash auto_pr.sh "Add feature" "Description"  # Asks confirmation

# Auto create (CE_AUTO_PR=1)
export CE_AUTO_PR=1
bash auto_pr.sh "Add feature" "Description"  # Creates immediately
```

#### Exit Codes

- `0`: PR created successfully
- `1`: Failed to create PR

#### Output

```
[INFO] Creating PR: Add user authentication
[INFO] Base: main ← feature/user-auth
[INFO] Changes: 5 files, +342 insertions, -12 deletions
[SUCCESS] PR created: #42
[INFO] URL: https://github.com/user/repo/pull/42
[SUCCESS] Added to merge queue (position: 1)
```

---

### 4. merge_queue_manager.sh

**Purpose**: FIFO queue for coordinating merges across terminals
**Tier**: 4 (Used automatically by auto_pr.sh)
**Location**: `.workflow/automation/queue/merge_queue_manager.sh`

#### Usage

```bash
bash merge_queue_manager.sh <command> [args]
```

#### Commands

**enqueue**: Add PR to queue
```bash
bash merge_queue_manager.sh enqueue <pr_number> [branch]
```

**process**: Process next item in queue
```bash
bash merge_queue_manager.sh process
```

**status**: Show queue status
```bash
bash merge_queue_manager.sh status
```

**clear**: Clear entire queue
```bash
bash merge_queue_manager.sh clear
```

#### Queue States

```
QUEUED → CONFLICT_CHECK → MERGING → MERGED
   ↓           ↓
FAILED ← ─ ─ ← ┘
```

#### Examples

```bash
# Add PR to queue
bash merge_queue_manager.sh enqueue 42 feature/auth
# Output: Added PR #42 to merge queue (position: 1)

# Check queue status
bash merge_queue_manager.sh status
# Output:
# ═══════════════════════════════════════
#          Merge Queue Status
# ═══════════════════════════════════════
# Pos  PR         Branch                      Status
# ───────────────────────────────────────────
# 1    #42        feature/auth                QUEUED
# 2    #43        feature/payment             QUEUED
# ═══════════════════════════════════════

# Process queue
bash merge_queue_manager.sh process
# [INFO] Processing PR #42 from queue
# [INFO] Checking for conflicts...
# [SUCCESS] No conflicts detected
# [INFO] Merging PR #42...
# [SUCCESS] PR #42 merged successfully

# Clear stuck queue
bash merge_queue_manager.sh clear
# [SUCCESS] Queue cleared
```

#### Conflict Detection

Uses `git merge-tree` for zero-side-effect conflict detection:

```bash
# Automatic conflict check
git merge-tree origin/main origin/feature-branch
# If conflicts found: Status → FAILED
# If clean: Status → MERGING
```

---

### 5. auto_release.sh

**Purpose**: Automated versioning and release creation
**Tier**: 5 (Configurable via `CE_AUTO_RELEASE`)
**Location**: `.workflow/automation/core/auto_release.sh`

#### Usage

```bash
bash auto_release.sh [version_bump]
```

#### Arguments

- `version_bump`: major | minor | patch (optional, default: patch)

#### Features

- ✅ Semantic versioning (semver)
- ✅ Auto-generates changelog from commits
- ✅ Creates git tag
- ✅ Publishes GitHub release
- ✅ Categorizes commits (feat/fix/docs/perf)
- ✅ Audit logging

#### Examples

```bash
# Patch release (1.0.0 → 1.0.1)
bash auto_release.sh patch

# Minor release (1.0.0 → 1.1.0)
bash auto_release.sh minor

# Major release (1.0.0 → 2.0.0)
bash auto_release.sh major

# Default (patch)
bash auto_release.sh

# With confirmation (CE_AUTO_RELEASE=0)
bash auto_release.sh minor  # Asks: "Create release v1.1.0? (y/N)"

# Auto release (CE_AUTO_RELEASE=1) - NOT RECOMMENDED
export CE_AUTO_RELEASE=1
bash auto_release.sh minor  # Creates immediately
```

#### Generated Release Notes

```markdown
## v1.1.0 - 2025-10-10

### Features
- feat: Add user authentication (#42)
- feat: Add payment integration (#43)

### Bug Fixes
- fix: Resolve login timeout (#44)

### Performance
- perf: Optimize database queries (#45)

### Documentation
- docs: Update API reference (#46)
```

---

### 6. rollback.sh

**Purpose**: Automated rollback with health checks
**Tier**: Emergency (Always ask confirmation)
**Location**: `.workflow/automation/rollback/rollback.sh`

#### Usage

```bash
bash rollback.sh [mode] [version]
```

#### Modes

**plan**: Preview rollback (dry run)
```bash
bash rollback.sh plan v1.0.0
```

**execute**: Perform rollback
```bash
bash rollback.sh execute v1.0.0
```

**health**: Run health checks only
```bash
bash rollback.sh health
```

#### Features

- ✅ Health check integration
- ✅ Backup current state before rollback
- ✅ Detailed rollback report
- ✅ Audit logging
- ✅ Automatic state recovery

#### Examples

```bash
# Plan rollback (shows what would happen)
bash rollback.sh plan v5.3.0
# Output: Shows commits to revert, files affected

# Execute rollback
bash rollback.sh execute v5.3.0
# [WARNING] About to rollback to v5.3.0
# [WARNING] Current: v5.4.0 (12 commits ahead)
# Proceed? (y/N): y
# [INFO] Creating backup: rollback-backup-1696934400
# [INFO] Reverting to v5.3.0...
# [SUCCESS] Rollback complete

# Check health after rollback
bash rollback.sh health
# [INFO] Running health checks...
# ✅ Database connectivity: OK
# ✅ API endpoints: OK
# ✅ Service health: OK
```

---

### 7. audit_log.sh

**Purpose**: Security audit logging with HMAC integrity
**Tier**: Core (Always active)
**Location**: `.workflow/automation/security/audit_log.sh`

#### Usage

```bash
bash audit_log.sh <action> [args]
```

#### Actions

**log**: Write audit entry
```bash
bash audit_log.sh log <event_type> <action> <resource> <result> [details]
```

**query**: Search audit logs
```bash
bash audit_log.sh query [filter] [limit]
```

**verify**: Verify log integrity
```bash
bash audit_log.sh verify
```

**cleanup**: Remove old logs
```bash
bash audit_log.sh cleanup
```

#### Event Types

- `GIT_OPERATION`: Git commands (commit, push, merge)
- `AUTOMATION`: Script executions
- `PERMISSION_CHECK`: Access control checks
- `OWNER_OPERATION`: Critical owner actions
- `SECURITY_EVENT`: Security-related events

#### Examples

```bash
# Log git operation
bash audit_log.sh log \
  "GIT_OPERATION" "commit" "feature-branch" "success" "Hash: abc123"

# Query recent operations
bash audit_log.sh query "GIT_OPERATION" 50

# Query owner operations (high priority)
bash audit_log.sh query "OWNER_OPERATION" 10

# Verify integrity
bash audit_log.sh verify
# [INFO] Verifying audit log integrity...
# [INFO] Audit verification complete:
# [INFO]   Checked: 150
# [INFO]   Valid:   150
# [INFO]   Invalid: 0

# Cleanup old logs (>90 days)
bash audit_log.sh cleanup
# [INFO] Cleanup complete: kept 145 entries, removed 5 entries
```

#### Audit Log Format (JSON)

```json
{
  "audit_id": "1696934400-a1b2c3d4",
  "timestamp": "2025-10-10T10:30:00-07:00",
  "event_type": "GIT_OPERATION",
  "action": "commit",
  "resource": "feature/user-auth",
  "result": "success",
  "user": "developer",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "ip_address": "192.168.1.100",
  "details": "Hash: abc123, Message: feat: Add auth",
  "pid": 12345,
  "ppid": 12344,
  "hmac": "d4e5f6a7b8c9..."
}
```

---

## Safety Features

### 1. Pre-Flight Checks

Every script performs validation before execution:

```bash
# Example: auto_push.sh pre-flight checks
✅ Git repository exists
✅ Current branch not protected
✅ Remote exists and reachable
✅ No uncommitted changes (if configured)
✅ Upstream tracking branch set
✅ Pre-push hooks installed
```

### 2. Dry Run Mode

Test without executing:

```bash
export CE_DRY_RUN=1
bash auto_commit.sh "feat: Test"
# Output: DRY RUN: Would commit with message: feat: Test
```

### 3. Fail-Safe Mechanisms

**Automatic Downgrade**:
```bash
# After 3 consecutive failures
if [[ $consecutive_failures -gt 3 ]]; then
    log_warning "Disabling auto-merge due to failures"
    export CE_AUTO_MERGE=0
fi
```

**Protected Branch Enforcement**:
```bash
# Never allow force push to main/master
if is_main_branch && [[ "$force_push" == "true" ]]; then
    die "Force push to protected branch blocked"
fi
```

### 4. Audit Trail

Every operation logged:

```bash
# Automatic audit logging in all scripts
audit_git_operation "push" "origin/feature-auth" "success" "Remote: origin"
```

### 5. Rollback Procedures

Quick rollback for any operation:

```bash
# Rollback last commit
git reset --soft HEAD~1

# Rollback last push (if no one pulled)
git push --force origin HEAD~1:feature-branch

# Rollback release
bash rollback.sh execute v5.3.0
```

---

## Real-World Examples

### Example 1: Solo Developer Daily Workflow

```bash
# Morning setup
cd ~/projects/my-app
source .env  # Loads CE_* variables

# Configuration
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=1
export CE_AUTO_PR=1
export CE_AUTO_MERGE=0  # Stay conservative

# Work on feature
git checkout -b feature/new-dashboard

# Make changes
vim src/dashboard.js

# Auto commit (Tier 1)
bash auto_commit.sh "feat(P3): Add new dashboard"
# ✅ Committed automatically

# Auto push (Tier 2)
bash auto_push.sh
# ✅ Pushed automatically

# Auto PR (Tier 3)
bash auto_pr.sh \
  "Add new dashboard" \
  "Implements user-requested dashboard with charts"
# ✅ PR created: #45
# ✅ Added to merge queue

# Wait for CI, then manually merge
gh pr merge 45 --auto --squash
```

---

### Example 2: Multi-Terminal Parallel Development

```bash
# Terminal 1 (Claude instance A)
cd ~/project
git checkout -b feature/auth
export CE_SESSION_ID="$(uuidgen)"
# ... work on auth ...
bash auto_commit.sh "feat(P3): Add authentication"
bash auto_pr.sh "Add auth" "Implements JWT auth"
# Added to queue: position 1

# Terminal 2 (Claude instance B)
cd ~/project
git checkout -b feature/payment
export CE_SESSION_ID="$(uuidgen)"
# ... work on payment ...
bash auto_commit.sh "feat(P3): Add payment"
bash auto_pr.sh "Add payment" "Stripe integration"
# Added to queue: position 2

# Terminal 3 (Monitor queue)
watch -n 5 'bash merge_queue_manager.sh status'
# Shows:
# Pos  PR    Branch              Status
# 1    #46   feature/auth        MERGING
# 2    #47   feature/payment     QUEUED
```

---

### Example 3: Emergency Hotfix

```bash
# Discover critical bug in production
git checkout master
git pull

# Create hotfix branch
git checkout -b hotfix/critical-security-fix

# Make fix
vim src/security.js

# Fast track with strict mode
export CE_STRICT_MODE=1
export CE_AUTO_PUSH=1
export CE_AUTO_PR=1

# Commit
bash auto_commit.sh "fix(security): Resolve SQL injection vulnerability"

# Create urgent PR
bash auto_pr.sh \
  "URGENT: Security fix" \
  "Resolves SQL injection in auth module. CVE-2025-XXXX" \
  --base master

# Merge immediately after CI
gh pr merge --admin --squash

# Tag hotfix release
bash auto_release.sh patch
# Creates v5.4.1
```

---

### Example 4: Progressive Automation Adoption

**Week 1: Learn the system**
```bash
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=0
export CE_AUTO_PR=0
# Manually confirm each step
```

**Week 2: Enable auto-push**
```bash
export CE_AUTO_PUSH=1
# Commits and pushes automatically
```

**Week 3: Enable auto-PR**
```bash
export CE_AUTO_PR=1
# Creates PRs automatically after push
```

**Week 4+: Full workflow**
```bash
export CE_AUTO_MERGE=1  # If solo developer
# Complete automation up to merge
```

---

## Troubleshooting

### Problem: "CE_EXECUTION_MODE not set"

**Symptom**: Scripts show instructions instead of executing

**Solution**:
```bash
export CE_EXECUTION_MODE=1
```

---

### Problem: "CE_AUDIT_SECRET not set"

**Symptom**: Audit logging fails

**Solution**:
```bash
# Generate secret
export CE_AUDIT_SECRET="$(openssl rand -hex 32)"

# Persist in .env
echo "export CE_AUDIT_SECRET=\"$CE_AUDIT_SECRET\"" >> .env
```

---

### Problem: Auto-push blocked on protected branch

**Symptom**: "Force push to protected branch blocked"

**Explanation**: This is intentional safety

**Solution**:
```bash
# Create feature branch first
git checkout -b feature/my-feature

# Or disable protection temporarily (NOT RECOMMENDED)
gh api -X DELETE /repos/:owner/:repo/branches/main/protection
```

---

### Problem: Merge queue not processing

**Symptom**: PRs stuck in QUEUED state

**Diagnosis**:
```bash
# Check queue status
bash merge_queue_manager.sh status

# Check logs
tail -f /var/log/claude-enhancer/audit.log | grep "merge_queue"
```

**Solution**:
```bash
# Manually process
bash merge_queue_manager.sh process

# Clear and restart
bash merge_queue_manager.sh clear
bash merge_queue_manager.sh enqueue <pr_number>
```

---

### Problem: Commit validation failing

**Symptom**: "Commit message validation failed"

**Common Issues**:
1. **Too short** - Must be ≥10 characters
2. **Missing phase** - Add `[P0-P7]` or `P0-P7`
3. **Wrong format** - Use conventional commits in strict mode

**Solution**:
```bash
# Check message length
echo "feat: Add feature" | wc -c  # Must be ≥10

# Add phase marker
bash auto_commit.sh "feat(P3): Add authentication"

# Disable strict mode temporarily
export CE_STRICT_MODE=0
```

---

### Problem: Large file blocking commit

**Symptom**: "Skipping large file (>10MB)"

**Solution**:
```bash
# Use Git LFS
git lfs track "*.bin"
git add .gitattributes

# Or increase limit in script
# Edit auto_commit.sh, change 10485760 (10MB) to higher value
```

---

### Problem: Permission denied on audit log

**Symptom**: "Permission denied: /var/log/claude-enhancer/audit.log"

**Solution**:
```bash
# Create directory with permissions
sudo mkdir -p /var/log/claude-enhancer
sudo chown $USER /var/log/claude-enhancer
chmod 750 /var/log/claude-enhancer

# Or use user directory
export AUDIT_LOG_DIR="$HOME/.claude-enhancer/logs"
mkdir -p "$AUDIT_LOG_DIR"
```

---

### Getting More Help

- **Complete Troubleshooting Guide**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Security Guide**: [SECURITY_GUIDE.md](SECURITY_GUIDE.md)
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **GitHub Issues**: [Report a bug](https://github.com/claude-enhancer/claude-enhancer/issues)

---

## Summary

### Key Takeaways

1. **Start Conservative** - Begin with `CE_AUTO_PUSH=0`
2. **Enable Progressively** - Add automation as confidence builds
3. **Never Skip CE_AUTO_RELEASE=0** - Always keep releases manual
4. **Audit Everything** - Set `CE_AUDIT_SECRET` and review logs
5. **Test with Dry Run** - Use `CE_DRY_RUN=1` before committing

### Quick Reference

```bash
# Safe solo developer configuration
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=1
export CE_AUTO_PR=1
export CE_AUTO_MERGE=0      # Conservative
export CE_AUTO_RELEASE=0    # Always manual
export CE_AUDIT_SECRET="$(openssl rand -hex 32)"

# Core scripts
auto_commit.sh "message" [files]
auto_push.sh [remote] [branch]
auto_pr.sh "title" "description"
merge_queue_manager.sh status
auto_release.sh [major|minor|patch]
rollback.sh [plan|execute|health]
audit_log.sh [log|query|verify]
```

---

**Next Steps**: Read [MERGE_QUEUE_GUIDE.md](MERGE_QUEUE_GUIDE.md) to understand multi-terminal workflows.

---

*Generated by Claude Enhancer v5.4.0 Documentation System*
*For updates, see: [CHANGELOG.md](../../CHANGELOG.md)*
