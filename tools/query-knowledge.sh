#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   tools/query-knowledge.sh pattern <name>
#   tools/query-knowledge.sh stats   <project_type> <phase:int>
CMD="${1:-}"; shift || true
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
K="${ROOT}/.claude/knowledge"

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not installed" >&2
  exit 1
fi

case "${CMD}" in
  pattern)
    NAME="${1:-}"; [[ -z "$NAME" ]] && { echo "need pattern name"; exit 2; }
    FILES=("${K}/patterns/${NAME}.json")
    if [[ ! -f "${FILES[0]}" ]]; then
      echo "Pattern not found: ${NAME}" >&2
      exit 3
    fi
    jq -s '
      # Simple confidence: success_rate weighted by sample count
      map(. + { _confidence: (.success_rate * (.n_samples // 1)) })
      | sort_by(-._confidence)
    ' "${FILES[@]}"
    ;;
  stats)
    PTYPE="${1:-}"; PHASE="${2:-}"
    [[ -z "$PTYPE" || -z "$PHASE" ]] && { echo "Usage: query-knowledge.sh stats <project_type> <phase>"; exit 2; }
    if [[ ! -f "${K}/metrics/by_type_phase.json" ]]; then
      echo "No metrics found. Run: bash tools/learn.sh" >&2
      exit 3
    fi
    jq --arg pt "$PTYPE" --argjson ph "$PHASE" -r '
      select(.project_type==$pt and .phase==$ph)
    ' "${K}/metrics/by_type_phase.json"
    ;;
  *)
    echo "Usage: query-knowledge.sh pattern <name> | stats <project_type> <phase>"
    exit 2
    ;;
esac
