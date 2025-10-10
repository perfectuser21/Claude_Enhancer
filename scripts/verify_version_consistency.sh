#!/bin/bash
# verify_version_consistency.sh - Version Consistency Verification
# Purpose: Verify all files have consistent version numbers
# Usage: ./scripts/verify_version_consistency.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${REPO_ROOT}/VERSION"

# Exit if VERSION file doesn't exist
if [[ ! -f "$VERSION_FILE" ]]; then
    echo -e "${RED}❌ VERSION file not found: ${VERSION_FILE}${NC}"
    echo "Please run: ./scripts/sync_version.sh"
    exit 1
fi

# Read expected version
EXPECTED_VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')

# Validate version format
if ! echo "$EXPECTED_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo -e "${RED}❌ Invalid version format: ${EXPECTED_VERSION}${NC}"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Version Consistency Check${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Expected Version: ${EXPECTED_VERSION}${NC}"
echo ""

# Track results
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_CHECKS=0

# Function to check version in a file
check_file() {
    local file=$1
    local path_expr=$2
    local tool=$3
    local friendly_name=$4

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [[ ! -f "$file" ]]; then
        echo -e "${YELLOW}⚠️  Skip (not found): ${friendly_name}${NC}"
        return
    fi

    local actual_version=""

    case "$tool" in
        yq)
            if command -v yq >/dev/null 2>&1; then
                actual_version=$(yq eval "$path_expr" "$file" 2>/dev/null | tr -d '"')
            else
                # Fallback to grep
                actual_version=$(grep "^version:" "$file" | head -1 | awk '{print $2}' | tr -d '"')
            fi
            ;;
        jq)
            if command -v jq >/dev/null 2>&1; then
                actual_version=$(jq -r "$path_expr" "$file" 2>/dev/null)
            else
                echo -e "${RED}❌ jq not found, cannot verify ${friendly_name}${NC}"
                FAIL_COUNT=$((FAIL_COUNT + 1))
                return
            fi
            ;;
        grep_changelog)
            # Check first version in CHANGELOG
            actual_version=$(grep -m 1 "^## \[" "$file" | sed 's/.*\[\(.*\)\].*/\1/')
            ;;
        grep_badge)
            # Check version badge in README
            actual_version=$(grep -o "version-[0-9.]*-blue" "$file" | head -1 | sed 's/version-\(.*\)-blue/\1/')
            ;;
        *)
            echo -e "${RED}❌ Unknown tool: ${tool}${NC}"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            return
            ;;
    esac

    # Compare versions
    if [[ "$actual_version" == "$EXPECTED_VERSION" ]]; then
        echo -e "${GREEN}✓ ${friendly_name}: ${actual_version}${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}❌ ${friendly_name}: expected ${EXPECTED_VERSION}, got ${actual_version}${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# Check all files
echo -e "${BLUE}Checking configuration files...${NC}"
check_file "${REPO_ROOT}/.workflow/manifest.yml" ".version" "yq" "Workflow Manifest"
check_file "${REPO_ROOT}/.claude/settings.json" ".version" "jq" "Claude Settings"

echo ""
echo -e "${BLUE}Checking documentation files...${NC}"
check_file "${REPO_ROOT}/CHANGELOG.md" "" "grep_changelog" "CHANGELOG (latest)"
check_file "${REPO_ROOT}/README.md" "" "grep_badge" "README (badge)"

# Check package.json if exists
if [[ -f "${REPO_ROOT}/package.json" ]]; then
    echo ""
    echo -e "${BLUE}Checking package files...${NC}"
    check_file "${REPO_ROOT}/package.json" ".version" "jq" "package.json"
fi

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Verification Results${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Expected:    ${GREEN}${EXPECTED_VERSION}${NC}"
echo -e "Checks:      ${TOTAL_CHECKS}"
echo -e "Passed:      ${GREEN}${PASS_COUNT}${NC}"
echo -e "Failed:      ${RED}${FAIL_COUNT}${NC}"
echo ""

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}✅ All versions are consistent!${NC}"
    exit 0
else
    echo -e "${RED}❌ Version inconsistency detected!${NC}"
    echo ""
    echo -e "${YELLOW}Fix command:${NC}"
    echo "  ./scripts/sync_version.sh"
    exit 1
fi
