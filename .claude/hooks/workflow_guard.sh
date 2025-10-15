#!/bin/bash
# Claude Enhancer v2.0 - Workflow Guard (Primary Enforcement)
# Adapted from core/hooks/enforcer_v2.sh with 5-layer detection
# Version: 2.0.0
# Purpose: Primary workflow enforcement with comprehensive detection

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly WORKFLOW_DIR="${PROJECT_ROOT}/.workflow"
readonly LOG_DIR="${PROJECT_ROOT}/.claude/logs"

# Create necessary directories
mkdir -p "${LOG_DIR}"

# Log configuration
readonly WORKFLOW_GUARD_LOG="${LOG_DIR}/workflow_guard.log"
readonly DEBUG_MODE="${DEBUG_WORKFLOW_GUARD:-0}"

# Color output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Performance target: <2s total execution
readonly MAX_EXECUTION_TIME=2

# ============================================================
# Logging Functions
# ============================================================
log_debug() {
    if [[ "${DEBUG_MODE}" == "1" ]]; then
        echo "[DEBUG] $*" | tee -a "${WORKFLOW_GUARD_LOG}" >&2
    fi
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "${WORKFLOW_GUARD_LOG}" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "${WORKFLOW_GUARD_LOG}" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${WORKFLOW_GUARD_LOG}" >&2
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $*" | tee -a "${WORKFLOW_GUARD_LOG}" >&2
}

log_block() {
    echo -e "${RED}[✗ BLOCKED]${NC} $*" | tee -a "${WORKFLOW_GUARD_LOG}" >&2
}

# ============================================================
# Layer 1: Phase Detection
# Purpose: Prevent phase skipping or wrong phase operations
# ============================================================
detect_phase_violation() {
    local input="$1"
    local current_phase=""
    local violations=0

    log_debug "Layer 1: Phase Detection - Start"

    # Read current phase
    if [[ -f "${WORKFLOW_DIR}/current" ]]; then
        current_phase=$(cat "${WORKFLOW_DIR}/current" | tr -d '[:space:]')
        log_debug "Current phase: ${current_phase}"
    else
        log_debug "No phase file, assuming discussion mode"
        return 0  # Skip check in discussion mode
    fi

    # Define phases
    local phases=("P0" "P1" "P2" "P3" "P4" "P5" "P6" "P7")

    # Skip keywords
    local skip_keywords=(
        "跳过" "skip" "bypass" "ignore" "省略" "忽略"
    )

    for keyword in "${skip_keywords[@]}"; do
        for phase in "${phases[@]}"; do
            if echo "$input" | grep -iqE "${keyword}[[:space:]]*${phase}"; then
                log_block "Detected phase skip attempt: ${keyword} ${phase}"
                ((violations++))
            fi
        done
    done

    # Check for direct jumps to future phases
    if [[ -n "$current_phase" ]]; then
        local current_phase_num="${current_phase#P}"
        for phase in "${phases[@]}"; do
            local phase_num="${phase#P}"
            if [[ $phase_num -gt $((current_phase_num + 1)) ]]; then
                if echo "$input" | grep -iqE "直接.*${phase}|directly.*${phase}"; then
                    log_block "Detected phase jump: ${current_phase} → ${phase}"
                    log_error "  Skipping: P$((current_phase_num + 1)) to P$((phase_num - 1))"
                    ((violations++))
                fi
            fi
        done
    fi

    log_debug "Layer 1: Found ${violations} violations"
    return $violations
}

# ============================================================
# Layer 2: Branch Detection
# Purpose: Prevent coding on protected branches (main/master)
# ============================================================
detect_branch_violation() {
    local input="$1"
    local current_branch
    local violations=0

    log_debug "Layer 2: Branch Detection - Start"

    # Get current branch
    if git rev-parse --git-dir > /dev/null 2>&1; then
        current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        log_debug "Current branch: ${current_branch}"
    else
        log_debug "Not a git repository, skipping"
        return 0
    fi

    # Check if on protected branch
    if [[ "$current_branch" =~ ^(main|master|production|release)$ ]]; then
        log_debug "On protected branch: ${current_branch}"

        # Coding operation keywords
        local coding_keywords=(
            "编码" "写代码" "实现" "implement" "code" "develop"
            "写.*function" "创建.*class" "修改.*文件" "create.*file"
            "modify.*code" "add.*feature" "写入.*文件" "更新.*代码"
        )

        for keyword in "${coding_keywords[@]}"; do
            if echo "$input" | grep -iqE "${keyword}"; then
                log_block "Coding operation detected on protected branch: ${current_branch}"
                log_error "  Keyword: ${keyword}"
                log_warn "  Suggestion: Create a new branch"
                log_warn "    git checkout -b feature/your-feature-name"
                ((violations++))
                break
            fi
        done
    fi

    log_debug "Layer 2: Found ${violations} violations"
    return $violations
}

