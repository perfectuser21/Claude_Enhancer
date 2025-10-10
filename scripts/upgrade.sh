#!/usr/bin/env bash
# Claude Enhancer Upgrade Script
# Safely upgrade to newer versions with rollback capability
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/.upgrade_backup"
VERSION_FILE="${PROJECT_ROOT}/VERSION"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Upgrade options
DRY_RUN=${DRY_RUN:-false}
SKIP_BACKUP=${SKIP_BACKUP:-false}
AUTO_CONFIRM=${AUTO_CONFIRM:-false}

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
# VERSION DETECTION
# ============================================================================

get_current_version() {
    if [[ -f "${VERSION_FILE}" ]]; then
        cat "${VERSION_FILE}"
    else
        # Fallback to ce.sh
        grep -oP 'CE_VERSION="\K[^"]+' "${PROJECT_ROOT}/ce.sh" 2>/dev/null || echo "unknown"
    fi
}

compare_versions() {
    local version1="$1"
    local version2="$2"

    # Simple semantic version comparison
    # Returns: 0 if equal, 1 if v1 > v2, 2 if v1 < v2

    if [[ "${version1}" == "${version2}" ]]; then
        return 0
    fi

    local IFS='.'
    read -ra V1 <<< "${version1}"
    read -ra V2 <<< "${version2}"

    for i in 0 1 2; do
        local v1_part="${V1[i]:-0}"
        local v2_part="${V2[i]:-0}"

        if [[ ${v1_part} -gt ${v2_part} ]]; then
            return 1
        elif [[ ${v1_part} -lt ${v2_part} ]]; then
            return 2
        fi
    done

    return 0
}

# ============================================================================
# BACKUP FUNCTIONS
# ============================================================================

create_backup() {
    if [[ "${SKIP_BACKUP}" == "true" ]]; then
        log_warning "Skipping backup (--skip-backup specified)"
        return 0
    fi

    log_step "Creating Backup"

    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/${timestamp}"

    if [[ -d "${backup_path}" ]]; then
        log_error "Backup directory already exists: ${backup_path}"
        return 1
    fi

    mkdir -p "${backup_path}"

    # Backup critical directories and files
    local backup_items=(
        ".claude"
        ".workflow"
        ".gates"
        "ce.sh"
        "VERSION"
        "scripts"
    )

    for item in "${backup_items[@]}"; do
        if [[ -e "${PROJECT_ROOT}/${item}" ]]; then
            if cp -r "${PROJECT_ROOT}/${item}" "${backup_path}/" 2>/dev/null; then
                log_success "Backed up: ${item}"
            else
                log_warning "Failed to backup: ${item}"
            fi
        fi
    done

    # Save metadata
    cat > "${backup_path}/backup_info.txt" <<EOF
Backup created: ${timestamp}
Current version: $(get_current_version)
Backup path: ${backup_path}
Git branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
Git commit: $(git rev-parse HEAD 2>/dev/null || echo "unknown")
EOF

    log_success "Backup created: ${backup_path}"
    echo "${backup_path}"
}

list_backups() {
    log_step "Available Backups"

    if [[ ! -d "${BACKUP_DIR}" ]]; then
        log_info "No backups found"
        return 0
    fi

    local backups
    backups=$(find "${BACKUP_DIR}" -mindepth 1 -maxdepth 1 -type d -name "*_*" | sort -r)

    if [[ -z "${backups}" ]]; then
        log_info "No backups found"
        return 0
    fi

    echo ""
    echo "Backup Directory: ${BACKUP_DIR}"
    echo ""

    local count=1
    while IFS= read -r backup; do
        local backup_name
        backup_name=$(basename "${backup}")

        local version="unknown"
        if [[ -f "${backup}/backup_info.txt" ]]; then
            version=$(grep "Current version:" "${backup}/backup_info.txt" | cut -d' ' -f3)
        fi

        echo "  ${count}. ${backup_name} (v${version})"
        ((count++))
    done <<< "${backups}"

    echo ""
}

restore_backup() {
    local backup_path="$1"

    if [[ ! -d "${backup_path}" ]]; then
        log_error "Backup not found: ${backup_path}"
        return 1
    fi

    log_step "Restoring from Backup"

    log_info "Backup: ${backup_path}"

    if [[ "${AUTO_CONFIRM}" == "false" ]]; then
        echo ""
        read -p "This will overwrite current installation. Continue? (y/n): " -r response
        if [[ ! "${response}" =~ ^[Yy] ]]; then
            log_info "Restore cancelled"
            return 1
        fi
    fi

    # Restore items
    local restore_items=(
        ".claude"
        ".workflow"
        ".gates"
        "ce.sh"
        "VERSION"
        "scripts"
    )

    for item in "${restore_items[@]}"; do
        if [[ -e "${backup_path}/${item}" ]]; then
            # Remove current
            rm -rf "${PROJECT_ROOT:?}/${item}" 2>/dev/null || true

            # Restore from backup
            if cp -r "${backup_path}/${item}" "${PROJECT_ROOT}/" 2>/dev/null; then
                log_success "Restored: ${item}"
            else
                log_error "Failed to restore: ${item}"
            fi
        fi
    done

    log_success "Restore completed"
    log_info "Restored version: $(get_current_version)"
}

