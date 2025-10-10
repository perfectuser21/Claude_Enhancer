#!/usr/bin/env bash
# Claude Enhancer Installation Script
# User-friendly installation with comprehensive validation
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Installation options
SKIP_GIT_HOOKS=${SKIP_GIT_HOOKS:-false}
SKIP_VALIDATION=${SKIP_VALIDATION:-false}
FORCE_INSTALL=${FORCE_INSTALL:-false}

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

print_banner() {
    cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          Claude Enhancer Installation System                 ║
║          AI-Driven Development Workflow                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo ""
}

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================

check_prerequisites() {
    log_step "Checking Prerequisites"

    local errors=0
    local warnings=0

    # Check Bash version (need 4.0+)
    if [[ "${BASH_VERSINFO[0]}" -lt 4 ]]; then
        log_error "Bash 4.0 or higher required (found ${BASH_VERSION})"
        ((errors++))
    else
        log_success "Bash version: ${BASH_VERSION}"
    fi

    # Check Git
    if command -v git &>/dev/null; then
        local git_version
        git_version=$(git --version | grep -oP '\d+\.\d+\.\d+' | head -1)
        log_success "Git version: ${git_version}"
    else
        log_error "Git not found - required for version control"
        ((errors++))
    fi

    # Check optional but recommended tools
    local optional_tools=(jq yq gh shellcheck)
    for tool in "${optional_tools[@]}"; do
        if command -v "${tool}" &>/dev/null; then
            log_success "Found optional tool: ${tool}"
        else
            log_warning "Optional tool not found: ${tool}"
            ((warnings++))
        fi
    done

    # Check if we're in a git repository
    if ! git rev-parse --git-dir &>/dev/null 2>&1; then
        log_warning "Not in a git repository (git hooks will not be installed)"
        SKIP_GIT_HOOKS=true
    else
        log_success "Git repository detected"
    fi

    # System checks
    local os_type
    os_type=$(uname -s)
    log_info "Operating system: ${os_type}"

    if [[ "${os_type}" != "Linux" && "${os_type}" != "Darwin" ]]; then
        log_warning "Unsupported OS detected. Installation may not work correctly."
        ((warnings++))
    fi

    # Summary
    echo ""
    if [[ ${errors} -gt 0 ]]; then
        log_error "Found ${errors} critical issue(s). Cannot proceed."
        return 1
    fi

    if [[ ${warnings} -gt 0 ]]; then
        log_warning "Found ${warnings} warning(s). Installation will continue but some features may be limited."
    else
        log_success "All prerequisite checks passed!"
    fi

    return 0
}

# ============================================================================
# BACKUP EXISTING INSTALLATION
# ============================================================================

backup_existing_installation() {
    log_step "Checking for Existing Installation"

    # Check if .claude directory exists with different configuration
    if [[ -d "${INSTALL_DIR}/.claude" ]]; then
        if [[ -f "${INSTALL_DIR}/.claude/WORKFLOW.md" ]]; then
            log_success "Claude Enhancer already installed"

            if [[ "${FORCE_INSTALL}" == "false" ]]; then
                log_warning "Use --force to reinstall"
                return 0
            fi
        else
            log_warning "Existing .claude directory found (different configuration)"

            if [[ "${FORCE_INSTALL}" == "false" ]]; then
                echo ""
                read -p "Backup existing configuration? (y/n): " -r response

                if [[ "${response}" =~ ^[Yy] ]]; then
                    local backup_dir=".claude.backup.$(date +%Y%m%d_%H%M%S)"
                    mv "${INSTALL_DIR}/.claude" "${INSTALL_DIR}/${backup_dir}"
                    log_success "Backed up to: ${backup_dir}"
                else
                    log_warning "Overwriting existing configuration"
                fi
            fi
        fi
    fi
}

# ============================================================================
# DIRECTORY CREATION
# ============================================================================

create_directories() {
    log_step "Creating Directory Structure"

    local directories=(
        ".workflow/cli/state/sessions"
        ".workflow/cli/state/branches"
        ".workflow/cli/state/locks"
        ".gates"
        "scripts"
        "test/reports"
        "dist"
        "logs"
    )

    for dir in "${directories[@]}"; do
        local full_path="${INSTALL_DIR}/${dir}"
        if [[ ! -d "${full_path}" ]]; then
            if mkdir -p "${full_path}" 2>/dev/null; then
                log_success "Created: ${dir}"
            else
                log_error "Failed to create: ${dir}"
                return 1
            fi
        else
            log_info "Already exists: ${dir}"
        fi
    done

    return 0
}

