#!/usr/bin/env bash
set -euo pipefail

# Aggregates sessions into metrics files (by project_type, phase).
# Usage: tools/learn.sh [--engine-root PATH]
ENG="${1:-}"; [[ "$ENG" == "--engine-root" ]] && { ENG="$2"; shift 2; } || true
[[ -z "${ENG}" ]] && ENG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

K="${ENG}/.claude/knowledge"
S="${K}/sessions"
M="${K}/metrics"
mkdir -p "${M}"

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not installed" >&2
  exit 1
fi

# Check if there are any session files
if ! ls "${S}"/*.json >/dev/null 2>&1; then
  echo "No session files found in ${S}" >&2
  exit 0
fi

jq -s '
  # group sessions by project_type + phase
  group_by(.project_type + ":" + (.phase|tostring))[]
  | {
      project_type: (.[0].project_type),
      phase: (.[0].phase),
      sample_count: length,
      avg_duration_seconds: ( [.[].duration_seconds] | add / length ),
      success_rate: ( [.[].success] | map( if . then 1 else 0 end ) | add / length ),
      common_errors: (
        [ .[].errors[]? ]
        | group_by(.)
        | map({error:.[0], count:length})
        | sort_by(-.count) | .[:10]
      )
    }
' "${S}"/*.json > "${M}/by_type_phase.json"

echo "learn: metrics updated -> ${M}/by_type_phase.json"
