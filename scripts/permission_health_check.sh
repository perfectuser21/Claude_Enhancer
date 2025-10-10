#!/usr/bin/env bash
# Claude Enhancer 5.3 - 权限健康检查系统
# 持续监控关键文件权限状态

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BLUE='\033[0;34m'
NC='\033[0m'

# 解析命令行参数
QUIET_MODE=false
AUTO_FIX=false
CONTINUOUS_MODE=false
CHECK_INTERVAL=300  # 5分钟

while [[ $# -gt 0 ]]; do
    case $1 in
        --quiet|-q)
            QUIET_MODE=true
            shift
            ;;
        --auto-fix|-f)
            AUTO_FIX=true
            shift
            ;;
        --continuous|-c)
            CONTINUOUS_MODE=true
            shift
            ;;
        --interval|-i)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        --help|-h)
            echo "权限健康检查系统"
            echo ""
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -q, --quiet       静默模式，只输出错误"
            echo "  -f, --auto-fix    自动修复发现的权限问题"
            echo "  -c, --continuous  持续监控模式"
            echo "  -i, --interval N  检查间隔（秒，默认300）"
            echo "  -h, --help        显示此帮助信息"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 项目根目录
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
LOG_DIR="$PROJECT_ROOT/.workflow/logs"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 日志文件
HEALTH_LOG="$LOG_DIR/permission_health.log"
ALERT_LOG="$LOG_DIR/permission_alerts.log"

# 记录日志函数
log() {
    local level="$1"
    shift
    echo "$(date +'%Y-%m-%d %H:%M:%S') [$level] $*" >> "$HEALTH_LOG"
    if [ "$QUIET_MODE" = false ] || [ "$level" = "ERROR" ] || [ "$level" = "CRITICAL" ]; then
        echo -e "$*"
    fi
}

# 发送告警函数
alert() {
    local message="$1"
    echo "$(date +'%Y-%m-%d %H:%M:%S') [ALERT] $message" >> "$ALERT_LOG"
    log "CRITICAL" "${RED}🚨 ALERT: $message${NC}"
}

# 权限检查函数
check_permissions() {
    local issues=0
    local critical_issues=0

    if [ "$QUIET_MODE" = false ]; then
        echo -e "${CYAN}🔍 权限健康检查 - $(date)${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi

    # 定义关键文件列表
    local -A CRITICAL_FILES=(
        ["$HOOKS_DIR/pre-commit"]="Git pre-commit hook"
        ["$HOOKS_DIR/commit-msg"]="Git commit-msg hook"
        ["$HOOKS_DIR/pre-push"]="Git pre-push hook"
        ["$PROJECT_ROOT/scripts/fix_permissions.sh"]="权限修复脚本"
        ["$PROJECT_ROOT/scripts/permission_health_check.sh"]="权限健康检查脚本"
    )

    local -A IMPORTANT_FILES=(
        ["$HOOKS_DIR/post-merge"]="Git post-merge hook"
        ["$HOOKS_DIR/post-commit"]="Git post-commit hook"
        ["$PROJECT_ROOT/.claude/install.sh"]="Claude Enhancer安装脚本"
        ["$PROJECT_ROOT/run_e2e_tests.sh"]="E2E测试脚本"
        ["$PROJECT_ROOT/comprehensive_performance_test.sh"]="性能测试脚本"
    )

    # 检查关键文件权限
    log "INFO" "检查关键文件权限..."
    for file in "${!CRITICAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            if [ ! -x "$file" ]; then
                alert "${CRITICAL_FILES[$file]} 缺少执行权限: $file"
                ((critical_issues++))
                ((issues++))
            elif [ "$QUIET_MODE" = false ]; then
                log "INFO" "${GREEN}✓ ${CRITICAL_FILES[$file]} 权限正常${NC}"
            fi
        else
            log "WARN" "${YELLOW}⚠️ ${CRITICAL_FILES[$file]} 不存在: $file${NC}"
        fi
    done

    # 检查重要文件权限
    log "INFO" "检查重要文件权限..."
    for file in "${!IMPORTANT_FILES[@]}"; do
        if [ -f "$file" ]; then
            if [ ! -x "$file" ]; then
                log "WARN" "${YELLOW}⚠️ ${IMPORTANT_FILES[$file]} 缺少执行权限: $file${NC}"
                ((issues++))
            elif [ "$QUIET_MODE" = false ]; then
                log "INFO" "${GREEN}✓ ${IMPORTANT_FILES[$file]} 权限正常${NC}"
            fi
        fi
    done

    # 检查.sh文件权限
    local sh_issues=0
    while IFS= read -r -d '' file; do
        if [ ! -x "$file" ]; then
            log "WARN" "${YELLOW}⚠️ Shell脚本缺少执行权限: $file${NC}"
            ((sh_issues++))
            ((issues++))
        fi
    done < <(find "$PROJECT_ROOT" -name "*.sh" -type f ! -path "*/.git/*" ! -perm -u+x -print0 2>/dev/null)

    if [ $sh_issues -eq 0 ] && [ "$QUIET_MODE" = false ]; then
        log "INFO" "${GREEN}✓ 所有Shell脚本权限正常${NC}"
    fi

    # 生成健康报告
    if [ "$QUIET_MODE" = false ]; then
        echo -e "\n${MAGENTA}📊 健康报告${NC}"
        echo "────────────────────────"
        echo "总问题数: $issues"
        echo "关键问题: $critical_issues"
        echo "Shell脚本问题: $sh_issues"
    fi

    # 自动修复（如果启用）
    if [ "$AUTO_FIX" = true ] && [ $issues -gt 0 ]; then
        log "INFO" "${BLUE}🔧 自动修复模式启用，开始修复...${NC}"
        if [ -x "$PROJECT_ROOT/scripts/fix_permissions.sh" ]; then
            bash "$PROJECT_ROOT/scripts/fix_permissions.sh"
        else
            log "ERROR" "${RED}❌ 权限修复脚本不可执行${NC}"
        fi
    fi

    # 返回状态
    if [ $critical_issues -gt 0 ]; then
        return 2  # 关键错误
    elif [ $issues -gt 0 ]; then
        return 1  # 普通错误
    else
        return 0  # 正常
    fi
}

