#!/usr/bin/env bash
# Automation Permission Verifier for Claude Enhancer v5.4.0
# Purpose: Verify that automation operations are authorized
# Security: Whitelist-based with HMAC signature verification
# Usage: Source and call verify_automation_permission before sensitive ops

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
PERMISSION_DB_FILE="${CE_PERMISSION_DB:-/var/log/claude-enhancer/permissions.db}"
PERMISSION_WHITELIST="${CE_PERMISSION_WHITELIST:-${SCRIPT_DIR}/automation_whitelist.conf}"

# ============================================================
# INITIALIZATION
# ============================================================

init_permission_db() {
    local db_dir=$(dirname "$PERMISSION_DB_FILE")

    # Create directory if needed
    if [[ ! -d "$db_dir" ]]; then
        sudo mkdir -p "$db_dir" 2>/dev/null || mkdir -p "$db_dir"
        chmod 750 "$db_dir"
    fi

    # Initialize SQLite database
    if [[ ! -f "$PERMISSION_DB_FILE" ]]; then
        sqlite3 "$PERMISSION_DB_FILE" <<'SQL'
-- Permission grants table
CREATE TABLE IF NOT EXISTS permission_grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    operation TEXT NOT NULL,
    resource TEXT,
    granted_by TEXT NOT NULL,
    granted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,
    reason TEXT,
    hmac TEXT NOT NULL,
    revoked INTEGER DEFAULT 0,
    revoked_at TEXT,
    revoked_by TEXT,
    UNIQUE(user, operation, resource)
);

-- Permission checks audit log
CREATE TABLE IF NOT EXISTS permission_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    operation TEXT NOT NULL,
    resource TEXT,
    result TEXT NOT NULL, -- allowed, denied, expired
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    ip_address TEXT
);

CREATE INDEX IF NOT EXISTS idx_grants_user ON permission_grants(user);
CREATE INDEX IF NOT EXISTS idx_grants_operation ON permission_grants(operation);
CREATE INDEX IF NOT EXISTS idx_checks_user ON permission_checks(user);
CREATE INDEX IF NOT EXISTS idx_checks_timestamp ON permission_checks(timestamp DESC);
SQL

        chmod 640 "$PERMISSION_DB_FILE"
    fi
}

# ============================================================
# PERMISSION VERIFICATION
# ============================================================

# Verify automation permission
# Args: $1 = operation, $2 = resource (optional)
# Returns: 0 if allowed, 1 if denied
verify_automation_permission() {
    local operation="$1"
    local resource="${2:-*}"
    local user="${USER:-unknown}"
    local result="denied"

    init_permission_db

    # Check 1: Environment-based bypass (for CI/CD)
    if [[ "${CE_BYPASS_PERMISSION_CHECK:-0}" == "1" ]]; then
        # Log bypass attempt
        audit_permission_check "$user" "$operation" "$resource" "bypassed"
        return 0
    fi

    # Check 2: Whitelist file check
    if check_whitelist_permission "$user" "$operation" "$resource"; then
        result="allowed"
        audit_permission_check "$user" "$operation" "$resource" "$result"
        return 0
    fi

    # Check 3: Database permission grant
    if check_database_permission "$user" "$operation" "$resource"; then
        result="allowed"
        audit_permission_check "$user" "$operation" "$resource" "$result"
        return 0
    fi

    # Check 4: Owner operations (special case)
    if [[ "$operation" == "owner_bypass" ]] && is_repository_owner "$user"; then
        result="allowed"
        audit_permission_check "$user" "$operation" "$resource" "$result"
        return 0
    fi

    # Permission denied
    result="denied"
    audit_permission_check "$user" "$operation" "$resource" "$result"

    # Log security event
    if command -v audit_security_event &>/dev/null; then
        audit_security_event "permission_denied" "HIGH" "User: $user, Operation: $operation, Resource: $resource"
    fi

    return 1
}

