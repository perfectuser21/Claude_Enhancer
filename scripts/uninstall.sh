#!/usr/bin/env bash
# Claude Enhancer Uninstall Script
# Clean removal with optional state backup
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Uninstall options
KEEP_STATE=${KEEP_STATE:-false}
BACKUP_STATE=${BACKUP_STATE:-true}
AUTO_CONFIRM=${AUTO_CONFIRM:-false}
DRY_RUN=${DRY_RUN:-false}

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*" >&2
}

log_step() {
    echo ""
    echo -e "${CYAN}${BOLD}▶ $*${NC}"
}

# ============================================================================
# STATE BACKUP
# ============================================================================

backup_state() {
    if [[ "${BACKUP_STATE}" == "false" ]]; then
        log_info "Skipping state backup"
        return 0
    fi

    log_step "Backing Up State"

    local backup_dir
    backup_dir="${HOME}/.claude-enhancer-backup-$(date +%Y%m%d_%H%M%S)"

    mkdir -p "${backup_dir}"

    # Backup state directories
    local state_items=(
        ".workflow/cli/state"
        ".gates"
        ".phase"
    )

    local backed_up=0
    for item in "${state_items[@]}"; do
        if [[ -e "${PROJECT_ROOT}/${item}" ]]; then
            if cp -r "${PROJECT_ROOT}/${item}" "${backup_dir}/" 2>/dev/null; then
                log_success "Backed up: ${item}"
                ((backed_up++))
            fi
        fi
    done

    if [[ ${backed_up} -gt 0 ]]; then
        log_success "State backed up to: ${backup_dir}"
        echo ""
        echo "  To restore state later, copy these directories back to your project:"
        echo "  ${backup_dir}"
        echo ""
    else
        log_info "No state to backup"
        rmdir "${backup_dir}" 2>/dev/null || true
    fi
}

# ============================================================================
# REMOVAL FUNCTIONS
# ============================================================================

remove_git_hooks() {
    log_step "Removing Git Hooks"

    if [[ ! -d "${PROJECT_ROOT}/.git/hooks" ]]; then
        log_info "No git hooks directory found"
        return 0
    fi

    local hooks=(pre-commit commit-msg pre-push)
    local removed=0

    for hook in "${hooks[@]}"; do
        local hook_file="${PROJECT_ROOT}/.git/hooks/${hook}"

        if [[ -f "${hook_file}" ]]; then
            # Check if it's a Claude Enhancer hook
            if grep -q "Claude Enhancer" "${hook_file}" 2>/dev/null; then
                if [[ "${DRY_RUN}" == "true" ]]; then
                    log_info "[DRY RUN] Would remove: ${hook}"
                else
                    # Restore backup if exists
                    local backup="${hook_file}.backup.*"
                    if ls ${backup} &>/dev/null 2>&1; then
                        local latest_backup
                        latest_backup=$(ls -t ${backup} 2>/dev/null | head -1)
                        mv "${latest_backup}" "${hook_file}"
                        log_success "Restored backup: ${hook}"
                    else
                        rm -f "${hook_file}"
                        log_success "Removed: ${hook}"
                    fi
                    ((removed++))
                fi
            else
                log_info "Keeping non-CE hook: ${hook}"
            fi
        fi
    done

    if [[ ${removed} -eq 0 ]]; then
        log_info "No git hooks to remove"
    fi
}

remove_claude_directory() {
    log_step "Removing Claude Configuration"

    if [[ ! -d "${PROJECT_ROOT}/.claude" ]]; then
        log_info "No .claude directory found"
        return 0
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would remove: .claude directory"
        return 0
    fi

    rm -rf "${PROJECT_ROOT}/.claude"
    log_success "Removed: .claude directory"
}

