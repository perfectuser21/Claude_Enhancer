#!/usr/bin/env bash
# Owner Operations Monitor for Claude Enhancer v5.4.0
# Purpose: Monitor GitHub Audit Log API for Owner bypass operations
# Security: Immutable append-only SQLite storage with HMAC integrity
# Sync Interval: 15 minutes (configurable)
# Security Update: SQL injection prevention with proper escaping

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"
# shellcheck source=./audit_log.sh
source "${SCRIPT_DIR}/audit_log.sh"
# shellcheck source=../utils/rate_limiter.sh
source "${SCRIPT_DIR}/../utils/rate_limiter.sh"

# Configuration
MONITOR_DB_DIR="/var/log/claude-enhancer/owner_ops"
MONITOR_DB_FILE="${MONITOR_DB_DIR}/owner_operations.db"
SYNC_INTERVAL=900  # 15 minutes in seconds
ALERT_WEBHOOK="${CE_ALERT_WEBHOOK:-}"
GITHUB_ORG="${GITHUB_REPOSITORY_OWNER:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# ============================================================
# SECURITY: SQL INJECTION PREVENTION
# ============================================================

# Escape single quotes for SQL strings (防止SQL注入)
# Usage: escaped=$(sql_escape "$untrusted_input")
sql_escape() {
    local input="$1"
    # Replace ' with '' (SQL standard escaping)
    echo "${input//\'/\'\'}"
}

