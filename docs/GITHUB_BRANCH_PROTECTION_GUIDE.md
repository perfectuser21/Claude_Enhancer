# GitHub Branch Protection Configuration Guide

**Claude Enhancer v5.4.0**

This guide provides step-by-step instructions for configuring GitHub Branch Protection rules for the Claude Enhancer repository to ensure production-grade workflow enforcement.

---

## 🎯 Overview

Branch Protection rules enforce quality gates and prevent accidental pushes to critical branches. For Claude Enhancer, we recommend protecting:

- `main` (or `master`) - Production branch
- `develop` - Development integration branch
- `release/*` - Release branches

---

## 📋 Quick Setup

### Option 1: Using GitHub Web Interface (Recommended)

1. **Navigate to Settings**
   ```
   https://github.com/perfectuser21/Claude_Enhancer/settings/branches
   ```

2. **Click "Add branch protection rule"**

3. **Configure according to templates below**

### Option 2: Using GitHub CLI (Advanced)

```bash
# Install gh CLI if not already installed
# https://cli.github.com/

# Authenticate
gh auth login

# Apply branch protection (see commands below)
```

---

## 🛡️ Protection Rules by Branch

### 1. Main Branch Protection (Production)

**Branch Name Pattern**: `main` or `master`

**Settings**:

#### Status Checks
```yaml
✅ Require status checks to pass before merging
  ✅ Require branches to be up to date before merging

  Required status checks:
    - security-tests (test/security/)
    - shellcheck-lint
    - version-consistency-check
    - bdd-tests (if available)
```

#### Pull Request Requirements
```yaml
✅ Require pull request before merging
  ✅ Require approvals: 1
  ✅ Dismiss stale pull request approvals when new commits are pushed
  ✅ Require review from Code Owners (if CODEOWNERS file exists)
  ☐ Require approval of the most recent reviewable push
```

#### Commit Restrictions
```yaml
✅ Require signed commits (GPG/SSH signature)
✅ Require linear history (no merge commits)
☐ Allow force pushes (DANGEROUS - keep disabled)
☐ Allow deletions (DANGEROUS - keep disabled)
```

#### Additional Settings
```yaml
✅ Require conversation resolution before merging
✅ Lock branch (make read-only)
☐ Do not allow bypassing the above settings (enforce for admins)
```

#### GitHub CLI Command
```bash
gh api -X PUT /repos/perfectuser21/Claude_Enhancer/branches/main/protection \
  -F required_status_checks[strict]=true \
  -F required_status_checks[contexts][]=security-tests \
  -F required_status_checks[contexts][]=shellcheck-lint \
  -F required_pull_request_reviews[required_approving_review_count]=1 \
  -F required_pull_request_reviews[dismiss_stale_reviews]=true \
  -F required_signatures=true \
  -F required_linear_history=true \
  -F allow_force_pushes=false \
  -F allow_deletions=false
```

---

### 2. Develop Branch Protection (Integration)

**Branch Name Pattern**: `develop`

**Settings**:

#### Status Checks
```yaml
✅ Require status checks to pass before merging
  ✅ Require branches to be up to date before merging

  Required status checks:
    - security-tests
    - shellcheck-lint
    - unit-tests
```

#### Pull Request Requirements
```yaml
✅ Require pull request before merging
  ✅ Require approvals: 1
  ☐ Dismiss stale pull request approvals
  ☐ Require review from Code Owners
```

#### Commit Restrictions
```yaml
✅ Require signed commits
☐ Require linear history (allow merge commits)
☐ Allow force pushes
☐ Allow deletions
```

#### GitHub CLI Command
```bash
gh api -X PUT /repos/perfectuser21/Claude_Enhancer/branches/develop/protection \
  -F required_status_checks[strict]=true \
  -F required_status_checks[contexts][]=security-tests \
  -F required_status_checks[contexts][]=shellcheck-lint \
  -F required_pull_request_reviews[required_approving_review_count]=1 \
  -F required_signatures=true \
  -F allow_force_pushes=false
```

---

### 3. Release Branch Protection

**Branch Name Pattern**: `release/*`

**Settings**:

#### Status Checks
```yaml
✅ Require status checks to pass before merging
  ✅ Require branches to be up to date before merging

  Required status checks:
    - security-tests
    - shellcheck-lint
    - version-consistency-check
    - release-notes-validation
```

#### Pull Request Requirements
```yaml
✅ Require pull request before merging
  ✅ Require approvals: 2 (higher threshold for releases)
  ✅ Dismiss stale pull request approvals when new commits are pushed
```

#### Commit Restrictions
```yaml
✅ Require signed commits
✅ Require linear history
☐ Allow force pushes
☐ Allow deletions
```

#### GitHub CLI Command
```bash
gh api -X PUT /repos/perfectuser21/Claude_Enhancer/branches/release/*/protection \
  -F required_status_checks[strict]=true \
  -F required_status_checks[contexts][]=security-tests \
  -F required_pull_request_reviews[required_approving_review_count]=2 \
  -F required_signatures=true \
  -F required_linear_history=true
```

---

## 🔧 Setting Up Status Checks

For branch protection to work with status checks, you need CI/CD workflows that report status to GitHub.

### GitHub Actions Workflow Example

Create `.github/workflows/ci.yml`:

