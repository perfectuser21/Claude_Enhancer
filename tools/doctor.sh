#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF="${ROOT}/.claude/engine/engine_api.json"
REQS=(jq git)
FIXED=0
ERRORS=0

echo "== CE Doctor (Self-Healing Mode) =="
echo "Root: $ROOT"
echo ""

# Check required binaries
echo "[1/5] Checking required binaries..."
for b in "${REQS[@]}"; do
  if command -v "$b" >/dev/null 2>&1; then
    echo "  ✓ $b found"
  else
    echo "  ✗ $b missing" >&2
    echo "    → Install: sudo apt-get install $b  # Debian/Ubuntu" >&2
    echo "    → Install: brew install $b          # macOS" >&2
    ((ERRORS++))
  fi
done

# Check engine_api.json
echo ""
echo "[2/5] Checking engine API configuration..."
if [[ -f "${CONF}" ]]; then
  API=$(jq -r .api "${CONF}" 2>/dev/null || echo "invalid")
  if [[ "${API}" != "invalid" ]]; then
    echo "  ✓ engine api: ${API}"
  else
    echo "  ✗ Invalid engine_api.json, regenerating..." >&2
    mkdir -p "$(dirname "$CONF")"
    echo '{"api":"7.0","min_project":"7.0"}' > "${CONF}"
    echo "  ✓ Fixed: Created valid engine_api.json"
    ((FIXED++))
  fi
else
  echo "  ⚠ Missing engine_api.json"
  mkdir -p "$(dirname "$CONF")"
  echo '{"api":"7.0","min_project":"7.0"}' > "${CONF}"
  echo "  ✓ Fixed: Created ${CONF}"
  ((FIXED++))
fi

# Check knowledge base structure
echo ""
echo "[3/5] Checking knowledge base structure..."
for d in sessions patterns metrics improvements; do
  if [[ -d "${ROOT}/.claude/knowledge/${d}" ]]; then
    count=$(ls -1 "${ROOT}/.claude/knowledge/${d}" 2>/dev/null | wc -l)
    echo "  ✓ knowledge/${d} exists (${count} files)"
  else
    echo "  ⚠ knowledge/${d} missing"
    mkdir -p "${ROOT}/.claude/knowledge/${d}"
    echo "  ✓ Fixed: Created ${ROOT}/.claude/knowledge/${d}"
    ((FIXED++))
  fi
done

# Check schema.json (auto-create default if missing)
echo ""
echo "[4/5] Checking schema definition..."
SCHEMA="${ROOT}/.claude/knowledge/schema.json"
if [[ -f "${SCHEMA}" ]]; then
  echo "  ✓ schema.json exists"
else
  echo "  ⚠ schema.json missing"
  cat > "${SCHEMA}" <<'EOF'
{
  "version": "1.0",
  "session": {
    "required": ["session_id", "project", "project_type", "phase", "timestamp"],
    "optional": ["duration_seconds", "agents_used", "errors", "warnings", "quality_score"]
  },
  "pattern": {
    "required": ["pattern_id", "project_type", "phase", "description"],
    "optional": ["success_rate", "sample_count", "tags"]
  },
  "metric": {
    "required": ["project_type", "phase", "sample_count"],
    "optional": ["avg_duration_seconds", "success_rate", "common_errors"]
  }
}
EOF
  echo "  ✓ Fixed: Created default ${SCHEMA}"
  ((FIXED++))
fi

# Check metrics initialization (create empty structure if missing)
echo ""
echo "[5/5] Checking metrics initialization..."
METRICS="${ROOT}/.claude/knowledge/metrics/by_type_phase.json"
if [[ -f "${METRICS}" ]]; then
  echo "  ✓ metrics file exists"
else
  echo "  ⚠ metrics file missing"
  jq -n --arg ts "$(date -u +%FT%TZ)" '{
    meta: {
      version: "1.0",
      schema: "by_type_phase",
      last_updated: $ts,
      sample_count: 0
    },
    data: []
  }' > "${METRICS}"
  echo "  ✓ Fixed: Created empty ${METRICS}"
  ((FIXED++))
fi

# Summary
echo ""
echo "== Summary =="
if (( ERRORS > 0 )); then
  echo "✗ ${ERRORS} error(s) found - manual intervention required"
  exit 1
elif (( FIXED > 0 )); then
  echo "✓ ${FIXED} issue(s) auto-fixed - system healthy"
  exit 0
else
  echo "✓ All checks passed - system healthy"
  exit 0
fi
