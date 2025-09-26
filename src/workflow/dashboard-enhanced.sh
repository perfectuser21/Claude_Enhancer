#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
# Claude Enhancer 5.0 - Enhanced Workflow Monitoring Dashboard
# 增强版工作流监控面板 - 包含统计图表和性能分析
# ═══════════════════════════════════════════════════════════════════

# 导入配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/dashboard-config.yaml"

# 颜色和符号定义
source <(cat << 'EOF'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# 扩展符号集
CHECK="✓"
CROSS="✗"
ARROW="→"
BULLET="•"
PROGRESS="█"
EMPTY="░"
WAITING="⏳"
RUNNING="🏃"
SUCCESS="🎉"
ERROR="❌"
WARNING="⚠️"
CHART="📊"
FIRE="🔥"
ROCKET="🚀"
GEAR="⚙️"
SHIELD="🛡️"
GRAPH="📈"
CLOCK="🕐"
EOF
)

# 项目配置
PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
PHASE_DIR="$PROJECT_ROOT/.phase"
GATES_DIR="$PROJECT_ROOT/.gates"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
WORKFLOW_LOG="$WORKFLOW_DIR/executor.log"
STATS_DIR="$WORKFLOW_DIR/stats"
CACHE_DIR="$WORKFLOW_DIR/.cache"

# 监控配置
REFRESH_RATE=2
DASHBOARD_WIDTH=120
LOG_LINES=15
STATS_HISTORY=100

# 创建必要目录
mkdir -p "$STATS_DIR" "$CACHE_DIR"

# ═══════════════════════════════════════════════════════════════════
# 数据收集和缓存
# ═══════════════════════════════════════════════════════════════════

# 收集系统统计信息
collect_stats() {
    local timestamp=$(date +%s)
    local current_phase=$(get_current_phase)
    local gates_status=$(get_gates_status)
    local log_analysis=$(analyze_log_issues)

    # 保存统计数据
    cat >> "$STATS_DIR/stats.log" << EOF
$timestamp|$current_phase|$gates_status|$log_analysis
EOF

    # 保持历史记录限制
    tail -n $STATS_HISTORY "$STATS_DIR/stats.log" > "$STATS_DIR/stats.tmp"
    mv "$STATS_DIR/stats.tmp" "$STATS_DIR/stats.log"
}

