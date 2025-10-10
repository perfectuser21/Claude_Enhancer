# Troubleshooting Guide / 故障定位指南

## 📋 Guide Version / 指南版本
- **Version**: 1.0.0
- **Last Updated**: 2025-10-09
- **Scope**: Claude Enhancer 5.3+ Failure Modes
- **Purpose**: Diagnose and fix common protection system failures

---

## 🎯 Failure Modes Overview / 故障模式概览

Claude Enhancer defines 5 failure modes (FM-1 to FM-5) that represent common ways the protection system can fail or be bypassed. This guide provides detailed diagnostics and fixes for each mode.

Claude Enhancer定义了5种故障模式（FM-1到FM-5），代表保护系统可能失败或被绕过的常见方式。本指南为每种模式提供详细的诊断和修复方法。

| 故障模式 | 描述 | 严重性 | 保障层 |
|---------|------|-------|-------|
| **FM-1** | 本地钩子没生效 | 🔴 Critical | Layer 3 |
| **FM-2** | `--no-verify`绕过 | 🟡 High | Layer 3 + Layer 4 |
| **FM-3** | AI在未初始化目录操作 | 🔴 Critical | Layer 1 + Layer 2 |
| **FM-4** | CI未设为Required | 🟡 High | Layer 4 |
| **FM-5** | 分支命名不规范 | 🟢 Medium | Layer 1 |

---

## 🔴 FM-1: Local Hooks Not Working / 本地钩子没生效

### 📝 Description / 描述

Local Git hooks (pre-commit, commit-msg, pre-push) are not executing, allowing commits that should be blocked.

本地Git钩子（pre-commit、commit-msg、pre-push）未执行，允许了应被阻止的提交。

### 🔍 Symptoms / 症状

**Indicator 1**: Commits succeed even when violating rules
```bash
# This should be blocked but succeeds:
git checkout main
echo "test" > file.txt && git add file.txt
git commit -m "test"  # ❌ Should fail but doesn't
```

**Indicator 2**: No hook output during commit
```bash
# Normal hook output should show:
# [BRANCH] main
# [WORKFLOW] P3
# [LINT] Checking...
# ✓ All checks passed

# But you see nothing - just git's default output
```

**Indicator 3**: Hook file permissions
```bash
ls -la .git/hooks/pre-commit
# Output: -rw-r--r--  (NOT executable - missing 'x')
# Expected: -rwxr-xr-x  (executable)
```

**Indicator 4**: Hook not installed
```bash
[ -f .git/hooks/pre-commit ] && echo "EXISTS" || echo "MISSING"
# Output: MISSING
```

### 🧪 Diagnostic Steps / 诊断步骤

#### Step 1: Check Hook Existence

```bash
# Check if hooks exist
for hook in pre-commit commit-msg pre-push; do
    if [ -f ".git/hooks/$hook" ]; then
        echo "✓ $hook exists"
    else
        echo "✗ $hook MISSING"
    fi
done
```

**Expected Output**:
```
✓ pre-commit exists
✓ commit-msg exists
✓ pre-push exists
```

---

#### Step 2: Check Hook Permissions

```bash
# Check if hooks are executable
ls -la .git/hooks/pre-commit .git/hooks/commit-msg .git/hooks/pre-push 2>/dev/null || echo "Some hooks missing"
```

**Expected Output**:
```
-rwxr-xr-x  1 user group  12345 Oct  9 10:00 .git/hooks/pre-commit
-rwxr-xr-x  1 user group   5678 Oct  9 10:00 .git/hooks/commit-msg
-rwxr-xr-x  1 user group   3456 Oct  9 10:00 .git/hooks/pre-push
```

**Problem**: If you see `-rw-r--r--` (no 'x'), hooks won't execute.

---

#### Step 3: Check Git Hooks Path Configuration

```bash
# Check if git is configured to use hooks
git config --get core.hooksPath
```

**Expected Output**:
```
.git/hooks
```

**Problem**: If empty or pointing elsewhere, hooks won't be found.

---

#### Step 4: Manually Test Hook Execution

```bash
# Try running the hook directly
bash .git/hooks/pre-commit
echo "Exit code: $?"
```

**Expected Output**:
```
❌ ERROR: 禁止直接提交到 main 分支
Exit code: 1  (non-zero means it's working)
```

**Problem**: If you see syntax errors or "Permission denied", the hook is broken.

---

#### Step 5: Check for Hook Bypasses in Git Config

```bash
# Check if hooks are disabled
git config --get core.hooksPath
git config --get commit.gpgSign
git config --get alias.commit
```

**Problem**: If `core.hooksPath` points to `/dev/null` or a non-existent directory, hooks are bypassed.

---

### 🔧 Fix Actions / 修复动作

#### Fix A: Run Bootstrap Script (Recommended)

