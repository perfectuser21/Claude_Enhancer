#!/usr/bin/env bash
# Automated Rollback Trigger System for Claude Enhancer v5.4.0
# Purpose: Monitor health and automatically trigger rollbacks
# Used by: Continuous monitoring, alert system integration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils/common.sh"
source "${SCRIPT_DIR}/rollback_decision.sh"

# Configuration
AUTO_ROLLBACK_ENABLED="${CE_AUTO_ROLLBACK_ENABLED:-true}"
MONITORING_INTERVAL="${CE_MONITORING_INTERVAL:-30}"  # seconds
ALERT_COOLDOWN="${CE_ALERT_COOLDOWN:-300}"  # 5 minutes between alerts
STATE_DIR="${CE_AUTO_ROLLBACK_STATE:-.workflow/automation/rollback/auto_state}"
ALERT_LOG="${CE_ALERT_LOG:-.workflow/automation/rollback/alerts.log}"

# Ensure directories
ensure_directory "$STATE_DIR"
ensure_directory "$(dirname "$ALERT_LOG")"

# State files
LAST_ALERT_FILE="${STATE_DIR}/last_alert"
ROLLBACK_HISTORY="${STATE_DIR}/rollback_history.jsonl"
METRICS_CACHE="${STATE_DIR}/metrics_cache.json"

# ============================================================================
# HEALTH MONITORING
# ============================================================================

monitor_health_checks() {
    log_info "Monitoring health checks..."

    local health_script="observability/probes/healthcheck.sh"

    if [[ ! -f "$health_script" ]]; then
        log_warning "Health check script not found: $health_script"
        return 0
    fi

    # Run all health checks
    local health_result
    health_result=$(bash "$health_script" all json 2>/dev/null || echo '{"overall_result":3}')

    local overall_result
    overall_result=$(echo "$health_result" | jq -r '.overall_result // 3')

    # 0=OK, 1=WARN, 2=CRITICAL, 3=UNKNOWN
    case "$overall_result" in
        0)
            log_success "Health checks: PASSED"
            return 0
            ;;
        1)
            log_warning "Health checks: DEGRADED"
            trigger_alert "health_check_degraded" "Health checks showing warnings"
            return 1
            ;;
        2|3)
            log_error "Health checks: CRITICAL"
            trigger_rollback_evaluation "health_check_failure" "$health_result"
            return 2
            ;;
        *)
            log_error "Health checks: UNKNOWN STATUS"
            return 3
            ;;
    esac
}

# ============================================================================
# SLO MONITORING
# ============================================================================

monitor_slo_violations() {
    log_info "Monitoring SLO violations..."

    local slo_file="observability/slo/slo.yml"

    if [[ ! -f "$slo_file" ]]; then
        log_debug "SLO file not found, skipping"
        return 0
    fi

    # Check if yq is available
    if ! command -v yq &>/dev/null; then
        log_debug "yq not available, skipping SLO checks"
        return 0
    fi

    # Read SLO targets
    local slos
    slos=$(yq eval '.slos[] | .name' "$slo_file" 2>/dev/null || echo "")

    if [[ -z "$slos" ]]; then
        log_debug "No SLOs defined"
        return 0
    fi

    local violations=0

    while IFS= read -r slo_name; do
        if check_slo_violation "$slo_name"; then
            ((violations++))
            log_error "SLO violation detected: $slo_name"
        fi
    done <<< "$slos"

    if [[ $violations -gt 0 ]]; then
        trigger_rollback_evaluation "slo_violation" "violations=$violations"
        return 1
    fi

    log_success "All SLOs within target"
    return 0
}

check_slo_violation() {
    local slo_name="$1"

    # This is a simplified check - in production, integrate with actual metrics
    # For now, check if error budget file exists and shows violations

    local error_budget_file="observability/slo/${slo_name}_error_budget.json"

    if [[ ! -f "$error_budget_file" ]]; then
        return 0  # No data means no violation
    fi

    local budget_remaining
    budget_remaining=$(jq -r '.budget_remaining_percent // 100' "$error_budget_file" 2>/dev/null || echo "100")

    if [[ $budget_remaining -lt 10 ]]; then
        return 1  # Violation detected
    fi

    return 0
}

