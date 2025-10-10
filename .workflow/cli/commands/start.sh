#!/usr/bin/env bash
set -euo pipefail

# Command: ce start <feature>
# Purpose: Create a new feature branch with proper naming and state initialization

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib"

source "${LIB_DIR}/common.sh"
source "${LIB_DIR}/branch_manager.sh"
source "${LIB_DIR}/state_manager.sh"
source "${LIB_DIR}/phase_manager.sh"

cmd_start_help() {
    cat <<'EOF'
Usage: ce start <feature> [options]

Create a new feature branch with automatic naming and state tracking.

Arguments:
  <feature>      Feature name (required, 2-50 characters)

Options:
  --phase <P>    Starting phase (default: P3)
  --terminal <T> Terminal ID (default: auto-detect)
  --description  Feature description

Examples:
  ce start auth-system
  ce start payment --phase P2
  ce start search --description "Search functionality"

See also: ce status, ce next
EOF
}

cmd_start_parse_args() {
    # Parse command line arguments
    FEATURE_NAME=""
    PHASE="P3"
    TERMINAL_ID="${CE_TERMINAL_ID:-t$(date +%s)}"
    DESCRIPTION=""

    if [[ $# -eq 0 ]]; then
        echo -e "${CE_COLOR_RED}Error: Feature name required${CE_COLOR_RESET}" >&2
        cmd_start_help
        return 1
    fi

    FEATURE_NAME="$1"
    shift

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --phase)
                PHASE="$2"
                shift 2
                ;;
            --terminal)
                TERMINAL_ID="$2"
                shift 2
                ;;
            --description)
                DESCRIPTION="$2"
                shift 2
                ;;
            --help|-h)
                cmd_start_help
                exit 0
                ;;
            *)
                echo -e "${CE_COLOR_RED}Error: Unknown option: $1${CE_COLOR_RESET}" >&2
                cmd_start_help
                return 1
                ;;
        esac
    done

    return 0
}

