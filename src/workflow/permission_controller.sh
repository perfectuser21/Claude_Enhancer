#!/bin/bash

# ================================================================
# Claude Enhancer 5.0 - Phase Permission Controller
# Advanced workflow phase access control system
# ================================================================
#
# Features:
# 1. Phase-based tool restriction
# 2. File modification whitelist control
# 3. Agent parallel execution limits
# 4. Permission violation reporting
# 5. Security audit logging
#
# Architecture:
# - Rule-based permission engine
# - Real-time violation detection
# - Configurable restriction policies
# - Comprehensive audit trails
#
# Author: Claude Code Backend Architect
# Version: 5.0.0
# ================================================================

set -euo pipefail

# ================================================================
# GLOBAL CONFIGURATION
# ================================================================

# Script metadata
readonly SCRIPT_NAME="permission_controller"
readonly VERSION="5.0.0"
readonly LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Directories
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
readonly LOG_DIR="${PROJECT_ROOT}/.claude/logs"
readonly CONFIG_DIR="${PROJECT_ROOT}/.claude/config"
readonly CACHE_DIR="${PROJECT_ROOT}/.claude/cache"

# Configuration files
readonly PERMISSION_CONFIG="${CONFIG_DIR}/permission_rules.json"
readonly PHASE_CONFIG="${CONFIG_DIR}/phase_definitions.json"
readonly AUDIT_LOG="${LOG_DIR}/permission_audit.log"
readonly VIOLATION_LOG="${LOG_DIR}/permission_violations.log"

# Create necessary directories
mkdir -p "$LOG_DIR" "$CONFIG_DIR" "$CACHE_DIR"

# ================================================================
# LOGGING SYSTEM
# ================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S.%3N')

    # Color codes for different log levels
    case "$level" in
        "ERROR")   echo -e "\e[31m[$timestamp] ERROR: $message\e[0m" >&2 ;;
        "WARN")    echo -e "\e[33m[$timestamp] WARN:  $message\e[0m" >&2 ;;
        "INFO")    echo -e "\e[32m[$timestamp] INFO:  $message\e[0m" ;;
        "DEBUG")   [[ "$LOG_LEVEL" == "DEBUG" ]] && echo -e "\e[36m[$timestamp] DEBUG: $message\e[0m" ;;
    esac

    # Always log to audit file
    echo "[$timestamp] [$level] $message" >> "$AUDIT_LOG"
}

log_violation() {
    local phase="$1"
    local tool="$2"
    local violation_type="$3"
    local details="$4"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S.%3N')

    local violation_entry=$(cat <<EOF
{
    "timestamp": "$timestamp",
    "phase": "$phase",
    "tool": "$tool",
    "violation_type": "$violation_type",
    "details": "$details",
    "severity": "HIGH",
    "action_taken": "BLOCKED"
}
EOF
)

    echo "$violation_entry" >> "$VIOLATION_LOG"
    log "ERROR" "PERMISSION VIOLATION: Phase=$phase, Tool=$tool, Type=$violation_type, Details=$details"
}

# ================================================================
# CONFIGURATION MANAGEMENT
# ================================================================

