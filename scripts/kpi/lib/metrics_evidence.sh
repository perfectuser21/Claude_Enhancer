#!/usr/bin/env bash
# Evidence Compliance Rate Metric
# Calculates percentage of completed checklist items with evidence

calculate_evidence_compliance() {
  # Find all checklist files
  local checklists
  checklists=$(find "$CE_HOME/docs" -name "*CHECKLIST*.md" 2>/dev/null || echo "")

  if [[ -z "$checklists" ]]; then
    echo "N/A (no checklists)"
    return
  fi

  local total_completed=0
  local with_evidence=0

  while IFS= read -r checklist; do
    [[ -f "$checklist" ]] || continue

    # Count completed items [x]
    local completed=0
    if grep -q '^\- \[x\]' "$checklist" 2>/dev/null; then
      completed=$(grep -c '^\- \[x\]' "$checklist" 2>/dev/null)
    fi
    total_completed=$((total_completed + completed))

    # Count evidence comments within 5 lines of [x]
    # Use validate_checklist.sh logic
    local evidenced=0
    while IFS=$'\t' read -r lineno line; do
      if [[ "$line" =~ ^\-\ \[x\] ]]; then
        # Look ahead 5 lines for evidence comment
        local lookahead_end=$((lineno + 5))
        if sed -n "${lineno},${lookahead_end}p" "$checklist" | \
           grep -q '<!-- evidence: EVID-[0-9]\{4\}W[0-9]\{2\}-[0-9]\{3\} -->' 2>/dev/null; then
          ((evidenced++))
        fi
      fi
    done < <(nl -ba "$checklist" 2>/dev/null || cat -n "$checklist")

    with_evidence=$((with_evidence + evidenced))
  done <<< "$checklists"

  if [[ $total_completed -eq 0 ]]; then
    echo "N/A (no completed items)"
    return
  fi

  local compliance_rate
  if command -v bc &>/dev/null; then
    compliance_rate=$(echo "scale=1; ($with_evidence * 100) / $total_completed" | bc)
  else
    compliance_rate=$(( (with_evidence * 100) / total_completed ))
  fi

  echo "${compliance_rate}%"
}
