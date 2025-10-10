#!/usr/bin/env bash
set -euo pipefail

# Command: ce validate
# Purpose: Run quality gate validation

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib"

source "${LIB_DIR}/common.sh"
source "${LIB_DIR}/gate_integrator.sh"
source "${LIB_DIR}/phase_manager.sh"

cmd_validate_help() {
    cat <<'EOF'
Usage: ce validate [options]

Run quality gate validation for current phase.

Options:
  --full         Full validation (default)
  --quick        Quick validation (cached)
  --incremental  Only validate changes
  --parallel <N> Parallel workers (default: 4)

Examples:
  ce validate
  ce validate --quick
  ce validate --incremental

See also: ce next, ce publish
EOF
}

cmd_validate_run_gates() {
    # Run phase gate validation
    local mode="${1:-full}"
    local parallel="${2:-4}"
    local phase="${3:-P3}"

    echo -e "${CE_COLOR_CYAN}Running quality gates for ${phase}...${CE_COLOR_RESET}"
    echo ""

    local gates_passed=0
    local gates_failed=0
    local gate_results=()

    # Define gates based on phase
    case "$phase" in
        P0)
            gate_results+=("$(cmd_validate_check_spike_docs)")
            ;;
        P1)
            gate_results+=("$(cmd_validate_check_plan_md)")
            ;;
        P2)
            gate_results+=("$(cmd_validate_check_structure)")
            ;;
        P3|P4)
            gate_results+=("$(cmd_validate_check_code_quality)")
            gate_results+=("$(cmd_validate_check_tests)")
            gate_results+=("$(cmd_validate_check_security)")
            ;;
        P5)
            gate_results+=("$(cmd_validate_check_review)")
            ;;
        P6)
            gate_results+=("$(cmd_validate_check_documentation)")
            ;;
        P7)
            gate_results+=("$(cmd_validate_check_monitoring)")
            ;;
    esac

    # Count results
    for result in "${gate_results[@]}"; do
        if [[ "$result" == "PASS" ]]; then
            ((gates_passed++))
        else
            ((gates_failed++))
        fi
    done

    echo ""
    echo -e "${CE_COLOR_CYAN}===== Validation Results =====${CE_COLOR_RESET}"
    echo -e "  Passed: ${CE_COLOR_GREEN}${gates_passed}${CE_COLOR_RESET}"
    echo -e "  Failed: ${CE_COLOR_RED}${gates_failed}${CE_COLOR_RESET}"
    echo -e "  Total:  $((gates_passed + gates_failed))"
    echo ""

    [[ $gates_failed -eq 0 ]] && return 0 || return 1
}

cmd_validate_check_spike_docs() {
    echo -n "  [P0] Spike documentation exists... "
    if [[ -f "docs/SPIKE.md" || -f "SPIKE.md" ]]; then
        echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET}"
        echo "PASS"
    else
        echo -e "${CE_COLOR_RED}FAIL${CE_COLOR_RESET} (no SPIKE.md found)"
        echo "FAIL"
    fi
}

cmd_validate_check_plan_md() {
    echo -n "  [P1] PLAN.md exists... "
    if [[ -f "PLAN.md" ]]; then
        local word_count=$(wc -w < PLAN.md)
        if [[ $word_count -gt 100 ]]; then
            echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET} ($word_count words)"
            echo "PASS"
        else
            echo -e "${CE_COLOR_YELLOW}WARN${CE_COLOR_RESET} (PLAN.md too short: $word_count words)"
            echo "FAIL"
        fi
    else
        echo -e "${CE_COLOR_RED}FAIL${CE_COLOR_RESET} (no PLAN.md found)"
        echo "FAIL"
    fi
}

cmd_validate_check_structure() {
    echo -n "  [P2] Directory structure valid... "
    local required_dirs=(".workflow" "docs" "src" "test")
    local missing_dirs=()

    for dir in "${required_dirs[@]}"; do
        [[ ! -d "$dir" ]] && missing_dirs+=("$dir")
    done

    if [[ ${#missing_dirs[@]} -eq 0 ]]; then
        echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET}"
        echo "PASS"
    else
        echo -e "${CE_COLOR_RED}FAIL${CE_COLOR_RESET} (missing: ${missing_dirs[*]})"
        echo "FAIL"
    fi
}

cmd_validate_check_code_quality() {
    echo -n "  [P3] Code quality... "
    # Check if there are any bash scripts with syntax errors
    local bash_files
    bash_files=$(find . -type f -name "*.sh" 2>/dev/null | grep -v node_modules || echo "")

    if [[ -z "$bash_files" ]]; then
        echo -e "${CE_COLOR_YELLOW}SKIP${CE_COLOR_RESET} (no bash files)"
        echo "PASS"
        return 0
    fi

    local errors=0
    while IFS= read -r file; do
        if ! bash -n "$file" 2>/dev/null; then
            ((errors++))
        fi
    done <<< "$bash_files"

    if [[ $errors -eq 0 ]]; then
        echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET}"
        echo "PASS"
    else
        echo -e "${CE_COLOR_RED}FAIL${CE_COLOR_RESET} ($errors files with syntax errors)"
        echo "FAIL"
    fi
}

cmd_validate_check_tests() {
    echo -n "  [P4] Tests exist... "
    local test_files
    test_files=$(find test -type f \( -name "*test*" -o -name "*spec*" \) 2>/dev/null | wc -l || echo "0")

    if [[ $test_files -gt 0 ]]; then
        echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET} ($test_files test files)"
        echo "PASS"
    else
        echo -e "${CE_COLOR_RED}FAIL${CE_COLOR_RESET} (no test files found)"
        echo "FAIL"
    fi
}