# Initialize default permission configuration if not exists
init_permission_config() {
    if [[ ! -f "$PERMISSION_CONFIG" ]]; then
        log "INFO" "Creating default permission configuration"
        cat > "$PERMISSION_CONFIG" <<'EOF'
{
  "version": "5.0.0",
  "description": "Claude Enhancer 5.0 Phase Permission Rules",
  "phases": {
    "P0": {
      "name": "Branch Creation",
      "allowed_tools": ["Bash", "Read"],
      "forbidden_tools": ["Write", "MultiEdit", "Task"],
      "max_agents": 0,
      "file_whitelist": [".git/**", ".gitignore", "README.md"],
      "file_blacklist": ["src/**/*.js", "src/**/*.py", "**/*.config.*"],
      "restrictions": {
        "no_code_modification": true,
        "git_operations_only": true,
        "branch_operations_only": true
      }
    },
    "P1": {
      "name": "Requirements Analysis",
      "allowed_tools": ["Read", "Grep", "Glob"],
      "forbidden_tools": ["Write", "MultiEdit", "Task", "Bash"],
      "max_agents": 0,
      "file_whitelist": ["**/*.md", "**/*.txt", "**/*.json", ".claude/**"],
      "file_blacklist": ["src/**", "test/**"],
      "restrictions": {
        "read_only_mode": true,
        "no_file_creation": true,
        "analysis_tools_only": true
      }
    },
    "P2": {
      "name": "Design Planning",
      "allowed_tools": ["Read", "Write", "Grep", "Glob"],
      "forbidden_tools": ["Task", "Bash"],
      "max_agents": 2,
      "file_whitelist": ["docs/**", ".claude/**", "**/*.md", "design/**"],
      "file_blacklist": ["src/**/*.js", "src/**/*.py", "test/**"],
      "restrictions": {
        "documentation_only": true,
        "no_implementation": true,
        "design_artifacts_only": true
      }
    },
    "P3": {
      "name": "Implementation",
      "allowed_tools": ["Task", "Write", "MultiEdit", "Read", "Grep", "Glob"],
      "forbidden_tools": ["Bash"],
      "max_agents": 8,
      "file_whitelist": ["src/**", "test/**", ".claude/**", "docs/**"],
      "file_blacklist": [".git/**", "node_modules/**", ".env*"],
      "restrictions": {
        "implementation_mode": true,
        "parallel_agents_required": true,
        "minimum_agents": 4
      }
    },
    "P4": {
      "name": "Local Testing",
      "allowed_tools": ["Bash", "Read", "Write"],
      "forbidden_tools": ["Task"],
      "max_agents": 3,
      "file_whitelist": ["test/**", "src/**", ".claude/**"],
      "file_blacklist": [".git/**", "node_modules/**"],
      "restrictions": {
        "testing_mode": true,
        "test_execution_only": true,
        "limited_code_changes": true
      }
    },
    "P5": {
      "name": "Code Commit",
      "allowed_tools": ["Bash", "Read"],
      "forbidden_tools": ["Write", "MultiEdit", "Task"],
      "max_agents": 0,
      "file_whitelist": [".git/**"],
      "file_blacklist": ["src/**", "test/**", "docs/**"],
      "restrictions": {
        "git_operations_only": true,
        "no_code_modification": true,
        "commit_mode": true
      }
    },
    "P6": {
      "name": "Code Review",
      "allowed_tools": ["Bash", "Read"],
      "forbidden_tools": ["Write", "MultiEdit", "Task"],
      "max_agents": 0,
      "file_whitelist": [".git/**", ".github/**"],
      "file_blacklist": ["src/**", "test/**", "docs/**"],
      "restrictions": {
        "review_mode": true,
        "pr_operations_only": true,
        "no_modifications": true
      }
    }
  },
  "global_restrictions": {
    "sensitive_files": [".env*", "**/*.key", "**/*.pem", "**/secrets/**"],
    "system_files": ["/etc/**", "/usr/**", "/bin/**", "/sbin/**"],
    "max_concurrent_agents": 8,
    "max_file_modifications_per_phase": {
      "P0": 5,
      "P1": 0,
      "P2": 10,
      "P3": 100,
      "P4": 20,
      "P5": 0,
      "P6": 0
    }
  },
  "enforcement": {
    "strict_mode": true,
    "violation_action": "BLOCK",
    "audit_all_operations": true,
    "require_justification": true
  }
}
EOF
        log "INFO" "Default permission configuration created"
    fi
}

# Load permission configuration
load_permission_config() {
    if [[ ! -f "$PERMISSION_CONFIG" ]]; then
        init_permission_config
    fi

    # Validate JSON syntax
    if ! jq empty "$PERMISSION_CONFIG" 2>/dev/null; then
        log "ERROR" "Invalid JSON in permission configuration file"
        return 1
    fi

    log "DEBUG" "Permission configuration loaded successfully"
}

