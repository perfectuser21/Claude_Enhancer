#!/usr/bin/env bash
# File Permissions Enforcement for Claude Enhancer v5.4.0
# Purpose: Set correct permissions for all automation scripts and sensitive files
# Security: 750 for scripts (owner+group execute, no world), 640 for configs
# Usage: Run during installation or as security audit

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# PERMISSION PROFILES
# ============================================================

# Executable scripts: 750 (rwxr-x---)
# - Owner: read, write, execute
# - Group: read, execute
# - World: no access
SCRIPT_PERMS=750

# Configuration files: 640 (rw-r-----)
# - Owner: read, write
# - Group: read
# - World: no access
CONFIG_PERMS=640

# Sensitive data: 600 (rw-------)
# - Owner: read, write
# - Group: no access
# - World: no access
SENSITIVE_PERMS=600

# Directories: 750 (rwxr-x---)
DIR_PERMS=750

# ============================================================
# LOGGING FUNCTIONS
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $*"
}

log_error() {
    echo -e "${RED}[✗]${NC} $*"
}

# ============================================================
# PERMISSION ENFORCEMENT
# ============================================================

# Set permissions for executable scripts
enforce_script_permissions() {
    local fixed=0
    local skipped=0
    local errors=0

    log_info "Enforcing script permissions (${SCRIPT_PERMS})..."

    # Find all .sh files in automation directory
    while IFS= read -r script; do
        if [[ -f "$script" ]]; then
            local current_perms=$(stat -c%a "$script" 2>/dev/null || stat -f%Lp "$script" 2>/dev/null || echo "000")

            if [[ "$current_perms" != "$SCRIPT_PERMS" ]]; then
                if chmod "$SCRIPT_PERMS" "$script" 2>/dev/null; then
                    log_success "Fixed: $script (${current_perms} → ${SCRIPT_PERMS})"
                    fixed=$((fixed + 1))
                else
                    log_error "Failed: $script (permission denied)"
                    errors=$((errors + 1))
                fi
            else
                skipped=$((skipped + 1))
            fi
        fi
    done < <(find "${PROJECT_ROOT}/.workflow/automation" -type f -name "*.sh" 2>/dev/null)

    # Also fix Claude hooks
    while IFS= read -r hook; do
        if [[ -f "$hook" ]]; then
            local current_perms=$(stat -c%a "$hook" 2>/dev/null || stat -f%Lp "$hook" 2>/dev/null || echo "000")

            if [[ "$current_perms" != "$SCRIPT_PERMS" ]]; then
                if chmod "$SCRIPT_PERMS" "$hook" 2>/dev/null; then
                    log_success "Fixed: $hook (${current_perms} → ${SCRIPT_PERMS})"
                    fixed=$((fixed + 1))
                else
                    log_error "Failed: $hook (permission denied)"
                    errors=$((errors + 1))
                fi
            else
                skipped=$((skipped + 1))
            fi
        fi
    done < <(find "${PROJECT_ROOT}/.claude/hooks" -type f -name "*.sh" 2>/dev/null)

    log_info "Scripts: ${fixed} fixed, ${skipped} already correct, ${errors} errors"
    return $errors
}

# Set permissions for configuration files
enforce_config_permissions() {
    local fixed=0
    local skipped=0
    local errors=0

    log_info "Enforcing config permissions (${CONFIG_PERMS})..."

    # Configuration file patterns
    local config_patterns=(
        "*.yml"
        "*.yaml"
        "*.json"
        "*.toml"
        "*.ini"
        ".env.example"
        ".shellcheckrc"
        ".flake8"
        "pyproject.toml"
        "pytest.ini"
        ".coveragerc"
    )

    for pattern in "${config_patterns[@]}"; do
        while IFS= read -r config; do
            if [[ -f "$config" ]]; then
                # Skip if it's in .git or node_modules
                if [[ "$config" =~ \.git/ ]] || [[ "$config" =~ node_modules/ ]]; then
                    continue
                fi

                local current_perms=$(stat -c%a "$config" 2>/dev/null || stat -f%Lp "$config" 2>/dev/null || echo "000")

                if [[ "$current_perms" != "$CONFIG_PERMS" ]]; then
                    if chmod "$CONFIG_PERMS" "$config" 2>/dev/null; then
                        log_success "Fixed: $config (${current_perms} → ${CONFIG_PERMS})"
                        fixed=$((fixed + 1))
                    else
                        log_warning "Skipped: $config (permission denied or not applicable)"
                        skipped=$((skipped + 1))
                    fi
                else
                    skipped=$((skipped + 1))
                fi
            fi
        done < <(find "${PROJECT_ROOT}" -maxdepth 3 -type f -name "$pattern" 2>/dev/null)
    done

    log_info "Configs: ${fixed} fixed, ${skipped} already correct or skipped"
    return 0
}

