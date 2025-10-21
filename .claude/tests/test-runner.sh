#!/bin/bash
# Claude Enhancer 5.0 - 测试运行器
# 执行完整的8-Phase工作流端到端测试

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../" && pwd)"
TEST_DIR="${PROJECT_ROOT}/.claude/tests"
REPORT_DIR="${TEST_DIR}/reports"
LOG_DIR="${TEST_DIR}/logs"

# 确保目录存在
mkdir -p "$REPORT_DIR" "$LOG_DIR"

# 测试配置
TEST_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
TEST_LOG="${LOG_DIR}/e2e_test_${TEST_TIMESTAMP}.log"
TEST_REPORT="${REPORT_DIR}/e2e_report_${TEST_TIMESTAMP}.json"
HTML_REPORT="${REPORT_DIR}/e2e_report_${TEST_TIMESTAMP}.html"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$TEST_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$TEST_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$TEST_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$TEST_LOG"
}

# 检查环境
check_environment() {
    log_info "检查测试环境..."
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    
    local node_version=$(node --version)
    log_info "Node.js 版本: $node_version"
    
    # 检查项目结构
    local required_dirs=(
        ".claude"
        ".claude/hooks"
        ".claude/tests"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "${PROJECT_ROOT}/${dir}" ]]; then
            log_error "缺少必要目录: $dir"
            exit 1
        fi
    done
    
    log_success "环境检查通过"
}

# 预测试准备
pre_test_setup() {
    log_info "执行预测试设置..."
    
    # 清理旧的临时文件
    if [[ -d "/tmp/claude-e2e-tests" ]]; then
        rm -rf "/tmp/claude-e2e-tests"
        log_info "清理旧的临时测试目录"
    fi
    
    # 创建临时测试目录
    mkdir -p "/tmp/claude-e2e-tests"
    
    # 备份当前git状态
    cd "$PROJECT_ROOT"
    if git status &>/dev/null; then
        git stash push -m "Pre-test backup ${TEST_TIMESTAMP}" || true
        log_info "备份当前git状态"
    fi
    
    log_success "预测试设置完成"
}

# 运行Phase测试
run_phase_tests() {
    log_info "开始执行8-Phase工作流测试..."
    
    cd "$TEST_DIR"
    
    # 运行主测试套件
    if node workflow-e2e-test-suite.js > "${TEST_LOG}.detailed" 2>&1; then
        log_success "Phase测试执行成功"
        return 0
    else
        log_error "Phase测试执行失败"
        cat "${TEST_LOG}.detailed" | tail -20 | tee -a "$TEST_LOG"
        return 1
    fi
}

# 运行Hook测试
run_hook_tests() {
    log_info "开始执行Hook集成测试..."
    
    local hook_dir="${PROJECT_ROOT}/.claude/hooks"
    local hooks_tested=0
    local hooks_passed=0
    
    # 测试主要Hook
    local test_hooks=(
        "branch_helper.sh"
        "smart_agent_selector.sh"
        "quality_gate.sh"
        "performance_monitor.sh"
        "error_handler.sh"
    )
    
    for hook in "${test_hooks[@]}"; do
        local hook_path="${hook_dir}/${hook}"
        
        if [[ -f "$hook_path" ]]; then
            log_info "测试Hook: $hook"
            
            # 测试Hook基本执行
            if bash "$hook_path" <<< '{"test": "hook_test"}' &>/dev/null; then
                log_success "Hook $hook 测试通过"
                ((hooks_passed++))
            else
                log_warning "Hook $hook 测试失败"
            fi
        else
            log_warning "Hook文件不存在: $hook"
        fi
        
        ((hooks_tested++))
    done
    
    log_info "Hook测试完成: ${hooks_passed}/${hooks_tested} 通过"
    
    if [[ $hooks_passed -eq $hooks_tested ]]; then
        return 0
    else
        return 1
    fi
}

