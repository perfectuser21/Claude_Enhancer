#!/bin/bash
# sync_version.sh - Version Synchronization Script
# Purpose: Sync VERSION file to all version-containing files
# Usage: ./scripts/sync_version.sh

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
    echo -e "${RED}❌ VERSION file not found at: ${VERSION_FILE}${NC}"
    echo "Please create VERSION file with version number (e.g., 5.3.4)"
    exit 1
fi

# Read version from VERSION file
VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')

# Validate version format (semver: X.Y.Z)
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo -e "${RED}❌ Invalid version format in VERSION file: ${VERSION}${NC}"
    echo "Expected format: X.Y.Z (e.g., 5.3.4)"
    exit 1
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Version Synchronization${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Source Version: ${VERSION}${NC}"
echo ""

# Track results
SUCCESS_COUNT=0
FAIL_COUNT=0
TOTAL_FILES=0

# Function to sync version to a file
sync_to_file() {
    local file=$1
    local path_expr=$2
    local tool=$3

    TOTAL_FILES=$((TOTAL_FILES + 1))

    if [[ ! -f "$file" ]]; then
        echo -e "${YELLOW}⚠️  Skip (not found): ${file}${NC}"
        return
    fi

    # Backup original file
    cp "$file" "${file}.backup.$(date +%s)" 2>/dev/null || true

    case "$tool" in
        yq)
            if command -v yq >/dev/null 2>&1; then
                yq eval "${path_expr} = \"${VERSION}\"" -i "$file"
                echo -e "${GREEN}✓ Synced (yq): ${file}${NC}"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                # Fallback to sed for YAML
                sed -i.bak "s/^version: .*/version: \"${VERSION}\"/" "$file"
                echo -e "${GREEN}✓ Synced (sed): ${file}${NC}"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            fi
            ;;
        jq)
            if command -v jq >/dev/null 2>&1; then
                jq "${path_expr} = \"${VERSION}\"" "$file" > "${file}.tmp"
                mv "${file}.tmp" "$file"
                echo -e "${GREEN}✓ Synced (jq): ${file}${NC}"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                echo -e "${RED}❌ Failed (jq not found): ${file}${NC}"
                FAIL_COUNT=$((FAIL_COUNT + 1))
            fi
            ;;
        sed_markdown)
            # Update markdown headers with version
            sed -i.bak "s/## \[.*\] - /## [${VERSION}] - /" "$file" 2>/dev/null || true
            # Update badge in README
            sed -i.bak "s/version-[0-9.]*-blue/version-${VERSION}-blue/" "$file" 2>/dev/null || true
            echo -e "${GREEN}✓ Synced (sed): ${file}${NC}"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            ;;
        sed_comment)
            # Update version in comment line
            sed -i.bak "s/^# Version: .*/# Version: ${VERSION}/" "$file" 2>/dev/null || true
            echo -e "${GREEN}✓ Synced (sed): ${file}${NC}"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            ;;
        *)
            echo -e "${RED}❌ Unknown tool: ${tool}${NC}"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            ;;
    esac
}

# Sync to all files
echo -e "${BLUE}Syncing to configuration files...${NC}"
sync_to_file "${REPO_ROOT}/.workflow/manifest.yml" ".version" "yq"
sync_to_file "${REPO_ROOT}/.claude/settings.json" ".version" "jq"

echo ""
echo -e "${BLUE}Syncing to documentation files...${NC}"
sync_to_file "${REPO_ROOT}/README.md" "" "sed_markdown"
sync_to_file "${REPO_ROOT}/CLAUDE.md" "" "sed_comment"

# Sync to package.json if exists
if [[ -f "${REPO_ROOT}/package.json" ]]; then
    echo ""
    echo -e "${BLUE}Syncing to package files...${NC}"
    sync_to_file "${REPO_ROOT}/package.json" ".version" "jq"
fi

# Clean up backup files older than 7 days
find "$REPO_ROOT" -name "*.backup.*" -mtime +7 -delete 2>/dev/null || true

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Version:         ${GREEN}${VERSION}${NC}"
echo -e "Files Processed: ${TOTAL_FILES}"
echo -e "Success:         ${GREEN}${SUCCESS_COUNT}${NC}"
echo -e "Failed:          ${RED}${FAIL_COUNT}${NC}"
echo ""

if [[ $FAIL_COUNT -eq 0 ]]; then
    echo -e "${GREEN}✅ All files synced successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Review changes: git diff"
    echo "  2. Verify version: ./scripts/verify_version_consistency.sh"
    echo "  3. Commit changes: git commit -am 'chore: sync version to ${VERSION}'"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some files failed to sync. Please review manually.${NC}"
    exit 1
fi
