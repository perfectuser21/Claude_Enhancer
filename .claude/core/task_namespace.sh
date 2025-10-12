#!/usr/bin/env bash
# Core task namespace library
# Source this file in hooks and scripts

set -euo pipefail

# Initialize environment
ROOT="${CLAUDE_ENHANCER_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
GATES_PATH="${ROOT}/.gates"
INDEX_FILE="${GATES_PATH}/_index.json"
LOCK_TIMEOUT=5

# Atomic file operations
source "${ROOT}/.claude/core/atomic_ops.sh" 2>/dev/null || true

# Get current active task ID
get_current_task() {
  if [ ! -f "$INDEX_FILE" ]; then
    return 1
  fi

  jq -r '.active_task_id // empty' "$INDEX_FILE" 2>/dev/null || true
}

# Get task directory
get_task_dir() {
  local task_id="${1:-$(get_current_task)}"

  if [ -z "$task_id" ]; then
    return 1
  fi

  echo "${GATES_PATH}/${task_id}"
}

# Record evidence entry
record_evidence() {
  local task_id="${1:-$(get_current_task)}"
  local entry="$2"

  if [ -z "$task_id" ]; then
    echo "⚠️  No active task, skipping evidence recording" >&2
    return 0
  fi

  local task_dir
  task_dir=$(get_task_dir "$task_id")
  local evidence_file="${task_dir}/evidence.json"

  if [ ! -f "$evidence_file" ]; then
    echo "⚠️  Evidence file not found: $evidence_file" >&2
    return 1
  fi

  # Atomic append
  atomic_json_append "$evidence_file" ".entries" "$entry"
}

# Record agent invocation
record_agent() {
  local task_id="${1:-$(get_current_task)}"
  local agent_name="$2"
  local context="${3:-}"

  if [ -z "$task_id" ]; then
    echo "⚠️  No active task, skipping agent recording" >&2
    return 0
  fi

  local task_dir
  task_dir=$(get_task_dir "$task_id")
  local agents_file="${task_dir}/agents.json"

  local invocation
  invocation=$(jq -n \
    --arg agent "$agent_name" \
    --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg ctx "$context" \
    '{
      "agent": $agent,
      "timestamp": $ts,
      "context": $ctx,
      "pid": $ENV.pid
    }' --arg pid "$$")

  atomic_json_append "$agents_file" ".invocations" "$invocation"
}

# Update task phase
update_task_phase() {
  local task_id="${1:-$(get_current_task)}"
  local new_phase="$2"

  if [ -z "$task_id" ]; then
    echo "❌ No active task" >&2
    return 1
  fi

  local task_dir
  task_dir=$(get_task_dir "$task_id")
  local meta_file="${task_dir}/task_meta.json"

  # Validate phase progression
  local current_phase
  current_phase=$(jq -r '.phase' "$meta_file")
  local current_num="${current_phase#P}"
  local new_num="${new_phase#P}"

  if (( new_num <= current_num )); then
    echo "⚠️  Phase regression detected: $current_phase → $new_phase" >&2
  fi

  # Atomic update
  atomic_json_update "$meta_file" ".phase" "\"$new_phase\""

  # Update index
  (
    flock -w $LOCK_TIMEOUT 200 || exit 1

    local temp
    temp=$(mktemp)
    jq --arg id "$task_id" --arg phase "$new_phase" \
      '.tasks[$id].phase = $phase' \
      "$INDEX_FILE" > "$temp"

    mv "$temp" "$INDEX_FILE"

  ) 200>"${INDEX_FILE}.lock"

  rm -f "${INDEX_FILE}.lock"
}

# Mark phase as complete
complete_phase() {
  local task_id="${1:-$(get_current_task)}"
  local phase="$2"

  if [ -z "$task_id" ]; then
    echo "❌ No active task" >&2
    return 1
  fi

  local task_dir
  task_dir=$(get_task_dir "$task_id")
  local phase_num="${phase#P}"
  local gate_file="${task_dir}/${phase_num}.ok"

  # Create gate marker
  cat > "$gate_file" <<EOF
Phase $phase completed successfully

Task: $task_id
Completed: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Commit: $(git rev-parse HEAD 2>/dev/null || echo 'none')
EOF

  echo "✅ Phase $phase gate created: $gate_file"
}

# Check if phase is complete
is_phase_complete() {
  local task_id="${1:-$(get_current_task)}"
  local phase="$2"

  if [ -z "$task_id" ]; then
    return 1
  fi

  local task_dir
  task_dir=$(get_task_dir "$task_id")
  local phase_num="${phase#P}"
  local gate_file="${task_dir}/${phase_num}.ok"

  [ -f "$gate_file" ]
}

# Get agent count for task
get_agent_count() {
  local task_id="${1:-$(get_current_task)}"

  if [ -z "$task_id" ]; then
    echo "0"
    return
  fi

  local task_dir
  task_dir=$(get_task_dir "$task_id")
  local agents_file="${task_dir}/agents.json"

  if [ ! -f "$agents_file" ]; then
    echo "0"
    return
  fi

  jq '.invocations | length' "$agents_file" 2>/dev/null || echo "0"
}

# Export functions for use in other scripts
export -f get_current_task
export -f get_task_dir
export -f record_evidence
export -f record_agent
export -f update_task_phase
export -f complete_phase
export -f is_phase_complete
export -f get_agent_count
