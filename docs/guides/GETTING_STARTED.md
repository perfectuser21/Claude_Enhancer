# Getting Started with Claude Enhancer v5.4.0

**Last Updated**: 2025-10-10
**Version**: 5.4.0
**Time to Complete**: 10 minutes

---

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Initial Configuration](#initial-configuration)
- [Your First Automation](#your-first-automation)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Introduction

Welcome to Claude Enhancer! This guide will help you install and configure the system in under 10 minutes. By the end, you'll have:

- ✅ Claude Enhancer installed in your project
- ✅ Git hooks configured for quality enforcement
- ✅ Automation system ready to use
- ✅ Your first automated workflow running

### What You're Installing

```
Claude Enhancer v5.4.0
├─ 8-Phase Workflow (P0-P7)
├─ Git Automation (commit/push/PR/merge/release)
├─ FIFO Merge Queue (multi-terminal support)
├─ Security Audit Logging
└─ Quality Gates (9 CI checks)
```

---

## Prerequisites

### Required Software

| Tool | Minimum Version | Check Command | Installation |
|------|----------------|---------------|--------------|
| **bash** | 4.0+ | `bash --version` | Pre-installed on Linux/macOS |
| **git** | 2.0+ | `git --version` | [git-scm.com](https://git-scm.com) |
| **GitHub CLI** | 2.0+ | `gh --version` | [cli.github.com](https://cli.github.com) |

### Optional Software

| Tool | Purpose | Check Command |
|------|---------|---------------|
| **Node.js** | BDD tests | `node --version` |
| **Python** | Advanced features | `python3 --version` |
| **curl** | API calls | `curl --version` |

### System Requirements

- **OS**: Linux, macOS, or WSL2 (Windows)
- **Disk Space**: 100MB for installation
- **RAM**: 256MB minimum
- **Network**: Internet access for GitHub API

### Permissions

You'll need:
- Write access to your Git repository
- Ability to create files in `/tmp/ce_locks/`
- (Optional) sudo for audit logs in `/var/log/`

---

## Installation

### Step 1: Verify Prerequisites

```bash
# Check all required tools
bash --version     # Should be 4.0+
git --version      # Should be 2.0+
gh --version       # Should be 2.0+

# Check GitHub CLI authentication
gh auth status     # Should show "Logged in"
```

**Problem?** See [Troubleshooting](#troubleshooting)

### Step 2: Copy Claude Enhancer Files

```bash
# Navigate to your project
cd /path/to/your/project

# Copy the three core directories
cp -r /path/to/claude-enhancer/.claude ./
cp -r /path/to/claude-enhancer/.workflow ./
cp -r /path/to/claude-enhancer/.github ./

# Verify structure
ls -la .claude .workflow .github/workflows
```

**Expected Output**:
```
.claude/
├── hooks/
│   ├── branch_helper.sh
│   ├── smart_agent_selector.sh
│   └── quality_gate.sh
├── install.sh
└── settings.json

.workflow/
├── automation/
│   ├── core/
│   ├── queue/
│   ├── security/
│   ├── rollback/
│   └── utils/
└── cli/

.github/
└── workflows/
    └── ci-workflow-v5.4.yml
```

### Step 3: Install Git Hooks

```bash
# Run the installation script
bash .claude/install.sh

# Verify hooks are installed
ls -l .git/hooks/
```

**Expected Output**:
```
-rwxr-xr-x  pre-commit
-rwxr-xr-x  commit-msg
-rwxr-xr-x  pre-push
```

### Step 4: Verify Installation

```bash
# Run validation script
bash test/validate_enhancement.sh

# Or check manually
which bash gh git
```

**Success Indicators**:
- ✅ All commands found
- ✅ Git hooks executable
- ✅ No permission errors

---

## Initial Configuration

### Step 1: Configure GitHub Authentication

```bash
# Authenticate with GitHub
gh auth login

# Choose:
# - GitHub.com
# - HTTPS
# - Authenticate with browser
```

### Step 2: Set Environment Variables

Create a configuration file:

```bash
# Create .env file in project root
cat > .env <<'EOF'
# Claude Enhancer Configuration

# Execution Mode (0=manual, 1=automated)
export CE_EXECUTION_MODE=1

# Automation Tiers (0=disabled, 1=enabled)
export CE_AUTO_PUSH=0       # Start conservative
export CE_AUTO_PR=0         # Start conservative
export CE_AUTO_MERGE=0      # Start conservative (dangerous!)
export CE_AUTO_RELEASE=0    # Always keep disabled

# Security (REQUIRED for audit logging)
export CE_AUDIT_SECRET="$(openssl rand -hex 32)"

# Optional: Session tracking
export CE_SESSION_ID="$(uuidgen || date +%s)"

# Optional: Debug mode
export CE_DEBUG=0

# Optional: Dry run (show what would happen)
export CE_DRY_RUN=0
EOF

# Source the configuration
source .env

# Add to your shell profile (optional)
echo "source $(pwd)/.env" >> ~/.bashrc
```

### Step 3: Test Configuration

```bash
# Check environment variables
echo "Execution Mode: $CE_EXECUTION_MODE"
echo "Auto Push: $CE_AUTO_PUSH"
echo "Audit Secret: ${CE_AUDIT_SECRET:0:8}..." # Show first 8 chars

# Test audit logging
bash .workflow/automation/security/audit_log.sh log \
  "GIT_OPERATION" "test" "config" "success" "Installation test"
```

**Expected Output**:
```
Execution Mode: 1
Auto Push: 0
Audit Secret: a1b2c3d4...
[SUCCESS] Audit logged: 1696934400-a1b2c3d4
```

---

## Your First Automation

Let's automate a simple commit and push workflow.

### Step 1: Create a Test Branch

```bash
# Create and switch to a new branch
git checkout -b feature/test-automation

# Verify you're on the new branch
git branch --show-current
# Output: feature/test-automation
```

### Step 2: Make a Test Change

```bash
# Create a test file
echo "# Test Automation" > TEST.md
echo "This is a test of Claude Enhancer automation." >> TEST.md

# Check status
git status
# Output: Untracked files: TEST.md
```

### Step 3: Automated Commit

```bash
# Use auto_commit.sh
bash .workflow/automation/core/auto_commit.sh \
  "feat(P3): Add test automation file" \
  TEST.md

# Verify commit
git log -1 --oneline
# Output: abc123 feat(P3): Add test automation file
```

**What Happened?**
1. Script validated commit message (≥10 chars, Phase marker)
2. Staged TEST.md file
3. Created commit with message
4. Logged operation to audit log

### Step 4: Manual Push (For Now)

```bash
# Since CE_AUTO_PUSH=0, we push manually
git push -u origin feature/test-automation

# In future, enable auto push:
# export CE_AUTO_PUSH=1
# bash .workflow/automation/core/auto_push.sh
```

### Step 5: Create Pull Request

```bash
# Use auto_pr.sh
bash .workflow/automation/core/auto_pr.sh \
  "Add test automation" \
  "Testing Claude Enhancer automation system"

# Output:
# [SUCCESS] PR created: #42
# [INFO] Added to merge queue (position: 1)
```

### Step 6: Check Merge Queue

```bash
# View queue status
bash .workflow/automation/queue/merge_queue_manager.sh status

# Expected output:
# ═══════════════════════════════════════
#          Merge Queue Status
# ═══════════════════════════════════════
# Pos  PR         Branch                      Status
# ───────────────────────────────────────
# 1    #42        feature/test-automation     QUEUED
# ═══════════════════════════════════════
```

**Congratulations!** You've completed your first automated workflow! 🎉

---

## Troubleshooting

### Problem: "bash: command not found"

**Solution**:
```bash
# Check if bash is installed
which bash

# If not found, install:
# macOS:
brew install bash

# Linux (Ubuntu/Debian):
sudo apt-get install bash

# Linux (RHEL/CentOS):
sudo yum install bash
```

### Problem: "gh: command not found"

**Solution**:
```bash
# macOS:
brew install gh

# Linux:
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
  sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
  https://cli.github.com/packages stable main" | \
  sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# After installation:
gh auth login
```

### Problem: "Permission denied" on Git hooks

**Solution**:
```bash
# Make hooks executable
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-push

# Re-run installation
bash .claude/install.sh
```

### Problem: "CE_AUDIT_SECRET not set"

**Solution**:
```bash
# Generate and set the secret
export CE_AUDIT_SECRET="$(openssl rand -hex 32)"

# Make it permanent
echo "export CE_AUDIT_SECRET=\"$CE_AUDIT_SECRET\"" >> ~/.bashrc
source ~/.bashrc

# Or add to project .env file
echo "export CE_AUDIT_SECRET=\"$CE_AUDIT_SECRET\"" >> .env
```

### Problem: Merge queue not processing

**Solution**:
```bash
# Check if queue file exists
ls -la /tmp/ce_locks/merge_queue.fifo

# Manually process queue
bash .workflow/automation/queue/merge_queue_manager.sh process

# Clear stuck queue
bash .workflow/automation/queue/merge_queue_manager.sh clear
```

### Problem: CI checks failing

**Solution**:
```bash
# Check CI status
gh pr checks

# View detailed logs
gh run view --log

# Common fixes:
# 1. Ensure all tests pass locally
npm test

# 2. Ensure code quality
shellcheck .workflow/automation/**/*.sh

# 3. Check commit message format
# Must be: type(scope): description
# Example: feat(P3): Add new feature
```

### Getting More Help

- **Documentation**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for 20+ scenarios
- **GitHub Issues**: [Report a bug](https://github.com/claude-enhancer/claude-enhancer/issues)
- **Discussions**: [Ask questions](https://github.com/claude-enhancer/claude-enhancer/discussions)

---

## Next Steps

### Recommended Learning Path

1. **Read the Automation Guide** (15 minutes)
   - [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)
   - Learn about all automation scripts
   - Understand tiered automation levels

2. **Explore Merge Queue** (10 minutes)
   - [MERGE_QUEUE_GUIDE.md](MERGE_QUEUE_GUIDE.md)
   - Multi-terminal workflows
   - Conflict handling

3. **Review Security** (15 minutes)
   - [SECURITY_GUIDE.md](SECURITY_GUIDE.md)
   - Audit logging
   - Permission management

4. **Try Advanced Features** (30 minutes)
   - [TESTING_GUIDE.md](TESTING_GUIDE.md)
   - Run the full test suite
   - Write your own tests

### Progressive Automation Enablement

Start conservatively and enable features as you gain confidence:

**Week 1: Manual Mode**
```bash
export CE_EXECUTION_MODE=1
export CE_AUTO_PUSH=0
export CE_AUTO_PR=0
export CE_AUTO_MERGE=0
```

**Week 2: Auto Push**
```bash
export CE_AUTO_PUSH=1  # Enable after 10+ successful commits
```

**Week 3: Auto PR**
```bash
export CE_AUTO_PR=1    # Enable after 5+ successful PRs
```

**Week 4+: Solo Developer Mode**
```bash
export CE_AUTO_MERGE=1 # Only if solo developer and confident
```

**Always Keep Disabled**
```bash
export CE_AUTO_RELEASE=0  # Tags are critical, always manual
```

### Explore the 8-Phase Workflow

```bash
# Read workflow documentation
cat .claude/WORKFLOW.md

# Try each phase:
echo "P0" > .phase/current  # Discovery
echo "P1" > .phase/current  # Plan
echo "P2" > .phase/current  # Skeleton
echo "P3" > .phase/current  # Implementation
echo "P4" > .phase/current  # Testing
echo "P5" > .phase/current  # Review
echo "P6" > .phase/current  # Release
echo "P7" > .phase/current  # Monitor
```

### Join the Community

- **Star the repo**: [github.com/claude-enhancer](https://github.com/claude-enhancer/claude-enhancer)
- **Follow updates**: Watch for releases
- **Share feedback**: Open discussions
- **Contribute**: See [CONTRIBUTING.md](../../CONTRIBUTING.md)

---

## Quick Reference Card

```bash
# Environment Setup
source .env                    # Load configuration
export CE_EXECUTION_MODE=1     # Enable automation

# Core Automation Scripts
auto_commit.sh "msg" [files]   # Commit changes
auto_push.sh                   # Push to remote
auto_pr.sh "title" "desc"      # Create PR
merge_queue_manager.sh status  # Check queue

# Queue Management
merge_queue_manager.sh enqueue <pr>  # Add to queue
merge_queue_manager.sh process       # Process queue
merge_queue_manager.sh clear         # Clear queue

# Audit Logging
audit_log.sh log <type> <action> <resource> <result>
audit_log.sh query [filter] [limit]
audit_log.sh verify

# Troubleshooting
gh auth status                 # Check GitHub auth
git log -1                     # Check last commit
bash -x script.sh             # Debug mode
```

---

**Installation Complete!** 🎉

You're now ready to use Claude Enhancer v5.4.0. Start with simple workflows and gradually enable more automation as you gain confidence.

**Need Help?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or [open an issue](https://github.com/claude-enhancer/claude-enhancer/issues).

---

*Generated by Claude Enhancer v5.4.0 Documentation System*
*For updates, see: [CHANGELOG.md](../../CHANGELOG.md)*
