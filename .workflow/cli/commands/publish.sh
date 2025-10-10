#!/usr/bin/env bash
set -euo pipefail

# Command: ce publish
# Purpose: Publish feature branch as PR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib"

source "${LIB_DIR}/common.sh"
source "${LIB_DIR}/pr_automator.sh"
source "${LIB_DIR}/git_operations.sh"

cmd_publish_help() {
    cat <<'EOF'
Usage: ce publish [options]

Publish feature branch and create pull request.

Options:
  --draft        Create as draft PR
  --no-push      Skip git push
  --base <branch> Target branch (default: main)

Examples:
  ce publish
  ce publish --draft
  ce publish --base develop

See also: ce validate, ce merge
EOF
}

cmd_publish_main() {
    local draft=false
    local push=true
    local base="main"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --draft) draft=true; shift ;;
            --no-push) push=false; shift ;;
            --base) base="$2"; shift 2 ;;
            --help|-h) cmd_publish_help; exit 0 ;;
            *) echo -e "${CE_COLOR_RED}Error: Unknown option: $1${CE_COLOR_RESET}" >&2; cmd_publish_help; exit 1 ;;
        esac
    done

    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${CE_COLOR_RED}Error: Not a git repository${CE_COLOR_RESET}" >&2
        exit 1
    fi

    local current_branch=$(git rev-parse --abbrev-ref HEAD)

    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}     Claude Enhancer - Publish PR${CE_COLOR_RESET}"
    echo -e "${CE_COLOR_BLUE}===================================================${CE_COLOR_RESET}"
    echo -e "  Branch: ${CE_COLOR_GREEN}${current_branch}${CE_COLOR_RESET}"
    echo -e "  Base:   ${CE_COLOR_GREEN}${base}${CE_COLOR_RESET}"
    echo -e "  Draft:  ${CE_COLOR_YELLOW}${draft}${CE_COLOR_RESET}"
    echo ""

    if [[ "$push" == "true" ]]; then
        echo -e "${CE_COLOR_CYAN}[1/2]${CE_COLOR_RESET} Pushing branch to remote..."
        if git push -u origin "$current_branch"; then
            echo -e "${CE_COLOR_GREEN}✓${CE_COLOR_RESET} Branch pushed"
        else
            echo -e "${CE_COLOR_RED}Failed to push branch${CE_COLOR_RESET}" >&2
            exit 1
        fi
    fi

    echo ""
    echo -e "${CE_COLOR_CYAN}[2/2]${CE_COLOR_RESET} Creating pull request..."

    local pr_opts=("--base=${base}")
    [[ "$draft" == "true" ]] && pr_opts+=("--draft")

    if pr_url=$(ce_pr_create "${pr_opts[@]}" 2>&1); then
        echo ""
        echo -e "${CE_COLOR_GREEN}===== PR Created Successfully! =====${CE_COLOR_RESET}"
        echo ""
        echo -e "${CE_COLOR_BLUE}PR URL:${CE_COLOR_RESET} ${pr_url}"
        echo ""
        exit 0
    else
        echo -e "${CE_COLOR_RED}Failed to create PR${CE_COLOR_RESET}" >&2
        exit 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cmd_publish_main "$@"
fi
