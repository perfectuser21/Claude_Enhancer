#!/usr/bin/env bash
# Auto-Fix Success Rate Metric
# Calculates rollback rate vs total fix attempts

calculate_autofix_success() {
  local rollback_log="$KPI_DIR/rollback.log"

  if [[ ! -f "$rollback_log" ]]; then
    echo "N/A (no data)"
    return
  fi

  # Count rollback events (failed fixes)
  local failed_count
  failed_count=$(wc -l < "$rollback_log" || echo "0")

  # Count Learning Items (total fix attempts - proxy)
  local total_items
  total_items=$(find "$CE_HOME/.learning" -name "*.md" -o -name "*.yml" 2>/dev/null | wc -l || echo "0")

  if [[ $total_items -eq 0 ]]; then
    echo "N/A (no fixes)"
    return
  fi

  local success_count=$((total_items - failed_count))
  local success_rate

  # Cross-platform arithmetic (use bc if available, fallback to integer math)
  if command -v bc &>/dev/null; then
    success_rate=$(echo "scale=1; ($success_count * 100) / $total_items" | bc)
  else
    success_rate=$(( (success_count * 100) / total_items ))
  fi

  echo "${success_rate}%"
}
