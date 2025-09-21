#!/bin/bash

##############################################################################
# Perfect21 Performance Testing Execution Script
##############################################################################
#
# This script orchestrates comprehensive performance testing including:
# - System baseline measurement
# - Load testing with multiple scenarios
# - Stress testing and spike testing
# - Performance report generation
# - Results analysis and recommendations
#
# Usage:
#   ./run_performance_tests.sh --target=staging
#   ./run_performance_tests.sh --scenario=all --users=500
#   ./run_performance_tests.sh --quick-test
#
##############################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/performance_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_RESULTS_DIR="$RESULTS_DIR/$TIMESTAMP"

# Default values
TARGET_HOST="http://localhost:8000"
SCENARIO="all"
MAX_USERS=500
TEST_DURATION=300
QUICK_TEST=false
GENERATE_REPORT=true
CLEANUP_AFTER=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Help function
show_help() {
    cat << EOF
Perfect21 Performance Testing Suite

Usage: $0 [OPTIONS]

OPTIONS:
    --target=URL           Target host URL (default: http://localhost:8000)
    --scenario=SCENARIO    Test scenario: baseline|load|stress|spike|all (default: all)
    --users=NUMBER         Maximum concurrent users (default: 500)
    --duration=SECONDS     Test duration in seconds (default: 300)
    --quick-test          Run quick tests (reduced duration and users)
    --no-report           Skip report generation
    --no-cleanup          Keep temporary files
    --help                Show this help message

SCENARIOS:
    baseline              Basic performance measurement
    load                  Normal load testing
    stress                High load stress testing
    spike                 Sudden traffic spike testing
    endurance            Long-running stability testing
    all                  Run all test scenarios

EXAMPLES:
    $0 --target=https://staging.perfect21.com --scenario=load
    $0 --quick-test --users=50
    $0 --scenario=stress --users=1000 --duration=600

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --target=*)
                TARGET_HOST="${1#*=}"
                shift
                ;;
            --scenario=*)
                SCENARIO="${1#*=}"
                shift
                ;;
            --users=*)
                MAX_USERS="${1#*=}"
                shift
                ;;
            --duration=*)
                TEST_DURATION="${1#*=}"
                shift
                ;;
            --quick-test)
                QUICK_TEST=true
                MAX_USERS=50
                TEST_DURATION=120
                shift
                ;;
            --no-report)
                GENERATE_REPORT=false
                shift
                ;;
            --no-cleanup)
                CLEANUP_AFTER=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"

    # Check if target is reachable
    if ! curl -s --connect-timeout 5 "$TARGET_HOST/health" > /dev/null 2>&1; then
        log_warning "Target host $TARGET_HOST is not reachable or health check failed"
        log_info "Continuing anyway - the service might not have a health endpoint"
    else
        log_success "Target host $TARGET_HOST is reachable"
    fi

    # Check required tools
    local tools=("python3" "curl" "jq")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done

    # Check optional tools
    if command -v "k6" &> /dev/null; then
        log_success "K6 load testing tool found"
        K6_AVAILABLE=true
    else
        log_warning "K6 not found - will use Python/Locust only"
        K6_AVAILABLE=false
    fi

    # Create results directory
    mkdir -p "$TEST_RESULTS_DIR"
    log_success "Results directory created: $TEST_RESULTS_DIR"
}

