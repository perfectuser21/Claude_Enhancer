#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# P2阶段设计顾问
if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "ℹ️ Design advisor active"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Design] Active"
fi

# 检查DESIGN.md关键元素
if [ -f "docs/DESIGN.md" ]; then
    if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
        echo "💡 设计建议:"
        echo "  - 确保API接口定义清晰"
        echo "  - 数据模型与PLAN对齐"
        echo "  - 目录结构符合项目规范"
    fi

    # 检查是否包含关键章节
    if ! grep -q "## API接口" docs/DESIGN.md; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "  ⚠️ 建议添加API接口定义"
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Design] ⚠️ 缺少API定义"
        fi
    fi

    if ! grep -q "## 数据模型" docs/DESIGN.md; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "  ⚠️ 建议添加数据模型设计"
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Design] ⚠️ 缺少数据模型"
        fi
    fi
fi