cmd_start_validate() {
    # Validate input parameters

    # Check feature name length
    local name_len=${#FEATURE_NAME}
    if [[ $name_len -lt 2 || $name_len -gt 50 ]]; then
        echo -e "${CE_COLOR_RED}Error: Feature name must be 2-50 characters (got: $name_len)${CE_COLOR_RESET}" >&2
        return 1
    fi

    # Check feature name format (alphanumeric and hyphens only)
    if [[ ! "$FEATURE_NAME" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]]; then
        echo -e "${CE_COLOR_RED}Error: Feature name must contain only lowercase letters, numbers, and hyphens${CE_COLOR_RESET}" >&2
        echo -e "${CE_COLOR_YELLOW}  Must start and end with alphanumeric character${CE_COLOR_RESET}" >&2
        return 1
    fi

    # Check phase is valid (P0-P7)
    if [[ ! "$PHASE" =~ ^P[0-7]$ ]]; then
        echo -e "${CE_COLOR_RED}Error: Invalid phase: $PHASE (must be P0-P7)${CE_COLOR_RESET}" >&2
        return 1
    fi

    # Check terminal ID format
    if [[ ! "$TERMINAL_ID" =~ ^t[a-z0-9]+$ ]]; then
        echo -e "${CE_COLOR_RED}Error: Invalid terminal ID format: $TERMINAL_ID${CE_COLOR_RESET}" >&2
        echo -e "${CE_COLOR_YELLOW}  Format: t<alphanumeric>  (e.g., t1, t2, t123)${CE_COLOR_RESET}" >&2
        return 1
    fi

    # Check if branch already exists
    local branch_name="feature/${PHASE}-${TERMINAL_ID}-${FEATURE_NAME}"
    if git show-ref --verify --quiet "refs/heads/${branch_name}"; then
        echo -e "${CE_COLOR_RED}Error: Branch already exists: ${branch_name}${CE_COLOR_RESET}" >&2
        echo -e "${CE_COLOR_YELLOW}  Use 'ce status' to see existing branches${CE_COLOR_RESET}" >&2
        return 1
    fi

    return 0
}

cmd_start_execute() {
    # Execute the start command

    local branch_name="feature/${PHASE}-${TERMINAL_ID}-${FEATURE_NAME}"
    local session_id="${TERMINAL_ID}-$(date +%Y%m%d%H%M%S)"

    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}     Claude Enhancer - Start New Feature${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo ""

    # Show configuration
    echo -e "${CE_COLOR_CYAN}Configuration:${CE_COLOR_RESET}"
    echo -e "  Feature:     ${CE_COLOR_GREEN}${FEATURE_NAME}${CE_COLOR_RESET}"
    echo -e "  Branch:      ${CE_COLOR_GREEN}${branch_name}${CE_COLOR_RESET}"
    echo -e "  Phase:       ${CE_COLOR_GREEN}${PHASE}${CE_COLOR_RESET}"
    echo -e "  Terminal:    ${CE_COLOR_GREEN}${TERMINAL_ID}${CE_COLOR_RESET}"
    echo -e "  Session:     ${CE_COLOR_GREEN}${session_id}${CE_COLOR_RESET}"
    if [[ -n "$DESCRIPTION" ]]; then
        echo -e "  Description: ${CE_COLOR_GREEN}${DESCRIPTION}${CE_COLOR_RESET}"
    fi
    echo ""

    # Step 1: Create feature branch
    echo -e "${CE_COLOR_CYAN}[1/5]${CE_COLOR_RESET} Creating feature branch..."
    if ! git checkout -b "${branch_name}"; then
        echo -e "${CE_COLOR_RED}Error: Failed to create branch${CE_COLOR_RESET}" >&2
        return 1
    fi
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Branch created: ${branch_name}"
    echo ""

    # Step 2: Initialize session directory
    echo -e "${CE_COLOR_CYAN}[2/5]${CE_COLOR_RESET} Initializing session state..."
    local session_dir=".workflow/state/sessions/${session_id}"
    mkdir -p "${session_dir}"
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Session directory created"
    echo ""

    # Step 3: Create session manifest
    echo -e "${CE_COLOR_CYAN}[3/5]${CE_COLOR_RESET} Creating session manifest..."
    local timestamp=$(date -Iseconds)
    cat > "${session_dir}/manifest.yml" <<EOF
session_id: ${session_id}
terminal_id: ${TERMINAL_ID}
feature_name: ${FEATURE_NAME}
branch_name: ${branch_name}
description: "${DESCRIPTION}"
phase: ${PHASE}
status: active
created_at: ${timestamp}
updated_at: ${timestamp}
commits: []
gates_passed: []
EOF
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Session manifest created"
    echo ""

    # Step 4: Update phase marker
    echo -e "${CE_COLOR_CYAN}[4/5]${CE_COLOR_RESET} Setting phase marker..."
    echo "${PHASE}" > .workflow/state/current_phase
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Phase set to ${PHASE}"
    echo ""

    # Step 5: Update active branches registry
    echo -e "${CE_COLOR_CYAN}[5/5]${CE_COLOR_RESET} Registering active branch..."
    local branches_file=".workflow/state/active_branches.yml"
    if [[ ! -f "${branches_file}" ]]; then
        echo "branches: []" > "${branches_file}"
    fi

    # Add branch to registry (simple append for now)
    cat >> "${branches_file}" <<EOF
  - branch: ${branch_name}
    terminal: ${TERMINAL_ID}
    session: ${session_id}
    phase: ${PHASE}
    started: ${timestamp}
EOF
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Branch registered"
    echo ""

    # Success message
    echo -e "${CE_COLOR_GREEN}===================================================${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_GREEN}     Feature branch created successfully!${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_GREEN}===================================================${CE_COLOR_RESET}"
    echo ""

    # Show next steps
    echo -e "${CE_COLOR_CYAN}Next Steps:${CE_COLOR_RESET}"
    echo ""

    case "$PHASE" in
        P0)
            echo -e "  ${CE_COLOR_YELLOW}Phase P0: Discovery${CE_COLOR_RESET}"
            echo -e "  ✓ Create technical spike documentation"
            echo -e "  ✓ Validate feasibility"
            echo -e "  ✓ Document findings"
            echo ""
            echo -e "  Run: ${CE_COLOR_CYAN}ce validate${CE_COLOR_RESET} to check phase requirements"
            echo -e "  Run: ${CE_COLOR_CYAN}ce next${CE_COLOR_RESET} to move to P1 when ready"
            ;;
        P1)
            echo -e "  ${CE_COLOR_YELLOW}Phase P1: Planning${CE_COLOR_RESET}"
            echo -e "  ✓ Create PLAN.md with requirements"
            echo -e "  ✓ Design architecture"
            echo -e "  ✓ Estimate effort"
            echo ""
            echo -e "  Run: ${CE_COLOR_CYAN}ce validate${CE_COLOR_RESET} to check phase requirements"
            echo -e "  Run: ${CE_COLOR_CYAN}ce next${CE_COLOR_RESET} to move to P2 when ready"
            ;;
        P2)
            echo -e "  ${CE_COLOR_YELLOW}Phase P2: Skeleton${CE_COLOR_RESET}"
            echo -e "  ✓ Create directory structure"
            echo -e "  ✓ Define interfaces"
            echo -e "  ✓ Setup configuration"
            echo ""
            echo -e "  Run: ${CE_COLOR_CYAN}ce validate${CE_COLOR_RESET} to check phase requirements"
            echo -e "  Run: ${CE_COLOR_CYAN}ce next${CE_COLOR_RESET} to move to P3 when ready"
            ;;
        P3)
            echo -e "  ${CE_COLOR_YELLOW}Phase P3: Implementation${CE_COLOR_RESET}"
            echo -e "  ✓ Implement core logic"
            echo -e "  ✓ Write unit tests"
            echo -e "  ✓ Add error handling"
            echo ""
            echo -e "  Run: ${CE_COLOR_CYAN}ce validate${CE_COLOR_RESET} to check code quality"
            echo -e "  Run: ${CE_COLOR_CYAN}ce next${CE_COLOR_RESET} to move to P4 when ready"
            ;;
        *)
            echo -e "  Run: ${CE_COLOR_CYAN}ce status${CE_COLOR_RESET} to see current status"
            echo -e "  Run: ${CE_COLOR_CYAN}ce validate${CE_COLOR_RESET} to check phase requirements"
            echo -e "  Run: ${CE_COLOR_CYAN}ce next${CE_COLOR_RESET} to advance to next phase"
            ;;
    esac

    echo ""
    echo -e "${CE_COLOR_CYAN}Quick Commands:${CE_COLOR_RESET}"
    echo -e "  ${CE_COLOR_CYAN}ce status${CE_COLOR_RESET}      - Show current status"
    echo -e "  ${CE_COLOR_CYAN}ce validate${CE_COLOR_RESET}    - Run quality gates"
    echo -e "  ${CE_COLOR_CYAN}ce next${CE_COLOR_RESET}        - Move to next phase"
    echo ""

    return 0
}

