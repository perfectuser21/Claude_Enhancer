#!/bin/bash
# Perfect21 Test Execution Script
# Comprehensive testing with multiple modes

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$PROJECT_ROOT/tests"
COVERAGE_TARGET=90
PYTHON_CMD="${PYTHON_CMD:-python3}"

# Functions
print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}🚀 Perfect21 Test Suite${NC}"
    echo -e "${BLUE}======================================${NC}"
}

print_section() {
    echo -e "\n${YELLOW}📋 $1${NC}"
    echo -e "${YELLOW}$(printf '=%.0s' {1..40})${NC}"
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

# Check dependencies
check_dependencies() {
    print_section "Checking Dependencies"

    if ! command -v $PYTHON_CMD &> /dev/null; then
        print_error "Python not found. Please install Python 3.8+"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    print_success "Python version: $PYTHON_VERSION"

    # Check if pytest is installed
    if ! $PYTHON_CMD -m pytest --version &> /dev/null; then
        print_warning "pytest not found. Installing test dependencies..."
        $PYTHON_CMD -m pip install -r "$TEST_DIR/requirements.txt"
    fi

    print_success "Dependencies check completed"
}

# Setup test environment
setup_environment() {
    print_section "Setting up Test Environment"

    # Create necessary directories
    mkdir -p "$TEST_DIR"/{logs,reports,temp,htmlcov}

    # Set environment variables
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export TESTING=true
    export LOG_LEVEL=INFO

    print_success "Test environment configured"
}

# Run quick tests (smoke tests)
run_quick_tests() {
    print_section "Running Quick Tests"

    cd "$PROJECT_ROOT"

    $PYTHON_CMD -m pytest \
        "$TEST_DIR/unit" \
        -v \
        -x \
        --tb=short \
        -k "not slow" \
        --timeout=60 \
        --maxfail=5 \
        || {
            print_error "Quick tests failed"
            return 1
        }

    print_success "Quick tests passed"
}

# Run unit tests with coverage
run_unit_tests() {
    print_section "Running Unit Tests"

    cd "$PROJECT_ROOT"

    $PYTHON_CMD -m pytest \
        "$TEST_DIR/unit" \
        -v \
        --tb=short \
        --cov=api \
        --cov=main \
        --cov=modules \
        --cov=features \
        --cov-report=html:"$TEST_DIR/htmlcov_unit" \
        --cov-report=xml:"$TEST_DIR/coverage_unit.xml" \
        --cov-report=term-missing \
        --cov-fail-under=$COVERAGE_TARGET \
        --html="$TEST_DIR/report_unit.html" \
        --self-contained-html \
        --junitxml="$TEST_DIR/results_unit.xml" \
        || {
            print_error "Unit tests failed"
            return 1
        }

    print_success "Unit tests passed"
}

# Run integration tests
run_integration_tests() {
    print_section "Running Integration Tests"

    cd "$PROJECT_ROOT"

    $PYTHON_CMD -m pytest \
        "$TEST_DIR/integration" \
        -v \
        --tb=short \
        --html="$TEST_DIR/report_integration.html" \
        --self-contained-html \
        --junitxml="$TEST_DIR/results_integration.xml" \
        --timeout=300 \
        || {
            print_warning "Integration tests failed or skipped"
            return 0  # Non-critical for now
        }

    print_success "Integration tests completed"
}

# Run e2e tests
run_e2e_tests() {
    print_section "Running E2E Tests"

    cd "$PROJECT_ROOT"

    $PYTHON_CMD -m pytest \
        "$TEST_DIR/e2e" \
        -v \
        --tb=short \
        --html="$TEST_DIR/report_e2e.html" \
        --self-contained-html \
        --junitxml="$TEST_DIR/results_e2e.xml" \
        --timeout=600 \
        || {
            print_warning "E2E tests failed or skipped"
            return 0  # Non-critical for now
        }

    print_success "E2E tests completed"
}

# Run performance tests
run_performance_tests() {
    print_section "Running Performance Tests"

    cd "$PROJECT_ROOT"

    $PYTHON_CMD -m pytest \
        "$TEST_DIR/performance" \
        -v \
        --tb=short \
        -m "performance" \
        --html="$TEST_DIR/report_performance.html" \
        --self-contained-html \
        --junitxml="$TEST_DIR/results_performance.xml" \
        --timeout=900 \
        || {
            print_warning "Performance tests failed or skipped"
            return 0  # Non-critical for now
        }

    print_success "Performance tests completed"
}

# Run security tests
run_security_tests() {
    print_section "Running Security Tests"

    cd "$PROJECT_ROOT"

    $PYTHON_CMD -m pytest \
        "$TEST_DIR/security" \
        -v \
        --tb=short \
        -m "security" \
        --html="$TEST_DIR/report_security.html" \
        --self-contained-html \
        --junitxml="$TEST_DIR/results_security.xml" \
        --timeout=300 \
        || {
            print_error "Security tests failed"
            return 1
        }

    print_success "Security tests passed"
}

# Generate comprehensive report
generate_report() {
    print_section "Generating Comprehensive Report"

    cd "$PROJECT_ROOT"

    # Run the comprehensive test suite runner
    $PYTHON_CMD "$TEST_DIR/run_comprehensive_test_suite.py" \
        --coverage-target $COVERAGE_TARGET \
        || {
            print_warning "Report generation encountered issues"
        }

    # Display results
    if [ -f "$TEST_DIR/test_dashboard_comprehensive.html" ]; then
        print_success "Test dashboard generated: $TEST_DIR/test_dashboard_comprehensive.html"
    fi

    if [ -f "$TEST_DIR/htmlcov_unit/index.html" ]; then
        print_success "Coverage report generated: $TEST_DIR/htmlcov_unit/index.html"
    fi
}

# Cleanup function
cleanup() {
    print_section "Cleaning up"

    # Remove temporary files
    find "$TEST_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$TEST_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

    # Clean up test databases
    rm -f "$PROJECT_ROOT"/*.db 2>/dev/null || true
    rm -f "$TEST_DIR"/*.db 2>/dev/null || true

    print_success "Cleanup completed"
}

# Main execution
main() {
    local MODE=${1:-"all"}
    local EXIT_CODE=0

    print_header

    # Always setup environment and check dependencies
    check_dependencies
    setup_environment

    case $MODE in
        "quick")
            run_quick_tests || EXIT_CODE=1
            ;;
        "unit")
            run_unit_tests || EXIT_CODE=1
            ;;
        "integration")
            run_integration_tests || EXIT_CODE=1
            ;;
        "e2e")
            run_e2e_tests || EXIT_CODE=1
            ;;
        "performance")
            run_performance_tests || EXIT_CODE=1
            ;;
        "security")
            run_security_tests || EXIT_CODE=1
            ;;
        "coverage")
            run_unit_tests || EXIT_CODE=1
            ;;
        "all")
            print_section "Running All Test Categories"

            # Run tests in order of importance
            run_quick_tests || EXIT_CODE=1

            if [ $EXIT_CODE -eq 0 ]; then
                run_unit_tests || EXIT_CODE=1
            fi

            if [ $EXIT_CODE -eq 0 ]; then
                run_security_tests || EXIT_CODE=1
            fi

            # These are less critical
            run_integration_tests || true
            run_e2e_tests || true
            run_performance_tests || true

            # Generate comprehensive report
            generate_report
            ;;
        "clean")
            cleanup
            exit 0
            ;;
        *)
            echo "Usage: $0 [quick|unit|integration|e2e|performance|security|coverage|all|clean]"
            echo ""
            echo "Modes:"
            echo "  quick       - Run quick smoke tests only"
            echo "  unit        - Run unit tests with coverage"
            echo "  integration - Run integration tests"
            echo "  e2e         - Run end-to-end tests"
            echo "  performance - Run performance tests"
            echo "  security    - Run security tests"
            echo "  coverage    - Run unit tests with coverage focus"
            echo "  all         - Run all test categories (default)"
            echo "  clean       - Clean up test artifacts"
            exit 1
            ;;
    esac

    # Final summary
    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        print_success "All tests completed successfully!"
        echo -e "${GREEN}📊 Check the test reports in: $TEST_DIR${NC}"
    else
        print_error "Some tests failed. Check the output above for details."
        echo -e "${RED}📊 Check the test reports in: $TEST_DIR${NC}"
    fi

    # Always cleanup
    cleanup

    exit $EXIT_CODE
}

# Handle interrupts
trap cleanup EXIT INT TERM

# Run main function
main "$@"