# ============================================================================
# FILE PERMISSIONS
# ============================================================================

set_permissions() {
    log_step "Setting File Permissions"

    # Make all .sh files executable
    local shell_scripts
    shell_scripts=$(find "${INSTALL_DIR}" -name "*.sh" -type f 2>/dev/null || true)

    local count=0
    for script in ${shell_scripts}; do
        if [[ -f "${script}" ]]; then
            chmod +x "${script}" 2>/dev/null && ((count++)) || true
        fi
    done

    log_success "Made ${count} shell scripts executable"

    # Make ce.sh executable
    if [[ -f "${INSTALL_DIR}/ce.sh" ]]; then
        chmod +x "${INSTALL_DIR}/ce.sh"
        log_success "Made ce.sh executable"
    fi

    # Secure state directories (600 for state files, 755 for directories)
    if [[ -d "${INSTALL_DIR}/.workflow/cli/state" ]]; then
        chmod 755 "${INSTALL_DIR}/.workflow/cli/state"
        chmod 755 "${INSTALL_DIR}/.workflow/cli/state"/* 2>/dev/null || true

        # Secure state files
        find "${INSTALL_DIR}/.workflow/cli/state" -type f -name "*.yml" -exec chmod 600 {} \; 2>/dev/null || true
        find "${INSTALL_DIR}/.workflow/cli/state" -type f -name "*.state*" -exec chmod 600 {} \; 2>/dev/null || true

        log_success "Secured state directories"
    fi

    return 0
}

# ============================================================================
# GIT HOOKS INSTALLATION
# ============================================================================

install_git_hooks() {
    if [[ "${SKIP_GIT_HOOKS}" == "true" ]]; then
        log_warning "Skipping git hooks installation"
        return 0
    fi

    log_step "Installing Git Hooks"

    if [[ ! -d ".git/hooks" ]]; then
        log_warning "Git hooks directory not found, skipping"
        return 0
    fi

    # Backup existing hooks
    local hooks=(pre-commit commit-msg pre-push)
    for hook in "${hooks[@]}"; do
        if [[ -f ".git/hooks/${hook}" ]]; then
            local backup_name="${hook}.backup.$(date +%Y%m%d)"
            if [[ ! -f ".git/hooks/${backup_name}" ]]; then
                cp ".git/hooks/${hook}" ".git/hooks/${backup_name}"
                log_info "Backed up existing: ${hook}"
            fi
        fi
    done

    # Install new hooks from .githooks or .claude/git-hooks
    local hook_source=""
    if [[ -d "${INSTALL_DIR}/.githooks" ]]; then
        hook_source="${INSTALL_DIR}/.githooks"
    elif [[ -d "${INSTALL_DIR}/.claude/git-hooks" ]]; then
        hook_source="${INSTALL_DIR}/.claude/git-hooks"
    fi

    if [[ -n "${hook_source}" ]]; then
        local installed=0
        for hook in "${hooks[@]}"; do
            if [[ -f "${hook_source}/${hook}" ]]; then
                cp "${hook_source}/${hook}" ".git/hooks/${hook}"
                chmod +x ".git/hooks/${hook}"
                log_success "Installed: ${hook}"
                ((installed++))
            fi
        done

        if [[ ${installed} -gt 0 ]]; then
            log_success "Installed ${installed} git hook(s)"
        else
            log_warning "No git hooks found to install"
        fi
    else
        log_warning "Git hooks source directory not found"
    fi

    return 0
}

# ============================================================================
# SYMLINK CREATION
# ============================================================================

create_symlinks() {
    log_step "Creating Symlinks"

    # Create symlink for ce command in PATH
    local ce_path="${INSTALL_DIR}/ce.sh"

    if [[ -f "${ce_path}" ]]; then
        log_info "Claude Enhancer CLI available at: ${ce_path}"
        log_info "Add to PATH or create alias:"
        echo ""
        echo "  # Add to ~/.bashrc or ~/.zshrc:"
        echo "  alias ce='${ce_path}'"
        echo ""
        echo "  # Or add to PATH:"
        echo "  export PATH=\"${INSTALL_DIR}:\${PATH}\""
        echo ""
    fi

    return 0
}

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

validate_installation() {
    if [[ "${SKIP_VALIDATION}" == "true" ]]; then
        log_warning "Skipping validation"
        return 0
    fi

    log_step "Validating Installation"

    # Check critical files exist
    local critical_files=(
        "ce.sh"
        ".claude/settings.json"
        ".workflow/ACTIVE"
        "VERSION"
    )

    local missing=0
    for file in "${critical_files[@]}"; do
        if [[ -f "${INSTALL_DIR}/${file}" ]]; then
            log_success "Found: ${file}"
        else
            log_error "Missing: ${file}"
            ((missing++))
        fi
    done

    if [[ ${missing} -gt 0 ]]; then
        log_error "Installation validation failed (${missing} missing files)"
        return 1
    fi

    # Run healthcheck if available
    if [[ -f "${INSTALL_DIR}/scripts/healthcheck.sh" ]]; then
        log_info "Running health check..."
        if bash "${INSTALL_DIR}/scripts/healthcheck.sh" &>/dev/null; then
            log_success "Health check passed"
        else
            log_warning "Health check reported issues (non-critical)"
        fi
    fi

    log_success "Installation validated successfully!"
    return 0
}

# ============================================================================
# POST-INSTALLATION INSTRUCTIONS
# ============================================================================

show_next_steps() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                 Installation Complete!                       ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    local version
    if [[ -f "${INSTALL_DIR}/VERSION" ]]; then
        version=$(cat "${INSTALL_DIR}/VERSION")
        echo -e "${GREEN}${BOLD}Claude Enhancer v${version} installed successfully!${NC}"
    else
        echo -e "${GREEN}${BOLD}Claude Enhancer installed successfully!${NC}"
    fi

    echo ""
    echo "Next Steps:"
    echo ""
    echo "  1. Add ce to your PATH:"
    echo "     ${CYAN}export PATH=\"${INSTALL_DIR}:\${PATH}\"${NC}"
    echo ""
    echo "  2. Or create an alias:"
    echo "     ${CYAN}alias ce='${INSTALL_DIR}/ce.sh'${NC}"
    echo ""
    echo "  3. Start using Claude Enhancer:"
    echo "     ${CYAN}ce start my-feature${NC}        # Start new feature"
    echo "     ${CYAN}ce status${NC}                  # Check status"
    echo "     ${CYAN}ce next${NC}                    # Advance workflow"
    echo "     ${CYAN}ce validate${NC}                # Run quality checks"
    echo ""
    echo "  4. Read the documentation:"
    echo "     ${CYAN}docs/CLI_GUIDE.md${NC}          # User guide"
    echo "     ${CYAN}docs/TROUBLESHOOTING_GUIDE.md${NC} # Common issues"
    echo ""
    echo "  5. Get help:"
    echo "     ${CYAN}ce --help${NC}                  # Show all commands"
    echo "     ${CYAN}ce <command> --help${NC}        # Command-specific help"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Happy coding with Claude Enhancer! 🚀"
    echo ""
}

# ============================================================================
# CLEANUP ON FAILURE
# ============================================================================

cleanup_on_error() {
    local exit_code=$?

    if [[ ${exit_code} -ne 0 ]]; then
        log_error "Installation failed with exit code: ${exit_code}"
        log_info "Please review the errors above and try again"
    fi

    return "${exit_code}"
}

# ============================================================================
# MAIN INSTALLATION FLOW
# ============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --skip-git-hooks)
                SKIP_GIT_HOOKS=true
                shift
                ;;
            --skip-validation)
                SKIP_VALIDATION=true
                shift
                ;;
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Install Claude Enhancer development workflow system.

OPTIONS:
    --skip-git-hooks     Skip git hooks installation
    --skip-validation    Skip installation validation
    --force              Force reinstallation
    -h, --help           Show this help message

EXAMPLES:
    $0                        # Standard installation
    $0 --skip-git-hooks       # Install without git hooks
    $0 --force                # Reinstall even if exists

ENVIRONMENT VARIABLES:
    SKIP_GIT_HOOKS=true      Same as --skip-git-hooks
    SKIP_VALIDATION=true     Same as --skip-validation
    FORCE_INSTALL=true       Same as --force

EOF
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                log_info "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Set up error handling
    trap cleanup_on_error EXIT

    # Print banner
    print_banner

    # Run installation steps
    check_prerequisites || exit 1
    backup_existing_installation
    create_directories || exit 1
    set_permissions || exit 1
    install_git_hooks
    create_symlinks
    validate_installation || exit 1

    # Show success message and next steps
    show_next_steps

    return 0
}

# Run main function
main "$@"