# Pre-test system check
pre_test_check() {
    log_section "Pre-Test System Check"

    # Basic connectivity test
    log_info "Testing basic connectivity..."
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$TARGET_HOST/" || echo "000")

    if [[ "$response_code" == "200" || "$response_code" == "404" ]]; then
        log_success "Basic connectivity test passed (HTTP $response_code)"
    else
        log_warning "Unexpected response code: $response_code"
    fi

    # Test authentication endpoint
    log_info "Testing authentication endpoint..."
    local auth_response=$(curl -s -X POST "$TARGET_HOST/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"invalid"}' \
        -w "%{http_code}" -o /dev/null || echo "000")

    if [[ "$auth_response" == "401" || "$auth_response" == "400" ]]; then
        log_success "Authentication endpoint is responsive"
    else
        log_warning "Authentication endpoint returned unexpected code: $auth_response"
    fi

    # Save pre-test info
    cat > "$TEST_RESULTS_DIR/test_config.json" << EOF
{
    "test_timestamp": "$TIMESTAMP",
    "target_host": "$TARGET_HOST",
    "scenario": "$SCENARIO",
    "max_users": $MAX_USERS,
    "test_duration": $TEST_DURATION,
    "quick_test": $QUICK_TEST,
    "pre_test_connectivity": "$response_code",
    "pre_test_auth": "$auth_response"
}
EOF
}

# Run baseline performance test
run_baseline_test() {
    log_section "Running Baseline Performance Test"

    local users=10
    local duration=120

    if [ "$QUICK_TEST" = true ]; then
        users=5
        duration=60
    fi

    log_info "Baseline test: $users users for ${duration}s"

    # Run Python/Locust baseline test
    cd "$PROJECT_ROOT"

    python3 load_tests/comprehensive_load_test.py \
        --scenario=baseline \
        --users=$users \
        --duration=$duration \
        --host="$TARGET_HOST" \
        > "$TEST_RESULTS_DIR/baseline_test.log" 2>&1 &

    local baseline_pid=$!

    # Monitor test progress
    local elapsed=0
    while kill -0 $baseline_pid 2>/dev/null; do
        sleep 10
        elapsed=$((elapsed + 10))
        local progress=$((elapsed * 100 / duration))
        log_info "Baseline test progress: ${progress}% (${elapsed}/${duration}s)"

        if [ $elapsed -ge $((duration + 30)) ]; then
            log_warning "Baseline test taking longer than expected, killing process"
            kill $baseline_pid 2>/dev/null || true
            break
        fi
    done

    wait $baseline_pid 2>/dev/null || true
    log_success "Baseline test completed"
}

# Run load test
run_load_test() {
    log_section "Running Load Test"

    local users=$MAX_USERS
    local duration=$TEST_DURATION

    if [ "$QUICK_TEST" = true ]; then
        users=$((MAX_USERS / 2))
        duration=$((TEST_DURATION / 2))
    fi

    log_info "Load test: $users users for ${duration}s"

    # Run with both tools if available
    if [ "$K6_AVAILABLE" = true ]; then
        log_info "Running K6 load test..."
        cd "$PROJECT_ROOT"

        K6_OPTIONS="--duration=${duration}s --vus=$users"
        k6 run $K6_OPTIONS \
            --env SCENARIO=load \
            --env BASE_URL="$TARGET_HOST" \
            load_tests/k6_performance_suite.js \
            > "$TEST_RESULTS_DIR/k6_load_test.log" 2>&1 &

        local k6_pid=$!

        # Monitor K6 test
        while kill -0 $k6_pid 2>/dev/null; do
            sleep 15
            log_info "K6 load test in progress..."
        done

        wait $k6_pid 2>/dev/null || true
        log_success "K6 load test completed"
    fi

    # Run Python/Locust load test
    log_info "Running Python load test..."
    python3 load_tests/comprehensive_load_test.py \
        --scenario=stress \
        --users=$users \
        --duration=$duration \
        --host="$TARGET_HOST" \
        > "$TEST_RESULTS_DIR/python_load_test.log" 2>&1 &

    local python_pid=$!

    # Monitor Python test
    while kill -0 $python_pid 2>/dev/null; do
        sleep 15
        log_info "Python load test in progress..."
    done

    wait $python_pid 2>/dev/null || true
    log_success "Python load test completed"
}

# Run stress test
run_stress_test() {
    log_section "Running Stress Test"

    local users=$((MAX_USERS * 2))
    local duration=$((TEST_DURATION / 2))

    if [ "$QUICK_TEST" = true ]; then
        users=$MAX_USERS
        duration=60
    fi

    log_info "Stress test: $users users for ${duration}s"

    if [ "$K6_AVAILABLE" = true ]; then
        log_info "Running K6 stress test..."
        k6 run --duration="${duration}s" --vus=$users \
            --env SCENARIO=stress \
            --env BASE_URL="$TARGET_HOST" \
            load_tests/k6_performance_suite.js \
            > "$TEST_RESULTS_DIR/k6_stress_test.log" 2>&1 &

        local k6_stress_pid=$!
        wait $k6_stress_pid 2>/dev/null || true
        log_success "K6 stress test completed"
    fi

    # Python stress test
    python3 load_tests/comprehensive_load_test.py \
        --scenario=stress \
        --users=$users \
        --duration=$duration \
        --host="$TARGET_HOST" \
        > "$TEST_RESULTS_DIR/python_stress_test.log" 2>&1 &

    local python_stress_pid=$!
    wait $python_stress_pid 2>/dev/null || true
    log_success "Python stress test completed"
}

# Run spike test
run_spike_test() {
    log_section "Running Spike Test"

    local peak_users=$((MAX_USERS * 3))
    local duration=180

    if [ "$QUICK_TEST" = true ]; then
        peak_users=$MAX_USERS
        duration=90
    fi

    log_info "Spike test: peak $peak_users users for ${duration}s"

    if [ "$K6_AVAILABLE" = true ]; then
        k6 run --duration="${duration}s" --vus=$peak_users \
            --env SCENARIO=spike \
            --env BASE_URL="$TARGET_HOST" \
            load_tests/k6_performance_suite.js \
            > "$TEST_RESULTS_DIR/k6_spike_test.log" 2>&1 &

        local spike_pid=$!
        wait $spike_pid 2>/dev/null || true
        log_success "Spike test completed"
    fi
}

# Run endurance test (only if not quick test)
run_endurance_test() {
    if [ "$QUICK_TEST" = true ]; then
        log_info "Skipping endurance test (quick test mode)"
        return
    fi

    log_section "Running Endurance Test"

    local users=$((MAX_USERS / 4))
    local duration=1800  # 30 minutes

    log_info "Endurance test: $users users for ${duration}s (30 minutes)"

    python3 load_tests/comprehensive_load_test.py \
        --scenario=endurance \
        --users=$users \
        --duration=$duration \
        --host="$TARGET_HOST" \
        > "$TEST_RESULTS_DIR/endurance_test.log" 2>&1 &

    local endurance_pid=$!

    # Monitor endurance test with periodic updates
    local elapsed=0
    while kill -0 $endurance_pid 2>/dev/null; do
        sleep 60
        elapsed=$((elapsed + 60))
        local progress=$((elapsed * 100 / duration))
        log_info "Endurance test progress: ${progress}% (${elapsed}/${duration}s)"
    done

    wait $endurance_pid 2>/dev/null || true
    log_success "Endurance test completed"
}

# Generate comprehensive performance report
generate_performance_report() {
    if [ "$GENERATE_REPORT" = false ]; then
        log_info "Skipping report generation (--no-report specified)"
        return
    fi

    log_section "Generating Performance Report"

    # Create report generation script
    cat > "$TEST_RESULTS_DIR/generate_report.py" << 'EOF'
#!/usr/bin/env python3
import json
import os
import sys
import glob
from datetime import datetime

def parse_locust_log(log_file):
    """Parse Locust log file for performance metrics"""
    if not os.path.exists(log_file):
        return None

    with open(log_file, 'r') as f:
        content = f.read()

    # Extract basic metrics (simplified parsing)
    metrics = {
        'total_requests': 0,
        'failed_requests': 0,
        'avg_response_time': 0,
        'rps': 0
    }

    # Look for summary lines
    for line in content.split('\n'):
        if 'Total:' in line and 'requests' in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part.isdigit():
                    metrics['total_requests'] = int(part)
                    break

    return metrics

def generate_html_report(results_dir):
    """Generate HTML performance report"""
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'test_results': {},
        'summary': {}
    }

    # Parse all log files
    log_files = glob.glob(os.path.join(results_dir, '*.log'))
    for log_file in log_files:
        test_name = os.path.basename(log_file).replace('.log', '')
        metrics = parse_locust_log(log_file)
        if metrics:
            report_data['test_results'][test_name] = metrics

    # Calculate summary
    total_requests = sum(result.get('total_requests', 0) for result in report_data['test_results'].values())
    total_failures = sum(result.get('failed_requests', 0) for result in report_data['test_results'].values())

    report_data['summary'] = {
        'total_requests': total_requests,
        'total_failures': total_failures,
        'overall_error_rate': total_failures / max(total_requests, 1),
        'tests_completed': len(report_data['test_results'])
    }

    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Perfect21 Performance Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .metric {{ margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }}
            .success {{ border-left-color: #28a745; }}
            .warning {{ border-left-color: #ffc107; }}
            .error {{ border-left-color: #dc3545; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Perfect21 Performance Test Report</h1>
            <p>Generated: {report_data['timestamp']}</p>
        </div>

        <h2>Test Summary</h2>
        <div class="metric {'success' if report_data['summary']['overall_error_rate'] < 0.01 else 'error'}">
            <strong>Overall Error Rate:</strong> {report_data['summary']['overall_error_rate']:.2%}
        </div>
        <div class="metric">
            <strong>Total Requests:</strong> {report_data['summary']['total_requests']:,}
        </div>
        <div class="metric">
            <strong>Tests Completed:</strong> {report_data['summary']['tests_completed']}
        </div>

        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test Name</th>
                <th>Total Requests</th>
                <th>Failed Requests</th>
                <th>Error Rate</th>
            </tr>
    """

    for test_name, results in report_data['test_results'].items():
        error_rate = results['failed_requests'] / max(results['total_requests'], 1)
        html_content += f"""
            <tr>
                <td>{test_name}</td>
                <td>{results['total_requests']:,}</td>
                <td>{results['failed_requests']:,}</td>
                <td>{error_rate:.2%}</td>
            </tr>
        """

    html_content += """
        </table>

        <h2>Recommendations</h2>
        <ul>
            <li>Review failed requests and identify bottlenecks</li>
            <li>Monitor database performance during peak load</li>
            <li>Consider implementing caching for frequently accessed data</li>
            <li>Evaluate auto-scaling policies for handling traffic spikes</li>
        </ul>
    </body>
    </html>
    """

    # Save HTML report
    report_file = os.path.join(results_dir, 'performance_report.html')
    with open(report_file, 'w') as f:
        f.write(html_content)

    # Save JSON data
    json_file = os.path.join(results_dir, 'performance_report.json')
    with open(json_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"Report generated: {report_file}")
    return report_file

if __name__ == '__main__':
    results_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    generate_html_report(results_dir)
EOF

    # Run report generation
    python3 "$TEST_RESULTS_DIR/generate_report.py" "$TEST_RESULTS_DIR"

    if [ -f "$TEST_RESULTS_DIR/performance_report.html" ]; then
        log_success "Performance report generated: $TEST_RESULTS_DIR/performance_report.html"
    else
        log_warning "Failed to generate performance report"
    fi
}

# Analyze results and provide recommendations
analyze_results() {
    log_section "Analyzing Results"

    # Basic analysis of log files
    local total_tests=0
    local failed_tests=0

    for log_file in "$TEST_RESULTS_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            total_tests=$((total_tests + 1))

            # Check if test failed (simple heuristic)
            if grep -q -i "error\|fail\|exception" "$log_file"; then
                failed_tests=$((failed_tests + 1))
                log_warning "Test $(basename "$log_file" .log) appears to have issues"
            fi
        fi
    done

    log_info "Test Analysis Summary:"
    log_info "  Total tests run: $total_tests"
    log_info "  Tests with issues: $failed_tests"

    if [ $failed_tests -eq 0 ]; then
        log_success "All tests completed without obvious issues"
    else
        log_warning "$failed_tests out of $total_tests tests had issues - review logs for details"
    fi

    # Generate recommendations based on test results
    cat > "$TEST_RESULTS_DIR/recommendations.md" << EOF
# Performance Test Recommendations

## Test Summary
- Total tests completed: $total_tests
- Tests with issues: $failed_tests
- Test configuration: $MAX_USERS max users, ${TEST_DURATION}s duration

## Next Steps
1. Review individual test logs for specific bottlenecks
2. Analyze response time patterns for performance degradation
3. Check error logs for recurring issues
4. Consider implementing recommended optimizations from the main performance plan

## Files Generated
- Test logs: *.log files
- Performance report: performance_report.html
- Configuration: test_config.json

EOF
}

# Cleanup function
cleanup() {
    if [ "$CLEANUP_AFTER" = true ]; then
        log_info "Cleaning up temporary files..."
        # Remove temporary scripts but keep results
        rm -f "$TEST_RESULTS_DIR/generate_report.py"
    fi
}

# Main execution flow
main() {
    parse_args "$@"

    log_section "Perfect21 Performance Testing Suite"
    log_info "Target: $TARGET_HOST"
    log_info "Scenario: $SCENARIO"
    log_info "Max Users: $MAX_USERS"
    log_info "Duration: ${TEST_DURATION}s"
    log_info "Quick Test: $QUICK_TEST"
    log_info "Results Dir: $TEST_RESULTS_DIR"

    # Setup and checks
    check_prerequisites
    pre_test_check

    # Run tests based on scenario
    case "$SCENARIO" in
        "baseline")
            run_baseline_test
            ;;
        "load")
            run_load_test
            ;;
        "stress")
            run_stress_test
            ;;
        "spike")
            run_spike_test
            ;;
        "endurance")
            run_endurance_test
            ;;
        "all")
            run_baseline_test
            run_load_test
            run_stress_test
            run_spike_test
            run_endurance_test
            ;;
        *)
            log_error "Unknown scenario: $SCENARIO"
            exit 1
            ;;
    esac

    # Post-test analysis
    generate_performance_report
    analyze_results
    cleanup

    log_section "Performance Testing Complete"
    log_success "All tests completed successfully!"
    log_info "Results available in: $TEST_RESULTS_DIR"

    if [ -f "$TEST_RESULTS_DIR/performance_report.html" ]; then
        log_info "Open performance_report.html in your browser to view detailed results"
    fi
}

# Handle script interruption
trap 'log_error "Script interrupted"; cleanup; exit 1' INT TERM

# Run main function with all arguments
main "$@"