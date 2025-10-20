# Code Quality Checker

A simple CLI tool for checking Python and Shell code quality.

## Features

- Check function complexity (line count, nesting depth)
- Check naming conventions (snake_case, PascalCase)
- Generate JSON and Markdown reports
- Configurable rules via YAML

## Quick Start

```bash
# Check a file
python3 src/main.py examples/sample_code.py

# JSON output
python3 src/main.py examples/sample_code.py --format json

# Save to file
python3 src/main.py examples/sample_code.py --output report.md
```

## Example Output

```
# Code Quality Report

## Summary
- Total Files: 1
- Total Issues: 5
- Errors: 3
- Warnings: 2
```

## Testing

```bash
pytest tests/ -v
```

## Configuration

See `config/default_rules.yml` for default rules.
