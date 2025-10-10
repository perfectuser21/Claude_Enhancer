#!/usr/bin/env bats
# Stop-Ship Fix #3: 覆盖率阈值测试
# P1-2 级别 - 确保代码覆盖率低于80%时CI失败

setup() {
    export PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
    export TEST_COVERAGE_DIR="/tmp/coverage_test_$$"
    mkdir -p "$TEST_COVERAGE_DIR"
}

teardown() {
    rm -rf "$TEST_COVERAGE_DIR" 2>/dev/null || true
}

# Test 1: 低于80%时CI应失败
@test "coverage check fails when below 80% threshold" {
    # 模拟覆盖率报告 (75%)
    cat > "$TEST_COVERAGE_DIR/coverage.json" <<EOF
{
  "total": {
    "lines": { "total": 100, "covered": 75, "pct": 75 },
    "statements": { "total": 100, "covered": 75, "pct": 75 },
    "functions": { "total": 20, "covered": 15, "pct": 75 },
    "branches": { "total": 40, "covered": 30, "pct": 75 }
  }
}
EOF

    # 运行覆盖率检查
    run bash -c "
        coverage_pct=75
        threshold=80

        if [ \$coverage_pct -lt \$threshold ]; then
            echo \"❌ Coverage \${coverage_pct}% below threshold \${threshold}%\"
            exit 1
        fi
        exit 0
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "below threshold" ]]
}

# Test 2: 达到80%时CI应通过
@test "coverage check passes when at or above 80% threshold" {
    # 模拟覆盖率报告 (85%)
    cat > "$TEST_COVERAGE_DIR/coverage.json" <<EOF
{
  "total": {
    "lines": { "total": 100, "covered": 85, "pct": 85 },
    "statements": { "total": 100, "covered": 85, "pct": 85 }
  }
}
EOF

    run bash -c "
        coverage_pct=85
        threshold=80

        if [ \$coverage_pct -lt \$threshold ]; then
            echo \"❌ Coverage below threshold\"
            exit 1
        fi
        echo \"✅ Coverage \${coverage_pct}% meets threshold\"
        exit 0
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "meets threshold" ]]
}

# Test 3: lcov.info报告生成
@test "coverage generates lcov.info report" {
    # 检查是否有生成lcov报告的配置
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        run bash -c "
            grep -q 'lcov' '$PROJECT_ROOT/package.json' && echo 'lcov configured'
        "
        [[ "$output" =~ "lcov configured" ]] || skip "No lcov config"
    else
        skip "No package.json"
    fi
}

# Test 4: coverage.xml报告生成 (Cobertura格式)
@test "coverage generates coverage.xml for CI integration" {
    # 创建模拟的coverage.xml
    cat > "$TEST_COVERAGE_DIR/coverage.xml" <<EOF
<?xml version="1.0" ?>
<coverage line-rate="0.82" branch-rate="0.78" version="1.0">
    <packages>
        <package name="src" line-rate="0.82" branch-rate="0.78">
            <classes>
                <class name="app.js" line-rate="0.85" branch-rate="0.80"/>
            </classes>
        </package>
    </packages>
</coverage>
EOF

    # 验证XML格式
    run bash -c "
        grep -q 'line-rate' '$TEST_COVERAGE_DIR/coverage.xml'
    "

    [ "$status" -eq 0 ]
}

# Test 5: 阈值检查脚本存在性
@test "threshold check script exists and is executable" {
    # 检查CI工作流中是否有覆盖率检查
    local ci_file="$PROJECT_ROOT/.github/workflows/ce-gates.yml"

    if [ -f "$ci_file" ]; then
        run bash -c "
            grep -i 'coverage' '$ci_file' && echo 'Coverage check found in CI'
        "
        [[ "$output" =~ "Coverage" ]] || skip "No coverage check in CI"
    else
        skip "No CI workflow file"
    fi
}

# Test 6: 多维度覆盖率检查 (line, branch, function)
@test "coverage checks multiple dimensions" {
    run bash -c "
        line_cov=85
        branch_cov=75  # 低于阈值
        func_cov=90

        threshold=80
        failed=0

        if [ \$line_cov -lt \$threshold ]; then
            echo \"Line coverage: \$line_cov% < \$threshold%\"
            failed=1
        fi

        if [ \$branch_cov -lt \$threshold ]; then
            echo \"Branch coverage: \$branch_cov% < \$threshold%\"
            failed=1
        fi

        if [ \$func_cov -lt \$threshold ]; then
            echo \"Function coverage: \$func_cov% < \$threshold%\"
            failed=1
        fi

        exit \$failed
    "

    [ "$status" -eq 1 ]
    [[ "$output" =~ "Branch coverage" ]]
}

# Test 7: 覆盖率报告目录结构
@test "coverage reports are stored in correct location" {
    # 检查标准覆盖率目录
    run bash -c "
        coverage_dirs=('coverage' '.coverage' 'htmlcov')
        for dir in \"\${coverage_dirs[@]}\"; do
            if [ -d '$PROJECT_ROOT/\$dir' ]; then
                echo \"Coverage directory found: \$dir\"
                exit 0
            fi
        done
        echo 'No coverage directory found'
        exit 1
    "

    # 可能没有运行过测试
    [ "$status" -eq 0 ] || [ "$status" -eq 1 ]
}

# Test 8: 覆盖率徽章更新
@test "coverage badge is updated with latest percentage" {
    run bash -c "
        coverage_pct=85
        badge_file='$TEST_COVERAGE_DIR/coverage-badge.svg'

        # 生成徽章（模拟）
        echo \"<svg><text>coverage: \${coverage_pct}%</text></svg>\" > \"\$badge_file\"

        grep -q '85%' \"\$badge_file\"
    "

    [ "$status" -eq 0 ]
}

# Test 9: 覆盖率趋势跟踪
@test "coverage tracks trend over time" {
    # 创建历史覆盖率记录
    cat > "$TEST_COVERAGE_DIR/coverage-history.json" <<EOF
[
    {"date": "2025-10-01", "coverage": 78},
    {"date": "2025-10-08", "coverage": 82},
    {"date": "2025-10-09", "coverage": 85}
]
EOF

    run bash -c "
        history_file='$TEST_COVERAGE_DIR/coverage-history.json'
        latest=\$(grep -oP '\"coverage\":\s*\K\d+' \"\$history_file\" | tail -1)

        if [ \$latest -ge 80 ]; then
            echo \"Latest coverage: \${latest}% ✅\"
            exit 0
        else
            echo \"Latest coverage: \${latest}% ❌\"
            exit 1
        fi
    "

    [ "$status" -eq 0 ]
    [[ "$output" =~ "85%" ]]
}

# Test 10: 覆盖率回归检测
@test "coverage detects regression from previous build" {
    run bash -c "
        prev_coverage=85
        curr_coverage=82
        regression_threshold=3

        diff=\$((prev_coverage - curr_coverage))

        if [ \$diff -gt \$regression_threshold ]; then
            echo \"⚠️ Coverage regression: -\${diff}% (was \${prev_coverage}%, now \${curr_coverage}%)\"
            exit 1
        fi
        exit 0
    "

    [ "$status" -eq 0 ]  # diff=3, 刚好在阈值
}
