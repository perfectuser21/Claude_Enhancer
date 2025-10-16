#!/bin/bash
#===============================================================================
# Claude Enhancer Health Checker v1.0.0
# 主控健康检查和修复工具
#
# 功能：一键自检系统健康状况，支持自动修复
#
# Usage:
#   ./scripts/health-checker.sh --check    # 只检查，不修复
#   ./scripts/health-checker.sh --fix      # 检查并自动修复
#   ./scripts/health-checker.sh --report   # 生成详细报告
#   ./scripts/health-checker.sh --all      # 检查+修复+报告
#
# Modular Usage (for CI/CD):
#   ./scripts/health-checker.sh --check-version      # Version check only
#   ./scripts/health-checker.sh --check-documents    # Document check only
#   ./scripts/health-checker.sh --check-workflows    # Workflow count only
#   ./scripts/health-checker.sh --check-bdd          # BDD feature count only
#   ./scripts/health-checker.sh --check-hooks        # Hooks count only
#   ./scripts/health-checker.sh --check-backups      # Backup file check only
#   ./scripts/health-checker.sh --check-configs      # Config duplication check only
#===============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${PROJECT_ROOT}/VERSION"
EVIDENCE_DIR="${PROJECT_ROOT}/evidence"
TEMP_DIR="${PROJECT_ROOT}/.temp"
GLOBAL_CLAUDE_MD="/root/.claude/CLAUDE.md"
LOCAL_CLAUDE_MD="${PROJECT_ROOT}/CLAUDE.md"

# Score tracking
TOTAL_SCORE=0
MAX_SCORE=0
ISSUES_FOUND=()
FIXES_APPLIED=()

# Check categories with weights
declare -A CHECK_WEIGHTS=(
    ["version_consistency"]=20
    ["document_duplication"]=15
    ["complexity_thresholds"]=15
    ["forbidden_keywords"]=15
    ["backup_cleanup"]=10
    ["temp_cleanup"]=10
    ["git_hooks_health"]=15
)

#===============================================================================
# Utility Functions
#===============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC} $*"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*"
}

log_section() {
    echo ""
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}$*${NC}"
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

add_issue() {
    ISSUES_FOUND+=("$1")
}

add_fix() {
    FIXES_APPLIED+=("$1")
}

update_score() {
    local category=$1
    local passed=$2  # 1 for pass, 0 for fail
    local weight=${CHECK_WEIGHTS[$category]}

    MAX_SCORE=$((MAX_SCORE + weight))
    if [[ $passed -eq 1 ]]; then
        TOTAL_SCORE=$((TOTAL_SCORE + weight))
    fi
}

#===============================================================================
# Check 1: Version Consistency (20 points)
#===============================================================================

check_version_consistency() {
    log_section "📦 Check 1: Version Consistency (5 files)"

    if [[ ! -f "$VERSION_FILE" ]]; then
        log_error "VERSION file not found"
        add_issue "VERSION file missing"
        update_score "version_consistency" 0
        return 1
    fi

    local master_version
    master_version=$(tr -d '[:space:]' < "$VERSION_FILE")
    log_info "Master version: ${BOLD}$master_version${NC}"

    local inconsistent=0
    local locations=()

    # Check settings.json
    if [[ -f "${PROJECT_ROOT}/.claude/settings.json" ]]; then
        local settings_version
        settings_version=$(grep -oP '"version":\s*"\K[^"]+' "${PROJECT_ROOT}/.claude/settings.json" | head -1 || echo "")
        if [[ "$settings_version" != "$master_version" ]]; then
            log_error "settings.json: $settings_version (expected: $master_version)"
            add_issue "settings.json version mismatch: $settings_version"
            inconsistent=1
            locations+=("settings.json:$settings_version")
        else
            log_success "settings.json: $settings_version"
        fi
    fi

    # Check manifest.yml
    if [[ -f "${PROJECT_ROOT}/.workflow/manifest.yml" ]]; then
        local manifest_version
        manifest_version=$(grep -oP '^version:\s*\K[0-9.]+' "${PROJECT_ROOT}/.workflow/manifest.yml" || echo "")
        if [[ "$manifest_version" != "$master_version" ]]; then
            log_error "manifest.yml: $manifest_version (expected: $master_version)"
            add_issue "manifest.yml version mismatch: $manifest_version"
            inconsistent=1
            locations+=("manifest.yml:$manifest_version")
        else
            log_success "manifest.yml: $manifest_version"
        fi
    fi

    # Check package.json
    if [[ -f "${PROJECT_ROOT}/package.json" ]]; then
        local pkg_version
        pkg_version=$(grep -oP '"version":\s*"\K[^"]+' "${PROJECT_ROOT}/package.json" || echo "")
        if [[ "$pkg_version" != "$master_version" ]]; then
            log_error "package.json: $pkg_version (expected: $master_version)"
            add_issue "package.json version mismatch: $pkg_version"
            inconsistent=1
            locations+=("package.json:$pkg_version")
        else
            log_success "package.json: $pkg_version"
        fi
    fi

    # Check CHANGELOG.md
    if [[ -f "${PROJECT_ROOT}/CHANGELOG.md" ]]; then
        local changelog_version
        changelog_version=$(grep -oP '\[\K[0-9]+\.[0-9]+\.[0-9]+(?=\])' "${PROJECT_ROOT}/CHANGELOG.md" | head -1 || echo "")
        if [[ "$changelog_version" != "$master_version" ]]; then
            log_error "CHANGELOG.md: $changelog_version (expected: $master_version)"
            add_issue "CHANGELOG.md version mismatch: $changelog_version"
            inconsistent=1
            locations+=("CHANGELOG.md:$changelog_version")
        else
            log_success "CHANGELOG.md: $changelog_version"
        fi
    fi

    # Check CLAUDE.md for version numbers (informational only)
    if [[ -f "$LOCAL_CLAUDE_MD" ]]; then
        # Count unique version numbers in CLAUDE.md
        local version_count
        version_count=$(grep -oP '\d+\.\d+\.\d+' "$LOCAL_CLAUDE_MD" | sort -u | wc -l)
        if [[ $version_count -gt 3 ]]; then
            log_warning "CLAUDE.md contains $version_count different version numbers (informational)"
        else
            log_info "CLAUDE.md version references: $version_count"
        fi
    fi

    if [[ $inconsistent -eq 0 ]]; then
        log_success "All 5 version files consistent: $master_version"
        update_score "version_consistency" 1
        return 0
    else
        log_error "Version inconsistencies found in ${#locations[@]} files"
        for loc in "${locations[@]}"; do
            log_error "  - $loc"
        done
        log_info "Run: bash scripts/check_version_consistency.sh"
        update_score "version_consistency" 0
        return 1
    fi
}

