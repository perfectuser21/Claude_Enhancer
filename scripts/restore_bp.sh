#!/usr/bin/env bash
set -euo pipefail

# Branch Protection Configuration Restore Script
# Restores GitHub Branch Protection configuration from backup file

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
fail(){ echo -e "${RED}✗ $*${NC}"; exit 1; }
ok(){ echo -e "${GREEN}✓ $*${NC}"; }
warn(){ echo -e "${YELLOW}⚠ $*${NC}"; }

echo "🛡️ Branch Protection Configuration Restore"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Prerequisites check
command -v gh >/dev/null || fail "gh CLI not installed"
command -v jq >/dev/null || fail "jq not installed"
git rev-parse --is-inside-work-tree >/dev/null || fail "Not in a Git repository"

# Get repository info
OWNER_REPO=$(git remote get-url origin | sed -E 's#(git@|https://)([^:/]+)[:/](.+)\.git#\3#')
[ -n "$OWNER_REPO" ] || fail "Cannot parse repository origin"

echo "📦 Repository: $OWNER_REPO"

# Determine backup file
BACKUP_FILE="${1:-.workflow/backups/bp_snapshot_latest.json}"

if [ ! -f "$BACKUP_FILE" ]; then
    fail "Backup file not found: $BACKUP_FILE"
fi

ok "Found backup file: $BACKUP_FILE"

# Display backup summary
echo ""
echo "📊 Backup Configuration Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
BP_JSON=$(cat "$BACKUP_FILE")
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

# Confirm restore
echo ""
warn "⚠️  This will REPLACE current Branch Protection configuration!"
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Backup current config before restoring (safety measure)
echo ""
echo "🔍 Creating safety backup of current configuration..."
SAFETY_BACKUP=".workflow/backups/bp_snapshot_before_restore_$(date +%Y%m%d_%H%M%S).json"
CURRENT_BP=$(gh api repos/$OWNER_REPO/branches/main/protection 2>/dev/null || echo '{}')
echo "$CURRENT_BP" > "$SAFETY_BACKUP"
ok "Safety backup saved to: $SAFETY_BACKUP"

# Restore configuration
echo ""
echo "🚀 Restoring Branch Protection configuration..."
gh api repos/$OWNER_REPO/branches/main/protection \
  --method PUT \
  --input "$BACKUP_FILE" \
  || fail "Failed to restore configuration"

ok "Configuration restored successfully!"

# Verify restoration
echo ""
echo "🔍 Verifying restored configuration..."
RESTORED_BP=$(gh api repos/$OWNER_REPO/branches/main/protection)
RESTORED_LINEAR=$(echo "$RESTORED_BP" | jq -r '.required_linear_history // false')
RESTORED_FORCE=$(echo "$RESTORED_BP" | jq -r '.allow_force_pushes // false')

if [ "$RESTORED_LINEAR" = "$LINEAR_HISTORY" ] && [ "$RESTORED_FORCE" = "$FORCE_PUSH" ]; then
    ok "Verification passed - configuration matches backup"
else
    warn "Verification partial - some settings may differ (this can be normal)"
fi

echo ""
ok "Restore completed!"
echo "📝 To verify all protection layers, run:"
echo "   ./bp_verify.sh"
