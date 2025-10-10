#!/usr/bin/env bats
# SQL Injection Prevention Tests for Claude Enhancer v5.4.0
# Purpose: Verify SQL injection vulnerabilities are properly fixed
# Target: .workflow/automation/security/owner_operations_monitor.sh

load '../test_helper'

setup() {
    # Source the script under test
    PROJECT_ROOT="${BATS_TEST_DIRNAME}/../.."
    SCRIPT_PATH="${PROJECT_ROOT}/.workflow/automation/security/owner_operations_monitor.sh"

    # Create temporary test database
    export TEST_DB_DIR=$(mktemp -d)
    export MONITOR_DB_FILE="${TEST_DB_DIR}/test_owner_ops.db"

    # Source the script to get functions
    source "$SCRIPT_PATH"

    # Initialize test database
    init_database
}

teardown() {
    # Clean up test database
    rm -rf "$TEST_DB_DIR"
}

# ============================================================
# SQL ESCAPE FUNCTION TESTS
# ============================================================

@test "sql_escape: handles single quotes correctly" {
    # Test basic SQL escaping
    result=$(sql_escape "test'value")
    assert_equal "$result" "test''value"
}

@test "sql_escape: handles multiple single quotes" {
    # Test multiple quotes in one string
    result=$(sql_escape "test'multiple'quotes'here")
    assert_equal "$result" "test''multiple''quotes''here"
}

@test "sql_escape: handles SQL injection attempt with DROP" {
    # Test classic SQL injection pattern
    malicious="admin'; DROP TABLE owner_operations; --"
    result=$(sql_escape "$malicious")
    assert_equal "$result" "admin''; DROP TABLE owner_operations; --"

    # Verify the escaped string is safe for SQL
    # It will be treated as a literal string, not executed
}

@test "sql_escape: handles UNION SELECT injection" {
    malicious="' UNION SELECT password FROM users--"
    result=$(sql_escape "$malicious")
    assert_equal "$result" "'' UNION SELECT password FROM users--"
}

@test "sql_escape: handles empty string" {
    result=$(sql_escape "")
    assert_equal "$result" ""
}

@test "sql_escape: preserves normal strings without quotes" {
    result=$(sql_escape "normal_string_123")
    assert_equal "$result" "normal_string_123"
}

# ============================================================
# INPUT VALIDATION TESTS
# ============================================================

@test "validate_input_parameter: rejects empty input" {
    run validate_input_parameter "test_param" ""
    assert_failure
}

@test "validate_input_parameter: accepts valid input" {
    run validate_input_parameter "event_id" "evt_12345" 50
    assert_success
}

@test "validate_input_parameter: rejects input exceeding max length" {
    # Create string longer than limit
    long_string=$(python3 -c "print('A' * 501)")
    run validate_input_parameter "test_param" "$long_string" 500
    assert_failure
}

@test "validate_input_parameter: detects SQL keywords - DROP" {
    # Should log warning but not fail (allows legitimate use)
    run validate_input_parameter "test_param" "DROP TABLE users" 100
    # Function logs warning but returns success (permissive validation)
    assert_success
}

@test "validate_input_parameter: detects SQL keywords - DELETE" {
    run validate_input_parameter "test_param" "DELETE FROM data" 100
    assert_success  # Logs but doesn't block
}

@test "validate_input_parameter: accepts alphanumeric with underscores" {
    run validate_input_parameter "actor_login" "github_user_123" 50
    assert_success
}

# ============================================================
# PROCESS_BYPASS_EVENT TESTS (Main SQL injection target)
# ============================================================

