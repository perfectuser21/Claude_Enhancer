#!/bin/bash

# Claude Enhancer Comprehensive Validation Test Suite
# Testing all system components after path fixes and optimizations

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging
LOG_FILE="/tmp/perfect21_validation.log"
exec 3>&1 4>&2
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

print_header() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}Claude Enhancer Validation Test Suite${NC}"
    echo -e "${CYAN}================================${NC}"
    echo "Timestamp: $(date)"
    echo "Test Log: $LOG_FILE"
    echo ""
}

print_section() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "\n${BLUE}Test $TOTAL_TESTS: $test_name${NC}"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Test functions
test_path_cleanup() {
    # Check for any remaining legacy references (we want none)
    local claude_enhancer_refs
    claude_enhancer_refs=$(find /home/xx/dev/Claude Enhancer -type f -name "*.sh" -o -name "*.md" -o -name "*.json" | xargs grep -l "Claude Enhancer" 2>/dev/null | wc -l)

    if [ "$claude_enhancer_refs" -eq 0 ]; then
        echo "No 'Claude Enhancer' references found (successful cleanup)"
        return 0
    else
        echo "Found $claude_enhancer_refs files with 'Claude Enhancer' references"
        find /home/xx/dev/Claude Enhancer -type f -name "*.sh" -o -name "*.md" -o -name "*.json" | xargs grep -l "Claude Enhancer" 2>/dev/null
        return 1
    fi
}

test_perfect21_branding() {
    # Check if Claude Enhancer branding is consistent
    local perfect21_refs
    perfect21_refs=$(find /home/xx/dev/Claude Enhancer -type f -name "*.sh" -o -name "*.md" | xargs grep -l "Claude Enhancer" 2>/dev/null | wc -l)

    if [ "$perfect21_refs" -gt 0 ]; then
        echo "Found Claude Enhancer branding in $perfect21_refs files"
        return 0
    else
        echo "No Claude Enhancer branding found"
        return 1
    fi
}

