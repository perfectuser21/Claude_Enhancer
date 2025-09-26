#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Error Handler Test Suite
# =============================================================================
# Comprehensive testing for the error handler and retry mechanism
# Max 20X quality - thorough validation of all features

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ERROR_HANDLER="$SCRIPT_DIR/error_handler.sh"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# =============================================================================
# TEST FRAMEWORK
# =============================================================================

log_test() {
    echo -e "${BLUE}[TEST $((++TESTS_TOTAL))]${NC} $1"
}

assert_success() {
    local command="$1"
    local description="$2"

    log_test "$description"

    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}  ❌ FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_failure() {
    local command="$1"
    local description="$2"

    log_test "$description"

    if ! eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ PASSED (expected failure)${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}  ❌ FAILED (should have failed)${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_file_exists() {
    local file="$1"
    local description="$2"

    log_test "$description"

    if [[ -f "$file" ]]; then
        echo -e "${GREEN}  ✅ PASSED - File exists: $file${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}  ❌ FAILED - File not found: $file${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_contains() {
    local file="$1"
    local pattern="$2"
    local description="$3"

    log_test "$description"

    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}  ✅ PASSED - Pattern found: $pattern${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}  ❌ FAILED - Pattern not found: $pattern${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# =============================================================================
# TEST CASES
# =============================================================================

test_error_handler_initialization() {
    echo -e "\n${BOLD}🧪 Testing Error Handler Initialization${NC}"
    echo "════════════════════════════════════════════════════════════"

    assert_file_exists "$ERROR_HANDLER" "Error handler script exists"
    assert_success "bash $ERROR_HANDLER configure" "Configuration creation"
    assert_file_exists "/home/xx/dev/Claude Enhancer 5.0/.claude/error_handler_config.json" "Configuration file created"
    assert_success "bash $ERROR_HANDLER --help" "Help command works"
}

test_error_classification() {
    echo -e "\n${BOLD}🔍 Testing Error Classification${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Test different error types by creating controlled failures

    # File not found error
    local temp_output="/tmp/error_test_output.txt"
    bash "$ERROR_HANDLER" handle "test_phase" "cat /nonexistent/file" 1 "No such file or directory" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "FILE_NOT_FOUND" "File not found error classification"

    # Permission denied error
    bash "$ERROR_HANDLER" handle "test_phase" "touch /root/restricted" 1 "Permission denied" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "PERMISSION_DENIED" "Permission denied error classification"

    # Network error
    bash "$ERROR_HANDLER" handle "test_phase" "curl http://nonexistent.localhost" 1 "Connection refused" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "NETWORK_ERROR" "Network error classification"

    # Memory error
    bash "$ERROR_HANDLER" handle "test_phase" "malloc_test" 137 "Out of memory" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "MEMORY_ERROR" "Memory error classification"

    rm -f "$temp_output"
}

test_recovery_suggestions() {
    echo -e "\n${BOLD}💡 Testing Recovery Suggestions${NC}"
    echo "════════════════════════════════════════════════════════════"

    local temp_output="/tmp/recovery_test_output.txt"

    # Test file not found suggestions
    bash "$ERROR_HANDLER" handle "test_phase" "cat missing.txt" 1 "No such file or directory" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "Check if the file path is correct" "File not found recovery suggestion"

    # Test permission denied suggestions
    bash "$ERROR_HANDLER" handle "test_phase" "rm /etc/passwd" 1 "Permission denied" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "Check file permissions" "Permission denied recovery suggestion"

    # Test network error suggestions
    bash "$ERROR_HANDLER" handle "test_phase" "wget timeout" 1 "Connection refused" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "Check internet connectivity" "Network error recovery suggestion"

    rm -f "$temp_output"
}

test_system_state_capture() {
    echo -e "\n${BOLD}🖥️  Testing System State Capture${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Trigger error handler to capture system state
    local temp_output="/tmp/system_state_test.txt"
    bash "$ERROR_HANDLER" handle "test_phase" "false" 1 "Test error for system state" > "$temp_output" 2>&1 || true

    # Check if system state file was created
    local state_files_count
    state_files_count=$(find "/home/xx/dev/Claude Enhancer 5.0/.claude/logs" -name "system_state_*.json" | wc -l)

    if [[ $state_files_count -gt 0 ]]; then
        echo -e "${GREEN}  ✅ PASSED - System state captured${NC}"
        ((TESTS_PASSED++))
        ((TESTS_TOTAL++))
    else
        echo -e "${RED}  ❌ FAILED - No system state files found${NC}"
        ((TESTS_FAILED++))
        ((TESTS_TOTAL++))
    fi

    rm -f "$temp_output"
}

test_error_reporting() {
    echo -e "\n${BOLD}📋 Testing Error Reporting${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Generate an error report
    local temp_output="/tmp/error_report_test.txt"
    bash "$ERROR_HANDLER" handle "Phase 3" "npm install nonexistent-package" 1 "Package not found" > "$temp_output" 2>&1 || true

    # Check if error report was created
    local report_files_count
    report_files_count=$(find "/home/xx/dev/Claude Enhancer 5.0/.claude/error_reports" -name "error_report_*.md" | wc -l)

    if [[ $report_files_count -gt 0 ]]; then
        echo -e "${GREEN}  ✅ PASSED - Error report generated${NC}"
        ((TESTS_PASSED++))
        ((TESTS_TOTAL++))

        # Check report content
        local latest_report
        latest_report=$(find "/home/xx/dev/Claude Enhancer 5.0/.claude/error_reports" -name "error_report_*.md" -type f -exec ls -t {} + | head -1)

        assert_contains "$latest_report" "Claude Enhancer 5.0 - Error Report" "Report contains header"
        assert_contains "$latest_report" "Recovery Suggestions" "Report contains recovery suggestions"
        assert_contains "$latest_report" "System State" "Report contains system state info"
    else
        echo -e "${RED}  ❌ FAILED - No error reports found${NC}"
        ((TESTS_FAILED++))
        ((TESTS_TOTAL++))
    fi

    rm -f "$temp_output"
}

test_retry_mechanism() {
    echo -e "\n${BOLD}🔄 Testing Retry Mechanism${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Test successful retry (command that fails initially but succeeds on retry)
    # We'll create a script that fails the first time but succeeds on subsequent attempts
    local retry_test_script="/tmp/retry_test.sh"
    local retry_counter="/tmp/retry_counter"

    cat > "$retry_test_script" << 'EOF'
#!/bin/bash
counter_file="/tmp/retry_counter"
if [[ ! -f "$counter_file" ]]; then
    echo "1" > "$counter_file"
    exit 1
else
    count=$(cat "$counter_file")
    if [[ $count -lt 2 ]]; then
        echo $((count + 1)) > "$counter_file"
        exit 1
    else
        echo "Success after retries"
        rm -f "$counter_file"
        exit 0
    fi
fi
EOF

    chmod +x "$retry_test_script"
    rm -f "$retry_counter"

    # Test retry with max 3 attempts
    local temp_output="/tmp/retry_mechanism_test.txt"
    if bash "$ERROR_HANDLER" retry "test_phase" "bash $retry_test_script" 3 > "$temp_output" 2>&1; then
        echo -e "${GREEN}  ✅ PASSED - Retry mechanism works${NC}"
        ((TESTS_PASSED++))
        ((TESTS_TOTAL++))

        assert_contains "$temp_output" "SUCCESS after" "Retry succeeded message"
    else
        echo -e "${RED}  ❌ FAILED - Retry mechanism failed${NC}"
        ((TESTS_FAILED++))
        ((TESTS_TOTAL++))
    fi

    # Clean up
    rm -f "$retry_test_script" "$retry_counter" "$temp_output"
}

test_exponential_backoff() {
    echo -e "\n${BOLD}⏱️  Testing Exponential Backoff${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Test that delays increase between retries
    local temp_output="/tmp/backoff_test.txt"
    local start_time end_time duration

    start_time=$(date +%s)
    bash "$ERROR_HANDLER" retry "test_phase" "false" 3 > "$temp_output" 2>&1 || true
    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # With exponential backoff (1s, 2s, 4s), minimum duration should be ~7 seconds
    if [[ $duration -ge 6 ]]; then
        echo -e "${GREEN}  ✅ PASSED - Exponential backoff timing correct (${duration}s)${NC}"
        ((TESTS_PASSED++))
        ((TESTS_TOTAL++))
    else
        echo -e "${RED}  ❌ FAILED - Exponential backoff too fast (${duration}s, expected >=6s)${NC}"
        ((TESTS_FAILED++))
        ((TESTS_TOTAL++))
    fi

    assert_contains "$temp_output" "Waiting" "Backoff delay messages present"

    rm -f "$temp_output"
}

test_error_statistics() {
    echo -e "\n${BOLD}📊 Testing Error Statistics${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Generate some test errors first
    bash "$ERROR_HANDLER" handle "Phase 1" "false" 1 "Test error 1" >/dev/null 2>&1 || true
    bash "$ERROR_HANDLER" handle "Phase 2" "false" 1 "Test error 2" >/dev/null 2>&1 || true
    bash "$ERROR_HANDLER" handle "Phase 3" "false" 1 "Test error 3" >/dev/null 2>&1 || true

    # Test statistics command
    local temp_output="/tmp/stats_test.txt"
    bash "$ERROR_HANDLER" stats 1 > "$temp_output" 2>&1

    assert_contains "$temp_output" "ERROR STATISTICS" "Statistics header present"
    assert_contains "$temp_output" "Total Errors:" "Total error count present"

    rm -f "$temp_output"
}

test_cleanup_functionality() {
    echo -e "\n${BOLD}🧹 Testing Cleanup Functionality${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Create some old test files
    local test_log="/home/xx/dev/Claude Enhancer 5.0/.claude/logs/test_old.log"
    local test_report="/home/xx/dev/Claude Enhancer 5.0/.claude/error_reports/test_old_report.md"

    mkdir -p "$(dirname "$test_log")" "$(dirname "$test_report")"
    echo "old log" > "$test_log"
    echo "old report" > "$test_report"

    # Make files appear old (31 days ago)
    touch -d "31 days ago" "$test_log" "$test_report"

    # Run cleanup
    local temp_output="/tmp/cleanup_test.txt"
    bash "$ERROR_HANDLER" cleanup 30 > "$temp_output" 2>&1

    assert_contains "$temp_output" "Cleaning up files" "Cleanup message present"
    assert_contains "$temp_output" "Cleanup completed" "Cleanup completion message"

    rm -f "$temp_output"
}

test_phase_specific_suggestions() {
    echo -e "\n${BOLD}🎯 Testing Phase-Specific Suggestions${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Test Phase 3 (implementation) specific suggestions
    local temp_output="/tmp/phase_test.txt"
    bash "$ERROR_HANDLER" handle "Phase 3" "npm install" 1 "Package not found" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "agents are available" "Phase 3 specific suggestion"

    # Test Phase 5 (commit) specific suggestions
    bash "$ERROR_HANDLER" handle "Phase 5" "git commit" 1 "Nothing to commit" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "files are staged" "Phase 5 specific suggestion"

    # Test Phase 7 (deploy) specific suggestions
    bash "$ERROR_HANDLER" handle "Phase 7" "deploy.sh" 1 "Deployment failed" > "$temp_output" 2>&1 || true
    assert_contains "$temp_output" "deployment environment" "Phase 7 specific suggestion"

    rm -f "$temp_output"
}

# =============================================================================
# STRESS TESTS
# =============================================================================

test_concurrent_error_handling() {
    echo -e "\n${BOLD}⚡ Testing Concurrent Error Handling${NC}"
    echo "════════════════════════════════════════════════════════════"

    local pids=()
    local temp_dir="/tmp/concurrent_test_$$"
    mkdir -p "$temp_dir"

    # Start multiple error handlers concurrently
    for i in {1..5}; do
        (
            bash "$ERROR_HANDLER" handle "Phase $i" "false" "$i" "Concurrent error $i" \
                > "$temp_dir/output_$i.txt" 2>&1 || true
        ) &
        pids+=($!)
    done

    # Wait for all to complete
    for pid in "${pids[@]}"; do
        wait "$pid"
    done

    # Verify all generated reports
    local success_count=0
    for i in {1..5}; do
        if [[ -f "$temp_dir/output_$i.txt" ]] && grep -q "ERROR DETECTED" "$temp_dir/output_$i.txt"; then
            ((success_count++))
        fi
    done

    if [[ $success_count -eq 5 ]]; then
        echo -e "${GREEN}  ✅ PASSED - All concurrent error handlers completed${NC}"
        ((TESTS_PASSED++))
        ((TESTS_TOTAL++))
    else
        echo -e "${RED}  ❌ FAILED - Only $success_count/5 concurrent handlers completed${NC}"
        ((TESTS_FAILED++))
        ((TESTS_TOTAL++))
    fi

    # Clean up
    rm -rf "$temp_dir"
}

test_large_error_message_handling() {
    echo -e "\n${BOLD}📏 Testing Large Error Message Handling${NC}"
    echo "════════════════════════════════════════════════════════════"

    # Create a very large error message (10KB)
    local large_error=""
    for i in {1..1000}; do
        large_error+="Error line $i: This is a very long error message that simulates stack traces or detailed error output. "
    done

    local temp_output="/tmp/large_error_test.txt"
    bash "$ERROR_HANDLER" handle "test_phase" "large_error_command" 1 "$large_error" > "$temp_output" 2>&1 || true

    # Check that it handled the large error without issues
    if [[ -f "$temp_output" ]] && grep -q "ERROR DETECTED" "$temp_output"; then
        echo -e "${GREEN}  ✅ PASSED - Large error message handled correctly${NC}"
        ((TESTS_PASSED++))
        ((TESTS_TOTAL++))
    else
        echo -e "${RED}  ❌ FAILED - Large error message handling failed${NC}"
        ((TESTS_FAILED++))
        ((TESTS_TOTAL++))
    fi

    rm -f "$temp_output"
}

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

main() {
    echo -e "${BOLD}${BLUE}"
    echo "═════════════════════════════════════════════════════════════════════"
    echo "  Claude Enhancer 5.0 - Error Handler Test Suite"
    echo "═════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"

    # Check if error handler exists
    if [[ ! -f "$ERROR_HANDLER" ]]; then
        echo -e "${RED}❌ Error handler script not found: $ERROR_HANDLER${NC}"
        exit 1
    fi

    # Make error handler executable
    chmod +x "$ERROR_HANDLER"

    echo -e "Starting comprehensive test suite...\n"

    # Run all test categories
    test_error_handler_initialization
    test_error_classification
    test_recovery_suggestions
    test_system_state_capture
    test_error_reporting
    test_retry_mechanism
    test_exponential_backoff
    test_error_statistics
    test_cleanup_functionality
    test_phase_specific_suggestions

    # Stress tests
    echo -e "\n${BOLD}🏋️  Running Stress Tests${NC}"
    echo "════════════════════════════════════════════════════════════"
    test_concurrent_error_handling
    test_large_error_message_handling

    # Final results
    echo -e "\n${BOLD}${BLUE}"
    echo "═════════════════════════════════════════════════════════════════════"
    echo "  TEST RESULTS SUMMARY"
    echo "═════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"

    echo -e "${BOLD}Total Tests:${NC} $TESTS_TOTAL"
    echo -e "${GREEN}${BOLD}Passed:${NC} $TESTS_PASSED"
    echo -e "${RED}${BOLD}Failed:${NC} $TESTS_FAILED"

    local success_rate=0
    if [[ $TESTS_TOTAL -gt 0 ]]; then
        success_rate=$(( (TESTS_PASSED * 100) / TESTS_TOTAL ))
    fi

    echo -e "${BOLD}Success Rate:${NC} ${success_rate}%"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}${BOLD}🎉 ALL TESTS PASSED! Error handler is working perfectly.${NC}"
        exit 0
    else
        echo -e "\n${YELLOW}${BOLD}⚠️  Some tests failed. Please review the error handler implementation.${NC}"
        exit 1
    fi
}

# Execute main function
main "$@"