#!/usr/bin/env bash
set -euo pipefail

# CE CLI Installation Script
# Sets up the ce command for multi-terminal development automation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Installing Claude Enhancer CE CLI..."
echo "   Project root: $PROJECT_ROOT"

# Step 1: Create directories
echo "📁 Creating directories..."
mkdir -p "$SCRIPT_DIR/state/sessions"
mkdir -p "$SCRIPT_DIR/state/branches"
mkdir -p "$SCRIPT_DIR/state/locks"
mkdir -p "$SCRIPT_DIR/commands"
mkdir -p "$SCRIPT_DIR/lib"
mkdir -p "$SCRIPT_DIR/templates"

# Step 2: Initialize global state if not exists
if [ ! -f "$SCRIPT_DIR/state/global.state.yml" ]; then
    echo "🔧 Initializing global state..."
    cat > "$SCRIPT_DIR/state/global.state.yml" <<'EOF'
active_terminals: []
active_branches: []
resource_locks: {}
last_cleanup: null
statistics:
  total_sessions: 0
  total_branches: 0
  total_merges: 0
EOF
fi

# Step 3: Set permissions
echo "🔐 Setting permissions..."
chmod 755 "$SCRIPT_DIR/ce.sh" 2>/dev/null || true
chmod 755 "$SCRIPT_DIR/install.sh"
chmod 755 "$SCRIPT_DIR/uninstall.sh" 2>/dev/null || true
chmod 755 "$SCRIPT_DIR/commands/"*.sh 2>/dev/null || true
chmod 644 "$SCRIPT_DIR/lib/"*.sh 2>/dev/null || true
chmod 755 "$SCRIPT_DIR/state"
chmod 755 "$SCRIPT_DIR/state/sessions"
chmod 755 "$SCRIPT_DIR/state/branches"
chmod 755 "$SCRIPT_DIR/state/locks"

# Step 4: Create symlink (optional)
if [ -d "$HOME/.local/bin" ]; then
    echo "🔗 Creating symlink in ~/.local/bin..."
    ln -sf "$SCRIPT_DIR/ce.sh" "$HOME/.local/bin/ce" || echo "   ⚠️  Symlink creation failed (you may need sudo)"
fi

# Step 5: Setup completion (future)
# TODO: Setup bash/zsh completion

# Step 6: Verify installation
echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Add to PATH: export PATH=\"$SCRIPT_DIR:\$PATH\""
echo "   2. Or use symlink: ln -s $SCRIPT_DIR/ce.sh /usr/local/bin/ce"
echo "   3. Test: ce status"
echo ""
echo "💡 Tips:"
echo "   - Run 'ce start <feature>' to begin a new task"
echo "   - Run 'ce status' to see current state"
echo "   - Run 'ce --help' for full command list"
echo ""
