#!/usr/bin/env bash
# Rollback Script for Claude Enhancer v5.4.0
# Purpose: Comprehensive automated rollback with multiple strategies
# Used by: P6 deployment, emergency recovery, automated triggers

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../utils/common.sh
source "${SCRIPT_DIR}/../utils/common.sh"

# Configuration
ROLLBACK_TIMEOUT="${CE_ROLLBACK_TIMEOUT:-300}"  # 5 minutes
HEALTH_CHECK_RETRIES="${CE_HEALTH_CHECK_RETRIES:-5}"
HEALTH_CHECK_DELAY="${CE_HEALTH_CHECK_DELAY:-10}"  # seconds
ROLLBACK_STATE_DIR="${CE_ROLLBACK_STATE_DIR:-.workflow/automation/rollback/state}"
ROLLBACK_AUDIT_LOG="${CE_ROLLBACK_AUDIT_LOG:-.workflow/automation/rollback/audit.log}"

# Ensure directories exist
ensure_directory "$ROLLBACK_STATE_DIR"
ensure_directory "$(dirname "$ROLLBACK_AUDIT_LOG")"

# Rollback strategies
readonly STRATEGY_REVERT="revert"        # git revert (non-destructive, recommended)
readonly STRATEGY_RESET="reset"          # git reset --hard (destructive, emergency)
readonly STRATEGY_SELECTIVE="selective"  # selective file rollback
readonly STRATEGY_AUTO="auto"            # auto-detect best strategy

# ============================================================================
# PRE-ROLLBACK VALIDATION
# ============================================================================

validate_rollback_safety() {
    local target_version="$1"
    local strategy="$2"

    log_info "Validating rollback safety..."

    # Check 1: Target version exists
    if ! git rev-parse "$target_version" &>/dev/null; then
        log_error "Target version not found: $target_version"
        return 1
    fi

    # Check 2: Working directory clean (for destructive strategies)
    if [[ "$strategy" == "$STRATEGY_RESET" ]]; then
        if [[ -n "$(git status --porcelain)" ]]; then
            log_error "Working directory has uncommitted changes"
            log_error "Cannot perform destructive rollback with uncommitted changes"
            return 1
        fi
    fi

    # Check 3: Not currently in a merge/rebase
    if git_merge_in_progress; then
        log_error "Git merge/rebase in progress"
        log_error "Please resolve or abort before rolling back"
        return 1
    fi

    # Check 4: Remote connectivity
    if ! git ls-remote origin &>/dev/null; then
        log_warning "Cannot connect to remote repository"
        log_warning "Rollback will be local only"
    fi

    # Check 5: Disk space
    local disk_usage
    disk_usage=$(df -h . | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 95 ]]; then
        log_error "Disk space critically low: ${disk_usage}%"
        return 1
    fi

    log_success "Rollback safety validation passed"
    return 0
}

git_merge_in_progress() {
    [[ -f .git/MERGE_HEAD ]] || [[ -f .git/REBASE_HEAD ]]
}