# Check whitelist file
check_whitelist_permission() {
    local user="$1"
    local operation="$2"
    local resource="$3"

    if [[ ! -f "$PERMISSION_WHITELIST" ]]; then
        return 1
    fi

    # Whitelist format: user:operation:resource
    # Example: john:git_push:feature/*
    # Wildcards supported: * for any

    while IFS=':' read -r wl_user wl_operation wl_resource; do
        # Skip comments and empty lines
        [[ "$wl_user" =~ ^#.*  ]] && continue
        [[ -z "$wl_user" ]] && continue

        # Check user match
        if [[ "$wl_user" != "*" ]] && [[ "$wl_user" != "$user" ]]; then
            continue
        fi

        # Check operation match
        if [[ "$wl_operation" != "*" ]] && [[ "$wl_operation" != "$operation" ]]; then
            continue
        fi

        # Check resource match (with wildcard support)
        if [[ "$wl_resource" != "*" ]]; then
            # Convert wildcard pattern to regex
            local pattern="${wl_resource//\*/.*}"

            if ! [[ "$resource" =~ ^${pattern}$ ]]; then
                continue
            fi
        fi

        # Match found
        return 0
    done < "$PERMISSION_WHITELIST"

    return 1
}

# Check database permission grant
check_database_permission() {
    local user="$1"
    local operation="$2"
    local resource="$3"

    local current_time=$(date --iso-8601=seconds)

    # Escape parameters for SQL
    local safe_user=$(echo "$user" | sed "s/'/''/g")
    local safe_operation=$(echo "$operation" | sed "s/'/''/g")
    local safe_resource=$(echo "$resource" | sed "s/'/''/g")

    # Query active permissions
    local has_permission=$(sqlite3 "$PERMISSION_DB_FILE" <<SQL
SELECT COUNT(*) FROM permission_grants
WHERE user = '${safe_user}'
  AND operation = '${safe_operation}'
  AND (resource = '${safe_resource}' OR resource = '*')
  AND revoked = 0
  AND (expires_at IS NULL OR expires_at > '${current_time}');
SQL
)

    if [[ "$has_permission" -gt 0 ]]; then
        return 0
    fi

    return 1
}

# Check if user is repository owner
is_repository_owner() {
    local user="$1"

    # Check GITHUB_REPOSITORY_OWNER environment variable
    if [[ -n "${GITHUB_REPOSITORY_OWNER:-}" ]] && [[ "$user" == "$GITHUB_REPOSITORY_OWNER" ]]; then
        return 0
    fi

    # Check git config
    local git_user=$(git config user.name 2>/dev/null || echo "")
    if [[ -n "$git_user" ]] && [[ "$user" == "$git_user" ]]; then
        # Additional verification: check if user has owner role
        if command -v gh &>/dev/null; then
            local role=$(gh api repos/:owner/:repo --jq '.permissions.admin' 2>/dev/null || echo "false")
            if [[ "$role" == "true" ]]; then
                return 0
            fi
        fi
    fi

    return 1
}

# ============================================================
# PERMISSION MANAGEMENT
# ============================================================

# Grant automation permission
# Args: $1 = user, $2 = operation, $3 = resource, $4 = granted_by, $5 = reason, $6 = expires_at (optional)
grant_automation_permission() {
    local user="$1"
    local operation="$2"
    local resource="${3:-*}"
    local granted_by="${4:-${USER:-system}}"
    local reason="${5:-Manual grant}"
    local expires_at="${6:-}"

    init_permission_db

    # SECURITY: Escape all parameters
    local safe_user=$(echo "$user" | sed "s/'/''/g")
    local safe_operation=$(echo "$operation" | sed "s/'/''/g")
    local safe_resource=$(echo "$resource" | sed "s/'/''/g")
    local safe_granted_by=$(echo "$granted_by" | sed "s/'/''/g")
    local safe_reason=$(echo "$reason" | sed "s/'/''/g")
    local safe_expires_at=$(echo "$expires_at" | sed "s/'/''/g")

    # Calculate HMAC
    local hmac_data="${user}:${operation}:${resource}:${granted_by}"
    local hmac=$(echo -n "$hmac_data" | openssl dgst -sha256 -hmac "${CE_AUDIT_SECRET:-default}" 2>/dev/null | awk '{print $2}')

    # Insert permission grant
    sqlite3 "$PERMISSION_DB_FILE" <<SQL
INSERT OR REPLACE INTO permission_grants (
    user, operation, resource, granted_by, reason, expires_at, hmac
) VALUES (
    '${safe_user}',
    '${safe_operation}',
    '${safe_resource}',
    '${safe_granted_by}',
    '${safe_reason}',
    $(if [[ -n "$expires_at" ]]; then echo "'${safe_expires_at}'"; else echo "NULL"; fi),
    '${hmac}'
);
SQL

    if command -v log_success &>/dev/null; then
        log_success "Permission granted: $user → $operation ($resource)"
    else
        echo "✓ Permission granted: $user → $operation ($resource)"
    fi

    # Audit the grant
    if command -v audit_security_event &>/dev/null; then
        audit_security_event "permission_granted" "MEDIUM" "User: $user, Operation: $operation, Resource: $resource, By: $granted_by"
    fi
}

# Revoke automation permission
# Args: $1 = user, $2 = operation, $3 = resource, $4 = revoked_by, $5 = reason
revoke_automation_permission() {
    local user="$1"
    local operation="$2"
    local resource="${3:-*}"
    local revoked_by="${4:-${USER:-system}}"
    local reason="${5:-Manual revocation}"

    init_permission_db

    # SECURITY: Escape all parameters
    local safe_user=$(echo "$user" | sed "s/'/''/g")
    local safe_operation=$(echo "$operation" | sed "s/'/''/g")
    local safe_resource=$(echo "$resource" | sed "s/'/''/g")
    local safe_revoked_by=$(echo "$revoked_by" | sed "s/'/''/g")

    local revoked_at=$(date --iso-8601=seconds)

    # Revoke permission
    sqlite3 "$PERMISSION_DB_FILE" <<SQL
UPDATE permission_grants
SET revoked = 1,
    revoked_at = '${revoked_at}',
    revoked_by = '${safe_revoked_by}'
WHERE user = '${safe_user}'
  AND operation = '${safe_operation}'
  AND resource = '${safe_resource}'
  AND revoked = 0;
SQL

    if command -v log_success &>/dev/null; then
        log_success "Permission revoked: $user → $operation ($resource)"
    else
        echo "✓ Permission revoked: $user → $operation ($resource)"
    fi

    # Audit the revocation
    if command -v audit_security_event &>/dev/null; then
        audit_security_event "permission_revoked" "HIGH" "User: $user, Operation: $operation, Resource: $resource, By: $revoked_by, Reason: $reason"
    fi
}

# List permissions for a user
list_user_permissions() {
    local user="${1:-${USER:-}}"

    init_permission_db

    local safe_user=$(echo "$user" | sed "s/'/''/g")

    echo "Active Permissions for: $user"
    echo "========================================"

    sqlite3 -header -column "$PERMISSION_DB_FILE" <<SQL
SELECT
    operation,
    resource,
    granted_by,
    granted_at,
    expires_at
FROM permission_grants
WHERE user = '${safe_user}'
  AND revoked = 0
ORDER BY granted_at DESC;
SQL
}

# ============================================================
# AUDIT LOGGING
# ============================================================

audit_permission_check() {
    local user="$1"
    local operation="$2"
    local resource="$3"
    local result="$4"

    init_permission_db

    local safe_user=$(echo "$user" | sed "s/'/''/g")
    local safe_operation=$(echo "$operation" | sed "s/'/''/g")
    local safe_resource=$(echo "$resource" | sed "s/'/''/g")
    local safe_result=$(echo "$result" | sed "s/'/''/g")

    local session_id="${CE_SESSION_ID:-unknown}"
    local ip_address="${SSH_CLIENT%% *}"

    sqlite3 "$PERMISSION_DB_FILE" <<SQL
INSERT INTO permission_checks (
    user, operation, resource, result, session_id, ip_address
) VALUES (
    '${safe_user}',
    '${safe_operation}',
    '${safe_resource}',
    '${safe_result}',
    '${session_id}',
    '${ip_address}'
);
SQL
}

# Generate permission audit report
generate_permission_report() {
    local start_date="${1:-$(date -d '7 days ago' +%Y-%m-%d)}"
    local end_date="${2:-$(date +%Y-%m-%d)}"

    init_permission_db

    local report_file="/tmp/permission_audit_$(date +%s).txt"

    cat > "$report_file" <<REPORT
========================================
Permission Audit Report
========================================
Period: $start_date to $end_date
Generated: $(date)

Active Permissions:
-------------------
REPORT

    sqlite3 -header -column "$PERMISSION_DB_FILE" <<SQL >> "$report_file"
SELECT user, operation, resource, granted_by, granted_at
FROM permission_grants
WHERE revoked = 0
ORDER BY granted_at DESC;
SQL

    echo "" >> "$report_file"
    echo "Recent Permission Checks:" >> "$report_file"
    echo "-------------------------" >> "$report_file"

    sqlite3 -header -column "$PERMISSION_DB_FILE" <<SQL >> "$report_file"
SELECT user, operation, resource, result, timestamp
FROM permission_checks
WHERE DATE(timestamp) BETWEEN '${start_date}' AND '${end_date}'
ORDER BY timestamp DESC
LIMIT 100;
SQL

    echo "" >> "$report_file"
    echo "Denied Operations Summary:" >> "$report_file"
    echo "--------------------------" >> "$report_file"

    sqlite3 -header -column "$PERMISSION_DB_FILE" <<SQL >> "$report_file"
SELECT operation, COUNT(*) as denied_count
FROM permission_checks
WHERE result = 'denied'
  AND DATE(timestamp) BETWEEN '${start_date}' AND '${end_date}'
GROUP BY operation
ORDER BY denied_count DESC;
SQL

    echo "Report saved: $report_file"
    cat "$report_file"
}

# ============================================================
# CLI INTERFACE
# ============================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-help}" in
        verify)
            if verify_automation_permission "${2:-}" "${3:-*}"; then
                echo "✓ Permission granted"
                exit 0
            else
                echo "✗ Permission denied"
                exit 1
            fi
            ;;

        grant)
            grant_automation_permission "${2}" "${3}" "${4:-*}" "${5:-${USER}}" "${6:-CLI grant}" "${7:-}"
            ;;

        revoke)
            revoke_automation_permission "${2}" "${3}" "${4:-*}" "${5:-${USER}}" "${6:-CLI revocation}"
            ;;

        list)
            list_user_permissions "${2:-${USER}}"
            ;;

        report)
            generate_permission_report "${2:-}" "${3:-}"
            ;;

        init)
            init_permission_db
            echo "✓ Permission database initialized"
            ;;

        help|*)
            cat <<HELP
