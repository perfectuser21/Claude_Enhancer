#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Branch Common Library - Main Loader
# Claude Enhancer v7.3.0 - Modularized version
# ═══════════════════════════════════════════════════════════════
# Purpose: Load modularized branch management functions
# This file is now < 100 lines to comply with script size limits
# ═══════════════════════════════════════════════════════════════

# Prevent multiple sourcing
if [[ -n "${_BRANCH_COMMON_LOADED:-}" ]]; then
    return 0
fi
_BRANCH_COMMON_LOADED=true

# Get library directory
BRANCH_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ═══════════════════════════════════════════════════════════════
# Load Modules
# ═══════════════════════════════════════════════════════════════

# 1. Load core functions (required)
if [[ -f "$BRANCH_LIB_DIR/branch_core.sh" ]]; then
    # shellcheck source=/dev/null
    source "$BRANCH_LIB_DIR/branch_core.sh"
else
    echo "ERROR: branch_core.sh not found!" >&2
    exit 1
fi

# 2. Load display functions (optional, for UI)
if [[ -f "$BRANCH_LIB_DIR/branch_display.sh" ]]; then
    # shellcheck source=/dev/null
    source "$BRANCH_LIB_DIR/branch_display.sh"
fi

# ═══════════════════════════════════════════════════════════════
# Export All Functions
# ═══════════════════════════════════════════════════════════════

# Core functions
export -f get_current_branch
export -f is_protected_branch
export -f is_git_repo
export -f log_hook_event
export -f auto_create_branch
export -f validate_json_file

# Display functions (if loaded)
if type show_branch_naming_guide >/dev/null 2>&1; then
    export -f show_branch_naming_guide
    export -f show_phase_workflow
    export -f show_protected_branch_warning
    export -f show_protected_branch_error
fi

# Utility functions
export -f is_silent_mode
export -f is_auto_mode
export -f is_auto_create_enabled
export -f is_git_hook_context
export -f is_claude_hook_context

# ═══════════════════════════════════════════════════════════════
# Module Information
# ═══════════════════════════════════════════════════════════════

if [[ "${DEBUG_MODE:-false}" == "true" ]]; then
    echo "Branch Common Library loaded:" >&2
    echo "  - branch_core.sh: Core functions" >&2
    echo "  - branch_display.sh: Display functions" >&2
    echo "  - Cache enabled: ${CACHE_ENABLED:-false}" >&2
fi

# Log successful load
log_hook_event "branch_common" "Modularized library loaded successfully"