```bash
# If bootstrap.sh exists, run it to set up everything
bash tools/bootstrap.sh
```

**What it does**:
- Configures `git config core.hooksPath .git/hooks`
- Sets executable permissions on all hooks: `chmod +x .git/hooks/*`
- Validates setup with health checks

---

#### Fix B: Manual Hook Installation

If bootstrap.sh doesn't exist or fails:

```bash
# 1. Configure hooks path
git config core.hooksPath .git/hooks

# 2. Ensure hooks directory exists
mkdir -p .git/hooks

# 3. Copy hooks from template (if available)
if [ -d ".claude/git-hooks-template" ]; then
    cp .claude/git-hooks-template/* .git/hooks/
fi

# 4. Set executable permissions
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-push

# 5. Verify
ls -la .git/hooks/pre-commit
```

---

#### Fix C: Fix Permissions Only

If hooks exist but aren't executable:

```bash
# Batch fix all hooks
chmod +x .git/hooks/*

# Or individually
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-push
```

---

#### Fix D: Reinstall from Repository

If hooks are corrupted:

```bash
# 1. Backup current hooks
mv .git/hooks .git/hooks.backup

# 2. Restore from a clean state
git checkout HEAD -- .git/hooks/

# Or copy from another working clone
# scp -r other-clone/.git/hooks/* .git/hooks/

# 3. Set permissions
chmod +x .git/hooks/*
```

---

### ✅ Verification / 验证

```bash
# Test the fix
git checkout main
touch test-file.txt && git add test-file.txt
git commit -m "test: should be blocked"

# Expected output:
# ❌ ERROR: 禁止直接提交到 main 分支
# (commit should be rejected)
```

---

### 🛡️ Prevention / 预防

```bash
# Add to .bashrc or .zshrc to warn if hooks aren't configured
if [ -d ".git" ] && [ -z "$(git config --get core.hooksPath)" ]; then
    echo "⚠️  Warning: Git hooks not configured. Run: git config core.hooksPath .git/hooks"
fi

# Add to team onboarding:
# 1. Run tools/bootstrap.sh on every new clone
# 2. Never use --no-verify
# 3. If hooks fail, fix the problem, don't bypass
```

---

## 🟡 FM-2: Developer Used `--no-verify` / 开发者用了--no-verify

### 📝 Description / 描述

Developer bypassed local hooks using `git commit --no-verify`, allowing rule violations to reach the remote repository.

开发者使用`git commit --no-verify`绕过了本地钩子，允许违规提交到达远程仓库。

### 🔍 Symptoms / 症状

**Indicator 1**: Commits on main branch appear in history
```bash
git log --oneline --graph main | head -n 10

# You see direct commits on main (should only have merge commits)
* abc1234 feat: add feature (direct commit - BAD)
* def5678 Merge pull request #123 (merge commit - GOOD)
```

**Indicator 2**: CI fails but local didn't
```bash
# Locally commit succeeded, but CI shows:
# ❌ branch-protection - Failed
# ❌ workflow-validation - Failed
```

**Indicator 3**: Git logs show --no-verify usage
```bash
# Check shell history for suspicious commands
grep -r "no-verify" ~/.bash_history ~/.zsh_history

# Output:
# git commit --no-verify -m "quick fix"
```

---

### 🧪 Diagnostic Steps / 诊断步骤

#### Step 1: Identify Violating Commits

```bash
# Find direct commits on main (not merges)
git log --oneline --no-merges main | head -n 20

# Each line is a potential violation
```

---

#### Step 2: Check CI Logs

```bash
# View the CI job that failed
gh run list --limit 5
gh run view <run-id>

# Look for:
# ❌ branch-protection: Detected commit on main branch
```

---

#### Step 3: Audit Recent Commits

```bash
# Check who committed directly to main
git log --format="%H %an %ae %s" --no-merges main -10

# Output:
# abc1234 John Doe john@example.com feat: add feature
```

---

#### Step 4: Review Branch Protection

```bash
# Check if branch protection is enabled on GitHub
gh api repos/:owner/:repo/branches/main/protection 2>/dev/null | jq '.required_status_checks'

# If null or missing, branch protection is NOT enforced
```

---

### 🔧 Fix Actions / 修复动作

#### Fix A: Revert the Violating Commit

```bash
# 1. Identify the commit
git log --oneline --no-merges main | head -n 5

# 2. Revert it (creates a new commit that undoes changes)
git revert <commit-hash>

# 3. Push
git push origin main
```

---

#### Fix B: Move Commit to Feature Branch (Preferred)

```bash
# 1. Create a feature branch from the violating commit
git checkout -b feature/fix-direct-commit <commit-hash>

# 2. Reset main to before the violation
git checkout main
git reset --hard <commit-hash>~1  # Go back one commit

# 3. Force push (⚠️ coordinate with team first!)
git push --force origin main

# 4. Push the feature branch
git checkout feature/fix-direct-commit
git push -u origin feature/fix-direct-commit

# 5. Create a PR
gh pr create --title "Fix: Move direct commit to feature branch"
```

