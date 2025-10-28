#!/usr/bin/env bash
# Validate Plan Execution - Anti-Hollow Gate v8.2
# Checks that PLAN items map to completed CHECKLIST items with evidence
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/id_mapping.sh"
source "$SCRIPT_DIR/lib/text_processing.sh"
source "$SCRIPT_DIR/lib/evidence_validation.sh"

# Configuration
PLAN_FILE="${1:-}"
CHECKLIST_FILE="${2:-}"
MAPPING_FILE=".workflow/PLAN_CHECKLIST_MAPPING.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Usage
usage() {
  cat <<EOF
Usage: $0 [PLAN_FILE] [CHECKLIST_FILE]

Validates that PLAN items are implemented and have evidence.

Options:
  PLAN_FILE       Path to PLAN.md (auto-detected if not specified)
  CHECKLIST_FILE  Path to CHECKLIST.md (auto-detected if not specified)

Examples:
  $0
  $0 docs/PLAN_xxx.md docs/ACCEPTANCE_CHECKLIST_xxx.md

Exit codes:
  0 - All validations passed
  1 - Validation failures detected
EOF
}

# Auto-detect files if not specified
auto_detect_files() {
  if [[ -z "$PLAN_FILE" ]]; then
    # Find PLAN file for current branch
    local branch
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

    # Extract feature name from branch
    # feature/anti-hollow-improvements → anti_hollow_improvements
    local feature
    feature=$(echo "$branch" | sed 's|^feature/||; s|-|_|g')

    PLAN_FILE="docs/PLAN_${feature}.md"

    if [[ ! -f "$PLAN_FILE" ]]; then
      # Fallback: find any PLAN file
      PLAN_FILE=$(find docs/ -name "PLAN_*.md" -type f 2>/dev/null | head -1)
    fi
  fi

  if [[ -z "$CHECKLIST_FILE" ]]; then
    # Derive checklist from plan filename
    local base
    base=$(basename "$PLAN_FILE" .md | sed 's/^PLAN_//')
    CHECKLIST_FILE="docs/ACCEPTANCE_CHECKLIST_${base}.md"
  fi

  # Derive mapping file
  if [[ -f "$PLAN_FILE" ]]; then
    local base
    base=$(basename "$PLAN_FILE" .md | sed 's/^PLAN_//')
    MAPPING_FILE=".workflow/PLAN_CHECKLIST_MAPPING_${base}.yml"

    # Fallback to default mapping file
    if [[ ! -f "$MAPPING_FILE" ]]; then
      MAPPING_FILE=".workflow/PLAN_CHECKLIST_MAPPING.yml"
    fi
  fi
}

