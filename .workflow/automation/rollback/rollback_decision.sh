#!/usr/bin/env bash
# Rollback Decision Engine for Claude Enhancer v5.4.0
# Purpose: Analyze failures and recommend rollback strategies
# Used by: Auto-rollback triggers, manual analysis

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils/common.sh"

# Decision thresholds
readonly ERROR_RATE_THRESHOLD_CRITICAL=50  # % error rate
readonly ERROR_RATE_THRESHOLD_HIGH=25      # % error rate
readonly RESPONSE_TIME_THRESHOLD_MS=5000   # milliseconds
readonly FAILURE_WINDOW_MINUTES=15         # time window for analysis

# Severity levels
readonly SEVERITY_CRITICAL="CRITICAL"
readonly SEVERITY_HIGH="HIGH"
readonly SEVERITY_MEDIUM="MEDIUM"
readonly SEVERITY_LOW="LOW"

# Recommendation types
readonly RECOMMEND_IMMEDIATE="IMMEDIATE_ROLLBACK"
readonly RECOMMEND_SCHEDULED="SCHEDULED_ROLLBACK"
readonly RECOMMEND_MONITOR="MONITOR_ONLY"
readonly RECOMMEND_NONE="NO_ACTION"

# ============================================================================
# FAILURE ANALYSIS
# ============================================================================

analyze_failure_severity() {
    local failure_type="$1"
    local failure_data="${2:-}"

    log_info "Analyzing failure severity: $failure_type"

    local severity="$SEVERITY_LOW"
    local confidence=0

    case "$failure_type" in
        health_check_failure)
            severity=$(analyze_health_check_severity "$failure_data")
            confidence=90
            ;;
        slo_violation)
            severity=$(analyze_slo_violation_severity "$failure_data")
            confidence=95
            ;;
        error_spike)
            severity=$(analyze_error_spike_severity "$failure_data")
            confidence=85
            ;;
        performance_degradation)
            severity=$(analyze_performance_severity "$failure_data")
            confidence=80
            ;;
        deployment_failure)
            severity="$SEVERITY_CRITICAL"
            confidence=100
            ;;
        *)
            severity="$SEVERITY_MEDIUM"
            confidence=50
            ;;
    esac

    cat <<EOF
{
  "failure_type": "$failure_type",
  "severity": "$severity",
  "confidence": $confidence,
  "analyzed_at": "$(date -Iseconds)"
}
EOF
}

analyze_health_check_severity() {
    local failure_data="$1"

    # Check health check results
    local failed_probes=0
    local total_probes=0

    if [[ -f "observability/probes/healthcheck.sh" ]]; then
        # Run health checks and count failures
        bash observability/probes/healthcheck.sh all json 2>/dev/null | \
            grep -o '"result": [0-9]*' | \
            awk '{sum+=$2; count++} END {
                if (count > 0 && sum >= 2) print "CRITICAL";
                else if (count > 0 && sum >= 1) print "HIGH";
                else print "MEDIUM"
            }' || echo "$SEVERITY_MEDIUM"
    else
        echo "$SEVERITY_MEDIUM"
    fi
}

analyze_slo_violation_severity() {
    local failure_data="$1"

    # Parse SLO violation data
    local violation_percentage
    violation_percentage=$(echo "$failure_data" | grep -oE '[0-9]+' | head -1 || echo "0")

    if [[ $violation_percentage -ge 50 ]]; then
        echo "$SEVERITY_CRITICAL"
    elif [[ $violation_percentage -ge 25 ]]; then
        echo "$SEVERITY_HIGH"
    elif [[ $violation_percentage -ge 10 ]]; then
        echo "$SEVERITY_MEDIUM"
    else
        echo "$SEVERITY_LOW"
    fi
}

analyze_error_spike_severity() {
    local failure_data="$1"

    # Check error rate from logs
    local error_count
    error_count=$(journalctl -u claude-enhancer --since "15 minutes ago" 2>/dev/null | \
                  grep -ci "error\|critical\|fatal" || echo "0")

    local total_count
    total_count=$(journalctl -u claude-enhancer --since "15 minutes ago" 2>/dev/null | \
                  wc -l || echo "1")

    local error_rate
    error_rate=$(( (error_count * 100) / total_count ))

    if [[ $error_rate -ge $ERROR_RATE_THRESHOLD_CRITICAL ]]; then
        echo "$SEVERITY_CRITICAL"
    elif [[ $error_rate -ge $ERROR_RATE_THRESHOLD_HIGH ]]; then
        echo "$SEVERITY_HIGH"
    else
        echo "$SEVERITY_MEDIUM"
    fi
}