---

#### Fix C: Enable Server-Side Branch Protection (Prevention)

**On GitHub**:
```bash
# Via GitHub UI:
# Repo Settings → Branches → Branch protection rules → Add rule
# Branch name: main
# ✅ Require pull request before merging
# ✅ Require status checks to pass before merging
#    - Select: branch-protection, workflow-validation, etc.
# ✅ Do not allow bypassing the above settings

# Via CLI:
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field 'required_status_checks[strict]=true' \
  --field 'required_status_checks[contexts][]=branch-protection' \
  --field 'required_status_checks[contexts][]=workflow-validation' \
  --field 'enforce_admins=true' \
  --field 'required_pull_request_reviews[required_approving_review_count]=1'
```

**On GitLab**:
```bash
# Project Settings → Repository → Protected Branches
# Branch: main
# Allowed to merge: Maintainers
# Allowed to push: No one
# Require approval: 1 approval
```

---

#### Fix D: Add Pre-Push Check for Remote

Add to `.git/hooks/pre-push`:

```bash
#!/bin/bash
# Detect if pushing directly to main
while read local_ref local_sha remote_ref remote_sha; do
    if [ "$remote_ref" = "refs/heads/main" ] && [ "$local_sha" != "0000000000000000000000000000000000000000" ]; then
        # Check if this push contains non-merge commits
        non_merge_commits=$(git log --oneline --no-merges $remote_sha..$local_sha 2>/dev/null | wc -l)
        if [ "$non_merge_commits" -gt 0 ]; then
            echo "❌ ERROR: Attempting to push $non_merge_commits direct commits to main"
            echo "This violates the branch protection policy"
            exit 1
        fi
    fi
done

exit 0
```

---

### ✅ Verification / 验证

```bash
# Test that --no-verify is caught by CI
git checkout main
echo "test" > test.txt && git add test.txt
git commit --no-verify -m "test: bypass local hooks"
git push

# Expected: Local push succeeds, but CI fails with:
# ❌ branch-protection job failed
```

---

### 🛡️ Prevention / 预防

```bash
# 1. Team Policy: Document and enforce
echo "NEVER use --no-verify" >> CONTRIBUTING.md

# 2. Monitor for violations
# Add to CI:
git log --format="%H %s" --grep="--no-verify" && echo "⚠️ Suspicious commit messages" || true

# 3. Education
# - Explain WHY hooks exist (quality, security)
# - Show how to fix issues instead of bypassing

# 4. Code Review
# - Reviewers should reject PRs with signs of --no-verify usage
```

---

## 🔴 FM-3: AI Operating in Uninitialized Directory / AI在未初始化目录操作

### 📝 Description / 描述

AI (Claude Code or other agents) attempts to modify files in a directory that hasn't been initialized with Claude Enhancer's workflow and hooks.

AI（Claude Code或其他代理）尝试在未使用Claude Enhancer工作流和钩子初始化的目录中修改文件。

### 🔍 Symptoms / 症状

**Indicator 1**: AI creates files without workflow context
```bash
# AI creates files directly:
src/new-feature.js  # Created without phase context
docs/README.md      # Modified without PLAN.md

# Missing context:
ls .phase/current   # No such file or directory
ls .gates/          # No such file or directory
```

**Indicator 2**: No hooks installed
```bash
[ -f .git/hooks/pre-commit ] && echo "✓ Hooks installed" || echo "✗ No hooks"
# Output: ✗ No hooks
```

**Indicator 3**: AI proceeds without verification
```
User: "Add a login feature"

AI (BAD - FM-3):
Sure! Creating src/auth/login.js...
[Writes code directly without checking setup]

AI (GOOD - Compliant):
Let me first verify the project is initialized with Claude Enhancer...
[Runs diagnostic checks]
❌ Hooks not found. Please run: bash tools/bootstrap.sh
```

---

### 🧪 Diagnostic Steps / 诊断步骤

#### Step 1: Check Claude Enhancer Initialization

```bash
# Full diagnostic check
echo "=== Claude Enhancer Initialization Status ==="

# 1. Git repository
git rev-parse --git-dir >/dev/null 2>&1 && echo "✓ Git repo" || echo "✗ Not a git repo"

# 2. Hooks installed
[ -f .git/hooks/pre-commit ] && echo "✓ Hooks installed" || echo "✗ No hooks"

# 3. Hooks executable
[ -x .git/hooks/pre-commit ] && echo "✓ Hooks executable" || echo "✗ Not executable"

# 4. Hooks path configured
hooks_path=$(git config --get core.hooksPath)
[ -n "$hooks_path" ] && echo "✓ Hooks path: $hooks_path" || echo "✗ Hooks path not set"

# 5. Workflow initialized
[ -f .phase/current ] && echo "✓ Workflow initialized ($(cat .phase/current))" || echo "✗ No workflow"

# 6. Gates directory
[ -d .gates ] && echo "✓ Gates directory exists" || echo "✗ No gates"
```

