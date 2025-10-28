#!/bin/bash
# 测试并行执行器集成
# 用途：验证parallel_executor已正确集成到executor.sh

set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Testing Parallel Executor Integration ==="

TESTS_PASSED=0
TESTS_TOTAL=0

run_test() {
    local name="$1"
    local command="$2"

    ((TESTS_TOTAL++))
    echo -e "\n[Test $TESTS_TOTAL] $name"

    if eval "$command"; then
        echo "✓ PASS"
        ((TESTS_PASSED++))
        return 0
    else
        echo "✗ FAIL"
        return 1
    fi
}

# Test 1: Phase命名统一性
run_test "Phase naming consistency" '
    p_count=$(grep -c "^  P[0-9]:" .workflow/STAGES.yml 2>/dev/null || echo 0)
    phase_count=$(grep -c "^  Phase[0-9]:" .workflow/STAGES.yml 2>/dev/null || echo 0)
    [[ $p_count -eq 0 && $phase_count -eq 6 ]]
'

# Test 2: parallel_executor可加载
run_test "parallel_executor loadable" '
    source .workflow/lib/parallel_executor.sh 2>/dev/null &&
    type init_parallel_system >/dev/null 2>&1
'

# Test 3: 日志目录存在
run_test "Logs directory exists" '
    [[ -d .workflow/logs ]]
'

# Test 4: executor.sh语法正确
run_test "executor.sh syntax valid" '
    bash -n .workflow/executor.sh
'

# Test 5: STAGES.yml有Phase3配置
run_test "Phase3 parallel configuration" '
    grep -q "^  Phase3:" .workflow/STAGES.yml
'

# Test 6: executor.sh包含is_parallel_enabled
run_test "is_parallel_enabled function exists" '
    grep -q "is_parallel_enabled()" .workflow/executor.sh
'

# Test 7: executor.sh包含execute_parallel_workflow
run_test "execute_parallel_workflow function exists" '
    grep -q "execute_parallel_workflow()" .workflow/executor.sh
'

# Test 8: executor.sh调用了并行执行
run_test "Parallel execution integrated in main" '
    grep -q "if is_parallel_enabled" .workflow/executor.sh
'

# 总结
echo -e "\n=== Test Summary ==="
echo "Total: $TESTS_TOTAL"
echo "Passed: $TESTS_PASSED"
echo "Failed: $((TESTS_TOTAL - TESTS_PASSED))"

if [[ $TESTS_PASSED -eq $TESTS_TOTAL ]]; then
    echo -e "\n✓ All tests passed!"
    exit 0
else
    echo -e "\n✗ Some tests failed"
    exit 1
fi