test_script_permissions() {
    local script_dir="/home/xx/dev/Claude Enhancer/.claude/scripts"
    local all_executable=true

    if [ ! -d "$script_dir" ]; then
        echo "Scripts directory not found: $script_dir"
        return 1
    fi

    for script in "$script_dir"/*.sh; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                echo "✓ $script is executable"
            else
                echo "✗ $script is NOT executable"
                all_executable=false
            fi
        fi
    done

    $all_executable
}

test_cleanup_script() {
    local cleanup_script="/home/xx/dev/Claude Enhancer/.claude/scripts/cleanup.sh"

    if [ ! -f "$cleanup_script" ]; then
        echo "Cleanup script not found: $cleanup_script"
        return 1
    fi

    # Test in dry-run mode
    echo "Testing cleanup script in dry-run mode..."
    if "$cleanup_script" --dry-run 2>&1 | grep -q "DRY RUN MODE"; then
        echo "✓ Cleanup script dry-run mode works"
        return 0
    else
        echo "✗ Cleanup script dry-run mode failed"
        return 1
    fi
}

test_agent_selector() {
    local selector_script="/home/xx/dev/Claude Enhancer/.claude/scripts/smart_agent_selector.sh"

    if [ ! -f "$selector_script" ]; then
        echo "Agent selector script not found: $selector_script"
        return 1
    fi

    # Test with different complexity levels
    echo "Testing agent selector with different complexity levels..."

    for complexity in simple standard complex; do
        echo "Testing complexity: $complexity"
        local output
        output=$("$selector_script" "$complexity" 2>&1)

        if echo "$output" | grep -q -E "(Recommended Agents|推荐Agent组合|Agent组合)"; then
            echo "✓ Agent selector works for $complexity complexity"
        else
            echo "✗ Agent selector failed for $complexity complexity"
            echo "Output: $output"
            return 1
        fi
    done

    return 0
}

test_print_statements() {
    local test_script="/tmp/test_print.sh"

    cat > "$test_script" << 'EOF'
#!/bin/bash
source /home/xx/dev/Claude Enhancer/.claude/scripts/config.sh

print_header "Test Header"
print_success "Test Success"
print_error "Test Error"
print_warning "Test Warning"
print_info "Test Info"
EOF

    chmod +x "$test_script"

    echo "Testing print functions..."
    local output
    output=$("$test_script" 2>&1)

    # Clean up
    rm -f "$test_script"

    if echo "$output" | grep -q "Test Header" && \
       echo "$output" | grep -q "Test Success" && \
       echo "$output" | grep -q "Test Error" && \
       echo "$output" | grep -q "Test Warning" && \
       echo "$output" | grep -q "Test Info"; then
        echo "✓ All print functions work correctly"
        return 0
    else
        echo "✗ Some print functions failed"
        echo "Output: $output"
        return 1
    fi
}

test_config_loading() {
    local config_script="/home/xx/dev/Claude Enhancer/.claude/scripts/config.sh"

    if [ ! -f "$config_script" ]; then
        echo "Config script not found: $config_script"
        return 1
    fi

    # Test config loading
    echo "Testing config loading..."

    # Source the config and check if variables are set
    if source "$config_script" 2>/dev/null; then
        echo "✓ Config script loads without errors"

        # Check if essential variables are defined
        if [ -n "$PERFECT21_ROOT" ] && [ -n "$CLAUDE_DIR" ]; then
            echo "✓ Essential variables are defined"
            echo "  PERFECT21_ROOT: $PERFECT21_ROOT"
            echo "  CLAUDE_DIR: $CLAUDE_DIR"
            return 0
        else
            echo "✗ Essential variables not defined"
            return 1
        fi
    else
        echo "✗ Config script failed to load"
        return 1
    fi
}

test_git_hooks_integration() {
    local git_hooks_dir="/home/xx/dev/Claude Enhancer/.git/hooks"
    local installed_hooks=0

    echo "Checking Git hooks installation..."

    for hook in pre-commit commit-msg pre-push; do
        local hook_file="$git_hooks_dir/$hook"
        if [ -f "$hook_file" ] && [ -x "$hook_file" ]; then
            echo "✓ $hook is installed and executable"
            installed_hooks=$((installed_hooks + 1))
        else
            echo "✗ $hook is missing or not executable"
        fi
    done

    if [ "$installed_hooks" -eq 3 ]; then
        echo "✓ All Git hooks are properly installed"
        return 0
    else
        echo "✗ $((3 - installed_hooks)) Git hooks are missing"
        return 1
    fi
}

test_phase_state_management() {
    local phase_state="/home/xx/dev/Claude Enhancer/.claude/phase_state.json"

    if [ ! -f "$phase_state" ]; then
        echo "Phase state file not found: $phase_state"
        return 1
    fi

    # Test if it's valid JSON
    if jq empty "$phase_state" 2>/dev/null; then
        echo "✓ Phase state file is valid JSON"

        # Check if required fields exist
        local current_phase
        current_phase=$(jq -r '.current_phase' "$phase_state" 2>/dev/null)

        if [ "$current_phase" != "null" ] && [ -n "$current_phase" ]; then
            echo "✓ Phase state has valid current_phase: $current_phase"
            return 0
        else
            echo "✗ Phase state missing valid current_phase"
            return 1
        fi
    else
        echo "✗ Phase state file is not valid JSON"
        return 1
    fi
}

test_agent_definitions() {
    local agents_dir="/home/xx/dev/Claude Enhancer/.claude/agents"
    local agent_count=0

    echo "Checking agent definitions..."

    if [ ! -d "$agents_dir" ]; then
        echo "Agents directory not found: $agents_dir"
        return 1
    fi

    # Count agent files
    agent_count=$(find "$agents_dir" -name "*.md" | wc -l)

    if [ "$agent_count" -gt 50 ]; then
        echo "✓ Found $agent_count agent definitions (target: 56)"

        # Check if key agents exist
        local key_agents=("backend-architect" "security-auditor" "test-engineer" "api-designer" "database-specialist")
        local found_key_agents=0

        for agent in "${key_agents[@]}"; do
            if find "$agents_dir" -name "*$agent*" | grep -q .; then
                echo "✓ Key agent found: $agent"
                found_key_agents=$((found_key_agents + 1))
            else
                echo "✗ Key agent missing: $agent"
            fi
        done

        if [ "$found_key_agents" -eq ${#key_agents[@]} ]; then
            echo "✓ All key agents are available"
            return 0
        else
            echo "✗ $((${#key_agents[@]} - found_key_agents)) key agents are missing"
            return 1
        fi
    else
        echo "✗ Insufficient agent definitions: $agent_count (expected > 50)"
        return 1
    fi
}

# Test execution performance
test_performance() {
    echo "Testing system performance..."

    local start_time
    local end_time
    local duration

    # Test config loading speed
    start_time=$(date +%s%N)
    source /home/xx/dev/Claude Enhancer/.claude/scripts/config.sh >/dev/null 2>&1
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 ))

    echo "Config loading time: ${duration}ms"

    if [ "$duration" -lt 500 ]; then
        echo "✓ Config loads quickly (< 500ms)"
        return 0
    else
        echo "✗ Config loading is slow (> 500ms)"
        return 1
    fi
}

# Generate test report
generate_report() {
    print_section "TEST SUMMARY"

    echo -e "\n${CYAN}Final Results:${NC}"
    echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "Success Rate: ${YELLOW}$success_rate%${NC}"

    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Claude Enhancer system is ready for production.${NC}"
        return 0
    else
        echo -e "\n${RED}⚠️  $FAILED_TESTS test(s) failed. Please review and fix issues.${NC}"
        return 1
    fi
}

# Main execution
main() {
    print_header

    print_section "PATH CLEANUP VERIFICATION"
    run_test "Check for Claude Enhancer remnants" "test_path_cleanup"
    run_test "Verify Claude Enhancer branding" "test_perfect21_branding"

    print_section "PERMISSION VERIFICATION"
    run_test "Check script permissions" "test_script_permissions"

    print_section "FUNCTIONALITY VERIFICATION"
    run_test "Test cleanup script" "test_cleanup_script"
    run_test "Test agent selector" "test_agent_selector"
    run_test "Test print functions" "test_print_statements"

    print_section "CONFIGURATION VERIFICATION"
    run_test "Test config loading" "test_config_loading"
    run_test "Test phase state management" "test_phase_state_management"

    print_section "INTEGRATION VERIFICATION"
    run_test "Test Git hooks integration" "test_git_hooks_integration"
    run_test "Test agent definitions" "test_agent_definitions"

    print_section "PERFORMANCE VERIFICATION"
    run_test "Test system performance" "test_performance"

    generate_report
}

# Execute main function
main "$@"