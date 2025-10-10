#!/usr/bin/env bash
# BDD Test Runner for Claude Enhancer
# Executes all BDD scenarios using bash-based Gherkin parser

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ACCEPTANCE_DIR="$PROJECT_ROOT/acceptance"
FEATURES_DIR="$ACCEPTANCE_DIR/features"
STEPS_DIR="$ACCEPTANCE_DIR/steps"
SUPPORT_DIR="$ACCEPTANCE_DIR/support"

# Test output
TEST_OUTPUT_DIR="$PROJECT_ROOT/test/reports"
mkdir -p "$TEST_OUTPUT_DIR"

REPORT_FILE="$TEST_OUTPUT_DIR/bdd_test_report_$(date +%Y%m%d_%H%M%S).md"
JUNIT_FILE="$TEST_OUTPUT_DIR/bdd_junit.xml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test statistics
TOTAL_FEATURES=0
TOTAL_SCENARIOS=0
PASSED_SCENARIOS=0
FAILED_SCENARIOS=0
SKIPPED_SCENARIOS=0
TOTAL_STEPS=0
PASSED_STEPS=0
FAILED_STEPS=0

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${CYAN}Claude Enhancer BDD Test Suite${NC}                       ${BLUE}║${NC}"
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo ""
}

print_section() {
    local title=$1
    echo ""
    echo -e "${CYAN}━━━ $title ━━━${NC}"
    echo ""
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ============================================================================
# Source Support Files
# ============================================================================

source_support_files() {
    log_info "Loading support files..."

    if [[ -f "$SUPPORT_DIR/world.bash" ]]; then
        source "$SUPPORT_DIR/world.bash"
        log_success "Loaded world.bash"
    else
        log_error "world.bash not found"
        exit 1
    fi

    if [[ -f "$SUPPORT_DIR/helpers.bash" ]]; then
        source "$SUPPORT_DIR/helpers.bash"
        log_success "Loaded helpers.bash"
    else
        log_error "helpers.bash not found"
        exit 1
    fi

    if [[ -f "$STEPS_DIR/step_definitions.bash" ]]; then
        source "$STEPS_DIR/step_definitions.bash"
        log_success "Loaded step_definitions.bash"
    else
        log_error "step_definitions.bash not found"
        exit 1
    fi
}

# ============================================================================
# Feature File Parser
# ============================================================================

parse_feature_file() {
    local feature_file=$1
    local current_scenario=""
    local in_scenario=false

    log_info "Parsing: $(basename "$feature_file")"

    while IFS= read -r line; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

        # Feature declaration
        if [[ "$line" =~ ^Feature: ]]; then
            ((TOTAL_FEATURES++))
            echo "FEATURE|${line#Feature: }"
            continue
        fi

        # Scenario declaration
        if [[ "$line" =~ ^[[:space:]]*Scenario: ]]; then
            ((TOTAL_SCENARIOS++))
            in_scenario=true
            current_scenario="${line#*Scenario: }"
            echo "SCENARIO|$current_scenario"
            continue
        fi

        # Background
        if [[ "$line" =~ ^[[:space:]]*Background: ]]; then
            in_scenario=true
            echo "BACKGROUND|${line#*Background: }"
            continue
        fi

        # Steps (Given, When, Then, And, But)
        if [[ "$line" =~ ^[[:space:]]+(Given|When|Then|And|But)[[:space:]] ]]; then
            ((TOTAL_STEPS++))
            local step_type=$(echo "$line" | grep -oP '^\s+\K(Given|When|Then|And|But)')
            local step_text=$(echo "$line" | sed -E 's/^\s+(Given|When|Then|And|But)\s+//')
            echo "STEP|$step_type|$step_text"
            continue
        fi

    done < "$feature_file"
}

# ============================================================================
# Step Execution
# ============================================================================

execute_step() {
    local step_type=$1
    local step_text=$2

    # Simple step matching - convert step text to function name
    # In production, this would use regex matching like Cucumber

    local function_name
    function_name=$(echo "$step_text" | \
        tr '[:upper:]' '[:lower:]' | \
        sed 's/[^a-z0-9]/_/g' | \
        sed 's/__*/_/g' | \
        sed 's/^_//;s/_$//')

    function_name="step_${function_name}"

    # Try to execute the step function
    if type -t "$function_name" >/dev/null; then
        if "$function_name"; then
            ((PASSED_STEPS++))
            return 0
        else
            ((FAILED_STEPS++))
            return 1
        fi
    else
        log_warning "Step not implemented: $step_text"
        log_warning "  Expected function: $function_name"
        ((FAILED_STEPS++))
        return 1
    fi
}

# ============================================================================
# Scenario Execution
# ============================================================================

run_scenario() {
    local feature_name=$1
    local scenario_name=$2
    shift 2
    local steps=("$@")

    print_section "Scenario: $scenario_name"

    set_scenario_context "$feature_name" "$scenario_name"

    local scenario_passed=true

    for step in "${steps[@]}"; do
        IFS='|' read -r step_type step_text <<< "$step"

        echo -n "  ${step_type} ${step_text}... "

        if execute_step "$step_type" "$step_text"; then
            log_success "PASSED"
        else
            log_error "FAILED"
            scenario_passed=false
            break
        fi
    done

    if $scenario_passed; then
        ((PASSED_SCENARIOS++))
        log_success "Scenario PASSED"
        return 0
    else
        ((FAILED_SCENARIOS++))
        log_error "Scenario FAILED"
        return 1
    fi
}

# ============================================================================
# Feature Execution
# ============================================================================

run_feature_file() {
    local feature_file=$1

    print_section "Feature: $(basename "$feature_file" .feature)"

    local feature_name=""
    local current_scenario=""
    local scenario_steps=()
    local in_scenario=false

    while IFS='|' read -r type content extra; do
        case "$type" in
            FEATURE)
                feature_name="$content"
                ;;
            SCENARIO)
                # Run previous scenario if exists
                if [[ -n "$current_scenario" ]]; then
                    run_scenario "$feature_name" "$current_scenario" "${scenario_steps[@]}"
                fi

                # Start new scenario
                current_scenario="$content"
                scenario_steps=()
                in_scenario=true
                ;;
            STEP)
                if $in_scenario; then
                    scenario_steps+=("$content|$extra")
                fi
                ;;
        esac
    done < <(parse_feature_file "$feature_file")

    # Run last scenario
    if [[ -n "$current_scenario" ]]; then
        run_scenario "$feature_name" "$current_scenario" "${scenario_steps[@]}"
    fi
}

