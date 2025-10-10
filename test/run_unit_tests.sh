#!/usr/bin/env bash
# run_unit_tests.sh - Execute all unit tests with bats-core
# Usage: ./test/run_unit_tests.sh [options]
#   -v, --verbose    Verbose output
#   -f, --filter     Run specific test file
#   -t, --tap        Output in TAP format
#   -j, --jobs       Number of parallel jobs

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
VERBOSE=false
TAP_OUTPUT=false
FILTER=""
JOBS=4

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--tap)
            TAP_OUTPUT=true
            shift
            ;;
        -f|--filter)
            FILTER="$2"
            shift 2
            ;;
        -j|--jobs)
            JOBS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose      Verbose output"
            echo "  -f, --filter FILE  Run specific test file"
            echo "  -t, --tap          Output in TAP format"
            echo "  -j, --jobs N       Number of parallel jobs (default: 4)"
            echo "  -h, --help         Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check for bats
if ! command -v bats &>/dev/null; then
    echo -e "${RED}Error: bats-core is not installed${RESET}"
    echo ""
    echo "Install bats-core:"
    echo "  - Ubuntu/Debian: sudo apt install bats"
    echo "  - macOS: brew install bats-core"
    echo "  - Manual: git clone https://github.com/bats-core/bats-core.git && cd bats-core && sudo ./install.sh /usr/local"
    exit 1
fi

echo -e "${BLUE}=====================================${RESET}"
echo -e "${BLUE}CE CLI Unit Test Runner${RESET}"
echo -e "${BLUE}=====================================${RESET}"
echo ""

# Prepare test environment
echo -e "${BLUE}Preparing test environment...${RESET}"
mkdir -p "${PROJECT_ROOT}/test/.tmp"
mkdir -p "${PROJECT_ROOT}/test/reports"

# Find test files
if [[ -n "${FILTER}" ]]; then
    if [[ -f "${PROJECT_ROOT}/test/unit/${FILTER}" ]]; then
        TEST_FILES=("${PROJECT_ROOT}/test/unit/${FILTER}")
    elif [[ -f "${PROJECT_ROOT}/test/unit/test_${FILTER}.bats" ]]; then
        TEST_FILES=("${PROJECT_ROOT}/test/unit/test_${FILTER}.bats")
    else
        echo -e "${RED}Error: Test file not found: ${FILTER}${RESET}"
        exit 1
    fi
else
    mapfile -t TEST_FILES < <(find "${PROJECT_ROOT}/test/unit" -name "test_*.bats" | sort)
fi

# Check if we have test files
if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
    echo -e "${RED}Error: No test files found${RESET}"
    exit 1
fi

echo -e "${BLUE}Found ${#TEST_FILES[@]} test file(s)${RESET}"
echo ""

# Build bats command
BATS_CMD=(bats)

if [[ "${VERBOSE}" == "true" ]]; then
    BATS_CMD+=(--verbose-run)
fi

if [[ "${TAP_OUTPUT}" == "true" ]]; then
    BATS_CMD+=(--tap)
else
    BATS_CMD+=(--pretty)
fi

BATS_CMD+=(--jobs "${JOBS}")
BATS_CMD+=(--timing)

# Run tests
echo -e "${BLUE}Running tests...${RESET}"
echo ""

START_TIME=$(date +%s)

# Execute tests
if "${BATS_CMD[@]}" "${TEST_FILES[@]}"; then
    TEST_RESULT=0
    RESULT_TEXT="${GREEN}PASSED${RESET}"
else
    TEST_RESULT=1
    RESULT_TEXT="${RED}FAILED${RESET}"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Summary
echo ""
echo -e "${BLUE}=====================================${RESET}"
echo -e "${BLUE}Test Summary${RESET}"
echo -e "${BLUE}=====================================${RESET}"
echo -e "Result: ${RESULT_TEXT}"
echo -e "Duration: ${DURATION}s"
echo -e "Test files: ${#TEST_FILES[@]}"
echo ""

# Cleanup
if [[ "${TEST_RESULT}" -eq 0 ]]; then
    echo -e "${GREEN}✓ All tests passed!${RESET}"
else
    echo -e "${RED}✗ Some tests failed${RESET}"
    echo ""
    echo "Run with --verbose for detailed output"
fi

# Clean up temporary files
rm -rf "${PROJECT_ROOT}/test/.tmp"/*

exit ${TEST_RESULT}