remove_workflow_directory() {
    log_step "Removing Workflow Files"

    if [[ ! -d "${PROJECT_ROOT}/.workflow" ]]; then
        log_info "No .workflow directory found"
        return 0
    fi

    if [[ "${KEEP_STATE}" == "true" ]]; then
        log_warning "Keeping state files (--keep-state specified)"

        # Only remove non-state files
        local workflow_items=(
            ".workflow/cli/commands"
            ".workflow/cli/lib"
            ".workflow/executor.sh"
            ".workflow/phase_switcher.sh"
        )

        for item in "${workflow_items[@]}"; do
            if [[ -e "${PROJECT_ROOT}/${item}" ]]; then
                if [[ "${DRY_RUN}" == "true" ]]; then
                    log_info "[DRY RUN] Would remove: ${item}"
                else
                    rm -rf "${PROJECT_ROOT:?}/${item}"
                    log_success "Removed: ${item}"
                fi
            fi
        done
    else
        if [[ "${DRY_RUN}" == "true" ]]; then
            log_info "[DRY RUN] Would remove: .workflow directory"
        else
            rm -rf "${PROJECT_ROOT}/.workflow"
            log_success "Removed: .workflow directory"
        fi
    fi
}

remove_gates() {
    log_step "Removing Quality Gates"

    if [[ "${KEEP_STATE}" == "true" ]]; then
        log_info "Keeping gate state (--keep-state specified)"
        return 0
    fi

    if [[ ! -d "${PROJECT_ROOT}/.gates" ]]; then
        log_info "No .gates directory found"
        return 0
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would remove: .gates directory"
    else
        rm -rf "${PROJECT_ROOT}/.gates"
        log_success "Removed: .gates directory"
    fi
}

remove_scripts() {
    log_step "Removing Scripts"

    local script_files=(
        "ce.sh"
        "VERSION"
    )

    for file in "${script_files[@]}"; do
        if [[ -f "${PROJECT_ROOT}/${file}" ]]; then
            if [[ "${DRY_RUN}" == "true" ]]; then
                log_info "[DRY RUN] Would remove: ${file}"
            else
                rm -f "${PROJECT_ROOT}/${file}"
                log_success "Removed: ${file}"
            fi
        fi
    done

    # Remove scripts directory (be careful!)
    if [[ -d "${PROJECT_ROOT}/scripts" ]]; then
        # Check if it's a CE scripts directory
        if [[ -f "${PROJECT_ROOT}/scripts/healthcheck.sh" ]] || [[ -f "${PROJECT_ROOT}/scripts/release.sh" ]]; then
            if [[ "${DRY_RUN}" == "true" ]]; then
                log_info "[DRY RUN] Would remove: scripts directory"
            else
                rm -rf "${PROJECT_ROOT}/scripts"
                log_success "Removed: scripts directory"
            fi
        else
            log_warning "Keeping scripts directory (not CE-specific)"
        fi
    fi
}

remove_documentation() {
    log_step "Removing Documentation"

    local doc_files=(
        "docs/CLI_GUIDE.md"
        "docs/SYSTEM_OVERVIEW_COMPLETE_V2.md"
        "docs/TROUBLESHOOTING_GUIDE.md"
        "docs/CAPABILITY_MATRIX.md"
    )

    local removed=0
    for file in "${doc_files[@]}"; do
        if [[ -f "${PROJECT_ROOT}/${file}" ]]; then
            # Only remove if it's CE-specific
            if grep -q "Claude Enhancer" "${PROJECT_ROOT}/${file}" 2>/dev/null; then
                if [[ "${DRY_RUN}" == "true" ]]; then
                    log_info "[DRY RUN] Would remove: ${file}"
                else
                    rm -f "${PROJECT_ROOT}/${file}"
                    log_success "Removed: ${file}"
                    ((removed++))
                fi
            fi
        fi
    done

    if [[ ${removed} -eq 0 ]]; then
        log_info "No documentation to remove"
    fi
}

