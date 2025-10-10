#!/usr/bin/env bash
# cache_manager.sh - High-performance caching layer for CE CLI
# Implements 5-minute TTL cache with automatic invalidation
set -euo pipefail

# Cache configuration
CE_CACHE_DIR=".workflow/cli/state/cache"
CE_CACHE_TTL=${CE_CACHE_TTL:-300}  # 5 minutes default
CE_CACHE_ENABLED=${CE_CACHE_ENABLED:-true}
CE_NO_CACHE=${CE_NO_CACHE:-false}  # Set by --no-cache flag

# Performance tracking
declare -g CE_CACHE_HITS=0
declare -g CE_CACHE_MISSES=0
declare -g CE_CACHE_INVALIDATIONS=0

# Initialize cache system
ce_cache_init() {
    if [[ "${CE_NO_CACHE}" == "true" ]]; then
        return 0
    fi

    mkdir -p "${CE_CACHE_DIR}"/{git,state,validation,gates}

    # Create cache metadata file
    local metadata_file="${CE_CACHE_DIR}/.metadata"
    if [[ ! -f "${metadata_file}" ]]; then
        cat > "${metadata_file}" <<EOF
{
  "initialized_at": "$(date -Iseconds)",
  "ttl": ${CE_CACHE_TTL},
  "version": "1.0.0"
}
EOF
    fi
}

# Get cache key hash (for consistent naming)
ce_cache_key_hash() {
    local key="$1"
    echo -n "${key}" | sha256sum | cut -d' ' -f1
}

# Check if cache entry is valid (not expired)
ce_cache_is_valid() {
    local cache_file="$1"

    if [[ "${CE_NO_CACHE}" == "true" ]] || [[ "${CE_CACHE_ENABLED}" != "true" ]]; then
        return 1
    fi

    if [[ ! -f "${cache_file}" ]]; then
        return 1
    fi

    local cache_time
    cache_time=$(stat -c %Y "${cache_file}" 2>/dev/null || stat -f %m "${cache_file}" 2>/dev/null || echo 0)
    local current_time
    current_time=$(date +%s)
    local age=$((current_time - cache_time))

    if [[ ${age} -lt ${CE_CACHE_TTL} ]]; then
        return 0
    else
        return 1
    fi
}

# Get value from cache
ce_cache_get() {
    local cache_category="$1"  # git, state, validation, gates
    local cache_key="$2"

    if [[ "${CE_NO_CACHE}" == "true" ]]; then
        ((CE_CACHE_MISSES++))
        return 1
    fi

    local cache_hash
    cache_hash=$(ce_cache_key_hash "${cache_key}")
    local cache_file="${CE_CACHE_DIR}/${cache_category}/${cache_hash}.cache"

    if ce_cache_is_valid "${cache_file}"; then
        ((CE_CACHE_HITS++))
        cat "${cache_file}"
        return 0
    else
        ((CE_CACHE_MISSES++))
        return 1
    fi
}

# Set value in cache
ce_cache_set() {
    local cache_category="$1"
    local cache_key="$2"
    local value="$3"

    if [[ "${CE_NO_CACHE}" == "true" ]]; then
        return 0
    fi

    local cache_hash
    cache_hash=$(ce_cache_key_hash "${cache_key}")
    local cache_file="${CE_CACHE_DIR}/${cache_category}/${cache_hash}.cache"
    local cache_meta="${CE_CACHE_DIR}/${cache_category}/${cache_hash}.meta"

    # Write cache value atomically
    local temp_file="${cache_file}.tmp.$$"
    echo -n "${value}" > "${temp_file}"
    mv "${temp_file}" "${cache_file}"

    # Write metadata
    cat > "${cache_meta}" <<EOF
{
  "key": "${cache_key}",
  "category": "${cache_category}",
  "created_at": "$(date -Iseconds)",
  "expires_at": "$(date -Iseconds -d "+${CE_CACHE_TTL} seconds" 2>/dev/null || date -Iseconds -v+${CE_CACHE_TTL}S 2>/dev/null)"
}
EOF
}

# Invalidate specific cache entry
ce_cache_invalidate() {
    local cache_category="$1"
    local cache_key="$2"

    local cache_hash
    cache_hash=$(ce_cache_key_hash "${cache_key}")
    local cache_file="${CE_CACHE_DIR}/${cache_category}/${cache_hash}.cache"
    local cache_meta="${CE_CACHE_DIR}/${cache_category}/${cache_hash}.meta"

    if [[ -f "${cache_file}" ]]; then
        rm -f "${cache_file}" "${cache_meta}"
        ((CE_CACHE_INVALIDATIONS++))
    fi
}

