#!/bin/bash
# =============================================================================
# Claude Enhancer 5.1 部署前检查清单
# 交互式检查清单，确保所有部署前准备工作完成
# =============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 检查清单状态
declare -A checklist_status
total_items=0
completed_items=0

# 显示标题
show_header() {
    clear
    echo -e "${PURPLE}"
    echo "  ╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "  ║                  Claude Enhancer 5.1 部署前检查清单                         ║"
    echo "  ║                    Pre-Deployment Checklist                                 ║"
    echo "  ╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"

    local completion_rate=0
    if (( total_items > 0 )); then
        completion_rate=$(( completed_items * 100 / total_items ))
    fi

    echo -e "${BLUE}进度: $completed_items/$total_items 项完成 (${completion_rate}%)${NC}"
    echo -e "${BLUE}$(printf '█%.0s' $(seq 1 $((completion_rate/2))))$(printf '░%.0s' $(seq 1 $((50-completion_rate/2))))${NC}"
    echo
}

# 检查项目函数
check_item() {
    local category="$1"
    local item="$2"
    local description="$3"
    local check_command="${4:-}"

    local key="${category}.${item}"
    ((total_items++))

    # 自动检查（如果提供了检查命令）
    local auto_status=""
    if [[ -n "$check_command" ]]; then
        if eval "$check_command" &> /dev/null; then
            auto_status=" ${GREEN}[自动检测: ✓]${NC}"
            checklist_status["$key"]="completed"
            ((completed_items++))
        else
            auto_status=" ${YELLOW}[自动检测: ✗]${NC}"
        fi
    fi

    # 显示检查项
    local status_icon="❌"
    local status_color="$RED"
    if [[ "${checklist_status[$key]:-}" == "completed" ]]; then
        status_icon="✅"
        status_color="$GREEN"
    fi

    echo -e "${status_color}$status_icon${NC} $description$auto_status"

    # 如果未自动检测通过，询问用户
    if [[ "${checklist_status[$key]:-}" != "completed" ]]; then
        echo -n "   已完成此项? (y/n/s[跳过]/h[帮助]): "
        read -r response

        case "$response" in
            y|Y)
                checklist_status["$key"]="completed"
                ((completed_items++))
                echo -e "   ${GREEN}✓ 已标记为完成${NC}"
                ;;
            s|S)
                checklist_status["$key"]="skipped"
                echo -e "   ${YELLOW}⚠ 已跳过${NC}"
                ;;
            h|H)
                show_help_for_item "$category" "$item"
                check_item "$category" "$item" "$description" "$check_command"
                return
                ;;
            *)
                echo -e "   ${RED}✗ 未完成${NC}"
                ;;
        esac
    fi

    echo
    sleep 0.5
}

# 显示帮助信息
show_help_for_item() {
    local category="$1"
    local item="$2"

    echo -e "\n${BLUE}━━━ 帮助信息 ━━━${NC}"

    case "$category.$item" in
        "env.production_config")
            cat << EOF
创建生产环境配置文件步骤:
1. 复制模板文件: cp .env.production.template .env.production
2. 编辑配置文件: vim .env.production
3. 填入实际的密码、密钥和配置信息
4. 确保所有 "YOUR_" 开头的值都已替换

关键配置项:
- DB_PASSWORD: 数据库密码
- REDIS_PASSWORD: Redis密码
- JWT_ACCESS_SECRET: JWT访问令牌密钥
- JWT_REFRESH_SECRET: JWT刷新令牌密钥
- SECRET_KEY: 应用密钥
- DOMAIN: 生产环境域名
EOF
            ;;
        "security.ssl_certificates")
            cat << EOF
SSL证书配置步骤:
1. 获取SSL证书（Let's Encrypt或商业证书）
2. 将证书文件放置在 ssl/ 目录下
3. 确保nginx配置文件引用正确的证书路径
4. 测试证书有效性: openssl x509 -in cert.pem -text -noout

证书文件结构:
ssl/
├── cert.pem      # 证书文件
├── privkey.pem   # 私钥文件
└── chain.pem     # 证书链文件
EOF
            ;;
        "monitoring.alerting")
            cat << EOF
告警配置步骤:
1. 配置AlertManager: deployment/monitoring/alertmanager.yml
2. 设置通知渠道（邮件、Slack、PagerDuty）
3. 验证告警规则: deployment/monitoring/alert_rules.yml
4. 测试告警发送: 手动触发测试告警

主要告警类型:
- 应用健康状态
- 系统资源使用
- 数据库连接
- 安全事件
EOF
            ;;
        "backup.strategy")
            cat << EOF
备份策略配置:
1. 数据库备份: 配置自动备份计划任务
2. 应用数据备份: 配置文件和上传文件备份
3. 配置备份: 环境配置文件备份
4. 验证备份恢复: 测试备份文件可以正常恢复

