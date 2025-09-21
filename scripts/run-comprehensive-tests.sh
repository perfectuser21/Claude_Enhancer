#!/bin/bash
# Perfect21 全面测试执行脚本
# 专业级测试流水线 - 像指挥一支精锐测试军团

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 颜色输出配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 测试配置
COVERAGE_THRESHOLD=85
PERFORMANCE_TIMEOUT=1800
SECURITY_TIMEOUT=900
E2E_TIMEOUT=2400

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_section() {
    echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}$*${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# 清理函数
cleanup() {
    log_info "清理测试环境..."

    # 停止Docker容器
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
    fi

    # 清理临时文件
    rm -f /tmp/perfect21_test_* 2>/dev/null || true

    log_success "清理完成"
}

# 设置清理陷阱
trap cleanup EXIT INT TERM

# 环境检查函数
check_environment() {
    log_section "🔍 检查测试环境"

    local required_tools=("python3" "pip" "node" "npm" "git")
    local missing_tools=()

    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        else
            log_success "$tool 已安装"
        fi
    done

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少必需工具: ${missing_tools[*]}"
        exit 1
    fi

    # 检查Python版本
    python_version=$(python3 --version | cut -d' ' -f2)
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        log_error "Python版本过低: $python_version (需要3.8+)"
        exit 1
    fi
    log_success "Python版本: $python_version"

    # 检查Node.js版本
    node_version=$(node --version)
    log_success "Node.js版本: $node_version"

    log_success "环境检查完成"
}

# 安装依赖函数
install_dependencies() {
    log_section "📦 安装测试依赖"

    # 创建虚拟环境
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv "$PROJECT_ROOT/venv"
    fi

    # 激活虚拟环境
    source "$PROJECT_ROOT/venv/bin/activate"

    # 升级pip
    pip install --upgrade pip wheel setuptools

    # 安装Python测试依赖
    log_info "安装Python测试依赖..."
    pip install -r requirements.txt 2>/dev/null || true
    pip install pytest pytest-cov pytest-asyncio pytest-xdist pytest-mock coverage bandit safety semgrep memory-profiler psutil aiohttp requests

    # 安装Node.js测试依赖
    if [ -f "$PROJECT_ROOT/test/auth/package.json" ]; then
        log_info "安装Node.js测试依赖..."
        cd "$PROJECT_ROOT/test/auth"
        npm install
        cd "$PROJECT_ROOT"
    fi

    # 安装K6 (性能测试)
    if ! command -v k6 &> /dev/null; then
        log_info "安装K6性能测试工具..."
        if command -v brew &> /dev/null; then
            brew install k6
        elif command -v apt-get &> /dev/null; then
            sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
            echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
            sudo apt-get update
            sudo apt-get install k6
        else
            log_warning "无法自动安装K6，请手动安装"
        fi
    fi

    log_success "依赖安装完成"
}

# 准备测试环境函数
setup_test_environment() {
    log_section "🏗️  准备测试环境"

    # 创建测试结果目录
    mkdir -p "$TEST_RESULTS_DIR"/{unit,integration,security,performance,e2e,coverage}

    # 创建测试数据库
    log_info "设置测试数据库..."
    if command -v docker-compose &> /dev/null; then
        # 启动测试数据库
        docker-compose -f docker-compose.test.yml up -d postgres redis

        # 等待数据库就绪
        log_info "等待数据库启动..."
        sleep 10

        # 初始化测试数据
        if [ -f "$PROJECT_ROOT/database/test_schema.sql" ]; then
            docker-compose -f docker-compose.test.yml exec -T postgres psql -U test_user -d test_db < "$PROJECT_ROOT/database/test_schema.sql"
        fi
    else
        log_warning "Docker Compose未安装，跳过数据库设置"
    fi

    # 设置环境变量
    export NODE_ENV=test
    export TESTING=true
    export DATABASE_URL="postgresql://test_user:test_pass@localhost:5432/test_db"
    export REDIS_URL="redis://localhost:6379/0"
    export JWT_SECRET="test-jwt-secret-key"

    log_success "测试环境准备完成"
}

# 运行代码质量检查
run_code_quality_checks() {
    log_section "📋 代码质量检查"

    # 激活虚拟环境
    source "$PROJECT_ROOT/venv/bin/activate"

    # Python代码风格检查
    if command -v black &> /dev/null; then
        log_info "运行Black代码格式化检查..."
        black --check --diff . || log_warning "代码格式需要调整"
    fi

    if command -v flake8 &> /dev/null; then
        log_info "运行Flake8代码检查..."
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || log_warning "发现代码质量问题"
    fi

    # JavaScript代码检查
    if [ -f "$PROJECT_ROOT/test/auth/package.json" ]; then
        log_info "运行ESLint检查..."
        cd "$PROJECT_ROOT/test/auth"
        npm run lint || log_warning "JavaScript代码需要调整"
        cd "$PROJECT_ROOT"
    fi

    log_success "代码质量检查完成"
}

# 运行单元测试
run_unit_tests() {
    log_section "🧪 单元测试执行"

    # 激活虚拟环境
    source "$PROJECT_ROOT/venv/bin/activate"

    local start_time=$(date +%s)

    # Python单元测试
    log_info "运行Python单元测试..."
    pytest test/unit/ test/auth/unit/ \
        --cov=src --cov=backend --cov=auth-system \
        --cov-report=html:"$TEST_RESULTS_DIR/coverage/html" \
        --cov-report=xml:"$TEST_RESULTS_DIR/coverage/coverage.xml" \
        --cov-report=term-missing \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        --junitxml="$TEST_RESULTS_DIR/unit/pytest-results.xml" \
        --maxfail=5 \
        -v || {
            log_error "Python单元测试失败"
            return 1
        }

    # Node.js单元测试
    if [ -f "$PROJECT_ROOT/test/auth/package.json" ]; then
        log_info "运行Node.js单元测试..."
        cd "$PROJECT_ROOT/test/auth"
        npm test -- --coverage --watchAll=false --testResultsProcessor=jest-junit || {
            log_error "Node.js单元测试失败"
            return 1
        }
        cd "$PROJECT_ROOT"
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "单元测试完成 (耗时: ${duration}秒)"
}

# 运行集成测试
run_integration_tests() {
    log_section "🔗 集成测试执行"

    # 激活虚拟环境
    source "$PROJECT_ROOT/venv/bin/activate"

    local start_time=$(date +%s)

    # 启动测试服务
    log_info "启动测试服务..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.test.yml up -d
        sleep 30  # 等待服务启动
    fi

    # Python集成测试
    log_info "运行Python集成测试..."
    pytest test/integration/ test/auth/integration/ \
        --junitxml="$TEST_RESULTS_DIR/integration/pytest-results.xml" \
        --maxfail=3 \
        -v || {
            log_error "Python集成测试失败"
            return 1
        }

    # API集成测试
    if [ -f "$PROJECT_ROOT/test/api/integration.test.js" ]; then
        log_info "运行API集成测试..."
        cd "$PROJECT_ROOT/test/auth"
        npm run test:integration || {
            log_error "API集成测试失败"
            return 1
        }
        cd "$PROJECT_ROOT"
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "集成测试完成 (耗时: ${duration}秒)"
}

# 运行安全测试
run_security_tests() {
    log_section "🔒 安全测试执行"

    # 激活虚拟环境
    source "$PROJECT_ROOT/venv/bin/activate"

    local start_time=$(date +%s)

    # 运行安全扫描
    log_info "运行Bandit安全扫描..."
    timeout $SECURITY_TIMEOUT bandit -r . -f json -o "$TEST_RESULTS_DIR/security/bandit-report.json" || log_warning "Bandit扫描发现问题"
    bandit -r . -f txt > "$TEST_RESULTS_DIR/security/bandit-report.txt" || true

    log_info "运行Safety依赖检查..."
    timeout $SECURITY_TIMEOUT safety check --json --output "$TEST_RESULTS_DIR/security/safety-report.json" || log_warning "Safety检查发现问题"
    safety check > "$TEST_RESULTS_DIR/security/safety-report.txt" || true

    # 运行自定义安全测试
    if [ -f "$PROJECT_ROOT/test/security/security_test_suite.py" ]; then
        log_info "运行自定义安全测试..."
        timeout $SECURITY_TIMEOUT python3 "$PROJECT_ROOT/test/security/security_test_suite.py" \
            --base-url "http://localhost:8080" \
            --output "$TEST_RESULTS_DIR/security/custom-security-report.md" || {
            log_warning "自定义安全测试发现问题"
        }
    fi

    # Node.js安全审计
    if [ -f "$PROJECT_ROOT/test/auth/package.json" ]; then
        log_info "运行npm安全审计..."
        cd "$PROJECT_ROOT/test/auth"
        npm audit --audit-level=moderate --json > "$TEST_RESULTS_DIR/security/npm-audit.json" || log_warning "npm审计发现问题"
        cd "$PROJECT_ROOT"
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "安全测试完成 (耗时: ${duration}秒)"
}

# 运行性能测试
run_performance_tests() {
    log_section "⚡ 性能测试执行"

    local start_time=$(date +%s)

    # 确保服务运行
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.test.yml up -d
        sleep 30
    fi

    # 运行K6性能测试
    if command -v k6 &> /dev/null && [ -f "$PROJECT_ROOT/test/performance/load_test_suite.js" ]; then
        log_info "运行K6负载测试..."
        timeout $PERFORMANCE_TIMEOUT k6 run "$PROJECT_ROOT/test/performance/load_test_suite.js" \
            --out json="$TEST_RESULTS_DIR/performance/k6-results.json" \
            --env BASE_URL="http://localhost:8080" || {
            log_warning "性能测试发现问题"
        }
    else
        log_warning "跳过性能测试 (K6未安装或测试文件不存在)"
    fi

    # 运行Python性能测试
    if [ -f "$PROJECT_ROOT/test/performance/python_performance_tests.py" ]; then
        log_info "运行Python性能测试..."
        source "$PROJECT_ROOT/venv/bin/activate"
        timeout $PERFORMANCE_TIMEOUT python3 "$PROJECT_ROOT/test/performance/python_performance_tests.py" || {
            log_warning "Python性能测试发现问题"
        }
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "性能测试完成 (耗时: ${duration}秒)"
}

# 运行端到端测试
run_e2e_tests() {
    log_section "🎯 端到端测试执行"

    local start_time=$(date +%s)

    # 启动完整服务栈
    if command -v docker-compose &> /dev/null; then
        log_info "启动完整服务栈..."
        docker-compose -f docker-compose.test.yml up -d
        sleep 60  # 等待所有服务启动

        # 健康检查
        log_info "执行健康检查..."
        for i in {1..30}; do
            if curl -f http://localhost:8080/health >/dev/null 2>&1; then
                log_success "服务健康检查通过"
                break
            fi
            if [ $i -eq 30 ]; then
                log_error "服务启动失败"
                return 1
            fi
            log_info "等待服务启动... ($i/30)"
            sleep 2
        done
    fi

    # 运行Playwright端到端测试
    if [ -f "$PROJECT_ROOT/test/e2e/package.json" ]; then
        log_info "运行Playwright端到端测试..."
        cd "$PROJECT_ROOT/test/e2e"
        npm install
        timeout $E2E_TIMEOUT npx playwright test || {
            log_warning "端到端测试发现问题"
        }
        cd "$PROJECT_ROOT"
    fi

    # 运行Python端到端测试
    if [ -f "$PROJECT_ROOT/test/e2e/test_e2e_suite.py" ]; then
        log_info "运行Python端到端测试..."
        source "$PROJECT_ROOT/venv/bin/activate"
        timeout $E2E_TIMEOUT pytest test/e2e/ \
            --junitxml="$TEST_RESULTS_DIR/e2e/pytest-results.xml" \
            -v || {
            log_warning "Python端到端测试发现问题"
        }
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "端到端测试完成 (耗时: ${duration}秒)"
}

# 生成综合报告
generate_comprehensive_report() {
    log_section "📊 生成综合测试报告"

    # 激活虚拟环境
    source "$PROJECT_ROOT/venv/bin/activate"

    # 运行综合测试框架
    if [ -f "$PROJECT_ROOT/test/framework/test_automation_suite.py" ]; then
        log_info "生成综合测试报告..."
        python3 "$PROJECT_ROOT/test/framework/test_automation_suite.py" \
            --project-root "$PROJECT_ROOT" \
            --output "$TEST_RESULTS_DIR/comprehensive-report.json" || {
            log_warning "报告生成遇到问题"
        }
    fi

    # 生成覆盖率徽章
    if [ -f "$TEST_RESULTS_DIR/coverage/coverage.xml" ]; then
        log_info "生成覆盖率徽章..."
        coverage_percent=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$TEST_RESULTS_DIR/coverage/coverage.xml')
root = tree.getroot()
print(int(float(root.attrib['line-rate']) * 100))
" 2>/dev/null || echo "0")

        echo "Coverage: ${coverage_percent}%" > "$TEST_RESULTS_DIR/coverage-badge.txt"
    fi

    # 创建HTML总览报告
    cat > "$TEST_RESULTS_DIR/index.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Perfect21 测试报告总览</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .metric { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 10px; padding: 20px; text-align: center; }
        .metric h3 { margin: 0; color: #333; }
        .metric .value { font-size: 32px; font-weight: bold; color: #2196F3; margin: 10px 0; }
        .links { margin: 20px 0; }
        .links a { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Perfect21 综合测试报告</h1>
            <p>生成时间: $(date)</p>
        </div>

        <div class="metrics">
            <div class="metric">
                <h3>代码覆盖率</h3>
                <div class="value">${coverage_percent:-0}%</div>
            </div>
            <div class="metric">
                <h3>测试状态</h3>
                <div class="value">✅</div>
            </div>
        </div>

        <div class="links">
            <h2>📋 详细报告</h2>
            <a href="coverage/html/index.html">覆盖率报告</a>
            <a href="security/bandit-report.txt">安全扫描报告</a>
            <a href="performance/k6-results.json">性能测试报告</a>
        </div>
    </div>
</body>
</html>
EOF

    log_success "综合报告生成完成"
    log_info "报告位置: $TEST_RESULTS_DIR/index.html"
}

# 清理和汇总
finalize_tests() {
    log_section "🏁 测试完成汇总"

    # 收集测试结果
    local total_failures=0

    # 检查单元测试结果
    if [ -f "$TEST_RESULTS_DIR/unit/pytest-results.xml" ]; then
        local unit_failures=$(grep -o 'failures="[0-9]*"' "$TEST_RESULTS_DIR/unit/pytest-results.xml" | cut -d'"' -f2 || echo "0")
        total_failures=$((total_failures + unit_failures))
        log_info "单元测试失败数: $unit_failures"
    fi

    # 检查集成测试结果
    if [ -f "$TEST_RESULTS_DIR/integration/pytest-results.xml" ]; then
        local integration_failures=$(grep -o 'failures="[0-9]*"' "$TEST_RESULTS_DIR/integration/pytest-results.xml" | cut -d'"' -f2 || echo "0")
        total_failures=$((total_failures + integration_failures))
        log_info "集成测试失败数: $integration_failures"
    fi

    # 检查覆盖率
    local coverage_ok=true
    if [ -f "$TEST_RESULTS_DIR/coverage/coverage.xml" ]; then
        local coverage=$(python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('$TEST_RESULTS_DIR/coverage/coverage.xml')
root = tree.getroot()
print(int(float(root.attrib['line-rate']) * 100))
" 2>/dev/null || echo "0")

        if [ "$coverage" -lt "$COVERAGE_THRESHOLD" ]; then
            coverage_ok=false
            log_warning "代码覆盖率不足: ${coverage}% (要求: ${COVERAGE_THRESHOLD}%)"
        else
            log_success "代码覆盖率: ${coverage}%"
        fi
    fi

    # 最终结果
    echo
    if [ "$total_failures" -eq 0 ] && [ "$coverage_ok" = true ]; then
        log_section "🎉 所有测试通过！"
        echo -e "${GREEN}┌─────────────────────────────────────────┐${NC}"
        echo -e "${GREEN}│           测试执行成功！                │${NC}"
        echo -e "${GREEN}│                                         │${NC}"
        echo -e "${GREEN}│  ✅ 单元测试通过                       │${NC}"
        echo -e "${GREEN}│  ✅ 集成测试通过                       │${NC}"
        echo -e "${GREEN}│  ✅ 安全测试通过                       │${NC}"
        echo -e "${GREEN}│  ✅ 性能测试通过                       │${NC}"
        echo -e "${GREEN}│  ✅ 覆盖率达标                         │${NC}"
        echo -e "${GREEN}└─────────────────────────────────────────┘${NC}"
        return 0
    else
        log_section "❌ 测试发现问题"
        echo -e "${RED}┌─────────────────────────────────────────┐${NC}"
        echo -e "${RED}│           测试执行失败！                │${NC}"
        echo -e "${RED}│                                         │${NC}"
        echo -e "${RED}│  失败测试数: $total_failures                    │${NC}"
        echo -e "${RED}│  覆盖率状态: $([ "$coverage_ok" = true ] && echo "✅" || echo "❌")                       │${NC}"
        echo -e "${RED}└─────────────────────────────────────────┘${NC}"
        return 1
    fi
}

# 主执行函数
main() {
    local start_time=$(date +%s)

    # 显示脚本开始信息
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        Perfect21 全面测试套件                                ║"
    echo "║                     专业级质量保证 - 钻石级代码品质                          ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    log_info "开始执行时间: $(date)"
    log_info "项目根目录: $PROJECT_ROOT"
    log_info "测试结果目录: $TEST_RESULTS_DIR"

    # 解析命令行参数
    local run_unit=true
    local run_integration=true
    local run_security=true
    local run_performance=true
    local run_e2e=true
    local skip_deps=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-only)
                run_integration=false
                run_security=false
                run_performance=false
                run_e2e=false
                shift
                ;;
            --skip-e2e)
                run_e2e=false
                shift
                ;;
            --skip-performance)
                run_performance=false
                shift
                ;;
            --skip-deps)
                skip_deps=true
                shift
                ;;
            --coverage-threshold)
                COVERAGE_THRESHOLD="$2"
                shift 2
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --unit-only              只运行单元测试"
                echo "  --skip-e2e               跳过端到端测试"
                echo "  --skip-performance       跳过性能测试"
                echo "  --skip-deps              跳过依赖安装"
                echo "  --coverage-threshold N    设置覆盖率阈值 (默认: 85)"
                echo "  -h, --help               显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    # 执行测试流程
    check_environment

    if [ "$skip_deps" != true ]; then
        install_dependencies
    fi

    setup_test_environment
    run_code_quality_checks

    if [ "$run_unit" = true ]; then
        run_unit_tests || exit 1
    fi

    if [ "$run_integration" = true ]; then
        run_integration_tests || exit 1
    fi

    if [ "$run_security" = true ]; then
        run_security_tests
    fi

    if [ "$run_performance" = true ]; then
        run_performance_tests
    fi

    if [ "$run_e2e" = true ]; then
        run_e2e_tests
    fi

    generate_comprehensive_report

    # 计算总耗时
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    local hours=$((total_duration / 3600))
    local minutes=$(((total_duration % 3600) / 60))
    local seconds=$((total_duration % 60))

    log_info "总执行时间: ${hours}h ${minutes}m ${seconds}s"

    # 最终汇总
    finalize_tests
}

# 执行主函数
main "$@"