#!/usr/bin/env bash
# Generate PLAN_CHECKLIST_MAPPING.yml from PLAN.md
# Usage: bash scripts/generate_mapping.sh docs/PLAN_xxx.md [output_file]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/id_mapping.sh"

# Input validation
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <PLAN_FILE> [output_file]"
  echo "Example: $0 docs/PLAN_anti_hollow_improvements.md"
  exit 1
fi

PLAN_FILE="$1"
OUTPUT_FILE="${2:-.workflow/PLAN_CHECKLIST_MAPPING.yml}"

if [[ ! -f "$PLAN_FILE" ]]; then
  echo "❌ PLAN file not found: $PLAN_FILE"
  exit 1
fi

# Extract feature name from filename
# docs/PLAN_anti_hollow_improvements.md → anti_hollow_improvements
FEATURE_NAME=$(basename "$PLAN_FILE" .md | sed 's/^PLAN_//')
CHECKLIST_FILE="docs/ACCEPTANCE_CHECKLIST_${FEATURE_NAME}.md"

if [[ ! -f "$CHECKLIST_FILE" ]]; then
  echo "⚠️  Warning: Checklist not found: $CHECKLIST_FILE"
  echo "    Will create mapping with plan items only"
fi

echo "📋 Generating mapping from PLAN to CHECKLIST..."
echo "   Plan: $PLAN_FILE"
echo "   Checklist: $CHECKLIST_FILE"
echo "   Output: $OUTPUT_FILE"

# Create .workflow directory if not exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Initialize YAML
cat > "$OUTPUT_FILE" <<EOF
# PLAN-CHECKLIST Mapping for Anti-Hollow Gate v8.2
# Auto-generated from: $PLAN_FILE
# Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

version: "1.0"
plan_file: "$PLAN_FILE"
checklist_file: "$CHECKLIST_FILE"
mappings:
EOF

# Parse PLAN.md structure
current_week=""
week_counter=0
plan_counter=0

# Strip code blocks first to avoid parsing code as content
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

