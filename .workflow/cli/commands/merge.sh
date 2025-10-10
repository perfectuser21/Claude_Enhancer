#!/usr/bin/env bash
set -euo pipefail

# Command: ce merge
# Purpose: Merge branch to main

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib"

source "${LIB_DIR}/common.sh"
source "${LIB_DIR}/git_operations.sh"

cmd_merge_help() {
    cat <<'EOF'
Usage: ce merge <branch> [options]

Merge feature branch to main.

Arguments:
  <branch>       Branch to merge (required)

Options:
  --no-delete    Keep branch after merge
  --no-healthcheck Skip health check
  --squash       Squash commits

Examples:
  ce merge feature/P3-t1-login
  ce merge feature/P3-t2-payment --squash

See also: ce publish, ce clean
EOF
}

cmd_merge_main() {
    local branch=""
    local delete=true
    local healthcheck=true
    local squash=false

    [[ $# -eq 0 ]] && { cmd_merge_help; exit 1; }

    branch="$1"
    shift

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-delete) delete=false; shift ;;
            --no-healthcheck) healthcheck=false; shift ;;
            --squash) squash=true; shift ;;
            --help|-h) cmd_merge_help; exit 0 ;;
            *) echo -e "${CE_COLOR_RED}Error: Unknown option: $1${CE_COLOR_RESET}" >&2; cmd_merge_help; exit 1 ;;
        esac
    done

    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}     Claude Enhancer - Merge Branch${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "  Branch: ${CE_COLOR_GREEN}${branch}${CE_COLOR_RESET}"
    echo ""

    if ! git show-ref --verify --quiet "refs/heads/${branch}"; then
        echo -e "${CE_COLOR_RED}Error: Branch does not exist: ${branch}${CE_COLOR_RESET}" >&2
        exit 1
    fi

    if [[ "$(git rev-parse --abbrev-ref HEAD)" == "$branch" ]]; then
        git checkout main
    fi

    echo -e "${CE_COLOR_CYAN}[1/3]${CE_COLOR_RESET} Fetching latest changes..."
    git fetch origin main
    echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Fetch complete"

    echo ""
    echo -e "${CE_COLOR_CYAN}[2/3]${CE_COLOR_RESET} Merging branch..."
    local merge_opts=("--no-ff")
    [[ "$squash" == "true" ]] && merge_opts=("--squash")

    if git merge "${merge_opts[@]}" "$branch"; then
        echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Merge successful"
    else
        echo -e "${CE_COLOR_RED}Merge failed - please resolve conflicts${CE_COLOR_RESET}" >&2
        exit 1
    fi

    echo ""
    echo -e "${CE_COLOR_CYAN}[3/3]${CE_COLOR_RESET} Pushing to remote..."
    if git push origin main; then
        echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Pushed to main"
    fi

    if [[ "$delete" == "true" ]]; then
        echo ""
        echo -e "${CE_COLOR_CYAN}Deleting merged branch...${CE_COLOR_RESET}"
        git branch -d "$branch"
        git push origin --delete "$branch" 2>/dev/null || true
        echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Branch deleted"
    fi

    echo ""
    echo -e "${CE_COLOR_GREEN}===== Merge Complete! =====${CE_COLOR_RESET}"
    echo ""
    exit 0
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cmd_merge_main "$@"
fi
