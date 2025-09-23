#!/bin/bash
# Hook Wrapper with Timeout Protection and Error Handling
# Usage: hook_wrapper.sh <hook_script> [timeout_seconds]

set -e

HOOK_SCRIPT="$1"
TIMEOUT_SECONDS="${2:-5}"  # Default 5 second timeout
HOOK_NAME=$(basename "$HOOK_SCRIPT" .sh)

# Validate hook script exists
if [[ ! -f "$HOOK_SCRIPT" ]]; then
    echo "ERROR: Hook script not found: $HOOK_SCRIPT" >&2
    exit 1
fi

# Read input
INPUT=$(cat)

# Create temp file for input
TEMP_INPUT=$(mktemp)
echo "$INPUT" > "$TEMP_INPUT"

# Execute hook with timeout protection
execute_hook_with_timeout() {
    timeout "$TIMEOUT_SECONDS" bash "$HOOK_SCRIPT" < "$TEMP_INPUT" 2>&1
}

# Main execution with error handling
if ! OUTPUT=$(execute_hook_with_timeout); then
    EXIT_CODE=$?

    # Cleanup temp file
    rm -f "$TEMP_INPUT"

    case $EXIT_CODE in
        124)
            echo "WARNING: Hook $HOOK_NAME timed out after ${TIMEOUT_SECONDS}s" >&2
            ;;
        *)
            echo "WARNING: Hook $HOOK_NAME failed with exit code $EXIT_CODE" >&2
            echo "Error output: $OUTPUT" >&2
            ;;
    esac

    # For non-blocking hooks, output original input on failure
    echo "$INPUT"
    exit 0
else
    # Success - output hook result
    echo "$OUTPUT"
    rm -f "$TEMP_INPUT"
    exit 0
fi