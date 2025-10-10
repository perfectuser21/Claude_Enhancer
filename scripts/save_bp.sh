#!/usr/bin/env bash
set -euo pipefail

# Branch Protection Configuration Backup Script
# Saves current GitHub Branch Protection configuration to .bp_snapshot.json

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
fail(){ echo -e "${RED}✗ $*${NC}"; exit 1; }
ok(){ echo -e "${GREEN}✓ $*${NC}"; }
warn(){ echo -e "${YELLOW}⚠ $*${NC}"; }

echo "🛡️ Branch Protection Configuration Backup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Prerequisites check
command -v gh >/dev/null || fail "gh CLI not installed"
command -v jq >/dev/null || fail "jq not installed"
git rev-parse --is-inside-work-tree >/dev/null || fail "Not in a Git repository"

# Get repository info
OWNER_REPO=$(git remote get-url origin | sed -E 's#(git@|https://)([^:/]+)[:/](.+)\.git#\3#')
[ -n "$OWNER_REPO" ] || fail "Cannot parse repository origin"

echo "📦 Repository: $OWNER_REPO"

# Backup directory
BACKUP_DIR=".workflow/backups"
mkdir -p "$BACKUP_DIR"

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/bp_snapshot_${TIMESTAMP}.json"

# Fetch current Branch Protection configuration
echo "🔍 Fetching Branch Protection configuration from GitHub..."
BP_JSON=$(gh api repos/$OWNER_REPO/branches/main/protection 2>/dev/null || true)

if [ -z "$BP_JSON" ]; then
    fail "No Branch Protection configuration found for main branch"
fi

# Save to file
echo "$BP_JSON" | jq '.' > "$BACKUP_FILE"
ok "Configuration saved to: $BACKUP_FILE"

# Create symlink to latest backup
ln -sf "$(basename "$BACKUP_FILE")" "$BACKUP_DIR/bp_snapshot_latest.json"
ok "Latest backup symlink updated"

# Display summary
echo ""
echo "📊 Configuration Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ENFORCE_ADMINS=$(echo "$BP_JSON" | jq -r '.enforce_admins.enabled // false')
PR_REQUIRED=$(echo "$BP_JSON" | jq -r '.required_pull_request_reviews != null')
LINEAR_HISTORY=$(echo "$BP_JSON" | jq -r '.required_linear_history // false')
FORCE_PUSH=$(echo "$BP_JSON" | jq -r '.allow_force_pushes // false')
DELETE_BRANCH=$(echo "$BP_JSON" | jq -r '.allow_deletions // false')

echo "  • Enforce Admins: $ENFORCE_ADMINS"
echo "  • PR Required: $PR_REQUIRED"
echo "  • Linear History: $LINEAR_HISTORY"
echo "  • Allow Force Push: $FORCE_PUSH"
echo "  • Allow Delete Branch: $DELETE_BRANCH"

echo ""
ok "Backup completed successfully!"
echo "📝 To restore this configuration, run:"
echo "   ./scripts/restore_bp.sh $BACKUP_FILE"
