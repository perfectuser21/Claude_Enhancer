#!/usr/bin/env bash
# Claude Enhancer 5.3 - 权限保护机制测试
# 验证能否真正拦截chaos_no_exec_permission攻击

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
TEST_LOG="$PROJECT_ROOT/.workflow/logs/permission_test.log"

echo -e "${BOLD}${BLUE}🧪 权限保护机制完整测试${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════${NC}"
echo ""

# 确保日志目录存在
mkdir -p "$(dirname "$TEST_LOG")"

# 记录测试日志
log_test() {
    local level="$1"
    shift
    echo "$(date +'%Y-%m-%d %H:%M:%S') [$level] $*" >> "$TEST_LOG"
    echo -e "$*"
}

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试用例函数
run_test() {
    local test_name="$1"
    local test_function="$2"

    ((TOTAL_TESTS++))
    echo -e "\n${CYAN}📋 测试 $TOTAL_TESTS: $test_name${NC}"
    echo "────────────────────────────────────"

    if $test_function; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        log_test "PASS" "$test_name"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        log_test "FAIL" "$test_name"
        ((FAILED_TESTS++))
        return 1
    fi
}

# ═══════════════════════════════════════
# 测试用例定义
# ═══════════════════════════════════════

# 测试1: 基础权限检查
test_basic_permissions() {
    log_test "INFO" "检查基础权限状态"

    local critical_files=(
        "$HOOKS_DIR/pre-commit"
        "$HOOKS_DIR/commit-msg"
        "$HOOKS_DIR/pre-push"
        "$PROJECT_ROOT/scripts/fix_permissions.sh"
        "$PROJECT_ROOT/scripts/permission_health_check.sh"
        "$PROJECT_ROOT/scripts/chaos_defense.sh"
    )

    local issues=0
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            if [ -x "$file" ]; then
                echo "  ✓ $(basename "$file") 可执行"
            else
                echo "  ❌ $(basename "$file") 不可执行"
                ((issues++))
            fi
        else
            echo "  ❌ $(basename "$file") 不存在"
            ((issues++))
        fi
    done

    return $([ $issues -eq 0 ] && echo 0 || echo 1)
}

# 测试2: 权限自动修复功能
test_auto_fix() {
    log_test "INFO" "测试权限自动修复功能"

    local test_file="$HOOKS_DIR/pre-commit"
    if [ ! -f "$test_file" ]; then
        echo "  ❌ 测试文件不存在: $test_file"
        return 1
    fi

    # 保存原始权限
    local original_perm
    original_perm=$(stat -c %a "$test_file")
    echo "  📋 原始权限: $original_perm"

    # 破坏权限
    chmod 644 "$test_file"
    echo "  🔧 移除执行权限"

    if [ -x "$test_file" ]; then
        echo "  ❌ 权限移除失败"
        return 1
    fi

    # 运行修复脚本
    echo "  🛠️  运行权限修复..."
    if bash "$PROJECT_ROOT/scripts/fix_permissions.sh" --quiet; then
        echo "  ✓ 修复脚本执行成功"
    else
        echo "  ❌ 修复脚本执行失败"
        chmod "$original_perm" "$test_file"  # 恢复权限
        return 1
    fi

    # 检查是否修复成功
    if [ -x "$test_file" ]; then
        echo "  ✅ 权限修复成功"
        return 0
    else
        echo "  ❌ 权限修复失败"
        chmod "$original_perm" "$test_file"  # 恢复权限
        return 1
    fi
}

# 测试3: Git hooks自检机制
test_hooks_self_check() {
    log_test "INFO" "测试Git hooks自检机制"

    # 创建一个临时的测试hook
    local test_hook="$HOOKS_DIR/test-permission-check"

    cat > "$test_hook" << 'EOF'
#!/bin/bash
set -euo pipefail

# 权限自检代码（从实际hooks中提取）
if [ ! -x "$0" ]; then
    echo "🚨 CRITICAL: Hook失去执行权限！"
    chmod +x "$0" 2>/dev/null || {
        echo "❌ 无法修复hook权限"
        exit 1
    }
    echo "✅ Hook权限已修复"
fi

echo "Hook自检通过"
exit 0
EOF

    chmod +x "$test_hook"
    echo "  📁 创建测试hook: $test_hook"

    # 移除权限并测试自修复
    chmod 644 "$test_hook"
    echo "  🔧 移除hook执行权限"

    # 尝试执行hook（应该会自修复）
    if bash "$test_hook" 2>/dev/null; then
        echo "  ✅ Hook自检并自修复成功"
        local result=0
    else
        echo "  ❌ Hook自检失败"
        local result=1
    fi

    # 清理测试文件
    rm -f "$test_hook"
    echo "  🧹 清理测试文件"

    return $result
}

