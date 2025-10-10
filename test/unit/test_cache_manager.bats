#!/usr/bin/env bats
# test_cache_manager.bats - Unit tests for cache_manager.sh library
# Tests caching operations, TTL, invalidation, and performance

load '../helpers/test_helper'
load '../helpers/mock_helper'

setup() {
    setup_test_env
    source_lib "cache_manager"
    ce_cache_init
}

teardown() {
    teardown_test_env
    mock_reset_all
}

# ============================================================================
# Cache Initialization
# ============================================================================

@test "ce_cache_init: creates cache directory structure" {
    ce_cache_init
    assert_dir_exists "${CE_CACHE_DIR}/git"
    assert_dir_exists "${CE_CACHE_DIR}/state"
    assert_dir_exists "${CE_CACHE_DIR}/validation"
    assert_dir_exists "${CE_CACHE_DIR}/gates"
}

@test "ce_cache_init: creates metadata file" {
    ce_cache_init
    assert_file_exists "${CE_CACHE_DIR}/.metadata"
}

@test "ce_cache_init: skips when CE_NO_CACHE set" {
    export CE_NO_CACHE=true
    run ce_cache_init
    assert_success
}

# ============================================================================
# Cache Get/Set Operations
# ============================================================================

@test "ce_cache_set: stores value in cache" {
    run ce_cache_set "git" "test-key" "test-value"
    assert_success
}

@test "ce_cache_get: retrieves cached value" {
    ce_cache_set "git" "test-key" "test-value"
    run ce_cache_get "git" "test-key"
    assert_success
    assert_output_equals "test-value"
}

@test "ce_cache_get: returns error for missing key" {
    run ce_cache_get "git" "nonexistent-key"
    assert_failure
}

@test "ce_cache_get: returns error when cache disabled" {
    export CE_NO_CACHE=true
    run ce_cache_get "git" "test-key"
    assert_failure
}

# ============================================================================
# Cache Invalidation
# ============================================================================

@test "ce_cache_invalidate: removes specific cache entry" {
    ce_cache_set "git" "test-key" "test-value"
    run ce_cache_invalidate "git" "test-key"
    assert_success

    run ce_cache_get "git" "test-key"
    assert_failure
}

@test "ce_cache_invalidate_category: removes all entries in category" {
    ce_cache_set "git" "key1" "value1"
    ce_cache_set "git" "key2" "value2"

    run ce_cache_invalidate_category "git"
    assert_success

    run ce_cache_get "git" "key1"
    assert_failure
}

@test "ce_cache_clear: removes all cache entries" {
    ce_cache_set "git" "key1" "value1"
    ce_cache_set "state" "key2" "value2"

    run ce_cache_clear
    assert_success
    assert_output_contains "Cleared"
}

# ============================================================================
# Cache TTL and Expiration
# ============================================================================

@test "ce_cache_is_valid: returns true for fresh cache" {
    ce_cache_set "git" "test-key" "test-value"
    local cache_hash=$(ce_cache_key_hash "test-key")
    local cache_file="${CE_CACHE_DIR}/git/${cache_hash}.cache"

    run ce_cache_is_valid "${cache_file}"
    assert_success
}

@test "ce_cache_cleanup_expired: removes expired entries" {
    # Set very short TTL
    export CE_CACHE_TTL=1

    ce_cache_set "git" "test-key" "test-value"
    sleep 2

    run ce_cache_cleanup_expired
    assert_success
    [[ "${output}" -gt 0 ]]
}

# ============================================================================
# Cache Statistics
# ============================================================================

@test "ce_cache_stats: returns cache statistics" {
    ce_cache_set "git" "key1" "value1"
    ce_cache_get "git" "key1"

    run ce_cache_stats
    assert_success
    assert_output_contains "cache_hits"
    assert_output_contains "cache_misses"
}

# ============================================================================
# Cached Git Operations
# ============================================================================

@test "ce_cache_git_current_branch: caches git branch" {
    git checkout -b test-branch --quiet

    run ce_cache_git_current_branch
    assert_success
    assert_output_equals "test-branch"
}

@test "ce_cache_git_branches: caches branch list" {
    run ce_cache_git_branches
    assert_success
}

@test "ce_cache_git_status: caches git status" {
    run ce_cache_git_status
    assert_success
}

# Add more tests for remaining cache_manager functions...
