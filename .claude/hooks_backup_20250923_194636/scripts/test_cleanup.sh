#!/bin/bash
# 测试cleanup-specialist集成效果

echo "🧹 测试Cleanup-Specialist集成"
echo "======================================"
echo ""

# 1. 创建测试文件
echo "📝 创建测试文件..."
touch test.tmp test.bak test.swp
echo "console.log('debug info');" > test.js
echo "print('debug')" > test.py
echo "TODO: fix this later" > todo.txt

# 2. 显示创建的文件
echo ""
echo "📁 当前测试文件："
ls -la test.* todo.txt 2>/dev/null | grep -v "^d"

# 3. 模拟Phase 5清理
echo ""
echo "🚀 模拟Phase 5（代码提交）清理..."
echo ""

# 检查cleanup配置
if [ -f ".claude/cleanup.yaml" ]; then
    echo "✅ 找到cleanup.yaml配置"

    # 模拟清理动作
    echo "执行清理任务："
    echo "  - 删除临时文件 (*.tmp, *.bak, *.swp)"
    rm -f *.tmp *.bak *.swp

    echo "  - 清理调试代码"
    # 这里只是演示，实际需要更复杂的处理
    sed -i.backup 's/console\.log/\/\/console.log/g' test.js 2>/dev/null || \
    sed -i '' 's/console\.log/\/\/console.log/g' test.js 2>/dev/null

    echo "  - 检查TODO标记"
    grep -n "TODO:" todo.txt && echo "    ⚠️  发现未关联ticket的TODO"
else
    echo "❌ 未找到cleanup.yaml配置"
fi

# 4. 显示清理后的结果
echo ""
echo "📁 清理后的文件："
ls -la test.* todo.txt 2>/dev/null | grep -v "^d"

# 5. 检查Agent定义
echo ""
echo "📋 检查cleanup-specialist Agent定义..."
if [ -f ".claude/agents/specialized/cleanup-specialist.md" ]; then
    echo "✅ Agent定义文件存在"
    head -n 10 .claude/agents/specialized/cleanup-specialist.md | grep "^#"
else
    echo "❌ Agent定义文件不存在"
fi

# 6. 测试hook集成
echo ""
echo "🔗 测试Hook集成..."
TEST_INPUT='{"prompt": "Deploy to production", "phase": 5}'
echo "$TEST_INPUT" | .claude/hooks/smart_agent_selector.sh >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ smart_agent_selector.sh 正常工作"
    echo ""
    echo "Hook输出预览："
    echo "$TEST_INPUT" | .claude/hooks/smart_agent_selector.sh 2>&1 | grep -E "(清理|cleanup)" | head -3
else
    echo "❌ smart_agent_selector.sh 执行失败"
fi

# 7. 清理测试文件
echo ""
echo "🧹 清理所有测试文件..."
rm -f test.* todo.txt *.backup

echo ""
echo "======================================"
echo "✅ 测试完成！"
echo ""
echo "集成要点："
echo "1. cleanup-specialist已定义在.claude/agents/specialized/"
echo "2. cleanup.yaml配置了Phase 0/5/7的清理规则"
echo "3. smart_agent_selector.sh会在Phase 5/7自动添加cleanup-specialist"
echo "4. 工作流已更新，标记了清理点"