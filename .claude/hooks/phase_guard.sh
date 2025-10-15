#!/bin/bash
# Claude Enhancer v2.0 - Phase Guard
# Purpose: Phase transition validation and prerequisite checking
# Version: 2.0.0

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly WORKFLOW_DIR="${PROJECT_ROOT}/.workflow"
readonly PHASE_DIR="${PROJECT_ROOT}/.phase"
readonly LOG_DIR="${PROJECT_ROOT}/.claude/logs"

# Create necessary directories
mkdir -p "${LOG_DIR}" "${PHASE_DIR}"

# Log configuration
readonly PHASE_GUARD_LOG="${LOG_DIR}/phase_guard.log"
readonly DEBUG_MODE="${DEBUG_PHASE_GUARD:-0}"

# Color output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# ============================================================
# Logging Functions
# ============================================================
log_debug() {
    if [[ "${DEBUG_MODE}" == "1" ]]; then
        echo "[DEBUG] $*" | tee -a "${PHASE_GUARD_LOG}" >&2
    fi
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "${PHASE_GUARD_LOG}" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "${PHASE_GUARD_LOG}" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${PHASE_GUARD_LOG}" >&2
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*" | tee -a "${PHASE_GUARD_LOG}" >&2
}

# ============================================================
# Phase State Management
# ============================================================
get_current_phase() {
    if [[ -f "${WORKFLOW_DIR}/current" ]]; then
        cat "${WORKFLOW_DIR}/current" | tr -d '[:space:]'
    elif [[ -f "${PHASE_DIR}/current" ]]; then
        cat "${PHASE_DIR}/current" | tr -d '[:space:]'
    else
        echo ""
    fi
}

set_current_phase() {
    local phase="$1"
    echo "$phase" > "${WORKFLOW_DIR}/current"
    echo "$phase" > "${PHASE_DIR}/current"
    log_info "Phase set to: ${phase}"
}

# ============================================================
# Phase Transition Validation
# ============================================================
# Valid transitions: Phase0→Phase1→Phase2→Phase3→Phase4→Phase5
# Also allow: Any→Phase0 (restart workflow)
is_valid_transition() {
    local from_phase="$1"
    local to_phase="$2"

    log_debug "Checking transition: ${from_phase} → ${to_phase}"

    # Empty from_phase means starting workflow
    if [[ -z "$from_phase" ]]; then
        if [[ "$to_phase" == "Phase0" ]] || [[ "$to_phase" == "Phase1" ]]; then
            return 0
        else
            log_error "Workflow must start with Phase0 or Phase1"
            return 1
        fi
    fi

    # Allow restart to Phase0
    if [[ "$to_phase" == "Phase0" ]]; then
        log_info "Restarting workflow from Phase0"
        return 0
    fi

    # Extract phase numbers (support both Phase0-5 and old Phase0-7 format)
    local from_num=""
    local to_num=""

    if [[ "$from_phase" =~ ^Phase([0-5])$ ]]; then
        from_num="${BASH_REMATCH[1]}"
    elif [[ "$from_phase" =~ ^P([0-7])$ ]]; then
        # Legacy format compatibility
        from_num="${BASH_REMATCH[1]}"
    fi

    if [[ "$to_phase" =~ ^Phase([0-5])$ ]]; then
        to_num="${BASH_REMATCH[1]}"
    elif [[ "$to_phase" =~ ^P([0-7])$ ]]; then
        # Legacy format compatibility
        to_num="${BASH_REMATCH[1]}"
    fi

    # Validate phase numbers
    if ! [[ "$from_num" =~ ^[0-5]$ ]] || ! [[ "$to_num" =~ ^[0-5]$ ]]; then
        log_error "Invalid phase numbers: ${from_phase} → ${to_phase}"
        return 1
    fi

    # Allow same phase (re-execution)
    if [[ "$from_num" -eq "$to_num" ]]; then
        log_warn "Re-executing current phase: ${to_phase}"
        return 0
    fi

    # Allow forward by 1
    if [[ "$to_num" -eq $((from_num + 1)) ]]; then
        log_success "Valid forward transition: ${from_phase} → ${to_phase}"
        return 0
    fi

    # Allow backward movement (for fixes/refinement)
    if [[ "$to_num" -lt "$from_num" ]]; then
        log_warn "Backward transition: ${from_phase} → ${to_phase}"
        log_warn "  Reason: Fixing issues or refining earlier phases"
        return 0
    fi

    # Invalid: Jumping forward
    if [[ "$to_num" -gt $((from_num + 1)) ]]; then
        log_error "Invalid transition: ${from_phase} → ${to_phase}"
        log_error "  Attempting to skip phases P$((from_num + 1)) to P$((to_num - 1))"
        log_error "  Must follow sequential workflow"
        return 1
    fi

    return 1
}

