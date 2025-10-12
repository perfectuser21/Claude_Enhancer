# Task Namespace Directory

This directory contains task-specific enforcement evidence and gates.

## Structure

```
.gates/
├── _index.json                 # Central task registry
├── README.md                   # This file
├── .gitignore                  # Ignore temporary files
└── <task_id>/                  # Per-task namespace
    ├── task_meta.json          # Task metadata
    ├── evidence.json           # Execution evidence
    ├── agents.json             # Agent invocations
    ├── 00.ok, 01.ok, ...      # Phase gate markers
    └── violations.log          # Bypass attempts (if any)
```

## Task ID Format

`<phase>_<YYYYMMDD>_<HHMMSS>_<PID>_<UUID8>`

Example: `P3_20251011_143022_12345_a1b2c3d4`

Components:
- **phase**: P0-P7 (phase when task started)
- **YYYYMMDD**: Date
- **HHMMSS**: Time
- **PID**: Process ID (prevents collision)
- **UUID8**: 8-char random UUID (extra safety)

## Lifecycle

1. **Task Creation**: `scripts/init_task_namespace.sh` creates new task directory
2. **Evidence Collection**: Hooks append to `evidence.json` and `agents.json`
3. **Gate Passing**: Phase completion creates `XX.ok` markers
4. **Completion**: Task marked as complete in `_index.json`
5. **Cleanup**: Old tasks archived after 90 days (configurable)

## Index File

`_index.json` maintains the master registry:

```json
{
  "tasks": {
    "P3_20251011_143022_12345_a1b2c3d4": {
      "created_at": "2025-10-11T14:30:22Z",
      "phase": "P3",
      "status": "in_progress",
      "branch": "feature/user-auth",
      "lane": "full"
    }
  },
  "active_task_id": "P3_20251011_143022_12345_a1b2c3d4"
}
```

## Concurrency Safety

- **Atomic Operations**: All writes use temp file + rename
- **File Locking**: `flock` prevents concurrent modifications
- **Retry Logic**: Exponential backoff on conflicts
- **UUID Component**: Ensures uniqueness even with concurrent creates

## Maintenance

- **Manual Cleanup**: `scripts/cleanup_old_tasks.sh --older-than 90`
- **Integrity Check**: `scripts/verify_task_namespace.sh`
- **Export Archive**: `scripts/export_tasks.sh --output tasks.tar.gz`

## Migration

For projects upgrading from Claude Enhancer 6.1 or earlier:
- Run `scripts/migrate_to_task_namespace.sh`
- Old `.phase/` state will be migrated to task namespaces
- Previous gates remain for historical reference
