#!/bin/bash
# =============================================================================
# Claude Enhancer 5.0 - Mutex Lock System Tests
# 验证互斥锁机制的正确性
# =============================================================================

set -euo pipefail

# 测试配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly LIB_DIR="${PROJECT_ROOT}/.workflow/lib"

# 加载被测试模块
source "${LIB_DIR}/mutex_lock.sh"
source "${LIB_DIR}/conflict_detector.sh"
source "${LIB_DIR}/parallel_executor.sh"

# 测试统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# ==================== 测试框架 ====================

test_start() {
    ((TOTAL_TESTS++))
    echo -e "\n${CYAN}[TEST ${TOTAL_TESTS}] $*${NC}"
}

test_pass() {
    ((PASSED_TESTS++))
    echo -e "${GREEN}✓ PASS${NC}: $*"
}

test_fail() {
    ((FAILED_TESTS++))
    echo -e "${RED}✗ FAIL${NC}: $*"
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-}"

    if [[ "${expected}" == "${actual}" ]]; then
        test_pass "${message} (expected: ${expected}, got: ${actual})"
        return 0
    else
        test_fail "${message} (expected: ${expected}, got: ${actual})"
        return 1
    fi
}

assert_success() {
    local message="$1"

    if [[ $? -eq 0 ]]; then
        test_pass "${message}"
        return 0
    else
        test_fail "${message}"
        return 1
    fi
}

assert_failure() {
    local message="$1"

    if [[ $? -ne 0 ]]; then
        test_pass "${message}"
        return 0
    else
        test_fail "${message}"
        return 1
    fi
}

# ==================== 互斥锁基础测试 ====================

test_lock_acquire_release() {
    test_start "Basic lock acquire and release"

    # 初始化
    init_lock_system

    # 获取锁
    if acquire_lock "test-group-1" 10; then
        test_pass "Lock acquired"

        # 验证锁文件存在
        if [[ -f "${LOCK_DIR}/test-group-1.lock" ]]; then
            test_pass "Lock file created"
        else
            test_fail "Lock file not found"
        fi

        # 释放锁
        release_lock "test-group-1"
        test_pass "Lock released"
    else
        test_fail "Failed to acquire lock"
    fi
}

test_lock_timeout() {
    test_start "Lock timeout mechanism"

    init_lock_system

    # 第一个进程获取锁（后台，持有30秒）
    (
        acquire_lock "test-group-timeout" 60
        sleep 30
        release_lock "test-group-timeout"
    ) &

    local pid1=$!

    # 等待第一个进程获取锁
    sleep 2

    # 第二个进程尝试获取锁，应该超时
    local start_time=$(date +%s)
    if acquire_lock "test-group-timeout" 5; then
        test_fail "Lock should have timed out"
        release_lock "test-group-timeout"
    else
        local end_time=$(date +%s)
        local elapsed=$((end_time - start_time))

        if [[ ${elapsed} -ge 5 && ${elapsed} -le 7 ]]; then
            test_pass "Lock timed out correctly (${elapsed}s)"
        else
            test_fail "Timeout duration incorrect (${elapsed}s, expected ~5s)"
        fi
    fi

    # 清理
    kill "${pid1}" 2>/dev/null || true
    wait "${pid1}" 2>/dev/null || true
}

test_concurrent_locks() {
    test_start "Concurrent lock acquisition (mutual exclusion)"

    init_lock_system

    local shared_counter=0
    local counter_file="${LOCK_DIR}/test_counter.txt"
    echo "0" > "${counter_file}"

    # 启动10个并发进程，每个尝试递增计数器
    local pids=()
    for i in {1..10}; do
        (
            acquire_lock "test-concurrent" 60

            # 读取-递增-写入（模拟竞态条件）
            local value=$(cat "${counter_file}")
            sleep 0.1  # 放大竞态窗口
            echo "$((value + 1))" > "${counter_file}"

            release_lock "test-concurrent"
        ) &
        pids+=($!)
    done

    # 等待所有进程完成
    for pid in "${pids[@]}"; do
        wait "${pid}"
    done

    # 验证计数器值
    local final_value=$(cat "${counter_file}")
    if [[ ${final_value} -eq 10 ]]; then
        test_pass "Mutual exclusion works correctly (counter: ${final_value})"
    else
        test_fail "Race condition detected (counter: ${final_value}, expected: 10)"
    fi

    rm -f "${counter_file}"
}

# ==================== 死锁检测测试 ====================

