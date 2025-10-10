#!/usr/bin/env bash
# Claude Enhancer Release Script
# Prepares and creates production releases
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_ROOT}/dist"
VERSION_FILE="${PROJECT_ROOT}/VERSION"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $*${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

check_prerequisites() {
    log_section "Checking Prerequisites"

    local missing=0

    # Check required commands
    local required_commands=(git tar gzip sha256sum)
    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" &>/dev/null; then
            log_error "Required command not found: ${cmd}"
            ((missing++))
        else
            log_info "Found: ${cmd}"
        fi
    done

    # Check optional commands
    local optional_commands=(gpg minisign gh)
    for cmd in "${optional_commands[@]}"; do
        if command -v "${cmd}" &>/dev/null; then
            log_info "Found optional: ${cmd}"
        else
            log_warning "Optional command not found: ${cmd} (some features may be limited)"
        fi
    done

    if [[ ${missing} -gt 0 ]]; then
        log_error "Missing ${missing} required command(s)"
        return 1
    fi

    log_success "All prerequisites satisfied"
    return 0
}

check_git_status() {
    log_section "Checking Git Status"

    # Check if we're in a git repository
    if ! git rev-parse --git-dir &>/dev/null; then
        log_error "Not in a git repository"
        return 1
    fi

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        log_error "Uncommitted changes detected"
        log_info "Please commit or stash your changes before releasing"
        git status --short
        return 1
    fi

    # Check for untracked files
    local untracked
    untracked=$(git ls-files --others --exclude-standard | wc -l)
    if [[ ${untracked} -gt 0 ]]; then
        log_warning "${untracked} untracked files found (will not be included in release)"
    fi

    log_success "Git status clean"
    return 0
}

run_tests() {
    log_section "Running Tests"

    local test_failed=0

    # Run healthcheck
    if [[ -f "${SCRIPT_DIR}/healthcheck.sh" ]]; then
        log_info "Running healthcheck..."
        if bash "${SCRIPT_DIR}/healthcheck.sh"; then
            log_success "Healthcheck passed"
        else
            log_error "Healthcheck failed"
            ((test_failed++))
        fi
    else
        log_warning "Healthcheck script not found, skipping"
    fi

    # Run unit tests if available
    if [[ -d "${PROJECT_ROOT}/test" ]]; then
        log_info "Running unit tests..."

        # Look for test scripts
        local test_scripts
        test_scripts=$(find "${PROJECT_ROOT}/test" -name "test_*.sh" -o -name "*_test.sh" | head -5)

        if [[ -n "${test_scripts}" ]]; then
            for test_script in ${test_scripts}; do
                log_info "Running: $(basename "${test_script}")"
                if bash "${test_script}" &>/dev/null; then
                    log_success "$(basename "${test_script}") passed"
                else
                    log_warning "$(basename "${test_script}") failed"
                fi
            done
        else
            log_warning "No test scripts found"
        fi
    fi

    # Run security checks
    if command -v shellcheck &>/dev/null; then
        log_info "Running ShellCheck..."
        local shell_scripts
        shell_scripts=$(find "${PROJECT_ROOT}" -name "*.sh" -not -path "*/.*" -not -path "*/node_modules/*" | head -10)

        local shellcheck_failed=0
        for script in ${shell_scripts}; do
            if ! shellcheck -x "${script}" &>/dev/null; then
                log_warning "ShellCheck issues in: $(basename "${script}")"
                ((shellcheck_failed++))
            fi
        done

        if [[ ${shellcheck_failed} -gt 0 ]]; then
            log_warning "${shellcheck_failed} scripts have ShellCheck warnings (non-blocking)"
        else
            log_success "ShellCheck passed"
        fi
    fi

    if [[ ${test_failed} -gt 0 ]]; then
        log_error "${test_failed} critical tests failed"
        return 1
    fi

    log_success "All tests passed"
    return 0
}

# ============================================================================
# VERSION MANAGEMENT
# ============================================================================

get_version() {
    if [[ -f "${VERSION_FILE}" ]]; then
        cat "${VERSION_FILE}"
    else
        log_error "VERSION file not found"
        return 1
    fi
}

validate_version_consistency() {
    log_section "Validating Version Consistency"

    local version
    version=$(get_version)

    log_info "Release version: ${version}"

    # Check ce.sh
    if [[ -f "${PROJECT_ROOT}/ce.sh" ]]; then
        local ce_version
        ce_version=$(grep -oP 'CE_VERSION="\K[^"]+' "${PROJECT_ROOT}/ce.sh" || echo "")

        if [[ "${ce_version}" == "${version}" ]]; then
            log_success "ce.sh version matches: ${ce_version}"
        else
            log_error "ce.sh version mismatch: ${ce_version} != ${version}"
            return 1
        fi
    fi

    # Check .claude/settings.json
    if [[ -f "${PROJECT_ROOT}/.claude/settings.json" ]]; then
        if command -v jq &>/dev/null; then
            local settings_version
            settings_version=$(jq -r '.version // empty' "${PROJECT_ROOT}/.claude/settings.json")

            if [[ -n "${settings_version}" ]]; then
                log_info ".claude/settings.json version: ${settings_version}"
            fi
        fi
    fi

    log_success "Version consistency validated"
    return 0
}

# ============================================================================
# RELEASE ARTIFACT GENERATION
# ============================================================================

create_dist_directory() {
    log_section "Creating Distribution Directory"

    if [[ -d "${DIST_DIR}" ]]; then
        log_warning "Cleaning existing dist directory"
        rm -rf "${DIST_DIR}"
    fi

    mkdir -p "${DIST_DIR}"
    log_success "Created: ${DIST_DIR}"
}

create_tarball() {
    log_section "Creating Release Tarball"

    local version
    version=$(get_version)
    local tarball_name="claude-enhancer-v${version}.tar.gz"
    local tarball_path="${DIST_DIR}/${tarball_name}"

    log_info "Creating: ${tarball_name}"

    # Create archive excluding development artifacts
    tar -czf "${tarball_path}" \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.coverage' \
        --exclude='htmlcov' \
        --exclude='dist' \
        --exclude='.pytest_cache' \
        --exclude='*.log' \
        --exclude='.chaos_backup' \
        --exclude='.performance_backup' \
        --transform "s,^,claude-enhancer-${version}/," \
        -C "${PROJECT_ROOT}" \
        .

    local size
    size=$(du -h "${tarball_path}" | cut -f1)

    log_success "Created tarball: ${tarball_name} (${size})"
    echo "${tarball_path}"
}

generate_checksums() {
    log_section "Generating Checksums"

    local checksums_file="${DIST_DIR}/checksums.txt"

    > "${checksums_file}"

    for file in "${DIST_DIR}"/*.tar.gz; do
        if [[ -f "${file}" ]]; then
            local filename
            filename=$(basename "${file}")

            log_info "Calculating SHA256 for: ${filename}"

            local checksum
            checksum=$(sha256sum "${file}" | cut -d' ' -f1)

            echo "SHA256(${filename})= ${checksum}" >> "${checksums_file}"
            log_success "${filename}: ${checksum:0:16}..."
        fi
    done

    log_success "Checksums written to: checksums.txt"
}

sign_artifacts() {
    log_section "Signing Release Artifacts"

    if ! command -v gpg &>/dev/null && ! command -v minisign &>/dev/null; then
        log_warning "Neither GPG nor minisign found, skipping signatures"
        return 0
    fi

    for file in "${DIST_DIR}"/*.tar.gz; do
        if [[ -f "${file}" ]]; then
            local filename
            filename=$(basename "${file}")

            # Try GPG first
            if command -v gpg &>/dev/null; then
                log_info "GPG signing: ${filename}"

                if gpg --detach-sign --armor "${file}" 2>/dev/null; then
                    log_success "GPG signature created: ${filename}.asc"
                else
                    log_warning "GPG signing failed (no key configured?)"
                fi
            fi

            # Try minisign if GPG failed
            if [[ ! -f "${file}.asc" ]] && command -v minisign &>/dev/null; then
                log_info "Minisign signing: ${filename}"

                if minisign -S -m "${file}" 2>/dev/null; then
                    log_success "Minisign signature created: ${filename}.minisig"
                else
                    log_warning "Minisign signing failed"
                fi
            fi
        fi
    done
}

# ============================================================================
# GIT TAG MANAGEMENT
# ============================================================================

create_git_tag() {
    log_section "Creating Git Tag"

    local version
    version=$(get_version)
    local tag_name="v${version}"

    # Check if tag already exists
    if git rev-parse "${tag_name}" &>/dev/null; then
        log_error "Tag ${tag_name} already exists"
        log_info "Delete it first with: git tag -d ${tag_name}"
        return 1
    fi

    # Create annotated tag
    log_info "Creating tag: ${tag_name}"

    local tag_message="Claude Enhancer v${version}

AI-Driven Development Workflow System

Release Date: $(date +%Y-%m-%d)
Build Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

See CHANGELOG.md for details."

    if git tag -a "${tag_name}" -m "${tag_message}"; then
        log_success "Tag created: ${tag_name}"
        log_info "Push tag with: git push origin ${tag_name}"
    else
        log_error "Failed to create tag"
        return 1
    fi
}

# ============================================================================
# RELEASE NOTES GENERATION
# ============================================================================

generate_release_notes() {
    log_section "Generating Release Notes"

    local version
    version=$(get_version)
    local notes_file="${DIST_DIR}/RELEASE_NOTES.md"

    cat > "${notes_file}" <<EOF
# Claude Enhancer v${version}

**AI-Driven Development Workflow System**

Release Date: $(date +%Y-%m-%d)

## Overview

Claude Enhancer is a production-grade AI programming workflow system that provides:
- 8-Phase development workflow (P0-P7)
- Multi-terminal development support
- Intelligent agent orchestration
- Quality gate validation
- CI/CD integration

## Installation

\`\`\`bash
# Download release
curl -LO https://github.com/your-org/claude-enhancer/releases/download/v${version}/claude-enhancer-v${version}.tar.gz

# Verify checksum
sha256sum -c checksums.txt

# Extract
tar -xzf claude-enhancer-v${version}.tar.gz
cd claude-enhancer-${version}

# Install
./install.sh
\`\`\`

## Quick Start

\`\`\`bash
# Start new feature
ce start user-authentication

# Check status
ce status

# Advance workflow
ce next

# Validate quality
ce validate

# Publish
ce publish
\`\`\`

## What's New

EOF

    # Extract changelog for this version
    if [[ -f "${PROJECT_ROOT}/CHANGELOG.md" ]]; then
        log_info "Extracting changelog entries..."

        # Extract first section from CHANGELOG
        awk '/^## \[/{if(++count==2)exit}count==1' "${PROJECT_ROOT}/CHANGELOG.md" \
            | tail -n +2 >> "${notes_file}"
    fi

    cat >> "${notes_file}" <<EOF

## System Requirements

- Bash 4.0 or higher
- Git 2.0 or higher
- Linux or macOS

## Optional Tools

- \`jq\` - JSON processing
- \`yq\` - YAML processing
- \`gh\` - GitHub CLI integration
- \`gpg\` - Release verification

## Documentation

- [User Guide](docs/CLI_GUIDE.md)
- [Architecture](docs/SYSTEM_OVERVIEW_COMPLETE_V2.md)
- [Troubleshooting](docs/TROUBLESHOOTING_GUIDE.md)

## Checksums

See \`checksums.txt\` for SHA256 checksums of release artifacts.

## Verification

\`\`\`bash
# Verify GPG signature (if available)
gpg --verify claude-enhancer-v${version}.tar.gz.asc

# Run health check
./scripts/healthcheck.sh
\`\`\`

## Support

- Issues: https://github.com/your-org/claude-enhancer/issues
- Discussions: https://github.com/your-org/claude-enhancer/discussions

---

Generated with Claude Enhancer Release System
EOF

    log_success "Release notes created: RELEASE_NOTES.md"
}

# ============================================================================
# SUMMARY AND REPORT
# ============================================================================

generate_release_summary() {
    log_section "Release Summary"

    local version
    version=$(get_version)

    echo ""
    echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
    echo "┃             Claude Enhancer v${version} Release              ┃"
    echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
    echo ""
    echo "Release Artifacts:"
    echo ""

    if [[ -d "${DIST_DIR}" ]]; then
        ls -lh "${DIST_DIR}" | tail -n +2 | while read -r line; do
            echo "  ${line}"
        done
    fi

    echo ""
    echo "Next Steps:"
    echo ""
    echo "  1. Review release artifacts in: ${DIST_DIR}"
    echo "  2. Test installation from tarball"
    echo "  3. Push git tag: git push origin v${version}"
    echo "  4. Create GitHub release (if using gh):"
    echo "     gh release create v${version} ${DIST_DIR}/* --notes-file ${DIST_DIR}/RELEASE_NOTES.md"
    echo "  5. Announce release"
    echo ""
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    local skip_tests=false
    local skip_tag=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --skip-tag)
                skip_tag=true
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Create a production release of Claude Enhancer.

OPTIONS:
    --skip-tests    Skip test execution
    --skip-tag      Skip git tag creation
    -h, --help      Show this help message

EXAMPLES:
    $0                    # Full release with tests and tag
    $0 --skip-tests       # Release without running tests
    $0 --skip-tag         # Release without creating git tag

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
    echo "║       Claude Enhancer Release Preparation System             ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    # Pre-flight checks
    check_prerequisites || exit 1
    check_git_status || exit 1
    validate_version_consistency || exit 1

    # Run tests unless skipped
    if [[ "${skip_tests}" == "false" ]]; then
        run_tests || {
            log_error "Tests failed. Use --skip-tests to override (not recommended)"
            exit 1
        }
    else
        log_warning "Skipping tests (--skip-tests specified)"
    fi

    # Create release artifacts
    create_dist_directory
    create_tarball
    generate_checksums
    sign_artifacts
    generate_release_notes

    # Create git tag unless skipped
    if [[ "${skip_tag}" == "false" ]]; then
        create_git_tag || log_warning "Tag creation failed (use --skip-tag to skip)"
    else
        log_warning "Skipping git tag creation (--skip-tag specified)"
    fi

    # Show summary
    generate_release_summary

    log_success "Release preparation completed successfully!"

    return 0
}

# Run main function
main "$@"
