#!/usr/bin/env bash
# regression_check.sh - Performance regression detection
# Compares current performance against baseline
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="${PROJECT_ROOT}/test/performance"
BASELINE_FILE="${TEST_DIR}/baseline.json"
CURRENT_FILE="${TEST_DIR}/results/current_benchmark.json"
REGRESSION_THRESHOLD=10  # 10% slower is considered a regression

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Performance Regression Check${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# Check if baseline exists
# ============================================================================

if [[ ! -f "${BASELINE_FILE}" ]]; then
    echo -e "${YELLOW}⚠ No baseline found, creating initial baseline...${NC}"
    echo ""

    # Run benchmark to create baseline
    bash "${TEST_DIR}/benchmark_commands.sh"

    echo ""
    echo -e "${GREEN}✓ Baseline created: ${BASELINE_FILE}${NC}"
    exit 0
fi

# ============================================================================
# Run current benchmarks
# ============================================================================

echo "Running current benchmarks..."
echo ""

# Run benchmarks and save to current file
bash "${TEST_DIR}/benchmark_commands.sh"

# The benchmark script saves to baseline.json, so we copy it to current
cp "${BASELINE_FILE}" "${CURRENT_FILE}"

# Restore original baseline (backup approach)
if [[ -f "${BASELINE_FILE}.backup" ]]; then
    mv "${BASELINE_FILE}.backup" "${BASELINE_FILE}"
else
    echo -e "${YELLOW}⚠ No baseline backup found, using current as baseline${NC}"
fi

# ============================================================================
# Compare baseline vs current
# ============================================================================

echo ""
echo "Comparing against baseline..."
echo ""

# Parse JSON files and compare
declare -A baseline_times
declare -A current_times

# Read baseline
if command -v jq &>/dev/null; then
    while IFS='=' read -r key value; do
        baseline_times["${key}"]="${value}"
    done < <(jq -r '.results | to_entries | .[] | "\(.key)=\(.value)"' "${BASELINE_FILE}" 2>/dev/null)
else
    echo -e "${RED}ERROR: jq not installed, cannot parse JSON${NC}"
    echo "Install: sudo apt-get install jq"
    exit 1
fi

# Read current
while IFS='=' read -r key value; do
    current_times["${key}"]="${value}"
done < <(jq -r '.results | to_entries | .[] | "\(.key)=\(.value)"' "${CURRENT_FILE}" 2>/dev/null)

# ============================================================================
# Analyze regressions
# ============================================================================

echo -e "${BLUE}Regression Analysis:${NC}"
echo ""

printf "%-30s %15s %15s %15s %10s\n" "Command" "Baseline (ms)" "Current (ms)" "Change (%)" "Status"
echo "──────────────────────────────────────────────────────────────────────────────────"

declare -A regressions
declare -A improvements

for cmd in "${!baseline_times[@]}"; do
    local baseline="${baseline_times[$cmd]%.*}"
    local current="${current_times[$cmd]:-0}"
    current="${current%.*}"

    if [[ ${current} == "0" ]]; then
        echo -e "${YELLOW}⚠ ${cmd} not found in current results${NC}"
        continue
    fi

    # Calculate change percentage
    local change=0
    if [[ ${baseline} -gt 0 ]]; then
        change=$(( (current - baseline) * 100 / baseline ))
    fi

    local status="="
    local status_color="${NC}"

    if (( change > REGRESSION_THRESHOLD )); then
        status="✗ REGRESSION"
        status_color="${RED}"
        regressions["${cmd}"]="${change}"
    elif (( change < -REGRESSION_THRESHOLD )); then
        status="✓ IMPROVEMENT"
        status_color="${GREEN}"
        improvements["${cmd}"]="${change}"
    else
        status="✓ STABLE"
        status_color="${GREEN}"
    fi

    local change_str
    if (( change >= 0 )); then
        change_str="+${change}"
    else
        change_str="${change}"
    fi

    printf "%-30s %15s %15s " "${cmd}" "${baseline}" "${current}"
    printf "%15s " "${change_str}%"
    echo -e "${status_color}${status}${NC}"
done

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}Summary:${NC}"
echo ""

local total_tests=${#baseline_times[@]}
local regression_count=${#regressions[@]}
local improvement_count=${#improvements[@]}
local stable_count=$((total_tests - regression_count - improvement_count))

echo "  Total tests: ${total_tests}"
echo -e "  ${GREEN}Improvements: ${improvement_count}${NC}"
echo -e "  ${GREEN}Stable: ${stable_count}${NC}"
echo -e "  ${RED}Regressions: ${regression_count}${NC}"

echo ""

if [[ ${regression_count} -gt 0 ]]; then
    echo -e "${RED}❌ Performance regressions detected!${NC}"
    echo ""
    echo "Regressions:"

    for cmd in "${!regressions[@]}"; do
        local change="${regressions[$cmd]}"
        echo -e "  ${RED}✗ ${cmd}: ${change}% slower${NC}"
    done

    echo ""
    echo "Action required: Investigate and fix performance regressions"
    exit 1
else
    echo -e "${GREEN}✅ No performance regressions detected!${NC}"

    if [[ ${improvement_count} -gt 0 ]]; then
        echo ""
        echo -e "${GREEN}Improvements detected:${NC}"

        for cmd in "${!improvements[@]}"; do
            local change="${improvements[$cmd]}"
            local improvement=$((change * -1))
            echo -e "  ${GREEN}✓ ${cmd}: ${improvement}% faster${NC}"
        done

        echo ""
        echo "Consider updating baseline with these improvements:"
        echo "  mv ${CURRENT_FILE} ${BASELINE_FILE}"
    fi
fi

echo ""

# ============================================================================
# Trend analysis
# ============================================================================

if [[ -d "${TEST_DIR}/results/history" ]]; then
    echo -e "${BLUE}Trend Analysis:${NC}"
    echo ""

    # Archive current results
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)

    mkdir -p "${TEST_DIR}/results/history"
    cp "${CURRENT_FILE}" "${TEST_DIR}/results/history/benchmark_${timestamp}.json"

    # Count history files
    local history_count
    history_count=$(ls -1 "${TEST_DIR}/results/history"/benchmark_*.json 2>/dev/null | wc -l)

    echo "  Historical benchmarks: ${history_count}"

    if [[ ${history_count} -gt 1 ]]; then
        echo "  Trend data available"
        echo ""
        echo "  To generate trend charts, run:"
        echo "    bash test/performance/generate_perf_report.sh --charts"
    fi

    echo ""
fi

# Save comparison report
cat > "${TEST_DIR}/results/regression_report.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "baseline_file": "${BASELINE_FILE}",
  "current_file": "${CURRENT_FILE}",
  "threshold_percent": ${REGRESSION_THRESHOLD},
  "total_tests": ${total_tests},
  "regressions": ${regression_count},
  "improvements": ${improvement_count},
  "stable": ${stable_count},
  "status": "$(if [[ ${regression_count} -gt 0 ]]; then echo "FAILED"; else echo "PASSED"; fi)"
}
EOF

echo "Regression report saved to: ${TEST_DIR}/results/regression_report.json"
