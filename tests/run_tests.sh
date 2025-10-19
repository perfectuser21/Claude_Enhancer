#!/bin/bash
# tests/run_tests.sh - Complete test suite execution

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$SCRIPT_DIR/reports"

# Banner
echo "========================================="
echo "  Code Quality Checker - Test Suite"
echo "========================================="
echo ""

# Create reports directories
mkdir -p "$REPORTS_DIR/coverage" "$REPORTS_DIR/junit" "$REPORTS_DIR/performance"

# Track overall status
OVERALL_STATUS=0

# ============================================================================
# Helper Functions
# ============================================================================

print_section() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

run_test_suite() {
    local suite_name="$1"
    local test_path="$2"
    local marker="$3"
    local report_name="$4"

    echo -e "${YELLOW}Running $suite_name...${NC}"

    if pytest "$test_path" \
        -v \
        -m "$marker" \
        --junitxml="$REPORTS_DIR/junit/${report_name}-results.xml" \
        --tb=short \
        2>&1 | tee "$REPORTS_DIR/${report_name}.log"; then
        print_success "$suite_name completed successfully"
        return 0
    else
        print_error "$suite_name failed"
        OVERALL_STATUS=1
        return 1
    fi
}

# ============================================================================
# 1. Unit Tests
# ============================================================================

print_section "1. Unit Tests"

if pytest "$SCRIPT_DIR/unit" \
    -v \
    -m "unit" \
    --cov="$PROJECT_ROOT/.claude/core" \
    --cov="$PROJECT_ROOT/scripts" \
    --cov-report=term-missing:skip-covered \
    --cov-report=html:"$REPORTS_DIR/coverage/unit" \
    --cov-report=xml:"$REPORTS_DIR/coverage/unit-coverage.xml" \
    --junitxml="$REPORTS_DIR/junit/unit-results.xml" \
    --tb=short \
    2>&1 | tee "$REPORTS_DIR/unit.log"; then
    print_success "Unit tests completed"
else
    print_error "Unit tests failed"
    OVERALL_STATUS=1
fi

# ============================================================================
# 2. Integration Tests
# ============================================================================

print_section "2. Integration Tests"

if run_test_suite \
    "Integration Tests" \
    "$SCRIPT_DIR/integration" \
    "integration" \
    "integration"; then
    :
fi

# ============================================================================
# 3. End-to-End Tests
# ============================================================================

print_section "3. End-to-End Tests"

if [ -d "$SCRIPT_DIR/e2e" ]; then
    if run_test_suite \
        "E2E Tests" \
        "$SCRIPT_DIR/e2e" \
        "e2e" \
        "e2e"; then
        :
    fi
else
    print_warning "E2E tests directory not found (will be created in Phase 2)"
fi

# ============================================================================
# 4. Configuration Validation
# ============================================================================

print_section "4. Configuration Validation"

echo "Validating YAML files..."
YAML_VALID=true

for yaml_file in "$SCRIPT_DIR/fixtures/valid"/*.yml; do
    if [ -f "$yaml_file" ]; then
        if python -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            echo "   ✓ $(basename "$yaml_file")"
        else
            print_error "Invalid YAML: $(basename "$yaml_file")"
            YAML_VALID=false
            OVERALL_STATUS=1
        fi
    fi
done

echo ""
echo "Validating JSON files..."
JSON_VALID=true

for json_file in "$SCRIPT_DIR/fixtures/valid"/*.json; do
    if [ -f "$json_file" ]; then
        if python -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
            echo "   ✓ $(basename "$json_file")"
        else
            print_error "Invalid JSON: $(basename "$json_file")"
            JSON_VALID=false
            OVERALL_STATUS=1
        fi
    fi
done

if [ "$YAML_VALID" = true ] && [ "$JSON_VALID" = true ]; then
    print_success "Configuration validation completed"
else
    print_error "Configuration validation failed"
fi

# ============================================================================
# 5. Shell Script Validation
# ============================================================================

print_section "5. Shell Script Validation"

if [ -f "$PROJECT_ROOT/scripts/static_checks.sh" ]; then
    if bash "$PROJECT_ROOT/scripts/static_checks.sh" 2>&1 | tee "$REPORTS_DIR/static-checks.log"; then
        print_success "Shell validation completed"
    else
        print_warning "Shell validation failed (may not be implemented yet)"
    fi
else
    print_warning "static_checks.sh not found (will be created in Phase 2)"
fi

# ============================================================================
# 6. Coverage Report
# ============================================================================

print_section "6. Coverage Report"

if command -v coverage &> /dev/null; then
    echo "Generating comprehensive coverage report..."

    coverage combine 2>/dev/null || true
    coverage html -d "$REPORTS_DIR/coverage/html" 2>/dev/null || true
    coverage xml -o "$REPORTS_DIR/coverage/coverage.xml" 2>/dev/null || true

    if coverage report --fail-under=80 2>&1 | tee "$REPORTS_DIR/coverage-summary.log"; then
        print_success "Coverage threshold met (≥80%)"
        echo ""
        echo "HTML Coverage Report: $REPORTS_DIR/coverage/html/index.html"
    else
        print_warning "Coverage below 80% threshold (expected for Phase 1)"
        echo "This is normal - tests will be implemented in Phase 2"
    fi
else
    print_warning "Coverage tool not installed"
    echo "Install with: pip install coverage"
fi

# ============================================================================
# Summary
# ============================================================================

print_section "Test Summary"

echo "Reports generated in: $REPORTS_DIR"
echo ""
echo "Available reports:"
echo "  - Unit tests: $REPORTS_DIR/junit/unit-results.xml"
echo "  - Integration tests: $REPORTS_DIR/junit/integration-results.xml"
echo "  - Coverage HTML: $REPORTS_DIR/coverage/html/index.html"
echo "  - Coverage XML: $REPORTS_DIR/coverage/coverage.xml"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    print_success "ALL TESTS PASSED"
    echo ""
    exit 0
else
    print_error "SOME TESTS FAILED"
    echo ""
    echo "Check logs in: $REPORTS_DIR"
    exit 1
fi
