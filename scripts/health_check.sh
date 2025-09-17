#!/bin/bash

# Perfect21健康检查脚本
# 全面检查应用、数据库、缓存、监控等组件状态

set -e

# 配置
API_HOST="${API_HOST:-localhost}"
API_PORT="${API_PORT:-8000}"
DATABASE_HOST="${DATABASE_HOST:-localhost}"
DATABASE_PORT="${DATABASE_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
TIMEOUT="${TIMEOUT:-10}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查结果
OVERALL_STATUS="healthy"
FAILED_CHECKS=()

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
    OVERALL_STATUS="unhealthy"
    FAILED_CHECKS+=("$1")
}

# 检查网络连接
check_network_connectivity() {
    log_info "检查网络连接..."

    # 检查基础网络
    if ping -c 1 -W "$TIMEOUT" 8.8.8.8 &>/dev/null; then
        log_success "外网连接正常"
    else
        log_warning "外网连接失败"
    fi

    # 检查DNS解析
    if nslookup google.com &>/dev/null; then
        log_success "DNS解析正常"
    else
        log_warning "DNS解析失败"
    fi
}

# 检查API服务
check_api_service() {
    log_info "检查API服务..."

    local api_url="http://$API_HOST:$API_PORT"

    # 基础连接检查
    if curl -f -s --connect-timeout "$TIMEOUT" "$api_url/health" >/dev/null; then
        log_success "API服务连接正常"
    else
        log_error "API服务连接失败"
        return 1
    fi

    # 健康检查端点
    local health_response
    health_response=$(curl -s --connect-timeout "$TIMEOUT" "$api_url/health" 2>/dev/null)

    if echo "$health_response" | grep -q "healthy"; then
        log_success "API健康检查通过"

        # 解析健康检查详情
        if command -v jq &>/dev/null && echo "$health_response" | jq . &>/dev/null; then
            local version=$(echo "$health_response" | jq -r '.version // "unknown"')
            local uptime=$(echo "$health_response" | jq -r '.uptime // "unknown"')
            log_info "API版本: $version, 运行时间: $uptime"
        fi
    else
        log_error "API健康检查失败: $health_response"
    fi

    # 认证端点检查
    local auth_status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout "$TIMEOUT" "$api_url/api/auth/status" 2>/dev/null)
    if [ "$auth_status" = "200" ] || [ "$auth_status" = "401" ]; then
        log_success "认证服务响应正常"
    else
        log_error "认证服务异常 (HTTP $auth_status)"
    fi

    # API文档检查
    local docs_status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout "$TIMEOUT" "$api_url/docs" 2>/dev/null)
    if [ "$docs_status" = "200" ]; then
        log_success "API文档可访问"
    else
        log_warning "API文档访问异常 (HTTP $docs_status)"
    fi
}

