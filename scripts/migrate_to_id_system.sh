#!/usr/bin/env bash
# Migrate v8.1.0 projects to v8.2 ID-based system
# Usage: bash scripts/migrate_to_id_system.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/id_mapping.sh"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Anti-Hollow Gate Migration Tool                     ║"
echo "║  v8.1.0 → v8.2 (ID-based system)                     ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

if $DRY_RUN; then
  echo "🔍 DRY RUN MODE - No files will be modified"
  echo ""
fi

# Find PLAN and CHECKLIST files
PLAN_FILES=$(find docs/ -name "PLAN_*.md" -type f 2>/dev/null || echo "")
if [[ -z "$PLAN_FILES" ]]; then
  echo "❌ No PLAN files found in docs/"
  exit 1
fi

for PLAN_FILE in $PLAN_FILES; do
  echo "Processing: $PLAN_FILE"

  # Derive checklist filename
  base=$(basename "$PLAN_FILE" .md | sed 's/^PLAN_//')
  CHECKLIST_FILE="docs/ACCEPTANCE_CHECKLIST_${base}.md"

  if [[ ! -f "$CHECKLIST_FILE" ]]; then
    echo "⚠️  Checklist not found: $CHECKLIST_FILE - Skipping"
    continue
  fi

  # Check if already migrated
  if grep -q '<!-- id: CL-' "$CHECKLIST_FILE" 2>/dev/null; then
    echo "✓ Already migrated (has IDs)"
    continue
  fi

  echo "  → Generating mapping..."
  if $DRY_RUN; then
    echo "  [DRY RUN] Would generate mapping for $PLAN_FILE"
  else
    bash "$SCRIPT_DIR/generate_mapping.sh" "$PLAN_FILE"
  fi

  echo "  → Updating checklist with IDs..."
  # TODO: Parse mapping and update checklist with ID comments
  # This would require complex YAML parsing and text insertion
  # For now, print instructions

  if $DRY_RUN; then
    echo "  [DRY RUN] Would update $CHECKLIST_FILE with ID comments"
  else
    echo "  ⚠️  Manual step required:"
    echo "     Please review generated mapping and update checklist manually"
    echo "     Or run: bash scripts/update_checklist_ids.sh $CHECKLIST_FILE"
  fi

  echo ""
done

echo "✅ Migration complete"
echo ""
echo "Next steps:"
echo "1. Review generated .workflow/PLAN_CHECKLIST_MAPPING.yml files"
echo "2. Update checklist files with ID comments (if not auto-updated)"
echo "3. Test validation: bash scripts/validate_plan_execution.sh"
