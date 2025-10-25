#!/bin/bash
# Cache Manager for Claude Enhancer
# Purpose: Prevent duplicate execution of expensive checks
# Version: 1.0.0
# Created: 2025-10-25

set -euo pipefail

# Cache configuration
readonly CACHE_DIR="${HOME}/.cache/claude-enhancer"
readonly CACHE_TTL_SECONDS=300  # 5 minutes default TTL
readonly CACHE_VERSION="1.0.0"

# Ensure cache directory exists
mkdir -p "$CACHE_DIR"

# Function: Generate cache key from command
generate_cache_key() {
    local command="$1"
    local context="${2:-default}"

    # Create deterministic hash from command + context
    echo -n "${command}:${context}" | sha256sum | cut -d' ' -f1
}

# Function: Get cache file path
get_cache_file() {
    local cache_key="$1"
    echo "${CACHE_DIR}/${cache_key}.cache"
}

# Function: Check if cache is valid
is_cache_valid() {
    local cache_file="$1"
    local ttl="${2:-$CACHE_TTL_SECONDS}"

    if [[ ! -f "$cache_file" ]]; then
        return 1  # Cache doesn't exist
    fi

    # Check if cache has expired
    local cache_age
    cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || echo 0) ))

    if [[ $cache_age -gt $ttl ]]; then
        return 1  # Cache expired
    fi

    return 0  # Cache is valid
}

# Function: Read from cache
read_cache() {
    local command="$1"
    local context="${2:-default}"
    local ttl="${3:-$CACHE_TTL_SECONDS}"

    local cache_key
    cache_key=$(generate_cache_key "$command" "$context")
    local cache_file
    cache_file=$(get_cache_file "$cache_key")

    if is_cache_valid "$cache_file" "$ttl"; then
        # Cache hit - return cached result
        cat "$cache_file"
        return 0
    else
        # Cache miss
        return 1
    fi
}

# Function: Write to cache
write_cache() {
    local command="$1"
    local context="${2:-default}"
    local data="$3"

    local cache_key
    cache_key=$(generate_cache_key "$command" "$context")
    local cache_file
    cache_file=$(get_cache_file "$cache_key")

    # Write data to cache with metadata
    {
        echo "# Cache Version: $CACHE_VERSION"
        echo "# Command: $command"
        echo "# Context: $context"
        echo "# Timestamp: $(date -Iseconds)"
        echo "# ---"
        echo "$data"
    } > "$cache_file"
}

# Function: Execute command with caching
execute_with_cache() {
    local command="$1"
    local context="${2:-default}"
    local ttl="${3:-$CACHE_TTL_SECONDS}"

    # Try to read from cache first
    if result=$(read_cache "$command" "$context" "$ttl"); then
        # Extract actual data (skip metadata lines)
        echo "$result" | sed '1,/^# ---$/d'
        echo "[CACHE HIT] Command result served from cache" >&2
        return 0
    fi

    # Cache miss - execute command
    echo "[CACHE MISS] Executing command..." >&2
    local result
    if result=$(eval "$command" 2>&1); then
        # Success - write to cache
        write_cache "$command" "$context" "$result"
        echo "$result"
        return 0
    else
        # Command failed - don't cache failures
        echo "$result"
        return 1
    fi
}

# Function: Invalidate cache
invalidate_cache() {
    local pattern="${1:-*}"

    if [[ "$pattern" == "*" ]]; then
        # Clear all cache
        rm -f "${CACHE_DIR}"/*.cache
        echo "All cache cleared" >&2
    else
        # Clear specific pattern
        local count=0
        for cache_file in "${CACHE_DIR}"/*"${pattern}"*.cache; do
            if [[ -f "$cache_file" ]]; then
                rm -f "$cache_file"
                ((count++))
            fi
        done
        echo "Cleared $count cache entries matching pattern: $pattern" >&2
    fi
}

# Function: Show cache statistics
cache_stats() {
    local total_files
    total_files=$(find "$CACHE_DIR" -name "*.cache" 2>/dev/null | wc -l)

    local total_size
    total_size=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)

    local expired=0
    local valid=0

    for cache_file in "${CACHE_DIR}"/*.cache; do
        if [[ -f "$cache_file" ]]; then
            if is_cache_valid "$cache_file"; then
                ((valid++))
            else
                ((expired++))
            fi
        fi
    done

    cat <<EOF
Cache Statistics:
  Directory: $CACHE_DIR
  Total files: $total_files
  Valid entries: $valid
  Expired entries: $expired
  Total size: $total_size
  TTL: ${CACHE_TTL_SECONDS}s
EOF
}

# Function: Clean expired cache entries
clean_expired() {
    local cleaned=0

    for cache_file in "${CACHE_DIR}"/*.cache; do
        if [[ -f "$cache_file" ]]; then
            if ! is_cache_valid "$cache_file"; then
                rm -f "$cache_file"
                ((cleaned++))
            fi
        fi
    done

    echo "Cleaned $cleaned expired cache entries" >&2
}

# Main execution (if called directly)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        stats)
            cache_stats
            ;;
        clean)
            clean_expired
            ;;
        invalidate)
            invalidate_cache "${2:-*}"
            ;;
        test)
            # Test the cache with a simple command
            echo "Testing cache with 'date' command..."
            execute_with_cache "date" "test" 5
            sleep 1
            execute_with_cache "date" "test" 5  # Should hit cache
            sleep 5
            execute_with_cache "date" "test" 5  # Cache expired
            ;;
        *)
            cat <<EOF
Usage: $(basename "$0") [command] [args]

Commands:
  stats              Show cache statistics
  clean              Clean expired cache entries
  invalidate [pat]   Invalidate cache entries (all or matching pattern)
  test               Run a simple cache test

Example usage in scripts:
  source cache_manager.sh
  result=\$(execute_with_cache "expensive_check --all" "branch-check" 600)
EOF
            ;;
    esac
fi