# ============================================================================
# ERROR RATE MONITORING
# ============================================================================

monitor_error_rate() {
    log_info "Monitoring error rate..."

    local log_file=".workflow/logs/automation.log"

    if [[ ! -f "$log_file" ]]; then
        log_debug "Log file not found, skipping error rate check"
        return 0
    fi

    # Count errors in last 15 minutes
    local cutoff_time
    cutoff_time=$(date -d '15 minutes ago' '+%Y-%m-%d %H:%M:%S' 2>/dev/null || \
                  date -v -15M '+%Y-%m-%d %H:%M:%S' 2>/dev/null || \
                  date '+%Y-%m-%d %H:%M:%S')

    local error_count
    error_count=$(grep -E '\[ERROR\]|\[CRITICAL\]' "$log_file" 2>/dev/null | \
                  awk -v cutoff="$cutoff_time" '$0 > cutoff' | \
                  wc -l || echo "0")

    local total_count
    total_count=$(awk -v cutoff="$cutoff_time" '$0 > cutoff' "$log_file" 2>/dev/null | \
                  wc -l || echo "1")

    local error_rate
    error_rate=$(( (error_count * 100) / total_count ))

    log_info "Error rate: ${error_rate}% (${error_count}/${total_count})"

    if [[ $error_rate -ge 50 ]]; then
        log_error "CRITICAL: Error rate at ${error_rate}%"
        trigger_rollback_evaluation "error_spike" "error_rate=${error_rate}%"
        return 2
    elif [[ $error_rate -ge 25 ]]; then
        log_warning "WARNING: Elevated error rate at ${error_rate}%"
        trigger_alert "error_rate_high" "Error rate at ${error_rate}%"
        return 1
    fi

    log_success "Error rate normal: ${error_rate}%"
    return 0
}

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

monitor_performance() {
    log_info "Monitoring performance metrics..."

    # Check system load
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',' || echo "0")

    local cpu_cores
    cpu_cores=$(nproc 2>/dev/null || echo "1")

    local load_threshold=$((cpu_cores * 3))

    if (( $(echo "$load_avg > $load_threshold" | bc -l 2>/dev/null || echo "0") )); then
        log_warning "High system load: $load_avg (threshold: $load_threshold)"
        trigger_alert "high_load" "System load at $load_avg"
        return 1
    fi

    # Check disk I/O wait
    if command -v iostat &>/dev/null; then
        local io_wait
        io_wait=$(iostat -c 1 2 2>/dev/null | tail -1 | awk '{print $4}' || echo "0")

        if (( $(echo "$io_wait > 50" | bc -l 2>/dev/null || echo "0") )); then
            log_warning "High I/O wait: ${io_wait}%"
            trigger_alert "high_io_wait" "I/O wait at ${io_wait}%"
            return 1
        fi
    fi

    log_success "Performance metrics normal"
    return 0
}

# ============================================================================
# ROLLBACK EVALUATION & EXECUTION
# ============================================================================

trigger_rollback_evaluation() {
    local failure_type="$1"
    local failure_data="${2:-}"

    log_warning "Triggering rollback evaluation for: $failure_type"

    # Check if auto-rollback is enabled
    if [[ "$AUTO_ROLLBACK_ENABLED" != "true" ]]; then
        log_warning "Auto-rollback is disabled, sending alert only"
        trigger_alert "rollback_candidate" "$failure_type: $failure_data"
        return 0
    fi

    # Generate decision
    local decision
    decision=$(bash "${SCRIPT_DIR}/rollback_decision.sh" analyze "$failure_type" "$failure_data")

    local recommendation
    recommendation=$(echo "$decision" | jq -r '.decision_summary.recommendation')

    log_info "Rollback recommendation: $recommendation"

    # Save decision to history
    echo "$decision" >> "$ROLLBACK_HISTORY"

    case "$recommendation" in
        IMMEDIATE_ROLLBACK)
            log_error "IMMEDIATE ROLLBACK RECOMMENDED"
            execute_automatic_rollback "$decision" "$failure_type"
            ;;

        SCHEDULED_ROLLBACK)
            log_warning "SCHEDULED ROLLBACK RECOMMENDED"
            schedule_rollback "$decision" "$failure_type"
            ;;

        MONITOR_ONLY)
            log_info "MONITOR ONLY - No rollback needed"
            trigger_alert "monitor_only" "$failure_type: Monitoring recommended"
            ;;

        NO_ACTION)
            log_info "NO ACTION NEEDED"
            ;;

        *)
            log_warning "Unknown recommendation: $recommendation"
            ;;
    esac
}

