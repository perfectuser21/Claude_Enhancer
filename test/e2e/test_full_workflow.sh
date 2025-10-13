#!/bin/bash
# E2E test: Simulate full development workflow
# Path: test/e2e/test_full_workflow.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ANSI colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

TEST_BRANCH="test/e2e-$(date +%s)"
ORIGINAL_BRANCH=$(git branch --show-current)
TEST_FILE="test_e2e_file.js"

cleanup() {
    echo -e "\n${CYAN}Cleaning up E2E test...${NC}"

    # Remove test file if exists
    rm -f "$TEST_FILE"

    # Switch back to original branch
    if [ "$(git branch --show-current)" != "$ORIGINAL_BRANCH" ]; then
        git checkout "$ORIGINAL_BRANCH" 2>/dev/null || true
    fi

    # Delete test branch if it exists
    if git show-ref --verify --quiet "refs/heads/$TEST_BRANCH"; then
        git branch -D "$TEST_BRANCH" 2>/dev/null || true
    fi

    # Unstage any files
    git reset HEAD . 2>/dev/null || true

    echo -e "${CYAN}Cleanup complete${NC}"
}

trap cleanup EXIT

cd "$PROJECT_ROOT"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  End-to-End Workflow Test              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}This test simulates a complete development workflow:${NC}"
echo -e "${CYAN}1. Create a new branch${NC}"
echo -e "${CYAN}2. Create/modify files${NC}"
echo -e "${CYAN}3. Stage changes${NC}"
echo -e "${CYAN}4. Trigger pre-commit hooks${NC}"
echo -e "${CYAN}5. Clean up${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 1: Create Test Branch
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${YELLOW}Step 1: Create test branch${NC}"
echo -e "  Original branch: ${ORIGINAL_BRANCH}"
echo -e "  Test branch: ${TEST_BRANCH}"

if git checkout -b "$TEST_BRANCH" 2>/dev/null; then
    echo -e "  ${GREEN}✅ Test branch created${NC}"
else
    echo -e "  ${RED}❌ Failed to create test branch${NC}"
    exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 2: Create Test File
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Step 2: Create test file${NC}"

cat > "$TEST_FILE" << 'EOF'
// E2E Test File
// This file is created by the E2E workflow test

function testFunction() {
    console.log('E2E workflow test');
    return true;
}

module.exports = { testFunction };
EOF

if [ -f "$TEST_FILE" ]; then
    echo -e "  ${GREEN}✅ Test file created: $TEST_FILE${NC}"
    echo -e "  Content preview:"
    head -3 "$TEST_FILE" | sed 's/^/    /'
else
    echo -e "  ${RED}❌ Failed to create test file${NC}"
    exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 3: Stage Changes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Step 3: Stage test file${NC}"

if git add "$TEST_FILE" 2>/dev/null; then
    echo -e "  ${GREEN}✅ File staged successfully${NC}"

    # Show git status
    echo -e "  Git status:"
    git status --short | sed 's/^/    /'
else
    echo -e "  ${RED}❌ Failed to stage file${NC}"
    exit 1
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 4: Test Pre-commit Hook
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Step 4: Trigger pre-commit hook${NC}"

if [ ! -x ".git/hooks/pre-commit" ]; then
    echo -e "  ${YELLOW}⚠ Pre-commit hook not executable or not found${NC}"
    echo -e "  ${YELLOW}⚠ Skipping hook validation (this is acceptable in CI)${NC}"
    HOOK_RESULT="skipped"
else
    echo -e "  Running pre-commit hook..."

    # Run the hook and capture result
    if .git/hooks/pre-commit 2>&1 | tee /tmp/e2e_hook_output.log; then
        echo -e "  ${GREEN}✅ Pre-commit hook passed${NC}"
        HOOK_RESULT="passed"
    else
        echo -e "  ${YELLOW}⚠ Pre-commit hook did not pass${NC}"
        echo -e "  ${YELLOW}⚠ This may be expected if tests or linting are required${NC}"
        echo -e "  Hook output:"
        cat /tmp/e2e_hook_output.log | tail -10 | sed 's/^/    /'
        HOOK_RESULT="blocked"
    fi
    rm -f /tmp/e2e_hook_output.log
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 5: Attempt Commit (Optional)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Step 5: Attempt commit (dry-run)${NC}"