# Get current phase from environment or detection
get_current_phase() {
    # Check environment variable first
    if [[ -n "${CLAUDE_ENHANCER_CURRENT_PHASE:-}" ]]; then
        echo "$CLAUDE_ENHANCER_CURRENT_PHASE"
        return
    fi

    # Check phase state file
    local phase_state_file="${CONFIG_DIR}/phase_state.json"
    if [[ -f "$phase_state_file" ]]; then
        local current_phase=$(jq -r '.current_phase // "P0"' "$phase_state_file" 2>/dev/null)
        if [[ "$current_phase" != "null" ]]; then
            echo "$current_phase"
            return
        fi
    fi

    # Detect phase from git branch and working directory state
    detect_phase_from_context
}

# Detect current phase based on context
detect_phase_from_context() {
    local git_status=""
    local has_uncommitted_changes=false
    local has_staged_changes=false

    # Check git status if in git repository
    if git rev-parse --git-dir >/dev/null 2>&1; then
        git_status=$(git status --porcelain 2>/dev/null || true)
        [[ -n "$git_status" ]] && has_uncommitted_changes=true

        if git diff --cached --quiet 2>/dev/null; then
            has_staged_changes=false
        else
            has_staged_changes=true
        fi
    fi

    # Phase detection logic
    if [[ "$has_staged_changes" == "true" ]]; then
        echo "P5"  # Ready to commit
    elif [[ "$has_uncommitted_changes" == "true" ]]; then
        if [[ -f "${PROJECT_ROOT}/test"* ]] || ls "${PROJECT_ROOT}"/test* >/dev/null 2>&1; then
            echo "P4"  # Testing phase
        else
            echo "P3"  # Implementation phase
        fi
    elif git log --oneline -1 2>/dev/null | grep -q "feat\|fix\|refactor"; then
        echo "P6"  # Code review phase
    else
        echo "P0"  # Default to branch creation
    fi
}

# ================================================================
# PERMISSION VALIDATION ENGINE
# ================================================================

# Check if tool is allowed in current phase
is_tool_allowed() {
    local phase="$1"
    local tool="$2"

    # Load configuration
    load_permission_config || return 1

    # Get allowed tools for phase
    local allowed_tools=$(jq -r ".phases[\"$phase\"].allowed_tools[]? // empty" "$PERMISSION_CONFIG" 2>/dev/null)
    local forbidden_tools=$(jq -r ".phases[\"$phase\"].forbidden_tools[]? // empty" "$PERMISSION_CONFIG" 2>/dev/null)

    # Check forbidden tools first (takes precedence)
    if echo "$forbidden_tools" | grep -q "^$tool$"; then
        log "DEBUG" "Tool '$tool' is explicitly forbidden in phase '$phase'"
        return 1
    fi

    # Check allowed tools
    if echo "$allowed_tools" | grep -q "^$tool$"; then
        log "DEBUG" "Tool '$tool' is allowed in phase '$phase'"
        return 0
    fi

    # If no explicit allow/forbid, check if strict mode
    local strict_mode=$(jq -r '.enforcement.strict_mode // true' "$PERMISSION_CONFIG" 2>/dev/null)
    if [[ "$strict_mode" == "true" ]]; then
        log "DEBUG" "Tool '$tool' not explicitly allowed in strict mode for phase '$phase'"
        return 1
    fi

    log "DEBUG" "Tool '$tool' allowed by default (non-strict mode) in phase '$phase'"
    return 0
}

