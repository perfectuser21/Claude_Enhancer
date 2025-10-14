# Quick Reference - Claude Enhancer Modules v2.0

## Import Cheat Sheet

### Logging
```python
from modules.utils import get_logger
logger = get_logger(__name__)
```

### File Operations
```python
from modules.utils import read_json_file, write_json_file, ensure_dir

config = read_json_file('config.json', default={})
write_json_file('output.json', data)
ensure_dir('logs/')
```

### Time Utilities
```python
from modules.utils import format_duration, time_ago, get_timestamp

print(format_duration(125.5))  # "2m 5s"
print(time_ago(some_datetime))  # "2 hours ago"
print(get_timestamp())  # "20251014_103045"
```

### Result Type (Error Handling)
```python
from modules.shared import success, failure, ErrorCode, Result

def my_function() -> Result:
    if error:
        return failure("Error message", ErrorCode.VALIDATION_ERROR)
    return success({'data': 'value'})

result = my_function()
if result.success:
    print(result.data)
else:
    print(f"Error: {result.error}")
```

### Git Operations
```python
from modules.integrations import GitIntegration

git = GitIntegration()

# Current branch
branch = git.get_current_branch()
print(f"On: {branch.data}")

# Create branch
git.create_branch('feature/test')

# Status
status = git.get_status()
print(f"Modified: {status.data['modified']}")

# Commit
git.commit("Update feature", files=['src/main.py'])

# Push
git.push(set_upstream=True)
```

### NPM Operations
```python
from modules.integrations import NPMIntegration

npm = NPMIntegration()

# Run script
npm.run_script('test')

# Install package
npm.install(['express'], dev=False)

# Check version
version = npm.get_version()
print(f"v{version.data}")

# Audit
audit = npm.audit()
```

## Common Patterns

### Safe File Write with Backup
```python
from modules.utils import safe_file_write

safe_file_write('important.txt', content, backup=True)
```

### Command Execution
```python
from modules.shared import CommandRunner

runner = CommandRunner(cwd='/path/to/dir', timeout=60)
result = runner.run(['ls', '-la'])
if result.success:
    print(result.data['stdout'])
```

### Table Formatting
```python
from modules.shared import format_table

headers = ['Name', 'Status', 'Time']
rows = [
    ['Task 1', 'Done', '2m'],
    ['Task 2', 'Running', '5m']
]
print(format_table(headers, rows))
```

## Error Codes

| Code | Value | Use Case |
|------|-------|----------|
| `SUCCESS` | 0 | Operation succeeded |
| `VALIDATION_ERROR` | 1 | Invalid input |
| `FILE_NOT_FOUND` | 2 | Missing file/dir |
| `EXECUTION_ERROR` | 4 | Command failed |
| `GIT_ERROR` | 9 | Git operation failed |

## Backward Compatibility

Old imports still work via symlinks:
```python
# Still works
from .claude.core.engine import WorkflowEngine
```

New imports (recommended):
```python
# Better
from core.workflow.engine import WorkflowEngine
```

## Full Documentation

- **API Reference**: `modules/README.md`
- **Migration Guide**: `modules/MIGRATION_GUIDE.md`
- **Examples**: Coming soon in `examples/`

---
**Version**: 2.0.0 | **Updated**: 2025-10-14
