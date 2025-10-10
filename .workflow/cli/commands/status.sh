#!/usr/bin/env bash
set -euo pipefail

# Command: ce status
# Purpose: Display multi-terminal development status

# Source required libraries
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib"

source "${LIB_DIR}/common.sh"
source "${LIB_DIR}/state_manager.sh"
source "${LIB_DIR}/phase_manager.sh"
source "${LIB_DIR}/conflict_detector.sh"

cmd_status_help() {
    cat <<'EOF'
Usage: ce status [options]

Display status of all active development sessions.

Options:
  --verbose, -v  Show detailed information
  --terminal <T> Show specific terminal only
  --json         Output in JSON format

Examples:
  ce status
  ce status --verbose
  ce status --terminal t1

See also: ce start, ce clean
EOF
}

cmd_status_collect_data() {
    # Collect status data from all sessions
    local terminal_filter="${1:-}"

    # Get current branch
    local current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "none")

    # Get current phase
    local current_phase="unknown"
    if [[ -f ".workflow/state/current_phase" ]]; then
        current_phase=$(cat .workflow/state/current_phase)
    fi

    # Collect active sessions
    local sessions=()
    if [[ -d ".workflow/state/sessions" ]]; then
        while IFS= read -r -d '' session_dir; do
            local session_id=$(basename "$session_dir")

            # Apply terminal filter if specified
            if [[ -n "$terminal_filter" ]] && [[ ! "$session_id" =~ ^${terminal_filter}- ]]; then
                continue
            fi

            if [[ -f "$session_dir/manifest.yml" ]]; then
                sessions+=("$session_dir/manifest.yml")
            fi
        done < <(find .workflow/state/sessions -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null)
    fi

    # Get git status
    local git_status=""
    if git rev-parse --git-dir &>/dev/null; then
        git_status=$(git status --porcelain 2>/dev/null || echo "")
    fi

    # Count modified files
    local modified_count=0
    local staged_count=0
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        modified_count=$((modified_count + 1))
        [[ "$line" =~ ^[MADRC] ]] && staged_count=$((staged_count + 1))
    done <<< "$git_status"

    # Export collected data
    export CE_STATUS_CURRENT_BRANCH="$current_branch"
    export CE_STATUS_CURRENT_PHASE="$current_phase"
    export CE_STATUS_MODIFIED_COUNT="$modified_count"
    export CE_STATUS_STAGED_COUNT="$staged_count"
    export CE_STATUS_SESSION_COUNT="${#sessions[@]}"
    export CE_STATUS_SESSIONS="${sessions[*]}"
}

cmd_status_format_output() {
    # Format status output based on options
    local verbose="${1:-false}"
    local format="${2:-human}"

    if [[ "$format" == "json" ]]; then
        cmd_status_format_json
        return 0
    fi

    # Human-readable format
    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}     Claude Enhancer - Development Status${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo ""

    # Current state
    echo -e "${CE_COLOR_CYAN}Current State:${CE_COLOR_RESET}"
    echo -e "  Branch:       ${CE_COLOR_GREEN}${CE_STATUS_CURRENT_BRANCH}${CE_COLOR_RESET}"
    echo -e "  Phase:        ${CE_COLOR_GREEN}${CE_STATUS_CURRENT_PHASE}${CE_COLOR_RESET}"
    echo -e "  Modified:     ${CE_COLOR_YELLOW}${CE_STATUS_MODIFIED_COUNT} files${CE_COLOR_RESET}"
    echo -e "  Staged:       ${CE_COLOR_YELLOW}${CE_STATUS_STAGED_COUNT} files${CE_COLOR_RESET}"
    echo ""

    # Active sessions
    if [[ ${CE_STATUS_SESSION_COUNT} -eq 0 ]]; then
        echo -e "${CE_COLOR_CYAN}Active Sessions:${CE_COLOR_RESET}"
        echo -e "  ${CE_COLOR_YELLOW}No active sessions${CE_COLOR_RESET}"
        echo ""
    else
        echo -e "${CE_COLOR_CYAN}Active Sessions (${CE_STATUS_SESSION_COUNT}):${CE_COLOR_RESET}"
        echo ""

        local sessions_array=($CE_STATUS_SESSIONS)
        for manifest_file in "${sessions_array[@]}"; do
            cmd_status_show_session "$manifest_file" "$verbose"
        done
    fi

    # Git status summary
    if [[ ${CE_STATUS_MODIFIED_COUNT} -gt 0 ]]; then
        echo -e "${CE_COLOR_CYAN}Modified Files:${CE_COLOR_RESET}"
        git status --short 2>/dev/null | head -10
        if [[ ${CE_STATUS_MODIFIED_COUNT} -gt 10 ]]; then
            echo -e "${CE_COLOR_YELLOW}  ... and $((CE_STATUS_MODIFIED_COUNT - 10)) more${CE_COLOR_RESET}"
        fi
        echo ""
    fi

    # Quick actions
    echo -e "${CE_COLOR_CYAN}Quick Actions:${CE_COLOR_RESET}"
    echo -e "  ${CE_COLOR_CYAN}ce validate${CE_COLOR_RESET}  - Run quality gates"
    echo -e "  ${CE_COLOR_CYAN}ce next${CE_COLOR_RESET}      - Move to next phase"
    echo -e "  ${CE_COLOR_CYAN}ce publish${CE_COLOR_RESET}   - Create pull request"
    echo ""
}