**Expected Output** (Initialized):
```
✓ Git repo
✓ Hooks installed
✓ Hooks executable
✓ Hooks path: .git/hooks
✓ Workflow initialized (P3)
✓ Gates directory exists
```

**Problem Output** (FM-3):
```
✓ Git repo
✗ No hooks
✗ Not executable
✗ Hooks path not set
✗ No workflow
✗ No gates
```

---

#### Step 2: Check AI Contract Compliance

```bash
# If AI_CONTRACT.md exists, AI should follow it
[ -f docs/AI_CONTRACT.md ] && echo "✓ AI Contract exists" || echo "✗ No AI Contract"

# Check if AI is following the 3-step sequence
echo "AI should verify:"
echo "  Step 1: Git repository status ✓/✗"
echo "  Step 2: Proper branch (not main) ✓/✗"
echo "  Step 3: Workflow entered (P0-P7) ✓/✗"
```

---

#### Step 3: Identify Unauthorized File Modifications

```bash
# Check for files created without workflow context
git log --all --format="%H %s" --grep="P[0-7]" --invert-grep | head -n 10

# These commits lack phase context, likely FM-3 violations
```

---

### 🔧 Fix Actions / 修复动作

#### Fix A: Initialize Claude Enhancer (First Time)

```bash
# 1. Run bootstrap script
bash tools/bootstrap.sh

# What it does:
# - Installs git hooks
# - Sets permissions
# - Configures git
# - Validates setup

# 2. Initialize workflow
mkdir -p .phase .gates
echo "P0" > .phase/current

# 3. Create initial spike document
mkdir -p docs
touch docs/SPIKE_$(date +%Y%m%d).md
```

---

#### Fix B: Educate AI with Contract

Ensure `docs/AI_CONTRACT.md` is in place and reference it in prompts:

```bash
# Add to user prompt:
"Before modifying any files, follow the AI Operation Contract (docs/AI_CONTRACT.md):
1. Verify git repository status
2. Ensure on feature branch (not main)
3. Enter workflow (P0-P7)
4. Follow phase-specific rules"
```

---

#### Fix C: Add AI Pre-Flight Check

Create a script that AI must run before ANY file modification:

**File**: `tools/ai_preflight_check.sh`

```bash
#!/bin/bash
# AI Pre-flight Check - Must pass before file modifications

set -euo pipefail

echo "=== AI Pre-flight Check ==="

# 1. Git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "❌ FAIL: Not a git repository"
    echo "Fix: git init"
    exit 1
fi
echo "✓ Git repository"

# 2. Hooks installed
if [ ! -f .git/hooks/pre-commit ]; then
    echo "❌ FAIL: Hooks not installed"
    echo "Fix: bash tools/bootstrap.sh"
    exit 1
fi
echo "✓ Hooks installed"

# 3. Not on main branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    echo "❌ FAIL: On protected branch ($BRANCH)"
    echo "Fix: git checkout -b feature/your-feature"
    exit 1
fi
echo "✓ On feature branch: $BRANCH"

# 4. Workflow initialized
if [ ! -f .phase/current ]; then
    echo "❌ FAIL: Workflow not initialized"
    echo "Fix: mkdir -p .phase && echo 'P0' > .phase/current"
    exit 1
fi
PHASE=$(cat .phase/current)
echo "✓ Workflow initialized: $PHASE"

# 5. Phase valid
if ! echo "$PHASE" | grep -qE '^P[0-7]$'; then
    echo "❌ FAIL: Invalid phase: $PHASE"
    echo "Fix: echo 'P0' > .phase/current"
    exit 1
fi
echo "✓ Valid phase: $PHASE"

echo ""
echo "✅ All checks passed! Safe to proceed with file modifications."
exit 0
```

Usage:
```bash
# AI runs this before any file modification
bash tools/ai_preflight_check.sh || exit 1

# If it passes, proceed with task
# If it fails, show user the fix commands
```

---

#### Fix D: Enforce in Global Claude Config

Add to `~/.claude/CLAUDE.md`:

```markdown
## MANDATORY: Before ANY File Modification

Run this verification:
\`\`\`bash
bash tools/ai_preflight_check.sh
\`\`\`

If it fails, DO NOT PROCEED. Instead:
1. Show the user the error
2. Provide the exact fix command
3. Wait for user to run the fix
4. Retry the check

NEVER bypass this check. NEVER modify files without passing the check.
```

