#!/bin/bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] HOOK TRIGGERED!" >> /tmp/hook_trigger_test.log
echo "Hook is working! Input received." >&2
cat  # Pass through the input
exit 0