fix_version_consistency() {
    log_info "🔧 Fixing version inconsistencies (5 files)..."

    if [[ ! -f "$VERSION_FILE" ]]; then
        log_error "Cannot fix: VERSION file missing"
        return 1
    fi

    local master_version
    master_version=$(tr -d '[:space:]' < "$VERSION_FILE")
    log_info "Master version: $master_version"

    # Fix settings.json
    if [[ -f "${PROJECT_ROOT}/.claude/settings.json" ]]; then
        local current_settings_version
        current_settings_version=$(grep -oP '"version":\s*"\K[^"]+' "${PROJECT_ROOT}/.claude/settings.json" | head -1 || echo "")

        if [[ "$current_settings_version" != "$master_version" ]]; then
            sed -i "s/\"version\":\s*\"[^\"]*\"/\"version\": \"$master_version\"/" "${PROJECT_ROOT}/.claude/settings.json"
            log_success "Updated settings.json: $current_settings_version → $master_version"
            add_fix "settings.json version synchronized to $master_version"
        fi
    fi

    # Fix manifest.yml
    if [[ -f "${PROJECT_ROOT}/.workflow/manifest.yml" ]]; then
        local current_manifest_version
        current_manifest_version=$(grep -oP '^version:\s*\K[0-9.]+' "${PROJECT_ROOT}/.workflow/manifest.yml" || echo "")

        if [[ "$current_manifest_version" != "$master_version" ]]; then
            sed -i "s/^version:.*/version: $master_version/" "${PROJECT_ROOT}/.workflow/manifest.yml"
            log_success "Updated manifest.yml: $current_manifest_version → $master_version"
            add_fix "manifest.yml version synchronized to $master_version"
        fi
    fi

    # Fix package.json
    if [[ -f "${PROJECT_ROOT}/package.json" ]]; then
        local current_pkg_version
        current_pkg_version=$(grep -oP '"version":\s*"\K[^"]+' "${PROJECT_ROOT}/package.json" || echo "")

        if [[ "$current_pkg_version" != "$master_version" ]]; then
            sed -i "s/\"version\":\s*\"[^\"]*\"/\"version\": \"$master_version\"/" "${PROJECT_ROOT}/package.json"
            log_success "Updated package.json: $current_pkg_version → $master_version"
            add_fix "package.json version synchronized to $master_version"
        fi
    fi

    # Fix CHANGELOG.md (update first version entry)
    if [[ -f "${PROJECT_ROOT}/CHANGELOG.md" ]]; then
        local current_changelog_version
        current_changelog_version=$(grep -oP '\[\K[0-9]+\.[0-9]+\.[0-9]+(?=\])' "${PROJECT_ROOT}/CHANGELOG.md" | head -1 || echo "")

        if [[ "$current_changelog_version" != "$master_version" ]]; then
            # This is informational only - CHANGELOG.md should be manually updated
            log_warning "CHANGELOG.md version mismatch: $current_changelog_version (expected: $master_version)"
            log_warning "CHANGELOG.md should be manually updated with release notes"
            add_issue "CHANGELOG.md requires manual update to $master_version"
        fi
    fi

    log_info "Note: CLAUDE.md version references are contextual and not auto-updated"

    return 0
}