# ============================================================
# Phase Prerequisites Check
# ============================================================
check_phase_prerequisites() {
    local phase="$1"

    log_debug "Checking prerequisites for ${phase}"

    case "$phase" in
        Phase0)
            # Phase0: Discovery - No prerequisites
            log_debug "Phase0: No prerequisites"
            return 0
            ;;
        Phase1)
            # Phase1: Planning - Should have discovery results
            log_debug "Phase1: Checking for Phase0 completion markers"
            # Flexible: Allow Phase1 without Phase0
            return 0
            ;;
        Phase2)
            # Phase2: Skeleton - Should have PLAN.md
            if [[ ! -f "${PROJECT_ROOT}/docs/PLAN.md" ]] && [[ ! -f "${PROJECT_ROOT}/PLAN.md" ]]; then
                log_warn "Phase2: PLAN.md not found"
                log_warn "  Suggestion: Generate PLAN.md in Phase1 phase"
                # Warning only, not blocking
            fi
            return 0
            ;;
        Phase3)
            # Phase3: Implementation - Should have architecture
            log_debug "Phase3: Checking for architecture artifacts"
            # Check for common architecture files
            if [[ ! -f "${PROJECT_ROOT}/docs/ARCHITECTURE.md" ]] && \
               [[ ! -f "${PROJECT_ROOT}/ARCHITECTURE.md" ]] && \
               [[ ! -d "${PROJECT_ROOT}/src" ]] && \
               [[ ! -d "${PROJECT_ROOT}/lib" ]]; then
                log_warn "Phase3: No architecture or code structure found"
                log_warn "  Suggestion: Complete Phase2 (Skeleton) first"
            fi
            return 0
            ;;
        Phase4)
            # Phase4: Testing - Should have implementation
            log_debug "Phase4: Checking for implementation artifacts"
            if [[ ! -d "${PROJECT_ROOT}/src" ]] && \
               [[ ! -d "${PROJECT_ROOT}/lib" ]] && \
               [[ ! -d "${PROJECT_ROOT}/app" ]]; then
                log_warn "Phase4: No implementation directory found"
                log_warn "  Suggestion: Complete Phase3 (Implementation) first"
            fi
            return 0
            ;;
        Phase5)
            # Phase5: Release & Monitor - Should have review and tests
            log_debug "Phase5: Checking for Phase4 completion"
            if [[ ! -f "${PROJECT_ROOT}/docs/REVIEW.md" ]] && [[ ! -f "${PROJECT_ROOT}/REVIEW.md" ]]; then
                log_warn "Phase5: REVIEW.md not found"
                log_warn "  Suggestion: Generate REVIEW.md in Phase4 phase"
            fi
            if [[ ! -d "${PROJECT_ROOT}/test" ]] && \
               [[ ! -d "${PROJECT_ROOT}/tests" ]] && \
               [[ ! -d "${PROJECT_ROOT}/__tests__" ]]; then
                log_warn "Phase5: No test directory found"
                log_warn "  Suggestion: Complete Phase3 (Testing) first"
            fi
            return 0
            ;;
        *)
            log_error "Unknown phase: ${phase}"
            return 1
            ;;
    esac
}

# ============================================================
# Phase Output Verification
# ============================================================
verify_phase_outputs() {
    local phase="$1"

    log_debug "Verifying outputs for ${phase}"

    case "$phase" in
        Phase0)
            # Phase0: Should have discovery notes or prototype
            log_debug "Phase0: Checking for discovery artifacts"
            # Flexible: Not strictly required
            return 0
            ;;
        Phase1)
            # Phase1: Should have PLAN.md
            if [[ ! -f "${PROJECT_ROOT}/docs/PLAN.md" ]] && [[ ! -f "${PROJECT_ROOT}/PLAN.md" ]]; then
                log_error "Phase1: PLAN.md not generated"
                log_error "  Required output: PLAN.md with requirements and design"
                return 1
            fi
            log_success "Phase1: PLAN.md found"
            return 0
            ;;
        Phase2)
            # Phase2: Should have directory structure
            if [[ ! -d "${PROJECT_ROOT}/src" ]] && \
               [[ ! -d "${PROJECT_ROOT}/lib" ]] && \
               [[ ! -d "${PROJECT_ROOT}/app" ]]; then
                log_error "Phase2: No code structure created"
                log_error "  Required output: Basic directory structure (src/, lib/, or app/)"
                return 1
            fi
            log_success "Phase2: Code structure found"
            return 0
            ;;
        Phase3)
            # Phase3: Should have committed code
            if ! git log --oneline -1 >/dev/null 2>&1; then
                log_warn "Phase3: No git commits found"
                log_warn "  Suggestion: Commit your implementation"
                return 0  # Warning only
            fi
            log_success "Phase3: Implementation committed"
            return 0
            ;;
        Phase4)
            # Phase4: Should have test files
            local test_files=$(find "${PROJECT_ROOT}" -type f \( -name "*test*" -o -name "*spec*" \) 2>/dev/null | wc -l)
            if [[ $test_files -eq 0 ]]; then
                log_error "Phase4: No test files found"
                log_error "  Required output: Test files (*test*, *spec*)"
                return 1
            fi
            log_success "Phase4: ${test_files} test file(s) found"
            return 0
            ;;
        Phase5)
            # Phase5: Should have REVIEW.md and release artifacts
            if [[ ! -f "${PROJECT_ROOT}/docs/REVIEW.md" ]] && [[ ! -f "${PROJECT_ROOT}/REVIEW.md" ]]; then
                log_error "Phase5: REVIEW.md not generated"
                log_error "  Required output: REVIEW.md with code review findings"
                return 1
            fi
            log_success "Phase5: REVIEW.md found"
            if [[ ! -f "${PROJECT_ROOT}/docs/CHANGELOG.md" ]] && [[ ! -f "${PROJECT_ROOT}/CHANGELOG.md" ]]; then
                log_warn "Phase5: CHANGELOG.md not updated"
            fi
            return 0
            ;;
        *)
            log_error "Unknown phase: ${phase}"
            return 1
            ;;
    esac
}

