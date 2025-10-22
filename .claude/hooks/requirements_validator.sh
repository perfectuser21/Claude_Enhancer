#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# Claude Enhancer 需求验证器

if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "📋 Requirements Validator"
    echo "━━━━━━━━━━━━━━━━━━━━━━━"
    echo "检查需求文档完整性："
    if [[ -f "docs/PLAN.md" ]]; then
        echo "  ✅ PLAN.md 存在"
    else
        echo "  ❌ PLAN.md 缺失"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    if [[ -f "docs/PLAN.md" ]]; then
        echo "[Requirements] ✅ PLAN.md"
    else
        echo "[Requirements] ❌ 缺少PLAN.md"
    fi
fi

exit 0
