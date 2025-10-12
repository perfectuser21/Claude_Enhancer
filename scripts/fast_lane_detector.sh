#!/usr/bin/env bash
# Fast Lane Detector
# Analyzes changes to determine if they qualify for fast lane processing
#
# Fast lane criteria:
# - Documentation-only changes (*.md, *.txt, *.rst)
# - Comment-only changes in code
# - Whitespace/formatting fixes
# - Small file count (≤ 3 files)
# - No src/** changes

set -euo pipefail

# Configuration
MAX_FILES_FAST_LANE=3
MAX_LINES_CHANGED=50

# Output modes: "eligible" or "full_lane"
# Exit codes: 0 = fast lane, 1 = full lane

analyze_commit() {
  local ref="${1:-HEAD}"

  # Get list of changed files
  local changed_files
  if git rev-parse --verify HEAD >/dev/null 2>&1; then
    changed_files=$(git diff --cached --name-only "$ref" 2>/dev/null || git diff --name-only "$ref~1" "$ref" 2>/dev/null || echo "")
  else
    # Initial commit
    changed_files=$(git diff --cached --name-only --diff-filter=A)
  fi

  if [ -z "$changed_files" ]; then
    echo "No changes detected"
    return 1
  fi

  # Count files
  local file_count
  file_count=$(echo "$changed_files" | wc -l)

  # Check file count threshold
  if [ "$file_count" -gt "$MAX_FILES_FAST_LANE" ]; then
    echo "Too many files changed: $file_count > $MAX_FILES_FAST_LANE"
    return 1
  fi

  # Analyze each file
  local docs_only=true
  local comments_only=true
  local has_src_changes=false

  while IFS= read -r file; do
    # Check if file is documentation
    if [[ ! "$file" =~ \.(md|txt|rst|adoc)$ ]] && [[ ! "$file" =~ ^docs/ ]]; then
      docs_only=false
    fi

    # Check if src/** is modified
    if [[ "$file" =~ ^src/ ]]; then
      has_src_changes=true
    fi

    # Check if only comments changed (for code files)
    if [[ "$file" =~ \.(py|js|ts|sh|bash)$ ]]; then
      local diff_content
      diff_content=$(git diff --cached "$ref" -- "$file" 2>/dev/null || git diff "$ref~1" "$ref" -- "$file" 2>/dev/null || echo "")

      # Simple heuristic: if all added lines start with # or // or /* or *, it's comments
      local added_lines
      added_lines=$(echo "$diff_content" | grep -E '^\+' | grep -v '^\+\+\+' || true)

      if [ -n "$added_lines" ]; then
        # Check if any non-comment code was added
        if echo "$added_lines" | grep -Ev '^\+[[:space:]]*(#|//|/\*|\*|$)' >/dev/null; then
          comments_only=false
        fi
      fi
    fi

  done <<< "$changed_files"

  # Determine fast lane eligibility
  local total_lines
  total_lines=$(git diff --cached --shortstat "$ref" 2>/dev/null | grep -oP '\d+ insertion' | grep -oP '\d+' || echo "0")

  # Decision logic
  if [ "$docs_only" = true ]; then
    echo "Fast lane: Documentation-only changes"
    return 0
  fi

  if [ "$comments_only" = true ] && [ "$file_count" -le 2 ]; then
    echo "Fast lane: Comments-only changes"
    return 0
  fi

  if [ "$has_src_changes" = false ] && [ "$file_count" -le 2 ] && [ "$total_lines" -le "$MAX_LINES_CHANGED" ]; then
    echo "Fast lane: Non-src trivial changes"
    return 0
  fi

  # All other cases require full lane
  echo "Full lane required:"
  echo "  - Files changed: $file_count"
  echo "  - Lines inserted: $total_lines"
  echo "  - Docs only: $docs_only"
  echo "  - Comments only: $comments_only"
  echo "  - Has src/ changes: $has_src_changes"
  return 1
}

# CLI interface
main() {
  local mode="${1:-check}"
  local ref="${2:-HEAD}"

  case "$mode" in
    check)
      if analyze_commit "$ref"; then
        echo "Result: FAST_LANE_ELIGIBLE"
        exit 0
      else
        echo "Result: FULL_LANE_REQUIRED"
        exit 1
      fi
      ;;

    auto)
      # Auto-detect and set lane in task metadata
      local ROOT
      ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

      if [ ! -f "${ROOT}/.claude/core/task_namespace.sh" ]; then
        echo "Task namespace not initialized"
        exit 1
      fi

      # shellcheck source=../.claude/core/task_namespace.sh
      source "${ROOT}/.claude/core/task_namespace.sh"

      local TASK_ID
      TASK_ID=$(get_current_task)

      if [ -z "$TASK_ID" ]; then
        echo "No active task"
        exit 1
      fi

      local TASK_DIR
      TASK_DIR=$(get_task_dir "$TASK_ID")
      local TASK_META="${TASK_DIR}/task_meta.json"

      if analyze_commit "$ref"; then
        # Update task metadata to fast lane
        atomic_json_update "$TASK_META" ".lane" '"fast"'
        echo "Task $TASK_ID switched to fast lane"
        exit 0
      else
        # Ensure full lane
        atomic_json_update "$TASK_META" ".lane" '"full"'
        echo "Task $TASK_ID requires full lane"
        exit 1
      fi
      ;;

    *)
      echo "Usage: $0 {check|auto} [ref]"
      echo ""
      echo "Modes:"
      echo "  check  - Check if changes qualify for fast lane (exit 0 = yes)"
      echo "  auto   - Auto-detect and update task metadata"
      echo ""
      echo "Examples:"
      echo "  $0 check              # Check staged changes"
      echo "  $0 check HEAD         # Check last commit"
      echo "  $0 auto               # Auto-detect and update task"
      exit 1
      ;;
  esac
}

main "$@"
