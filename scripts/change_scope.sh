#!/bin/bash
# ChangeScope - File Modification Whitelist Mechanism
# Defines and enforces which files can be modified during a task
#
# Usage:
#   source scripts/change_scope.sh
#   changescope_init "hooks scripts/.claude/hooks"
#   changescope_check "scripts/new_script.sh"
#   changescope_validate_commit

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
SCOPE_FILE="${SCOPE_FILE:-.workflow/changescope.txt}"
SCOPE_PATH="$PROJECT_ROOT/$SCOPE_FILE"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Initialization
# ============================================

# Initialize ChangeScope for a new task
# Usage: changescope_init "hooks scripts docs"
changescope_init() {
    local scope_patterns="$1"

    mkdir -p "$(dirname "$SCOPE_PATH")"

    cat > "$SCOPE_PATH" <<EOF
# ChangeScope - Allowed File Modifications
# Created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Task: ${TASK_DESCRIPTION:-"No description"}
#
# Only files matching these patterns can be modified:

$scope_patterns

# Special allowances:
# - .workflow/*.md (task documentation)
# - CHANGELOG.md (version history)
# - README.md (if needed)
# - tests/** (test files)
EOF

    echo -e "${GREEN}✓${NC} ChangeScope initialized"
    echo -e "${BLUE}Allowed patterns:${NC}"
    echo "$scope_patterns" | tr ' ' '\n' | sed 's/^/  - /'

    # Update state.json
    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        state_set "change_scope.enabled" "true"
        # Store scope as array (simplified - just store as string for now)
        state_set "change_scope.current_scope" "$scope_patterns"
    fi
}

# Disable ChangeScope
changescope_disable() {
    if [[ -f "$SCOPE_PATH" ]]; then
        rm -f "$SCOPE_PATH"
        echo -e "${YELLOW}⚠️${NC}  ChangeScope disabled"
    fi

    # Update state.json
    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        state_set "change_scope.enabled" "false"
    fi
}

# Check if ChangeScope is enabled
changescope_is_enabled() {
    [[ -f "$SCOPE_PATH" ]]
}

# ============================================
# Validation
# ============================================