execute_automatic_rollback() {
    local decision="$1"
    local failure_type="$2"

    log_error "=================================="
    log_error "  EXECUTING AUTOMATIC ROLLBACK"
    log_error "=================================="

    # Extract rollback details
    local target_version
    target_version=$(echo "$decision" | jq -r '.deployment_info.target_version')

    local strategy
    strategy=$(echo "$decision" | jq -r '.rollback_recommendation.rollback_strategy')

    local reason="Automatic rollback triggered by: $failure_type"

    # Send critical alert
    send_critical_alert "AUTOMATIC_ROLLBACK_INITIATED" "$reason"

    # Execute rollback
    if bash "${SCRIPT_DIR}/rollback.sh" execute "$target_version" "$strategy" "$reason"; then
        log_success "Automatic rollback completed successfully"
        send_critical_alert "AUTOMATIC_ROLLBACK_SUCCESS" "Rollback to $target_version succeeded"

        # Record success
        record_rollback_event "automatic" "success" "$target_version" "$failure_type"
    else
        log_error "Automatic rollback FAILED"
        send_critical_alert "AUTOMATIC_ROLLBACK_FAILED" "Rollback to $target_version FAILED - manual intervention required"

        # Record failure
        record_rollback_event "automatic" "failed" "$target_version" "$failure_type"
    fi
}

schedule_rollback() {
    local decision="$1"
    local failure_type="$2"

    log_warning "Scheduling rollback for execution..."

    local rollback_window
    rollback_window=$(echo "$decision" | jq -r '.rollback_recommendation.rollback_window_seconds')

    local target_version
    target_version=$(echo "$decision" | jq -r '.deployment_info.target_version')

    # Create scheduled rollback file
    cat > "${STATE_DIR}/scheduled_rollback.json" <<EOF
{
  "scheduled_at": "$(date -Iseconds)",
  "execute_at": "$(date -d "+${rollback_window} seconds" -Iseconds 2>/dev/null || date -Iseconds)",
  "target_version": "$target_version",
  "failure_type": "$failure_type",
  "decision": $decision
}
EOF

    log_info "Rollback scheduled to execute in ${rollback_window}s"
    send_alert "ROLLBACK_SCHEDULED" "Rollback to $target_version scheduled in ${rollback_window}s"

    # Schedule execution (using at or cron, or simple sleep in background)
    (
        sleep "$rollback_window"
        if [[ -f "${STATE_DIR}/scheduled_rollback.json" ]]; then
            log_info "Executing scheduled rollback..."
            execute_automatic_rollback "$decision" "$failure_type"
            rm -f "${STATE_DIR}/scheduled_rollback.json"
        fi
    ) &

    disown
}

# ============================================================================
# ALERT SYSTEM
# ============================================================================

trigger_alert() {
    local alert_type="$1"
    local message="$2"

    # Check cooldown
    if ! check_alert_cooldown; then
        log_debug "Alert in cooldown period, skipping"
        return 0
    fi

    log_warning "ALERT: [$alert_type] $message"

    # Log to alert file
    cat >> "$ALERT_LOG" <<EOF
[$(date -Iseconds)] ALERT: $alert_type
Message: $message
Severity: WARNING
---
EOF

    # Update last alert time
    date +%s > "$LAST_ALERT_FILE"

    # Send notification (integrate with actual notification system)
    send_alert "$alert_type" "$message"
}

