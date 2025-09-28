#!/bin/bash
# Claude Enhancer 5.2 - 主测试运行器
# 统一执行所有测试：性能、单元、输出、集成测试

set -e

# 测试配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly TEST_RESULTS_DIR="$SCRIPT_DIR/reports"

# 创建结果目录
mkdir -p "$TEST_RESULTS_DIR"

# 颜色输出
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# 测试统计
declare -A test_suite_results=()
declare -A test_suite_times=()
declare -i total_test_suites=0
declare -i passed_test_suites=0

# 日志函数
log_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_suite() {
    echo -e "${PURPLE}[SUITE]${NC} $1"
}

# 执行测试套件
run_test_suite() {
    local suite_name="$1"
    local test_script="$2"
    local description="$3"

    ((total_test_suites++))
    log_suite "执行测试套件: $suite_name"
    log_info "$description"

    # 检查测试脚本存在性
    if [ ! -f "$test_script" ]; then
        log_error "测试脚本不存在: $test_script"
        test_suite_results["$suite_name"]="SKIP"
        test_suite_times["$suite_name"]="0"
        return 1
    fi

    # 使测试脚本可执行
    chmod +x "$test_script" 2>/dev/null || true

    # 执行测试
    local start_time=$(date +%s)
    local exit_code=0

    if "$test_script" > "$TEST_RESULTS_DIR/${suite_name}_output.log" 2>&1; then
        exit_code=0
    else
        exit_code=$?
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # 记录结果
    test_suite_times["$suite_name"]=$duration

    if [ $exit_code -eq 0 ]; then
        log_success "$suite_name 测试通过 (${duration}s)"
        test_suite_results["$suite_name"]="PASS"
        ((passed_test_suites++))
    else
        log_error "$suite_name 测试失败 (${duration}s)"
        test_suite_results["$suite_name"]="FAIL"
        echo "   详细日志: $TEST_RESULTS_DIR/${suite_name}_output.log"
    fi

    echo
    return $exit_code
}

# Python环境检查
check_python_environment() {
    log_info "检查Python测试环境..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        return 1
    fi

    # 检查必要的Python模块
    local required_modules=("unittest" "json" "time" "threading")
    for module in "${required_modules[@]}"; do
        if ! python3 -c "import $module" 2>/dev/null; then
            log_error "Python模块 '$module' 不可用"
            return 1
        fi
    done

    # 检查lazy_orchestrator可导入性
    if ! python3 -c "import sys; sys.path.insert(0, '$PROJECT_ROOT/core'); from lazy_orchestrator import LazyAgentOrchestrator" 2>/dev/null; then
        log_warning "lazy_orchestrator.py 导入检查失败，相关测试可能跳过"
    fi

    log_success "Python环境检查通过"
    return 0
}

