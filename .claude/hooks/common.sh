#!/usr/bin/env bash
# Common functions for dual-language checklist system
# Used by: checklist_generator.sh, validate_checklist_mapping.sh, acceptance_report_generator.sh

set -Eeuo pipefail
IFS=$'\n\t'

# Dependency check
need() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "ERROR: Missing dependency: $1" >&2
        echo "Install with: sudo apt-get install $1" >&2
        exit 90
    }
}

# Check all required tools
check_deps() {
    need yq
    need jq
}

# Atomic write (Alex's improved version with permission preservation)
out_atomic() {
    local target="$1"
    local tmp; tmp="$(mktemp "${target}.XXXXXX")"
    trap 'rm -f "$tmp"' EXIT
    cat >"$tmp"
    chmod --reference="$target" "$tmp" 2>/dev/null || chmod 644 "$tmp"
    mv -f "$tmp" "$target"
    trap - EXIT
}

# File locking wrapper
with_lock() {
    local lockfile="$1"
    shift
    exec 9>"$lockfile"
    if ! flock -w 15 9; then
        echo "ERROR: Could not acquire lock on $lockfile after 15 seconds" >&2
        exit 91
    fi
    "$@"
    flock -u 9
}

# Get analogy from library
get_analogy() {
    local feature="$1"
    local lib="${ANALOGY_LIB:-.claude/data/analogy_library.yml}"

    if [[ ! -f "$lib" ]]; then
        echo "（功能说明）"
        return
    fi

    # Try each category
    local categories
    categories=$(yq eval '.categories | keys | .[]' "$lib" 2>/dev/null)

    while IFS= read -r category; do
        # For each pattern in this category, check if feature matches
        local count
        count=$(yq eval ".categories.$category | length" "$lib" 2>/dev/null)

        for ((i=0; i<count; i++)); do
            local pattern analogy
            pattern=$(yq eval ".categories.$category[$i].pattern" "$lib" 2>/dev/null)

            # Test if feature matches this pattern
            if echo "$feature" | grep -qiE "$pattern"; then
                analogy=$(yq eval ".categories.$category[$i].analogy" "$lib" 2>/dev/null)
                echo "$analogy"
                return
            fi
        done
    done <<< "$categories"

    echo "（功能说明）"
}

# Get "why" explanation
get_why() {
    local feature="$1"
    local lib="${ANALOGY_LIB:-.claude/data/analogy_library.yml}"

    if [[ ! -f "$lib" ]]; then
        echo "提供此功能"
        return
    fi

    # Try each category
    local categories
    categories=$(yq eval '.categories | keys | .[]' "$lib" 2>/dev/null)

    while IFS= read -r category; do
        # For each pattern in this category, check if feature matches
        local count
        count=$(yq eval ".categories.$category | length" "$lib" 2>/dev/null)

        for ((i=0; i<count; i++)); do
            local pattern why
            pattern=$(yq eval ".categories.$category[$i].pattern" "$lib" 2>/dev/null)

            # Test if feature matches this pattern
            if echo "$feature" | grep -qiE "$pattern"; then
                why=$(yq eval ".categories.$category[$i].why" "$lib" 2>/dev/null)
                echo "$why"
                return
            fi
        done
    done <<< "$categories"

    echo "提供此功能"
}

# Check forbidden terms (skip code blocks)
check_forbidden_terms() {
    local file="$1"
    local lib="${ANALOGY_LIB:-.claude/data/analogy_library.yml}"

    # Get forbidden terms list
    local forbidden_terms
    forbidden_terms=$(yq eval '.forbidden_terms[]' "$lib" 2>/dev/null)

    if [[ -z "$forbidden_terms" ]]; then
        return 0
    fi

    # Remove code blocks and inline code, then check
    local cleaned
    cleaned=$(sed '/^```/,/^```/d' "$file" | sed 's/`[^`]*`//g')

    local found=0
    while IFS= read -r term; do
        if echo "$cleaned" | grep -iqw "$term"; then
            echo "ERROR: Forbidden term '$term' found in user checklist" >&2
            found=1
        fi
    done <<< "$forbidden_terms"

    return $found
}

# Generate unique ID
gen_id() {
    local prefix="$1"
    local num="$2"
    printf "%s-%03d" "$prefix" "$num"
}

export -f need check_deps out_atomic with_lock get_analogy get_why check_forbidden_terms gen_id
