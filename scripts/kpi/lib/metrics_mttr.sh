#!/usr/bin/env bash
# Mean Time To Repair (MTTR) Metric
# Calculates average repair time from creation to resolution

calculate_mttr() {
  local learning_dir="$CE_HOME/.learning"

  if [[ ! -d "$learning_dir" ]]; then
    echo "N/A (no data)"
    return
  fi

  # Find Learning Items with resolution timestamps
  local total_time=0
  local resolved_count=0

  for item in "$learning_dir"/*.md "$learning_dir"/*.yml; do
    [[ -f "$item" ]] || continue

    # Extract creation time (from filename or file timestamp)
    local created
    if [[ "$(uname)" == "Darwin" ]]; then
      # macOS
      created=$(stat -f %B "$item")
    else
      # Linux
      created=$(stat -c %Y "$item")
    fi

    # Check if item has solution (marked as resolved)
    if grep -q "## Solution" "$item" 2>/dev/null || grep -q "solution:" "$item" 2>/dev/null; then
      # Item is resolved, calculate repair time
      local modified
      if [[ "$(uname)" == "Darwin" ]]; then
        modified=$(stat -f %m "$item")
      else
        modified=$(stat -c %Y "$item")
      fi

      local repair_time=$((modified - created))
      total_time=$((total_time + repair_time))
      ((resolved_count++))
    fi
  done

  if [[ $resolved_count -eq 0 ]]; then
    echo "N/A (no resolved items)"
    return
  fi

  # Calculate average in hours
  local avg_seconds=$((total_time / resolved_count))
  local avg_hours

  if command -v bc &>/dev/null; then
    avg_hours=$(echo "scale=1; $avg_seconds / 3600" | bc)
    # Handle empty result from bc
    if [[ -z "$avg_hours" ]]; then
      avg_hours="0.0"
    fi
  else
    avg_hours=$((avg_seconds / 3600))
  fi

  echo "${avg_hours}h"
}
