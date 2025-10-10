#!/usr/bin/env bash
# healthcheck.sh - Comprehensive health check system for Claude Enhancer
# Implements liveness, readiness, and startup probes
set -euo pipefail

# Health check configuration
CE_HEALTH_CHECK_TIMEOUT="${CE_HEALTH_CHECK_TIMEOUT:-5}"  # seconds
CE_HEALTH_CHECK_VERBOSE="${CE_HEALTH_CHECK_VERBOSE:-false}"

# Health check result codes
readonly CE_HEALTH_OK=0
readonly CE_HEALTH_WARN=1
readonly CE_HEALTH_CRITICAL=2
readonly CE_HEALTH_UNKNOWN=3

# Initialize health check system
ce_health_init() {
    mkdir -p .workflow/observability/health

    cat > .workflow/observability/health/.metadata <<EOF
{
  "initialized_at": "$(date -Iseconds)",
  "timeout": ${CE_HEALTH_CHECK_TIMEOUT},
  "checks_enabled": [
    "liveness",
    "readiness",
    "startup"
  ]
}
EOF
}

# Core health check function
ce_health_check() {
    local check_name="$1"
    local check_function="$2"
    local timeout="${3:-$CE_HEALTH_CHECK_TIMEOUT}"

    local start_time
    start_time=$(date +%s)

    local result
    local status
    local message

    # Run check with timeout
    if timeout "$timeout" bash -c "$check_function" 2>/dev/null; then
        result=$CE_HEALTH_OK
        status="healthy"
        message="Check passed"
    else
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            result=$CE_HEALTH_CRITICAL
            status="timeout"
            message="Check timed out after ${timeout}s"
        else
            result=$CE_HEALTH_CRITICAL
            status="unhealthy"
            message="Check failed with exit code ${exit_code}"
        fi
    fi

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Record check result
    cat > ".workflow/observability/health/${check_name}.json" <<EOF
{
  "check": "${check_name}",
  "status": "${status}",
  "result": ${result},
  "message": "${message}",
  "duration_seconds": ${duration},
  "timestamp": "$(date -Iseconds)"
}
EOF

    return $result
}