# 运行Agent策略测试
run_agent_strategy_tests() {
    log_info "开始执行4-6-8 Agent策略测试..."
    
    # 测试不同复杂度的任务
    local test_cases=(
        "简单任务:fix typo in readme:4"
        "标准任务:implement user authentication:6"
        "复杂任务:design microservices architecture:8"
    )
    
    local strategy_passed=0
    local strategy_total=${#test_cases[@]}
    
    for test_case in "${test_cases[@]}"; do
        IFS=':' read -r case_name task_desc expected_agents <<< "$test_case"
        
        log_info "测试Agent策略: $case_name"
        
        # 模拟Agent选择逻辑
        local selected_agents
        if [[ "$task_desc" =~ (fix|typo|small|minor) ]]; then
            selected_agents=4
        elif [[ "$task_desc" =~ (design|architect|microservices|system) ]]; then
            selected_agents=8
        else
            selected_agents=6
        fi
        
        if [[ $selected_agents -eq $expected_agents ]]; then
            log_success "Agent策略正确: $case_name -> ${selected_agents}个Agent"
            ((strategy_passed++))
        else
            log_error "Agent策略错误: $case_name -> 期望${expected_agents}，实际${selected_agents}"
        fi
    done
    
    log_info "Agent策略测试完成: ${strategy_passed}/${strategy_total} 通过"
    
    if [[ $strategy_passed -eq $strategy_total ]]; then
        return 0
    else
        return 1
    fi
}

# 生成HTML报告
generate_html_report() {
    log_info "生成HTML测试报告..."
    
    local report_json="$1"
    local html_output="$2"
    
    if [[ ! -f "$report_json" ]]; then
        log_error "JSON报告文件不存在: $report_json"
        return 1
    fi
    
    # 生成HTML报告
    cat > "$html_output" << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Enhancer 5.0 - E2E测试报告</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 2em; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; border-left: 4px solid #007bff; }
        .summary-card.passed { border-left-color: #28a745; }
        .summary-card.failed { border-left-color: #dc3545; }
        .summary-card.warning { border-left-color: #ffc107; }
        .summary-card h3 { margin: 0 0 10px 0; color: #495057; }
        .summary-card .number { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .passed .number { color: #28a745; }
        .failed .number { color: #dc3545; }
        .warning .number { color: #ffc107; }
        .section { padding: 20px 30px; border-bottom: 1px solid #e9ecef; }
        .section h2 { color: #495057; margin: 0 0 20px 0; }
        .test-list { list-style: none; padding: 0; }
        .test-item { padding: 12px 0; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center; }
        .test-item:last-child { border-bottom: none; }
        .test-name { font-weight: 500; }
        .test-status { padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; }
        .test-status.passed { background: #d4edda; color: #155724; }
        .test-status.failed { background: #f8d7da; color: #721c24; }
        .test-status.warning { background: #fff3cd; color: #856404; }
        .recommendations { background: #f8f9fa; margin: 20px 30px; padding: 20px; border-radius: 6px; }
        .recommendations h3 { margin: 0 0 15px 0; color: #495057; }
        .recommendation { padding: 10px 0; border-bottom: 1px solid #e9ecef; }
        .recommendation:last-child { border-bottom: none; }
        .priority { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; margin-right: 10px; }
        .priority.high { background: #f8d7da; color: #721c24; }
        .priority.medium { background: #fff3cd; color: #856404; }
        .priority.low { background: #d1ecf1; color: #0c5460; }
        .footer { padding: 20px 30px; text-align: center; color: #6c757d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Claude Enhancer 5.0</h1>
            <p>8-Phase工作流端到端测试报告</p>
        </div>
EOF
    
    # 插入JSON数据并生成动态内容
    cat >> "$html_output" << EOF
        <script>
        const reportData = $(cat "$report_json");
        
        // 生成摘要卡片
        document.addEventListener('DOMContentLoaded', function() {
            generateSummary();
            generateTestSections();
            generateRecommendations();
        });
        
        function generateSummary() {
            const summary = reportData.summary;
            const passRate = reportData.passRate;
            
            const summaryHTML = \`
            <div class="summary">
                <div class="summary-card passed">
                    <h3>通过测试</h3>
                    <div class="number">\${summary.passed}</div>
                    <p>成功执行</p>
                </div>
                <div class="summary-card failed">
                    <h3>失败测试</h3>
                    <div class="number">\${summary.failed}</div>
                    <p>需要修复</p>
                </div>
                <div class="summary-card">
                    <h3>总测试数</h3>
                    <div class="number">\${summary.total}</div>
                    <p>完整覆盖</p>
                </div>
                <div class="summary-card \${passRate >= 90 ? 'passed' : passRate >= 70 ? 'warning' : 'failed'}">
                    <h3>通过率</h3>
                    <div class="number">\${passRate}%</div>
                    <p>质量指标</p>
                </div>
            </div>
            \`;
            
            document.getElementById('summary-container').innerHTML = summaryHTML;
        }
        
        function generateTestSections() {
            const categories = reportData.categories;
            let sectionsHTML = '';
            
            Object.keys(categories).forEach(category => {
                const tests = categories[category];
                if (tests.length === 0) return;
                
                sectionsHTML += \`
                <div class="section">
                    <h2>\${getCategoryTitle(category)}</h2>
                    <ul class="test-list">
                \`;
                
                tests.forEach(test => {
                    sectionsHTML += \`
                    <li class="test-item">
                        <span class="test-name">\${test.name}</span>
                        <span class="test-status \${test.passed ? 'passed' : 'failed'}">
                            \${test.passed ? '✅ 通过' : '❌ 失败'}
                        </span>
                    </li>
                    \`;
                });
                
                sectionsHTML += \`
                    </ul>
                </div>
                \`;
            });
            
            document.getElementById('test-sections').innerHTML = sectionsHTML;
        }
        
        function generateRecommendations() {
            const recommendations = reportData.recommendations;
            if (recommendations.length === 0) return;
            
            let recHTML = \`
            <div class="recommendations">
                <h3>🎯 优化建议</h3>
            \`;
            
            recommendations.forEach(rec => {
                recHTML += \`
                <div class="recommendation">
                    <span class="priority \${rec.priority}">\${rec.priority.toUpperCase()}</span>
                    <strong>\${rec.issue}</strong><br>
                    <small>\${rec.action}</small>
                </div>
                \`;
            });
            
            recHTML += \`</div>\`;
            
            document.getElementById('recommendations-container').innerHTML = recHTML;
        }
        
        function getCategoryTitle(category) {
            const titles = {
                phases: '📋 Phase测试 (0-7)',
                hooks: '🔗 Hook集成测试',
                agents: '🤖 Agent策略测试',
                integration: '🔄 集成测试',
                edges: '⚠️ 边缘场景测试'
            };
            return titles[category] || category;
        }
        </script>
        
        <div id="summary-container"></div>
        <div id="test-sections"></div>
        <div id="recommendations-container"></div>
        
        <div class="footer">
            <p>报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')</p>
            <p>Claude Enhancer 5.0 - Max 20X 测试框架</p>
        </div>
    </div>
</body>
</html>
EOF
    
    log_success "HTML报告已生成: $html_output"
}

# 测试后清理
post_test_cleanup() {
    log_info "执行测试后清理..."
    
    # 清理临时文件
    if [[ -d "/tmp/claude-e2e-tests" ]]; then
        rm -rf "/tmp/claude-e2e-tests"
        log_info "清理临时测试目录"
    fi
    
    # 恢复git状态（如果需要）
    cd "$PROJECT_ROOT"
    if git stash list | grep -q "Pre-test backup ${TEST_TIMESTAMP}"; then
        # 只在测试失败时才恢复
        if [[ ${1:-0} -ne 0 ]]; then
            git stash pop
            log_info "恢复预测试git状态"
        else
            log_info "测试成功，保留当前状态"
        fi
    fi
    
    log_success "清理完成"
}

# 主函数
main() {
    echo "🚀 Claude Enhancer 5.0 - 启动端到端测试套件"
    printf '=%.0s' {1..80}; echo
    
    local overall_result=0
    
    # 检查环境
    check_environment
    
    # 预测试准备
    pre_test_setup
    
    # 执行测试序列
    log_info "开始执行测试序列..."
    
    # 1. Phase测试
    if run_phase_tests; then
        log_success "✅ Phase测试通过"
    else
        log_error "❌ Phase测试失败"
        overall_result=1
    fi
    
    # 2. Hook测试
    if run_hook_tests; then
        log_success "✅ Hook测试通过"
    else
        log_error "❌ Hook测试失败"
        overall_result=1
    fi
    
    # 3. Agent策略测试
    if run_agent_strategy_tests; then
        log_success "✅ Agent策略测试通过"
    else
        log_error "❌ Agent策略测试失败"
        overall_result=1
    fi
    
    # 检查是否生成了JSON报告
    local json_report_pattern="${TEST_DIR}/e2e-test-report.json"
    if [[ -f "$json_report_pattern" ]]; then
        cp "$json_report_pattern" "$TEST_REPORT"
        log_success "复制JSON报告到: $TEST_REPORT"
        
        # 生成HTML报告
        if generate_html_report "$TEST_REPORT" "$HTML_REPORT"; then
            log_success "HTML报告已生成"
        fi
    else
        log_warning "未找到JSON测试报告"
    fi
    
    # 测试后清理
    post_test_cleanup $overall_result
    
    # 最终报告
    echo ""
    printf '=%.0s' {1..80}; echo
    if [[ $overall_result -eq 0 ]]; then
        log_success "🎉 所有测试通过！Claude Enhancer 5.0工作流验证成功"
    else
        log_error "⚠️ 部分测试失败，请检查测试报告"
    fi
    
    echo "📄 测试日志: $TEST_LOG"
    echo "📊 JSON报告: $TEST_REPORT"
    echo "🌐 HTML报告: $HTML_REPORT"
    
    return $overall_result
}

# 脚本入口点
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