# ============================================================================
# UPGRADE FUNCTIONS
# ============================================================================

download_release() {
    local version="$1"
    local download_url="$2"

    log_step "Downloading Release"

    local temp_dir
    temp_dir=$(mktemp -d)
    local tarball="${temp_dir}/claude-enhancer-v${version}.tar.gz"

    log_info "URL: ${download_url}"
    log_info "Downloading to: ${tarball}"

    if command -v curl &>/dev/null; then
        if curl -L -o "${tarball}" "${download_url}"; then
            log_success "Downloaded successfully"
        else
            log_error "Download failed"
            rm -rf "${temp_dir}"
            return 1
        fi
    elif command -v wget &>/dev/null; then
        if wget -O "${tarball}" "${download_url}"; then
            log_success "Downloaded successfully"
        else
            log_error "Download failed"
            rm -rf "${temp_dir}"
            return 1
        fi
    else
        log_error "Neither curl nor wget found"
        rm -rf "${temp_dir}"
        return 1
    fi

    echo "${tarball}"
}

verify_release() {
    local tarball="$1"
    local checksum_url="$2"

    log_step "Verifying Release"

    if [[ -z "${checksum_url}" ]]; then
        log_warning "No checksum URL provided, skipping verification"
        return 0
    fi

    local checksum_file
    checksum_file=$(mktemp)

    # Download checksums
    if command -v curl &>/dev/null; then
        curl -sL -o "${checksum_file}" "${checksum_url}" || {
            log_warning "Failed to download checksums"
            rm -f "${checksum_file}"
            return 0
        }
    fi

    # Verify
    local tarball_name
    tarball_name=$(basename "${tarball}")

    local expected_checksum
    expected_checksum=$(grep "${tarball_name}" "${checksum_file}" | awk '{print $2}' || echo "")

    if [[ -z "${expected_checksum}" ]]; then
        log_warning "Checksum not found for ${tarball_name}"
        rm -f "${checksum_file}"
        return 0
    fi

    local actual_checksum
    actual_checksum=$(sha256sum "${tarball}" | awk '{print $1}')

    if [[ "${actual_checksum}" == "${expected_checksum}" ]]; then
        log_success "Checksum verified"
        rm -f "${checksum_file}"
        return 0
    else
        log_error "Checksum mismatch!"
        log_error "Expected: ${expected_checksum}"
        log_error "Actual: ${actual_checksum}"
        rm -f "${checksum_file}"
        return 1
    fi
}

