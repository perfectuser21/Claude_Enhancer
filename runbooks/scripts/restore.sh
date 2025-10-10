#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup-file>"
    echo "Available backups:"
    ls -lh ../../backups/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "=== Restoring from Backup ==="
echo "Backup: $BACKUP_FILE"

# Extract backup
tar -xzf "$BACKUP_FILE" -C /tmp/

# Restore files
BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)
cp -r "/tmp/$BACKUP_NAME/.claude" . 2>/dev/null || true
cp "/tmp/$BACKUP_NAME/.env" . 2>/dev/null || true
cp -r "/tmp/$BACKUP_NAME/.workflow" . 2>/dev/null || true
cp -r "/tmp/$BACKUP_NAME/.phase" . 2>/dev/null || true

# Cleanup
rm -rf "/tmp/$BACKUP_NAME"

echo "✓ Restore complete"
