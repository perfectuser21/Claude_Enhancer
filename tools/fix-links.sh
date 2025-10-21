#!/usr/bin/env bash
set -euo pipefail
NEW="${1:-}"; [[ -z "$NEW" ]] && { echo "Usage: fix-links.sh <new-ce-root>"; exit 2; }

echo "Fixing symlinks to new CE root: $NEW"
echo ""

count=0
find ~ -type d -name ".claude" 2>/dev/null | while read -r D; do
  # Skip the CE itself
  [[ "$D" == "$NEW/.claude" ]] && continue

  # Check if this looks like a project (has config.json)
  [[ ! -f "${D}/config.json" ]] && continue

  echo "Processing: $D"

  for name in engine hooks templates; do
    T="${D}/${name}"
    if [[ -L "${T}" || -d "${T}" ]]; then
      rm -rf "${T}"
      ln -sf "${NEW}/.claude/${name}" "${T}" || cp -R "${NEW}/.claude/${name}" "${T}"
      echo "  ✓ fixed: ${name}"
    fi
  done

  # Update project config's engine_root
  CFG="${D}/config.json"
  if [[ -f "${CFG}" ]]; then
    tmp="$(mktemp)"
    if jq --arg p "$NEW" '.engine_root=$p' "$CFG" > "$tmp" 2>/dev/null; then
      mv "$tmp" "$CFG"
      echo "  ✓ updated: config.json"
    else
      rm -f "$tmp"
      echo "  ⚠ failed to update config.json"
    fi
  fi

  count=$((count + 1))
  echo ""
done

echo "✓ Fixed $count project(s)"