---

### ✅ Verification / 验证

```bash
# Test AI compliance

# Scenario 1: Uninitialized directory
cd /tmp/test-project
git init

# Ask AI: "Create a login feature"
# Expected: AI runs preflight check, detects missing hooks, refuses to proceed

# Scenario 2: After initialization
bash tools/bootstrap.sh
mkdir -p .phase && echo "P0" > .phase/current

# Ask AI: "Create a login feature"
# Expected: AI proceeds through P0 (spike) → P1 (plan) → P2 (skeleton) → P3 (implementation)
```

---

### 🛡️ Prevention / 预防

```bash
# 1. Template Repository
# Create a template with Claude Enhancer pre-installed
gh repo create my-project --template my-org/claude-enhancer-template

# 2. Onboarding Checklist
cat > ONBOARDING.md <<EOF
# Project Onboarding

## Step 1: Clone
\`\`\`bash
git clone <repo-url>
cd <repo>
\`\`\`

## Step 2: Initialize Claude Enhancer
\`\`\`bash
bash tools/bootstrap.sh
\`\`\`

## Step 3: Verify
\`\`\`bash
bash tools/ai_preflight_check.sh
\`\`\`

## Step 4: Start Working
\`\`\`bash
git checkout -b feature/my-feature
echo "P0" > .phase/current
# Now you can work with AI
\`\`\`
EOF

# 3. AI System Prompt
# Include in .claude/CLAUDE.md or project CLAUDE.md:
"This project uses Claude Enhancer. ALWAYS run tools/ai_preflight_check.sh before modifying files."
```

---

## 🟡 FM-4: CI Not Set as Required / CI未设为Required

### 📝 Description / 描述

GitHub/GitLab CI checks exist but are not enforced as required status checks for merging PRs, allowing bypasses.

GitHub/GitLab CI检查存在但未设置为合并PR的必需状态检查，允许绕过。

### 🔍 Symptoms / 症状

**Indicator 1**: PR can merge despite failing CI
```bash
# On GitHub PR page:
❌ branch-protection — Failed
❌ workflow-validation — Failed
[Merge pull request] ← Button is still enabled (BAD)
```

**Indicator 2**: Branch protection not configured
```bash
# Check via API
gh api repos/:owner/:repo/branches/main/protection 2>&1 | grep "Branch not protected"

# Output:
# HTTP 404: Branch not protected
```

**Indicator 3**: Status checks not required
```bash
gh api repos/:owner/:repo/branches/main/protection | jq '.required_status_checks'

# Output:
# null  (or missing the CE checks)
```

---

### 🧪 Diagnostic Steps / 诊断步骤

#### Step 1: Check Branch Protection Status

```bash
# GitHub
gh api repos/:owner/:repo/branches/main/protection 2>/dev/null && echo "✓ Protected" || echo "✗ Not protected"

# GitLab
# Via UI: Settings → Repository → Protected Branches
```

---

#### Step 2: List Required Status Checks

```bash
# GitHub
gh api repos/:owner/:repo/branches/main/protection | jq '.required_status_checks.contexts[]'

# Expected output (should include):
# "branch-protection"
# "workflow-validation"
# "path-whitelist"
# "security-scan"
# "must-produce"
# "code-quality"
# "test-execution"
```

---

#### Step 3: Test PR Merge Without Passing CI

```bash
# 1. Create a test PR with failing CI
git checkout -b test/fm4-check
echo "test" > test.txt && git add test.txt
git commit -m "test: trigger CI"
git push -u origin test/fm4-check

gh pr create --title "Test: FM-4 check" --body "Should not be mergeable with failing CI"

# 2. Check if merge button is enabled despite CI failure
gh pr view --json mergeable,statusCheckRollup

# If mergeable: true despite failures → FM-4 confirmed
```

---

### 🔧 Fix Actions / 修复动作

#### Fix A: Enable Branch Protection (GitHub)

**Via GitHub UI**:
```
1. Go to: Repo → Settings → Branches
2. Click: "Add rule" (or edit existing for main)
3. Branch name pattern: main
4. Enable: ✅ Require status checks to pass before merging
5. Select status checks:
   ✅ branch-protection
   ✅ workflow-validation
   ✅ path-whitelist
   ✅ security-scan
   ✅ must-produce
   ✅ code-quality
   ✅ test-execution
6. Enable: ✅ Require branches to be up to date before merging
7. Enable: ✅ Require pull request before merging
8. Enable: ✅ Include administrators (important!)
9. Click: "Create" or "Save changes"
```