#===============================================================================
# Check 2: Document Duplication (15 points)
#===============================================================================

check_document_duplication() {
    log_section "📄 Check 2: Document Duplication"

    local issues=0

    # Check root directory document count
    local root_doc_count
    root_doc_count=$(find "$PROJECT_ROOT" -maxdepth 1 -name "*.md" -type f | wc -l)
    log_info "Root directory: $root_doc_count .md files"

    if [[ $root_doc_count -gt 7 ]]; then
        log_error "Too many root documents: $root_doc_count (limit: 7)"
        add_issue "Root document count: $root_doc_count (exceeds limit of 7)"
        issues=1

        # List extra documents
        echo "  Documents in root:"
        find "$PROJECT_ROOT" -maxdepth 1 -name "*.md" -type f -exec basename {} \; | sort
    else
        log_success "Root document count: $root_doc_count (within limit)"
    fi

    # Check for duplicate CLAUDE.md files
    local claude_count
    claude_count=$(find "$PROJECT_ROOT" -name "CLAUDE*.md" -type f | wc -l)

    if [[ $claude_count -eq 1 ]]; then
        log_success "Single CLAUDE.md found"
    else
        log_error "Multiple CLAUDE files: $claude_count"
        add_issue "Multiple CLAUDE.md files detected: $claude_count"
        issues=1
        find "$PROJECT_ROOT" -name "CLAUDE*.md" -type f
    fi

    # Check for duplicate README files
    local readme_count
    readme_count=$(find "$PROJECT_ROOT" -name "README*.md" -type f | wc -l)

    if [[ $readme_count -eq 1 ]]; then
        log_success "Single README.md found"
    else
        log_warning "Multiple README files: $readme_count"
        add_issue "Multiple README files detected: $readme_count"
        issues=1
        find "$PROJECT_ROOT" -name "README*.md" -type f
    fi

    # Calculate similarity between local and global CLAUDE.md
    if [[ -f "$LOCAL_CLAUDE_MD" && -f "$GLOBAL_CLAUDE_MD" ]]; then
        local total_lines
        total_lines=$(wc -l < "$LOCAL_CLAUDE_MD")

        local matching_lines=0
        while IFS= read -r line; do
            if grep -Fxq "$line" "$GLOBAL_CLAUDE_MD" 2>/dev/null; then
                matching_lines=$((matching_lines + 1))
            fi
        done < "$LOCAL_CLAUDE_MD"

        local similarity=0
        if [[ $total_lines -gt 0 ]]; then
            similarity=$((matching_lines * 100 / total_lines))
        fi

        log_info "CLAUDE.md similarity (local vs global): ${similarity}%"

        if [[ $similarity -gt 80 ]]; then
            log_error "CLAUDE.md files too similar: ${similarity}% (threshold: 80%)"
            add_issue "CLAUDE.md duplication: ${similarity}% similar"
            issues=1
        elif [[ $similarity -gt 50 ]]; then
            log_warning "CLAUDE.md moderate similarity: ${similarity}%"
        else
            log_success "CLAUDE.md appropriately distinct: ${similarity}%"
        fi
    fi

    if [[ $issues -eq 0 ]]; then
        update_score "document_duplication" 1
        return 0
    else
        update_score "document_duplication" 0
        return 1
    fi
}

#===============================================================================
# Check 3: Complexity Thresholds (15 points)
#===============================================================================

check_complexity_thresholds() {
    log_section "📊 Check 3: Complexity Thresholds"

    local issues=0

    # Check BDD feature count
    local bdd_count=0
    if [[ -d "${PROJECT_ROOT}/acceptance/features" ]]; then
        bdd_count=$(find "${PROJECT_ROOT}/acceptance/features" -name "*.feature" 2>/dev/null | wc -l)
    fi
    log_info "BDD features: $bdd_count"

    if [[ $bdd_count -gt 100 ]]; then
        log_warning "BDD feature count high: $bdd_count (threshold: 100)"
        add_issue "High BDD feature count: $bdd_count"
        issues=1
    else
        log_success "BDD feature count acceptable: $bdd_count"
    fi

    # Check workflow count
    local workflow_count=0
    if [[ -d "${PROJECT_ROOT}/.github/workflows" ]]; then
        workflow_count=$(find "${PROJECT_ROOT}/.github/workflows" -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l)
    fi
    log_info "CI/CD workflows: $workflow_count"

    if [[ $workflow_count -gt 20 ]]; then
        log_warning "Workflow count high: $workflow_count (threshold: 20)"
        add_issue "High workflow count: $workflow_count"
        issues=1
    else
        log_success "Workflow count acceptable: $workflow_count"
    fi

    # Check CLAUDE.md size
    local claude_lines=0
    if [[ -f "$LOCAL_CLAUDE_MD" ]]; then
        claude_lines=$(wc -l < "$LOCAL_CLAUDE_MD")
    fi
    log_info "CLAUDE.md lines: $claude_lines"

    if [[ $claude_lines -gt 2000 ]]; then
        log_warning "CLAUDE.md very large: $claude_lines lines (threshold: 2000)"
        add_issue "Large CLAUDE.md: $claude_lines lines"
        issues=1
    else
        log_success "CLAUDE.md size acceptable: $claude_lines lines"
    fi

    # Check scripts directory size
    local script_count=0
    if [[ -d "${PROJECT_ROOT}/scripts" ]]; then
        script_count=$(find "${PROJECT_ROOT}/scripts" -type f -name "*.sh" 2>/dev/null | wc -l)
    fi
    log_info "Script files: $script_count"

    if [[ $script_count -gt 80 ]]; then
        log_warning "Script count high: $script_count (threshold: 80)"
        add_issue "High script count: $script_count"
        issues=1
    else
        log_success "Script count acceptable: $script_count"
    fi

    if [[ $issues -eq 0 ]]; then
        update_score "complexity_thresholds" 1
        return 0
    else
        update_score "complexity_thresholds" 0
        return 1
    fi
}

