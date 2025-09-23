#!/bin/bash
# =============================================================================
# Claude Enhancer 监控系统启动脚本
# =============================================================================

set -e

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/claude_enhancer_monitor.py"
PID_FILE="$SCRIPT_DIR/.monitor.pid"
LOG_FILE="$PROJECT_ROOT/.claude/logs/monitor.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_status() {
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

# 检查依赖
check_dependencies() {
    print_status "检查依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi

    # 检查必要的Python包
    local required_packages=(
        "asyncio"
        "psutil"
        "prometheus_client"
        "aiohttp"
        "websockets"
        "numpy"
        "sqlite3"
    )

    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            print_warning "缺少Python包: $package"
            pip3 install $package || {
                print_error "安装 $package 失败"
                exit 1
            }
        fi
    done

    print_success "依赖检查完成"
}

# 创建必要目录
create_directories() {
    print_status "创建必要目录..."

    local directories=(
        "$PROJECT_ROOT/.claude/logs"
        "$PROJECT_ROOT/.claude/data"
        "$PROJECT_ROOT/.claude/monitoring"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "创建目录: $dir"
        fi
    done

    print_success "目录创建完成"
}

# 检查端口占用
check_ports() {
    print_status "检查端口占用..."

    local ports=(8091 9091)

    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "端口 $port 已被占用"
            local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            print_warning "占用进程PID: $pid"

            # 如果是我们的监控进程，先停止它
            if [ -f "$PID_FILE" ]; then
                local monitor_pid=$(cat "$PID_FILE")
                if [ "$pid" = "$monitor_pid" ]; then
                    print_status "停止已运行的监控进程..."
                    stop_monitor
                fi
            fi
        fi
    done

    print_success "端口检查完成"
}

# 启动监控
start_monitor() {
    print_status "启动Claude Enhancer监控系统..."

    # 检查监控脚本是否存在
    if [ ! -f "$MONITOR_SCRIPT" ]; then
        print_error "监控脚本不存在: $MONITOR_SCRIPT"
        exit 1
    fi

    # 启动监控进程
    cd "$PROJECT_ROOT"
    nohup python3 "$MONITOR_SCRIPT" > "$LOG_FILE" 2>&1 &
    local pid=$!

    # 保存PID
    echo $pid > "$PID_FILE"

    # 等待启动
    sleep 3

    # 检查进程是否正在运行
    if kill -0 $pid 2>/dev/null; then
        print_success "监控系统启动成功"
        print_status "PID: $pid"
        print_status "日志文件: $LOG_FILE"
        print_status "Web Dashboard: http://localhost:8091"
        print_status "Prometheus Metrics: http://localhost:9091/metrics"
    else
        print_error "监控系统启动失败"
        if [ -f "$LOG_FILE" ]; then
            print_error "错误信息:"
            tail -10 "$LOG_FILE"
        fi
        exit 1
    fi
}

# 停止监控
stop_monitor() {
    print_status "停止监控系统..."

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            sleep 2

            # 强制杀死如果还在运行
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid
                print_warning "强制停止进程 $pid"
            else
                print_success "监控系统已停止"
            fi
        else
            print_warning "监控进程不存在或已停止"
        fi

        rm -f "$PID_FILE"
    else
        print_warning "PID文件不存在"
    fi
}

# 检查状态
check_status() {
    print_status "检查监控系统状态..."

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 $pid 2>/dev/null; then
            print_success "监控系统正在运行 (PID: $pid)"

            # 检查服务是否响应
            if curl -s http://localhost:8091/ >/dev/null 2>&1; then
                print_success "Web Dashboard可访问"
            else
                print_warning "Web Dashboard不可访问"
            fi

            if curl -s http://localhost:9091/metrics >/dev/null 2>&1; then
                print_success "Prometheus Metrics可访问"
            else
                print_warning "Prometheus Metrics不可访问"
            fi
        else
            print_error "监控进程不存在，但PID文件存在"
            rm -f "$PID_FILE"
        fi
    else
        print_error "监控系统未运行"
    fi
}

# 查看日志
view_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_status "监控系统日志 (Ctrl+C退出):"
        tail -f "$LOG_FILE"
    else
        print_error "日志文件不存在: $LOG_FILE"
    fi
}

# 重启监控
restart_monitor() {
    print_status "重启监控系统..."
    stop_monitor
    sleep 2
    start_monitor
}

# 安装为系统服务
install_service() {
    print_status "安装为系统服务..."

    local service_file="/etc/systemd/system/claude-enhancer-monitor.service"

    if [ ! -w "/etc/systemd/system" ]; then
        print_error "需要sudo权限来安装系统服务"
        exit 1
    fi

    cat > "$service_file" << EOF
[Unit]
Description=Claude Enhancer Monitoring System
After=network.target

[Service]
Type=forking
User=$(whoami)
WorkingDirectory=$PROJECT_ROOT
ExecStart=$SCRIPT_DIR/start_monitoring.sh start
ExecStop=$SCRIPT_DIR/start_monitoring.sh stop
ExecReload=$SCRIPT_DIR/start_monitoring.sh restart
PIDFile=$PID_FILE
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable claude-enhancer-monitor

    print_success "系统服务安装完成"
    print_status "使用以下命令管理服务:"
    print_status "  启动: sudo systemctl start claude-enhancer-monitor"
    print_status "  停止: sudo systemctl stop claude-enhancer-monitor"
    print_status "  状态: sudo systemctl status claude-enhancer-monitor"
}

# 卸载系统服务
uninstall_service() {
    print_status "卸载系统服务..."

    local service_file="/etc/systemd/system/claude-enhancer-monitor.service"

    if [ -f "$service_file" ]; then
        systemctl stop claude-enhancer-monitor 2>/dev/null || true
        systemctl disable claude-enhancer-monitor 2>/dev/null || true
        rm -f "$service_file"
        systemctl daemon-reload
        print_success "系统服务卸载完成"
    else
        print_warning "系统服务未安装"
    fi
}

# 显示帮助
show_help() {
    echo "Claude Enhancer 监控系统管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start              启动监控系统"
    echo "  stop               停止监控系统"
    echo "  restart            重启监控系统"
    echo "  status             检查运行状态"
    echo "  logs               查看实时日志"
    echo "  install-service    安装为系统服务"
    echo "  uninstall-service  卸载系统服务"
    echo "  check-deps         检查依赖"
    echo "  help               显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 start           # 启动监控"
    echo "  $0 status          # 查看状态"
    echo "  $0 logs            # 查看日志"
}

# 主函数
main() {
    local command="${1:-start}"

    case "$command" in
        start)
            check_dependencies
            create_directories
            check_ports
            start_monitor
            ;;
        stop)
            stop_monitor
            ;;
        restart)
            restart_monitor
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs
            ;;
        install-service)
            install_service
            ;;
        uninstall-service)
            uninstall_service
            ;;
        check-deps)
            check_dependencies
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"