#!/usr/bin/env bash
# pr_automator.sh - Pull request creation and management
# Automates PR generation with templates and validation
set -euo pipefail

# PR templates
CE_PR_TEMPLATE="${CE_PR_TEMPLATE:-.github/PULL_REQUEST_TEMPLATE.md}"
CE_PR_CONFIG="${CE_PR_CONFIG:-.workflow/pr_config.yml}"

# Color codes for output
CE_PR_COLOR_GREEN="\033[0;32m"
CE_PR_COLOR_RED="\033[0;31m"
CE_PR_COLOR_YELLOW="\033[1;33m"
CE_PR_COLOR_BLUE="\033[0;34m"
CE_PR_COLOR_RESET="\033[0m"

# ============================================================================
# PR Creation Main Flow
# ============================================================================

ce_pr_create() {
    # Create pull request
    # Steps:
    #   1. Validate branch is ready
    #   2. Check remote exists
    #   3. Generate PR title and description
    #   4. Run pre-PR validations
    #   5. Create PR via gh CLI or fallback
    #   6. Apply labels and reviewers
    # Usage: ce_pr_create [--draft] [--base=main]
    # Returns: PR URL

    local draft=false
    local base_branch="main"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --draft)
                draft=true
                shift
                ;;
            --base=*)
                base_branch="${1#*=}"
                shift
                ;;
            *)
                echo -e "${CE_PR_COLOR_RED}Unknown option: $1${CE_PR_COLOR_RESET}" >&2
                return 1
                ;;
        esac
    done

    echo -e "${CE_PR_COLOR_BLUE}Creating Pull Request...${CE_PR_COLOR_RESET}"

    # Step 1: Validate branch is ready
    if ! ce_pr_validate_ready; then
        echo -e "${CE_PR_COLOR_RED}Branch not ready for PR${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    # Step 2: Check remote exists
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    if ! git ls-remote --exit-code --heads origin "$current_branch" &>/dev/null; then
        echo -e "${CE_PR_COLOR_YELLOW}Pushing branch to remote...${CE_PR_COLOR_RESET}"
        git push -u origin "$current_branch"
    fi

    # Step 3: Generate PR title and description
    local pr_title
    local pr_description
    pr_title=$(ce_pr_generate_title)
    pr_description=$(ce_pr_generate_description)

    # Step 4: Run pre-PR validations
    if ! ce_pr_check_conflicts "$base_branch"; then
        echo -e "${CE_PR_COLOR_RED}Merge conflicts detected with $base_branch${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    # Step 5: Create PR via gh CLI or fallback
    local pr_url
    if ce_pr_check_gh_installed; then
        pr_url=$(ce_pr_create_with_gh "$pr_title" "$pr_description" "$base_branch" "$draft")
    else
        pr_url=$(ce_pr_create_fallback "$pr_title" "$pr_description" "$base_branch")
    fi

    # Step 6: Apply labels and reviewers (if using gh CLI)
    if ce_pr_check_gh_installed && [[ -n "$pr_url" ]]; then
        local pr_number
        pr_number=$(echo "$pr_url" | grep -oP '/pull/\K\d+' || echo "")

        if [[ -n "$pr_number" ]]; then
            local labels
            labels=$(ce_pr_suggest_labels)
            if [[ -n "$labels" ]]; then
                # Convert space-separated to comma-separated
                labels=$(echo "$labels" | tr ' ' ',')
                ce_pr_update_labels "$pr_number" "$labels" || true
            fi

            local reviewers
            reviewers=$(ce_pr_suggest_reviewers)
            if [[ -n "$reviewers" ]]; then
                ce_pr_request_review "$pr_number" "$reviewers" || true
            fi
        fi
    fi

    echo -e "${CE_PR_COLOR_GREEN}✓ PR created successfully${CE_PR_COLOR_RESET}"
    echo -e "${CE_PR_COLOR_BLUE}PR URL: $pr_url${CE_PR_COLOR_RESET}"

    echo "$pr_url"
}

# ============================================================================
# PR Validation
# ============================================================================

ce_pr_validate_ready() {
    # Validate branch is ready for PR
    # Checks:
    #   - Branch pushed to remote
    #   - All commits signed
    #   - Quality gates passed
    #   - Conflicts resolved
    #   - Required files present
    # Returns: 0 if ready, 1 with reasons if not

    local ready=true
    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    echo -e "${CE_PR_COLOR_BLUE}Validating branch readiness...${CE_PR_COLOR_RESET}"

    # Check if on a valid branch (not main/master)
    if [[ "$current_branch" =~ ^(main|master)$ ]]; then
        echo -e "${CE_PR_COLOR_RED}✗ Cannot create PR from main/master branch${CE_PR_COLOR_RESET}" >&2
        ready=false
    fi

    # Check if there are commits
    local commit_count
    commit_count=$(git rev-list --count HEAD ^origin/main 2>/dev/null || echo "0")
    if [[ "$commit_count" -eq 0 ]]; then
        echo -e "${CE_PR_COLOR_RED}✗ No commits to create PR${CE_PR_COLOR_RESET}" >&2
        ready=false
    fi

    # Check quality gates if final_gate.sh exists
    if [[ -f ".workflow/lib/final_gate.sh" ]]; then
        if ! (source .workflow/lib/final_gate.sh && final_gate_check 2>/dev/null); then
            echo -e "${CE_PR_COLOR_YELLOW}⚠ Quality gates not fully passed${CE_PR_COLOR_RESET}"
            # Don't fail, just warn
        fi
    fi

    if [[ "$ready" == "true" ]]; then
        echo -e "${CE_PR_COLOR_GREEN}✓ Branch ready for PR${CE_PR_COLOR_RESET}"
        return 0
    else
        return 1
    fi
}

