#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 智能Git工作流

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "🔀 Smart Git Workflow"
    echo "━━━━━━━━━━━━━━━━━━━"
    echo "当前分支: $CURRENT_BRANCH"

    if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
        echo "⚠️ 在主分支上，建议创建feature分支"
    else
        echo "✅ 在feature分支上"
    fi
    echo "━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
        echo "[Git] ⚠️ 主分支"
    else
        echo "[Git] ✅ $CURRENT_BRANCH"
    fi
fi

exit 0
