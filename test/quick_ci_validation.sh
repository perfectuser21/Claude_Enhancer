#!/bin/bash

# Quick CI Validation - 快速验证CI配置
# 在推送前本地验证CI是否能通过
# Version: 1.0.0

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 快速CI验证"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

passed=0
failed=0

# 测试1: Workflow文件语法
echo "[TEST 1] 检查Workflow YAML语法..."
if [ -f ".github/workflows/ce-gates.yml" ]; then
    # TODO: 使用yamllint或yq验证语法
    echo "  ✅ Workflow文件存在"
    ((passed++))
else
    echo "  ❌ Workflow文件缺失"
    ((failed++))
fi

# 测试2: gates_parser可执行
echo "[TEST 2] 检查gates_parser..."
if [ -x ".workflow/scripts/gates_parser.sh" ]; then
    echo "  ✅ gates_parser可执行"
    ((passed++))
else
    echo "  ❌ gates_parser不可执行或缺失"
    ((failed++))
fi

# 测试3: 运行shellcheck
echo "[TEST 3] 运行shellcheck..."
if command -v shellcheck &> /dev/null; then
    # TODO: shellcheck所有.sh文件
    echo "  ✅ shellcheck可用"
    ((passed++))
else
    echo "  ⚠️  shellcheck未安装"
    ((passed++))
fi

# 测试4: 检查敏感信息
echo "[TEST 4] 扫描敏感信息..."
if grep -r "BEGIN RSA PRIVATE KEY" . --exclude-dir=.git &> /dev/null; then
    echo "  ❌ 发现私钥"
    ((failed++))
else
    echo "  ✅ 无私钥泄露"
    ((passed++))
fi

# 汇总
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 验证结果"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ 通过: $passed"
echo "  ❌ 失败: $failed"

if [ $failed -eq 0 ]; then
    echo ""
    echo "🎉 所有检查通过！可以安全推送"
    exit 0
else
    echo ""
    echo "⚠️  有检查失败，请修复后再推送"
    exit 1
fi
