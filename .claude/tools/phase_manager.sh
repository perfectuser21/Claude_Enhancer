#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Phase Manager - 7-Phase工作流统一管理器 (Modularized)
# Claude Enhancer v7.3.0 - Phase-centric架构核心
# ═══════════════════════════════════════════════════════════════
# 用途：统一管理7个Phase的检查、转换和验证
# 版本：1.1 (modularized)
# 创建日期：2025-10-25
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# Get library directory
PHASE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib"

# ═══════════════════════════════════════════════════════════════
# Load Modules
# ═══════════════════════════════════════════════════════════════

# 1. Load core functions (required)
if [[ -f "$PHASE_LIB_DIR/phase_core.sh" ]]; then
    # shellcheck source=/dev/null
    source "$PHASE_LIB_DIR/phase_core.sh"
else
    echo "ERROR: phase_core.sh not found!" >&2
    exit 1
fi

# 2. Load check functions (required)
if [[ -f "$PHASE_LIB_DIR/phase_checks.sh" ]]; then
    # shellcheck source=/dev/null
    source "$PHASE_LIB_DIR/phase_checks.sh"
else
    echo "ERROR: phase_checks.sh not found!" >&2
    exit 1
fi

# 3. Load display functions (required)
if [[ -f "$PHASE_LIB_DIR/phase_display.sh" ]]; then
    # shellcheck source=/dev/null
    source "$PHASE_LIB_DIR/phase_display.sh"
else
    echo "ERROR: phase_display.sh not found!" >&2
    exit 1
fi

# ═══════════════════════════════════════════════════════════════
# Main Function
# ═══════════════════════════════════════════════════════════════

main() {
    local command="${1:-status}"
    shift || true

    case "$command" in
        status|s)
            show_status
            ;;
        check|c)
            local phase="${1:-$(get_current_phase)}"
            local mode="${2:-full}"
            run_phase_checks "$phase" "$mode"
            ;;
        switch|sw)
            local new_phase="${1:-}"
            if [[ -z "$new_phase" ]]; then
                echo -e "${RED}Usage: $0 switch <Phase1-7>${NC}"
                exit 1
            fi
            if switch_to_phase "$new_phase"; then
                show_phase_transition "$(get_current_phase)" "$new_phase"
            fi
            ;;
        next|n)
            local current_phase
            current_phase=$(get_current_phase)
            local phase_num="${current_phase#Phase}"
            local next_num=$((phase_num + 1))
            if [[ $next_num -le 7 ]]; then
                local next_phase="Phase${next_num}"
                if switch_to_phase "$next_phase"; then
                    show_phase_transition "$current_phase" "$next_phase"
                fi
            else
                echo -e "${YELLOW}Already at final phase (Phase7)${NC}"
            fi
            ;;
        help|h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# ═══════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

# Module Information (for documentation)
: <<'MODULE_INFO'
Modular Structure:
- phase_manager.sh: Main loader (95 lines)
- lib/phase_core.sh: Core functions (97 lines)
- lib/phase_checks.sh: Phase checking logic (215 lines)
- lib/phase_display.sh: Display and UI functions (105 lines)
- Total: 512 lines (same as original, but modularized)

Benefits:
- Each module is under 300 lines
- Functions are logically grouped
- Easier to maintain and test
- Can be sourced independently
MODULE_INFO