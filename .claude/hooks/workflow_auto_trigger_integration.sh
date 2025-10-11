#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 工作流自动触发集成

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "⚡ Workflow Auto Trigger"
    echo "━━━━━━━━━━━━━━━━━━━━━"
    echo "监控工作流触发条件..."
    echo "━━━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Trigger] 监控中"
fi

exit 0
