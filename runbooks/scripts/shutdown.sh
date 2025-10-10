#!/bin/bash
set -euo pipefail

echo "=== Claude Enhancer 5.3 Shutdown ==="
echo "Time: $(date)"

# Graceful shutdown
echo "Stopping services gracefully..."

# Mark as shutting down
echo "shutdown" > ../../.workflow/ACTIVE 2>/dev/null || true

# Kill any running processes
pkill -TERM -f "claude-enhancer" 2>/dev/null || echo "No processes to stop"

sleep 2

# Force kill if still running
pkill -KILL -f "claude-enhancer" 2>/dev/null || true

echo "✓ Shutdown complete"
echo "$(date)"