# Check if a file is within scope
# Usage: changescope_check "scripts/new_script.sh"
# Returns: 0 if allowed, 1 if not allowed
changescope_check() {
    local file="$1"

    if ! changescope_is_enabled; then
        # Scope not enabled, allow all
        return 0
    fi

    # Extract patterns from scope file (skip comments and empty lines)
    local patterns
    patterns=$(grep -v '^#' "$SCOPE_PATH" | grep -v '^$' | tr '\n' ' ')

    # Check if file matches any pattern
    for pattern in $patterns; do
        # Expand glob pattern
        if [[ "$file" == "$pattern" ]] || [[ "$file" =~ ^${pattern} ]]; then
            return 0  # Allowed
        fi

        # Handle ** glob (matches any depth)
        if [[ "$pattern" == *"**"* ]]; then
            local base_pattern="${pattern%%/**}"
            if [[ "$file" =~ ^${base_pattern}/ ]]; then
                return 0  # Allowed
            fi
        fi
    done

    # Check special allowances
    case "$file" in
        .workflow/*.md|CHANGELOG.md|README.md|tests/*|test/*)
            return 0  # Allowed
            ;;
    esac

    # Not allowed
    return 1
}

# Validate all staged files against ChangeScope
# Returns: 0 if all allowed, 1 if violations found
changescope_validate_commit() {
    if ! changescope_is_enabled; then
        return 0  # Scope not enabled
    fi

    local staged_files
    staged_files=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)

    if [[ -z "$staged_files" ]]; then
        return 0  # No files staged
    fi

    local violations=()
    while IFS= read -r file; do
        if ! changescope_check "$file"; then
            violations+=("$file")
        fi
    done <<< "$staged_files"

    if [[ ${#violations[@]} -gt 0 ]]; then
        echo ""
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}❌ ERROR: ChangeScope Violation${NC}"
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo -e "${YELLOW}Files outside allowed scope:${NC}"
        for file in "${violations[@]}"; do
            echo "  - $file"
        done
        echo ""
        echo -e "${BLUE}Allowed scope:${NC}"
        grep -v '^#' "$SCOPE_PATH" | grep -v '^$' | sed 's/^/  - /'
        echo ""
        echo -e "${BLUE}💡 To fix:${NC}"
        echo "  1. Remove out-of-scope files from commit:"
        echo "     git reset HEAD <file>"
        echo ""
        echo "  2. Or expand scope if needed:"
        echo "     vim $SCOPE_FILE"
        echo ""
        echo -e "${RED}🚨 This is a HARD BLOCK - commit cannot proceed${NC}"
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo ""

        # Update state.json
        if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
            source "$PROJECT_ROOT/scripts/state_manager.sh"
            state_increment "change_scope.violations"
            local timestamp
            timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            state_set "change_scope.last_violation_at" "$timestamp"
        fi

        return 1
    fi

    echo -e "${GREEN}✓${NC} ChangeScope validation passed (${#staged_files} files in scope)"
    return 0
}

# ============================================
# Reporting
# ============================================

# Show current ChangeScope
changescope_show() {
    if ! changescope_is_enabled; then
        echo -e "${YELLOW}⚠️${NC}  ChangeScope is not enabled"
        echo ""
        echo "To enable:"
        echo "  changescope_init \"pattern1 pattern2 ...\""
        return 0
    fi

    echo "════════════════════════════════════════════"
    echo "  ChangeScope - Allowed Modifications"
    echo "════════════════════════════════════════════"
    echo ""
    echo "Enabled: ✓"
    echo ""
    echo "Allowed patterns:"
    grep -v '^#' "$SCOPE_PATH" | grep -v '^$' | sed 's/^/  - /'
    echo ""
    echo "Special allowances:"
    echo "  - .workflow/*.md (task docs)"
    echo "  - CHANGELOG.md"
    echo "  - README.md"
    echo "  - tests/**"
    echo "════════════════════════════════════════════"
}

# Show ChangeScope statistics
changescope_stats() {
    if ! changescope_is_enabled; then
        echo "ChangeScope: Disabled"
        return 0
    fi

    if [[ -f "$PROJECT_ROOT/scripts/state_manager.sh" ]]; then
        source "$PROJECT_ROOT/scripts/state_manager.sh"
        local violations
        violations=$(state_get "change_scope.violations")
        echo "ChangeScope: Enabled"
        echo "Violations: $violations"
    else
        echo "ChangeScope: Enabled (stats unavailable)"
    fi
}

# ============================================
# Presets (Common Scopes)
# ============================================

# Hooks-only scope
changescope_preset_hooks() {
    changescope_init ".claude/hooks/** .git/hooks/**"
}

# Scripts-only scope
changescope_preset_scripts() {
    changescope_init "scripts/**"
}

# Documentation-only scope
changescope_preset_docs() {
    changescope_init "docs/** *.md"
}

# Tests-only scope
changescope_preset_tests() {
    changescope_init "tests/** test/**"
}

# Full scope (hooks + scripts + docs)
changescope_preset_full() {
    changescope_init ".claude/hooks/** .git/hooks/** scripts/** docs/**"
}

# ============================================
# Main (if run directly)
# ============================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being run directly, not sourced
    case "${1:-}" in
        init)
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 init \"pattern1 pattern2 ...\""
                exit 1
            fi
            changescope_init "$2"
            ;;
        disable)
            changescope_disable
            ;;
        check)
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 check <file>"
                exit 1
            fi
            if changescope_check "$2"; then
                echo "✓ File is within scope: $2"
                exit 0
            else
                echo "✗ File is outside scope: $2"
                exit 1
            fi
            ;;
        validate)
            changescope_validate_commit
            ;;
        show)
            changescope_show
            ;;
        stats)
            changescope_stats
            ;;
        preset-hooks)
            changescope_preset_hooks
            ;;
        preset-scripts)
            changescope_preset_scripts
            ;;
        preset-docs)
            changescope_preset_docs
            ;;
        preset-tests)
            changescope_preset_tests
            ;;
        preset-full)
            changescope_preset_full
            ;;
        *)
            echo "ChangeScope - File Modification Whitelist"
            echo ""
            echo "Usage:"
            echo "  $0 init \"pattern1 pattern2\"   - Initialize scope"
            echo "  $0 disable                      - Disable scope"
            echo "  $0 check <file>                 - Check if file in scope"
            echo "  $0 validate                     - Validate staged files"
            echo "  $0 show                         - Show current scope"
            echo "  $0 stats                        - Show statistics"
            echo ""
            echo "Presets:"
            echo "  $0 preset-hooks                 - Hooks only"
            echo "  $0 preset-scripts               - Scripts only"
            echo "  $0 preset-docs                  - Docs only"
            echo "  $0 preset-tests                 - Tests only"
            echo "  $0 preset-full                  - Hooks + Scripts + Docs"
            echo ""
            echo "Or source this file:"
            echo "  source scripts/change_scope.sh"
            echo "  changescope_init \"hooks/** scripts/**\""
            exit 1
            ;;
    esac
fi
