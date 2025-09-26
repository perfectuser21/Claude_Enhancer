#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 部署验证脚本
# 全面验证部署准备状态和系统健康度
# =============================================================================

set -euo pipefail

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${PROJECT_ROOT}/deployment_validation_report_${TIMESTAMP}.json"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 验证结果存储
declare -A VALIDATION_RESULTS
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✅ PASS]${NC} $1"
    ((PASSED_CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}[⚠️  WARN]${NC} $1"
    ((WARNING_CHECKS++))
}

log_error() {
    echo -e "${RED}[❌ FAIL]${NC} $1"
    ((FAILED_CHECKS++))
}

log_header() {
    echo -e "${PURPLE}[━━━ $1 ━━━]${NC}"
}

# 记录验证结果
record_result() {
    local category=$1
    local check_name=$2
    local status=$3
    local message=$4

    VALIDATION_RESULTS["${category}.${check_name}"]="$status:$message"
    ((TOTAL_CHECKS++))
}

# 检查系统环境
check_system_environment() {
    log_header "系统环境检查"

    # Docker检查
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        log_success "Docker已安装 (版本: $docker_version)"
        record_result "system" "docker" "PASS" "Docker版本$docker_version"

        # Docker服务状态
        if docker info &> /dev/null; then
            log_success "Docker服务运行正常"
            record_result "system" "docker_service" "PASS" "Docker daemon运行中"
        else
            log_error "Docker服务未运行"
            record_result "system" "docker_service" "FAIL" "Docker daemon未运行"
        fi
    else
        log_error "Docker未安装"
        record_result "system" "docker" "FAIL" "Docker未安装"
    fi

    # Docker Compose检查
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        if command -v docker-compose &> /dev/null; then
            local compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        else
            local compose_version=$(docker compose version --short)
        fi
        log_success "Docker Compose已安装 (版本: $compose_version)"
        record_result "system" "docker_compose" "PASS" "Docker Compose版本$compose_version"
    else
        log_error "Docker Compose未安装"
        record_result "system" "docker_compose" "FAIL" "Docker Compose未安装"
    fi

    # 系统资源检查
    local total_mem=$(free -h | awk '/^Mem:/ {print $2}')
    local available_mem=$(free -h | awk '/^Mem:/ {print $7}')
    local cpu_cores=$(nproc)

    log_info "系统资源: CPU核心数: $cpu_cores, 总内存: $total_mem, 可用内存: $available_mem"

    if (( cpu_cores >= 2 )); then
        log_success "CPU核心数满足要求 (≥2核)"
        record_result "system" "cpu_cores" "PASS" "${cpu_cores}核心"
    else
        log_warning "CPU核心数不足 (建议≥2核)"
        record_result "system" "cpu_cores" "WARN" "仅${cpu_cores}核心"
    fi

    # 磁盘空间检查
    local disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    log_info "可用磁盘空间: $disk_usage"
    record_result "system" "disk_space" "INFO" "可用空间${disk_usage}"
}

# 检查项目文件结构
check_project_structure() {
    log_header "项目文件结构检查"

    local required_files=(
        "Dockerfile"
        "docker-compose.production.yml"
        "deploy.sh"
        ".env.example"
        "requirements.txt"
        "k8s/deployment.yaml"
    )

    for file in "${required_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            log_success "发现必要文件: $file"
            record_result "structure" "file_${file//\//_}" "PASS" "文件存在"
        else
            log_error "缺少必要文件: $file"
            record_result "structure" "file_${file//\//_}" "FAIL" "文件不存在"
        fi
    done

    # Claude Enhancer特定文件检查
    local claude_files=(
        ".claude/settings.json"
        ".claude/hooks/branch_helper.sh"
        ".claude/hooks/smart_agent_selector.sh"
        ".phase/current"
    )

    for file in "${claude_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            log_success "发现Claude Enhancer文件: $file"
            record_result "claude" "file_${file//\//_}" "PASS" "Claude文件存在"
        else
            log_warning "Claude Enhancer文件缺失: $file"
            record_result "claude" "file_${file//\//_}" "WARN" "Claude文件不存在"
        fi
    done
}

