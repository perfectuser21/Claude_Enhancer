#!/bin/bash
# 简单的验证测试

echo "🧪 Claude Enhancer 简单验证测试"
echo "======================================"

# 测试1: 路径修复
echo -n "1. 检查Claude Enhancer路径... "
if grep -q "Claude Enhancer" .claude/hooks/smart_dispatcher.py; then
    echo "✅"
else
    echo "❌"
fi

# 测试2: Agent文件
echo -n "2. backend-engineer.md存在... "
if [ -f .claude/agents/development/backend-engineer.md ]; then
    echo "✅"
else
    echo "❌"
fi

echo -n "3. cleanup-specialist.md存在... "
if [ -f .claude/agents/specialized/cleanup-specialist.md ]; then
    echo "✅"
else
    echo "❌"
fi

# 测试3: 文件权限
echo -n "4. 脚本权限正确(750)... "
PERM=$(stat -c %a .claude/hooks/smart_agent_selector.sh)
if [ "$PERM" = "750" ]; then
    echo "✅"
else
    echo "❌ (实际: $PERM)"
fi

# 测试4: 配置文件
echo -n "5. 统一配置存在... "
if [ -f .claude/config/unified_main.yaml ]; then
    echo "✅"
else
    echo "❌"
fi

# 测试5: Cleanup优化版
echo -n "6. Cleanup是Ultra版本... "
if grep -q "Ultra-Optimized" .claude/scripts/cleanup.sh; then
    echo "✅"
else
    echo "❌"
fi

# 测试6: Print语句
echo -n "7. Print语句正常... "
if grep -q 'print(item.get("result"' .claude/hooks/smart_dispatcher.py; then
    echo "✅"
else
    echo "❌"
fi

# 测试7: 品牌名称
echo -n "8. 品牌名称已更新为Claude Enhancer... "
if grep -q "Claude Enhancer" .claude/hooks/enforcer_interceptor.py; then
    echo "✅"
else
    echo "❌"
fi

echo "======================================"
echo "测试完成！"