# ============================================================
# Layer 3: "Continue" Bypass Detection (CRITICAL)
# Purpose: Prevent workflow bypass using "continue" keywords
# This is the most critical layer - fixes v1.x vulnerability
# ============================================================
detect_continue_bypass() {
    local input="$1"
    local violations=0

    log_debug "Layer 3: Continue Bypass Detection - Start"

    # Continue patterns (extended list)
    local continue_patterns=(
        "继续" "continue" "接着" "然后" "下一步" "proceed"
        "next" "move on" "carry on" "接下来" "之后" "following"
        "subsequently"
    )

    # Programming keywords (precise matching)
    local programming_keywords=(
        "写代码" "编码" "实现" "implement" "code" "develop"
        "create function" "add feature" "修改" "modify"
        "update code" "写.*function" "创建.*class" "定义.*method"
        "编写.*逻辑" "构建.*API"
    )

    # Detect "continue + programming" combinations
    for continue_word in "${continue_patterns[@]}"; do
        for prog_word in "${programming_keywords[@]}"; do
            # Forward check: continue...programming
            if echo "$input" | grep -iqE "${continue_word}[[:space:][:punct:]]{0,20}${prog_word}"; then
                log_block "Continue bypass pattern detected"
                log_error "  Pattern: '${continue_word}' → '${prog_word}'"
                log_warn "  Explanation: This pattern may bypass workflow validation"
                log_warn "  Suggestion: Explicitly state which Phase for operation"
                ((violations++))
                break 2
            fi

            # Reverse check: programming...continue
            if echo "$input" | grep -iqE "${prog_word}[[:space:][:punct:]]{0,20}${continue_word}"; then
                log_block "Programming+continue pattern detected"
                log_error "  Pattern: '${prog_word}' → '${continue_word}'"
                ((violations++))
                break 2
            fi
        done
    done

    # Additional: Implicit continue patterns
    local implicit_continue_patterns=(
        "继续上次" "继续之前" "继续刚才"
        "continue where.*left" "continue from.*last" "resume.*previous"
    )

    for pattern in "${implicit_continue_patterns[@]}"; do
        if echo "$input" | grep -iqE "${pattern}"; then
            log_block "Implicit continue pattern detected: ${pattern}"
            log_warn "  Please explicitly state current workflow state and Phase"
            ((violations++))
        fi
    done

    log_debug "Layer 3: Found ${violations} violations"
    return $violations
}

# ============================================================
# Layer 4: Programming Keyword Detection
# Purpose: Prevent programming without workflow activation
# ============================================================
detect_programming_without_workflow() {
    local input="$1"
    local workflow_active="no"
    local violations=0

    log_debug "Layer 4: Programming Keyword Detection - Start"

    # Check if workflow is active
    if [[ -f "${WORKFLOW_DIR}/ACTIVE" ]]; then
        workflow_active="yes"
        log_debug "Workflow is active"
    else
        log_debug "Workflow is NOT active"
    fi

    # If workflow not active, detect programming operations
    if [[ "$workflow_active" == "no" ]]; then
        # Programming syntax patterns (language-agnostic)
        local programming_patterns=(
            "function[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\("
            "class[[:space:]]+[A-Z][a-zA-Z0-9_]*"
            "def[[:space:]]+[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\("
            "import[[:space:]]+[a-zA-Z_]"
            "from[[:space:]]+[a-zA-Z_].*import"
            "async[[:space:]]+def"
            "const[[:space:]]+[a-zA-Z_]"
            "let[[:space:]]+[a-zA-Z_]"
            "var[[:space:]]+[a-zA-Z_]"
            "interface[[:space:]]+[A-Z]"
            "type[[:space:]]+[A-Z].*="
            "@[a-zA-Z_]+.*\("
            "public[[:space:]]+class"
            "private[[:space:]]+[a-zA-Z_]"
            "protected[[:space:]]+[a-zA-Z_]"
        )

        for pattern in "${programming_patterns[@]}"; do
            if echo "$input" | grep -qE "$pattern"; then
                log_block "Programming code detected but workflow not active"
                log_error "  Pattern: ${pattern}"
                log_warn "  Suggestion: Start workflow first"
                log_warn "    Method 1: Explicitly say 'start workflow'"
                log_warn "    Method 2: Specify Phase (e.g., 'In P3 phase...')"
                ((violations++))
                break
            fi
        done
    fi

    log_debug "Layer 4: Found ${violations} violations"
    return $violations
}

