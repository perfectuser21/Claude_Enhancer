#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer Smart Agent Selector (Simple Fixed Version)

set -e

# Read input
INPUT=$(cat)

# Extract task description
TASK_DESC=$(echo "$INPUT" | grep -oP '"prompt"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
if [ -z "$TASK_DESC" ]; then
    TASK_DESC=$(echo "$INPUT" | grep -oP '"description"\s*:\s*"[^"]+' | cut -d'"' -f4 || echo "")
fi

# Convert to lowercase for matching
TASK_LOWER=$(echo "$TASK_DESC" | tr '[:upper:]' '[:lower:]')

# Determine complexity
determine_complexity() {
    local desc="$1"

    # Complex task keywords (8 agents)
    if echo "$desc" | grep -qE "architect|design system|integrate|migrate|refactor entire|complex"; then
        echo "complex"
        return
    fi

    # Simple task keywords (4 agents)
    if echo "$desc" | grep -qE "fix bug|typo|minor|quick|simple|small change"; then
        echo "simple"
        return
    fi

    # Default standard task (6 agents)
    echo "standard"
}

# Main logic
if [ -n "$TASK_DESC" ]; then
    COMPLEXITY=$(determine_complexity "$TASK_LOWER")

    echo "Agent Selection: $COMPLEXITY task detected" >&2
    echo "Task: $(echo "$TASK_DESC" | head -c 50)..." >&2

    case "$COMPLEXITY" in
        simple)
            echo "4 Agents recommended" >&2
            ;;
        complex)
            echo "8 Agents recommended" >&2
            ;;
        *)
            echo "6 Agents recommended" >&2
            ;;
    esac

    # Safe logging with file lock
    {
        flock -x 200
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Complexity: $COMPLEXITY" >> /tmp/claude_agent_selection.log
    } 200>/tmp/claude_agent_selection.log.lock 2>/dev/null || true
fi

# Output original content
echo "$INPUT"
exit 0