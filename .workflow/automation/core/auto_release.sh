#!/usr/bin/env bash
# Auto Release Script for Claude Enhancer v5.4.0
# Purpose: Automated version tagging, changelog generation, and GitHub releases
# Used by: P6 release workflow
# Tier: 5 (Critical - Requires explicit confirmation)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"
# shellcheck source=../security/audit_log.sh
source "${SCRIPT_DIR}/../security/audit_log.sh"

# Configuration
VERSION_FILE="VERSION"
CHANGELOG_FILE="CHANGELOG.md"
DRY_RUN="${CE_DRY_RUN:-0}"
AUTO_RELEASE="${CE_AUTO_RELEASE:-0}"
PRERELEASE="${CE_PRERELEASE:-0}"
GENERATE_ASSETS="${CE_GENERATE_ASSETS:-0}"

# Semver regex
SEMVER_REGEX='^v?([0-9]+)\.([0-9]+)\.([0-9]+)(-([a-zA-Z0-9.-]+))?(\+([a-zA-Z0-9.-]+))?$'

# ============================================================
# VERSION CALCULATION
# ============================================================

get_current_version() {
    local version=""

    # Strategy 1: Read from VERSION file
    if [[ -f "$VERSION_FILE" ]]; then
        version=$(cat "$VERSION_FILE" | tr -d '[:space:]')
        if [[ -n "$version" ]]; then
            echo "$version"
            return 0
        fi
    fi

    # Strategy 2: Get latest git tag
    version=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$version" ]]; then
        echo "$version"
        return 0
    fi

    # Strategy 3: Default to v0.0.0
    echo "v0.0.0"
}

get_next_version() {
    local current_version="$1"
    local bump_type="${2:-patch}"

    log_debug "Calculating next version: current=$current_version, bump=$bump_type"

    # Parse semver
    if [[ "$current_version" =~ $SEMVER_REGEX ]]; then
        local major="${BASH_REMATCH[1]}"
        local minor="${BASH_REMATCH[2]}"
        local patch="${BASH_REMATCH[3]}"
        local prerelease="${BASH_REMATCH[5]}"
        local buildmeta="${BASH_REMATCH[7]}"

        log_debug "Parsed version: major=$major, minor=$minor, patch=$patch"

        case "$bump_type" in
            major)
                echo "v$((major + 1)).0.0"
                ;;
            minor)
                echo "v${major}.$((minor + 1)).0.0"
                ;;
            patch)
                echo "v${major}.${minor}.$((patch + 1))"
                ;;
            prerelease)
                # Increment prerelease version
                if [[ -n "$prerelease" ]]; then
                    # Extract numeric part
                    if [[ "$prerelease" =~ ([a-zA-Z]+)\.([0-9]+)$ ]]; then
                        local pre_label="${BASH_REMATCH[1]}"
                        local pre_num="${BASH_REMATCH[2]}"
                        echo "v${major}.${minor}.${patch}-${pre_label}.$((pre_num + 1))"
                    else
                        echo "v${major}.${minor}.${patch}-${prerelease}.1"
                    fi
                else
                    echo "v${major}.${minor}.${patch}-rc.1"
                fi
                ;;
            *)
                die "Invalid bump type: $bump_type (use: major, minor, patch, prerelease)"
                ;;
        esac
    else
        die "Invalid version format: $current_version (expected semver: v1.2.3)"
    fi
}

detect_bump_type_from_commits() {
    local since_tag="$1"

    log_debug "Detecting bump type from commits since $since_tag"

    # Get commits since last tag
    local commits=$(git log --pretty=format:"%s" "${since_tag}..HEAD" 2>/dev/null || echo "")

    if [[ -z "$commits" ]]; then
        log_warning "No commits found since $since_tag"
        echo "patch"
        return
    fi

    # Check for breaking changes (major bump)
    if echo "$commits" | grep -qiE "BREAKING CHANGE|BREAKING:|!:"; then
        echo "major"
        return
    fi

    # Check for new features (minor bump)
    if echo "$commits" | grep -qiE "^feat(\(|:)|^feature(\(|:)"; then
        echo "minor"
        return
    fi

    # Default to patch
    echo "patch"
}

