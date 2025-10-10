#!/usr/bin/env bash
# ce - Claude Enhancer CLI
# Unified command-line interface for workflow, branch, and session management
set -euo pipefail

# ============================================================================
# METADATA & CONFIGURATION
# ============================================================================

CE_VERSION="1.0.0"
CE_BUILD_DATE="2025-10-10"
CE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Global options
CE_VERBOSE=${CE_VERBOSE:-false}
CE_DEBUG=${CE_DEBUG:-false}
CE_TERMINAL_ID=${CE_TERMINAL_ID:-}
CE_COLOR=${CE_COLOR:-auto}

# ============================================================================
# LIBRARY LOADING
# ============================================================================

# Load all library files in dependency order
ce_load_libraries() {
    local lib_dir="${CE_ROOT}/.workflow/cli/lib"

    # Core libraries (must be loaded first)
    local core_libs=(
        "common.sh"
        "state_manager.sh"
        "phase_manager.sh"
        "branch_manager.sh"
        "git_operations.sh"
        "gate_integrator.sh"
        "pr_automator.sh"
        "conflict_detector.sh"
    )

    # Load each library
    for lib in "${core_libs[@]}"; do
        local lib_path="${lib_dir}/${lib}"
        if [[ -f "${lib_path}" ]]; then
            # shellcheck source=/dev/null
            source "${lib_path}"
        else
            echo "Warning: Library ${lib} not found at ${lib_path}" >&2
        fi
    done

    return 0
}

# Load specific command script
ce_load_command() {
    local command="$1"
    local cmd_dir="${CE_ROOT}/.workflow/cli/commands"
    local cmd_file="${cmd_dir}/${command}.sh"

    if [[ ! -f "${cmd_file}" ]]; then
        echo "Error: Command '${command}' not found" >&2
        return 1
    fi

    # shellcheck source=/dev/null
    source "${cmd_file}"
    return 0
}

# ============================================================================
# ENVIRONMENT INITIALIZATION
# ============================================================================

# Initialize environment variables
ce_init_environment() {
    # Set CE environment variables
    export CE_ROOT
    export CE_VERSION
    export CE_VERBOSE
    export CE_DEBUG

    # Detect and set terminal ID
    ce_detect_terminal_id
    export CE_TERMINAL_ID

    # Set color mode
    if [[ "${CE_COLOR}" == "auto" ]]; then
        if [[ -t 1 ]]; then
            CE_COLOR="always"
        else
            CE_COLOR="never"
        fi
    fi
    export CE_COLOR

    # Set state directories
    export CE_STATE_DIR="${CE_ROOT}/.workflow/cli/state"
    export CE_SESSION_DIR="${CE_STATE_DIR}/sessions"
    export CE_BRANCH_DIR="${CE_STATE_DIR}/branches"
    export CE_LOCK_DIR="${CE_STATE_DIR}/locks"

    # Create directories if they don't exist
    mkdir -p "${CE_SESSION_DIR}" "${CE_BRANCH_DIR}" "${CE_LOCK_DIR}" 2>/dev/null || true

    return 0
}

# Auto-detect or use CE_TERMINAL_ID
ce_detect_terminal_id() {
    # If already set, validate and use it
    if [[ -n "${CE_TERMINAL_ID}" ]]; then
        if [[ ! "${CE_TERMINAL_ID}" =~ ^t[0-9]+$ ]]; then
            echo "Warning: Invalid CE_TERMINAL_ID format: ${CE_TERMINAL_ID}" >&2
            echo "Expected format: t1, t2, t3, etc." >&2
            CE_TERMINAL_ID=""
        else
            return 0
        fi
    fi

    # Try to auto-detect from various sources
    local detected_id=""

    # Method 1: Check TERM_SESSION_ID (some terminals)
    if [[ -n "${TERM_SESSION_ID:-}" ]]; then
        detected_id="t${TERM_SESSION_ID}"
    fi

    # Method 2: Check TTY number
    if [[ -z "${detected_id}" && -t 0 ]]; then
        local tty_num
        tty_num=$(tty | grep -oP '\d+$' || echo "")
        if [[ -n "${tty_num}" ]]; then
            detected_id="t${tty_num}"
        fi
    fi

    # Method 3: Check tmux/screen pane
    if [[ -z "${detected_id}" ]]; then
        if [[ -n "${TMUX_PANE:-}" ]]; then
            local pane_num="${TMUX_PANE##*%}"
            detected_id="t${pane_num}"
        elif [[ -n "${STY:-}" ]]; then
            local screen_num="${STY##*.}"
            detected_id="t${screen_num}"
        fi
    fi

    # Method 4: Default to t1
    if [[ -z "${detected_id}" ]]; then
        detected_id="t1"
    fi

    CE_TERMINAL_ID="${detected_id}"

    if [[ "${CE_DEBUG}" == "true" ]]; then
        echo "Auto-detected terminal ID: ${CE_TERMINAL_ID}" >&2
    fi

    return 0
}

