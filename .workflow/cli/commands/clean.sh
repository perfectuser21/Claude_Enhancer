#!/usr/bin/env bash
set -euo pipefail

# Command: ce clean
# Purpose: Clean up merged branches

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib"

source "${LIB_DIR}/common.sh"
source "${LIB_DIR}/branch_manager.sh"
source "${LIB_DIR}/state_manager.sh"

cmd_clean_help() {
    cat <<'EOF'
Usage: ce clean [options]

Clean up merged branches and stale sessions.

Options:
  --dry-run      Show what would be cleaned
  --force        Force cleanup
  --all          Clean all sessions

Examples:
  ce clean
  ce clean --dry-run
  ce clean --all

See also: ce status, ce merge
EOF
}

cmd_clean_main() {
    local dry_run=false
    local force=false
    local all=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run) dry_run=true; shift ;;
            --force) force=true; shift ;;
            --all) all=true; shift ;;
            --help|-h) cmd_clean_help; exit 0 ;;
            *) echo -e "${CE_COLOR_RED}Error: Unknown option: $1${CE_COLOR_RESET}" >&2; cmd_clean_help; exit 1 ;;
        esac
    done

    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}     Claude Enhancer - Cleanup${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo ""

    [[ "$dry_run" == "true" ]] && echo -e "${CE_COLOR_YELLOW}DRY RUN MODE - No changes will be made${CE_COLOR_RESET}" && echo ""

    local merged_branches=()
    echo -e "${CE_COLOR_CYAN}Finding merged branches...${CE_COLOR_RESET}"

    while IFS= read -r branch; do
        [[ -z "$branch" ]] && continue
        [[ "$branch" =~ ^(main|master|develop)$ ]] && continue
        merged_branches+=("$branch")
    done < <(git branch --merged main 2>/dev/null | sed 's/^[* ]*//')

    if [[ ${#merged_branches[@]} -eq 0 ]]; then
        echo -e "${CE_COLOR_GREEN}No merged branches to clean${CE_COLOR_RESET}"
    else
        echo -e "${CE_COLOR_YELLOW}Found ${#merged_branches[@]} merged branches:${CE_COLOR_RESET}"
        for branch in "${merged_branches[@]}"; do
            echo "  - $branch"
        done
        echo ""

        if [[ "$dry_run" != "true" ]]; then
            if [[ "$force" != "true" ]] && ! ce_confirm "Delete these branches?"; then
                echo "Cancelled"
                exit 0
            fi

            for branch in "${merged_branches[@]}"; do
                echo -n "Deleting $branch... "
                if git branch -d "$branch" 2>/dev/null; then
                    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET}"
                else
                    echo -e "${CE_COLOR_RED}✗${CE_COLOR_RESET}"
                fi
            done
        fi
    fi

    echo ""
    echo -e "${CE_COLOR_CYAN}Cleaning stale sessions...${CE_COLOR_RESET}"

    if [[ -d ".workflow/state/sessions" ]]; then
        local stale_count=0
        for session_file in .workflow/state/sessions/*.yml; do
            [[ ! -f "$session_file" ]] && continue

            local last_update=$(stat -c %Y "$session_file" 2>/dev/null || echo "0")
            local now=$(date +%s)
            local age=$((now - last_update))

            if [[ $age -gt 604800 ]]; then  # 7 days
                ((stale_count++))
                echo "  - $(basename "$session_file") ($(((age / 86400))) days old)"

                if [[ "$dry_run" != "true" ]] && ([[ "$force" == "true" ]] || [[ "$all" == "true" ]]); then
                    rm -f "$session_file"
                fi
            fi
        done

        if [[ $stale_count -eq 0 ]]; then
            echo -e "${CE_COLOR_GREEN}No stale sessions found${CE_COLOR_RESET}"
        fi
    fi

    echo ""
    echo -e "${CE_COLOR_GREEN}===== Cleanup Complete! =====${CE_COLOR_RESET}"
    echo ""
    exit 0
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cmd_clean_main "$@"
fi