# ============================================================
# Layer 5: Workflow State Detection
# Purpose: Ensure operations match current phase
# ============================================================
detect_workflow_state_violation() {
    local input="$1"
    local current_phase=""
    local violations=0

    log_debug "Layer 5: Workflow State Detection - Start"

    # Read current phase
    if [[ -f "${WORKFLOW_DIR}/current" ]]; then
        current_phase=$(cat "${WORKFLOW_DIR}/current" | tr -d '[:space:]')
        log_debug "Current phase: ${current_phase}"
    else
        log_debug "No phase file, skipping state detection"
        return 0  # Discussion mode
    fi

    # Coding keywords
    local coding_keywords=(
        "写代码" "编码" "实现.*function" "创建.*class"
        "implement.*method" "code.*logic" "develop.*feature"
    )

    # Check if coding allowed in current phase
    local allows_coding=0
    case "$current_phase" in
        P3|P4)
            allows_coding=1
            log_debug "Current phase allows coding: ${current_phase}"
            ;;
        *)
            allows_coding=0
            log_debug "Current phase does NOT allow coding: ${current_phase}"
            ;;
    esac

    # If current phase doesn't allow coding, detect coding operations
    if [[ $allows_coding -eq 0 ]]; then
        for keyword in "${coding_keywords[@]}"; do
            if echo "$input" | grep -iqE "${keyword}"; then
                log_block "Current phase ${current_phase} does not allow coding operations"
                log_error "  Detected keyword: ${keyword}"
                log_warn "  Suggestion: Coding should be in P3 (Implementation) or P4 (Testing)"

                # Phase-specific suggestions
                case "$current_phase" in
                    P0) log_warn "  P0: Focus on exploration, feasibility validation, prototyping" ;;
                    P1) log_warn "  P1: Focus on requirements analysis, planning, generate PLAN.md" ;;
                    P2) log_warn "  P2: Focus on architecture, directory structure, setup" ;;
                    P5) log_warn "  P5: Focus on code review, quality check, generate REVIEW.md" ;;
                    P6) log_warn "  P6: Focus on documentation, release preparation, deployment" ;;
                    P7) log_warn "  P7: Focus on production monitoring, SLO tracking, performance" ;;
                esac

                ((violations++))
                break
            fi
        done
    fi

    log_debug "Layer 5: Found ${violations} violations"
    return $violations
}