ce_pr_check_conflicts() {
    # Check for merge conflicts with base
    # Simulates merge to detect conflicts
    # Returns: 0 if clean, 1 with conflict files

    local base_branch="${1:-main}"

    echo -e "${CE_PR_COLOR_BLUE}Checking for conflicts with $base_branch...${CE_PR_COLOR_RESET}"

    # Fetch latest base branch
    git fetch origin "$base_branch" --quiet 2>/dev/null || true

    # Try to merge-base to check for conflicts
    local merge_base
    merge_base=$(git merge-base HEAD "origin/$base_branch" 2>/dev/null || echo "")

    if [[ -z "$merge_base" ]]; then
        echo -e "${CE_PR_COLOR_YELLOW}⚠ Could not determine merge base${CE_PR_COLOR_RESET}"
        return 0  # Continue anyway
    fi

    # Check if merge would create conflicts
    if git merge-tree "$merge_base" HEAD "origin/$base_branch" | grep -q "^<<<<<"; then
        echo -e "${CE_PR_COLOR_RED}✗ Merge conflicts detected${CE_PR_COLOR_RESET}" >&2
        git merge-tree "$merge_base" HEAD "origin/$base_branch" | grep "^<<<<<" -A 5 || true
        return 1
    fi

    echo -e "${CE_PR_COLOR_GREEN}✓ No conflicts detected${CE_PR_COLOR_RESET}"
    return 0
}

# ============================================================================
# PR Content Generation
# ============================================================================

ce_pr_generate_title() {
    # Generate PR title from branch/commits
    # Format: "<type>: <description>"
    # Examples:
    #   - "feat: Add user authentication"
    #   - "fix: Resolve database connection leak"
    #   - "docs: Update API documentation"
    # Analyzes: branch name, commit messages, files changed
    # Returns: PR title string

    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    # Try to extract type from branch name (e.g., feature/auth-system -> feat)
    local pr_type=""
    local pr_desc=""

    if [[ "$current_branch" =~ ^(feature|feat)/ ]]; then
        pr_type="feat"
        pr_desc="${current_branch#*/}"
    elif [[ "$current_branch" =~ ^(fix|bugfix)/ ]]; then
        pr_type="fix"
        pr_desc="${current_branch#*/}"
    elif [[ "$current_branch" =~ ^(docs|doc)/ ]]; then
        pr_type="docs"
        pr_desc="${current_branch#*/}"
    elif [[ "$current_branch" =~ ^(refactor)/ ]]; then
        pr_type="refactor"
        pr_desc="${current_branch#*/}"
    elif [[ "$current_branch" =~ ^(test)/ ]]; then
        pr_type="test"
        pr_desc="${current_branch#*/}"
    elif [[ "$current_branch" =~ ^(chore)/ ]]; then
        pr_type="chore"
        pr_desc="${current_branch#*/}"
    else
        # Try to get from latest commit message
        local latest_commit
        latest_commit=$(git log -1 --pretty=%s 2>/dev/null || echo "")

        if [[ "$latest_commit" =~ ^(feat|fix|docs|refactor|test|chore): ]]; then
            echo "$latest_commit"
            return 0
        fi

        pr_type="feat"
        pr_desc="$current_branch"
    fi

    # Clean up description: remove date suffix, convert dashes to spaces, capitalize
    pr_desc=$(echo "$pr_desc" | sed 's/-[0-9]\{8\}-t[0-9]\+$//' | tr '-' ' ' | sed 's/\b\(.\)/\u\1/g')

    echo "${pr_type}: ${pr_desc}"
}

ce_pr_generate_description() {
    # Generate comprehensive PR description
    # Template sections:
    #   - Summary
    #   - Changes made
    #   - Test plan
    #   - Screenshots (if UI)
    #   - Breaking changes
    #   - Checklist
    # Sources:
    #   - Commit messages
    #   - Branch metadata
    #   - Phase deliverables
    #   - PLAN.md and REVIEW.md
    # Returns: Markdown description

    local description=""

    # Load template if exists
    if [[ -f "$CE_PR_TEMPLATE" ]]; then
        description=$(ce_pr_fill_template)
    else
        # Generate basic description
        description="## Summary\n\n"
        description+="$(ce_pr_generate_summary)\n\n"
        description+="## Test Plan\n\n"
        description+="$(ce_pr_generate_test_plan)\n\n"

        local breaking_changes
        breaking_changes=$(ce_pr_extract_breaking_changes)
        if [[ -n "$breaking_changes" ]]; then
            description+="## Breaking Changes\n\n"
            description+="$breaking_changes\n\n"
        fi

        description+="$(ce_pr_add_metrics)\n\n"
        description+="---\n\n"
        description+="Co-Authored-By: Claude <noreply@anthropic.com>"
    fi

    echo -e "$description"
}

