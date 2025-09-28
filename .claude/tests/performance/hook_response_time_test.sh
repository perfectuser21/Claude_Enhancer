#!/bin/bash
# Claude Enhancer Hook响应时间性能测试
# 验证 quality_gate.sh 和 smart_agent_selector.sh 响应时间 < 100ms

set -e

# 测试配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
readonly HOOKS_DIR="$PROJECT_ROOT/hooks"
readonly TEST_RESULTS_DIR="$SCRIPT_DIR/../reports"
readonly MAX_RESPONSE_TIME_MS=100
readonly TEST_ITERATIONS=50
readonly WARMUP_ITERATIONS=5

# 创建结果目录
mkdir -p "$TEST_RESULTS_DIR"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# 测试结果统计
declare -A test_results=()
declare -A performance_stats=()

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# 性能测试函数
measure_hook_performance() {
    local hook_script="$1"
    local test_input="$2"
    local hook_name="$3"

    log_info "测试 $hook_name 性能..."

    # 预热执行
    log_info "执行 $WARMUP_ITERATIONS 次预热..."
    for ((i=1; i<=WARMUP_ITERATIONS; i++)); do
        echo "$test_input" | "$hook_script" >/dev/null 2>&1 || true
    done

    # 正式测试
    local times=()
    local success_count=0
    local error_count=0

    for ((i=1; i<=TEST_ITERATIONS; i++)); do
        local start_time=$(date +%s%N)

        # 执行Hook
        local output
        local exit_code=0
        output=$(echo "$test_input" | "$hook_script" 2>&1) || exit_code=$?

        local end_time=$(date +%s%N)
        local duration_ms=$(( (end_time - start_time) / 1000000 ))

        times+=($duration_ms)

        if [ $exit_code -eq 0 ]; then
            ((success_count++))
        else
            ((error_count++))
            log_warning "迭代 $i 失败: exit_code=$exit_code"
        fi

        # 实时进度
        if (( i % 10 == 0 )); then
            log_info "已完成 $i/$TEST_ITERATIONS 次测试"
        fi
    done

    # 计算统计信息
    local total_time=0
    local min_time=${times[0]}
    local max_time=${times[0]}

    for time in "${times[@]}"; do
        total_time=$((total_time + time))
        if [ $time -lt $min_time ]; then
            min_time=$time
        fi
        if [ $time -gt $max_time ]; then
            max_time=$time
        fi
    done

    local avg_time=$((total_time / TEST_ITERATIONS))
    local success_rate=$((success_count * 100 / TEST_ITERATIONS))

    # 计算95百分位
    local sorted_times=($(printf '%s\n' "${times[@]}" | sort -n))
    local p95_index=$(( TEST_ITERATIONS * 95 / 100 ))
    local p95_time=${sorted_times[$p95_index]}

    # 存储结果
    performance_stats["${hook_name}_avg"]=$avg_time
    performance_stats["${hook_name}_min"]=$min_time
    performance_stats["${hook_name}_max"]=$max_time
    performance_stats["${hook_name}_p95"]=$p95_time
    performance_stats["${hook_name}_success_rate"]=$success_rate

    # 判断是否通过
    local passed=true
    if [ $avg_time -gt $MAX_RESPONSE_TIME_MS ]; then
        passed=false
        test_results["${hook_name}_avg_time"]="FAIL"
    else
        test_results["${hook_name}_avg_time"]="PASS"
    fi

    if [ $p95_time -gt $((MAX_RESPONSE_TIME_MS * 2)) ]; then
        passed=false
        test_results["${hook_name}_p95_time"]="FAIL"
    else
        test_results["${hook_name}_p95_time"]="PASS"
    fi

    if [ $success_rate -lt 95 ]; then
        passed=false
        test_results["${hook_name}_success_rate"]="FAIL"
    else
        test_results["${hook_name}_success_rate"]="PASS"
    fi

    # 输出结果
    if [ "$passed" = true ]; then
        log_success "$hook_name 性能测试通过"
    else
        log_error "$hook_name 性能测试失败"
    fi

    echo "  平均时间: ${avg_time}ms (要求: <${MAX_RESPONSE_TIME_MS}ms)"
    echo "  最小时间: ${min_time}ms"
    echo "  最大时间: ${max_time}ms"
    echo "  95百分位: ${p95_time}ms"
    echo "  成功率: ${success_rate}%"
    echo

    return $([ "$passed" = true ] && echo 0 || echo 1)
}