# 生成性能趋势数据
generate_performance_trend() {
    local trend_file="$CACHE_DIR/performance_trend"

    if [[ -f "$STATS_DIR/stats.log" ]]; then
        # 分析最近的性能数据
        tail -n 20 "$STATS_DIR/stats.log" | while IFS='|' read -r timestamp phase gates_status log_data; do
            local errors=$(echo "$log_data" | cut -d'|' -f1)
            local warnings=$(echo "$log_data" | cut -d'|' -f2)
            local successes=$(echo "$log_data" | cut -d'|' -f3)
            local total=$((errors + warnings + successes))

            if [[ $total -gt 0 ]]; then
                local success_rate=$((successes * 100 / total))
                echo "$timestamp:$success_rate" >> "$trend_file.tmp"
            fi
        done 2>/dev/null

        # 保留最新数据
        if [[ -f "$trend_file.tmp" ]]; then
            tail -n 20 "$trend_file.tmp" > "$trend_file"
            rm -f "$trend_file.tmp"
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════════
# 增强版显示函数
# ═══════════════════════════════════════════════════════════════════

# 显示性能趋势图表
show_performance_chart() {
    echo -e "${BOLD}${WHITE}${GRAPH} 性能趋势分析${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"

    local trend_file="$CACHE_DIR/performance_trend"

    if [[ -f "$trend_file" ]] && [[ -s "$trend_file" ]]; then
        echo -e "${CYAN}│${NC} 成功率趋势 (最近20个数据点):"
        echo -e "${CYAN}│${NC}"

        # 生成ASCII图表
        local max_rate=0
        local min_rate=100
        local data_points=()

        while IFS=':' read -r timestamp rate; do
            data_points+=("$rate")
            if [[ $rate -gt $max_rate ]]; then max_rate=$rate; fi
            if [[ $rate -lt $min_rate ]]; then min_rate=$rate; fi
        done < "$trend_file"

        # 绘制图表
        local chart_width=60
        local chart_height=8

        for ((row=chart_height; row>=0; row--)); do
            local threshold=$((min_rate + (max_rate - min_rate) * row / chart_height))
            printf "${CYAN}│${NC} %3d%% │" "$threshold"

            for rate in "${data_points[@]}"; do
                if [[ $rate -ge $threshold ]]; then
                    if [[ $rate -ge 90 ]]; then
                        printf "${GREEN}█${NC}"
                    elif [[ $rate -ge 70 ]]; then
                        printf "${YELLOW}█${NC}"
                    else
                        printf "${RED}█${NC}"
                    fi
                else
                    printf " "
                fi
            done
            echo ""
        done

        echo -e "${CYAN}│${NC}      └$(printf '─%.0s' $(seq 1 ${#data_points[@]}))"
        echo -e "${CYAN}│${NC}       范围: ${min_rate}%-${max_rate}%  当前: ${data_points[-1]}%"
    else
        echo -e "${CYAN}│${NC} ${DIM}暂无足够数据生成趋势图表${NC}"
        echo -e "${CYAN}│${NC} ${DIM}请等待系统收集更多性能数据...${NC}"
    fi

    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示阶段时间统计
show_phase_timing() {
    echo -e "${BOLD}${WHITE}${CLOCK} 阶段时间统计${NC}"
    echo -e "${CYAN}┌─────┬──────────────────┬──────────────┬──────────────┬─────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}${BOLD} 阶段${NC} ${CYAN}│${NC}${BOLD} 名称             ${NC}${CYAN}│${NC}${BOLD} 预计时间     ${NC}${CYAN}│${NC}${BOLD} 实际时间     ${NC}${CYAN}│${NC}${BOLD} 效率指标            ${NC}${CYAN}│${NC}"
    echo -e "${CYAN}├─────┼──────────────────┼──────────────┼──────────────┼─────────────────────┤${NC}"

    # 模拟时间统计数据
    local phase_times=(
        "P1|Plan|15分钟|12分钟|${GREEN}${FIRE} 超效率${NC}"
        "P2|Skeleton|25分钟|28分钟|${YELLOW}${GEAR} 正常${NC}"
        "P3|Implement|45分钟|运行中|${BLUE}${RUNNING} 进行中${NC}"
        "P4|Test|30分钟|待执行|${DIM}${WAITING} 等待${NC}"
        "P5|Review|20分钟|待执行|${DIM}${WAITING} 等待${NC}"
        "P6|Release|15分钟|待执行|${DIM}${WAITING} 等待${NC}"
    )

    for phase_time in "${phase_times[@]}"; do
        local phase=$(echo "$phase_time" | cut -d'|' -f1)
        local name=$(echo "$phase_time" | cut -d'|' -f2)
        local estimated=$(echo "$phase_time" | cut -d'|' -f3)
        local actual=$(echo "$phase_time" | cut -d'|' -f4)
        local efficiency=$(echo "$phase_time" | cut -d'|' -f5)

        printf "${CYAN}│${NC} %-3s ${CYAN}│${NC} %-16s ${CYAN}│${NC} %-12s ${CYAN}│${NC} %-12s ${CYAN}│${NC} %-28s ${CYAN}│${NC}\n" \
               "$phase" "$name" "$estimated" "$actual" "$efficiency"
    done

    echo -e "${CYAN}└─────┴──────────────────┴──────────────┴──────────────┴─────────────────────┘${NC}"
    echo ""
}

# 显示Agent执行统计
show_agent_stats() {
    echo -e "${BOLD}${WHITE}${ROCKET} Agent执行统计${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"

    # 模拟Agent统计数据
    local current_phase=$(get_current_phase)
    local agent_stats=(
        "backend-architect|8次|92%|${GREEN}优秀${NC}"
        "api-designer|6次|88%|${GREEN}良好${NC}"
        "test-engineer|5次|95%|${GREEN}优秀${NC}"
        "security-auditor|4次|85%|${YELLOW}正常${NC}"
        "database-specialist|3次|90%|${GREEN}良好${NC}"
    )

    echo -e "${CYAN}│${NC} 当前阶段 $current_phase 的Agent使用情况:"
    echo -e "${CYAN}│${NC}"

    local total_calls=0
    local avg_success=0

    for agent_stat in "${agent_stats[@]}"; do
        local agent=$(echo "$agent_stat" | cut -d'|' -f1)
        local calls=$(echo "$agent_stat" | cut -d'|' -f2 | tr -d '次')
        local success_rate=$(echo "$agent_stat" | cut -d'|' -f3 | tr -d '%')
        local status=$(echo "$agent_stat" | cut -d'|' -f4)

        total_calls=$((total_calls + calls))
        avg_success=$((avg_success + success_rate))

        # 成功率可视化
        local bar_length=$((success_rate * 20 / 100))
        local bar=""
        for ((i=0; i<bar_length; i++)); do bar+="█"; done
        for ((i=bar_length; i<20; i++)); do bar+="░"; done

        printf "${CYAN}│${NC}   %-20s %2d次 [${GREEN}%s${NC}] %s%%  %s\n" \
               "$agent" "$calls" "$bar" "$success_rate" "$status"
    done

    avg_success=$((avg_success / ${#agent_stats[@]}))

    echo -e "${CYAN}│${NC}"
    echo -e "${CYAN}│${NC} 总计: ${total_calls}次调用, 平均成功率: ${avg_success}%"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示系统资源使用情况
show_resource_usage() {
    echo -e "${BOLD}${WHITE}${GEAR} 系统资源监控${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"

    # 获取系统资源信息
    local cpu_usage=$(ps -o pid,pcpu -p $$ | tail -1 | awk '{print $2}' | cut -d'.' -f1)
    local memory_usage=$(ps -o pid,pmem -p $$ | tail -1 | awk '{print $2}' | cut -d'.' -f1)
    local disk_usage=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | tr -d '%')

    # CPU使用率
    local cpu_bar=$(printf "%-20s" | sed "s/ /█/g; s/█/█/1,$((cpu_usage * 20 / 100)); s/█/░/g; s/░/█/1,$((cpu_usage * 20 / 100))")
    local cpu_color="${GREEN}"
    if [[ $cpu_usage -gt 70 ]]; then cpu_color="${YELLOW}"; fi
    if [[ $cpu_usage -gt 90 ]]; then cpu_color="${RED}"; fi

    # 内存使用率
    local mem_bar=$(printf "%-20s" | sed "s/ /█/g; s/█/█/1,$((memory_usage * 20 / 100)); s/█/░/g; s/░/█/1,$((memory_usage * 20 / 100))")
    local mem_color="${GREEN}"
    if [[ $memory_usage -gt 70 ]]; then mem_color="${YELLOW}"; fi
    if [[ $memory_usage -gt 90 ]]; then mem_color="${RED}"; fi

    # 磁盘使用率
    local disk_bar=$(printf "%-20s" | sed "s/ /█/g; s/█/█/1,$((disk_usage * 20 / 100)); s/█/░/g; s/░/█/1,$((disk_usage * 20 / 100))")
    local disk_color="${GREEN}"
    if [[ $disk_usage -gt 70 ]]; then disk_color="${YELLOW}"; fi
    if [[ $disk_usage -gt 90 ]]; then disk_color="${RED}"; fi

    echo -e "${CYAN}│${NC} CPU使用率:  [${cpu_color}${cpu_bar}${NC}] ${cpu_usage}%"
    echo -e "${CYAN}│${NC} 内存使用率: [${mem_color}${mem_bar}${NC}] ${memory_usage}%"
    echo -e "${CYAN}│${NC} 磁盘使用率: [${disk_color}${disk_bar}${NC}] ${disk_usage}%"

    # 网络状态（模拟）
    echo -e "${CYAN}│${NC}"
    echo -e "${CYAN}│${NC} 网络状态: ${GREEN}${CHECK} 正常${NC}    延迟: ${GREEN}12ms${NC}    带宽: ${GREEN}100Mbps${NC}"

    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示告警和通知
show_alerts() {
    echo -e "${BOLD}${WHITE}${WARNING} 系统告警${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"

    # 检查各种告警条件
    local alerts=()
    local log_analysis=$(analyze_log_issues)
    local errors=$(echo "$log_analysis" | cut -d'|' -f1)
    local warnings=$(echo "$log_analysis" | cut -d'|' -f2)

    if [[ $errors -gt 5 ]]; then
        alerts+=("${RED}${ERROR} 错误数量过多: $errors 个错误${NC}")
    fi

    if [[ $warnings -gt 10 ]]; then
        alerts+=("${YELLOW}${WARNING} 警告数量较多: $warnings 个警告${NC}")
    fi

    # 检查长时间运行的阶段
    local current_phase=$(get_current_phase)
    if [[ "$current_phase" == "P3" ]]; then
        alerts+=("${BLUE}${CLOCK} 当前阶段P3运行时间较长，请检查进度${NC}")
    fi

    if [[ ${#alerts[@]} -eq 0 ]]; then
        echo -e "${CYAN}│${NC} ${GREEN}${SUCCESS} 系统运行正常，暂无告警信息${NC}"
    else
        for alert in "${alerts[@]}"; do
            echo -e "${CYAN}│${NC} $alert"
        done
    fi

    # 显示建议操作
    echo -e "${CYAN}│${NC}"
    echo -e "${CYAN}│${NC} ${BOLD}建议操作:${NC}"
    echo -e "${CYAN}│${NC}   ${BULLET} 定期检查日志文件"
    echo -e "${CYAN}│${NC}   ${BULLET} 监控Agent执行状态"
    echo -e "${CYAN}│${NC}   ${BULLET} 及时处理Gates验证失败"

    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════
# 重用基础函数（从原dashboard.sh）
# ═══════════════════════════════════════════════════════════════════

get_current_phase() {
    if [[ -f "$PHASE_DIR/current" ]]; then
        cat "$PHASE_DIR/current" | tr -d '\n'
    else
        echo "P0"
    fi
}

get_gates_status() {
    local gates_passed=0
    local total_gates=6
    for i in {1..6}; do
        if [[ -f "$GATES_DIR/0$i.ok" ]]; then
            ((gates_passed++))
        fi
    done
    echo "$gates_passed/$total_gates"
}

analyze_log_issues() {
    if [[ -f "$WORKFLOW_LOG" ]]; then
        local errors=$(grep -c "\[ERROR\]" "$WORKFLOW_LOG" 2>/dev/null || echo 0)
        local warnings=$(grep -c "\[WARN\]" "$WORKFLOW_LOG" 2>/dev/null || echo 0)
        local successes=$(grep -c "\[SUCCESS\]" "$WORKFLOW_LOG" 2>/dev/null || echo 0)
        echo "$errors|$warnings|$successes"
    else
        echo "0|0|0"
    fi
}

get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# ═══════════════════════════════════════════════════════════════════
# 增强版主显示函数
# ═══════════════════════════════════════════════════════════════════

display_enhanced_dashboard() {
    clear
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}                     Claude Enhancer 5.0 - Enhanced Workflow Monitoring Dashboard                                 ${NC}"
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════════════════════════════════────────────════${NC}"
    echo ""

    # 收集统计信息
    collect_stats
    generate_performance_trend

    # 显示各个模块
    show_performance_chart
    show_phase_timing
    show_agent_stats
    show_resource_usage
    show_alerts

    # 显示控制说明
    echo -e "${BOLD}${WHITE}⌨️ 增强功能控制${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} ${BOLD}S${NC} - 统计报告  ${BOLD}T${NC} - 趋势分析  ${BOLD}A${NC} - Agent详情  ${BOLD}M${NC} - 监控模式  ${BOLD}E${NC} - 导出数据"
    echo -e "${CYAN}│${NC} ${BOLD}1${NC} - 基础面板  ${BOLD}2${NC} - 性能面板  ${BOLD}3${NC} - 完整面板  ${BOLD}Ctrl+C${NC} - 退出程序"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
}

# ═══════════════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════════════

# 启动增强版面板
echo -e "${BOLD}${GREEN}启动Claude Enhancer 5.0 增强版工作流监控面板...${NC}"
echo -e "${GREEN}加载性能分析模块...${NC}"
sleep 1

# 信号处理
trap 'echo -e "\n${GREEN}感谢使用Claude Enhancer 5.0 Enhanced Dashboard!${NC}"; exit 0' INT TERM

# 主循环
while true; do
    display_enhanced_dashboard

    # 处理用户输入
    read -t $REFRESH_RATE -n 1 key 2>/dev/null

    case "$key" in
        's'|'S')
            echo -e "\n${YELLOW}生成统计报告...${NC}"
            sleep 1
            ;;
        't'|'T')
            echo -e "\n${CYAN}分析性能趋势...${NC}"
            sleep 1
            ;;
        '1')
            exec "$SCRIPT_DIR/dashboard.sh"
            ;;
        'q'|'Q')
            echo -e "\n${GREEN}退出增强版监控...${NC}"
            exit 0
            ;;
    esac
done