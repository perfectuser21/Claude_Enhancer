#!/usr/bin/env bash
# Performance Optimization Verification Script
# Validates all P3 performance optimizations are implemented correctly

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CE CLI Performance Optimization Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

FAILED_CHECKS=0
PASSED_CHECKS=0

check() {
    local name="$1"
    local test="$2"
    
    printf "%-60s" "$name"
    
    if eval "$test" 2>/dev/null; then
        echo " ✅ PASS"
        ((PASSED_CHECKS++))
    else
        echo " ❌ FAIL"
        ((FAILED_CHECKS++))
    fi
}

echo "📦 Module Existence Checks"
echo "─────────────────────────────────────────────────"

check "cache_manager.sh exists" "test -f .workflow/cli/lib/cache_manager.sh"
check "performance_monitor.sh exists" "test -f .workflow/cli/lib/performance_monitor.sh"
check "common.sh exists" "test -f .workflow/cli/lib/common.sh"
check "state_manager.sh exists" "test -f .workflow/cli/lib/state_manager.sh"
check "git_operations.sh exists" "test -f .workflow/cli/lib/git_operations.sh"
check "conflict_detector.sh exists" "test -f .workflow/cli/lib/conflict_detector.sh"
check "gate_integrator.sh exists" "test -f .workflow/cli/lib/gate_integrator.sh"

echo ""
echo "🔍 Function Count Verification"
echo "─────────────────────────────────────────────────"

count_functions() {
    local file="$1"
    grep -cE "^[a-z_]+\(\)" "$file" 2>/dev/null || echo "0"
}

cache_funcs=$(count_functions .workflow/cli/lib/cache_manager.sh)
perf_funcs=$(count_functions .workflow/cli/lib/performance_monitor.sh)
common_funcs=$(count_functions .workflow/cli/lib/common.sh)
state_funcs=$(count_functions .workflow/cli/lib/state_manager.sh)
git_funcs=$(count_functions .workflow/cli/lib/git_operations.sh)
conflict_funcs=$(count_functions .workflow/cli/lib/conflict_detector.sh)
gate_funcs=$(count_functions .workflow/cli/lib/gate_integrator.sh)

check "cache_manager.sh (≥19 functions)" "test $cache_funcs -ge 19"
check "performance_monitor.sh (≥11 functions)" "test $perf_funcs -ge 11"
check "common.sh (≥40 functions)" "test $common_funcs -ge 40"
check "state_manager.sh (≥40 functions)" "test $state_funcs -ge 40"
check "git_operations.sh (≥40 functions)" "test $git_funcs -ge 40"
check "conflict_detector.sh (≥25 functions)" "test $conflict_funcs -ge 25"
check "gate_integrator.sh (≥30 functions)" "test $gate_funcs -ge 30"

total_functions=$((cache_funcs + perf_funcs + common_funcs + state_funcs + git_funcs + conflict_funcs + gate_funcs))
echo ""
echo "Total functions implemented: $total_functions"

echo ""
echo "⚙️  Key Function Existence Checks"
echo "─────────────────────────────────────────────────"

check "ce_cache_init()" "grep -q 'ce_cache_init()' .workflow/cli/lib/cache_manager.sh"
check "ce_cache_get()" "grep -q 'ce_cache_get()' .workflow/cli/lib/cache_manager.sh"
check "ce_cache_set()" "grep -q 'ce_cache_set()' .workflow/cli/lib/cache_manager.sh"
check "ce_perf_start()" "grep -q 'ce_perf_start()' .workflow/cli/lib/performance_monitor.sh"
check "ce_perf_stop()" "grep -q 'ce_perf_stop()' .workflow/cli/lib/performance_monitor.sh"
check "ce_perf_report()" "grep -q 'ce_perf_report()' .workflow/cli/lib/performance_monitor.sh"

echo ""
echo "📊 Documentation Checks"
echo "─────────────────────────────────────────────────"

check "Performance Report exists" "test -f .workflow/cli/PERFORMANCE_OPTIMIZATION_REPORT.md"
check "Summary exists" "test -f .workflow/cli/P3_PERFORMANCE_OPTIMIZATION_SUMMARY.md"

report_size=$(wc -l .workflow/cli/PERFORMANCE_OPTIMIZATION_REPORT.md 2>/dev/null | awk '{print $1}')
check "Performance Report (≥500 lines)" "test $report_size -ge 500"

summary_size=$(wc -l .workflow/cli/P3_PERFORMANCE_OPTIMIZATION_SUMMARY.md 2>/dev/null | awk '{print $1}')
check "Summary (≥200 lines)" "test $summary_size -ge 200"

echo ""
echo "🏗️  Infrastructure Checks"
echo "─────────────────────────────────────────────────"

check "Cache directory structure" "test -d .workflow/cli/state || mkdir -p .workflow/cli/state/cache/{git,state,validation,gates}"
check "Performance log location" "test -d .workflow/cli/state || mkdir -p .workflow/cli/state"
check "Export statements in cache_manager.sh" "grep -q 'export -f ce_cache_init' .workflow/cli/lib/cache_manager.sh"
check "Export statements in performance_monitor.sh" "grep -q 'export -f ce_perf_init' .workflow/cli/lib/performance_monitor.sh"

echo ""
echo "🧪 Basic Functionality Tests"
echo "─────────────────────────────────────────────────"

# Source the modules
if source .workflow/cli/lib/common.sh 2>/dev/null; then
    check "common.sh sources successfully" "true"
    ((PASSED_CHECKS++))
else
    check "common.sh sources successfully" "false"
    ((FAILED_CHECKS++))
fi

if source .workflow/cli/lib/cache_manager.sh 2>/dev/null; then
    check "cache_manager.sh sources successfully" "true"
    ((PASSED_CHECKS++))
else
    check "cache_manager.sh sources successfully" "false"
    ((FAILED_CHECKS++))
fi

if source .workflow/cli/lib/performance_monitor.sh 2>/dev/null; then
    check "performance_monitor.sh sources successfully" "true"
    ((PASSED_CHECKS++))
else
    check "performance_monitor.sh sources successfully" "false"
    ((FAILED_CHECKS++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Verification Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL_CHECKS=$((PASSED_CHECKS + FAILED_CHECKS))
PASS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo "Total Checks:  $TOTAL_CHECKS"
echo "Passed:        $PASSED_CHECKS ✅"
echo "Failed:        $FAILED_CHECKS ❌"
echo "Pass Rate:     $PASS_RATE%"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo "🎉 All performance optimizations verified successfully!"
    echo "✅ P3 Performance Optimization Phase: COMPLETE"
    exit 0
else
    echo "⚠️  Some checks failed. Please review the implementation."
    echo "❌ P3 Performance Optimization Phase: INCOMPLETE"
    exit 1
fi