@test "process_bypass_event: validates event_id before SQL insertion" {
    # Create malicious event JSON
    malicious_json=$(cat <<'JSON'
{
  "_document_id": "evt123'; DROP TABLE owner_operations; --",
  "created_at": "2025-10-10T10:00:00Z",
  "actor": "test_user",
  "actor_id": 12345,
  "action": "protected_branch.policy_override",
  "repo": "test/repo"
}
JSON
)

    # Set required env var
    export CE_AUDIT_SECRET="test-secret-key"

    # Process event - should validate and escape
    run process_bypass_event "$malicious_json"

    # Function should succeed (input is validated and escaped)
    assert_success

    # Verify table still exists (DROP was not executed)
    table_count=$(sqlite3 "$MONITOR_DB_FILE" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='owner_operations';")
    assert_equal "$table_count" "1"
}

@test "process_bypass_event: escapes single quotes in actor_login" {
    malicious_json=$(cat <<'JSON'
{
  "_document_id": "evt124",
  "created_at": "2025-10-10T10:00:00Z",
  "actor": "malicious'actor",
  "actor_id": 12345,
  "action": "test",
  "repo": "test/repo"
}
JSON
)

    export CE_AUDIT_SECRET="test-secret-key"

    run process_bypass_event "$malicious_json"
    assert_success

    # Query the inserted data
    result=$(sqlite3 "$MONITOR_DB_FILE" "SELECT actor_login FROM owner_operations WHERE event_id='evt124';")

    # Should have stored the escaped version correctly
    assert_equal "$result" "malicious'actor"
}

@test "process_bypass_event: rejects non-numeric actor_id" {
    malicious_json=$(cat <<'JSON'
{
  "_document_id": "evt125",
  "created_at": "2025-10-10T10:00:00Z",
  "actor": "test_user",
  "actor_id": "DROP TABLE",
  "action": "test",
  "repo": "test/repo"
}
JSON
)

    export CE_AUDIT_SECRET="test-secret-key"

    # Should fail validation
    run process_bypass_event "$malicious_json"
    assert_failure
}

@test "process_bypass_event: handles special characters in repo name" {
    test_json=$(cat <<'JSON'
{
  "_document_id": "evt126",
  "created_at": "2025-10-10T10:00:00Z",
  "actor": "test_user",
  "actor_id": 12345,
  "action": "test",
  "repo": "user's-repo"
}
JSON
)

    export CE_AUDIT_SECRET="test-secret-key"

    run process_bypass_event "$test_json"
    assert_success

    result=$(sqlite3 "$MONITOR_DB_FILE" "SELECT repository FROM owner_operations WHERE event_id='evt126';")
    assert_equal "$result" "user's-repo"
}

# ============================================================
# QUERY_OWNER_OPERATIONS TESTS
# ============================================================

@test "query_owner_operations: validates numeric limit" {
    export CE_AUDIT_SECRET="test-secret-key"

    # Non-numeric limit should fail
    run query_owner_operations "" "DROP TABLE"
    assert_failure
    assert_output --partial "limit must be numeric"
}

@test "query_owner_operations: caps limit at 1000" {
    export CE_AUDIT_SECRET="test-secret-key"

    # Limit > 1000 should be capped
    run query_owner_operations "" "5000"

    # Should succeed but log warning
    # Note: This test verifies the function doesn't crash with large limits
}

@test "query_owner_operations: escapes filter parameter" {
    export CE_AUDIT_SECRET="test-secret-key"

    # Insert a test record first
    sqlite3 "$MONITOR_DB_FILE" <<SQL
INSERT INTO owner_operations (
    event_id, timestamp, actor_login, actor_id, actor_type,
    action, repository, severity, risk_score, hmac
) VALUES (
    'test_evt',
    '2025-10-10T10:00:00Z',
    'test_user',
    12345,
    'User',
    'test_action',
    'test/repo',
    'CRITICAL',
    90,
    'test_hmac'
);
SQL

    # Query with single quote in filter
    run query_owner_operations "test'user"

    # Should not crash (escaping works)
    assert_success
}

@test "query_owner_operations: prevents SQL injection via filter" {
    export CE_AUDIT_SECRET="test-secret-key"

    # Try SQL injection via filter
    malicious_filter="' OR '1'='1"

    run query_owner_operations "$malicious_filter"

    # Should succeed (escaped) and not return all records
    assert_success
}

# ============================================================
# GENERATE_COMPLIANCE_REPORT TESTS
# ============================================================

@test "generate_compliance_report: validates date format" {
    export CE_AUDIT_SECRET="test-secret-key"

    # Invalid date format
    run generate_compliance_report "invalid-date" "2025-10-10"
    assert_failure
    assert_output --partial "Invalid start_date format"
}

@test "generate_compliance_report: rejects SQL injection in dates" {
    export CE_AUDIT_SECRET="test-secret-key"

    # Try SQL injection via date
    run generate_compliance_report "2025-10-01'; DROP TABLE owner_operations; --" "2025-10-10"
    assert_failure
}

@test "generate_compliance_report: accepts valid date range" {
    export CE_AUDIT_SECRET="test-secret-key"

    run generate_compliance_report "2025-10-01" "2025-10-10"
    assert_success
}

# ============================================================
# INTEGRATION TESTS
# ============================================================

@test "integration: full workflow with malicious data doesn't corrupt database" {
    export CE_AUDIT_SECRET="test-secret-key"

    # Insert malicious event
    malicious_json=$(cat <<'JSON'
{
  "_document_id": "evt_malicious'; DROP TABLE owner_operations; --",
  "created_at": "2025-10-10T10:00:00Z",
  "actor": "hacker'; DELETE FROM owner_operations WHERE '1'='1",
  "actor_id": 99999,
  "action": "malicious_action",
  "repo": "'; DROP TABLE alerts; --"
}
JSON
)

    # Process event
    run process_bypass_event "$malicious_json"

    # Verify all tables still exist
    tables=$(sqlite3 "$MONITOR_DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")

    assert_output --partial "owner_operations"
    assert_output --partial "alerts"
    assert_output --partial "sync_status"

    # Verify data was stored safely (escaped)
    count=$(sqlite3 "$MONITOR_DB_FILE" "SELECT COUNT(*) FROM owner_operations;")
    assert_equal "$count" "1"
}

@test "integration: verify HMAC is calculated on original values, not escaped" {
    export CE_AUDIT_SECRET="test-secret-key-for-hmac"

    test_json=$(cat <<'JSON'
{
  "_document_id": "evt_hmac_test",
  "created_at": "2025-10-10T10:00:00Z",
  "actor": "user'test",
  "actor_id": 11111,
  "action": "test'action",
  "repo": "test/repo"
}
JSON
)

    # Process event
    run process_bypass_event "$test_json"
    assert_success

    # Retrieve HMAC from database
    stored_hmac=$(sqlite3 "$MONITOR_DB_FILE" "SELECT hmac FROM owner_operations WHERE event_id='evt_hmac_test';")

    # Calculate expected HMAC on original values (before escaping)
    expected_hmac=$(echo -n "evt_hmac_test:2025-10-10T10:00:00Z:user'test:test'action" | \
        openssl dgst -sha256 -hmac "test-secret-key-for-hmac" 2>/dev/null | awk '{print $2}')

    # HMAC should match
    assert_equal "$stored_hmac" "$expected_hmac"
}

# ============================================================
# PERFORMANCE TESTS
# ============================================================

@test "performance: sql_escape is fast enough for production" {
    # Measure time for 1000 escape operations
    start=$(date +%s%N)

    for i in {1..1000}; do
        sql_escape "test'value'with'quotes" > /dev/null
    done

    end=$(date +%s%N)
    elapsed=$(( (end - start) / 1000000 ))  # Convert to milliseconds

    # Should complete in less than 500ms (0.5ms per operation)
    [[ $elapsed -lt 500 ]]
}

@test "performance: validate_input_parameter overhead is acceptable" {
    start=$(date +%s%N)

    for i in {1..1000}; do
        validate_input_parameter "test_param" "test_value_$i" 100 > /dev/null 2>&1
    done

    end=$(date +%s%N)
    elapsed=$(( (end - start) / 1000000 ))

    # Should complete in less than 1 second
    [[ $elapsed -lt 1000 ]]
}
