#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 并行Agent高亮器

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "🌈 Parallel Agent Highlighter"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💡 提醒：所有Agent应该并行执行"
    echo "  ✅ 正确：在同一function_calls块中"
    echo "  ❌ 错误：分开调用Agent"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Parallel] Agents并行提醒"
fi

exit 0