# 检查Docker镜像构建能力
check_docker_build() {
    log_header "Docker镜像构建检查"

    cd "$PROJECT_ROOT"

    # 检查Dockerfile语法
    if docker build --target production --dry-run . &> /dev/null; then
        log_success "Dockerfile语法检查通过"
        record_result "docker" "dockerfile_syntax" "PASS" "语法正确"
    else
        log_error "Dockerfile语法错误"
        record_result "docker" "dockerfile_syntax" "FAIL" "语法错误"
    fi

    # 测试镜像构建（仅构建第一阶段）
    log_info "测试镜像构建能力..."
    if timeout 300 docker build --target python-builder -t claude-enhancer-test:latest . &> /dev/null; then
        log_success "Docker镜像构建测试通过"
        record_result "docker" "build_test" "PASS" "构建成功"

        # 清理测试镜像
        docker rmi claude-enhancer-test:latest &> /dev/null || true
    else
        log_error "Docker镜像构建失败"
        record_result "docker" "build_test" "FAIL" "构建失败"
    fi
}

# 检查配置文件
check_configuration() {
    log_header "配置文件检查"

    # 检查.env.example
    if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
        local env_vars=(
            "DB_NAME" "DB_USER" "DB_PASSWORD"
            "REDIS_PASSWORD"
            "JWT_ACCESS_SECRET" "JWT_REFRESH_SECRET"
            "SECRET_KEY"
        )

        for var in "${env_vars[@]}"; do
            if grep -q "^$var=" "$PROJECT_ROOT/.env.example"; then
                log_success "环境变量模板包含: $var"
                record_result "config" "env_var_$var" "PASS" "环境变量定义"
            else
                log_warning "环境变量模板缺少: $var"
                record_result "config" "env_var_$var" "WARN" "环境变量未定义"
            fi
        done
    fi

    # 检查Docker Compose配置
    if [[ -f "$PROJECT_ROOT/docker-compose.production.yml" ]]; then
        if docker-compose -f "$PROJECT_ROOT/docker-compose.production.yml" config &> /dev/null; then
            log_success "Docker Compose生产配置语法正确"
            record_result "config" "docker_compose_prod" "PASS" "配置语法正确"
        else
            log_error "Docker Compose生产配置语法错误"
            record_result "config" "docker_compose_prod" "FAIL" "配置语法错误"
        fi
    fi

    # 检查Kubernetes配置
    if [[ -f "$PROJECT_ROOT/k8s/deployment.yaml" ]] && command -v kubectl &> /dev/null; then
        if kubectl apply --dry-run=client -f "$PROJECT_ROOT/k8s/deployment.yaml" &> /dev/null; then
            log_success "Kubernetes部署配置语法正确"
            record_result "config" "k8s_deployment" "PASS" "K8s配置语法正确"
        else
            log_warning "Kubernetes部署配置可能有问题"
            record_result "config" "k8s_deployment" "WARN" "K8s配置语法问题"
        fi
    fi
}

# 检查监控配置
check_monitoring() {
    log_header "监控配置检查"

    local monitoring_files=(
        "deployment/monitoring/prometheus.yml"
        "deployment/monitoring/alert_rules.yml"
        "deployment/monitoring/alertmanager.yml"
    )

    for file in "${monitoring_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            log_success "发现监控配置: $file"
            record_result "monitoring" "config_${file//\//_}" "PASS" "监控配置存在"
        else
            log_warning "缺少监控配置: $file"
            record_result "monitoring" "config_${file//\//_}" "WARN" "监控配置缺失"
        fi
    done

    # 检查Prometheus配置语法
    if [[ -f "$PROJECT_ROOT/deployment/monitoring/prometheus.yml" ]] && command -v promtool &> /dev/null; then
        if promtool check config "$PROJECT_ROOT/deployment/monitoring/prometheus.yml" &> /dev/null; then
            log_success "Prometheus配置语法正确"
            record_result "monitoring" "prometheus_syntax" "PASS" "配置语法正确"
        else
            log_warning "Prometheus配置语法问题"
            record_result "monitoring" "prometheus_syntax" "WARN" "配置语法问题"
        fi
    fi
}

