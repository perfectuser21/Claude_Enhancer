# Merge Queue Manager - Quick Start Guide

**File**: `.workflow/automation/queue/merge_queue_manager.sh`
**Version**: 5.4.0

## Quick Reference

### Basic Commands

```bash
# Show queue status
./merge_queue_manager.sh status

# Show detailed status (with wait times and retries)
./merge_queue_manager.sh status --detailed

# Add PR to queue
./merge_queue_manager.sh enqueue 123

# Add PR with specific branch
./merge_queue_manager.sh enqueue 123 feature/my-feature

# Process queue manually (usually automatic)
./merge_queue_manager.sh process

# Clean up stale entries (older than 15 minutes)
./merge_queue_manager.sh cleanup

# Clean up entries older than custom threshold (in seconds)
./merge_queue_manager.sh cleanup 600

# Clear entire queue (with confirmation)
./merge_queue_manager.sh clear

# Clear queue without confirmation
./merge_queue_manager.sh clear --force

# Show help
./merge_queue_manager.sh help
```

## Common Scenarios

### Scenario 1: Multiple Terminals Want to Merge

**Terminal 1:**
```bash
cd project
git checkout feature/user-auth
# ... make changes, commit ...
gh pr create --title "Add user auth" --body "..."
./merge_queue_manager.sh enqueue 123 feature/user-auth
```

**Terminal 2:**
```bash
cd project
git checkout feature/payment
# ... make changes, commit ...
gh pr create --title "Add payment" --body "..."
./merge_queue_manager.sh enqueue 124 feature/payment
```

**Result:**
- PR #123 merges first
- PR #124 waits in queue
- PR #124 merges after #123 completes
- No race conditions or conflicts

### Scenario 2: Check Merge Status

```bash
# Quick check
./merge_queue_manager.sh status

# Expected output:
═══════════════════════════════════════════════════════════════════
                       Merge Queue Status
═══════════════════════════════════════════════════════════════════

Pos  PR       Branch                    Status
───────────────────────────────────────────────────────────────────
1    #123     feature/user-auth         MERGING
2    #124     feature/payment           QUEUED
═══════════════════════════════════════════════════════════════════
Summary: Total=2 | Queued=1 | Processing=1 | Merged=0 | Failed=0
```

### Scenario 3: Conflict Detected

**What happens:**
1. Queue detects conflicts automatically
2. PR marked as `CONFLICT_DETECTED`
3. Retry attempted (up to 3 times)
4. If still failing, marked as `FAILED`

**Check conflicts:**
```bash
./merge_queue_manager.sh status --detailed

# Pos  PR     Branch              Status                Wait(s)  Retries
# 1    #125   fix/bug-123         CONFLICT_DETECTED    120      2
```

**Resolution:**
```bash
# Option 1: Resolve conflicts manually
cd project
git checkout fix/bug-123
git pull origin main
# Resolve conflicts
git add .
git commit
git push

# Re-enqueue
./merge_queue_manager.sh enqueue 125 fix/bug-123

# Option 2: Close and recreate PR
gh pr close 125
# Create new PR after rebasing
```

### Scenario 4: Cleanup Old Entries

```bash
# View current queue
./merge_queue_manager.sh status

# Clean up entries older than 15 minutes
./merge_queue_manager.sh cleanup

# Clean up more aggressively (5 minutes)
./merge_queue_manager.sh cleanup 300
```

## Understanding Queue States

| State | Meaning | What to Do |
|-------|---------|------------|
| `QUEUED` | Waiting in line | Wait for processing |
| `CONFLICT_CHECK` | Checking for conflicts | Automatic, should be quick (< 10s) |
| `MERGING` | Currently merging | Automatic, wait (< 30s) |
| `MERGED` | Successfully merged ✅ | Done! Can remove from queue |
| `FAILED` | Merge failed ❌ | Check logs, fix issues, re-enqueue |
| `CONFLICT_DETECTED` | Has conflicts ⚠️ | Resolve conflicts and re-enqueue |
| `TIMEOUT` | Took too long | Check queue health, re-enqueue |

