#!/usr/bin/env bash
# Auto Commit Script for Claude Enhancer v5.4.0
# Purpose: Automated git commit with quality checks and Phase validation
# Used by: Claude automation, CI/CD pipeline
# Tier: 1 (Safe - Always automated)

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"
# shellcheck source=../security/audit_log.sh
source "${SCRIPT_DIR}/../security/audit_log.sh"

# Configuration
COMMIT_MESSAGE_MIN_LENGTH=10
COMMIT_MESSAGE_MAX_LENGTH=500
DRY_RUN="${CE_DRY_RUN:-0}"
STRICT_MODE="${CE_STRICT_MODE:-0}"

# Conventional commit types
declare -a VALID_TYPES=(
    "feat" "fix" "docs" "style" "refactor" "perf" "test"
    "build" "ci" "chore" "revert"
)

# Phase markers
declare -A PHASE_NAMES=(
    [0]="探索"
    [1]="规划"
    [2]="骨架"
    [3]="实现"
    [4]="测试"
    [5]="审查"
    [6]="发布"
    [7]="监控"
)

# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

check_prerequisites() {
    log_debug "Checking prerequisites..."

    # Verify git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not a git repository"
        audit_git_operation "check_repo" "current_dir" "failed" "Not a git repository"
        return 1
    fi

    # Check git user configuration
    if ! git config user.name > /dev/null 2>&1; then
        log_error "Git user.name not configured"
        log_info "Run: git config --global user.name 'Your Name'"
        return 1
    fi

    if ! git config user.email > /dev/null 2>&1; then
        log_error "Git user.email not configured"
        log_info "Run: git config --global user.email 'you@example.com'"
        return 1
    fi

    # Verify hooks are installed
    if [[ ! -f ".git/hooks/pre-commit" ]]; then
        log_warning "pre-commit hook not installed"
        log_info "Quality checks may be skipped"
    fi

    # Verify commit-msg hook
    if [[ ! -f ".git/hooks/commit-msg" ]]; then
        log_warning "commit-msg hook not installed"
        log_info "Commit message validation may be limited"
    fi

    log_debug "Prerequisites check passed"
    return 0
}

