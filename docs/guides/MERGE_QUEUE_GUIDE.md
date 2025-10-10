# Merge Queue Guide - Claude Enhancer v5.4.0

**Last Updated**: 2025-10-10
**Version**: 5.4.0
**Queue Type**: FIFO (First In, First Out)

---

## Table of Contents

- [Introduction](#introduction)
- [How It Works](#how-it-works)
- [Multi-Terminal Workflows](#multi-terminal-workflows)
- [Conflict Handling](#conflict-handling)
- [Queue Management](#queue-management)
- [Performance Tips](#performance-tips)

---

## Introduction

The Merge Queue Manager solves a critical problem: **coordinating merges across multiple terminals or developers without conflicts**.

### The Problem Without Queue

```
Terminal 1: Merging PR #42 (feature/auth)
Terminal 2: Merging PR #43 (feature/payment) ← Might conflict!
Terminal 3: Merging PR #44 (feature/billing) ← Might conflict!

Result: Race condition, broken main branch
```

### The Solution With Queue

```
FIFO Queue:
1. PR #42 (feature/auth)      → MERGING   ✓
2. PR #43 (feature/payment)   → QUEUED    ⏳ Waiting
3. PR #44 (feature/billing)   → QUEUED    ⏳ Waiting

Each PR waits its turn, conflicts detected before merge
```

---

## How It Works

### Queue Lifecycle

```
┌──────────┐
│  Created │ Auto-added by auto_pr.sh
└────┬─────┘
     │
     ▼
┌──────────┐
│  QUEUED  │ Waiting in line
└────┬─────┘
     │
     ▼
┌──────────────────┐
│ CONFLICT_CHECK   │ git merge-tree analysis
└────┬───────┬─────┘
     │       │
     │       └─► CONFLICT_DETECTED → Retry or FAILED
     ▼
┌──────────┐
│ MERGING  │ Executing merge
└────┬──────┘
     │
     ▼
┌──────────┐
│  MERGED  │ Success! Removed from queue
└──────────┘
```

### State Machine

| State | Description | Next States |
|-------|-------------|-------------|
| `QUEUED` | Waiting for turn | `CONFLICT_CHECK` |
| `CONFLICT_CHECK` | Checking conflicts | `MERGING`, `CONFLICT_DETECTED` |
| `MERGING` | Executing merge | `MERGED`, `FAILED` |
| `MERGED` | Successfully merged | (removed) |
| `CONFLICT_DETECTED` | Has conflicts | `QUEUED` (retry) or `FAILED` |
| `FAILED` | Merge failed | (terminal state) |
| `TIMEOUT` | Exceeded time limit | (terminal state) |

### Time Limits

```bash
QUEUE_TIMEOUT=600s        # 10 min max in queue
MERGE_TIMEOUT=300s        # 5 min for merge operation
LOCK_TIMEOUT=30s          # 30s for lock acquisition
CONFLICT_CHECK_TIMEOUT=10s # 10s for conflict detection
```

---

## Multi-Terminal Workflows

### Scenario 1: Solo Developer, Multiple Features

**Setup**: One developer, three features in parallel

```bash
# Terminal 1: User Authentication
cd ~/project
git checkout -b feature/auth
export CE_SESSION_ID="auth-session-$(uuidgen)"

# Work on feature
vim src/auth.js
bash auto_commit.sh "feat(P3): Add JWT authentication"
bash auto_pr.sh "Add authentication" "Implements JWT-based auth"
# → Added to queue: position 1

# Terminal 2: Payment Integration
cd ~/project
git checkout -b feature/payment
export CE_SESSION_ID="payment-session-$(uuidgen)"

# Work on feature
vim src/payment.js
bash auto_commit.sh "feat(P3): Add Stripe payment"
bash auto_pr.sh "Add payment" "Stripe integration"
# → Added to queue: position 2

# Terminal 3: Email Notifications
cd ~/project
git checkout -b feature/email
export CE_SESSION_ID="email-session-$(uuidgen)"

# Work on feature
vim src/email.js
bash auto_commit.sh "feat(P3): Add email notifications"
bash auto_pr.sh "Add email" "SendGrid integration"
# → Added to queue: position 3
```

**Queue Status**:
```
Pos  PR    Branch                Status
1    #42   feature/auth          MERGING ← Processing now
2    #43   feature/payment       QUEUED  ← Waiting
3    #44   feature/email         QUEUED  ← Waiting
```

**Execution Order** (FIFO):
1. PR #42 merges first
2. PR #43 conflict-checked, then merged
3. PR #44 conflict-checked, then merged

---

### Scenario 2: AI Multi-Terminal Development

**Setup**: Claude instances across terminals

```bash
# Terminal 1 (Claude A): Backend API
export CE_SESSION_ID="claude-a-$(uuidgen)"
git checkout -b feature/api-endpoints
# Claude A develops REST API
bash auto_pr.sh "Add REST API" "Complete CRUD endpoints"

# Terminal 2 (Claude B): Frontend UI
export CE_SESSION_ID="claude-b-$(uuidgen)"
git checkout -b feature/dashboard-ui
# Claude B develops dashboard
bash auto_pr.sh "Add dashboard UI" "User dashboard with charts"

# Terminal 3 (Claude C): Database Schema
export CE_SESSION_ID="claude-c-$(uuidgen)"
git checkout -b feature/db-migrations
# Claude C creates migrations
bash auto_pr.sh "Add DB schema" "PostgreSQL migrations"
```

**Benefits**:
- ✅ No race conditions
- ✅ Each Claude instance works independently
- ✅ Conflicts detected before merge
- ✅ Audit trail per session

---

### Scenario 3: Team Collaboration

**Setup**: Team of 3 developers

```bash
# Developer 1: Alice
export CE_SESSION_ID="alice-$(uuidgen)"
git checkout -b feature/user-profile
bash auto_pr.sh "User profile" "Add user profile page"
# → Position 1

# Developer 2: Bob
export CE_SESSION_ID="bob-$(uuidgen)"
git checkout -b feature/search
bash auto_pr.sh "Search feature" "Add search functionality"
# → Position 2

# Developer 3: Charlie
export CE_SESSION_ID="charlie-$(uuidgen)"
git checkout -b feature/notifications
bash auto_pr.sh "Notifications" "Real-time notifications"
# → Position 3
```

**Coordination**:
- Queue ensures merge order
- No need for manual coordination
- Each developer sees queue status

---

## Conflict Handling

### Conflict Detection

Uses `git merge-tree` for zero-side-effect detection:

```bash
# How it works
git merge-tree <merge-base> <base-branch> <feature-branch>

# If output contains "<<<<<<<" → Conflicts detected
# Otherwise → Clean merge
```

### Conflict Resolution Workflow

```
1. Conflict Detected
   ├─ Status: CONFLICT_DETECTED
   └─ Log: Lists conflicting files

2. Developer Notified
   ├─ Email/Slack alert (if configured)
   └─ Queue status shows conflict

3. Developer Resolves
   ├─ Rebase feature branch
   ├─ Fix conflicts manually
   └─ Force push (git push --force-with-lease)

4. Re-enter Queue
   ├─ Automatic retry (up to 3 times)
   └─ Or manual re-enqueue
```

### Example: Resolving Conflicts

```bash
# Conflict detected for PR #43
bash merge_queue_manager.sh status
# Output:
# 2   #43   feature/payment   CONFLICT_DETECTED

# Developer resolves locally
git checkout feature/payment
git fetch origin main
git rebase origin/main
# Fix conflicts
git add .
git rebase --continue
git push --force-with-lease

# Queue automatically retries
bash merge_queue_manager.sh process
# → Conflict resolved, merging...
```

### Automatic Retries

```bash
# Configuration
MAX_RETRIES=3
RETRY_DELAY=5s

# Retry strategy
Attempt 1: Wait 5s
Attempt 2: Wait 10s (backoff × 2)
Attempt 3: Wait 20s (backoff × 2)
Failed after 3: Status → FAILED
```

---

## Queue Management

### View Queue Status

```bash
# Basic status
bash merge_queue_manager.sh status

# Detailed status (includes wait times, retries)
bash merge_queue_manager.sh status --detailed

# Watch queue (updates every 5s)
watch -n 5 'bash merge_queue_manager.sh status'
```

**Output**:
```
═══════════════════════════════════════════════════════════════════
                       Merge Queue Status
═══════════════════════════════════════════════════════════════════

Pos  PR         Branch                      Status
───────────────────────────────────────────────────────────────────
1    #42        feature/auth                MERGING
2    #43        feature/payment             QUEUED
3    #44        feature/email               QUEUED
═══════════════════════════════════════════════════════════════════
Summary: Total=3 | Queued=2 | Processing=1 | Merged=0 | Failed=0
```

---

### Manually Add to Queue

```bash
# Add PR to queue
bash merge_queue_manager.sh enqueue <pr_number> [branch]

# Example
bash merge_queue_manager.sh enqueue 45 feature/hotfix
# Output: Added PR #45 to merge queue (position: 4)
```

---

### Process Queue Manually

```bash
# Trigger processing (usually automatic)
bash merge_queue_manager.sh process

# Output:
# [INFO] Processing PR #42 from queue
# [INFO] Checking for conflicts...
# [SUCCESS] No conflicts detected
# [INFO] Merging PR #42...
# [SUCCESS] PR #42 merged successfully
```

---

### Cleanup Stale Entries

```bash
# Remove entries older than 15 minutes
bash merge_queue_manager.sh cleanup

# Custom threshold (seconds)
bash merge_queue_manager.sh cleanup 1800  # 30 minutes
```

---

### Clear Queue

```bash
# Interactive clear (asks confirmation)
bash merge_queue_manager.sh clear

# Force clear (no confirmation)
bash merge_queue_manager.sh clear --force
```

**Warning**: This removes all queue entries! Use only when stuck.

---

## Performance Tips

### Optimize Queue Processing

```bash
# 1. Enable parallel conflict checking
# Queue processes one at a time, but conflict checks are fast

# 2. Keep queue size reasonable
# Recommended: < 10 PRs at a time
bash merge_queue_manager.sh status | wc -l

# 3. Clean up stale entries regularly
# Add to cron: */15 * * * * bash merge_queue_manager.sh cleanup
```

### Reduce Conflict Rate

```bash
# 1. Rebase before creating PR
git fetch origin main
git rebase origin/main
git push --force-with-lease

# 2. Keep PRs small and focused
# Target: < 500 lines changed per PR

# 3. Merge frequently
# Don't let PRs sit for days
```

### Monitor Queue Health

```bash
# Check queue length
queue_length() {
    bash merge_queue_manager.sh status | grep -c "^[0-9]"
}

# Alert if queue too long
if [[ $(queue_length) -gt 10 ]]; then
    echo "WARNING: Queue has $(queue_length) items!"
fi
```

---

## Troubleshooting

### Queue Stuck, Not Processing

**Diagnosis**:
```bash
# Check if lock is stale
ls -ld /tmp/ce_locks/merge_queue.lock
# If older than 15 minutes, it's stale

# Check for zombie processes
ps aux | grep merge_queue_manager
```

**Solution**:
```bash
# Remove stale lock
rm -rf /tmp/ce_locks/merge_queue.lock

# Manually trigger processing
bash merge_queue_manager.sh process
```

---

### PR Stuck in CONFLICT_CHECK

**Diagnosis**:
```bash
# Check how long it's been
bash merge_queue_manager.sh status --detailed
# Shows wait time
```

**Solution**:
```bash
# Manually advance if timeout
bash merge_queue_manager.sh process

# Or remove and re-add
# (Not recommended, better to resolve conflict)
```

---

### Multiple PRs in MERGING State

**This shouldn't happen** (indicates bug)

**Solution**:
```bash
# Clear queue and restart
bash merge_queue_manager.sh clear --force

# Re-add PRs manually
bash merge_queue_manager.sh enqueue 42
bash merge_queue_manager.sh enqueue 43
```

---

## Advanced Features

### Custom Merge Methods

```bash
# Default: squash
bash merge_queue_manager.sh enqueue 42

# In perform_merge (internal):
# - squash: Squash commits
# - merge: Create merge commit
# - rebase: Rebase and fast-forward
```

### Session Tracking

```bash
# Track operations by session
export CE_SESSION_ID="sprint-42-$(uuidgen)"

# All PRs from this session will be tagged
# Useful for debugging and audit trails
```

### Conflict Logs

```bash
# View conflict history
cat /tmp/ce_locks/conflicts.log

# Example output:
# [2025-10-10T10:30:00Z] PR #43 (feature/payment)
# Conflicts:
#   src/payment.js
#   src/billing.js
# ---
```

---

## Summary

### Key Concepts

- **FIFO Queue**: First in, first out processing
- **Conflict Detection**: Zero-side-effect using git merge-tree
- **Multi-Terminal Safe**: Coordinates across terminals/developers
- **Automatic Retry**: Up to 3 retries for transient failures
- **Audit Trail**: Every operation logged

### Quick Reference

```bash
# View status
bash merge_queue_manager.sh status

# Add to queue (usually automatic)
bash merge_queue_manager.sh enqueue <pr_number>

# Process queue (usually automatic)
bash merge_queue_manager.sh process

# Cleanup
bash merge_queue_manager.sh cleanup

# Clear (emergency)
bash merge_queue_manager.sh clear --force
```

---

**Next Steps**: Read [SECURITY_GUIDE.md](SECURITY_GUIDE.md) to understand audit logging and permissions.

---

*Generated by Claude Enhancer v5.4.0 Documentation System*
