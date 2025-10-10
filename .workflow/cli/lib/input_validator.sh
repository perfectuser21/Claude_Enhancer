#!/usr/bin/env bash
# input_validator.sh - Comprehensive input validation and sanitization
# Security: Prevents command injection, path traversal, and malicious input
set -euo pipefail

# ============================================================================
# Input Sanitization Functions
# ============================================================================

# Sanitize alphanumeric input with hyphens
# Usage: sanitized=$(ce_sanitize_alphanum "user-input" 50)
# Returns: Sanitized string with only alphanumeric and hyphens
ce_sanitize_alphanum() {
    local input="$1"
    local max_length="${2:-256}"
    
    # Remove all non-alphanumeric characters except hyphens
    local sanitized="${input//[^a-zA-Z0-9-]/}"
    
    # Truncate to max length
    sanitized="${sanitized:0:$max_length}"
    
    echo "$sanitized"
}

# Sanitize for use in filenames (replace slashes, remove dangerous chars)
# Usage: filename=$(ce_sanitize_filename "user/input.txt")
# Returns: Safe filename string
ce_sanitize_filename() {
    local input="$1"
    local max_length="${2:-255}"
    
    # Replace slashes with underscores
    local sanitized="${input//\//_}"
    
    # Remove any remaining dangerous characters (keep alphanum, underscore, dot, hyphen)
    sanitized="${sanitized//[^a-zA-Z0-9_.-]/}"
    
    # Remove leading dots (prevent hidden files)
    sanitized="${sanitized#.}"
    
    # Truncate to max length
    sanitized="${sanitized:0:$max_length}"
    
    echo "$sanitized"
}

# ============================================================================
# Validation Functions
# ============================================================================

