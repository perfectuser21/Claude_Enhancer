#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# P5阶段提交质量门
if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "ℹ️ Commit quality gate active"

    # 提交前检查清单
    echo "💡 提交前检查:"
    echo "  - [ ] 代码已格式化"
    echo "  - [ ] 测试全部通过"
    echo "  - [ ] 无console.log/print调试"
    echo "  - [ ] commit message符合规范"
elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
    echo "[Commit Gate] Active"
fi

# 检查commit message规范
if [ -d ".git" ]; then
    last_msg=$(git log -1 --pretty=%B 2>/dev/null | head -1)
    if [[ $last_msg =~ ^(feat|fix|docs|style|refactor|test|chore): ]]; then
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "  ✅ 最近提交符合规范"
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Commit Gate] ✅ 规范"
        fi
    else
        if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
            echo "  ⚠️ 提交信息应以feat/fix/docs等前缀开头"
        elif [[ "${CE_COMPACT_OUTPUT:-false}" == "true" ]]; then
            echo "[Commit Gate] ⚠️ 格式错误"
        fi
    fi
fi

# 建议的提交格式
if [[ "${CE_SILENT_MODE:-false}" != "true" ]]; then
    echo "  建议格式:"
    echo "    feat: 新功能"
    echo "    fix: 修复bug"
    echo "    docs: 文档更新"
fi