# 检查部署脚本
check_deployment_scripts() {
    log_header "部署脚本检查"

    local deployment_scripts=(
        "deploy.sh"
        "deployment/scripts/deploy-blue-green.sh"
        "deployment/scripts/deploy-canary.sh"
        "deployment/scripts/deploy-rolling.sh"
        "deployment/scripts/rollback.sh"
    )

    for script in "${deployment_scripts[@]}"; do
        if [[ -f "$PROJECT_ROOT/$script" ]]; then
            if [[ -x "$PROJECT_ROOT/$script" ]]; then
                log_success "部署脚本可执行: $script"
                record_result "deployment" "script_${script//\//_}" "PASS" "脚本可执行"
            else
                log_warning "部署脚本无执行权限: $script"
                record_result "deployment" "script_${script//\//_}" "WARN" "缺少执行权限"
            fi
        else
            log_error "缺少部署脚本: $script"
            record_result "deployment" "script_${script//\//_}" "FAIL" "脚本不存在"
        fi
    done

    # 测试主部署脚本语法
    if [[ -f "$PROJECT_ROOT/deploy.sh" ]]; then
        if bash -n "$PROJECT_ROOT/deploy.sh" &> /dev/null; then
            log_success "主部署脚本语法正确"
            record_result "deployment" "main_script_syntax" "PASS" "语法正确"
        else
            log_error "主部署脚本语法错误"
            record_result "deployment" "main_script_syntax" "FAIL" "语法错误"
        fi
    fi
}

# 检查安全配置
check_security() {
    log_header "安全配置检查"

    # 检查Dockerfile安全最佳实践
    if [[ -f "$PROJECT_ROOT/Dockerfile" ]]; then
        local security_checks=0
        local security_passed=0

        # 检查非root用户
        if grep -q "USER.*claude" "$PROJECT_ROOT/Dockerfile"; then
            log_success "Dockerfile使用非root用户"
            ((security_passed++))
        else
            log_warning "Dockerfile应使用非root用户"
        fi
        ((security_checks++))

        # 检查HEALTHCHECK
        if grep -q "HEALTHCHECK" "$PROJECT_ROOT/Dockerfile"; then
            log_success "Dockerfile包含健康检查"
            ((security_passed++))
        else
            log_warning "Dockerfile应包含健康检查"
        fi
        ((security_checks++))

        # 检查apt清理
        if grep -q "rm -rf /var/lib/apt/lists" "$PROJECT_ROOT/Dockerfile"; then
            log_success "Dockerfile正确清理apt缓存"
            ((security_passed++))
        else
            log_warning "Dockerfile应清理apt缓存"
        fi
        ((security_checks++))

        record_result "security" "dockerfile" "INFO" "${security_passed}/${security_checks}项通过"
    fi

    # 检查敏感文件
    local sensitive_patterns=("password" "secret" "key" "token")
    local sensitive_files=0

    for pattern in "${sensitive_patterns[@]}"; do
        if find "$PROJECT_ROOT" -name "*.env" -o -name "*.yaml" -o -name "*.yml" | xargs grep -l "$pattern" 2>/dev/null | grep -v ".example" | head -1 &> /dev/null; then
            ((sensitive_files++))
        fi
    done

    if (( sensitive_files == 0 )); then
        log_success "未发现敏感信息泄露"
        record_result "security" "sensitive_files" "PASS" "无敏感文件"
    else
        log_warning "发现可能包含敏感信息的文件"
        record_result "security" "sensitive_files" "WARN" "${sensitive_files}个可疑文件"
    fi
}

# 检查网络配置
check_networking() {
    log_header "网络配置检查"

    # 检查端口配置
    local required_ports=(8080 5432 6379)

    for port in "${required_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            log_warning "端口 $port 已被占用"
            record_result "network" "port_$port" "WARN" "端口被占用"
        else
            log_success "端口 $port 可用"
            record_result "network" "port_$port" "PASS" "端口可用"
        fi
    done

    # 检查网络连通性
    if ping -c 1 google.com &> /dev/null; then
        log_success "外网连接正常"
        record_result "network" "internet" "PASS" "外网连通"
    else
        log_warning "外网连接可能有问题"
        record_result "network" "internet" "WARN" "外网连接异常"
    fi
}