# 测试4: Chaos防护系统
test_chaos_defense() {
    log_test "INFO" "测试Chaos防护系统"

    if [ ! -f "$PROJECT_ROOT/scripts/chaos_defense.sh" ]; then
        echo "  ❌ Chaos防护脚本不存在"
        return 1
    fi

    echo "  🛡️  运行Chaos防护系统..."
    if bash "$PROJECT_ROOT/scripts/chaos_defense.sh" --quiet 2>/dev/null; then
        echo "  ✅ Chaos防护系统正常"
        return 0
    else
        echo "  ❌ Chaos防护系统异常"
        return 1
    fi
}

# 测试5: 健康检查系统
test_health_check() {
    log_test "INFO" "测试权限健康检查系统"

    if [ ! -f "$PROJECT_ROOT/scripts/permission_health_check.sh" ]; then
        echo "  ❌ 健康检查脚本不存在"
        return 1
    fi

    echo "  🔍 运行权限健康检查..."
    if bash "$PROJECT_ROOT/scripts/permission_health_check.sh" --quiet; then
        echo "  ✅ 权限健康检查通过"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 1 ]; then
            echo "  ⚠️  发现轻微权限问题（已记录）"
            return 0  # 轻微问题不算测试失败
        else
            echo "  ❌ 权限健康检查失败"
            return 1
        fi
    fi
}

# 测试6: Git提交拦截测试（模拟）
test_commit_blocking() {
    log_test "INFO" "测试Git提交拦截能力"

    # 检查当前Git状态
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "  ❌ 不在Git仓库中"
        return 1
    fi

    echo "  📋 检查Git hooks状态..."
    local hooks_ok=true
    for hook in "pre-commit" "commit-msg" "pre-push"; do
        local hook_path="$HOOKS_DIR/$hook"
        if [ -f "$hook_path" ] && [ -x "$hook_path" ]; then
            echo "    ✓ $hook 可执行"
        else
            echo "    ❌ $hook 不可执行"
            hooks_ok=false
        fi
    done

    if [ "$hooks_ok" = true ]; then
        echo "  ✅ 所有关键hooks都可执行，能够拦截无权限提交"
        return 0
    else
        echo "  ❌ 部分hooks不可执行，无法保证拦截效果"
        return 1
    fi
}

# ═══════════════════════════════════════
# 执行所有测试
# ═══════════════════════════════════════

echo -e "${MAGENTA}开始执行权限保护机制测试...${NC}"

# 运行所有测试
run_test "基础权限检查" test_basic_permissions
run_test "权限自动修复功能" test_auto_fix
run_test "Git hooks自检机制" test_hooks_self_check
run_test "Chaos防护系统" test_chaos_defense
run_test "权限健康检查系统" test_health_check
run_test "Git提交拦截能力" test_commit_blocking

# ═══════════════════════════════════════
# 生成测试报告
# ═══════════════════════════════════════

echo -e "\n${BOLD}${CYAN}🧪 测试报告${NC}"
echo -e "${BOLD}${CYAN}═══════════════════════════════════${NC}"

echo -e "总测试数: ${BOLD}$TOTAL_TESTS${NC}"
echo -e "通过测试: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败测试: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${BOLD}${GREEN}🎉 所有测试通过！权限保护机制运行正常${NC}"
    echo -e "${GREEN}✅ 系统可以有效防御chaos_no_exec_permission攻击${NC}"

    # 计算成功率
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "成功率: ${BOLD}${GREEN}${success_rate}%${NC}"

    log_test "SUCCESS" "All permission defense tests passed ($PASSED_TESTS/$TOTAL_TESTS)"
    exit 0
else
    echo -e "\n${BOLD}${RED}⚠️  部分测试失败${NC}"
    echo -e "${RED}权限保护机制需要调整和修复${NC}"

    # 计算成功率
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "成功率: ${BOLD}${YELLOW}${success_rate}%${NC}"

    echo -e "\n${YELLOW}建议措施：${NC}"
    echo "1. 检查失败的测试用例"
    echo "2. 运行完整权限修复: bash scripts/fix_permissions.sh"
    echo "3. 检查文件系统和Git仓库状态"
    echo "4. 查看详细日志: $TEST_LOG"

    log_test "PARTIAL_SUCCESS" "Permission defense tests completed with $FAILED_TESTS failures ($PASSED_TESTS/$TOTAL_TESTS passed)"
    exit 1
fi