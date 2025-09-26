#!/bin/bash

# ================================================================
# Tool Validator Module
# Claude Enhancer 5.0 - Phase-based tool usage validation
# ================================================================

set -euo pipefail

# Tool-specific validation functions
validate_task_tool() {
    local phase="$1"
    local context="$2"

    case "$phase" in
        "P0"|"P1"|"P2"|"P4"|"P5"|"P6")
            echo "Task tool not allowed in phase $phase"
            return 1
            ;;
        "P3")
            # Check agent count for Task tool
            local agent_count=$(echo "$context" | jq -r '.agent_count // 1' 2>/dev/null)
            if [[ "$agent_count" -lt 4 ]]; then
                echo "P3 requires minimum 4 agents, got $agent_count"
                return 1
            fi
            if [[ "$agent_count" -gt 8 ]]; then
                echo "P3 allows maximum 8 agents, got $agent_count"
                return 1
            fi
            return 0
            ;;
        *)
            return 0
            ;;
    esac
}

validate_write_tool() {
    local phase="$1"
    local context="$2"

    case "$phase" in
        "P0"|"P1"|"P5"|"P6")
            echo "Write tool not allowed in phase $phase"
            return 1
            ;;
        *)
            return 0
            ;;
    esac
}

validate_bash_tool() {
    local phase="$1"
    local context="$2"

    local command=$(echo "$context" | jq -r '.command // ""' 2>/dev/null)

    case "$phase" in
        "P0")
            if [[ "$command" =~ ^git\ ]] || [[ "$command" =~ checkout|branch|status ]]; then
                return 0
            else
                echo "P0 only allows git commands, got: $command"
                return 1
            fi
            ;;
        "P1"|"P2")
            echo "Bash tool not allowed in phase $phase"
            return 1
            ;;
        "P3")
            echo "Bash tool not allowed in P3 (use Task instead)"
            return 1
            ;;
        "P4")
            if [[ "$command" =~ test|npm\ test|pytest|jest|mocha ]]; then
                return 0
            else
                echo "P4 only allows test commands, got: $command"
                return 1
            fi
            ;;
        "P5"|"P6")
            if [[ "$command" =~ ^git\ ]] || [[ "$command" =~ commit|push|merge|pr\ create ]]; then
                return 0
            else
                echo "P5/P6 only allow git commands, got: $command"
                return 1
            fi
            ;;
        *)
            return 0
            ;;
    esac
}

# Main validation function
validate_tool_usage() {
    local tool="$1"
    local phase="$2"
    local context="$3"

    case "$tool" in
        "Task")
            validate_task_tool "$phase" "$context"
            ;;
        "Write"|"MultiEdit")
            validate_write_tool "$phase" "$context"
            ;;
        "Bash")
            validate_bash_tool "$phase" "$context"
            ;;
        "Read"|"Grep"|"Glob")
            # These are generally allowed in all phases
            return 0
            ;;
        *)
            echo "Unknown tool: $tool"
            return 1
            ;;
    esac
}

# Export function for use in main controller
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    export -f validate_tool_usage
fi