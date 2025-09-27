#!/bin/bash
# P2阶段设计顾问
echo "ℹ️ Design advisor active"

# 检查DESIGN.md关键元素
if [ -f "docs/DESIGN.md" ]; then
    echo "💡 设计建议:"
    echo "  - 确保API接口定义清晰"
    echo "  - 数据模型与PLAN对齐"
    echo "  - 目录结构符合项目规范"
    
    # 检查是否包含关键章节
    grep -q "## API接口" docs/DESIGN.md || echo "  ⚠️ 建议添加API接口定义"
    grep -q "## 数据模型" docs/DESIGN.md || echo "  ⚠️ 建议添加数据模型设计"
fi
