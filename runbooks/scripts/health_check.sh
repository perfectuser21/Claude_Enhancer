#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

echo "=== Health Check ==="

# Check Git
if command -v git &> /dev/null; then
    echo "✓ Git: $(git --version | cut -d' ' -f3)"
else
    echo "✗ Git: Not installed"
fi

# Check Node.js
if command -v node &> /dev/null; then
    echo "✓ Node.js: $(node --version)"
else
    echo "✗ Node.js: Not installed"
fi

# Check npm
if command -v npm &> /dev/null; then
    echo "✓ npm: $(npm --version)"
else
    echo "✗ npm: Not installed"
fi

# Check Git hooks
if [ -x .git/hooks/pre-commit ]; then
    echo "✓ Git hooks: Installed"
else
    echo "✗ Git hooks: Not installed"
fi

# Check configuration
if [ -f .claude/settings.json ]; then
    echo "✓ Configuration: Present"
else
    echo "✗ Configuration: Missing"
fi

# Check workflow state
if [ -f .workflow/ACTIVE ]; then
    echo "✓ Workflow: $(cat .workflow/ACTIVE)"
else
    echo "✗ Workflow: Not initialized"
fi

echo "=== Health Check Complete ==="
