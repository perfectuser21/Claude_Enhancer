#!/bin/bash
# State Manager - Single Source of Truth for Claude Enhancer
# Provides read/write operations for .workflow/state.json
#
# Usage:
#   source scripts/state_manager.sh
#   state_get "current_phase.phase"
#   state_set "current_phase.phase" "Phase2"
#   state_update_timestamp

set -euo pipefail

STATE_FILE="${STATE_FILE:-.workflow/state.json}"
PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
STATE_PATH="$PROJECT_ROOT/$STATE_FILE"

# ============================================
# Utility Functions
# ============================================

# Check if jq is available
check_jq() {
    if ! command -v jq &>/dev/null; then
        echo "❌ ERROR: jq is required but not installed" >&2
        echo "Install: sudo apt-get install jq" >&2
        return 1
    fi
}

# Initialize state file if it doesn't exist
state_init() {
    if [[ ! -f "$STATE_PATH" ]]; then
        mkdir -p "$(dirname "$STATE_PATH")"
        cat > "$STATE_PATH" <<'EOF'
{
  "version": "1.0.0",
  "last_updated": null,
  "current_phase": {"phase": "Phase1", "substage": null, "started_at": null, "last_checkpoint": null, "progress_percent": 0},
  "current_task": {"branch": null, "task_id": null, "title": null, "started_at": null, "documents": {}},
  "quality_gates": {"gate1_phase3": {"passed": false, "checks": {}}, "gate2_phase4": {"passed": false, "checks": {}}},
  "version_control": {"current_version": "8.6.1", "files_in_sync": true},
  "system_health": {"hooks_count": 0, "scripts_count": 0, "docs_count": 0},
  "workflow_metrics": {"total_tasks_completed": 0},
  "immutable_kernel": {"enabled": true, "mode": "strict", "files": []},
  "change_scope": {"enabled": false, "current_scope": []},
  "lane_enforcer": {"enabled": false, "current_lane": "planning"}
}
EOF
        echo "✓ Initialized state file: $STATE_PATH"
    fi
}

# ============================================
# Read Operations
# ============================================

# Get value from state
# Usage: state_get "current_phase.phase"
state_get() {
    local path="$1"
    check_jq || return 1
    state_init

    jq -r ".${path}" "$STATE_PATH" 2>/dev/null || echo "null"
}

# Get entire state as JSON
state_get_all() {
    check_jq || return 1
    state_init

    cat "$STATE_PATH"
}

# Check if state exists
state_exists() {
    [[ -f "$STATE_PATH" ]]
}

# ============================================
# Write Operations
# ============================================

# Set value in state
# Usage: state_set "current_phase.phase" "Phase2"
state_set() {
    local path="$1"
    local value="$2"
    check_jq || return 1
    state_init

    # Determine if value is string or other type
    local json_value
    if [[ "$value" =~ ^[0-9]+$ ]]; then
        # Number
        json_value="$value"
    elif [[ "$value" == "true" ]] || [[ "$value" == "false" ]]; then
        # Boolean
        json_value="$value"
    elif [[ "$value" == "null" ]]; then
        # Null
        json_value="null"
    else
        # String (quote it)
        json_value="\"$value\""
    fi

    # Use jq to update
    local tmp_file
    tmp_file=$(mktemp)
    jq ".${path} = ${json_value}" "$STATE_PATH" > "$tmp_file"
    mv "$tmp_file" "$STATE_PATH"

    state_update_timestamp
}

# Update last_updated timestamp
state_update_timestamp() {
    check_jq || return 1

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local tmp_file
    tmp_file=$(mktemp)
    jq ".last_updated = \"$timestamp\"" "$STATE_PATH" > "$tmp_file"
    mv "$tmp_file" "$STATE_PATH"
}

# Increment a numeric value
# Usage: state_increment "system_health.hooks_count"
state_increment() {
    local path="$1"
    check_jq || return 1
    state_init

    local current_value
    current_value=$(state_get "$path")
    local new_value=$((current_value + 1))

    state_set "$path" "$new_value"
}

# ============================================
# Phase Management
# ============================================

# Set current phase
# Usage: state_set_phase "Phase2"
state_set_phase() {
    local phase="$1"
    check_jq || return 1

    # Validate phase
    if [[ ! "$phase" =~ ^Phase[1-7]$ ]]; then
        echo "❌ ERROR: Invalid phase: $phase" >&2
        echo "Valid phases: Phase1-Phase7" >&2
        return 1
    fi

    state_set "current_phase.phase" "$phase"

    # Update started_at if not already set for this phase
    local started_at
    started_at=$(state_get "current_phase.started_at")
    if [[ "$started_at" == "null" ]]; then
        local timestamp
        timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        state_set "current_phase.started_at" "$timestamp"
    fi

    echo "✓ Phase set to: $phase"
}

# Get current phase
state_get_phase() {
    state_get "current_phase.phase"
}

# Set phase substage (for Phase 1)
# Usage: state_set_substage "1.3"
state_set_substage() {
    local substage="$1"
    state_set "current_phase.substage" "$substage"
}

# ============================================
# Quality Gate Management
# ============================================

# Mark quality gate as passed
# Usage: state_pass_gate "gate1_phase3"
state_pass_gate() {
    local gate="$1"
    check_jq || return 1

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    state_set "quality_gates.${gate}.passed" "true"
    state_set "quality_gates.${gate}.passed_at" "$timestamp"

    echo "✓ Quality gate passed: $gate"
}

