#!/bin/bash
# Cleanup Legacy P0/P1 Documentation Files
# Part of Option B: Thorough Cleanup
# Date: 2025-10-19

set -euo pipefail

PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
DOCS_DIR="$PROJECT_ROOT/docs"
EVIDENCE_FILE="/tmp/doc_cleanup_evidence.txt"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Legacy Documentation Cleanup Script                       ║"
echo "║  Option B: Thorough Cleanup                                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Collect BEFORE evidence
echo "═══ BEFORE CLEANUP ===" > "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "📊 Collecting before-state evidence..."
echo "Total P0_*.md files:" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "P0_*.md" 2>/dev/null | wc -l >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Total P1_*.md files:" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "P1_*.md" 2>/dev/null | wc -l >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Total backup files:" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "*backup*.md" 2>/dev/null | wc -l >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Disk usage (docs/):" >> "$EVIDENCE_FILE"
du -sh "$DOCS_DIR" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Old Phase references in DECISION_TREE.md:" >> "$EVIDENCE_FILE"
grep -c "Phase 0\|Phase -1" "$DOCS_DIR/DECISION_TREE.md" >> "$EVIDENCE_FILE" || echo "0" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Old Phase references in WORKFLOW_VALIDATION.md:" >> "$EVIDENCE_FILE"
grep -c "Phase 0\|Phase -1" "$DOCS_DIR/WORKFLOW_VALIDATION.md" >> "$EVIDENCE_FILE" || echo "0" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Files to be deleted:" >> "$EVIDENCE_FILE"
echo "════════════════════" >> "$EVIDENCE_FILE"

# List P0 files (excluding P0_DISCOVERY.md)
echo "" >> "$EVIDENCE_FILE"
echo "P0 Files (15):" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "P0_*.md" ! -name "P0_DISCOVERY.md" -exec ls -lh {} \; >> "$EVIDENCE_FILE" 2>/dev/null

# List P1 files
echo "" >> "$EVIDENCE_FILE"
echo "P1 Files (5):" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "P1_*.md" -exec ls -lh {} \; >> "$EVIDENCE_FILE" 2>/dev/null

# List backup files
echo "" >> "$EVIDENCE_FILE"
echo "Backup Files (2):" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "*backup*.md" -exec ls -lh {} \; >> "$EVIDENCE_FILE" 2>/dev/null

echo "✅ Before-state evidence collected"
echo ""

# DELETE Phase
echo "🗑️  Deleting legacy files..."
echo ""

DELETED_COUNT=0

# Delete P0 files (keep P0_DISCOVERY.md)
echo "Deleting P0 files..."
for file in \
    "P0_GIT_BRANCH_PR_AUTOMATION_SPIKE.md" \
    "P0_AUDIT_FIX_DISCOVERY.md" \
    "P0_DELIVERABLES_SUMMARY.md" \
    "P0_AI_PARALLEL_DEV_DISCOVERY.md" \
    "P0_FULL_AUTOMATION_DISCOVERY.md" \
    "P0_ARCHITECTURE_DIAGRAM.md" \
    "P0_ENFORCEMENT_OPTIMIZATION_DISCOVERY.md" \
    "P0_DECISION_TREE.md" \
    "P0_QUICK_REFERENCE.md" \
    "P0_enforcement_optimization_DISCOVERY_TEMPLATE.md" \
    "P0_SUMMARY.md" \
    "P0_enforcement_optimization_DISCOVERY.md" \
    "P0_RELEASE_AUTOMATION_DISCOVERY.md" \
    "P0_PHASE_MINUS1_FIX_DISCOVERY.md" \
    "P0_TASK_BRANCH_BINDING_DISCOVERY.md"
do
    if [ -f "$DOCS_DIR/$file" ]; then
        rm -fv "$DOCS_DIR/$file"
        ((DELETED_COUNT++))
    fi
done

echo ""
echo "Deleting P1 files..."
for file in \
    "P1_PLANNING_COMPLETE_SUMMARY.md" \
    "P1_CE_COMMAND_ARCHITECTURE.md" \
    "P1_ROLLBACK_DELIVERABLES_SUMMARY.md" \
    "P1_PHASE_MINUS1_FIX_PLAN.md" \
    "P1_TASK_BRANCH_BINDING_PLAN.md"
do
    if [ -f "$DOCS_DIR/$file" ]; then
        rm -fv "$DOCS_DIR/$file"
        ((DELETED_COUNT++))
    fi
done

echo ""
echo "Deleting backup files..."
for file in \
    "PLAN_doc_fix_backup.md" \
    "REVIEW_phase_enforcement_backup.md"
do
    if [ -f "$DOCS_DIR/$file" ]; then
        rm -fv "$DOCS_DIR/$file"
        ((DELETED_COUNT++))
    fi
done

echo ""
echo "✅ Deleted $DELETED_COUNT files"
echo ""

# Collect AFTER evidence
echo "" >> "$EVIDENCE_FILE"
echo "═══ AFTER CLEANUP ===" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Remaining P0_*.md files:" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "P0_*.md" 2>/dev/null | wc -l >> "$EVIDENCE_FILE"
echo "(Should be 1: P0_DISCOVERY.md)" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Remaining P1_*.md files:" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "P1_*.md" 2>/dev/null | wc -l >> "$EVIDENCE_FILE"
echo "(Should be 0)" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Remaining backup files:" >> "$EVIDENCE_FILE"
find "$DOCS_DIR" -name "*backup*.md" 2>/dev/null | wc -l >> "$EVIDENCE_FILE"
echo "(Should be 0)" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Disk usage (docs/):" >> "$EVIDENCE_FILE"
du -sh "$DOCS_DIR" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

echo "Files still to update:" >> "$EVIDENCE_FILE"
echo "- DECISION_TREE.md: Phase 0/Phase -1 references" >> "$EVIDENCE_FILE"
echo "- WORKFLOW_VALIDATION.md: Phase 0/Phase -1 references" >> "$EVIDENCE_FILE"
echo "" >> "$EVIDENCE_FILE"

# Summary
echo "" >> "$EVIDENCE_FILE"
echo "═══ SUMMARY ===" >> "$EVIDENCE_FILE"
echo "Files deleted: $DELETED_COUNT" >> "$EVIDENCE_FILE"
echo "Disk space freed: [calculated from du diff]" >> "$EVIDENCE_FILE"
echo "Next steps: Update DECISION_TREE.md and WORKFLOW_VALIDATION.md" >> "$EVIDENCE_FILE"

echo "📋 Evidence report generated: $EVIDENCE_FILE"
echo ""
cat "$EVIDENCE_FILE"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Legacy Documentation Cleanup Complete                  ║"
echo "║  Files deleted: $DELETED_COUNT                             ║"
echo "║  Evidence saved to: $EVIDENCE_FILE                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