validate_commit_message() {
    local message="$1"
    local errors=()

    log_debug "Validating commit message: $message"

    # Check minimum length
    if [[ ${#message} -lt ${COMMIT_MESSAGE_MIN_LENGTH} ]]; then
        errors+=("Message too short (minimum ${COMMIT_MESSAGE_MIN_LENGTH} characters)")
    fi

    # Check maximum length
    if [[ ${#message} -gt ${COMMIT_MESSAGE_MAX_LENGTH} ]]; then
        errors+=("Message too long (maximum ${COMMIT_MESSAGE_MAX_LENGTH} characters)")
    fi

    # Check for empty message
    if [[ -z "$(echo "$message" | tr -d '[:space:]')" ]]; then
        errors+=("Message cannot be empty")
    fi

    # Validate conventional commit format (if strict mode)
    if [[ "$STRICT_MODE" == "1" ]]; then
        if ! validate_conventional_commit "$message"; then
            errors+=("Must follow conventional commit format: type(scope): description")
        fi
    fi

    # Check for Phase marker (P0-P7)
    if ! echo "$message" | grep -qE '\[P[0-7]\]|\bP[0-7]\b|Phase [0-7]'; then
        if [[ "$STRICT_MODE" == "1" ]]; then
            errors+=("Missing Phase marker (P0-P7)")
        else
            log_warning "Commit message missing Phase marker (recommended: [P0-P7])"
        fi
    fi

    # Check for WIP commits in strict mode
    if [[ "$STRICT_MODE" == "1" ]] && echo "$message" | grep -iq "WIP\|work in progress"; then
        errors+=("WIP commits not allowed in strict mode")
    fi

    # Report errors
    if [[ ${#errors[@]} -gt 0 ]]; then
        log_error "Commit message validation failed:"
        for error in "${errors[@]}"; do
            log_error "  - $error"
        done
        return 1
    fi

    log_debug "Commit message validation passed"
    return 0
}

validate_conventional_commit() {
    local message="$1"

    # Extract type from message
    local type=$(echo "$message" | sed -E 's/^([a-z]+)(\([^)]+\))?:.*/\1/')

    # Check if type is valid
    for valid_type in "${VALID_TYPES[@]}"; do
        if [[ "$type" == "$valid_type" ]]; then
            return 0
        fi
    done

    return 1
}

inject_phase_marker() {
    local message="$1"
    local phase="${CE_CURRENT_PHASE:-}"

    # If phase is set and message doesn't have phase marker, inject it
    if [[ -n "$phase" ]] && ! echo "$message" | grep -qE '\[P[0-7]\]'; then
        # Check if conventional commit format
        if echo "$message" | grep -qE '^[a-z]+(\([^)]+\))?:'; then
            # Inject after type(scope):
            message=$(echo "$message" | sed -E "s/^([a-z]+(\([^)]+\))?:)/\1 [P${phase}]/")
        else
            # Prepend to message
            message="[P${phase}] $message"
        fi
        log_info "Injected Phase marker: P${phase}"
    fi

    echo "$message"
}

# ============================================================
# STAGING FUNCTIONS
# ============================================================

stage_changes() {
    local files=("$@")

    if [[ ${#files[@]} -eq 0 ]]; then
        log_info "No specific files provided, staging all changes"

        # Check for large files before staging
        check_large_files || return 1

        git add -A
        audit_git_operation "stage_all" "all_files" "success" "Staged all changes"
    else
        log_info "Staging ${#files[@]} specific file(s)"

        local staged=0
        local skipped=0

        for file in "${files[@]}"; do
            if [[ -f "$file" || -d "$file" ]]; then
                # Check file size
                if [[ -f "$file" ]]; then
                    local size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo "0")
                    if [[ $size -gt 10485760 ]]; then  # 10MB
                        log_warning "Skipping large file (>10MB): $file"
                        skipped=$((skipped + 1))
                        continue
                    fi
                fi

                git add "$file"
                staged=$((staged + 1))
                log_debug "Staged: $file"
            else
                log_warning "File not found, skipping: $file"
                skipped=$((skipped + 1))
            fi
        done

        log_info "Staged: $staged, Skipped: $skipped"
        audit_git_operation "stage_specific" "${staged}_files" "success" "Staged $staged files, skipped $skipped"
    fi
}

check_large_files() {
    local large_files=$(git diff --cached --name-only --diff-filter=ACM | while read -r file; do
        if [[ -f "$file" ]]; then
            local size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo "0")
            if [[ $size -gt 10485760 ]]; then  # 10MB
                echo "$file ($((size / 1048576))MB)"
            fi
        fi
    done)

    if [[ -n "$large_files" ]]; then
        log_warning "Large files detected:"
        echo "$large_files" | while read -r line; do
            log_warning "  $line"
        done

        if [[ "$STRICT_MODE" == "1" ]]; then
            log_error "Large files not allowed in strict mode"
            return 1
        else
            log_info "Consider using Git LFS for large files"
        fi
    fi

    return 0
}

check_sensitive_files() {
    local sensitive_patterns=(
        "*.env"
        "*.pem"
        "*.key"
        "*secret*"
        "*password*"
        "*credentials*"
        ".aws/credentials"
        ".ssh/id_*"
    )

    local sensitive_found=()

    for pattern in "${sensitive_patterns[@]}"; do
        local matches=$(git diff --cached --name-only --diff-filter=ACM | grep -i "$pattern" || true)
        if [[ -n "$matches" ]]; then
            sensitive_found+=("$matches")
        fi
    done

    if [[ ${#sensitive_found[@]} -gt 0 ]]; then
        log_error "Sensitive files detected in staged changes:"
        for file in "${sensitive_found[@]}"; do
            log_error "  - $file"
        done

        audit_security_event "sensitive_file_commit_attempt" "HIGH" "User attempted to commit sensitive files"

        log_error "Aborting commit to prevent credential exposure"
        return 1
    fi

    return 0
}

# ============================================================
# COMMIT FUNCTIONS
# ============================================================

show_commit_summary() {
    log_info "Files to be committed:"
    git diff --cached --name-status | while read -r status file; do
        case "$status" in
            A) log_info "  ${GREEN}[+]${NC} $file" ;;
            M) log_info "  ${YELLOW}[~]${NC} $file" ;;
            D) log_info "  ${RED}[-]${NC} $file" ;;
            R*) log_info "  ${BLUE}[→]${NC} $file" ;;
            *) log_info "  $status $file" ;;
        esac
    done

    # Show stats
    local stats=$(git diff --cached --shortstat)
    if [[ -n "$stats" ]]; then
        log_info "Changes: $stats"
    fi
}

create_commit() {
    local message="$1"
    shift
    local files=("$@")

    # Audit the commit attempt
    audit_git_operation "commit_attempt" "$(get_current_branch)" "started" "Message: $message"

    # Check prerequisites
    check_prerequisites || return 1

    # Inject Phase marker if needed
    message=$(inject_phase_marker "$message")

    # Validate commit message
    validate_commit_message "$message" || return 1

    # Stage changes
    stage_changes "${files[@]}" || return 1

    # Check if there are changes to commit
    if git diff --cached --quiet; then
        log_warning "No changes to commit"
        audit_git_operation "commit" "$(get_current_branch)" "skipped" "No changes"
        return 0
    fi

    # Check for sensitive files
    check_sensitive_files || return 1

    # Show what will be committed
    show_commit_summary

    # Dry run mode
    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would commit with message:"
        echo ""
        echo "  $message"
        echo ""
        audit_git_operation "commit" "$(get_current_branch)" "dry_run" "Message: $message"
        return 0
    fi

    # Create commit
    log_info "Creating commit..."
    if git commit -m "$message"; then
        local commit_hash=$(git rev-parse --short HEAD)
        log_success "Commit created successfully"
        log_info "Commit hash: $commit_hash"
        log_info "Branch: $(get_current_branch)"

        # Show commit details
        git log -1 --stat

        # Audit successful commit
        audit_git_operation "commit" "$(get_current_branch)" "success" "Hash: $commit_hash, Message: $message"

        # Check if commit triggered hooks
        if [[ -f ".git/hooks/post-commit" ]]; then
            log_debug "Running post-commit hook..."
        fi

        return 0
    else
        log_error "Commit failed"
        audit_git_operation "commit" "$(get_current_branch)" "failed" "Message: $message"
        return 1
    fi
}

# ============================================================
# TEMPLATE FUNCTIONS
# ============================================================

get_commit_template() {
    local template_type="${1:-standard}"

    case "$template_type" in
        feature)
            echo "feat(P3): Add [feature description]"
            ;;
        bugfix)
            echo "fix(P3): Resolve [issue description]"
            ;;
        docs)
            echo "docs(P6): Update [documentation topic]"
            ;;
        perf)
            echo "perf(P3): Optimize [performance aspect]"
            ;;
        test)
            echo "test(P4): Add [test description]"
            ;;
        refactor)
            echo "refactor(P3): Restructure [code area]"
            ;;
        *)
            echo "[P?]: [type] [description]"
            ;;
    esac
}

show_templates() {
    echo "Available commit message templates:"
    echo ""
    echo "  Feature:   $(get_commit_template feature)"
    echo "  Bug Fix:   $(get_commit_template bugfix)"
    echo "  Docs:      $(get_commit_template docs)"
    echo "  Perf:      $(get_commit_template perf)"
    echo "  Test:      $(get_commit_template test)"
    echo "  Refactor:  $(get_commit_template refactor)"
    echo ""
    echo "Phases: P0=探索 P1=规划 P2=骨架 P3=实现 P4=测试 P5=审查 P6=发布 P7=监控"
}

# ============================================================
# MAIN EXECUTION
# ============================================================

main() {
    if [[ $# -lt 1 ]]; then
        cat <<EOF
Usage: $0 <commit_message> [files...]
       $0 --template [type]

Creates a git commit with automated quality checks and Phase validation.

Arguments:
  commit_message    Commit message (required)
  files            Specific files to commit (optional, default: all changes)

Options:
  --template [type]   Show commit message templates
                      Types: feature, bugfix, docs, perf, test, refactor

Environment Variables:
  CE_DRY_RUN=1           Dry run mode (show what would be done)
  CE_STRICT_MODE=1       Enable strict validation
  CE_CURRENT_PHASE=N     Current phase (0-7) for auto-injection

Examples:
  # Commit all changes
  $0 'feat(P3): Add user authentication'

  # Commit specific files
  $0 'fix(P3): Resolve login bug' src/auth.js tests/auth.test.js

  # Show templates
  $0 --template feature

  # Strict mode with dry run
  CE_STRICT_MODE=1 CE_DRY_RUN=1 $0 'feat: Add feature'

Commit Message Format (Conventional Commits):
  <type>(<scope>): <description>

  type:  feat, fix, docs, style, refactor, perf, test, build, ci, chore
  scope: Optional module/component name

Phase Markers (Recommended):
  [P0] - 探索 (Discovery)
  [P1] - 规划 (Planning)
  [P2] - 骨架 (Skeleton)
  [P3] - 实现 (Implementation)
  [P4] - 测试 (Testing)
  [P5] - 审查 (Review)
  [P6] - 发布 (Release)
  [P7] - 监控 (Monitoring)

Tier: 1 (Safe - Always automated in execution mode)
EOF
        exit 1
    fi

    # Handle template request
    if [[ "$1" == "--template" ]]; then
        if [[ $# -eq 2 ]]; then
            get_commit_template "$2"
        else
            show_templates
        fi
        exit 0
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