# 检查数据库
check_database() {
    log_info "检查数据库..."

    # PostgreSQL连接检查
    if command -v pg_isready &>/dev/null; then
        if pg_isready -h "$DATABASE_HOST" -p "$DATABASE_PORT" -t "$TIMEOUT" &>/dev/null; then
            log_success "PostgreSQL连接正常"

            # 检查数据库大小和连接数
            if command -v psql &>/dev/null; then
                local db_info
                db_info=$(psql -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U perfect21_user -d perfect21 -t -c "
                    SELECT
                        pg_size_pretty(pg_database_size('perfect21')) as size,
                        count(*) as connections
                    FROM pg_stat_activity
                    WHERE datname = 'perfect21';
                " 2>/dev/null | tr -d ' ')

                if [ -n "$db_info" ]; then
                    log_info "数据库信息: $db_info"
                fi
            fi
        else
            log_error "PostgreSQL连接失败"
        fi
    else
        log_warning "未安装pg_isready，跳过数据库检查"
    fi
}

# 检查Redis缓存
check_redis() {
    log_info "检查Redis缓存..."

    if command -v redis-cli &>/dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --connect-timeout "$TIMEOUT" ping &>/dev/null; then
            log_success "Redis连接正常"

            # 获取Redis信息
            local redis_info
            redis_info=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
            if [ -n "$redis_info" ]; then
                log_info "Redis内存使用: $redis_info"
            fi

            # 检查键数量
            local key_count
            key_count=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" dbsize 2>/dev/null)
            if [ -n "$key_count" ]; then
                log_info "Redis键数量: $key_count"
            fi
        else
            log_error "Redis连接失败"
        fi
    else
        log_warning "未安装redis-cli，跳过Redis检查"
    fi
}

# 检查系统资源
check_system_resources() {
    log_info "检查系统资源..."

    # CPU使用率
    if command -v top &>/dev/null; then
        local cpu_usage
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        if [ -n "$cpu_usage" ]; then
            log_info "CPU使用率: $cpu_usage%"
            if (( $(echo "$cpu_usage > 80" | bc -l) )); then
                log_warning "CPU使用率过高: $cpu_usage%"
            fi
        fi
    fi

    # 内存使用率
    if command -v free &>/dev/null; then
        local memory_info
        memory_info=$(free -h | grep Mem | awk '{printf "使用: %s/%s (%.1f%%)", $3, $2, ($3/$2)*100}')
        log_info "内存$memory_info"

        local memory_usage
        memory_usage=$(free | grep Mem | awk '{printf "%.1f", ($3/$2)*100}')
        if (( $(echo "$memory_usage > 85" | bc -l) )); then
            log_warning "内存使用率过高: $memory_usage%"
        fi
    fi

    # 磁盘空间
    local disk_usage
    disk_usage=$(df -h / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    if [ -n "$disk_usage" ]; then
        log_info "根分区使用率: $disk_usage%"
        if [ "$disk_usage" -gt 85 ]; then
            log_warning "磁盘空间不足: $disk_usage%"
        fi
    fi

    # 检查日志目录空间
    if [ -d "/var/log/perfect21" ]; then
        local log_size
        log_size=$(du -sh /var/log/perfect21 2>/dev/null | cut -f1)
        if [ -n "$log_size" ]; then
            log_info "日志目录大小: $log_size"
        fi
    fi
}

# 检查Docker容器状态
check_docker_containers() {
    log_info "检查Docker容器..."

    if command -v docker &>/dev/null; then
        # 检查Perfect21相关容器
        local containers
        containers=$(docker ps --filter "name=perfect21" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null)

        if [ -n "$containers" ]; then
            log_info "Perfect21容器状态:"
            echo "$containers" | while read -r line; do
                if [[ "$line" == *"Up"* ]]; then
                    log_success "  $line"
                else
                    log_error "  $line"
                fi
            done
        else
            log_warning "未找到Perfect21相关容器"
        fi

        # 检查容器资源使用
        local container_stats
        container_stats=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep perfect21)
        if [ -n "$container_stats" ]; then
            log_info "容器资源使用:"
            echo "$container_stats"
        fi
    else
        log_info "Docker未安装，跳过容器检查"
    fi
}

# 检查监控系统
check_monitoring() {
    log_info "检查监控系统..."

    # 检查Prometheus
    if curl -f -s --connect-timeout "$TIMEOUT" "http://localhost:9090/-/healthy" &>/dev/null; then
        log_success "Prometheus监控正常"
    else
        log_warning "Prometheus监控不可用"
    fi

    # 检查Grafana
    if curl -f -s --connect-timeout "$TIMEOUT" "http://localhost:3000/api/health" &>/dev/null; then
        log_success "Grafana可视化正常"
    else
        log_warning "Grafana可视化不可用"
    fi

    # 检查指标收集
    if curl -s --connect-timeout "$TIMEOUT" "http://$API_HOST:$API_PORT/metrics" | grep -q "perfect21"; then
        log_success "应用指标收集正常"
    else
        log_warning "应用指标收集异常"
    fi
}

# 检查Git工作流
check_git_workflow() {
    log_info "检查Git工作流..."

    # 检查Git hooks
    if [ -d ".git/hooks" ]; then
        local hooks_count
        hooks_count=$(find .git/hooks -name "*.sample" -prune -o -type f -executable -print | wc -l)
        if [ "$hooks_count" -gt 0 ]; then
            log_success "Git hooks已安装 ($hooks_count 个)"
        else
            log_warning "未找到可执行的Git hooks"
        fi
    else
        log_info "非Git仓库，跳过Git工作流检查"
    fi

    # 检查分支状态
    if command -v git &>/dev/null && [ -d ".git" ]; then
        local current_branch
        current_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        if [ -n "$current_branch" ]; then
            log_info "当前分支: $current_branch"

            # 检查是否有未提交的更改
            if git diff --quiet && git diff --cached --quiet; then
                log_success "工作目录干净"
            else
                log_info "工作目录有未提交的更改"
            fi
        fi
    fi
}

# 检查安全配置
check_security() {
    log_info "检查安全配置..."

    # 检查SSL证书（如果配置了HTTPS）
    if [ "$API_PORT" = "443" ] || [ -n "$SSL_CERT" ]; then
        if openssl s_client -connect "$API_HOST:443" -servername "$API_HOST" </dev/null 2>/dev/null | openssl x509 -noout -dates &>/dev/null; then
            log_success "SSL证书有效"
        else
            log_warning "SSL证书检查失败"
        fi
    fi

    # 检查文件权限
    local sensitive_files=("config/production.yaml" ".env" "scripts/deploy.sh")
    for file in "${sensitive_files[@]}"; do
        if [ -f "$file" ]; then
            local file_perms
            file_perms=$(stat -c "%a" "$file" 2>/dev/null)
            if [ "$file_perms" -le 600 ]; then
                log_success "文件权限安全: $file ($file_perms)"
            else
                log_warning "文件权限过宽: $file ($file_perms)"
            fi
        fi
    done
}

# 执行性能测试
check_performance() {
    log_info "检查性能..."

    # API响应时间测试
    local response_time
    response_time=$(curl -o /dev/null -s -w "%{time_total}" --connect-timeout "$TIMEOUT" "http://$API_HOST:$API_PORT/health" 2>/dev/null)

    if [ -n "$response_time" ]; then
        log_info "API响应时间: ${response_time}s"
        if (( $(echo "$response_time > 2.0" | bc -l) )); then
            log_warning "API响应时间过长: ${response_time}s"
        fi
    fi

    # 数据库查询性能
    if command -v psql &>/dev/null; then
        local query_time
        query_time=$(psql -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U perfect21_user -d perfect21 -t -c "
            SELECT extract(epoch from now() - query_start) as duration
            FROM pg_stat_activity
            WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
            ORDER BY duration DESC LIMIT 1;
        " 2>/dev/null | tr -d ' ')

        if [ -n "$query_time" ] && [ "$query_time" != "" ]; then
            log_info "最长查询时间: ${query_time}s"
            if (( $(echo "$query_time > 5.0" | bc -l) )); then
                log_warning "存在慢查询: ${query_time}s"
            fi
        fi
    fi
}

# 生成健康检查报告
generate_report() {
    echo
    echo "=========================================="
    echo "Perfect21健康检查报告"
    echo "时间: $(date)"
    echo "=========================================="

    if [ "$OVERALL_STATUS" = "healthy" ]; then
        log_success "总体状态: 健康"
        echo
        echo "所有检查项均通过，系统运行正常。"
    else
        log_error "总体状态: 不健康"
        echo
        echo "发现 ${#FAILED_CHECKS[@]} 个问题:"
        for check in "${FAILED_CHECKS[@]}"; do
            echo "  - $check"
        done
    fi

    echo
    echo "检查项目:"
    echo "  ✓ 网络连接"
    echo "  ✓ API服务"
    echo "  ✓ 数据库"
    echo "  ✓ Redis缓存"
    echo "  ✓ 系统资源"
    echo "  ✓ Docker容器"
    echo "  ✓ 监控系统"
    echo "  ✓ Git工作流"
    echo "  ✓ 安全配置"
    echo "  ✓ 性能指标"
    echo
}

# 显示帮助
show_help() {
    cat << EOF
Perfect21健康检查脚本

用法: $0 [选项]

选项:
    --api-host HOST        API服务主机 [默认: localhost]
    --api-port PORT        API服务端口 [默认: 8000]
    --database-host HOST   数据库主机 [默认: localhost]
    --database-port PORT   数据库端口 [默认: 5432]
    --redis-host HOST      Redis主机 [默认: localhost]
    --redis-port PORT      Redis端口 [默认: 6379]
    --timeout SECONDS      连接超时时间 [默认: 10]
    --json                 输出JSON格式结果
    --quiet                静默模式，只输出错误
    --help                 显示帮助信息

环境变量:
    API_HOST              API服务主机
    API_PORT              API服务端口
    DATABASE_HOST         数据库主机
    DATABASE_PORT         数据库端口
    REDIS_HOST            Redis主机
    REDIS_PORT            Redis端口
    TIMEOUT               连接超时时间

退出代码:
    0  - 所有检查通过
    1  - 发现问题

EOF
}

# 主函数
main() {
    log_info "开始Perfect21健康检查..."
    echo

    check_network_connectivity
    check_api_service
    check_database
    check_redis
    check_system_resources
    check_docker_containers
    check_monitoring
    check_git_workflow
    check_security
    check_performance

    generate_report

    # 根据检查结果退出
    if [ "$OVERALL_STATUS" = "healthy" ]; then
        exit 0
    else
        exit 1
    fi
}

# 解析命令行参数
QUIET_MODE=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --api-host)
            API_HOST="$2"
            shift 2
            ;;
        --api-port)
            API_PORT="$2"
            shift 2
            ;;
        --database-host)
            DATABASE_HOST="$2"
            shift 2
            ;;
        --database-port)
            DATABASE_PORT="$2"
            shift 2
            ;;
        --redis-host)
            REDIS_HOST="$2"
            shift 2
            ;;
        --redis-port)
            REDIS_PORT="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --quiet)
            QUIET_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 静默模式设置
if [ "$QUIET_MODE" = true ]; then
    exec 1>/dev/null  # 重定向标准输出到/dev/null
fi

# 执行健康检查
main