#!/usr/bin/env bash
set -euo pipefail

# Time Drift Check - Reality Check for Evidence Timestamps
# Prevents nonce time sequence issues due to local clock drift

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
fail(){ echo -e "${RED}✗ $*${NC}"; exit 1; }
ok(){ echo -e "${GREEN}✓ $*${NC}"; }
warn(){ echo -e "${YELLOW}⚠ $*${NC}"; }
info(){ echo -e "${BLUE}ℹ $*${NC}"; }

# Configuration
MAX_DRIFT_SECONDS=120  # Alert if drift > 120 seconds
TIME_SOURCE_URL="https://github.com"  # Use GitHub as time source

# ============================================================================
# TIME SOURCE FUNCTIONS
# ============================================================================

get_remote_time() {
    # Get server time from HTTP Date header
    local response
    response=$(curl -sI "$TIME_SOURCE_URL" 2>/dev/null || echo "")

    if [ -z "$response" ]; then
        warn "Failed to fetch remote time from $TIME_SOURCE_URL"
        return 1
    fi

    # Extract Date header
    local date_header
    date_header=$(echo "$response" | grep -i "^Date:" | cut -d' ' -f2- | tr -d '\r')

    if [ -z "$date_header" ]; then
        warn "No Date header found in response"
        return 1
    fi

    # Convert to Unix timestamp
    local remote_timestamp
    remote_timestamp=$(date -d "$date_header" +%s 2>/dev/null || echo "")

    if [ -z "$remote_timestamp" ]; then
        warn "Failed to parse date: $date_header"
        return 1
    fi

    echo "$remote_timestamp"
}

get_local_time() {
    date +%s
}

# ============================================================================
# DRIFT CALCULATION
# ============================================================================

calculate_drift() {
    info "Checking time drift against $TIME_SOURCE_URL..."

    local local_time
    local_time=$(get_local_time)

    local remote_time
    remote_time=$(get_remote_time) || {
        warn "Could not retrieve remote time, skipping drift check"
        return 2
    }

    local drift=$(( local_time - remote_time ))
    local abs_drift=${drift#-}  # Absolute value

    # Store drift information
    local drift_file=".workflow/logs/time_drift.log"
    mkdir -p "$(dirname "$drift_file")"

    cat >> "$drift_file" <<EOF
$(date -Iseconds) | Local: $local_time | Remote: $remote_time | Drift: ${drift}s
EOF

    # Display results
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Time Drift Check Results"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Local Time:   $(date -d @$local_time -Iseconds)"
    echo "  Remote Time:  $(date -d @$remote_time -Iseconds)"
    echo "  Drift:        ${drift}s"

    if [ $abs_drift -gt $MAX_DRIFT_SECONDS ]; then
        echo -e "  Status:       ${YELLOW}⚠ WARNING${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        warn "Time drift exceeds threshold!"
        warn "Drift: ${drift}s (threshold: ${MAX_DRIFT_SECONDS}s)"
        echo ""
        echo "⚠️  Recommendations:"
        echo "  1. Sync your system clock with NTP:"
        echo "     sudo ntpdate pool.ntp.org"
        echo "     # OR"
        echo "     sudo timedatectl set-ntp true"
        echo ""
        echo "  2. Check your timezone settings:"
        echo "     timedatectl status"
        echo ""
        echo "  3. For WSL users, sync with Windows time:"
        echo "     sudo hwclock -s"
        echo ""
        return 1
    else
        echo -e "  Status:       ${GREEN}✓ OK${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        ok "Time drift within acceptable range (${abs_drift}s < ${MAX_DRIFT_SECONDS}s)"
        return 0
    fi
}

# ============================================================================
# DRIFT HISTORY
# ============================================================================

show_drift_history() {
    local drift_file=".workflow/logs/time_drift.log"

    if [ ! -f "$drift_file" ]; then
        info "No drift history found"
        return 0
    fi

    info "Recent time drift history (last 10 entries):"
    echo ""
    tail -10 "$drift_file" | while IFS='|' read -r timestamp local remote drift; do
        echo "  $timestamp | Drift: $drift"
    done
    echo ""
}

# ============================================================================
# CONTINUOUS MONITORING
# ============================================================================

monitor_drift() {
    local interval="${1:-300}"  # Default: check every 5 minutes

    info "Starting continuous drift monitoring (interval: ${interval}s)"
    info "Press Ctrl+C to stop"
    echo ""

    while true; do
        calculate_drift || true
        echo ""
        info "Next check in ${interval}s..."
        sleep "$interval"
    done
}

# ============================================================================
# UPDATE EVIDENCE WITH SERVER TIME
# ============================================================================

update_evidence_timestamp() {
    local evidence_file="${1:-.workflow/logs/evidence.log}"

    info "Updating evidence with server timestamp..."

    local remote_time
    remote_time=$(get_remote_time) || {
        fail "Could not retrieve remote time for evidence update"
    }

    local remote_date
    remote_date=$(date -d @$remote_time -Iseconds)

    mkdir -p "$(dirname "$evidence_file")"

    cat >> "$evidence_file" <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Timestamp: $remote_date (server-verified)
Local Time: $(date -Iseconds)
Time Source: $TIME_SOURCE_URL
Drift: $(( $(get_local_time) - remote_time ))s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

    ok "Evidence timestamp updated with server time"
    ok "Evidence file: $evidence_file"
}

# ============================================================================
# USAGE AND MAIN
# ============================================================================

usage() {
    cat <<EOF
Usage: $0 [command] [options]

Commands:
    check                         Check current time drift (default)
    history                       Show drift history
    monitor [interval]            Continuous monitoring (default: 300s)
    update-evidence [file]        Update evidence with server timestamp

Options:
    --max-drift <seconds>         Maximum acceptable drift (default: 120)
    --time-source <url>           Time source URL (default: https://github.com)

Examples:
    # Check current drift
    $0 check

    # Show drift history
    $0 history

    # Monitor drift every 60 seconds
    $0 monitor 60

    # Update evidence with server timestamp
    $0 update-evidence .workflow/logs/release_evidence.log

Environment Variables:
    MAX_DRIFT_SECONDS    Maximum acceptable drift (default: 120)
    TIME_SOURCE_URL      Time source URL (default: https://github.com)

Notes:
    - Drift is calculated as: local_time - remote_time
    - Positive drift means local clock is ahead
    - Negative drift means local clock is behind
    - Drift history is logged to .workflow/logs/time_drift.log
EOF
    exit 0
}

main() {
    local command="${1:-check}"

    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --max-drift)
                MAX_DRIFT_SECONDS="$2"
                shift 2
                ;;
            --time-source)
                TIME_SOURCE_URL="$2"
                shift 2
                ;;
            -h|--help|help)
                usage
                ;;
            *)
                command="$1"
                shift
                break
                ;;
        esac
    done

    case "$command" in
        check)
            calculate_drift
            ;;
        history)
            show_drift_history
            ;;
        monitor)
            local interval="${1:-300}"
            monitor_drift "$interval"
            ;;
        update-evidence)
            local evidence_file="${1:-.workflow/logs/evidence.log}"
            update_evidence_timestamp "$evidence_file"
            ;;
        *)
            fail "Unknown command: $command (use --help for usage)"
            ;;
    esac
}

main "$@"
