# Claude Enhancer Modules

Shared utilities and integrations for the Claude Enhancer v2.0 system.

## Overview

The `modules/` directory contains reusable components that are used across different parts of Claude Enhancer:

- **utils/**: Common utilities (logging, file I/O, time operations)
- **shared/**: Shared types and patterns (Result type, error codes)
- **integrations/**: External tool wrappers (Git, NPM)

## Quick Start

### Logging
```python
from modules.utils import get_logger

logger = get_logger(__name__)
logger.info("Starting process...")
logger.error("Something went wrong")
```

### File Operations
```python
from modules.utils import read_json_file, write_json_file

# Read with default fallback
config = read_json_file('config.json', default={})

# Atomic write with backup
write_json_file('output.json', data)
```

### Time Utilities
```python
from modules.utils import format_duration, time_ago, get_timestamp

duration = format_duration(125.5)  # "2m 5s"
timestamp = get_timestamp()  # "20251014_103045"
```

### Result Types (Error Handling)
```python
from modules.shared import success, failure, ErrorCode, Result

def process_file(path: str) -> Result:
    if not path:
        return failure("Path required", ErrorCode.VALIDATION_ERROR)

    # ... do work ...

    return success(data={'lines': 42})

# Usage
result = process_file('data.txt')
if result.success:
    print(f"Processed {result.data['lines']} lines")
else:
    print(f"Error: {result.error} ({result.error_code})")
```

### Git Integration
```python
from modules.integrations import GitIntegration

git = GitIntegration()

# Get current branch
branch_result = git.get_current_branch()
if branch_result.success:
    print(f"On branch: {branch_result.data}")

# Create new branch
result = git.create_branch('feature/new-feature')

# Commit changes
result = git.commit("Add new feature", files=['src/main.py'])
```

### NPM Integration
```python
from modules.integrations import NPMIntegration

npm = NPMIntegration()

# Run npm script
result = npm.run_script('test')
if result.success:
    print(result.data)

# Check for outdated packages
result = npm.outdated()
if result.success:
    for pkg, info in result.data.items():
        print(f"{pkg}: {info['current']} -> {info['latest']}")
```

## Module Reference

### modules.utils.logger

| Function | Description |
|----------|-------------|
| `setup_logger(name, level, log_file)` | Create logger with console and optional file output |
| `get_logger(name)` | Get or create logger with default config |
| `LogContext(logger, level)` | Context manager for temporary log level changes |
| `log_execution_time(logger)` | Decorator to log function execution time |

### modules.utils.file_handler

| Function | Description |
|----------|-------------|
| `ensure_dir(path)` | Ensure directory exists, create if needed |
| `read_json_file(path, default)` | Read JSON with error handling |
| `write_json_file(path, data)` | Atomic JSON write with backup |
| `read_yaml_file(path, default)` | Read YAML with error handling |
| `write_yaml_file(path, data)` | Atomic YAML write with backup |
| `safe_file_write(path, content, backup)` | Write file with optional backup |
| `copy_with_backup(src, dst)` | Copy file with destination backup |

### modules.utils.time_utils

| Function | Description |
|----------|-------------|
| `get_timestamp(format)` | Get formatted timestamp string |
| `format_duration(seconds)` | Format seconds to human-readable (e.g., "2m 5s") |
| `parse_datetime(string, format)` | Parse datetime string |
| `time_ago(dt)` | Convert datetime to "time ago" format |
| `is_within_days(dt, days)` | Check if datetime within N days |
| `add_days(dt, days)` | Add/subtract days from datetime |
| `get_date_range(start, end)` | Get list of dates in range |

### modules.shared.common

#### Result Type
```python
@dataclass
class Result:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: ErrorCode = ErrorCode.SUCCESS
```

#### Error Codes
- `SUCCESS = 0`
- `VALIDATION_ERROR = 1`
- `FILE_NOT_FOUND = 2`
- `PERMISSION_ERROR = 3`
- `EXECUTION_ERROR = 4`
- `CONFIGURATION_ERROR = 5`
- `HOOK_FAILURE = 6`
- `PHASE_TRANSITION_ERROR = 7`
- `AGENT_ERROR = 8`
- `GIT_ERROR = 9`
- `UNKNOWN_ERROR = 99`

#### Helper Functions
| Function | Description |
|----------|-------------|
| `success(data)` | Create success Result |
| `failure(error, error_code, data)` | Create failure Result |
| `CommandRunner(cwd, timeout)` | Safe command execution wrapper |
| `validate_path(path, must_exist, must_be_file)` | Validate file system path |
| `format_table(headers, rows)` | Format data as ASCII table |

### modules.integrations.git.GitIntegration

| Method | Description |
|--------|-------------|
| `is_git_repo()` | Check if directory is git repo |
| `get_current_branch()` | Get current branch name |
| `get_remote_branches()` | List remote branches |
| `create_branch(name, base)` | Create new branch |
| `switch_branch(name)` | Switch to existing branch |
| `get_status()` | Get git status (modified, added, deleted files) |
| `stage_files(files)` | Stage files for commit |
| `commit(message, files)` | Create commit |
| `push(branch, set_upstream)` | Push to remote |
| `get_diff(cached)` | Get diff (staged or unstaged) |
| `get_log(count, oneline)` | Get commit history |
| `is_clean()` | Check if working directory is clean |
| `get_remote_url()` | Get remote repository URL |

### modules.integrations.npm.NPMIntegration

| Method | Description |
|--------|-------------|
| `has_package_json()` | Check if package.json exists |
| `read_package_json()` | Read package.json content |
| `write_package_json(data)` | Write package.json |
| `install(packages, dev)` | Install npm packages |
| `uninstall(packages)` | Uninstall packages |
| `run_script(name, args)` | Run npm script |
| `list_scripts()` | List available scripts |
| `get_version()` | Get project version |
| `set_version(version)` | Set project version |
| `outdated()` | Check for outdated packages |
| `audit(fix)` | Run security audit |
| `get_dependencies(include_dev)` | Get dependencies dict |
| `check_node_version()` | Check Node.js version |
| `check_npm_version()` | Check npm version |

## Design Principles

1. **Consistent Error Handling**: All functions return `Result` type
2. **Safe Operations**: Atomic file writes, command timeouts, error recovery
3. **Clear APIs**: Self-documenting function names and parameters
4. **Type Safety**: Type hints throughout for IDE support
5. **Testability**: Easy to mock and test

## Testing

```python
from unittest.mock import patch, MagicMock

# Mock file operations
with patch('modules.utils.file_handler.read_json_file') as mock_read:
    mock_read.return_value = {'key': 'value'}
    # Test code

# Mock Git operations
with patch('modules.integrations.git.GitIntegration.get_current_branch') as mock_git:
    mock_git.return_value = success('main')
    # Test code
```

## Contributing

When adding new utilities:

1. Place in appropriate submodule (utils/shared/integrations)
2. Add to `__init__.py` exports
3. Include docstrings with type hints
4. Return `Result` type for operations that can fail
5. Add entry to this README
6. Write tests

## Migration from v1.x

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for detailed migration instructions.

## Version

Current version: **2.0.0**

See [CHANGELOG.md](../CHANGELOG.md) for version history.