# ============================================================
# Layer 6: Phase Commit Requirements (NEW - Fix for P3-P7)
# Purpose: Validate git commit meets phase-specific requirements
# ============================================================
detect_phase_commit_violations() {
    local violations=0
    local current_phase=""

    log_debug "Layer 6: Phase Commit Requirements - Start"

    # Read current phase
    if [[ -f "${WORKFLOW_DIR}/current" ]]; then
        current_phase=$(cat "${WORKFLOW_DIR}/current" | tr -d '[:space:]')
        log_debug "Current phase: ${current_phase}"
    elif [[ -f "${PROJECT_ROOT}/.phase/current" ]]; then
        current_phase=$(cat "${PROJECT_ROOT}/.phase/current" | tr -d '[:space:]')
        log_debug "Current phase (from .phase): ${current_phase}"
    else
        log_debug "No phase set, skipping commit requirements check"
        return 0
    fi

    # Only validate P3-P7 (implementation, testing, review, release, monitor)
    case "$current_phase" in
        P3)
            # P3: Implementation phase validation
            log_debug "P3: Checking agent count and code changes"

            # Check 1: Agent count (minimum 3 for implementation)
            local agent_count=0
            if [[ -f "${PROJECT_ROOT}/.gates/agents_invocation.json" ]]; then
                if command -v jq >/dev/null 2>&1; then
                    agent_count=$(jq '.agents | length' "${PROJECT_ROOT}/.gates/agents_invocation.json" 2>/dev/null || echo "0")
                else
                    log_warn "jq not found, skipping agent count check"
                fi
            fi

            if [[ $agent_count -lt 3 ]] && [[ $agent_count -gt 0 ]]; then
                log_block "P3 requires ≥3 agents for implementation (found: $agent_count)"
                log_error "  Use: backend-architect, test-engineer, devops-engineer"
                ((violations++))
            fi

            # Check 2: Code changes present
            if git diff --cached --name-only 2>/dev/null | grep -qE '\.(py|sh|js|ts|yml|yaml|json)$'; then
                log_debug "P3: Code changes detected"
            else
                log_warn "P3: No code changes in commit"
            fi
            ;;

        P4)
            # P4: Testing phase validation
            log_debug "P4: Checking for test files"

            # Check: Test files exist in commit
            local test_files
            test_files=$(git diff --cached --name-only 2>/dev/null | grep -E 'test_|_test\.|\.test\.|spec\.|\.spec\.' || echo "")

            if [[ -z "$test_files" ]]; then
                log_block "P4 requires test files in commit"
                log_error "  Add tests in test/ directory"
                ((violations++))
            else
                log_debug "P4: Test files found in commit"
            fi
            ;;

        P5)
            # P5: Review phase validation
            log_debug "P5: Checking for REVIEW.md"

            # Check: REVIEW.md exists or is being committed
            if [[ ! -f "${PROJECT_ROOT}/docs/REVIEW.md" ]] && \
               ! git diff --cached --name-only 2>/dev/null | grep -q "docs/REVIEW.md"; then
                log_block "P5 requires REVIEW.md"
                log_error "  Generate code review report: docs/REVIEW.md"
                ((violations++))
            else
                log_debug "P5: REVIEW.md found"
            fi
            ;;

        P6)
            # P6: Release phase validation
            log_debug "P6: Checking for CHANGELOG.md update"

            # Check: CHANGELOG.md updated
            if ! git diff --cached --name-only 2>/dev/null | grep -q "CHANGELOG.md"; then
                log_block "P6 requires CHANGELOG.md update"
                log_error "  Add release notes to CHANGELOG.md"
                ((violations++))
            else
                log_debug "P6: CHANGELOG.md updated"
            fi

            # Check 2: Documentation updated (warning only)
            local doc_files
            doc_files=$(git diff --cached --name-only 2>/dev/null | grep -E '\.md$|docs/' | wc -l || echo "0")
            if [[ $doc_files -eq 0 ]]; then
                log_warn "P6: No documentation updates in release"
            fi
            ;;

        P7)
            # P7: Monitor phase - usually no commit restrictions
            log_debug "P7: Monitoring phase - no commit restrictions"
            ;;

        P0|P1|P2)
            # Early phases - no commit requirements
            log_debug "${current_phase}: No specific commit requirements"
            ;;

        *)
            log_debug "Unknown or unset phase: ${current_phase}"
            ;;
    esac

    log_debug "Layer 6: Found ${violations} violations"
    return $violations
}

