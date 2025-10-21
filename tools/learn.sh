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

# Atomic write using mktemp + mv (concurrent safety)
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

# Collect session files (tolerate empty set)
mapfile -t FILES < <(find "${S}" -maxdepth 1 -type f -name '*.json' -print 2>/dev/null || true)

# Handle empty data case
if (( ${#FILES[@]} == 0 )); then
  # Write empty structure with metadata
  jq -n --arg ts "$(date -u +%FT%TZ)" '{
    meta: {
      version: "1.0",
      schema: "by_type_phase",
      last_updated: $ts,
      sample_count: 0
    },
    data: []
  }' > "${TMP}"
  mv "${TMP}" "${M}/by_type_phase.json"
  echo "learn: no sessions found, empty metrics written -> ${M}/by_type_phase.json"
  exit 0
fi

# Process sessions and add metadata
{
  echo '{'
  echo '  "meta": {'
  echo '    "version": "1.0",'
  echo '    "schema": "by_type_phase",'
  echo "    \"last_updated\": \"$(date -u +%FT%TZ)\","
  echo "    \"sample_count\": ${#FILES[@]}"
  echo '  },'
  echo '  "data":'

  jq -s '
    # group sessions by project_type + phase
    [ group_by(.project_type + ":" + (.phase|tostring))[]
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
    ]
  ' "${FILES[@]}"

  echo '}'
} > "${TMP}"

# Atomic move to final location
mv "${TMP}" "${M}/by_type_phase.json"

echo "learn: metrics updated -> ${M}/by_type_phase.json (${#FILES[@]} sessions)"