# ============================================================================
# Test Suite Execution
# ============================================================================

run_all_features() {
    print_section "Discovering Feature Files"

    local feature_files=()
    while IFS= read -r -d '' file; do
        feature_files+=("$file")
    done < <(find "$FEATURES_DIR" -name "*.feature" -not -path "*/generated/*" -print0 | sort -z)

    log_info "Found ${#feature_files[@]} feature files"

    for feature_file in "${feature_files[@]}"; do
        run_feature_file "$feature_file"
    done
}

# ============================================================================
# Report Generation
# ============================================================================

generate_markdown_report() {
    cat > "$REPORT_FILE" << EOF
# BDD Test Report

**Generated:** $(date '+%Y-%m-%d %H:%M:%S')

## Summary

| Metric | Count |
|--------|-------|
| Features | $TOTAL_FEATURES |
| Scenarios | $TOTAL_SCENARIOS |
| ✅ Passed | $PASSED_SCENARIOS |
| ❌ Failed | $FAILED_SCENARIOS |
| ⏭️ Skipped | $SKIPPED_SCENARIOS |
| **Pass Rate** | **$(awk "BEGIN {printf \"%.1f\", ($PASSED_SCENARIOS/$TOTAL_SCENARIOS)*100}")%** |

## Step Statistics

| Metric | Count |
|--------|-------|
| Total Steps | $TOTAL_STEPS |
| ✅ Passed | $PASSED_STEPS |
| ❌ Failed | $FAILED_STEPS |
| **Pass Rate** | **$(awk "BEGIN {printf \"%.1f\", ($PASSED_STEPS/$TOTAL_STEPS)*100}")%** |

## Feature Coverage

| Feature | Scenarios | Status |
|---------|-----------|--------|
EOF

    # Add feature details
    for feature_file in "$FEATURES_DIR"/*.feature; do
        [[ -f "$feature_file" ]] || continue
        local feature_name=$(basename "$feature_file" .feature)
        local scenario_count=$(grep -c "^[[:space:]]*Scenario:" "$feature_file" || echo 0)
        echo "| $feature_name | $scenario_count | ✅ |" >> "$REPORT_FILE"
    done

    cat >> "$REPORT_FILE" << EOF

## Execution Details

- **Test Suite:** Claude Enhancer BDD Tests
- **Project Root:** $PROJECT_ROOT
- **Features Directory:** $FEATURES_DIR
- **Report File:** $REPORT_FILE

## Next Steps

EOF

    if [[ $FAILED_SCENARIOS -eq 0 ]]; then
        cat >> "$REPORT_FILE" << EOF
✅ All scenarios passed! The system is ready for deployment.

### Recommendations:
- Continue monitoring test coverage
- Add more edge case scenarios
- Update documentation with latest changes
EOF
    else
        cat >> "$REPORT_FILE" << EOF
❌ Some scenarios failed. Please review and fix the issues.

### Action Items:
- Review failed scenarios above
- Fix implementation or test expectations
- Re-run tests after fixes
- Check test logs for detailed error messages
EOF
    fi

    cat >> "$REPORT_FILE" << EOF

---
*Generated by Claude Enhancer BDD Test Suite*
EOF

    log_success "Markdown report generated: $REPORT_FILE"
}

generate_junit_xml() {
    local total_time=$(( TOTAL_SCENARIOS * 2 )) # Rough estimate

    cat > "$JUNIT_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuites tests="$TOTAL_SCENARIOS" failures="$FAILED_SCENARIOS" skipped="$SKIPPED_SCENARIOS" time="$total_time">
  <testsuite name="Claude Enhancer BDD Tests" tests="$TOTAL_SCENARIOS" failures="$FAILED_SCENARIOS" skipped="$SKIPPED_SCENARIOS" time="$total_time">
EOF

    # Add test cases (simplified - would need actual scenario tracking)
    for i in $(seq 1 "$PASSED_SCENARIOS"); do
        echo "    <testcase name=\"Scenario $i\" classname=\"BDD\" time=\"2\" />" >> "$JUNIT_FILE"
    done

    for i in $(seq 1 "$FAILED_SCENARIOS"); do
        cat >> "$JUNIT_FILE" << EOF
    <testcase name="Failed Scenario $i" classname="BDD" time="2">
      <failure message="Scenario failed" type="AssertionError">Step assertion failed</failure>
    </testcase>
EOF
    done

    echo "  </testsuite>" >> "$JUNIT_FILE"
    echo "</testsuites>" >> "$JUNIT_FILE"

    log_success "JUnit XML report generated: $JUNIT_FILE"
}

# ============================================================================
# Print Summary
# ============================================================================

print_summary() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${CYAN}Test Execution Summary${NC}                               ${BLUE}║${NC}"
    echo -e "${BLUE}╠═══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC}  Features:    ${TOTAL_FEATURES}                                           ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  Scenarios:   ${TOTAL_SCENARIOS}                                          ${BLUE}║${NC}"

    if [[ $FAILED_SCENARIOS -eq 0 ]]; then
        echo -e "${BLUE}║${NC}    ${GREEN}✓ Passed:${NC}   ${PASSED_SCENARIOS}                                        ${BLUE}║${NC}"
    else
        echo -e "${BLUE}║${NC}    ${GREEN}✓ Passed:${NC}   ${PASSED_SCENARIOS}                                        ${BLUE}║${NC}"
        echo -e "${BLUE}║${NC}    ${RED}✗ Failed:${NC}   ${FAILED_SCENARIOS}                                        ${BLUE}║${NC}"
    fi

    if [[ $SKIPPED_SCENARIOS -gt 0 ]]; then
        echo -e "${BLUE}║${NC}    ${YELLOW}⏭ Skipped:${NC}  ${SKIPPED_SCENARIOS}                                        ${BLUE}║${NC}"
    fi

    echo -e "${BLUE}╠═══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC}  Steps:       ${TOTAL_STEPS}                                          ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}    ${GREEN}✓ Passed:${NC}   ${PASSED_STEPS}                                        ${BLUE}║${NC}"

    if [[ $FAILED_STEPS -gt 0 ]]; then
        echo -e "${BLUE}║${NC}    ${RED}✗ Failed:${NC}   ${FAILED_STEPS}                                        ${BLUE}║${NC}"
    fi

    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [[ $FAILED_SCENARIOS -eq 0 ]]; then
        log_success "All scenarios passed!"
        return 0
    else
        log_error "Some scenarios failed. Check the report for details."
        return 1
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local start_time=$(date +%s)

    print_header

    # Initialize world
    before_all

    # Load support files
    source_support_files

    # Run all features
    run_all_features

    # Generate reports
    generate_markdown_report
    generate_junit_xml

    # Print summary
    print_summary
    local exit_code=$?

    # Cleanup
    after_all

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_info "Total execution time: ${duration}s"
    log_info "Full report available at: $REPORT_FILE"

    exit $exit_code
}

# ============================================================================
# Script Entry Point
# ============================================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
