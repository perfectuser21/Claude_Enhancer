# Installation Guide - Claude Enhancer 6.2.0

Complete installation guide for Claude Enhancer, the production-ready AI programming workflow system.

## Prerequisites

### Required Software
- **Git**: 2.30+
- **Node.js**: 18+ (for BDD testing and tools)
- **Python**: 3.8+ (for automation scripts)
- **Bash**: 4.0+ (for hooks and scripts)

### Optional but Recommended
- **Docker**: For containerized development
- **GitHub CLI**: For automated PR workflows

## Quick Installation

### 1. Clone or Initialize in Existing Project

```bash
# For new projects
git clone https://github.com/yourusername/claude-enhancer.git
cd claude-enhancer

# For existing projects
cd your-project
# Copy Claude Enhancer files here
```

### 2. Run Installation Script

```bash
# Make installation script executable
chmod +x .claude/install.sh

# Run installation
./.claude/install.sh
```

The install script will:
- ✅ Set up Git hooks (pre-commit, commit-msg, pre-push)
- ✅ Configure Claude hooks (.claude/hooks/)
- ✅ Install npm dependencies (if package.json exists)
- ✅ Create required directories (.temp, evidence, archive)
- ✅ Verify installation integrity

### 3. Verify Installation

```bash
# Check metrics
python3 scripts/auto_metrics.py --report

# Run cleanup to organize documents
bash scripts/cleanup_documents.sh

# Test Git hooks
git commit --allow-empty -m "test: verify installation"
```

## Manual Installation

If you prefer manual installation or need to troubleshoot:

### 1. Set Up Git Hooks

```bash
# Copy hooks to .git/hooks/
cp .git-hooks/pre-commit .git/hooks/pre-commit
cp .git-hooks/commit-msg .git/hooks/commit-msg
cp .git-hooks/pre-push .git/hooks/pre-push

# Make them executable
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
chmod +x .git/hooks/pre-push
```

### 2. Configure Claude Hooks

```bash
# Make Claude hooks executable
chmod +x .claude/hooks/*.sh

# Verify they work
bash .claude/hooks/branch_helper.sh --check
```

### 3. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (if using Python scripts)
pip3 install pyyaml
```

### 4. Create Required Directories

```bash
mkdir -p .temp/analysis
mkdir -p .temp/reports
mkdir -p .temp/quarantine
mkdir -p evidence
mkdir -p archive
mkdir -p docs/releases
```

## Configuration

### 1. Claude Settings

Edit `.claude/settings.json`:

```json
{
  "workflow": {
    "phases": ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"],
    "enforce_sequence": true,
    "quality_gates": true
  },
  "agents": {
    "min_count": 3,
    "recommended_count": 5,
    "max_parallel": 8
  },
  "branch_protection": {
    "protected_branches": ["main", "master", "production"],
    "require_pr": true
  }
}
```

### 2. Branch Protection (GitHub)

Enable branch protection rules for `main`:

1. Go to: Settings → Branches → Branch protection rules
2. Add rule for `main`:
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
   - ✅ Include administrators

### 3. CI/CD Setup

Ensure GitHub Actions workflows are enabled:

```bash
# Check workflows
ls .github/workflows/

# Key workflows:
# - ce-unified-gates.yml  (main quality gate)
# - bp-guard.yml          (branch protection)
# - test-suite.yml        (tests)
# - auto-pr.yml           (auto PR creation)
# - positive-health.yml   (health checks)
```

## Verification Steps

### 1. Test Git Hooks

```bash
# Test pre-commit (should check code quality)
git add .
git commit -m "test: installation"

# Test pre-push (should block push to main)
git checkout main
echo "test" > test.txt
git add test.txt
git commit -m "test: should be blocked"
git push origin main  # Should be blocked by hook
```

### 2. Test Metrics Collection

```bash
# Collect real metrics
python3 scripts/auto_metrics.py --report

# Check for inflation
python3 scripts/auto_metrics.py --check-only
```

### 3. Test Document Cleanup

```bash
# Run cleanup
bash scripts/cleanup_documents.sh

# Should show:
# - Core documents: ≤7
# - Quarantined unauthorized files
# - Cleanup statistics
```

### 4. Test BDD Scenarios

```bash
# Run BDD tests
npm run bdd

# Or with specific tags
npm run bdd -- --tags "@critical"
```

## Troubleshooting

### Git Hooks Not Running

```bash
# Verify hooks are executable
ls -la .git/hooks/

# Re-install hooks
./.claude/install.sh --force

# Check Git hooks path
git config --get core.hooksPath
```

### Permission Denied Errors

```bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py
chmod +x .claude/hooks/*.sh
```

### Python Script Errors

```bash
# Install missing dependencies
pip3 install pyyaml

# Verify Python version
python3 --version  # Should be 3.8+
```

### Branch Protection Issues

```bash
# Check current branch
git branch --show-current

# If on protected branch, create new branch
git checkout -b feature/your-feature

# Verify hook is working
bash .git/hooks/pre-push
```

## Uninstallation

To remove Claude Enhancer:

```bash
# Remove Git hooks
rm .git/hooks/pre-commit
rm .git/hooks/commit-msg
rm .git/hooks/pre-push

# Remove Claude directory
rm -rf .claude

# Remove scripts
rm -rf scripts/auto_metrics.py
rm -rf scripts/cleanup_documents.sh

# Remove temporary directories
rm -rf .temp
rm -rf evidence
```

## Next Steps

After installation:

1. Read [CLAUDE.md](CLAUDE.md) for system overview
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) for 8-Phase workflow
3. Read [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow
4. Create your first feature branch: `git checkout -b feature/my-first-feature`
5. Start development with P0-P7 workflow

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Installation Complete!** 🎉

Claude Enhancer is now ready to provide production-grade AI programming workflow.
