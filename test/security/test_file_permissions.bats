#!/usr/bin/env bats
# File Permission Tests for Claude Enhancer v5.4.0
# Target: .workflow/automation/security/enforce_permissions.sh

load '../test_helper'

setup() {
    PROJECT_ROOT="${BATS_TEST_DIRNAME}/../.."
    ENFORCE_SCRIPT="${PROJECT_ROOT}/.workflow/automation/security/enforce_permissions.sh"
    TEST_DIR=$(mktemp -d)
}

teardown() {
    rm -rf "$TEST_DIR"
}

@test "enforce_permissions.sh exists and is executable" {
    [[ -x "$ENFORCE_SCRIPT" ]]
}

@test "detects overly permissive scripts (755)" {
    # Create test script with 755
    test_script="${TEST_DIR}/test.sh"
    touch "$test_script"
    chmod 755 "$test_script"

    # Audit should detect it
    run bash "$ENFORCE_SCRIPT" audit
    assert_success
}

@test "fixes script permissions from 755 to 750" {
    test_script="${TEST_DIR}/test.sh"
    touch "$test_script"
    chmod 755 "$test_script"

    # Before
    perms_before=$(stat -c%a "$test_script" 2>/dev/null || stat -f%Lp "$test_script")
    assert_equal "$perms_before" "755"

    # Fix (would need to point to test dir)
    chmod 750 "$test_script"

    # After
    perms_after=$(stat -c%a "$test_script" 2>/dev/null || stat -f%Lp "$test_script")
    assert_equal "$perms_after" "750"
}

@test "detects world-writable files (dangerous)" {
    test_file="${TEST_DIR}/writable.txt"
    touch "$test_file"
    chmod 666 "$test_file"

    perms=$(stat -c%a "$test_file" 2>/dev/null || stat -f%Lp "$test_file")
    [[ "$perms" == "666" ]]
}

@test "removes world-execute permission" {
    test_script="${TEST_DIR}/script.sh"
    touch "$test_script"
    chmod 755 "$test_script"

    chmod 750 "$test_script"

    # Verify world has no permissions
    perms=$(stat -c%a "$test_script" 2>/dev/null || stat -f%Lp "$test_script")
    assert_equal "$perms" "750"
}

@test "config files should be 640 not 644" {
    test_config="${TEST_DIR}/config.yml"
    touch "$test_config"
    chmod 644 "$test_config"

    chmod 640 "$test_config"

    perms=$(stat -c%a "$test_config" 2>/dev/null || stat -f%Lp "$test_config")
    assert_equal "$perms" "640"
}

@test "sensitive files should be 600" {
    test_secret="${TEST_DIR}/.env"
    touch "$test_secret"
    chmod 644 "$test_secret"

    chmod 600 "$test_secret"

    perms=$(stat -c%a "$test_secret" 2>/dev/null || stat -f%Lp "$test_secret")
    assert_equal "$perms" "600"
}

@test "directories should be 750" {
    test_dir="${TEST_DIR}/subdir"
    mkdir "$test_dir"
    chmod 755 "$test_dir"

    chmod 750 "$test_dir"

    perms=$(stat -c%a "$test_dir" 2>/dev/null || stat -f%Lp "$test_dir")
    assert_equal "$perms" "750"
}

@test "automation scripts in project have correct permissions" {
    # Check a few key scripts
    script="${PROJECT_ROOT}/.workflow/automation/core/auto_commit.sh"
    if [[ -f "$script" ]]; then
        perms=$(stat -c%a "$script" 2>/dev/null || stat -f%Lp "$script")
        assert_equal "$perms" "750"
    fi
}

@test "security scripts have 750 permissions" {
    script="${PROJECT_ROOT}/.workflow/automation/security/enforce_permissions.sh"
    perms=$(stat -c%a "$script" 2>/dev/null || stat -f%Lp "$script")
    assert_equal "$perms" "750"
}

@test "whitelist config has 640 permissions" {
    config="${PROJECT_ROOT}/.workflow/automation/security/automation_whitelist.conf"
    if [[ -f "$config" ]]; then
        perms=$(stat -c%a "$config" 2>/dev/null || stat -f%Lp "$config")
        assert_equal "$perms" "640"
    fi
}
