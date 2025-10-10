#!/usr/bin/env bash
set -euo pipefail

# Command: ce next
# Purpose: Transition to next phase

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib"

source "${LIB_DIR}/common.sh"
source "${LIB_DIR}/phase_manager.sh"
source "${LIB_DIR}/gate_integrator.sh"

cmd_next_help() {
    cat <<'EOF'
Usage: ce next [options]

Transition to the next development phase.

Options:
  --skip-validation  Skip gate validation (dangerous)
  --force            Force transition
  --dry-run          Show what would happen

Examples:
  ce next
  ce next --dry-run

See also: ce validate, ce publish
EOF
}

cmd_next_validate_transition() {
    local from_phase="$1"
    local to_phase="$2"
    local skip_validation="$3"

    if [[ "$skip_validation" == "true" ]]; then
        echo -e "${CE_COLOR_YELLOW}Warning: Skipping validation${CE_COLOR_RESET}"
        return 0
    fi

    echo -e "${CE_COLOR_CYAN}Validating transition from ${from_phase} to ${to_phase}...${CE_COLOR_RESET}"

    # Check for uncommitted changes
    if git status --porcelain 2>/dev/null | grep -q .; then
        echo -e "${CE_COLOR_YELLOW}Warning: You have uncommitted changes${CE_COLOR_RESET}"
    fi

    # Check if gates passed (simplified)
    local gates_file=".gates/${from_phase}.ok"
    if [[ ! -f "$gates_file" ]]; then
        echo -e "${CE_COLOR_RED}Error: Gates not passed for ${from_phase}${CE_COLOR_RESET}"
        echo -e "${CE_COLOR_YELLOW}Run 'ce validate' first${CE_COLOR_RESET}"
        return 1
    fi

    return 0
}

cmd_next_execute_transition() {
    local from_phase="$1"
    local to_phase="$2"
    local dry_run="$3"

    if [[ "$dry_run" == "true" ]]; then
        echo ""
        echo -e "${CE_COLOR_CYAN}[DRY RUN] Would transition:${CE_COLOR_RESET}"
        echo -e "  From: ${CE_COLOR_YELLOW}${from_phase}${CE_COLOR_RESET}"
        echo -e "  To:   ${CE_COLOR_GREEN}${to_phase}${CE_COLOR_RESET}"
        return 0
    fi

    echo ""
    echo -e "${CE_COLOR_CYAN}[1/4]${CE_COLOR_RESET} Updating phase marker..."
    mkdir -p .workflow/state
    echo "$to_phase" > .workflow/state/current_phase
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Phase marker updated"

    echo ""
    echo -e "${CE_COLOR_CYAN}[2/4]${CE_COLOR_RESET} Creating phase transition commit..."
    git add .workflow/state/current_phase 2>/dev/null || true
    git commit -m "chore: transition from ${from_phase} to ${to_phase}" --allow-empty 2>/dev/null || true
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Commit created"

    echo ""
    echo -e "${CE_COLOR_CYAN}[3/4]${CE_COLOR_RESET} Updating session manifest..."
    if [[ -d ".workflow/state/sessions" ]]; then
        for manifest in .workflow/state/sessions/*/manifest.yml; do
            [[ -f "$manifest" ]] || continue
            sed -i "s/^phase:.*/phase: ${to_phase}/" "$manifest" 2>/dev/null || true
        done
    fi
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Session updated"

    echo ""
    echo -e "${CE_COLOR_CYAN}[4/4]${CE_COLOR_RESET} Generating checklist..."
    cmd_next_generate_checklist "$to_phase"
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Checklist generated"

    return 0
}

cmd_next_generate_checklist() {
    local phase="$1"

    echo ""
    echo -e "${CE_COLOR_GREEN}Phase ${phase} Checklist:${CE_COLOR_RESET}"

    case "$phase" in
        P1)
            echo "  [ ] Create PLAN.md with requirements"
            echo "  [ ] Design system architecture"
            echo "  [ ] Identify dependencies"
            echo "  [ ] Estimate effort and timeline"
            ;;
        P2)
            echo "  [ ] Create directory structure"
            echo "  [ ] Define module interfaces"
            echo "  [ ] Setup configuration files"
            echo "  [ ] Create skeleton classes/functions"
            ;;
        P3)
            echo "  [ ] Implement core business logic"
            echo "  [ ] Add error handling"
            echo "  [ ] Write unit tests"
            echo "  [ ] Add logging and debugging"
            ;;
        P4)
            echo "  [ ] Run all unit tests"
            echo "  [ ] Add integration tests"
            echo "  [ ] Achieve 80%+ test coverage"
            echo "  [ ] Perform load/stress testing"
            ;;
        P5)
            echo "  [ ] Complete code review"
            echo "  [ ] Create REVIEW.md"
            echo "  [ ] Address review feedback"
            echo "  [ ] Verify code quality standards"
            ;;
        P6)
            echo "  [ ] Update README.md"
            echo "  [ ] Update CHANGELOG.md"
            echo "  [ ] Write API documentation"
            echo "  [ ] Create user guides"
            ;;
        P7)
            echo "  [ ] Setup monitoring and alerts"
            echo "  [ ] Define SLO targets"
            echo "  [ ] Configure health checks"
            echo "  [ ] Plan incident response"
            ;;
    esac
}

cmd_next_main() {
    local skip_validation=false
    local force=false
    local dry_run=false

    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --skip-validation)
                skip_validation=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help|-h)
                cmd_next_help
                exit 0
                ;;
            *)
                echo -e "${CE_COLOR_RED}Error: Unknown option: $1${CE_COLOR_RESET}" >&2
                cmd_next_help
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
    local current_phase="P3"
    if [[ -f ".workflow/state/current_phase" ]]; then
        current_phase=$(cat .workflow/state/current_phase)
    fi

    # Calculate next phase
    local phase_num="${current_phase#P}"
    local next_phase_num=$((phase_num + 1))

    if [[ $next_phase_num -gt 7 ]]; then
        echo -e "${CE_COLOR_GREEN}Already at final phase (P7)${CE_COLOR_RESET}"
        echo -e "${CE_COLOR_CYAN}Use 'ce publish' to create a pull request${CE_COLOR_RESET}"
        exit 0
    fi

    local next_phase="P${next_phase_num}"

    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}     Claude Enhancer - Phase Transition${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo ""
    echo -e "  Current Phase: ${CE_COLOR_YELLOW}${current_phase}${CE_COLOR_RESET}"
    echo -e "  Next Phase:    ${CE_COLOR_GREEN}${next_phase}${CE_COLOR_RESET}"
    echo ""

    # Validate transition
    if ! cmd_next_validate_transition "$current_phase" "$next_phase" "$skip_validation"; then
        exit 1
    fi

    # Execute transition
    if cmd_next_execute_transition "$current_phase" "$next_phase" "$dry_run"; then
        if [[ "$dry_run" != "true" ]]; then
            echo ""
            echo -e "${CE_COLOR_GREEN}===== Phase Transition Complete! =====${CE_COLOR_RESET}"
            echo ""
            echo -e "${CE_COLOR_CYAN}Next Steps:${CE_COLOR_RESET}"
            echo -e "  ${CE_COLOR_CYAN}ce status${CE_COLOR_RESET}    - Check current status"
            echo -e "  ${CE_COLOR_CYAN}ce validate${CE_COLOR_RESET}  - Validate new phase requirements"
            echo ""
        fi
        exit 0
    else
        echo -e "${CE_COLOR_RED}Phase transition failed${CE_COLOR_RESET}" >&2
        exit 1
    fi
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cmd_next_main "$@"
fi