validate_version() {
    local version="$1"

    if [[ ! "$version" =~ $SEMVER_REGEX ]]; then
        log_error "Invalid semver format: $version"
        log_info "Expected format: v1.2.3 or v1.2.3-rc.1+build.123"
        return 1
    fi

    # Check if tag already exists
    if git rev-parse "$version" &>/dev/null; then
        log_error "Tag $version already exists"
        log_info "Use a different version or delete the existing tag"
        return 1
    fi

    return 0
}

# ============================================================
# CHANGELOG GENERATION
# ============================================================

generate_release_notes() {
    local version="$1"
    local previous_version="$2"

    log_info "Generating release notes for $version..."

    # Get commit range
    local commit_range="${previous_version}..HEAD"
    if [[ -z "$previous_version" || "$previous_version" == "v0.0.0" ]]; then
        commit_range="HEAD"
    fi

    # Get commits
    local commits=$(git log "$commit_range" --pretty=format:"- %s (%h)" --no-merges 2>/dev/null || echo "")

    if [[ -z "$commits" ]]; then
        log_warning "No commits found in range: $commit_range"
        commits="- Initial release"
    fi

    # Categorize commits
    local features=$(echo "$commits" | grep -E "^- (feat|feature)(\(|:)" || true)
    local fixes=$(echo "$commits" | grep -E "^- (fix|bugfix)(\(|:)" || true)
    local perf=$(echo "$commits" | grep -E "^- (perf|performance)(\(|:)" || true)
    local docs=$(echo "$commits" | grep -E "^- (docs|documentation)(\(|:)" || true)
    local breaking=$(echo "$commits" | grep -E "BREAKING|!:" || true)
    local others=$(echo "$commits" | grep -vE "^- (feat|feature|fix|bugfix|perf|performance|docs|documentation)" || true)

    # Get statistics
    local stats=$(get_release_stats "$commit_range")

    # Build release notes
    cat <<EOF
## Release $version

**Release Date**: $(date +"%Y-%m-%d %H:%M:%S %Z")
**Previous Version**: ${previous_version:-None}

$(if [[ -n "$breaking" ]]; then echo "### ⚠️  BREAKING CHANGES

$breaking
"; fi)

### ✨ New Features

$(if [[ -n "$features" ]]; then echo "$features"; else echo "No new features in this release."; fi)

### 🐛 Bug Fixes

$(if [[ -n "$fixes" ]]; then echo "$fixes"; else echo "No bug fixes in this release."; fi)

### ⚡ Performance Improvements

$(if [[ -n "$perf" ]]; then echo "$perf"; else echo "No performance improvements in this release."; fi)

### 📚 Documentation

$(if [[ -n "$docs" ]]; then echo "$docs"; else echo "No documentation updates in this release."; fi)

### 🔧 Other Changes

$(if [[ -n "$others" ]]; then echo "$others"; else echo "No other changes in this release."; fi)

---

### 📊 Statistics

$stats

---

### 🔗 Links

**Full Changelog**: https://github.com/$(get_repo_slug)/compare/${previous_version}...${version}

---

**Generated by Claude Enhancer v5.4.0**
EOF
}

get_release_stats() {
    local commit_range="$1"

    # Count commits
    local commit_count=$(git rev-list --count $commit_range 2>/dev/null || echo "0")

    # Count contributors
    local contributors=$(git log $commit_range --format='%aN' --no-merges 2>/dev/null | sort -u | wc -l)

    # Get file changes
    local files_changed=$(git diff --name-only $commit_range 2>/dev/null | wc -l)
    local insertions=$(git diff --shortstat $commit_range 2>/dev/null | \
        grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo "0")
    local deletions=$(git diff --shortstat $commit_range 2>/dev/null | \
        grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo "0")

    cat <<EOF
- **Commits**: $commit_count
- **Contributors**: $contributors
- **Files Changed**: $files_changed
- **Insertions**: +$insertions
- **Deletions**: -$deletions
EOF
}

update_changelog_file() {
    local version="$1"
    local release_notes="$2"

    log_info "Updating $CHANGELOG_FILE..."

    # Create CHANGELOG.md if it doesn't exist
    if [[ ! -f "$CHANGELOG_FILE" ]]; then
        cat > "$CHANGELOG_FILE" <<EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

EOF
    fi

    # Insert new release notes at the top (after header)
    local temp_file="${CHANGELOG_FILE}.tmp"

    # Extract header
    head -n 6 "$CHANGELOG_FILE" > "$temp_file"

    # Add new release
    echo "$release_notes" >> "$temp_file"
    echo "" >> "$temp_file"

    # Append existing content (skip header)
    tail -n +7 "$CHANGELOG_FILE" >> "$temp_file" 2>/dev/null || true

    # Replace original
    mv "$temp_file" "$CHANGELOG_FILE"

    log_success "Changelog updated"
}

# ============================================================
# GIT TAG OPERATIONS
# ============================================================

create_git_tag() {
    local version="$1"
    local release_notes="$2"

    log_info "Creating git tag: $version"

    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would create tag $version"
        return 0
    fi

    # Create annotated tag with release notes
    local tag_message="Release $version

$(echo "$release_notes" | head -20)
"

    if git tag -a "$version" -m "$tag_message"; then
        log_success "Git tag created: $version"
        audit_git_operation "create_tag" "$version" "success" "Annotated tag created"
        return 0
    else
        log_error "Failed to create git tag"
        audit_git_operation "create_tag" "$version" "failed" "Tag creation failed"
        return 1
    fi
}

push_tag() {
    local version="$1"

    log_info "Pushing tag to remote..."

    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would push tag $version"
        return 0
    fi

    if git push origin "$version"; then
        log_success "Tag pushed to remote: $version"
        audit_git_operation "push_tag" "$version" "success" "Tag pushed to origin"
        return 0
    else
        log_error "Failed to push tag"
        audit_git_operation "push_tag" "$version" "failed" "Push failed"
        return 1
    fi
}

create_rollback_tag() {
    local version="$1"
    local previous_version="$2"

    # Create rollback tag pointing to previous version
    local rollback_tag="${version}-rollback"

    log_info "Creating rollback tag: $rollback_tag"

    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would create rollback tag"
        return 0
    fi

    if [[ -n "$previous_version" ]] && git rev-parse "$previous_version" &>/dev/null; then
        if git tag "$rollback_tag" "$previous_version"; then
            log_success "Rollback tag created: $rollback_tag"
            git push origin "$rollback_tag" 2>/dev/null || true
        fi
    fi
}

# ============================================================
# GITHUB RELEASE
# ============================================================

create_github_release() {
    local version="$1"
    local release_notes="$2"

    log_info "Creating GitHub release..."

    # Check if gh CLI is available
    if ! command -v gh &>/dev/null; then
        log_error "GitHub CLI (gh) not installed"
        log_info "Install from: https://cli.github.com"
        return 1
    fi

    if [[ "$DRY_RUN" == "1" ]]; then
        log_info "DRY RUN: Would create GitHub release"
        echo ""
        echo "--- Release Notes Preview ---"
        echo "$release_notes"
        echo "--- End Preview ---"
        return 0
    fi

    # Prepare flags
    local flags=("--title" "Release $version" "--notes-file" "-")

    # Prerelease flag
    if [[ "$PRERELEASE" == "1" ]] || [[ "$version" =~ -(alpha|beta|rc) ]]; then
        flags+=("--prerelease")
        log_info "Marking as pre-release"
    fi

    # Generate release assets if enabled
    if [[ "$GENERATE_ASSETS" == "1" ]]; then
        generate_release_assets "$version"
    fi

    # Create release
    log_info "Publishing release to GitHub..."
    if echo "$release_notes" | gh release create "$version" "${flags[@]}"; then
        local release_url="https://github.com/$(get_repo_slug)/releases/tag/$version"
        log_success "GitHub release created successfully"
        log_info "Release URL: $release_url"

        audit_git_operation "create_release" "$version" "success" "GitHub release published"
        return 0
    else
        log_error "Failed to create GitHub release"
        audit_git_operation "create_release" "$version" "failed" "Release creation failed"
        return 1
    fi
}

generate_release_assets() {
    local version="$1"

    log_info "Generating release assets..."

    # Create assets directory
    local assets_dir=".claude/release-assets"
    ensure_directory "$assets_dir"

    # Generate VERSION file
    echo "$version" > "${assets_dir}/VERSION"

    # Generate checksums
    if command -v sha256sum &>/dev/null; then
        find . -type f -name "*.sh" -o -name "*.md" | \
            xargs sha256sum > "${assets_dir}/checksums.txt" 2>/dev/null || true
    fi

    log_success "Release assets generated in $assets_dir"
}

# ============================================================
# RELEASE PREREQUISITES
# ============================================================

check_release_prerequisites() {
    local branch="$1"

    log_info "Checking release prerequisites..."

    # Check 1: Must be on main/master branch
    if ! is_main_branch "$branch"; then
        log_error "Must be on main/master branch to create release"
        log_error "Current branch: $branch"
        log_info "Switch to main: git checkout main"
        return 1
    fi

    # Check 2: Working directory must be clean
    if ! git diff-index --quiet HEAD --; then
        log_error "Working directory has uncommitted changes"
        log_info "Commit or stash changes before releasing"
        git status --short
        return 1
    fi

    # Check 3: Up to date with remote
    git fetch origin "$branch" --quiet 2>/dev/null || true
    local behind=$(git rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo "0")
    if [[ "$behind" -gt 0 ]]; then
        log_error "Local branch is behind remote by $behind commit(s)"
        log_info "Pull changes: git pull --rebase"
        return 1
    fi

    # Check 4: CI checks passing (if available)
    if command -v gh &>/dev/null; then
        local commit_sha=$(git rev-parse HEAD)
        local ci_status=$(gh api "repos/:owner/:repo/commits/${commit_sha}/status" \
            --jq '.state' 2>/dev/null || echo "unknown")

        if [[ "$ci_status" == "failure" ]]; then
            log_error "CI checks are failing"
            log_error "Fix CI before creating release"
            return 1
        elif [[ "$ci_status" == "pending" ]]; then
            log_warning "CI checks are still running"
        fi
    fi

    # Check 5: All PRs merged
    if command -v gh &>/dev/null; then
        local open_prs=$(gh pr list --json number --jq 'length' 2>/dev/null || echo "0")
        if [[ "$open_prs" -gt 0 ]]; then
            log_warning "There are $open_prs open pull request(s)"
            log_warning "Consider merging PRs before releasing"
        fi
    fi

    log_success "Release prerequisites check passed"
    return 0
}

# ============================================================
# MAIN RELEASE FLOW
# ============================================================

create_release() {
    local version="$1"
    local bump_type="${2:-auto}"

    log_info "Starting release process..."

    # Audit release attempt
    audit_git_operation "release_attempt" "$version" "started" "Bump: $bump_type"

    # Get current branch
    local branch=$(get_current_branch)

    # Check prerequisites
    check_release_prerequisites "$branch" || return 1

    # Get current version
    local current_version=$(get_current_version)
    log_info "Current version: $current_version"

    # Calculate new version
    if [[ "$version" == "auto" ]]; then
        if [[ "$bump_type" == "auto" ]]; then
            bump_type=$(detect_bump_type_from_commits "$current_version")
            log_info "Auto-detected bump type: $bump_type"
        fi

        version=$(get_next_version "$current_version" "$bump_type")
        log_info "Auto-calculated version: $version"
    else
        # Validate provided version
        validate_version "$version" || return 1
    fi

    # Show release summary
    show_release_summary "$current_version" "$version" "$bump_type"

    # Confirm unless auto-release is enabled
    if [[ "$AUTO_RELEASE" != "1" ]] && [[ "$DRY_RUN" != "1" ]]; then
        echo ""
        read -p "Create release $version? (y/N): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "Release cancelled by user"
            return 0
        fi
    fi

    # Generate release notes
    local release_notes=$(generate_release_notes "$version" "$current_version")

    # Update VERSION file
    if [[ "$DRY_RUN" != "1" ]]; then
        echo "$version" > "$VERSION_FILE"
        log_success "Updated $VERSION_FILE"
    fi

    # Update CHANGELOG.md
    if [[ "$DRY_RUN" != "1" ]]; then
        update_changelog_file "$version" "$release_notes"
    fi

    # Commit version bump
    if [[ "$DRY_RUN" != "1" ]]; then
        git add "$VERSION_FILE" "$CHANGELOG_FILE"
        git commit -m "chore(release): bump version to $version

[skip ci]" || true
        log_success "Committed version bump"
    fi

    # Create git tag
    create_git_tag "$version" "$release_notes" || return 1

    # Push changes and tag
    if [[ "$DRY_RUN" != "1" ]]; then
        git push origin "$branch"
        push_tag "$version" || return 1
    fi

    # Create GitHub release
    create_github_release "$version" "$release_notes" || return 1

    # Create rollback tag
    create_rollback_tag "$version" "$current_version"

    # Audit successful release
    audit_git_operation "release" "$version" "success" "Released $version from $current_version"

    # Show completion message
    show_release_completion "$version")

    return 0
}