# Validate using ID-based mapping
validate_with_id_mapping() {
  echo "🔍 Validating with ID-based mapping..."

  if [[ ! -f "$MAPPING_FILE" ]]; then
    echo -e "${RED}❌ Mapping file not found: $MAPPING_FILE${NC}"
    echo "   Generate with: bash scripts/generate_mapping.sh $PLAN_FILE"
    return 1
  fi

  local total_plan_items=0
  local completed_items=0
  local incomplete_items=0
  local missing_evidence=0

  # Get all plan IDs from mapping
  local plan_ids
  plan_ids=$(yq eval '.mappings[].plan_items[].id' "$MAPPING_FILE" 2>/dev/null)

  while IFS= read -r plan_id; do
    [[ -z "$plan_id" ]] && continue
    ((total_plan_items++))

    # Get plan item text for display
    local plan_text
    plan_text=$(yq eval ".mappings[].plan_items[] | select(.id == \"$plan_id\") | .text" "$MAPPING_FILE" 2>/dev/null | head -1)

    # Find mapped checklist items
    local checklist_ids
    checklist_ids=$(yq eval ".mappings[] | select(.plan_items[].id == \"$plan_id\") | .checklist_items[].id" "$MAPPING_FILE" 2>/dev/null)

    if [[ -z "$checklist_ids" ]]; then
      echo -e "${YELLOW}⚠️  $plan_id: No checklist items mapped${NC}"
      echo "   Plan: $plan_text"
      ((incomplete_items++))
      continue
    fi

    # Check each checklist item
    local all_completed=true

    while IFS= read -r cl_id; do
      [[ -z "$cl_id" ]] && continue

      # Find line with this checklist ID in CHECKLIST file
      local cl_line
      cl_line=$(grep -n "<!-- id: $cl_id" "$CHECKLIST_FILE" 2>/dev/null | head -1)

      if [[ -z "$cl_line" ]]; then
        echo -e "${RED}❌ $cl_id: Not found in checklist${NC}"
        all_completed=false
        continue
      fi

      # Extract line number
      local line_num
      line_num=$(echo "$cl_line" | cut -d: -f1)

      # Get the checklist item line (should be just before the comment)
      local item_line
      item_line=$(sed -n "$((line_num - 1))p" "$CHECKLIST_FILE" 2>/dev/null)

      # Check if [x] or [X]
      if [[ ! "$item_line" =~ \[x\]|\[X\] ]]; then
        all_completed=false
        break
      fi

      # Extract evidence ID from comment
      local comment_line
      comment_line=$(sed -n "${line_num}p" "$CHECKLIST_FILE" 2>/dev/null)

      local evidence_id
      evidence_id=$(extract_evidence_id_from_comment "$comment_line")

      if [[ -z "$evidence_id" ]]; then
        echo -e "${RED}❌ $cl_id: No evidence ID in comment${NC}"
        ((missing_evidence++))
        all_completed=false
        break
      fi

      # Validate evidence file
      local ev_file
      ev_file=$(find .evidence -type f -name "${evidence_id}.yml" 2>/dev/null | head -1)

      if [[ -z "$ev_file" ]]; then
        echo -e "${RED}❌ $cl_id: Evidence file not found: ${evidence_id}.yml${NC}"
        ((missing_evidence++))
        all_completed=false
        break
      fi

      # Validate evidence schema
      if ! validate_evidence_file "$ev_file" 2>&1 | grep -q "^❌"; then
        # Evidence is valid
        :
      else
        echo -e "${RED}❌ $cl_id: Evidence validation failed${NC}"
        validate_evidence_file "$ev_file"
        all_completed=false
        break
      fi

    done <<< "$checklist_ids"

    if $all_completed; then
      ((completed_items++))
      echo -e "${GREEN}✓${NC} $plan_id: Complete with evidence"
    else
      ((incomplete_items++))
    fi

  done <<< "$plan_ids"

  # Summary
  echo ""
  echo "═══════════════════════════════════════"
  echo "Validation Summary (ID-based)"
  echo "═══════════════════════════════════════"
  echo "Total Plan Items: $total_plan_items"
  echo -e "${GREEN}Completed: $completed_items${NC}"
  echo -e "${YELLOW}Incomplete: $incomplete_items${NC}"
  echo -e "${RED}Missing Evidence: $missing_evidence${NC}"

  local completion_rate=0
  if [[ $total_plan_items -gt 0 ]]; then
    completion_rate=$((completed_items * 100 / total_plan_items))
  fi

  echo "Completion Rate: ${completion_rate}%"

  if [[ $completion_rate -ge 90 ]]; then
    echo -e "${GREEN}✅ PASS: ≥90% completion${NC}"
    return 0
  else
    echo -e "${RED}❌ FAIL: <90% completion${NC}"
    return 1
  fi
}

# Validate using legacy text matching (fallback)
validate_legacy() {
  echo "🔍 Validating with legacy text matching..."
  echo "⚠️  This mode is less reliable. Consider migrating to ID-based system."

  # Extract plan content without code blocks
  local plan_content
  plan_content=$(strip_code_blocks < "$PLAN_FILE")

  # Simple validation: check for key requirements
  local total_checks=0
  local passed_checks=0

  # Example checks (customize based on project)
  local keywords=("Performance" "Testing" "Evidence" "Documentation")

  for keyword in "${keywords[@]}"; do
    ((total_checks++))

    if echo "$plan_content" | grep -qi "$keyword"; then
      # Check if mentioned in checklist
      if grep -qi "\[x\].*$keyword" "$CHECKLIST_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $keyword: Mentioned and completed"
        ((passed_checks++))
      else
        echo -e "${YELLOW}⚠️${NC}  $keyword: Mentioned but not completed"
      fi
    fi
  done

  echo ""
  echo "Legacy validation: $passed_checks/$total_checks checks passed"

  if [[ $passed_checks -eq $total_checks ]]; then
    return 0
  else
    return 1
  fi
}

# Main execution
main() {
  if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi

  auto_detect_files

  echo "═══════════════════════════════════════"
  echo "Anti-Hollow Gate - Plan Execution Validator"
  echo "═══════════════════════════════════════"
  echo "Plan: $PLAN_FILE"
  echo "Checklist: $CHECKLIST_FILE"
  echo "Mapping: $MAPPING_FILE"
  echo ""

  # Validate files exist
  if [[ ! -f "$PLAN_FILE" ]]; then
    echo -e "${RED}❌ Plan file not found: $PLAN_FILE${NC}"
    exit 1
  fi

  if [[ ! -f "$CHECKLIST_FILE" ]]; then
    echo -e "${RED}❌ Checklist file not found: $CHECKLIST_FILE${NC}"
    exit 1
  fi

  # Detect mode (ID-based vs legacy)
  if is_id_based_checklist "$CHECKLIST_FILE"; then
    validate_with_id_mapping
  else
    validate_legacy
  fi
}

main "$@"
