#!/usr/bin/env bash
# Initialize a new task namespace
# Usage: ./init_task_namespace.sh [phase] [description]

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CONFIG="$ROOT/.claude/config.yml"
INDEX_FILE="$ROOT/.gates/_index.json"

# Load configuration
if command -v yq >/dev/null 2>&1 && [ -f "$CONFIG" ]; then
  GATES_PATH=$(yq e '.enforcement.task_namespace.path' "$CONFIG" 2>/dev/null || echo ".gates")
else
  GATES_PATH=".gates"
fi

# Generate atomic task ID
generate_task_id() {
  local phase="${1:-P0}"
  local timestamp
  timestamp=$(date +%Y%m%d_%H%M%S)
  local pid=$$
  local uuid
  uuid=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)

  echo "${phase}_${timestamp}_${pid}_${uuid}"
}

# Atomic write to index
atomic_update_index() {
  local task_id="$1"
  local temp_file="${INDEX_FILE}.tmp.$$"

  # Use flock for exclusive access
  (
    flock -x 200 || exit 1

    if [ ! -f "$INDEX_FILE" ]; then
      echo '{"version":"1.0.0","tasks":{},"active_task_id":null,"metadata":{"total_tasks":0}}' > "$INDEX_FILE"
    fi

    jq --arg id "$task_id" \
       --arg created "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
       --arg phase "${PHASE:-P0}" \
       --arg branch "$(git branch --show-current 2>/dev/null || echo 'unknown')" \
       '.tasks[$id] = {
          "created_at": $created,
          "phase": $phase,
          "status": "in_progress",
          "branch": $branch,
          "lane": "full"
        } | .active_task_id = $id | .metadata.total_tasks += 1' \
       "$INDEX_FILE" > "$temp_file"

    mv "$temp_file" "$INDEX_FILE"

  ) 200>"${INDEX_FILE}.lock"

  rm -f "${INDEX_FILE}.lock"
}

# Main execution
main() {
  local phase="${1:-P0}"
  local description="${2:-}"

  # Validate phase
  if ! [[ "$phase" =~ ^P[0-7]$ ]]; then
    echo "❌ Invalid phase: $phase (must be P0-P7)" >&2
    exit 1
  fi

  # Generate task ID
  TASK_ID=$(generate_task_id "$phase")
  TASK_DIR="$ROOT/$GATES_PATH/$TASK_ID"

  # Create task directory
  mkdir -p "$TASK_DIR"

  # Create task metadata
  cat > "$TASK_DIR/task_meta.json" <<EOF
{
  "task_id": "$TASK_ID",
  "phase": "$phase",
  "description": "$description",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
  "commit": "$(git rev-parse HEAD 2>/dev/null || echo 'none')",
  "lane": "full",
  "status": "in_progress"
}
EOF

  # Initialize evidence file
  cat > "$TASK_DIR/evidence.json" <<EOF
{
  "task_id": "$TASK_ID",
  "entries": []
}
EOF

  # Initialize agents file
  cat > "$TASK_DIR/agents.json" <<EOF
{
  "task_id": "$TASK_ID",
  "invocations": []
}
EOF

  # Update central index
  atomic_update_index "$TASK_ID"

  echo "✅ Task namespace created: $TASK_ID"
  echo "   Path: $TASK_DIR"
  echo "   Phase: $phase"
  [ -n "$description" ] && echo "   Description: $description"

  # Export for other scripts
  echo "$TASK_ID"
}

main "$@"
