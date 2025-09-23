#!/bin/bash
# =============================================================================
# Claude Enhancer 监控系统部署脚本
# 一键部署完整的监控、告警和Dashboard解决方案
# =============================================================================

set -e

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.monitoring.yml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${CYAN}=================================${NC}"
    echo -e "${CYAN} $1 ${NC}"
    echo -e "${CYAN}=================================${NC}"
}

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

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_header "检查系统依赖"

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装Docker Compose"
        exit 1
    fi

    # 检查端口占用
    local ports=(3001 8091 9090 9091 9093 9100 9115 3100 8080)
    local occupied_ports=()

    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            occupied_ports+=($port)
        fi
    done

    if [ ${#occupied_ports[@]} -gt 0 ]; then
        print_warning "以下端口已被占用: ${occupied_ports[*]}"
        print_warning "这可能影响监控服务的启动"
        read -p "是否继续? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    print_success "依赖检查完成"
}

# 创建必要目录和文件
setup_directories() {
    print_header "设置目录结构"

    local directories=(
        "$PROJECT_ROOT/.claude/logs"
        "$PROJECT_ROOT/.claude/data"
        "$PROJECT_ROOT/.claude/monitoring/grafana/provisioning/dashboards"
        "$PROJECT_ROOT/.claude/monitoring/grafana/provisioning/datasources"
        "$PROJECT_ROOT/.claude/monitoring/grafana/dashboards"
        "$PROJECT_ROOT/data"
        "$PROJECT_ROOT/logs"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "创建目录: $dir"
        fi
    done

    print_success "目录设置完成"
}

# 生成配置文件
generate_configs() {
    print_header "生成配置文件"

    # 生成Grafana数据源配置
    cat > "$SCRIPT_DIR/grafana/provisioning/datasources/datasource.yaml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "5s"

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      maxLines: 1000
EOF

    # 生成Grafana Dashboard配置
    cat > "$SCRIPT_DIR/grafana/provisioning/dashboards/dashboard.yaml" << 'EOF'
apiVersion: 1

providers:
  - name: 'claude-enhancer'
    orgId: 1
    folder: 'Claude Enhancer'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    # 复制Dashboard JSON文件
    if [ -f "$SCRIPT_DIR/grafana_dashboard.json" ]; then
        cp "$SCRIPT_DIR/grafana_dashboard.json" "$SCRIPT_DIR/grafana/dashboards/"
        print_status "Dashboard配置已复制"
    fi

    # 生成AlertManager配置
    cat > "$SCRIPT_DIR/alertmanager.claude.yml" << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@claude-enhancer.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'claude-enhancer-alerts'

receivers:
  - name: 'claude-enhancer-alerts'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#claude-enhancer-alerts'
        title: 'Claude Enhancer Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
EOF

    # 生成Loki配置
    cat > "$SCRIPT_DIR/loki.claude.yml" << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 1h
  max_chunk_age: 1h
  chunk_target_size: 1048576
  chunk_retain_period: 30s
  max_transfer_retries: 0

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

ruler:
  storage:
    type: local
    local:
      directory: /loki/rules
  rule_path: /loki/rules-temp
  alertmanager_url: http://alertmanager:9093
  ring:
    kvstore:
      store: inmemory
  enable_api: true
EOF

    # 生成Promtail配置
    cat > "$SCRIPT_DIR/promtail.claude.yml" << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: claude-enhancer-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: claude-enhancer
          __path__: /var/log/claude/*.log

  - job_name: application-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: application
          __path__: /var/log/app/*.log
EOF

    # 生成Blackbox配置
    cat > "$SCRIPT_DIR/blackbox.claude.yml" << 'EOF'
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: []
      method: GET
      follow_redirects: true
      preferred_ip_protocol: "ip4"

  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: "ip4"
EOF

    print_success "配置文件生成完成"
}

# 构建Docker镜像
build_images() {
    print_header "构建Docker镜像"

    cd "$SCRIPT_DIR"

    print_step "构建监控应用镜像..."
    docker build -f Dockerfile.monitor -t claude-enhancer-monitor:latest .

    print_step "构建性能收集器镜像..."
    docker build -f Dockerfile.collector -t claude-enhancer-collector:latest .

    print_success "Docker镜像构建完成"
}

# 启动监控栈
start_monitoring() {
    print_header "启动监控服务栈"

    cd "$SCRIPT_DIR"

    print_step "启动所有监控服务..."
    docker-compose -f "$COMPOSE_FILE" up -d

    print_step "等待服务启动..."
    sleep 30

    # 检查服务状态
    print_step "检查服务状态..."
    docker-compose -f "$COMPOSE_FILE" ps

    print_success "监控服务栈启动完成"
}

# 显示服务信息
show_service_info() {
    print_header "服务访问信息"

    echo -e "${GREEN}🚀 Claude Enhancer 监控系统部署完成！${NC}"
    echo ""
    echo -e "${CYAN}📊 监控服务访问地址:${NC}"
    echo -e "  ${YELLOW}• Claude Enhancer Dashboard:${NC} http://localhost:8091"
    echo -e "  ${YELLOW}• Grafana Dashboard:${NC}         http://localhost:3001 (admin/admin123)"
    echo -e "  ${YELLOW}• Prometheus:${NC}                http://localhost:9090"
    echo -e "  ${YELLOW}• AlertManager:${NC}              http://localhost:9093"
    echo -e "  ${YELLOW}• Node Exporter:${NC}             http://localhost:9100"
    echo -e "  ${YELLOW}• cAdvisor:${NC}                  http://localhost:8080"
    echo ""
    echo -e "${CYAN}📈 指标端点:${NC}"
    echo -e "  ${YELLOW}• Claude Enhancer Metrics:${NC}   http://localhost:9091/metrics"
    echo -e "  ${YELLOW}• System Metrics:${NC}            http://localhost:9100/metrics"
    echo ""
    echo -e "${CYAN}🔧 管理命令:${NC}"
    echo -e "  ${YELLOW}• 查看日志:${NC}     docker-compose -f $COMPOSE_FILE logs -f"
    echo -e "  ${YELLOW}• 停止服务:${NC}     docker-compose -f $COMPOSE_FILE down"
    echo -e "  ${YELLOW}• 重启服务:${NC}     docker-compose -f $COMPOSE_FILE restart"
    echo -e "  ${YELLOW}• 查看状态:${NC}     docker-compose -f $COMPOSE_FILE ps"
    echo ""
    echo -e "${GREEN}✨ 监控系统已就绪，开始享受全面的观测能力！${NC}"
}

# 停止监控栈
stop_monitoring() {
    print_header "停止监控服务栈"

    cd "$SCRIPT_DIR"

    print_step "停止所有监控服务..."
    docker-compose -f "$COMPOSE_FILE" down

    print_success "监控服务栈已停止"
}

# 清理资源
cleanup_monitoring() {
    print_header "清理监控资源"

    cd "$SCRIPT_DIR"

    print_step "停止并删除所有服务..."
    docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans

    print_step "清理Docker镜像..."
    docker rmi claude-enhancer-monitor:latest claude-enhancer-collector:latest 2>/dev/null || true

    print_step "清理数据卷..."
    docker volume prune -f

    print_success "监控资源清理完成"
}

# 查看日志
view_logs() {
    print_header "查看监控服务日志"

    cd "$SCRIPT_DIR"

    local service="${1:-}"

    if [ -z "$service" ]; then
        print_status "显示所有服务日志 (Ctrl+C退出):"
        docker-compose -f "$COMPOSE_FILE" logs -f
    else
        print_status "显示 $service 服务日志 (Ctrl+C退出):"
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    fi
}

# 显示状态
show_status() {
    print_header "监控服务状态"

    cd "$SCRIPT_DIR"

    # 显示Docker Compose状态
    print_step "Docker Compose服务状态:"
    docker-compose -f "$COMPOSE_FILE" ps

    echo ""

    # 显示端口监听状态
    print_step "端口监听状态:"
    local ports=(3001 8091 9090 9091 9093 9100 9115 3100 8080)
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} 端口 $port 正在监听"
        else
            echo -e "  ${RED}✗${NC} 端口 $port 未监听"
        fi
    done

    echo ""

    # 显示健康检查状态
    print_step "服务健康检查:"
    local endpoints=(
        "http://localhost:8091/health|Claude Enhancer Monitor"
        "http://localhost:9090/-/healthy|Prometheus"
        "http://localhost:3001/api/health|Grafana"
        "http://localhost:9093/-/healthy|AlertManager"
    )

    for endpoint in "${endpoints[@]}"; do
        local url=$(echo "$endpoint" | cut -d'|' -f1)
        local name=$(echo "$endpoint" | cut -d'|' -f2)

        if curl -s -f "$url" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $name 健康"
        else
            echo -e "  ${RED}✗${NC} $name 不健康"
        fi
    done
}

# 生成性能报告
generate_report() {
    print_header "生成监控性能报告"

    cd "$SCRIPT_DIR"

    local report_file="$PROJECT_ROOT/.claude/reports/monitoring_report_$(date +%Y%m%d_%H%M%S).html"
    mkdir -p "$(dirname "$report_file")"

    # 调用监控API生成报告
    if curl -s http://localhost:8091/api/report > "$report_file" 2>/dev/null; then
        print_success "报告已生成: $report_file"
    else
        print_error "报告生成失败，请检查监控服务是否运行"
    fi
}

# 显示帮助
show_help() {
    echo "Claude Enhancer 监控系统部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  deploy         部署完整监控栈"
    echo "  start          启动监控服务"
    echo "  stop           停止监控服务"
    echo "  restart        重启监控服务"
    echo "  status         查看服务状态"
    echo "  logs [service] 查看服务日志"
    echo "  cleanup        清理所有资源"
    echo "  report         生成性能报告"
    echo "  info           显示服务信息"
    echo "  help           显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 deploy      # 一键部署监控系统"
    echo "  $0 logs        # 查看所有服务日志"
    echo "  $0 logs grafana# 查看Grafana日志"
    echo "  $0 status      # 查看服务状态"
}

# 主函数
main() {
    local command="${1:-deploy}"

    case "$command" in
        deploy)
            check_dependencies
            setup_directories
            generate_configs
            build_images
            start_monitoring
            show_service_info
            ;;
        start)
            start_monitoring
            show_service_info
            ;;
        stop)
            stop_monitoring
            ;;
        restart)
            stop_monitoring
            sleep 5
            start_monitoring
            ;;
        status)
            show_status
            ;;
        logs)
            view_logs "$2"
            ;;
        cleanup)
            cleanup_monitoring
            ;;
        report)
            generate_report
            ;;
        info)
            show_service_info
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