**Via GitHub CLI**:
```bash
# Define required checks
REQUIRED_CHECKS='["branch-protection","workflow-validation","path-whitelist","security-scan","must-produce","code-quality","test-execution"]'

# Apply branch protection
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field "required_status_checks[strict]=true" \
  --field "required_status_checks[contexts]=$REQUIRED_CHECKS" \
  --field "enforce_admins=true" \
  --field "required_pull_request_reviews[required_approving_review_count]=1" \
  --field "required_pull_request_reviews[dismiss_stale_reviews]=true" \
  --field "restrictions=null"

echo "✅ Branch protection enabled for main"
```

---

#### Fix B: Enable Branch Protection (GitLab)

**Via GitLab UI**:
```
1. Project → Settings → Repository → Protected Branches
2. Branch: main
3. Allowed to merge: Maintainers (or Developers with approval)
4. Allowed to push: No one
5. Allowed to force push: ❌ No
6. Code owner approval: ✅ Enabled (if using CODEOWNERS)
7. Save changes

Then: Settings → General → Merge requests
8. Enable: ✅ Pipelines must succeed
9. Enable: ✅ All threads must be resolved
10. Enable: ✅ Require approval (1 approver minimum)
```

**Via GitLab API**:
```bash
# Protect main branch
curl --request POST \
  --header "PRIVATE-TOKEN: <your-token>" \
  "https://gitlab.com/api/v4/projects/:id/protected_branches" \
  --data "name=main&push_access_level=0&merge_access_level=30&unprotect_access_level=40"

# Require CI to pass
curl --request PUT \
  --header "PRIVATE-TOKEN: <your-token>" \
  "https://gitlab.com/api/v4/projects/:id/merge_requests/:mr_id/merge" \
  --data "should_remove_source_branch=true&merge_when_pipeline_succeeds=true"
```

---

#### Fix C: Add CODEOWNERS File

**File**: `.github/CODEOWNERS` (GitHub) or `CODEOWNERS` (GitLab)

```bash
# Claude Enhancer critical files require review from maintainers

# Workflow and CI configuration
/.github/workflows/              @team/maintainers
/.workflow/                      @team/maintainers
/.git/hooks/                     @team/maintainers

# Gates configuration
/.workflow/gates.yml             @team/maintainers
/.gates/                         @team/maintainers

# Security and contracts
/docs/AI_CONTRACT.md             @team/maintainers
/docs/CAPABILITY_MATRIX.md       @team/maintainers

# All other files
*                                @team/developers
```

Enable in branch protection:
```
✅ Require review from Code Owners
```

---

#### Fix D: Automate Protection Setup

**File**: `scripts/setup_branch_protection.sh`

```bash
#!/bin/bash
# Automated branch protection setup

set -euo pipefail

REPO="$1"  # Format: owner/repo
MAIN_BRANCH="${2:-main}"

echo "Setting up branch protection for ${REPO}/${MAIN_BRANCH}..."

# Required status checks
REQUIRED_CHECKS='["branch-protection","workflow-validation","path-whitelist","security-scan","must-produce","code-quality","test-execution"]'

# Apply protection
gh api "repos/${REPO}/branches/${MAIN_BRANCH}/protection" \
  --method PUT \
  --field "required_status_checks[strict]=true" \
  --field "required_status_checks[contexts]=${REQUIRED_CHECKS}" \
  --field "enforce_admins=true" \
  --field "required_pull_request_reviews[required_approving_review_count]=1" \
  --field "required_pull_request_reviews[dismiss_stale_reviews]=true" \
  --field "required_pull_request_reviews[require_code_owner_reviews]=true" \
  --field "restrictions=null"

echo "✅ Branch protection configured successfully!"
echo ""
echo "Verification:"
gh api "repos/${REPO}/branches/${MAIN_BRANCH}/protection" | jq '{
  required_status_checks: .required_status_checks.contexts,
  enforce_admins: .enforce_admins.enabled,
  required_approving_reviews: .required_pull_request_reviews.required_approving_review_count
}'
```

Usage:
```bash
bash scripts/setup_branch_protection.sh your-org/your-repo main
```

---

### ✅ Verification / 验证

```bash
# Test 1: Create PR with failing CI
git checkout -b test/failing-ci
echo "bad code" > test.txt && git add test.txt
git commit -m "test: will fail CI"
git push -u origin test/failing-ci
gh pr create --title "Test: Should not be mergeable"

# Expected: Merge button disabled with message "Required status checks must pass"

# Test 2: Verify protection via API
gh api repos/:owner/:repo/branches/main/protection | jq '.required_status_checks.contexts[]'

# Expected output (all required checks listed):
# "branch-protection"
# "workflow-validation"
# ...
```

---

### 🛡️ Prevention / 预防

