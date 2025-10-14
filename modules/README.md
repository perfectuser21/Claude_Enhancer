# Modules Layer

This directory contains **shared utilities** used by both core/ and features/.

## Architecture

```
modules/
├── utils/          # General utilities (logging, file I/O, etc.)
├── shared/         # Shared business logic
└── integrations/   # Third-party integrations (git, npm, etc.)
```

## Module Principles

1. **Stateless** - Modules should be pure functions or stateless classes
2. **Reusable** - Used by multiple components
3. **Tested** - High test coverage required
4. **Documented** - Clear API documentation

## Usage Example

```python
# From core/
from modules.utils import logger, file_handler

# From features/
from modules.integrations import GitIntegration
```

## Module Structure

```
module-category/
├── __init__.py           # Module exports
├── README.md            # Module documentation
├── tests/               # Module tests
└── src/                 # Module implementation
```

## Version: 2.0.0
