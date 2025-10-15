#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 任务-分支绑定系统测试套件
# Claude Enhancer v6.5.0
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_LIFECYCLE="$PROJECT_ROOT/.claude/hooks/task_lifecycle.sh"
TASK_ENFORCER="$PROJECT_ROOT/.claude/hooks/task_branch_enforcer.sh"
TASK_MAP="$PROJECT_ROOT/.workflow/task_branch_map.json"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# 测试计数器
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

print_result() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"

    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        echo -e "   Expected: $expected"
        echo -e "   Actual: $actual"
        ((TESTS_FAILED++))
        return 1
    fi
}

skip_test() {
    local test_name="$1"
    local reason="$2"
    echo -e "${YELLOW}⚠️ SKIP${NC}: $test_name - $reason"
    ((TESTS_SKIPPED++))
}

cleanup_task() {
    if [[ -f "$TASK_MAP" ]]; then
        rm -f "$TASK_MAP"
    fi
}

setup_test_env() {
    cleanup_task
    mkdir -p "$PROJECT_ROOT/.workflow"
}

# ═══════════════════════════════════════════════════════════════
# Test 1: 任务启动创建绑定记录
# ═══════════════════════════════════════════════════════════════

test_task_start_creates_binding() {
    echo -e "\n${BLUE}[TEST 1]${NC} 任务启动应该创建绑定记录"

    setup_test_env

    # 启动任务
    bash "$TASK_LIFECYCLE" start "测试任务" "feature/test" >/dev/null 2>&1

    # 验证JSON文件存在
    if [[ ! -f "$TASK_MAP" ]]; then
        print_result "JSON文件创建" "EXISTS" "NOT_FOUND"
        cleanup_task
        return 1
    fi

    # 验证JSON内容
    local active_task=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null)
    if [[ -z "$active_task" ]]; then
        print_result "活动任务记录" "EXISTS" "EMPTY"
        cleanup_task
        return 1
    fi

    # 验证分支绑定
    local bound_branch=$(echo "$active_task" | jq -r '.branch')
    print_result "分支绑定正确" "feature/test" "$bound_branch"

    cleanup_task
}

# ═══════════════════════════════════════════════════════════════
# Test 2: 正确分支应该允许操作
# ═══════════════════════════════════════════════════════════════