# Set permissions for sensitive files (secrets, keys, credentials)
enforce_sensitive_permissions() {
    local fixed=0
    local skipped=0
    local errors=0

    log_info "Enforcing sensitive file permissions (${SENSITIVE_PERMS})..."

    # Sensitive file patterns
    local sensitive_patterns=(
        ".env"
        "*.pem"
        "*.key"
        "*secret*"
        "*credentials*"
        ".aws/credentials"
        ".ssh/id_*"
    )

    for pattern in "${sensitive_patterns[@]}"; do
        while IFS= read -r file; do
            if [[ -f "$file" ]] && [[ ! "$file" =~ \.example$ ]]; then
                local current_perms=$(stat -c%a "$file" 2>/dev/null || stat -f%Lp "$file" 2>/dev/null || echo "000")

                if [[ "$current_perms" != "$SENSITIVE_PERMS" ]]; then
                    if chmod "$SENSITIVE_PERMS" "$file" 2>/dev/null; then
                        log_success "Fixed: $file (${current_perms} → ${SENSITIVE_PERMS})"
                        fixed=$((fixed + 1))
                    else
                        log_error "Failed: $file (permission denied)"
                        errors=$((errors + 1))
                    fi
                else
                    skipped=$((skipped + 1))
                fi
            fi
        done < <(find "${PROJECT_ROOT}" -maxdepth 3 -type f -name "$pattern" 2>/dev/null)
    done

    log_info "Sensitive: ${fixed} fixed, ${skipped} already correct, ${errors} errors"
    return $errors
}

# Set permissions for directories
enforce_directory_permissions() {
    local fixed=0
    local skipped=0
    local errors=0

    log_info "Enforcing directory permissions (${DIR_PERMS})..."

    # Important directories
    local directories=(
        "${PROJECT_ROOT}/.workflow/automation/core"
        "${PROJECT_ROOT}/.workflow/automation/security"
        "${PROJECT_ROOT}/.workflow/automation/queue"
        "${PROJECT_ROOT}/.workflow/automation/rollback"
        "${PROJECT_ROOT}/.workflow/automation/utils"
        "${PROJECT_ROOT}/.claude/hooks"
        "${PROJECT_ROOT}/.claude/core"
    )

    for dir in "${directories[@]}"; do
        if [[ -d "$dir" ]]; then
            local current_perms=$(stat -c%a "$dir" 2>/dev/null || stat -f%Lp "$dir" 2>/dev/null || echo "000")

            if [[ "$current_perms" != "$DIR_PERMS" ]]; then
                if chmod "$DIR_PERMS" "$dir" 2>/dev/null; then
                    log_success "Fixed: $dir (${current_perms} → ${DIR_PERMS})"
                    fixed=$((fixed + 1))
                else
                    log_error "Failed: $dir (permission denied)"
                    errors=$((errors + 1))
                fi
            else
                skipped=$((skipped + 1))
            fi
        fi
    done

    log_info "Directories: ${fixed} fixed, ${skipped} already correct, ${errors} errors"
    return $errors
}

# ============================================================
# AUDIT & REPORTING
# ============================================================

# Audit current permissions
audit_permissions() {
    log_info "Auditing file permissions..."
    echo ""

    local insecure_count=0

    # Check for world-writable files
    log_info "Checking for world-writable files (dangerous)..."
    while IFS= read -r file; do
        if [[ ! "$file" =~ \.git/ ]]; then
            log_error "World-writable: $file"
            insecure_count=$((insecure_count + 1))
        fi
    done < <(find "${PROJECT_ROOT}" -type f -perm -0002 2>/dev/null | head -20)

    if [[ $insecure_count -eq 0 ]]; then
        log_success "No world-writable files found"
    else
        log_warning "Found $insecure_count world-writable files"
    fi

    echo ""

    # Check for overly permissive scripts (755 or 777)
    log_info "Checking for overly permissive scripts..."
    local permissive_count=0

    while IFS= read -r script; do
        if [[ -f "$script" ]] && [[ ! "$script" =~ \.git/ ]]; then
            local perms=$(stat -c%a "$script" 2>/dev/null || stat -f%Lp "$script" 2>/dev/null || echo "000")

            if [[ "$perms" == "755" ]] || [[ "$perms" == "777" ]]; then
                log_warning "Overly permissive: $script ($perms, should be $SCRIPT_PERMS)"
                permissive_count=$((permissive_count + 1))
            fi
        fi
    done < <(find "${PROJECT_ROOT}/.workflow" -type f -name "*.sh" 2>/dev/null)

    if [[ $permissive_count -eq 0 ]]; then
        log_success "All scripts have appropriate permissions"
    else
        log_warning "Found $permissive_count scripts with overly permissive settings"
    fi

    echo ""
}

