# GitHub Merge Queue Setup Guide

**Purpose**: Eliminate CI double-run (PR + merge) by using GitHub Merge Queue
**Requirement**: GitHub Pro/Team/Enterprise
**Savings**: ~5 minutes per merge
**Date**: 2025-10-25

---

## Problem

Currently CI runs twice for every merge:
1. **PR Creation**: CE Unified Gates runs (~5 min)
2. **Merge to main**: CE Unified Gates runs again (~5 min)

**Total waste**: ~5 minutes per merge

---

## Solution: GitHub Merge Queue

Merge Queue ensures CI runs only once and reuses results when merging.

---

## Step 1: Enable Merge Queue

### Via GitHub Web UI:

1. Navigate to: `https://github.com/perfectuser21/Claude_Enhancer/settings/branches`

2. Edit branch protection rule for `main`:
   - Click "Edit" next to `main` branch rule

3. Scroll to **"Require merge queue"**:
   - ☑️ Check "Require merge queue"

4. Configure merge queue settings:
   ```
   ┌─────────────────────────────────────────────┐
   │ ☑️ Require merge queue                      │
   │                                             │
   │ Merge method: ▼ Squash and merge           │
   │ Build concurrency: [5]                      │
   │ Minimum pull requests to merge: [1]         │
   │ Maximum pull requests to merge: [5]         │
   │                                             │
   │ Status check timeout: [60] minutes          │
   │ Merge commit message:                       │
   │   ◉ Pull request title                      │
   │   ○ Pull request title and commit messages  │
   │   ○ Pull request body                       │
   └─────────────────────────────────────────────┘
   ```

5. **Save changes**

---

## Step 2: Update GitHub Actions Workflows

Add `merge_group` trigger to all CI workflows:

### File: `.github/workflows/ce-unified-gates.yml`

```yaml
name: CE Unified Gates

on:
  pull_request:          # Existing: Run on PR
  push:
    branches: [main]     # Existing: Run on push to main
  merge_group:           # NEW: Run on merge queue

# ... rest of workflow
```

### File: `.github/workflows/hardened-gates.yml`

```yaml
name: Hardened Gates

on:
  pull_request:
  merge_group:           # Add this line

# ... rest of workflow
```

### Apply to all CI workflows:
- `ce-unified-gates.yml` ✓
- `hardened-gates.yml` ✓
- `test-suite.yml` ✓
- `security-scan.yml` ✓
- `quality-gate-required.yml` ✓

---

## Step 3: Test the Setup

### 3.1 Create a test PR:
```bash
git checkout -b test/merge-queue
echo "# Test merge queue" >> test-file.md
git add test-file.md
git commit -m "test: verify merge queue setup"
git push origin test/merge-queue
gh pr create --title "test: merge queue" --body "Testing merge queue setup"
```

### 3.2 Wait for CI to complete:
```bash
gh pr checks --watch
```

### 3.3 Add to merge queue:
```bash
# Via GitHub UI: Click "Merge when ready" button
# Or via CLI:
gh pr merge --auto --squash
```

### 3.4 Observe behavior:

**Expected**:
```
✅ CE Unified Gates completed (from PR check)
🔄 Adding to merge queue...
✅ Merge queue: Reusing CI results
✅ Merged to main (NO re-run of CI)
```

**If Merge Queue NOT enabled**:
```
✅ CE Unified Gates completed (from PR check)
🔄 Merging to main...
⏳ CE Unified Gates running again... (5 min waste)
✅ Merged to main
```

---

## Step 4: Update Documentation

### CLAUDE.md

Add note about Merge Queue:

```markdown
### Phase 7: Closure

**CI Optimization** (GitHub Pro):
- ✅ Merge Queue enabled - CI runs only once
- ✅ Saves ~5 minutes per merge
- ✅ PR checks reused for merge validation
```

### CHANGELOG.md

Add entry:

```markdown
## [7.3.1] - 2025-10-25

### 🚀 Performance: Merge Queue Integration

**Optimization**: Eliminate CI double-run using GitHub Merge Queue

- Configure merge queue on main branch (GitHub Pro feature)
- Update 5 workflows to support `merge_group` trigger
- CI results from PR reused during merge
- **Savings**: ~5 minutes per merge

**Impact**: Faster merge workflow with same quality assurance
```

---

## How It Works

### Without Merge Queue:
```
Developer                GitHub                    CI
    |                       |                      |
    |--PR create---------->|                      |
    |                       |--trigger CI--------->|
    |                       |<-------result--------|
    |                       |     (5 min)          |
    |--merge click-------->|                      |
    |                       |--trigger CI--------->|
    |                       |<-------result--------|
    |                       |     (5 min again!)   |
    |                       |--merge to main------>|
```

**Total time**: PR checks (5min) + Merge checks (5min) = 10min

### With Merge Queue:
```
Developer                GitHub MQ                 CI
    |                       |                      |
    |--PR create---------->|                      |
    |                       |--trigger CI--------->|
    |                       |<-------result--------|
    |                       |     (5 min)          |
    |--add to queue------->|                      |
    |                       |--reuse CI results--->|
    |                       |     (instant!)       |
    |                       |--merge to main------>|
```

**Total time**: PR checks (5min) + Merge (instant) = 5min

**Savings**: 5 minutes = 50% faster

---

## Benefits

1. **Faster merges**: 50% reduction in wait time
2. **Resource efficiency**: Half the CI minutes used
3. **Same quality**: All checks still required
4. **Better UX**: Less waiting for developers

---

## Troubleshooting

### Issue: "Merge queue not available"
**Cause**: Account not Pro/Team/Enterprise
**Solution**: Upgrade GitHub plan or use alternative (see below)

### Issue: CI fails in merge queue
**Cause**: Workflow missing `merge_group` trigger
**Solution**: Add `merge_group:` to workflow `on:` section

### Issue: Merge queue stuck
**Cause**: Status check timeout or failing checks
**Solution**:
```bash
# Check queue status
gh api repos/perfectuser21/Claude_Enhancer/merge-queue

# Remove from queue if needed
gh pr ready --undo  # Remove from queue
gh pr checks        # Debug failed checks
```

---

## Alternative for Free Accounts

If you don't have GitHub Pro, use **branch protection + auto-merge**:

### 1. Enable auto-merge without queue:
```yaml
# .github/workflows/auto-merge.yml
name: Auto Merge

on:
  pull_request_review:
    types: [submitted]
  check_suite:
    types: [completed]

jobs:
  auto-merge:
    if: github.event.review.state == 'approved'
    runs-on: ubuntu-latest
    steps:
      - uses: pascalgn/automerge-action@v0.15.6
        env:
          GITHUB_TOKEN: "${{ secrets.GITHUB_TOKEN }}"
          MERGE_METHOD: "squash"
```

**Note**: This still runs CI twice, but at least it's automatic.

---

## Verification

After setup, verify with:

```bash
# Check if merge queue is enabled
gh api repos/perfectuser21/Claude_Enhancer/branches/main/protection \
  --jq '.required_pull_request_reviews.require_merge_queue'

# Expected output: true
```

---

## References

- [GitHub Docs: Merge Queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)
- [GitHub Blog: Merge Queue GA](https://github.blog/2023-07-12-github-merge-queue-is-generally-available/)

---

**Status**: ⏳ Manual configuration required
**Priority**: P1 (Performance optimization)
**Estimated setup time**: 10 minutes