# 准备测试数据
prepare_test_data() {
    # quality_gate.sh 测试输入
    cat > /tmp/quality_gate_test_input.json << 'EOF'
{
    "prompt": "实现用户认证系统，包括JWT令牌生成、验证和刷新功能",
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 4000
}
EOF

    # smart_agent_selector.sh 测试输入
    cat > /tmp/agent_selector_test_input.json << 'EOF'
{
    "description": "开发完整的电商支付系统，包括支付网关集成、订单管理和安全验证",
    "prompt": "创建一个安全可靠的支付处理系统",
    "complexity": "complex"
}
EOF
}

# 生成性能报告
generate_performance_report() {
    local report_file="$TEST_RESULTS_DIR/hook_performance_report.html"

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Hook 性能测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007acc; background: #f9f9f9; }
        .pass { border-left-color: #28a745; }
        .fail { border-left-color: #dc3545; }
        .stats-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .stats-table th, .stats-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .stats-table th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Claude Enhancer Hook 性能测试报告</h1>
        <p>测试时间: $(date)</p>
        <p>测试标准: 响应时间 < ${MAX_RESPONSE_TIME_MS}ms</p>
        <p>测试迭代: ${TEST_ITERATIONS} 次</p>
    </div>

    <h2>测试结果总览</h2>
EOF

    # 添加测试结果表格
    echo '<table class="stats-table">' >> "$report_file"
    echo '<tr><th>Hook</th><th>指标</th><th>值</th><th>状态</th></tr>' >> "$report_file"

    for hook in "quality_gate" "smart_agent_selector"; do
        echo "<tr><td rowspan=\"4\">$hook</td><td>平均时间</td><td>${performance_stats[${hook}_avg]}ms</td><td class=\"${test_results[${hook}_avg_time],,}\">${test_results[${hook}_avg_time]}</td></tr>" >> "$report_file"
        echo "<tr><td>95百分位</td><td>${performance_stats[${hook}_p95]}ms</td><td class=\"${test_results[${hook}_p95_time],,}\">${test_results[${hook}_p95_time]}</td></tr>" >> "$report_file"
        echo "<tr><td>最大时间</td><td>${performance_stats[${hook}_max]}ms</td><td>-</td></tr>" >> "$report_file"
        echo "<tr><td>成功率</td><td>${performance_stats[${hook}_success_rate]}%</td><td class=\"${test_results[${hook}_success_rate],,}\">${test_results[${hook}_success_rate]}</td></tr>" >> "$report_file"
    done

    echo '</table>' >> "$report_file"
    echo '</body></html>' >> "$report_file"

    log_success "性能报告已生成: $report_file"
}

# 主测试流程
main() {
    echo "🚀 Claude Enhancer Hook 性能测试开始"
    echo "========================================"
    echo

    # 检查必要文件
    local quality_gate_script="$HOOKS_DIR/quality_gate.sh"
    local agent_selector_script="$HOOKS_DIR/smart_agent_selector.sh"

    if [ ! -f "$quality_gate_script" ]; then
        log_error "找不到 quality_gate.sh: $quality_gate_script"
        exit 1
    fi

    if [ ! -f "$agent_selector_script" ]; then
        log_error "找不到 smart_agent_selector.sh: $agent_selector_script"
        exit 1
    fi

    # 准备测试数据
    prepare_test_data

    # 执行性能测试
    local overall_passed=true

    # 测试 quality_gate.sh
    if ! measure_hook_performance "$quality_gate_script" "$(cat /tmp/quality_gate_test_input.json)" "quality_gate"; then
        overall_passed=false
    fi

    # 测试 smart_agent_selector.sh
    if ! measure_hook_performance "$agent_selector_script" "$(cat /tmp/agent_selector_test_input.json)" "smart_agent_selector"; then
        overall_passed=false
    fi

    # 生成报告
    generate_performance_report

    # 清理临时文件
    rm -f /tmp/quality_gate_test_input.json /tmp/agent_selector_test_input.json

    # 输出总结
    echo "========================================"
    if [ "$overall_passed" = true ]; then
        log_success "🎉 所有Hook性能测试通过！"
        echo
        echo "✅ quality_gate.sh: 平均 ${performance_stats[quality_gate_avg]}ms"
        echo "✅ smart_agent_selector.sh: 平均 ${performance_stats[smart_agent_selector_avg]}ms"
        exit 0
    else
        log_error "❌ 部分Hook性能测试失败"
        echo
        echo "📊 详细结果请查看报告: $TEST_RESULTS_DIR/hook_performance_report.html"
        exit 1
    fi
}

# 执行测试
main "$@"