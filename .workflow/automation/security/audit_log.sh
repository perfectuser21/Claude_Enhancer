#!/usr/bin/env bash
# Security Audit Log for Claude Enhancer v5.4.0
# Purpose: Structured security audit logging with immutability
# Used by: All automation scripts, security audits

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"

# Configuration
AUDIT_LOG_DIR="/var/log/claude-enhancer"
AUDIT_LOG_FILE="${AUDIT_LOG_DIR}/audit.log"
AUDIT_DB_FILE="${AUDIT_LOG_DIR}/audit.db"
RETENTION_DAYS=90

# Ensure audit directory exists with restricted permissions
ensure_audit_directory() {
    if [[ ! -d "$AUDIT_LOG_DIR" ]]; then
        sudo mkdir -p "$AUDIT_LOG_DIR" 2>/dev/null || mkdir -p "$AUDIT_LOG_DIR"
        chmod 750 "$AUDIT_LOG_DIR"
    fi
}

# Generate audit entry ID (timestamp + random)
generate_audit_id() {
    echo "$(date +%s)-$(openssl rand -hex 4 2>/dev/null || echo $RANDOM)"
}

# Calculate HMAC for audit entry
calculate_hmac() {
    local data="$1"

    # Require CE_AUDIT_SECRET to be set - no insecure defaults
    if [[ -z "${CE_AUDIT_SECRET:-}" ]]; then
        log_error "CE_AUDIT_SECRET environment variable must be set"
        log_error "Generate one with: openssl rand -hex 32"
        return 1
    fi

    echo -n "$data" | openssl dgst -sha256 -hmac "$CE_AUDIT_SECRET" 2>/dev/null | awk '{print $2}'
}

# Write audit log entry
audit_log() {
    local event_type="$1"
    local action="$2"
    local resource="$3"
    local result="$4"
    local details="${5:-}"

    ensure_audit_directory

    # Generate entry
    local audit_id=$(generate_audit_id)
    local timestamp=$(date --iso-8601=seconds)
    local user="${USER:-unknown}"
    local session_id="${CE_SESSION_ID:-unknown}"
    local ip_address="${SSH_CLIENT%% *}"
    [[ -z "$ip_address" ]] && ip_address="127.0.0.1"

    # Build JSON entry
    local json_entry=$(cat <<EOF
{
  "audit_id": "$audit_id",
  "timestamp": "$timestamp",
  "event_type": "$event_type",
  "action": "$action",
  "resource": "$resource",
  "result": "$result",
  "user": "$user",
  "session_id": "$session_id",
  "ip_address": "$ip_address",
  "details": "$details",
  "pid": $$,
  "ppid": $PPID
}
EOF
)

    # Calculate HMAC
    local hmac=$(calculate_hmac "$json_entry")
    local signed_entry="${json_entry:0:-1}, \"hmac\": \"$hmac\"}"

    # Append to log file (atomic operation)
    echo "$signed_entry" >> "$AUDIT_LOG_FILE"

    # Log to syslog if available
    if command -v logger &>/dev/null; then
        logger -t "claude-enhancer" -p auth.info "$event_type: $action on $resource -> $result"
    fi

    log_debug "Audit logged: $audit_id"
}

# Audit specific events

audit_git_operation() {
    local operation="$1"
    local target="$2"
    local result="$3"
    local details="${4:-}"

    audit_log "GIT_OPERATION" "$operation" "$target" "$result" "$details"
}

audit_automation() {
    local script="$1"
    local result="$2"
    local details="${3:-}"

    audit_log "AUTOMATION" "execute_script" "$script" "$result" "$details"
}

audit_permission_check() {
    local operation="$1"
    local resource="$2"
    local result="$3"

    audit_log "PERMISSION_CHECK" "$operation" "$resource" "$result" ""
}

audit_owner_operation() {
    local operation="$1"
    local resource="$2"
    local result="$3"
    local details="${4:-}"

    # Owner operations are critical - always log
    audit_log "OWNER_OPERATION" "$operation" "$resource" "$result" "$details"

    # Also send alert
    if command -v mail &>/dev/null && [[ -n "${CE_ADMIN_EMAIL:-}" ]]; then
        echo "Owner operation detected: $operation on $resource -> $result" | \
            mail -s "[ALERT] Claude Enhancer Owner Operation" "$CE_ADMIN_EMAIL"
    fi
}

