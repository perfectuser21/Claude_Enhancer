#!/usr/bin/env bash
set -euo pipefail

# CE CLI Uninstallation Script
# Removes ce command and optionally backs up state

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🗑️  Uninstalling Claude Enhancer CE CLI..."

# Confirmation prompt
read -p "⚠️  This will remove CE CLI. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Uninstallation cancelled."
    exit 1
fi

# Step 1: Backup state (optional)
read -p "💾 Backup state files? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    BACKUP_DIR="$PROJECT_ROOT/.workflow/cli_backup_$(date +%Y%m%d_%H%M%S)"
    echo "📦 Creating backup at $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    cp -r "$SCRIPT_DIR/state" "$BACKUP_DIR/" 2>/dev/null || true
    cp "$SCRIPT_DIR/config.yml" "$BACKUP_DIR/" 2>/dev/null || true
    echo "   ✅ Backup created"
fi

# Step 2: Remove symlinks
echo "🔗 Removing symlinks..."
rm -f "$HOME/.local/bin/ce" 2>/dev/null || true
rm -f "/usr/local/bin/ce" 2>/dev/null || true

# Step 3: Clean directories (optional)
read -p "🧹 Clean state directories? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning state directories..."
    rm -rf "$SCRIPT_DIR/state/sessions/"* 2>/dev/null || true
    rm -rf "$SCRIPT_DIR/state/branches/"* 2>/dev/null || true
    rm -rf "$SCRIPT_DIR/state/locks/"* 2>/dev/null || true
    rm -f "$SCRIPT_DIR/state/global.state.yml" 2>/dev/null || true
    echo "   ✅ State cleaned"
fi

echo ""
echo "✅ Uninstallation complete!"
echo ""
if [ -n "${BACKUP_DIR:-}" ]; then
    echo "📦 Your state backup is at: $BACKUP_DIR"
fi
echo ""