# Validate environment requirements
ce_validate_environment() {
    local errors=0

    # Check if we're in a git repository
    if ! git rev-parse --git-dir &>/dev/null; then
        echo "Error: Not in a git repository" >&2
        ((errors++))
    fi

    # Check required commands
    local required_cmds=(git bash)
    for cmd in "${required_cmds[@]}"; do
        if ! command -v "${cmd}" &>/dev/null; then
            echo "Error: Required command not found: ${cmd}" >&2
            ((errors++))
        fi
    done

    # Check bash version (need 4.0+)
    if [[ "${BASH_VERSINFO[0]}" -lt 4 ]]; then
        echo "Error: Bash 4.0 or higher required (found ${BASH_VERSION})" >&2
        ((errors++))
    fi

    # Check for .workflow directory
    if [[ ! -d "${CE_ROOT}/.workflow" ]]; then
        echo "Error: Claude Enhancer project structure not found" >&2
        echo "Expected .workflow directory in: ${CE_ROOT}" >&2
        ((errors++))
    fi

    # Optional but recommended tools
    local optional_cmds=(jq yq gh)
    for cmd in "${optional_cmds[@]}"; do
        if ! command -v "${cmd}" &>/dev/null; then
            if [[ "${CE_VERBOSE}" == "true" ]]; then
                echo "Warning: Optional command not found: ${cmd} (some features may be limited)" >&2
            fi
        fi
    done

    if [[ ${errors} -gt 0 ]]; then
        echo "Error: Environment validation failed with ${errors} error(s)" >&2
        return 1
    fi

    return 0
}

# ============================================================================
# COMMAND ROUTING
# ============================================================================

# Route to appropriate command handler
ce_route_command() {
    local command="${1:-}"
    shift || true

    if [[ -z "${command}" ]]; then
        ce_show_help
        exit 0
    fi

    # Map command aliases to actual commands
    case "${command}" in
        init|start)
            ce_load_command "start" && cmd_start_main "$@"
            ;;
        status|st)
            ce_load_command "status" && cmd_status_main "$@"
            ;;
        next|advance)
            ce_load_command "next" && cmd_next_main "$@"
            ;;
        phase|ph)
            ce_load_command "phase" && cmd_phase_main "$@"
            ;;
        validate|check)
            ce_load_command "validate" && cmd_validate_main "$@"
            ;;
        publish|pub)
            ce_load_command "publish" && cmd_publish_main "$@"
            ;;
        merge|mr)
            ce_load_command "merge" && cmd_merge_main "$@"
            ;;
        clean|cleanup)
            ce_load_command "clean" && cmd_clean_main "$@"
            ;;
        branch|br)
            # Branch subcommands handled by branch command
            ce_load_command "branch" && cmd_branch_main "$@"
            ;;
        pr)
            # PR subcommands handled by pr command
            ce_load_command "pr" && cmd_pr_main "$@"
            ;;
        gate|gates)
            # Gate subcommands handled by gate command
            ce_load_command "gate" && cmd_gate_main "$@"
            ;;
        help)
            ce_show_help
            ;;
        version)
            ce_show_version
            ;;
        *)
            echo "Error: Unknown command: ${command}" >&2
            echo "Use 'ce --help' for available commands" >&2
            exit 1
            ;;
    esac
}