estimate_rollback_impact() {
    local target_version="$1"
    local current_version="${2:-HEAD}"

    log_info "Estimating rollback impact..."

    local commits_count
    commits_count=$(git rev-list --count "${target_version}..${current_version}" 2>/dev/null || echo "0")

    local files_affected
    files_affected=$(git diff --name-only "${target_version}..${current_version}" 2>/dev/null | wc -l)

    local lines_changed
    lines_changed=$(git diff --shortstat "${target_version}..${current_version}" 2>/dev/null | \
                    grep -oE '[0-9]+ insertions|[0-9]+ deletions' | \
                    grep -oE '[0-9]+' | \
                    awk '{s+=$1} END {print s}')

    local database_migrations
    database_migrations=$(git diff --name-only "${target_version}..${current_version}" | \
                         grep -c "migrations/" || echo "0")

    cat > "${ROLLBACK_STATE_DIR}/impact_estimate.json" <<EOF
{
  "target_version": "$target_version",
  "current_version": "$current_version",
  "commits_to_revert": $commits_count,
  "files_affected": $files_affected,
  "lines_changed": ${lines_changed:-0},
  "database_migrations": $database_migrations,
  "estimated_time_seconds": $((commits_count * 2 + files_affected)),
  "risk_level": "$(calculate_risk_level "$commits_count" "$files_affected" "$database_migrations")",
  "timestamp": "$(date -Iseconds)"
}
EOF

    log_info "Impact estimate saved to: ${ROLLBACK_STATE_DIR}/impact_estimate.json"

    echo "Rollback Impact Summary:"
    echo "  Commits to revert: $commits_count"
    echo "  Files affected: $files_affected"
    echo "  Lines changed: ${lines_changed:-0}"
    echo "  Database migrations: $database_migrations"
    echo "  Estimated time: $((commits_count * 2 + files_affected)) seconds"
    echo "  Risk level: $(calculate_risk_level "$commits_count" "$files_affected" "$database_migrations")"

    return 0
}

calculate_risk_level() {
    local commits="$1"
    local files="$2"
    local migrations="$3"

    if [[ $migrations -gt 0 ]] || [[ $commits -gt 10 ]] || [[ $files -gt 50 ]]; then
        echo "HIGH"
    elif [[ $commits -gt 5 ]] || [[ $files -gt 20 ]]; then
        echo "MEDIUM"
    else
        echo "LOW"
    fi
}

# ============================================================================
# ROLLBACK STRATEGIES
# ============================================================================

perform_revert_rollback() {
    local target_version="$1"
    local reason="$2"

    log_info "Performing git revert rollback (non-destructive)..."

    # Create revert commits for all commits since target
    if git revert --no-commit "${target_version}..HEAD"; then
        git commit -m "chore(rollback): Revert to $target_version

Reason: $reason
Strategy: git revert (non-destructive)
Timestamp: $(date -Iseconds)
Original commits preserved in history

🤖 Generated with Claude Enhancer v5.4.0
Co-Authored-By: Claude <noreply@anthropic.com>"

        log_success "Revert rollback completed"
        return 0
    else
        log_error "Revert failed - conflicts detected"
        git revert --abort 2>/dev/null || true
        return 1
    fi
}

perform_reset_rollback() {
    local target_version="$1"
    local reason="$2"

    log_warning "⚠️  DESTRUCTIVE OPERATION: git reset --hard"
    log_warning "This will permanently lose all commits after $target_version"

    # Create emergency backup tag
    local backup_tag="rollback-emergency-backup-$(date +%Y%m%d-%H%M%S)"
    git tag "$backup_tag" HEAD
    log_info "Created emergency backup tag: $backup_tag"

    # Perform hard reset
    if git reset --hard "$target_version"; then
        log_success "Reset rollback completed"

        # Log to audit
        log_to_audit "RESET_ROLLBACK" "$target_version" "$reason" "$backup_tag"

        return 0
    else
        log_error "Reset rollback failed"
        return 1
    fi
}

