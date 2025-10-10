# Command Routing Flow Diagram

## User Command Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Invokes CLI                            │
│                   $ ce --verbose status                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ce_main() Entry Point                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Parse Arguments Loop                                      │  │
│  │  - Extract global options (--verbose, --debug, etc.)     │  │
│  │  - Separate command and command-specific args            │  │
│  │  - Handle --help and --version (early exit)              │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 ce_init_environment()                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. Export CE_ROOT, CE_VERSION, etc.                      │  │
│  │ 2. Detect terminal ID (t1, t2, ...)                      │  │
│  │ 3. Set color mode (auto/always/never)                    │  │
│  │ 4. Create state directories                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ce_load_libraries()                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Load in dependency order:                                │  │
│  │  1. common.sh          → Logging, colors, utils          │  │
│  │  2. state_manager.sh   → Session management              │  │
│  │  3. phase_manager.sh   → Phase transitions               │  │
│  │  4. branch_manager.sh  → Branch operations               │  │
│  │  5. git_operations.sh  → Git helpers                     │  │
│  │  6. gate_integrator.sh → Quality gates                   │  │
│  │  7. pr_automator.sh    → PR automation                   │  │
│  │  8. conflict_detector.sh → Conflict detection            │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                ce_validate_environment()                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Check:                                                    │  │
│  │  ✓ Git repository exists                                 │  │
│  │  ✓ Required commands (git, bash 4.0+)                    │  │
│  │  ✓ .workflow directory structure                         │  │
│  │  ⚠ Optional tools (jq, yq, gh)                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ce_route_command("status")                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Command Mapping (case statement):                        │  │
│  │                                                           │  │
│  │  start|init      → ce_load_command "start"               │  │
│  │  status|st       → ce_load_command "status"  ◄── MATCH  │  │
│  │  next|advance    → ce_load_command "next"                │  │
│  │  validate|check  → ce_load_command "validate"            │  │
│  │  ...             → ...                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ce_load_command("status")                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Source command script:                                    │  │
│  │  .workflow/cli/commands/status.sh                        │  │
│  │                                                           │  │
│  │ Functions now available:                                 │  │
│  │  - cmd_status_help()                                     │  │
│  │  - cmd_status_collect_data()                             │  │
│  │  - cmd_status_format_output()                            │  │
│  │  - cmd_status_main()  ◄── Entry point                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  cmd_status_main("--verbose")                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Command-specific logic:                                  │  │
│  │  1. Parse command options (--verbose, --json, etc.)      │  │
│  │  2. Validate inputs                                      │  │
│  │  3. Collect status data                                  │  │
│  │  4. Format and display output                            │  │
│  │  5. Exit with status code                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Output to User                              │
│                                                                  │
│  ===================================================           │
│       Claude Enhancer - Development Status                     │
│  ===================================================           │
│                                                                  │
│  Current State:                                                │
│    Branch:       feature/P0-capability-enhancement             │
│    Phase:        P3                                            │
│    Modified:     240 files                                     │
│    Staged:       0 files                                       │
│                                                                  │
│  Active Sessions:                                              │
│    No active sessions                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Function Call Hierarchy

```
ce_main()
├── [Parse Global Options]
│   ├── --help → ce_show_help() → exit(0)
│   ├── --version → ce_show_version() → exit(0)
│   └── [Other options stored]
│
├── ce_init_environment()
│   ├── ce_detect_terminal_id()
│   │   ├── Check TERM_SESSION_ID
│   │   ├── Check TTY number
│   │   ├── Check TMUX_PANE/STY
│   │   └── Default to "t1"
│   └── [Setup directories]
│
├── ce_load_libraries()
│   ├── source common.sh
│   ├── source state_manager.sh
│   ├── source phase_manager.sh
│   ├── source branch_manager.sh
│   ├── source git_operations.sh
│   ├── source gate_integrator.sh
│   ├── source pr_automator.sh
│   └── source conflict_detector.sh
│
├── ce_validate_environment()
│   ├── Check git repository
│   ├── Check required commands
│   ├── Check bash version
│   ├── Check .workflow directory
│   └── Warn about optional tools
│
└── ce_route_command(args...)
    ├── [Match command]
    ├── ce_load_command("command_name")
    │   └── source .workflow/cli/commands/command_name.sh
    └── cmd_command_main(args...)
        ├── Parse command options
        ├── Validate inputs
        ├── Execute command logic
        └── exit(status)
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Execution Path                              │
│                         (any stage)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    [ERROR OCCURS]
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              trap 'ce_handle_error ${LINENO}' ERR                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Captures:                                                 │  │
│  │  - Exit code ($?)                                         │  │
│  │  - Line number (${LINENO})                                │  │
│  │  - Stack trace (if --debug)                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ce_cleanup_on_exit()                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Cleanup Actions:                                          │  │
│  │  1. Remove temp files (CE_TEMP_FILES)                     │  │
│  │  2. Remove temp dirs (CE_TEMP_DIRS)                       │  │
│  │  3. Release locks (PID-based search)                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Exit with Code                              │
│                     (non-zero on error)                          │
└─────────────────────────────────────────────────────────────────┘
```

## Library Dependency Graph

