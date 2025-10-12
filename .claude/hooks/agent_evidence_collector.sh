#!/usr/bin/env bash
# Agent Evidence Collector Hook
# Intercepts agent invocations and records evidence for enforcement
#
# Hook Type: PreToolUse
# Triggers: Before Task tool execution
# Purpose: Build evidence of multi-agent execution for quality gates

set -euo pipefail

# Initialize environment
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CLAUDE_CORE="${ROOT}/.claude/core"

# Source core libraries
if [ -f "${CLAUDE_CORE}/task_namespace.sh" ]; then
  # shellcheck source=../../.claude/core/task_namespace.sh
  source "${CLAUDE_CORE}/task_namespace.sh"
else
  echo "⚠️  Task namespace library not found, skipping evidence collection" >&2
  exit 0
fi

# Load configuration
CONFIG="${ROOT}/.claude/config.yml"
ENFORCEMENT_ENABLED=true
MIN_AGENTS_FULL=3
MIN_AGENTS_FAST=0

if command -v yq >/dev/null 2>&1 && [ -f "$CONFIG" ]; then
  ENFORCEMENT_ENABLED=$(yq e '.enforcement.enabled' "$CONFIG" 2>/dev/null || echo "true")
  MIN_AGENTS_FULL=$(yq e '.enforcement.agent_evidence.min_agents.full_lane' "$CONFIG" 2>/dev/null || echo "3")
  MIN_AGENTS_FAST=$(yq e '.enforcement.agent_evidence.min_agents.fast_lane' "$CONFIG" 2>/dev/null || echo "0")
fi

# Check if enforcement is enabled
if [ "$ENFORCEMENT_ENABLED" != "true" ]; then
  echo "ℹ️  Enforcement disabled, skipping agent evidence collection" >&2
  exit 0
fi

# Get current task context
TASK_ID=$(get_current_task)
if [ -z "$TASK_ID" ]; then
  echo "ℹ️  No active task, agent evidence not required" >&2
  exit 0
fi

TASK_DIR=$(get_task_dir "$TASK_ID")
if [ ! -d "$TASK_DIR" ]; then
  echo "⚠️  Task directory not found: $TASK_DIR" >&2
  exit 0
fi

# Parse tool invocation from stdin/arguments
# This hook receives the tool name and parameters
TOOL_NAME="${1:-unknown}"
AGENT_TYPE="${2:-}"

# Only track Task tool invocations (agent launches)
if [ "$TOOL_NAME" != "Task" ]; then
  exit 0
fi

# Extract agent type from parameters
if [ -z "$AGENT_TYPE" ]; then
  # Try to parse from JSON input if available
  if [ -t 0 ]; then
    # No stdin, skip
    exit 0
  fi

  # Read JSON from stdin
  JSON_INPUT=$(cat)
  AGENT_TYPE=$(echo "$JSON_INPUT" | jq -r '.subagent_type // empty' 2>/dev/null || echo "")
fi

if [ -z "$AGENT_TYPE" ]; then
  echo "⚠️  Could not determine agent type" >&2
  exit 0
fi

# Record agent invocation
echo "📝 Recording agent: $AGENT_TYPE for task $TASK_ID" >&2
record_agent "$TASK_ID" "$AGENT_TYPE" "PreToolUse hook interception"

# Get current agent count
AGENT_COUNT=$(get_agent_count "$TASK_ID")

# Determine lane type from task metadata
TASK_META="${TASK_DIR}/task_meta.json"
LANE="full"
if [ -f "$TASK_META" ]; then
  LANE=$(jq -r '.lane // "full"' "$TASK_META" 2>/dev/null || echo "full")
fi

# Determine minimum agents required
MIN_AGENTS=$MIN_AGENTS_FULL
if [ "$LANE" = "fast" ]; then
  MIN_AGENTS=$MIN_AGENTS_FAST
fi

# Check if minimum agent count met
if [ "$AGENT_COUNT" -lt "$MIN_AGENTS" ]; then
  echo "⚠️  Agent count ($AGENT_COUNT) below minimum for $LANE lane ($MIN_AGENTS)" >&2
  echo "   This will be validated at commit time" >&2
fi

# Log to evidence file
EVIDENCE_ENTRY=$(jq -n \
  --arg type "agent_invocation" \
  --arg agent "$AGENT_TYPE" \
  --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg count "$AGENT_COUNT" \
  '{
    "type": $type,
    "agent": $agent,
    "timestamp": $ts,
    "total_count": ($count | tonumber),
    "hook": "PreToolUse"
  }')

record_evidence "$TASK_ID" "$EVIDENCE_ENTRY"

echo "✅ Agent evidence recorded: $AGENT_TYPE (total: $AGENT_COUNT/$MIN_AGENTS)" >&2

exit 0