perform_selective_rollback() {
    local target_version="$1"
    local files=("${@:2}")

    log_info "Performing selective file rollback..."

    local failed_files=()
    local success_count=0

    for file in "${files[@]}"; do
        if git checkout "$target_version" -- "$file" 2>/dev/null; then
            log_success "Rolled back: $file"
            ((success_count++))
        else
            log_error "Failed to rollback: $file"
            failed_files+=("$file")
        fi
    done

    if [[ ${#failed_files[@]} -eq 0 ]]; then
        # Commit selective rollback
        git commit -m "chore(rollback): Selective rollback to $target_version

Files rolled back: $success_count
$(printf '%s\n' "${files[@]}" | sed 's/^/  - /')

🤖 Generated with Claude Enhancer v5.4.0"

        log_success "Selective rollback completed: $success_count files"
        return 0
    else
        log_error "Selective rollback partially failed"
        log_error "Failed files: ${failed_files[*]}"
        return 1
    fi
}

select_rollback_strategy() {
    local target_version="$1"
    local impact_file="${ROLLBACK_STATE_DIR}/impact_estimate.json"

    if [[ ! -f "$impact_file" ]]; then
        estimate_rollback_impact "$target_version"
    fi

    local risk_level
    risk_level=$(grep -o '"risk_level": "[^"]*"' "$impact_file" | cut -d'"' -f4)

    local migrations_count
    migrations_count=$(grep -o '"database_migrations": [0-9]*' "$impact_file" | grep -oE '[0-9]+')

    # Decision logic
    if [[ "$migrations_count" -gt 0 ]]; then
        # Database migrations require careful handling
        echo "$STRATEGY_REVERT"
    elif [[ "$risk_level" == "HIGH" ]]; then
        # High risk - use safer revert
        echo "$STRATEGY_REVERT"
    else
        # Low/Medium risk - revert is still preferred
        echo "$STRATEGY_REVERT"
    fi
}

# ============================================================================
# POST-ROLLBACK VERIFICATION
# ============================================================================

run_health_checks() {
    local health_script="${1:-observability/probes/healthcheck.sh}"

    if [[ ! -f "$health_script" ]]; then
        log_warning "Health check script not found: $health_script"
        return 0  # Assume healthy if no script
    fi

    log_info "Running health checks..."

    local attempt=1
    while [[ $attempt -le $HEALTH_CHECK_RETRIES ]]; do
        if bash "$health_script" all >/dev/null 2>&1; then
            log_success "Health check passed (attempt $attempt)"
            return 0
        fi

        log_warning "Health check failed (attempt $attempt/$HEALTH_CHECK_RETRIES)"
        if [[ $attempt -lt $HEALTH_CHECK_RETRIES ]]; then
            log_info "Retrying in ${HEALTH_CHECK_DELAY}s..."
            sleep "$HEALTH_CHECK_DELAY"
        fi

        attempt=$((attempt + 1))
    done

    log_error "All health checks failed"
    return 1
}

run_smoke_tests() {
    log_info "Running smoke tests..."

    # Test 1: Git repository integrity
    if ! git fsck --quick &>/dev/null; then
        log_error "Git repository integrity check failed"
        return 1
    fi
    log_success "✓ Git repository integrity OK"

    # Test 2: Core files exist
    local core_files=(
        ".workflow/executor.sh"
        ".workflow/gates.yml"
        ".claude/hooks/branch_helper.sh"
    )

    for file in "${core_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Core file missing: $file"
            return 1
        fi
    done
    log_success "✓ Core files present"

    # Test 3: No syntax errors in shell scripts
    local shell_errors=0
    while IFS= read -r script; do
        if ! bash -n "$script" 2>/dev/null; then
            log_error "Syntax error in: $script"
            ((shell_errors++))
        fi
    done < <(find .workflow -name "*.sh" -type f)

    if [[ $shell_errors -gt 0 ]]; then
        log_error "Found $shell_errors shell script(s) with syntax errors"
        return 1
    fi
    log_success "✓ Shell scripts syntax OK"

    log_success "All smoke tests passed"
    return 0
}

rollback_database_migrations() {
    log_info "Checking for database migrations to rollback..."

    local migrations_dir="migrations"
    if [[ ! -d "$migrations_dir" ]]; then
        log_info "No migrations directory found, skipping"
        return 0
    fi

    # Find rollback scripts
    local rollback_scripts=()
    while IFS= read -r migration; do
        local rollback_file="${migration%.sql}_rollback.sql"
        if [[ -f "$rollback_file" ]]; then
            rollback_scripts+=("$rollback_file")
        fi
    done < <(git diff --name-only HEAD@{1}..HEAD "$migrations_dir" | grep "\.sql$")

    if [[ ${#rollback_scripts[@]} -eq 0 ]]; then
        log_info "No database rollbacks needed"
        return 0
    fi

    log_warning "Found ${#rollback_scripts[@]} database rollback script(s)"
    for script in "${rollback_scripts[@]}"; do
        log_info "  - $script"
    done

    log_warning "⚠️  Database rollbacks require manual execution"
    log_warning "Please run the rollback scripts manually"

    return 0
}

# ============================================================================
# ROLLBACK REPORTING
# ============================================================================

generate_rollback_report() {
    local target_version="$1"
    local strategy="$2"
    local success="$3"
    local duration="$4"
    local reason="${5:-Manual rollback}"

    local report_file="${ROLLBACK_STATE_DIR}/rollback_report_$(date +%Y%m%d_%H%M%S).json"

    local current_commit
    current_commit=$(git rev-parse HEAD)

    local previous_commit
    previous_commit=$(git rev-parse HEAD@{1} 2>/dev/null || echo "unknown")

    cat > "$report_file" <<EOF
{
  "rollback_info": {
    "target_version": "$target_version",
    "strategy": "$strategy",
    "reason": "$reason",
    "success": $success,
    "duration_seconds": $duration
  },
  "git_state": {
    "current_commit": "$current_commit",
    "previous_commit": "$previous_commit",
    "current_branch": "$(get_current_branch)"
  },
  "timestamps": {
    "started_at": "$(date -d "@$(($(date +%s) - duration))" -Iseconds 2>/dev/null || date -Iseconds)",
    "completed_at": "$(date -Iseconds)"
  },
  "health_checks": {
    "passed": $(run_health_checks && echo true || echo false)
  },
  "metadata": {
    "user": "${USER:-unknown}",
    "hostname": "${HOSTNAME:-unknown}",
    "claude_enhancer_version": "5.4.0"
  }
}
EOF

    log_info "Rollback report saved to: $report_file"

    # Display summary
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "              ROLLBACK REPORT SUMMARY"
    echo "═══════════════════════════════════════════════════════════"
    echo "  Target Version:  $target_version"
    echo "  Strategy:        $strategy"
    echo "  Success:         $(if [[ $success == "true" ]]; then echo "✓ YES"; else echo "✗ NO"; fi)"
    echo "  Duration:        ${duration}s"
    echo "  Report:          $report_file"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
}

log_to_audit() {
    local action="$1"
    local target="$2"
    local reason="$3"
    local metadata="${4:-}"

    local audit_entry
    audit_entry=$(cat <<EOF
[$(date -Iseconds)] $action
  Target: $target
  Reason: $reason
  Metadata: $metadata
  User: ${USER:-unknown}
  Branch: $(get_current_branch)
---
EOF
)

    echo "$audit_entry" >> "$ROLLBACK_AUDIT_LOG"
    log_debug "Audit log entry created"
}

# ============================================================================
# MAIN ROLLBACK EXECUTION
# ============================================================================

get_previous_version() {
    # Get the tag before the current one
    local current_version
    current_version=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

    if [[ -z "$current_version" ]]; then
        log_error "No tags found in repository"
        return 1
    fi

    local previous_version
    previous_version=$(git describe --tags --abbrev=0 "${current_version}^" 2>/dev/null || echo "")

    if [[ -z "$previous_version" ]]; then
        log_error "No previous version found before $current_version"
        return 1
    fi

    echo "$previous_version"
}

perform_rollback() {
    local target_version="${1:-auto}"
    local strategy="${2:-$STRATEGY_AUTO}"
    local reason="${3:-Manual rollback}"

    local start_time
    start_time=$(date +%s)

    log_info "========================================="
    log_info "         ROLLBACK INITIATED"
    log_info "========================================="
    log_info "Reason: $reason"
    log_info "Time: $(date)"
    log_info ""

    # Auto-detect target version
    if [[ "$target_version" == "auto" ]]; then
        target_version=$(get_previous_version)
        log_info "Auto-detected target version: $target_version"
    fi

    # Verify target version exists
    if ! git rev-parse "$target_version" &>/dev/null; then
        die "Target version not found: $target_version"
    fi

    # Pre-rollback validation
    if ! validate_rollback_safety "$target_version" "$strategy"; then
        die "Rollback safety validation failed"
    fi

    # Estimate impact
    estimate_rollback_impact "$target_version"

    # Auto-select strategy if needed
    if [[ "$strategy" == "$STRATEGY_AUTO" ]]; then
        strategy=$(select_rollback_strategy "$target_version")
        log_info "Auto-selected strategy: $strategy"
    fi

    # Get current branch
    local current_branch
    current_branch=$(get_current_branch)
    log_info "Current branch: $current_branch"

    # Ensure on main/master for rollback
    if ! is_main_branch "$current_branch"; then
        log_warning "Not on main/master branch"
        log_info "Switching to $(get_default_branch)..."
        git checkout "$(get_default_branch)"
    fi

    # Create backup branch
    local backup_branch="rollback-backup-$(date +%Y%m%d-%H%M%S)"
    log_info "Creating backup branch: $backup_branch"
    git branch "$backup_branch"

    # Execute rollback based on strategy
    local rollback_success=false
    case "$strategy" in
        "$STRATEGY_REVERT")
            if perform_revert_rollback "$target_version" "$reason"; then
                rollback_success=true
            fi
            ;;
        "$STRATEGY_RESET")
            if perform_reset_rollback "$target_version" "$reason"; then
                rollback_success=true
            fi
            ;;
        "$STRATEGY_SELECTIVE")
            log_error "Selective rollback requires file list"
            rollback_success=false
            ;;
        *)
            log_error "Unknown rollback strategy: $strategy"
            rollback_success=false
            ;;
    esac

    if [[ "$rollback_success" != true ]]; then
        log_error "Rollback execution failed"
        log_info "Backup branch available: $backup_branch"

        local end_time
        end_time=$(date +%s)
        generate_rollback_report "$target_version" "$strategy" "false" "$((end_time - start_time))" "$reason"

        return 1
    fi

    # Push rollback (if connected to remote)
    if git ls-remote origin &>/dev/null; then
        log_info "Pushing rollback to remote..."
        if retry_with_backoff 3 5 30 git push origin "$(get_current_branch)"; then
            log_success "Rollback pushed successfully"
        else
            log_error "Failed to push rollback (check network)"
        fi
    fi

    # Wait for system to stabilize
    log_info "Waiting for system to stabilize (30s)..."
    sleep 30

    # Post-rollback verification
    log_info "Running post-rollback verification..."

    local verification_passed=true

    if ! run_health_checks; then
        log_error "Health checks failed after rollback"
        verification_passed=false
    fi

    if ! run_smoke_tests; then
        log_error "Smoke tests failed after rollback"
        verification_passed=false
    fi

    # Check database migrations
    rollback_database_migrations

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Generate report
    generate_rollback_report "$target_version" "$strategy" "$verification_passed" "$duration" "$reason"

    # Log to audit
    log_to_audit "ROLLBACK_COMPLETED" "$target_version" "$reason" "strategy=$strategy,success=$verification_passed,duration=${duration}s"

    if [[ "$verification_passed" == true ]]; then
        log_success ""
        log_success "========================================="
        log_success "    ROLLBACK COMPLETED SUCCESSFULLY"
        log_success "========================================="
        log_success "Target version: $target_version"
        log_success "Strategy: $strategy"
        log_success "Backup branch: $backup_branch"
        log_success "Duration: ${duration}s"
        log_success ""

        return 0
    else
        log_error ""
        log_error "========================================="
        log_error "    ROLLBACK COMPLETED WITH WARNINGS"
        log_error "========================================="
        log_error "Target version: $target_version"
        log_error "Verification: FAILED"
        log_error "Manual intervention may be required"
        log_error "Backup branch available: $backup_branch"
        log_error ""

        return 1
    fi
}

show_rollback_plan() {
    local target_version="${1:-auto}"

    if [[ "$target_version" == "auto" ]]; then
        target_version=$(get_previous_version)
    fi

    local current_version
    current_version=$(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD")

    echo "========================================="
    echo "         ROLLBACK PLAN"
    echo "========================================="
    echo ""
    echo "Current version: $current_version"
    echo "Target version:  $target_version"
    echo ""
    echo "Commits to be reverted:"
    git log --oneline --no-merges "${target_version}..HEAD" | head -20
    echo ""
    echo "Files affected:"
    local files_count
    files_count=$(git diff --name-only "${target_version}..HEAD" | wc -l)
    echo "  Total: $files_count"
    git diff --name-only "${target_version}..HEAD" | head -20
    if [[ $files_count -gt 20 ]]; then
        echo "  ... and $((files_count - 20)) more"
    fi
    echo ""

    # Show recommended strategy
    estimate_rollback_impact "$target_version" >/dev/null 2>&1
    local strategy
    strategy=$(select_rollback_strategy "$target_version")
    echo "Recommended strategy: $strategy"
    echo ""
    echo "========================================="
}

# ============================================================================
# MAIN COMMAND DISPATCHER
# ============================================================================

main() {
    local action="${1:-plan}"
    shift || true

    case "$action" in
        execute)
            local target_version="${1:-auto}"
            local strategy="${2:-auto}"
            local reason="${3:-Manual rollback}"
            perform_rollback "$target_version" "$strategy" "$reason"
            ;;
        plan)
            local target_version="${1:-auto}"
            show_rollback_plan "$target_version"
            ;;
        health)
            run_health_checks "$@"
            ;;
        validate)
            local target_version="${1:-auto}"
            if [[ "$target_version" == "auto" ]]; then
                target_version=$(get_previous_version)
            fi
            validate_rollback_safety "$target_version" "${2:-revert}"
            ;;
        estimate)
            local target_version="${1:-auto}"
            if [[ "$target_version" == "auto" ]]; then
                target_version=$(get_previous_version)
            fi
            estimate_rollback_impact "$target_version"
            ;;
        *)
            cat <<EOF
