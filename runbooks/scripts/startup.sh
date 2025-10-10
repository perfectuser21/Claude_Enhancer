#!/bin/bash
set -euo pipefail

# Claude Enhancer 5.3 - Startup Script
# Purpose: Start all system components

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=== Claude Enhancer 5.3 Startup ==="
echo "Time: $(date)"

# Step 1: Pre-start checks
echo ""
echo "[1/5] Pre-start checks..."

if ! command -v git &> /dev/null; then
    echo "Error: Git not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "Error: Node.js not installed"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "Error: npm not installed"
    exit 1
fi

echo "✓ Dependencies check passed"

# Step 2: Initialize environment
echo ""
echo "[2/5] Initializing environment..."

# Create necessary directories
mkdir -p logs
mkdir -p .workflow
mkdir -p .phase
mkdir -p backups

# Initialize workflow state if not exists
if [ ! -f .workflow/ACTIVE ]; then
    echo "ready" > .workflow/ACTIVE
    echo "0" > .phase/current
    echo "✓ Workflow initialized"
else
    echo "✓ Workflow already initialized"
fi

# Step 3: Install Git hooks if needed
echo ""
echo "[3/5] Verifying Git hooks..."

if [ ! -x .git/hooks/pre-commit ]; then
    echo "Installing Git hooks..."
    ./.claude/install.sh
    echo "✓ Git hooks installed"
else
    echo "✓ Git hooks already installed"
fi

# Step 4: Clear locks
echo ""
echo "[4/5] Clearing old locks..."

rm -f .workflow/*.lock 2>/dev/null || true
rm -f /tmp/claude_*.lock 2>/dev/null || true
echo "✓ Locks cleared"

# Step 5: Verify startup
echo ""
echo "[5/5] Verifying startup..."

if [ -x ./scripts/healthcheck.sh ]; then
    ./scripts/healthcheck.sh || echo "Warning: Health check reported issues"
else
    echo "✓ Basic checks passed"
fi

echo ""
echo "=== Startup Complete ==="
echo "Claude Enhancer 5.3 is ready"
echo "$(date)"
