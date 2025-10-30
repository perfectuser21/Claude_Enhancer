#!/usr/bin/env bash
# Agent Evidence Collector Hook (Simplified v2.0)
# Purpose: Record agent invocations for quality gate enforcement
# No external dependencies - self-contained
#
# Hook Type: PreToolUse
# Triggers: Before Task tool execution
# Output: .workflow/agent_evidence/agents_YYYYMMDD.jsonl

set -euo pipefail

# Initialize environment
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
EVIDENCE_DIR="${ROOT}/.workflow/agent_evidence"
mkdir -p "$EVIDENCE_DIR"

# Get tool invocation info
TOOL_NAME="${1:-unknown}"
AGENT_TYPE="${2:-}"

# Only track Task tool invocations (agent launches)
if [ "$TOOL_NAME" != "Task" ]; then
  exit 0
fi

# Extract agent type from stdin if not provided
if [ -z "$AGENT_TYPE" ] && [ ! -t 0 ]; then
  # Read JSON from stdin
  JSON_INPUT=$(cat)
  AGENT_TYPE=$(echo "$JSON_INPUT" | jq -r '.subagent_type // empty' 2>/dev/null || echo "")
fi

if [ -z "$AGENT_TYPE" ]; then
  echo "⚠️  Could not determine agent type" >&2
  exit 0
fi

# Record agent invocation
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EVIDENCE_FILE="${EVIDENCE_DIR}/agents_$(date +%Y%m%d).jsonl"

# Append evidence (JSONL format - one JSON object per line)
jq -n \
  --arg type "agent_invocation" \
  --arg agent "$AGENT_TYPE" \
  --arg ts "$TIMESTAMP" \
  '{
    "type": $type,
    "agent": $agent,
    "timestamp": $ts,
    "hook": "PreToolUse"
  }' >> "$EVIDENCE_FILE"

# Count today's agents
AGENT_COUNT=$(grep -c "agent_invocation" "$EVIDENCE_FILE" 2>/dev/null || echo "0")

echo "✅ Agent evidence recorded: $AGENT_TYPE (total today: $AGENT_COUNT)" >&2

exit 0