clean_empty_directories() {
    log_step "Cleaning Empty Directories"

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would clean empty directories"
        return 0
    fi

    # Remove empty directories
    find "${PROJECT_ROOT}" -type d -empty -delete 2>/dev/null || true

    log_success "Cleaned empty directories"
}

# ============================================================================
# VERIFICATION
# ============================================================================

verify_removal() {
    log_step "Verifying Removal"

    local remaining_items=(
        ".claude"
        ".workflow"
        ".gates"
        "ce.sh"
    )

    local still_exists=0
    for item in "${remaining_items[@]}"; do
        if [[ -e "${PROJECT_ROOT}/${item}" ]]; then
            log_warning "Still exists: ${item}"
            ((still_exists++))
        fi
    done

    if [[ ${still_exists} -eq 0 ]]; then
        log_success "All Claude Enhancer files removed"
    else
        log_warning "${still_exists} items still exist"
    fi
}

# ============================================================================
# SUMMARY
# ============================================================================

show_summary() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              Uninstall Complete                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    log_success "Claude Enhancer has been uninstalled"

    echo ""
    echo "What was removed:"
    echo "  • .claude directory (configuration)"
    echo "  • .workflow directory (workflow files)"
    echo "  • .gates directory (quality gates)"
    echo "  • ce.sh (CLI script)"
    echo "  • Git hooks (if present)"
    echo ""

    if [[ "${KEEP_STATE}" == "true" ]]; then
        echo "State files preserved:"
        echo "  • .workflow/cli/state (session data)"
        echo ""
    fi

    if [[ -n "${backup_dir:-}" ]]; then
        echo "State backed up to:"
        echo "  ${backup_dir}"
        echo ""
    fi

    echo "To reinstall Claude Enhancer:"
    echo "  ./install.sh"
    echo ""
}

# ============================================================================
# MAIN UNINSTALL FLOW
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --keep-state)
                KEEP_STATE=true
                shift
                ;;
            --no-backup)
                BACKUP_STATE=false
                shift
                ;;
            --yes|-y)
                AUTO_CONFIRM=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Uninstall Claude Enhancer from the current project.

OPTIONS:
    --keep-state     Keep state files (.workflow/cli/state)
    --no-backup      Skip backing up state
    --yes, -y        Auto-confirm without prompting
    --dry-run        Show what would be removed
    -h, --help       Show this help message

EXAMPLES:
    # Standard uninstall with state backup
    $0

    # Uninstall but keep state
    $0 --keep-state

    # Uninstall without backup
    $0 --no-backup --yes

    # Dry run (show what would be removed)
    $0 --dry-run

EOF
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║          Claude Enhancer Uninstall System                    ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN MODE - No files will be removed"
        echo ""
    fi

    # Confirm uninstall
    if [[ "${AUTO_CONFIRM}" == "false" && "${DRY_RUN}" == "false" ]]; then
        echo -e "${YELLOW}${BOLD}WARNING:${NC} This will remove Claude Enhancer from:"
        echo "  ${PROJECT_ROOT}"
        echo ""

        if [[ "${KEEP_STATE}" == "true" ]]; then
            echo "State files will be preserved"
        elif [[ "${BACKUP_STATE}" == "true" ]]; then
            echo "State will be backed up to: ${HOME}/.claude-enhancer-backup-*"
        else
            echo "State will NOT be backed up"
        fi

        echo ""
        read -p "Are you sure you want to uninstall? (yes/no): " -r response

        if [[ "${response}" != "yes" ]]; then
            log_info "Uninstall cancelled"
            exit 0
        fi
    fi

    # Backup state
    backup_state

    # Remove components
    remove_git_hooks
    remove_claude_directory
    remove_workflow_directory
    remove_gates
    remove_scripts
    remove_documentation
    clean_empty_directories

    # Verify
    if [[ "${DRY_RUN}" == "false" ]]; then
        verify_removal
    fi

    # Show summary
    show_summary

    return 0
}

main "$@"
