#!/usr/bin/env bash
# validate_suite.sh - Validate performance test suite setup
# Quick smoke test to ensure all components are working
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Performance Test Suite Validation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="${PROJECT_ROOT}/test/performance"

cd "${PROJECT_ROOT}"

# Track results
declare -a checks_passed
declare -a checks_failed

# ============================================================================
# Check 1: Required files exist
# ============================================================================

echo -e "${YELLOW}[1/7] Checking required files...${NC}"

required_files=(
    "test/performance/benchmark_commands.sh"
    "test/performance/benchmark_workflows.sh"
    "test/performance/load_test.sh"
    "test/performance/cache_performance.sh"
    "test/performance/stress_test.sh"
    "test/performance/memory_profiling.sh"
    "test/performance/regression_check.sh"
    "test/run_performance_tests.sh"
    "test/generate_perf_report.sh"
    "test/performance/README.md"
    "metrics/perf_budget.yml"
)

for file in "${required_files[@]}"; do
    if [[ -f "${PROJECT_ROOT}/${file}" ]]; then
        echo -e "  ${GREEN}✓${NC} ${file}"
    else
        echo -e "  ${RED}✗${NC} ${file} - MISSING"
        checks_failed+=("File missing: ${file}")
    fi
done

checks_passed+=("Required files check")
echo ""

# ============================================================================
# Check 2: Scripts are executable
# ============================================================================

echo -e "${YELLOW}[2/7] Checking script permissions...${NC}"

for file in test/performance/*.sh test/run_performance_tests.sh test/generate_perf_report.sh; do
    if [[ -x "${file}" ]]; then
        echo -e "  ${GREEN}✓${NC} ${file} is executable"
    else
        echo -e "  ${RED}✗${NC} ${file} is not executable"
        checks_failed+=("Not executable: ${file}")
    fi
done

checks_passed+=("Script permissions check")
echo ""

# ============================================================================
# Check 3: Required tools available
# ============================================================================

echo -e "${YELLOW}[3/7] Checking required tools...${NC}"

required_tools=(
    "bash"
    "jq"
    "git"
    "python3"
)

recommended_tools=(
    "hyperfine"
    "gnuplot"
    "valgrind"
    "iostat"
)

for tool in "${required_tools[@]}"; do
    if command -v "${tool}" &>/dev/null; then
        version=$(${tool} --version 2>&1 | head -1 || echo "unknown")
        echo -e "  ${GREEN}✓${NC} ${tool} - ${version}"
    else
        echo -e "  ${RED}✗${NC} ${tool} - NOT FOUND"
        checks_failed+=("Required tool missing: ${tool}")
    fi
done

echo ""
echo "  Recommended tools (optional):"
for tool in "${recommended_tools[@]}"; do
    if command -v "${tool}" &>/dev/null; then
        echo -e "    ${GREEN}✓${NC} ${tool}"
    else
        echo -e "    ${YELLOW}○${NC} ${tool} - not installed (optional)"
    fi
done

checks_passed+=("Required tools check")
echo ""

# ============================================================================
# Check 4: CE CLI exists and works
# ============================================================================

echo -e "${YELLOW}[4/7] Checking CE CLI...${NC}"

CE_BIN="${PROJECT_ROOT}/.workflow/cli/ce"

if [[ -f "${CE_BIN}" ]]; then
    echo -e "  ${GREEN}✓${NC} CE CLI found: ${CE_BIN}"

    if [[ -x "${CE_BIN}" ]]; then
        echo -e "  ${GREEN}✓${NC} CE CLI is executable"

        # Test basic command
        if timeout 5s "${CE_BIN}" status &>/dev/null || [[ $? -eq 1 ]]; then
            echo -e "  ${GREEN}✓${NC} CE CLI responds to commands"
        else
            echo -e "  ${YELLOW}⚠${NC} CE CLI may have issues (non-zero exit)"
        fi
    else
        echo -e "  ${RED}✗${NC} CE CLI is not executable"
        checks_failed+=("CE CLI not executable")
    fi
else
    echo -e "  ${RED}✗${NC} CE CLI not found: ${CE_BIN}"
    checks_failed+=("CE CLI not found")
fi

checks_passed+=("CE CLI check")
echo ""

# ============================================================================
# Check 5: Performance budget file
# ============================================================================

echo -e "${YELLOW}[5/7] Checking performance budgets...${NC}"

BUDGET_FILE="${PROJECT_ROOT}/metrics/perf_budget.yml"

if [[ -f "${BUDGET_FILE}" ]]; then
    echo -e "  ${GREEN}✓${NC} Performance budget file exists"

    # Validate YAML syntax
    if python3 -c "import yaml; yaml.safe_load(open('${BUDGET_FILE}'))" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} YAML syntax is valid"

        # Count budgets
        budget_count
        budget_count=$(grep -c "^  - name:" "${BUDGET_FILE}" || echo "0")
        echo -e "  ${GREEN}✓${NC} Found ${budget_count} performance budgets"
    else
        echo -e "  ${RED}✗${NC} YAML syntax error"
        checks_failed+=("Invalid YAML in perf_budget.yml")
    fi
else
    echo -e "  ${RED}✗${NC} Performance budget file not found"
    checks_failed+=("Performance budget file missing")
fi

checks_passed+=("Performance budget check")
echo ""

# ============================================================================
# Check 6: Test syntax validation
# ============================================================================

echo -e "${YELLOW}[6/7] Validating test script syntax...${NC}"

for script in test/performance/*.sh; do
    if bash -n "${script}" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $(basename "${script}") - syntax OK"
    else
        echo -e "  ${RED}✗${NC} $(basename "${script}") - syntax errors"
        checks_failed+=("Syntax error in $(basename "${script}")")
    fi
done

checks_passed+=("Script syntax check")
echo ""

# ============================================================================
# Check 7: Directory structure
# ============================================================================

echo -e "${YELLOW}[7/7] Checking directory structure...${NC}"

required_dirs=(
    "test/performance"
    "test/performance/results"
    ".workflow/cli"
    ".workflow/cli/state"
    "metrics"
)

for dir in "${required_dirs[@]}"; do
    if [[ -d "${PROJECT_ROOT}/${dir}" ]]; then
        echo -e "  ${GREEN}✓${NC} ${dir}/"
    else
        echo -e "  ${YELLOW}○${NC} ${dir}/ - will be created on first run"
        mkdir -p "${PROJECT_ROOT}/${dir}"
    fi
done

checks_passed+=("Directory structure check")
echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Validation Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${GREEN}Passed checks: ${#checks_passed[@]}${NC}"

for check in "${checks_passed[@]}"; do
    echo -e "  ${GREEN}✓${NC} ${check}"
done

echo ""

if [[ ${#checks_failed[@]} -gt 0 ]]; then
    echo -e "${RED}Failed checks: ${#checks_failed[@]}${NC}"

    for check in "${checks_failed[@]}"; do
        echo -e "  ${RED}✗${NC} ${check}"
    done

    echo ""
    echo -e "${RED}❌ Validation FAILED${NC}"
    echo ""
    echo "Please fix the issues above before running performance tests."
    exit 1
else
    echo -e "${GREEN}✅ Validation PASSED${NC}"
    echo ""
    echo "Performance test suite is ready to run!"
    echo ""
    echo "Quick start:"
    echo "  bash test/run_performance_tests.sh --quick"
    echo ""
    echo "Full test suite:"
    echo "  bash test/run_performance_tests.sh"
    echo ""
    echo "Generate report:"
    echo "  bash test/generate_perf_report.sh"
fi

echo ""
