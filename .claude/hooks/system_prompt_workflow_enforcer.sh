#!/bin/bash
# SystemPrompt Workflow Enforcer
# Ensures Claude Code automatically follows Claude Enhancer 5.0 workflow
# Version: 5.0.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get current phase
get_current_phase() {
    if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
        cat "$PROJECT_ROOT/.phase/current"
    else
        echo "0"
    fi
}

# Get phase name
get_phase_name() {
    local phase="$1"
    case "$phase" in
        0) echo "Branch Creation" ;;
        1) echo "Requirements Analysis" ;;
        2) echo "Design Planning" ;;
        3) echo "Implementation" ;;
        4) echo "Local Testing" ;;
        5) echo "Code Commit" ;;
        6) echo "Code Review" ;;
        7) echo "Merge & Deploy" ;;
        *) echo "Unknown Phase" ;;
    esac
}

# Generate workflow enforcement prompt
generate_workflow_prompt() {
    local current_phase=$(get_current_phase)
    local phase_name=$(get_phase_name "$current_phase")

    echo -e "\n${PURPLE}🤖 Claude Enhancer 5.0 Workflow Enforcer${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Current phase status
    echo -e "${GREEN}📍 Current Phase: $current_phase ($phase_name)${NC}"
    echo ""

    # Phase-specific enforcement
    case "$current_phase" in
        0)
            echo -e "${BLUE}🎯 Phase 0 Enforcement:${NC}"
            echo "   MUST: Create feature branch if not exists"
            echo "   MUST: Clean up development environment"
            echo "   SHOULD: Initialize project structure"
            echo ""
            echo -e "${YELLOW}⚡ Next Actions:${NC}"
            echo "   → git checkout -b feature/your-feature-name"
            echo "   → Clean temporary files and prepare workspace"
            ;;

        1)
            echo -e "${BLUE}🎯 Phase 1 Enforcement:${NC}"
            echo "   MUST: Thoroughly understand requirements"
            echo "   MUST: Ask clarifying questions if needed"
            echo "   SHOULD: Create user stories or acceptance criteria"
            echo ""
            echo -e "${YELLOW}⚡ Focus Areas:${NC}"
            echo "   → What problem are we solving?"
            echo "   → Who are the users and what do they need?"
            echo "   → What does success look like?"
            ;;

        2)
            echo -e "${BLUE}🎯 Phase 2 Enforcement:${NC}"
            echo "   MUST: Design system architecture"
            echo "   MUST: Select appropriate technologies"
            echo "   SHOULD: Create technical specifications"
            echo ""
            echo -e "${YELLOW}⚡ Design Checklist:${NC}"
            echo "   → Architecture patterns and components"
            echo "   → Data models and API design"
            echo "   → Technology stack selection"
            echo "   → Security and performance considerations"
            ;;

        3)
            echo -e "${BLUE}🎯 Phase 3 Enforcement - AGENT ORCHESTRATION REQUIRED:${NC}"
            echo -e "${RED}   🚨 MANDATORY: Use 4-6-8 Agent Strategy${NC}"
            echo "   MUST: Execute ALL Agents in parallel (single function_calls block)"
            echo "   FORBIDDEN: Sequential Agent execution"
            echo "   FORBIDDEN: SubAgent calling other SubAgents"
            echo ""

            echo -e "${PURPLE}🤖 Agent Selection Guide:${NC}"
            echo "   Simple tasks (5-10 min):  4 Agents"
            echo "   Standard tasks (15-20 min): 6 Agents"
            echo "   Complex tasks (25-30 min):  8 Agents"
            echo ""

            echo -e "${YELLOW}⚡ Agent Categories Available:${NC}"
            echo "   📊 Architecture: backend-architect, system-designer"
            echo "   🔒 Security: security-auditor, authentication-expert"
            echo "   🗄️  Database: database-specialist, data-architect"
            echo "   🌐 API: api-designer, rest-specialist"
            echo "   🧪 Testing: test-engineer, qa-specialist"
            echo "   ⚡ Performance: performance-engineer, optimization-expert"
            echo "   🚀 DevOps: devops-engineer, deployment-specialist"
            echo "   📝 Documentation: technical-writer, doc-specialist"
            echo ""

            echo -e "${RED}❌ CRITICAL VIOLATIONS TO AVOID:${NC}"
            echo "   ❌ Using only 1-2 Agents"
            echo "   ❌ Calling Agents one by one"
            echo "   ❌ SubAgent → SubAgent calls"
            echo "   ❌ Skipping Agent orchestration"
            ;;

        4)
            echo -e "${BLUE}🎯 Phase 4 Enforcement:${NC}"
            echo "   MUST: Run comprehensive tests"
            echo "   MUST: Validate against requirements"
            echo "   SHOULD: Performance testing if applicable"
            echo ""
            echo -e "${YELLOW}⚡ Testing Checklist:${NC}"
            echo "   → Unit tests for core functionality"
            echo "   → Integration tests for system interactions"
            echo "   → End-to-end testing for user workflows"
            echo "   → Security testing for vulnerabilities"
            ;;

        5)
            echo -e "${BLUE}🎯 Phase 5 Enforcement:${NC}"
            echo "   MUST: Auto-cleanup will trigger before commit"
            echo "   MUST: Follow commit message conventions"
            echo "   SHOULD: Review changes before commit"
            echo ""
            echo -e "${YELLOW}⚡ Pre-Commit Checklist:${NC}"
            echo "   → Remove temporary files and debug code"
            echo "   → Format code according to standards"
            echo "   → Update documentation if needed"
            echo "   → Run security scan"
            ;;

        6)
            echo -e "${BLUE}🎯 Phase 6 Enforcement:${NC}"
            echo "   MUST: Create pull request with proper description"
            echo "   MUST: Address all review feedback"
            echo "   SHOULD: Update tests based on feedback"
            echo ""
            echo -e "${YELLOW}⚡ Code Review Process:${NC}"
            echo "   → Create detailed PR description"
            echo "   → Respond to all review comments"
            echo "   → Make requested improvements"
            echo "   → Ensure CI/CD pipeline passes"
            ;;

        7)
            echo -e "${BLUE}🎯 Phase 7 Enforcement:${NC}"
            echo "   MUST: Final cleanup and optimization"
            echo "   MUST: Deploy to target environment"
            echo "   SHOULD: Create deployment documentation"
            echo ""
            echo -e "${YELLOW}⚡ Deployment Checklist:${NC}"
            echo "   → Final security scan"
            echo "   → Remove development dependencies"
            echo "   → Optimize for production"
            echo "   → Create deployment guides"
            ;;
    esac

    # Universal workflow reminders
    echo ""
    echo -e "${PURPLE}🔄 Universal Workflow Rules:${NC}"
    echo "   • Complete current phase before advancing"
    echo "   • Each phase builds on the previous ones"
    echo "   • Quality gates ensure standards compliance"
    echo "   • Auto-cleanup happens at Phase 5 and 7"
    echo ""

    # Max 20X reminder
    echo -e "${CYAN}💎 Max 20X Principles:${NC}"
    echo "   • Quality over speed - take time to do it right"
    echo "   • Use all available Agents for comprehensive solutions"
    echo "   • Don't skip phases - they ensure quality"
    echo "   • Token cost is irrelevant - aim for excellence"

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check if specific workflow rules are being followed
check_workflow_compliance() {
    local current_phase=$(get_current_phase)

    case "$current_phase" in
        3)
            # Check if we're in implementation phase
            echo ""
            echo -e "${RED}🚨 PHASE 3 COMPLIANCE CHECK:${NC}"
            echo ""
            echo -e "${YELLOW}Before proceeding with implementation, confirm:${NC}"
            echo "   □ Will you use 4-6-8 Agents based on task complexity?"
            echo "   □ Will you execute ALL Agents in a single function_calls block?"
            echo "   □ Have you selected appropriate Agents for this specific task?"
            echo ""
            echo -e "${RED}⚠️  VIOLATION ALERT: Using fewer than 4 Agents or sequential execution${NC}"
            echo -e "${RED}     will trigger workflow violation warnings!${NC}"
            ;;

        5)
            echo ""
            echo -e "${GREEN}🧹 PHASE 5 AUTO-CLEANUP ACTIVE:${NC}"
            echo "   Auto-cleanup will remove:"
            echo "   • Temporary files (*.tmp, *.bak)"
            echo "   • Debug code and console.log statements"
            echo "   • Unused imports and variables"
            echo "   • Sensitive information"
            ;;
    esac
}

# Main execution
main() {
    # Always show workflow status
    generate_workflow_prompt

    # Phase-specific compliance checks
    check_workflow_compliance

    # Check if auto-trigger system is running
    if [[ -f "$PROJECT_ROOT/src/workflow/auto_trigger.sh" ]]; then
        local auto_trigger="$PROJECT_ROOT/src/workflow/auto_trigger.sh"
        if [[ -x "$auto_trigger" ]]; then
            # Quick status check (non-blocking)
            timeout 2s "$auto_trigger" status 2>/dev/null | grep -E "(Active|Inactive)" || true
        fi
    fi

    echo ""
    echo -e "${GREEN}🎬 Ready to proceed with Phase $(get_current_phase) activities...${NC}"
    echo ""
}

# Execute main function
main "$@"