cmd_validate_check_security() {
    echo -n "  [P3] Security check... "
    # Check for common secrets patterns
    local secrets_found=0

    # Simple pattern check for common secrets
    if git ls-files | xargs grep -iE "(password|secret|token|api[_-]?key)" 2>/dev/null | grep -v "# " | grep -v "//" | wc -l | grep -q "^0$"; then
        echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET}"
        echo "PASS"
    else
        echo -e "${CE_COLOR_YELLOW}WARN${CE_COLOR_RESET} (potential secrets found)"
        echo "PASS"  # Warning but not failure
    fi
}

cmd_validate_check_review() {
    echo -n "  [P5] Review completed... "
    if [[ -f "REVIEW.md" ]]; then
        echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET}"
        echo "PASS"
    else
        echo -e "${CE_COLOR_RED}FAIL${CE_COLOR_RESET} (no REVIEW.md found)"
        echo "FAIL"
    fi
}

cmd_validate_check_documentation() {
    echo -n "  [P6] Documentation updated... "
    if [[ -f "README.md" ]]; then
        local last_commit=$(git log -1 --format=%ct README.md 2>/dev/null || echo "0")
        local now=$(date +%s)
        local age=$((now - last_commit))

        if [[ $age -lt 604800 ]]; then  # Less than 7 days old
            echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET} (recently updated)"
            echo "PASS"
        else
            echo -e "${CE_COLOR_YELLOW}WARN${CE_COLOR_RESET} (README.md is old)"
            echo "PASS"
        fi
    else
        echo -e "${CE_COLOR_RED}FAIL${CE_COLOR_RESET} (no README.md found)"
        echo "FAIL"
    fi
}

cmd_validate_check_monitoring() {
    echo -n "  [P7] Monitoring configured... "
    if [[ -d "observability" || -f "observability/slo/slo.yml" ]]; then
        echo -e "${CE_COLOR_GREEN}PASS${CE_COLOR_RESET}"
        echo "PASS"
    else
        echo -e "${CE_COLOR_RED}FAIL${CE_COLOR_RESET} (no monitoring config)"
        echo "FAIL"
    fi
}

cmd_validate_check_phase() {
    # Check phase-specific requirements
    local phase="${1:-P3}"

    echo -e "${CE_COLOR_CYAN}Checking ${phase} requirements...${CE_COLOR_RESET}"
    echo ""

    case "$phase" in
        P0)
            echo "  P0: Discovery Phase"
            echo "  - Technical spike documentation"
            echo "  - Feasibility validation"
            ;;
        P1)
            echo "  P1: Planning Phase"
            echo "  - PLAN.md with requirements"
            echo "  - Architecture design"
            ;;
        P2)
            echo "  P2: Skeleton Phase"
            echo "  - Directory structure"
            echo "  - Interface definitions"
            ;;
        P3)
            echo "  P3: Implementation Phase"
            echo "  - Code quality gates"
            echo "  - Unit tests"
            echo "  - Security checks"
            ;;
        P4)
            echo "  P4: Testing Phase"
            echo "  - Test coverage"
            echo "  - Integration tests"
            ;;
        P5)
            echo "  P5: Review Phase"
            echo "  - Code review completed"
            echo "  - REVIEW.md exists"
            ;;
        P6)
            echo "  P6: Release Phase"
            echo "  - Documentation updated"
            echo "  - CHANGELOG updated"
            ;;
        P7)
            echo "  P7: Monitoring Phase"
            echo "  - SLO configured"
            echo "  - Monitoring setup"
            ;;
    esac
    echo ""

    return 0
}

cmd_validate_main() {
    # Main entry point for validate command

    local mode="full"
    local parallel=4

    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --full)
                mode="full"
                shift
                ;;
            --quick)
                mode="quick"
                shift
                ;;
            --incremental)
                mode="incremental"
                shift
                ;;
            --parallel)
                parallel="$2"
                shift 2
                ;;
            --help|-h)
                cmd_validate_help
                exit 0
                ;;
            *)
                echo -e "${CE_COLOR_RED}Error: Unknown option: $1${CE_COLOR_RESET}" >&2
                cmd_validate_help
                exit 1
                ;;
        esac
    done

    # Ensure we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${CE_COLOR_RED}Error: Not a git repository${CE_COLOR_RESET}" >&2
        exit 1
    fi

    # Get current phase
    local phase="P3"
    if [[ -f ".workflow/state/current_phase" ]]; then
        phase=$(cat .workflow/state/current_phase)
    fi

    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}     Claude Enhancer - Gate Validation${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo ""
    echo -e "  Phase: ${CE_COLOR_GREEN}${phase}${CE_COLOR_RESET}"
    echo -e "  Mode:  ${CE_COLOR_CYAN}${mode}${CE_COLOR_RESET}"
    echo ""

    # Check phase requirements
    cmd_validate_check_phase "$phase"

    # Run gate validation
    if cmd_validate_run_gates "$mode" "$parallel" "$phase"; then
        echo -e "${CE_COLOR_GREEN}===== All Gates Passed! =====${CE_COLOR_RESET}"
        echo ""
        echo -e "${CE_COLOR_CYAN}Next Steps:${CE_COLOR_RESET}"
        echo -e "  ${CE_COLOR_CYAN}ce next${CE_COLOR_RESET}     - Move to next phase"
        echo -e "  ${CE_COLOR_CYAN}ce publish${CE_COLOR_RESET}  - Create pull request"
        echo ""
        exit 0
    else
        echo -e "${CE_COLOR_RED}===== Some Gates Failed =====${CE_COLOR_RESET}"
        echo ""
        echo -e "${CE_COLOR_YELLOW}Please fix the issues and run 'ce validate' again${CE_COLOR_RESET}"
        echo ""
        exit 1
    fi
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cmd_validate_main "$@"
fi