# Check if file modification is allowed
is_file_modification_allowed() {
    local phase="$1"
    local file_path="$2"

    load_permission_config || return 1

    # Get whitelist and blacklist patterns
    local whitelist_patterns=$(jq -r ".phases[\"$phase\"].file_whitelist[]? // empty" "$PERMISSION_CONFIG" 2>/dev/null)
    local blacklist_patterns=$(jq -r ".phases[\"$phase\"].file_blacklist[]? // empty" "$PERMISSION_CONFIG" 2>/dev/null)
    local global_sensitive_files=$(jq -r '.global_restrictions.sensitive_files[]? // empty' "$PERMISSION_CONFIG" 2>/dev/null)

    # Check global sensitive files first
    while IFS= read -r pattern; do
        [[ -z "$pattern" ]] && continue
        if [[ "$file_path" == $pattern ]]; then
            log "DEBUG" "File '$file_path' matches global sensitive pattern '$pattern'"
            return 1
        fi
    done <<< "$global_sensitive_files"

    # Check blacklist patterns
    while IFS= read -r pattern; do
        [[ -z "$pattern" ]] && continue
        if [[ "$file_path" == $pattern ]]; then
            log "DEBUG" "File '$file_path' matches blacklist pattern '$pattern' in phase '$phase'"
            return 1
        fi
    done <<< "$blacklist_patterns"

    # Check whitelist patterns
    while IFS= read -r pattern; do
        [[ -z "$pattern" ]] && continue
        if [[ "$file_path" == $pattern ]]; then
            log "DEBUG" "File '$file_path' matches whitelist pattern '$pattern' in phase '$phase'"
            return 0
        fi
    done <<< "$whitelist_patterns"

    # If no whitelist match, check if strict mode
    local strict_mode=$(jq -r '.enforcement.strict_mode // true' "$PERMISSION_CONFIG" 2>/dev/null)
    if [[ "$strict_mode" == "true" ]]; then
        log "DEBUG" "File '$file_path' not whitelisted in strict mode for phase '$phase'"
        return 1
    fi

    log "DEBUG" "File '$file_path' allowed by default (non-strict mode) in phase '$phase'"
    return 0
}

# Check agent count limits
is_agent_count_allowed() {
    local phase="$1"
    local agent_count="$2"

    load_permission_config || return 1

    # Get phase-specific limits
    local max_agents=$(jq -r ".phases[\"$phase\"].max_agents // 999" "$PERMISSION_CONFIG" 2>/dev/null)
    local min_agents=$(jq -r ".phases[\"$phase\"].restrictions.minimum_agents // 0" "$PERMISSION_CONFIG" 2>/dev/null)
    local global_max=$(jq -r '.global_restrictions.max_concurrent_agents // 999' "$PERMISSION_CONFIG" 2>/dev/null)

    # Check minimum requirement
    if [[ "$agent_count" -lt "$min_agents" ]]; then
        log "DEBUG" "Agent count $agent_count below minimum $min_agents for phase '$phase'"
        return 1
    fi

    # Check phase-specific maximum
    if [[ "$agent_count" -gt "$max_agents" ]]; then
        log "DEBUG" "Agent count $agent_count exceeds phase maximum $max_agents for phase '$phase'"
        return 1
    fi

    # Check global maximum
    if [[ "$agent_count" -gt "$global_max" ]]; then
        log "DEBUG" "Agent count $agent_count exceeds global maximum $global_max"
        return 1
    fi

    log "DEBUG" "Agent count $agent_count is allowed for phase '$phase'"
    return 0
}

# ================================================================
# MAIN PERMISSION CONTROLLER FUNCTIONS
# ================================================================

# Validate tool usage
validate_tool_usage() {
    local tool="$1"
    local context_data="${2:-{}}"

    local current_phase=$(get_current_phase)
    log "INFO" "Validating tool '$tool' usage in phase '$current_phase'"

    # Check if tool is allowed in current phase
    if ! is_tool_allowed "$current_phase" "$tool"; then
        log_violation "$current_phase" "$tool" "FORBIDDEN_TOOL" "Tool '$tool' not allowed in phase '$current_phase'"
        return 1
    fi

    # Additional context-specific validations
    case "$tool" in
        "Task")
            # Check agent count for Task tool (parallel agent execution)
            local agent_count=$(echo "$context_data" | jq -r '.agent_count // 1' 2>/dev/null)
            if ! is_agent_count_allowed "$current_phase" "$agent_count"; then
                log_violation "$current_phase" "$tool" "AGENT_COUNT_EXCEEDED" "Agent count $agent_count not allowed in phase '$current_phase'"
                return 1
            fi
            ;;
        "Write"|"MultiEdit")
            # Check file modification permissions
            local file_path=$(echo "$context_data" | jq -r '.file_path // ""' 2>/dev/null)
            if [[ -n "$file_path" ]] && ! is_file_modification_allowed "$current_phase" "$file_path"; then
                log_violation "$current_phase" "$tool" "FILE_MODIFICATION_FORBIDDEN" "File '$file_path' modification not allowed in phase '$current_phase'"
                return 1
            fi
            ;;
        "Bash")
            # Check bash command restrictions
            local command=$(echo "$context_data" | jq -r '.command // ""' 2>/dev/null)
            if ! validate_bash_command "$current_phase" "$command"; then
                log_violation "$current_phase" "$tool" "BASH_COMMAND_FORBIDDEN" "Bash command '$command' not allowed in phase '$current_phase'"
                return 1
            fi
            ;;
    esac

    log "INFO" "Tool '$tool' usage validated successfully for phase '$current_phase'"
    return 0
}

