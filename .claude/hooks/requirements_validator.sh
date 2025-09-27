#!/bin/bash
# P1阶段需求验证器
echo "ℹ️ Requirements validator active"

# 检查PLAN.md结构完整性
if [ -f "docs/PLAN.md" ]; then
    if grep -q "## 任务列表" docs/PLAN.md && \
       grep -q "## 受影响路径" docs/PLAN.md && \
       grep -q "## 回滚计划" docs/PLAN.md; then
        echo "✅ PLAN.md结构完整"
    else
        echo "⚠️ 建议: PLAN.md需包含任务列表、受影响路径、回滚计划"
    fi
fi
