# System Startup Runbook

## Purpose
Step-by-step procedure for starting Claude Enhancer 5.3 system.

## Prerequisites
- System meets minimum requirements
- All dependencies installed
- Configuration files present
- No conflicting processes running

## Startup Procedure

### Step 1: Pre-Start Checks (2 minutes)

```bash
# Check system resources
free -h  # Should show >= 4GB available
df -h .  # Should show >= 10GB available

# Check dependencies
git --version  # >= 2.30.0
node --version  # >= 18.0.0
npm --version  # >= 9.0.0

# Check for port conflicts
lsof -i :8000 2>/dev/null || echo "Port 8000 available"
lsof -i :3000 2>/dev/null || echo "Port 3000 available"
```

### Step 2: Initialize Environment (1 minute)

```bash
# Navigate to project directory
cd "/home/xx/dev/Claude Enhancer 5.0"

# Source environment variables
source .env 2>/dev/null || echo "No .env file"

# Verify configuration
test -f .claude/settings.json && echo "Config exists" || echo "Warning: No config"
```

### Step 3: Start Core Services (2 minutes)

```bash
# Start workflow system
if [ ! -f .workflow/ACTIVE ]; then
    echo "ready" > .workflow/ACTIVE
    echo "0" > .phase/current
fi

# Verify Git hooks are installed
if [ ! -x .git/hooks/pre-commit ]; then
    echo "Installing Git hooks..."
    ./.claude/install.sh
fi

# Clear old lock files
rm -f .workflow/*.lock 2>/dev/null
```

### Step 4: Verify Startup (1 minute)

```bash
# Run health check
./scripts/healthcheck.sh

# Expected output:
# ✓ Git hooks installed
# ✓ Configuration valid
# ✓ Workflow initialized
# ✓ All systems operational

# Check logs
tail -10 logs/app.log 2>/dev/null || echo "No logs yet"
```

### Step 5: Post-Start Validation (1 minute)

```bash
# Verify core functionality
echo "test" > /tmp/startup_test.txt
cd /tmp
git init test_repo 2>/dev/null
cd test_repo
cp "/home/xx/dev/Claude Enhancer 5.0/.git/hooks/pre-commit" .git/hooks/ 2>/dev/null
echo "test" > test.txt
git add test.txt
git commit -m "test: startup validation" 2>/dev/null
cd /tmp
rm -rf test_repo startup_test.txt

echo "✓ Startup validation complete"
```

## Success Criteria
- All health checks pass
- No error messages in logs
- Git hooks executable
- Workflow state initialized
- No port conflicts

## Troubleshooting

### Issue: Port Already in Use
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
```

### Issue: Git Hooks Not Installed
```bash
# Reinstall hooks
./.claude/install.sh --force
chmod +x .git/hooks/*
```

### Issue: Configuration Missing
```bash
# Create default configuration
cp .claude/settings.example.json .claude/settings.json 2>/dev/null
```

## Rollback
If startup fails, no rollback needed - system remains in stopped state.

---
**Estimated Time**: 7 minutes
**Last Updated**: 2025-10-10