cmd_status_show_session() {
    # Show individual session details
    local manifest_file="$1"
    local verbose="${2:-false}"

    # Parse manifest (basic YAML parsing)
    local session_id=$(grep "^session_id:" "$manifest_file" | cut -d: -f2- | xargs)
    local terminal_id=$(grep "^terminal_id:" "$manifest_file" | cut -d: -f2- | xargs)
    local feature_name=$(grep "^feature_name:" "$manifest_file" | cut -d: -f2- | xargs)
    local branch_name=$(grep "^branch_name:" "$manifest_file" | cut -d: -f2- | xargs)
    local phase=$(grep "^phase:" "$manifest_file" | cut -d: -f2- | xargs)
    local status=$(grep "^status:" "$manifest_file" | cut -d: -f2- | xargs)
    local created_at=$(grep "^created_at:" "$manifest_file" | cut -d: -f2- | xargs)

    # Calculate duration
    local created_timestamp=$(date -d "$created_at" +%s 2>/dev/null || echo "0")
    local now_timestamp=$(date +%s)
    local duration=$((now_timestamp - created_timestamp))
    local duration_str=$(ce_format_duration "$duration")

    # Session marker
    local marker="  "
    if [[ "$branch_name" == "$CE_STATUS_CURRENT_BRANCH" ]]; then
        marker="${CE_COLOR_GREEN}→ ${CE_COLOR_RESET}"
    else
        marker="  "
    fi

    # Basic info
    echo -e "${marker}${CE_COLOR_GREEN}${terminal_id}${CE_COLOR_RESET}: ${feature_name}"
    echo -e "    Branch:   ${branch_name}"
    echo -e "    Phase:    ${phase} (${status})"
    echo -e "    Duration: ${duration_str}"

    # Verbose info
    if [[ "$verbose" == "true" ]]; then
        echo -e "    Session:  ${session_id}"
        echo -e "    Created:  ${created_at}"

        # Check for conflicts
        if [[ "$branch_name" != "main" ]] && [[ "$branch_name" != "develop" ]]; then
            local conflict_check=$(git diff --name-only "$branch_name...main" 2>/dev/null | wc -l)
            if [[ $conflict_check -gt 0 ]]; then
                echo -e "    Diverged: ${CE_COLOR_YELLOW}${conflict_check} files differ from main${CE_COLOR_RESET}"
            fi
        fi
    fi

    echo ""
}

cmd_status_format_json() {
    # Format status as JSON
    local sessions_json="[]"

    # Build JSON for sessions
    if [[ ${CE_STATUS_SESSION_COUNT} -gt 0 ]]; then
        local sessions_array=($CE_STATUS_SESSIONS)
        local session_items=()

        for manifest_file in "${sessions_array[@]}"; do
            local session_id=$(grep "^session_id:" "$manifest_file" | cut -d: -f2- | xargs)
            local terminal_id=$(grep "^terminal_id:" "$manifest_file" | cut -d: -f2- | xargs)
            local feature_name=$(grep "^feature_name:" "$manifest_file" | cut -d: -f2- | xargs)
            local branch_name=$(grep "^branch_name:" "$manifest_file" | cut -d: -f2- | xargs)
            local phase=$(grep "^phase:" "$manifest_file" | cut -d: -f2- | xargs)
            local status=$(grep "^status:" "$manifest_file" | cut -d: -f2- | xargs)

            session_items+=("    {\"session_id\":\"$session_id\",\"terminal_id\":\"$terminal_id\",\"feature_name\":\"$feature_name\",\"branch_name\":\"$branch_name\",\"phase\":\"$phase\",\"status\":\"$status\"}")
        done

        sessions_json="[\n$(IFS=$',\n'; echo "${session_items[*]}")\n  ]"
    fi

    cat <<EOF
{
  "current_branch": "${CE_STATUS_CURRENT_BRANCH}",
  "current_phase": "${CE_STATUS_CURRENT_PHASE}",
  "modified_files": ${CE_STATUS_MODIFIED_COUNT},
  "staged_files": ${CE_STATUS_STAGED_COUNT},
  "active_sessions": ${CE_STATUS_SESSION_COUNT},
  "sessions": ${sessions_json}
}
EOF
}

cmd_status_main() {
    # Main entry point for status command

    local verbose=false
    local terminal_id=""
    local format="human"

    # Parse options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose|-v)
                verbose=true
                shift
                ;;
            --terminal)
                terminal_id="$2"
                shift 2
                ;;
            --json)
                format="json"
                shift
                ;;
            --help|-h)
                cmd_status_help
                exit 0
                ;;
            *)
                echo -e "${CE_COLOR_RED}Error: Unknown option: $1${CE_COLOR_RESET}" >&2
                cmd_status_help
                exit 1
                ;;
        esac
    done

    # Ensure we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${CE_COLOR_RED}Error: Not a git repository${CE_COLOR_RESET}" >&2
        exit 1
    fi

    # Ensure .workflow directory exists
    if [[ ! -d ".workflow" ]]; then
        echo -e "${CE_COLOR_RED}Error: Not a Claude Enhancer project${CE_COLOR_RESET}" >&2
        echo -e "${CE_COLOR_YELLOW}Run 'ce start <feature>' to begin${CE_COLOR_RESET}" >&2
        exit 1
    fi

    # Collect status data
    cmd_status_collect_data "$terminal_id"

    # Format and display output
    cmd_status_format_output "$verbose" "$format"

    exit 0
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cmd_status_main "$@"
fi