```yaml
name: CI - Claude Enhancer

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  security-tests:
    name: Security Test Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install BATS
        run: npm install -g bats

      - name: Run Security Tests
        run: ./test/security/run_security_tests.sh

      - name: Upload Test Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-test-report
          path: test/security/security_test_report.txt

  shellcheck-lint:
    name: ShellCheck Static Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install ShellCheck
        run: sudo apt-get install -y shellcheck

      - name: Run ShellCheck
        run: |
          shellcheck .workflow/automation/security/*.sh
          shellcheck .workflow/automation/utils/*.sh

  version-consistency-check:
    name: Version Consistency Validation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Verify Version Consistency
        run: |
          if [ -f ./scripts/verify_version_consistency.sh ]; then
            ./scripts/verify_version_consistency.sh
          else
            echo "Version consistency script not found, skipping"
          fi
```

---

## 🚀 Deployment Strategy

### Step 1: Create Feature Branch Protection First

Start with less restrictive rules for feature branches to test the setup:

```bash
gh api -X PUT /repos/perfectuser21/Claude_Enhancer/branches/feature/*/protection \
  -F required_status_checks[strict]=false \
  -F required_status_checks[contexts][]=security-tests
```

### Step 2: Gradually Tighten Main Branch

1. **Week 1**: Enable PR requirement only
2. **Week 2**: Add status check requirement
3. **Week 3**: Enable signed commits
4. **Week 4**: Full protection (linear history, lock branch)

### Step 3: Monitor and Adjust

- Check GitHub Insights → Branches to see protection enforcement
- Review blocked pushes and adjust rules if needed
- Collect team feedback

---

## 🔍 Verification

### Check Protection Status

```bash
# Using gh CLI
gh api /repos/perfectuser21/Claude_Enhancer/branches/main/protection

# Or check via web
https://github.com/perfectuser21/Claude_Enhancer/settings/branch_protection_rules
```

### Test Protection

```bash
# Try to push directly to main (should fail)
git checkout main
echo "test" >> README.md
git commit -am "test: direct push"
git push origin main
# Expected: remote: error: GH006: Protected branch update failed
```

---

## 🛠️ Troubleshooting

### Issue: Can't Enable Branch Protection

**Cause**: Repository may not be owned or lack admin rights

**Solution**:
- Verify you have admin access to the repository
- For organization repos, check organization settings
- Repository must not be archived

### Issue: Status Checks Not Appearing

**Cause**: CI workflow not configured or not reporting status

**Solution**:
1. Ensure GitHub Actions workflow exists (`.github/workflows/*.yml`)
2. Workflow must use `on: pull_request` or `on: push`
3. Check Actions tab for workflow run status
4. Status check names must match exactly

### Issue: Signed Commits Failing

**Cause**: GPG/SSH key not configured

**Solution**:
```bash
# Configure GPG signing
git config --global commit.gpgsign true
git config --global user.signingkey YOUR_GPG_KEY_ID

# Or use SSH signing (GitHub-recommended)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
```

### Issue: Force Push Needed for Rebase

**Cause**: Linear history requirement conflicts with rebase workflow

**Solution**:
- Use `--force-with-lease` instead of `--force`
- Or disable "Require linear history" (not recommended)
- Consider using merge commits instead of rebase

---

## 📚 Additional Resources

### GitHub Documentation

- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Managing branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- [Required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)

### Claude Enhancer Documentation

- `docs/WORKFLOW.md` - 8-Phase workflow explanation
- `docs/P5_REVIEW.md` - Code quality standards
- `test/security/run_security_tests.sh` - Security test runner

---

## 🎯 Recommended Configuration Summary

For **Claude Enhancer v5.4.0**, we recommend:

| Setting | Main | Develop | Feature/* |
|---------|------|---------|-----------|
| Require PR | ✅ | ✅ | ☐ |
| Require Approvals | 1 | 1 | 0 |
| Require Status Checks | ✅ | ✅ | ✅ |
| Signed Commits | ✅ | ✅ | ☐ |
| Linear History | ✅ | ☐ | ☐ |
| Lock Branch | ✅ | ☐ | ☐ |
| Allow Force Push | ❌ | ❌ | ✅ |

---

## 🔐 Security Considerations

### Required Status Checks

Ensure these checks are enforced:

1. **security-tests**: Validates P3 security fixes (71 tests)
2. **shellcheck-lint**: Static analysis (0 errors required)
3. **version-consistency-check**: Ensures VERSION file consistency

### Bypass Settings

⚠️ **WARNING**: Do NOT enable "Allow specified actors to bypass"

Even admins should go through the standard process to maintain audit trail.

### Emergency Procedures

If you need to bypass protection for emergency hotfix:

1. Create a hotfix branch from main
2. Apply fix and test thoroughly
3. Create PR with expedited review
4. Use admin override ONLY if absolutely necessary (document reason)

---

## 📞 Support

For issues with branch protection setup:

1. Check GitHub Status: https://www.githubstatus.com/
2. Review GitHub Docs: https://docs.github.com/
3. Claude Enhancer Issues: https://github.com/perfectuser21/Claude_Enhancer/issues

---

**Document Version**: 1.0
**Last Updated**: 2025-10-10
**Compatible with**: Claude Enhancer v5.4.0

---

*This guide is part of the Claude Enhancer v5.4.0 (P6 Release) documentation suite.*

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