# Validate bash command based on phase restrictions
validate_bash_command() {
    local phase="$1"
    local command="$2"

    case "$phase" in
        "P0")
            # Only git operations allowed in P0
            if [[ "$command" =~ ^git ]] || [[ "$command" =~ checkout|branch|status ]]; then
                return 0
            else
                log "DEBUG" "Non-git command '$command' not allowed in P0"
                return 1
            fi
            ;;
        "P1"|"P2")
            # No bash commands in analysis and design phases
            log "DEBUG" "Bash commands not allowed in phase '$phase'"
            return 1
            ;;
        "P4")
            # Only test-related commands in P4
            if [[ "$command" =~ test|npm\ test|pytest|jest|mocha ]]; then
                return 0
            else
                log "DEBUG" "Non-test command '$command' not allowed in P4"
                return 1
            fi
            ;;
        "P5"|"P6")
            # Only git operations in commit and review phases
            if [[ "$command" =~ ^git ]] || [[ "$command" =~ commit|push|merge ]] || [[ "$command" == "pr create" ]]; then
                return 0
            else
                log "DEBUG" "Non-git command '$command' not allowed in phase '$phase'"
                return 1
            fi
            ;;
        *)
            # Default allow for other phases
            return 0
            ;;
    esac
}

# Generate permission violation report
generate_violation_report() {
    local output_file="${1:-${LOG_DIR}/permission_violation_report.json}"
    local start_date="${2:-$(date -d '24 hours ago' '+%Y-%m-%d')}"

    log "INFO" "Generating permission violation report"

    # Initialize report structure
    cat > "$output_file" <<EOF
{
    "report_metadata": {
        "generated_at": "$(date -Iseconds)",
        "report_period": "24 hours",
        "start_date": "$start_date",
        "version": "$VERSION"
    },
    "summary": {},
    "violations_by_phase": {},
    "violations_by_tool": {},
    "detailed_violations": []
}
EOF

    # Process violation log if exists
    if [[ -f "$VIOLATION_LOG" ]]; then
        local total_violations=0
        local violations_by_phase="{}"
        local violations_by_tool="{}"
        local detailed_violations="[]"

        # Count violations by phase and tool
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue

            local violation_data
            if violation_data=$(echo "$line" | jq . 2>/dev/null); then
                local phase=$(echo "$violation_data" | jq -r '.phase')
                local tool=$(echo "$violation_data" | jq -r '.tool')

                ((total_violations++))

                # Count by phase
                local phase_count=$(echo "$violations_by_phase" | jq ".\"$phase\" // 0")
                violations_by_phase=$(echo "$violations_by_phase" | jq ".\"$phase\" = $((phase_count + 1))")

                # Count by tool
                local tool_count=$(echo "$violations_by_tool" | jq ".\"$tool\" // 0")
                violations_by_tool=$(echo "$violations_by_tool" | jq ".\"$tool\" = $((tool_count + 1))")

                # Add to detailed violations
                detailed_violations=$(echo "$detailed_violations" | jq ". + [$violation_data]")
            fi
        done < "$VIOLATION_LOG"

        # Update report with data
        jq --arg total "$total_violations" \
           --argjson by_phase "$violations_by_phase" \
           --argjson by_tool "$violations_by_tool" \
           --argjson detailed "$detailed_violations" \
           '
           .summary.total_violations = ($total | tonumber) |
           .summary.violations_by_phase = $by_phase |
           .summary.violations_by_tool = $by_tool |
           .violations_by_phase = $by_phase |
           .violations_by_tool = $by_tool |
           .detailed_violations = $detailed
           ' "$output_file" > "${output_file}.tmp" && mv "${output_file}.tmp" "$output_file"
    fi

    log "INFO" "Permission violation report generated: $output_file"

    # Display summary
    local total_violations=$(jq -r '.summary.total_violations // 0' "$output_file")
    echo "=================================================="
    echo "PERMISSION VIOLATION REPORT SUMMARY"
    echo "=================================================="
    echo "Total Violations: $total_violations"
    echo "Report Period: $start_date to $(date '+%Y-%m-%d')"
    echo "Report File: $output_file"
    echo "=================================================="

    return 0
}

