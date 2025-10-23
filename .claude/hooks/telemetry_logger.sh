#!/usr/bin/env bash
# ==============================================================================
# CE Telemetry Logger Hook
# Purpose: Log workflow events to JSONL for dashboard monitoring
# Version: 7.1.2
# Trigger: PostToolUse (after every Claude Code tool execution)
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVENTS_FILE="${PROJECT_ROOT}/.temp/ce_events.jsonl"
MAX_FILE_SIZE=$((10 * 1024 * 1024))  # 10MB in bytes
PROJECT_NAME="Claude Enhancer"

# Ensure .temp directory exists
mkdir -p "${PROJECT_ROOT}/.temp"

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

# Generate ISO 8601 timestamp
get_timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Escape JSON string (replace quotes and newlines)
escape_json() {
    local str="$1"
    # Replace backslash first, then quotes, then newlines
    str="${str//\\/\\\\}"
    str="${str//\"/\\\"}"
    str="${str//$'\n'/\\n}"
    str="${str//$'\r'/\\r}"
    str="${str//$'\t'/\\t}"
    echo "$str"
}

# Log event to JSONL file
log_event() {
    local event_type="$1"
    local task_name="${2:-}"
    local phase_id="${3:-}"
    local phase_name="${4:-}"
    local metadata="${5:-{}}"

    local timestamp
    timestamp="$(get_timestamp)"

    # Build JSON manually (no jq dependency)
    local json_line
    json_line="{"
    json_line+="\"timestamp\":\"${timestamp}\","
    json_line+="\"event_type\":\"${event_type}\","
    json_line+="\"project_name\":\"$(escape_json "$PROJECT_NAME")\","
    json_line+="\"task_name\":\"$(escape_json "$task_name")\""

    if [[ -n "$phase_id" ]]; then
        json_line+=",\"phase_id\":\"$(escape_json "$phase_id")\""
    else
        json_line+=",\"phase_id\":null"
    fi

    if [[ -n "$phase_name" ]]; then
        json_line+=",\"phase_name\":\"$(escape_json "$phase_name")\""
    else
        json_line+=",\"phase_name\":null"
    fi

    json_line+=",\"metadata\":${metadata}"
    json_line+="}"

    # Append to JSONL file with file locking
    (
        flock -n 200 || exit 0  # Non-blocking lock, skip if busy
        echo "$json_line" >> "$EVENTS_FILE"
    ) 200>"${EVENTS_FILE}.lock"
}

# Rotate JSONL file if it exceeds MAX_FILE_SIZE
rotate_if_needed() {
    if [[ ! -f "$EVENTS_FILE" ]]; then
        return 0
    fi

    local file_size
    file_size=$(stat -c%s "$EVENTS_FILE" 2>/dev/null || stat -f%z "$EVENTS_FILE" 2>/dev/null || echo 0)

    if (( file_size >= MAX_FILE_SIZE )); then
        local timestamp
        timestamp=$(date -u +"%Y%m%d_%H%M%S")
        local archive_file="${EVENTS_FILE%.jsonl}_${timestamp}.jsonl.gz"

        # Rotate with file locking
        (
            flock -n 200 || exit 0  # Non-blocking lock, skip if busy
            if [[ -f "$EVENTS_FILE" ]]; then
                gzip -c "$EVENTS_FILE" > "$archive_file" 2>/dev/null || true
                > "$EVENTS_FILE"  # Truncate file
            fi
        ) 200>"${EVENTS_FILE}.lock"
    fi
}

# ------------------------------------------------------------------------------
# Main Logic
# ------------------------------------------------------------------------------

main() {
    # Always rotate first (if needed)
    rotate_if_needed || true

    # Extract context from environment variables (set by Claude Code hooks system)
    local tool_name="${TOOL_NAME:-unknown}"
    local current_phase="${CURRENT_PHASE:-}"
    local task_name="${TASK_NAME:-Untitled Task}"

    # Detect event type based on tool usage patterns
    local event_type="unknown"
    local metadata="{}"

    # Task lifecycle events
    if [[ "$tool_name" == "TodoWrite" ]]; then
        # Detect task start/phase transitions from todo list updates
        if [[ -n "$current_phase" ]]; then
            if [[ "$current_phase" =~ ^Phase\ *1 ]]; then
                event_type="task_start"
            elif [[ "$current_phase" =~ Phase ]]; then
                event_type="phase_start"
                local phase_num="${current_phase//[^0-9]/}"
                local phase_id="Phase${phase_num}"
                local phase_name
                case "$phase_num" in
                    1) phase_name="Discovery & Planning" ;;
                    2) phase_name="Implementation" ;;
                    3) phase_name="Testing" ;;
                    4) phase_name="Review" ;;
                    5) phase_name="Release" ;;
                    6) phase_name="Acceptance" ;;
                    7) phase_name="Closure" ;;
                    *) phase_name="Unknown" ;;
                esac
                log_event "$event_type" "$task_name" "$phase_id" "$phase_name" "$metadata" || true
                exit 0
            fi
        fi
    fi

    # Error events (detect from Bash tool failures)
    if [[ "$tool_name" == "Bash" && -n "${ERROR_MESSAGE:-}" ]]; then
        event_type="error"
        metadata="{\"error_type\":\"bash_error\",\"error_message\":\"$(escape_json "${ERROR_MESSAGE}")\"}"
    fi

    # Generic tool usage logging (optional, can be disabled for MVP)
    # Uncomment to log all tool usage:
    # metadata="{\"tool_name\":\"$(escape_json "$tool_name")\"}"
    # log_event "tool_use" "$task_name" "$current_phase" "" "$metadata" || true

    # Log the event (always non-blocking)
    if [[ "$event_type" != "unknown" ]]; then
        log_event "$event_type" "$task_name" "$current_phase" "" "$metadata" || true
    fi

    exit 0  # Always exit 0 to not block workflow
}

# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------

# Always exit 0 even if main() fails (non-blocking hook)
main "$@" || exit 0
