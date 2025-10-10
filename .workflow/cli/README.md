# CE CLI - Multi-Terminal Development Automation

A powerful CLI tool for managing multi-terminal development workflows with Claude Enhancer 5.0.

## Overview

CE CLI enables seamless parallel development across multiple terminal sessions, each working on independent feature branches with proper state management, conflict detection, and quality gates.

## Directory Structure

```
.workflow/cli/
├── commands/           # Command implementations
│   ├── start.sh       # Start new task/branch
│   ├── status.sh      # Show current state
│   ├── next.sh        # Advance to next phase
│   ├── publish.sh     # Publish/merge branch
│   ├── validate.sh    # Run validations
│   ├── merge.sh       # Merge branches
│   └── clean.sh       # Cleanup stale state
├── lib/               # Shared libraries
│   ├── common.sh      # Common utilities
│   ├── state_manager.sh    # State management
│   ├── branch_manager.sh   # Branch operations
│   └── phase_manager.sh    # Phase transitions
├── state/             # State management
│   ├── sessions/      # Terminal sessions
│   ├── branches/      # Branch metadata
│   ├── locks/         # File locks
│   └── global.state.yml    # Global state
├── templates/         # File templates
│   ├── session.template.yml
│   └── branch.template.yml
├── config.yml         # Configuration
├── install.sh         # Installation script
├── uninstall.sh       # Uninstallation script
└── README.md          # This file
```

## Installation

### Quick Install

```bash
cd /home/xx/dev/Claude\ Enhancer\ 5.0/.workflow/cli
./install.sh
```

This will:
1. Create necessary directories
2. Set proper permissions
3. Initialize global state
4. Create symlink in `~/.local/bin` (if available)

### Manual Setup

If you prefer manual setup:

```bash
# Add to PATH
export PATH="/home/xx/dev/Claude Enhancer 5.0/.workflow/cli:$PATH"

# Or create symlink
ln -s "/home/xx/dev/Claude Enhancer 5.0/.workflow/cli/ce.sh" /usr/local/bin/ce
```

## Usage

### Basic Commands

```bash
# Start a new task
ce start <feature-name>
# Example: ce start user-authentication

# Check current status
ce status

# Advance to next phase
ce next

# Run validations
ce validate

# Publish/merge branch
ce publish

# Clean stale state
ce clean
```

### Multi-Terminal Workflow

**Terminal 1 (t1):**
```bash
ce start login-feature
# Creates: feature/P3-t1-20251009-login-feature
# Work on login implementation...
ce next  # P3 → P4
ce validate
```

**Terminal 2 (t2) - Simultaneously:**
```bash
ce start signup-api
# Creates: feature/P3-t2-20251009-signup-api
# Work on signup API...
ce next  # P3 → P4
ce validate
```

**Terminal 3 (t3) - Code Review:**
```bash
ce status  # See all active branches
# Review t1 and t2 branches
ce merge t1 t2  # Merge compatible branches
```

### Advanced Usage

```bash
# Check specific terminal
ce status --terminal t2

# Force phase transition
ce next --force

# Dry-run publish
ce publish --dry-run

# Show detailed metrics
ce status --verbose

# Clean specific terminal
ce clean --terminal t1
```

## Configuration

Edit `.workflow/cli/config.yml` to customize settings:

```yaml
# Terminal settings
terminal:
  default_id: "t1"
  auto_detect: true
  idle_timeout: 3600

# Branch settings
branch:
  naming_pattern: "feature/<phase>-<terminal>-<timestamp>-<name>"
  max_active_per_terminal: 5
  auto_cleanup_merged: true

# State settings
state:
  auto_save: true
  save_interval: 60
  cleanup_interval: 3600
  max_stale_age: 86400
```

## State Management

### Session State

Each terminal session maintains its own state file:

```yaml
# .workflow/cli/state/sessions/t1.yml
terminal_id: "t1"
branch: "feature/P3-t1-20251009-login"
phase: "P3"
status: "active"
gates_passed: [00, 01, 02, 03]
metrics:
  commits: 5
  lines_added: 234
  tests_added: 12
```

