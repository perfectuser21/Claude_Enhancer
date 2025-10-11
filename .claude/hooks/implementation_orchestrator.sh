#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# P3阶段实现编排器
echo "ℹ️ Implementation orchestrator active"

# 提醒代码质量标准
echo "💡 实现提醒:"
echo "  - 遵循项目代码规范"
echo "  - 添加必要的注释"
echo "  - 考虑错误处理"

# 检查是否有未提交的更改
if [ -d ".git" ]; then
    changes=$(git status --porcelain | wc -l)
    if [ $changes -gt 0 ]; then
        echo "  ⚠️ 有${changes}个未提交的更改"
    fi
fi

# 建议运行的检查
echo "  建议运行:"
echo "    - lint检查"
echo "    - 类型检查"
echo "    - 格式化"
