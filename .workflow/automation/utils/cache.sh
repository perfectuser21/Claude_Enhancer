#!/usr/bin/env bash
# Caching Layer for Claude Enhancer v5.4.0
# Purpose: Reduce expensive operations through intelligent caching
# Used by: All automation scripts

set -euo pipefail

# Configuration
CACHE_DIR="${CE_CACHE_DIR:-/tmp/ce_cache}"
CACHE_TTL="${CE_CACHE_TTL:-900}"  # 15 minutes default
CACHE_ENABLED="${CE_CACHE_ENABLED:-1}"
MAX_CACHE_SIZE_MB="${CE_MAX_CACHE_SIZE_MB:-100}"

# Ensure cache directory exists
mkdir -p "$CACHE_DIR"

# Cache statistics
declare -A CACHE_STATS=(
    [hits]=0
    [misses]=0
    [evictions]=0
    [writes]=0
)

# ============================================================================
# Core Cache Functions
# ============================================================================

cache_key_hash() {
    local key="$1"
    echo -n "$key" | md5sum 2>/dev/null | cut -d' ' -f1 || echo -n "$key" | shasum -a 256 | cut -d' ' -f1
}

cache_get() {
    local key="$1"
    local key_hash=$(cache_key_hash "$key")
    local cache_file="${CACHE_DIR}/${key_hash}.cache"
    local meta_file="${CACHE_DIR}/${key_hash}.meta"

    if [[ "$CACHE_ENABLED" != "1" ]]; then
        return 1
    fi

    # Check if cache exists
    if [[ ! -f "$cache_file" || ! -f "$meta_file" ]]; then
        CACHE_STATS[misses]=$((${CACHE_STATS[misses]} + 1))
        return 1
    fi

    # Check TTL
    local created_at=$(cat "$meta_file" 2>/dev/null || echo "0")
    local now=$(date +%s)
    local age=$((now - created_at))

    if [[ $age -gt $CACHE_TTL ]]; then
        # Expired
        rm -f "$cache_file" "$meta_file"
        CACHE_STATS[misses]=$((${CACHE_STATS[misses]} + 1))
        CACHE_STATS[evictions]=$((${CACHE_STATS[evictions]} + 1))
        return 1
    fi

    # Cache hit
    CACHE_STATS[hits]=$((${CACHE_STATS[hits]} + 1))
    cat "$cache_file"
    return 0
}

cache_set() {
    local key="$1"
    local value="$2"
    local ttl="${3:-$CACHE_TTL}"

    if [[ "$CACHE_ENABLED" != "1" ]]; then
        return 0
    fi

    local key_hash=$(cache_key_hash "$key")
    local cache_file="${CACHE_DIR}/${key_hash}.cache"
    local meta_file="${CACHE_DIR}/${key_hash}.meta"

    # Store value
    echo "$value" > "$cache_file"

    # Store metadata (creation timestamp)
    date +%s > "$meta_file"

    CACHE_STATS[writes]=$((${CACHE_STATS[writes]} + 1))

    # Check cache size and evict if necessary
    check_cache_size
}

cache_delete() {
    local key="$1"
    local key_hash=$(cache_key_hash "$key")
    local cache_file="${CACHE_DIR}/${key_hash}.cache"
    local meta_file="${CACHE_DIR}/${key_hash}.meta"

    rm -f "$cache_file" "$meta_file"
}