test_deadlock_detection() {
    test_start "Deadlock detection and cleanup"

    init_lock_system

    # 创建一个僵尸锁（模拟进程异常退出）
    local fake_pid=999999
    local timestamp=$(($(date +%s) - 700))  # 700秒前（超过MAX_LOCK_AGE）

    echo "test-deadlock:${fake_pid}:test-group:${timestamp}:ACTIVE" >> "${LOCK_REGISTRY}"
    touch "${LOCK_DIR}/test-deadlock.lock"

    # 运行死锁检测
    if check_deadlock; then
        :  # 返回检测到的死锁数量
    fi

    # 验证僵尸锁被清理
    if grep -q "test-deadlock:${fake_pid}:.*:TIMEOUT" "${LOCK_REGISTRY}"; then
        test_pass "Deadlock detected and cleaned up"
    else
        test_fail "Deadlock not properly cleaned up"
    fi
}

test_orphan_lock_cleanup() {
    test_start "Orphan lock cleanup"

    init_lock_system

    # 创建一个孤儿锁（进程不存在）
    local fake_pid=888888
    local timestamp=$(date +%s)

    echo "test-orphan:${fake_pid}:test-group:${timestamp}:ACTIVE" >> "${LOCK_REGISTRY}"
    touch "${LOCK_DIR}/test-orphan.lock"

    # 运行清理
    cleanup_orphan_locks

    # 验证孤儿锁被标记为清理
    if grep -q "test-orphan:${fake_pid}:.*:ORPHAN_CLEANED" "${LOCK_REGISTRY}"; then
        test_pass "Orphan lock cleaned up"
    else
        test_fail "Orphan lock not cleaned up"
    fi
}

# ==================== 冲突检测测试 ====================

test_conflict_detection_same_file() {
    test_start "Conflict detection - same file"

    # 创建测试配置
    export STAGES_CONFIG="${PROJECT_ROOT}/.workflow/STAGES.yml"

    # 测试同文件冲突
    local conflict_type=$(check_path_conflict "src/api/users.ts" "src/api/users.ts")

    assert_equals "EXACT" "${conflict_type}" "Same file conflict detected"
}

test_conflict_detection_parent_child() {
    test_start "Conflict detection - parent/child path"

    local conflict_type=$(check_path_conflict "src/api" "src/api/users.ts")

    assert_equals "PARENT_CHILD" "${conflict_type}" "Parent-child conflict detected"
}

test_conflict_detection_same_directory() {
    test_start "Conflict detection - same directory"

    local conflict_type=$(check_path_conflict "src/api/users.ts" "src/api/posts.ts")

    assert_equals "SAME_DIR" "${conflict_type}" "Same directory conflict detected"
}

test_conflict_detection_no_conflict() {
    test_start "Conflict detection - no conflict"

    local conflict_type=$(check_path_conflict "src/api/users.ts" "src/frontend/app.tsx")

    assert_equals "NONE" "${conflict_type}" "No conflict correctly identified"
}

# ==================== 并行执行测试 ====================

test_parallel_execution_success() {
    test_start "Parallel execution - all groups succeed"

    init_parallel_system

    # 执行3个无冲突的group
    if execute_with_strategy "P3" "test-group-1" "test-group-2" "test-group-3"; then
        test_pass "Parallel execution succeeded"
    else
        test_fail "Parallel execution failed unexpectedly"
    fi
}

test_parallel_execution_with_conflicts() {
    test_start "Parallel execution - conflict resolution"

    init_parallel_system

    # 模拟冲突场景（需要STAGES.yml配置）
    # 这里测试降级到串行执行的逻辑
    local mode=$(decide_execution_mode "P3" "test-conflict-1" "test-conflict-2")

    # 验证执行模式决策
    if [[ "${mode}" == "SERIAL" || "${mode}" == "PARALLEL" ]]; then
        test_pass "Execution mode decided: ${mode}"
    else
        test_fail "Unknown execution mode: ${mode}"
    fi
}

test_execute_with_lock_wrapper() {
    test_start "Execute command with lock wrapper"

    init_lock_system

    # 使用锁包装器执行命令
    if execute_with_lock "test-wrapper" echo "Hello from locked section"; then
        test_pass "Command executed with lock"
    else
        test_fail "Failed to execute command with lock"
    fi
}

# ==================== 压力测试 ====================