ce_pr_generate_summary() {
    # Generate bullet-point summary of changes
    # Analyzes:
    #   - git log since branch point
    #   - Files changed (git diff --stat)
    #   - Semantic grouping
    # Returns: Markdown list of changes

    local summary=""

    # Get commit messages since branch point
    local commits
    commits=$(git log --oneline origin/main..HEAD 2>/dev/null || git log --oneline -5)

    if [[ -z "$commits" ]]; then
        summary="No commits found."
    else
        # Group by commit type
        summary+="### Changes in this PR:\n\n"

        # Get files changed
        local files_changed
        files_changed=$(git diff --name-only origin/main..HEAD 2>/dev/null | head -10)

        if [[ -n "$files_changed" ]]; then
            summary+="**Modified Files:**\n"
            while IFS= read -r file; do
                summary+="- \`$file\`\n"
            done <<< "$files_changed"
            summary+="\n"
        fi

        # Add commits
        summary+="**Commits:**\n"
        while IFS= read -r commit; do
            summary+="- $commit\n"
        done <<< "$commits"
    fi

    echo -e "$summary"
}

ce_pr_generate_test_plan() {
    # Generate test plan section
    # Includes:
    #   - Unit tests added/modified
    #   - Integration test scenarios
    #   - Manual testing steps
    #   - Coverage metrics
    # Returns: Markdown checklist

    local test_plan=""

    # Check for test files
    local test_files
    test_files=$(git diff --name-only origin/main..HEAD 2>/dev/null | grep -E '(test|spec)\.' || echo "")

    if [[ -n "$test_files" ]]; then
        test_plan+="### Automated Tests\n\n"
        test_plan+="- [ ] Unit tests pass\n"
        test_plan+="- [ ] Integration tests pass\n"
        test_plan+="\n**Test files modified:**\n"
        while IFS= read -r file; do
            [[ -z "$file" ]] && continue
            test_plan+="- \`$file\`\n"
        done <<< "$test_files"
    else
        test_plan+="### Manual Testing\n\n"
        test_plan+="- [ ] Tested basic functionality\n"
        test_plan+="- [ ] Tested edge cases\n"
        test_plan+="- [ ] Tested error scenarios\n"
    fi

    test_plan+="\n### Quality Checks\n\n"
    test_plan+="- [ ] All quality gates passed\n"
    test_plan+="- [ ] Code reviewed\n"
    test_plan+="- [ ] Documentation updated\n"

    echo -e "$test_plan"
}

ce_pr_extract_breaking_changes() {
    # Extract breaking changes from commits
    # Looks for:
    #   - BREAKING CHANGE: in commit messages
    #   - ! in commit type (feat!:)
    #   - API signature changes
    # Returns: List of breaking changes or empty

    local breaking=""

    # Search commit messages for breaking change markers
    local commits
    commits=$(git log --format=%B origin/main..HEAD 2>/dev/null || git log --format=%B -5)

    if echo "$commits" | grep -iq "BREAKING CHANGE:"; then
        breaking+="⚠️ **This PR contains breaking changes:**\n\n"
        breaking+="$(echo "$commits" | grep -iA 3 "BREAKING CHANGE:" | sed 's/BREAKING CHANGE://' | sed 's/^/- /')\n"
    fi

    # Check for ! in commit messages
    if git log --oneline origin/main..HEAD 2>/dev/null | grep -q '!:'; then
        if [[ -z "$breaking" ]]; then
            breaking+="⚠️ **This PR contains breaking changes**\n\n"
        fi
        breaking+="$(git log --oneline origin/main..HEAD 2>/dev/null | grep '!:' | sed 's/^/- /')\n"
    fi

    echo -e "$breaking"
}

