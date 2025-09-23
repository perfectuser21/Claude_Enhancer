#!/bin/bash
# Claude Enhancer端到端功能验证测试

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 Claude Enhancer端到端功能测试"
echo "======================================"
echo ""

# 测试计数
PASSED=0
FAILED=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local expected="$3"

    echo -n "测试: $test_name ... "

    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ 失败${NC}"
        echo "  命令: $test_cmd"
        ((FAILED++))
    fi
}

# 1. 路径验证
echo "📂 1. 路径验证"
run_test "Claude Enhancer路径正确" "grep -q 'Claude Enhancer' .claude/hooks/smart_dispatcher.py"
run_test "无/Claude Enhancer/路径残留" "! grep -l '/Claude Enhancer/' .claude/hooks/*.py 2>/dev/null | grep -q '.'"

# 2. Agent类型验证
echo ""
echo "🤖 2. Agent类型验证"
run_test "backend-engineer存在" "[ -f .claude/agents/development/backend-engineer.md ]"
run_test "cleanup-specialist存在" "[ -f .claude/agents/specialized/cleanup-specialist.md ]"

# 3. 文件权限验证
echo ""
echo "🔐 3. 文件权限验证"
run_test "Shell脚本权限750" "[ $(stat -c %a .claude/hooks/smart_agent_selector.sh) = '750' ]"
run_test "配置文件权限640" "[ $(stat -c %a .claude/settings.json) = '640' ]"
run_test "Git Hooks权限750" "[ $(stat -c %a .git/hooks/pre-commit) = '750' ]"

# 4. 配置管理验证
echo ""
echo "⚙️ 4. 配置管理验证"
run_test "统一配置文件存在" "[ -f .claude/config/unified_main.yaml ]"
run_test "配置加载器存在" "[ -f .claude/scripts/load_config.sh ]"
run_test "配置验证器存在" "[ -f .claude/scripts/config_validator.py ]"

# 5. Cleanup脚本验证
echo ""
echo "🧹 5. Cleanup脚本验证"
run_test "Cleanup.sh是Ultra版本" "grep -q 'Ultra-Optimized' .claude/scripts/cleanup.sh"
run_test "Cleanup支持dry-run" ".claude/scripts/cleanup.sh --dry-run > /dev/null 2>&1"

# 6. Hook系统验证
echo ""
echo "🔗 6. Hook系统验证"
run_test "Smart Agent Selector可执行" ".claude/hooks/smart_agent_selector.sh <<< '{}' > /dev/null 2>&1"
run_test "Phase State JSON有效" "python3 -m json.tool .claude/phase_state.json > /dev/null 2>&1"

# 7. 文档验证
echo ""
echo "📚 7. 文档验证"
run_test "安装指南存在" "[ -f INSTALLATION_GUIDE.md ]"
run_test "故障排除指南存在" "[ -f TROUBLESHOOTING.md ]"
run_test "API参考文档存在" "[ -f API_REFERENCE.md ]"

# 8. 功能性验证
echo ""
echo "⚡ 8. 功能性验证"
run_test "Print语句正常" "grep -q '^[[:space:]]*print(' .claude/hooks/smart_dispatcher.py"
run_test "品牌名称统一" "grep -q 'Claude Enhancer' .claude/hooks/enforcer.sh"

# 总结
echo ""
echo "======================================"
echo "📊 测试结果总结"
echo "✅ 通过: $PASSED"
echo "❌ 失败: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！Claude Enhancer系统验证成功！${NC}"
    exit 0
else
    echo -e "${RED}⚠️ 有 $FAILED 个测试失败，请检查！${NC}"
    exit 1
fi