# ============================================================
# Integrated Detection Engine
# ============================================================
run_all_detections() {
    local input="$1"
    local total_violations=0
    local layer_results=()
    local start_time=$(date +%s%N)

    log_info "========================================"
    log_info "Workflow Guard - 6-Layer Detection"
    log_info "========================================"
    echo ""

    # Layer 1: Phase Detection
    log_info "[1/6] Phase Detection..."
    if detect_phase_violation "$input"; then
        layer_results+=("1:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("1:PASS")
        log_success "Pass"
    fi
    echo ""

    # Layer 2: Branch Detection
    log_info "[2/6] Branch Detection..."
    if detect_branch_violation "$input"; then
        layer_results+=("2:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("2:PASS")
        log_success "Pass"
    fi
    echo ""

    # Layer 3: Continue Bypass Detection
    log_info "[3/6] Continue Bypass Detection..."
    if detect_continue_bypass "$input"; then
        layer_results+=("3:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("3:PASS")
        log_success "Pass"
    fi
    echo ""

    # Layer 4: Programming Keyword Detection
    log_info "[4/6] Programming Keyword Detection..."
    if detect_programming_without_workflow "$input"; then
        layer_results+=("4:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("4:PASS")
        log_success "Pass"
    fi
    echo ""

    # Layer 5: Workflow State Detection
    log_info "[5/6] Workflow State Detection..."
    if detect_workflow_state_violation "$input"; then
        layer_results+=("5:FAIL")
        ((total_violations += $?))
    else
        layer_results+=("5:PASS")
        log_success "Pass"
    fi
    echo ""

    # Layer 6: Phase Commit Requirements (NEW)
    log_info "[6/6] Phase Commit Requirements..."
    detect_phase_commit_violations
    local layer6_result=$?
    if [[ $layer6_result -eq 0 ]]; then
        layer_results+=("6:PASS")
        log_success "Pass"
    else
        layer_results+=("6:FAIL")
        ((total_violations += layer6_result))
    fi
    echo ""

    # Summary report
    log_info "========================================"
    log_info "Detection Summary"
    log_info "========================================"

    local passed=0
    local failed=0

    for result in "${layer_results[@]}"; do
        local layer="${result%%:*}"
        local status="${result##*:}"

        if [[ "$status" == "PASS" ]]; then
            echo -e "  Layer ${layer}: ${GREEN}✓ Pass${NC}"
            ((passed++))
        else
            echo -e "  Layer ${layer}: ${RED}✗ Fail${NC}"
            ((failed++))
        fi
    done

    echo ""
    log_info "Passed: ${passed}/6"
    log_info "Failed: ${failed}/6"
    log_info "Total violations: ${total_violations}"

    # Performance check
    local end_time=$(date +%s%N)
    local duration_ns=$((end_time - start_time))
    local duration_s=$((duration_ns / 1000000000))
    local duration_ms=$(((duration_ns % 1000000000) / 1000000))

    log_info "Execution time: ${duration_s}.${duration_ms}s"
    if [[ $duration_s -ge $MAX_EXECUTION_TIME ]]; then
        log_warn "Performance warning: Exceeded ${MAX_EXECUTION_TIME}s target"
    fi

    log_info "========================================"

    # Final judgment
    if [[ $total_violations -gt 0 ]]; then
        echo ""
        log_error "❌ Workflow guard blocked operation"
        echo ""
        log_warn "Fix suggestions:"
        log_warn "1. Check current phase: cat .workflow/current"
        log_warn "2. Confirm branch: git branch --show-current"
        log_warn "3. Ensure workflow active: ls .workflow/ACTIVE"
        log_warn "4. Follow 8-Phase workflow specification"
        log_warn "5. Avoid vague words like '继续', explicitly state Phase"
        echo ""

        # Write violation log
        {
            echo "=========================================="
            echo "Violation Report"
            echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "Total Violations: ${total_violations}"
            echo "Input: ${input}"
            echo "=========================================="
        } >> "${LOG_DIR}/violations.log"

        return 1
    fi

    echo ""
    log_success "✅ All detections passed, operation allowed"
    return 0
}

# ============================================================
# Main Entry
# ============================================================
show_help() {
    cat << 'EOF'
Claude Enhancer v2.0 - Workflow Guard

Usage:
  workflow_guard.sh <input_text>
  workflow_guard.sh --test
  workflow_guard.sh --help

Options:
  --test          Run built-in test cases
  --help          Show help information
  --debug         Enable debug mode

Environment Variables:
  DEBUG_WORKFLOW_GUARD=1    Enable debug output

Examples:
  workflow_guard.sh "Implement user login in P3"
  workflow_guard.sh "继续写代码"  # Should be blocked
  DEBUG_WORKFLOW_GUARD=1 workflow_guard.sh "test input"

6-Layer Detection:
  1. Phase Detection - Prevent phase skipping
  2. Branch Detection - Prevent coding on protected branches
  3. Continue Detection - Prevent "continue" bypass
  4. Programming Detection - Prevent coding without workflow
  5. State Detection - Ensure phase operation matching
  6. Commit Requirements - Validate P3-P7 commit requirements

EOF
}

main() {
    # Parse arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --test)
            log_info "Test mode not implemented in workflow_guard.sh"
            log_info "Use core/hooks/enforcer_v2.sh --test instead"
            exit 0
            ;;
        --debug)
            export DEBUG_WORKFLOW_GUARD=1
            shift
            ;;
        "")
            log_error "Error: Missing input parameter"
            echo ""
            show_help
            exit 1
            ;;
    esac

    local input_text="$*"

    # Execute detection
    if run_all_detections "$input_text"; then
        exit 0
    else
        exit 1
    fi
}

# Execute main function
main "$@"