cmd_start_main() {
    # Main entry point for start command

    # Check for help
    if [[ $# -gt 0 ]] && [[ "$1" == "--help" || "$1" == "-h" ]]; then
        cmd_start_help
        exit 0
    fi

    # Ensure we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${CE_COLOR_RED}Error: Not a git repository${CE_COLOR_RESET}" >&2
        echo -e "${CE_COLOR_YELLOW}Run 'git init' first or cd to a git repository${CE_COLOR_RESET}" >&2
        exit 1
    fi

    # Ensure .workflow directory exists
    if [[ ! -d ".workflow" ]]; then
        echo -e "${CE_COLOR_RED}Error: Not a Claude Enhancer project${CE_COLOR_RESET}" >&2
        echo -e "${CE_COLOR_YELLOW}Run 'ce init' first to setup Claude Enhancer${CE_COLOR_RESET}" >&2
        exit 1
    fi

    # Parse arguments
    if ! cmd_start_parse_args "$@"; then
        exit 1
    fi

    # Validate inputs
    if ! cmd_start_validate; then
        exit 1
    fi

    # Execute command
    if ! cmd_start_execute; then
        echo ""
        echo -e "${CE_COLOR_RED}Failed to create feature branch${CE_COLOR_RESET}" >&2
        exit 1
    fi

    exit 0
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cmd_start_main "$@"
fi
