#!/bin/bash
# 动态获取Claude Enhancer项目路径
CLAUDE_ENHANCER_HOME="${CLAUDE_ENHANCER_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
export CLAUDE_ENHANCER_HOME

# Claude Enhancer Pre-Task Hook Wrapper
# 在Task执行前运行所有Claude Enhancer验证

exec bash ${CLAUDE_ENHANCER_HOME}/.claude/hooks/claude_enhancer_master.sh
