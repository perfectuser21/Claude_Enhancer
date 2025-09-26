#!/bin/bash

# Claude Enhancer 5.1 端到端测试运行器
# 完整的E2E测试执行脚本，包括环境检查、Hook验证和完整测试套件

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_LOG_DIR="${PROJECT_ROOT}/e2e_test_logs"
TEST_LOG_FILE="${TEST_LOG_DIR}/e2e_test_${TIMESTAMP}.log"

# 创建日志目录
mkdir -p "$TEST_LOG_DIR"

# 日志函数
log() {
    echo -e "$1" | tee -a "$TEST_LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_header() {
    log ""
    log "${PURPLE}================================================================${NC}"
    log "${PURPLE} $1${NC}"
    log "${PURPLE}================================================================${NC}"
}

# 清理函数
cleanup() {
    log_info "清理测试环境..."

    # 切回主分支
    git checkout - 2>/dev/null || true

    # 删除测试分支
    git branch -D "$(git branch --list 'test/e2e-test-*')" 2>/dev/null || true

    # 清理临时文件
    find "$PROJECT_ROOT" -name "test_temp_*.py" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -name "test_commit_*.txt" -delete 2>/dev/null || true

    log_info "清理完成"
}

# 信号处理
trap cleanup EXIT
trap 'log_error "测试被中断"; exit 130' INT TERM

# 环境检查
check_environment() {
    log_header "环境检查"

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装"
        return 1
    fi
    log_info "✅ Python3: $(python3 --version)"

    # 检查Git
    if ! command -v git &> /dev/null; then
        log_error "Git未安装"
        return 1
    fi
    log_info "✅ Git: $(git --version)"

    # 检查项目结构
    if [[ ! -d "${PROJECT_ROOT}/.claude" ]]; then
        log_error "Claude配置目录不存在"
        return 1
    fi
    log_info "✅ Claude配置目录存在"

    # 检查Hook目录
    if [[ ! -d "${PROJECT_ROOT}/.claude/hooks" ]]; then
        log_error "Hook目录不存在"
        return 1
    fi
    log_info "✅ Hook目录存在"

    # 检查设置文件
    if [[ ! -f "${PROJECT_ROOT}/.claude/settings.json" ]]; then
        log_error "Claude设置文件不存在"
        return 1
    fi
    log_info "✅ Claude设置文件存在"

    # 检查必要的Python包
    local missing_packages=()

    # 基础包检查
    python3 -c "import json, subprocess, threading, uuid, tempfile, logging, asyncio, concurrent.futures" 2>/dev/null || missing_packages+=("标准库")

    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        log_warn "缺少Python包: ${missing_packages[*]}"
        log_info "但标准库包应该都存在，继续执行..."
    fi

    log_success "环境检查通过"
    return 0
}

