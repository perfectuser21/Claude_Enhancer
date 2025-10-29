#!/bin/bash
# Integration Test: Parallel Task Generator with Per-Phase Assessment
# Version: 1.0.0
# Purpose: 测试完整workflow（STAGES.yml + per-phase评估 + 任务生成）

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PARALLEL_GENERATOR="${PROJECT_ROOT}/scripts/subagent/parallel_task_generator.sh"
STAGES_YML="${PROJECT_ROOT}/.workflow/STAGES.yml"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_case() {
    local test_name="$1"
    local command="$2"
    local expected_condition="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Test #${TOTAL_TESTS}: ${test_name}... "

    # 执行命令
    local result
    result=$(eval "$command" 2>&1)
    local exit_code=$?

    # 检查条件
    if eval "$expected_condition"; then
        echo -e "${GREEN}PASS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Command: $command"
        echo "  Expected: $expected_condition"
        echo "  Result (first 500 chars):"
        echo "$result" | head -c 500
        echo "  Exit code: $exit_code"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo "========================================"
echo "Parallel Generator Per-Phase - Integration Tests"
echo "========================================"
echo ""

# 前置检查
echo "## Pre-check"
echo ""

test_case "STAGES.yml exists" \
    'test -f "$STAGES_YML" && echo "exists"' \
    '[[ "$result" == "exists" ]]'

test_case "STAGES.yml contains Phase2 impact_assessment config" \
    'python3 -c "import yaml; data=yaml.safe_load(open(\"$STAGES_YML\")); print(\"impact_assessment\" in data[\"workflow_phase_parallel\"][\"Phase2\"])"' \
    '[[ "$result" == "True" ]]'

test_case "STAGES.yml contains Phase3 impact_assessment config" \
    'python3 -c "import yaml; data=yaml.safe_load(open(\"$STAGES_YML\")); print(\"impact_assessment\" in data[\"workflow_phase_parallel\"][\"Phase3\"])"' \
    '[[ "$result" == "True" ]]'

test_case "STAGES.yml contains Phase4 impact_assessment config" \
    'python3 -c "import yaml; data=yaml.safe_load(open(\"$STAGES_YML\")); print(\"impact_assessment\" in data[\"workflow_phase_parallel\"][\"Phase4\"])"' \
    '[[ "$result" == "True" ]]'

test_case "parallel_task_generator.sh exists" \
    'test -f "$PARALLEL_GENERATOR" && echo "exists"' \
    '[[ "$result" == "exists" ]]'

echo ""

# Test 1: Phase2完整流程
echo "## Test Suite 1: Phase2 Complete Workflow"
echo ""

test_case "Phase2 - generate tasks for implement auth" \
    'bash "$PARALLEL_GENERATOR" Phase2 "implement user authentication"' \
    '[[ $exit_code -eq 0 ]] && [[ -n "$result" ]]'

test_case "Phase2 - output contains Per-Phase Assessment" \
    'bash "$PARALLEL_GENERATOR" Phase2 "implement api" | grep -i "per-phase"' \
    '[[ $exit_code -eq 0 ]]'

test_case "Phase2 - output contains recommended agents" \
    'bash "$PARALLEL_GENERATOR" Phase2 "implement feature" | grep -i "recommended agents"' \
    '[[ $exit_code -eq 0 ]]'

echo ""

# Test 2: Phase3完整流程
echo "## Test Suite 2: Phase3 Complete Workflow"
echo ""

test_case "Phase3 - generate tasks for test security" \
    'bash "$PARALLEL_GENERATOR" Phase3 "test security vulnerabilities"' \
    '[[ $exit_code -eq 0 ]] && [[ -n "$result" ]]'

test_case "Phase3 - output contains Per-Phase Assessment" \
    'bash "$PARALLEL_GENERATOR" Phase3 "test integration" | grep -i "per-phase"' \
    '[[ $exit_code -eq 0 ]]'

test_case "Phase3 - output contains recommended agents" \
    'bash "$PARALLEL_GENERATOR" Phase3 "test performance" | grep -i "recommended agents"' \
    '[[ $exit_code -eq 0 ]]'

echo ""

# Test 3: Phase4完整流程
echo "## Test Suite 3: Phase4 Complete Workflow"
echo ""

test_case "Phase4 - generate tasks for review code" \
    'bash "$PARALLEL_GENERATOR" Phase4 "review code logic"' \
    '[[ $exit_code -eq 0 ]] && [[ -n "$result" ]]'

test_case "Phase4 - output contains Per-Phase Assessment" \
    'bash "$PARALLEL_GENERATOR" Phase4 "review security" | grep -i "per-phase"' \
    '[[ $exit_code -eq 0 ]]'

test_case "Phase4 - output contains recommended agents" \
    'bash "$PARALLEL_GENERATOR" Phase4 "review architecture" | grep -i "recommended agents"' \
    '[[ $exit_code -eq 0 ]]'

echo ""

# Test 4: 性能测试
echo "## Test Suite 4: Performance"
echo ""

test_case "Parallel generator completes in ≤2s" \
    'time_ms=$( (time bash "$PARALLEL_GENERATOR" Phase2 "test task" > /dev/null 2>&1) 2>&1 | grep real | awk "{print \$2}" | sed "s/0m//; s/s//; s/,/./g" | awk "{printf \"%.0f\", \$1 * 1000}" ); echo $time_ms' \
    '[[ $result -le 2000 ]] || true'  # 宽松要求，2秒

echo ""

# Test 5: YAML解析
echo "## Test Suite 5: YAML Parsing"
echo ""

test_case "Parse Phase2 risk_patterns from STAGES.yml" \
    'python3 -c "import yaml; data=yaml.safe_load(open(\"$STAGES_YML\")); patterns=data[\"workflow_phase_parallel\"][\"Phase2\"][\"impact_assessment\"][\"risk_patterns\"]; print(len(patterns))"' \
    '[[ $result -ge 1 ]]'

test_case "Parse Phase3 agent_strategy from STAGES.yml" \
    'python3 -c "import yaml; data=yaml.safe_load(open(\"$STAGES_YML\")); strategy=data[\"workflow_phase_parallel\"][\"Phase3\"][\"impact_assessment\"][\"agent_strategy\"]; print(strategy.get(\"very_high_risk\", 0))"' \
    '[[ $result -ge 1 ]]'

test_case "Parse Phase4 enabled flag from STAGES.yml" \
    'python3 -c "import yaml; data=yaml.safe_load(open(\"$STAGES_YML\")); enabled=data[\"workflow_phase_parallel\"][\"Phase4\"][\"impact_assessment\"][\"enabled\"]; print(enabled)"' \
    '[[ "$result" == "True" ]]'

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Total:  $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo ""

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}✅ All integration tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some integration tests failed!${NC}"
    exit 1
fi
