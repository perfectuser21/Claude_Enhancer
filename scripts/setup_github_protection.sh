#!/bin/bash
# Setup GitHub Branch Protection Rules
# This script configures branch protection for Claude Enhancer repository

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO="${GITHUB_REPOSITORY:-}"
BRANCH="${BRANCH_NAME:-main}"
DRY_RUN="${DRY_RUN:-false}"

echo -e "${BLUE}🔒 GitHub Branch Protection Setup${NC}"
echo "=================================="
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Get repository from git remote if not set
if [ -z "$REPO" ]; then
    REPO=$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/' || echo "")
fi

if [ -z "$REPO" ]; then
    echo -e "${RED}❌ Could not determine repository${NC}"
    echo "Set GITHUB_REPOSITORY environment variable or run in git repo"
    exit 1
fi

echo -e "${GREEN}Repository: $REPO${NC}"
echo -e "${GREEN}Branch: $BRANCH${NC}"
echo ""

# Protection rules configuration
PROTECTION_CONFIG=$(cat <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "quality-gate",
      "hook-performance",
      "test-suite-performance",
      "coverage-check"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true
}
EOF
)

echo -e "${YELLOW}📋 Protection Rules to Apply:${NC}"
echo "$PROTECTION_CONFIG" | jq '.' 2>/dev/null || echo "$PROTECTION_CONFIG"
echo ""

if [ "$DRY_RUN" = "true" ]; then
    echo -e "${YELLOW}🧪 DRY RUN MODE - No changes will be made${NC}"
    exit 0
fi

# Confirm before applying
read -p "Apply these protection rules? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠️ Aborted by user${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🔧 Applying branch protection...${NC}"

# Apply protection rules
if gh api "repos/$REPO/branches/$BRANCH/protection" \
    --method PUT \
    --input - <<< "$PROTECTION_CONFIG" 2>/dev/null; then
    echo -e "${GREEN}✅ Branch protection configured successfully${NC}"
else
    echo -e "${RED}❌ Failed to configure branch protection${NC}"
    echo ""
    echo "Possible reasons:"
    echo "  1. Insufficient permissions (need admin access)"
    echo "  2. Repository not found"
    echo "  3. Branch does not exist"
    echo ""
    exit 1
fi

echo ""
echo -e "${BLUE}📋 Verifying configuration...${NC}"

# Verify the configuration
if protection=$(gh api "repos/$REPO/branches/$BRANCH/protection" 2>/dev/null); then
    echo -e "${GREEN}✅ Configuration verified${NC}"
    echo ""
    echo "Active protection rules:"
    echo "$protection" | jq '{
      enforce_admins: .enforce_admins.enabled,
      required_reviews: .required_pull_request_reviews.required_approving_review_count,
      required_checks: .required_status_checks.contexts,
      allow_force_pushes: .allow_force_pushes.enabled,
      allow_deletions: .allow_deletions.enabled
    }' 2>/dev/null || echo "$protection"
else
    echo -e "${YELLOW}⚠️ Could not verify configuration${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Branch protection setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Test by creating a PR"
echo "  2. Verify status checks are enforced"
echo "  3. Ensure direct pushes are blocked"
echo ""

# Additional checks to set up
echo -e "${BLUE}📋 Additional Recommendations:${NC}"
echo "  1. Create CODEOWNERS file for automatic reviewers"
echo "  2. Set up required status checks in GitHub UI"
echo "  3. Configure notification rules for failed checks"
echo "  4. Document protection rules in team wiki"
echo ""

# Generate CODEOWNERS template if it doesn't exist
if [ ! -f ".github/CODEOWNERS" ]; then
    echo -e "${YELLOW}📝 Creating CODEOWNERS template...${NC}"
    mkdir -p .github
    cat > .github/CODEOWNERS <<'CODEOWNERS'
# Code owners for automatic review requests

# Global owners
* @claude-enhancer-team

# Workflows and CI/CD
/.github/workflows/ @devops-team
/.github/actions/ @devops-team

# Core configuration
/.claude/ @core-team
/.workflow/ @core-team

# Security-sensitive files
/scripts/setup_github_protection.sh @security-team
/.git/hooks/ @security-team

# Documentation
/*.md @docs-team
/docs/ @docs-team
CODEOWNERS

    echo -e "${GREEN}✅ CODEOWNERS template created${NC}"
    echo "   Edit .github/CODEOWNERS to set actual team/user handles"
fi

echo ""
echo -e "${BLUE}🔍 Testing branch protection...${NC}"

# Test if direct push is blocked (this should fail)
echo "Testing if direct push is blocked..."
if git push origin "$BRANCH" --dry-run 2>&1 | grep -q "protected"; then
    echo -e "${GREEN}✅ Direct push correctly blocked${NC}"
else
    echo -e "${YELLOW}⚠️ Could not verify push protection (may need real push to test)${NC}"
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
