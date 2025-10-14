# Module Migration Guide

This guide explains the new module structure in Claude Enhancer v2.0 and how to migrate from v1.x imports.

## Architecture Overview

### Old Structure (v1.x)
```
.claude/core/
├── engine.py
├── orchestrator.py
├── lazy_orchestrator.py
├── git_automation.py
└── ... (12 files)
```

### New Structure (v2.0)
```
core/                    # Core functionality (v2.0)
├── workflow/
│   └── engine.py
├── agents/
│   └── selector.py
├── state/
│   └── manager.py
├── hooks/
│   └── manager.py
└── config/
    └── loader.py

modules/                 # Shared utilities (NEW)
├── utils/
│   ├── logger.py
│   ├── file_handler.py
│   └── time_utils.py
├── shared/
│   └── common.py
└── integrations/
    ├── git.py
    └── npm.py

.claude/                 # Backward compatibility layer
├── engine.py -> ../core/workflow/engine.py
├── agent_selector.py -> ../core/agents/selector.py
└── ... (symlinks)
```

## Migration Path

### Phase 1: Backward Compatibility (Current)
Symlinks in `.claude/` point to new locations. **No code changes needed.**

```python
# Old imports still work via symlinks
from .claude.engine import WorkflowEngine  # ✓ Works
from .claude.agent_selector import AgentSelector  # ✓ Works
```

### Phase 2: Direct Imports (Recommended)
Update imports to use new structure for better IDE support.

```python
# New imports (recommended)
from core.workflow.engine import WorkflowEngine
from core.agents.selector import AgentSelector
from modules.utils import get_logger
from modules.integrations import GitIntegration
```

### Phase 3: Legacy Removal (Future)
Eventually, symlinks will be removed. Timeline: TBD (at least 3 months notice).

## Import Mapping

### Core Engine
```python
# Old
from .claude.core.engine import WorkflowEngine

# New
from core.workflow.engine import WorkflowEngine
```

### Agent Orchestrator
```python
# Old
from .claude.core.orchestrator import AgentOrchestrator
from .claude.core.lazy_orchestrator import LazyAgentOrchestrator

# New
from core.agents.selector import AgentSelector
```

### Utilities (NEW)

#### Logging
```python
# Instead of custom logging setup
from modules.utils import get_logger, setup_logger

logger = get_logger(__name__)
```

#### File Operations
```python
# Instead of open(), json.load(), etc.
from modules.utils import read_json_file, write_json_file, ensure_dir

config = read_json_file('config.json', default={})
write_json_file('output.json', data)
```

#### Time Utilities
```python
# Instead of datetime.strftime(), etc.
from modules.utils import get_timestamp, format_duration, time_ago

timestamp = get_timestamp()  # "20251014_103045"
duration = format_duration(125.5)  # "2m 5s"
ago = time_ago(datetime.now() - timedelta(days=2))  # "2 days ago"
```

#### Result Types (NEW)
```python
# For consistent error handling
from modules.shared import success, failure, ErrorCode, Result

def my_function() -> Result:
    if error:
        return failure("Error message", ErrorCode.VALIDATION_ERROR)
    return success(data={'key': 'value'})
```

#### Git Operations
```python
# Instead of subprocess.run(['git', ...])
from modules.integrations import GitIntegration

git = GitIntegration()
result = git.get_current_branch()
if result.success:
    print(f"Current branch: {result.data}")
```

#### NPM Operations
```python
# Instead of subprocess.run(['npm', ...])
from modules.integrations import NPMIntegration

npm = NPMIntegration()
result = npm.run_script('test')
if result.success:
    print(result.data)
```

## Benefits of New Structure

### 1. Clear Separation of Concerns
- **core/**: Workflow engine logic (rarely changes)
- **modules/**: Reusable utilities (shared across tools)
- **.claude/**: Compatibility layer (temporary)

### 2. Better IDE Support
- Proper package structure (`__init__.py` files)
- Clear import paths
- Type hints throughout

### 3. Reduced Duplication
- Git operations consolidated in `modules/integrations/git.py`
- File I/O helpers in `modules/utils/file_handler.py`
- Common patterns in `modules/shared/common.py`

### 4. Easier Testing
```python
# Mock at module level
from unittest.mock import patch

with patch('modules.integrations.git.GitIntegration.get_current_branch'):
    # Test code
```

### 5. Consistent Error Handling
```python
# Every function returns Result type
result = git.create_branch('feature/test')
if result.success:
    print(result.data)
else:
    print(f"Error: {result.error} (code: {result.error_code})")
```

## Migration Checklist

For each Python file using old imports:

- [ ] Identify imported modules from `.claude/core/`
- [ ] Check if equivalent exists in `core/` or `modules/`
- [ ] Update import statements
- [ ] Update function calls if API changed
- [ ] Test functionality
- [ ] Update any documentation

## Example Migration

### Before (v1.x)
```python
#!/usr/bin/env python3
import json
import subprocess
from .claude.core.engine import WorkflowEngine
from .claude.core.git_automation import GitAutomation

# Load config
with open('config.json') as f:
    config = json.load(f)

# Get git status
result = subprocess.run(['git', 'status'], capture_output=True, text=True)
if result.returncode == 0:
    print(result.stdout)

# Create engine
engine = WorkflowEngine(config)
```

### After (v2.0)
```python
#!/usr/bin/env python3
from core.workflow.engine import WorkflowEngine
from modules.utils import read_json_file, get_logger
from modules.integrations import GitIntegration

# Setup logging
logger = get_logger(__name__)

# Load config
config = read_json_file('config.json', default={})

# Get git status
git = GitIntegration()
result = git.get_status()
if result.success:
    logger.info(f"Git status: {result.data}")
else:
    logger.error(f"Git error: {result.error}")

# Create engine
engine = WorkflowEngine(config)
```

## FAQs

### Q: Do I need to migrate immediately?
**A:** No. Symlinks provide backward compatibility. Migrate at your convenience.

### Q: Will symlinks be removed?
**A:** Eventually, yes. But not before v3.0 (at least 3 months notice).

### Q: What if I find a bug in new modules?
**A:** Report in GitHub issues. We'll fix and maintain backward compatibility.

### Q: Can I use both old and new imports?
**A:** Yes, but not recommended. Pick one style for consistency.

### Q: How do I know which import to use?
**A:** Check `modules/__init__.py` and submodule `__init__.py` files for available exports.

## Support

- Documentation: `/home/xx/dev/Claude Enhancer 5.0/docs/`
- Examples: `/home/xx/dev/Claude Enhancer 5.0/examples/` (coming soon)
- Issues: GitHub Issues

## Version History

- **v2.0.0** (2025-10-14): Initial module structure with backward compatibility
- **v2.1.0** (TBD): Additional utility functions
- **v3.0.0** (TBD): Remove backward compatibility symlinks