cache_clear() {
    rm -rf "${CACHE_DIR}"/*
    mkdir -p "$CACHE_DIR"
    CACHE_STATS[evictions]=$((${CACHE_STATS[evictions]} + ${CACHE_STATS[writes]}))
    CACHE_STATS[writes]=0
}

cache_exists() {
    local key="$1"
    local key_hash=$(cache_key_hash "$key")
    local cache_file="${CACHE_DIR}/${key_hash}.cache"
    local meta_file="${CACHE_DIR}/${key_hash}.meta"

    if [[ -f "$cache_file" && -f "$meta_file" ]]; then
        # Check if not expired
        local created_at=$(cat "$meta_file" 2>/dev/null || echo "0")
        local now=$(date +%s)
        local age=$((now - created_at))

        if [[ $age -le $CACHE_TTL ]]; then
            return 0
        fi
    fi

    return 1
}

# ============================================================================
# Cache Size Management
# ============================================================================

get_cache_size_mb() {
    local size_kb=$(du -sk "$CACHE_DIR" 2>/dev/null | cut -f1 || echo "0")
    echo "scale=2; $size_kb / 1024" | bc
}

check_cache_size() {
    local size_mb=$(get_cache_size_mb)

    if (( $(echo "$size_mb > $MAX_CACHE_SIZE_MB" | bc -l) )); then
        # Evict oldest entries
        evict_oldest_entries
    fi
}

evict_oldest_entries() {
    # Find and remove oldest 25% of cache
    local total_files=$(find "$CACHE_DIR" -name "*.cache" | wc -l)
    local to_remove=$((total_files / 4))

    if [[ $to_remove -gt 0 ]]; then
        find "$CACHE_DIR" -name "*.cache" -type f -printf '%T@ %p\n' | \
            sort -n | \
            head -n "$to_remove" | \
            cut -d' ' -f2- | \
            while read -r file; do
                rm -f "$file" "${file%.cache}.meta"
                CACHE_STATS[evictions]=$((${CACHE_STATS[evictions]} + 1))
            done
    fi
}

# ============================================================================
# Specialized Cache Functions
# ============================================================================

cache_github_api() {
    local endpoint="$1"
    local ttl="${2:-900}"  # 15 minutes for API responses

    local cache_key="gh_api:${endpoint}"

    # Try to get from cache
    if cache_exists "$cache_key"; then
        cache_get "$cache_key"
        return 0
    fi

    # Fetch from API
    local response
    if command -v gh &>/dev/null; then
        response=$(gh api "$endpoint" 2>/dev/null || echo "")
    else
        return 1
    fi

    # Cache the response
    if [[ -n "$response" ]]; then
        cache_set "$cache_key" "$response" "$ttl"
        echo "$response"
        return 0
    fi

    return 1
}

cache_git_command() {
    local cmd="$1"
    local ttl="${2:-300}"  # 5 minutes for git commands

    local cache_key="git_cmd:${cmd}"

    # Try to get from cache
    if cache_exists "$cache_key"; then
        cache_get "$cache_key"
        return 0
    fi

    # Execute git command
    local result
    result=$(eval "$cmd" 2>/dev/null || echo "")

    # Cache the result
    if [[ -n "$result" ]]; then
        cache_set "$cache_key" "$result" "$ttl"
        echo "$result"
        return 0
    fi

    return 1
}

cache_file_stat() {
    local file="$1"
    local ttl="${2:-60}"  # 1 minute for file stats

    local cache_key="file_stat:${file}"

    # Try to get from cache
    if cache_exists "$cache_key"; then
        cache_get "$cache_key"
        return 0
    fi

    # Get file stats
    local stat_result
    if [[ -f "$file" ]]; then
        stat_result=$(stat "$file" 2>/dev/null || echo "")
    else
        return 1
    fi

    # Cache the result
    if [[ -n "$stat_result" ]]; then
        cache_set "$cache_key" "$stat_result" "$ttl"
        echo "$stat_result"
        return 0
    fi

    return 1
}

# ============================================================================
# Memoization Support
# ============================================================================

memoize() {
    local func_name="$1"
    shift
    local args=("$@")

    # Create cache key from function name and arguments
    local cache_key="${func_name}:$(printf '%s,' "${args[@]}")"

    # Try to get cached result
    if cache_exists "$cache_key"; then
        cache_get "$cache_key"
        return 0
    fi

    # Execute function and cache result
    local result
    result=$("$func_name" "${args[@]}")
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        cache_set "$cache_key" "$result"
        echo "$result"
    fi

    return $exit_code
}

# ============================================================================
# Cache Warming
# ============================================================================

warm_cache() {
    local items=("$@")

    for item in "${items[@]}"; do
        case "$item" in
            git_status)
                cache_git_command "git status --porcelain" 300
                ;;
            git_branches)
                cache_git_command "git branch -a" 600
                ;;
            git_remotes)
                cache_git_command "git remote -v" 600
                ;;
            github_user)
                cache_github_api "/user" 3600
                ;;
            github_repo)
                local repo=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]\([^/]*\/[^.]*\).*/\1/')
                if [[ -n "$repo" ]]; then
                    cache_github_api "/repos/${repo}" 900
                fi
                ;;
        esac
    done
}

# ============================================================================
# Cache Statistics and Monitoring
# ============================================================================