#===============================================================================
# Check 4: Forbidden Keywords (15 points)
#===============================================================================

check_forbidden_keywords() {
    log_section "🚫 Check 4: Forbidden Keywords"

    # Keywords that indicate incorrect positioning (should be personal tool, not enterprise)
    local forbidden=(
        "企业级"
        "Enterprise-grade"
        "Enterprise-level"
        "团队协作"
        "Team collaboration"
        "多用户"
        "Multi-user"
        "Multi-tenant"
    )

    local found=0
    local found_keywords=()

    for keyword in "${forbidden[@]}"; do
        if [[ -f "$LOCAL_CLAUDE_MD" ]] && grep -qi "$keyword" "$LOCAL_CLAUDE_MD"; then
            log_error "Found forbidden keyword: '$keyword'"
            add_issue "Forbidden keyword: $keyword"
            found_keywords+=("$keyword")
            found=1
        fi
    done

    if [[ $found -eq 0 ]]; then
        log_success "No forbidden keywords found"
        update_score "forbidden_keywords" 1
        return 0
    else
        log_error "Found ${#found_keywords[@]} forbidden keywords"
        update_score "forbidden_keywords" 0
        return 1
    fi
}

fix_forbidden_keywords() {
    log_info "🔧 Removing forbidden keywords..."

    if [[ ! -f "$LOCAL_CLAUDE_MD" ]]; then
        log_warning "CLAUDE.md not found, skipping"
        return 0
    fi

    # Create backup
    cp "$LOCAL_CLAUDE_MD" "${LOCAL_CLAUDE_MD}.bak.$(date +%Y%m%d_%H%M%S)"

    # Replace keywords - Chinese
    local changes=0
    if grep -q "企业级" "$LOCAL_CLAUDE_MD"; then
        sed -i 's/企业级/个人工具/g' "$LOCAL_CLAUDE_MD"
        changes=1
    fi
    if grep -q "团队协作" "$LOCAL_CLAUDE_MD"; then
        sed -i 's/团队协作/个人使用/g' "$LOCAL_CLAUDE_MD"
        changes=1
    fi
    if grep -q "多用户" "$LOCAL_CLAUDE_MD"; then
        sed -i 's/多用户/单用户/g' "$LOCAL_CLAUDE_MD"
        changes=1
    fi

    # Replace keywords - English
    if grep -qi "Enterprise-grade" "$LOCAL_CLAUDE_MD"; then
        sed -i 's/Enterprise-grade/Personal tool/g' "$LOCAL_CLAUDE_MD"
        sed -i 's/Enterprise-level/Personal-level/g' "$LOCAL_CLAUDE_MD"
        changes=1
    fi
    if grep -qi "Team collaboration" "$LOCAL_CLAUDE_MD"; then
        sed -i 's/Team collaboration/Personal use/g' "$LOCAL_CLAUDE_MD"
        changes=1
    fi
    if grep -qi "Multi-user" "$LOCAL_CLAUDE_MD"; then
        sed -i 's/Multi-user/Single-user/g' "$LOCAL_CLAUDE_MD"
        sed -i 's/Multi-tenant/Single-tenant/g' "$LOCAL_CLAUDE_MD"
        changes=1
    fi

    if [[ $changes -eq 1 ]]; then
        log_success "Forbidden keywords removed"
        add_fix "Removed forbidden positioning keywords from CLAUDE.md"
    else
        log_info "No forbidden keywords to remove"
    fi

    return 0
}

#===============================================================================
# Check 5: Backup File Cleanup (10 points)
#===============================================================================