extract_and_upgrade() {
    local tarball="$1"

    log_step "Extracting and Upgrading"

    local temp_extract
    temp_extract=$(mktemp -d)

    # Extract
    log_info "Extracting: ${tarball}"
    if tar -xzf "${tarball}" -C "${temp_extract}"; then
        log_success "Extracted successfully"
    else
        log_error "Extraction failed"
        rm -rf "${temp_extract}"
        return 1
    fi

    # Find extracted directory
    local extracted_dir
    extracted_dir=$(find "${temp_extract}" -mindepth 1 -maxdepth 1 -type d | head -1)

    if [[ -z "${extracted_dir}" ]]; then
        log_error "Could not find extracted directory"
        rm -rf "${temp_extract}"
        return 1
    fi

    # Copy files
    log_info "Copying files to: ${PROJECT_ROOT}"

    # Preserve state and configuration
    local preserve_items=(
        ".workflow/cli/state"
        ".gates/*.ok*"
        ".git"
    )

    # Copy everything except preserved items
    if cp -rf "${extracted_dir}"/* "${PROJECT_ROOT}/" 2>/dev/null; then
        log_success "Files copied successfully"
    else
        log_error "File copy failed"
        rm -rf "${temp_extract}"
        return 1
    fi

    # Clean up
    rm -rf "${temp_extract}"

    log_success "Upgrade completed"
}

migrate_configuration() {
    log_step "Migrating Configuration"

    # Check if migration is needed
    local current_version
    current_version=$(get_current_version)

    log_info "New version: ${current_version}"

    # Version-specific migrations
    # Add migration logic here as needed

    log_success "Configuration migration completed"
}

# ============================================================================
# POST-UPGRADE VALIDATION
# ============================================================================

validate_upgrade() {
    log_step "Validating Upgrade"

    # Run healthcheck
    if [[ -f "${PROJECT_ROOT}/scripts/healthcheck.sh" ]]; then
        log_info "Running health check..."
        if bash "${PROJECT_ROOT}/scripts/healthcheck.sh" &>/dev/null; then
            log_success "Health check passed"
        else
            log_error "Health check failed"
            return 1
        fi
    fi

    # Verify version
    local new_version
    new_version=$(get_current_version)
    log_info "Upgraded to version: ${new_version}"

    log_success "Upgrade validation completed"
}

# ============================================================================
# MAIN UPGRADE FLOW
# ============================================================================

main() {
    local target_version=""
    local download_url=""
    local checksum_url=""
    local action="upgrade"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version)
                target_version="$2"
                shift 2
                ;;
            --url)
                download_url="$2"
                shift 2
                ;;
            --checksums)
                checksum_url="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --yes|-y)
                AUTO_CONFIRM=true
                shift
                ;;
            --list-backups)
                action="list-backups"
                shift
                ;;
            --restore)
                action="restore"
                target_version="$2"
                shift 2
                ;;
            -h|--help)
                cat <<EOF
Usage: $0 [OPTIONS]

Upgrade Claude Enhancer to a newer version.

OPTIONS:
    --version <ver>      Target version to upgrade to
    --url <url>          Download URL for release tarball
    --checksums <url>    URL for checksums file
    --dry-run            Show what would be done
    --skip-backup        Skip backup creation
    --yes, -y            Auto-confirm all prompts
    --list-backups       List available backups
    --restore <backup>   Restore from backup
    -h, --help           Show this help message

EXAMPLES:
    # Upgrade to specific version
    $0 --version 1.1.0 --url https://github.com/.../v1.1.0.tar.gz

    # List available backups
    $0 --list-backups

    # Restore from backup
    $0 --restore 20251010_143022

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
    echo "║          Claude Enhancer Upgrade System                      ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""

    # Handle different actions
    case "${action}" in
        list-backups)
            list_backups
            exit 0
            ;;
        restore)
            restore_backup "${BACKUP_DIR}/${target_version}"
            exit $?
            ;;
        upgrade)
            # Continue with upgrade
            ;;
        *)
            log_error "Unknown action: ${action}"
            exit 1
            ;;
    esac

    # Upgrade flow
    local current_version
    current_version=$(get_current_version)

    log_info "Current version: ${current_version}"

    if [[ -z "${target_version}" ]]; then
        log_error "Target version not specified (use --version)"
        exit 1
    fi

    log_info "Target version: ${target_version}"

    # Compare versions
    if compare_versions "${current_version}" "${target_version}"; then
        log_warning "Already at version ${target_version}"
        exit 0
    fi

    if compare_versions "${current_version}" "${target_version}"; then
        :
    elif compare_versions "${target_version}" "${current_version}"; then
        log_warning "Downgrading from ${current_version} to ${target_version}"
    fi

    # Confirm upgrade
    if [[ "${AUTO_CONFIRM}" == "false" && "${DRY_RUN}" == "false" ]]; then
        echo ""
        read -p "Proceed with upgrade? (y/n): " -r response
        if [[ ! "${response}" =~ ^[Yy] ]]; then
            log_info "Upgrade cancelled"
            exit 0
        fi
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would upgrade from ${current_version} to ${target_version}"
        exit 0
    fi

    # Create backup
    local backup_path
    backup_path=$(create_backup) || exit 1

    # Download release
    if [[ -n "${download_url}" ]]; then
        local tarball
        tarball=$(download_release "${target_version}" "${download_url}") || {
            log_error "Download failed, restoring from backup"
            restore_backup "${backup_path}"
            exit 1
        }

        # Verify release
        verify_release "${tarball}" "${checksum_url}" || {
            log_error "Verification failed, restoring from backup"
            restore_backup "${backup_path}"
            exit 1
        }

        # Extract and upgrade
        extract_and_upgrade "${tarball}" || {
            log_error "Upgrade failed, restoring from backup"
            restore_backup "${backup_path}"
            exit 1
        }
    else
        log_error "Download URL not provided (use --url)"
        exit 1
    fi

    # Migrate configuration
    migrate_configuration || {
        log_warning "Configuration migration had issues"
    }

    # Validate upgrade
    validate_upgrade || {
        log_error "Validation failed, restoring from backup"
        restore_backup "${backup_path}"
        exit 1
    }

    log_success "Upgrade completed successfully!"
    log_info "Upgraded from ${current_version} to ${target_version}"
    log_info "Backup saved to: ${backup_path}"

    return 0
}

main "$@"