get_cache_stats() {
    local total_requests=$((${CACHE_STATS[hits]} + ${CACHE_STATS[misses]}))
    local hit_rate=0

    if [[ $total_requests -gt 0 ]]; then
        hit_rate=$(echo "scale=2; ${CACHE_STATS[hits]} * 100 / $total_requests" | bc)
    fi

    local cache_size=$(get_cache_size_mb)
    local cache_files=$(find "$CACHE_DIR" -name "*.cache" | wc -l)

    cat <<EOF
Cache Statistics:
  Hits:         ${CACHE_STATS[hits]}
  Misses:       ${CACHE_STATS[misses]}
  Hit Rate:     ${hit_rate}%
  Writes:       ${CACHE_STATS[writes]}
  Evictions:    ${CACHE_STATS[evictions]}
  Size:         ${cache_size}MB / ${MAX_CACHE_SIZE_MB}MB
  Files:        ${cache_files}
  TTL:          ${CACHE_TTL}s
  Enabled:      ${CACHE_ENABLED}
EOF
}

show_cache_contents() {
    local format="${1:-summary}"

    echo "Cache Contents:"
    echo ""

    case "$format" in
        detailed)
            find "$CACHE_DIR" -name "*.cache" -type f -printf '%T@ %p\n' | \
                sort -rn | \
                while read -r timestamp file; do
                    local meta_file="${file%.cache}.meta"
                    local created_at=$(cat "$meta_file" 2>/dev/null || echo "0")
                    local now=$(date +%s)
                    local age=$((now - created_at))
                    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
                    local size_kb=$((size / 1024))

                    echo "  File: $(basename "$file")"
                    echo "    Age: ${age}s"
                    echo "    Size: ${size_kb}KB"
                    echo "    TTL Remaining: $((CACHE_TTL - age))s"
                    echo ""
                done
            ;;
        *)
            local total_files=$(find "$CACHE_DIR" -name "*.cache" | wc -l)
            local total_size=$(get_cache_size_mb)
            echo "  Total Files: $total_files"
            echo "  Total Size: ${total_size}MB"
            ;;
    esac
}

# ============================================================================
# Cache Invalidation
# ============================================================================

invalidate_cache_pattern() {
    local pattern="$1"

    find "$CACHE_DIR" -name "*.cache" -type f | while read -r cache_file; do
        local content=$(cat "$cache_file")
        if echo "$content" | grep -q "$pattern"; then
            rm -f "$cache_file" "${cache_file%.cache}.meta"
            CACHE_STATS[evictions]=$((${CACHE_STATS[evictions]} + 1))
        fi
    done
}

invalidate_git_cache() {
    find "$CACHE_DIR" -name "*.cache" -type f | while read -r cache_file; do
        local basename=$(basename "$cache_file" .cache)
        if [[ "$basename" == *"git_cmd"* ]]; then
            rm -f "$cache_file" "${cache_file%.cache}.meta"
        fi
    done
}

invalidate_github_cache() {
    find "$CACHE_DIR" -name "*.cache" -type f | while read -r cache_file; do
        local basename=$(basename "$cache_file" .cache)
        if [[ "$basename" == *"gh_api"* ]]; then
            rm -f "$cache_file" "${cache_file%.cache}.meta"
        fi
    done
}

# ============================================================================
# Automatic Cache Cleanup
# ============================================================================

cleanup_expired_cache() {
    local removed=0
    local now=$(date +%s)

    find "$CACHE_DIR" -name "*.meta" -type f | while read -r meta_file; do
        local created_at=$(cat "$meta_file" 2>/dev/null || echo "0")
        local age=$((now - created_at))

        if [[ $age -gt $CACHE_TTL ]]; then
            local cache_file="${meta_file%.meta}.cache"
            rm -f "$cache_file" "$meta_file"
            removed=$((removed + 1))
        fi
    done

    echo "Removed $removed expired cache entries"
}

# ============================================================================
# Cache Preloading
# ============================================================================

preload_common_data() {
    # Preload frequently accessed data in background
    (
        # Git information
        cache_git_command "git status --porcelain" 300 &
        cache_git_command "git branch -a" 600 &
        cache_git_command "git remote -v" 600 &

        # GitHub information (if available)
        if command -v gh &>/dev/null; then
            cache_github_api "/user" 3600 &
        fi

        wait
    ) &
}

# ============================================================================
# Export Functions
# ============================================================================

export -f cache_get
export -f cache_set
export -f cache_delete
export -f cache_clear
export -f cache_exists
export -f cache_github_api
export -f cache_git_command
export -f memoize
export -f get_cache_stats
export -f invalidate_git_cache
export -f invalidate_github_cache
export -f cleanup_expired_cache

# Auto-cleanup on startup
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Cleanup expired entries in background
    cleanup_expired_cache > /dev/null 2>&1 &
fi
