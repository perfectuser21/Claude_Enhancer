#!/usr/bin/env bash
# Evidence Validation Library for Anti-Hollow Gate v8.2
# Provides strict schema validation with jq

# Check if jq is available
check_jq_available() {
  if ! command -v jq &>/dev/null; then
    echo "❌ jq not installed"
    echo "   Install: apt-get install jq (Debian/Ubuntu) or brew install jq (macOS)"
    return 1
  fi
  return 0
}

# Validate evidence file against schema
# Usage: validate_evidence_file "$evidence_file"
# Returns 0 if valid, 1 if invalid
validate_evidence_file() {
  local evid_file="$1"
  local schema_file="${2:-.evidence/schema.json}"

  # Check file exists
  if [[ ! -f "$evid_file" ]]; then
    echo "❌ Evidence file not found: $evid_file"
    return 1
  fi

  # Check schema exists
  if [[ ! -f "$schema_file" ]]; then
    echo "❌ Schema file not found: $schema_file"
    return 1
  fi

  # Check jq availability
  if ! check_jq_available; then
    echo "⚠️  Falling back to basic validation (yq only)"
    validate_evidence_file_basic "$evid_file"
    return $?
  fi

  # Extract type field from evidence
  local ev_type
  ev_type=$(yq -r '.type // ""' "$evid_file" 2>/dev/null)

  if [[ -z "$ev_type" ]]; then
    echo "❌ $evid_file: missing 'type' field"
    return 1
  fi

  # Validate type is in allowed list
  local allowed_types
  allowed_types=$(jq -r '.evidence_types[].type' "$schema_file" 2>/dev/null)

  if ! echo "$allowed_types" | grep -q "^${ev_type}$"; then
    echo "❌ $evid_file: invalid type '$ev_type'"
    echo "   Allowed types: $(echo "$allowed_types" | tr '\n' ', ' | sed 's/,$//')"
    return 1
  fi

  # Get required fields for this evidence type
  local required_fields
  required_fields=$(jq -r --arg t "$ev_type" \
    '.evidence_types[] | select(.type==$t) | .required_fields[]' \
    "$schema_file" 2>/dev/null)

  if [[ -z "$required_fields" ]]; then
    echo "⚠️  No required fields defined for type: $ev_type"
    return 0
  fi

  # Validate each required field exists and is non-empty
  local missing_fields=()

  while IFS= read -r field; do
    # Check if field exists in YAML
    if ! yq -e ".$field" "$evid_file" >/dev/null 2>&1; then
      missing_fields+=("$field")
      continue
    fi

    # Check if field value is non-empty
    local field_value
    field_value=$(yq -r ".$field // \"\"" "$evid_file" 2>/dev/null)

    if [[ -z "$field_value" ]] || [[ "$field_value" == "null" ]]; then
      missing_fields+=("$field (empty)")
    fi
  done <<< "$required_fields"

  # Report validation result
  if [[ ${#missing_fields[@]} -gt 0 ]]; then
    echo "❌ $evid_file: missing required fields:"
    for field in "${missing_fields[@]}"; do
      echo "   - $field"
    done
    return 1
  fi

  return 0
}

# Basic validation without jq (fallback)
# Only checks type field exists
validate_evidence_file_basic() {
  local evid_file="$1"

  # Extract type
  local ev_type
  ev_type=$(yq -r '.type // ""' "$evid_file" 2>/dev/null)

  if [[ -z "$ev_type" ]]; then
    echo "❌ $evid_file: missing 'type' field"
    return 1
  fi

  # Basic type validation (enum check)
  case "$ev_type" in
    functional_test|performance_test|stress_test|benchmark)
      # Valid type
      return 0
      ;;
    *)
      echo "❌ $evid_file: invalid type '$ev_type'"
      echo "   Allowed: functional_test, performance_test, stress_test, benchmark"
      return 1
      ;;
  esac
}

# Validate all evidence files in a directory
# Usage: validate_all_evidence "$evidence_dir"
validate_all_evidence() {
  local evidence_dir="$1"
  local schema_file="${2:-.evidence/schema.json}"

  if [[ ! -d "$evidence_dir" ]]; then
    echo "❌ Evidence directory not found: $evidence_dir"
    return 1
  fi

  local total=0
  local passed=0
  local failed=0

  # Find all .yml files
  while IFS= read -r evid_file; do
    ((total++))

    if validate_evidence_file "$evid_file" "$schema_file"; then
      ((passed++))
    else
      ((failed++))
    fi
  done < <(find "$evidence_dir" -type f -name "*.yml" 2>/dev/null)

  echo ""
  echo "Evidence Validation Summary:"
  echo "  Total: $total"
  echo "  Passed: $passed"
  echo "  Failed: $failed"

  if [[ $failed -gt 0 ]]; then
    return 1
  fi

  return 0
}

# Get required fields for evidence type
# Usage: get_required_fields "$evidence_type" "$schema_file"
get_required_fields() {
  local ev_type="$1"
  local schema_file="${2:-.evidence/schema.json}"

  if [[ ! -f "$schema_file" ]]; then
    return 1
  fi

  if ! check_jq_available; then
    # Fallback: return hardcoded fields
    case "$ev_type" in
      functional_test)
        echo "test_command"
        echo "exit_code"
        echo "output_sample"
        ;;
      performance_test)
        echo "test_command"
        echo "execution_time"
        echo "baseline"
        ;;
      stress_test)
        echo "test_command"
        echo "scale"
        echo "result"
        ;;
      benchmark)
        echo "test_command"
        echo "comparison"
        echo "result"
        ;;
    esac
    return 0
  fi

  jq -r --arg t "$ev_type" \
    '.evidence_types[] | select(.type==$t) | .required_fields[]' \
    "$schema_file" 2>/dev/null
}

# Create evidence template for given type
# Usage: create_evidence_template "$type" "$output_file"
create_evidence_template() {
  local ev_type="$1"
  local output_file="$2"

  local required_fields
  required_fields=$(get_required_fields "$ev_type")

  cat > "$output_file" <<EOF
id: "EVID-YYYY-WWW-NNN"
type: "$ev_type"
description: "Description of what this evidence demonstrates"
created_at: "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
EOF

  while IFS= read -r field; do
    case "$field" in
      test_command)
        echo "test_command: \"bash scripts/test.sh\"" >> "$output_file"
        ;;
      exit_code)
        echo "exit_code: 0" >> "$output_file"
        ;;
      output_sample)
        echo "output_sample: |" >> "$output_file"
        echo "  Test output here" >> "$output_file"
        ;;
      execution_time)
        echo "execution_time: \"1.5s\"" >> "$output_file"
        ;;
      baseline)
        echo "baseline: \"2.0s\"" >> "$output_file"
        ;;
      scale)
        echo "scale: \"1000 items\"" >> "$output_file"
        ;;
      result)
        echo "result: \"PASS\"" >> "$output_file"
        ;;
      comparison)
        echo "comparison: \"50% faster than baseline\"" >> "$output_file"
        ;;
      *)
        echo "$field: \"\"" >> "$output_file"
        ;;
    esac
  done <<< "$required_fields"

  echo "✅ Evidence template created: $output_file"
  echo "   Type: $ev_type"
  echo "   Required fields: $(echo "$required_fields" | wc -l)"
}
