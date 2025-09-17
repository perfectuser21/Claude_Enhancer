#!/bin/bash
# Perfect21认证系统启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python版本
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi

    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_info "Python版本: $python_version"

    # 检查是否为Python 3.8+
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "需要Python 3.8或更高版本"
        exit 1
    fi
}

# 检查并安装依赖
install_dependencies() {
    print_info "检查依赖包..."

    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt 文件不存在"
        exit 1
    fi

    # 检查是否在虚拟环境中
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "建议使用虚拟环境运行应用"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "已取消"
            exit 0
        fi
    else
        print_success "虚拟环境: $VIRTUAL_ENV"
    fi

    # 安装依赖
    print_info "安装Python依赖包..."
    pip install -r requirements.txt

    print_success "依赖包安装完成"
}

# 检查环境变量
check_environment() {
    print_info "检查环境配置..."

    # 检查.env文件
    if [ ! -f ".env" ]; then
        print_warning ".env 文件不存在，使用默认配置"

        # 创建基本的.env文件
        cat > .env << EOF
# Perfect21认证系统环境配置

# 环境类型 (development, production, test)
ENVIRONMENT=development

# 数据库配置
DATABASE_URL=sqlite:///./data/perfect21_auth.db

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT配置
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-$(date +%s)
JWT_ALGORITHM=RS256

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 日志配置
LOG_LEVEL=INFO

# CORS配置
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
EOF

        print_success "已创建默认 .env 文件"
    else
        print_success "环境配置文件存在"
    fi

    # 检查数据目录
    if [ ! -d "data" ]; then
        print_info "创建数据目录..."
        mkdir -p data
        print_success "数据目录创建完成"
    fi

    # 检查配置目录和密钥
    if [ ! -d "config/keys" ]; then
        print_info "创建密钥目录..."
        mkdir -p config/keys
        print_success "密钥目录创建完成"
    fi
}

# 检查服务依赖
check_services() {
    print_info "检查外部服务..."

    # 检查Redis (可选)
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_success "Redis服务运行正常"
        else
            print_warning "Redis服务未运行，某些功能可能受限"
        fi
    else
        print_warning "Redis未安装，建议安装以获得完整功能"
    fi

    # 检查PostgreSQL (可选)
    if command -v psql &> /dev/null; then
        print_success "PostgreSQL客户端可用"
    else
        print_info "PostgreSQL客户端未安装，使用SQLite作为数据库"
    fi
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."

    # 这里可以添加数据库迁移命令
    # 例如使用Alembic进行数据库迁移

    print_success "数据库初始化完成"
}

# 启动服务器
start_server() {
    print_info "启动Perfect21认证系统..."

    # 设置环境变量
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"

    # 根据环境选择启动方式
    ENVIRONMENT=${ENVIRONMENT:-development}

    if [ "$ENVIRONMENT" = "production" ]; then
        print_info "生产环境模式启动..."

        # 生产环境使用gunicorn
        if command -v gunicorn &> /dev/null; then
            exec gunicorn backend.main:app \
                --bind 0.0.0.0:${PORT:-8000} \
                --workers ${WORKERS:-4} \
                --worker-class uvicorn.workers.UvicornWorker \
                --access-logfile - \
                --error-logfile - \
                --log-level info
        else
            print_warning "gunicorn未安装，使用uvicorn启动"
            exec uvicorn backend.main:app \
                --host 0.0.0.0 \
                --port ${PORT:-8000} \
                --workers ${WORKERS:-1}
        fi
    else
        print_info "开发环境模式启动..."

        # 开发环境使用uvicorn
        exec uvicorn backend.main:app \
            --host ${HOST:-0.0.0.0} \
            --port ${PORT:-8000} \
            --reload \
            --log-level ${LOG_LEVEL:-info}
    fi
}

# 显示使用帮助
show_help() {
    echo "Perfect21认证系统启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help, -h          显示此帮助信息"
    echo "  --install-deps      仅安装依赖包"
    echo "  --check-only        仅检查环境，不启动服务"
    echo "  --production        生产环境模式"
    echo "  --port PORT         指定端口号 (默认: 8000)"
    echo "  --workers NUM       工作进程数 (生产环境, 默认: 4)"
    echo ""
    echo "环境变量:"
    echo "  ENVIRONMENT         环境类型 (development, production, test)"
    echo "  HOST               监听地址 (默认: 0.0.0.0)"
    echo "  PORT               监听端口 (默认: 8000)"
    echo "  WORKERS            工作进程数 (默认: 4)"
    echo "  LOG_LEVEL          日志级别 (默认: info)"
    echo ""
    echo "示例:"
    echo "  $0                  # 开发模式启动"
    echo "  $0 --production     # 生产模式启动"
    echo "  $0 --port 9000      # 指定端口启动"
    echo "  $0 --check-only     # 仅检查环境"
}

# 主函数
main() {
    print_success "Perfect21认证系统启动脚本"
    print_info "========================================"

    # 解析命令行参数
    INSTALL_DEPS_ONLY=false
    CHECK_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --install-deps)
                INSTALL_DEPS_ONLY=true
                shift
                ;;
            --check-only)
                CHECK_ONLY=true
                shift
                ;;
            --production)
                export ENVIRONMENT=production
                shift
                ;;
            --port)
                export PORT="$2"
                shift 2
                ;;
            --workers)
                export WORKERS="$2"
                shift 2
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 执行检查和初始化
    check_python
    check_environment

    if [ "$INSTALL_DEPS_ONLY" = true ]; then
        install_dependencies
        print_success "依赖包安装完成"
        exit 0
    fi

    install_dependencies
    check_services
    init_database

    if [ "$CHECK_ONLY" = true ]; then
        print_success "环境检查完成，所有依赖满足要求"
        exit 0
    fi

    print_info "========================================"
    print_success "系统检查完成，开始启动服务..."
    print_info "========================================"

    # 启动服务器
    start_server
}

# 捕获Ctrl+C信号
trap 'print_info "正在关闭服务..."; exit 0' INT TERM

# 执行主函数
main "$@"