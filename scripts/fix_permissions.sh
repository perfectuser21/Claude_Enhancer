#!/usr/bin/env bash
# fix_permissions.sh - Standardize file permissions across CLI system
set -euo pipefail

echo "===================================================="
echo "  Claude Enhancer - Fix File Permissions"
echo "===================================================="
echo ""

PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

fixed_count=0
error_count=0

# Function to set and verify permissions
set_perms() {
    local file="$1"
    local target_perms="$2"
    local description="$3"
    
    if [[ ! -e "$file" ]]; then
        echo -e "${YELLOW}[SKIP]${RESET} $file (not found)"
        return 0
    fi
    
    local current_perms
    current_perms=$(stat -c '%a' "$file" 2>/dev/null || stat -f '%Lp' "$file" 2>/dev/null)
    
    if [[ "$current_perms" == "$target_perms" ]]; then
        echo -e "${GREEN}[OK]${RESET} $file ($current_perms) - $description"
        return 0
    fi
    
    echo -n "Fixing: $file ($current_perms → $target_perms)... "
    
    if chmod "$target_perms" "$file" 2>/dev/null; then
        # Verify
        local new_perms
        new_perms=$(stat -c '%a' "$file" 2>/dev/null || stat -f '%Lp' "$file" 2>/dev/null)
        
        if [[ "$new_perms" == "$target_perms" ]]; then
            echo -e "${GREEN}✓${RESET}"
            ((fixed_count++))
            return 0
        else
            echo -e "${RED}✗ (verification failed: got $new_perms)${RESET}"
            ((error_count++))
            return 1
        fi
    else
        echo -e "${RED}✗ (chmod failed)${RESET}"
        ((error_count++))
        return 1
    fi
}

echo -e "${BLUE}[1/5]${RESET} Fixing command file permissions (755 - executable)..."
echo ""

for cmd_file in "$PROJECT_ROOT"/.workflow/cli/commands/*.sh; do
    [[ -f "$cmd_file" ]] && set_perms "$cmd_file" "755" "Command script"
done

echo ""
echo -e "${BLUE}[2/5]${RESET} Fixing library file permissions (755 - executable, sourced)..."
echo ""

for lib_file in "$PROJECT_ROOT"/.workflow/cli/lib/*.sh; do
    [[ -f "$lib_file" ]] && set_perms "$lib_file" "755" "Library script"
done

echo ""
echo -e "${BLUE}[3/5]${RESET} Fixing main CLI files (755 - executable)..."
echo ""

set_perms "$PROJECT_ROOT/ce.sh" "755" "Main CLI entry point"
[[ -f "$PROJECT_ROOT/.workflow/cli/install.sh" ]] && set_perms "$PROJECT_ROOT/.workflow/cli/install.sh" "755" "Install script"
[[ -f "$PROJECT_ROOT/.workflow/cli/uninstall.sh" ]] && set_perms "$PROJECT_ROOT/.workflow/cli/uninstall.sh" "755" "Uninstall script"

echo ""
echo -e "${BLUE}[4/5]${RESET} Fixing state file permissions (600 - secure data)..."
echo ""

if [[ -d "$PROJECT_ROOT/.workflow/state" ]]; then
    find "$PROJECT_ROOT/.workflow/state" -type f \( -name "*.yml" -o -name "*.json" -o -name "*.state" \) -print0 2>/dev/null | \
        while IFS= read -r -d '' state_file; do
            set_perms "$state_file" "600" "State data file"
        done
else
    echo -e "${YELLOW}[SKIP]${RESET} .workflow/state directory not found"
fi

echo ""
echo -e "${BLUE}[5/5]${RESET} Fixing directory permissions..."
echo ""

# Ensure state directories are secure
if [[ -d "$PROJECT_ROOT/.workflow/state" ]]; then
    set_perms "$PROJECT_ROOT/.workflow/state" "700" "State directory"
    
    if [[ -d "$PROJECT_ROOT/.workflow/state/sessions" ]]; then
        set_perms "$PROJECT_ROOT/.workflow/state/sessions" "700" "Sessions directory"
    fi
    
    if [[ -d "$PROJECT_ROOT/.workflow/state/locks" ]]; then
        set_perms "$PROJECT_ROOT/.workflow/state/locks" "700" "Locks directory"
    fi
fi

# Regular directories should be 755
find "$PROJECT_ROOT/.workflow/cli" -type d -not -path "*/.workflow/state*" -print0 2>/dev/null | \
    while IFS= read -r -d '' dir; do
        set_perms "$dir" "755" "Regular directory"
    done

echo ""
echo "===================================================="
echo "  Permission Fix Complete"
echo "===================================================="
echo ""
echo -e "Fixed: ${GREEN}$fixed_count${RESET} files"
echo -e "Errors: ${RED}$error_count${RESET} files"
echo ""

if [[ $error_count -gt 0 ]]; then
    echo -e "${YELLOW}⚠ Some permissions could not be fixed${RESET}"
    exit 1
else
    echo -e "${GREEN}✓ All permissions corrected${RESET}"
    exit 0
fi
