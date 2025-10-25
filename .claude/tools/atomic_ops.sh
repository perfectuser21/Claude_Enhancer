#!/usr/bin/env bash
# Atomic file operations library
# Ensures data consistency in concurrent scenarios

set -euo pipefail

LOCK_TIMEOUT=5
MAX_RETRIES=3
RETRY_DELAY=0.1

# Atomic write to file
atomic_write() {
  local file="$1"
  local content="$2"
  local temp_file="${file}.tmp.$$"

  echo "$content" > "$temp_file"
  fsync "$temp_file" 2>/dev/null || true
  mv "$temp_file" "$file"
}

# Atomic JSON update
atomic_json_update() {
  local file="$1"
  local jq_filter="$2"
  local value="$3"
  local retry=0

  # Pre-validate that value is valid JSON (if it looks like JSON)
  if [[ "$value" =~ ^[{\[] ]] || [[ "$value" =~ ^\" ]]; then
    if ! echo "$value" | jq empty 2>/dev/null; then
      echo "❌ Invalid JSON value provided" >&2
      return 1
    fi
  fi

  while (( retry < MAX_RETRIES )); do
    (
      flock -w $LOCK_TIMEOUT 200 || exit 1

      if [ ! -f "$file" ]; then
        echo '{}' > "$file"
      fi

      local temp
      temp=$(mktemp)
      jq "$jq_filter = $value" "$file" > "$temp" 2>/dev/null || exit 1

      # Validate output JSON
      if jq empty "$temp" 2>/dev/null; then
        mv "$temp" "$file"
        exit 0
      else
        rm -f "$temp"
        exit 1
      fi

    ) 200>"${file}.lock"

    local status=$?
    # Do NOT remove lock file - flock handles it, and removing causes race conditions

    if [ $status -eq 0 ]; then
      return 0
    fi

    ((retry++)) || true
    sleep "$(echo "$RETRY_DELAY * $retry" | bc)"
  done

  echo "❌ Atomic update failed after $MAX_RETRIES retries" >&2
  return 1
}

# Atomic JSON append to array
atomic_json_append() {
  local file="$1"
  local array_path="$2"
  local item="$3"

  atomic_json_update "$file" "$array_path" "($array_path + [$item])"
}

# Safe file locking with timeout
# Usage: ( flock -w $timeout 200 || exit 1; your_code; ) 200>lockfile
safe_lock() {
  local timeout="${1:-$LOCK_TIMEOUT}"

  flock -w "$timeout" 200 || return 1
}

# Cleanup orphaned temp files
cleanup_temp_files() {
  local dir="${1:-.}"

  find "$dir" -name "*.tmp.*" -mmin +60 -delete 2>/dev/null || true
}

# Crash recovery - detect incomplete writes
recover_from_crash() {
  local file="$1"
  local backup="${file}.backup"

  if [ -f "$backup" ] && [ ! -f "$file" ]; then
    echo "🔄 Recovering $file from backup..." >&2
    cp "$backup" "$file"
    return 0
  fi

  return 1
}

# Create backup before risky operation
create_backup() {
  local file="$1"
  local backup="${file}.backup"

  if [ -f "$file" ]; then
    cp "$file" "$backup"
  fi
}

# Export functions
export -f atomic_write
export -f atomic_json_update
export -f atomic_json_append
export -f safe_lock
export -f cleanup_temp_files
export -f recover_from_crash
export -f create_backup