# Validate feature name
# Security: Prevents command injection via feature names
# Pattern: lowercase alphanumeric + hyphens, 2-50 chars
ce_validate_feature_name() {
    local feature_name="$1"
    
    # Length check
    local len=${#feature_name}
    if [[ $len -lt 2 || $len -gt 50 ]]; then
        echo "Error: Feature name must be 2-50 characters (got: $len)" >&2
        return 1
    fi
    
    # Pattern check: lowercase alphanumeric and hyphens only
    if [[ ! "$feature_name" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]]; then
        echo "Error: Feature name must contain only lowercase letters, numbers, and hyphens" >&2
        echo "Error: Must start and end with alphanumeric character" >&2
        return 1
    fi
    
    # No consecutive hyphens
    if [[ "$feature_name" =~ -- ]]; then
        echo "Error: Feature name cannot contain consecutive hyphens" >&2
        return 1
    fi
    
    # Prevent command injection patterns
    if [[ "$feature_name" =~ [\;\|\&\$\`] ]]; then
        echo "Error: Feature name contains prohibited characters" >&2
        return 1
    fi
    
    return 0
}

# Validate terminal ID
# Security: Prevents path traversal via terminal IDs
# Pattern: t[0-9]+ (e.g., t1, t2, t123)
ce_validate_terminal_id() {
    local terminal_id="$1"
    
    # Pattern: t followed by digits only
    if [[ ! "$terminal_id" =~ ^t[0-9]+$ ]]; then
        echo "Error: Terminal ID must match pattern 't[0-9]+' (e.g., t1, t2, t123)" >&2
        return 1
    fi
    
    # Length check (reasonable limit: t + up to 18 digits)
    if [[ ${#terminal_id} -gt 20 ]]; then
        echo "Error: Terminal ID too long (max 20 characters)" >&2
        return 1
    fi
    
    # Explicit path traversal prevention (belt and suspenders)
    if [[ "$terminal_id" == *".."* ]] || [[ "$terminal_id" == *"/"* ]] || [[ "$terminal_id" == *"\\"* ]]; then
        echo "Error: Terminal ID contains invalid path characters" >&2
        return 1
    fi
    
    return 0
}

# Validate and canonicalize path (prevent traversal)
# Security: Ensures path is within allowed directory
# Usage: safe_path=$(ce_validate_path "$user_input" "$allowed_prefix")
ce_validate_path() {
    local input_path="$1"
    local allowed_prefix="$2"
    
    # Input validation
    if [[ -z "$input_path" ]]; then
        echo "Error: Path cannot be empty" >&2
        return 1
    fi
    
    if [[ -z "$allowed_prefix" ]]; then
        echo "Error: Allowed prefix must be specified" >&2
        return 1
    fi
    
    # Resolve to absolute canonical path
    local canonical_path
    canonical_path=$(realpath -m "$input_path" 2>/dev/null) || {
        echo "Error: Invalid path: $input_path" >&2
        return 1
    }
    
    # Resolve allowed prefix to absolute path
    local canonical_prefix
    canonical_prefix=$(realpath -m "$allowed_prefix" 2>/dev/null) || {
        echo "Error: Invalid allowed prefix: $allowed_prefix" >&2
        return 1
    }
    
    # Ensure canonical_prefix ends without trailing slash for consistent comparison
    canonical_prefix="${canonical_prefix%/}"
    
    # Check if resolved path is within allowed prefix
    # Must either be equal or start with prefix followed by /
    if [[ "$canonical_path" != "$canonical_prefix" ]] && [[ "$canonical_path" != "$canonical_prefix"/* ]]; then
        echo "Error: Path traversal detected - path outside allowed directory" >&2
        echo "Error: Attempted: $canonical_path" >&2
        echo "Error: Allowed: $canonical_prefix" >&2
        return 1
    fi
    
    # Return the validated canonical path
    echo "$canonical_path"
}

# Validate phase name
# Security: Ensures only valid phase names are used
# Pattern: P[0-7]
ce_validate_phase() {
    local phase="$1"
    
    if [[ ! "$phase" =~ ^P[0-7]$ ]]; then
        echo "Error: Invalid phase. Must be P0, P1, P2, P3, P4, P5, P6, or P7" >&2
        return 1
    fi
    
    return 0
}

# Validate branch name
# Security: Prevents malicious branch names
# Pattern: <type>/<description> with restrictions
ce_validate_branch_name() {
    local branch_name="$1"
    
    # Allow common branch patterns
    # Types: feature, feat, fix, docs, test, refactor, chore, hotfix, release
    local valid_pattern='^(feature|feat|fix|docs|test|refactor|chore|hotfix|release)\/[a-zA-Z0-9][a-zA-Z0-9\/_-]*$'
    
    if [[ ! "$branch_name" =~ $valid_pattern ]]; then
        echo "Error: Invalid branch name format" >&2
        echo "Error: Must be <type>/<description> where type is: feature, feat, fix, docs, test, refactor, chore, hotfix, or release" >&2
        return 1
    fi
    
    # Length check
    if [[ ${#branch_name} -lt 3 || ${#branch_name} -gt 80 ]]; then
        echo "Error: Branch name must be 3-80 characters" >&2
        return 1
    fi
    
    # No path traversal patterns
    if [[ "$branch_name" == *".."* ]]; then
        echo "Error: Branch name contains path traversal patterns" >&2
        return 1
    fi
    
    # No command injection characters
    if [[ "$branch_name" =~ [\;\|\&\$\`] ]]; then
        echo "Error: Branch name contains prohibited characters" >&2
        return 1
    fi
    
    return 0
}

# Validate description text
# Security: Prevents injection in descriptions
# Allows most characters but limits length
ce_validate_description() {
    local description="$1"
    local max_length="${2:-500}"
    
    # Length check
    if [[ ${#description} -gt $max_length ]]; then
        echo "Error: Description exceeds maximum length of $max_length characters" >&2
        return 1
    fi
    
    # Reject control characters and null bytes
    if [[ "$description" =~ [[:cntrl:]] ]]; then
        echo "Error: Description contains control characters" >&2
        return 1
    fi
    
    return 0
}

# Validate session ID
# Security: Ensures session IDs are properly formatted
# Pattern: <terminal_id>-<timestamp> or alphanumeric-timestamp
ce_validate_session_id() {
    local session_id="$1"
    
    # Pattern: alphanumeric-timestamp (flexible but safe)
    if [[ ! "$session_id" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "Error: Session ID contains invalid characters" >&2
        return 1
    fi
    
    # Length check
    if [[ ${#session_id} -lt 3 || ${#session_id} -gt 100 ]]; then
        echo "Error: Session ID must be 3-100 characters" >&2
        return 1
    fi
    
    # Path traversal prevention
    if [[ "$session_id" == *".."* ]] || [[ "$session_id" == *"/"* ]]; then
        echo "Error: Session ID contains path traversal patterns" >&2
        return 1
    fi
    
    return 0
}

# Validate commit message
# Security: Basic validation for commit messages
ce_validate_commit_message() {
    local message="$1"
    local min_length="${2:-10}"
    local max_length="${3:-500}"
    
    # Length checks
    if [[ ${#message} -lt $min_length ]]; then
        echo "Error: Commit message too short (minimum $min_length characters)" >&2
        return 1
    fi
    
    if [[ ${#message} -gt $max_length ]]; then
        echo "Error: Commit message too long (maximum $max_length characters)" >&2
        return 1
    fi
    
    # Should not be only whitespace
    if [[ "$message" =~ ^[[:space:]]*$ ]]; then
        echo "Error: Commit message cannot be empty or only whitespace" >&2
        return 1
    fi
    
    return 0
}

# ============================================================================
# Combined Validation Functions
# ============================================================================

# Validate and sanitize feature input (comprehensive)
# Usage: if ce_validate_feature_input "$name" "$desc" "$phase"; then ...
ce_validate_feature_input() {
    local feature_name="$1"
    local description="${2:-}"
    local phase="${3:-P3}"
    
    # Validate feature name
    if ! ce_validate_feature_name "$feature_name"; then
        return 1
    fi
    
    # Validate phase
    if ! ce_validate_phase "$phase"; then
        return 1
    fi
    
    # Validate description if provided
    if [[ -n "$description" ]]; then
        if ! ce_validate_description "$description"; then
            return 1
        fi
    fi
    
    return 0
}

# Validate session path (comprehensive path + terminal ID validation)
# Usage: session_path=$(ce_validate_session_path "$terminal_id" "$base_dir")
ce_validate_session_path() {
    local terminal_id="$1"
    local session_base_dir="${2:-.workflow/state/sessions}"
    
    # Validate terminal ID first
    if ! ce_validate_terminal_id "$terminal_id"; then
        return 1
    fi
    
    # Construct session path
    local session_path="${session_base_dir}/${terminal_id}"
    
    # Validate path is within allowed directory
    local validated_path
    validated_path=$(ce_validate_path "$session_path" "$session_base_dir") || return 1
    
    echo "$validated_path"
}

# ============================================================================
# Export Functions
# ============================================================================

# Export all validation functions for use in other scripts
export -f ce_sanitize_alphanum
export -f ce_sanitize_filename
export -f ce_validate_feature_name
export -f ce_validate_terminal_id
export -f ce_validate_path
export -f ce_validate_phase
export -f ce_validate_branch_name
export -f ce_validate_description
export -f ce_validate_session_id
export -f ce_validate_commit_message
export -f ce_validate_feature_input
export -f ce_validate_session_path