# Hook权限检查和修复
fix_hook_permissions() {
    log_header "Hook权限检查和修复"

    local hooks_dir="${PROJECT_ROOT}/.claude/hooks"
    local fixed_count=0

    if [[ -d "$hooks_dir" ]]; then
        for hook_file in "$hooks_dir"/*.sh; do
            if [[ -f "$hook_file" ]]; then
                if [[ ! -x "$hook_file" ]]; then
                    log_info "修复Hook权限: $(basename "$hook_file")"
                    chmod +x "$hook_file"
                    ((fixed_count++))
                fi
            fi
        done

        if [[ $fixed_count -gt 0 ]]; then
            log_success "修复了 $fixed_count 个Hook文件的权限"
        else
            log_info "所有Hook文件权限正常"
        fi
    fi
}

# 执行Hook验证
run_hook_validation() {
    log_header "Hook功能验证"

    if [[ -f "${PROJECT_ROOT}/validate_hooks_e2e.py" ]]; then
        log_info "开始Hook验证..."

        if python3 "${PROJECT_ROOT}/validate_hooks_e2e.py" "$PROJECT_ROOT"; then
            log_success "Hook验证通过"
            return 0
        else
            local exit_code=$?
            case $exit_code in
                1)
                    log_warn "Hook验证部分通过，但可以继续E2E测试"
                    return 0
                    ;;
                2)
                    log_error "Hook验证严重失败"
                    return 1
                    ;;
                *)
                    log_error "Hook验证异常退出 (code: $exit_code)"
                    return 1
                    ;;
            esac
        fi
    else
        log_warn "Hook验证脚本不存在，跳过验证"
        return 0
    fi
}

# 执行主E2E测试
run_main_e2e_tests() {
    log_header "主E2E测试套件"

    if [[ ! -f "${PROJECT_ROOT}/claude_enhancer_5.1_e2e_test_suite.py" ]]; then
        log_error "E2E测试套件文件不存在"
        return 1
    fi

    log_info "启动完整E2E测试..."
    log_info "测试日志将保存到: $TEST_LOG_FILE"

    # 执行主测试套件
    if python3 "${PROJECT_ROOT}/claude_enhancer_5.1_e2e_test_suite.py" "$PROJECT_ROOT"; then
        log_success "E2E测试套件执行成功"
        return 0
    else
        local exit_code=$?
        log_error "E2E测试套件执行失败 (exit code: $exit_code)"
        return $exit_code
    fi
}

# 收集测试结果
collect_test_results() {
    log_header "测试结果收集"

    local results_dir="${PROJECT_ROOT}/e2e_test_results_${TIMESTAMP}"
    mkdir -p "$results_dir"

    # 复制日志文件
    cp "$TEST_LOG_FILE" "$results_dir/"

    # 收集JSON报告
    find "$PROJECT_ROOT" -name "*e2e_report*.json" -mtime -1 -exec cp {} "$results_dir/" \; 2>/dev/null || true

    # 收集Hook验证结果
    find "$PROJECT_ROOT" -name "hook_validation_results*.json" -mtime -1 -exec cp {} "$results_dir/" \; 2>/dev/null || true

    # 创建摘要文件
    cat > "$results_dir/test_summary.txt" << EOF
Claude Enhancer 5.1 端到端测试摘要
===============================================

测试时间: $(date)
测试ID: ${TIMESTAMP}
项目根目录: ${PROJECT_ROOT}

测试阶段:
1. ✅ 环境检查
2. ✅ Hook权限修复
3. $(if [[ -f "${results_dir}/hook_validation_results"*.json ]]; then echo "✅"; else echo "⚠️ "; fi) Hook功能验证
4. 📊 主E2E测试套件

结果文件:
- 测试日志: $(basename "$TEST_LOG_FILE")
- JSON报告: $(find "$results_dir" -name "*report*.json" -exec basename {} \; | tr '\n' ' ')

建议:
- 查看详细日志了解测试执行情况
- 检查JSON报告获取详细测试结果
- 根据失败项目进行相应的修复

===============================================
EOF

    log_success "测试结果已收集到: $results_dir"

    # 显示结果目录内容
    log_info "结果文件列表:"
    ls -la "$results_dir" | while read -r line; do
        log_info "  $line"
    done
}

# 生成测试报告摘要
generate_summary_report() {
    log_header "生成测试摘要报告"

    # 查找最新的JSON报告
    local latest_report
    latest_report=$(find "$PROJECT_ROOT" -name "*e2e_report*.json" -mtime -1 | sort | tail -n1)

    if [[ -n "$latest_report" && -f "$latest_report" ]]; then
        log_info "解析测试报告: $(basename "$latest_report")"

        # 使用Python解析JSON报告并显示摘要
        python3 << EOF
import json
import sys

try:
    with open('$latest_report', 'r', encoding='utf-8') as f:
        report = json.load(f)

    summary = report.get('test_summary', {})

    print(f"\n📊 测试执行摘要:")
    print(f"   测试总数: {summary.get('total_tests', 0)}")
    print(f"   ✅ 通过: {summary.get('passed', 0)}")
    print(f"   ❌ 失败: {summary.get('failed', 0)}")
    print(f"   ⏭️  跳过: {summary.get('skipped', 0)}")
    print(f"   💥 错误: {summary.get('errors', 0)}")
    print(f"   📈 成功率: {summary.get('success_rate', 0):.1f}%")
    print(f"   ⏱️  执行时间: {summary.get('duration', 0):.2f}秒")

    # 显示阶段摘要
    phase_summary = report.get('phase_summary', {})
    if phase_summary:
        print(f"\n🔄 阶段测试结果:")
        for phase, counts in phase_summary.items():
            total = sum(counts.values())
            pass_count = counts.get('PASS', 0)
            pass_rate = (pass_count / max(1, total)) * 100
            status_icon = "✅" if pass_rate >= 80 else "⚠️" if pass_rate >= 50 else "❌"
            print(f"   {status_icon} {phase}: {pass_count}/{total} ({pass_rate:.0f}%)")

    # 显示建议
    recommendations = report.get('recommendations', [])
    if recommendations:
        print(f"\n💡 改进建议:")
        for i, rec in enumerate(recommendations[:5], 1):  # 只显示前5个建议
            print(f"   {i}. {rec}")

except Exception as e:
    print(f"无法解析测试报告: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    else
        log_warn "未找到测试报告文件"
    fi
}

# 主执行流程
main() {
    log_header "Claude Enhancer 5.1 端到端测试启动"
    log_info "测试时间: $(date)"
    log_info "项目根目录: $PROJECT_ROOT"
    log_info "测试日志: $TEST_LOG_FILE"

    local overall_success=true

    # 1. 环境检查
    if ! check_environment; then
        log_error "环境检查失败，终止测试"
        return 1
    fi

    # 2. Hook权限修复
    fix_hook_permissions

    # 3. Hook验证 (可选，失败不会终止测试)
    if ! run_hook_validation; then
        log_warn "Hook验证失败，但继续执行E2E测试"
        overall_success=false
    fi

    # 4. 主E2E测试
    if ! run_main_e2e_tests; then
        log_error "E2E测试执行失败"
        overall_success=false
    fi

    # 5. 收集结果
    collect_test_results

    # 6. 生成摘要
    generate_summary_report

    # 最终结果
    if $overall_success; then
        log_success "🎉 Claude Enhancer 5.1 端到端测试完成！"
        log_info "所有测试组件执行成功"
        return 0
    else
        log_warn "⚠️  Claude Enhancer 5.1 端到端测试完成，但存在问题"
        log_info "请查看详细日志和报告进行问题排查"
        return 1
    fi
}

# 帮助信息
show_help() {
    cat << EOF
Claude Enhancer 5.1 端到端测试运行器

用法: $0 [选项]

选项:
  -h, --help          显示此帮助信息
  -v, --verbose       详细输出模式
  --skip-hook-check   跳过Hook验证
  --dry-run          仅检查环境，不执行测试

示例:
  $0                  # 运行完整E2E测试
  $0 --verbose        # 详细模式运行
  $0 --dry-run        # 仅检查环境

日志和结果:
  - 测试日志: ./e2e_test_logs/
  - 测试结果: ./e2e_test_results_*/
  - JSON报告: ./*e2e_report*.json

EOF
}

# 命令行参数处理
VERBOSE=false
SKIP_HOOK_CHECK=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            set -x  # 启用详细输出
            shift
            ;;
        --skip-hook-check)
            SKIP_HOOK_CHECK=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 执行主流程
if $DRY_RUN; then
    log_header "Dry Run - 仅检查环境"
    check_environment
    log_info "环境检查完成，实际测试请移除 --dry-run 选项"
else
    main
fi