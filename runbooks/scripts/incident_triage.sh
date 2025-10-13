#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TRIAGE_DIR="/tmp/incident_triage_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$TRIAGE_DIR"
cd "$PROJECT_ROOT" || exit

echo "=== Incident Triage - Collecting Diagnostics ==="

# System info
echo "Collecting system information..."
uname -a > "$TRIAGE_DIR/system_info.txt"
free -h > "$TRIAGE_DIR/memory.txt"
df -h > "$TRIAGE_DIR/disk.txt"

# Version info
git --version > "$TRIAGE_DIR/versions.txt" 2>&1
node --version >> "$TRIAGE_DIR/versions.txt" 2>&1
npm --version >> "$TRIAGE_DIR/versions.txt" 2>&1

# Configuration
cp .claude/settings.json "$TRIAGE_DIR/" 2>/dev/null || echo "No config" > "$TRIAGE_DIR/no_config.txt"

# Workflow state
cp .workflow/ACTIVE "$TRIAGE_DIR/" 2>/dev/null || echo "No workflow" > "$TRIAGE_DIR/no_workflow.txt"
cp .phase/current "$TRIAGE_DIR/" 2>/dev/null || echo "No phase" > "$TRIAGE_DIR/no_phase.txt"

# Recent logs
tail -100 logs/error.log > "$TRIAGE_DIR/recent_errors.txt" 2>/dev/null || echo "No logs" > "$TRIAGE_DIR/no_logs.txt"

# Git status
git status > "$TRIAGE_DIR/git_status.txt" 2>&1
git log --oneline -10 > "$TRIAGE_DIR/recent_commits.txt" 2>&1

# Create archive
tar -czf "${TRIAGE_DIR}.tar.gz" -C /tmp "$(basename "$TRIAGE_DIR")"

echo "✓ Diagnostics collected: ${TRIAGE_DIR}.tar.gz"
echo "Size: $(du -h "${TRIAGE_DIR}.tar.gz" | cut -f1)"
echo ""
echo "Please attach this file when reporting the incident"