备份计划建议:
- 数据库: 每天全量备份 + 增量备份
- 应用数据: 每周备份
- 配置文件: 每次变更后备份
EOF
            ;;
        *)
            echo "暂无此项目的详细帮助信息"
            ;;
    esac

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━${NC}\n"
    echo -n "按Enter键继续..."
    read -r
}

# 执行检查清单
run_checklist() {
    show_header

    echo -e "${PURPLE}━━━ 1. 环境配置检查 ━━━${NC}"
    check_item "env" "production_config" "生产环境配置文件 (.env.production) 已创建并配置" "[[ -f .env.production ]]"
    check_item "env" "database_config" "数据库连接配置正确" ""
    check_item "env" "redis_config" "Redis连接配置正确" ""
    check_item "env" "secrets" "所有密钥和密码已设置为强随机值" ""
    check_item "env" "domain" "生产域名配置正确" ""

    show_header
    echo -e "${PURPLE}━━━ 2. 基础设施检查 ━━━${NC}"
    check_item "infra" "docker" "Docker环境运行正常" "docker info"
    check_item "infra" "kubernetes" "Kubernetes集群可访问 (如使用K8s)" "kubectl cluster-info"
    check_item "infra" "network" "网络端口可用 (8080, 5432, 6379)" ""
    check_item "infra" "storage" "存储空间充足 (>20GB)" "df -h . | awk 'NR==2 {print \$4}' | grep -E '^[2-9][0-9]+G|^[0-9]+[0-9]G|^[0-9]+T'"
    check_item "infra" "resources" "系统资源满足要求 (>=4GB RAM, >=2 CPU)" ""

    show_header
    echo -e "${PURPLE}━━━ 3. 安全配置检查 ━━━${NC}"
    check_item "security" "ssl_certificates" "SSL证书已配置" "[[ -f ssl/cert.pem && -f ssl/privkey.pem ]]"
    check_item "security" "firewall" "防火墙规则已配置" ""
    check_item "security" "access_control" "访问控制策略已设置" ""
    check_item "security" "secrets_management" "敏感信息安全存储" ""
    check_item "security" "vulnerability_scan" "安全漏洞扫描已完成" ""

    show_header
    echo -e "${PURPLE}━━━ 4. 监控和告警检查 ━━━${NC}"
    check_item "monitoring" "prometheus" "Prometheus配置正确" "[[ -f deployment/monitoring/prometheus.yml ]]"
    check_item "monitoring" "grafana" "Grafana仪表板已配置" ""
    check_item "monitoring" "alerting" "告警规则和通知已配置" "[[ -f deployment/monitoring/alert_rules.yml ]]"
    check_item "monitoring" "logging" "日志收集配置正确" ""
    check_item "monitoring" "health_checks" "健康检查端点已验证" ""

    show_header
    echo -e "${PURPLE}━━━ 5. 数据和备份检查 ━━━${NC}"
    check_item "data" "database_ready" "数据库已初始化并可连接" ""
    check_item "data" "redis_ready" "Redis已配置并可连接" ""
    check_item "backup" "strategy" "备份策略已制定和测试" ""
    check_item "backup" "restore_test" "数据恢复流程已验证" ""
    check_item "backup" "retention" "备份保留策略已配置" ""

    show_header
    echo -e "${PURPLE}━━━ 6. 应用配置检查 ━━━${NC}"
    check_item "app" "claude_enhancer" "Claude Enhancer系统配置完整" "[[ -d .claude ]]"
    check_item "app" "agents" "56个Agent配置文件存在" ""
    check_item "app" "hooks" "Git Hooks已安装并测试" "[[ -f .git/hooks/pre-commit ]]"
    check_item "app" "workflows" "8-Phase工作流配置正确" "[[ -f .phase/current ]]"
    check_item "app" "quality_gates" "质量网关配置启用" ""

    show_header
    echo -e "${PURPLE}━━━ 7. 部署脚本检查 ━━━${NC}"
    check_item "deploy" "scripts" "部署脚本存在且可执行" "[[ -x deploy.sh ]]"
    check_item "deploy" "blue_green" "蓝绿部署脚本准备就绪" "[[ -x deployment/scripts/deploy-blue-green.sh ]]"
    check_item "deploy" "rollback" "回滚脚本准备就绪" "[[ -x deployment/scripts/rollback.sh ]]"
    check_item "deploy" "validation" "部署验证脚本可用" "[[ -x deployment/scripts/deployment-validator.sh ]]"
    check_item "deploy" "docker_images" "Docker镜像构建测试通过" ""

    show_header
    echo -e "${PURPLE}━━━ 8. 团队准备检查 ━━━${NC}"
    check_item "team" "contact_info" "应急联系人信息已更新" ""
    check_item "team" "deployment_window" "部署时间窗口已确认" ""
    check_item "team" "rollback_plan" "回滚计划已制定" ""
    check_item "team" "notification" "用户通知计划已准备" ""
    check_item "team" "monitoring_duty" "部署期间监控值班已安排" ""

    show_header
    echo -e "${PURPLE}━━━ 9. 最终确认检查 ━━━${NC}"
    check_item "final" "code_review" "代码审查已完成" ""
    check_item "final" "testing" "全面测试已通过 (单元、集成、E2E)" ""
    check_item "final" "performance" "性能测试已通过" ""
    check_item "final" "security_review" "安全评审已通过" ""
    check_item "final" "documentation" "文档已更新" ""
}

