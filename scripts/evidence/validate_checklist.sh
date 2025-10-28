#!/usr/bin/env bash
# Checklist Evidence Validator (v1.1 - ChatGPT Reviewed & Patched)
# Validates that all completed checklist items have evidence
#
# Fixes Applied:
# - P0-3: Line-skipping bug fixed (use nl -ba + sed -n)
# - P0-3: No nested read consuming input stream
# - P0-3: Index missing gracefully handled
# - P1-8: Evidence window = 5 lines (consistent with KPI)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Usage
usage() {
  cat << EOF
Usage: bash scripts/evidence/validate_checklist.sh <checklist_file>

Validates that all completed checklist items ([x]) have evidence comments.

Example:
  bash scripts/evidence/validate_checklist.sh \\
    docs/ACCEPTANCE_CHECKLIST_anti_hollow_gate.md

Evidence Format:
  - [x] 1.1 Task description
  <!-- evidence: EVID-2025W44-001 -->

Note: Evidence comment must appear within 5 lines after the [x] item.
EOF
  exit 1
}

# Check arguments
if [[ $# -lt 1 ]]; then
  echo -e "${RED}Error: Missing checklist file argument${NC}"
  usage
fi

CHECKLIST_FILE="$1"

if [[ ! -f "$CHECKLIST_FILE" ]]; then
  echo -e "${RED}Error: Checklist file not found: $CHECKLIST_FILE${NC}"
  exit 1
fi

# Detect CE_HOME
if [[ -z "${CE_HOME:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CE_HOME="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

EVIDENCE_INDEX="$CE_HOME/.evidence/index.json"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Evidence Validation - Anti-Hollow Gate                  ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Validating: $CHECKLIST_FILE${NC}"
echo ""

# Statistics
TOTAL_ITEMS=0
TOTAL_COMPLETED=0
WITH_EVIDENCE=0
MISSING_EVIDENCE=0
INVALID_EVIDENCE=0

# Count total items
TOTAL_ITEMS=$(grep -c "^- \[" "$CHECKLIST_FILE" || echo 0)

echo -e "${CYAN}Checklist Statistics:${NC}"
echo -e "  Total items: $TOTAL_ITEMS"
echo ""

if [[ $TOTAL_ITEMS -eq 0 ]]; then
  echo -e "${YELLOW}⚠️  No checklist items found${NC}"
  exit 0
fi

echo -e "${CYAN}Checking completed items...${NC}"
echo ""

# Validate each completed item (P0-3 fix: use nl -ba to preserve line numbers)
# This avoids the nested read bug that consumed input lines
while IFS=$'\t' read -r LINENO line; do
  # Match completed items: - [x] 1.1 Description
  if [[ "$line" =~ ^-\ \[x\]\ ([0-9]+\.[0-9]+)\ (.+)$ ]]; then
    ITEM_ID="${BASH_REMATCH[1]}"
    ITEM_DESC="${BASH_REMATCH[2]}"
    TOTAL_COMPLETED=$((TOTAL_COMPLETED + 1))

    # Look ahead 5 lines for evidence comment (P0-3 fix: use sed instead of nested read)
    # This prevents consuming lines from the main input stream
    EVIDENCE_FOUND=false
    LOOKAHEAD=$(sed -n "$((LINENO+1)),$((LINENO+5))p" "$CHECKLIST_FILE")

    if [[ -n "$LOOKAHEAD" ]]; then
      # Check for evidence comment: <!-- evidence: EVID-YYYYWWW-NNN -->
      if [[ "$LOOKAHEAD" =~ \<\!--\ evidence:\ (EVID-[0-9]{4}W[0-9]{2}-[0-9]{3})\ --\> ]]; then
        EVIDENCE_ID="${BASH_REMATCH[1]}"

        # Validate evidence ID exists in index (P0-3 fix: handle missing index gracefully)
        if [[ -f "$EVIDENCE_INDEX" ]]; then
          if jq -e ".evidence[] | select(.id == \"$EVIDENCE_ID\")" "$EVIDENCE_INDEX" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $ITEM_ID: $ITEM_DESC"
            echo -e "    ${CYAN}Evidence: $EVIDENCE_ID${NC}"
            WITH_EVIDENCE=$((WITH_EVIDENCE + 1))
            EVIDENCE_FOUND=true
          else
            echo -e "  ${RED}✗${NC} $ITEM_ID: $ITEM_DESC"
            echo -e "    ${RED}Evidence ID not found in index: $EVIDENCE_ID${NC}"
            echo -e "    ${YELLOW}Hint: Run 'bash scripts/evidence/collect.sh' to create evidence${NC}"
            INVALID_EVIDENCE=$((INVALID_EVIDENCE + 1))
            EVIDENCE_FOUND=true
          fi
        else
          echo -e "  ${RED}✗${NC} $ITEM_ID: $ITEM_DESC"
          echo -e "    ${RED}Evidence index missing: $EVIDENCE_INDEX${NC}"
          echo -e "    ${YELLOW}Hint: Evidence system not initialized${NC}"
          INVALID_EVIDENCE=$((INVALID_EVIDENCE + 1))
          EVIDENCE_FOUND=true
        fi
      fi
    fi

    # If no evidence found
    if [[ "$EVIDENCE_FOUND" == false ]]; then
      echo -e "  ${RED}✗${NC} $ITEM_ID: $ITEM_DESC"
      echo -e "    ${RED}Missing evidence comment (must be within 5 lines)${NC}"
      echo -e "    ${YELLOW}Hint: Add '<!-- evidence: EVID-... -->' after this item${NC}"
      MISSING_EVIDENCE=$((MISSING_EVIDENCE + 1))
    fi
  fi
done < <(nl -ba "$CHECKLIST_FILE")  # P0-3 fix: nl -ba adds line numbers without consuming input

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Validation Summary${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "  Total items:           $TOTAL_ITEMS"
echo -e "  Completed items:       $TOTAL_COMPLETED"
echo -e "  Items with evidence:   $WITH_EVIDENCE"
echo -e "  Missing evidence:      $MISSING_EVIDENCE"
echo -e "  Invalid evidence IDs:  $INVALID_EVIDENCE"

# Calculate completion rate
if [[ $TOTAL_ITEMS -gt 0 ]]; then
  COMPLETION_RATE=$((TOTAL_COMPLETED * 100 / TOTAL_ITEMS))
  echo -e "  Completion rate:       $COMPLETION_RATE%"
fi

# Calculate evidence compliance rate
if [[ $TOTAL_COMPLETED -gt 0 ]]; then
  COMPLIANCE_RATE=$((WITH_EVIDENCE * 100 / TOTAL_COMPLETED))
  echo -e "  Evidence compliance:   $COMPLIANCE_RATE%"
fi

echo ""

# Determine exit code
FAILED=$((MISSING_EVIDENCE + INVALID_EVIDENCE))

if [[ $TOTAL_COMPLETED -eq 0 ]]; then
  echo -e "${YELLOW}⚠️  No completed items found${NC}"
  echo -e "   Mark items as [x] when completed, then add evidence."
  exit 0
fi

if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}✅ All completed items have valid evidence${NC}"
  echo -e "   Evidence compliance: 100% ($WITH_EVIDENCE/$TOTAL_COMPLETED)"
  exit 0
else
  echo -e "${RED}❌ $FAILED item(s) missing or have invalid evidence${NC}"
  echo ""
  echo -e "${CYAN}To fix:${NC}"
  echo ""

  if [[ $MISSING_EVIDENCE -gt 0 ]]; then
    echo -e "${YELLOW}For missing evidence:${NC}"
    echo -e "  1. Collect evidence for each item:"
    echo -e "     ${CYAN}bash scripts/evidence/collect.sh \\${NC}"
    echo -e "       --type test_result \\
       --checklist-item X.X \\
       --description \"Evidence description\" \\
       --command \"test command\""
    echo ""
    echo -e "  2. Add evidence comment after the item:"
    echo -e "     - [x] X.X Task description"
    echo -e "     <!-- evidence: EVID-2025W44-001 -->"
    echo ""
  fi

  if [[ $INVALID_EVIDENCE -gt 0 ]]; then
    echo -e "${YELLOW}For invalid evidence IDs:${NC}"
    echo -e "  1. Check the evidence ID exists:"
    echo -e "     ${CYAN}ls .evidence/2025W44/${NC}"
    echo ""
    echo -e "  2. Verify index is up-to-date:"
    echo -e "     ${CYAN}cat .evidence/index.json${NC}"
    echo ""
    echo -e "  3. Re-collect evidence if needed"
    echo ""
  fi

  echo -e "${RED}Note: Anti-Hollow Gate requires 100% evidence compliance${NC}"
  echo -e "${RED}      before Phase 4+ transitions and merge.${NC}"
  echo ""

  exit 1
fi
