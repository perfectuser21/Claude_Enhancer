# CE CLI API Reference

**Version**: 1.0.0
**Last Updated**: 2025-10-09
**Target Audience**: Developers, Contributors

---

## 📖 Table of Contents

1. [Overview](#1-overview)
2. [Core Functions](#2-core-functions)
3. [Branch Management](#3-branch-management)
4. [State Management](#4-state-management)
5. [Phase Management](#5-phase-management)
6. [Gate Integration](#6-gate-integration)
7. [PR Automation](#7-pr-automation)
8. [Git Operations](#8-git-operations)
9. [Report Generation](#9-report-generation)
10. [Utility Functions](#10-utility-functions)

---

## 1. Overview

This document provides detailed API documentation for all functions in CE CLI.

### Function Naming Convention

```
ce_<module>_<action>()

Examples:
- ce_branch_create()
- ce_state_save()
- ce_phase_next()
```

### Return Codes

All functions follow standard Unix exit codes:
- `0` - Success
- `1` - General error
- `2` - Invalid arguments
- `3` - Permission denied
- `4` - Resource not found
- `5` - Resource already exists
- `6` - Timeout

---

## 2. Core Functions

### `ce_init()`

**Module**: `lib/common.sh`
**Description**: Initializes CE CLI environment.

```bash
ce_init()
```

**Returns**:
- `0` - Success
- `1` - Initialization failed

**Side Effects**:
- Creates state directories
- Sets up environment variables
- Initializes logging

**Example**:
```bash
ce_init || exit 1
```

---

### `ce_cleanup()`

**Module**: `lib/common.sh`
**Description**: Cleans up temporary files and releases locks.

```bash
ce_cleanup()
```

**Returns**:
- `0` - Success

**Side Effects**:
- Removes temporary files
- Releases file locks
- Closes log files

**Example**:
```bash
trap ce_cleanup EXIT
```

---

### `echo_success()`

**Module**: `lib/common.sh`
**Description**: Prints success message with green checkmark.

```bash
echo_success <message>
```

**Arguments**:
- `$1` (string) - Message to display

**Example**:
```bash
echo_success "Operation completed!"
# Output: ✅ Operation completed!
```

---

### `echo_error()`

**Module**: `lib/common.sh`
**Description**: Prints error message with red X.

```bash
echo_error <message>
```

**Arguments**:
- `$1` (string) - Error message

**Example**:
```bash
echo_error "Operation failed!"
# Output: ❌ Operation failed!
```

---

### `echo_warning()`

**Module**: `lib/common.sh`
**Description**: Prints warning message with yellow warning sign.

```bash
echo_warning <message>
```

**Arguments**:
- `$1` (string) - Warning message

**Example**:
```bash
echo_warning "This action is irreversible"
# Output: ⚠️  This action is irreversible
```

---

### `echo_info()`

**Module**: `lib/common.sh`
**Description**: Prints info message with blue info icon.

```bash
echo_info <message>
```

**Arguments**:
- `$1` (string) - Info message

**Example**:
```bash
echo_info "Processing request..."
# Output: ℹ️  Processing request...
```

---

## 3. Branch Management

### `ce_branch_create()`

**Module**: `lib/branch_manager.sh`
**Description**: Creates a new feature branch with proper naming convention.

```bash
ce_branch_create <feature_name> [from_branch] [terminal_id]
```

**Arguments**:
- `$1` (string, required) - Feature name (kebab-case)
- `$2` (string, optional) - Base branch (default: "main")
- `$3` (string, optional) - Terminal ID (default: $CE_TERMINAL_ID or "t1")

**Returns**:
- `0` - Branch created successfully
- `1` - Invalid feature name
- `2` - Branch already exists
- `3` - Base branch not found

**Branch Naming Format**:
```
feature/<feature-name>-YYYYMMDD-<terminal-id>

Example: feature/user-auth-20251009-t1
```

**Side Effects**:
- Creates Git branch
- Saves branch metadata to `state/branches/<branch>.yml`
- Updates session state

**Example**:
```bash
ce_branch_create "user-authentication" "main" "t1"
# Creates: feature/user-authentication-20251009-t1
```

---

### `ce_branch_get_current()`

**Module**: `lib/branch_manager.sh`
**Description**: Gets the name of the current branch.

```bash
ce_branch_get_current()
```

**Returns**:
- `0` - Success

**Output**:
- Stdout: Current branch name

**Example**:
```bash
CURRENT_BRANCH=$(ce_branch_get_current)
echo "On branch: $CURRENT_BRANCH"
# Output: On branch: feature/user-auth-20251009-t1
```

---

### `ce_branch_exists()`

**Module**: `lib/branch_manager.sh`
**Description**: Checks if a branch exists.

```bash
ce_branch_exists <branch_name>
```

**Arguments**:
- `$1` (string, required) - Branch name

**Returns**:
- `0` - Branch exists
- `1` - Branch does not exist

**Example**:
```bash
if ce_branch_exists "feature/user-auth-20251009-t1"; then
    echo "Branch exists"
fi
```

---

### `ce_branch_is_merged()`

**Module**: `lib/branch_manager.sh`
**Description**: Checks if a branch has been merged into target branch.

```bash
ce_branch_is_merged <branch_name> [target_branch]
```

**Arguments**:
- `$1` (string, required) - Branch name to check
- `$2` (string, optional) - Target branch (default: "main")

**Returns**:
- `0` - Branch is merged
- `1` - Branch is not merged

**Example**:
```bash
if ce_branch_is_merged "feature/old-feature" "main"; then
    ce_branch_delete "feature/old-feature"
fi
```

---

### `ce_branch_delete()`

**Module**: `lib/branch_manager.sh`
**Description**: Deletes a branch (local and optionally remote).

```bash
ce_branch_delete <branch_name> [force] [delete_remote]
```

**Arguments**:
- `$1` (string, required) - Branch name
- `$2` (bool, optional) - Force delete (default: false)
- `$3` (bool, optional) - Also delete remote (default: false)

**Returns**:
- `0` - Branch deleted successfully
- `1` - Branch not merged (and force=false)
- `2` - Branch not found

**Side Effects**:
- Deletes local branch
- Optionally deletes remote branch
- Removes branch metadata file

**Example**:
```bash
# Safe delete (only if merged)
ce_branch_delete "feature/old-feature"

# Force delete
ce_branch_delete "feature/abandoned" "true"

# Delete local and remote
ce_branch_delete "feature/completed" "true" "true"
```

---

### `ce_branch_list_merged()`

**Module**: `lib/branch_manager.sh`
**Description**: Lists all merged feature branches.

```bash
ce_branch_list_merged [target_branch]
```

**Arguments**:
- `$1` (string, optional) - Target branch (default: "main")

**Returns**:
- `0` - Success

**Output**:
- Stdout: List of merged branch names (one per line)

**Example**:
```bash
ce_branch_list_merged "main" | while read -r branch; do
    echo "Cleaning up: $branch"
    ce_branch_delete "$branch"
done
```

---

### `ce_branch_save_metadata()`

**Module**: `lib/branch_manager.sh`
**Description**: Saves branch metadata to state file.

```bash
ce_branch_save_metadata <branch_name>
```

**Arguments**:
- `$1` (string, required) - Branch name

**Returns**:
- `0` - Success

**Metadata File Format** (`state/branches/<branch>.yml`):
```yaml
branch_name: feature/user-auth-20251009-t1
feature_name: user-auth
created_at: 2025-10-09T10:30:00Z
created_by: terminal_t1
base_branch: main
status: active
```

**Example**:
```bash
ce_branch_save_metadata "feature/user-auth-20251009-t1"
```

---

## 4. State Management

### `ce_state_save()`

**Module**: `lib/state_manager.sh`
**Description**: Saves current session state to state file.

```bash
ce_state_save()
```

**Returns**:
- `0` - Success
- `1` - Failed to acquire lock

**Side Effects**:
- Creates/updates `state/sessions/<terminal_id>.state`
- Updates `last_active` timestamp

**State File Format**:
```yaml
terminal_id: t1
session_id: session-20251009-103000
phase: P3
branch: feature/user-auth-20251009-t1
started_at: 2025-10-09T10:30:00Z
last_active: 2025-10-09T14:30:00Z
status: active
```

**Example**:
```bash
CURRENT_PHASE=P3
ce_state_save
```

---

### `ce_state_load()`

**Module**: `lib/state_manager.sh`
**Description**: Loads session state from state file.

```bash
ce_state_load()
```

**Returns**:
- `0` - State loaded successfully
- `1` - No saved state found

**Side Effects**:
- Sets environment variables: `CURRENT_PHASE`, `SESSION_ID`, etc.

**Example**:
```bash
ce_state_load
echo "Current phase: $CURRENT_PHASE"
```

---

### `ce_state_lock()`

**Module**: `lib/state_manager.sh`
**Description**: Acquires file lock for safe concurrent access.

```bash
ce_state_lock [timeout]
```

**Arguments**:
- `$1` (int, optional) - Timeout in seconds (default: 10)

**Returns**:
- `0` - Lock acquired
- `1` - Timeout (lock not acquired)

**Side Effects**:
- Creates lock file: `state/locks/<terminal_id>.lock`
- Blocks until lock acquired or timeout

**Example**:
```bash
if ce_state_lock 10; then
    # Critical section
    ce_state_save
    ce_state_unlock
else
    echo_error "Could not acquire lock"
fi
```

---

### `ce_state_unlock()`

**Module**: `lib/state_manager.sh`
**Description**: Releases file lock.

```bash
ce_state_unlock()
```

**Returns**:
- `0` - Success

**Example**:
```bash
ce_state_lock
# ... do work ...
ce_state_unlock
```

---

### `ce_state_exists()`

**Module**: `lib/state_manager.sh`
**Description**: Checks if state file exists for terminal.

```bash
ce_state_exists [terminal_id]
```

**Arguments**:
- `$1` (string, optional) - Terminal ID (default: $CE_TERMINAL_ID)

**Returns**:
- `0` - State exists
- `1` - State does not exist

**Example**:
```bash
if ce_state_exists "t1"; then
    echo "Terminal t1 has active session"
fi
```

---

### `ce_state_list_active()`

**Module**: `lib/state_manager.sh`
**Description**: Lists all active terminal sessions.

```bash
ce_state_list_active()
```

**Returns**:
- `0` - Success

**Output**:
- Stdout: List of terminal IDs with active sessions (one per line)

**Example**:
```bash
ce_state_list_active | while read -r tid; do
    echo "Active terminal: $tid"
done
```

---

### `ce_state_cleanup_stale()`

**Module**: `lib/state_manager.sh`
**Description**: Removes stale state files and locks.

```bash
ce_state_cleanup_stale [max_age_hours]
```

**Arguments**:
- `$1` (int, optional) - Max age in hours (default: 24)

**Returns**:
- `0` - Success

**Side Effects**:
- Deletes state files older than max_age
- Removes associated lock files

**Example**:
```bash
# Clean up sessions older than 7 days
ce_state_cleanup_stale 168
```

---

## 5. Phase Management

### `ce_phase_get_current()`

**Module**: `lib/phase_manager.sh`
**Description**: Gets current phase from state.

```bash
ce_phase_get_current()
```

**Returns**:
- `0` - Success

**Output**:
- Stdout: Current phase (P0-P7) or empty string if not set

**Example**:
```bash
PHASE=$(ce_phase_get_current)
echo "Current phase: $PHASE"
```

---

### `ce_phase_set()`

**Module**: `lib/phase_manager.sh`
**Description**: Sets current phase.

```bash
ce_phase_set <phase>
```

**Arguments**:
- `$1` (string, required) - Phase (P0-P7)

**Returns**:
- `0` - Phase set successfully
- `1` - Invalid phase

**Side Effects**:
- Updates `.phase/current`
- Updates `.workflow/ACTIVE`
- Saves session state

**Example**:
```bash
ce_phase_set "P3"
```

---

### `ce_phase_validate()`

**Module**: `lib/phase_manager.sh`
**Description**: Validates phase name format.

```bash
ce_phase_validate <phase>
```

**Arguments**:
- `$1` (string, required) - Phase to validate

**Returns**:
- `0` - Valid phase
- `1` - Invalid phase

**Valid Phases**: P0, P1, P2, P3, P4, P5, P6, P7

**Example**:
```bash
if ce_phase_validate "P3"; then
    echo "Valid phase"
fi
```

---

### `ce_phase_next()`

**Module**: `lib/phase_manager.sh`
**Description**: Advances to next phase.

```bash
ce_phase_next()
```

**Returns**:
- `0` - Advanced to next phase
- `1` - Already at final phase (P7)

**Side Effects**:
- Updates current phase
- Saves state

**Example**:
```bash
ce_phase_next
echo "Advanced to: $(ce_phase_get_current)"
```

---

### `ce_phase_calculate_next()`

**Module**: `lib/phase_manager.sh`
**Description**: Calculates the next phase without changing state.

```bash
ce_phase_calculate_next <current_phase>
```

**Arguments**:
- `$1` (string, required) - Current phase

**Returns**:
- `0` - Success

**Output**:
- Stdout: Next phase or empty string if at P7

**Example**:
```bash
NEXT=$(ce_phase_calculate_next "P3")
echo "Next phase will be: $NEXT"
# Output: Next phase will be: P4
```

---

### `ce_phase_get_info()`

**Module**: `lib/phase_manager.sh`
**Description**: Gets human-readable phase information.

```bash
ce_phase_get_info <phase>
```

**Arguments**:
- `$1` (string, required) - Phase (P0-P7)

**Returns**:
- `0` - Success

**Output**:
- Stdout: Phase name and description

**Example**:
```bash
INFO=$(ce_phase_get_info "P3")
echo "$INFO"
# Output: Implementation (编码开发)
```

---

### `ce_phase_get_requirements()`

**Module**: `lib/phase_manager.sh`
**Description**: Gets requirements for a specific phase.

```bash
ce_phase_get_requirements <phase>
```

**Arguments**:
- `$1` (string, required) - Phase (P0-P7)

**Returns**:
- `0` - Success

**Output**:
- Stdout: Multi-line list of requirements

**Example**:
```bash
ce_phase_get_requirements "P1"
# Output:
# • Create docs/PLAN.md
# • At least 10 task items
# • Affected files list
# • Rollback plan
```

---

### `ce_phase_is_completed()`

**Module**: `lib/phase_manager.sh`
**Description**: Checks if a phase has been completed (gate passed).

```bash
ce_phase_is_completed <phase>
```

**Arguments**:
- `$1` (string, required) - Phase (P0-P7)

**Returns**:
- `0` - Phase completed (gate file exists)
- `1` - Phase not completed

**Example**:
```bash
if ce_phase_is_completed "P3"; then
    echo "P3 implementation complete"
fi
```

---

### `ce_phase_get_completed_list()`

**Module**: `lib/phase_manager.sh`
**Description**: Gets list of all completed phases.

```bash
ce_phase_get_completed_list()
```

**Returns**:
- `0` - Success

**Output**:
- Stdout: Space-separated list of completed phases

**Example**:
```bash
COMPLETED=$(ce_phase_get_completed_list)
echo "Completed phases: $COMPLETED"
# Output: Completed phases: P0 P1 P2
```

---

## 6. Gate Integration

### `ce_gate_validate()`

**Module**: `lib/gate_integrator.sh`
**Description**: Runs quality gate validation for current phase.

```bash
ce_gate_validate <phase> [mode]
```

**Arguments**:
- `$1` (string, required) - Phase (P0-P7)
- `$2` (string, optional) - Validation mode: `full`, `quick`, `incremental`, `parallel` (default: `parallel`)

**Returns**:
- `0` - Validation passed
- `1` - Validation failed

**Validation Modes**:
- `full`: Complete validation, no shortcuts (10-15s)
- `quick`: Essential checks only (5-8s)
- `incremental`: Only validate changed files (2-3s)
- `parallel`: Run checks in parallel (3-5s)

**Example**:
```bash
if ce_gate_validate "P3" "parallel"; then
    echo_success "Validation passed"
    ce_phase_next
else
    echo_error "Validation failed"
fi
```

---

### `ce_gate_validate_parallel()`

**Module**: `lib/gate_integrator.sh`
**Description**: Runs validation checks in parallel.

```bash
ce_gate_validate_parallel <phase>
```

**Arguments**:
- `$1` (string, required) - Phase (P0-P7)

**Returns**:
- `0` - All checks passed
- `1` - One or more checks failed

**Parallel Checks**:
- Path validation
- Produces validation
- Security scan
- Quality checks

**Example**:
```bash
ce_gate_validate_parallel "P3"
```

---

### `ce_gate_check_paths()`

**Module**: `lib/gate_integrator.sh`
**Description**: Validates required paths exist.

```bash
ce_gate_check_paths <phase>
```

**Arguments**:
- `$1` (string, required) - Phase (P0-P7)

**Returns**:
- `0` - All required paths exist
- `1` - Missing paths

**Example**:
```bash
ce_gate_check_paths "P1"
```

---

### `ce_gate_check_produces()`

**Module**: `lib/gate_integrator.sh`
**Description**: Validates expected outputs were produced.

```bash
ce_gate_check_produces <phase>
```

**Arguments**:
- `$1` (string, required) - Phase (P0-P7)

**Returns**:
- `0` - All expected files produced
- `1` - Missing outputs

**Example**:
```bash
ce_gate_check_produces "P2"
```

---

### `ce_gate_check_security()`

**Module**: `lib/gate_integrator.sh`
**Description**: Runs security scans (secrets detection).

```bash
ce_gate_check_security()
```

**Returns**:
- `0` - No security issues
- `1` - Security issues found

**Checks**:
- Secrets in code
- Hardcoded credentials
- API keys
- Private keys

**Example**:
```bash
ce_gate_check_security
```

---

### `ce_gate_check_quality()`

**Module**: `lib/gate_integrator.sh`
**Description**: Runs quality checks (linting, formatting, tests).

```bash
ce_gate_check_quality()
```

**Returns**:
- `0` - Quality checks passed
- `1` - Quality issues found

**Checks**:
- Shellcheck (for .sh files)
- Linting
- Code formatting
- Test execution

**Example**:
```bash
ce_gate_check_quality
```

---

## 7. PR Automation

### `ce_pr_create()`

**Module**: `lib/pr_automator.sh`
**Description**: Creates a pull request.

```bash
ce_pr_create <title> [body] [draft]
```

**Arguments**:
- `$1` (string, required) - PR title
- `$2` (string, optional) - PR body/description (uses template if not provided)
- `$3` (bool, optional) - Create as draft (default: false)

**Returns**:
- `0` - PR created successfully
- `1` - PR creation failed

**Methods**:
1. GitHub CLI (gh) - Primary
2. Web browser - Fallback

**Example**:
```bash
ce_pr_create "feat: User authentication module" "" "false"
```

---

### `ce_pr_generate_description()`

**Module**: `lib/pr_automator.sh`
**Description**: Generates PR description from template.

```bash
ce_pr_generate_description <feature_name>
```

**Arguments**:
- `$1` (string, required) - Feature name

**Returns**:
- `0` - Success

**Output**:
- Stdout: Formatted PR description

**Template Variables Replaced**:
- `[FEATURE_NAME]` - Feature name
- `[SCORE]` - Quality score
- `[COVERAGE]` - Test coverage
- `[SIGS]` - Number of gate signatures

**Example**:
```bash
DESC=$(ce_pr_generate_description "user-authentication")
echo "$DESC"
```

---

### `ce_pr_get_url()`

**Module**: `lib/pr_automator.sh`
**Description**: Gets URL of current branch's PR.

```bash
ce_pr_get_url()
```

**Returns**:
- `0` - PR URL found

**Output**:
- Stdout: PR URL or empty string

**Example**:
```bash
URL=$(ce_pr_get_url)
if [[ -n "$URL" ]]; then
    echo "PR: $URL"
fi
```

---

## 8. Git Operations

### `ce_git_safe_push()`

**Module**: `lib/git_ops.sh`
**Description**: Pushes to remote with retry logic.

```bash
ce_git_safe_push [branch] [max_retries]
```

**Arguments**:
- `$1` (string, optional) - Branch name (default: current branch)
- `$2` (int, optional) - Max retries (default: 3)

**Returns**:
- `0` - Push successful
- `1` - Push failed after retries

**Retry Strategy**:
- Exponential backoff: 2s, 4s, 8s
- Network error recovery
- Conflict detection

**Example**:
```bash
ce_git_safe_push "feature/user-auth-20251009-t1" 3
```

---

### `ce_git_safe_pull()`

**Module**: `lib/git_ops.sh`
**Description**: Pulls from remote with conflict handling.

```bash
ce_git_safe_pull [branch]
```

**Arguments**:
- `$1` (string, optional) - Branch name (default: current branch)

**Returns**:
- `0` - Pull successful
- `1` - Pull failed or conflicts detected

**Example**:
```bash
ce_git_safe_pull "main"
```

---

### `ce_git_has_uncommitted_changes()`

**Module**: `lib/git_ops.sh`
**Description**: Checks for uncommitted changes.

```bash
ce_git_has_uncommitted_changes()
```

**Returns**:
- `0` - Has uncommitted changes
- `1` - Working tree clean

**Example**:
```bash
if ce_git_has_uncommitted_changes; then
    echo_warning "You have uncommitted changes"
fi
```

---

## 9. Report Generation

### `ce_report_status()`

**Module**: `lib/report.sh`
**Description**: Generates comprehensive status report.

```bash
ce_report_status [verbose]
```

**Arguments**:
- `$1` (bool, optional) - Verbose mode (default: false)

**Returns**:
- `0` - Success

**Output Sections**:
1. Basic Information
2. Workflow Progress
3. Quality Gates
4. Current Phase Requirements (if verbose)
5. Next Steps

**Example**:
```bash
ce_report_status "true"
```

---

### `ce_report_json()`

**Module**: `lib/report.sh`
**Description**: Generates JSON status report.

```bash
ce_report_json()
```

**Returns**:
- `0` - Success

**Output**:
- Stdout: JSON object

**JSON Schema**:
```json
{
  "terminal_id": "t1",
  "current_phase": "P3",
  "branch": "feature/user-auth-20251009-t1",
  "started_at": "2025-10-09T10:30:00Z",
  "completed_phases": ["P0", "P1", "P2"],
  "validation": {
    "passed": true,
    "last_run": "2025-10-09T14:30:00Z"
  }
}
```

**Example**:
```bash
ce_report_json | jq '.current_phase'
```

---

## 10. Utility Functions

### `ce_util_confirm()`

**Module**: `lib/common.sh`
**Description**: Prompts user for confirmation.

```bash
ce_util_confirm <message> [default]
```

**Arguments**:
- `$1` (string, required) - Confirmation message
- `$2` (string, optional) - Default answer: "yes" or "no" (default: "no")

**Returns**:
- `0` - User confirmed (yes)
- `1` - User declined (no)

**Example**:
```bash
if ce_util_confirm "Delete this branch?"; then
    ce_branch_delete "$BRANCH"
fi
```

---

### `ce_util_spinner()`

**Module**: `lib/common.sh`
**Description**: Shows loading spinner while command runs.

```bash
ce_util_spinner <pid> <message>
```

**Arguments**:
- `$1` (int, required) - Process ID to monitor
- `$2` (string, required) - Message to display

**Returns**:
- `0` - Success

**Example**:
```bash
long_running_command &
PID=$!
ce_util_spinner $PID "Processing..."
wait $PID
```

---

### `ce_util_format_duration()`

**Module**: `lib/common.sh`
**Description**: Formats duration in seconds to human-readable format.

```bash
ce_util_format_duration <seconds>
```

**Arguments**:
- `$1` (int, required) - Duration in seconds

**Returns**:
- `0` - Success

**Output**:
- Stdout: Formatted duration (e.g., "2h 30m 15s")

**Example**:
```bash
DURATION=$(ce_util_format_duration 9015)
echo "Took: $DURATION"
# Output: Took: 2h 30m 15s
```

---

### `ce_util_generate_id()`

**Module**: `lib/common.sh`
**Description**: Generates unique session/ticket ID.

```bash
ce_util_generate_id [prefix]
```

**Arguments**:
- `$1` (string, optional) - ID prefix (default: "session")

**Returns**:
- `0` - Success

**Output**:
- Stdout: Unique ID (format: `<prefix>-YYYYMMDD-HHMMSS`)

**Example**:
```bash
SESSION_ID=$(ce_util_generate_id "session")
echo "$SESSION_ID"
# Output: session-20251009-103000
```

---

## Error Codes Reference

| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Operation completed successfully |
| 1 | ERROR_GENERAL | General error |
| 2 | ERROR_INVALID_ARGS | Invalid arguments provided |
| 3 | ERROR_PERMISSION | Permission denied |
| 4 | ERROR_NOT_FOUND | Resource not found |
| 5 | ERROR_EXISTS | Resource already exists |
| 6 | ERROR_TIMEOUT | Operation timed out |
| 7 | ERROR_NETWORK | Network error |
| 8 | ERROR_VALIDATION | Validation failed |
| 9 | ERROR_LOCK | Could not acquire lock |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CE_TERMINAL_ID` | Terminal identifier (t1, t2, t3) | `t1` |
| `CE_CACHE_TTL` | Cache TTL in seconds | `300` |
| `CE_PARALLEL_JOBS` | Number of parallel jobs | `4` |
| `CE_VALIDATE_MODE` | Default validation mode | `parallel` |
| `CE_DEBUG` | Enable debug output | `0` |
| `CE_PR_TEMPLATE` | Path to PR template | `templates/pr_description.md` |

---

## Related Documentation

- [User Guide](./USER_GUIDE.md) - End user documentation
- [Developer Guide](./DEVELOPER_GUIDE.md) - Development guide
- [Architecture](../../../docs/P1_CE_COMMAND_ARCHITECTURE.md) - System architecture

---

**Last Updated**: 2025-10-09
**Version**: 1.0.0
**Status**: ⚠️ TEMPLATE - Implementation pending (P3)

---

*Generated by Claude Code - CE CLI API Documentation Team*