send_critical_alert() {
    local alert_type="$1"
    local message="$2"

    log_error "CRITICAL ALERT: [$alert_type] $message"

    # Log to alert file
    cat >> "$ALERT_LOG" <<EOF
[$(date -Iseconds)] CRITICAL ALERT: $alert_type
Message: $message
Severity: CRITICAL
---
EOF

    # Send high-priority notification
    send_alert "$alert_type" "$message" "CRITICAL"
}

send_alert() {
    local alert_type="$1"
    local message="$2"
    local severity="${3:-WARNING}"

    # Integration points for notification systems:

    # 1. Slack webhook
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"[$severity] $alert_type: $message\"}" \
            &>/dev/null || true
    fi

    # 2. Email (using mail command)
    if command -v mail &>/dev/null && [[ -n "${ALERT_EMAIL:-}" ]]; then
        echo "$message" | mail -s "[$severity] Claude Enhancer: $alert_type" "$ALERT_EMAIL" || true
    fi

    # 3. PagerDuty / OpsGenie integration point
    # Add your integration here

    # 4. Write to notification file for polling
    cat > "${STATE_DIR}/latest_alert.json" <<EOF
{
  "type": "$alert_type",
  "message": "$message",
  "severity": "$severity",
  "timestamp": "$(date -Iseconds)"
}
EOF
}

check_alert_cooldown() {
    if [[ ! -f "$LAST_ALERT_FILE" ]]; then
        return 0
    fi

    local last_alert
    last_alert=$(cat "$LAST_ALERT_FILE")

    local now
    now=$(date +%s)

    local elapsed=$((now - last_alert))

    if [[ $elapsed -lt $ALERT_COOLDOWN ]]; then
        return 1
    fi

    return 0
}

# ============================================================================
# ROLLBACK HISTORY
# ============================================================================

record_rollback_event() {
    local trigger_type="$1"  # automatic, scheduled, manual
    local result="$2"        # success, failed
    local target_version="$3"
    local reason="$4"

    local event
    event=$(cat <<EOF
{
  "trigger_type": "$trigger_type",
  "result": "$result",
  "target_version": "$target_version",
  "reason": "$reason",
  "timestamp": "$(date -Iseconds)",
  "user": "${USER:-unknown}"
}
EOF
)

    echo "$event" >> "$ROLLBACK_HISTORY"
}

get_rollback_stats() {
    if [[ ! -f "$ROLLBACK_HISTORY" ]]; then
        cat <<EOF
{
  "total_rollbacks": 0,
  "automatic_rollbacks": 0,
  "successful_rollbacks": 0,
  "failed_rollbacks": 0,
  "last_rollback": null
}
EOF
        return
    fi

    local total
    total=$(wc -l < "$ROLLBACK_HISTORY")

    local automatic
    automatic=$(grep -c '"trigger_type": "automatic"' "$ROLLBACK_HISTORY" || echo "0")

    local successful
    successful=$(grep -c '"result": "success"' "$ROLLBACK_HISTORY" || echo "0")

    local failed
    failed=$(grep -c '"result": "failed"' "$ROLLBACK_HISTORY" || echo "0")

    local last_rollback
    last_rollback=$(tail -1 "$ROLLBACK_HISTORY" 2>/dev/null || echo "null")

    cat <<EOF
{
  "total_rollbacks": $total,
  "automatic_rollbacks": $automatic,
  "successful_rollbacks": $successful,
  "failed_rollbacks": $failed,
  "last_rollback": $last_rollback
}
EOF
}

# ============================================================================
# MONITORING LOOP
# ============================================================================

run_monitoring_loop() {
    log_info "Starting automated rollback monitoring loop..."
    log_info "Interval: ${MONITORING_INTERVAL}s"
    log_info "Auto-rollback enabled: $AUTO_ROLLBACK_ENABLED"

    local iteration=0

    while true; do
        ((iteration++))
        log_info "Monitoring iteration #$iteration"

        # Run all checks
        monitor_health_checks || true
        monitor_slo_violations || true
        monitor_error_rate || true
        monitor_performance || true

        # Check for scheduled rollbacks
        check_scheduled_rollbacks

        # Update metrics cache
        update_metrics_cache

        # Sleep until next iteration
        sleep "$MONITORING_INTERVAL"
    done
}

