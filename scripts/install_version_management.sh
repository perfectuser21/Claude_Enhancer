#!/bin/bash
# install_version_management.sh - Install Version Management System
# Purpose: Set up VERSION as single source of truth and sync all files

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Version Management System Installation${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Step 1: Create VERSION file
echo -e "${YELLOW}Step 1: Creating VERSION file...${NC}"
if [[ -f "${REPO_ROOT}/VERSION" ]]; then
    echo -e "${GREEN}✓ VERSION file already exists${NC}"
    VERSION=$(cat "${REPO_ROOT}/VERSION")
    echo -e "  Current version: ${VERSION}"
else
    echo "5.3.4" > "${REPO_ROOT}/VERSION"
    echo -e "${GREEN}✓ Created VERSION file with 5.3.4${NC}"
fi
echo ""

# Step 2: Make scripts executable
echo -e "${YELLOW}Step 2: Making scripts executable...${NC}"
chmod +x "${REPO_ROOT}/scripts/sync_version.sh"
chmod +x "${REPO_ROOT}/scripts/verify_version_consistency.sh"
chmod +x "${REPO_ROOT}/scripts/update_readme_version.sh"
echo -e "${GREEN}✓ Scripts are now executable${NC}"
echo ""

# Step 3: Update README.md
echo -e "${YELLOW}Step 3: Updating README.md version...${NC}"
bash "${REPO_ROOT}/scripts/update_readme_version.sh"
echo -e "${GREEN}✓ README.md updated${NC}"
echo ""

# Step 4: Sync all files
echo -e "${YELLOW}Step 4: Syncing version to all files...${NC}"
if bash "${REPO_ROOT}/scripts/sync_version.sh"; then
    echo -e "${GREEN}✓ All files synced successfully${NC}"
else
    echo -e "${RED}❌ Sync failed${NC}"
    exit 1
fi
echo ""

# Step 5: Verify consistency
echo -e "${YELLOW}Step 5: Verifying version consistency...${NC}"
if bash "${REPO_ROOT}/scripts/verify_version_consistency.sh"; then
    echo -e "${GREEN}✓ Version consistency verified${NC}"
else
    echo -e "${RED}❌ Verification failed${NC}"
    exit 1
fi
echo ""

# Step 6: Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Installation Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Version Management System installed successfully!${NC}"
echo ""
echo -e "${YELLOW}Key Files:${NC}"
echo "  ✓ VERSION - Single source of truth"
echo "  ✓ scripts/sync_version.sh - Sync script"
echo "  ✓ scripts/verify_version_consistency.sh - Verification script"
echo "  ✓ docs/VERSION_MANAGEMENT.md - Documentation"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review changes: git diff"
echo "  2. Commit changes:"
echo "     git add VERSION scripts/ docs/VERSION_MANAGEMENT.md .workflow/ .claude/ CHANGELOG.md README.md"
echo "     git commit -m 'chore: establish VERSION as single source of truth (v5.3.4)'"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo "  Update version: echo '5.3.5' > VERSION && ./scripts/sync_version.sh"
echo "  Verify: ./scripts/verify_version_consistency.sh"
echo ""
