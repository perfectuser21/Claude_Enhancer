#!/bin/bash
# Auto Trigger System for Claude Enhancer 5.0 Workflow
# Monitors file changes and automatically triggers appropriate phase validations
# Version: 5.0.0
# Author: Claude Code + DevOps Engineer

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PHASE_DIR="$PROJECT_ROOT/.phase"
HOOKS_DIR="$PROJECT_ROOT/.claude/hooks"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
LOG_FILE="$PROJECT_ROOT/.workflow/auto_trigger.log"

# Phase definitions (0-7)
declare -A PHASE_PERMISSIONS=(
    [0]="branch_creation,environment_setup,cleanup_preparation"
    [1]="requirements_analysis,user_story_creation,acceptance_criteria"
    [2]="design_planning,architecture_design,technical_selection"
    [3]="implementation,coding,agent_orchestration"
    [4]="local_testing,unit_tests,integration_tests,validation"
    [5]="code_commit,git_operations,quality_checks,cleanup_staging"
    [6]="code_review,pr_creation,feedback_integration"
    [7]="merge_deploy,production_deployment,final_cleanup"
)

# File patterns that trigger specific phases
declare -A FILE_PHASE_TRIGGERS=(
    ["*.feature,*.story,requirements.md"]="1"
    ["*.design.md,architecture.md,*.uml,*.diagram"]="2"
    ["*.js,*.py,*.sh,*.yaml,*.json,src/*"]="3"
    ["*.test.js,*.spec.py,test/*,tests/*"]="4"
    [".git/*,CHANGELOG.md,commit*"]="5"
    ["*.pr.md,review/*,PULL_REQUEST_TEMPLATE.md"]="6"
    ["deploy/*,Dockerfile,docker-compose.yml,k8s/*"]="7"
)

# System prompt hooks
SYSTEM_PROMPT_HOOKS=(
    "phase_permission_guard"
    "workflow_compliance_check"
    "agent_orchestration_validator"
    "quality_gate_enforcer"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"

    case "$level" in
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" >&2 ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "INFO")  echo -e "${GREEN}[INFO]${NC} $message" ;;
        "DEBUG") echo -e "${BLUE}[DEBUG]${NC} $message" ;;
        *) echo "[$level] $message" ;;
    esac
}

# Initialize auto-trigger system
initialize() {
    log "INFO" "🚀 Initializing Claude Enhancer 5.0 Auto-Trigger System"

    # Create necessary directories
    mkdir -p "$PHASE_DIR" "$WORKFLOW_DIR" "$(dirname "$LOG_FILE")"

    # Initialize current phase if not exists
    if [[ ! -f "$PHASE_DIR/current" ]]; then
        echo "0" > "$PHASE_DIR/current"
        log "INFO" "Initialized current phase to 0 (Branch Creation)"
    fi

    # Setup file watchers
    setup_file_watchers

    # Install system prompt hooks
    install_system_prompt_hooks

    log "INFO" "✅ Auto-Trigger System initialized successfully"
}

# Setup file watchers using inotify
setup_file_watchers() {
    log "INFO" "Setting up file watchers for automatic phase detection"

    # Check if inotify-tools is available
    if ! command -v inotifywait &> /dev/null; then
        log "WARN" "inotify-tools not found. File watching will use polling mode."
        return 0
    fi

    # Start background file watcher
    (
        inotifywait -m -r "$PROJECT_ROOT" \
            --exclude '\.git|node_modules|\.claude|__pycache__|\.pyc$' \
            -e modify,create,delete,move 2>/dev/null | \
        while read -r directory events filename; do
            handle_file_change "$directory" "$events" "$filename"
        done
    ) &

    local watcher_pid=$!
    echo "$watcher_pid" > "$WORKFLOW_DIR/file_watcher.pid"
    log "INFO" "File watcher started with PID: $watcher_pid"
}