# Generate permission report
generate_report() {
    local report_file="/tmp/permission_audit_$(date +%s).txt"

    log_info "Generating detailed permission report..."

    cat > "$report_file" <<REPORT
========================================
Permission Audit Report
========================================
Generated: $(date)
Project: Claude Enhancer v5.4.0

Security Standards:
- Scripts: ${SCRIPT_PERMS} (rwxr-x---)
- Configs: ${CONFIG_PERMS} (rw-r-----)
- Sensitive: ${SENSITIVE_PERMS} (rw-------)
- Directories: ${DIR_PERMS} (rwxr-x---)

========================================
Current Permissions
========================================

REPORT

    # Automation scripts
    echo "Automation Scripts:" >> "$report_file"
    find "${PROJECT_ROOT}/.workflow/automation" -type f -name "*.sh" -exec ls -lh {} \; 2>/dev/null >> "$report_file"

    echo "" >> "$report_file"

    # Claude hooks
    echo "Claude Hooks:" >> "$report_file"
    find "${PROJECT_ROOT}/.claude/hooks" -type f -name "*.sh" -exec ls -lh {} \; 2>/dev/null >> "$report_file"

    echo "" >> "$report_file"

    # Configuration files
    echo "Configuration Files:" >> "$report_file"
    find "${PROJECT_ROOT}" -maxdepth 2 -type f \( -name "*.yml" -o -name "*.yaml" -o -name "*.json" \) -exec ls -lh {} \; 2>/dev/null >> "$report_file"

    log_success "Report saved: $report_file"
    echo ""
    cat "$report_file"
}

# ============================================================
# MAIN EXECUTION
# ============================================================

main() {
    local command="${1:-enforce}"

    echo ""
    log_info "╔════════════════════════════════════════════════════╗"
    log_info "║   Permission Enforcement - Claude Enhancer v5.4.0  ║"
    log_info "╚════════════════════════════════════════════════════╝"
    echo ""

    case "$command" in
        enforce)
            log_info "Mode: Enforce (will fix permissions)"
            echo ""

            local total_errors=0

            enforce_script_permissions || total_errors=$((total_errors + $?))
            echo ""

            enforce_config_permissions || total_errors=$((total_errors + $?))
            echo ""

            enforce_sensitive_permissions || total_errors=$((total_errors + $?))
            echo ""

            enforce_directory_permissions || total_errors=$((total_errors + $?))
            echo ""

            if [[ $total_errors -eq 0 ]]; then
                log_success "All permissions enforced successfully"
                return 0
            else
                log_warning "Completed with $total_errors errors"
                return 1
            fi
            ;;

        audit)
            log_info "Mode: Audit (read-only, no changes)"
            echo ""

            audit_permissions
            ;;

        report)
            log_info "Mode: Report (generate detailed report)"
            echo ""

            generate_report
            ;;

        help|*)
            cat <<HELP
Usage: $0 [command]

Commands:
  enforce    Fix file permissions (default)
  audit      Audit current permissions (read-only)
  report     Generate detailed permission report

Permission Standards:
  Scripts (*.sh):        750 (rwxr-x---) - owner+group execute only
  Configs (*.yml, etc):  640 (rw-r-----) - owner write, group read
  Sensitive (*.pem):     600 (rw-------) - owner only
  Directories:           750 (rwxr-x---) - owner+group access only

Examples:
  $0                    # Fix all permissions
  $0 audit              # Check current permissions
  $0 report             # Generate detailed report

Security Benefits:
  ✓ Prevents unauthorized execution by non-group users
  ✓ Protects sensitive configuration from world access
  ✓ Follows least-privilege principle
  ✓ Complies with security best practices

Note: Some operations may require sudo for system directories.
HELP
            ;;
    esac
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
