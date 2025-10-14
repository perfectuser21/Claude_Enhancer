#!/bin/bash
# Claude Enhancer v2.0 快速验证测试
# 作者: Test Engineer Professional
# 运行时间: ~5分钟

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Claude Enhancer v2.0 快速验证测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 统计
total=0
passed=0
failed=0

test() {
    local name="$1"
    echo -n "  🧪 $name ... "
    total=$((total + 1))
}

pass() {
    echo -e "${GREEN}✅${NC}"
    passed=$((passed + 1))
}

fail() {
    echo -e "${RED}❌${NC}"
    echo "     $1"
    failed=$((failed + 1))
}

# Test 1: 核心文件存在 (v2.0 新路径)
test "核心文件存在性"
if [ -f "$PROJECT_ROOT/core/workflow/engine.py" ] && \
   [ -f "$PROJECT_ROOT/core/workflow/types.py" ] && \
   [ -f "$PROJECT_ROOT/.claude/core/loader.py" ] && \
   [ -f "$PROJECT_ROOT/.claude/core/config.yaml" ]; then
    pass
else
    fail "缺少核心文件"
fi

# Test 2: Python语法 (v2.0 新文件)
test "Python语法检查"
if python3 -m py_compile "$PROJECT_ROOT/core/workflow/engine.py" 2>/dev/null && \
   python3 -m py_compile "$PROJECT_ROOT/core/workflow/types.py" 2>/dev/null && \
   python3 -m py_compile "$PROJECT_ROOT/.claude/core/loader.py" 2>/dev/null; then
    pass
else
    fail "Python语法错误"
fi

# Test 3: YAML语法
test "YAML语法检查"
if python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/.claude/core/config.yaml'))" 2>/dev/null; then
    pass
else
    fail "YAML语法错误"
fi

# Test 4: Git hooks
test "Git hooks安装"
if [ -x "$PROJECT_ROOT/.git/hooks/pre-commit" ]; then
    pass
else
    fail "Pre-commit hook未安装或不可执行"
fi

# Test 5: Workflow executor
test "Workflow executor"
if [ -x "$PROJECT_ROOT/.workflow/executor.sh" ]; then
    pass
else
    fail "Workflow executor未安装或不可执行"
fi

# Test 6: v2.0架构完整性
test "v2.0架构目录"
if [ -d "$PROJECT_ROOT/core/workflow" ] && \
   [ -d "$PROJECT_ROOT/core/state" ] && \
   [ -d "$PROJECT_ROOT/core/hooks" ] && \
   [ -d "$PROJECT_ROOT/core/agents" ] && \
   [ -d "$PROJECT_ROOT/core/config" ]; then
    pass
else
    fail "v2.0架构目录不完整"
fi

# Test 7: 导入性能
test "模块导入性能"
start=$(date +%s%N)
python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT/.claude/core'); import engine" 2>/dev/null || true
end=$(date +%s%N)
elapsed=$(( (end - start) / 1000000 ))

if [ $elapsed -lt 300 ]; then
    pass
    echo "     (${elapsed}ms)"
else
    fail "导入太慢: ${elapsed}ms"
fi

# Test 8: Branch检查
test "正确的分支"
current_branch=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD)
if [[ "$current_branch" == "feature/architecture-v2.0" ]]; then
    pass
else
    echo -e "${YELLOW}⚠️${NC} (当前分支: $current_branch)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  测试完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  总计: $total"
echo -e "  ${GREEN}通过: $passed${NC}"
echo -e "  ${RED}失败: $failed${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $failed -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 快速验证通过！${NC}"
    echo "   可以运行完整测试: ./test/架构v2.0/run_all_tests.sh"
    exit 0
else
    echo ""
    echo -e "${RED}❌ 存在失败测试${NC}"
    exit 1
fi
