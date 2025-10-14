#!/bin/bash
# Claude Enhancer v2.0 架构重构测试运行器
# 作者: Test Engineer Professional
# 版本: v2.0
# 日期: 2025-10-14

set -euo pipefail

# ============= 配置 =============
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_REPORT_DIR="$SCRIPT_DIR/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# ============= 函数定义 =============

print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

print_section() {
    echo ""
    echo "──────────────────────────────────────────────"
    echo "  $1"
    echo "──────────────────────────────────────────────"
}

print_test() {
    local test_name="$1"
    echo -n "  🧪 $test_name ... "
}

print_pass() {
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

print_fail() {
    local message="$1"
    echo -e "${RED}❌ FAIL${NC}"
    echo -e "${RED}     $message${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

print_skip() {
    local reason="$1"
    echo -e "${YELLOW}⏭️  SKIP${NC} ($reason)"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
}

# ============= 测试函数 =============

# Phase 1: 迁移正确性测试
run_migration_tests() {
    print_section "Phase 1: 迁移正确性测试"

    # Test 1.1.1: 核心文件存在性检查
    print_test "1.1.1 核心文件存在性"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    local core_files=(
        "$PROJECT_ROOT/.claude/core/engine.py"
        "$PROJECT_ROOT/.claude/core/orchestrator.py"
        "$PROJECT_ROOT/.claude/core/loader.py"
        "$PROJECT_ROOT/.claude/core/config.yaml"
    )

    local all_exist=true
    for file in "${core_files[@]}"; do
        if [ ! -f "$file" ]; then
            all_exist=false
            print_fail "Core file missing: $file"
            return 1
        fi
    done

    if $all_exist; then
        print_pass
    fi

    # Test 1.1.2: 旧位置文件已删除
    print_test "1.1.2 旧位置文件清理"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 注意：这里假设迁移后旧文件应该被删除或转为软链接
    # 如果是软链接，应该检查软链接而不是普通文件
    if [ -f "$PROJECT_ROOT/.claude/engine.py" ] && [ ! -L "$PROJECT_ROOT/.claude/engine.py" ]; then
        print_fail "Old engine.py still exists as regular file"
        return 1
    fi

    print_pass

    # Test 1.1.3: 核心文件行数检查
    print_test "1.1.3 核心文件内容完整"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    local min_lines=50
    if [ $(wc -l < "$PROJECT_ROOT/.claude/core/engine.py") -lt $min_lines ]; then
        print_fail "engine.py too small (< $min_lines lines)"
        return 1
    fi

    if [ $(wc -l < "$PROJECT_ROOT/.claude/core/orchestrator.py") -lt $min_lines ]; then
        print_fail "orchestrator.py too small (< $min_lines lines)"
        return 1
    fi

    print_pass

    # Test 1.2.1: Python语法检查
    print_test "1.2.1 Python语法验证"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    for pyfile in "$PROJECT_ROOT/.claude/core"/*.py; do
        if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
            print_fail "Python syntax error in $(basename $pyfile)"
            return 1
        fi
    done

    print_pass

    # Test 1.2.2: YAML语法检查
    print_test "1.2.2 YAML语法验证"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if ! python3 -c "import yaml; yaml.safe_load(open('$PROJECT_ROOT/.claude/core/config.yaml'))" 2>/dev/null; then
        print_fail "YAML syntax error in config.yaml"
        return 1
    fi

    print_pass
}

# Phase 2: 锁定机制测试
run_locking_tests() {
    print_section "Phase 2: 锁定机制测试"

    # Test 2.1.1: Pre-commit hook存在性
    print_test "2.1.1 Pre-commit hook安装"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ ! -f "$PROJECT_ROOT/.git/hooks/pre-commit" ]; then
        print_fail "Pre-commit hook not installed"
        return 1
    fi

    if [ ! -x "$PROJECT_ROOT/.git/hooks/pre-commit" ]; then
        print_fail "Pre-commit hook not executable"
        return 1
    fi

    print_pass

    # Test 2.1.2: Hook包含core/保护逻辑
    print_test "2.1.2 Hook保护逻辑存在"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if ! grep -q "core/" "$PROJECT_ROOT/.git/hooks/pre-commit"; then
        print_fail "Hook doesn't contain core/ protection"
        return 1
    fi

    print_pass

    # Test 2.2.1: Hash文件存在
    print_test "2.2.1 Integrity Hash文件"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.claude/core/.integrity.sha256" ]; then
        print_pass
    else
        print_skip "Hash file not yet generated (expected in migration)"
    fi

    # Test 2.3.1: Claude PreToolUse hook存在
    print_test "2.3.1 Claude PreToolUse hook"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    local claude_hook="$PROJECT_ROOT/.claude/hooks/pre_tool_use.sh"
    if [ -f "$claude_hook" ]; then
        if [ ! -x "$claude_hook" ]; then
            print_fail "Claude hook not executable"
            return 1
        fi
        print_pass
    else
        print_skip "Claude hook not yet created (expected in migration)"
    fi
}

# Phase 3: Feature系统测试
run_feature_tests() {
    print_section "Phase 3: Feature系统测试"

    # Test 3.1.1: Feature配置文件
    print_test "3.1.1 Feature配置存在"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.claude/features/config.yaml" ]; then
        print_pass
    else
        print_skip "Feature config not yet created (expected in migration)"
    fi

    # Test 3.2.1: Feature目录结构
    print_test "3.2.1 Feature目录结构"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    local feature_dirs=(
        "$PROJECT_ROOT/.claude/features/basic"
        "$PROJECT_ROOT/.claude/features/standard"
        "$PROJECT_ROOT/.claude/features/advanced"
    )

    local structure_exists=true
    for dir in "${feature_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            structure_exists=false
            break
        fi
    done

    if $structure_exists; then
        print_pass
    else
        print_skip "Feature directory structure not yet created"
    fi

    # Test 3.3.1: Loader模块存在
    print_test "3.3.1 Loader模块存在"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.claude/core/loader.py" ]; then
        # 检查是否有load_features函数
        if grep -q "def load_features" "$PROJECT_ROOT/.claude/core/loader.py"; then
            print_pass
        else
            print_fail "loader.py missing load_features function"
            return 1
        fi
    else
        print_skip "loader.py not yet created"
    fi
}

# Phase 4: Hook增强测试
run_hook_enhancement_tests() {
    print_section "Phase 4: Hook增强测试"

    # Test 4.1.1: Workflow guard存在
    print_test "4.1.1 Workflow guard hook"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.claude/hooks/workflow_guard.sh" ]; then
        # 检查是否包含"继续"检测逻辑
        if grep -q "继续" "$PROJECT_ROOT/.claude/hooks/workflow_guard.sh"; then
            print_pass
        else
            print_fail "workflow_guard.sh missing '继续' detection"
            return 1
        fi
    else
        print_skip "workflow_guard.sh not yet created"
    fi

    # Test 4.2.1: Phase guard存在
    print_test "4.2.1 Phase guard hook"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.claude/hooks/phase_guard.sh" ]; then
        print_pass
    else
        print_skip "phase_guard.sh not yet created"
    fi

    # Test 4.3.1: Branch helper存在并工作
    print_test "4.3.1 Branch helper hook"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.claude/hooks/branch_helper.sh" ]; then
        if [ -x "$PROJECT_ROOT/.claude/hooks/branch_helper.sh" ]; then
            print_pass
        else
            print_fail "branch_helper.sh not executable"
            return 1
        fi
    else
        print_skip "branch_helper.sh not yet created (may exist already)"
    fi

    # Test 4.4.1: Comprehensive guard存在
    print_test "4.4.1 Comprehensive guard (5层)"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.claude/hooks/comprehensive_guard.sh" ]; then
        # 检查是否有5层检测
        local layer_count=$(grep -c "Layer [0-9]" "$PROJECT_ROOT/.claude/hooks/comprehensive_guard.sh" || echo 0)
        if [ "$layer_count" -ge 5 ]; then
            print_pass
        else
            print_fail "comprehensive_guard.sh has only $layer_count layers (expected 5)"
            return 1
        fi
    else
        print_skip "comprehensive_guard.sh not yet created"
    fi
}

# Phase 5: 兼容性测试
run_compatibility_tests() {
    print_section "Phase 5: 兼容性测试"

    # Test 5.1.1: 软链接兼容
    print_test "5.1.1 软链接兼容性"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # 检查关键软链接
    if [ -L "$PROJECT_ROOT/.claude/engine.py" ]; then
        local target=$(readlink "$PROJECT_ROOT/.claude/engine.py")
        if [[ "$target" == *"core/engine.py"* ]]; then
            print_pass
        else
            print_fail "Symlink points to wrong target: $target"
            return 1
        fi
    else
        print_skip "Symlinks not yet created (expected in migration)"
    fi

    # Test 5.2.1: Workflow executor存在
    print_test "5.2.1 Workflow executor"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.workflow/executor.sh" ]; then
        if [ -x "$PROJECT_ROOT/.workflow/executor.sh" ]; then
            print_pass
        else
            print_fail "executor.sh not executable"
            return 1
        fi
    else
        print_fail "executor.sh missing"
        return 1
    fi

    # Test 5.3.1: 配置文件可读
    print_test "5.3.1 配置文件访问"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -r "$PROJECT_ROOT/.claude/core/config.yaml" ]; then
        print_pass
    else
        print_fail "config.yaml not readable"
        return 1
    fi
}

# Phase 6: 性能测试
run_performance_tests() {
    print_section "Phase 6: 性能测试"

    # Test 6.1.1: 导入性能测试
    print_test "6.1.1 模块导入性能"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    cd "$PROJECT_ROOT"
    local start=$(date +%s%N)

    # 尝试导入（如果存在）
    python3 -c "import sys; sys.path.insert(0, '.claude/core'); import engine" 2>/dev/null || true

    local end=$(date +%s%N)
    local elapsed=$(( (end - start) / 1000000 ))  # 转换为毫秒

    if [ $elapsed -lt 200 ]; then
        print_pass
        echo "     Import time: ${elapsed}ms"
    else
        print_fail "Import too slow: ${elapsed}ms (>200ms)"
        return 1
    fi

    # Test 6.2.1: Hash验证性能
    print_test "6.2.1 Hash验证性能"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -f "$PROJECT_ROOT/.claude/core/.integrity.sha256" ]; then
        cd "$PROJECT_ROOT/.claude/core"

        local start=$(date +%s%N)
        sha256sum -c .integrity.sha256 --quiet >/dev/null 2>&1 || true
        local end=$(date +%s%N)
        local elapsed=$(( (end - start) / 1000000 ))

        cd "$PROJECT_ROOT"

        if [ $elapsed -lt 50 ]; then
            print_pass
            echo "     Hash verification: ${elapsed}ms"
        else
            print_fail "Hash verification too slow: ${elapsed}ms (>50ms)"
            return 1
        fi
    else
        print_skip "Hash file not yet generated"
    fi

    # Test 6.3.1: Hook性能测试
    print_test "6.3.1 Pre-commit hook性能"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ -x "$PROJECT_ROOT/.git/hooks/pre-commit" ]; then
        local start=$(date +%s%N)
        # 运行hook但不实际提交（dry-run模式）
        # 注意：这里需要设置环境让hook知道是测试
        export TEST_MODE=1
        "$PROJECT_ROOT/.git/hooks/pre-commit" >/dev/null 2>&1 || true
        unset TEST_MODE
        local end=$(date +%s%N)
        local elapsed=$(( (end - start) / 1000000 ))

        if [ $elapsed -lt 3000 ]; then
            print_pass
            echo "     Hook execution: ${elapsed}ms"
        else
            print_fail "Hook too slow: ${elapsed}ms (>3000ms)"
            return 1
        fi
    else
        print_skip "Pre-commit hook not installed"
    fi
}

# ============= 报告生成 =============

generate_report() {
    local report_file="$TEST_REPORT_DIR/test_report_${TIMESTAMP}.md"
    mkdir -p "$TEST_REPORT_DIR"

    cat > "$report_file" <<EOF
# Claude Enhancer v2.0 架构重构测试报告

**生成时间**: $(date)
**测试分支**: $(git rev-parse --abbrev-ref HEAD)
**Commit**: $(git rev-parse --short HEAD)

## 📊 测试摘要

- **总测试数**: $TOTAL_TESTS
- **通过**: $PASSED_TESTS ($(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)%)
- **失败**: $FAILED_TESTS
- **跳过**: $SKIPPED_TESTS

## 测试结果

### Phase 1: 迁移正确性测试
- 状态: 完成
- 通过率: 查看详细日志

### Phase 2: 锁定机制测试
- 状态: 完成
- 通过率: 查看详细日志

### Phase 3: Feature系统测试
- 状态: 完成
- 通过率: 查看详细日志

### Phase 4: Hook增强测试
- 状态: 完成
- 通过率: 查看详细日志

### Phase 5: 兼容性测试
- 状态: 完成
- 通过率: 查看详细日志

### Phase 6: 性能测试
- 状态: 完成
- 通过率: 查看详细日志

## 结论

EOF

    if [ $FAILED_TESTS -eq 0 ]; then
        cat >> "$report_file" <<EOF
✅ **所有测试通过**

架构v2.0迁移测试成功，系统可以进入下一阶段。
EOF
    else
        cat >> "$report_file" <<EOF
❌ **存在失败测试**

请检查失败的测试用例，修复后重新运行。
EOF
    fi

    echo ""
    echo "📊 测试报告已生成: $report_file"
}

# ============= 主函数 =============

main() {
    print_header "Claude Enhancer v2.0 架构重构测试套件"

    echo "📍 项目根目录: $PROJECT_ROOT"
    echo "📍 测试目录: $SCRIPT_DIR"
    echo "📍 报告目录: $TEST_REPORT_DIR"
    echo ""

    # 检查是否在正确分支
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_branch" != "feature/architecture-v2.0" ]]; then
        echo -e "${YELLOW}⚠️  警告: 当前分支是 '$current_branch'，不是 'feature/architecture-v2.0'${NC}"
        read -p "是否继续测试? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "测试已取消"
            exit 0
        fi
    fi

    # 运行所有测试阶段
    local start_time=$(date +%s)

    run_migration_tests || true
    run_locking_tests || true
    run_feature_tests || true
    run_hook_enhancement_tests || true
    run_compatibility_tests || true
    run_performance_tests || true

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # 打印总结
    print_header "测试完成"

    echo "📊 测试统计:"
    echo "   总测试数: $TOTAL_TESTS"
    echo -e "   ${GREEN}通过: $PASSED_TESTS${NC}"
    echo -e "   ${RED}失败: $FAILED_TESTS${NC}"
    echo -e "   ${YELLOW}跳过: $SKIPPED_TESTS${NC}"
    echo "   执行时间: ${duration}秒"
    echo ""

    # 生成报告
    generate_report

    # 返回状态
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✅ 所有测试通过！${NC}"
        exit 0
    else
        echo -e "${RED}❌ 存在失败测试，请检查${NC}"
        exit 1
    fi
}

# 运行主函数
main "$@"
