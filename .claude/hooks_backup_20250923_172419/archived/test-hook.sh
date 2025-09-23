#!/bin/bash
echo "[$(date)] Hook triggered!" >> /tmp/hook_test.log
echo "🎯 TEST HOOK IS WORKING!" >&2
exit 0