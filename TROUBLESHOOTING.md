# Perfect21 Troubleshooting Guide

> Complete troubleshooting guide for Perfect21 system issues, debugging methods, and performance optimization

## 📋 Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues & Solutions](#common-issues--solutions)
- [Hook Debugging](#hook-debugging)
- [Agent Selection Problems](#agent-selection-problems)
- [Git Integration Issues](#git-integration-issues)
- [Performance Problems](#performance-problems)
- [Log Analysis](#log-analysis)
- [System Recovery](#system-recovery)
- [Advanced Debugging](#advanced-debugging)

## 🔍 Quick Diagnostics

### Instant Health Check

Run this comprehensive diagnostic command:

```bash
bash << 'EOF'
#!/bin/bash
echo "🏥 Perfect21 Quick Diagnostics"
echo "========================================"
echo ""

# System info
echo "📊 System Information:"
echo "  OS: $(uname -s -r)"
echo "  Shell: $SHELL"
echo "  PWD: $PWD"
echo "  User: $(whoami)"
echo ""

# Git status
echo "📝 Git Repository:"
if git status &>/dev/null; then
    echo "  ✅ Valid git repository"
    echo "  Branch: $(git branch --show-current)"
    echo "  Status: $(git status --porcelain | wc -l) changed files"
else
    echo "  ❌ Not a git repository or git not available"
fi
echo ""

# Perfect21 files
echo "🗂️  Perfect21 Files:"
echo "  .claude folder: $([ -d .claude ] && echo "✅ EXISTS" || echo "❌ MISSING")"
echo "  settings.json: $([ -f .claude/settings.json ] && echo "✅ EXISTS" || echo "❌ MISSING")"
echo "  install.sh: $([ -f .claude/install.sh ] && echo "✅ EXISTS" || echo "❌ MISSING")"
echo ""

# Executable permissions
echo "🔐 Permissions:"
EXEC_SCRIPTS=$(find .claude -name "*.sh" -executable 2>/dev/null | wc -l)
TOTAL_SCRIPTS=$(find .claude -name "*.sh" 2>/dev/null | wc -l)
echo "  Executable scripts: $EXEC_SCRIPTS/$TOTAL_SCRIPTS"
if [ "$EXEC_SCRIPTS" -ne "$TOTAL_SCRIPTS" ]; then
    echo "  ⚠️  Some scripts are not executable"
fi
echo ""

# Git hooks
echo "🪝 Git Hooks:"
echo "  pre-commit: $([ -f .git/hooks/pre-commit ] && echo "✅ INSTALLED" || echo "❌ MISSING")"
echo "  commit-msg: $([ -f .git/hooks/commit-msg ] && echo "✅ INSTALLED" || echo "❌ MISSING")"
echo ""

# Agents
echo "🤖 Agents:"
AGENT_COUNT=$(find .claude/agents -name "*.md" 2>/dev/null | wc -l)
echo "  Available agents: $AGENT_COUNT"
if [ $AGENT_COUNT -lt 50 ]; then
    echo "  ⚠️  Expected 56 agents, found $AGENT_COUNT"
fi
echo ""

# Hook testing
echo "🧪 Hook Testing:"
if [ -f .claude/hooks/smart_agent_selector.sh ]; then
    if echo '{"prompt": "test"}' | timeout 5 bash .claude/hooks/smart_agent_selector.sh >/dev/null 2>&1; then
        echo "  ✅ Agent selector working"
    else
        echo "  ❌ Agent selector failed"
    fi
else
    echo "  ❌ Agent selector missing"
fi
echo ""

# Overall status
echo "========================================"
if [ -f .claude/settings.json ] && [ $AGENT_COUNT -gt 50 ] && [ $EXEC_SCRIPTS -eq $TOTAL_SCRIPTS ]; then
    echo "🎉 Overall Status: HEALTHY"
else
    echo "⚠️  Overall Status: ISSUES DETECTED"
    echo ""
    echo "Quick fixes to try:"
    echo "  1. chmod +x .claude/hooks/*.sh"
    echo "  2. bash .claude/install.sh"
    echo "  3. Check TROUBLESHOOTING.md"
fi
echo "========================================"
EOF
```

### Environment Check
```bash
# Check required tools
for tool in git bash chmod find grep; do
    if command -v $tool >/dev/null; then
        echo "✅ $tool available"
    else
        echo "❌ $tool missing"
    fi
done

# Check Python (optional)
if command -v python3 >/dev/null; then
    echo "✅ Python3: $(python3 --version)"
else
    echo "⚠️  Python3 not available (optional)"
fi
```

## 🐛 Common Issues & Solutions

### Issue 1: "Permission denied" on hooks

**Symptoms:**
```
bash: .claude/hooks/smart_agent_selector.sh: Permission denied
```

**Root Cause:** Script files don't have execute permissions.

**Solution:**
```bash
# Fix permissions for all scripts
chmod +x .claude/hooks/*.sh
chmod +x .claude/scripts/*.sh 2>/dev/null
chmod +x .git/hooks/pre-commit 2>/dev/null
chmod +x .git/hooks/commit-msg 2>/dev/null

# Verify fix
ls -la .claude/hooks/*.sh | grep -E "rwx"
```

**Prevention:** Always run `bash .claude/install.sh` after copying files.

### Issue 2: Agent selector returns no output

**Symptoms:**
```bash
echo '{"prompt": "test"}' | bash .claude/hooks/smart_agent_selector.sh
# No output or error
```

**Debugging Steps:**
```bash
# 1. Test with verbose output
echo '{"prompt": "test task"}' | bash -x .claude/hooks/smart_agent_selector.sh

# 2. Check script syntax
bash -n .claude/hooks/smart_agent_selector.sh

# 3. Run with error output
echo '{"prompt": "test"}' | bash .claude/hooks/smart_agent_selector.sh 2>&1

# 4. Test input parsing
echo '{"prompt": "create API endpoint"}' | bash .claude/hooks/smart_agent_selector.sh
```

**Common Fixes:**
```bash
# Fix 1: Ensure input format is correct
echo '{"prompt": "your task description"}' | bash .claude/hooks/smart_agent_selector.sh

# Fix 2: Check for special characters in task description
echo '{"prompt": "simple task without special chars"}' | bash .claude/hooks/smart_agent_selector.sh

# Fix 3: Reinstall if script is corrupted
cp .claude/hooks/smart_agent_selector.sh .claude/hooks/smart_agent_selector.sh.backup
# Re-copy from source or restore from backup
```

### Issue 3: Git hooks not triggering

**Symptoms:**
- Commits succeed without pre-commit checks
- No Perfect21 output during git operations

**Diagnosis:**
```bash
# Check if hooks exist
ls -la .git/hooks/pre-commit .git/hooks/commit-msg

# Check hook permissions
ls -la .git/hooks/ | grep -E "(pre-commit|commit-msg)"

# Test hooks manually
.git/hooks/pre-commit
echo "test: commit message" | .git/hooks/commit-msg /dev/stdin
```

**Solutions:**
```bash
# Solution 1: Reinstall hooks
bash .claude/install.sh

# Solution 2: Manual installation
cp .claude/git-hooks/pre-commit .git/hooks/pre-commit
cp .claude/git-hooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg

# Solution 3: Check git config
git config core.hooksPath
# Should be empty or point to .git/hooks

# Solution 4: Reset hooks path if needed
git config --unset core.hooksPath
```

### Issue 4: Claude Code not recognizing Perfect21

**Symptoms:**
- Claude Code doesn't mention agent selection
- No Perfect21 workflow guidance appears

**Debugging:**
```bash
# Check settings.json format
cat .claude/settings.json | python3 -m json.tool

# Verify hooks configuration
grep -A 10 '"hooks"' .claude/settings.json

# Test hook manually
echo "test user prompt" | bash .claude/hooks/branch_helper.sh
```

**Solutions:**
```bash
# Solution 1: Validate JSON syntax
python3 -c "import json; print(json.load(open('.claude/settings.json')))"

# Solution 2: Restore default settings
cp .claude/config-archive/settings-complete.json .claude/settings.json

# Solution 3: Check hook paths in settings.json
grep "command.*bash" .claude/settings.json
# Ensure paths are relative to project root
```

### Issue 5: "Agent not found" errors

**Symptoms:**
```
Error: Agent 'backend-architect' not found
Available agents: [list...]
```

**Investigation:**
```bash
# List all available agents
find .claude/agents -name "*.md" | sort | sed 's|.claude/agents/||' | sed 's|\.md||'

# Check specific agent file
ls -la .claude/agents/development/backend-architect.md

# Count agents by category
for dir in .claude/agents/*/; do
    echo "$(basename "$dir"): $(find "$dir" -name "*.md" | wc -l) agents"
done
```

**Solutions:**
```bash
# Solution 1: Verify agent files exist
if [ ! -f .claude/agents/development/backend-architect.md ]; then
    echo "❌ backend-architect.md missing"
    # Re-copy agent files from source
fi

# Solution 2: Check agent file format
head -5 .claude/agents/development/backend-architect.md

# Solution 3: Use alternative agents if some are missing
echo '{"prompt": "backend task"}' | bash .claude/hooks/smart_agent_selector.sh 2>&1 | grep "推荐Agent"
```

## 🪝 Hook Debugging

### Enable Debug Mode

```bash
# Method 1: Environment variable
export CLAUDE_ENHANCER_DEBUG=true
echo '{"prompt": "test"}' | bash .claude/hooks/smart_agent_selector.sh

# Method 2: Bash debug mode
echo '{"prompt": "test"}' | bash -x .claude/hooks/smart_agent_selector.sh

# Method 3: Add debug output to script
sed -i '1a set -x' .claude/hooks/smart_agent_selector.sh
# Remember to remove later: sed -i '/set -x/d' .claude/hooks/smart_agent_selector.sh
```

### Hook Execution Flow

```bash
# Trace hook execution
echo "Tracing hook execution..." > /tmp/perfect21_debug.log

# Test UserPromptSubmit hook
echo "test prompt" 2>&1 | tee -a /tmp/perfect21_debug.log | bash .claude/hooks/branch_helper.sh

# Test PreToolUse hook
echo '{"prompt": "test task", "tool": "Task"}' 2>&1 | tee -a /tmp/perfect21_debug.log | bash .claude/hooks/smart_agent_selector.sh

# Check results
cat /tmp/perfect21_debug.log
```

### Hook Performance Analysis

```bash
# Measure hook execution time
time echo '{"prompt": "test"}' | bash .claude/hooks/smart_agent_selector.sh

# Profile hook with detailed timing
bash << 'EOF'
start_time=$(date +%s.%N)
echo '{"prompt": "complex microservice architecture"}' | bash .claude/hooks/smart_agent_selector.sh > /dev/null
end_time=$(date +%s.%N)
echo "Hook execution time: $(echo "$end_time - $start_time" | bc)s"
EOF

# Monitor hook resource usage
{ time bash .claude/hooks/smart_agent_selector.sh < /dev/null; } 2>&1 | grep -E "(real|user|sys)"
```

### Custom Hook Testing

```bash
# Create test hook for debugging
cat > /tmp/test_hook.sh << 'EOF'
#!/bin/bash
echo "🧪 Test Hook Debug"
echo "Input: $*"
echo "Stdin: $(cat)"
echo "Environment: $CLAUDE_ENHANCER_MODE"
echo "PWD: $PWD"
echo "PATH: $PATH"
EOF

chmod +x /tmp/test_hook.sh

# Test the debug hook
echo '{"test": "data"}' | /tmp/test_hook.sh arg1 arg2
```

## 🤖 Agent Selection Problems

### Debug Agent Selection Logic

```bash
# Test different complexity levels
test_complexities() {
    local tasks=(
        "fix typo"
        "add new API endpoint"
        "refactor entire microservice architecture"
        "implement OAuth2 authentication system"
        "fix simple bug in login form"
        "design distributed logging system"
    )

    for task in "${tasks[@]}"; do
        echo "Testing task: '$task'"
        echo "{\"prompt\": \"$task\"}" | bash .claude/hooks/smart_agent_selector.sh 2>&1 | grep -E "(复杂度|执行模式|预计时间)"
        echo "---"
    done
}

test_complexities
```

### Analyze Complexity Detection

```bash
# Extract and test complexity function
extract_complexity_function() {
    # Extract the determine_complexity function from the script
    sed -n '/^determine_complexity()/,/^}/p' .claude/hooks/smart_agent_selector.sh
}

# Test complexity detection manually
test_complexity() {
    local desc="$1"
    local desc_lower=$(echo "$desc" | tr '[:upper:]' '[:lower:]')

    echo "Testing: $desc"

    # Complex task check
    if echo "$desc_lower" | grep -qE "architect|design system|integrate|migrate|refactor entire|complex|全栈|架构|重构整个|复杂"; then
        echo "  → Complex task detected"
    # Simple task check
    elif echo "$desc_lower" | grep -qE "fix bug|typo|minor|quick|simple|small change|修复bug|小改动|简单|快速"; then
        echo "  → Simple task detected"
    else
        echo "  → Standard task (default)"
    fi
}

# Test various descriptions
test_complexity "fix bug in login"
test_complexity "architect new microservice"
test_complexity "add validation to form"
test_complexity "refactor entire authentication system"
```

### Agent Availability Check

```bash
# Verify all expected agents exist
expected_agents=(
    "development/backend-architect"
    "development/backend-engineer"
    "development/database-specialist"
    "development/frontend-specialist"
    "quality/test-engineer"
    "quality/security-auditor"
    "quality/performance-engineer"
    "process/technical-writer"
    "process/code-reviewer"
    "specialized/cleanup-specialist"
)

echo "🤖 Agent Availability Check:"
for agent in "${expected_agents[@]}"; do
    if [ -f ".claude/agents/$agent.md" ]; then
        echo "  ✅ $agent"
    else
        echo "  ❌ $agent (MISSING)"
    fi
done
```

### Custom Agent Configuration

```bash
# Create custom agent selection for your project
cat > .claude/hooks/custom_agent_selector.sh << 'EOF'
#!/bin/bash
# Custom agent selector for your specific project needs

INPUT=$(cat)
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")

echo "🎯 Custom Agent Selection for $(basename $PWD)"

# Your custom selection logic here
if echo "$TASK_DESC" | grep -qi "database\|sql\|migration"; then
    echo "Database-focused task detected"
    echo "Recommended agents:"
    echo "  1. database-specialist"
    echo "  2. backend-architect"
    echo "  3. test-engineer"
    echo "  4. performance-engineer"
elif echo "$TASK_DESC" | grep -qi "frontend\|ui\|react\|vue"; then
    echo "Frontend-focused task detected"
    echo "Recommended agents:"
    echo "  1. frontend-specialist"
    echo "  2. react-pro"
    echo "  3. test-engineer"
    echo "  4. technical-writer"
fi

# Pass through to original selector
echo "$INPUT" | bash .claude/hooks/smart_agent_selector.sh
EOF

chmod +x .claude/hooks/custom_agent_selector.sh
```

## 🔧 Git Integration Issues

### Git Hook Debugging

```bash
# Test pre-commit hook in isolation
debug_pre_commit() {
    echo "🔍 Testing pre-commit hook..."

    # Create test scenario
    echo "test content" > test_file.tmp
    git add test_file.tmp

    # Run pre-commit manually
    if .git/hooks/pre-commit; then
        echo "✅ Pre-commit passed"
    else
        echo "❌ Pre-commit failed"
    fi

    # Cleanup
    git reset HEAD test_file.tmp 2>/dev/null
    rm -f test_file.tmp
}

debug_pre_commit
```

### Commit Message Validation

```bash
# Test commit-msg hook
test_commit_messages() {
    local messages=(
        "fix: simple bug fix"
        "feat: add new feature"
        "invalid commit message"
        "docs: update README"
        "test: add unit tests"
    )

    for msg in "${messages[@]}"; do
        echo "Testing: '$msg'"
        if echo "$msg" | .git/hooks/commit-msg /dev/stdin 2>/dev/null; then
            echo "  ✅ Valid"
        else
            echo "  ❌ Invalid"
        fi
    done
}

test_commit_messages
```

### Git Configuration Issues

```bash
# Check git configuration that might affect hooks
echo "📊 Git Configuration:"
echo "  hooks path: $(git config core.hooksPath || echo "default (.git/hooks)")"
echo "  user.name: $(git config user.name)"
echo "  user.email: $(git config user.email)"
echo "  core.fileMode: $(git config core.fileMode)"

# Check for conflicting git configs
git config --list | grep -i hook

# Verify git version compatibility
echo "Git version: $(git --version)"
```

### Git Hook Recovery

```bash
# Backup and restore git hooks
backup_git_hooks() {
    local backup_dir=".git/hooks.backup.$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    cp .git/hooks/* "$backup_dir"/ 2>/dev/null
    echo "Git hooks backed up to: $backup_dir"
}

restore_perfect21_hooks() {
    echo "🔄 Restoring Perfect21 git hooks..."

    # Remove existing hooks
    rm -f .git/hooks/pre-commit .git/hooks/commit-msg

    # Reinstall from Perfect21
    if [ -f .claude/git-hooks/pre-commit ]; then
        cp .claude/git-hooks/pre-commit .git/hooks/pre-commit
        chmod +x .git/hooks/pre-commit
        echo "  ✅ pre-commit restored"
    fi

    if [ -f .claude/git-hooks/commit-msg ]; then
        cp .claude/git-hooks/commit-msg .git/hooks/commit-msg
        chmod +x .git/hooks/commit-msg
        echo "  ✅ commit-msg restored"
    fi
}
```

## ⚡ Performance Problems

### Performance Monitoring

```bash
# Monitor hook performance
monitor_hook_performance() {
    echo "📊 Monitoring Perfect21 Performance..."

    # Test agent selector performance
    echo "Agent Selector:"
    for i in {1..5}; do
        start=$(date +%s.%N)
        echo '{"prompt": "test task"}' | bash .claude/hooks/smart_agent_selector.sh > /dev/null
        end=$(date +%s.%N)
        echo "  Run $i: $(echo "$end - $start" | bc)s"
    done

    # Test branch helper performance
    echo "Branch Helper:"
    for i in {1..5}; do
        start=$(date +%s.%N)
        echo "test" | bash .claude/hooks/branch_helper.sh > /dev/null
        end=$(date +%s.%N)
        echo "  Run $i: $(echo "$end - $start" | bc)s"
    done
}

monitor_hook_performance
```

### Resource Usage Analysis

```bash
# Monitor resource usage during hook execution
profile_resource_usage() {
    echo "💾 Resource Usage Analysis..."

    # Memory usage before
    local mem_before=$(ps -o pid,vsz,rss,comm -p $$ | tail -n1)
    echo "Memory before: $mem_before"

    # CPU usage monitoring
    { time echo '{"prompt": "complex microservice system"}' | bash .claude/hooks/smart_agent_selector.sh > /dev/null; } 2>&1

    # Memory usage after
    local mem_after=$(ps -o pid,vsz,rss,comm -p $$ | tail -n1)
    echo "Memory after: $mem_after"
}

profile_resource_usage
```

### Performance Optimization

```bash
# Optimize hook performance
optimize_hooks() {
    echo "🚀 Optimizing Perfect21 Performance..."

    # 1. Cache agent file list
    if [ ! -f /tmp/perfect21_agent_cache ]; then
        find .claude/agents -name "*.md" > /tmp/perfect21_agent_cache
        echo "  ✅ Created agent cache"
    fi

    # 2. Reduce grep complexity
    # Replace multiple greps with single awk command in smart_agent_selector.sh

    # 3. Enable fast mode for simple tasks
    export CLAUDE_ENHANCER_FAST_MODE=true

    echo "  ✅ Performance optimizations applied"
}

optimize_hooks
```

### Timeout Configuration

```bash
# Configure timeouts to prevent hanging
configure_timeouts() {
    echo "⏰ Configuring timeouts..."

    # Update settings.json with reasonable timeouts
    python3 -c "
import json
with open('.claude/settings.json', 'r') as f:
    config = json.load(f)

# Set timeouts
for hook_type in config.get('hooks', {}):
    for hook in config['hooks'][hook_type]:
        if 'timeout' not in hook:
            hook['timeout'] = 5000  # 5 seconds default

with open('.claude/settings.json', 'w') as f:
    json.dump(config, f, indent=2)
"

    echo "  ✅ Timeouts configured"
}

configure_timeouts
```

## 📊 Log Analysis

### Enable Comprehensive Logging

```bash
# Setup logging infrastructure
setup_logging() {
    mkdir -p .claude/logs

    # Create log rotation script
    cat > .claude/scripts/rotate_logs.sh << 'EOF'
#!/bin/bash
# Rotate Perfect21 logs
find .claude/logs -name "*.log" -mtime +7 -delete
find /tmp -name "claude_*.log" -mtime +1 -delete
EOF

    chmod +x .claude/scripts/rotate_logs.sh

    # Enable logging in environment
    export CLAUDE_ENHANCER_LOG_FILE=".claude/logs/enhancer.log"
    export CLAUDE_ENHANCER_LOG_LEVEL="INFO"

    echo "📝 Logging configured:"
    echo "  Log directory: .claude/logs"
    echo "  Log file: $CLAUDE_ENHANCER_LOG_FILE"
    echo "  Log level: $CLAUDE_ENHANCER_LOG_LEVEL"
}

setup_logging
```

### Log Analysis Tools

```bash
# Analyze Perfect21 logs
analyze_logs() {
    echo "📊 Perfect21 Log Analysis"
    echo "========================="

    # Check if logs exist
    if [ -f /tmp/claude_agent_selection.log ]; then
        echo "Agent Selection Log:"
        echo "  Total selections: $(wc -l < /tmp/claude_agent_selection.log)"
        echo "  Simple tasks: $(grep -c "Simple" /tmp/claude_agent_selection.log)"
        echo "  Standard tasks: $(grep -c "Standard" /tmp/claude_agent_selection.log)"
        echo "  Complex tasks: $(grep -c "Complex" /tmp/claude_agent_selection.log)"
        echo ""

        echo "Recent selections:"
        tail -5 /tmp/claude_agent_selection.log | sed 's/^/  /'
        echo ""
    fi

    # Check git hook logs
    if [ -f .claude/logs/git-hooks.log ]; then
        echo "Git Hook Log:"
        echo "  Total commits: $(grep -c "pre-commit" .claude/logs/git-hooks.log 2>/dev/null)"
        echo "  Failed commits: $(grep -c "BLOCKED" .claude/logs/git-hooks.log 2>/dev/null)"
    fi

    # Check error logs
    local error_logs="/tmp/claude_error.log .claude/logs/error.log"
    for log in $error_logs; do
        if [ -f "$log" ]; then
            local error_count=$(wc -l < "$log")
            echo "Errors in $log: $error_count"
            if [ $error_count -gt 0 ]; then
                echo "Recent errors:"
                tail -3 "$log" | sed 's/^/  /'
            fi
        fi
    done
}

analyze_logs
```

### Real-time Log Monitoring

```bash
# Monitor logs in real-time
monitor_logs() {
    echo "👀 Real-time log monitoring (Ctrl+C to stop)..."

    # Create named pipes for log aggregation
    mkfifo /tmp/perfect21_monitor 2>/dev/null || true

    # Monitor multiple log sources
    {
        tail -f /tmp/claude_agent_selection.log 2>/dev/null | sed 's/^/[AGENT] /' &
        tail -f .claude/logs/enhancer.log 2>/dev/null | sed 's/^/[HOOK] /' &
        tail -f /tmp/claude_error.log 2>/dev/null | sed 's/^/[ERROR] /' &
        wait
    } | while read line; do
        echo "[$(date +%H:%M:%S)] $line"
    done
}

# Usage: monitor_logs &
```

## 🔄 System Recovery

### Complete Reset Procedure

```bash
# Complete Perfect21 reset
reset_perfect21() {
    echo "🔄 Resetting Perfect21 System..."

    # 1. Backup current state
    local backup_dir="perfect21_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    cp -r .claude "$backup_dir/" 2>/dev/null
    cp -r .git/hooks "$backup_dir/git_hooks" 2>/dev/null
    echo "  ✅ Current state backed up to: $backup_dir"

    # 2. Remove Perfect21 components
    rm -rf .claude/hooks/*
    rm -rf .claude/logs/*
    rm -f .git/hooks/pre-commit .git/hooks/commit-msg
    echo "  ✅ Perfect21 components removed"

    # 3. Clean temporary files
    rm -f /tmp/claude_*.log
    rm -f /tmp/perfect21_*.log
    echo "  ✅ Temporary files cleaned"

    # 4. Reinstall from source
    if [ -d "$backup_dir/.claude" ]; then
        cp -r "$backup_dir/.claude"/* .claude/
        bash .claude/install.sh
        echo "  ✅ Perfect21 reinstalled"
    else
        echo "  ⚠️  Manual reinstallation required"
    fi

    echo "🎉 Reset complete!"
}

# Usage: reset_perfect21
```

### Partial Recovery Procedures

```bash
# Recover only git hooks
recover_git_hooks() {
    echo "🔧 Recovering Git Hooks..."
    rm -f .git/hooks/pre-commit .git/hooks/commit-msg
    bash .claude/install.sh
    echo "  ✅ Git hooks recovered"
}

# Recover only agent files
recover_agents() {
    echo "🤖 Recovering Agent Files..."
    if [ -d .claude/agents ]; then
        local agent_count=$(find .claude/agents -name "*.md" | wc -l)
        echo "  Current agents: $agent_count"
        if [ $agent_count -lt 50 ]; then
            echo "  ⚠️  Missing agents detected, manual recovery needed"
        else
            echo "  ✅ Agent files appear complete"
        fi
    else
        echo "  ❌ Agents directory missing, full reinstall needed"
    fi
}

# Recover only hook scripts
recover_hooks() {
    echo "🪝 Recovering Hook Scripts..."
    chmod +x .claude/hooks/*.sh 2>/dev/null
    chmod +x .claude/scripts/*.sh 2>/dev/null
    echo "  ✅ Hook permissions restored"
}
```

### Emergency Mode

```bash
# Enable emergency mode (minimal functionality)
enable_emergency_mode() {
    echo "🚨 Enabling Perfect21 Emergency Mode..."

    # Create minimal settings
    cat > .claude/settings.emergency.json << 'EOF'
{
  "version": "4.0.0-emergency",
  "project": "Perfect21 Emergency Mode",
  "description": "Minimal functionality mode",
  "hooks": {},
  "environment": {
    "CLAUDE_ENHANCER_MODE": "advisory"
  }
}
EOF

    # Backup current settings and switch
    mv .claude/settings.json .claude/settings.backup.json
    mv .claude/settings.emergency.json .claude/settings.json

    echo "  ✅ Emergency mode enabled"
    echo "  ℹ️  Original settings backed up to settings.backup.json"
    echo "  ℹ️  To restore: mv .claude/settings.backup.json .claude/settings.json"
}

disable_emergency_mode() {
    echo "🔄 Disabling Emergency Mode..."
    if [ -f .claude/settings.backup.json ]; then
        mv .claude/settings.backup.json .claude/settings.json
        echo "  ✅ Normal mode restored"
    else
        echo "  ⚠️  No backup found, manual configuration needed"
    fi
}
```

## 🛠️ Advanced Debugging

### Hook Interception

```bash
# Create hook interceptor for debugging
create_hook_interceptor() {
    cat > .claude/hooks/debug_interceptor.sh << 'EOF'
#!/bin/bash
# Hook interceptor for debugging
echo "[DEBUG] Hook intercepted at $(date)"
echo "[DEBUG] Script: $0"
echo "[DEBUG] Args: $*"
echo "[DEBUG] Working directory: $PWD"
echo "[DEBUG] Input size: $(wc -c | cat)"

# Save input to debug file
local input=$(cat)
echo "$input" > /tmp/hook_debug_input.json
echo "[DEBUG] Input saved to /tmp/hook_debug_input.json"

# Forward to actual hook
echo "$input" | bash "$1"
EOF

    chmod +x .claude/hooks/debug_interceptor.sh
    echo "🪝 Hook interceptor created"
}
```

### Network Debugging

```bash
# Debug network issues affecting Claude API calls
debug_network() {
    echo "🌐 Network Debugging for Claude API..."

    # Check DNS resolution
    echo "DNS Resolution:"
    nslookup claude.ai 2>/dev/null && echo "  ✅ claude.ai resolves" || echo "  ❌ DNS issue"

    # Check connectivity
    echo "Connectivity:"
    if command -v curl >/dev/null; then
        if curl -s --connect-timeout 5 https://claude.ai > /dev/null; then
            echo "  ✅ Can reach claude.ai"
        else
            echo "  ❌ Cannot reach claude.ai"
        fi
    fi

    # Check proxy settings
    echo "Proxy Settings:"
    echo "  HTTP_PROXY: ${HTTP_PROXY:-not set}"
    echo "  HTTPS_PROXY: ${HTTPS_PROXY:-not set}"
    echo "  NO_PROXY: ${NO_PROXY:-not set}"
}

debug_network
```

### Memory and Process Debugging

```bash
# Debug memory and process issues
debug_processes() {
    echo "🔍 Process and Memory Debugging..."

    # Check running processes related to Perfect21
    echo "Perfect21 processes:"
    ps aux | grep -E "(claude|perfect21|smart_agent)" | grep -v grep

    # Check memory usage
    echo "Memory usage:"
    free -h

    # Check disk space
    echo "Disk space:"
    df -h .

    # Check open files
    echo "Open files by current process:"
    lsof -p $$ 2>/dev/null | grep -E "\\.claude|perfect21"
}

debug_processes
```

### Trace Mode

```bash
# Enable comprehensive tracing
enable_trace_mode() {
    echo "🔬 Enabling Perfect21 Trace Mode..."

    # Set tracing environment
    export CLAUDE_ENHANCER_TRACE=true
    export CLAUDE_ENHANCER_DEBUG=true
    export PS4='+ [$(date +%H:%M:%S)] ${BASH_SOURCE##*/}:${LINENO}: '

    # Create trace log
    exec 19>/tmp/perfect21_trace.log
    BASH_XTRACEFD=19
    set -x

    echo "  ✅ Trace mode enabled"
    echo "  📝 Trace log: /tmp/perfect21_trace.log"
    echo "  💡 Run: 'set +x' to disable"
}

# Disable tracing
disable_trace_mode() {
    set +x
    exec 19>&-
    unset BASH_XTRACEFD
    echo "🔬 Trace mode disabled"
}
```

## 📞 Getting Help

### Automated Support Information

```bash
# Generate comprehensive support report
generate_support_report() {
    local report_file="perfect21_support_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
Perfect21 Support Report
Generated: $(date)
System: $(uname -a)
User: $(whoami)
Directory: $PWD

=== System Information ===
$(bash << 'EOSYS'
echo "OS: $(uname -s -r)"
echo "Shell: $SHELL"
echo "Git: $(git --version)"
echo "Python: $(python3 --version 2>/dev/null || echo "Not available")"
echo "Bash: $BASH_VERSION"
EOSYS
)

=== Perfect21 Status ===
$(bash << 'EOSTATUS'
echo "Settings file: $([ -f .claude/settings.json ] && echo "EXISTS" || echo "MISSING")"
echo "Install script: $([ -f .claude/install.sh ] && echo "EXISTS" || echo "MISSING")"
echo "Agent count: $(find .claude/agents -name "*.md" 2>/dev/null | wc -l)"
echo "Executable hooks: $(find .claude/hooks -name "*.sh" -executable 2>/dev/null | wc -l)"
echo "Git hooks: pre-commit=$([ -f .git/hooks/pre-commit ] && echo "YES" || echo "NO"), commit-msg=$([ -f .git/hooks/commit-msg ] && echo "YES" || echo "NO")"
EOSTATUS
)

=== Recent Logs ===
Agent Selection Log:
$(tail -10 /tmp/claude_agent_selection.log 2>/dev/null || echo "No log file found")

Error Log:
$(tail -5 /tmp/claude_error.log 2>/dev/null || echo "No error log found")

=== Configuration ===
$(cat .claude/settings.json 2>/dev/null || echo "Settings file not found")

=== Last Error ===
$(cat /tmp/perfect21_last_error 2>/dev/null || echo "No recent errors recorded")

EOF

    echo "📋 Support report generated: $report_file"
    echo "📧 Please include this file when reporting issues"
}

# Usage: generate_support_report
```

### Self-Diagnosis Checklist

```bash
# Run comprehensive self-diagnosis
self_diagnosis() {
    echo "🏥 Perfect21 Self-Diagnosis"
    echo "==========================="

    local issues=0

    # Check 1: Basic file structure
    echo "1. File Structure:"
    local required_files=(".claude/settings.json" ".claude/install.sh" ".claude/hooks/smart_agent_selector.sh")
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo "   ✅ $file"
        else
            echo "   ❌ $file (MISSING)"
            ((issues++))
        fi
    done

    # Check 2: Permissions
    echo "2. Permissions:"
    local exec_count=$(find .claude/hooks -name "*.sh" -executable 2>/dev/null | wc -l)
    local total_count=$(find .claude/hooks -name "*.sh" 2>/dev/null | wc -l)
    if [ "$exec_count" -eq "$total_count" ] && [ "$total_count" -gt 0 ]; then
        echo "   ✅ All scripts executable ($exec_count/$total_count)"
    else
        echo "   ❌ Permission issues ($exec_count/$total_count executable)"
        ((issues++))
    fi

    # Check 3: Git integration
    echo "3. Git Integration:"
    if git status &>/dev/null; then
        echo "   ✅ Valid git repository"
        if [ -f .git/hooks/pre-commit ]; then
            echo "   ✅ Pre-commit hook installed"
        else
            echo "   ❌ Pre-commit hook missing"
            ((issues++))
        fi
    else
        echo "   ❌ Not a git repository"
        ((issues++))
    fi

    # Check 4: Hook functionality
    echo "4. Hook Functionality:"
    if echo '{"prompt": "test"}' | timeout 10 bash .claude/hooks/smart_agent_selector.sh &>/dev/null; then
        echo "   ✅ Agent selector working"
    else
        echo "   ❌ Agent selector failed"
        ((issues++))
    fi

    # Summary
    echo "==========================="
    if [ $issues -eq 0 ]; then
        echo "🎉 Diagnosis complete: No issues found!"
    else
        echo "⚠️  Diagnosis complete: $issues issues found"
        echo ""
        echo "💡 Recommended fixes:"
        echo "   1. Run: bash .claude/install.sh"
        echo "   2. Run: chmod +x .claude/hooks/*.sh"
        echo "   3. Check TROUBLESHOOTING.md for specific solutions"
    fi
}

# Usage: self_diagnosis
```

---

## 📚 Additional Resources

- **Installation Guide**: [INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)
- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md)
- **Project Documentation**: [CLAUDE.md](./CLAUDE.md)
- **GitHub Issues**: Create an issue with your support report

## 🎯 Emergency Contacts

When all else fails:

1. **Generate Support Report**: Run `generate_support_report`
2. **Try Safe Mode**: Run `enable_emergency_mode`
3. **Complete Reset**: Run `reset_perfect21` (last resort)
4. **Manual Recovery**: Re-copy Perfect21 files and run install.sh

Remember: Perfect21 is designed to be robust and self-healing. Most issues can be resolved with a simple reinstall! 🚀