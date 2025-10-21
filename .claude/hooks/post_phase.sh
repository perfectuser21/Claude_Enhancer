#!/usr/bin/env bash
set -euo pipefail

# Usage: .claude/hooks/post_phase.sh <phase:int 1-7> [quality_score:int]
PHASE="${1:-}"; QUALITY="${2:-}"
if [[ -z "${PHASE}" || ! "${PHASE}" =~ ^[1-7]$ ]]; then
  echo "post_phase: invalid phase '${PHASE}'" >&2; exit 2
fi

# Resolve project root (hook 相对项目根调用或绝对路径调用都可)
PROJ_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CONF="${PROJ_ROOT}/.claude/config.json"
if [[ ! -f "${CONF}" ]]; then echo "config missing: ${CONF}" >&2; exit 3; fi

# Read config
PROJECT=$(jq -r '.project // input_filename' "${CONF}")
PTYPE=$(jq -r '.type // "unknown"' "${CONF}")
ENGINE_ROOT=$(jq -r '.engine_root // ""' "${CONF}")
LEARNING_ENABLED=$(jq -r '.learning.enabled // true' "${CONF}")

[[ "${LEARNING_ENABLED}" != "true" ]] && { echo "learning disabled; skip"; exit 0; }

# Central knowledge dir
KROOT="${ENGINE_ROOT}/.claude/knowledge"
SESS_DIR="${KROOT}/sessions"
mkdir -p "${SESS_DIR}"

# Input validation: convert to JSON array if needed
# Accepts: valid JSON array, space-separated string, or empty
to_json_array() {
  local raw="$1"
  # Empty case
  [[ -z "${raw}" ]] && { echo "[]"; return; }

  # Check if already valid JSON
  if echo "$raw" | jq -e . >/dev/null 2>&1; then
    echo "$raw"
    return
  fi

  # Convert space-separated to JSON array ["a","b","c"]
  echo "$raw" | awk '{
    printf "["
    for(i=1; i<=NF; i++) {
      if(i>1) printf ","
      printf "\"%s\"", $i
    }
    printf "]"
  }'
}

# Collect basics
TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
SID="$(date -u +"%Y%m%d_%H%M%S")_${PROJECT}"
DUR="${DURATION_SECONDS:-0}" # 可由调用方预先导出
AGENTS="$(to_json_array "${AGENTS_USED:-}")"  # 传入形如 '["a","b"]' 的 JSON 字符串或空格分隔
ERRORS="$(to_json_array "${ERRORS_JSON:-}")"
WARNINGS="$(to_json_array "${WARNINGS_JSON:-}")"
Q="${QUALITY:-null}"

# Compose JSON with jq (required)
TMP="$(mktemp)"
jq -n --arg sid "$SID" --arg proj "$PROJECT" --arg ptype "$PTYPE" \
      --arg ts "$TS" --argjson phase "$PHASE" --argjson dur "$DUR" \
      --argjson agents "${AGENTS}" --argjson errs "${ERRORS}" \
      --argjson warns "${WARNINGS}" --argjson q "${Q}" '
{
  session_id: $sid,
  project: $proj,
  project_type: $ptype,
  phase: $phase,
  duration_seconds: $dur,
  agents_used: $agents,
  errors: $errs,
  warnings: $warns,
  success: ( ($errs|length)==0 ),
  timestamp: $ts,
  files_changed: (env.FILES_CHANGED|tonumber? // 0),
  quality_score: ( $q // 0 )
}
' > "${TMP}"

# Atomic write
DST="${SESS_DIR}/${SID}.json"
mv "${TMP}" "${DST}"
echo "post_phase: wrote ${DST}"