# 生成检查报告
generate_report() {
    local report_file="pre_deployment_checklist_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" << EOF
# Claude Enhancer 5.1 部署前检查清单报告

**生成时间**: $(date)
**检查完成度**: $completed_items/$total_items 项

## 检查结果摘要

EOF

    local skipped_items=0
    local pending_items=0

    for key in "${!checklist_status[@]}"; do
        local category="${key%%.*}"
        local item="${key#*.}"
        local status="${checklist_status[$key]}"

        case "$status" in
            "completed")
                echo "- ✅ **$category.$item**: 已完成" >> "$report_file"
                ;;
            "skipped")
                echo "- ⚠️ **$category.$item**: 已跳过" >> "$report_file"
                ((skipped_items++))
                ;;
            *)
                echo "- ❌ **$category.$item**: 待完成" >> "$report_file"
                ((pending_items++))
                ;;
        esac
    done

    cat >> "$report_file" << EOF

## 统计信息

- **总计检查项**: $total_items
- **已完成项**: $completed_items
- **已跳过项**: $skipped_items
- **待完成项**: $pending_items
- **完成率**: $(( completed_items * 100 / total_items ))%

## 部署建议

EOF

    if (( pending_items == 0 && skipped_items <= 2 )); then
        echo "✅ **建议**: 可以执行部署" >> "$report_file"
    elif (( pending_items <= 3 )); then
        echo "⚠️ **建议**: 建议完成剩余项目后再部署" >> "$report_file"
    else
        echo "❌ **建议**: 不建议现在部署，请完成更多检查项" >> "$report_file"
    fi

    cat >> "$report_file" << EOF

## 下一步行动

1. 完成所有待完成的检查项
2. 处理已跳过的重要项目
3. 执行部署验证脚本
4. 开始正式部署

---
*此报告由部署前检查清单工具生成*
EOF

    echo "检查报告已生成: $report_file"
}

# 显示最终总结
show_summary() {
    show_header

    echo -e "${PURPLE}━━━ 检查清单完成 ━━━${NC}\n"

    local completion_rate=$(( completed_items * 100 / total_items ))
    local skipped_count=0
    local pending_count=0

    for status in "${checklist_status[@]}"; do
        case "$status" in
            "skipped") ((skipped_count++)) ;;
            "") ((pending_count++)) ;;
        esac
    done

    echo -e "📊 **检查结果**:"
    echo -e "   ✅ 已完成: ${GREEN}$completed_items${NC}"
    echo -e "   ⚠️  已跳过: ${YELLOW}$skipped_count${NC}"
    echo -e "   ❌ 待完成: ${RED}$pending_count${NC}"
    echo -e "   📈 完成率: ${BLUE}${completion_rate}%${NC}\n"

    if (( completion_rate >= 90 && pending_count == 0 )); then
        echo -e "${GREEN}🎉 恭喜！Claude Enhancer 5.1 已准备好部署！${NC}"
        echo -e "\n建议下一步操作:"
        echo -e "1. 运行部署验证脚本: ${BLUE}./deployment/scripts/deployment-validator.sh${NC}"
        echo -e "2. 执行生产部署: ${BLUE}./deployment/scripts/deploy-production.sh${NC}"
    elif (( completion_rate >= 80 )); then
        echo -e "${YELLOW}⚠️ Claude Enhancer 5.1 基本准备就绪，但建议完成剩余项目${NC}"
        echo -e "\n请完成以下关键项目后再部署"
    else
        echo -e "${RED}❌ Claude Enhancer 5.1 尚未准备好部署${NC}"
        echo -e "\n请完成更多检查项目后再尝试部署"
    fi

    echo
    read -p "是否生成详细检查报告? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        generate_report
    fi

    echo -e "\n感谢使用 Claude Enhancer 5.1 部署前检查清单！"
}

# 主函数
main() {
    # 检查是否在正确的目录
    if [[ ! -f "Dockerfile" ]] || [[ ! -d ".claude" ]]; then
        echo -e "${RED}错误: 请在Claude Enhancer项目根目录下运行此脚本${NC}"
        exit 1
    fi

    # 运行检查清单
    run_checklist

    # 显示总结
    show_summary
}

# 执行主函数
main "$@"