#!/usr/bin/env bash
# Learning Reuse Rate Metric
# Calculates percentage of items with prevention strategies

calculate_learning_reuse() {
  local learning_dir="$CE_HOME/.learning"

  if [[ ! -d "$learning_dir" ]]; then
    echo "N/A (no data)"
    return
  fi

  local total_items=0
  local with_prevention=0

  for item in "$learning_dir"/*.md "$learning_dir"/*.yml; do
    [[ -f "$item" ]] || continue
    ((total_items++))

    # Check if item has prevention strategy
    if grep -q "## Prevention Strategy" "$item" 2>/dev/null || \
       grep -q "prevention:" "$item" 2>/dev/null; then
      ((with_prevention++))
    fi
  done

  if [[ $total_items -eq 0 ]]; then
    echo "N/A (no items)"
    return
  fi

  local reuse_rate
  if command -v bc &>/dev/null; then
    reuse_rate=$(echo "scale=1; ($with_prevention * 100) / $total_items" | bc)
  else
    reuse_rate=$(( (with_prevention * 100) / total_items ))
  fi

  echo "${reuse_rate}%"
}