# Process PLAN.md (without code blocks)
while IFS= read -r line; do
  # Detect week section headers
  # Example: "## 🎯 Week 1: Core Infrastructure" or "### Week 2: Testing"
  if [[ "$line" =~ ^#{2,3}[[:space:]]*([🎯🔧📝🚀]?[[:space:]]*Week[[:space:]]+([0-9]+):[[:space:]]*(.+))$ ]]; then
    week_num="${BASH_REMATCH[2]}"
    section_title="${BASH_REMATCH[3]}"

    if [[ "$week_num" != "$current_week" ]]; then
      current_week="$week_num"
      ((week_counter++)) || true
      plan_counter=1  # Reset counter for new week

      # Start new mapping section
      cat >> "$OUTPUT_FILE" <<EOF

  - plan_section: "Week ${week_num}: ${section_title}"
    plan_items:
EOF
    fi
    continue
  fi

  # Detect plan items within week sections
  # Example: "- Item description" or "1. Item description"
  if [[ -n "$current_week" ]] && [[ "$line" =~ ^[[:space:]]*[-*]|^[[:space:]]*[0-9]+\.[[:space:]](.+)$ ]]; then
    item_text="${BASH_REMATCH[1]}"
    # Clean up item text (remove leading/trailing whitespace)
    item_text=$(echo "$item_text" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')

    # Skip empty items
    [[ -z "$item_text" ]] && continue

    # Generate plan ID
    plan_id=$(generate_plan_id "$current_week" "$plan_counter")

    # Add to mapping
    cat >> "$OUTPUT_FILE" <<EOF
      - id: $plan_id
        text: "$item_text"
EOF

    ((plan_counter++)) || true
  fi
done < <(strip_code_blocks < "$PLAN_FILE")

# Now parse CHECKLIST.md and add checklist_items to each mapping
if [[ -f "$CHECKLIST_FILE" ]]; then
  echo "   Parsing checklist items..."

  # Temporary file to hold updated mapping
  temp_file=$(mktemp)
  cp "$OUTPUT_FILE" "$temp_file"

  # Parse checklist and add items
  current_section=""
  cl_counter=1

  while IFS= read -r line; do
    # Detect section headers matching plan sections
    if [[ "$line" =~ ^#{2,3}[[:space:]]*([🎯🔧📝🚀P0-]?[[:space:]]*(Week[[:space:]]+[0-9]+|P0-[0-9]+):[[:space:]]*(.+))$ ]]; then
      # Extract section (BASH_REMATCH[2] is Week/P0 part, but not used currently)
      current_section="${BASH_REMATCH[1]}"
      cl_counter=1
      continue
    fi

    # Detect checklist items
    # Example: "- [ ] 1.1.1 Item description"
    if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*\[[[:space:]xX]?\][[:space:]]*(.+)$ ]]; then
      item_text="${BASH_REMATCH[1]}"
      item_text=$(echo "$item_text" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')

      [[ -z "$item_text" ]] && continue

      # Extract week number from section if possible
      week_num=""
      if [[ "$current_section" =~ Week[[:space:]]+([0-9]+) ]]; then
        week_num="${BASH_REMATCH[1]}"
      elif [[ "$current_section" =~ P0-([0-9]+) ]]; then
        # For P0 sections, use section number as week
        week_num="${BASH_REMATCH[1]}"
      else
        # Default to section 1 if no week detected
        week_num="1"
      fi

      # Generate checklist ID
      cl_id=$(generate_checklist_id "$week_num" "$cl_counter")

      # Detect required evidence type from item text
      evidence_type="functional_test"  # default
      if echo "$item_text" | grep -iq "performance\|benchmark"; then
        evidence_type="performance_test"
      elif echo "$item_text" | grep -iq "stress\|scale\|1000+"; then
        evidence_type="stress_test"
      elif echo "$item_text" | grep -iq "integration\|end-to-end"; then
        evidence_type="functional_test"
      fi

      # Add checklist item to mapping (will be inserted later)
      echo "$current_section|$cl_id|$item_text|$evidence_type" >> "${temp_file}.cl_items"

      ((cl_counter++)) || true
    fi
  done < "$CHECKLIST_FILE"

  # Insert checklist_items into mapping sections
  # This is a simplified approach - in production, would use yq for precise insertion
  # For now, append checklist_items section to each mapping entry

  if [[ -f "${temp_file}.cl_items" ]]; then
    # Group checklist items by section and append to mapping
    echo "   Adding checklist items to mapping..."

    # Read plan sections and add corresponding checklist items
    sections=$(grep "plan_section:" "$temp_file" | sed 's/.*plan_section: "\(.*\)"/\1/')

    while IFS= read -r section; do
      # Find checklist items for this section
      matching_items=$(grep "^${section}|" "${temp_file}.cl_items" 2>/dev/null || true)

      if [[ -n "$matching_items" ]]; then
        # Add checklist_items array to this mapping entry
        # Note: line_num could be used for proper YAML insertion with yq, but for
        # simplicity we just append to the file

        # Insert checklist_items after plan_items
        echo "    checklist_items:" >> "$OUTPUT_FILE"

        while IFS='|' read -r sec cl_id item_text ev_type; do
          # Note: sec is part of IFS parsing but not used in output
          cat >> "$OUTPUT_FILE" <<EOF
      - id: $cl_id
        text: "$item_text"
        required_evidence_type: "$ev_type"
EOF
        done <<< "$matching_items"
      fi
    done <<< "$sections"

    rm -f "${temp_file}.cl_items"
  fi

  rm -f "$temp_file"
fi

# Validate generated mapping
echo "   Validating ID uniqueness..."
if validate_id_uniqueness "$OUTPUT_FILE"; then
  echo "✅ Mapping generated successfully: $OUTPUT_FILE"

  # Show summary
  plan_count=$(yq eval '.mappings[].plan_items[].id' "$OUTPUT_FILE" 2>/dev/null | wc -l)
  cl_count=$(yq eval '.mappings[].checklist_items[].id' "$OUTPUT_FILE" 2>/dev/null | wc -l)

  echo "   Plan items: $plan_count"
  echo "   Checklist items: $cl_count"
else
  echo "❌ Validation failed: Duplicate IDs detected"
  exit 1
fi
