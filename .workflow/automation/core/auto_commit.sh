#!/usr/bin/env bash
# Auto Commit Script for Claude Enhancer v5.4.0
# Purpose: Automated git commit with quality checks and Phase validation
# Used by: Claude automation, CI/CD pipeline

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"

# Configuration
COMMIT_MESSAGE_MIN_LENGTH=10
DRY_RUN="${CE_DRY_RUN:-0}"

# Functions

check_prerequisites() {
    # Verify git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not a git repository"
        return 1
    fi

    # Verify hooks are installed
    if [[ ! -f ".git/hooks/pre-commit" ]]; then
        log_warning "pre-commit hook not installed"
    fi

    return 0
}

validate_commit_message() {
    local message="$1"

    # Check minimum length
    if [[ ${#message} -lt ${COMMIT_MESSAGE_MIN_LENGTH} ]]; then
        log_error "Commit message too short (minimum ${COMMIT_MESSAGE_MIN_LENGTH} characters)"
        return 1
    fi

    # Check for Phase marker (P0-P7)
    if ! echo "$message" | grep -qE '\[P[0-7]\]|\bP[0-7]\b|Phase [0-7]'; then
        log_warning "Commit message missing Phase marker"
    fi

    return 0
}

stage_changes() {
    local files=("$@")

    if [[ ${#files[@]} -eq 0 ]]; then
        log_info "No specific files, staging all changes"
        git add -A
    else
        log_info "Staging ${#files[@]} files"
        for file in "${files[@]}"; do
            if [[ -f "$file" ]]; then
                git add "$file"
            else
                log_warning "File not found: $file"
            fi
        done
    fi
}

create_commit() {
    local message="$1"
    shift
    local files=("$@")

    # Check prerequisites
    check_prerequisites || return 1

    # Validate commit message
    validate_commit_message "$message" || return 1

    # Stage changes
    stage_changes "${files[@]}"

    # Check if there are changes to commit
    if git diff --cached --quiet; then
        log_warning "No changes to commit"
        return 0
    fi

    # Show what will be committed
    log_info "Files to be committed:"
    git diff --cached --name-status

    # Dry run mode
    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would commit with message: $message"
        return 0
    fi

    # Create commit
    log_info "Creating commit..."
    if git commit -m "$message"; then
        log_success "Commit created successfully"
        log_info "Commit hash: $(git rev-parse --short HEAD)"
        return 0
    else
        log_error "Commit failed"
        return 1
    fi
}

# Main execution
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: $0 <commit_message> [files...]"
        echo ""
        echo "Environment variables:"
        echo "  CE_DRY_RUN=1    - Dry run mode (no actual commit)"
        echo ""
        echo "Example:"
        echo "  $0 'feat(P2): Add automation scripts' .workflow/automation/"
        exit 1
    fi

    local message="$1"
    shift
    local files=("$@")

    create_commit "$message" "${files[@]}"
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
