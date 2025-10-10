#!/usr/bin/env bash
# Claude Enhancer Release Verification Script
# Comprehensive validation before and after release
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERSION_FILE="${PROJECT_ROOT}/VERSION"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Test results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

log_failure() {
    echo -e "${RED}[✗]${NC} $*"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $*"
    ((WARNING_CHECKS++))
    ((TOTAL_CHECKS++))
}

log_section() {
    echo ""
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}  $*${NC}"
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# VERSION VERIFICATION
# ============================================================================

verify_version() {
    log_section "Version Verification"

    # Check VERSION file exists
    if [[ ! -f "${VERSION_FILE}" ]]; then
        log_failure "VERSION file not found"
        return 1
    fi

    local version
    version=$(cat "${VERSION_FILE}")
    log_info "Version: ${version}"

    # Check version format (semantic versioning)
    if [[ ! "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_failure "Invalid version format: ${version} (expected: X.Y.Z)"
    else
        log_success "Version format valid: ${version}"
    fi

    # Check ce.sh version
    if [[ -f "${PROJECT_ROOT}/ce.sh" ]]; then
        local ce_version
        ce_version=$(grep -oP 'CE_VERSION="\K[^"]+' "${PROJECT_ROOT}/ce.sh" || echo "")

        if [[ "${ce_version}" == "${version}" ]]; then
            log_success "ce.sh version matches: ${ce_version}"
        else
            log_failure "ce.sh version mismatch: ${ce_version} != ${version}"
        fi
    else
        log_failure "ce.sh not found"
    fi

    # Check .claude/settings.json version (if exists)
    if [[ -f "${PROJECT_ROOT}/.claude/settings.json" ]]; then
        if command -v jq &>/dev/null; then
            local settings_version
            settings_version=$(jq -r '.version // empty' "${PROJECT_ROOT}/.claude/settings.json")

            if [[ -n "${settings_version}" ]]; then
                log_info ".claude/settings.json version: ${settings_version}"
            fi
        fi
    fi
}

# ============================================================================
# FILE STRUCTURE VERIFICATION
# ============================================================================

verify_file_structure() {
    log_section "File Structure Verification"

    # Critical files
    local critical_files=(
        "VERSION"
        "ce.sh"
        "install.sh"
        "CHANGELOG.md"
        "README.md"
        ".claude/settings.json"
        ".workflow/ACTIVE"
        ".workflow/gates.yml"
        "scripts/healthcheck.sh"
        "scripts/release.sh"
    )

    for file in "${critical_files[@]}"; do
        if [[ -f "${PROJECT_ROOT}/${file}" ]]; then
            log_success "Found: ${file}"
        else
            log_failure "Missing: ${file}"
        fi
    done

    # Critical directories
    local critical_dirs=(
        ".claude"
        ".workflow"
        ".workflow/cli"
        "scripts"
        "docs"
    )

    for dir in "${critical_dirs[@]}"; do
        if [[ -d "${PROJECT_ROOT}/${dir}" ]]; then
            log_success "Found directory: ${dir}"
        else
            log_failure "Missing directory: ${dir}"
        fi
    done
}

# ============================================================================
# DOCUMENTATION VERIFICATION
# ============================================================================

verify_documentation() {
    log_section "Documentation Verification"

    # Check CHANGELOG
    if [[ -f "${PROJECT_ROOT}/CHANGELOG.md" ]]; then
        local version
        version=$(cat "${VERSION_FILE}")

        if grep -q "\[${version}\]" "${PROJECT_ROOT}/CHANGELOG.md"; then
            log_success "CHANGELOG has entry for version ${version}"
        else
            log_failure "CHANGELOG missing entry for version ${version}"
        fi
    else
        log_failure "CHANGELOG.md not found"
    fi

    # Check README
    if [[ -f "${PROJECT_ROOT}/README.md" ]]; then
        log_success "README.md exists"

        # Check if README is empty
        if [[ ! -s "${PROJECT_ROOT}/README.md" ]]; then
            log_warning "README.md is empty"
        fi
    else
        log_failure "README.md not found"
    fi

    # Check documentation files
    local doc_files=(
        "docs/CLI_GUIDE.md"
        "docs/TROUBLESHOOTING_GUIDE.md"
        "docs/RELEASE_CHECKLIST.md"
    )

    for doc in "${doc_files[@]}"; do
        if [[ -f "${PROJECT_ROOT}/${doc}" ]]; then
            log_success "Documentation: ${doc}"
        else
            log_warning "Optional documentation missing: ${doc}"
        fi
    done
}

# ============================================================================
# GIT VERIFICATION
# ============================================================================

verify_git() {
    log_section "Git Repository Verification"

    # Check if git repo
    if ! git -C "${PROJECT_ROOT}" rev-parse --git-dir &>/dev/null; then
        log_failure "Not a git repository"
        return 1
    fi

    log_success "Git repository detected"

    # Check for uncommitted changes
    if git -C "${PROJECT_ROOT}" diff-index --quiet HEAD --; then
        log_success "No uncommitted changes"
    else
        log_warning "Uncommitted changes detected"
    fi

    # Check current branch
    local branch
    branch=$(git -C "${PROJECT_ROOT}" rev-parse --abbrev-ref HEAD)
    log_info "Current branch: ${branch}"

    # Check if tag exists for current version
    local version
    version=$(cat "${VERSION_FILE}")
    local tag="v${version}"

    if git -C "${PROJECT_ROOT}" rev-parse "${tag}" &>/dev/null; then
        log_info "Git tag ${tag} exists"
    else
        log_warning "Git tag ${tag} does not exist yet"
    fi
}

# ============================================================================
# SCRIPT VERIFICATION
# ============================================================================

verify_scripts() {
    log_section "Script Verification"

    # Check script permissions
    local scripts=(
        "ce.sh"
        "install.sh"
        "scripts/release.sh"
        "scripts/healthcheck.sh"
        "scripts/upgrade.sh"
        "scripts/uninstall.sh"
    )

    for script in "${scripts[@]}"; do
        local script_path="${PROJECT_ROOT}/${script}"

        if [[ -f "${script_path}" ]]; then
            if [[ -x "${script_path}" ]]; then
                log_success "Executable: ${script}"
            else
                log_failure "Not executable: ${script}"
            fi
        else
            log_warning "Script not found: ${script}"
        fi
    done

    # Run ShellCheck if available
    if command -v shellcheck &>/dev/null; then
        log_info "Running ShellCheck..."

        local check_failed=0
        for script in "${scripts[@]}"; do
            local script_path="${PROJECT_ROOT}/${script}"

            if [[ -f "${script_path}" ]]; then
                if shellcheck -x "${script_path}" &>/dev/null; then
                    log_success "ShellCheck passed: ${script}"
                else
                    log_warning "ShellCheck issues: ${script}"
                    ((check_failed++))
                fi
            fi
        done

        if [[ ${check_failed} -eq 0 ]]; then
            log_success "All scripts passed ShellCheck"
        fi
    else
        log_warning "ShellCheck not available"
    fi
}

# ============================================================================
# WORKFLOW VERIFICATION
# ============================================================================

verify_workflows() {
    log_section "CI/CD Workflow Verification"

    # Check GitHub Actions workflows
    local workflows=(
        ".github/workflows/release.yml"
        ".github/workflows/test.yml"
    )

    for workflow in "${workflows[@]}"; do
        if [[ -f "${PROJECT_ROOT}/${workflow}" ]]; then
            log_success "Workflow exists: ${workflow}"

            # Basic YAML syntax check
            if command -v yamllint &>/dev/null; then
                if yamllint "${PROJECT_ROOT}/${workflow}" &>/dev/null; then
                    log_success "YAML syntax valid: ${workflow}"
                else
                    log_warning "YAML syntax issues: ${workflow}"
                fi
            fi
        else
            log_failure "Workflow missing: ${workflow}"
        fi
    done
}

# ============================================================================
# FUNCTIONAL TESTS
# ============================================================================

verify_functionality() {
    log_section "Functional Tests"

    # Test ce.sh basic commands
    if [[ -x "${PROJECT_ROOT}/ce.sh" ]]; then
        log_info "Testing ce.sh commands..."

        # Test --version
        if "${PROJECT_ROOT}/ce.sh" --version &>/dev/null; then
            log_success "ce.sh --version works"
        else
            log_failure "ce.sh --version failed"
        fi

        # Test --help
        if "${PROJECT_ROOT}/ce.sh" --help &>/dev/null; then
            log_success "ce.sh --help works"
        else
            log_failure "ce.sh --help failed"
        fi
    else
        log_failure "ce.sh not executable, cannot test"
    fi

    # Test healthcheck
    if [[ -f "${PROJECT_ROOT}/scripts/healthcheck.sh" ]]; then
        log_info "Running healthcheck..."

        if bash "${PROJECT_ROOT}/scripts/healthcheck.sh" &>/dev/null; then
            log_success "Healthcheck passed"
        else
            log_warning "Healthcheck reported issues"
        fi
    else
        log_warning "Healthcheck script not found"
    fi
}

# ============================================================================
# SECURITY CHECKS
# ============================================================================

verify_security() {
    log_section "Security Verification"

    # Check for common secrets
    log_info "Scanning for secrets..."

    local issues=0

    # API keys
    if grep -r -i "api[_-]key\s*=\s*['\"]" --include="*.sh" --include="*.yml" "${PROJECT_ROOT}" 2>/dev/null | grep -v "example"; then
        log_failure "Potential API keys found"
        ((issues++))
    fi

    # Passwords
    if grep -r -i "password\s*=\s*['\"][^'\"]\+" --include="*.sh" --include="*.yml" "${PROJECT_ROOT}" 2>/dev/null | grep -v "example"; then
        log_failure "Potential hardcoded passwords found"
        ((issues++))
    fi

    if [[ ${issues} -eq 0 ]]; then
        log_success "No obvious secrets found"
    fi

    # Check file permissions
    log_info "Checking file permissions..."

    # No world-writable files
    if find "${PROJECT_ROOT}" -type f -perm -002 ! -path "*/.git/*" 2>/dev/null | grep -q .; then
        log_warning "World-writable files found"
    else
        log_success "No world-writable files"
    fi
}

# ============================================================================
# RELEASE ARTIFACTS VERIFICATION
# ============================================================================

verify_release_artifacts() {
    log_section "Release Artifacts Verification"

    if [[ -d "${PROJECT_ROOT}/dist" ]]; then
        log_info "Checking dist directory..."

        # Check for tarball
        local version
        version=$(cat "${VERSION_FILE}")
        local tarball="dist/claude-enhancer-v${version}.tar.gz"

        if [[ -f "${PROJECT_ROOT}/${tarball}" ]]; then
            log_success "Release tarball exists: ${tarball}"

            # Check tarball size
            local size
            size=$(du -h "${PROJECT_ROOT}/${tarball}" | cut -f1)
            log_info "Tarball size: ${size}"
        else
            log_warning "Release tarball not found (run scripts/release.sh)"
        fi

        # Check for checksums
        if [[ -f "${PROJECT_ROOT}/dist/checksums.txt" ]]; then
            log_success "Checksums file exists"
        else
            log_warning "Checksums file not found"
        fi

        # Check for release notes
        if [[ -f "${PROJECT_ROOT}/dist/RELEASE_NOTES.md" ]]; then
            log_success "Release notes exist"
        else
            log_warning "Release notes not found"
        fi
    else
        log_warning "No dist directory (run scripts/release.sh to create)"
    fi
}

# ============================================================================
# SUMMARY REPORT
# ============================================================================

generate_summary() {
    log_section "Verification Summary"

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              Release Verification Report                      ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    local version
    version=$(cat "${VERSION_FILE}" 2>/dev/null || echo "unknown")

    echo "  Version: ${version}"
    echo "  Date: $(date +"%Y-%m-%d %H:%M:%S")"
    echo ""
    echo "  Total Checks: ${TOTAL_CHECKS}"
    echo -e "  ${GREEN}Passed: ${PASSED_CHECKS}${NC}"
    echo -e "  ${RED}Failed: ${FAILED_CHECKS}${NC}"
    echo -e "  ${YELLOW}Warnings: ${WARNING_CHECKS}${NC}"
    echo ""

    local pass_rate=0
    if [[ ${TOTAL_CHECKS} -gt 0 ]]; then
        pass_rate=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    fi

    echo "  Pass Rate: ${pass_rate}%"
    echo ""

    if [[ ${FAILED_CHECKS} -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}✓ Release verification PASSED${NC}"
        echo ""
        echo "  The release appears ready. Next steps:"
        echo "    1. Review any warnings above"
        echo "    2. Run: scripts/release.sh"
        echo "    3. Test installation from tarball"
        echo "    4. Push tag: git push origin v${version}"
        echo ""
        return 0
    else
        echo -e "${RED}${BOLD}✗ Release verification FAILED${NC}"
        echo ""
        echo "  ${FAILED_CHECKS} critical issue(s) must be fixed before release"
        echo "  Please review the failures above and fix them"
        echo ""
        return 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    local run_all=true
    local categories=()

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version)
                categories+=("version")
                run_all=false
                shift
                ;;
            --files)
                categories+=("files")
                run_all=false
                shift
                ;;
            --docs)
                categories+=("docs")
                run_all=false
                shift
                ;;
            --git)
                categories+=("git")
                run_all=false
                shift
                ;;
            --scripts)
                categories+=("scripts")
                run_all=false
                shift
                ;;
            --workflows)
                categories+=("workflows")
                run_all=false
                shift
                ;;
            --security)
                categories+=("security")
                run_all=false
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Verify release readiness for Claude Enhancer.

OPTIONS:
    --version       Verify version consistency only
    --files         Verify file structure only
    --docs          Verify documentation only
    --git           Verify git status only
    --scripts       Verify scripts only
    --workflows     Verify CI/CD workflows only
    --security      Run security checks only
    -h, --help      Show this help message

EXAMPLES:
    $0                  # Run all verifications
    $0 --version --git  # Run specific verifications

EOF
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║         Claude Enhancer Release Verification System          ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    # Run verifications
    if [[ "${run_all}" == "true" ]]; then
        verify_version
        verify_file_structure
        verify_documentation
        verify_git
        verify_scripts
        verify_workflows
        verify_functionality
        verify_security
        verify_release_artifacts
    else
        for category in "${categories[@]}"; do
            case "${category}" in
                version) verify_version ;;
                files) verify_file_structure ;;
                docs) verify_documentation ;;
                git) verify_git ;;
                scripts) verify_scripts ;;
                workflows) verify_workflows ;;
                security) verify_security ;;
            esac
        done
    fi

    # Generate summary
    generate_summary

    # Exit with appropriate code
    if [[ ${FAILED_CHECKS} -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