check_scheduled_rollbacks() {
    local scheduled_file="${STATE_DIR}/scheduled_rollback.json"

    if [[ ! -f "$scheduled_file" ]]; then
        return 0
    fi

    local execute_at
    execute_at=$(jq -r '.execute_at' "$scheduled_file")

    local now
    now=$(date -Iseconds)

    if [[ "$now" > "$execute_at" ]]; then
        log_info "Scheduled rollback is due for execution"
        # The background job should handle it, but check if it's still there
        if [[ -f "$scheduled_file" ]]; then
            log_warning "Scheduled rollback file still exists - may have been missed"
        fi
    fi
}

update_metrics_cache() {
    cat > "$METRICS_CACHE" <<EOF
{
  "last_check": "$(date -Iseconds)",
  "iteration": $(date +%s),
  "monitoring_active": true
}
EOF
}

# ============================================================================
# MAIN COMMAND DISPATCHER
# ============================================================================

main() {
    local action="${1:-monitor}"
    shift || true

    case "$action" in
        monitor)
            run_monitoring_loop
            ;;

        check)
            log_info "Running one-time check..."
            monitor_health_checks
            monitor_slo_violations
            monitor_error_rate
            monitor_performance
            ;;

        test-rollback)
            local failure_type="${1:-health_check_failure}"
            log_warning "Testing rollback evaluation for: $failure_type"
            trigger_rollback_evaluation "$failure_type" "test_data"
            ;;

        stats)
            get_rollback_stats | jq .
            ;;

        enable)
            log_info "Enabling auto-rollback..."
            echo "true" > "${STATE_DIR}/auto_rollback_enabled"
            log_success "Auto-rollback enabled"
            ;;

        disable)
            log_warning "Disabling auto-rollback..."
            echo "false" > "${STATE_DIR}/auto_rollback_enabled"
            log_warning "Auto-rollback disabled - alerts will still be sent"
            ;;

        status)
            cat <<EOF
Auto-Rollback Status
====================
Enabled: $(if [[ -f "${STATE_DIR}/auto_rollback_enabled" ]]; then cat "${STATE_DIR}/auto_rollback_enabled"; else echo "$AUTO_ROLLBACK_ENABLED"; fi)
Monitoring Interval: ${MONITORING_INTERVAL}s
Alert Cooldown: ${ALERT_COOLDOWN}s

Rollback Statistics:
$(get_rollback_stats | jq .)

Last Alert:
$(if [[ -f "${STATE_DIR}/latest_alert.json" ]]; then cat "${STATE_DIR}/latest_alert.json" | jq .; else echo "None"; fi)
EOF
            ;;

        *)
            cat <<EOF
Usage: $0 {monitor|check|test-rollback|stats|enable|disable|status}

Actions:
  monitor                    - Start continuous monitoring loop
  check                      - Run one-time check of all monitors
  test-rollback <type>       - Test rollback evaluation (dry-run)
  stats                      - Show rollback statistics
  enable                     - Enable automatic rollbacks
  disable                    - Disable automatic rollbacks (alerts only)
  status                     - Show current status

Examples:
  $0 monitor                               # Start monitoring daemon
  $0 check                                 # One-time health check
  $0 test-rollback health_check_failure   # Test rollback logic
  $0 stats                                 # View rollback history
  $0 status                                # Check current status

Environment Variables:
  CE_AUTO_ROLLBACK_ENABLED=true/false     # Enable/disable auto-rollback
  CE_MONITORING_INTERVAL=30               # Check interval in seconds
  CE_ALERT_COOLDOWN=300                   # Seconds between alerts
  SLACK_WEBHOOK_URL=...                   # Slack integration
  ALERT_EMAIL=...                         # Email for alerts

Monitored Metrics:
  - Health check status (liveness, readiness, startup)
  - SLO violations (error budget tracking)
  - Error rate spikes (>25% critical, >50% immediate)
  - Performance degradation (CPU, I/O, response time)

For more information, see: docs/AUTO_ROLLBACK.md
EOF
            exit 1
            ;;
    esac
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
