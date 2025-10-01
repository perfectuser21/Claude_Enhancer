#!/bin/bash
# Fix Git Hooks Permissions - Claude Enhancer 5.0
# DevOps Engineer Agent - Simple & Efficient

set -euo pipefail

# Colors for clean output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Project root and key directories
readonly PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
readonly GITHOOKS_DIR="$PROJECT_ROOT/.githooks"
readonly GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${BLUE}🔧 Git Hooks Permission Fix${NC}"
echo "══════════════════════════════════════════════════════════"

# 1. Check .githooks directory
if [[ ! -d "$GITHOOKS_DIR" ]]; then
    log_error ".githooks directory not found"
    exit 1
fi

log_info "Fixing permissions for .githooks/*"

# 2. Fix permissions for all files in .githooks
find "$GITHOOKS_DIR" -type f -exec chmod +x {} \;

# 3. Verify and set git config
current_hooks_path=$(git config --get core.hooksPath 2>/dev/null || echo "")

if [[ "$current_hooks_path" != ".githooks" ]]; then
    log_info "Setting git config core.hooksPath to .githooks"
    git config core.hooksPath .githooks
else
    log_info "Git hooks path already configured correctly"
fi

# 4. Enable file mode tracking
git config --local core.filemode true 2>/dev/null || true

# 5. Verification and results
echo -e "\n${BLUE}📊 Verification Results${NC}"
echo "──────────────────────────────────────────────────────────"

echo "📁 Hooks Directory: $(find "$GITHOOKS_DIR" -type f | wc -l) files"
echo "🔧 Git Config: core.hooksPath = $(git config --get core.hooksPath)"
echo "✅ Executable Files:"

find "$GITHOOKS_DIR" -type f -executable | while read -r file; do
    echo "   $(basename "$file") - $(stat -c '%A' "$file")"
done

log_info "Permission fix completed successfully"
exit 0