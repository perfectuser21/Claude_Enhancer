#!/usr/bin/env bash
# verify_installation.sh - Verify observability system installation
set -euo pipefail

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║    Claude Enhancer Observability Installation Verification        ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
RESET="\033[0m"

# Check counters
total_checks=0
passed_checks=0

check_file() {
    local file="$1"
    local description="$2"
    ((total_checks++))

    if [[ -f "$file" ]]; then
        echo -e "  ${GREEN}✓${RESET} ${description}"
        ((passed_checks++))
    else
        echo -e "  ${RED}✗${RESET} ${description} - MISSING"
    fi
}

check_executable() {
    local file="$1"
    local description="$2"
    ((total_checks++))

    if [[ -x "$file" ]]; then
        echo -e "  ${GREEN}✓${RESET} ${description}"
        ((passed_checks++))
    else
        echo -e "  ${YELLOW}⚠${RESET} ${description} - NOT EXECUTABLE"
    fi
}

echo "Checking Core Components..."
echo "─────────────────────────────────────────────────────────────────────"
check_executable "observability/metrics/collector.sh" "Metrics Collector"
check_executable "observability/logging/logger.sh" "Structured Logger"
check_executable "observability/probes/healthcheck.sh" "Health Check System"
check_executable "observability/alerts/notifier.sh" "Alert Notifier"
check_executable "observability/dashboards/status.sh" "Status Dashboard"
check_executable "observability/performance/monitor.sh" "Performance Monitor"
check_executable "observability/analytics/usage_tracker.sh" "Usage Analytics"
echo ""

echo "Checking Configuration Files..."
echo "─────────────────────────────────────────────────────────────────────"
check_file "observability/slo/slo.yml" "SLO Definitions"
check_file "observability/alerts/alert_rules.yml" "Alert Rules"
check_file "metrics/perf_budget.yml" "Performance Budgets"
check_file "observability/README.md" "Documentation"
echo ""

echo "Checking Directory Structure..."
echo "─────────────────────────────────────────────────────────────────────"
check_file "observability/metrics/.gitkeep" "Metrics Directory"
check_file "observability/logging/.gitkeep" "Logging Directory"
check_file "observability/probes/.gitkeep" "Probes Directory"
check_file "observability/alerts/.gitkeep" "Alerts Directory"
check_file "observability/dashboards/.gitkeep" "Dashboards Directory"
check_file "observability/performance/.gitkeep" "Performance Directory"
check_file "observability/analytics/.gitkeep" "Analytics Directory"
echo ""

echo "Running Functional Tests..."
echo "─────────────────────────────────────────────────────────────────────"

# Test health check
((total_checks++))
if ./observability/probes/healthcheck.sh quick &>/dev/null; then
    echo -e "  ${GREEN}✓${RESET} Health check execution"
    ((passed_checks++))
else
    echo -e "  ${RED}✗${RESET} Health check execution - FAILED"
fi

# Test logger initialization
((total_checks++))
if ./observability/logging/logger.sh init &>/dev/null; then
    echo -e "  ${GREEN}✓${RESET} Logger initialization"
    ((passed_checks++))
else
    echo -e "  ${RED}✗${RESET} Logger initialization - FAILED"
fi

# Test metrics collection
((total_checks++))
if ./observability/metrics/collector.sh collect &>/dev/null; then
    echo -e "  ${GREEN}✓${RESET} Metrics collection"
    ((passed_checks++))
else
    echo -e "  ${RED}✗${RESET} Metrics collection - FAILED"
fi

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo ""

# Calculate percentage
percentage=$((passed_checks * 100 / total_checks))

echo "Verification Results:"
echo "  Total Checks:  ${total_checks}"
echo "  Passed:        ${passed_checks}"
echo "  Failed:        $((total_checks - passed_checks))"
echo "  Success Rate:  ${percentage}%"
echo ""

if [[ $passed_checks -eq $total_checks ]]; then
    echo -e "${GREEN}✓ All checks passed! Observability system is ready.${RESET}"
    exit 0
elif [[ $percentage -ge 80 ]]; then
    echo -e "${YELLOW}⚠ Most checks passed. Review warnings above.${RESET}"
    exit 0
else
    echo -e "${RED}✗ Multiple checks failed. Review errors above.${RESET}"
    exit 1
fi
