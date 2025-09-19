#!/bin/bash
# Perfect21 Integration Test
# 测试Claude hooks和Git hooks的完整集成

echo "================================================"
echo "Perfect21 完整集成测试"
echo "================================================"

# 1. 测试Git Pre-commit Hook
echo ""
echo "📝 测试1: Git Pre-commit Hook"
echo "--------------------------------"
echo "test content" > test_integration.txt
git add test_integration.txt
git commit -m "test: integration test" || echo "Commit执行"

# 2. 测试Python Hooks
echo ""
echo "🐍 测试2: Python Hooks"
echo "--------------------------------"
cd .claude/hooks
python3 -c "
import subprocess
import json

# Test task analysis
print('Testing task analysis...')
result = subprocess.run(
    ['python3', 'perfect21_core.py', 'analyze-task'],
    input='实现用户登录系统',
    text=True,
    capture_output=True
)
print(f'  Result: {result.stdout[:50]}...')

# Test security
print('Testing security...')
result = subprocess.run(
    ['python3', 'security_validator.py'],
    input='ls -la',
    text=True,
    capture_output=True
)
print(f'  Safe command result: exit code {result.returncode}')
"

# 3. 测试工作流日志
echo ""
echo "📊 测试3: 工作流日志"
echo "--------------------------------"
if [ -f /tmp/perfect21_hooks.log ]; then
    echo "日志文件存在"
    tail -5 /tmp/perfect21_hooks.log
else
    echo "日志文件不存在或为空"
fi

# 4. 测试Pre-commit框架
echo ""
echo "🔧 测试4: Pre-commit框架"
echo "--------------------------------"
if [ -f .pre-commit-config.yaml ]; then
    echo "✅ Pre-commit配置存在"
    echo "检查配置的hooks:"
    grep -E "^\s+-\s+id:" ../../.pre-commit-config.yaml | head -5
else
    echo "❌ Pre-commit配置不存在"
fi

# 5. 验证Claude全局配置
echo ""
echo "🌐 测试5: Claude全局配置"
echo "--------------------------------"
if grep -q "hooks" ~/.claude/settings.json 2>/dev/null; then
    echo "✅ 全局hooks已配置"
    grep -A 5 '"hooks"' ~/.claude/settings.json | head -10
else
    echo "❌ 全局hooks未配置"
fi

# 6. 测试文件权限
echo ""
echo "🔐 测试6: Hook文件权限"
echo "--------------------------------"
ls -la *.py 2>/dev/null | grep -E "^-rwx" | wc -l | xargs -I {} echo "可执行Python hooks: {} 个"
ls -la *.sh 2>/dev/null | grep -E "^-rwx" | wc -l | xargs -I {} echo "可执行Shell hooks: {} 个"

# 清理测试文件
cd ../..
rm -f test_integration.txt
git reset HEAD test_integration.txt 2>/dev/null

echo ""
echo "================================================"
echo "✅ 集成测试完成"
echo "================================================"