# ============================================================================
# HELP & VERSION
# ============================================================================

# Display main help text
ce_show_help() {
    cat <<'EOF'
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    Claude Enhancer CLI v1.0.0                        ┃
┃          Multi-Terminal Development Workflow Automation              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

USAGE:
    ce [global-options] <command> [command-options] [arguments]

CORE COMMANDS:
    start <feature>         Start new feature branch with session tracking
    status                  Show multi-terminal development status
    next                    Advance to next workflow phase
    validate                Run quality gate validations
    publish                 Publish/merge completed work
    clean                   Cleanup stale sessions and branches

WORKFLOW COMMANDS:
    phase <name>            Jump to specific phase (P0-P7)
    merge <branches>        Merge multiple branches intelligently

BRANCH COMMANDS:
    branch list             List all active branches
    branch create <name>    Create new feature branch
    branch delete <name>    Delete branch and cleanup state
    branch metadata         Show/update branch metadata

PULL REQUEST COMMANDS:
    pr create               Create pull request from current branch
    pr update               Update PR description and metadata
    pr check                Validate PR readiness

QUALITY GATE COMMANDS:
    gate check              Run all quality gate validations
    gate score              Show quality gate scores
    gate report             Generate detailed gate report

GLOBAL OPTIONS:
    -h, --help              Show this help message
    -v, --version           Show version information
    --verbose               Enable verbose output
    --debug                 Enable debug mode (very verbose)
    --terminal <id>         Specify terminal ID (t1, t2, etc.)
    --no-color              Disable colored output
    --color <mode>          Color mode: auto, always, never

EXAMPLES:
    # Start new feature development
    ce start user-authentication
    ce start payment-api --terminal t2

    # Check status across all terminals
    ce status
    ce status --verbose
    ce status --terminal t1

    # Workflow progression
    ce next                 # Advance to next phase
    ce phase P4             # Jump directly to P4 (Testing)
    ce validate             # Run quality checks

    # Multi-terminal development
    # Terminal 1:
    ce start login-form
    # ... develop ...
    ce next && ce validate

    # Terminal 2 (simultaneously):
    ce start login-api --terminal t2
    # ... develop ...
    ce next && ce validate

    # Terminal 3 (integration):
    ce merge login-form login-api
    ce publish

    # Cleanup
    ce clean                # Remove stale sessions
    ce clean --terminal t2  # Clean specific terminal
    ce clean --force        # Force cleanup all

WORKFLOW PHASES:
    P0  Discovery       Technical spike and feasibility
    P1  Planning        Requirements analysis
    P2  Skeleton        Architecture design
    P3  Implementation  Feature development (default start)
    P4  Testing         Quality assurance
    P5  Review          Code review
    P6  Release         Documentation and deployment
    P7  Monitoring      Production monitoring

STATE MANAGEMENT:
    Sessions:   .workflow/cli/state/sessions/<terminal-id>.yml
    Branches:   .workflow/cli/state/branches/<branch-name>.yml
    Global:     .workflow/cli/state/global.state.yml
    Locks:      .workflow/cli/state/locks/<resource>.lock

ENVIRONMENT VARIABLES:
    CE_TERMINAL_ID          Terminal identifier (auto-detected if not set)
    CE_VERBOSE              Enable verbose output (true/false)
    CE_DEBUG                Enable debug mode (true/false)
    CE_COLOR                Color mode (auto/always/never)

CONFIGURATION:
    Edit: .workflow/cli/config.yml

DOCUMENTATION:
    Full Guide:         docs/CLI_GUIDE.md
    Architecture:       .workflow/cli/INFRASTRUCTURE_REPORT.md
    Troubleshooting:    docs/TROUBLESHOOTING_GUIDE.md

For command-specific help, use:
    ce <command> --help

Report issues at: https://github.com/your-org/claude-enhancer/issues

EOF
}

