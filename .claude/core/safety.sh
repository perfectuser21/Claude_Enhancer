#!/bin/bash
# Claude Enhancer - Safety Wrapper Functions
# Version: 1.0
# Purpose: Prevent dangerous operations

set -euo pipefail

# Safe rm -rf with validation
safe_rm_rf() {
    local target="$1"
    
    # Validate not dangerous root paths
    if [[ "$target" =~ ^(/|/bin|/usr|/etc|/var|/home|/root|$HOME)$ ]]; then
        echo "❌ Refusing dangerous path: $target" >&2
        echo "   This appears to be a system directory" >&2
        return 1
    fi
    
    # Validate target exists
    if [[ ! -e "$target" ]]; then
        # Not an error - already doesn't exist
        return 0
    fi
    
    # Validate under project (if PROJECT_ROOT is set)
    if [[ -n "${PROJECT_ROOT:-}" ]]; then
        local abs_target
        abs_target=$(cd "$(dirname "$target")" && pwd)/$(basename "$target")
        
        if [[ ! "$abs_target" =~ ^"$PROJECT_ROOT" ]]; then
            echo "❌ Refusing to delete path outside project: $target" >&2
            echo "   Project root: $PROJECT_ROOT" >&2
            echo "   Target path: $abs_target" >&2
            return 1
        fi
    fi
    
    # Execute with safety flags
    rm -rf --preserve-root -- "$target"
}

# Safe directory creation
safe_mkdir() {
    local target="$1"
    
    # Validate not trying to create root paths
    if [[ "$target" =~ ^(/|/bin|/usr|/etc|/var)$ ]]; then
        echo "❌ Refusing dangerous mkdir: $target" >&2
        return 1
    fi
    
    mkdir -p "$target"
}

# Safe file write with backup
safe_write_file() {
    local file="$1"
    local content="$2"
    local backup
    backup="${file}.backup.$(date +%Y%m%d-%H%M%S)"
    
    # Create backup if file exists
    if [[ -f "$file" ]]; then
        cp "$file" "$backup"
    fi
    
    # Write atomically
    echo "$content" > "${file}.tmp"
    mv "${file}.tmp" "$file"
    
    # Clean old backups (keep last 5)
    find "$(dirname "$file")" -name "$(basename "$file").backup.*" -type f 2>/dev/null | \
        sort -r | tail -n +6 | xargs rm -f 2>/dev/null || true
}

# Validate path is safe for operations
validate_safe_path() {
    local path="$1"
    local _operation="${2:-any}"  # Reserved for future operation-specific checks

    # Check for dangerous patterns
    local dangerous_patterns=(
        "^/$"
        "^/bin"
        "^/usr"
        "^/etc"
        "^/var"
        "^/home$"
        "^/root$"
        "^\.\./\.\."  # Multiple parent directory traversal
    )
    
    for pattern in "${dangerous_patterns[@]}"; do
        if [[ "$path" =~ $pattern ]]; then
            echo "❌ Dangerous path pattern detected: $path" >&2
            return 1
        fi
    done
    
    # Check for suspicious characters
    if [[ "$path" =~ [';$`'] ]]; then
        echo "❌ Suspicious characters in path: $path" >&2
        return 1
    fi
    
    return 0
}

# Safe command execution with validation
safe_exec() {
    local cmd="$1"
    shift
    local args=("$@")
    
    # Whitelist of safe commands
    local safe_commands=(
        "git" "npm" "yarn" "python3" "pytest" "shellcheck"
        "jq" "grep" "awk" "sed" "find" "cat" "ls"
    )
    
    local is_safe=false
    for safe_cmd in "${safe_commands[@]}"; do
        if [[ "$cmd" == "$safe_cmd" ]]; then
            is_safe=true
            break
        fi
    done
    
    if [[ "$is_safe" == "false" ]]; then
        echo "❌ Command not in safe list: $cmd" >&2
        return 1
    fi
    
    # Execute safely
    "$cmd" "${args[@]}"
}

# Export functions
export -f safe_rm_rf
export -f safe_mkdir
export -f safe_write_file
export -f validate_safe_path
export -f safe_exec