show_release_summary() {
    local current_version="$1"
    local new_version="$2"
    local bump_type="$3"

    echo ""
    log_info "╔════════════════════════════════════════╗"
    log_info "║         Release Summary                ║"
    log_info "╠════════════════════════════════════════╣"
    log_info "  Current Version: $current_version"
    log_info "  New Version:     $new_version"
    log_info "  Bump Type:       $bump_type"
    log_info "  Branch:          $(get_current_branch)"
    log_info "╚════════════════════════════════════════╝"
    echo ""
}

show_release_completion() {
    local version="$1"

    echo ""
    log_success "╔════════════════════════════════════════╗"
    log_success "║      Release $version Complete! 🎉       "
    log_success "╚════════════════════════════════════════╝"
    echo ""

    log_info "Next steps:"
    log_info "  1. Announce the release to your team"
    log_info "  2. Update documentation if needed"
    log_info "  3. Monitor for issues"
    log_info "  4. Rollback if needed: git tag ${version}-rollback"
    echo ""

    local release_url="https://github.com/$(get_repo_slug)/releases/tag/$version"
    log_info "Release URL: $release_url"
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

get_repo_slug() {
    local remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")

    if [[ "$remote_url" =~ github\.com[:/]([^/]+/[^/]+?)(\.git)?$ ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "unknown/unknown"
    fi
}

# ============================================================
# MAIN EXECUTION
# ============================================================

main() {
    local version="${1:-auto}"
    local bump_type="${2:-auto}"

    log_info "Auto Release - Claude Enhancer v5.4.0"

    # Check environment
    check_environment || exit 1

    # Create release
    create_release "$version" "$bump_type"
}

# Show help
show_help() {
    cat <<EOF
Usage: $0 [version] [bump_type]

Automated release creation with version tagging and changelog generation.

Arguments:
  version     Version to release (default: auto)
              - "auto" calculates next version automatically
              - Or specify: v1.2.3
  bump_type   How to bump version (default: auto)
              - major: v1.0.0 → v2.0.0
              - minor: v1.0.0 → v1.1.0
              - patch: v1.0.0 → v1.0.1
              - prerelease: v1.0.0 → v1.0.0-rc.1
              - auto: detect from commits

Environment Variables:
  CE_EXECUTION_MODE=1    Enable automation mode
  CE_AUTO_RELEASE=1      Skip confirmation prompt (Tier 5)
  CE_PRERELEASE=1        Mark as pre-release
  CE_GENERATE_ASSETS=1   Generate release assets
  CE_DRY_RUN=1           Dry run mode (preview only)

Examples:
  # Auto-detect version and bump type
  $0

  # Auto-bump with specific type
  $0 auto minor

  # Specific version
  $0 v1.2.3

  # Create pre-release
  CE_PRERELEASE=1 $0 v1.0.0-rc.1

  # Preview release without creating
  CE_DRY_RUN=1 $0

Features:
  ✓ Semantic versioning (semver)
  ✓ Auto-detect bump type from commits
  ✓ Changelog generation
  ✓ GitHub release creation
  ✓ Rollback tag creation
  ✓ Release asset generation
  ✓ CI status validation

Commit-based Bump Detection:
  - BREAKING CHANGE → major bump
  - feat: → minor bump
  - fix: → patch bump

Prerequisites:
  ✓ Must be on main/master branch
  ✓ Working directory must be clean
  ✓ Up-to-date with remote
  ✓ CI checks passing (if available)

Tier: 5 (Critical - Requires confirmation by default)
EOF
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        show_help
        exit 0
    fi

    main "$@"
fi