# Show version and build info
ce_show_version() {
    cat <<EOF
Claude Enhancer CLI v${CE_VERSION}
Build Date: ${CE_BUILD_DATE}
Installation: ${CE_ROOT}

System Information:
  Bash Version: ${BASH_VERSION}
  Git Version: $(git --version 2>/dev/null || echo "not installed")
  Terminal ID: ${CE_TERMINAL_ID:-auto-detect}
  Platform: $(uname -s) $(uname -m)

Optional Tools:
  jq: $(command -v jq &>/dev/null && echo "installed" || echo "not installed")
  yq: $(command -v yq &>/dev/null && echo "installed" || echo "not installed")
  gh: $(command -v gh &>/dev/null && echo "installed" || echo "not installed")

Configuration:
  State Dir: ${CE_STATE_DIR:-${CE_ROOT}/.workflow/cli/state}
  Debug Mode: ${CE_DEBUG}
  Verbose: ${CE_VERBOSE}
  Color: ${CE_COLOR}

For more information, run: ce --help
EOF
}

# ============================================================================
# ERROR HANDLING
# ============================================================================

# Global error handler
ce_handle_error() {
    local exit_code=$?
    local line_number=${1:-unknown}

    echo "Error: An error occurred at line ${line_number} (exit code: ${exit_code})" >&2

    if [[ "${CE_DEBUG}" == "true" ]]; then
        echo "Stack trace:" >&2
        local frame=0
        while caller $frame; do
            ((frame++))
        done
    fi

    # Cleanup before exit
    ce_cleanup_on_exit

    exit "${exit_code}"
}

# Cleanup on exit
ce_cleanup_on_exit() {
    # Remove temporary files if any
    if [[ -n "${CE_TEMP_FILES:-}" ]]; then
        for tmp_file in ${CE_TEMP_FILES}; do
            [[ -f "${tmp_file}" ]] && rm -f "${tmp_file}"
        done
    fi

    # Remove temporary directories if any
    if [[ -n "${CE_TEMP_DIRS:-}" ]]; then
        for tmp_dir in ${CE_TEMP_DIRS}; do
            [[ -d "${tmp_dir}" ]] && rm -rf "${tmp_dir}"
        done
    fi

    # Release any locks held by this process
    if [[ -n "${CE_LOCK_DIR:-}" && -d "${CE_LOCK_DIR}" ]]; then
        local pid=$$
        find "${CE_LOCK_DIR}" -name "*.lock" -exec grep -l "${pid}" {} \; 2>/dev/null | while read -r lock_file; do
            rm -f "${lock_file}"
        done
    fi

    return 0
}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

# Main orchestration function
ce_main() {
    # Set up error handling
    trap 'ce_handle_error ${LINENO}' ERR
    trap 'ce_cleanup_on_exit' EXIT

    # Parse global options first
    local args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                ce_show_help
                exit 0
                ;;
            -v|--version)
                ce_show_version
                exit 0
                ;;
            --verbose)
                CE_VERBOSE=true
                shift
                ;;
            --debug)
                CE_DEBUG=true
                CE_VERBOSE=true
                set -x
                shift
                ;;
            --terminal)
                if [[ -n "${2:-}" && ! "${2}" =~ ^- ]]; then
                    CE_TERMINAL_ID="$2"
                    shift 2
                else
                    echo "Error: --terminal requires a terminal ID (e.g., t1, t2)" >&2
                    exit 1
                fi
                ;;
            --no-color)
                CE_COLOR="never"
                shift
                ;;
            --color)
                if [[ -n "${2:-}" && ! "${2}" =~ ^- ]]; then
                    CE_COLOR="$2"
                    shift 2
                else
                    CE_COLOR="always"
                    shift
                fi
                ;;
            -*)
                echo "Error: Unknown option: $1" >&2
                echo "Use 'ce --help' for usage information" >&2
                exit 1
                ;;
            *)
                # Not a global option, save for command routing
                args+=("$1")
                shift
                ;;
        esac
    done

    # Initialize environment
    ce_init_environment

    # Load all libraries
    ce_load_libraries

    # Validate environment before executing commands
    if ! ce_validate_environment; then
        echo "Error: Environment validation failed" >&2
        echo "Fix the errors above and try again" >&2
        exit 1
    fi

    # Route to appropriate command with remaining args
    ce_route_command "${args[@]}"
}

# ============================================================================
# EXECUTION
# ============================================================================

# Only run main if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ce_main "$@"
fi
