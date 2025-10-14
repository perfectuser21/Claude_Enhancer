#!/bin/bash
# Claude Enhancer v2.0 - Comprehensive Guard
# Purpose: Unified guard orchestrating all individual guards
# Version: 2.0.0

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly LOG_DIR="${PROJECT_ROOT}/.claude/logs"

# Create necessary directories
mkdir -p "${LOG_DIR}"

# Log configuration
readonly COMPREHENSIVE_LOG="${LOG_DIR}/comprehensive_guard.log"
readonly DEBUG_MODE="${DEBUG_COMPREHENSIVE_GUARD:-0}"

# Color output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Performance target
readonly MAX_EXECUTION_TIME=2

# Individual guards
readonly WORKFLOW_GUARD="${SCRIPT_DIR}/workflow_guard.sh"
readonly PHASE_GUARD="${SCRIPT_DIR}/phase_guard.sh"
readonly BRANCH_HELPER="${SCRIPT_DIR}/branch_helper.sh"

# ============================================================
# Logging Functions
# ============================================================
log_debug() {
    if [[ "${DEBUG_MODE}" == "1" ]]; then
        echo "[DEBUG] $*" | tee -a "${COMPREHENSIVE_LOG}" >&2
    fi
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "${COMPREHENSIVE_LOG}" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "${COMPREHENSIVE_LOG}" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${COMPREHENSIVE_LOG}" >&2
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*" | tee -a "${COMPREHENSIVE_LOG}" >&2
}

log_section() {
    echo -e "${CYAN}[SECTION]${NC} $*" | tee -a "${COMPREHENSIVE_LOG}" >&2
}

# ============================================================
# Guard Execution Functions
# ============================================================

run_branch_guard() {
    log_section "Running Branch Guard..."
    echo ""

    # Branch helper runs in execution mode detection
    # It checks if on protected branch and blocks modifications
    if [[ -x "$BRANCH_HELPER" ]]; then
        # Set execution mode indicator
        export CE_EXECUTION_MODE=true

        if "$BRANCH_HELPER" 2>&1 | tee -a "${COMPREHENSIVE_LOG}"; then
            log_success "Branch guard passed"
            return 0
        else
            log_error "Branch guard failed"
            return 1
        fi
    else
        log_warn "Branch helper not found or not executable: ${BRANCH_HELPER}"
        return 0  # Don't block if guard missing
    fi
}

run_workflow_guard() {
    local input="$1"

    log_section "Running Workflow Guard..."
    echo ""

    if [[ -x "$WORKFLOW_GUARD" ]]; then
        if "$WORKFLOW_GUARD" "$input" 2>&1 | tee -a "${COMPREHENSIVE_LOG}"; then
            log_success "Workflow guard passed"
            return 0
        else
            log_error "Workflow guard failed"
            return 1
        fi
    else
        log_warn "Workflow guard not found or not executable: ${WORKFLOW_GUARD}"
        return 0  # Don't block if guard missing
    fi
}

run_phase_guard() {
    local target_phase="$1"

    log_section "Running Phase Guard..."
    echo ""

    if [[ -x "$PHASE_GUARD" ]]; then
        if "$PHASE_GUARD" "$target_phase" 2>&1 | tee -a "${COMPREHENSIVE_LOG}"; then
            log_success "Phase guard passed"
            return 0
        else
            log_error "Phase guard failed"
            return 1
        fi
    else
        log_warn "Phase guard not found or not executable: ${PHASE_GUARD}"
        return 0  # Don't block if guard missing
    fi
}

# ============================================================
# Comprehensive Validation
# ============================================================

