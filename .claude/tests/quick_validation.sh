#!/bin/bash
# Claude Enhancer 5.2 - 快速验证脚本
# 快速验证三个核心修复是否正常工作

set -e

# 测试配置
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly HOOKS_DIR="$PROJECT_ROOT/hooks"
readonly CORE_DIR="$PROJECT_ROOT/core"

# 颜色输出
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# 验证计数
declare -i total_checks=0
declare -i passed_checks=0

# 检查函数
check_component() {
    local component_name="$1"
    local test_command="$2"
    local expected_pattern="$3"

    ((total_checks++))
    log_info "检查 $component_name..."

    local result
    local exit_code=0
    result=$(eval "$test_command" 2>&1) || exit_code=$?

    if [ $exit_code -eq 0 ] && echo "$result" | grep -q "$expected_pattern"; then
        log_success "$component_name 工作正常"
        ((passed_checks++))
        return 0
    else
        log_error "$component_name 检查失败"
        echo "   命令: $test_command"
        echo "   期望: $expected_pattern"
        echo "   实际: $result"
        return 1
    fi
}

# 主验证流程
main() {
    echo "🚀 Claude Enhancer 5.2 - 快速验证"
    echo "====================================="
    echo

    # 1. 验证 quality_gate.sh
    local test_input='{"prompt": "implement user authentication system", "model": "claude-3-sonnet"}'
    check_component \
        "quality_gate.sh" \
        "echo '$test_input' | '$HOOKS_DIR/quality_gate.sh'" \
        "质量评分"

    # 2. 验证 smart_agent_selector.sh
    check_component \
        "smart_agent_selector.sh" \
        "echo '$test_input' | '$HOOKS_DIR/smart_agent_selector.sh' 2>&1" \
        "🤖 Claude Enhancer - Agent Selector"

    # 3. 验证 lazy_orchestrator.py
    if command -v python3 &> /dev/null; then
        check_component \
            "lazy_orchestrator.py" \
            "python3 -c 'import sys; sys.path.insert(0, \"$CORE_DIR\"); from lazy_orchestrator import LazyAgentOrchestrator; orch = LazyAgentOrchestrator(); result = orch.select_agents_intelligent(\"implement authentication\"); print(result[\"complexity\"])'" \
            "standard"
    else
        log_warning "Python3 未找到，跳过 lazy_orchestrator.py 验证"
        ((total_checks++))
    fi

    # 4. 验证基本性能
    log_info "检查基本性能..."
    ((total_checks++))
    local start_time=$(date +%s%N)
    echo "$test_input" | "$HOOKS_DIR/quality_gate.sh" >/dev/null 2>&1
    local end_time=$(date +%s%N)
    local duration_ms=$(( (end_time - start_time) / 1000000 ))

    if [ $duration_ms -lt 500 ]; then
        log_success "性能检查通过 (${duration_ms}ms < 500ms)"
        ((passed_checks++))
    else
        log_warning "性能可能需要优化 (${duration_ms}ms)"
    fi

    # 输出结果
    echo
    echo "====================================="
    echo "📊 验证结果: $passed_checks/$total_checks 通过"

    if [ $passed_checks -eq $total_checks ]; then
        log_success "🎉 所有组件工作正常！"
        echo "✅ quality_gate.sh - 质量检查正常"
        echo "✅ smart_agent_selector.sh - Agent选择正常"
        echo "✅ lazy_orchestrator.py - 编排器正常"
        echo "✅ 基本性能达标"
        echo
        echo "💡 建议: 运行完整测试套件进行深度验证"
        echo "   执行: $SCRIPT_DIR/master_test_runner.sh"
        exit 0
    else
        log_error "❌ 部分组件存在问题"
        echo
        echo "🔧 修复建议:"
        [ $passed_checks -lt $total_checks ] && echo "   1. 检查相关脚本的权限和依赖"
        echo "   2. 查看错误信息并修复"
        echo "   3. 运行完整测试套件获取详细诊断"
        exit 1
    fi
}

# 执行验证
main "$@"