# 持续监控函数
continuous_monitor() {
    log "INFO" "${CYAN}🔄 启动持续监控模式（间隔: ${CHECK_INTERVAL}秒）${NC}"

    while true; do
        if ! check_permissions; then
            local exit_code=$?
            if [ $exit_code -eq 2 ]; then
                alert "发现关键权限问题，建议立即处理"
            fi
        fi

        sleep "$CHECK_INTERVAL"
    done
}

# Git hooks状态检查
check_git_hooks_status() {
    local hooks_ok=true

    if [ "$QUIET_MODE" = false ]; then
        echo -e "\n${BLUE}🔗 Git Hooks状态检查${NC}"
        echo "────────────────────────"
    fi

    # 检查hooks是否能够拦截提交
    local test_result
    if test_result=$(git config --get core.hooksPath 2>/dev/null); then
        log "INFO" "自定义hooks路径: $test_result"
    fi

    # 检查每个hook的SHA256以验证完整性
    local critical_hooks=("pre-commit" "commit-msg" "pre-push")
    for hook in "${critical_hooks[@]}"; do
        local hook_path="$HOOKS_DIR/$hook"
        if [ -f "$hook_path" ]; then
            if [ -x "$hook_path" ]; then
                # 检查hook文件大小（太小可能被破坏）
                local size
                size=$(stat -c%s "$hook_path" 2>/dev/null || echo "0")
                if [ "$size" -lt 100 ]; then
                    log "WARN" "${YELLOW}⚠️ $hook 文件过小，可能被损坏${NC}"
                    hooks_ok=false
                fi

                # 检查hook是否包含必要的内容
                if ! grep -q "set -euo pipefail" "$hook_path" 2>/dev/null; then
                    log "WARN" "${YELLOW}⚠️ $hook 缺少错误处理机制${NC}"
                fi

                if [ "$QUIET_MODE" = false ]; then
                    log "INFO" "${GREEN}✓ $hook 状态正常（大小: ${size}字节）${NC}"
                fi
            else
                log "ERROR" "${RED}❌ $hook 不可执行${NC}"
                hooks_ok=false
            fi
        else
            log "ERROR" "${RED}❌ $hook 不存在${NC}"
            hooks_ok=false
        fi
    done

    if [ "$hooks_ok" = true ] && [ "$QUIET_MODE" = false ]; then
        log "INFO" "${GREEN}✅ Git hooks状态良好${NC}"
    fi

    return $([ "$hooks_ok" = true ] && echo 0 || echo 1)
}

# 权限历史分析
analyze_permission_history() {
    if [ "$QUIET_MODE" = false ]; then
        echo -e "\n${MAGENTA}📈 权限历史分析${NC}"
        echo "────────────────────────"
    fi

    if [ -f "$HEALTH_LOG" ]; then
        local total_checks
        total_checks=$(grep -c "\[INFO\] 检查关键文件权限" "$HEALTH_LOG" 2>/dev/null || echo "0")
        local error_count
        error_count=$(grep -c "\[ERROR\]" "$HEALTH_LOG" 2>/dev/null || echo "0")
        local alert_count
        alert_count=$(grep -c "\[ALERT\]" "$ALERT_LOG" 2>/dev/null || echo "0")

        if [ "$QUIET_MODE" = false ]; then
            echo "总检查次数: $total_checks"
            echo "错误次数: $error_count"
            echo "告警次数: $alert_count"

            if [ "$total_checks" -gt 0 ]; then
                local success_rate
                success_rate=$(( (total_checks - error_count) * 100 / total_checks ))
                echo "成功率: ${success_rate}%"
            fi
        fi

        # 显示最近的告警
        if [ "$alert_count" -gt 0 ] && [ -f "$ALERT_LOG" ]; then
            echo -e "\n最近的告警:"
            tail -3 "$ALERT_LOG" 2>/dev/null | sed 's/^/  /'
        fi
    else
        if [ "$QUIET_MODE" = false ]; then
            echo "暂无历史数据"
        fi
    fi
}

# 主执行逻辑
main() {
    # 确保脚本本身有执行权限
    if [ ! -x "$0" ]; then
        chmod +x "$0" 2>/dev/null || {
            echo "ERROR: 无法修复自身权限" >&2
            exit 1
        }
    fi

    if [ "$CONTINUOUS_MODE" = true ]; then
        continuous_monitor
    else
        # 单次检查
        local exit_code=0

        check_permissions || exit_code=$?
        check_git_hooks_status || exit_code=$((exit_code > 0 ? exit_code : 1))
        analyze_permission_history

        if [ "$QUIET_MODE" = false ]; then
            echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            case $exit_code in
                0)
                    echo -e "${GREEN}✅ 权限健康检查通过${NC}"
                    ;;
                1)
                    echo -e "${YELLOW}⚠️ 发现权限问题，建议修复${NC}"
                    ;;
                2)
                    echo -e "${RED}❌ 发现关键权限问题，需要立即修复${NC}"
                    ;;
            esac
        fi

        exit $exit_code
    fi
}

# 处理中断信号
trap 'log "INFO" "权限健康检查被中断"; exit 130' INT TERM

# 启动主程序
main "$@"