# Validate input parameters (输入验证)
# Returns 0 if valid, 1 if invalid
validate_input_parameter() {
    local param_name="$1"
    local param_value="$2"
    local max_length="${3:-500}"

    # Check for null/empty
    if [[ -z "$param_value" ]]; then
        log_error "Security: Parameter '$param_name' is empty"
        return 1
    fi

    # Check length
    if [[ ${#param_value} -gt $max_length ]]; then
        log_error "Security: Parameter '$param_name' exceeds maximum length ($max_length)"
        return 1
    fi

    # Check for dangerous SQL keywords in untrusted input
    if echo "$param_value" | grep -iE "(DROP|DELETE|INSERT|UPDATE|ALTER|UNION|EXEC|SCRIPT)" >/dev/null 2>&1; then
        log_warning "Security: Parameter '$param_name' contains suspicious SQL keywords"
        # Continue but log for audit
        audit_security_event "suspicious_input" "MEDIUM" "Parameter: $param_name, Value length: ${#param_value}"
    fi

    return 0
}

# Ensure monitoring database directory exists
ensure_monitor_directory() {
    if [[ ! -d "$MONITOR_DB_DIR" ]]; then
        sudo mkdir -p "$MONITOR_DB_DIR" 2>/dev/null || mkdir -p "$MONITOR_DB_DIR"
        chmod 750 "$MONITOR_DB_DIR"
    fi
}

# Initialize SQLite database with immutable schema
init_database() {
    ensure_monitor_directory
    
    if [[ ! -f "$MONITOR_DB_FILE" ]]; then
        log_info "Initializing owner operations database..."
        
        sqlite3 "$MONITOR_DB_FILE" <<'SQL'
-- Owner operations tracking table (append-only)
CREATE TABLE IF NOT EXISTS owner_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    timestamp TEXT NOT NULL,
    actor_login TEXT NOT NULL,
    actor_id INTEGER NOT NULL,
    actor_type TEXT NOT NULL,
    
    action TEXT NOT NULL,
    repository TEXT NOT NULL,
    branch TEXT,
    
    bypass_reason TEXT,
    bypassed_rules TEXT,  -- JSON array
    
    commit_sha TEXT,
    commit_message TEXT,
    
    ip_address TEXT,
    user_agent TEXT,
    geo_location TEXT,  -- JSON object
    
    severity TEXT NOT NULL DEFAULT 'CRITICAL',
    risk_score INTEGER NOT NULL DEFAULT 90,
    
    alerted_at TEXT,
    alert_status TEXT DEFAULT 'pending',
    
    metadata TEXT,  -- JSON object
    hmac TEXT NOT NULL,
    
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent updates (immutability trigger will enforce)
    CHECK (created_at IS NOT NULL)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_owner_ops_timestamp ON owner_operations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_owner_ops_actor ON owner_operations(actor_login);
CREATE INDEX IF NOT EXISTS idx_owner_ops_alert_status ON owner_operations(alert_status);
CREATE INDEX IF NOT EXISTS idx_owner_ops_repository ON owner_operations(repository);

-- Sync status tracking
CREATE TABLE IF NOT EXISTS sync_status (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_sync_at TEXT NOT NULL,
    last_event_id TEXT,
    events_synced INTEGER NOT NULL DEFAULT 0,
    errors_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Initialize sync status
INSERT OR IGNORE INTO sync_status (id, last_sync_at) 
VALUES (1, datetime('now', '-1 hour'));

-- Trigger to enforce immutability (prevent UPDATE/DELETE)
CREATE TRIGGER IF NOT EXISTS prevent_owner_ops_update
BEFORE UPDATE ON owner_operations
BEGIN
    SELECT RAISE(FAIL, 'owner_operations table is append-only - updates not allowed');
END;

CREATE TRIGGER IF NOT EXISTS prevent_owner_ops_delete
BEFORE DELETE ON owner_operations
BEGIN
    SELECT RAISE(FAIL, 'owner_operations table is append-only - deletes not allowed');
END;

-- Alert log table
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_operation_id INTEGER NOT NULL REFERENCES owner_operations(id),
    alert_type TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    sent_at TEXT,
    response TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
SQL
        
        log_success "Database initialized: $MONITOR_DB_FILE"
    fi
}

# Calculate HMAC for database entry
calculate_entry_hmac() {
    local event_id="$1"
    local timestamp="$2"
    local actor="$3"
    local action="$4"
    
    if [[ -z "${CE_AUDIT_SECRET:-}" ]]; then
        log_error "CE_AUDIT_SECRET not set - cannot calculate HMAC"
        return 1
    fi
    
    local data="${event_id}:${timestamp}:${actor}:${action}"
    echo -n "$data" | openssl dgst -sha256 -hmac "$CE_AUDIT_SECRET" 2>/dev/null | awk '{print $2}'
}

# Fetch GitHub Audit Log events
fetch_github_audit_events() {
    local since_timestamp="$1"
    
    if [[ -z "$GITHUB_TOKEN" ]]; then
        log_error "GITHUB_TOKEN not set - cannot fetch audit events"
        return 1
    fi
    
    if [[ -z "$GITHUB_ORG" ]]; then
        log_error "GITHUB_REPOSITORY_OWNER not set - cannot fetch audit events"
        return 1
    fi
    
    log_info "Fetching GitHub audit events since $since_timestamp"
    
    # Fetch audit log events from GitHub API
    local response
    response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/orgs/${GITHUB_ORG}/audit-log?phrase=action:protected_branch.policy_override created:>=${since_timestamp}&per_page=100" \
        2>/dev/null || echo "{}")
    
    echo "$response"
}

# Parse and store owner bypass events
process_bypass_event() {
    local event_json="$1"

    # Extract fields using jq (untrusted input from GitHub API)
    local event_id=$(echo "$event_json" | jq -r '._document_id // .event_id // empty')
    local timestamp=$(echo "$event_json" | jq -r '.created_at // .timestamp // empty')
    local actor_login=$(echo "$event_json" | jq -r '.actor // .user // empty')
    local actor_id=$(echo "$event_json" | jq -r '.actor_id // 0')
    local action=$(echo "$event_json" | jq -r '.action // empty')
    local repo=$(echo "$event_json" | jq -r '.repo // .repository // empty')
    local branch=$(echo "$event_json" | jq -r '.data.branch_name // .branch // empty')
    local commit_sha=$(echo "$event_json" | jq -r '.data.commit_sha // empty')
    local ip_address=$(echo "$event_json" | jq -r '.actor_ip // empty')

    # Validate required fields
    if [[ -z "$event_id" || -z "$timestamp" || -z "$actor_login" ]]; then
        log_warning "Incomplete event data - skipping"
        return 1
    fi

    # SECURITY: Validate all inputs before SQL insertion
    validate_input_parameter "event_id" "$event_id" 100 || return 1
    validate_input_parameter "timestamp" "$timestamp" 50 || return 1
    validate_input_parameter "actor_login" "$actor_login" 100 || return 1
    validate_input_parameter "action" "$action" 100 || return 1
    validate_input_parameter "repo" "$repo" 200 || return 1

    # Validate actor_id is numeric
    if ! [[ "$actor_id" =~ ^[0-9]+$ ]]; then
        log_error "Security: actor_id is not numeric: $actor_id"
        return 1
    fi

    # SECURITY: SQL escape all string values (防止SQL注入)
    local safe_event_id=$(sql_escape "$event_id")
    local safe_timestamp=$(sql_escape "$timestamp")
    local safe_actor_login=$(sql_escape "$actor_login")
    local safe_action=$(sql_escape "$action")
    local safe_repo=$(sql_escape "$repo")
    local safe_branch=$(sql_escape "$branch")
    local safe_commit_sha=$(sql_escape "$commit_sha")
    local safe_ip_address=$(sql_escape "$ip_address")

    # Calculate HMAC with original (non-escaped) values
    local hmac=$(calculate_entry_hmac "$event_id" "$timestamp" "$actor_login" "$action")
    local safe_hmac=$(sql_escape "$hmac")

    # Escape JSON metadata
    local safe_metadata=$(sql_escape "$(echo "$event_json" | jq -c .)")

    # Calculate risk score
    local risk_score=90  # Default high risk for owner bypass

    # Insert into database with escaped values
    sqlite3 "$MONITOR_DB_FILE" <<SQL
INSERT OR IGNORE INTO owner_operations (
    event_id, timestamp, actor_login, actor_id, actor_type,
    action, repository, branch,
    bypass_reason, bypassed_rules,
    commit_sha, ip_address,
    severity, risk_score, hmac, metadata
) VALUES (
    '${safe_event_id}',
    '${safe_timestamp}',
    '${safe_actor_login}',
    ${actor_id},
    'User',
    '${safe_action}',
    '${safe_repo}',
    $(if [[ -n "$branch" ]]; then echo "'${safe_branch}'"; else echo "NULL"; fi),
    'Emergency override detected',
    '["protected_branch.policy_override"]',
    $(if [[ -n "$commit_sha" ]]; then echo "'${safe_commit_sha}'"; else echo "NULL"; fi),
    $(if [[ -n "$ip_address" ]]; then echo "'${safe_ip_address}'"; else echo "NULL"; fi),
    'CRITICAL',
    ${risk_score},
    '${safe_hmac}',
    '${safe_metadata}'
);
SQL

    local insert_result=$?

    if [[ $insert_result -eq 0 ]]; then
        log_success "Stored owner bypass event: $event_id"

        # Trigger alert
        trigger_alert "$safe_event_id"

        # Log to audit system
        audit_owner_operation "bypass_protection" "${safe_repo}/${safe_branch}" "detected" "GitHub Audit Log sync"

        return 0
    else
        log_debug "Event already exists or insert failed: $event_id"
        return 1
    fi
}

# Trigger real-time alert
trigger_alert() {
    local event_id="$1"

    # SECURITY: Validate and escape event_id
    validate_input_parameter "event_id" "$event_id" 100 || return 1
    local safe_event_id=$(sql_escape "$event_id")

    # Get event details from database
    local event_data
    event_data=$(sqlite3 "$MONITOR_DB_FILE" <<SQL
SELECT
    actor_login,
    action,
    repository,
    branch,
    timestamp,
    risk_score,
    commit_sha
FROM owner_operations
WHERE event_id = '${safe_event_id}';
SQL
)
    
    if [[ -z "$event_data" ]]; then
        log_warning "Event not found for alerting: $event_id"
        return 1
    fi
    
    IFS='|' read -r actor action repo branch timestamp risk_score commit_sha <<< "$event_data"
    
    # Build alert message
    local alert_message
    alert_message=$(cat <<ALERT
🚨 **CRITICAL Security Alert: Owner Bypass Detected**

**Actor**: ${actor} (Repository Owner)
**Repository**: ${repo}
**Branch**: ${branch:-unknown}
**Action**: ${action}
**Timestamp**: ${timestamp}
**Risk Score**: ${risk_score}/100
**Commit**: ${commit_sha:-N/A}

**Bypassed Rules**: Branch protection policies
**Reason**: Emergency override detected via GitHub Audit Log

**Actions Required**:
1. Review the operation legitimacy
2. Verify commit changes if applicable
3. Approve or escalate in dashboard

**Event ID**: ${event_id}

*This alert was triggered by Owner Operations Monitor*
*Sync Interval: 15 minutes*
ALERT
)
    
    log_warning "$alert_message"
    
    # Send to Slack/webhook if configured
    if [[ -n "$ALERT_WEBHOOK" ]]; then
        send_webhook_alert "$alert_message" "$event_id"
    fi
    
    # Send email if configured
    if command -v mail &>/dev/null && [[ -n "${CE_ADMIN_EMAIL:-}" ]]; then
        echo "$alert_message" | mail -s "[CRITICAL] Owner Bypass Detected: $actor" "$CE_ADMIN_EMAIL"
    fi
    
    # Update alert status in database
    local alert_time=$(date --iso-8601=seconds)
    local safe_alert_time=$(sql_escape "$alert_time")

    sqlite3 "$MONITOR_DB_FILE" <<SQL
UPDATE owner_operations
SET alerted_at = '${safe_alert_time}', alert_status = 'sent'
WHERE event_id = '${safe_event_id}';

INSERT INTO alerts (owner_operation_id, alert_type, channel, status, sent_at)
SELECT id, 'owner_bypass', 'webhook,email', 'sent', '${safe_alert_time}'
FROM owner_operations WHERE event_id = '${safe_event_id}';
SQL
    
    log_success "Alert triggered for event: $event_id"
}

# Send webhook alert
send_webhook_alert() {
    local message="$1"
    local event_id="$2"
    
    if [[ -z "$ALERT_WEBHOOK" ]]; then
        return 0
    fi
    
    local payload
    payload=$(jq -n \
        --arg msg "$message" \
        --arg event "$event_id" \
        --arg severity "critical" \
        '{
            text: $msg,
            event_id: $event,
            severity: $severity,
            alert_type: "owner_bypass",
            timestamp: (now | todate)
        }')
    
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        >/dev/null 2>&1 || log_error "Failed to send webhook alert"
}

# Sync GitHub Audit Log
sync_github_audit_log() {
    # SECURITY: Rate limit sync operations (max 5 per 5 minutes)
    if ! check_owner_ops_rate_limit; then
        log_rate_limit_exceeded "owner_operations_sync"
        return 1
    fi

    init_database

    # Get last sync timestamp
    local last_sync
    last_sync=$(sqlite3 "$MONITOR_DB_FILE" "SELECT last_sync_at FROM sync_status WHERE id = 1;")

    log_info "Last sync: $last_sync"
    
    # Fetch events since last sync
    local events_json
    events_json=$(fetch_github_audit_events "$last_sync")
    
    # Parse and process each event
    local events_count=0
    local new_events=0
    
    # Check if response is valid JSON array
    if echo "$events_json" | jq -e 'type == "array"' >/dev/null 2>&1; then
        events_count=$(echo "$events_json" | jq 'length')
        log_info "Found $events_count audit events"
        
        # Process each event
        for i in $(seq 0 $((events_count - 1))); do
            local event
            event=$(echo "$events_json" | jq ".[$i]")
            
            if process_bypass_event "$event"; then
                new_events=$((new_events + 1))
            fi
        done
    else
        log_warning "No events returned or invalid JSON response"
    fi
    
    # Update sync status
    local current_time=$(date --iso-8601=seconds)
    sqlite3 "$MONITOR_DB_FILE" <<SQL
UPDATE sync_status SET 
    last_sync_at = '$current_time',
    events_synced = events_synced + $new_events,
    updated_at = '$current_time'
WHERE id = 1;
SQL
    
    log_success "Sync complete: processed $events_count events, $new_events new"
}

# Query owner operations
query_owner_operations() {
    local filter="${1:-}"
    local limit="${2:-50}"

    # SECURITY: Rate limit queries to prevent abuse
    if ! check_owner_ops_rate_limit; then
        log_rate_limit_exceeded "owner_operations_query"
        return 1
    fi

    init_database

    log_info "Querying owner operations (limit: $limit)..."

    # SECURITY: Validate limit is numeric
    if ! [[ "$limit" =~ ^[0-9]+$ ]]; then
        log_error "Security: limit must be numeric"
        return 1
    fi

    # Cap limit at 1000 to prevent resource exhaustion
    if [[ "$limit" -gt 1000 ]]; then
        log_warning "Security: limit capped at 1000 (requested: $limit)"
        limit=1000
    fi

    local query="SELECT
        event_id,
        timestamp,
        actor_login,
        action,
        repository,
        branch,
        alert_status,
        risk_score
    FROM owner_operations"

    if [[ -n "$filter" ]]; then
        # SECURITY: Validate and escape filter parameter
        validate_input_parameter "filter" "$filter" 100 || return 1
        local safe_filter=$(sql_escape "$filter")

        query="$query WHERE actor_login LIKE '%${safe_filter}%' OR repository LIKE '%${safe_filter}%'"
    fi

    query="$query ORDER BY timestamp DESC LIMIT ${limit};"

    sqlite3 -header -column "$MONITOR_DB_FILE" "$query"
}

# Verify database integrity
verify_database_integrity() {
    init_database
    
    log_info "Verifying database integrity..."
    
    local total_records
    total_records=$(sqlite3 "$MONITOR_DB_FILE" "SELECT COUNT(*) FROM owner_operations;")
    
    log_info "Total records: $total_records"
    
    local valid=0
    local invalid=0
    
    # Verify HMAC for each record
    while IFS='|' read -r event_id timestamp actor action hmac; do
        local calculated_hmac
        calculated_hmac=$(calculate_entry_hmac "$event_id" "$timestamp" "$actor" "$action")
        
        if [[ "$hmac" == "$calculated_hmac" ]]; then
            valid=$((valid + 1))
        else
            invalid=$((invalid + 1))
            log_error "Invalid HMAC for event: $event_id"
        fi
    done < <(sqlite3 "$MONITOR_DB_FILE" "SELECT event_id, timestamp, actor_login, action, hmac FROM owner_operations;")
    
    log_info "Verification complete:"
    log_info "  Valid:   $valid"
    log_info "  Invalid: $invalid"
    
    [[ $invalid -eq 0 ]]
}

# Generate compliance report
generate_compliance_report() {
    local start_date="${1:-$(date -d '30 days ago' +%Y-%m-%d)}"
    local end_date="${2:-$(date +%Y-%m-%d)}"

    init_database

    # SECURITY: Validate date format (YYYY-MM-DD)
    if ! [[ "$start_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        log_error "Security: Invalid start_date format (expected: YYYY-MM-DD)"
        return 1
    fi

    if ! [[ "$end_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        log_error "Security: Invalid end_date format (expected: YYYY-MM-DD)"
        return 1
    fi

    # SECURITY: Escape dates (even though validated, defense in depth)
    local safe_start_date=$(sql_escape "$start_date")
    local safe_end_date=$(sql_escape "$end_date")

    log_info "Generating compliance report: $start_date to $end_date"

    local report_file="/tmp/owner_ops_compliance_report_$(date +%s).txt"

    cat > "$report_file" <<REPORT
========================================
Owner Operations Compliance Report
========================================
Period: $start_date to $end_date
Generated: $(date)

Summary Statistics:
-------------------
REPORT

    sqlite3 "$MONITOR_DB_FILE" <<SQL >> "$report_file"
SELECT
    'Total Owner Bypass Operations: ' || COUNT(*)
FROM owner_operations
WHERE DATE(timestamp) BETWEEN '${safe_start_date}' AND '${safe_end_date}';

SELECT
    'Critical Severity Events: ' || COUNT(*)
FROM owner_operations
WHERE severity = 'CRITICAL' AND DATE(timestamp) BETWEEN '${safe_start_date}' AND '${safe_end_date}';

SELECT
    'Average Risk Score: ' || AVG(risk_score)
FROM owner_operations
WHERE DATE(timestamp) BETWEEN '${safe_start_date}' AND '${safe_end_date}';

SELECT '';
SELECT 'By Actor:';
SELECT '----------';
SELECT actor_login || ': ' || COUNT(*) || ' operations'
FROM owner_operations
WHERE DATE(timestamp) BETWEEN '${safe_start_date}' AND '${safe_end_date}'
GROUP BY actor_login
ORDER BY COUNT(*) DESC;

SELECT '';
SELECT 'By Repository:';
SELECT '--------------';
SELECT repository || ': ' || COUNT(*) || ' operations'
FROM owner_operations
WHERE DATE(timestamp) BETWEEN '${safe_start_date}' AND '${safe_end_date}'
GROUP BY repository
ORDER BY COUNT(*) DESC;
SQL

    echo "" >> "$report_file"
    echo "Detailed Events:" >> "$report_file"
    echo "----------------" >> "$report_file"

    sqlite3 -header -column "$MONITOR_DB_FILE" <<SQL >> "$report_file"
SELECT
    timestamp,
    actor_login,
    repository,
    branch,
    action,
    alert_status
FROM owner_operations
WHERE DATE(timestamp) BETWEEN '${safe_start_date}' AND '${safe_end_date}'
ORDER BY timestamp DESC;
SQL

    log_success "Report generated: $report_file"
    cat "$report_file"
}

# Main execution
main() {
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        sync)
            sync_github_audit_log
            ;;
        query)
            query_owner_operations "$@"
            ;;
        verify)
            verify_database_integrity
            ;;
        report)
            generate_compliance_report "$@"
            ;;
        init)
            init_database
            ;;
        help|*)
            cat <<HELP
Owner Operations Monitor - Claude Enhancer v5.4.0

Usage: $0 <command> [options]

Commands:
  sync              Sync GitHub Audit Log (run every 15 minutes)
  query [filter]    Query owner operations (optional filter)
  verify            Verify database integrity (HMAC checks)
  report [start] [end]  Generate compliance report
  init              Initialize database

Environment Variables:
  CE_AUDIT_SECRET         HMAC secret (required)
  GITHUB_TOKEN            GitHub API token (required for sync)
  GITHUB_REPOSITORY_OWNER Organization name (required for sync)
  CE_ALERT_WEBHOOK        Webhook URL for alerts (optional)
  CE_ADMIN_EMAIL          Admin email for alerts (optional)

Examples:
  $0 sync
  $0 query john-doe
  $0 verify
  $0 report 2025-09-01 2025-10-10

Database: $MONITOR_DB_FILE
HELP
            ;;
    esac
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