```
ce_main()
    │
    └─→ common.sh                    [No dependencies]
            │
            └─→ state_manager.sh     [Requires: common.sh]
                    │
                    ├─→ phase_manager.sh    [Requires: common.sh, state_manager.sh]
                    │
                    └─→ branch_manager.sh   [Requires: common.sh, state_manager.sh]
                            │
                            ├─→ git_operations.sh      [Requires: common.sh]
                            │
                            ├─→ gate_integrator.sh     [Requires: common.sh, phase_manager.sh]
                            │
                            ├─→ pr_automator.sh        [Requires: common.sh, branch_manager.sh]
                            │
                            └─→ conflict_detector.sh   [Requires: common.sh, git_operations.sh]
```

## Command Execution Timeline

```
Time →
│
0ms   │ User enters command: $ ce --verbose status
      │
5ms   │ ├─ ce_main() starts
      │ ├─ Parse global options
      │ └─ Set CE_VERBOSE=true
      │
10ms  │ ├─ ce_init_environment()
      │ ├─ Detect terminal ID: t1
      │ └─ Create state directories
      │
20ms  │ ├─ ce_load_libraries()
      │ ├─ Load 8 library files
      │ └─ Export 50+ functions
      │
30ms  │ ├─ ce_validate_environment()
      │ ├─ Check git repo ✓
      │ ├─ Check bash 4.0+ ✓
      │ ├─ Check .workflow dir ✓
      │ └─ Warn about missing yq, gh
      │
40ms  │ ├─ ce_route_command("status")
      │ ├─ Match "status" → "status.sh"
      │ └─ ce_load_command("status")
      │
45ms  │ ├─ cmd_status_main()
      │ ├─ Parse command options
      │ └─ cmd_status_collect_data()
      │
80ms  │ ├─ Collect git status (240 files)
      │ ├─ Query session directories
      │ └─ Build status data structure
      │
100ms │ ├─ cmd_status_format_output()
      │ ├─ Generate color-coded output
      │ └─ Print to stdout
      │
110ms │ ├─ exit(0)
      │ └─ trap ce_cleanup_on_exit
      │
120ms │ ├─ Cleanup (no temp files)
      │ └─ Process exits
      │
Total: 120ms (0.12 seconds)
```

## State Directory Structure

```
.workflow/cli/state/
│
├── sessions/                    # Active terminal sessions
│   ├── t1-20251009193000/
│   │   └── manifest.yml
│   ├── t2-20251009194500/
│   │   └── manifest.yml
│   └── ...
│
├── branches/                    # Branch metadata
│   ├── feature-P3-t1-login.yml
│   ├── feature-P4-t2-signup.yml
│   └── ...
│
├── locks/                       # File locks
│   ├── state.lock/
│   │   ├── pid
│   │   └── timestamp
│   └── ...
│
├── history/                     # Archived sessions
│   ├── t1-20251008_*.state.gz
│   └── ...
│
├── backups/                     # State backups
│   ├── state_20251009_120000.yml
│   └── ...
│
├── contexts/                    # Saved contexts
│   └── ...
│
├── global.state.yml            # Global state file
└── current_phase               # Current phase marker
```

## Environment Variables Used

```bash
# Set by ce_main()
CE_ROOT="/home/xx/dev/Claude Enhancer 5.0"
CE_VERSION="1.0.0"
CE_BUILD_DATE="2025-10-09"

# Set by argument parsing
CE_VERBOSE="true"          # --verbose flag
CE_DEBUG="false"           # --debug flag
CE_TERMINAL_ID="t1"        # --terminal or auto-detected
CE_COLOR="always"          # --color or auto-detected

# Set by ce_init_environment()
CE_STATE_DIR="${CE_ROOT}/.workflow/cli/state"
CE_SESSION_DIR="${CE_STATE_DIR}/sessions"
CE_BRANCH_DIR="${CE_STATE_DIR}/branches"
CE_LOCK_DIR="${CE_STATE_DIR}/locks"

# Used by commands (exported by libraries)
CE_TEMP_FILES=()           # Array of temp files for cleanup
CE_TEMP_DIRS=()            # Array of temp dirs for cleanup
```

## Command Aliases Reference

| User Types | Actual Command | Script Loaded |
|-----------|---------------|--------------|
| `ce start` | start | commands/start.sh |
| `ce init` | start | commands/start.sh |
| `ce status` | status | commands/status.sh |
| `ce st` | status | commands/status.sh |
| `ce next` | next | commands/next.sh |
| `ce advance` | next | commands/next.sh |
| `ce validate` | validate | commands/validate.sh |
| `ce check` | validate | commands/validate.sh |
| `ce publish` | publish | commands/publish.sh |
| `ce pub` | publish | commands/publish.sh |
| `ce merge` | merge | commands/merge.sh |
| `ce mr` | merge | commands/merge.sh |
| `ce clean` | clean | commands/clean.sh |
| `ce cleanup` | clean | commands/clean.sh |
| `ce branch` | branch | commands/branch.sh |
| `ce br` | branch | commands/branch.sh |
| `ce phase` | phase | commands/phase.sh |
| `ce ph` | phase | commands/phase.sh |

---

**This diagram shows the complete flow from user input to command execution and cleanup.**