analyze_performance_severity() {
    local failure_data="$1"

    # Check performance metrics
    local avg_response_time
    avg_response_time=$(echo "$failure_data" | grep -oE '[0-9]+ms' | grep -oE '[0-9]+' | head -1 || echo "0")

    if [[ $avg_response_time -ge $((RESPONSE_TIME_THRESHOLD_MS * 2)) ]]; then
        echo "$SEVERITY_CRITICAL"
    elif [[ $avg_response_time -ge $RESPONSE_TIME_THRESHOLD_MS ]]; then
        echo "$SEVERITY_HIGH"
    else
        echo "$SEVERITY_MEDIUM"
    fi
}

# ============================================================================
# ROLLBACK STRATEGY RECOMMENDATION
# ============================================================================

recommend_rollback_strategy() {
    local severity="$1"
    local failure_type="$2"
    local deployment_age_minutes="${3:-0}"

    log_info "Determining rollback strategy recommendation..."

    local recommendation
    local rollback_strategy
    local rollback_window
    local reason

    case "$severity" in
        "$SEVERITY_CRITICAL")
            if [[ $deployment_age_minutes -le 30 ]]; then
                recommendation="$RECOMMEND_IMMEDIATE"
                rollback_strategy="revert"
                rollback_window=300  # 5 minutes
                reason="Critical failure detected within 30 minutes of deployment"
            else
                recommendation="$RECOMMEND_SCHEDULED"
                rollback_strategy="revert"
                rollback_window=900  # 15 minutes
                reason="Critical failure detected, but deployment is stable for >30min"
            fi
            ;;

        "$SEVERITY_HIGH")
            if [[ $deployment_age_minutes -le 60 ]]; then
                recommendation="$RECOMMEND_SCHEDULED"
                rollback_strategy="revert"
                rollback_window=1800  # 30 minutes
                reason="High severity failure detected within 1 hour of deployment"
            else
                recommendation="$RECOMMEND_MONITOR"
                rollback_strategy="none"
                rollback_window=0
                reason="High severity failure, but deployment is mature (>1h)"
            fi
            ;;

        "$SEVERITY_MEDIUM")
            recommendation="$RECOMMEND_MONITOR"
            rollback_strategy="none"
            rollback_window=0
            reason="Medium severity failure - monitoring recommended"
            ;;

        *)
            recommendation="$RECOMMEND_NONE"
            rollback_strategy="none"
            rollback_window=0
            reason="Low severity failure - no action needed"
            ;;
    esac

    cat <<EOF
{
  "recommendation": "$recommendation",
  "rollback_strategy": "$rollback_strategy",
  "rollback_window_seconds": $rollback_window,
  "reason": "$reason",
  "severity": "$severity",
  "failure_type": "$failure_type",
  "deployment_age_minutes": $deployment_age_minutes,
  "timestamp": "$(date -Iseconds)"
}
EOF
}

# ============================================================================
# ROLLBACK WINDOW CALCULATION
# ============================================================================

calculate_rollback_window() {
    local target_version="$1"
    local strategy="${2:-revert}"

    log_info "Calculating rollback window..."

    # Get impact estimates
    local commits_count
    commits_count=$(git rev-list --count "${target_version}..HEAD" 2>/dev/null || echo "0")

    local files_count
    files_count=$(git diff --name-only "${target_version}..HEAD" | wc -l || echo "0")

    # Base time estimates
    local base_time=60  # 1 minute base
    local time_per_commit=2
    local time_per_file=1
    local health_check_time=60
    local deployment_time=120

    # Calculate total time
    local total_time=$((
        base_time +
        (commits_count * time_per_commit) +
        (files_count * time_per_file) +
        health_check_time +
        deployment_time
    ))

    # Add buffer for strategy
    case "$strategy" in
        reset)
            total_time=$((total_time / 2))  # Reset is faster
            ;;
        revert)
            total_time=$((total_time * 3 / 2))  # Revert needs more time
            ;;
    esac

    # Add 20% safety margin
    total_time=$((total_time * 12 / 10))

    cat <<EOF
{
  "target_version": "$target_version",
  "strategy": "$strategy",
  "estimated_time_seconds": $total_time,
  "breakdown": {
    "base_time": $base_time,
    "commit_processing": $((commits_count * time_per_commit)),
    "file_processing": $((files_count * time_per_file)),
    "health_checks": $health_check_time,
    "deployment": $deployment_time,
    "safety_margin": $((total_time / 6))
  },
  "calculated_at": "$(date -Iseconds)"
}
EOF

    echo "$total_time"
}

