#!/bin/bash

LOG_FILE="/tmp/claude_hook_debug.log"
echo "===== HOOK DEBUG START $(date) =====" >> "$LOG_FILE"
echo "PWD: $(pwd)" >> "$LOG_FILE"
echo "Script: $0" >> "$LOG_FILE"
echo "Args: $@" >> "$LOG_FILE"
echo "ENV CLAUDE_TOOL: ${CLAUDE_TOOL:-not set}" >> "$LOG_FILE"
echo "ENV CLAUDE_INPUT: ${CLAUDE_INPUT:-not set}" >> "$LOG_FILE"
echo "Working Directory: $(pwd)" >> "$LOG_FILE"
echo "Settings file exists: $([ -f .claude/settings.json ] && echo 'YES' || echo 'NO')" >> "$LOG_FILE"

# Also output to stderr so Claude can see it
echo "🔧 Debug Hook Triggered at $(date)" >&2
echo "📁 Working Directory: $(pwd)" >&2
echo "🎯 Tool: ${CLAUDE_TOOL:-none}" >&2

exit 0