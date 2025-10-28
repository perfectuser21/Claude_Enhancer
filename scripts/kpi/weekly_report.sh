#!/usr/bin/env bash
# KPI Dashboard - Anti-Hollow Gate Weekly Report
# Generates 4 key metrics for quality assurance

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Detect CE_HOME
if [[ -z "${CE_HOME:-}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  CE_HOME="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

KPI_DIR="$CE_HOME/.kpi"
mkdir -p "$KPI_DIR"

# ============================================================================
# Load Metric Calculation Modules
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/metrics_autofix.sh"
source "$SCRIPT_DIR/lib/metrics_mttr.sh"
source "$SCRIPT_DIR/lib/metrics_learning.sh"
source "$SCRIPT_DIR/lib/metrics_evidence.sh"

# ============================================================================
# Module 5: Generate Report
# ============================================================================
generate_report() {
  local week_num
  week_num=$(date +%GW%V)

  echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║  Anti-Hollow Gate - Weekly KPI Report                   ║${NC}"
  echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${CYAN}Report Period:${NC} Week $week_num"
  echo -e "${CYAN}Generated:${NC} $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  echo ""

  # Calculate metrics
  local autofix_success
  autofix_success=$(calculate_autofix_success)

  local mttr
  mttr=$(calculate_mttr)

  local learning_reuse
  learning_reuse=$(calculate_learning_reuse)

  local evidence_compliance
  evidence_compliance=$(calculate_evidence_compliance)

  # Display metrics
  echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${CYAN}  Key Performance Indicators${NC}"
  echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
  echo ""

  echo -e "  ${CYAN}1. Auto-Fix Success Rate${NC}"
  echo -e "     Current: $autofix_success"
  echo -e "     Target:  ≥80%"
  echo ""

  echo -e "  ${CYAN}2. Mean Time To Repair (MTTR)${NC}"
  echo -e "     Current: $mttr"
  echo -e "     Target:  <24h"
  echo ""

  echo -e "  ${CYAN}3. Learning Reuse Rate${NC}"
  echo -e "     Current: $learning_reuse"
  echo -e "     Target:  ≥50%"
  echo ""

  echo -e "  ${CYAN}4. Evidence Compliance Rate${NC}"
  echo -e "     Current: $evidence_compliance"
  echo -e "     Target:  100%"
  echo ""

  # Save baseline if first run
  local baseline_file="$KPI_DIR/baseline.json"
  if [[ ! -f "$baseline_file" ]]; then
    cat > "$baseline_file" <<EOF
{
  "week": "$week_num",
  "date": "$(date -u +"%Y-%m-%d")",
  "autofix_success": "$autofix_success",
  "mttr": "$mttr",
  "learning_reuse": "$learning_reuse",
  "evidence_compliance": "$evidence_compliance"
}
EOF
    echo -e "${GREEN}✓${NC} Baseline established for Week $week_num"
    echo ""
  fi

  # Append to history
  local history_file="$KPI_DIR/history.jsonl"
  echo "{\"week\":\"$week_num\",\"autofix\":\"$autofix_success\",\"mttr\":\"$mttr\",\"reuse\":\"$learning_reuse\",\"evidence\":\"$evidence_compliance\"}" >> "$history_file"
}

# ============================================================================
# Main Entry Point
# ============================================================================
main() {
  local mode="${1:-interactive}"

  if [[ "$mode" == "--auto" ]]; then
    # Auto mode: generate report silently, return JSON
    local autofix mttr reuse evidence
    autofix=$(calculate_autofix_success)
    mttr=$(calculate_mttr)
    reuse=$(calculate_learning_reuse)
    evidence=$(calculate_evidence_compliance)

    echo "{\"autofix\":\"$autofix\",\"mttr\":\"$mttr\",\"reuse\":\"$reuse\",\"evidence\":\"$evidence\"}"
  else
    # Interactive mode: full report with colors
    generate_report
  fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