# 生成测试执行总结报告
generate_master_report() {
    local report_file="$TEST_RESULTS_DIR/master_test_report.html"

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Claude Enhancer 5.2 - 完整测试报告</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .summary-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .summary-card h3 {
            font-size: 1.2em;
            margin-bottom: 15px;
            opacity: 0.9;
        }
        .summary-card .number {
            font-size: 3em;
            font-weight: bold;
            display: block;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .summary-card.success { background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); }
        .summary-card.warning { background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; }
        .summary-card.error { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
        .test-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .test-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            transition: transform 0.3s ease;
        }
        .test-card:hover { transform: translateY(-5px); }
        .test-card-header {
            padding: 20px;
            font-weight: bold;
            font-size: 1.1em;
        }
        .test-card-header.pass { background: #d4edda; color: #155724; }
        .test-card-header.fail { background: #f8d7da; color: #721c24; }
        .test-card-header.skip { background: #fff3cd; color: #856404; }
        .test-card-body {
            padding: 20px;
            background: white;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #84fab0 0%, #8fd3f4 100%);
            transition: width 0.3s ease;
        }
        .timestamp {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-style: italic;
        }
        .badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin: 5px;
        }
        .badge.pass { background: #d4edda; color: #155724; }
        .badge.fail { background: #f8d7da; color: #721c24; }
        .badge.skip { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Claude Enhancer 5.2</h1>
            <p>完整测试执行报告 - $(date)</p>
        </div>

        <div class="card">
            <div class="summary">
                <div class="summary-card $([ $passed_test_suites -eq $total_test_suites ] && echo 'success' || echo 'warning')">
                    <h3>总体通过率</h3>
                    <span class="number">$(( passed_test_suites * 100 / total_test_suites ))%</span>
                </div>
                <div class="summary-card success">
                    <h3>通过测试套件</h3>
                    <span class="number">$passed_test_suites</span>
                </div>
                <div class="summary-card $([ $((total_test_suites - passed_test_suites)) -eq 0 ] && echo 'success' || echo 'error')">
                    <h3>失败测试套件</h3>
                    <span class="number">$((total_test_suites - passed_test_suites))</span>
                </div>
                <div class="summary-card warning">
                    <h3>总执行时间</h3>
                    <span class="number">$(($(printf '%s\n' "${test_suite_times[@]}" | paste -sd+ | bc)))s</span>
                </div>
            </div>

            <div class="progress-bar">
                <div class="progress-fill" style="width: $(( passed_test_suites * 100 / total_test_suites ))%"></div>
            </div>
        </div>

        <div class="card">
            <h2>🎯 测试套件执行结果</h2>
            <div class="test-grid">
EOF

    # 添加测试套件卡片
    for suite in "${!test_suite_results[@]}"; do
        local status="${test_suite_results[$suite]}"
        local time="${test_suite_times[$suite]}"
        local status_class=$(echo "$status" | tr '[:upper:]' '[:lower:]')

        cat >> "$report_file" << EOF
                <div class="test-card">
                    <div class="test-card-header $status_class">
                        $suite
                        <span class="badge $status_class">$status</span>
                    </div>
                    <div class="test-card-body">
                        <p><strong>执行时间:</strong> ${time}秒</p>
                        <p><strong>日志文件:</strong> ${suite}_output.log</p>
EOF

        # 添加套件描述
        case "$suite" in
            "performance")
                echo "                        <p><strong>测试内容:</strong> Hook响应时间 < 100ms验证</p>" >> "$report_file"
                ;;
            "unit")
                echo "                        <p><strong>测试内容:</strong> select_agents_intelligent方法单元测试</p>" >> "$report_file"
                ;;
            "output")
                echo "                        <p><strong>测试内容:</strong> smart_agent_selector.sh输出格式验证</p>" >> "$report_file"
                ;;
            "integration")
                echo "                        <p><strong>测试内容:</strong> 端到端工作流集成测试</p>" >> "$report_file"
                ;;
        esac

        echo "                    </div>" >> "$report_file"
        echo "                </div>" >> "$report_file"
    done

    cat >> "$report_file" << EOF
            </div>
        </div>

        <div class="card">
            <h2>📋 验收标准达成情况</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding: 15px; border: 1px solid #ddd;">验收标准</th>
                        <th style="padding: 15px; border: 1px solid #ddd;">要求</th>
                        <th style="padding: 15px; border: 1px solid #ddd;">状态</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 15px; border: 1px solid #ddd;">质量门禁性能</td>
                        <td style="padding: 15px; border: 1px solid #ddd;">响应时间 < 100ms</td>
                        <td style="padding: 15px; border: 1px solid #ddd;">
                            <span class="badge $([ "${test_suite_results[performance]}" = "PASS" ] && echo 'pass' || echo 'fail')">${test_suite_results[performance]:-SKIP}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; border: 1px solid #ddd;">核心方法逻辑</td>
                        <td style="padding: 15px; border: 1px solid #ddd;">单元测试覆盖率 > 90%</td>
                        <td style="padding: 15px; border: 1px solid #ddd;">
                            <span class="badge $([ "${test_suite_results[unit]}" = "PASS" ] && echo 'pass' || echo 'fail')">${test_suite_results[unit]:-SKIP}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; border: 1px solid #ddd;">输出格式正确性</td>
                        <td style="padding: 15px; border: 1px solid #ddd;">格式符合标准</td>
                        <td style="padding: 15px; border: 1px solid #ddd;">
                            <span class="badge $([ "${test_suite_results[output]}" = "PASS" ] && echo 'pass' || echo 'fail')">${test_suite_results[output]:-SKIP}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 15px; border: 1px solid #ddd;">工作流集成</td>
                        <td style="padding: 15px; border: 1px solid #ddd;">端到端执行无错误</td>
                        <td style="padding: 15px; border: 1px solid #ddd;">
                            <span class="badge $([ "${test_suite_results[integration]}" = "PASS" ] && echo 'pass' || echo 'fail')">${test_suite_results[integration]:-SKIP}</span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>🚀 下一步建议</h2>
EOF

    if [ $passed_test_suites -eq $total_test_suites ]; then
        cat >> "$report_file" << EOF
            <div style="background: #d4edda; padding: 20px; border-radius: 10px; color: #155724;">
                <h3>🎉 恭喜！所有测试通过</h3>
                <p>Claude Enhancer 5.2的三个核心修复已通过全面验证：</p>
                <ul style="margin: 15px 0 0 20px;">
                    <li>✅ quality_gate.sh 性能达标（响应时间 < 100ms）</li>
                    <li>✅ select_agents_intelligent 方法逻辑正确</li>
                    <li>✅ smart_agent_selector.sh 输出格式规范</li>
                    <li>✅ 整体工作流运行稳定</li>
                </ul>
                <p><strong>建议：</strong>系统已准备好投入生产使用！</p>
            </div>
EOF
    else
        cat >> "$report_file" << EOF
            <div style="background: #f8d7da; padding: 20px; border-radius: 10px; color: #721c24;">
                <h3>⚠️ 需要修复的问题</h3>
                <p>以下测试套件需要关注：</p>
                <ul style="margin: 15px 0 0 20px;">
EOF
        for suite in "${!test_suite_results[@]}"; do
            if [ "${test_suite_results[$suite]}" != "PASS" ]; then
                echo "                    <li>❌ $suite 测试套件：${test_suite_results[$suite]}</li>" >> "$report_file"
            fi
        done

        cat >> "$report_file" << EOF
                </ul>
                <p><strong>建议：</strong>修复失败测试后再次执行完整测试。</p>
            </div>
EOF
    fi

    cat >> "$report_file" << EOF
        </div>

        <div class="timestamp">
            <p>报告生成时间: $(date) | Claude Enhancer v5.2 测试框架</p>
        </div>
    </div>
</body>
</html>
EOF

    log_success "主测试报告已生成: $report_file"
}

# 显示使用帮助
show_help() {
    cat << EOF
Claude Enhancer 5.2 - 主测试运行器

用法: $0 [选项]

选项:
  --performance-only    只运行性能测试
  --unit-only          只运行单元测试
  --output-only        只运行输出测试
  --integration-only   只运行集成测试
  --quick              快速测试（跳过耗时较长的测试）
  --help              显示此帮助信息

示例:
  $0                   # 运行所有测试
  $0 --performance-only # 只运行性能测试
  $0 --quick           # 快速测试模式

测试覆盖:
  🔧 性能测试: Hook响应时间验证
  🧪 单元测试: 核心方法逻辑验证
  📝 输出测试: 格式和内容验证
  🔄 集成测试: 端到端工作流验证
EOF
}

# 主执行流程
main() {
    # 解析命令行参数
    local performance_only=false
    local unit_only=false
    local output_only=false
    local integration_only=false
    local quick_mode=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --performance-only)
                performance_only=true
                shift
                ;;
            --unit-only)
                unit_only=true
                shift
                ;;
            --output-only)
                output_only=true
                shift
                ;;
            --integration-only)
                integration_only=true
                shift
                ;;
            --quick)
                quick_mode=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 开始测试
    log_header "Claude Enhancer 5.2 - 完整测试执行"
    echo
    log_info "项目根目录: $PROJECT_ROOT"
    log_info "测试结果目录: $TEST_RESULTS_DIR"
    echo

    # 环境检查
    check_python_environment
    echo

    # 清理旧的测试结果
    rm -f "$TEST_RESULTS_DIR"/*.log "$TEST_RESULTS_DIR"/*.html 2>/dev/null || true

    # 执行测试套件
    if [ "$performance_only" = true ]; then
        run_test_suite "performance" "$SCRIPT_DIR/performance/hook_response_time_test.sh" "Hook响应时间性能测试"
    elif [ "$unit_only" = true ]; then
        run_test_suite "unit" "$SCRIPT_DIR/unit/test_lazy_orchestrator.py" "select_agents_intelligent方法单元测试"
    elif [ "$output_only" = true ]; then
        run_test_suite "output" "$SCRIPT_DIR/output/smart_agent_selector_output_test.sh" "smart_agent_selector.sh输出验证测试"
    elif [ "$integration_only" = true ]; then
        run_test_suite "integration" "$SCRIPT_DIR/integration/workflow_integration_test.sh" "端到端工作流集成测试"
    else
        # 执行所有测试
        log_info "开始执行完整测试套件..."
        echo

        # 1. 性能测试
        run_test_suite "performance" "$SCRIPT_DIR/performance/hook_response_time_test.sh" "Hook响应时间性能测试 - 验证响应时间 < 100ms"

        # 2. 单元测试
        run_test_suite "unit" "$SCRIPT_DIR/unit/test_lazy_orchestrator.py" "LazyOrchestrator单元测试 - 验证select_agents_intelligent方法逻辑"

        # 3. 输出测试
        run_test_suite "output" "$SCRIPT_DIR/output/smart_agent_selector_output_test.sh" "SmartAgentSelector输出测试 - 验证输出格式和内容正确性"

        # 4. 集成测试（如果不是快速模式）
        if [ "$quick_mode" = false ]; then
            run_test_suite "integration" "$SCRIPT_DIR/integration/workflow_integration_test.sh" "工作流集成测试 - 验证端到端协作"
        else
            log_warning "快速模式：跳过集成测试"
        fi
    fi

    # 生成总体报告
    generate_master_report

    # 输出最终结果
    echo
    log_header "测试执行完成"

    echo
    echo "📊 测试结果总览:"
    echo "   总测试套件: $total_test_suites"
    echo "   通过套件: $passed_test_suites"
    echo "   失败套件: $((total_test_suites - passed_test_suites))"
    echo "   成功率: $(( passed_test_suites * 100 / total_test_suites ))%"
    echo
    echo "📋 详细报告: $TEST_RESULTS_DIR/master_test_report.html"

    # 列出测试套件状态
    echo
    echo "🔍 各测试套件状态:"
    for suite in "${!test_suite_results[@]}"; do
        local status="${test_suite_results[$suite]}"
        local time="${test_suite_times[$suite]}"
        case "$status" in
            "PASS")
                log_success "$suite: $status (${time}s)"
                ;;
            "FAIL")
                log_error "$suite: $status (${time}s)"
                ;;
            *)
                log_warning "$suite: $status (${time}s)"
                ;;
        esac
    done

    echo
    if [ $passed_test_suites -eq $total_test_suites ]; then
        log_success "🎉 所有测试通过！Claude Enhancer 5.2 准备就绪"
        exit 0
    else
        log_error "❌ 存在失败测试，请检查日志并修复"
        exit 1
    fi
}

# 执行主流程
main "$@"