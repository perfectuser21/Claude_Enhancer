#!/usr/bin/env bats
# Permission Verification Tests for Claude Enhancer v5.4.0
# Target: .workflow/automation/security/automation_permission_verifier.sh

load '../test_helper'

setup() {
    PROJECT_ROOT="${BATS_TEST_DIRNAME}/../.."
    VERIFIER="${PROJECT_ROOT}/.workflow/automation/security/automation_permission_verifier.sh"
    WHITELIST="${PROJECT_ROOT}/.workflow/automation/security/automation_whitelist.conf"

    # Create temp permission DB
    export TEST_PERM_DB=$(mktemp)
    export CE_PERMISSION_DB="$TEST_PERM_DB"

    # Create temp whitelist
    export TEST_WHITELIST=$(mktemp)
    export CE_PERMISSION_WHITELIST="$TEST_WHITELIST"

    # Source verifier
    source "$VERIFIER"

    # Initialize DB
    init_permission_db
}

teardown() {
    rm -f "$TEST_PERM_DB" "$TEST_WHITELIST"
}

@test "automation_permission_verifier.sh exists" {
    [[ -f "$VERIFIER" ]]
}

@test "init_permission_db: creates tables" {
    # Check tables exist
    tables=$(sqlite3 "$CE_PERMISSION_DB" "SELECT name FROM sqlite_master WHERE type='table';")

    assert_output --partial "permission_grants"
    assert_output --partial "permission_checks"
}

@test "verify_automation_permission: allows bypass mode" {
    export CE_BYPASS_PERMISSION_CHECK=1

    run verify_automation_permission "any_operation" "any_resource"
    assert_success
}

@test "verify_automation_permission: denies without whitelist" {
    # No whitelist entry, no database grant
    run verify_automation_permission "restricted_op" "resource"
    assert_failure
}

@test "check_whitelist_permission: matches exact user:operation:resource" {
    echo "alice:git_push:feature/test" > "$TEST_WHITELIST"

    export USER=alice
    run check_whitelist_permission "alice" "git_push" "feature/test"
    assert_success
}

@test "check_whitelist_permission: matches wildcards" {
    echo "*:git_status:*" > "$TEST_WHITELIST"

    run check_whitelist_permission "anyone" "git_status" "anything"
    assert_success
}

@test "check_whitelist_permission: matches operation wildcard" {
    echo "bob:*:feature/*" > "$TEST_WHITELIST"

    run check_whitelist_permission "bob" "any_op" "feature/branch"
    assert_success
}

@test "check_whitelist_permission: matches resource pattern" {
    echo "user:auto_commit:feature/*" > "$TEST_WHITELIST"

    run check_whitelist_permission "user" "auto_commit" "feature/auth"
    assert_success
}

@test "check_whitelist_permission: rejects mismatched user" {
    echo "alice:git_push:*" > "$TEST_WHITELIST"

    run check_whitelist_permission "bob" "git_push" "main"
    assert_failure
}

@test "grant_automation_permission: adds to database" {
    export CE_AUDIT_SECRET="test-secret"

    run grant_automation_permission "alice" "git_push" "*" "admin" "Test grant"
    assert_success

    # Verify in DB
    count=$(sqlite3 "$CE_PERMISSION_DB" "SELECT COUNT(*) FROM permission_grants WHERE user='alice';")
    assert_equal "$count" "1"
}

@test "check_database_permission: finds active grant" {
    export CE_AUDIT_SECRET="test-secret"

    # Grant permission
    grant_automation_permission "bob" "auto_commit" "feature/*" "admin" "Test"

    # Check
    run check_database_permission "bob" "auto_commit" "feature/test"
    assert_success
}

@test "check_database_permission: ignores revoked grants" {
    export CE_AUDIT_SECRET="test-secret"

    # Grant then revoke
    grant_automation_permission "charlie" "auto_push" "*" "admin" "Test"
    revoke_automation_permission "charlie" "auto_push" "*" "admin" "Revoked"

    # Should fail
    run check_database_permission "charlie" "auto_push" "main"
    assert_failure
}

@test "check_database_permission: respects expiration" {
    export CE_AUDIT_SECRET="test-secret"

    # Grant with past expiration
    expires_at=$(date -d '1 day ago' --iso-8601=seconds 2>/dev/null || date -v-1d +%Y-%m-%dT%H:%M:%S)

    sqlite3 "$CE_PERMISSION_DB" <<SQL
INSERT INTO permission_grants (user, operation, resource, granted_by, expires_at, hmac)
VALUES ('expired_user', 'test_op', '*', 'admin', '$expires_at', 'test_hmac');
SQL

    # Should fail (expired)
    run check_database_permission "expired_user" "test_op" "*"
    assert_failure
}

@test "audit_permission_check: logs all checks" {
    export CE_AUDIT_SECRET="test-secret"

    audit_permission_check "test_user" "test_op" "test_resource" "denied"

    # Verify audit log
    count=$(sqlite3 "$CE_PERMISSION_DB" "SELECT COUNT(*) FROM permission_checks WHERE user='test_user';")
    assert_equal "$count" "1"
}

@test "list_user_permissions: shows user grants" {
    export CE_AUDIT_SECRET="test-secret"

    grant_automation_permission "dave" "git_push" "*" "admin" "Test"

    run list_user_permissions "dave"
    assert_output --partial "git_push"
}

@test "generate_permission_report: creates report" {
    export CE_AUDIT_SECRET="test-secret"

    grant_automation_permission "eve" "auto_commit" "*" "admin" "Test"
    audit_permission_check "eve" "auto_commit" "*" "allowed"

    run generate_permission_report "2025-10-01" "2025-10-31"
    assert_success
    assert_output --partial "Permission Audit Report"
}

@test "whitelist config: real config has safe defaults" {
    real_whitelist="${PROJECT_ROOT}/.workflow/automation/security/automation_whitelist.conf"

    if [[ -f "$real_whitelist" ]]; then
        # Check for dangerous wildcards
        run grep -E "^\*:\*:\*$" "$real_whitelist"
        assert_failure  # Should NOT have full wildcard (security risk)

        # Check has safe operations
        run grep "git_status" "$real_whitelist"
        assert_success  # Should allow read-only ops
    fi
}

@test "integration: complete permission workflow" {
    export CE_AUDIT_SECRET="test-secret"

    # 1. No permission initially
    run verify_automation_permission "sensitive_op" "main"
    assert_failure

    # 2. Grant permission
    grant_automation_permission "$USER" "sensitive_op" "main" "admin" "Test"

    # 3. Now allowed
    run verify_automation_permission "sensitive_op" "main"
    assert_success

    # 4. Revoke permission
    revoke_automation_permission "$USER" "sensitive_op" "main" "admin" "End test"

    # 5. Denied again
    run verify_automation_permission "sensitive_op" "main"
    assert_failure
}