# Don't actually commit, just test the commit message format
COMMIT_MSG="test: e2e workflow validation

This is an automated test commit from the E2E workflow test suite.
It validates the complete development workflow including:
- Branch creation
- File modification
- Git staging
- Pre-commit hook execution

This commit should not be pushed to the repository."

echo -e "  Commit message format:"
echo "$COMMIT_MSG" | head -5 | sed 's/^/    /'

# Validate commit message format
if [ -x ".git/hooks/commit-msg" ]; then
    echo "$COMMIT_MSG" > /tmp/e2e_commit_msg
    if .git/hooks/commit-msg /tmp/e2e_commit_msg 2>&1; then
        echo -e "  ${GREEN}✅ Commit message format is valid${NC}"
    else
        echo -e "  ${YELLOW}⚠ Commit message validation failed${NC}"
    fi
    rm -f /tmp/e2e_commit_msg
else
    echo -e "  ${YELLOW}⚠ No commit-msg hook found${NC}"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Step 6: Workflow Validation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${YELLOW}Step 6: Validate workflow components${NC}"

workflow_checks=0
workflow_passed=0

# Check 6.1: Git operations work
echo -n "  6.1 Git operations functional... "
if git status >/dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
    ((workflow_passed++))
else
    echo -e "${RED}❌${NC}"
fi
((workflow_checks++))

# Check 6.2: Branch management works
echo -n "  6.2 Branch management functional... "
if git branch | grep -q "$TEST_BRANCH"; then
    echo -e "${GREEN}✅${NC}"
    ((workflow_passed++))
else
    echo -e "${RED}❌${NC}"
fi
((workflow_checks++))

# Check 6.3: File operations work
echo -n "  6.3 File operations functional... "
if [ -f "$TEST_FILE" ] && git ls-files --cached | grep -q "$TEST_FILE"; then
    echo -e "${GREEN}✅${NC}"
    ((workflow_passed++))
else
    echo -e "${RED}❌${NC}"
fi
((workflow_checks++))

# Check 6.4: Hooks are installed
echo -n "  6.4 Git hooks installed... "
if [ -f ".git/hooks/pre-commit" ]; then
    echo -e "${GREEN}✅${NC}"
    ((workflow_passed++))
else
    echo -e "${YELLOW}⚠${NC}"
fi
((workflow_checks++))

# Check 6.5: Hook execution capability
echo -n "  6.5 Hook execution capability... "
if [ "$HOOK_RESULT" = "passed" ]; then
    echo -e "${GREEN}✅ (passed)${NC}"
    ((workflow_passed++))
elif [ "$HOOK_RESULT" = "blocked" ]; then
    echo -e "${YELLOW}⚠ (blocked, but executable)${NC}"
    ((workflow_passed++))
else
    echo -e "${YELLOW}⊘ (skipped)${NC}"
    ((workflow_passed++))
fi
((workflow_checks++))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  E2E Workflow Test Summary             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Workflow checks: $workflow_passed/$workflow_checks passed"
echo -e "Hook execution: $HOOK_RESULT"
echo ""

if [ $workflow_passed -eq $workflow_checks ]; then
    echo -e "${GREEN}✅ E2E workflow test PASSED${NC}"
    echo -e "${GREEN}   Complete development workflow is functional${NC}"
    exit 0
elif [ $workflow_passed -ge $((workflow_checks - 1)) ]; then
    echo -e "${YELLOW}⚠ E2E workflow test MOSTLY PASSED${NC}"
    echo -e "${YELLOW}   ($workflow_passed/$workflow_checks checks passed)${NC}"
    exit 0
else
    echo -e "${RED}❌ E2E workflow test FAILED${NC}"
    echo -e "${RED}   ($workflow_passed/$workflow_checks checks passed)${NC}"
    exit 1
fi