test_correct_branch_allows_operation() {
    echo -e "\n${BLUE}[TEST 2]${NC} 正确分支应该允许Write操作"

    setup_test_env

    # 创建测试分支
    git checkout -b test_branch_correct 2>/dev/null || git checkout test_branch_correct

    # 启动任务
    bash "$TASK_LIFECYCLE" start "测试任务" "test_branch_correct" >/dev/null 2>&1

    # 尝试操作（应该成功）
    if bash "$TASK_ENFORCER" 2>/dev/null; then
        print_result "正确分支允许操作" "ALLOWED" "ALLOWED"
        local result=0
    else
        print_result "正确分支允许操作" "ALLOWED" "BLOCKED"
        local result=1
    fi

    cleanup_task
    git checkout main 2>/dev/null
    git branch -D test_branch_correct 2>/dev/null || true

    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 3: 任务完成应该清理绑定
# ═══════════════════════════════════════════════════════════════

test_task_complete_clears_binding() {
    echo -e "\n${BLUE}[TEST 3]${NC} 任务完成应该清除绑定记录"

    setup_test_env

    # 启动并完成任务
    bash "$TASK_LIFECYCLE" start "测试任务" "feature/test" >/dev/null 2>&1
    bash "$TASK_LIFECYCLE" complete >/dev/null 2>&1

    # 验证绑定已清除
    local active_task=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null)

    if [[ -z "$active_task" || "$active_task" == "null" ]]; then
        print_result "绑定已清除" "CLEARED" "CLEARED"
        local result=0
    else
        print_result "绑定已清除" "CLEARED" "STILL_EXISTS"
        local result=1
    fi

    cleanup_task
    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 4: 错误分支应该阻止操作
# ═══════════════════════════════════════════════════════════════

test_wrong_branch_blocks_operation() {
    echo -e "\n${BLUE}[TEST 4]${NC} 错误分支应该阻止Write操作"

    setup_test_env

    # 创建测试分支
    git checkout -b test_branch_wrong 2>/dev/null || git checkout test_branch_wrong

    # 启动任务（绑定到test_branch_wrong）
    bash "$TASK_LIFECYCLE" start "测试任务" "test_branch_wrong" >/dev/null 2>&1

    # 切换到错误分支
    git checkout main 2>/dev/null

    # 尝试操作（应该被阻止）
    if bash "$TASK_ENFORCER" 2>/dev/null; then
        print_result "错误分支阻止操作" "BLOCKED" "ALLOWED"
        local result=1
    else
        print_result "错误分支阻止操作" "BLOCKED" "BLOCKED"
        local result=0
    fi

    cleanup_task
    git branch -D test_branch_wrong 2>/dev/null || true

    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 5: 无活动任务应该允许操作
# ═══════════════════════════════════════════════════════════════

test_no_active_task_allows_operation() {
    echo -e "\n${BLUE}[TEST 5]${NC} 无活动任务应该允许任何分支操作"

    setup_test_env

    # 不启动任务，直接尝试操作
    if bash "$TASK_ENFORCER" 2>/dev/null; then
        print_result "无任务时允许操作" "ALLOWED" "ALLOWED"
        return 0
    else
        print_result "无任务时允许操作" "ALLOWED" "BLOCKED"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════
# Test 6: JSON损坏应该降级允许
# ═══════════════════════════════════════════════════════════════

test_corrupted_json_degrades_gracefully() {
    echo -e "\n${BLUE}[TEST 6]${NC} JSON损坏应该降级处理（允许操作）"

    setup_test_env

    # 创建损坏的JSON
    echo "{ invalid json" > "$TASK_MAP"

    # 尝试操作（应该降级允许）
    if bash "$TASK_ENFORCER" 2>/dev/null; then
        print_result "JSON损坏时降级" "ALLOWED" "ALLOWED"
        local result=0
    else
        print_result "JSON损坏时降级" "ALLOWED" "BLOCKED"
        local result=1
    fi

    cleanup_task
    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 7: task_status显示当前任务
# ═══════════════════════════════════════════════════════════════

test_task_status_shows_current_task() {
    echo -e "\n${BLUE}[TEST 7]${NC} task_status应该显示当前任务信息"

    setup_test_env

    # 启动任务
    bash "$TASK_LIFECYCLE" start "测试任务123" "feature/test123" >/dev/null 2>&1

    # 查询状态
    local status_output=$(bash "$TASK_LIFECYCLE" status 2>&1)

    # 验证输出包含任务信息
    if echo "$status_output" | grep -q "测试任务123" && echo "$status_output" | grep -q "feature/test123"; then
        print_result "status显示任务信息" "SHOWN" "SHOWN"
        local result=0
    else
        print_result "status显示任务信息" "SHOWN" "NOT_SHOWN"
        local result=1
    fi

    cleanup_task
    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 8: task_cancel强制取消绑定
# ═══════════════════════════════════════════════════════════════

test_task_cancel_forces_unbind() {
    echo -e "\n${BLUE}[TEST 8]${NC} task_cancel应该强制取消绑定"

    setup_test_env

    # 启动任务
    bash "$TASK_LIFECYCLE" start "测试任务" "feature/test" >/dev/null 2>&1

    # 取消任务
    bash "$TASK_LIFECYCLE" cancel >/dev/null 2>&1

    # 验证绑定已清除
    local active_task=$(jq -r '.active_task // empty' "$TASK_MAP" 2>/dev/null)

    if [[ -z "$active_task" || "$active_task" == "null" ]]; then
        print_result "cancel清除绑定" "CLEARED" "CLEARED"
        local result=0
    else
        print_result "cancel清除绑定" "CLEARED" "STILL_EXISTS"
        local result=1
    fi

    cleanup_task
    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 9: task_history显示历史任务
# ═══════════════════════════════════════════════════════════════

test_task_history_shows_completed_tasks() {
    echo -e "\n${BLUE}[TEST 9]${NC} task_history应该显示已完成任务"

    setup_test_env

    # 启动并完成任务
    bash "$TASK_LIFECYCLE" start "历史任务1" "feature/hist1" >/dev/null 2>&1
    bash "$TASK_LIFECYCLE" complete >/dev/null 2>&1

    # 查询历史
    local history_output=$(bash "$TASK_LIFECYCLE" history 2>&1)

    # 验证输出包含历史任务
    if echo "$history_output" | grep -q "历史任务1"; then
        print_result "history显示历史任务" "SHOWN" "SHOWN"
        local result=0
    else
        print_result "history显示历史任务" "SHOWN" "NOT_SHOWN"
        local result=1
    fi

    cleanup_task
    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 10: Hook执行时间 < 50ms
# ═══════════════════════════════════════════════════════════════

test_hook_performance() {
    echo -e "\n${BLUE}[TEST 10]${NC} Hook执行时间应该 < 50ms"

    setup_test_env

    # 启动任务
    git checkout -b test_branch_perf 2>/dev/null || git checkout test_branch_perf
    bash "$TASK_LIFECYCLE" start "性能测试" "test_branch_perf" >/dev/null 2>&1

    # 测试执行时间
    local start_time=$(date +%s%N)
    bash "$TASK_ENFORCER" >/dev/null 2>&1 || true
    local end_time=$(date +%s%N)

    local duration_ms=$(( (end_time - start_time) / 1000000 ))

    if [[ $duration_ms -lt 50 ]]; then
        print_result "Hook性能 (<50ms)" "PASS" "PASS (${duration_ms}ms)"
        local result=0
    else
        print_result "Hook性能 (<50ms)" "PASS" "FAIL (${duration_ms}ms)"
        local result=1
    fi

    cleanup_task
    git checkout main 2>/dev/null
    git branch -D test_branch_perf 2>/dev/null || true

    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 11: 分支名特殊字符处理
# ═══════════════════════════════════════════════════════════════

test_branch_name_special_chars() {
    echo -e "\n${BLUE}[TEST 11]${NC} 分支名包含特殊字符应该正确处理"

    setup_test_env

    local special_branch="feature/test-branch_123"

    # 创建特殊分支名
    git checkout -b "$special_branch" 2>/dev/null || git checkout "$special_branch"

    # 启动任务
    bash "$TASK_LIFECYCLE" start "特殊字符测试" "$special_branch" >/dev/null 2>&1

    # 验证操作
    if bash "$TASK_ENFORCER" 2>/dev/null; then
        print_result "特殊字符分支名处理" "PASS" "PASS"
        local result=0
    else
        print_result "特殊字符分支名处理" "PASS" "FAIL"
        local result=1
    fi

    cleanup_task
    git checkout main 2>/dev/null
    git branch -D "$special_branch" 2>/dev/null || true

    return $result
}

# ═══════════════════════════════════════════════════════════════
# Test 12: 防止重复启动任务
# ═══════════════════════════════════════════════════════════════

test_prevent_duplicate_task_start() {
    echo -e "\n${BLUE}[TEST 12]${NC} 应该阻止重复启动任务"

    setup_test_env

    # 启动第一个任务
    bash "$TASK_LIFECYCLE" start "任务1" "feature/task1" >/dev/null 2>&1

    # 尝试启动第二个任务（应该被阻止）
    if bash "$TASK_LIFECYCLE" start "任务2" "feature/task2" >/dev/null 2>&1; then
        print_result "阻止重复启动" "BLOCKED" "ALLOWED"
        local result=1
    else
        print_result "阻止重复启动" "BLOCKED" "BLOCKED"
        local result=0
    fi

    cleanup_task
    return $result
}

# ═══════════════════════════════════════════════════════════════
# 主测试流程
# ═══════════════════════════════════════════════════════════════

main() {
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  任务-分支绑定系统测试套件${NC}"
    echo -e "${BOLD}  Claude Enhancer v6.5.0${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"

    # 检查必需工具
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${RED}❌ 错误：jq未安装${NC}" >&2
        echo "请安装jq: sudo apt-get install jq (或 brew install jq)" >&2
        exit 1
    fi

    # 保存当前分支
    local original_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

    # 运行所有测试
    test_task_start_creates_binding || true
    test_correct_branch_allows_operation || true
    test_task_complete_clears_binding || true
    test_wrong_branch_blocks_operation || true
    test_no_active_task_allows_operation || true
    test_corrupted_json_degrades_gracefully || true
    test_task_status_shows_current_task || true
    test_task_cancel_forces_unbind || true
    test_task_history_shows_completed_tasks || true
    test_hook_performance || true
    test_branch_name_special_chars || true
    test_prevent_duplicate_task_start || true

    # 恢复原始分支
    git checkout "$original_branch" 2>/dev/null || true

    # 汇总结果
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  测试汇总${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}通过:${NC} $TESTS_PASSED"
    echo -e "${RED}失败:${NC} $TESTS_FAILED"
    echo -e "${YELLOW}跳过:${NC} $TESTS_SKIPPED"
    echo -e "${BLUE}总计:${NC} $((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))"
    echo ""

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}✅ 所有测试通过！${NC}"
        exit 0
    else
        echo -e "${RED}${BOLD}❌ ${TESTS_FAILED} 个测试失败${NC}"
        exit 1
    fi
}

# 如果直接执行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
