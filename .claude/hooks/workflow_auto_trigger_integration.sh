#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Workflow Auto-Trigger Integration Hook
# Integrates auto_trigger.sh with Claude Enhancer 5.0 hook system
# Version: 5.0.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
AUTO_TRIGGER_SCRIPT="$PROJECT_ROOT/src/workflow/auto_trigger.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Hook configuration
HOOK_CONFIG='{
    "name": "workflow_auto_trigger_integration",
    "version": "5.0.0",
    "blocking": false,
    "timeout": 3000,
    "triggers": [
        "before_tool_execution",
        "after_file_change",
        "phase_transition",
        "claude_code_startup"
    ]
}'

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "ERROR") echo -e "${RED}[AUTO-TRIGGER ERROR]${NC} $message" >&2 ;;
        "WARN")  echo -e "${YELLOW}[AUTO-TRIGGER WARN]${NC} $message" ;;
        "INFO")  echo -e "${GREEN}[AUTO-TRIGGER INFO]${NC} $message" ;;
        "DEBUG") echo -e "${BLUE}[AUTO-TRIGGER DEBUG]${NC} $message" ;;
        *) echo "[AUTO-TRIGGER $level] $message" ;;
    esac
}

# Main integration logic
main() {
    local trigger_type="${1:-startup}"
    local context="${2:-}"

    log "INFO" "🔄 Auto-Trigger Integration activated"
    log "DEBUG" "Trigger: $trigger_type, Context: $context"

    # Ensure auto-trigger script exists and is executable
    if [[ ! -x "$AUTO_TRIGGER_SCRIPT" ]]; then
        log "ERROR" "Auto-trigger script not found or not executable: $AUTO_TRIGGER_SCRIPT"
        return 1
    fi

    case "$trigger_type" in
        "startup"|"claude_code_startup")
            handle_claude_startup
            ;;
        "before_tool_execution")
            handle_tool_execution_check "$context"
            ;;
        "after_file_change")
            handle_file_change_notification "$context"
            ;;
        "phase_transition")
            handle_phase_transition "$context"
            ;;
        "status")
            show_integration_status
            ;;
        "install")
            install_integration
            ;;
        *)
            log "WARN" "Unknown trigger type: $trigger_type"
            ;;
    esac
}

# Handle Claude Code startup
handle_claude_startup() {
    log "INFO" "🚀 Claude Code startup detected - initializing workflow system"

    # Check if auto-trigger is already running
    if "$AUTO_TRIGGER_SCRIPT" status &>/dev/null; then
        log "INFO" "✅ Auto-trigger system already active"
    else
        log "INFO" "Starting auto-trigger system in background..."

        # Start auto-trigger system in background
        nohup "$AUTO_TRIGGER_SCRIPT" start > /dev/null 2>&1 &
        local auto_trigger_pid=$!

        # Give it a moment to initialize
        sleep 2

        if kill -0 "$auto_trigger_pid" 2>/dev/null; then
            log "INFO" "✅ Auto-trigger system started successfully"
        else
            log "WARN" "⚠️  Auto-trigger system may have failed to start"
        fi
    fi

    # Show current workflow status
    display_workflow_status
}

# Display current workflow status
display_workflow_status() {
    echo -e "\n${CYAN}📊 Claude Enhancer 5.0 Workflow Status${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Get current phase information
    if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
        local current_phase=$(cat "$PROJECT_ROOT/.phase/current")
        local phase_name

        case "$current_phase" in
            0) phase_name="Branch Creation" ;;
            1) phase_name="Requirements Analysis" ;;
            2) phase_name="Design Planning" ;;
            3) phase_name="Implementation" ;;
            4) phase_name="Local Testing" ;;
            5) phase_name="Code Commit" ;;
            6) phase_name="Code Review" ;;
            7) phase_name="Merge & Deploy" ;;
            *) phase_name="Unknown Phase" ;;
        esac

        echo -e "${GREEN}🎯 Current Phase:${NC} $current_phase ($phase_name)"

        # Show phase-specific guidance
        case "$current_phase" in
            0)
                echo -e "${BLUE}📋 Recommended Actions:${NC}"
                echo "   • Create feature branch with: git checkout -b feature/your-feature"
                echo "   • Clean up development environment"
                echo "   • Initialize project structure"
                ;;
            1)
                echo -e "${BLUE}📋 Recommended Actions:${NC}"
                echo "   • Analyze user requirements and business needs"
                echo "   • Create user stories and acceptance criteria"
                echo "   • Define success metrics"
                ;;
            2)
                echo -e "${BLUE}📋 Recommended Actions:${NC}"
                echo "   • Design system architecture"
                echo "   • Select appropriate technologies"
                echo "   • Plan implementation approach"
                ;;
            3)
                echo -e "${BLUE}📋 Recommended Actions:${NC}"
                echo "   • 🤖 Use 4-6-8 Agent Strategy for parallel implementation"
                echo "   • Simple tasks: 4 Agents | Standard: 6 Agents | Complex: 8 Agents"
                echo "   • Execute ALL Agents in single function_calls block"
                ;;
            4)
                echo -e "${BLUE}📋 Recommended Actions:${NC}"
                echo "   • Run comprehensive test suites"
                echo "   • Perform integration testing"
                echo "   • Validate functionality against requirements"
                ;;
            5)
                echo -e "${BLUE}📋 Recommended Actions:${NC}"
                echo "   • Commit code with proper cleanup"
                echo "   • Auto-cleanup will remove temporary files"
                echo "   • Ensure commit messages follow conventions"
                ;;
            6)
                echo -e "${BLUE}📋 Recommended Actions:${NC}"
                echo "   • Create pull request for team review"
                echo "   • Address feedback and make improvements"
                echo "   • Ensure all quality checks pass"
                ;;
            7)
                echo -e "${BLUE}📋 Recommended Actions:${NC}"
                echo "   • Deploy to production environment"
                echo "   • Perform final cleanup and optimization"
                echo "   • Create deployment documentation"
                ;;
        esac

    else
        echo -e "${YELLOW}⚠️  Phase tracking not initialized${NC}"
        echo "Run: $AUTO_TRIGGER_SCRIPT start"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Handle tool execution check
