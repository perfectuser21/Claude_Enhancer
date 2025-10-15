#!/bin/bash
# Claude Enhancer Agent Usage Enforcer
# Validates 4-6-8 Agent strategy based on task complexity
# Version: 1.0.0

# ============================================================================
# SECTION 1: Setup and Configuration
# ============================================================================

# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi

set -euo pipefail

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Logging
LOG_FILE="$PROJECT_ROOT/.workflow/logs/claude_hooks.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "$(date +'%F %T') [agent_usage_enforcer.sh] triggered" >> "$LOG_FILE"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fast lane patterns (skip validation)
FAST_LANE_PATTERNS=(
    "^docs/.*\.md$"      # Documentation only
    "^README\.md$"       # README updates
    "^\.github/.*\.md$"  # GitHub docs
    "^CHANGELOG\.md$"    # Changelog updates
)

# ============================================================================
# SECTION 2: Fast Lane Detection
# ============================================================================

is_fast_lane() {
    # Check if changes are trivial (docs-only, <10 lines)
    local changed_files
    changed_files=$(git diff --cached --name-only 2>/dev/null || echo "")

    if [[ -z "$changed_files" ]]; then
        return 0  # No changes = fast lane
    fi

    # Check file count
    local file_count
    file_count=$(echo "$changed_files" | wc -l)

    if [ "$file_count" -le 2 ]; then
        # Check if all files match fast lane patterns
        local all_match=true
        while IFS= read -r file; do
            local matches=false
            for pattern in "${FAST_LANE_PATTERNS[@]}"; do
                if [[ "$file" =~ $pattern ]]; then
                    matches=true
                    break
                fi
            done
            if ! $matches; then
                all_match=false
                break
            fi
        done <<< "$changed_files"

        if $all_match; then
            echo "⚡ Fast lane: Documentation-only changes" >> "$LOG_FILE"
            return 0
        fi
    fi

    # Check line count
    local lines_changed
    lines_changed=$(git diff --cached --numstat 2>/dev/null | awk '{sum+=$1+$2} END {print sum}' || echo "0")

    if [ "$lines_changed" -le 10 ]; then
        echo "⚡ Fast lane: Trivial changes (<10 lines)" >> "$LOG_FILE"
        return 0
    fi

    return 1  # Not fast lane
}

# ============================================================================
# SECTION 3: Complexity Calculation
# ============================================================================

calculate_complexity() {
    # Calculate task complexity based on git diff

    # Metric 1: Files changed
    local files_changed
    files_changed=$(git diff --cached --name-only 2>/dev/null | wc -l || echo "0")

    # Metric 2: Lines changed (insertions + deletions)
    local lines_changed
    lines_changed=$(git diff --cached --numstat 2>/dev/null | awk '{sum+=$1+$2} END {print sum+0}')

    # Metric 3: Architecture changes
    local has_architecture="no"
    if git diff --cached --name-only | grep -qE '(core/|modules/|architecture/|\.claude/)'; then
        has_architecture="yes"
    fi

    # Metric 4: Test file changes
    local has_tests="no"
    if git diff --cached --name-only | grep -qE '(test_|_test\.|tests/|spec/)'; then
        has_tests="yes"
    fi

    # Metric 5: Configuration changes
    local has_config="no"
    if git diff --cached --name-only | grep -qE '\.(yml|yaml|json|toml|ini)$'; then
        has_config="yes"
    fi

    # Log metrics
    echo "  files_changed=$files_changed" >> "$LOG_FILE"
    echo "  lines_changed=$lines_changed" >> "$LOG_FILE"
    echo "  has_architecture=$has_architecture" >> "$LOG_FILE"
    echo "  has_tests=$has_tests" >> "$LOG_FILE"
    echo "  has_config=$has_config" >> "$LOG_FILE"

    # Return as JSON-like string for parsing
    echo "$files_changed|$lines_changed|$has_architecture|$has_tests|$has_config"
}

determine_tier() {
    local metrics="$1"

    # Parse metrics
    IFS='|' read -r files lines arch tests config <<< "$metrics"

    # Decision matrix for complexity tier
    local tier="simple"
    local required=4

    # Simple: ≤3 files, ≤100 lines, no architecture, maybe tests
    if [ "$files" -le 3 ] && [ "$lines" -le 100 ] && [ "$arch" = "no" ]; then
        tier="simple"
        required=4

    # Standard: 4-10 files, 101-500 lines, OR has tests + config
    elif [ "$files" -le 10 ] && [ "$lines" -le 500 ]; then
        tier="standard"
        required=6

    # Complex: >10 files, >500 lines, OR has architecture changes
    else
        tier="complex"
        required=8
    fi

    # Architecture changes always bump to at least standard
    if [ "$arch" = "yes" ] && [ "$tier" = "simple" ]; then
        tier="standard"
        required=6
    fi

    # Architecture + many files = complex
    if [ "$arch" = "yes" ] && [ "$files" -gt 10 ]; then
        tier="complex"
        required=8
    fi

    echo "$tier|$required"
}

# ============================================================================
# SECTION 4: Agent Count Validation
# ============================================================================