# ============================================================================
# RECOVERY TIME ESTIMATION
# ============================================================================

estimate_recovery_time() {
    local failure_type="$1"
    local rollback_strategy="$2"

    log_info "Estimating recovery time..."

    local rollback_time=300  # 5 minutes default
    local verification_time=120  # 2 minutes
    local propagation_time=60  # 1 minute

    # Adjust based on failure type
    case "$failure_type" in
        database_failure)
            verification_time=300  # 5 minutes for DB checks
            ;;
        cache_corruption)
            propagation_time=300  # 5 minutes for cache propagation
            ;;
        deployment_failure)
            rollback_time=600  # 10 minutes for deployment rollback
            ;;
    esac

    # Adjust based on strategy
    case "$rollback_strategy" in
        reset)
            rollback_time=$((rollback_time / 2))
            ;;
        selective)
            rollback_time=$((rollback_time / 3))
            ;;
    esac

    local total_recovery_time=$((rollback_time + verification_time + propagation_time))

    cat <<EOF
{
  "failure_type": "$failure_type",
  "rollback_strategy": "$rollback_strategy",
  "estimated_recovery_time_seconds": $total_recovery_time,
  "breakdown": {
    "rollback": $rollback_time,
    "verification": $verification_time,
    "propagation": $propagation_time
  },
  "estimated_at": "$(date -Iseconds)"
}
EOF
}

# ============================================================================
# ROLLBACK FEASIBILITY CHECK
# ============================================================================