handle_tool_execution_check() {
    local tool_name="$1"

    if [[ -z "$tool_name" ]]; then
        log "DEBUG" "No tool name provided for permission check"
        return 0
    fi

    log "DEBUG" "Checking permissions for tool: $tool_name"

    # Check with auto-trigger system
    if "$AUTO_TRIGGER_SCRIPT" check-permission "$tool_name" 2>/dev/null; then
        log "DEBUG" "✅ Tool '$tool_name' permission granted"
        return 0
    else
        local current_phase=$(cat "$PROJECT_ROOT/.phase/current" 2>/dev/null || echo "0")
        log "WARN" "⚠️  Tool '$tool_name' not optimal for current phase $current_phase"

        # Show contextual guidance
        case "$tool_name" in
            "Write"|"MultiEdit")
                if [[ "$current_phase" != "3" && "$current_phase" != "5" ]]; then
                    echo -e "${YELLOW}💡 Suggestion:${NC} File modifications are typically done in Phase 3 (Implementation) or Phase 5 (Code Commit)"
                fi
                ;;
            "Bash")
                if [[ "$current_phase" == "1" || "$current_phase" == "2" ]]; then
                    echo -e "${YELLOW}💡 Suggestion:${NC} Command execution is more common in implementation phases (3-7)"
                fi
                ;;
        esac

        return 0  # Non-blocking - just advisory
    fi
}

# Handle file change notifications
handle_file_change_notification() {
    local changed_file="$1"

    if [[ -z "$changed_file" ]]; then
        return 0
    fi

    log "DEBUG" "File change notification: $changed_file"

    # Let auto-trigger system handle the file change analysis
    # This is a passive notification - the file watcher in auto_trigger.sh
    # will handle the actual phase detection and validation
}

# Handle phase transitions
handle_phase_transition() {
    local transition_info="$1"
    log "INFO" "Phase transition detected: $transition_info"

    # Trigger validation for new phase
    "$AUTO_TRIGGER_SCRIPT" trigger-validation
}

# Show integration status
show_integration_status() {
    echo -e "\n${CYAN}🔧 Auto-Trigger Integration Status${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Check auto-trigger script
    if [[ -x "$AUTO_TRIGGER_SCRIPT" ]]; then
        echo -e "${GREEN}✅ Auto-trigger script:${NC} Available and executable"

        # Check if system is running
        if "$AUTO_TRIGGER_SCRIPT" status &>/dev/null; then
            echo -e "${GREEN}✅ Auto-trigger system:${NC} Active"
        else
            echo -e "${YELLOW}⚠️  Auto-trigger system:${NC} Inactive"
        fi
    else
        echo -e "${RED}❌ Auto-trigger script:${NC} Missing or not executable"
    fi

    # Check phase tracking
    if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
        local current_phase=$(cat "$PROJECT_ROOT/.phase/current")
        echo -e "${GREEN}✅ Phase tracking:${NC} Active (Phase $current_phase)"
    else
        echo -e "${YELLOW}⚠️  Phase tracking:${NC} Not initialized"
    fi

    # Check system prompt hooks
    local hook_count=$(find "$SCRIPT_DIR" -name "system_prompt_*.sh" -type f | wc -l)
    if [[ $hook_count -gt 0 ]]; then
        echo -e "${GREEN}✅ System prompt hooks:${NC} $hook_count installed"
    else
        echo -e "${YELLOW}⚠️  System prompt hooks:${NC} None found"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Install integration
install_integration() {
    log "INFO" "📦 Installing Auto-Trigger Integration"

    # Make auto-trigger script executable
    chmod +x "$AUTO_TRIGGER_SCRIPT"

    # Create systemd service file for auto-start (optional)
    create_systemd_service

    # Add to Claude hooks registry if it exists
    register_with_claude_hooks

    log "INFO" "✅ Auto-Trigger Integration installed successfully"
    log "INFO" "🎬 Run 'startup' to activate the system"
}

# Create systemd service (for persistent background running)
create_systemd_service() {
    local service_file="$HOME/.config/systemd/user/claude-enhancer-auto-trigger.service"

    mkdir -p "$(dirname "$service_file")"

    cat > "$service_file" << EOF
[Unit]
Description=Claude Enhancer 5.0 Auto-Trigger System
After=graphical-session.target

[Service]
Type=simple
ExecStart=$AUTO_TRIGGER_SCRIPT start
Restart=always
RestartSec=10
Environment=PATH=$PATH

[Install]
WantedBy=default.target
EOF

    log "INFO" "Created systemd service: $service_file"
    log "INFO" "To enable auto-start: systemctl --user enable claude-enhancer-auto-trigger"
}

# Register with Claude hooks if registry exists
register_with_claude_hooks() {
    local hooks_registry="$SCRIPT_DIR/hooks_registry.json"

    if [[ -f "$hooks_registry" ]]; then
        # Add this hook to the registry
        local temp_file=$(mktemp)
        jq ". + [$(echo "$HOOK_CONFIG")]" "$hooks_registry" > "$temp_file"
        mv "$temp_file" "$hooks_registry"
        log "INFO" "Registered with Claude hooks registry"
    fi
}

# Execute main function
main "$@"