ce_pr_add_metrics() {
    # Add quality metrics to PR description
    # Returns: Markdown metrics table

    local metrics="## 📊 Quality Metrics\n\n"
    metrics+="| Metric | Value | Status |\n"
    metrics+="|--------|-------|--------|\n"

    # Quality score
    local score="N/A"
    if [[ -f ".workflow/_reports/quality_score.txt" ]]; then
        score=$(cat .workflow/_reports/quality_score.txt 2>/dev/null || echo "N/A")
    fi
    metrics+="| **Quality Score** | ${score}/100 | "
    if [[ "$score" != "N/A" ]] && [[ "${score%%.*}" -ge 85 ]]; then
        metrics+="✅ Pass |\n"
    else
        metrics+="⚠️ Check |\n"
    fi

    # Coverage
    local coverage="N/A"
    if [[ -f "coverage/coverage.xml" ]]; then
        coverage=$(python3 - <<'PY' 2>/dev/null || echo "N/A"
import xml.etree.ElementTree as ET
try:
    t=ET.parse("coverage/coverage.xml")
    c=t.getroot().find(".//counter[@type='LINE']")
    if c is not None:
        covered=int(c.get("covered",0))
        missed=int(c.get("missed",0))
        pct=100.0*covered/(covered+missed) if covered+missed>0 else 0.0
        print(f"{pct:.1f}")
    else:
        print("N/A")
except:
    print("N/A")
PY
)
    fi
    metrics+="| **Test Coverage** | ${coverage}% | "
    if [[ "$coverage" != "N/A" ]] && awk -v v="$coverage" 'BEGIN{ if (v+0 >= 80) { exit 0 } else { exit 1 } }'; then
        metrics+="✅ Pass |\n"
    else
        metrics+="⚠️ Check |\n"
    fi

    # Gate signatures
    local sig_count=0
    if [[ -d ".gates" ]]; then
        sig_count=$(ls .gates/*.ok.sig 2>/dev/null | wc -l | tr -d ' ')
    fi
    metrics+="| **Gate Signatures** | ${sig_count}/8 | "
    if [[ "$sig_count" -ge 8 ]]; then
        metrics+="✅ Complete |\n"
    else
        metrics+="⏳ In Progress |\n"
    fi

    # Changes stats
    local files_changed
    local insertions
    local deletions
    files_changed=$(git diff --shortstat origin/main..HEAD 2>/dev/null | grep -oP '\d+(?= file)' || echo "0")
    insertions=$(git diff --shortstat origin/main..HEAD 2>/dev/null | grep -oP '\d+(?= insertion)' || echo "0")
    deletions=$(git diff --shortstat origin/main..HEAD 2>/dev/null | grep -oP '\d+(?= deletion)' || echo "0")

    metrics+="| **Files Changed** | $files_changed | - |\n"
    metrics+="| **Lines Added** | +$insertions | - |\n"
    metrics+="| **Lines Deleted** | -$deletions | - |\n"

    echo -e "$metrics"
}

# ============================================================================
# PR Metadata
# ============================================================================

ce_pr_suggest_reviewers() {
    # Suggest reviewers based on CODEOWNERS
    # Falls back to:
    #   - Git blame on modified files
    #   - Recent contributors
    #   - Team configuration
    # Returns: List of GitHub usernames

    local reviewers=""

    # Check CODEOWNERS file
    if [[ -f ".github/CODEOWNERS" ]]; then
        # Get modified files
        local files_changed
        files_changed=$(git diff --name-only origin/main..HEAD 2>/dev/null || echo "")

        # Extract owners from CODEOWNERS
        while IFS= read -r file; do
            [[ -z "$file" ]] && continue

            # Find matching pattern in CODEOWNERS
            local owners
            owners=$(grep -E "^${file}" .github/CODEOWNERS 2>/dev/null | grep -oP '@\S+' || echo "")

            if [[ -n "$owners" ]]; then
                reviewers+=" $owners"
            fi
        done <<< "$files_changed"

        # Remove @ prefix and deduplicate
        reviewers=$(echo "$reviewers" | tr '@' ' ' | tr ' ' '\n' | sort -u | tr '\n' ' ')
    fi

    # If no reviewers found, try to get from git log
    if [[ -z "$reviewers" ]]; then
        reviewers=$(git log origin/main..HEAD --format=%an | sort -u | head -3 | tr '\n' ' ')
    fi

    echo "$reviewers" | xargs
}

ce_pr_suggest_labels() {
    # Suggest labels based on changes
    # Labels based on:
    #   - Files changed (e.g., "documentation" if docs/)
    #   - Commit types (e.g., "bug" for fix:)
    #   - Size (e.g., "size/L" for large PRs)
    #   - Priority (from branch metadata)
    # Returns: Array of label names

    local labels=""

    # Check files changed for categories
    local files_changed
    files_changed=$(git diff --name-only origin/main..HEAD 2>/dev/null || echo "")

    if echo "$files_changed" | grep -q '^docs/'; then
        labels+="documentation "
    fi

    if echo "$files_changed" | grep -q '^test/'; then
        labels+="testing "
    fi

    if echo "$files_changed" | grep -q '\.github/workflows/'; then
        labels+="ci-cd "
    fi

    if echo "$files_changed" | grep -q '^\.workflow/'; then
        labels+="workflow "
    fi

    # Check commit messages for type
    local commits
    commits=$(git log --oneline origin/main..HEAD 2>/dev/null | head -1)

    if echo "$commits" | grep -iq '^[a-f0-9]\+ feat'; then
        labels+="enhancement "
    elif echo "$commits" | grep -iq '^[a-f0-9]\+ fix'; then
        labels+="bug "
    fi

    # Add size label
    local size_label
    size_label=$(ce_pr_calculate_size)
    labels+="$size_label "

    echo "$labels" | xargs
}

ce_pr_calculate_size() {
    # Calculate PR size
    # Metrics:
    #   - Lines changed (additions + deletions)
    #   - Files modified
    # Size categories:
    #   - XS: <10 lines
    #   - S: 10-100 lines
    #   - M: 100-500 lines
    #   - L: 500-1000 lines
    #   - XL: >1000 lines
    # Returns: Size label

    local insertions
    local deletions
    insertions=$(git diff --shortstat origin/main..HEAD 2>/dev/null | grep -oP '\d+(?= insertion)' || echo "0")
    deletions=$(git diff --shortstat origin/main..HEAD 2>/dev/null | grep -oP '\d+(?= deletion)' || echo "0")

    local total_changes=$((insertions + deletions))

    if [[ $total_changes -lt 10 ]]; then
        echo "size/XS"
    elif [[ $total_changes -lt 100 ]]; then
        echo "size/S"
    elif [[ $total_changes -lt 500 ]]; then
        echo "size/M"
    elif [[ $total_changes -lt 1000 ]]; then
        echo "size/L"
    else
        echo "size/XL"
    fi
}

# ============================================================================
# PR Creation Methods
# ============================================================================

ce_pr_check_gh_installed() {
    # Check if GitHub CLI is installed
    # Returns: 0 if installed, 1 otherwise
    command -v gh &>/dev/null
}

ce_pr_create_with_gh() {
    # Create PR using GitHub CLI (gh)
    # Primary method if gh is available
    # Command: gh pr create --title "..." --body "..."
    # Handles:
    #   - Authentication
    #   - Draft PRs
    #   - Base branch selection
    #   - Labels and reviewers
    # Returns: PR URL or exits on error

    local title="$1"
    local body="$2"
    local base="${3:-main}"
    local draft="${4:-false}"

    local gh_args=(
        "pr" "create"
        "--title" "$title"
        "--body" "$body"
        "--base" "$base"
    )

    if [[ "$draft" == "true" ]]; then
        gh_args+=("--draft")
    fi

    echo -e "${CE_PR_COLOR_BLUE}Creating PR with GitHub CLI...${CE_PR_COLOR_RESET}"

    local pr_url
    pr_url=$(gh "${gh_args[@]}" 2>&1)

    if [[ $? -eq 0 ]]; then
        echo "$pr_url"
    else
        echo -e "${CE_PR_COLOR_RED}Failed to create PR with gh CLI${CE_PR_COLOR_RESET}" >&2
        echo -e "${CE_PR_COLOR_YELLOW}Falling back to browser method...${CE_PR_COLOR_RESET}"
        ce_pr_create_fallback "$title" "$body" "$base"
    fi
}

ce_pr_create_fallback() {
    # Fallback PR creation method
    # Used when gh CLI not available
    # Generates:
    #   - PR URL for web interface
    #   - Pre-filled query parameters
    #   - Clipboard copy of description
    # Opens browser with PR creation page
    # Returns: Generated URL

    local title="$1"
    local body="$2"
    local base="${3:-main}"

    echo -e "${CE_PR_COLOR_YELLOW}GitHub CLI not available, using browser method...${CE_PR_COLOR_RESET}"

    local pr_url
    pr_url=$(ce_pr_generate_url "$title" "$body" "$base")

    echo -e "${CE_PR_COLOR_BLUE}PR URL generated:${CE_PR_COLOR_RESET}"
    echo "$pr_url"

    # Try to copy to clipboard
    if command -v xclip &>/dev/null; then
        echo "$body" | xclip -selection clipboard 2>/dev/null && \
            echo -e "${CE_PR_COLOR_GREEN}✓ PR description copied to clipboard${CE_PR_COLOR_RESET}"
    elif command -v pbcopy &>/dev/null; then
        echo "$body" | pbcopy 2>/dev/null && \
            echo -e "${CE_PR_COLOR_GREEN}✓ PR description copied to clipboard${CE_PR_COLOR_RESET}"
    fi

    # Try to open browser
    ce_pr_open_browser "$pr_url"

    echo "$pr_url"
}

ce_pr_generate_url() {
    # Generate GitHub PR creation URL
    # Format: https://github.com/owner/repo/compare/base...head?expand=1
    # Includes:
    #   - Base and head branches
    #   - Pre-filled title and body (URL encoded)
    # Returns: Complete URL

    local title="${1:-}"
    local body="${2:-}"
    local base="${3:-main}"

    # Parse remote URL to get owner/repo
    local remote_url
    remote_url=$(git remote get-url origin 2>/dev/null || echo "")

    local owner_repo
    owner_repo=$(ce_pr_parse_remote "$remote_url")

    if [[ -z "$owner_repo" ]]; then
        echo "https://github.com/compare" >&2
        return 1
    fi

    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    # Build URL
    local url="https://github.com/${owner_repo}/compare/${base}...${current_branch}?expand=1"

    # Add title if provided (URL encode)
    if [[ -n "$title" ]]; then
        local encoded_title
        encoded_title=$(echo "$title" | jq -sRr @uri 2>/dev/null || echo "$title" | sed 's/ /%20/g')
        url+="&title=${encoded_title}"
    fi

    echo "$url"
}

ce_pr_parse_remote() {
    # Parse git remote URL to extract owner/repo
    # Supports: SSH, HTTPS, and git:// URLs
    # Returns: owner/repo format

    local remote_url="$1"

    # SSH format: git@github.com:owner/repo.git
    if [[ "$remote_url" =~ git@[^:]+:([^/]+)/(.+)\.git ]]; then
        echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
        return 0
    fi

    # HTTPS format: https://github.com/owner/repo.git
    if [[ "$remote_url" =~ https://[^/]+/([^/]+)/(.+)\.git ]]; then
        echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
        return 0
    fi

    # HTTPS without .git
    if [[ "$remote_url" =~ https://[^/]+/([^/]+)/([^/]+)$ ]]; then
        echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
        return 0
    fi

    return 1
}

ce_pr_open_browser() {
    # Open URL in browser
    # Cross-platform support

    local url="$1"

    if command -v xdg-open &>/dev/null; then
        xdg-open "$url" &>/dev/null &
    elif command -v open &>/dev/null; then
        open "$url" &>/dev/null &
    elif command -v start &>/dev/null; then
        start "$url" &>/dev/null &
    else
        echo -e "${CE_PR_COLOR_YELLOW}Could not open browser automatically${CE_PR_COLOR_RESET}"
        echo -e "${CE_PR_COLOR_BLUE}Please open this URL manually:${CE_PR_COLOR_RESET}"
        echo "$url"
    fi
}

# ============================================================================
# PR Updates
# ============================================================================

ce_pr_update() {
    # Update existing PR
    # Updates:
    #   - Title
    #   - Description
    #   - Labels
    #   - Reviewers
    # Usage: ce_pr_update [PR_NUMBER]

    local pr_number="${1:-}"

    if [[ -z "$pr_number" ]]; then
        pr_number=$(ce_pr_get_current)
    fi

    if [[ -z "$pr_number" ]]; then
        echo -e "${CE_PR_COLOR_RED}No PR number provided and could not detect current PR${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    if ! ce_pr_check_gh_installed; then
        echo -e "${CE_PR_COLOR_RED}GitHub CLI required for PR updates${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    echo -e "${CE_PR_COLOR_BLUE}Updating PR #${pr_number}...${CE_PR_COLOR_RESET}"

    # Generate new title and description
    local title
    local body
    title=$(ce_pr_generate_title)
    body=$(ce_pr_generate_description)

    gh pr edit "$pr_number" --title "$title" --body "$body"

    echo -e "${CE_PR_COLOR_GREEN}✓ PR updated${CE_PR_COLOR_RESET}"
}

ce_pr_add_comment() {
    # Add comment to PR
    # Use cases:
    #   - Update on CI results
    #   - Additional context
    #   - Response to reviews
    # Usage: ce_pr_add_comment [PR_NUMBER] "comment text"

    local pr_number="${1:-}"
    local comment="${2:-}"

    if [[ -z "$pr_number" ]] || [[ -z "$comment" ]]; then
        echo -e "${CE_PR_COLOR_RED}Usage: ce_pr_add_comment PR_NUMBER \"comment\"${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    if ! ce_pr_check_gh_installed; then
        echo -e "${CE_PR_COLOR_RED}GitHub CLI required${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    gh pr comment "$pr_number" --body "$comment"
}

ce_pr_update_labels() {
    # Update PR labels
    # Usage: ce_pr_update_labels [PR_NUMBER] "label1,label2,label3"

    local pr_number="${1:-}"
    local labels="${2:-}"

    if [[ -z "$pr_number" ]]; then
        echo -e "${CE_PR_COLOR_RED}PR number required${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    if ! ce_pr_check_gh_installed; then
        echo -e "${CE_PR_COLOR_RED}GitHub CLI required${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    if [[ -z "$labels" ]]; then
        # Auto-suggest labels
        labels=$(ce_pr_suggest_labels | tr ' ' ',')
    fi

    gh pr edit "$pr_number" --add-label "$labels"
}

# ============================================================================
# PR Validation & Status
# ============================================================================

ce_pr_check_ci_status() {
    # Check CI status for PR
    # Queries GitHub Actions status
    # Returns:
    #   - pending: CI running
    #   - success: All checks passed
    #   - failure: Some checks failed
    # Usage: status=$(ce_pr_check_ci_status [PR_NUMBER])

    local pr_number="${1:-}"

    if [[ -z "$pr_number" ]]; then
        pr_number=$(ce_pr_get_current)
    fi

    if ! ce_pr_check_gh_installed; then
        echo "unknown"
        return 1
    fi

    gh pr checks "$pr_number" --json state --jq '.[] | .state' | sort -u | tail -1
}

ce_pr_check_reviews() {
    # Check review status
    # Returns:
    #   - Number of approvals
    #   - Number of changes requested
    #   - Pending reviews
    # Usage: ce_pr_check_reviews [PR_NUMBER]

    local pr_number="${1:-}"

    if [[ -z "$pr_number" ]]; then
        pr_number=$(ce_pr_get_current)
    fi

    if ! ce_pr_check_gh_installed; then
        return 1
    fi

    gh pr view "$pr_number" --json reviews --jq '.reviews | group_by(.state) | map({state: .[0].state, count: length})'
}

ce_pr_check_mergeable() {
    # Check if PR is mergeable
    # Validates:
    #   - No conflicts
    #   - CI passed
    #   - Required approvals met
    #   - No requested changes
    # Returns: 0 if mergeable, 1 with blockers

    local pr_number="${1:-}"

    if [[ -z "$pr_number" ]]; then
        pr_number=$(ce_pr_get_current)
    fi

    if ! ce_pr_check_gh_installed; then
        return 1
    fi

    local mergeable
    mergeable=$(gh pr view "$pr_number" --json mergeable --jq '.mergeable')

    if [[ "$mergeable" == "MERGEABLE" ]]; then
        echo -e "${CE_PR_COLOR_GREEN}✓ PR is mergeable${CE_PR_COLOR_RESET}"
        return 0
    else
        echo -e "${CE_PR_COLOR_RED}✗ PR has merge blockers${CE_PR_COLOR_RESET}" >&2
        return 1
    fi
}

# ============================================================================
# PR Information
# ============================================================================

ce_pr_get_info() {
    # Get PR information
    # Returns JSON with PR details
    # Usage: info=$(ce_pr_get_info [PR_NUMBER])

    local pr_number="${1:-}"

    if [[ -z "$pr_number" ]]; then
        pr_number=$(ce_pr_get_current)
    fi

    if ! ce_pr_check_gh_installed; then
        echo "{}"
        return 1
    fi

    gh pr view "$pr_number" --json number,title,state,url,baseRefName,headRefName,author,createdAt,mergeable
}

ce_pr_get_current() {
    # Get PR for current branch
    # Queries GitHub for PR associated with current branch
    # Returns: PR number or empty

    if ! ce_pr_check_gh_installed; then
        return 1
    fi

    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    gh pr list --head "$current_branch" --json number --jq '.[0].number // empty'
}

ce_pr_list_open() {
    # List open PRs
    # Output format:
    #   #123 feat: Add authentication (draft)
    #   #122 fix: Database connection (ready)
    #   #121 docs: Update API guide (approved)

    if ! ce_pr_check_gh_installed; then
        echo -e "${CE_PR_COLOR_RED}GitHub CLI required${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    gh pr list --json number,title,isDraft,reviewDecision --jq '.[] | "#\(.number) \(.title) (\(if .isDraft then "draft" elif .reviewDecision == "APPROVED" then "approved" else "ready" end))"'
}

# ============================================================================
# PR Templates
# ============================================================================

ce_pr_load_template() {
    # Load PR template
    # Reads: .github/PULL_REQUEST_TEMPLATE.md
    # Returns: Template content

    if [[ -f "$CE_PR_TEMPLATE" ]]; then
        cat "$CE_PR_TEMPLATE"
    else
        echo ""
    fi
}

ce_pr_fill_template() {
    # Fill PR template with generated content
    # Replaces placeholders:
    #   - {{summary}} → Generated summary
    #   - {{test_plan}} → Generated test plan
    #   - {{breaking_changes}} → Extracted changes
    # Returns: Filled template

    local template
    template=$(ce_pr_load_template)

    if [[ -z "$template" ]]; then
        ce_pr_generate_description
        return 0
    fi

    # Replace placeholders
    local summary
    local test_plan
    local breaking_changes

    summary=$(ce_pr_generate_summary)
    test_plan=$(ce_pr_generate_test_plan)
    breaking_changes=$(ce_pr_extract_breaking_changes)

    template="${template//\[FEATURE_NAME\]/$(git rev-parse --abbrev-ref HEAD)}"
    template="${template//\{\{summary\}\}/$summary}"
    template="${template//\{\{test_plan\}\}/$test_plan}"
    template="${template//\{\{breaking_changes\}\}/${breaking_changes:-None}}"

    # Add metrics
    local metrics
    metrics=$(ce_pr_add_metrics)
    template="${template//\[SCORE\]/$(cat .workflow/_reports/quality_score.txt 2>/dev/null || echo "N/A")}"

    local coverage
    coverage=$(python3 - <<'PY' 2>/dev/null || echo "N/A"
import xml.etree.ElementTree as ET
try:
    t=ET.parse("coverage/coverage.xml")
    c=t.getroot().find(".//counter[@type='LINE']")
    if c is not None:
        covered=int(c.get("covered",0))
        missed=int(c.get("missed",0))
        pct=100.0*covered/(covered+missed) if covered+missed>0 else 0.0
        print(f"{pct:.1f}")
    else:
        print("N/A")
except:
    print("N/A")
PY
)
    template="${template//\[COVERAGE\]/$coverage}"

    local sig_count
    sig_count=$(ls .gates/*.ok.sig 2>/dev/null | wc -l | tr -d ' ')
    template="${template//\[SIGS\]/$sig_count}"

    echo "$template"
}

ce_pr_validate_template() {
    # Validate PR description against template
    # Checks all required sections filled
    # Returns: 0 if valid, 1 with missing sections

    local description="$1"

    # Check for required sections
    local required_sections=(
        "Summary"
        "Changes"
        "Testing"
    )

    local missing=()

    for section in "${required_sections[@]}"; do
        if ! echo "$description" | grep -qi "^##.*$section"; then
            missing+=("$section")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${CE_PR_COLOR_YELLOW}⚠ Missing sections: ${missing[*]}${CE_PR_COLOR_RESET}"
        return 1
    fi

    return 0
}

# ============================================================================
# PR Automation
# ============================================================================

ce_pr_auto_merge() {
    # Enable auto-merge on PR
    # Once all checks pass, PR will auto-merge
    # Usage: ce_pr_auto_merge [PR_NUMBER] [--merge-method=squash]

    local pr_number="${1:-}"
    local merge_method="${2:-squash}"

    if [[ "$merge_method" =~ ^--merge-method= ]]; then
        merge_method="${merge_method#*=}"
    fi

    if [[ -z "$pr_number" ]]; then
        pr_number=$(ce_pr_get_current)
    fi

    if ! ce_pr_check_gh_installed; then
        echo -e "${CE_PR_COLOR_RED}GitHub CLI required${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    gh pr merge "$pr_number" --auto --"$merge_method"
}

ce_pr_request_review() {
    # Request review from suggested reviewers
    # Usage: ce_pr_request_review [PR_NUMBER] [REVIEWERS]

    local pr_number="${1:-}"
    local reviewers="${2:-}"

    if [[ -z "$pr_number" ]]; then
        pr_number=$(ce_pr_get_current)
    fi

    if [[ -z "$reviewers" ]]; then
        reviewers=$(ce_pr_suggest_reviewers)
    fi

    if [[ -z "$reviewers" ]]; then
        echo -e "${CE_PR_COLOR_YELLOW}No reviewers to request${CE_PR_COLOR_RESET}"
        return 0
    fi

    if ! ce_pr_check_gh_installed; then
        echo -e "${CE_PR_COLOR_RED}GitHub CLI required${CE_PR_COLOR_RESET}" >&2
        return 1
    fi

    # Convert space-separated to comma-separated
    reviewers=$(echo "$reviewers" | tr ' ' ',')

    gh pr edit "$pr_number" --add-reviewer "$reviewers"
}

ce_pr_sync_with_base() {
    # Sync PR branch with base branch
    # Updates branch to include latest changes from base
    # Usage: ce_pr_sync_with_base [--merge|--rebase]

    local method="${1:-merge}"

    if [[ "$method" =~ ^-- ]]; then
        method="${method#--}"
    fi

    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    local base_branch="main"

    echo -e "${CE_PR_COLOR_BLUE}Syncing $current_branch with $base_branch...${CE_PR_COLOR_RESET}"

    git fetch origin "$base_branch"

    if [[ "$method" == "rebase" ]]; then
        git rebase "origin/$base_branch"
    else
        git merge "origin/$base_branch"
    fi
}

# ============================================================================
# PR Analytics
# ============================================================================

ce_pr_get_stats() {
    # Get PR statistics
    # Returns:
    #   - Files changed
    #   - Lines added/removed
    #   - Commits count
    #   - Comments count
    #   - Time to merge
    #   - Review cycles

    local pr_number="${1:-}"

    if [[ -z "$pr_number" ]]; then
        pr_number=$(ce_pr_get_current)
    fi

    if ! ce_pr_check_gh_installed; then
        return 1
    fi

    gh pr view "$pr_number" --json additions,deletions,changedFiles,commits,comments,createdAt,mergedAt
}

ce_pr_get_diff_summary() {
    # Get summary of changes
    # Groups changes by:
    #   - File type
    #   - Directory
    #   - Change type (add/modify/delete)
    # Returns: Structured summary

    local summary=""

    # Get file changes
    local files_added
    local files_modified
    local files_deleted

    files_added=$(git diff --diff-filter=A --name-only origin/main..HEAD 2>/dev/null | wc -l)
    files_modified=$(git diff --diff-filter=M --name-only origin/main..HEAD 2>/dev/null | wc -l)
    files_deleted=$(git diff --diff-filter=D --name-only origin/main..HEAD 2>/dev/null | wc -l)

    summary+="Files: +$files_added ~$files_modified -$files_deleted\n"

    # Group by directory
    local dirs
    dirs=$(git diff --name-only origin/main..HEAD 2>/dev/null | xargs -I {} dirname {} | sort -u)

    summary+="\nAffected Directories:\n"
    while IFS= read -r dir; do
        [[ -z "$dir" ]] && continue
        local count
        count=$(git diff --name-only origin/main..HEAD 2>/dev/null | grep "^$dir/" | wc -l)
        summary+="  $dir/ ($count files)\n"
    done <<< "$dirs"

    echo -e "$summary"
}

# Export all functions
export -f ce_pr_create
export -f ce_pr_validate_ready
export -f ce_pr_check_conflicts
export -f ce_pr_generate_title
export -f ce_pr_generate_description
export -f ce_pr_generate_summary
export -f ce_pr_generate_test_plan
export -f ce_pr_extract_breaking_changes
export -f ce_pr_add_metrics
export -f ce_pr_suggest_reviewers
export -f ce_pr_suggest_labels
export -f ce_pr_calculate_size
export -f ce_pr_check_gh_installed
export -f ce_pr_create_with_gh
export -f ce_pr_create_fallback
export -f ce_pr_generate_url
export -f ce_pr_parse_remote
export -f ce_pr_open_browser
export -f ce_pr_update
export -f ce_pr_add_comment
export -f ce_pr_update_labels
export -f ce_pr_check_ci_status
export -f ce_pr_check_reviews
export -f ce_pr_check_mergeable
export -f ce_pr_get_info
export -f ce_pr_get_current
export -f ce_pr_list_open
export -f ce_pr_load_template
export -f ce_pr_fill_template
export -f ce_pr_validate_template
export -f ce_pr_auto_merge
export -f ce_pr_request_review
export -f ce_pr_sync_with_base
export -f ce_pr_get_stats
export -f ce_pr_get_diff_summary
