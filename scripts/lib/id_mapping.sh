#!/usr/bin/env bash
# ID Mapping Library for Anti-Hollow Gate v8.2
# Provides stable ID generation and lookup functions

# Generate Plan ID
# Format: PLAN-W{week}-{nnn}
# Example: PLAN-W4-001
generate_plan_id() {
  local week="$1"
  local counter="$2"
  printf "PLAN-W%s-%03d" "$week" "$counter"
}

# Generate Checklist ID
# Format: CL-W{week}-{nnn}
# Example: CL-W4-005
generate_checklist_id() {
  local week="$1"
  local counter="$2"
  printf "CL-W%s-%03d" "$week" "$counter"
}

# Validate ID format
# Returns 0 if valid, 1 if invalid
validate_id_format() {
  local id="$1"
  local type="$2"  # "plan" or "checklist"

  case "$type" in
    plan)
      [[ "$id" =~ ^PLAN-W[0-9]+-[0-9]{3}$ ]] && return 0
      ;;
    checklist)
      [[ "$id" =~ ^CL-W[0-9]+-[0-9]{3}$ ]] && return 0
      ;;
    *)
      echo "❌ Invalid type: $type (must be 'plan' or 'checklist')"
      return 1
      ;;
  esac

  echo "❌ Invalid ID format: $id"
  return 1
}

# Check ID uniqueness in mapping file
# Returns 0 if unique, 1 if collision detected
validate_id_uniqueness() {
  local mapping_file="$1"

  if [[ ! -f "$mapping_file" ]]; then
    # No mapping file yet, all IDs are unique
    return 0
  fi

  # Check for duplicate plan IDs
  local plan_ids
  plan_ids=$(yq eval '.mappings[].plan_items[].id' "$mapping_file" 2>/dev/null | sort)
  local plan_dupes
  plan_dupes=$(echo "$plan_ids" | uniq -d)

  if [[ -n "$plan_dupes" ]]; then
    echo "❌ Duplicate Plan IDs detected:"
    echo "$plan_dupes"
    return 1
  fi

  # Check for duplicate checklist IDs
  local checklist_ids
  checklist_ids=$(yq eval '.mappings[].checklist_items[].id' "$mapping_file" 2>/dev/null | sort)
  local cl_dupes
  cl_dupes=$(echo "$checklist_ids" | uniq -d)

  if [[ -n "$cl_dupes" ]]; then
    echo "❌ Duplicate Checklist IDs detected:"
    echo "$cl_dupes"
    return 1
  fi

  return 0
}

# Lookup checklist items by plan ID
# Returns list of checklist IDs mapped to the given plan ID
lookup_checklist_items_by_plan_id() {
  local mapping_file="$1"
  local plan_id="$2"

  if [[ ! -f "$mapping_file" ]]; then
    echo "❌ Mapping file not found: $mapping_file" >&2
    return 1
  fi

  # Query MAPPING.yml for checklist items mapped to this plan_id
  yq eval ".mappings[] | select(.plan_items[].id == \"$plan_id\") | .checklist_items[].id" "$mapping_file" 2>/dev/null
}

# Lookup plan item by checklist ID
# Returns plan ID that maps to the given checklist ID
lookup_plan_id_by_checklist_id() {
  local mapping_file="$1"
  local checklist_id="$2"

  if [[ ! -f "$mapping_file" ]]; then
    echo "❌ Mapping file not found: $mapping_file" >&2
    return 1
  fi

  # Find the mapping entry containing this checklist ID
  yq eval ".mappings[] | select(.checklist_items[].id == \"$checklist_id\") | .plan_items[].id" "$mapping_file" 2>/dev/null | head -1
}

# Extract checklist ID from comment line
# Input: <!-- id: CL-W4-005; evidence: EVID-2025W44-015 -->
# Output: CL-W4-005
extract_checklist_id_from_comment() {
  local comment_line="$1"

  # Match <!-- id: {ID}; ... -->
  if [[ "$comment_line" =~ id:\ ([A-Z]+-W[0-9]+-[0-9]{3}) ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi

  return 1
}

# Extract evidence ID from comment line
# Input: <!-- id: CL-W4-005; evidence: EVID-2025W44-015 -->
# Output: EVID-2025W44-015
extract_evidence_id_from_comment() {
  local comment_line="$1"

  # Match evidence: {EVID-...}
  if [[ "$comment_line" =~ evidence:\ (EVID-[0-9]{4}W[0-9]{2}-[0-9]{3}) ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi

  return 1
}

# Check if checklist uses ID system
# Returns 0 if ID-based, 1 if legacy text-based
is_id_based_checklist() {
  local checklist_file="$1"

  if [[ ! -f "$checklist_file" ]]; then
    return 1
  fi

  # Check if any line contains <!-- id: CL- -->
  grep -q '<!-- id: CL-' "$checklist_file" 2>/dev/null
}

# Get week number from section header
# Input: "## Week 4: KPI Dashboard"
# Output: 4
extract_week_number() {
  local section_header="$1"

  if [[ "$section_header" =~ Week\ ([0-9]+) ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi

  return 1
}