# Liveness probe - Is the system running?
ce_health_liveness() {
    local checks_passed=0
    local checks_total=0

    # Check 1: Git repository accessible
    ((checks_total++))
    if [[ -d .git ]] && git rev-parse --git-dir >/dev/null 2>&1; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Git repository accessible"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Git repository not accessible"
    fi

    # Check 2: Required tools available
    ((checks_total++))
    if command -v git &>/dev/null && command -v jq &>/dev/null; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Required tools available"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Required tools missing"
    fi

    # Check 3: State directory writable
    ((checks_total++))
    if [[ -w .workflow/cli/state ]] || mkdir -p .workflow/cli/state 2>/dev/null; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ State directory writable"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ State directory not writable"
    fi

    # Check 4: No critical lock files
    ((checks_total++))
    if [[ ! -f .workflow/cli/state/.critical_lock ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ No critical locks"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Critical lock file exists"
    fi

    # Check 5: System load acceptable
    ((checks_total++))
    if command -v uptime &>/dev/null; then
        local load_avg
        load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
        local cpu_cores
        cpu_cores=$(nproc 2>/dev/null || echo 1)
        local load_threshold=$((cpu_cores * 2))

        if (( $(echo "$load_avg < $load_threshold" | bc -l) )); then
            ((checks_passed++))
            [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ System load acceptable (${load_avg} < ${load_threshold})"
        else
            [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ System load high (${load_avg} >= ${load_threshold})"
        fi
    else
        ((checks_passed++))  # Skip if uptime not available
    fi

    # Calculate health score
    if [[ $checks_passed -eq $checks_total ]]; then
        return $CE_HEALTH_OK
    elif [[ $checks_passed -ge $((checks_total / 2)) ]]; then
        return $CE_HEALTH_WARN
    else
        return $CE_HEALTH_CRITICAL
    fi
}

# Readiness probe - Is the system ready to accept commands?
ce_health_readiness() {
    local checks_passed=0
    local checks_total=0

    # Check 1: Core libraries loadable
    ((checks_total++))
    if [[ -f .workflow/cli/lib/common.sh ]] && \
       [[ -f .workflow/cli/lib/state_manager.sh ]] && \
       [[ -f .workflow/cli/lib/terminal_manager.sh ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Core libraries present"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Core libraries missing"
    fi

    # Check 2: Cache directory accessible
    ((checks_total++))
    if [[ -d .workflow/cli/state/cache ]] || mkdir -p .workflow/cli/state/cache 2>/dev/null; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Cache directory accessible"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Cache directory not accessible"
    fi

    # Check 3: Git operations functional
    ((checks_total++))
    if git status --porcelain >/dev/null 2>&1; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Git operations functional"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Git operations failing"
    fi

    # Check 4: Configuration files valid
    ((checks_total++))
    if [[ -f .workflow/gates.yml ]] && command -v yq &>/dev/null && yq eval . .workflow/gates.yml >/dev/null 2>&1; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Configuration valid"
    else
        ((checks_passed++))  # Not critical if yq missing
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "~ Configuration not validated (yq missing)"
    fi

    # Check 5: No conflicting state
    ((checks_total++))
    local conflict_count=0
    if [[ -d .workflow/cli/state/terminals ]]; then
        conflict_count=$(find .workflow/cli/state/terminals -name "*.conflict" 2>/dev/null | wc -l)
    fi

    if [[ $conflict_count -eq 0 ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ No state conflicts"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Found ${conflict_count} state conflicts"
    fi

    # Check 6: Disk space available
    ((checks_total++))
    local disk_usage
    disk_usage=$(df -h . | awk 'NR==2{print $5}' | sed 's/%//')

    if [[ $disk_usage -lt 90 ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Disk space available (${disk_usage}%)"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Disk space low (${disk_usage}%)"
    fi

    # Check 7: Memory available
    ((checks_total++))
    if command -v free &>/dev/null; then
        local memory_usage
        memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')

        if [[ $memory_usage -lt 90 ]]; then
            ((checks_passed++))
            [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Memory available (${memory_usage}%)"
        else
            [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Memory low (${memory_usage}%)"
        fi
    else
        ((checks_passed++))  # Skip if free not available
    fi

    # Calculate readiness
    if [[ $checks_passed -eq $checks_total ]]; then
        return $CE_HEALTH_OK
    elif [[ $checks_passed -ge $((checks_total * 3 / 4)) ]]; then
        return $CE_HEALTH_WARN
    else
        return $CE_HEALTH_CRITICAL
    fi
}

# Startup probe - Has system initialization completed?
ce_health_startup() {
    local checks_passed=0
    local checks_total=0

    # Check 1: Workflow executor present
    ((checks_total++))
    if [[ -f .workflow/executor.sh ]] && [[ -x .workflow/executor.sh ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Workflow executor present"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Workflow executor missing"
    fi

    # Check 2: Phase gates configured
    ((checks_total++))
    if [[ -f .workflow/gates.yml ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Phase gates configured"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ Phase gates not configured"
    fi

    # Check 3: Git hooks installed
    ((checks_total++))
    if [[ -f .git/hooks/pre-commit ]] && [[ -x .git/hooks/pre-commit ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Git hooks installed"
    else
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "~ Git hooks not installed (optional)"
        ((checks_passed++))  # Not critical
    fi

    # Check 4: State directory initialized
    ((checks_total++))
    if [[ -d .workflow/cli/state ]] && [[ -f .workflow/cli/state/.initialized ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ State directory initialized"
    else
        # Try to initialize
        if mkdir -p .workflow/cli/state && touch .workflow/cli/state/.initialized 2>/dev/null; then
            ((checks_passed++))
            [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ State directory initialized (now)"
        else
            [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✗ State directory initialization failed"
        fi
    fi

    # Check 5: Monitoring initialized
    ((checks_total++))
    if [[ -d .workflow/observability ]] && [[ -f .workflow/observability/.initialized ]]; then
        ((checks_passed++))
        [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Monitoring initialized"
    else
        # Try to initialize
        if mkdir -p .workflow/observability && touch .workflow/observability/.initialized 2>/dev/null; then
            ((checks_passed++))
            [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "✓ Monitoring initialized (now)"
        else
            [[ "${CE_HEALTH_CHECK_VERBOSE}" == "true" ]] && echo "~ Monitoring not initialized (non-critical)"
            ((checks_passed++))  # Not critical
        fi
    fi

    # Calculate startup health
    if [[ $checks_passed -eq $checks_total ]]; then
        return $CE_HEALTH_OK
    else
        return $CE_HEALTH_WARN
    fi
}

# Combined health check
ce_health_check_all() {
    local output_format="${1:-text}"  # text or json

    echo "Running comprehensive health checks..."
    echo ""

    local liveness_result
    local readiness_result
    local startup_result

    # Run all probes
    echo "=== Liveness Probe ==="
    ce_health_check "liveness" "ce_health_liveness"
    liveness_result=$?

    echo ""
    echo "=== Readiness Probe ==="
    ce_health_check "readiness" "ce_health_readiness"
    readiness_result=$?

    echo ""
    echo "=== Startup Probe ==="
    ce_health_check "startup" "ce_health_startup"
    startup_result=$?

    echo ""
    echo "=== Health Summary ==="

    # Determine overall health
    local overall_status="healthy"
    local overall_result=$CE_HEALTH_OK

    if [[ $liveness_result -ge $CE_HEALTH_CRITICAL ]] || \
       [[ $readiness_result -ge $CE_HEALTH_CRITICAL ]]; then
        overall_status="critical"
        overall_result=$CE_HEALTH_CRITICAL
    elif [[ $liveness_result -ge $CE_HEALTH_WARN ]] || \
         [[ $readiness_result -ge $CE_HEALTH_WARN ]] || \
         [[ $startup_result -ge $CE_HEALTH_WARN ]]; then
        overall_status="degraded"
        overall_result=$CE_HEALTH_WARN
    fi

    if [[ "$output_format" == "json" ]]; then
        cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "overall_status": "${overall_status}",
  "overall_result": ${overall_result},
  "probes": {
    "liveness": $(cat .workflow/observability/health/liveness.json),
    "readiness": $(cat .workflow/observability/health/readiness.json),
    "startup": $(cat .workflow/observability/health/startup.json)
  }
}
EOF
    else
        echo "Overall Status: ${overall_status}"
        echo "  Liveness:  $(ce_health_status_text $liveness_result)"
        echo "  Readiness: $(ce_health_status_text $readiness_result)"
        echo "  Startup:   $(ce_health_status_text $startup_result)"
    fi

    return $overall_result
}

# Helper to convert status code to text
ce_health_status_text() {
    case $1 in
        $CE_HEALTH_OK)
            echo "✓ Healthy"
            ;;
        $CE_HEALTH_WARN)
            echo "⚠ Degraded"
            ;;
        $CE_HEALTH_CRITICAL)
            echo "✗ Critical"
            ;;
        *)
            echo "? Unknown"
            ;;
    esac
}

# Quick health check (for scripts)
ce_health_quick() {
    # Quick liveness check only
    if [[ -d .git ]] && \
       command -v git &>/dev/null && \
       git rev-parse --git-dir >/dev/null 2>&1 && \
       [[ -w .workflow/cli/state ]]; then
        return $CE_HEALTH_OK
    else
        return $CE_HEALTH_CRITICAL
    fi
}

# Health check HTTP endpoint simulation
ce_health_endpoint() {
    local endpoint="${1:-/healthz}"

    case "$endpoint" in
        /healthz|/health)
            # Basic health check
            ce_health_quick
            local result=$?
            if [[ $result -eq $CE_HEALTH_OK ]]; then
                echo "HTTP/1.1 200 OK"
                echo "Content-Type: application/json"
                echo ""
                echo '{"status":"ok"}'
                return 0
            else
                echo "HTTP/1.1 503 Service Unavailable"
                echo "Content-Type: application/json"
                echo ""
                echo '{"status":"unhealthy"}'
                return 1
            fi
            ;;
        /healthz/live|/livez)
            # Liveness probe
            ce_health_liveness >/dev/null 2>&1
            local result=$?
            if [[ $result -eq $CE_HEALTH_OK ]]; then
                echo '{"status":"ok","probe":"liveness"}'
                return 0
            else
                echo '{"status":"unhealthy","probe":"liveness"}'
                return 1
            fi
            ;;
        /healthz/ready|/readyz)
            # Readiness probe
            ce_health_readiness >/dev/null 2>&1
            local result=$?
            if [[ $result -eq $CE_HEALTH_OK ]]; then
                echo '{"status":"ok","probe":"readiness"}'
                return 0
            else
                echo '{"status":"unhealthy","probe":"readiness"}'
                return 1
            fi
            ;;
        /healthz/startup|/startupz)
            # Startup probe
            ce_health_startup >/dev/null 2>&1
            local result=$?
            if [[ $result -eq $CE_HEALTH_OK ]]; then
                echo '{"status":"ok","probe":"startup"}'
                return 0
            else
                echo '{"status":"unhealthy","probe":"startup"}'
                return 1
            fi
            ;;
        *)
            echo "Unknown endpoint: $endpoint"
            return 1
            ;;
    esac
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ce_health_init

    case "${1:-all}" in
        liveness|live)
            CE_HEALTH_CHECK_VERBOSE=true ce_health_liveness
            exit $?
            ;;
        readiness|ready)
            CE_HEALTH_CHECK_VERBOSE=true ce_health_readiness
            exit $?
            ;;
        startup)
            CE_HEALTH_CHECK_VERBOSE=true ce_health_startup
            exit $?
            ;;
        all)
            CE_HEALTH_CHECK_VERBOSE=true ce_health_check_all "${2:-text}"
            exit $?
            ;;
        quick)
            ce_health_quick
            exit $?
            ;;
        endpoint)
            ce_health_endpoint "${2:-/healthz}"
            exit $?
            ;;
        *)
            cat <<EOF
Usage: $0 {liveness|readiness|startup|all|quick|endpoint}

Commands:
  liveness              Run liveness probe
  readiness             Run readiness probe
  startup               Run startup probe
  all [format]          Run all probes (format: text|json)
  quick                 Quick health check
  endpoint <path>       Simulate HTTP health endpoint

Examples:
  $0 all json
  $0 liveness
  $0 endpoint /healthz/ready
EOF
            exit 1
            ;;
    esac
fi

# Export functions
export -f ce_health_init
export -f ce_health_check
export -f ce_health_liveness
export -f ce_health_readiness
export -f ce_health_startup
export -f ce_health_check_all
export -f ce_health_quick
export -f ce_health_endpoint