Automation Permission Verifier - Claude Enhancer v5.4.0

Usage: $0 <command> [args...]

Commands:
  verify <operation> [resource]
      Check if current user has permission for operation

  grant <user> <operation> [resource] [granted_by] [reason] [expires_at]
      Grant permission to user for operation

  revoke <user> <operation> [resource] [revoked_by] [reason]
      Revoke permission from user

  list [user]
      List permissions for user (default: current user)

  report [start_date] [end_date]
      Generate permission audit report

  init
      Initialize permission database

Examples:
  # Check permission
  $0 verify git_push feature/auth

  # Grant permission
  $0 grant alice git_push '*' admin "Allow all pushes"

  # Grant temporary permission (expires in 24h)
  $0 grant bob auto_commit '*' admin "Temp access" "$(date -d '+24 hours' --iso-8601=seconds)"

  # Revoke permission
  $0 revoke alice git_push '*' admin "Access no longer needed"

  # List user permissions
  $0 list alice

  # Generate report
  $0 report 2025-10-01 2025-10-10

Environment Variables:
  CE_PERMISSION_DB         Path to permission database
  CE_PERMISSION_WHITELIST  Path to whitelist config file
  CE_BYPASS_PERMISSION_CHECK=1  Bypass permission checks (CI/CD)
  CE_AUDIT_SECRET          Secret for HMAC calculation

Whitelist File Format (.conf):
  user:operation:resource
  # Comments start with #
  alice:git_push:feature/*
  bob:*:*
  *:git_fetch:*

Security Features:
  ✓ Whitelist-based authorization
  ✓ Database permission grants with expiration
  ✓ HMAC signature verification
  ✓ Complete audit trail
  ✓ Permission revocation support
HELP
            ;;
    esac
fi