comprehensive_validation() {
    local input="$1"
    local target_phase="${2:-}"
    local failures=0
    local start_time=$(date +%s%N)

    log_info "╔════════════════════════════════════════════════════════╗"
    log_info "║   Claude Enhancer v2.0 - Comprehensive Guard         ║"
    log_info "║   Multi-Layer Validation System                       ║"
    log_info "╚════════════════════════════════════════════════════════╝"
    echo ""

    log_info "Input: ${input}"
    if [[ -n "$target_phase" ]]; then
        log_info "Target Phase: ${target_phase}"
    fi
    echo ""
    log_info "Starting validation sequence..."
    echo ""

    # Guard 1: Branch Guard
    log_info "[1/3] Branch Protection Check"
    log_info "────────────────────────────────────────────────────────"
    if ! run_branch_guard; then
        ((failures++))
        log_error "✗ Branch guard failed"
    else
        log_success "✓ Branch guard passed"
    fi
    echo ""

    # Guard 2: Workflow Guard (5-layer detection)
    log_info "[2/3] Workflow Enforcement Check"
    log_info "────────────────────────────────────────────────────────"
    if ! run_workflow_guard "$input"; then
        ((failures++))
        log_error "✗ Workflow guard failed"
    else
        log_success "✓ Workflow guard passed"
    fi
    echo ""

    # Guard 3: Phase Guard (if target phase specified)
    if [[ -n "$target_phase" ]]; then
        log_info "[3/3] Phase Transition Check"
        log_info "────────────────────────────────────────────────────────"
        if ! run_phase_guard "$target_phase"; then
            ((failures++))
            log_error "✗ Phase guard failed"
        else
            log_success "✓ Phase guard passed"
        fi
        echo ""
    else
        log_info "[3/3] Phase Transition Check - Skipped (no target phase)"
        echo ""
    fi

    # Performance measurement
    local end_time=$(date +%s%N)
    local duration_ns=$((end_time - start_time))
    local duration_s=$((duration_ns / 1000000000))
    local duration_ms=$(((duration_ns % 1000000000) / 1000000))

    # Summary
    log_info "╔════════════════════════════════════════════════════════╗"
    log_info "║   Validation Summary                                  ║"
    log_info "╚════════════════════════════════════════════════════════╝"
    echo ""

    if [[ $failures -eq 0 ]]; then
        log_success "Result: ALL GUARDS PASSED ✓"
        log_success "Status: OPERATION ALLOWED"
    else
        log_error "Result: ${failures} GUARD(S) FAILED ✗"
        log_error "Status: OPERATION BLOCKED"
    fi

    echo ""
    log_info "Execution time: ${duration_s}.${duration_ms}s"

    if [[ $duration_s -ge $MAX_EXECUTION_TIME ]]; then
        log_warn "Performance warning: Exceeded ${MAX_EXECUTION_TIME}s target"
    else
        log_success "Performance: Within ${MAX_EXECUTION_TIME}s target"
    fi

    echo ""
    log_info "════════════════════════════════════════════════════════"

    # Write comprehensive log
    {
        echo "=========================================="
        echo "Comprehensive Guard Report"
        echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Input: ${input}"
        echo "Target Phase: ${target_phase:-N/A}"
        echo "Failures: ${failures}"
        echo "Duration: ${duration_s}.${duration_ms}s"
        echo "Result: $(if [[ $failures -eq 0 ]]; then echo "PASS"; else echo "FAIL"; fi)"
        echo "=========================================="
    } >> "${LOG_DIR}/comprehensive_guard_history.log"

    # Return result
    if [[ $failures -eq 0 ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================================
# Quick Check Mode
# ============================================================

quick_check() {
    local check_type="$1"

    case "$check_type" in
        branch)
            run_branch_guard
            ;;
        workflow)
            log_error "Quick workflow check requires input text"
            return 1
            ;;
        phase)
            log_error "Quick phase check requires target phase"
            return 1
            ;;
        *)
            log_error "Unknown check type: ${check_type}"
            log_error "  Valid types: branch, workflow, phase"
            return 1
            ;;
    esac
}

# ============================================================
# Status Report
# ============================================================