```bash
# 1. Include in project setup checklist
cat > docs/PROJECT_SETUP.md <<EOF
## GitHub Repository Setup

### Required Steps:
1. Enable branch protection for main
2. Require status checks:
   - branch-protection
   - workflow-validation
   - path-whitelist
   - security-scan
   - must-produce
   - code-quality
   - test-execution
3. Require 1 approval
4. Enable CODEOWNERS enforcement
5. Prevent force pushes

### Verification:
\`\`\`bash
bash scripts/setup_branch_protection.sh <org>/<repo> main
\`\`\`
EOF

# 2. Add to CI to detect missing protection
# .github/workflows/verify-protection.yml
# (Runs daily to ensure protection is still enabled)

# 3. Team Training
# - Why branch protection matters
# - How to properly merge PRs
# - Never bypass required checks
```

---

## 🟢 FM-5: Branch Naming Not Compliant / 分支命名不规范

### 📝 Description / 描述

Feature branches don't follow the naming convention (e.g., `feature/`, `bugfix/`, `hotfix/`), making tracking and automation difficult.

功能分支不遵循命名约定（如`feature/`、`bugfix/`、`hotfix/`），导致跟踪和自动化困难。

### 🔍 Symptoms / 症状

**Indicator 1**: Branches with non-standard names
```bash
git branch -a | grep -v "feature/" | grep -v "bugfix/" | grep -v "hotfix/" | grep -v "main"

# Output (problematic branches):
  test
  john-test-branch
  fix
  temp
  wip-stuff
```

**Indicator 2**: CI warnings about branch names
```bash
# In CI logs:
⚠️ Warning: Branch 'test' does not follow naming convention
Expected: feature/, bugfix/, hotfix/, release/, docs/
```

---

### 🧪 Diagnostic Steps / 诊断步骤

#### Step 1: List Non-Compliant Branches

```bash
# Show all branches
git branch -a

# Filter for non-compliant (not matching allowed prefixes)
git branch | grep -vE '^[* ] (main|master|develop|feature/|bugfix/|hotfix/|release/|docs/)' || echo "All branches compliant"
```

---

#### Step 2: Check Branch Naming Rules

```bash
# Check if naming rules are documented
cat CONTRIBUTING.md | grep -A10 "Branch Naming"

# Check if rules are enforced in CI
grep -A5 "branch.*name" .github/workflows/*.yml
```

---

### 🔧 Fix Actions / 修复动作

#### Fix A: Rename Non-Compliant Branches

```bash
# Rename local branch
git branch -m old-branch-name feature/descriptive-name

# If already pushed, update remote
git push origin :old-branch-name  # Delete old remote branch
git push -u origin feature/descriptive-name  # Push renamed branch
```

---

#### Fix B: Document Branch Naming Convention

**File**: `CONTRIBUTING.md`

```markdown
## Branch Naming Convention

All branches must follow this naming scheme:

### Prefixes

- `feature/` - New features
  - Example: `feature/user-authentication`
  - Example: `feature/P3-payment-integration`

- `bugfix/` - Bug fixes
  - Example: `bugfix/login-timeout`
  - Example: `bugfix/P4-memory-leak`

- `hotfix/` - Urgent production fixes
  - Example: `hotfix/security-patch`

- `release/` - Release preparation
  - Example: `release/v1.2.0`

- `docs/` - Documentation updates
  - Example: `docs/api-reference`

- `refactor/` - Code refactoring
  - Example: `refactor/simplify-auth`

### Format Rules

1. **Prefix required**: Must start with allowed prefix
2. **Kebab-case**: Use hyphens, not underscores or spaces
3. **Descriptive**: Name should indicate purpose
4. **Phase optional**: Can include phase (e.g., `feature/P3-login`)

### Valid Examples

```
feature/add-dark-mode
bugfix/fix-api-timeout
hotfix/security-cve-2024-1234
release/v2.0.0
docs/update-readme
refactor/P5-simplify-hooks
```

### Invalid Examples

```
test               ❌ No prefix
my_feature         ❌ Underscore instead of hyphen
feature/Add Login  ❌ Spaces and capital letters
john-branch        ❌ Personal name
wip                ❌ Too vague
```

### Enforcement

- **Pre-commit hook**: Warns on invalid branch names
- **CI validation**: Blocks PR merge if branch name invalid
- **Automatic PR labeling**: Based on branch prefix
```

---

#### Fix C: Add Branch Naming Validation to CI

**File**: `.github/workflows/branch-naming.yml`

```yaml
name: Branch Naming Validation

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  validate-branch-name:
    runs-on: ubuntu-latest
    steps:
      - name: Check branch name
        run: |
          BRANCH_NAME="${{ github.head_ref }}"

          # Allowed prefixes
          ALLOWED_PREFIXES="feature/|bugfix/|hotfix/|release/|docs/|refactor/"

          if echo "$BRANCH_NAME" | grep -qE "^($ALLOWED_PREFIXES)"; then
            echo "✅ Branch name is compliant: $BRANCH_NAME"
            exit 0
          else
            echo "❌ Invalid branch name: $BRANCH_NAME"
            echo ""
            echo "Branch names must start with one of:"
            echo "  - feature/"
            echo "  - bugfix/"
            echo "  - hotfix/"
            echo "  - release/"
            echo "  - docs/"
            echo "  - refactor/"
            echo ""
            echo "Example: feature/add-user-login"
            exit 1
          fi
```

