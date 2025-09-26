#!/bin/bash
# Auto-Trigger System Installer
# Installs and configures the complete workflow auto-trigger system
# Version: 5.0.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
AUTO_TRIGGER_SCRIPT="$SCRIPT_DIR/auto_trigger.sh"
INTEGRATION_HOOK="$PROJECT_ROOT/.claude/hooks/workflow_auto_trigger_integration.sh"
WORKFLOW_ENFORCER="$PROJECT_ROOT/.claude/hooks/system_prompt_workflow_enforcer.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" >&2 ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "INFO")  echo -e "${GREEN}[INFO]${NC} $message" ;;
        "DEBUG") echo -e "${BLUE}[DEBUG]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        *) echo "[$level] $message" ;;
    esac
}

# Check system prerequisites
check_prerequisites() {
    log "INFO" "🔍 Checking system prerequisites..."

    local missing_deps=()

    # Check for required commands
    local required_commands=("inotifywait" "jq" "timeout")

    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "WARN" "Missing dependencies: ${missing_deps[*]}"
        log "INFO" "Installing missing dependencies..."

        # Attempt to install missing dependencies
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            for dep in "${missing_deps[@]}"; do
                case "$dep" in
                    "inotifywait") sudo apt-get install -y inotify-tools ;;
                    "jq") sudo apt-get install -y jq ;;
                    "timeout") sudo apt-get install -y coreutils ;;
                esac
            done
        elif command -v yum &> /dev/null; then
            for dep in "${missing_deps[@]}"; do
                case "$dep" in
                    "inotifywait") sudo yum install -y inotify-tools ;;
                    "jq") sudo yum install -y jq ;;
                    "timeout") sudo yum install -y coreutils ;;
                esac
            done
        else
            log "WARN" "Could not auto-install dependencies. Please install manually:"
            for dep in "${missing_deps[@]}"; do
                echo "  - $dep"
            done
        fi
    else
        log "SUCCESS" "✅ All prerequisites satisfied"
    fi
}

# Create directory structure
setup_directories() {
    log "INFO" "📁 Setting up directory structure..."

    local directories=(
        "$PROJECT_ROOT/.phase"
        "$PROJECT_ROOT/.workflow"
        "$PROJECT_ROOT/.workflow/logs"
        "$PROJECT_ROOT/.claude/hooks"
        "$PROJECT_ROOT/src/workflow"
    )

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "INFO" "Created directory: $dir"
        fi
    done

    # Set appropriate permissions
    chmod 700 "$PROJECT_ROOT/.phase"  # Phase tracking is sensitive
    chmod 755 "$PROJECT_ROOT/.workflow"
    chmod 755 "$PROJECT_ROOT/.claude/hooks"

    log "SUCCESS" "✅ Directory structure created"
}

# Install main auto-trigger script
install_auto_trigger() {
    log "INFO" "📦 Installing auto-trigger system..."

    # Make auto-trigger script executable
    chmod +x "$AUTO_TRIGGER_SCRIPT"

    # Initialize phase tracking
    if [[ ! -f "$PROJECT_ROOT/.phase/current" ]]; then
        echo "0" > "$PROJECT_ROOT/.phase/current"
        log "INFO" "Initialized phase tracking to Phase 0"
    fi

    # Create initial configuration
    cat > "$PROJECT_ROOT/.workflow/config.yaml" << EOF
# Claude Enhancer 5.0 Auto-Trigger Configuration
version: "5.0.0"
project_root: "$PROJECT_ROOT"

# Phase configuration
phases:
  0: "Branch Creation"
  1: "Requirements Analysis"
  2: "Design Planning"
  3: "Implementation"
  4: "Local Testing"
  5: "Code Commit"
  6: "Code Review"
  7: "Merge & Deploy"

# File watcher settings
file_watcher:
  enabled: true
  exclude_patterns:
    - "*.git*"
    - "node_modules"
    - "__pycache__"
    - "*.pyc"
    - "*.tmp"
    - "*.log"

# Auto-trigger settings
auto_trigger:
  timeout: 30
  retry_count: 3
  log_level: "INFO"

# Agent orchestration
agent_strategy:
  simple_tasks: 4
  standard_tasks: 6
  complex_tasks: 8
  parallel_execution: true
EOF

    log "SUCCESS" "✅ Auto-trigger system installed"
}

# Install integration hooks
install_integration_hooks() {
    log "INFO" "🔗 Installing integration hooks..."

    # Make integration hooks executable
    chmod +x "$INTEGRATION_HOOK"
    chmod +x "$WORKFLOW_ENFORCER"

    # Create hooks registry if it doesn't exist
    local hooks_registry="$PROJECT_ROOT/.claude/hooks/hooks_registry.json"
    if [[ ! -f "$hooks_registry" ]]; then
        echo "[]" > "$hooks_registry"
    fi

    # Register the integration hook
    local temp_file=$(mktemp)
    jq '. + [{
        "name": "workflow_auto_trigger_integration",
        "version": "5.0.0",
        "script": "workflow_auto_trigger_integration.sh",
        "blocking": false,
        "timeout": 3000,
        "triggers": ["before_tool_execution", "after_file_change", "phase_transition", "claude_code_startup"]
    }]' "$hooks_registry" > "$temp_file"
    mv "$temp_file" "$hooks_registry"

    # Register the workflow enforcer
    temp_file=$(mktemp)
    jq '. + [{
        "name": "system_prompt_workflow_enforcer",
        "version": "5.0.0",
        "script": "system_prompt_workflow_enforcer.sh",
        "blocking": false,
        "timeout": 2000,
        "triggers": ["claude_code_startup", "phase_change"]
    }]' "$hooks_registry" > "$temp_file"
    mv "$temp_file" "$hooks_registry"

    log "SUCCESS" "✅ Integration hooks installed and registered"
}

