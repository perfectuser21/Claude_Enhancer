#!/bin/bash

# ================================================================
# File Access Validator Module
# Claude Enhancer 5.0 - Phase-based file access validation
# ================================================================

set -euo pipefail

# File pattern matching function
matches_pattern() {
    local file_path="$1"
    local pattern="$2"

    # Convert glob pattern to regex for matching
    case "$pattern" in
        *"**"*)
            # Handle recursive glob patterns
            local regex_pattern=$(echo "$pattern" | sed 's/\*\*/.*/' | sed 's/\*/[^\/]*/')
            [[ "$file_path" =~ $regex_pattern ]]
            ;;
        *)
            # Simple glob matching
            [[ "$file_path" == $pattern ]]
            ;;
    esac
}

# Check if file is in whitelist
is_file_whitelisted() {
    local phase="$1"
    local file_path="$2"
    local config_file="$3"

    local whitelist_patterns=$(jq -r ".phases[\"$phase\"].file_whitelist[]? // empty" "$config_file" 2>/dev/null)

    while IFS= read -r pattern; do
        [[ -z "$pattern" ]] && continue
        if matches_pattern "$file_path" "$pattern"; then
            return 0
        fi
    done <<< "$whitelist_patterns"

    return 1
}

# Check if file is in blacklist
is_file_blacklisted() {
    local phase="$1"
    local file_path="$2"
    local config_file="$3"

    local blacklist_patterns=$(jq -r ".phases[\"$phase\"].file_blacklist[]? // empty" "$config_file" 2>/dev/null)
    local global_sensitive_files=$(jq -r '.global_restrictions.sensitive_files[]? // empty' "$config_file" 2>/dev/null)

    # Check global sensitive files
    while IFS= read -r pattern; do
        [[ -z "$pattern" ]] && continue
        if matches_pattern "$file_path" "$pattern"; then
            return 0
        fi
    done <<< "$global_sensitive_files"

    # Check phase-specific blacklist
    while IFS= read -r pattern; do
        [[ -z "$pattern" ]] && continue
        if matches_pattern "$file_path" "$pattern"; then
            return 0
        fi
    done <<< "$blacklist_patterns"

    return 1
}

# Main file validation function
validate_file_access() {
    local phase="$1"
    local file_path="$2"
    local config_file="$3"

    # Check blacklist first (takes precedence)
    if is_file_blacklisted "$phase" "$file_path" "$config_file"; then
        echo "File '$file_path' is blacklisted for phase '$phase'"
        return 1
    fi

    # Check whitelist
    if is_file_whitelisted "$phase" "$file_path" "$config_file"; then
        return 0
    fi

    # If not explicitly whitelisted, check strict mode
    local strict_mode=$(jq -r '.enforcement.strict_mode // true' "$config_file" 2>/dev/null)
    if [[ "$strict_mode" == "true" ]]; then
        echo "File '$file_path' not whitelisted in strict mode for phase '$phase'"
        return 1
    fi

    return 0
}

# Export function for use in main controller
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    export -f validate_file_access matches_pattern is_file_whitelisted is_file_blacklisted
fi