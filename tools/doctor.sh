#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF="${ROOT}/.claude/engine/engine_api.json"
REQS=(jq git)

echo "== CE Doctor =="
echo "Root: $ROOT"

# Check required binaries
for b in "${REQS[@]}"; do
  if command -v "$b" >/dev/null 2>&1; then
    echo "✓ $b found"
  else
    echo "✗ $b missing - please install" >&2
    exit 2
  fi
done

# Check engine_api.json
if [[ -f "${CONF}" ]]; then
  API=$(jq -r .api "${CONF}")
  echo "✓ engine api: ${API}"
else
  echo "⚠ missing engine_api.json (will create default)"
  mkdir -p "$(dirname "$CONF")"
  echo '{"api":"7.0","min_project":"7.0"}' > "${CONF}"
fi

# Check knowledge base structure
for d in sessions patterns metrics improvements; do
  if [[ -d "${ROOT}/.claude/knowledge/${d}" ]]; then
    count=$(ls -1 "${ROOT}/.claude/knowledge/${d}" 2>/dev/null | wc -l)
    echo "✓ knowledge/${d} exists (${count} files)"
  else
    echo "⚠ knowledge/${d} missing (will create)"
    mkdir -p "${ROOT}/.claude/knowledge/${d}"
  fi
done

# Check schema
if [[ -f "${ROOT}/.claude/knowledge/schema.json" ]]; then
  echo "✓ schema.json exists"
else
  echo "⚠ schema.json missing"
fi

echo ""
echo "== Summary =="
echo "✓ All checks passed"
