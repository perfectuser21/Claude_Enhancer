#!/usr/bin/env bash
# generate_coverage.sh - Generate test coverage report for shell scripts
# Uses kcov for bash code coverage analysis

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Configuration
COVERAGE_DIR="${PROJECT_ROOT}/test/coverage"
SOURCE_DIR="${PROJECT_ROOT}/.workflow/cli/lib"
MIN_COVERAGE=80

echo -e "${BLUE}=====================================${RESET}"
echo -e "${BLUE}CE CLI Coverage Report Generator${RESET}"
echo -e "${BLUE}=====================================${RESET}"
echo ""

# Check for coverage tools
COVERAGE_TOOL=""

if command -v kcov &>/dev/null; then
    COVERAGE_TOOL="kcov"
    echo -e "${GREEN}✓ Found kcov${RESET}"
elif command -v shcov &>/dev/null; then
    COVERAGE_TOOL="shcov"
    echo -e "${GREEN}✓ Found shcov${RESET}"
else
    echo -e "${YELLOW}⚠ No coverage tool found${RESET}"
    echo ""
    echo "Install kcov for coverage analysis:"
    echo "  - Ubuntu/Debian: sudo apt install kcov"
    echo "  - macOS: brew install kcov"
    echo ""
    echo "Generating manual coverage report..."
    COVERAGE_TOOL="manual"
fi

echo ""

# Prepare coverage directory
mkdir -p "${COVERAGE_DIR}"
rm -rf "${COVERAGE_DIR}"/*

if [[ "${COVERAGE_TOOL}" == "kcov" ]]; then
    echo -e "${BLUE}Running tests with kcov...${RESET}"

    # Run tests with kcov
    kcov \
        --include-path="${SOURCE_DIR}" \
        --exclude-pattern="/test/" \
        "${COVERAGE_DIR}" \
        "${PROJECT_ROOT}/test/run_unit_tests.sh"

    # Generate summary
    echo ""
    echo -e "${BLUE}Coverage Summary:${RESET}"
    if [[ -f "${COVERAGE_DIR}/index.html" ]]; then
        echo "HTML report: ${COVERAGE_DIR}/index.html"
    fi

elif [[ "${COVERAGE_TOOL}" == "manual" ]]; then
    echo -e "${BLUE}Generating manual coverage report...${RESET}"

    # Count total functions and tested functions
    TOTAL_FUNCTIONS=0
    TESTED_FUNCTIONS=0

    # Find all library files
    mapfile -t LIB_FILES < <(find "${SOURCE_DIR}" -name "*.sh" | sort)

    # Create coverage report
    REPORT_FILE="${COVERAGE_DIR}/coverage_report.md"
    cat > "${REPORT_FILE}" <<EOF
# CE CLI Unit Test Coverage Report

**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Summary

| Metric | Value |
|--------|-------|
EOF

    for lib_file in "${LIB_FILES[@]}"; do
        lib_name=$(basename "${lib_file}" .sh)

        # Count functions in library
        func_count=$(grep -cE '^\s*[a-z_]+\(\)\s*\{' "${lib_file}" || echo "0")
        TOTAL_FUNCTIONS=$((TOTAL_FUNCTIONS + func_count))

        # Check for corresponding test file
        test_file="${PROJECT_ROOT}/test/unit/test_${lib_name}.bats"

        if [[ -f "${test_file}" ]]; then
            # Count test cases
            test_count=$(grep -cE '^@test' "${test_file}" || echo "0")
            TESTED_FUNCTIONS=$((TESTED_FUNCTIONS + test_count))

            cat >> "${REPORT_FILE}" <<EOF
| ${lib_name} | ${test_count}/${func_count} tests |
EOF
        else
            cat >> "${REPORT_FILE}" <<EOF
| ${lib_name} | ⚠ No tests |
EOF
        fi
    done

    # Calculate coverage percentage
    if [[ ${TOTAL_FUNCTIONS} -gt 0 ]]; then
        COVERAGE_PCT=$((TESTED_FUNCTIONS * 100 / TOTAL_FUNCTIONS))
    else
        COVERAGE_PCT=0
    fi

    # Add summary
    sed -i "/## Summary/a| **Total Functions** | ${TOTAL_FUNCTIONS} |\n| **Test Cases** | ${TESTED_FUNCTIONS} |\n| **Estimated Coverage** | ${COVERAGE_PCT}% |" "${REPORT_FILE}"

    # Add recommendations
    cat >> "${REPORT_FILE}" <<EOF

## Coverage Status

EOF

    if [[ ${COVERAGE_PCT} -ge ${MIN_COVERAGE} ]]; then
        cat >> "${REPORT_FILE}" <<EOF
✅ **PASSED** - Coverage meets minimum threshold of ${MIN_COVERAGE}%

EOF
    else
        cat >> "${REPORT_FILE}" <<EOF
❌ **FAILED** - Coverage below minimum threshold of ${MIN_COVERAGE}%

Need to add $((MIN_COVERAGE - COVERAGE_PCT))% more coverage.

EOF
    fi

    cat >> "${REPORT_FILE}" <<EOF
## Recommendations

1. Achieve at least ${MIN_COVERAGE}% code coverage
2. Test all public functions
3. Include edge cases and error scenarios
4. Mock external dependencies
5. Test security validations

## Test File Status

EOF

    for lib_file in "${LIB_FILES[@]}"; do
        lib_name=$(basename "${lib_file}" .sh)
        test_file="${PROJECT_ROOT}/test/unit/test_${lib_name}.bats"

        if [[ -f "${test_file}" ]]; then
            echo "- ✅ ${lib_name} - Test file exists" >> "${REPORT_FILE}"
        else
            echo "- ❌ ${lib_name} - **Missing test file**" >> "${REPORT_FILE}"
        fi
    done

    echo ""
    echo -e "${BLUE}Coverage Report:${RESET}"
    echo "  File: ${REPORT_FILE}"
    echo "  Estimated Coverage: ${COVERAGE_PCT}%"
    echo "  Test Cases: ${TESTED_FUNCTIONS}"
    echo "  Total Functions: ${TOTAL_FUNCTIONS}"
    echo ""

    if [[ ${COVERAGE_PCT} -ge ${MIN_COVERAGE} ]]; then
        echo -e "${GREEN}✓ Coverage meets minimum threshold (${MIN_COVERAGE}%)${RESET}"
        exit 0
    else
        echo -e "${RED}✗ Coverage below minimum threshold (${MIN_COVERAGE}%)${RESET}"
        echo -e "${YELLOW}Need $((MIN_COVERAGE - COVERAGE_PCT))% more coverage${RESET}"
        exit 1
    fi
fi