# Check if gate passed
# Usage: state_is_gate_passed "gate1_phase3"
state_is_gate_passed() {
    local gate="$1"
    local passed
    passed=$(state_get "quality_gates.${gate}.passed")
    [[ "$passed" == "true" ]]
}

# ============================================
# Task Management
# ============================================

# Start new task
# Usage: state_start_task "feature/new-feature" "Implement X"
state_start_task() {
    local branch="$1"
    local title="$2"
    check_jq || return 1

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    local task_id
    task_id="TASK-$(date +%Y%m%d-%H%M%S)"

    state_set "current_task.branch" "$branch"
    state_set "current_task.task_id" "$task_id"
    state_set "current_task.title" "$title"
    state_set "current_task.started_at" "$timestamp"

    # Reset phase to Phase1
    state_set_phase "Phase1"

    echo "✓ Task started: $task_id - $title"
}

# Complete task
state_complete_task() {
    check_jq || return 1

    # Increment task counter
    state_increment "workflow_metrics.total_tasks_completed"

    # Clear current task
    state_set "current_task.branch" "null"
    state_set "current_task.task_id" "null"
    state_set "current_task.title" "null"

    echo "✓ Task completed"
}

# ============================================
# System Health
# ============================================

# Update system health metrics
state_update_health() {
    check_jq || return 1

    # Count hooks
    local hooks_count
    hooks_count=$(find .claude/hooks -type f -name "*.sh" 2>/dev/null | wc -l || echo 0)
    state_set "system_health.hooks_count" "$hooks_count"

    # Count scripts
    local scripts_count
    scripts_count=$(find scripts -type f -name "*.sh" 2>/dev/null | wc -l || echo 0)
    state_set "system_health.scripts_count" "$scripts_count"

    # Count root docs
    local docs_count
    docs_count=$(find . -maxdepth 1 -type f -name "*.md" 2>/dev/null | wc -l || echo 0)
    state_set "system_health.docs_count" "$docs_count"

    # .temp size
    local temp_size_mb
    if [[ -d ".temp" ]]; then
        temp_size_mb=$(du -sm .temp 2>/dev/null | cut -f1 || echo 0)
    else
        temp_size_mb=0
    fi
    state_set "system_health.temp_dir_size_mb" "$temp_size_mb"

    echo "✓ System health updated: $hooks_count hooks, $scripts_count scripts, $docs_count docs"
}

# ============================================
# Validation
# ============================================

# Validate state against schema
state_validate() {
    check_jq || return 1
    state_init

    local schema_file="$PROJECT_ROOT/.workflow/state.schema.json"
    if [[ ! -f "$schema_file" ]]; then
        echo "⚠️  Warning: Schema file not found: $schema_file" >&2
        return 0
    fi

    # Basic validation (jq can parse it)
    if ! jq empty "$STATE_PATH" 2>/dev/null; then
        echo "❌ ERROR: state.json is not valid JSON" >&2
        return 1
    fi

    echo "✓ State file is valid JSON"
    return 0
}

# ============================================
# Display
# ============================================

# Show current state summary
state_show() {
    check_jq || return 1
    state_init

    echo "════════════════════════════════════════════"
    echo "  Claude Enhancer - Current State"
    echo "════════════════════════════════════════════"
    echo ""
    echo "Phase: $(state_get 'current_phase.phase')"
    echo "Substage: $(state_get 'current_phase.substage')"
    echo "Task: $(state_get 'current_task.title')"
    echo "Branch: $(state_get 'current_task.branch')"
    echo ""
    echo "Quality Gates:"
    echo "  Gate 1 (Phase 3): $(state_get 'quality_gates.gate1_phase3.passed')"
    echo "  Gate 2 (Phase 4): $(state_get 'quality_gates.gate2_phase4.passed')"
    echo ""
    echo "System Health:"
    echo "  Hooks: $(state_get 'system_health.hooks_count')"
    echo "  Scripts: $(state_get 'system_health.scripts_count')"
    echo "  Root Docs: $(state_get 'system_health.docs_count')"
    echo ""
    echo "Last Updated: $(state_get 'last_updated')"
    echo "════════════════════════════════════════════"
}

# ============================================
# Main (if run directly)
# ============================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being run directly, not sourced
    case "${1:-}" in
        get)
            state_get "$2"
            ;;
        set)
            state_set "$2" "$3"
            ;;
        phase)
            if [[ -n "${2:-}" ]]; then
                state_set_phase "$2"
            else
                state_get_phase
            fi
            ;;
        show)
            state_show
            ;;
        validate)
            state_validate
            ;;
        health)
            state_update_health
            ;;
        *)
            echo "State Manager - Single Source of Truth"
            echo ""
            echo "Usage:"
            echo "  $0 get <path>           - Get value"
            echo "  $0 set <path> <value>   - Set value"
            echo "  $0 phase [phase]        - Get/set current phase"
            echo "  $0 show                 - Show state summary"
            echo "  $0 validate             - Validate state.json"
            echo "  $0 health               - Update system health metrics"
            echo ""
            echo "Or source this file to use functions:"
            echo "  source scripts/state_manager.sh"
            echo "  state_get 'current_phase.phase'"
            exit 1
            ;;
    esac
fi