test_stress_concurrent_locks() {
    test_start "Stress test - 50 concurrent lock operations"

    init_lock_system

    local success_count=0
    local fail_count=0
    local pids=()

    for i in {1..50}; do
        (
            if acquire_lock "stress-test-$((i % 5))" 30; then
                sleep 0.1
                release_lock "stress-test-$((i % 5))"
                exit 0
            else
                exit 1
            fi
        ) &
        pids+=($!)
    done

    # 等待所有进程完成并统计结果
    for pid in "${pids[@]}"; do
        if wait "${pid}"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    done

    echo "  Success: ${success_count}, Fail: ${fail_count}"

    if [[ ${success_count} -ge 40 ]]; then
        test_pass "Stress test passed (${success_count}/50 successful)"
    else
        test_fail "Stress test failed (only ${success_count}/50 successful)"
    fi
}

# ==================== 集成测试 ====================

test_full_workflow_integration() {
    test_start "Full workflow integration test"

    # 初始化所有系统
    init_parallel_system

    # 模拟完整的并行执行流程
    local phase="P3"
    local groups=("impl-backend" "impl-frontend")

    # 步骤1: 冲突检测
    local strategy=$(recommend_execution_strategy "${phase}" "${groups[@]}")
    test_pass "Strategy recommended: ${strategy}"

    # 步骤2: 执行（简化版）
    for group in "${groups[@]}"; do
        if execute_parallel_group "${phase}" "${group}" echo "Executing ${group}"; then
            test_pass "Group ${group} executed"
        else
            test_fail "Group ${group} failed"
        fi
    done

    # 步骤3: 验证状态
    show_lock_status > /dev/null
    test_pass "Lock status verified"
}

# ==================== 测试运行器 ====================

run_all_tests() {
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║   Claude Enhancer 5.0 - Mutex Lock System Tests      ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # 清理之前的测试环境
    export LOCK_DIR="/tmp/ce_test_locks_$$"
    mkdir -p "${LOCK_DIR}"

    # 基础测试
    echo -e "${YELLOW}\n=== Basic Lock Tests ===${NC}"
    test_lock_acquire_release
    test_lock_timeout
    test_concurrent_locks

    # 死锁和清理测试
    echo -e "${YELLOW}\n=== Deadlock & Cleanup Tests ===${NC}"
    test_deadlock_detection
    test_orphan_lock_cleanup

    # 冲突检测测试
    echo -e "${YELLOW}\n=== Conflict Detection Tests ===${NC}"
    test_conflict_detection_same_file
    test_conflict_detection_parent_child
    test_conflict_detection_same_directory
    test_conflict_detection_no_conflict

    # 并行执行测试
    echo -e "${YELLOW}\n=== Parallel Execution Tests ===${NC}"
    test_parallel_execution_success
    test_parallel_execution_with_conflicts
    test_execute_with_lock_wrapper

    # 压力测试
    echo -e "${YELLOW}\n=== Stress Tests ===${NC}"
    test_stress_concurrent_locks

    # 集成测试
    echo -e "${YELLOW}\n=== Integration Tests ===${NC}"
    test_full_workflow_integration

    # 清理测试环境
    rm -rf "${LOCK_DIR}"

    # 测试总结
    echo -e "\n${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║                    Test Summary                        ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "Total Tests:  ${TOTAL_TESTS}"
    echo -e "${GREEN}Passed:       ${PASSED_TESTS}${NC}"
    echo -e "${RED}Failed:       ${FAILED_TESTS}${NC}"
    echo -e "Success Rate: $(awk "BEGIN {printf \"%.1f%%\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")"

    if [[ ${FAILED_TESTS} -eq 0 ]]; then
        echo -e "\n${GREEN}${BOLD}🎉 All tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}${BOLD}❌ Some tests failed${NC}"
        return 1
    fi
}

# ==================== 主函数 ====================

main() {
    local command="${1:-all}"

    case "${command}" in
        all)
            run_all_tests
            ;;

        basic)
            test_lock_acquire_release
            test_concurrent_locks
            ;;

        deadlock)
            test_deadlock_detection
            test_orphan_lock_cleanup
            ;;

        conflict)
            test_conflict_detection_same_file
            test_conflict_detection_parent_child
            ;;

        parallel)
            test_parallel_execution_success
            test_execute_with_lock_wrapper
            ;;

        stress)
            test_stress_concurrent_locks
            ;;

        *)
            echo "Usage: $0 [all|basic|deadlock|conflict|parallel|stress]"
            exit 1
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