audit_security_event() {
    local event="$1"
    local severity="$2"
    local details="$3"

    audit_log "SECURITY_EVENT" "$event" "system" "$severity" "$details"
}

# Query audit logs

query_audit_logs() {
    local filter="${1:-}"
    local limit="${2:-100}"

    if [[ ! -f "$AUDIT_LOG_FILE" ]]; then
        log_warning "No audit log found"
        return 0
    fi

    if [[ -n "$filter" ]]; then
        grep "$filter" "$AUDIT_LOG_FILE" | tail -n "$limit"
    else
        tail -n "$limit" "$AUDIT_LOG_FILE"
    fi
}

# Verify audit log integrity

verify_audit_integrity() {
    local entries_checked=0
    local entries_valid=0
    local entries_invalid=0

    if [[ ! -f "$AUDIT_LOG_FILE" ]]; then
        log_warning "No audit log to verify"
        return 0
    fi

    log_info "Verifying audit log integrity..."

    while IFS= read -r entry; do
        entries_checked=$((entries_checked + 1))

        # Extract HMAC
        local stored_hmac=$(echo "$entry" | grep -o '"hmac": "[^"]*"' | cut -d'"' -f4)

        # Remove HMAC from entry
        local entry_without_hmac="${entry%, \"hmac\": \"$stored_hmac\"}"

        # Recalculate HMAC
        local calculated_hmac=$(calculate_hmac "$entry_without_hmac")

        if [[ "$stored_hmac" == "$calculated_hmac" ]]; then
            entries_valid=$((entries_valid + 1))
        else
            entries_invalid=$((entries_invalid + 1))
            local audit_id=$(echo "$entry" | grep -o '"audit_id": "[^"]*"' | cut -d'"' -f4)
            log_error "Invalid HMAC for entry: $audit_id"
        fi
    done < "$AUDIT_LOG_FILE"

    log_info "Audit verification complete:"
    log_info "  Checked: $entries_checked"
    log_info "  Valid:   $entries_valid"
    log_info "  Invalid: $entries_invalid"

    [[ $entries_invalid -eq 0 ]]
}

# Cleanup old audit logs

cleanup_old_logs() {
    if [[ ! -f "$AUDIT_LOG_FILE" ]]; then
        return 0
    fi

    log_info "Cleaning up audit logs older than $RETENTION_DAYS days..."

    local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%s 2>/dev/null || \
                        date -v-"${RETENTION_DAYS}d" +%s 2>/dev/null)

    local temp_file="${AUDIT_LOG_FILE}.tmp"
    : > "$temp_file"

    local kept=0
    local removed=0

    while IFS= read -r entry; do
        local timestamp=$(echo "$entry" | grep -o '"timestamp": "[^"]*"' | cut -d'"' -f4)
        local entry_date=$(date -d "$timestamp" +%s 2>/dev/null || \
                          date -j -f "%Y-%m-%dT%H:%M:%S%z" "$timestamp" +%s 2>/dev/null)

        if [[ $entry_date -ge $cutoff_date ]]; then
            echo "$entry" >> "$temp_file"
            kept=$((kept + 1))
        else
            removed=$((removed + 1))
        fi
    done < "$AUDIT_LOG_FILE"

    mv "$temp_file" "$AUDIT_LOG_FILE"

    log_info "Cleanup complete: kept $kept entries, removed $removed entries"
}

# Main execution
main() {
    local action="${1:-help}"
    shift || true

    case "$action" in
        log)
            if [[ $# -lt 4 ]]; then
                die "Usage: $0 log <event_type> <action> <resource> <result> [details]"
            fi
            audit_log "$@"
            ;;
        query)
            query_audit_logs "$@"
            ;;
        verify)
            verify_audit_integrity
            ;;
        cleanup)
            cleanup_old_logs
            ;;
        *)
            echo "Usage: $0 {log|query|verify|cleanup}"
            echo ""
            echo "Actions:"
            echo "  log <event_type> <action> <resource> <result> [details]"
            echo "  query [filter] [limit]"
            echo "  verify"
            echo "  cleanup"
            echo ""
            echo "Examples:"
            echo "  $0 log GIT_OPERATION commit file.txt success 'Added feature'"
            echo "  $0 query OWNER_OPERATION 50"
            echo "  $0 verify"
            echo "  $0 cleanup"
            exit 1
            ;;
    esac
}

# Export functions for use in other scripts
export -f audit_log audit_git_operation audit_automation
export -f audit_permission_check audit_owner_operation audit_security_event

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
