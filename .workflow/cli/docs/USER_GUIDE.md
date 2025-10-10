# CE CLI User Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-09
**Target Audience**: End Users, Developers

---

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Commands Reference](#commands-reference)
5. [Advanced Usage](#advanced-usage)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)
9. [Best Practices](#best-practices)

---

## 1. Introduction

### What is CE CLI?

CE CLI (`ce`) is a command-line interface for **Claude Enhancer**, designed to streamline AI-driven development workflows. It provides a unified interface to manage:

- **Feature Development**: Start, track, and complete features across 8 phases (P0-P7)
- **Multi-Terminal Support**: Work on multiple features simultaneously without conflicts
- **Quality Gates**: Automated validation and quality checks
- **PR Automation**: Simplified pull request creation and merging

### Why CE CLI?

**Traditional Workflow Problems**:
- ❌ Manual branch creation and naming (5-10 minutes per feature)
- ❌ Remembering complex Git commands and workflow steps
- ❌ Manual quality gate validation (10-15 minutes)
- ❌ Terminal state conflicts when working on multiple features
- ❌ Forgetting which phase you're in

**CE CLI Solutions**:
- ✅ One command to start a feature: `ce start <feature>` (30 seconds)
- ✅ Automatic branch naming with phase awareness
- ✅ Automated quality gate validation: `ce validate` (5-10 seconds)
- ✅ Multi-terminal session management (t1, t2, t3)
- ✅ Clear status visibility: `ce status` (2 seconds)

### Key Features

| Feature | Description | Time Saved |
|---------|-------------|------------|
| **Smart Start** | Creates feature branch with proper naming convention | 5-10 min → 30 sec |
| **Status Dashboard** | Shows all terminals, branches, and phase progress | 5 min → 2 sec |
| **Auto Validation** | Runs quality gates with caching and parallelization | 10-15 min → 5-10 sec |
| **Phase Navigation** | Safely move between P0-P7 phases | 15-20 min → 5-8 sec |
| **PR Automation** | Creates and manages pull requests | 15-20 min → 1 min |
| **Clean Merges** | Merges with health checks and rollback capability | 20-30 min → 1-2 min |

**Total Time Saved**: ~67% per feature (17.7 hours → 5.8 hours)

---

## 2. Installation

### Prerequisites

Ensure you have the following tools installed:

```bash
# Required
git --version          # Git 2.30+
gh --version           # GitHub CLI 2.0+
bash --version         # Bash 4.0+

# Optional (for advanced features)
jq --version           # JSON processor
yq --version           # YAML processor
```

### Quick Install

```bash
# Navigate to your Claude Enhancer project
cd /path/to/your/project

# Run the installation script
bash .workflow/cli/install.sh

# Verify installation
ce --version
# Output: ce v1.0.0 (Claude Enhancer 5.4.0)
```

### Manual Install

If the quick install fails, follow these steps:

```bash
# 1. Create symbolic link
sudo ln -sf "$(pwd)/.workflow/cli/ce.sh" /usr/local/bin/ce

# 2. Make executable
chmod +x .workflow/cli/ce.sh

# 3. Verify
which ce
# Output: /usr/local/bin/ce

# 4. Test
ce --help
```

### Uninstall

```bash
# Remove symbolic link
sudo rm /usr/local/bin/ce

# Remove CLI directory (optional)
rm -rf .workflow/cli
```

---

## 3. Getting Started

### Your First Feature

Let's create a new feature from scratch using CE CLI.

#### Step 1: Start a Feature

```bash
# Start a new feature (creates branch, sets up state)
ce start user-authentication

# Output:
# 🚀 Claude Enhancer - Starting New Feature
#
# 📍 Creating branch: feature/user-authentication-20251009
# ⚙️  Initializing workflow...
# ✅ Current phase: P0 (Discovery)
#
# 📋 P0 Phase Requirements:
#   • Create feasibility analysis document
#   • Validate at least 2 key technical points
#   • Assess technical/business/time risks
#   • Reach clear conclusion (GO/NO-GO/NEEDS-DECISION)
#
# 💡 Suggested Next Steps:
#   1. Create docs/P0_user-authentication_DISCOVERY.md
#   2. Perform technical spike validation
#   3. Run 'ce validate' to check P0 completion
#   4. Run 'ce next' to enter P1 phase
```

#### Step 2: Check Status

```bash
ce status

# Output:
# ═══════════════════════════════════════════════════
#   📊 Claude Enhancer Status Report
# ═══════════════════════════════════════════════════
#
# 📍 Basic Information
#   Project: Claude Enhancer 5.0
#   Branch: feature/user-authentication-20251009
#   Phase: P0 (Discovery)
#   Started: 2025-10-09T10:30:00Z
#
# 📈 Workflow Progress
#   ✅ P0 Discovery - Complete
#   ▶️  P1 Plan - In Progress
#   ⏸️  P2 Skeleton - Pending
#   ⏸️  P3 Implementation - Pending
#   ⏸️  P4 Testing - Pending
#   ⏸️  P5 Review - Pending
#   ⏸️  P6 Release - Pending
#   ⏸️  P7 Monitor - Pending
#
# 🔒 Quality Gates Status
#   ✅ Gate 00 (P0) - Verified
#   Completed: 1/8
#
# 💡 Next Steps
#   1. Run 'ce next' to enter next phase
```

#### Step 3: Validate Phase

```bash
# Validate current phase requirements
ce validate

# Output:
# 🔍 Validating P0 (Discovery)...
#
# ✅ [1/4] Checking required paths...
# ✅ [2/4] Checking produces...
# ✅ [3/4] Security validation...
# ✅ [4/4] Quality checks...
#
# ✅ Phase P0 validation passed!
#
# 💡 Next: Run 'ce next' to proceed to P1
```

#### Step 4: Move to Next Phase

```bash
# Proceed to next phase
ce next

# Output:
# 🚀 Advancing to next phase...
#
# Current: P0 (Discovery)
# Next: P1 (Plan)
#
# ⚠️  P1 Phase Requirements:
#   • Create docs/PLAN.md
#   • At least 10 task items
#   • Affected files list
#   • Rollback plan
#
# ✅ Advanced to P1
```

### Multi-Terminal Workflow

Work on multiple features simultaneously using terminal IDs.

```bash
# Terminal 1 (default: t1)
ce start feature-auth
# Works in session t1

# Terminal 2
export CE_TERMINAL_ID=t2
ce start feature-payment
# Works in session t2 (isolated from t1)

# Terminal 3
export CE_TERMINAL_ID=t3
ce start feature-reports
# Works in session t3 (isolated from t1 and t2)

# View all sessions
ce status --all

# Output shows all 3 terminals working independently:
# Terminal t1: feature-auth (P3 Implementation)
# Terminal t2: feature-payment (P2 Skeleton)
# Terminal t3: feature-reports (P1 Plan)
```

---

## 4. Commands Reference

### `ce start`

**Purpose**: Create a new feature branch and initialize workflow.

**Syntax**:
```bash
ce start <feature-name> [options]
```

**Options**:
- `--from=<branch>` - Base branch (default: main)
- `--phase=<PX>` - Initial phase (default: P0)
- `--force` - Force creation even if branch exists

**Examples**:
```bash
# Basic usage
ce start user-login

# Start from specific branch
ce start hotfix-bug --from=release/1.0

# Start at specific phase
ce start quick-fix --phase=P2

# Force recreate existing branch
ce start user-login --force
```

**Exit Codes**:
- `0` - Success
- `1` - Invalid arguments
- `2` - Branch already exists
- `3` - Uncommitted changes detected

---

### `ce status`

**Purpose**: Display current workflow status across all terminals.

**Syntax**:
```bash
ce status [options]
```

**Options**:
- `--verbose`, `-v` - Show detailed information
- `--json` - Output in JSON format
- `--all` - Show all terminal sessions
- `--terminal=<id>` - Show specific terminal (t1, t2, t3)

**Examples**:
```bash
# Basic status
ce status

# Detailed status
ce status --verbose

# JSON output (for scripting)
ce status --json | jq '.current_phase'

# All terminals
ce status --all

# Specific terminal
ce status --terminal=t2
```

**Output Sections**:
1. **Basic Information**: Project, branch, phase, start time
2. **Workflow Progress**: P0-P7 completion status
3. **Quality Gates**: Which gates have passed
4. **Current Phase**: Requirements and next steps

---

### `ce validate`

**Purpose**: Run quality gate validation for current phase.

**Syntax**:
```bash
ce validate [options]
```

**Options**:
- `--mode=<mode>` - Validation mode: `full`, `quick`, `incremental`, `parallel` (default: `parallel`)
- `--fix` - Attempt automatic fixes (future feature)
- `--cache` - Use cached results (default: true)
- `--force` - Force re-validation (ignore cache)

**Examples**:
```bash
# Quick validation (parallel mode)
ce validate

# Full validation (no parallelization)
ce validate --mode=full

# Incremental (only changed files)
ce validate --mode=incremental

# Force re-validation
ce validate --force
```

**Validation Types**:
- ✅ **Path Checks**: Required files exist
- ✅ **Produces Checks**: Expected outputs created
- ✅ **Security Scans**: No secrets in code
- ✅ **Quality Checks**: Linting, formatting, tests

---

### `ce next`

**Purpose**: Advance to the next phase in the workflow.

**Syntax**:
```bash
ce next [options]
```

**Options**:
- `--skip-validation` - Skip validation (not recommended)
- `--force` - Force advance even if current phase incomplete

**Examples**:
```bash
# Normal advance (with validation)
ce next

# Skip validation (use with caution)
ce next --skip-validation

# Force advance
ce next --force
```

**Phase Transitions**:
```
P0 (Discovery)      →  P1 (Plan)
P1 (Plan)           →  P2 (Skeleton)
P2 (Skeleton)       →  P3 (Implementation)
P3 (Implementation) →  P4 (Testing)
P4 (Testing)        →  P5 (Review)
P5 (Review)         →  P6 (Release)
P6 (Release)        →  P7 (Monitor)
```

---

### `ce publish`

**Purpose**: Publish feature branch to remote and create pull request.

**Syntax**:
```bash
ce publish [options]
```

**Options**:
- `--title=<title>` - PR title (auto-generated if not provided)
- `--body=<body>` - PR description (uses template if not provided)
- `--draft` - Create as draft PR
- `--no-pr` - Push only, don't create PR

**Examples**:
```bash
# Basic publish (creates PR)
ce publish

# Custom PR title
ce publish --title="feat: User authentication module"

# Draft PR
ce publish --draft

# Push only (no PR)
ce publish --no-pr
```

**What Happens**:
1. Final validation run
2. Git push to origin
3. PR creation (using gh CLI or web fallback)
4. Health check execution
5. Summary report generation

---

### `ce merge`

**Purpose**: Merge feature branch into target branch.

**Syntax**:
```bash
ce merge [target-branch] [options]
```

**Options**:
- `--squash` - Squash commits
- `--no-ff` - No fast-forward
- `--strategy=<strategy>` - Merge strategy: `merge`, `squash`, `rebase`
- `--delete-branch` - Delete feature branch after merge

**Examples**:
```bash
# Merge to main
ce merge main

# Squash merge
ce merge main --squash

# Merge and delete branch
ce merge main --delete-branch
```

**Safety Features**:
- ✅ Pre-merge validation
- ✅ Conflict detection
- ✅ Health check after merge
- ✅ Automatic rollback on failure

---

### `ce clean`

**Purpose**: Clean up merged branches and old sessions.

**Syntax**:
```bash
ce clean [options]
```

**Options**:
- `--branches` - Clean merged branches
- `--sessions` - Clean old session files
- `--logs` - Clean old log files
- `--all` - Clean everything
- `--dry-run` - Show what would be deleted without deleting

**Examples**:
```bash
# Clean merged branches
ce clean --branches

# Clean old sessions (>7 days)
ce clean --sessions

# Clean everything
ce clean --all

# Preview what will be cleaned
ce clean --all --dry-run
```

---

### `ce pause`

**Purpose**: Pause current session (save state).

**Syntax**:
```bash
ce pause [message]
```

**Examples**:
```bash
# Pause with message
ce pause "Switching to hotfix"

# Pause without message
ce pause
```

---

### `ce resume`

**Purpose**: Resume paused session.

**Syntax**:
```bash
ce resume [session-id]
```

**Examples**:
```bash
# Resume last paused session
ce resume

# Resume specific session
ce resume feature-auth-20251009
```

---

### `ce end`

**Purpose**: End current session (cleanup and archive).

**Syntax**:
```bash
ce end [options]
```

**Options**:
- `--keep-branch` - Don't delete branch
- `--archive` - Archive session state

**Examples**:
```bash
# End and cleanup
ce end

# End but keep branch
ce end --keep-branch
```

---

## 5. Advanced Usage

### Performance Optimization

#### Caching

CE CLI automatically caches validation results to improve performance.

```bash
# Check cache status
ce status --cache-info

# Clear cache
ce validate --clear-cache

# Disable caching for this run
ce validate --no-cache
```

**Cache Behavior**:
- ✅ TTL: 5 minutes
- ✅ Invalidated on file changes
- ✅ Per-commit basis
- ✅ Per-phase isolation

#### Parallel Validation

```bash
# Use parallel validation (fastest)
ce validate --mode=parallel

# Number of parallel jobs (default: 4)
ce validate --mode=parallel --jobs=8
```

**Performance Comparison**:
| Mode | Time | When to Use |
|------|------|-------------|
| `full` | 10-15s | First-time validation |
| `quick` | 5-8s | Partial checks |
| `incremental` | 2-3s | After small changes |
| `parallel` | 3-5s | Default, balanced speed |

---

### Multi-Terminal Patterns

#### Pattern 1: Feature Segmentation

```bash
# Terminal 1: Backend
export CE_TERMINAL_ID=t1
ce start backend-api

# Terminal 2: Frontend
export CE_TERMINAL_ID=t2
ce start frontend-ui

# Terminal 3: Database
export CE_TERMINAL_ID=t3
ce start db-migration
```

#### Pattern 2: Phase Separation

```bash
# Terminal 1: New feature (P0-P2)
export CE_TERMINAL_ID=t1
ce start new-feature

# Terminal 2: Implementation (P3-P4)
export CE_TERMINAL_ID=t2
ce start ongoing-feature --phase=P3

# Terminal 3: Review/Release (P5-P6)
export CE_TERMINAL_ID=t3
ce start ready-feature --phase=P5
```

#### Pattern 3: Emergency Hotfix

```bash
# Save current work
ce pause "Production issue - switching to hotfix"

# Switch to hotfix
ce start hotfix-critical --from=production --phase=P3

# After hotfix
ce end --keep-branch

# Resume previous work
ce resume
```

---

### Scripting with CE CLI

#### Bash Script Example

```bash
#!/bin/bash
# auto-feature.sh - Automated feature workflow

FEATURE_NAME=$1

# Start feature
ce start "$FEATURE_NAME" || exit 1

# Auto-progress through phases
for phase in P0 P1 P2; do
    echo "Working on phase $phase..."

    # Do work here
    # ... your development work ...

    # Validate
    ce validate || exit 1

    # Next phase
    ce next || exit 1
done

echo "Feature ready for implementation (P3)"
```

#### JSON Output for Integration

```bash
# Get status as JSON
STATUS=$(ce status --json)

# Extract current phase
PHASE=$(echo "$STATUS" | jq -r '.current_phase')

# Check if validation passed
VALID=$(echo "$STATUS" | jq -r '.validation.passed')

if [[ "$VALID" == "true" ]]; then
    echo "Phase $PHASE validated successfully"
    ce next
fi
```

---

## 6. Configuration

### Environment Variables

```bash
# Terminal ID (t1, t2, t3, etc.)
export CE_TERMINAL_ID=t1

# Cache TTL (seconds)
export CE_CACHE_TTL=300

# Parallel jobs
export CE_PARALLEL_JOBS=4

# Validation mode
export CE_VALIDATE_MODE=parallel

# Auto-advance on validation success
export CE_AUTO_ADVANCE=false

# PR template
export CE_PR_TEMPLATE=.workflow/cli/templates/pr_description.md
```

### Configuration File

`.workflow/cli/config.yml`:

```yaml
# [TEMPLATE - TO BE IMPLEMENTED IN P3]
defaults:
  terminal_id: t1
  initial_phase: P0
  base_branch: main

validation:
  mode: parallel
  cache_ttl: 300
  parallel_jobs: 4

git:
  auto_push: false
  require_pr: true
  default_merge_strategy: squash

ui:
  colored_output: true
  show_progress: true
  verbose_errors: true
```

---

## 7. Troubleshooting

### Common Issues

#### Issue: `ce: command not found`

**Symptom**:
```bash
ce --version
# bash: ce: command not found
```

**Solution**:
```bash
# Check if symbolic link exists
ls -la /usr/local/bin/ce

# If not, recreate it
sudo ln -sf "$(pwd)/.workflow/cli/ce.sh" /usr/local/bin/ce
chmod +x .workflow/cli/ce.sh
```

---

#### Issue: Terminal State Conflict

**Symptom**:
```bash
ce status
# Error: State file locked by another terminal
```

**Solution**:
```bash
# Check lock files
ls .workflow/cli/state/locks/

# Remove stale locks (>1 hour old)
find .workflow/cli/state/locks/ -type f -mmin +60 -delete

# Or use different terminal ID
export CE_TERMINAL_ID=t2
```

---

#### Issue: Validation Fails

**Symptom**:
```bash
ce validate
# ❌ Phase P2 validation failed!
```

**Solution**:
```bash
# Run verbose validation to see details
ce validate --verbose

# Check specific requirement
ce validate --mode=full

# Get suggested fixes
ce validate --suggest-fixes
```

---

#### Issue: Cache Issues

**Symptom**: Validation returns cached results despite file changes.

**Solution**:
```bash
# Clear cache
rm -rf .workflow/.cache

# Or force re-validation
ce validate --force
```

---

### Debug Mode

```bash
# Enable debug output
export CE_DEBUG=1
ce status

# Check logs
tail -f .workflow/logs/ce.log

# Verbose mode
ce validate --verbose --debug
```

---

## 8. FAQ

### General

**Q: Can I use CE CLI without Claude Code?**
A: Yes, CE CLI is a standalone tool that works with any development workflow. However, it's designed to complement Claude Code's AI capabilities.

**Q: How many terminals can I use simultaneously?**
A: Up to 10 terminals (t1-t10). Most users need 2-3.

**Q: Does CE CLI work on Windows?**
A: Yes, through WSL (Windows Subsystem for Linux) or Git Bash.

---

### Workflow

**Q: Can I skip phases?**
A: Not recommended. Use `ce next --force` if absolutely necessary, but quality gates exist for a reason.

**Q: What happens if I forget which phase I'm in?**
A: Run `ce status` to see current phase and progress.

**Q: Can I go back to a previous phase?**
A: Use `ce pause` to save current work, then `ce start` a new branch if you need to restart.

---

### Performance

**Q: Why is `ce validate` slow the first time?**
A: First run performs full validation. Subsequent runs use cache and incremental checks (3-5x faster).

**Q: How can I speed up validation?**
A: Use `ce validate --mode=parallel` or `--mode=incremental`.

---

### Multi-Terminal

**Q: How do I switch between terminals?**
A: Set `CE_TERMINAL_ID` environment variable: `export CE_TERMINAL_ID=t2`

**Q: Can two terminals work on the same feature?**
A: No, each terminal should work on a separate feature to avoid conflicts.

---

## 9. Best Practices

### Naming Conventions

✅ **Good Feature Names**:
```bash
ce start user-authentication
ce start payment-integration
ce start fix-login-bug
```

❌ **Bad Feature Names**:
```bash
ce start test          # Too generic
ce start "New Feature" # Spaces and caps
ce start update        # Unclear purpose
```

---

### Phase Progression

✅ **Follow the Flow**:
```bash
# Complete each phase fully
ce start my-feature     # P0
# ... do discovery work ...
ce validate && ce next  # P0 → P1

# ... do planning work ...
ce validate && ce next  # P1 → P2

# ... and so on ...
```

❌ **Don't Skip**:
```bash
# Don't rush through phases
ce start my-feature --phase=P3  # ❌ Skip discovery and planning
ce next --skip-validation       # ❌ Skip quality checks
```

---

### Multi-Terminal Usage

✅ **Clear Separation**:
```bash
# Terminal 1: Major feature
export CE_TERMINAL_ID=t1
ce start major-feature

# Terminal 2: Independent bug fix
export CE_TERMINAL_ID=t2
ce start bug-fix

# Terminal 3: Documentation
export CE_TERMINAL_ID=t3
ce start update-docs
```

❌ **Overlap**:
```bash
# Don't work on same files in multiple terminals
# Terminal 1: Editing user.py
# Terminal 2: Also editing user.py  # ❌ Conflict!
```

---

### Validation

✅ **Regular Checks**:
```bash
# Validate frequently during development
ce validate

# Before committing
ce validate && git commit -m "..."

# Before advancing phase
ce validate && ce next
```

❌ **Ignore Warnings**:
```bash
# Don't bypass validation unless emergency
ce next --skip-validation  # ❌
```

---

### Git Integration

✅ **Clean Commits**:
```bash
# CE CLI handles branching
ce start my-feature

# You handle commits
git add .
git commit -m "feat: implement user auth"

# CE CLI handles publishing
ce publish
```

❌ **Manual Branch Creation**:
```bash
# Don't create branches manually when using CE CLI
git checkout -b feature/my-feature  # ❌ CE CLI should handle this
```

---

## Related Documentation

- [Developer Guide](./DEVELOPER_GUIDE.md) - For extending CE CLI
- [API Reference](./API_REFERENCE.md) - Function-level documentation
- [Architecture](../../../docs/P1_CE_COMMAND_ARCHITECTURE.md) - System design

---

## Support

- **Issues**: Report bugs at GitHub Issues
- **Discussions**: Ask questions in GitHub Discussions
- **Documentation**: https://docs.claude-enhancer.com

---

**Last Updated**: 2025-10-09
**Version**: 1.0.0
**Status**: ⚠️ TEMPLATE - Implementation pending (P3)

---

*Generated by Claude Code - CE CLI Documentation Team*
