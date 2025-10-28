#!/usr/bin/env bash
# Text Processing Library for Anti-Hollow Gate v8.2
# Provides code block filtering and regex escaping

# Strip Markdown code blocks from input
# Usage: strip_code_blocks < file.md
# Removes all ``` fenced code blocks, preserving other content
strip_code_blocks() {
  awk '
    BEGIN { in_block = 0 }
    /^```/ {
      in_block = !in_block
      next
    }
    !in_block { print }
  '
}

# Escape special characters for use in regex
# Usage: escaped=$(echo "$text" | re_escape)
# Escapes: ^ $ . * + ? ( ) [ ] { } | \
re_escape() {
  sed -e 's/[^^$.*+?()[\]{}|\\]/\\&/g'
}

# Escape special characters for grep -F (fixed string)
# Usage: escaped=$(echo "$text" | grep_escape)
# This is simpler than re_escape as grep -F treats input as literal
grep_escape() {
  # For grep -F, we mainly need to escape newlines and special shell chars
  sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

# Extract text between markers (useful for extracting sections)
# Usage: extract_between "START_MARKER" "END_MARKER" < file
extract_between() {
  local start_marker="$1"
  local end_marker="$2"

  awk -v start="$start_marker" -v end="$end_marker" '
    $0 ~ start { found=1; next }
    $0 ~ end { found=0 }
    found { print }
  '
}

# Remove leading/trailing whitespace
# Usage: trimmed=$(echo "$text" | trim)
trim() {
  sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

# Check if line is inside a code block
# Usage: is_in_code_block "$line_number" "$file"
# Returns 0 if inside code block, 1 if not
is_in_code_block() {
  local target_line="$1"
  local file="$2"

  local in_block=0
  local current_line=0

  while IFS= read -r line; do
    ((current_line++))

    if [[ "$line" =~ ^\`\`\` ]]; then
      # Toggle block state
      if [[ $in_block -eq 0 ]]; then
        in_block=1
      else
        in_block=0
      fi
    fi

    if [[ $current_line -eq $target_line ]]; then
      return $in_block
    fi
  done < "$file"

  return 1
}

# Count code blocks in file
# Usage: count=$(count_code_blocks "$file")
count_code_blocks() {
  local file="$1"

  if [[ ! -f "$file" ]]; then
    echo "0"
    return
  fi

  # Count backtick markers and divide by 2
  local markers
  markers=$(grep -c '^\`\`\`' "$file" 2>/dev/null || echo "0")

  echo $((markers / 2))
}

# Extract non-code content from Markdown
# Usage: extract_non_code < file.md
# Same as strip_code_blocks but more explicit name
extract_non_code() {
  strip_code_blocks
}

# Safe grep with regex escaping
# Usage: safe_grep "$pattern" "$file"
# Automatically escapes the pattern
safe_grep() {
  local pattern="$1"
  local file="$2"
  local escaped_pattern

  escaped_pattern=$(echo "$pattern" | re_escape)

  grep -E "$escaped_pattern" "$file"
}

# Safe grep for fixed strings (no regex)
# Usage: safe_grep_fixed "$literal_string" "$file"
safe_grep_fixed() {
  local pattern="$1"
  local file="$2"

  grep -F "$pattern" "$file"
}