# ============================================================
# Main Guard Function
# ============================================================
guard_phase_transition() {
    local target_phase="$1"
    local current_phase
    current_phase=$(get_current_phase)

    log_info "========================================"
    log_info "Phase Guard - Transition Validation"
    log_info "========================================"
    echo ""

    log_info "Current Phase: ${current_phase:-None}"
    log_info "Target Phase: ${target_phase}"
    echo ""

    # Validate transition
    log_info "[1/3] Validating phase transition..."
    if ! is_valid_transition "$current_phase" "$target_phase"; then
        log_error "❌ Invalid phase transition"
        return 1
    fi
    log_success "Transition valid"
    echo ""

    # Check prerequisites
    log_info "[2/3] Checking phase prerequisites..."
    if ! check_phase_prerequisites "$target_phase"; then
        log_error "❌ Prerequisites not met"
        return 1
    fi
    log_success "Prerequisites met"
    echo ""

    # Verify current phase outputs (if transitioning forward)
    if [[ -n "$current_phase" ]] && [[ "$target_phase" != "$current_phase" ]]; then
        local current_num="${current_phase#P}"
        local target_num="${target_phase#P}"

        if [[ "$target_num" -gt "$current_num" ]]; then
            log_info "[3/3] Verifying current phase outputs..."
            if ! verify_phase_outputs "$current_phase"; then
                log_error "❌ Current phase outputs incomplete"
                log_error "  Complete ${current_phase} before moving to ${target_phase}"
                return 1
            fi
            log_success "Current phase outputs verified"
        else
            log_info "[3/3] Backward transition - skipping output verification"
        fi
    else
        log_info "[3/3] Initial phase - skipping output verification"
    fi

    echo ""
    log_info "========================================"
    log_success "✅ Phase guard passed - Transition allowed"
    log_info "========================================"

    # Update phase state
    set_current_phase "$target_phase"

    return 0
}

# ============================================================
# Main Entry
# ============================================================
show_help() {
    cat << 'EOF'
Claude Enhancer v2.0 - Phase Guard

Usage:
  phase_guard.sh <target_phase>
  phase_guard.sh --current
  phase_guard.sh --help

Options:
  --current       Show current phase
  --help          Show help information
  --debug         Enable debug mode

Environment Variables:
  DEBUG_PHASE_GUARD=1    Enable debug output

Examples:
  phase_guard.sh Phase1     # Transition to Phase1
  phase_guard.sh Phase3     # Transition to Phase3
  phase_guard.sh --current

Phase Transition Rules:
  - Sequential: Phase0→Phase1→Phase2→Phase3→Phase4→Phase5
  - Allow restart: Any→Phase0
  - Allow backward: For fixes/refinement
  - Block jumping: Cannot skip phases

Phase Prerequisites:
  Phase0: None (Discovery)
  Phase1: None (Planning & Architecture)
  Phase2: PLAN.md recommended (Implementation)
  Phase3: Architecture/structure from Phase1 (Testing)
  Phase4: Implementation from Phase2 (Review)
  Phase5: Tests from Phase3, Review from Phase4 (Release & Monitor)

EOF
}

main() {
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --current)
            local current_phase
            current_phase=$(get_current_phase)
            if [[ -n "$current_phase" ]]; then
                echo "Current Phase: $current_phase"
            else
                echo "No phase set (Workflow not started)"
            fi
            exit 0
            ;;
        --debug)
            export DEBUG_PHASE_GUARD=1
            shift
            ;;
        "")
            log_error "Error: Missing target phase parameter"
            echo ""
            show_help
            exit 1
            ;;
        Phase[0-5])
            # Valid phase
            ;;
        *)
            log_error "Error: Invalid phase '${1}'"
            log_error "  Valid phases: Phase0, Phase1, Phase2, Phase3, Phase4, Phase5"
            exit 1
            ;;
    esac

    local target_phase="$1"

    # Execute guard
    if guard_phase_transition "$target_phase"; then
        exit 0
    else
        exit 1
    fi
}

# Execute main function
main "$@"
