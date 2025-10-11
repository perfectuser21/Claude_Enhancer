#!/bin/bash
# Auto-mode detection
if [[ "$CE_AUTO_MODE" == "true" ]]; then
    export CE_SILENT_MODE=true
fi
# P4阶段测试协调器
echo "ℹ️ Testing coordinator active"

# 测试覆盖建议
echo "💡 测试建议:"
echo "  - 单元测试覆盖核心功能"
echo "  - 集成测试验证模块交互"
echo "  - 边界条件测试"
echo "  - 性能测试基准"

# 检查测试文件
test_count=0
if [ -d "tests" ]; then
    test_count=$(find tests -name "*.py" -o -name "*.js" -o -name "*.test.*" | wc -l)
    echo "  ✅ 发现${test_count}个测试文件"
fi

# 检查TEST-REPORT.md
if [ -f "docs/TEST-REPORT.md" ]; then
    echo "  ✅ 测试报告已生成"
else
    echo "  ⚠️ 记得生成TEST-REPORT.md"
fi