# Create systemd service for persistence
install_systemd_service() {
    log "INFO" "🔧 Setting up systemd service (optional)..."

    local service_dir="$HOME/.config/systemd/user"
    local service_file="$service_dir/claude-enhancer-auto-trigger.service"

    mkdir -p "$service_dir"

    cat > "$service_file" << EOF
[Unit]
Description=Claude Enhancer 5.0 Auto-Trigger System
Documentation=file://$PROJECT_ROOT/src/workflow/auto_trigger.sh
After=graphical-session.target

[Service]
Type=simple
ExecStart=$AUTO_TRIGGER_SCRIPT start
ExecStop=$AUTO_TRIGGER_SCRIPT stop
Restart=always
RestartSec=10
Environment=PATH=$PATH
Environment=PROJECT_ROOT=$PROJECT_ROOT
WorkingDirectory=$PROJECT_ROOT

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_ROOT

[Install]
WantedBy=default.target
EOF

    log "SUCCESS" "✅ Systemd service created: $service_file"
    log "INFO" "To enable auto-start: systemctl --user enable claude-enhancer-auto-trigger"
    log "INFO" "To start now: systemctl --user start claude-enhancer-auto-trigger"
}

# Create convenience scripts
create_convenience_scripts() {
    log "INFO" "📝 Creating convenience scripts..."

    # Create workflow command wrapper
    cat > "$PROJECT_ROOT/workflow" << 'EOF'
#!/bin/bash
# Claude Enhancer 5.0 Workflow Command Wrapper
# Convenient access to workflow commands

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_TRIGGER="$SCRIPT_DIR/src/workflow/auto_trigger.sh"

if [[ -x "$AUTO_TRIGGER" ]]; then
    exec "$AUTO_TRIGGER" "$@"
else
    echo "Error: Auto-trigger system not found or not executable"
    echo "Run: src/workflow/install_auto_trigger.sh"
    exit 1
fi
EOF

    chmod +x "$PROJECT_ROOT/workflow"

    # Create quick status check
    cat > "$PROJECT_ROOT/workflow-status" << 'EOF'
#!/bin/bash
# Quick workflow status check

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_ENFORCER="$SCRIPT_DIR/.claude/hooks/system_prompt_workflow_enforcer.sh"

if [[ -x "$WORKFLOW_ENFORCER" ]]; then
    exec "$WORKFLOW_ENFORCER"
else
    echo "Workflow system not installed"
    exit 1
fi
EOF

    chmod +x "$PROJECT_ROOT/workflow-status"

    log "SUCCESS" "✅ Convenience scripts created:"
    log "INFO" "  • ./workflow [command] - Main workflow control"
    log "INFO" "  • ./workflow-status - Quick status check"
}

# Run installation tests
run_installation_tests() {
    log "INFO" "🧪 Running installation tests..."

    local test_failures=0

    # Test 1: Auto-trigger script exists and is executable
    if [[ -x "$AUTO_TRIGGER_SCRIPT" ]]; then
        log "SUCCESS" "✅ Test 1: Auto-trigger script is executable"
    else
        log "ERROR" "❌ Test 1: Auto-trigger script not executable"
        ((test_failures++))
    fi

    # Test 2: Integration hooks exist and are executable
    if [[ -x "$INTEGRATION_HOOK" && -x "$WORKFLOW_ENFORCER" ]]; then
        log "SUCCESS" "✅ Test 2: Integration hooks are executable"
    else
        log "ERROR" "❌ Test 2: Integration hooks not executable"
        ((test_failures++))
    fi

    # Test 3: Phase tracking initialized
    if [[ -f "$PROJECT_ROOT/.phase/current" ]]; then
        local current_phase=$(cat "$PROJECT_ROOT/.phase/current")
        if [[ "$current_phase" =~ ^[0-7]$ ]]; then
            log "SUCCESS" "✅ Test 3: Phase tracking initialized (Phase $current_phase)"
        else
            log "ERROR" "❌ Test 3: Invalid phase value: $current_phase"
            ((test_failures++))
        fi
    else
        log "ERROR" "❌ Test 3: Phase tracking not initialized"
        ((test_failures++))
    fi

    # Test 4: Configuration file exists
    if [[ -f "$PROJECT_ROOT/.workflow/config.yaml" ]]; then
        log "SUCCESS" "✅ Test 4: Configuration file exists"
    else
        log "ERROR" "❌ Test 4: Configuration file missing"
        ((test_failures++))
    fi

    # Test 5: Hooks registry exists
    if [[ -f "$PROJECT_ROOT/.claude/hooks/hooks_registry.json" ]]; then
        local hook_count=$(jq length "$PROJECT_ROOT/.claude/hooks/hooks_registry.json")
        if [[ $hook_count -ge 2 ]]; then
            log "SUCCESS" "✅ Test 5: Hooks registry has $hook_count hooks registered"
        else
            log "WARN" "⚠️  Test 5: Hooks registry has only $hook_count hooks"
        fi
    else
        log "ERROR" "❌ Test 5: Hooks registry missing"
        ((test_failures++))
    fi

    # Summary
    if [[ $test_failures -eq 0 ]]; then
        log "SUCCESS" "🎉 All installation tests passed!"
        return 0
    else
        log "ERROR" "💥 $test_failures tests failed!"
        return 1
    fi
}