get_agent_count() {
    # Try multiple evidence file patterns
    local evidence_file=""

    # Pattern 1: Standard invocation file
    if [[ -f ".gates/agents_invocation.json" ]]; then
        evidence_file=".gates/agents_invocation.json"
    # Pattern 2: Phase-specific gate files
    elif [[ -f ".gates/03.ok" ]]; then  # P3 gate
        # Parse agent count from gate file if it contains agent info
        local count
        count=$(grep -oP 'agents?:\s*\K\d+' ".gates/03.ok" 2>/dev/null || echo "0")
        echo "$count"
        return 0
    fi

    if [[ -z "$evidence_file" ]]; then
        echo "0"
        return 0
    fi

    # Validate JSON structure
    if ! jq -e '.agents' "$evidence_file" >/dev/null 2>&1; then
        echo "0"
        return 0
    fi

    # Extract agent count
    local count
    count=$(jq '.agents | length' "$evidence_file" 2>/dev/null || echo "0")

    echo "$count"
}

get_agent_names() {
    local evidence_file=".gates/agents_invocation.json"

    if [[ ! -f "$evidence_file" ]]; then
        echo "unknown"
        return
    fi

    # Extract comma-separated agent names
    local names
    names=$(jq -r '.agents[].agent_name' "$evidence_file" 2>/dev/null | paste -sd, - || echo "unknown")

    echo "$names"
}

# ============================================================================
# SECTION 5: Error Messages and Suggestions
# ============================================================================

display_error() {
    local tier="$1"
    local required="$2"
    local actual="$3"
    local agent_names="$4"

    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}" >&2
        echo -e "${RED}║     🚫 Agent Usage Policy Violation              ║${NC}" >&2
        echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}" >&2
        echo "" >&2
        echo -e "${YELLOW}❌ Insufficient agents for $tier task${NC}" >&2
        echo -e "   Required: ≥$required agents" >&2
        echo -e "   Actual: $actual agents" >&2
        if [[ "$agent_names" != "unknown" ]]; then
            echo -e "   Used: $agent_names" >&2
        fi
        echo "" >&2
        echo -e "${BLUE}📋 Claude Enhancer 4-6-8 Strategy:${NC}" >&2
        echo -e "   • Simple tasks: 4 agents" >&2
        echo -e "   • Standard tasks: 6 agents" >&2
        echo -e "   • Complex tasks: 8 agents" >&2
        echo "" >&2
    fi

    # Tier-specific suggestions
    case "$tier" in
        "simple")
            suggest_agents_simple
            ;;
        "standard")
            suggest_agents_standard
            ;;
        "complex")
            suggest_agents_complex
            ;;
    esac

    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo "" >&2
        echo -e "${RED}🚫 Commit blocked until agent requirements met${NC}" >&2
        echo "════════════════════════════════════════════════════" >&2
    elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
        echo "[AgentEnforcer] ❌ Need $required agents, found $actual ($tier task)" >&2
    fi
}

suggest_agents_simple() {
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo -e "${GREEN}💡 Suggested 4-agent combination:${NC}" >&2
        echo "   1. backend-architect - Design and architecture" >&2
        echo "   2. test-engineer - Test design and quality" >&2
        echo "   3. code-reviewer - Code review and best practices" >&2
        echo "   4. technical-writer - Documentation" >&2
    fi
}

suggest_agents_standard() {
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo -e "${GREEN}💡 Suggested 6-agent combination:${NC}" >&2
        echo "   1. backend-architect - System design" >&2
        echo "   2. devops-engineer - Deployment and infrastructure" >&2
        echo "   3. test-engineer - Test strategy and execution" >&2
        echo "   4. security-auditor - Security review" >&2
        echo "   5. code-reviewer - Code quality review" >&2
        echo "   6. technical-writer - Documentation" >&2
    fi
}

suggest_agents_complex() {
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo -e "${GREEN}💡 Suggested 8-agent combination:${NC}" >&2
        echo "   1. backend-architect - Architecture design" >&2
        echo "   2. devops-engineer - Infrastructure and deployment" >&2
        echo "   3. test-engineer - Test strategy" >&2
        echo "   4. security-auditor - Security analysis" >&2
        echo "   5. performance-engineer - Performance optimization" >&2
        echo "   6. code-reviewer - Code quality" >&2
        echo "   7. api-designer - API design" >&2
        echo "   8. technical-writer - Comprehensive documentation" >&2
    fi
}

# ============================================================================
# SECTION 6: Main Validation Logic
# ============================================================================

main() {
    # Fast lane check
    if is_fast_lane; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "⚡ Fast lane: Skipping agent validation" >&2
        fi
        exit 0
    fi

    # Calculate complexity
    local metrics
    metrics=$(calculate_complexity)

    local tier_info
    tier_info=$(determine_tier "$metrics")

    IFS='|' read -r tier required <<< "$tier_info"

    # Get actual agent count
    local actual
    actual=$(get_agent_count)

    # Validation
    if [ "$actual" -ge "$required" ]; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo -e "${GREEN}✅ Agent usage validated: $actual agents for $tier task${NC}" >&2
        fi
        echo "$(date +'%F %T') PASS: $actual agents for $tier task (required: $required)" >> "$LOG_FILE"
        exit 0
    else
        # Get agent names for error message
        local agent_names
        agent_names=$(get_agent_names)

        # Display error and suggestions
        display_error "$tier" "$required" "$actual" "$agent_names"

        # Log violation
        echo "$(date +'%F %T') BLOCK: $actual agents for $tier task (required: $required)" >> "$LOG_FILE"

        # Block commit
        exit 1
    fi
}

# Execute main function
main "$@"