# 生成验证报告
generate_report() {
    log_header "生成验证报告"

    local overall_status="READY"
    local readiness_percentage=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))

    if (( FAILED_CHECKS > 0 )); then
        overall_status="NOT_READY"
    elif (( WARNING_CHECKS > 5 )); then
        overall_status="READY_WITH_WARNINGS"
    fi

    # 生成JSON报告
    cat > "$REPORT_FILE" <<EOF
{
  "report_generated": "$(date -Iseconds)",
  "claude_enhancer_version": "5.1",
  "validation_summary": {
    "overall_status": "$overall_status",
    "readiness_percentage": $readiness_percentage,
    "total_checks": $TOTAL_CHECKS,
    "passed_checks": $PASSED_CHECKS,
    "failed_checks": $FAILED_CHECKS,
    "warning_checks": $WARNING_CHECKS
  },
  "detailed_results": {
EOF

    local first=true
    for key in "${!VALIDATION_RESULTS[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo "," >> "$REPORT_FILE"
        fi

        local status_msg="${VALIDATION_RESULTS[$key]}"
        local status="${status_msg%%:*}"
        local message="${status_msg#*:}"

        cat >> "$REPORT_FILE" <<EOF
    "$key": {
      "status": "$status",
      "message": "$message"
    }
EOF
    done

    cat >> "$REPORT_FILE" <<EOF
  },
  "recommendations": [
EOF

    local recommendations=()

    if (( FAILED_CHECKS > 0 )); then
        recommendations+=("\"解决所有失败的检查项目\"")
    fi

    if (( WARNING_CHECKS > 0 )); then
        recommendations+=("\"处理警告项目以提高系统稳定性\"")
    fi

    if [[ ! -f "$PROJECT_ROOT/.env.production" ]]; then
        recommendations+=("\"创建生产环境配置文件 .env.production\"")
    fi

    recommendations+=("\"执行完整的端到端测试\"")
    recommendations+=("\"验证监控和告警配置\"")

    for i in "${!recommendations[@]}"; do
        if (( i > 0 )); then
            echo "," >> "$REPORT_FILE"
        fi
        echo "    ${recommendations[$i]}" >> "$REPORT_FILE"
    done

    cat >> "$REPORT_FILE" <<EOF
  ]
}
EOF

    log_success "验证报告已生成: $REPORT_FILE"
}

# 显示验证摘要
show_summary() {
    log_header "验证摘要"

    echo -e "${BLUE}总检查项目: $TOTAL_CHECKS${NC}"
    echo -e "${GREEN}✅ 通过: $PASSED_CHECKS${NC}"
    echo -e "${YELLOW}⚠️  警告: $WARNING_CHECKS${NC}"
    echo -e "${RED}❌ 失败: $FAILED_CHECKS${NC}"

    local readiness_percentage=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))
    echo -e "\n${PURPLE}准备度: $readiness_percentage%${NC}"

    if (( FAILED_CHECKS == 0 && WARNING_CHECKS < 5 )); then
        echo -e "\n${GREEN}🚀 Claude Enhancer 5.1 已准备好部署！${NC}"
        exit 0
    elif (( FAILED_CHECKS == 0 )); then
        echo -e "\n${YELLOW}⚠️ Claude Enhancer 5.1 基本准备就绪，建议处理警告项目${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ Claude Enhancer 5.1 尚未准备好部署，请解决失败项目${NC}"
        exit 1
    fi
}

# 主函数
main() {
    echo -e "${PURPLE}"
    echo "  ╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "  ║                    Claude Enhancer 5.1 部署验证器                           ║"
    echo "  ║                     Deployment Validation System                            ║"
    echo "  ╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"

    log_info "开始验证Claude Enhancer 5.1部署准备状态..."
    log_info "项目目录: $PROJECT_ROOT"

    # 执行所有检查
    check_system_environment
    check_project_structure
    check_docker_build
    check_configuration
    check_monitoring
    check_deployment_scripts
    check_security
    check_networking

    # 生成报告和摘要
    generate_report
    show_summary
}

# 错误处理
trap 'echo -e "${RED}验证过程中断！${NC}"; exit 1' INT TERM

# 执行主函数
main "$@"