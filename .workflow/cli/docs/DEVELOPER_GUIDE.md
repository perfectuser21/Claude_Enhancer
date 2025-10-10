# CE CLI Developer Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-09
**Target Audience**: Contributors, Maintainers, Developers

---

## 📖 Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Getting Started](#2-getting-started)
3. [Project Structure](#3-project-structure)
4. [Module Reference](#4-module-reference)
5. [Adding New Commands](#5-adding-new-commands)
6. [Testing](#6-testing)
7. [Code Style Guide](#7-code-style-guide)
8. [Contributing](#8-contributing)
9. [Debugging](#9-debugging)
10. [Release Process](#10-release-process)

---

## 1. Architecture Overview

### 1.1 System Architecture

CE CLI follows a **modular architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                   CE CLI (ce.sh)                     │
│                  Command Router                      │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│   Commands   │          │  Core Libs   │
│              │          │              │
│ • start.sh   │◄─────────┤ • common.sh  │
│ • status.sh  │          │ • branch_...│
│ • validate.sh│          │ • state_... │
│ • next.sh    │          │ • phase_... │
│ • publish.sh │          │ • gate_...  │
│ • merge.sh   │          │ • pr_...    │
│ • clean.sh   │          │ • git_ops.sh│
│ • pause.sh   │          │ • report.sh │
│ • resume.sh  │          └──────────────┘
│ • end.sh     │                 │
└──────────────┘                 │
        │                         │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  External Systems   │
        │                     │
        │ • Git              │
        │ • GitHub CLI (gh)  │
        │ • .workflow system │
        │ • Quality Gates    │
        └─────────────────────┘
```

### 1.2 Core Modules

| Module | Responsibility | File |
|--------|---------------|------|
| **Command Router** | Parse and dispatch commands | `ce.sh` |
| **Branch Manager** | Branch creation, naming, cleanup | `lib/branch_manager.sh` |
| **State Manager** | Multi-terminal state isolation | `lib/state_manager.sh` |
| **Phase Manager** | Phase transitions (P0-P7) | `lib/phase_manager.sh` |
| **Gate Integrator** | Quality gate validation | `lib/gate_integrator.sh` |
| **PR Automator** | Pull request automation | `lib/pr_automator.sh` |
| **Git Operations** | Git wrapper with retry logic | `lib/git_ops.sh` |
| **Report Generator** | Status and summary reports | `lib/report.sh` |

### 1.3 Data Flow

```
User Command
    ↓
ce.sh (Router)
    ↓
Command Script (e.g., start.sh)
    ↓
Core Libraries (branch_manager, state_manager, etc.)
    ↓
External Systems (Git, gh, .workflow)
    ↓
State Update
    ↓
Report to User
```

### 1.4 State Management

**State Storage Structure**:
```
.workflow/cli/state/
├── sessions/           # Per-terminal session state
│   ├── t1.state       # YAML: phase, branch, started_at
│   ├── t2.state
│   └── t3.state
├── branches/          # Per-branch metadata
│   ├── feature-auth-20251009.yml
│   └── feature-pay-20251009.yml
├── locks/             # File locks for safety
│   ├── t1.lock
│   └── t2.lock
└── global.state       # Global state (active sessions count)
```

**State File Format** (`sessions/t1.state`):
```yaml
terminal_id: t1
session_id: session-20251009-103000
phase: P3
branch: feature/user-auth-20251009
started_at: 2025-10-09T10:30:00Z
last_active: 2025-10-09T14:30:00Z
status: active
```

---

## 2. Getting Started

### 2.1 Development Environment Setup

```bash
# Clone the repository
cd /path/to/claude-enhancer-5.0

# Create development branch
git checkout -b dev/ce-cli-dev

# Install development dependencies
npm install --dev

# Install testing tools
sudo apt install bats  # Bash Automated Testing System
sudo apt install shellcheck  # Shell script linter
```

### 2.2 Running from Source

```bash
# Make script executable
chmod +x .workflow/cli/ce.sh

# Run directly (no install)
./.workflow/cli/ce.sh --version

# Or create local alias
alias ce-dev="./.workflow/cli/ce.sh"
ce-dev --help
```

### 2.3 Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/add-new-command

# 2. Make changes
vim .workflow/cli/commands/mycommand.sh

# 3. Run linter
shellcheck .workflow/cli/commands/mycommand.sh

# 4. Run tests
bats test/unit/test_mycommand.bats

# 5. Test manually
./.workflow/cli/ce.sh mycommand

# 6. Commit
git commit -m "feat: add mycommand"

# 7. Create PR
gh pr create --title "feat: add mycommand"
```

---

## 3. Project Structure

### 3.1 Directory Layout

```
.workflow/cli/
├── ce.sh                      # Main entry point (200 lines)
├── commands/                  # Command implementations
│   ├── start.sh              # ce start (150 lines)
│   ├── status.sh             # ce status (200 lines)
│   ├── validate.sh           # ce validate (300 lines)
│   ├── next.sh               # ce next (250 lines)
│   ├── publish.sh            # ce publish (350 lines)
│   ├── merge.sh              # ce merge (400 lines)
│   └── clean.sh              # ce clean (250 lines)
├── lib/                      # Shared libraries
│   ├── common.sh             # Common functions (200 lines)
│   ├── branch_manager.sh     # Branch management (150 lines)
│   ├── state_manager.sh      # State management (200 lines)
│   ├── phase_manager.sh      # Phase management (150 lines)
│   ├── gate_integrator.sh    # Gate integration (200 lines)
│   ├── pr_automator.sh       # PR automation (250 lines)
│   ├── git_ops.sh            # Git operations (200 lines)
│   └── report.sh             # Report generation (250 lines)
├── state/                    # Runtime state (created at runtime)
│   ├── sessions/
│   ├── branches/
│   ├── locks/
│   └── global.state
├── templates/                # Templates
│   ├── pr_description.md     # PR template
│   ├── session.yml           # Session state template
│   └── branch.yml            # Branch metadata template
├── config/                   # Configuration
│   └── config.yml            # Default configuration
├── docs/                     # Documentation
│   ├── USER_GUIDE.md         # User documentation
│   ├── DEVELOPER_GUIDE.md    # This file
│   └── API_REFERENCE.md      # API documentation
├── install.sh                # Installation script
└── uninstall.sh              # Uninstall script
```

### 3.2 File Naming Conventions

- **Commands**: `commands/<verb>.sh` (e.g., `start.sh`, `validate.sh`)
- **Libraries**: `lib/<module>_<purpose>.sh` (e.g., `branch_manager.sh`)
- **Templates**: `templates/<name>.<ext>` (e.g., `pr_description.md`)
- **Tests**: `test/unit/test_<module>.bats`

### 3.3 Coding Standards

**Shell Script Header Template**:
```bash
#!/bin/bash
# <filename>.sh - <brief description>
#
# Usage: <usage example>
#
# Author: Claude Enhancer Team
# Version: 1.0.0
# Last Updated: 2025-10-09

set -euo pipefail  # Strict mode

# Source dependencies
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"
```

---

## 4. Module Reference

### 4.1 Branch Manager (`lib/branch_manager.sh`)

**Purpose**: Handle all branch-related operations.

**Key Functions**:

#### `ce_branch_create()`

Creates a new feature branch with proper naming.

```bash
# Function signature
ce_branch_create() {
    local feature_name="$1"
    local from_branch="${2:-main}"
    local terminal_id="${CE_TERMINAL_ID:-t1}"

    # Generate branch name: feature/<name>-<date>-<terminal>
    local branch_name="feature/${feature_name}-$(date +%Y%m%d)-${terminal_id}"

    # Create branch
    git checkout -b "$branch_name" "$from_branch"

    # Store metadata
    ce_branch_save_metadata "$branch_name"
}
```

**Usage**:
```bash
source lib/branch_manager.sh
ce_branch_create "user-auth" "main"
```

---

#### `ce_branch_get_current()`

Gets the current branch name.

```bash
ce_branch_get_current() {
    git branch --show-current
}
```

---

#### `ce_branch_delete()`

Safely deletes a branch.

```bash
ce_branch_delete() {
    local branch_name="$1"
    local force="${2:-false}"

    # Check if merged
    if ! ce_branch_is_merged "$branch_name" && [[ "$force" != "true" ]]; then
        echo_error "Branch not merged. Use --force to delete anyway."
        return 1
    fi

    git branch -d "$branch_name"
}
```

---

#### `ce_branch_list_merged()`

Lists all merged branches.

```bash
ce_branch_list_merged() {
    local target_branch="${1:-main}"
    git branch --merged "$target_branch" | grep -v "^\*" | grep -v "main"
}
```

---

### 4.2 State Manager (`lib/state_manager.sh`)

**Purpose**: Manage multi-terminal session state.

**Key Functions**:

#### `ce_state_save()`

Saves current state to session file.

```bash
ce_state_save() {
    local terminal_id="${CE_TERMINAL_ID:-t1}"
    local state_file="${STATE_DIR}/sessions/${terminal_id}.state"

    cat > "$state_file" << EOF
terminal_id: ${terminal_id}
session_id: ${SESSION_ID}
phase: ${CURRENT_PHASE}
branch: $(git branch --show-current)
started_at: ${STARTED_AT}
last_active: $(date -u +%Y-%m-%dT%H:%M:%SZ)
status: active
EOF
}
```

---

#### `ce_state_load()`

Loads state from session file.

```bash
ce_state_load() {
    local terminal_id="${CE_TERMINAL_ID:-t1}"
    local state_file="${STATE_DIR}/sessions/${terminal_id}.state"

    if [[ ! -f "$state_file" ]]; then
        echo_warning "No saved state for terminal $terminal_id"
        return 1
    fi

    # Parse YAML
    CURRENT_PHASE=$(grep "^phase:" "$state_file" | cut -d' ' -f2)
    SESSION_ID=$(grep "^session_id:" "$state_file" | cut -d' ' -f2)
    # ... etc
}
```

---

#### `ce_state_lock()`

Acquires file lock for safe concurrent access.

```bash
ce_state_lock() {
    local terminal_id="${CE_TERMINAL_ID:-t1}"
    local lock_file="${STATE_DIR}/locks/${terminal_id}.lock"

    # Create lock with timeout
    exec 200>"$lock_file"
    flock -x -w 10 200 || {
        echo_error "Could not acquire lock (timeout)"
        return 1
    }
}
```

---

#### `ce_state_unlock()`

Releases file lock.

```bash
ce_state_unlock() {
    flock -u 200
}
```

---

### 4.3 Phase Manager (`lib/phase_manager.sh`)

**Purpose**: Handle phase transitions (P0-P7).

**Key Functions**:

#### `ce_phase_get_current()`

Gets current phase from state.

```bash
ce_phase_get_current() {
    if [[ -f "$PHASE_FILE" ]]; then
        cat "$PHASE_FILE" | tr -d '\n\r'
    else
        echo ""
    fi
}
```

---

#### `ce_phase_set()`

Sets current phase.

```bash
ce_phase_set() {
    local phase="$1"

    # Validate phase
    if ! ce_phase_validate "$phase"; then
        echo_error "Invalid phase: $phase"
        return 1
    fi

    # Update .phase/current
    echo "$phase" > "$PHASE_FILE"

    # Update .workflow/ACTIVE
    cat > "$ACTIVE_FILE" << EOF
phase: $phase
ticket: exec-$(date +%Y%m%d-%H%M%S)
started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

    # Update session state
    ce_state_save
}
```

---

#### `ce_phase_next()`

Advances to next phase.

```bash
ce_phase_next() {
    local current=$(ce_phase_get_current)
    local next=$(ce_phase_calculate_next "$current")

    if [[ -z "$next" ]]; then
        echo_error "Already at final phase (P7)"
        return 1
    fi

    ce_phase_set "$next"
}
```

---

#### `ce_phase_get_requirements()`

Gets requirements for a specific phase.

```bash
ce_phase_get_requirements() {
    local phase="$1"

    case "$phase" in
        P0)
            cat << 'EOF'
• Create feasibility analysis document
• Validate at least 2 key technical points
• Assess technical/business/time risks
• Reach clear conclusion (GO/NO-GO/NEEDS-DECISION)
EOF
            ;;
        P1)
            cat << 'EOF'
• Create docs/PLAN.md
• At least 10 task items
• Affected files list
• Rollback plan
EOF
            ;;
        # ... other phases
    esac
}
```

---

### 4.4 Gate Integrator (`lib/gate_integrator.sh`)

**Purpose**: Integrate with existing quality gate system.

**Key Functions**:

#### `ce_gate_validate()`

Runs quality gate validation.

```bash
ce_gate_validate() {
    local phase="$1"
    local mode="${2:-parallel}"

    case "$mode" in
        full)
            bash .workflow/lib/final_gate.sh --full
            ;;
        quick)
            bash .workflow/lib/final_gate.sh --quick
            ;;
        incremental)
            ce_gate_validate_incremental "$phase"
            ;;
        parallel)
            ce_gate_validate_parallel "$phase"
            ;;
    esac
}
```

---

#### `ce_gate_validate_parallel()`

Runs validation checks in parallel.

```bash
ce_gate_validate_parallel() {
    local phase="$1"

    # Run checks in parallel
    {
        ce_gate_check_paths &
        ce_gate_check_produces &
        ce_gate_check_security &
        ce_gate_check_quality &
        wait
    } || return 1
}
```

---

### 4.5 PR Automator (`lib/pr_automator.sh`)

**Purpose**: Automate pull request creation and management.

**Key Functions**:

#### `ce_pr_create()`

Creates a pull request.

```bash
ce_pr_create() {
    local title="$1"
    local body="$2"
    local draft="${3:-false}"

    # Try gh CLI first
    if command -v gh &> /dev/null; then
        local draft_flag=""
        [[ "$draft" == "true" ]] && draft_flag="--draft"

        gh pr create \
            --title "$title" \
            --body "$body" \
            $draft_flag
    else
        # Fallback to web
        ce_pr_create_web "$title" "$body"
    fi
}
```

---

#### `ce_pr_generate_description()`

Generates PR description from template.

```bash
ce_pr_generate_description() {
    local template="${PR_TEMPLATE:-templates/pr_description.md}"
    local feature_name="$1"

    # Replace placeholders
    sed -e "s/\[FEATURE_NAME\]/$feature_name/g" \
        -e "s/\[SCORE\]/$(ce_quality_score)/g" \
        -e "s/\[COVERAGE\]/$(ce_test_coverage)/g" \
        "$template"
}
```

---

### 4.6 Git Operations (`lib/git_ops.sh`)

**Purpose**: Wrap Git commands with error handling and retry logic.

**Key Functions**:

#### `ce_git_safe_push()`

Pushes with retry logic.

```bash
ce_git_safe_push() {
    local branch="${1:-$(git branch --show-current)}"
    local max_retries=3
    local retry_delay=2

    for ((i=1; i<=max_retries; i++)); do
        if git push origin "$branch"; then
            return 0
        fi

        if [[ $i -lt $max_retries ]]; then
            echo_warning "Push failed, retrying in ${retry_delay}s... ($i/$max_retries)"
            sleep $retry_delay
        fi
    done

    echo_error "Push failed after $max_retries attempts"
    return 1
}
```

---

### 4.7 Report Generator (`lib/report.sh`)

**Purpose**: Generate status reports and summaries.

**Key Functions**:

#### `ce_report_status()`

Generates status report.

```bash
ce_report_status() {
    local verbose="${1:-false}"

    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  📊 Claude Enhancer Status Report${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo ""

    # Basic info
    ce_report_basic_info

    # Workflow progress
    ce_report_workflow_progress

    # Quality gates
    ce_report_quality_gates

    # Current phase requirements
    if [[ "$verbose" == "true" ]]; then
        ce_report_phase_details
    fi

    # Next steps
    ce_report_next_steps
}
```

---

## 5. Adding New Commands

### 5.1 Command Template

Create `commands/mycommand.sh`:

```bash
#!/bin/bash
# mycommand.sh - Brief description
#
# Usage: ce mycommand [options]

set -euo pipefail

# Source dependencies
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"
source "${SCRIPT_DIR}/../lib/state_manager.sh"

# Main command function
cmd_mycommand() {
    local arg1="$1"
    local option="${2:-default}"

    # Validate arguments
    if [[ -z "$arg1" ]]; then
        echo_error "Usage: ce mycommand <arg1> [option]"
        return 1
    fi

    # Load state
    ce_state_lock
    ce_state_load

    # Do work
    echo_info "Executing mycommand with $arg1..."

    # Implementation here
    # ...

    # Save state
    ce_state_save
    ce_state_unlock

    echo_success "mycommand completed!"
}

# Run command if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cmd_mycommand "$@"
fi
```

### 5.2 Register Command

Edit `ce.sh` to add new command:

```bash
# In ce.sh, add to command routing
case "$COMMAND" in
    start) source "${CLI_DIR}/commands/start.sh"; cmd_start "$@" ;;
    status) source "${CLI_DIR}/commands/status.sh"; cmd_status "$@" ;;
    # ... existing commands ...
    mycommand) source "${CLI_DIR}/commands/mycommand.sh"; cmd_mycommand "$@" ;;  # NEW
    *)
        echo_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
```

### 5.3 Add Help Text

Add help text in `ce.sh`:

```bash
show_help() {
    cat << 'EOF'
Usage: ce <command> [options]

Commands:
  start <feature>      Start new feature
  status               Show current status
  # ... existing commands ...
  mycommand <arg>      Description of mycommand  # NEW

Options:
  --help, -h           Show this help
  --version, -v        Show version
EOF
}
```

### 5.4 Create Tests

Create `test/unit/test_mycommand.bats`:

```bash
#!/usr/bin/env bats

setup() {
    # Setup test environment
    export CE_TERMINAL_ID=test
    source .workflow/cli/commands/mycommand.sh
}

teardown() {
    # Cleanup
    rm -rf .workflow/cli/state/sessions/test.state
}

@test "mycommand: basic functionality" {
    run cmd_mycommand "test-arg"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "completed" ]]
}

@test "mycommand: missing argument" {
    run cmd_mycommand ""
    [ "$status" -eq 1 ]
    [[ "$output" =~ "Usage:" ]]
}
```

---

## 6. Testing

### 6.1 Test Structure

```
test/
├── unit/                      # Unit tests (BATS)
│   ├── test_branch_manager.bats
│   ├── test_state_manager.bats
│   └── test_phase_manager.bats
├── integration/               # Integration tests
│   ├── test_full_workflow.bats
│   └── test_multi_terminal.bats
├── e2e/                      # End-to-end tests
│   └── test_complete_feature.sh
└── helpers/                  # Test helpers
    └── test_helpers.bash
```

### 6.2 Running Tests

```bash
# Run all unit tests
bats test/unit/*.bats

# Run specific test file
bats test/unit/test_branch_manager.bats

# Run with verbose output
bats -t test/unit/*.bats

# Run integration tests
bats test/integration/*.bats

# Run all tests
bats test/**/*.bats
```

### 6.3 Writing Good Tests

**Test Naming**:
```bash
@test "module_name: what_it_should_do" {
    # Test implementation
}
```

**Example**:
```bash
@test "branch_manager: creates branch with correct naming" {
    run ce_branch_create "my-feature"

    [ "$status" -eq 0 ]
    [[ "$(git branch --show-current)" =~ ^feature/my-feature-[0-9]{8}-t1$ ]]
}

@test "state_manager: saves and loads state correctly" {
    # Setup
    export CE_TERMINAL_ID=test
    CURRENT_PHASE=P3

    # Save
    ce_state_save

    # Modify
    CURRENT_PHASE=""

    # Load
    ce_state_load

    # Assert
    [ "$CURRENT_PHASE" = "P3" ]
}
```

---

## 7. Code Style Guide

### 7.1 Shell Script Best Practices

**Use Strict Mode**:
```bash
set -euo pipefail
# -e: Exit on error
# -u: Exit on undefined variable
# -o pipefail: Exit on pipe failure
```

**Declare Constants**:
```bash
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly STATE_DIR="${SCRIPT_DIR}/../state"
```

**Use Local Variables**:
```bash
my_function() {
    local arg1="$1"
    local result=""

    # ... function logic
}
```

**Quote Variables**:
```bash
# Good
echo "$MY_VAR"
rm -rf "$DIR_PATH"

# Bad
echo $MY_VAR
rm -rf $DIR_PATH
```

**Error Handling**:
```bash
if ! command_that_might_fail; then
    echo_error "Command failed"
    return 1
fi
```

---

### 7.2 Naming Conventions

**Functions**: `lowercase_with_underscores`
```bash
ce_branch_create() { ... }
ce_state_save() { ... }
```

**Constants**: `UPPERCASE_WITH_UNDERSCORES`
```bash
readonly MAX_RETRIES=3
readonly STATE_DIR="/path/to/state"
```

**Variables**: `lowercase_with_underscores`
```bash
local feature_name="user-auth"
local current_phase="P3"
```

---

### 7.3 Documentation

**Function Documentation**:
```bash
# Description: Creates a new feature branch
# Arguments:
#   $1 - feature_name: Name of the feature
#   $2 - from_branch: Base branch (default: main)
# Returns:
#   0 - Success
#   1 - Failure
# Example:
#   ce_branch_create "user-auth" "main"
ce_branch_create() {
    # Implementation
}
```

---

## 8. Contributing

### 8.1 Contribution Guidelines

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/my-feature`
3. **Follow code style guide**
4. **Add tests** for new functionality
5. **Update documentation**
6. **Run linter**: `shellcheck`
7. **Run tests**: `bats test/unit/*.bats`
8. **Commit with conventional commits**: `feat: add new command`
9. **Create pull request**

---

### 8.2 Conventional Commits

Format: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```bash
git commit -m "feat(commands): add pause command"
git commit -m "fix(state): resolve lock timeout issue"
git commit -m "docs(api): update function signatures"
```

---

## 9. Debugging

### 9.1 Debug Mode

```bash
# Enable debug output
export CE_DEBUG=1
ce status

# Trace mode (shows all commands)
bash -x .workflow/cli/ce.sh status
```

### 9.2 Logging

```bash
# Check logs
tail -f .workflow/logs/ce.log

# Verbose mode
ce validate --verbose --debug
```

### 9.3 Common Debug Scenarios

**State Issues**:
```bash
# Check session state
cat .workflow/cli/state/sessions/t1.state

# Check locks
ls -la .workflow/cli/state/locks/
```

**Branch Issues**:
```bash
# Check current branch
git branch --show-current

# Check branch metadata
cat .workflow/cli/state/branches/*.yml
```

---

## 10. Release Process

### 10.1 Versioning

Follow **Semantic Versioning** (semver.org):
- `MAJOR.MINOR.PATCH`
- `1.0.0` → `1.0.1` (patch)
- `1.0.0` → `1.1.0` (minor)
- `1.0.0` → `2.0.0` (major)

### 10.2 Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped in `ce.sh`
- [ ] Git tag created: `git tag v1.0.1`
- [ ] Tag pushed: `git push --tags`
- [ ] Release notes created

---

## Related Documentation

- [User Guide](./USER_GUIDE.md) - End user documentation
- [API Reference](./API_REFERENCE.md) - Function-level API docs
- [Architecture](../../../docs/P1_CE_COMMAND_ARCHITECTURE.md) - System architecture

---

**Last Updated**: 2025-10-09
**Version**: 1.0.0
**Status**: ⚠️ TEMPLATE - Implementation pending (P3)

---

*Generated by Claude Code - CE CLI Development Team*
