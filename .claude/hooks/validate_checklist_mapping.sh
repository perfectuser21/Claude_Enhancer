#!/usr/bin/env bash
# Validate Checklist Mapping - Pre-Phase 2 & Phase 4
# Exit codes: 0=ok, 1=coverage, 2=mapping, 3=forbidden, 4=format, 5=parse

set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

check_deps

USER_CHECKLIST=".workflow/ACCEPTANCE_CHECKLIST.md"
TECH_CHECKLIST=".workflow/TECHNICAL_CHECKLIST.md"
TRACEABILITY=".workflow/TRACEABILITY.yml"

ANALOGY_LIB="${ANALOGY_LIB:-.claude/data/analogy_library.yml}"

# Validation functions
validate_files_exist() {
    local missing=0
    for file in "$USER_CHECKLIST" "$TECH_CHECKLIST" "$TRACEABILITY"; do
        if [[ ! -f "$file" ]]; then
            echo "ERROR: Missing required file: $file" >&2
            missing=1
        fi
    done
    return $missing
}

validate_traceability() {
    echo "Validating traceability mapping..." >&2

    # Parse YAML
    local links
    links=$(yq eval '.links' "$TRACEABILITY" 2>/dev/null) || {
        echo "ERROR: Invalid YAML in TRACEABILITY.yml" >&2
        return 5
    }

    # Count U items
    local u_count
    u_count=$(yq eval '.links | length' "$TRACEABILITY")

    # Verify coverage (each U has at least one T)
    local idx=0
    while [[ $idx -lt $u_count ]]; do
        local t_list
        t_list=$(yq eval ".links[$idx].t | length" "$TRACEABILITY")

        if [[ $t_list -eq 0 ]]; then
            local u_id
            u_id=$(yq eval ".links[$idx].u" "$TRACEABILITY")
            echo "ERROR: User item $u_id has no technical mappings" >&2
            return 1
        fi

        ((idx++))
    done

    echo "✓ Traceability mapping valid ($u_count user items)" >&2
    return 0
}

validate_forbidden_terms() {
    echo "Checking forbidden terms in user checklist..." >&2

    if check_forbidden_terms "$USER_CHECKLIST"; then
        echo "✓ No forbidden terms found" >&2
        return 0
    else
        return 3
    fi
}

validate_markdown_format() {
    echo "Validating Markdown format..." >&2

    # Basic format checks
    if ! grep -q "^# Acceptance Checklist" "$USER_CHECKLIST"; then
        echo "ERROR: User checklist missing title" >&2
        return 4
    fi

    if ! grep -q "^# Technical Checklist" "$TECH_CHECKLIST"; then
        echo "ERROR: Technical checklist missing title" >&2
        return 4
    fi

    echo "✓ Markdown format valid" >&2
    return 0
}

# Main validation
main() {
    local exit_code=0

    validate_files_exist || exit_code=$?
    [[ $exit_code -ne 0 ]] && exit $exit_code

    validate_traceability || exit_code=$?
    [[ $exit_code -ne 0 ]] && exit $exit_code

    validate_forbidden_terms || exit_code=$?
    [[ $exit_code -ne 0 ]] && exit $exit_code

    validate_markdown_format || exit_code=$?
    [[ $exit_code -ne 0 ]] && exit $exit_code

    echo "✓ All validations passed" >&2
    return 0
}

main