### Branch Metadata

Each branch has metadata tracking:

```yaml
# .workflow/cli/state/branches/feature-P3-t1-20251009-login.yml
branch_name: "feature/P3-t1-20251009-login"
terminal_id: "t1"
phase: "P3"
created_at: "2025-10-09T10:00:00"
status: "active"
dependencies: []
conflicts: []
```

### Global State

System-wide tracking:

```yaml
# .workflow/cli/state/global.state.yml
active_terminals: ["t1", "t2", "t3"]
active_branches: ["feature/P3-t1-...", "feature/P4-t2-..."]
resource_locks:
  "src/auth/login.py": "t1"
  "api/signup.go": "t2"
statistics:
  total_sessions: 15
  total_branches: 47
  total_merges: 23
```

## Features

### Conflict Detection

CE CLI automatically detects:
- File-level conflicts (same file edited by multiple terminals)
- Branch dependency conflicts
- Phase incompatibility (can't merge P3 with P6)

### Quality Gates

Integrated with Claude Enhancer quality gates:
- Phase gate validation before transition
- Test coverage requirements
- Lint and security checks
- Performance budgets

### State Synchronization

- Auto-save every 60 seconds (configurable)
- Lock-free concurrent access
- Automatic cleanup of stale state
- Crash recovery

### Performance

- Cache-based performance (5-minute TTL)
- Parallel operations (4 workers)
- Retry mechanism (3 attempts)
- Efficient state queries

## Integration

### Git Hooks Integration

CE CLI integrates with existing Git hooks:
- Pre-commit: Phase validation
- Commit-msg: Branch tracking
- Pre-push: Quality gates

### GitHub CLI Integration

Automatically uses `gh` CLI when available:
- PR creation with proper metadata
- Branch protection status
- CI/CD status checks

## Troubleshooting

### Common Issues

**Issue: "Terminal not found"**
```bash
# Initialize terminal explicitly
ce start --terminal t1 <feature>
```

**Issue: "Branch already exists"**
```bash
# Use unique feature name or clean old branch
ce clean --terminal t1
git branch -D feature/P3-t1-...
```

**Issue: "State file corrupted"**
```bash
# Reset state (backup first!)
cp .workflow/cli/state/global.state.yml ~/backup.yml
ce clean --reset
```

### Debug Mode

Enable verbose logging:
```bash
export CE_DEBUG=1
ce status
```

### Manual State Inspection

```bash
# View global state
cat .workflow/cli/state/global.state.yml

# View terminal state
cat .workflow/cli/state/sessions/t1.yml

# View branch metadata
cat .workflow/cli/state/branches/feature-*.yml
```

## Uninstallation

```bash
./uninstall.sh
```

This will:
1. Prompt for state backup
2. Remove symlinks
3. Optionally clean state directories

## Best Practices

1. **One Task Per Terminal**: Keep terminal sessions focused on single tasks
2. **Frequent Status Checks**: Run `ce status` to avoid conflicts
3. **Regular Cleanup**: Run `ce clean` weekly to remove stale state
4. **Descriptive Names**: Use clear feature names (e.g., `user-auth-jwt` not `fix`)
5. **Phase Discipline**: Follow the 8-phase workflow strictly

## Examples

### Complete Workflow Example

```bash
# Terminal 1: Feature Development
ce start user-login-form
# ... implement login form ...
git add src/components/LoginForm.tsx
git commit -m "feat: add login form component"
ce next  # P3 → P4
# ... write tests ...
ce validate
ce publish

# Terminal 2: API Development
ce start login-api-endpoint
# ... implement API ...
git add api/auth/login.go
git commit -m "feat: add login endpoint"
ce next  # P3 → P4
# ... write tests ...
ce validate
ce publish

# Terminal 3: Integration
ce merge user-login-form login-api-endpoint
# ... resolve any conflicts ...
ce validate
ce publish --squash
```

## Contributing

This is part of Claude Enhancer 5.0. See main project documentation for contribution guidelines.

## License

Same as Claude Enhancer 5.0 project.

---

**CE CLI v1.0.0** - Multi-Terminal Development Made Easy
