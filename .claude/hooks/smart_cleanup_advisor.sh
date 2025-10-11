#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 智能清理顾问

TEMP_FILES=$(find . -name "*.tmp" -o -name "*.log" -o -name "*~" 2>/dev/null | wc -l)

if [[ $TEMP_FILES -gt 20 ]]; then
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo "🧹 Smart Cleanup Advisor"
        echo "━━━━━━━━━━━━━━━━━━━━━"
        echo "发现 $TEMP_FILES 个临时文件"
        echo "建议运行清理脚本"
        echo "━━━━━━━━━━━━━━━━━━━━━"
    elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
        echo "[Cleanup] ${TEMP_FILES}个临时文件"
    fi
fi

exit 0