# Invalidate entire category
ce_cache_invalidate_category() {
    local cache_category="$1"

    if [[ -d "${CE_CACHE_DIR}/${cache_category}" ]]; then
        local count
        count=$(find "${CE_CACHE_DIR}/${cache_category}" -name "*.cache" | wc -l)
        rm -rf "${CE_CACHE_DIR}/${cache_category}"/*
        CE_CACHE_INVALIDATIONS=$((CE_CACHE_INVALIDATIONS + count))
    fi
}

# Clear all cache
ce_cache_clear() {
    if [[ -d "${CE_CACHE_DIR}" ]]; then
        local count
        count=$(find "${CE_CACHE_DIR}" -name "*.cache" | wc -l)
        find "${CE_CACHE_DIR}" -name "*.cache" -delete
        find "${CE_CACHE_DIR}" -name "*.meta" -delete
        CE_CACHE_INVALIDATIONS=$((CE_CACHE_INVALIDATIONS + count))
        echo "Cleared ${count} cache entries"
    fi
}

# Clean expired cache entries
ce_cache_cleanup_expired() {
    local cleaned=0

    if [[ ! -d "${CE_CACHE_DIR}" ]]; then
        return 0
    fi

    while IFS= read -r cache_file; do
        if ! ce_cache_is_valid "${cache_file}"; then
            local cache_meta="${cache_file%.cache}.meta"
            rm -f "${cache_file}" "${cache_meta}"
            ((cleaned++))
        fi
    done < <(find "${CE_CACHE_DIR}" -name "*.cache" 2>/dev/null)

    if [[ ${cleaned} -gt 0 ]]; then
        CE_CACHE_INVALIDATIONS=$((CE_CACHE_INVALIDATIONS + cleaned))
    fi

    echo "${cleaned}"
}

# Get cache statistics
ce_cache_stats() {
    local total_entries=0
    local total_size=0

    if [[ -d "${CE_CACHE_DIR}" ]]; then
        total_entries=$(find "${CE_CACHE_DIR}" -name "*.cache" 2>/dev/null | wc -l)
        total_size=$(du -sb "${CE_CACHE_DIR}" 2>/dev/null | cut -f1)
    fi

    local hit_rate=0
    local total_requests=$((CE_CACHE_HITS + CE_CACHE_MISSES))
    if [[ ${total_requests} -gt 0 ]]; then
        hit_rate=$((CE_CACHE_HITS * 100 / total_requests))
    fi

    cat <<EOF
{
  "total_entries": ${total_entries},
  "total_size_bytes": ${total_size},
  "cache_hits": ${CE_CACHE_HITS},
  "cache_misses": ${CE_CACHE_MISSES},
  "cache_invalidations": ${CE_CACHE_INVALIDATIONS},
  "hit_rate_percent": ${hit_rate},
  "ttl_seconds": ${CE_CACHE_TTL}
}
EOF
}

# Cached git operations
ce_cache_git_branches() {
    local cache_key="git:branches"
    local cached

    if cached=$(ce_cache_get "git" "${cache_key}"); then
        echo "${cached}"
        return 0
    fi

    # Execute git command and cache result
    local result
    result=$(git branch --list 2>/dev/null || echo "")
    ce_cache_set "git" "${cache_key}" "${result}"
    echo "${result}"
}

ce_cache_git_remote_branches() {
    local cache_key="git:remote_branches"
    local cached

    if cached=$(ce_cache_get "git" "${cache_key}"); then
        echo "${cached}"
        return 0
    fi

    local result
    result=$(git branch -r 2>/dev/null || echo "")
    ce_cache_set "git" "${cache_key}" "${result}"
    echo "${result}"
}

ce_cache_git_status() {
    local cache_key="git:status"
    local cached

    if cached=$(ce_cache_get "git" "${cache_key}"); then
        echo "${cached}"
        return 0
    fi

    local result
    result=$(git status --porcelain 2>/dev/null || echo "")
    ce_cache_set "git" "${cache_key}" "${result}"
    echo "${result}"
}

ce_cache_git_current_branch() {
    local cache_key="git:current_branch"
    local cached

    if cached=$(ce_cache_get "git" "${cache_key}"); then
        echo "${cached}"
        return 0
    fi

    local result
    result=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
    ce_cache_set "git" "${cache_key}" "${result}"
    echo "${result}"
}

# Invalidate git cache on state changes
ce_cache_invalidate_on_git_change() {
    ce_cache_invalidate_category "git"
}

# Cached state operations
ce_cache_state_load() {
    local state_file="$1"
    local cache_key="state:${state_file}"
    local cached

    # Check if file has been modified since cache
    if [[ -f "${state_file}" ]]; then
        local file_mtime
        file_mtime=$(stat -c %Y "${state_file}" 2>/dev/null || stat -f %m "${state_file}" 2>/dev/null || echo 0)

        local cache_hash
        cache_hash=$(ce_cache_key_hash "${cache_key}")
        local cache_file="${CE_CACHE_DIR}/state/${cache_hash}.cache"

        if [[ -f "${cache_file}" ]]; then
            local cache_mtime
            cache_mtime=$(stat -c %Y "${cache_file}" 2>/dev/null || stat -f %m "${cache_file}" 2>/dev/null || echo 0)

            # If file is newer than cache, invalidate
            if [[ ${file_mtime} -gt ${cache_mtime} ]]; then
                ce_cache_invalidate "state" "${cache_key}"
            fi
        fi
    fi

    if cached=$(ce_cache_get "state" "${cache_key}"); then
        echo "${cached}"
        return 0
    fi

    if [[ -f "${state_file}" ]]; then
        local result
        result=$(cat "${state_file}")
        ce_cache_set "state" "${cache_key}" "${result}"
        echo "${result}"
    fi
}

# Cache warming (pre-populate frequently accessed data)
ce_cache_warm() {
    echo "Warming cache..."

    # Warm git data
    ce_cache_git_current_branch > /dev/null 2>&1 &
    ce_cache_git_branches > /dev/null 2>&1 &
    ce_cache_git_status > /dev/null 2>&1 &

    # Wait for background jobs
    wait

    echo "Cache warmed"
}

# Export functions
export -f ce_cache_init
export -f ce_cache_get
export -f ce_cache_set
export -f ce_cache_invalidate
export -f ce_cache_invalidate_category
export -f ce_cache_clear
export -f ce_cache_cleanup_expired
export -f ce_cache_stats
export -f ce_cache_git_branches
export -f ce_cache_git_status
export -f ce_cache_git_current_branch
export -f ce_cache_invalidate_on_git_change
export -f ce_cache_warm
