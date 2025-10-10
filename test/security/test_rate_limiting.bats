#!/usr/bin/env bats
# Rate Limiting Tests for Claude Enhancer v5.4.0
# Target: .workflow/automation/utils/rate_limiter.sh

load '../test_helper'

setup() {
    PROJECT_ROOT="${BATS_TEST_DIRNAME}/../.."
    RATE_LIMITER="${PROJECT_ROOT}/.workflow/automation/utils/rate_limiter.sh"

    # Create temp rate limit dir
    export CE_RATE_LIMIT_DIR=$(mktemp -d)

    # Source rate limiter
    source "$RATE_LIMITER"
}

teardown() {
    rm -rf "$CE_RATE_LIMIT_DIR"
}

@test "rate_limiter.sh exists and is sourceable" {
    [[ -f "$RATE_LIMITER" ]]
    source "$RATE_LIMITER"
}

@test "check_rate_limit: allows first operation" {
    run check_rate_limit "test_op" 10 60
    assert_success
}

@test "check_rate_limit: blocks after limit exceeded" {
    # Consume all tokens
    for i in {1..10}; do
        check_rate_limit "test_rapid" 10 60
    done

    # Next should be blocked
    run check_rate_limit "test_rapid" 10 60
    assert_failure
}

@test "check_rate_limit: refills tokens over time" {
    # Consume all tokens
    for i in {1..5}; do
        check_rate_limit "test_refill" 5 10
    done

    # Should be blocked
    run check_rate_limit "test_refill" 5 10
    assert_failure

    # Wait for refill (11 seconds for 1 token at 5 tokens/10s rate)
    sleep 3

    # Should now be allowed
    run check_rate_limit "test_refill" 5 10
    assert_success
}

@test "get_rate_limit_status: returns available tokens" {
    # Consume 3 tokens
    for i in {1..3}; do
        check_rate_limit "test_status" 10 60
    done

    # Should have 7 tokens left
    status=$(get_rate_limit_status "test_status")
    assert_equal "$status" "7"
}

@test "reset_rate_limit: clears bucket" {
    # Consume all tokens
    for i in {1..10}; do
        check_rate_limit "test_reset" 10 60
    done

    # Reset
    run reset_rate_limit "test_reset"
    assert_success

    # Should be allowed again
    run check_rate_limit "test_reset" 10 60
    assert_success
}

@test "check_git_rate_limit: uses correct defaults" {
    run check_git_rate_limit "commit"
    assert_success
}

@test "check_api_rate_limit: uses correct defaults" {
    run check_api_rate_limit "github"
    assert_success
}

@test "check_automation_rate_limit: enforces limits" {
    # Default is 10 ops / 60s
    for i in {1..10}; do
        check_automation_rate_limit "test_auto"
    done

    run check_automation_rate_limit "test_auto"
    assert_failure
}

@test "wait_for_rate_limit: blocks until allowed" {
    # Consume all tokens
    for i in {1..5}; do
        check_rate_limit "test_wait" 5 5
    done

    # Wait should succeed after refill (max 3 attempts, 1 second apart)
    run timeout 10 wait_for_rate_limit "test_wait" 3
    assert_success
}

@test "cleanup_rate_limits: removes old files" {
    # Create old bucket file
    old_bucket="${CE_RATE_LIMIT_DIR}/old_op.bucket"
    echo "10:1000000000" > "$old_bucket"
    touch -d "2 days ago" "$old_bucket"

    run cleanup_rate_limits
    assert_success

    # Old file should be removed
    [[ ! -f "$old_bucket" ]]
}

@test "enable_dev_mode: sets relaxed limits" {
    enable_dev_mode

    assert_equal "$CE_GIT_MAX_OPS" "50"
    assert_equal "$CE_API_MAX_OPS" "100"
}

@test "enable_prod_mode: sets strict limits" {
    enable_prod_mode

    assert_equal "$CE_GIT_MAX_OPS" "10"
    assert_equal "$CE_API_MAX_OPS" "30"
}

@test "concurrent access: file locking prevents race conditions" {
    # Simulate concurrent access
    for i in {1..5}; do
        (check_rate_limit "test_concurrent" 10 60) &
    done
    wait

    # All should succeed without corruption
    status=$(get_rate_limit_status "test_concurrent")
    assert_equal "$status" "5"
}

@test "log_rate_limit_exceeded: logs properly" {
    export CE_RATE_LIMIT_WAIT=5

    run log_rate_limit_exceeded "test_operation"
    assert_output --partial "Rate limit exceeded"
    assert_output --partial "test_operation"
}
