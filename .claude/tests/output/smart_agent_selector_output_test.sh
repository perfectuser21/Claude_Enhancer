#!/bin/bash
# Claude Enhancer Smart Agent Selector 输出测试
# 验证 smart_agent_selector.sh 输出格式和内容正确性

set -e

# 测试配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly HOOKS_DIR="$PROJECT_ROOT/hooks"
readonly TEST_RESULTS_DIR="$SCRIPT_DIR/../reports"
readonly AGENT_SELECTOR_SCRIPT="$HOOKS_DIR/smart_agent_selector.sh"

# 创建结果目录
mkdir -p "$TEST_RESULTS_DIR"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# 测试结果统计
declare -i total_tests=0
declare -i passed_tests=0
declare -i failed_tests=0
declare -a test_failures=()

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((passed_tests++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((failed_tests++))
    test_failures+=("$1")
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 测试用例执行函数
run_test() {
    local test_name="$1"
    local test_input="$2"
    local expected_complexity="$3"
    local expected_agent_count="$4"

    ((total_tests++))
    log_info "执行测试: $test_name"

    # 执行脚本并捕获输出
    local stdout_output
    local stderr_output
    local exit_code=0

    stdout_output=$(echo "$test_input" | "$AGENT_SELECTOR_SCRIPT" 2>/dev/null) || exit_code=$?
    stderr_output=$(echo "$test_input" | "$AGENT_SELECTOR_SCRIPT" 2>&1 >/dev/null) || true

    # 验证退出代码
    if [ $exit_code -ne 0 ]; then
        log_error "$test_name: 脚本执行失败，退出代码: $exit_code"
        return 1
    fi

    # 验证stdout输出（原始输入应该不变）
    if [ "$stdout_output" != "$test_input" ]; then
        log_error "$test_name: stdout 输出不匹配原始输入"
        echo "期望: $test_input"
        echo "实际: $stdout_output"
        return 1
    fi

    # 验证stderr输出格式
    if ! echo "$stderr_output" | grep -q "🤖 Claude Enhancer - Agent Selector"; then
        log_error "$test_name: 缺少标准头部信息"
        return 1
    fi

    # 验证复杂度检测
    if ! echo "$stderr_output" | grep -q "🎯 Complexity: $expected_complexity"; then
        log_error "$test_name: 复杂度检测错误，期望: $expected_complexity"
        echo "实际输出: $stderr_output"
        return 1
    fi

    # 验证Agent数量
    if ! echo "$stderr_output" | grep -q "($expected_agent_count agents)"; then
        log_error "$test_name: Agent数量错误，期望: $expected_agent_count"
        echo "实际输出: $stderr_output"
        return 1
    fi

    # 验证推荐Agent列表存在
    if ! echo "$stderr_output" | grep -q "💡 Recommended Agents:"; then
        log_error "$test_name: 缺少推荐Agent列表"
        return 1
    fi

    # 验证日志记录
    if [ -f "/tmp/claude_agent_selection.log" ]; then
        local latest_log=$(tail -1 /tmp/claude_agent_selection.log)
        if ! echo "$latest_log" | grep -q "Complexity: $expected_complexity"; then
            log_warning "$test_name: 日志记录可能不准确"
        fi
    fi

    log_success "$test_name: 所有验证通过"
    return 0
}

# 测试输出格式结构
test_output_structure() {
    local test_input='{"prompt": "implement user authentication", "model": "claude-3-sonnet"}'
    local stderr_output

    stderr_output=$(echo "$test_input" | "$AGENT_SELECTOR_SCRIPT" 2>&1 >/dev/null)

    log_info "测试输出结构格式..."

    # 检查必需的输出元素
    local required_elements=(
        "============================================"
        "🤖 Claude Enhancer - Agent Selector"
        "📋 Task:"
        "🎯 Complexity:"
        "💡 Recommended Agents:"
    )

    local structure_valid=true
    for element in "${required_elements[@]}"; do
        if ! echo "$stderr_output" | grep -qF "$element"; then
            log_error "缺少必需输出元素: $element"
            structure_valid=false
        fi
    done

    if [ "$structure_valid" = true ]; then
        log_success "输出结构格式验证通过"
        ((passed_tests++))
    else
        ((failed_tests++))
        test_failures+=("输出结构格式验证")
    fi

    ((total_tests++))
}

# 测试边界情况
test_edge_cases() {
    log_info "测试边界情况..."

    # 测试空输入
    ((total_tests++))
    local empty_output
    empty_output=$(echo "" | "$AGENT_SELECTOR_SCRIPT" 2>&1)
    if echo "$empty_output" | grep -q "⚠️.*No task description found"; then
        log_success "空输入处理正确"
        ((passed_tests++))
    else
        log_error "空输入处理失败"
        ((failed_tests++))
        test_failures+=("空输入处理")
    fi

    # 测试无效JSON
    ((total_tests++))
    local invalid_json_output
    invalid_json_output=$(echo "invalid json {}" | "$AGENT_SELECTOR_SCRIPT" 2>&1)
    if echo "$invalid_json_output" | grep -q "⚠️.*No task description found"; then
        log_success "无效JSON处理正确"
        ((passed_tests++))
    else
        log_error "无效JSON处理失败"
        ((failed_tests++))
        test_failures+=("无效JSON处理")
    fi

    # 测试非常长的任务描述
    ((total_tests++))
    local long_task="implement a very complex and comprehensive enterprise-grade application with microservices architecture and advanced security features"
    local long_input="{\"prompt\": \"$long_task\"}"
    local long_output
    long_output=$(echo "$long_input" | "$AGENT_SELECTOR_SCRIPT" 2>&1 >/dev/null)
    if echo "$long_output" | grep -qE "📋 Task:.*\.\.\."; then
        log_success "长任务描述截断正确"
        ((passed_tests++))
    else
        log_error "长任务描述处理失败"
        ((failed_tests++))
        test_failures+=("长任务描述处理")
    fi
}

# 测试Agent推荐的合理性
test_agent_recommendations() {
    log_info "测试Agent推荐合理性..."

    # 简单任务应该推荐4个特定Agent
    ((total_tests++))
    local simple_input='{"prompt": "fix small bug in form validation"}'
    local simple_output
    simple_output=$(echo "$simple_input" | "$AGENT_SELECTOR_SCRIPT" 2>&1 >/dev/null)

    local simple_expected_agents=("backend-architect" "test-engineer" "security-auditor" "api-designer")
    local simple_valid=true

    for agent in "${simple_expected_agents[@]}"; do
        if ! echo "$simple_output" | grep -q "$agent"; then
            log_error "简单任务缺少推荐Agent: $agent"
            simple_valid=false
        fi
    done

    if [ "$simple_valid" = true ]; then
        log_success "简单任务Agent推荐正确"
        ((passed_tests++))
    else
        ((failed_tests++))
        test_failures+=("简单任务Agent推荐")
    fi

    # 复杂任务应该推荐8个Agent
    ((total_tests++))
    local complex_input='{"prompt": "design complete microservices architecture with security"}'
    local complex_output
    complex_output=$(echo "$complex_input" | "$AGENT_SELECTOR_SCRIPT" 2>&1 >/dev/null)

    # 统计推荐的Agent数量
    local agent_count
    agent_count=$(echo "$complex_output" | grep -oE "💡 Recommended Agents:.*" | grep -o "," | wc -l)
    agent_count=$((agent_count + 1))  # 逗号数量+1

    if [ "$agent_count" -eq 8 ]; then
        log_success "复杂任务Agent数量正确 (8个)"
        ((passed_tests++))
    else
        log_error "复杂任务Agent数量错误，期望8个，实际${agent_count}个"
        ((failed_tests++))
        test_failures+=("复杂任务Agent数量")
    fi
}

# 测试多种输入格式
test_input_format_flexibility() {
    log_info "测试输入格式灵活性..."

    local test_cases=(
        '{"prompt": "create API"}'
        '{"description": "build frontend"}'
        '{"task": "optimize performance"}'
        '{"request": "fix security issue"}'
        '"implement user authentication system"'  # 直接字符串
    )

    for input in "${test_cases[@]}"; do
        ((total_tests++))
        local output
        output=$(echo "$input" | "$AGENT_SELECTOR_SCRIPT" 2>&1 >/dev/null)

        if echo "$output" | grep -q "🎯 Complexity:"; then
            log_success "输入格式 '$input' 处理正确"
            ((passed_tests++))
        else
            log_error "输入格式 '$input' 处理失败"
            ((failed_tests++))
            test_failures+=("输入格式: $input")
        fi
    done
}

# 测试日志功能
test_logging_functionality() {
    log_info "测试日志功能..."

    # 清空日志文件
    > /tmp/claude_agent_selection.log || true

    ((total_tests++))
    local test_input='{"prompt": "test logging functionality"}'
    echo "$test_input" | "$AGENT_SELECTOR_SCRIPT" >/dev/null 2>&1

    # 检查日志是否记录
    if [ -f "/tmp/claude_agent_selection.log" ] && [ -s "/tmp/claude_agent_selection.log" ]; then
        local log_content
        log_content=$(cat /tmp/claude_agent_selection.log)
        if echo "$log_content" | grep -q "test logging functionality"; then
            log_success "日志记录功能正常"
            ((passed_tests++))
        else
            log_error "日志内容不正确"
            ((failed_tests++))
            test_failures+=("日志内容")
        fi
    else
        log_error "日志文件未创建或为空"
        ((failed_tests++))
        test_failures+=("日志创建")
    fi
}

# 生成详细测试报告
generate_output_test_report() {
    local report_file="$TEST_RESULTS_DIR/smart_agent_selector_output_report.html"

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Smart Agent Selector 输出测试报告</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .summary { background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .pass { color: #28a745; font-weight: bold; }
        .fail { color: #dc3545; font-weight: bold; }
        .test-section { margin: 20px 0; padding: 15px; border-left: 4px solid #007acc; background: #f9f9f9; }
        .failure-list { background: #f8d7da; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .code { background: #f4f4f4; padding: 10px; border-radius: 3px; font-family: monospace; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Smart Agent Selector 输出测试报告</h1>
        <p><strong>测试时间:</strong> $(date)</p>
        <p><strong>测试脚本:</strong> $AGENT_SELECTOR_SCRIPT</p>
        <p><strong>测试目标:</strong> 验证输出格式、内容正确性和边界情况处理</p>
    </div>

    <div class="summary">
        <h2>📊 测试结果总览</h2>
        <table>
            <tr><th>指标</th><th>值</th><th>状态</th></tr>
            <tr><td>总测试数</td><td>$total_tests</td><td>-</td></tr>
            <tr><td>通过测试</td><td>$passed_tests</td><td class="pass">PASS</td></tr>
            <tr><td>失败测试</td><td>$failed_tests</td><td class="$([ $failed_tests -eq 0 ] && echo 'pass' || echo 'fail')">$([ $failed_tests -eq 0 ] && echo 'PASS' || echo 'FAIL')</td></tr>
            <tr><td>成功率</td><td>$(( passed_tests * 100 / total_tests ))%</td><td class="$([ $failed_tests -eq 0 ] && echo 'pass' || echo 'fail')">$([ $failed_tests -eq 0 ] && echo 'EXCELLENT' || echo 'NEEDS IMPROVEMENT')</td></tr>
        </table>
    </div>

    <div class="test-section">
        <h3>🔍 测试覆盖范围</h3>
        <ul>
            <li>✅ 输出结构格式验证</li>
            <li>✅ 复杂度检测准确性</li>
            <li>✅ Agent推荐合理性</li>
            <li>✅ 边界情况处理</li>
            <li>✅ 输入格式灵活性</li>
            <li>✅ 日志功能验证</li>
            <li>✅ 错误处理机制</li>
        </ul>
    </div>
EOF

    if [ $failed_tests -gt 0 ]; then
        cat >> "$report_file" << EOF
    <div class="failure-list">
        <h3>❌ 失败测试详情</h3>
        <ul>
EOF
        for failure in "${test_failures[@]}"; do
            echo "            <li>$failure</li>" >> "$report_file"
        done

        cat >> "$report_file" << EOF
        </ul>
    </div>
EOF
    fi

    cat >> "$report_file" << EOF
    <div class="test-section">
        <h3>🏆 质量评估</h3>
        <p><strong>整体评分:</strong> $(( passed_tests * 100 / total_tests ))/100</p>
        <p><strong>建议:</strong>
EOF

    if [ $failed_tests -eq 0 ]; then
        echo "所有测试通过，输出质量优秀！建议保持当前实现质量。" >> "$report_file"
    else
        echo "存在 $failed_tests 个失败测试，建议重点关注失败项并进行修复。" >> "$report_file"
    fi

    cat >> "$report_file" << EOF
        </p>
    </div>

    <div class="test-section">
        <h3>📋 验收标准检查</h3>
        <table>
            <tr><th>标准</th><th>要求</th><th>实际</th><th>状态</th></tr>
            <tr><td>输出格式</td><td>结构化输出</td><td>$([ $failed_tests -eq 0 ] && echo '符合标准' || echo '部分不符合')</td><td class="$([ $failed_tests -eq 0 ] && echo 'pass' || echo 'fail')">$([ $failed_tests -eq 0 ] && echo 'PASS' || echo 'FAIL')</td></tr>
            <tr><td>错误处理</td><td>优雅处理边界情况</td><td>$([ $failed_tests -eq 0 ] && echo '处理完善' || echo '需要改进')</td><td class="$([ $failed_tests -eq 0 ] && echo 'pass' || echo 'fail')">$([ $failed_tests -eq 0 ] && echo 'PASS' || echo 'FAIL')</td></tr>
            <tr><td>成功率</td><td>>95%</td><td>$(( passed_tests * 100 / total_tests ))%</td><td class="$([ $(( passed_tests * 100 / total_tests )) -ge 95 ] && echo 'pass' || echo 'fail')">$([ $(( passed_tests * 100 / total_tests )) -ge 95 ] && echo 'PASS' || echo 'FAIL')</td></tr>
        </table>
    </div>

    <p><em>报告生成时间: $(date)</em></p>
</body>
</html>
EOF

    log_success "详细测试报告已生成: $report_file"
}

# 主测试流程
main() {
    echo "🧪 Smart Agent Selector 输出测试开始"
    echo "========================================"
    echo

    # 检查脚本存在性
    if [ ! -f "$AGENT_SELECTOR_SCRIPT" ]; then
        log_error "找不到测试脚本: $AGENT_SELECTOR_SCRIPT"
        exit 1
    fi

    if [ ! -x "$AGENT_SELECTOR_SCRIPT" ]; then
        log_error "脚本不可执行: $AGENT_SELECTOR_SCRIPT"
        exit 1
    fi

    # 执行基础功能测试
    run_test "简单任务" '{"prompt": "fix typo in login form"}' "simple" "4"
    run_test "标准任务" '{"prompt": "implement user authentication system"}' "standard" "6"
    run_test "复杂任务" '{"prompt": "design microservices architecture"}' "complex" "8"

    # 执行专项测试
    test_output_structure
    test_edge_cases
    test_agent_recommendations
    test_input_format_flexibility
    test_logging_functionality

    # 生成报告
    generate_output_test_report

    # 输出测试总结
    echo
    echo "========================================"
    echo "🏁 测试完成!"
    echo "   总测试数: $total_tests"
    echo "   通过: $passed_tests"
    echo "   失败: $failed_tests"
    echo "   成功率: $(( passed_tests * 100 / total_tests ))%"

    if [ $failed_tests -eq 0 ]; then
        log_success "🎉 所有输出测试通过！"
        exit 0
    else
        log_error "❌ 有 $failed_tests 个测试失败"
        echo "📋 失败测试:"
        for failure in "${test_failures[@]}"; do
            echo "   • $failure"
        done
        exit 1
    fi
}

# 执行测试
main "$@"