## Environment Variables

```bash
# Enable debug logging
export CE_DEBUG=1
./merge_queue_manager.sh status

# Custom session ID
export CE_SESSION_ID="my-session-123"
./merge_queue_manager.sh enqueue 123
```

## Integration with Workflow

### In Your Scripts

```bash
#!/bin/bash
# my-deployment-script.sh

# Source the queue manager
source .workflow/automation/queue/merge_queue_manager.sh

# Create PR
pr_number=$(gh pr create --title "Deploy v1.2.3" --body "..." | grep -oP '\d+')

# Enqueue for merge
enqueue_pr "$pr_number" "$(git branch --show-current)"

# Wait for merge completion (optional)
while ! grep -q ":${pr_number}:.*:MERGED:" /tmp/ce_locks/merge_queue.fifo; do
    echo "Waiting for merge..."
    sleep 10
done

echo "Deployment PR merged!"
```

### In Git Hooks

```bash
# .git/hooks/pre-push

#!/bin/bash
branch=$(git rev-parse --abbrev-ref HEAD)

if [[ "$branch" == feature/* ]]; then
    echo "🔄 This branch will be auto-queued for merge after PR creation"
    echo "   Use: ./merge_queue_manager.sh enqueue <pr_number>"
fi
```

## Troubleshooting

### Queue Not Processing

**Symptom:** PRs stuck in QUEUED state

**Check:**
```bash
# Is there a stale lock?
ls -ld /tmp/ce_locks/merge_queue.lock

# Manually process
./merge_queue_manager.sh process
```

### "Failed to acquire lock" Error

**Cause:** Another process holds the lock or stale lock

**Fix:**
```bash
# Check lock age
ls -ld /tmp/ce_locks/merge_queue.lock

# If older than 15 minutes, remove it
rm -rf /tmp/ce_locks/merge_queue.lock

# Try again
./merge_queue_manager.sh enqueue 123
```

### GitHub CLI Not Authenticated

**Error:** `Not authenticated with GitHub CLI`

**Fix:**
```bash
# Login to GitHub
gh auth login

# Verify
gh auth status
```

### Network Timeout

**Error:** `Failed to fetch branches (timeout or network error)`

**Fix:**
```bash
# Check network
ping github.com

# Check git config
git config --get remote.origin.url

# Try manual fetch
git fetch origin main
```

## Performance Tips

1. **Regular Cleanup:**
   ```bash
   # Add to cron (every hour)
   0 * * * * cd /path/to/project && ./merge_queue_manager.sh cleanup
   ```

2. **Monitor Queue Size:**
   ```bash
   # Check queue size
   wc -l /tmp/ce_locks/merge_queue.fifo

   # If > 100 entries, investigate why
   ```

3. **Use --detailed Sparingly:**
   ```bash
   # Quick check (fast)
   ./merge_queue_manager.sh status

   # Detailed analysis (slower)
   ./merge_queue_manager.sh status --detailed
   ```

4. **Batch Operations:**
   ```bash
   # Instead of:
   for pr in 1 2 3; do
       ./merge_queue_manager.sh enqueue $pr
   done

   # Do:
   for pr in 1 2 3; do
       ./merge_queue_manager.sh enqueue $pr &
   done
   wait
   ```

## Advanced Usage

### Custom Merge Method

```bash
# Default is squash
./merge_queue_manager.sh enqueue 123

# To use different method, modify perform_merge() function
# Or use gh directly after queue processing
```

### Monitoring Queue Metrics