check_rollback_feasibility() {
    local target_version="$1"

    log_info "Checking rollback feasibility..."

    local feasible=true
    local blockers=()
    local warnings=()

    # Check 1: Target version exists
    if ! git rev-parse "$target_version" &>/dev/null; then
        feasible=false
        blockers+=("Target version does not exist")
    fi

    # Check 2: No active transactions
    if [[ -f ".workflow/cli/state/.active_transaction" ]]; then
        feasible=false
        blockers+=("Active transaction in progress")
    fi

    # Check 3: Database state
    if [[ -d "migrations" ]]; then
        local migration_count
        migration_count=$(git diff --name-only "${target_version}..HEAD" migrations/ 2>/dev/null | wc -l || echo "0")
        if [[ $migration_count -gt 0 ]]; then
            warnings+=("$migration_count database migrations will need manual rollback")
        fi
    fi

    # Check 4: Data compatibility
    local version_diff
    version_diff=$(git rev-list --count "${target_version}..HEAD" 2>/dev/null || echo "0")
    if [[ $version_diff -gt 20 ]]; then
        warnings+=("Large version gap ($version_diff commits) - data compatibility risk")
    fi

    # Check 5: Disk space
    local disk_usage
    disk_usage=$(df -h . | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        feasible=false
        blockers+=("Insufficient disk space: ${disk_usage}%")
    fi

    # Check 6: Network connectivity
    if ! git ls-remote origin &>/dev/null; then
        warnings+=("No network connectivity - rollback will be local only")
    fi

    # Generate report
    local blockers_json
    blockers_json=$(printf '%s\n' "${blockers[@]}" | jq -R . | jq -s . || echo "[]")

    local warnings_json
    warnings_json=$(printf '%s\n' "${warnings[@]}" | jq -R . | jq -s . || echo "[]")

    cat <<EOF
{
  "feasible": $feasible,
  "target_version": "$target_version",
  "blockers": $blockers_json,
  "warnings": $warnings_json,
  "checks_performed": 6,
  "checked_at": "$(date -Iseconds)"
}
EOF

    if [[ "$feasible" == true ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# DECISION SUMMARY
# ============================================================================

generate_decision_summary() {
    local failure_type="$1"
    local failure_data="${2:-}"

    log_info "Generating rollback decision summary..."

    # Analyze failure
    local severity_json
    severity_json=$(analyze_failure_severity "$failure_type" "$failure_data")
    local severity
    severity=$(echo "$severity_json" | jq -r '.severity')

    # Get deployment age
    local deployment_age
    deployment_age=$(get_deployment_age_minutes)

    # Get recommendation
    local recommendation_json
    recommendation_json=$(recommend_rollback_strategy "$severity" "$failure_type" "$deployment_age")
    local recommendation
    recommendation=$(echo "$recommendation_json" | jq -r '.recommendation')

    # Get target version
    local target_version
    target_version=$(git describe --tags --abbrev=0 2>/dev/null || echo "unknown")

    # Check feasibility
    local feasibility_json
    feasibility_json=$(check_rollback_feasibility "$target_version")

    # Calculate times
    local rollback_window_json
    rollback_window_json=$(calculate_rollback_window "$target_version" "revert")

    local recovery_time_json
    recovery_time_json=$(estimate_recovery_time "$failure_type" "revert")

    # Generate comprehensive summary
    cat <<EOF
{
  "decision_summary": {
    "recommendation": "$recommendation",
    "severity": "$severity",
    "confidence": "high"
  },
  "failure_analysis": $severity_json,
  "rollback_recommendation": $recommendation_json,
  "feasibility_check": $feasibility_json,
  "time_estimates": {
    "rollback_window": $rollback_window_json,
    "recovery_time": $recovery_time_json
  },
  "deployment_info": {
    "age_minutes": $deployment_age,
    "target_version": "$target_version"
  },
  "generated_at": "$(date -Iseconds)"
}
EOF
}

get_deployment_age_minutes() {
    local latest_commit_time
    latest_commit_time=$(git log -1 --format=%ct 2>/dev/null || echo "0")

    local current_time
    current_time=$(date +%s)

    local age_seconds=$((current_time - latest_commit_time))
    local age_minutes=$((age_seconds / 60))

    echo "$age_minutes"
}

# ============================================================================
# MAIN COMMAND DISPATCHER
# ============================================================================

main() {
    local action="${1:-analyze}"
    shift || true

    case "$action" in
        analyze)
            local failure_type="${1:-unknown}"
            local failure_data="${2:-}"
            generate_decision_summary "$failure_type" "$failure_data"
            ;;

        severity)
            local failure_type="${1:-unknown}"
            local failure_data="${2:-}"
            analyze_failure_severity "$failure_type" "$failure_data"
            ;;

        recommend)
            local severity="${1:-MEDIUM}"
            local failure_type="${2:-unknown}"
            local age="${3:-0}"
            recommend_rollback_strategy "$severity" "$failure_type" "$age"
            ;;

        feasibility)
            local target_version="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo 'HEAD')}"
            check_rollback_feasibility "$target_version"
            ;;

        window)
            local target_version="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo 'HEAD')}"
            local strategy="${2:-revert}"
            calculate_rollback_window "$target_version" "$strategy"
            ;;

        recovery-time)
            local failure_type="${1:-unknown}"
            local strategy="${2:-revert}"
            estimate_recovery_time "$failure_type" "$strategy"
            ;;

        *)
            cat <<EOF
Usage: $0 {analyze|severity|recommend|feasibility|window|recovery-time} [options]

Actions:
  analyze <failure_type> [data]           - Generate comprehensive decision summary
  severity <failure_type> [data]          - Analyze failure severity
  recommend <severity> <type> [age]       - Get rollback recommendation
  feasibility <target_version>            - Check if rollback is feasible
  window <target_version> [strategy]      - Calculate rollback time window
  recovery-time <failure_type> [strategy] - Estimate recovery time

Failure Types:
  - health_check_failure
  - slo_violation
  - error_spike
  - performance_degradation
  - deployment_failure
  - database_failure
  - cache_corruption

Severity Levels:
  - CRITICAL  (immediate action required)
  - HIGH      (urgent attention needed)
  - MEDIUM    (monitoring recommended)
  - LOW       (informational)

Examples:
  $0 analyze health_check_failure
  $0 severity slo_violation "error_rate=35%"
  $0 recommend CRITICAL deployment_failure 15
  $0 feasibility v5.3.5
  $0 window v5.3.5 revert
  $0 recovery-time database_failure reset

Exit codes:
  0 = Success / Rollback recommended
  1 = Failure / Rollback not recommended

Output Format:
  All commands output JSON for easy integration with automation

For more information, see: docs/ROLLBACK_DECISION_ENGINE.md
EOF
            exit 1
            ;;
    esac
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