# ================================================================
# CLI INTERFACE
# ================================================================

# Display usage information
usage() {
    cat <<EOF
Claude Enhancer 5.0 - Phase Permission Controller

USAGE:
    $0 <command> [options]

COMMANDS:
    validate-tool <tool> [context_json]     Validate tool usage in current phase
    check-file <file_path>                  Check if file modification is allowed
    check-agents <count>                    Check if agent count is allowed
    get-phase                               Get current phase
    set-phase <phase>                       Set current phase
    generate-report [output_file]           Generate violation report
    init-config                             Initialize permission configuration
    show-permissions [phase]                Show permissions for phase
    audit-log [lines]                       Show recent audit log entries

EXAMPLES:
    $0 validate-tool Write '{"file_path": "src/main.js"}'
    $0 check-file src/components/App.jsx
    $0 check-agents 6
    $0 set-phase P3
    $0 generate-report ./violations.json

OPTIONS:
    -h, --help          Show this help message
    -v, --version       Show version information
    -d, --debug         Enable debug logging
    --strict            Enable strict mode validation
    --no-audit          Disable audit logging

PHASE REFERENCE:
    P0 - Branch Creation    (git operations only)
    P1 - Requirements       (read-only analysis)
    P2 - Design Planning    (documentation only)
    P3 - Implementation     (4-8 agents, full development)
    P4 - Local Testing      (test execution only)
    P5 - Code Commit        (git operations only)
    P6 - Code Review        (pr operations only)

For more information, see: .claude/WORKFLOW.md
EOF
}

# Show permissions for a specific phase
show_permissions() {
    local phase="${1:-$(get_current_phase)}"

    load_permission_config || return 1

    echo "=================================================="
    echo "PERMISSIONS FOR PHASE: $phase"
    echo "=================================================="

    local phase_data=$(jq ".phases[\"$phase\"]" "$PERMISSION_CONFIG" 2>/dev/null)
    if [[ "$phase_data" == "null" ]]; then
        echo "ERROR: Phase '$phase' not found in configuration"
        return 1
    fi

    echo "Phase Name: $(echo "$phase_data" | jq -r '.name')"
    echo
    echo "Allowed Tools:"
    echo "$phase_data" | jq -r '.allowed_tools[]?' | sed 's/^/  - /'
    echo
    echo "Forbidden Tools:"
    echo "$phase_data" | jq -r '.forbidden_tools[]?' | sed 's/^/  - /'
    echo
    echo "Max Agents: $(echo "$phase_data" | jq -r '.max_agents')"
    echo
    echo "File Whitelist:"
    echo "$phase_data" | jq -r '.file_whitelist[]?' | sed 's/^/  - /'
    echo
    echo "File Blacklist:"
    echo "$phase_data" | jq -r '.file_blacklist[]?' | sed 's/^/  - /'
    echo
    echo "Restrictions:"
    echo "$phase_data" | jq -r '.restrictions | to_entries[] | "  - \(.key): \(.value)"'
    echo "=================================================="
}

# Show recent audit log entries
show_audit_log() {
    local lines="${1:-20}"

    if [[ -f "$AUDIT_LOG" ]]; then
        echo "Recent Audit Log Entries (last $lines lines):"
        echo "=================================================="
        tail -n "$lines" "$AUDIT_LOG"
        echo "=================================================="
    else
        echo "No audit log found at: $AUDIT_LOG"
    fi
}