```bash
# Queue size over time
watch -n 5 'wc -l /tmp/ce_locks/merge_queue.fifo'

# Success rate
merged=$(grep -c ":MERGED:" /tmp/ce_locks/merge_queue.fifo)
failed=$(grep -c ":FAILED:" /tmp/ce_locks/merge_queue.fifo)
echo "Success rate: $((merged * 100 / (merged + failed)))%"

# Average wait time
awk -F: 'BEGIN {total=0; count=0}
         {wait = systime() - $1; total += wait; count++}
         END {print "Avg wait: " total/count " seconds"}' \
    /tmp/ce_locks/merge_queue.fifo
```

### Queue State Export

```bash
# Export to JSON
echo "["
while IFS=: read -r ts pr branch session status retry started; do
    echo "  {\"pr\": $pr, \"branch\": \"$branch\", \"status\": \"$status\"},"
done < /tmp/ce_locks/merge_queue.fifo | sed '$ s/,$//'
echo "]"
```

## Best Practices

1. **Always check status before enqueuing:**
   ```bash
   ./merge_queue_manager.sh status
   ./merge_queue_manager.sh enqueue 123
   ```

2. **Don't force-clear unless necessary:**
   ```bash
   # Bad: Loses queue state
   ./merge_queue_manager.sh clear --force

   # Good: Selective cleanup
   ./merge_queue_manager.sh cleanup
   ```

3. **Monitor conflicts proactively:**
   ```bash
   # Check for conflicts daily
   grep "CONFLICT_DETECTED" /tmp/ce_locks/merge_queue.fifo
   ```

4. **Use descriptive branch names:**
   ```bash
   # Good
   ./merge_queue_manager.sh enqueue 123 feature/user-authentication

   # Bad
   ./merge_queue_manager.sh enqueue 123 test
   ```

5. **Log important operations:**
   ```bash
   ./merge_queue_manager.sh enqueue 123 2>&1 | tee -a merge_queue.log
   ```

## Quick Health Check

```bash
#!/bin/bash
# queue_health_check.sh

echo "=== Merge Queue Health Check ==="

# Check queue file exists
[[ -f /tmp/ce_locks/merge_queue.fifo ]] && echo "✅ Queue file exists" || echo "❌ Queue file missing"

# Check lock state
[[ -d /tmp/ce_locks/merge_queue.lock ]] && echo "⚠️  Queue locked" || echo "✅ Queue unlocked"

# Count entries by state
echo ""
echo "Queue contents:"
for state in QUEUED CONFLICT_CHECK MERGING MERGED FAILED; do
    count=$(grep -c ":${state}:" /tmp/ce_locks/merge_queue.fifo 2>/dev/null || echo 0)
    echo "  $state: $count"
done

# Check oldest entry
echo ""
oldest=$(head -n1 /tmp/ce_locks/merge_queue.fifo 2>/dev/null | cut -d: -f1)
if [[ -n "$oldest" ]]; then
    age=$(($(date +%s) - oldest))
    echo "Oldest entry: ${age}s ago"
    [[ $age -gt 900 ]] && echo "⚠️  WARNING: Oldest entry > 15 minutes" || echo "✅ Age OK"
fi

echo ""
echo "=== Health Check Complete ==="
```

Save as `queue_health_check.sh` and run periodically.

## File Locations

- **Queue File:** `/tmp/ce_locks/merge_queue.fifo`
- **Lock Directory:** `/tmp/ce_locks/merge_queue.lock`
- **Backup File:** `/tmp/ce_locks/merge_queue.backup`
- **Conflict Log:** `/tmp/ce_locks/conflicts.log`
- **Status JSON:** `/tmp/ce_locks/merge_queue_status.json`

## Getting Help

```bash
# Built-in help
./merge_queue_manager.sh help

# Check logs with debug mode
export CE_DEBUG=1
./merge_queue_manager.sh process

# Read implementation report
cat docs/MERGE_QUEUE_IMPLEMENTATION_REPORT.md

# Read architecture document
cat docs/P1_MERGE_QUEUE_ARCHITECTURE.md
```

---

**Questions?** Check the full implementation report for detailed information on error handling, edge cases, and performance characteristics.