show_status() {
    log_info "╔════════════════════════════════════════════════════════╗"
    log_info "║   Claude Enhancer Guard Status                        ║"
    log_info "╚════════════════════════════════════════════════════════╝"
    echo ""

    # Check guards availability
    log_info "Guard Availability:"
    echo ""

    if [[ -x "$BRANCH_HELPER" ]]; then
        log_success "  ✓ Branch Helper: Available"
    else
        log_warn "  ✗ Branch Helper: Missing or not executable"
    fi

    if [[ -x "$WORKFLOW_GUARD" ]]; then
        log_success "  ✓ Workflow Guard: Available"
    else
        log_warn "  ✗ Workflow Guard: Missing or not executable"
    fi

    if [[ -x "$PHASE_GUARD" ]]; then
        log_success "  ✓ Phase Guard: Available"
    else
        log_warn "  ✗ Phase Guard: Missing or not executable"
    fi

    echo ""

    # Check workflow state
    log_info "Workflow State:"
    echo ""

    if [[ -f "${PROJECT_ROOT}/.workflow/ACTIVE" ]]; then
        log_success "  ✓ Workflow: Active"
    else
        log_info "  ○ Workflow: Inactive (Discussion mode)"
    fi

    if [[ -f "${PROJECT_ROOT}/.workflow/current" ]]; then
        local current_phase
        current_phase=$(cat "${PROJECT_ROOT}/.workflow/current" | tr -d '[:space:]')
        log_info "  ○ Current Phase: ${current_phase}"
    else
        log_info "  ○ Current Phase: None"
    fi

    echo ""

    # Check git state
    log_info "Git State:"
    echo ""

    if git rev-parse --git-dir > /dev/null 2>&1; then
        local current_branch
        current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")

        if [[ "$current_branch" =~ ^(main|master|production|release)$ ]]; then
            log_warn "  ⚠ Branch: ${current_branch} (Protected)"
        else
            log_success "  ✓ Branch: ${current_branch} (Feature branch)"
        fi
    else
        log_info "  ○ Not a git repository"
    fi

    echo ""
    log_info "════════════════════════════════════════════════════════"
}

# ============================================================
# Main Entry
# ============================================================

show_help() {
    cat << 'EOF'
Claude Enhancer v2.0 - Comprehensive Guard

Usage:
  comprehensive_guard.sh <input_text> [target_phase]
  comprehensive_guard.sh --quick <check_type>
  comprehensive_guard.sh --status
  comprehensive_guard.sh --help

Options:
  --quick <type>  Run single guard (branch|workflow|phase)
  --status        Show guard system status
  --help          Show help information
  --debug         Enable debug mode

Environment Variables:
  DEBUG_COMPREHENSIVE_GUARD=1    Enable debug output

Examples:
  # Full validation
  comprehensive_guard.sh "Implement login feature in P3" "P3"

  # Quick checks
  comprehensive_guard.sh --quick branch
  comprehensive_guard.sh --status

  # Debug mode
  DEBUG_COMPREHENSIVE_GUARD=1 comprehensive_guard.sh "test" "P1"

Guard System:
  1. Branch Guard      - Protect main/master branches
  2. Workflow Guard    - 5-layer workflow enforcement
  3. Phase Guard       - Phase transition validation

Performance Target:
  - Total execution: <2s
  - All guards run in parallel when possible

EOF
}

main() {
    # Parse arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --status)
            show_status
            exit 0
            ;;
        --quick)
            if [[ -z "${2:-}" ]]; then
                log_error "Error: --quick requires check type"
                echo ""
                show_help
                exit 1
            fi
            quick_check "$2"
            exit $?
            ;;
        --debug)
            export DEBUG_COMPREHENSIVE_GUARD=1
            shift
            ;;
        "")
            log_error "Error: Missing input parameter"
            echo ""
            show_help
            exit 1
            ;;
    esac

    local input_text="$1"
    local target_phase="${2:-}"

    # Execute comprehensive validation
    if comprehensive_validation "$input_text" "$target_phase"; then
        exit 0
    else
        exit 1
    fi
}

# Execute main function
main "$@"
