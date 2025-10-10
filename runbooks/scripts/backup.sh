#!/bin/bash
set -euo pipefail

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=== Creating Backup ==="
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp -r .claude "$BACKUP_DIR/" 2>/dev/null || true
cp .env "$BACKUP_DIR/" 2>/dev/null || true

# Backup workflow state
cp -r .workflow "$BACKUP_DIR/" 2>/dev/null || true
cp -r .phase "$BACKUP_DIR/" 2>/dev/null || true

# Create archive
tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR/"

echo "✓ Backup created: ${BACKUP_DIR}.tar.gz"
echo "Size: $(du -h "${BACKUP_DIR}.tar.gz" | cut -f1)"
