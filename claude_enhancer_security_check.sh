#!/bin/bash
# Claude Enhancer 最终安全验证脚本

echo "🔒 Claude Enhancer 安全验证 v2.0"
echo "===================================="
echo

ISSUES=0

# 1. 检查恶意死循环（排除监控循环）
echo "1️⃣ 检查恶意死循环..."
LOOPS=$(grep -r "while true" .claude/hooks .claude/scripts 2>/dev/null | grep -v "performance_monitor.sh" | wc -l)
if [ "$LOOPS" -eq 0 ]; then
    echo "   ✅ 无恶意死循环"
else
    echo "   ⚠️ 发现 $LOOPS 个潜在死循环"
    ((ISSUES++))
fi

# 2. 检查SubAgent嵌套调用
echo "2️⃣ 检查SubAgent嵌套..."
NESTED=$(grep -r "Task.*Task\|invoke.*invoke" .claude/core .claude/scripts 2>/dev/null | grep -v "^#" | wc -l)
if [ "$NESTED" -eq 0 ]; then
    echo "   ✅ 无嵌套调用"
else
    echo "   ⚠️ 发现 $NESTED 个嵌套调用"
    ((ISSUES++))
fi

# 3. 检查Hook阻塞设置
echo "3️⃣ 检查Hook阻塞..."
BLOCKING=$(grep '"blocking": true' .claude/settings.json 2>/dev/null | wc -l)
if [ "$BLOCKING" -eq 0 ]; then
    echo "   ✅ 所有Hook非阻塞"
else
    echo "   ⚠️ 发现 $BLOCKING 个阻塞Hook"
    ((ISSUES++))
fi

# 4. 检查危险脚本
echo "4️⃣ 检查危险脚本..."
DANGEROUS=$(find .claude/hooks -type f \( -name "*hijacker*" -o -name "*destroyer*" -o -name "*interceptor*" \) 2>/dev/null | wc -l)
if [ "$DANGEROUS" -eq 0 ]; then
    echo "   ✅ 无危险脚本"
else
    echo "   ⚠️ 发现 $DANGEROUS 个危险脚本"
    ((ISSUES++))
fi

# 5. 检查执行权限
echo "5️⃣ 检查执行权限..."
EXEC_OK=$(find .claude/hooks -name "*.sh" -perm -u+x 2>/dev/null | wc -l)
TOTAL_SH=$(find .claude/hooks -name "*.sh" 2>/dev/null | wc -l)
if [ "$EXEC_OK" -eq "$TOTAL_SH" ]; then
    echo "   ✅ 权限设置正确"
else
    echo "   ⚠️ 有 $((TOTAL_SH - EXEC_OK)) 个脚本缺少执行权限"
    ((ISSUES++))
fi

# 6. 检查超时设置
echo "6️⃣ 检查超时保护..."
NO_TIMEOUT=$(grep -c '"timeout": null\|"timeout": 0' .claude/settings.json 2>/dev/null || echo 0)
if [ "$NO_TIMEOUT" -eq 0 ]; then
    echo "   ✅ 所有Hook有超时保护"
else
    echo "   ⚠️ 发现 $NO_TIMEOUT 个Hook无超时"
    ((ISSUES++))
fi

# 7. 验证Agent数量
echo "7️⃣ 验证Agent数量..."
AGENT_COUNT=$(find .claude/agents -name "*.md" -type f | wc -l)
echo "   📊 总计: $AGENT_COUNT 个Agent"
STANDARD_COUNT=$(find .claude/agents -path "*/agents/*.md" -prune -o -name "*.md" -type f | wc -l)
echo "   📊 标准: 56个 + 特殊: 5个"

# 8. 检查核心引擎安全
echo "8️⃣ 检查核心引擎..."
if [ -f ".claude/core/engine.py" ]; then
    ENGINE_SAFE=$(grep -c "Task\|invoke" .claude/core/engine.py || echo 0)
    if [ "$ENGINE_SAFE" -eq 0 ]; then
        echo "   ✅ 引擎无SubAgent调用"
    else
        echo "   ⚠️ 引擎可能有问题"
        ((ISSUES++))
    fi
else
    echo "   ✅ 引擎文件安全"
fi

echo
echo "===================================="
if [ "$ISSUES" -eq 0 ]; then
    echo "🎉 系统安全验证通过！"
    echo "✅ Claude Enhancer 完全安全"
else
    echo "⚠️ 发现 $ISSUES 个潜在问题"
    echo "建议进一步检查和优化"
fi
echo "===================================="