---

#### Fix D: Add Pre-Commit Warning

Add to `.git/hooks/pre-commit`:

```bash
# Branch name validation (warning only, not blocking)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
ALLOWED_PREFIXES="^(feature/|bugfix/|hotfix/|release/|docs/|refactor/)"

if ! echo "$BRANCH" | grep -qE "$ALLOWED_PREFIXES"; then
    echo ""
    echo "⚠️  Warning: Branch name '$BRANCH' does not follow convention"
    echo "   Recommended prefixes: feature/, bugfix/, hotfix/, release/, docs/, refactor/"
    echo "   Example: feature/add-login"
    echo ""
    echo "   To rename:"
    echo "   git branch -m $BRANCH feature/$(echo $BRANCH | tr '_' '-')"
    echo ""
    # Don't exit 1 - just warn
fi
```

---

### ✅ Verification / 验证

```bash
# Test compliant branches
git checkout -b feature/test-naming
git checkout -b bugfix/test-fix
git checkout -b hotfix/urgent-patch

# All should pass validation

# Test non-compliant branch
git checkout -b test-branch

# Expected: Warning in pre-commit, CI fails if pushed
```

---

### 🛡️ Prevention / 预防

```bash
# 1. Provide branch creation helper
cat > scripts/new-branch.sh <<'EOF'
#!/bin/bash
# Interactive branch creation with validation

echo "Create a new branch"
echo ""
echo "Select type:"
echo "  1) feature   - New feature"
echo "  2) bugfix    - Bug fix"
echo "  3) hotfix    - Urgent fix"
echo "  4) release   - Release prep"
echo "  5) docs      - Documentation"
echo "  6) refactor  - Code refactor"
read -p "Choice (1-6): " choice

case $choice in
  1) prefix="feature/" ;;
  2) prefix="bugfix/" ;;
  3) prefix="hotfix/" ;;
  4) prefix="release/" ;;
  5) prefix="docs/" ;;
  6) prefix="refactor/" ;;
  *) echo "Invalid choice"; exit 1 ;;
esac

read -p "Branch name (kebab-case): " name

# Validate kebab-case
if ! echo "$name" | grep -qE '^[a-z0-9-]+$'; then
    echo "❌ Invalid name. Use lowercase, numbers, and hyphens only."
    exit 1
fi

BRANCH="${prefix}${name}"
git checkout -b "$BRANCH"
echo "✅ Created and switched to: $BRANCH"
EOF

chmod +x scripts/new-branch.sh

# Usage:
# bash scripts/new-branch.sh

# 2. Add to onboarding
# "Always use scripts/new-branch.sh to create branches"

# 3. Team reminder in PR template
# .github/PULL_REQUEST_TEMPLATE.md includes:
# "Branch name follows convention: feature/, bugfix/, hotfix/, etc."
```

---

## 📊 Failure Mode Summary / 故障模式总结

| FM | Issue | Detection | Fix Time | Severity |
|----|-------|-----------|----------|----------|
| FM-1 | Hooks not working | Local test fails | 5 min | 🔴 Critical |
| FM-2 | `--no-verify` bypass | CI catches | 10 min | 🟡 High |
| FM-3 | AI uninitialized | AI refuses | 5 min | 🔴 Critical |
| FM-4 | CI not required | PR mergeable | 15 min | 🟡 High |
| FM-5 | Branch naming | Warning only | 2 min | 🟢 Medium |

---

## 🚀 Quick Reference Commands / 快速参考命令

```bash
# Diagnose all failure modes
bash scripts/diagnose_all.sh

# Fix FM-1: Hooks not working
bash tools/bootstrap.sh

# Fix FM-2: Prevent --no-verify
bash scripts/setup_branch_protection.sh <org>/<repo> main

# Fix FM-3: Initialize for AI
bash tools/ai_preflight_check.sh

# Fix FM-4: Enable branch protection
# (See Fix A in FM-4 section)

# Fix FM-5: Rename branch
git branch -m old-name feature/new-name
```

---

## 📞 Support / 支持

If you encounter failure modes not covered here:
1. Check `docs/CAPABILITY_MATRIX.md` for capability-specific issues
2. Review `docs/AI_CONTRACT.md` for AI behavior issues
3. Run diagnostic: `bash scripts/gap_scan.sh`
4. Consult Claude Enhancer documentation

---

**Guide Version**: 1.0.0
**Last Updated**: 2025-10-09
**Maintainer**: Claude Enhancer Team
**Status**: ✅ Production Ready