# Handle file changes and trigger appropriate phase validations
handle_file_change() {
    local directory="$1"
    local events="$2"
    local filename="$3"
    local filepath="${directory}${filename}"

    log "DEBUG" "File change detected: $filepath ($events)"

    # Skip temporary files and system files
    [[ "$filename" =~ \.(tmp|swp|log)$ ]] && return 0
    [[ "$filename" =~ ^\.# ]] && return 0

    # Determine which phase this file change should trigger
    local suggested_phase=$(detect_phase_from_file "$filepath")

    if [[ -n "$suggested_phase" ]]; then
        local current_phase=$(get_current_phase)

        if [[ "$suggested_phase" != "$current_phase" ]]; then
            log "INFO" "🔄 File change suggests phase $suggested_phase, current phase is $current_phase"
            validate_phase_transition "$current_phase" "$suggested_phase" "$filepath"
        fi
    fi
}

# Detect phase from file path/type
detect_phase_from_file() {
    local filepath="$1"
    local filename=$(basename "$filepath")
    local extension="${filename##*.}"
    local relative_path="${filepath#$PROJECT_ROOT/}"

    # Check each pattern
    for pattern in "${!FILE_PHASE_TRIGGERS[@]}"; do
        IFS=',' read -ra PATTERNS <<< "$pattern"
        for pat in "${PATTERNS[@]}"; do
            if [[ "$relative_path" == $pat || "$filename" == $pat ]]; then
                echo "${FILE_PHASE_TRIGGERS[$pattern]}"
                return 0
            fi
        done
    done

    # Default phase detection based on directory structure
    case "$relative_path" in
        requirements/*|docs/requirements*) echo "1" ;;
        design/*|architecture/*|docs/design*) echo "2" ;;
        src/*|lib/*|components/*) echo "3" ;;
        test/*|tests/*|spec/*) echo "4" ;;
        .git/*|CHANGELOG*) echo "5" ;;
        review/*|pr/*) echo "6" ;;
        deploy/*|k8s/*|docker*) echo "7" ;;
    esac
}

# Get current phase
get_current_phase() {
    if [[ -f "$PHASE_DIR/current" ]]; then
        cat "$PHASE_DIR/current"
    else
        echo "0"
    fi
}

# Set current phase
set_current_phase() {
    local phase="$1"
    echo "$phase" > "$PHASE_DIR/current"
    echo "$(date +%s)" > "$PHASE_DIR/last_updated_$(date +%s)"
    log "INFO" "🎯 Current phase updated to: $phase"
}

# Validate phase transition
validate_phase_transition() {
    local current_phase="$1"
    local suggested_phase="$2"
    local trigger_file="$3"

    # Allow backward transitions (e.g., from testing back to implementation)
    # But warn about forward jumps
    if (( suggested_phase > current_phase + 1 )); then
        log "WARN" "⚠️  Jumping from phase $current_phase to $suggested_phase"
        log "WARN" "   Triggered by: $trigger_file"
        log "WARN" "   Consider completing intermediate phases"
    fi

    # Auto-advance for logical progressions
    if (( suggested_phase == current_phase + 1 )); then
        log "INFO" "✅ Natural phase progression detected"
        set_current_phase "$suggested_phase"
        trigger_phase_validation "$suggested_phase"
    fi
}

# Trigger phase validation
trigger_phase_validation() {
    local phase="$1"
    log "INFO" "🔍 Triggering validation for Phase $phase"

    # Call appropriate Claude hooks based on phase
    case "$phase" in
        0) run_hook "branch_helper.sh" ;;
        1) run_hook "task_type_detector.sh" ;;
        2) run_hook "smart_agent_selector.sh" "design" ;;
        3) run_hook "smart_agent_selector.sh" "implementation" ;;
        4) run_hook "performance_monitor.sh" "testing" ;;
        5) run_hook "smart_cleanup_advisor.sh" "pre-commit" ;;
        6) run_hook "quality_gate.sh" "review" ;;
        7) run_hook "smart_cleanup_advisor.sh" "deployment" ;;
    esac
}

# Run a Claude hook
run_hook() {
    local hook_script="$1"
    shift
    local hook_args="$*"
    local hook_path="$HOOKS_DIR/$hook_script"

    if [[ -x "$hook_path" ]]; then
        log "INFO" "🪝 Running hook: $hook_script $hook_args"

        # Run hook with timeout to prevent hanging
        timeout 30s "$hook_path" $hook_args 2>&1 | while IFS= read -r line; do
            log "DEBUG" "Hook output: $line"
        done

        local exit_code=$?
        if [[ $exit_code -eq 0 ]]; then
            log "INFO" "✅ Hook $hook_script completed successfully"
        else
            log "WARN" "⚠️  Hook $hook_script exited with code $exit_code"
        fi
    else
        log "WARN" "Hook not found or not executable: $hook_path"
    fi
}

# Check tool permissions before execution
check_tool_permission() {
    local tool_name="$1"
    local current_phase=$(get_current_phase)
    local permissions="${PHASE_PERMISSIONS[$current_phase]}"

    log "DEBUG" "Checking permission for tool '$tool_name' in phase $current_phase"

    # Basic permission mapping
    case "$tool_name" in
        "git"*|"Write"|"MultiEdit")
            if [[ "$permissions" =~ (implementation|coding|code_commit|git_operations) ]]; then
                return 0
            fi
            ;;
        "Bash"*|"Read"*|"Grep"*|"Glob"*)
            # These tools are generally allowed in most phases
            return 0
            ;;
        *)
            # Unknown tool - allow but log
            log "WARN" "Unknown tool '$tool_name' - allowing execution"
            return 0
            ;;
    esac

    log "WARN" "⛔ Tool '$tool_name' not recommended for current phase $current_phase"
    log "WARN" "   Current phase permissions: $permissions"
    return 1
}

# Install System Prompt Hooks
install_system_prompt_hooks() {
    log "INFO" "Installing System Prompt Hooks for Claude Code compliance"

    # Phase Permission Guard
    create_system_prompt_hook "phase_permission_guard" '
# Phase Permission Guard
# Ensures Claude Code respects current workflow phase

CURRENT_PHASE=$(cat "$PROJECT_ROOT/.phase/current" 2>/dev/null || echo "0")
PHASE_NAME=$(case $CURRENT_PHASE in
    0) echo "Branch Creation" ;;
    1) echo "Requirements Analysis" ;;
    2) echo "Design Planning" ;;
    3) echo "Implementation" ;;
    4) echo "Local Testing" ;;
    5) echo "Code Commit" ;;
    6) echo "Code Review" ;;
    7) echo "Merge & Deploy" ;;
esac)

echo "🎯 Current Workflow Phase: $CURRENT_PHASE ($PHASE_NAME)"
echo "📋 Recommended actions for this phase:"

case $CURRENT_PHASE in
    0) echo "  - Create feature branch" ;;
    1) echo "  - Analyze requirements and user needs" ;;
    2) echo "  - Design architecture and plan implementation" ;;
    3) echo "  - Use 4-6-8 Agent strategy for parallel implementation" ;;
    4) echo "  - Run tests and validate functionality" ;;
    5) echo "  - Commit code with proper cleanup" ;;
    6) echo "  - Create PR and conduct code review" ;;
    7) echo "  - Deploy and perform final cleanup" ;;
esac
'

    # Workflow Compliance Checker
    create_system_prompt_hook "workflow_compliance_check" '
# Workflow Compliance Check
# Reminds Claude Code to follow 8-Phase workflow

echo "📚 Claude Enhancer 5.0 Workflow Reminder:"
echo "  Phase 0-7: Complete lifecycle from branch to deployment"
echo "  4-6-8 Strategy: Select appropriate Agent count based on complexity"
echo "  Quality Gates: Built-in hooks ensure code quality at each phase"
echo ""
echo "⚠️  Remember: Only Claude Code can orchestrate SubAgents"
echo "🎯 Focus: Complete the current phase before advancing"
'

    # Agent Orchestration Validator
    create_system_prompt_hook "agent_orchestration_validator" '
# Agent Orchestration Validator
# Ensures proper Agent usage in Phase 3 (Implementation)

if [[ "$CURRENT_PHASE" == "3" ]]; then
    echo "🤖 Phase 3: Implementation - Agent Orchestration Required"
    echo ""
    echo "MANDATORY: Use 4-6-8 Agent Strategy:"
    echo "  - Simple tasks: 4 Agents (5-10 minutes)"
    echo "  - Standard tasks: 6 Agents (15-20 minutes)"
    echo "  - Complex tasks: 8 Agents (25-30 minutes)"
    echo ""
    echo "⚡ Execute ALL Agents in parallel within single function_calls block"
    echo "❌ NEVER call Agents sequentially"
    echo "❌ SubAgents CANNOT call other SubAgents"
    echo ""
    echo "Available Agent Categories:"
    echo "  - Backend: backend-architect, api-designer, database-specialist"
    echo "  - Security: security-auditor, authentication-expert"
    echo "  - Testing: test-engineer, performance-engineer"
    echo "  - Infrastructure: devops-engineer, deployment-specialist"
fi
'

    # Quality Gate Enforcer
    create_system_prompt_hook "quality_gate_enforcer" '
# Quality Gate Enforcer
# Enforces quality standards at key phases

case $CURRENT_PHASE in
    4) echo "🧪 Phase 4: Testing Required - Validate all functionality" ;;
    5) echo "🧹 Phase 5: Cleanup Required - Auto-cleanup will trigger" ;;
    6) echo "👥 Phase 6: Code Review Required - Create PR for team review" ;;
    7) echo "🚀 Phase 7: Deployment Ready - Final cleanup and deploy" ;;
esac

echo ""
echo "Quality Standards:"
echo "  ✅ All code must be tested"
echo "  ✅ No temporary files in commits"
echo "  ✅ Follow naming conventions"
echo "  ✅ Security scan passed"
'

    log "INFO" "✅ System Prompt Hooks installed successfully"
}

# Create a system prompt hook file
create_system_prompt_hook() {
    local hook_name="$1"
    local hook_content="$2"
    local hook_file="$HOOKS_DIR/system_prompt_${hook_name}.sh"

    cat > "$hook_file" << EOF
#!/bin/bash
# System Prompt Hook: $hook_name
# Auto-generated by Claude Enhancer 5.0 Auto-Trigger System

PROJECT_ROOT="$PROJECT_ROOT"
$hook_content
EOF

    chmod +x "$hook_file"
    log "INFO" "Created system prompt hook: $hook_name"
}

# Main command dispatcher
main() {
    case "${1:-}" in
        "start")
            initialize
            log "INFO" "🎬 Auto-Trigger System is now active"

            # Keep the script running for file monitoring
            while true; do
                sleep 60
                # Periodic health check
                if [[ ! -f "$WORKFLOW_DIR/file_watcher.pid" ]]; then
                    log "WARN" "File watcher PID not found, restarting..."
                    setup_file_watchers
                fi
            done
            ;;

        "stop")
            if [[ -f "$WORKFLOW_DIR/file_watcher.pid" ]]; then
                local watcher_pid=$(cat "$WORKFLOW_DIR/file_watcher.pid")
                kill "$watcher_pid" 2>/dev/null || true
                rm -f "$WORKFLOW_DIR/file_watcher.pid"
                log "INFO" "🛑 Auto-Trigger System stopped"
            fi
            ;;

        "status")
            local current_phase=$(get_current_phase)
            local phase_name="${PHASE_PERMISSIONS[$current_phase]}"

            echo -e "${CYAN}📊 Claude Enhancer 5.0 Auto-Trigger Status${NC}"
            echo -e "${GREEN}Current Phase:${NC} $current_phase"
            echo -e "${GREEN}Phase Permissions:${NC} $phase_name"

            if [[ -f "$WORKFLOW_DIR/file_watcher.pid" ]]; then
                local watcher_pid=$(cat "$WORKFLOW_DIR/file_watcher.pid")
                if kill -0 "$watcher_pid" 2>/dev/null; then
                    echo -e "${GREEN}File Watcher:${NC} Active (PID: $watcher_pid)"
                else
                    echo -e "${RED}File Watcher:${NC} Inactive"
                fi
            else
                echo -e "${RED}File Watcher:${NC} Not started"
            fi
            ;;

        "check-permission")
            local tool_name="${2:-}"
            if [[ -z "$tool_name" ]]; then
                echo "Usage: $0 check-permission <tool_name>"
                exit 1
            fi

            if check_tool_permission "$tool_name"; then
                echo -e "${GREEN}✅ Tool '$tool_name' is allowed in current phase${NC}"
                exit 0
            else
                echo -e "${RED}❌ Tool '$tool_name' is not recommended for current phase${NC}"
                exit 1
            fi
            ;;

        "set-phase")
            local new_phase="${2:-}"
            if [[ -z "$new_phase" || ! "$new_phase" =~ ^[0-7]$ ]]; then
                echo "Usage: $0 set-phase <0-7>"
                exit 1
            fi

            set_current_phase "$new_phase"
            trigger_phase_validation "$new_phase"
            ;;

        "trigger-validation")
            local phase="${2:-$(get_current_phase)}"
            trigger_phase_validation "$phase"
            ;;

        *)
            echo "Claude Enhancer 5.0 Auto-Trigger System"
            echo ""
            echo "Usage: $0 {start|stop|status|check-permission|set-phase|trigger-validation}"
            echo ""
            echo "Commands:"
            echo "  start                     - Start the auto-trigger system"
            echo "  stop                      - Stop the auto-trigger system"
            echo "  status                    - Show current system status"
            echo "  check-permission <tool>   - Check if tool is allowed in current phase"
            echo "  set-phase <0-7>          - Manually set current workflow phase"
            echo "  trigger-validation [phase] - Trigger validation for specific phase"
            echo ""
            echo "Phases:"
            echo "  0: Branch Creation        4: Local Testing"
            echo "  1: Requirements Analysis  5: Code Commit"
            echo "  2: Design Planning        6: Code Review"
            echo "  3: Implementation         7: Merge & Deploy"
            ;;
    esac
}

# Trap to cleanup on exit
trap 'main stop' EXIT INT TERM

# Execute main function
main "$@"