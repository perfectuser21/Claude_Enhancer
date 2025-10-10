#!/bin/bash
# Stop-Ship Fixes Validation Master Script
# 验证所有7个Stop-Ship修复的完整性

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$PROJECT_ROOT/test"

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}        Stop-Ship Fixes Validation Suite${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查bats是否安装
check_bats() {
    if ! command -v bats &> /dev/null; then
        echo -e "${YELLOW}⚠️  bats not found, installing...${NC}"

        if command -v npm &> /dev/null; then
            npm install -g bats || {
                echo -e "${RED}❌ Failed to install bats${NC}"
                echo "Please install manually: https://github.com/bats-core/bats-core"
                exit 1
            }
        else
            echo -e "${RED}❌ npm not found, cannot install bats${NC}"
            echo "Please install bats manually: https://github.com/bats-core/bats-core"
            exit 1
        fi
    fi
    echo -e "${GREEN}✅ bats is installed${NC}"
}

# 运行单个测试文件
run_test_file() {
    local test_file="$1"
    local test_name="$(basename "$test_file" .bats)"

    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Running: $test_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local output_file="/tmp/bats_output_$$.txt"

    if bats "$test_file" > "$output_file" 2>&1; then
        # 测试通过
        local passed=$(grep -c "✓" "$output_file" 2>/dev/null || echo 0)
        local skipped=$(grep -c "skipped" "$output_file" 2>/dev/null || echo 0)

        PASSED_TESTS=$((PASSED_TESTS + passed))
        SKIPPED_TESTS=$((SKIPPED_TESTS + skipped))
        TOTAL_TESTS=$((TOTAL_TESTS + passed + skipped))

        echo -e "${GREEN}✅ $test_name: $passed tests passed${NC}"
        if [ "$skipped" -gt 0 ]; then
            echo -e "${YELLOW}   ⊘ $skipped tests skipped${NC}"
        fi
    else
        # 测试失败
        local failed=$(grep -c "✗" "$output_file" 2>/dev/null || echo 1)
        local passed=$(grep -c "✓" "$output_file" 2>/dev/null || echo 0)
        local skipped=$(grep -c "skipped" "$output_file" 2>/dev/null || echo 0)

        FAILED_TESTS=$((FAILED_TESTS + failed))
        PASSED_TESTS=$((PASSED_TESTS + passed))
        SKIPPED_TESTS=$((SKIPPED_TESTS + skipped))
        TOTAL_TESTS=$((TOTAL_TESTS + passed + failed + skipped))

        echo -e "${RED}❌ $test_name: $failed tests failed${NC}"
        echo -e "${YELLOW}   Failed tests:${NC}"
        grep "✗" "$output_file" | sed 's/^/   /'
    fi

    # 显示详细输出（如果有错误）
    if grep -q "✗" "$output_file"; then
        echo -e "\n${YELLOW}Detailed output:${NC}"
        cat "$output_file" | sed 's/^/   /'
    fi

    rm -f "$output_file"
}

# 生成测试报告
generate_report() {
    local report_file="$PROJECT_ROOT/test/reports/stop_ship_fixes_$(date +%Y%m%d_%H%M%S).md"
    mkdir -p "$(dirname "$report_file")"

    cat > "$report_file" <<EOF
# Stop-Ship Fixes Validation Report

**Date**: $(date +'%Y-%m-%d %H:%M:%S')
**Project**: Claude Enhancer 5.0

## Summary

| Metric | Count |
|--------|-------|
| Total Tests | $TOTAL_TESTS |
| Passed | $PASSED_TESTS |
| Failed | $FAILED_TESTS |
| Skipped | $SKIPPED_TESTS |
| Success Rate | $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS / $TOTAL_TESTS) * 100}")% |

## Test Coverage

### P0: rm -rf Safety Protection
- Path whitelist validation
- Dry-run mode
- Interactive confirmation
- Symlink detection
- Critical path blocking

### P1-1: commit-msg Force Block
- No Phase file rejection
- Exit code validation
- Error message display
- Phase validation logic
- Automatic Phase prefix

### P1-2: Coverage Threshold
- Below 80% rejection
- Report generation (lcov.info, coverage.xml)
- Multi-dimensional coverage
- Regression detection

### P1-3: Parallel Task Mutex
- Conflict detection
- Timeout mechanism
- Deadlock prevention
- Lock cleanup
- Atomic operations

### P1-4: Signature Verification
- Tamper detection
- Missing signature rejection
- Timestamp validation
- Replay attack prevention
- SHA-256 hashing

### P1-5: Version Consistency
- VERSION file validation
- manifest.yml sync
- settings.json sync
- Semver compliance
- Git tag matching

### P1-6: Hooks Activation
- Hook triggering
- Log recording
- Timestamp tracking
- Trigger counting
- Performance monitoring

## Results

EOF

    # 添加每个测试的结果
    for test_file in "$TEST_DIR"/stop_ship_*.bats; do
        [ -f "$test_file" ] || continue
        local test_name="$(basename "$test_file" .bats)"
        echo "- [$test_name]($test_file)" >> "$report_file"
    done

    cat >> "$report_file" <<EOF

## Recommendations

EOF

    if [ "$FAILED_TESTS" -gt 0 ]; then
        cat >> "$report_file" <<EOF
### ⚠️ Action Required

$FAILED_TESTS test(s) failed. Please review the failures above and:

1. Verify the fix implementation
2. Update tests if requirements changed
3. Re-run validation after fixes

EOF
    else
        cat >> "$report_file" <<EOF
### ✅ All Tests Passed

All Stop-Ship fixes have been validated successfully. The system is ready for:

1. Production deployment
2. PR merge approval
3. Release tagging

EOF
    fi

    echo -e "${GREEN}📄 Report generated: $report_file${NC}"
}

# 主函数
main() {
    cd "$PROJECT_ROOT"

    # 检查bats安装
    check_bats

    echo -e "\n${CYAN}🔍 Discovering test files...${NC}"

    # 查找所有Stop-Ship测试文件
    local test_files=()
    for test_file in "$TEST_DIR"/stop_ship_*.bats; do
        if [ -f "$test_file" ]; then
            test_files+=("$test_file")
            echo -e "   Found: $(basename "$test_file")"
        fi
    done

    if [ ${#test_files[@]} -eq 0 ]; then
        echo -e "${RED}❌ No test files found in $TEST_DIR${NC}"
        exit 1
    fi

    echo -e "${GREEN}   Total: ${#test_files[@]} test suites${NC}"

    # 运行所有测试
    for test_file in "${test_files[@]}"; do
        run_test_file "$test_file"
    done

    # 生成报告
    echo ""
    generate_report

    # 显示最终统计
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}                    Final Results${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "   Total Tests:   ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "   ${GREEN}✅ Passed:      $PASSED_TESTS${NC}"
    echo -e "   ${RED}❌ Failed:      $FAILED_TESTS${NC}"
    echo -e "   ${YELLOW}⊘  Skipped:     $SKIPPED_TESTS${NC}"
    echo ""

    if [ "$FAILED_TESTS" -eq 0 ]; then
        success_rate=$(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS / $TOTAL_TESTS) * 100}")
        echo -e "   ${GREEN}Success Rate:  ${success_rate}%${NC}"
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}  🎉 All Stop-Ship Fixes Validated Successfully!${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        exit 0
    else
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}  ⚠️  Some Tests Failed - Review Required${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        exit 1
    fi
}

# 运行主函数
main "$@"
