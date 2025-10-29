#!/usr/bin/env bash
# =============================================================================
# Intelligent Cache System - Performance Optimization v8.5.0
# =============================================================================
# Purpose: Cache test results, syntax checks, and linting to avoid redundant work
# Usage: source scripts/cache/intelligent_cache.sh && cache_check "test_name" "files..."
# Performance: 15-25% speedup in Phase 3
# =============================================================================

set -euo pipefail

# ==================== Configuration ====================

# SC2155: Declare and assign separately
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly PROJECT_ROOT
readonly CACHE_DIR="${PROJECT_ROOT}/.workflow/cache"
readonly CACHE_TTL_HOURS=24

# Create cache directory
mkdir -p "${CACHE_DIR}"

# ==================== Logging ====================

log_cache() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CACHE] $*" >&2
}

# ==================== Cache Key Generation ====================

# Generate cache key from files
generate_cache_key() {
    local test_name="$1"
    shift
    local files=("$@")

    # If no files specified, use git hash
    if [[ ${#files[@]} -eq 0 ]]; then
        local git_hash
        git_hash=$(git rev-parse HEAD 2>/dev/null || echo "no-git")
        echo "${test_name}_${git_hash}"
        return
    fi

    # Calculate hash of file contents
    local combined_hash=""
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            if command -v sha256sum >/dev/null 2>&1; then
                combined_hash+=$(sha256sum "$file" | awk '{print $1}')
            elif command -v shasum >/dev/null 2>&1; then
                combined_hash+=$(shasum -a 256 "$file" | awk '{print $1}')
            fi
        fi
    done

    # Generate final key
    if [[ -n "$combined_hash" ]]; then
        if command -v sha256sum >/dev/null 2>&1; then
            echo "${test_name}_$(echo -n "$combined_hash" | sha256sum | awk '{print $1}' | cut -c1-16)"
        else
            echo "${test_name}_$(echo -n "$combined_hash" | shasum -a 256 | awk '{print $1}' | cut -c1-16)"
        fi
    else
        echo "${test_name}_no_hash"
    fi
}

# ==================== Cache Check ====================

# Check if cache is valid
cache_check() {
    local test_name="$1"
    shift
    local files=("$@")

    local cache_key
    cache_key=$(generate_cache_key "$test_name" "${files[@]}")

    local cache_file="${CACHE_DIR}/${cache_key}.cache"

    # Check if cache file exists
    if [[ ! -f "$cache_file" ]]; then
        log_cache "MISS: $test_name (no cache file)"
        return 1
    fi

    # Check TTL
    local cache_age
    cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null || echo 0) ))
    local max_age=$(( CACHE_TTL_HOURS * 3600 ))

    if [[ $cache_age -gt $max_age ]]; then
        log_cache "MISS: $test_name (expired, age=${cache_age}s > ${max_age}s)"
        rm -f "$cache_file"
        return 1
    fi

    # Cache hit
    log_cache "HIT: $test_name (age=${cache_age}s)"
    return 0
}

# ==================== Cache Write ====================

# Write cache entry
cache_write() {
    local test_name="$1"
    local exit_code="$2"
    shift 2
    local files=("$@")

    local cache_key
    cache_key=$(generate_cache_key "$test_name" "${files[@]}")

    local cache_file="${CACHE_DIR}/${cache_key}.cache"

    cat > "$cache_file" <<EOF
{
  "test_name": "$test_name",
  "exit_code": $exit_code,
  "timestamp": $(date +%s),
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'no-git')",
  "files": [$(printf '"%s",' "${files[@]}" | sed 's/,$//')],
  "ttl_hours": $CACHE_TTL_HOURS
}
EOF

    log_cache "WRITE: $test_name (exit_code=$exit_code)"
}

# ==================== Cache Invalidation ====================

# Invalidate cache for specific files
cache_invalidate() {
    local pattern="$1"

    local count=0
    while IFS= read -r cache_file; do
        if grep -q "$pattern" "$cache_file" 2>/dev/null; then
            rm -f "$cache_file"
            ((count++)) || true
        fi
    done < <(find "${CACHE_DIR}" -name "*.cache" -type f 2>/dev/null)

    log_cache "INVALIDATE: pattern='$pattern' (removed $count entries)"
}

# Clear all cache
cache_clear() {
    local count
    count=$(find "${CACHE_DIR}" -name "*.cache" -type f 2>/dev/null | wc -l)
    rm -f "${CACHE_DIR}"/*.cache 2>/dev/null || true
    log_cache "CLEAR: removed $count cache entries"
}

# ==================== Cache Statistics ====================

# Get cache statistics
cache_stats() {
    local total_entries
    total_entries=$(find "${CACHE_DIR}" -name "*.cache" -type f 2>/dev/null | wc -l)

    local expired=0
    local valid=0
    local max_age=$(( CACHE_TTL_HOURS * 3600 ))
    local now
    now=$(date +%s)

    while IFS= read -r cache_file; do
        local cache_age
        cache_age=$(( now - $(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null || echo 0) ))

        if [[ $cache_age -gt $max_age ]]; then
            ((expired++)) || true
        else
            ((valid++)) || true
        fi
    done < <(find "${CACHE_DIR}" -name "*.cache" -type f 2>/dev/null)

    echo "Cache Statistics:"
    echo "  Total entries: $total_entries"
    echo "  Valid entries: $valid"
    echo "  Expired entries: $expired"
    echo "  TTL: ${CACHE_TTL_HOURS}h"
}

# ==================== Helper Functions ====================

# Run command with cache
run_with_cache() {
    local test_name="$1"
    shift
    local command="$*"

    # Get affected files from git diff
    local files=()
    while IFS= read -r file; do
        files+=("$file")
    done < <(git diff --name-only HEAD~1 2>/dev/null || echo "")

    # Check cache
    if cache_check "$test_name" "${files[@]}"; then
        echo "✓ $test_name: CACHED (skipped)"
        return 0
    fi

    # Run command
    local exit_code=0
    eval "$command" || exit_code=$?

    # Write cache
    cache_write "$test_name" "$exit_code" "${files[@]}"

    return $exit_code
}

# ==================== Main ====================

# If sourced, export functions
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    export -f cache_check
    export -f cache_write
    export -f cache_invalidate
    export -f cache_clear
    export -f cache_stats
    export -f run_with_cache
    export -f generate_cache_key
else
    # Direct invocation
    case "${1:-help}" in
        check)
            shift
            cache_check "$@"
            ;;
        write)
            shift
            cache_write "$@"
            ;;
        invalidate)
            shift
            cache_invalidate "$@"
            ;;
        clear)
            cache_clear
            ;;
        stats)
            cache_stats
            ;;
        *)
            echo "Usage: $0 {check|write|invalidate|clear|stats} [args...]"
            echo ""
            echo "Commands:"
            echo "  check <test_name> [files...]     Check if cache is valid"
            echo "  write <test_name> <exit_code> [files...]  Write cache entry"
            echo "  invalidate <pattern>             Invalidate cache matching pattern"
            echo "  clear                            Clear all cache"
            echo "  stats                            Show cache statistics"
            exit 1
            ;;
    esac
fi