check_backup_cleanup() {
    log_section "🧹 Check 5: Backup File Cleanup"

    # Find backup files older than 7 days
    local backup_files=()
    while IFS= read -r -d '' file; do
        backup_files+=("$file")
    done < <(find "$PROJECT_ROOT" -type f \
        \( -name "*.bak" -o -name "*.backup" -o -name "*~" -o -name "*.orig" \) \
        -not -path "*/node_modules/*" -not -path "*/.git/*" \
        -mtime +7 -print0 2>/dev/null)

    local count=${#backup_files[@]}

    if [[ $count -eq 0 ]]; then
        log_success "No old backup files found"
        update_score "backup_cleanup" 1
        return 0
    else
        log_warning "Found $count backup files older than 7 days"
        for file in "${backup_files[@]}"; do
            local rel_path="${file#$PROJECT_ROOT/}"
            log_info "  - $rel_path"
        done
        add_issue "Old backup files: $count files"
        update_score "backup_cleanup" 0
        return 1
    fi
}

fix_backup_cleanup() {
    log_info "🔧 Cleaning up old backup files..."

    local removed=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        local rel_path="${file#$PROJECT_ROOT/}"
        log_success "Removed: $rel_path"
        removed=$((removed + 1))
    done < <(find "$PROJECT_ROOT" -type f \
        \( -name "*.bak" -o -name "*.backup" -o -name "*~" -o -name "*.orig" \) \
        -not -path "*/node_modules/*" -not -path "*/.git/*" \
        -mtime +7 -print0 2>/dev/null)

    if [[ $removed -gt 0 ]]; then
        add_fix "Removed $removed old backup files (>7 days)"
        log_success "Cleaned up $removed backup files"
    else
        log_info "No backup files to clean"
    fi

    return 0
}

#===============================================================================
# Check 6: Temp Directory Cleanup (10 points)
#===============================================================================

check_temp_cleanup() {
    log_section "🗑️  Check 6: Temp Directory Cleanup"

    if [[ ! -d "$TEMP_DIR" ]]; then
        log_success "No .temp directory (clean)"
        update_score "temp_cleanup" 1
        return 0
    fi

    # Find files older than 7 days
    local old_files=()
    while IFS= read -r -d '' file; do
        old_files+=("$file")
    done < <(find "$TEMP_DIR" -type f -mtime +7 -print0 2>/dev/null)

    local count=${#old_files[@]}
    local temp_size
    temp_size=$(du -sh "$TEMP_DIR" 2>/dev/null | cut -f1)

    log_info ".temp directory size: $temp_size"

    if [[ $count -eq 0 ]]; then
        log_success "No old temporary files found"
        update_score "temp_cleanup" 1
        return 0
    else
        log_warning "Found $count temporary files older than 7 days"
        add_issue "Old temp files: $count files"
        update_score "temp_cleanup" 0
        return 1
    fi
}

fix_temp_cleanup() {
    log_info "🔧 Cleaning up old temporary files..."

    if [[ ! -d "$TEMP_DIR" ]]; then
        log_info "No .temp directory to clean"
        return 0
    fi

    local removed=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        removed=$((removed + 1))
    done < <(find "$TEMP_DIR" -type f -mtime +7 -print0 2>/dev/null)

    # Remove empty directories
    find "$TEMP_DIR" -type d -empty -delete 2>/dev/null || true

    if [[ $removed -gt 0 ]]; then
        add_fix "Removed $removed old temporary files (>7 days)"
        log_success "Cleaned up $removed temporary files"
    else
        log_info "No temporary files to clean"
    fi

    return 0
}

#===============================================================================
# Check 7: Git Hooks Health (15 points)
#===============================================================================

check_git_hooks_health() {
    log_section "🪝 Check 7: Git Hooks Health"

    local git_hooks_dir="${PROJECT_ROOT}/.git/hooks"
    local issues=0

    if [[ ! -d "$git_hooks_dir" ]]; then
        log_error "Git hooks directory not found"
        add_issue "Git hooks directory missing"
        update_score "git_hooks_health" 0
        return 1
    fi

    # Check critical hooks
    local required_hooks=("pre-commit" "commit-msg" "pre-push")

    for hook in "${required_hooks[@]}"; do
        local hook_path="$git_hooks_dir/$hook"

        if [[ ! -f "$hook_path" ]]; then
            log_error "Missing hook: $hook"
            add_issue "Missing git hook: $hook"
            issues=1
        elif [[ ! -x "$hook_path" ]]; then
            log_error "Hook not executable: $hook"
            add_issue "Non-executable git hook: $hook"
            issues=1
        else
            log_success "Hook OK: $hook"
        fi
    done

    # Check for bash strict mode in hooks
    for hook in "${required_hooks[@]}"; do
        local hook_path="$git_hooks_dir/$hook"
        if [[ -f "$hook_path" ]]; then
            if ! grep -q "set -euo pipefail" "$hook_path"; then
                log_warning "Hook missing strict mode: $hook"
                add_issue "Hook without strict mode: $hook"
                issues=1
            fi
        fi
    done

    if [[ $issues -eq 0 ]]; then
        log_success "All git hooks healthy"
        update_score "git_hooks_health" 1
        return 0
    else
        log_error "Git hooks health issues found"
        update_score "git_hooks_health" 0
        return 1
    fi
}

fix_git_hooks_health() {
    log_info "🔧 Fixing git hooks health..."

    local git_hooks_dir="${PROJECT_ROOT}/.git/hooks"
    local fixed=0

    # Make hooks executable
    for hook in pre-commit commit-msg pre-push; do
        local hook_path="$git_hooks_dir/$hook"
        if [[ -f "$hook_path" && ! -x "$hook_path" ]]; then
            chmod +x "$hook_path"
            log_success "Made executable: $hook"
            add_fix "Made $hook executable"
            fixed=1
        fi
    done

    # Reinstall hooks if missing
    local missing=0
    for hook in pre-commit commit-msg pre-push; do
        if [[ ! -f "$git_hooks_dir/$hook" ]]; then
            missing=1
            break
        fi
    done

    if [[ $missing -eq 1 && -f "${PROJECT_ROOT}/.claude/install.sh" ]]; then
        log_info "Reinstalling Claude hooks..."
        bash "${PROJECT_ROOT}/.claude/install.sh" >/dev/null 2>&1 || true
        add_fix "Reinstalled Claude hooks"
        fixed=1
    fi

    if [[ $fixed -eq 0 ]]; then
        log_info "No git hooks fixes needed"
    fi

    return 0
}

#===============================================================================
# Report Generation
#===============================================================================

generate_report() {
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local report_file="$EVIDENCE_DIR/health-report-$timestamp.md"

    mkdir -p "$EVIDENCE_DIR"

    local percentage=0
    if [[ $MAX_SCORE -gt 0 ]]; then
        percentage=$((TOTAL_SCORE * 100 / MAX_SCORE))
    fi

    cat > "$report_file" <<EOF
# Claude Enhancer Health Report
**Generated**: $(date '+%Y-%m-%d %H:%M:%S')
**Report ID**: health-$timestamp

## 📊 Executive Summary

### Overall Health Score
- **Score**: ${TOTAL_SCORE}/${MAX_SCORE} (${percentage}%)
- **Status**: $(get_status_text $percentage)
- **Issues Found**: ${#ISSUES_FOUND[@]}
- **Fixes Applied**: ${#FIXES_APPLIED[@]}

### Score Distribution
EOF

    for category in "${!CHECK_WEIGHTS[@]}"; do
        local weight=${CHECK_WEIGHTS[$category]}
        echo "- **${category}**: ${weight} points" >> "$report_file"
    done

    cat >> "$report_file" <<EOF

## ❌ Issues Detected

EOF

    if [[ ${#ISSUES_FOUND[@]} -eq 0 ]]; then
        echo "✅ **No issues found!** System is healthy." >> "$report_file"
    else
        local counter=1
        for issue in "${ISSUES_FOUND[@]}"; do
            echo "${counter}. $issue" >> "$report_file"
            counter=$((counter + 1))
        done
    fi

    cat >> "$report_file" <<EOF

## ✅ Fixes Applied

EOF

    if [[ ${#FIXES_APPLIED[@]} -eq 0 ]]; then
        echo "_No fixes were applied (check-only mode or no fixable issues)_" >> "$report_file"
    else
        local counter=1
        for fix in "${FIXES_APPLIED[@]}"; do
            echo "${counter}. $fix" >> "$report_file"
            counter=$((counter + 1))
        done
    fi

    cat >> "$report_file" <<EOF

## 📈 Detailed Analysis

### Version Consistency
$(print_check_detail "version_consistency")

### Document Organization
$(print_check_detail "document_duplication")

### Complexity Metrics
$(print_check_detail "complexity_thresholds")

### Code Quality
$(print_check_detail "forbidden_keywords")

### Housekeeping
$(print_check_detail "backup_cleanup")
$(print_check_detail "temp_cleanup")

### Infrastructure
$(print_check_detail "git_hooks_health")

## 💡 Recommendations

EOF

    if [[ $percentage -lt 70 ]]; then
        cat >> "$report_file" <<EOF
⚠️ **CRITICAL**: Health score below 70%. Immediate action required.

**Priority Actions:**
1. Run \`./scripts/health-checker.sh --fix\` to auto-fix issues
2. Review all failed checks manually
3. Address critical issues before deploying
4. Re-run health check to verify improvements

**Risk Level**: HIGH - Not recommended for production
EOF
    elif [[ $percentage -lt 90 ]]; then
        cat >> "$report_file" <<EOF
⚡ **ATTENTION**: Health score below 90%. Some improvements needed.

**Recommended Actions:**
1. Review issues listed above
2. Apply fixes where appropriate
3. Consider running \`--fix\` mode for automated cleanup
4. Monitor complexity metrics

**Risk Level**: MEDIUM - Review before production deployment
EOF
    else
        cat >> "$report_file" <<EOF
✅ **EXCELLENT**: System health is good (≥90%).

**Maintenance Tips:**
- Run health checks regularly (recommended: weekly)
- Keep monitoring complexity metrics
- Continue following best practices
- Schedule next check: $(date -d '+7 days' '+%Y-%m-%d' 2>/dev/null || date -v +7d '+%Y-%m-%d')

**Risk Level**: LOW - Safe for production
EOF
    fi

    cat >> "$report_file" <<EOF

## 🔄 Next Steps

- [ ] Review all reported issues
- [ ] Apply recommended fixes
- [ ] Verify fixes with \`--check\` mode
- [ ] Update documentation if needed
- [ ] Schedule next health check: **$(date -d '+7 days' '+%Y-%m-%d' 2>/dev/null || date -v +7d '+%Y-%m-%d')**

## 📋 Historical Tracking

To enable trend analysis, run this health checker regularly and compare:
\`\`\`bash
# Compare reports
diff evidence/health-report-*.md

# Track score over time
grep "Score:" evidence/health-report-*.md
\`\`\`

---
*Report generated by Claude Enhancer Health Checker v1.0.0*
*Project: ${PROJECT_ROOT}*
EOF

    log_success "Report saved: $report_file"
    echo ""
    echo -e "${CYAN}📄 Report location:${NC}"
    echo "   $report_file"
}

get_status_text() {
    local score=$1
    if [[ $score -ge 90 ]]; then
        echo "🟢 EXCELLENT"
    elif [[ $score -ge 70 ]]; then
        echo "🟡 NEEDS WORK"
    else
        echo "🔴 CRITICAL"
    fi
}

print_check_detail() {
    local category=$1
    local weight=${CHECK_WEIGHTS[$category]}

    # Check if issues contain this category
    local has_issues=0
    for issue in "${ISSUES_FOUND[@]}"; do
        if [[ "$issue" == *"$category"* ]]; then
            has_issues=1
            break
        fi
    done

    if [[ $has_issues -eq 0 ]]; then
        echo "✅ Passed (${weight} points)"
    else
        echo "❌ Failed (0/${weight} points)"
    fi
}

#===============================================================================
# Main Execution
#===============================================================================

show_usage() {
    cat <<EOF
${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}
${BOLD}${CYAN}║         Claude Enhancer Health Checker v1.0.0                 ║${NC}
${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}

${BOLD}USAGE:${NC}
  $0 ${GREEN}--check${NC}      Check system health (read-only, no modifications)
  $0 ${YELLOW}--fix${NC}        Check and automatically fix issues
  $0 ${BLUE}--report${NC}     Check and generate detailed report
  $0 ${MAGENTA}--all${NC}        Check + Fix + Report (complete analysis)
  $0 ${CYAN}--help${NC}       Show this help message

${BOLD}MODULAR CHECKS (for CI/CD):${NC}
  $0 ${GREEN}--check-version${NC}      Version consistency check only
  $0 ${GREEN}--check-documents${NC}    Document duplication check only
  $0 ${GREEN}--check-workflows${NC}    Workflow count check only
  $0 ${GREEN}--check-bdd${NC}          BDD feature count check only
  $0 ${GREEN}--check-hooks${NC}        Hooks count check only
  $0 ${GREEN}--check-backups${NC}      Backup file check only
  $0 ${GREEN}--check-configs${NC}      Config duplication check only

${BOLD}EXAMPLES:${NC}
  ${CYAN}# Daily quick check${NC}
  $0 --check

  ${CYAN}# Weekly maintenance${NC}
  $0 --fix

  ${CYAN}# Before release${NC}
  $0 --all

  ${CYAN}# Generate report for review${NC}
  $0 --report

  ${CYAN}# CI/CD individual check${NC}
  $0 --check-version

${BOLD}EXIT CODES:${NC}
  ${GREEN}0${NC} - All checks passed (score 100%)
  ${YELLOW}1${NC} - Some checks failed (score < 100%)
  ${RED}2${NC} - Critical error or invalid usage

${BOLD}HEALTH CHECKS:${NC}
  📦 Version Consistency     (20 points)
  📄 Document Duplication    (15 points)
  📊 Complexity Thresholds   (15 points)
  🚫 Forbidden Keywords      (15 points)
  🧹 Backup Cleanup          (10 points)
  🗑️  Temp Cleanup            (10 points)
  🪝 Git Hooks Health        (15 points)
  ${BOLD}────────────────────────────────${NC}
  ${BOLD}TOTAL:                 100 points${NC}

${BOLD}MORE INFO:${NC}
  Report location: ${PROJECT_ROOT}/evidence/
  Documentation: ${PROJECT_ROOT}/CLAUDE.md
EOF
}

main() {
    local mode="${1:-}"

    case "$mode" in
        --check)
            log_section "🏥 Health Check Mode (Read-Only)"
            ;;
        --fix)
            log_section "🔧 Health Check & Auto-Fix Mode"
            ;;
        --report)
            log_section "📋 Health Check & Report Generation"
            ;;
        --all)
            log_section "🚀 Complete Health Analysis"
            ;;
        --check-version)
            check_version_consistency
            exit $?
            ;;
        --check-documents)
            check_document_duplication
            exit $?
            ;;
        --check-workflows)
            check_complexity_thresholds
            exit $?
            ;;
        --check-bdd)
            check_complexity_thresholds
            exit $?
            ;;
        --check-hooks)
            check_git_hooks_health
            exit $?
            ;;
        --check-backups)
            check_backup_cleanup
            exit $?
            ;;
        --check-configs)
            check_document_duplication
            exit $?
            ;;
        --help|-h|"")
            show_usage
            exit 0
            ;;
        *)
            log_error "Invalid option: $mode"
            echo ""
            show_usage
            exit 2
            ;;
    esac

    echo ""
    log_info "Project root: ${PROJECT_ROOT}"
    log_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "Mode: $mode"
    echo ""

    # Run all checks
    check_version_consistency || true
    check_document_duplication || true
    check_complexity_thresholds || true
    check_forbidden_keywords || true
    check_backup_cleanup || true
    check_temp_cleanup || true
    check_git_hooks_health || true

    # Apply fixes if requested
    if [[ "$mode" == "--fix" || "$mode" == "--all" ]]; then
        log_section "🔧 Applying Automated Fixes"
        echo ""

        fix_version_consistency || true
        fix_forbidden_keywords || true
        fix_backup_cleanup || true
        fix_temp_cleanup || true
        fix_git_hooks_health || true

        echo ""
        log_info "Fixes completed. Re-checking..."
        echo ""

        # Re-check after fixes
        TOTAL_SCORE=0
        MAX_SCORE=0
        ISSUES_FOUND=()

        check_version_consistency || true
        check_document_duplication || true
        check_complexity_thresholds || true
        check_forbidden_keywords || true
        check_backup_cleanup || true
        check_temp_cleanup || true
        check_git_hooks_health || true
    fi

    # Display final results
    log_section "📊 Final Results"
    echo ""

    local percentage=0
    if [[ $MAX_SCORE -gt 0 ]]; then
        percentage=$((TOTAL_SCORE * 100 / MAX_SCORE))
    fi

    # ASCII art summary box
    echo -e "${BOLD}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║              HEALTH CHECK SUMMARY                              ║${NC}"
    echo -e "${BOLD}╠════════════════════════════════════════════════════════════════╣${NC}"

    if [[ $percentage -ge 90 ]]; then
        echo -e "${BOLD}║  Score: ${GREEN}${TOTAL_SCORE}/${MAX_SCORE} (${percentage}%)${NC}  ${GREEN}✓ EXCELLENT${NC}                           ║${NC}"
    elif [[ $percentage -ge 70 ]]; then
        echo -e "${BOLD}║  Score: ${YELLOW}${TOTAL_SCORE}/${MAX_SCORE} (${percentage}%)${NC}  ${YELLOW}⚠ NEEDS WORK${NC}                          ║${NC}"
    else
        echo -e "${BOLD}║  Score: ${RED}${TOTAL_SCORE}/${MAX_SCORE} (${percentage}%)${NC}  ${RED}✗ CRITICAL${NC}                            ║${NC}"
    fi

    echo -e "${BOLD}║                                                                ║${NC}"
    printf "${BOLD}║  Issues Found:   %-45s ║${NC}\n" "${#ISSUES_FOUND[@]}"
    printf "${BOLD}║  Fixes Applied:  %-45s ║${NC}\n" "${#FIXES_APPLIED[@]}"
    echo -e "${BOLD}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Show issues
    if [[ ${#ISSUES_FOUND[@]} -gt 0 ]]; then
        log_warning "Issues requiring attention:"
        for issue in "${ISSUES_FOUND[@]}"; do
            echo "  • $issue"
        done
        echo ""
    fi

    # Show fixes
    if [[ ${#FIXES_APPLIED[@]} -gt 0 ]]; then
        log_success "Fixes applied:"
        for fix in "${FIXES_APPLIED[@]}"; do
            echo "  • $fix"
        done
        echo ""
    fi

    # Generate report if requested
    if [[ "$mode" == "--report" || "$mode" == "--all" ]]; then
        echo ""
        generate_report
        echo ""
    fi

    # Recommendations
    if [[ "$mode" == "--check" && ${#ISSUES_FOUND[@]} -gt 0 ]]; then
        echo ""
        log_info "💡 Next steps:"
        echo "   • Run ${BOLD}--fix${NC} to automatically resolve issues"
        echo "   • Run ${BOLD}--report${NC} to generate detailed analysis"
        echo "   • Run ${BOLD}--all${NC} for complete check + fix + report"
    fi

    echo ""

    # Exit code based on score
    if [[ $percentage -eq 100 ]]; then
        exit 0
    else
        exit 1
    fi
}

# Execute main function
main "$@"