# Show installation summary
show_installation_summary() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}          ${CYAN}Claude Enhancer 5.0 Auto-Trigger System${NC}          ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}                    ${GREEN}Installation Complete${NC}                    ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${GREEN}📦 Installed Components:${NC}"
    echo "  • Auto-trigger system with file watching"
    echo "  • Phase-based workflow enforcement"
    echo "  • SystemPrompt hooks for Claude Code guidance"
    echo "  • Integration with existing .claude/hooks/ system"
    echo "  • Systemd service for persistence"
    echo "  • Convenience wrapper scripts"
    echo ""

    echo -e "${BLUE}🚀 Quick Start:${NC}"
    echo "  1. Start the system:    ./workflow start"
    echo "  2. Check status:        ./workflow status"
    echo "  3. View current phase:  ./workflow-status"
    echo "  4. Set phase manually:  ./workflow set-phase <0-7>"
    echo ""

    echo -e "${YELLOW}📋 Workflow Phases (0-7):${NC}"
    echo "  Phase 0: Branch Creation     │ Phase 4: Local Testing"
    echo "  Phase 1: Requirements        │ Phase 5: Code Commit"
    echo "  Phase 2: Design Planning     │ Phase 6: Code Review"
    echo "  Phase 3: Implementation      │ Phase 7: Merge & Deploy"
    echo ""

    echo -e "${PURPLE}💎 Key Features:${NC}"
    echo "  • Automatic phase detection based on file changes"
    echo "  • Real-time workflow guidance for Claude Code"
    echo "  • Non-blocking advisory system"
    echo "  • 4-6-8 Agent orchestration enforcement in Phase 3"
    echo "  • Auto-cleanup at Phase 5 and 7"
    echo "  • Integration with existing quality gates"
    echo ""

    local current_phase=$(cat "$PROJECT_ROOT/.phase/current" 2>/dev/null || echo "0")
    echo -e "${CYAN}🎯 Current Phase: $current_phase${NC}"
    echo ""

    echo -e "${GREEN}✨ Ready to enhance your Claude Code workflow experience!${NC}"
}

# Main installation flow
main() {
    echo -e "${CYAN}🚀 Starting Claude Enhancer 5.0 Auto-Trigger Installation...${NC}"
    echo ""

    # Installation steps
    check_prerequisites
    setup_directories
    install_auto_trigger
    install_integration_hooks
    install_systemd_service
    create_convenience_scripts

    echo ""
    log "INFO" "🧪 Running post-installation tests..."

    if run_installation_tests; then
        show_installation_summary

        # Offer to start the system
        echo ""
        read -p "Start the auto-trigger system now? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "INFO" "🎬 Starting auto-trigger system..."
            "$AUTO_TRIGGER_SCRIPT" start &
            sleep 2
            "$AUTO_TRIGGER_SCRIPT" status
        fi
    else
        log "ERROR" "Installation completed with errors. Please review the test failures above."
        exit 1
    fi
}

# Handle command line arguments
case "${1:-install}" in
    "install")
        main
        ;;
    "uninstall")
        log "INFO" "🗑️  Uninstalling auto-trigger system..."
        # Stop the system if running
        if [[ -f "$PROJECT_ROOT/.workflow/file_watcher.pid" ]]; then
            "$AUTO_TRIGGER_SCRIPT" stop
        fi
        # Remove systemd service
        systemctl --user stop claude-enhancer-auto-trigger 2>/dev/null || true
        systemctl --user disable claude-enhancer-auto-trigger 2>/dev/null || true
        rm -f "$HOME/.config/systemd/user/claude-enhancer-auto-trigger.service"
        # Remove convenience scripts
        rm -f "$PROJECT_ROOT/workflow" "$PROJECT_ROOT/workflow-status"
        log "SUCCESS" "✅ Auto-trigger system uninstalled"
        ;;
    "reinstall")
        "$0" uninstall
        sleep 2
        "$0" install
        ;;
    *)
        echo "Usage: $0 {install|uninstall|reinstall}"
        echo ""
        echo "Commands:"
        echo "  install    - Install the auto-trigger system (default)"
        echo "  uninstall  - Remove the auto-trigger system"
        echo "  reinstall  - Uninstall and reinstall the system"
        ;;
esac