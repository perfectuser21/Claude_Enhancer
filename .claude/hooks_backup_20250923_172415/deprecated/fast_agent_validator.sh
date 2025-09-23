#!/bin/bash
# High-Performance Agent Validator
# Optimized for minimal latency and resource usage

set -e

# Performance optimization: read input once
INPUT=$(cat)

# Fast exit for non-Task operations
if [[ ! "$INPUT" =~ "subagent_type" ]]; then
    echo "$INPUT"
    exit 0
fi

# Use the optimized Python dispatcher
exec python3 /home/xx/dev/Claude Enhancer/.claude/hooks/performance_optimized_dispatcher.py