Usage: $0 {execute|plan|health|validate|estimate} [options]

Actions:
  execute [version] [strategy] [reason]  - Perform rollback
    Strategies: revert (default), reset (destructive), auto

  plan [version]                         - Show rollback plan

  health [script]                        - Check system health

  validate [version] [strategy]          - Validate rollback safety

  estimate [version]                     - Estimate rollback impact

Examples:
  $0 plan                                           # Show plan for auto-rollback
  $0 plan v5.3.5                                   # Show plan for specific version
  $0 execute                                        # Execute auto-rollback with revert
  $0 execute v5.3.5 revert "Critical bug found"    # Rollback to specific version
  $0 execute auto reset "Emergency recovery"        # Destructive rollback
  $0 validate v5.3.5                               # Validate rollback to v5.3.5
  $0 estimate v5.3.5                               # Estimate impact

Exit codes:
  0 = Success
  1 = Failure

Rollback Strategies:
  revert     - Non-destructive, creates new commits (recommended)
  reset      - Destructive, hard reset (emergency only, requires clean working dir)
  selective  - Rollback specific files only
  auto       - Automatically select best strategy

Environment Variables:
  CE_ROLLBACK_TIMEOUT=300           # Rollback timeout in seconds
  CE_HEALTH_CHECK_RETRIES=5         # Number of health check retries
  CE_HEALTH_CHECK_DELAY=10          # Delay between retries
  CE_ROLLBACK_STATE_DIR=...         # State directory
  CE_ROLLBACK_AUDIT_LOG=...         # Audit log file

For more information, see: docs/ROLLBACK_GUIDE.md
EOF
            exit 1
            ;;
    esac
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
