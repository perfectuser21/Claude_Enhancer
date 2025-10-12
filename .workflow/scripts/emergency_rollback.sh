#!/usr/bin/env bash
# Emergency Rollback Script - One-Command Recovery
# Usage: ./emergency_rollback.sh [reason]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

REASON="${1:-unspecified}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  EMERGENCY ROLLBACK - Enforcement v6.2 → v6.1             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Reason: $REASON"
echo "Started: $(date)"
echo ""

# Step 1: Create backup
echo "[1/7] Creating pre-rollback backup..."
BACKUP_DIR=".workflow/backups/rollback_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"
cp -r .ce/ "$BACKUP_DIR/ce/" 2>/dev/null || true
cp -r .gates/ "$BACKUP_DIR/gates/" 2>/dev/null || true
cp .git/hooks/pre-commit "$BACKUP_DIR/pre-commit.current" 2>/dev/null || true
cp .git/hooks/commit-msg "$BACKUP_DIR/commit-msg.current" 2>/dev/null || true
echo "   ✓ Backup created: $BACKUP_DIR"

# Step 2: Restore git hooks
echo "[2/7] Restoring git hooks from backup..."
HOOK_BACKUP=".git/hooks/backup_20251011_000000"
if [[ -d "$HOOK_BACKUP" ]]; then
    cp "$HOOK_BACKUP/pre-commit" .git/hooks/pre-commit
    cp "$HOOK_BACKUP/commit-msg" .git/hooks/commit-msg
    chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
    echo "   ✓ Git hooks restored"
else
    echo "   ⚠ Warning: Backup not found, using git history"
    git show HEAD~1:.git/hooks/pre-commit > .git/hooks/pre-commit
    git show HEAD~1:.git/hooks/commit-msg > .git/hooks/commit-msg
    chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
fi

# Step 3: Archive infrastructure
echo "[3/7] Archiving enforcement infrastructure..."
ARCHIVE_DIR=".workflow/archives/enforcement_$TIMESTAMP"
mkdir -p "$ARCHIVE_DIR"
[[ -d .ce ]] && mv .ce/ "$ARCHIVE_DIR/ce/" 2>/dev/null || true
[[ -d .gates ]] && mv .gates/ "$ARCHIVE_DIR/gates/" 2>/dev/null || true
echo "   ✓ Infrastructure archived: $ARCHIVE_DIR"

# Step 4: Remove new Claude hooks
echo "[4/7] Removing new Claude hooks..."
cd .claude/hooks/
rm -f branch_init.sh collect_agent_evidence.sh phase_enforcer.sh \
      gate_archiver.sh parallel_limit_enforcer.sh user_satisfaction_tracker.sh 2>/dev/null || true
cd "$PROJECT_ROOT"
echo "   ✓ New hooks removed"

# Step 5: Revert configuration
echo "[5/7] Reverting configuration files..."
git show HEAD~1:.workflow/gates.yml > .workflow/gates.yml 2>/dev/null || true
git show HEAD~1:.workflow/config.yml > .workflow/config.yml 2>/dev/null || true
sed -i '/hooks.enforcement_config/d' .claude/config.yaml 2>/dev/null || true
git checkout HEAD~1 -- .gitignore 2>/dev/null || true
echo "   ✓ Configuration reverted"

# Step 6: Verify rollback
echo "[6/7] Verifying rollback..."
ERRORS=0

# Test commit without enforcement
echo "test" > .rollback_test.txt
git add .rollback_test.txt
if git commit -m "test: verify rollback" --quiet 2>/dev/null; then
    echo "   ✓ Commits work without enforcement"
    git reset --soft HEAD~1  # Undo test commit
    rm .rollback_test.txt
else
    echo "   ✗ Commit test failed"
    ERRORS=$((ERRORS + 1))
fi

# Test git integrity
if git fsck --quick &>/dev/null; then
    echo "   ✓ Git integrity verified"
else
    echo "   ✗ Git integrity check failed"
    ERRORS=$((ERRORS + 1))
fi

if [[ $ERRORS -eq 0 ]]; then
    echo "   ✓ Rollback verification passed"
else
    echo "   ⚠ Rollback verification had $ERRORS errors"
fi

# Step 7: Create notification
echo "[7/7] Creating rollback notice..."
cat > ROLLBACK_NOTICE.md <<EOF
# Enforcement Rollback Notice

**Date**: $(date)
**Version**: v6.2 → v6.1
**Reason**: $REASON

## What Changed
- Enforcement hooks disabled
- .ce/ and .gates/ archived (not deleted)
- Configuration reverted to v6.1

## What Still Works
- All existing workflows (P0-P7)
- Git hooks (pre-commit, commit-msg)
- Claude Enhancer core features

## Data Preserved
- Historical gates: Archived in $ARCHIVE_DIR
- Backup created: $BACKUP_DIR

## Verification Status
- Commits: $([ $ERRORS -eq 0 ] && echo "✓ Working" || echo "⚠ Check required")
- Git integrity: $(git fsck --quick &>/dev/null && echo "✓ OK" || echo "⚠ Check required")

---
*Rollback completed at $(date)*
EOF

git add ROLLBACK_NOTICE.md
git commit -m "[ROLLBACK] Revert to v6.1 - enforcement disabled

Reason: $REASON
Evidence preserved in: $ARCHIVE_DIR

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>" 2>/dev/null || echo "   ⚠ Could not commit notice (manual commit required)"

echo "   ✓ Rollback notice created: ROLLBACK_NOTICE.md"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ROLLBACK COMPLETE                                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Duration: $((SECONDS))s"
echo "Status: $([ $ERRORS -eq 0 ] && echo "SUCCESS" || echo "PARTIAL (check errors above)")"
echo ""
echo "Next steps:"
echo "  1. Review ROLLBACK_NOTICE.md"
echo "  2. Notify team"
echo "  3. Run: ./.workflow/scripts/generate_incident_report.sh"
echo ""