# Set current phase
set_current_phase() {
    local phase="$1"

    # Validate phase
    load_permission_config || return 1

    if ! jq -e ".phases[\"$phase\"]" "$PERMISSION_CONFIG" >/dev/null 2>&1; then
        log "ERROR" "Invalid phase: $phase"
        return 1
    fi

    # Update phase state file
    local phase_state_file="${CONFIG_DIR}/phase_state.json"
    cat > "$phase_state_file" <<EOF
{
    "current_phase": "$phase",
    "updated_at": "$(date -Iseconds)",
    "updated_by": "${USER:-system}"
}
EOF

    # Set environment variable for current session
    export CLAUDE_ENHANCER_CURRENT_PHASE="$phase"

    log "INFO" "Current phase set to: $phase"
    echo "Current phase set to: $phase"
}

# ================================================================
# MAIN FUNCTION
# ================================================================

main() {
    # Parse global options
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--version)
                echo "$SCRIPT_NAME version $VERSION"
                exit 0
                ;;
            -d|--debug)
                export LOG_LEVEL="DEBUG"
                shift
                ;;
            --strict)
                export CLAUDE_ENHANCER_STRICT_MODE="true"
                shift
                ;;
            --no-audit)
                export CLAUDE_ENHANCER_NO_AUDIT="true"
                shift
                ;;
            -*)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                break
                ;;
        esac
    done

    # Require command
    if [[ $# -eq 0 ]]; then
        echo "ERROR: Command required"
        usage
        exit 1
    fi

    local command="$1"
    shift

    # Initialize configuration
    init_permission_config

    # Execute command
    case "$command" in
        "validate-tool")
            [[ $# -eq 0 ]] && { echo "ERROR: Tool name required"; exit 1; }
            local tool="$1"
            local context_data="${2:-{}}"
            if validate_tool_usage "$tool" "$context_data"; then
                echo "✅ Tool '$tool' usage is allowed"
                exit 0
            else
                echo "❌ Tool '$tool' usage is forbidden"
                exit 1
            fi
            ;;
        "check-file")
            [[ $# -eq 0 ]] && { echo "ERROR: File path required"; exit 1; }
            local file_path="$1"
            local current_phase=$(get_current_phase)
            if is_file_modification_allowed "$current_phase" "$file_path"; then
                echo "✅ File '$file_path' modification allowed in phase '$current_phase'"
                exit 0
            else
                echo "❌ File '$file_path' modification forbidden in phase '$current_phase'"
                exit 1
            fi
            ;;
        "check-agents")
            [[ $# -eq 0 ]] && { echo "ERROR: Agent count required"; exit 1; }
            local agent_count="$1"
            local current_phase=$(get_current_phase)
            if is_agent_count_allowed "$current_phase" "$agent_count"; then
                echo "✅ Agent count '$agent_count' allowed in phase '$current_phase'"
                exit 0
            else
                echo "❌ Agent count '$agent_count' not allowed in phase '$current_phase'"
                exit 1
            fi
            ;;
        "get-phase")
            local current_phase=$(get_current_phase)
            echo "Current phase: $current_phase"
            ;;
        "set-phase")
            [[ $# -eq 0 ]] && { echo "ERROR: Phase required"; exit 1; }
            set_current_phase "$1"
            ;;
        "generate-report")
            local output_file="${1:-${LOG_DIR}/permission_violation_report.json}"
            generate_violation_report "$output_file"
            ;;
        "init-config")
            init_permission_config
            echo "✅ Permission configuration initialized"
            ;;
        "show-permissions")
            local phase="${1:-$(get_current_phase)}"
            show_permissions "$phase"
            ;;
        "audit-log")
            local lines="${1:-20}"
            show_audit_log "$lines"
            ;;
        *)
            echo "ERROR: Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# ================================================================
# SCRIPT EXECUTION
# ================================================================

# Only run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

# ================================================================
# END OF SCRIPT
# ================================================================