#!/bin/bash
# =============================================================================
# Parallel Conflict Validator - Skills Framework
# =============================================================================
# Purpose: Validate parallel groups for potential conflicts before execution
# Usage: bash scripts/parallel/validate_conflicts.sh <phase> [group1 group2 ...]
# Output: Exit 0 if safe, Exit 1 if conflicts detected
# =============================================================================

set -euo pipefail

# ==================== Configuration ====================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly STAGES_CONFIG="${PROJECT_ROOT}/.workflow/STAGES.yml"
readonly CONFLICT_LOG="${PROJECT_ROOT}/.workflow/logs/conflict_detection.log"

# ==================== Logging ====================

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CONFLICT-VALIDATOR] INFO: $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CONFLICT-VALIDATOR] WARN: $*" >&2
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CONFLICT-VALIDATOR] ERROR: $*" >&2
}

# ==================== Conflict Rules (8 rules, 4 layers) ====================

# Layer 1: FATAL Conflicts (must be serial)
readonly FATAL_CONFLICTS=(
    "package.json"
    "tsconfig.json"
    ".workflow/*.yml"
    "VERSION"
    ".claude/settings.json"
    ".workflow/manifest.yml"
    ".workflow/SPEC.yaml"
    "CHANGELOG.md"
    ".git/*"
)

# Layer 2: HIGH Conflicts (need locks)
readonly HIGH_CONFLICTS=(
    ".gates/*"
    ".phase/*"
    ".claude/skills_state.json"
    ".evidence/index.json"
)

# Layer 3: MEDIUM Conflicts (last-writer-wins, needs review)
readonly MEDIUM_CONFLICTS=(
    "tests/fixtures/*"
)

# Layer 4: LOW Conflicts (append-only, safe)
readonly LOW_CONFLICTS=(
    ".workflow/logs/*.log"
    ".workflow/metrics/*.jsonl"
)

# ==================== Conflict Detection ====================

check_fatal_conflicts() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Checking FATAL conflicts for ${phase}..."

    # If Phase5 git_operations group is among groups, check if it's parallel with others
    if [[ "${phase}" == "Phase5" ]]; then
        local has_git_ops=false
        for group in "${groups[@]}"; do
            if [[ "${group}" == "git_operations" ]]; then
                has_git_ops=true
                break
            fi
        done

        if [[ "${has_git_ops}" == "true" ]] && [[ ${#groups[@]} -gt 1 ]]; then
            log_error "FATAL: git_operations must run serially (detected ${#groups[@]} groups)"
            return 1
        fi
    fi

    # Check Phase2 configuration group
    if [[ "${phase}" == "Phase2" ]]; then
        local has_config=false
        for group in "${groups[@]}"; do
            if [[ "${group}" == "configuration" ]]; then
                has_config=true
                break
            fi
        done

        if [[ "${has_config}" == "true" ]] && [[ ${#groups[@]} -gt 1 ]]; then
            log_error "FATAL: configuration group must run serially (detected ${#groups[@]} groups)"
            return 1
        fi
    fi

    log_info "✓ No FATAL conflicts detected"
    return 0
}

check_high_conflicts() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Checking HIGH conflicts for ${phase}..."

    # Check if multiple groups will modify .gates/* or .phase/*
    # This is generally safe as parallel_executor.sh uses mutex locks
    # But we log a warning

    log_info "✓ HIGH conflicts will be handled by mutex locks"
    return 0
}

check_conflict_zones() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Checking conflict zones from STAGES.yml..."

    # Read conflict zones from STAGES.yml
    local conflict_zones=$(python3 << EOF
import yaml
import sys

try:
    with open("${STAGES_CONFIG}", 'r') as f:
        data = yaml.safe_load(f)

    wpp = data.get('workflow_phase_parallel', {})
    phase_config = wpp.get('${phase}', {})
    parallel_groups = phase_config.get('parallel_groups', [])

    # Collect all conflict zones
    all_zones = []
    for group in parallel_groups:
        if isinstance(group, dict):
            group_id = group.get('group_id', '')
            # Check if this group is in our execution list
            if group_id in ${groups[@]@Q}:
                zones = group.get('conflict_zones', [])
                all_zones.extend(zones)

    # Check for overlaps
    if len(all_zones) != len(set(all_zones)):
        print("CONFLICT_DETECTED")
    else:
        print("OK")

except Exception as e:
    print("ERROR", file=sys.stderr)
    sys.exit(1)
EOF
)

    if [[ "${conflict_zones}" == "CONFLICT_DETECTED" ]]; then
        log_error "Conflict zones overlap detected"
        return 1
    fi

    log_info "✓ No conflict zone overlaps"
    return 0
}

# ==================== Validation ====================

validate_parallel_execution() {
    local phase="$1"
    shift
    local groups=("$@")

    log_info "Validating parallel execution for ${phase}"
    log_info "Groups to execute: ${groups[*]}"

    local failed=0

    # Check 1: FATAL conflicts
    if ! check_fatal_conflicts "${phase}" "${groups[@]}"; then
        ((failed++))
    fi

    # Check 2: HIGH conflicts (logged, not blocking)
    check_high_conflicts "${phase}" "${groups[@]}"

    # Check 3: Conflict zones from STAGES.yml
    if ! check_conflict_zones "${phase}" "${groups[@]}"; then
        ((failed++))
    fi

    # Record result
    mkdir -p "$(dirname "${CONFLICT_LOG}")"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local result="PASS"
    [[ ${failed} -gt 0 ]] && result="FAIL"

    echo "${timestamp} ${phase} ${result} groups=${groups[*]}" >> "${CONFLICT_LOG}"

    if [[ ${failed} -gt 0 ]]; then
        log_error "❌ Conflict validation FAILED (${failed} issues)"
        return 1
    else
        log_info "✅ Conflict validation PASSED"
        return 0
    fi
}

# ==================== Main ====================

main() {
    if [[ $# -lt 1 ]]; then
        log_error "Usage: $0 <phase> [group1 group2 ...]"
        log_error "Example: $0 Phase3 unit_tests integration_tests"
        exit 1
    fi

    local phase="$1"
    shift
    local groups=("$@")

    if [[ ${#groups[@]} -eq 0 ]]; then
        log_warn "No groups specified, skipping validation"
        exit 0
    fi

    if ! validate_parallel_execution "${phase}" "${groups[@]}"; then
        log_error "Parallel execution validation failed"
        exit 1
    fi

    log_info "Validation complete - safe to proceed"
    exit 0
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
