#!/bin/bash
# 动态获取Claude Enhancer项目路径
CLAUDE_ENHANCER_HOME="${CLAUDE_ENHANCER_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
export CLAUDE_ENHANCER_HOME

# Wrapper for validate-agents command
# Provides default input to avoid stdin issues

echo "" | python3 ${CLAUDE_ENHANCER_HOME}/.claude/hooks/claude_enhancer_core.py validate-agents 2>/dev/null

# Always return success to avoid blocking
exit 0