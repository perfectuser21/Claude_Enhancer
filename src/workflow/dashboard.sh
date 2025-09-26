#!/bin/bash

# ═══════════════════════════════════════════════════════════════════
# Claude Enhancer 5.0 - Workflow Monitoring Dashboard
# 实时监控8-Phase工作流系统状态
# ═══════════════════════════════════════════════════════════════════

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# 特殊符号
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

# 项目路径
PROJECT_ROOT="/home/xx/dev/Claude Enhancer 5.0"
PHASE_DIR="$PROJECT_ROOT/.phase"
GATES_DIR="$PROJECT_ROOT/.gates"
WORKFLOW_DIR="$PROJECT_ROOT/.workflow"
WORKFLOW_LOG="$WORKFLOW_DIR/executor.log"

# 监控配置
REFRESH_RATE=2
DASHBOARD_WIDTH=120
LOG_LINES=15

# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════

# 清屏并设置标题
clear_screen() {
    clear
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}                            Claude Enhancer 5.0 - Workflow Monitoring Dashboard                                ${NC}"
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# 获取当前时间戳
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# 获取当前阶段
get_current_phase() {
    if [[ -f "$PHASE_DIR/current" ]]; then
        cat "$PHASE_DIR/current" | tr -d '\n'
    else
        echo "P0"
    fi
}

# 获取Gates状态
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

# 获取阶段进度百分比
get_phase_progress() {
    local current_phase=$(get_current_phase)
    case $current_phase in
        "P0") echo "0" ;;
        "P1") echo "17" ;;
        "P2") echo "33" ;;
        "P3") echo "50" ;;
        "P4") echo "67" ;;
        "P5") echo "83" ;;
        "P6") echo "100" ;;
        *) echo "0" ;;
    esac
}

# 绘制进度条
draw_progress_bar() {
    local percentage=$1
    local width=${2:-50}
    local filled=$((percentage * width / 100))
    local empty=$((width - filled))

    local bar=""
    for ((i=0; i<filled; i++)); do
        bar+="${PROGRESS}"
    done
    for ((i=0; i<empty; i++)); do
        bar+="${EMPTY}"
    done

    echo -e "${GREEN}${bar}${NC} ${percentage}%"
}

# 获取阶段名称和描述
get_phase_info() {
    local phase=$1
    case $phase in
        "P0") echo "Branch Creation|创建feature分支，准备开发环境" ;;
        "P1") echo "Plan|需求分析和任务规划" ;;
        "P2") echo "Skeleton|架构设计和骨架构建" ;;
        "P3") echo "Implement|功能实现和代码开发" ;;
        "P4") echo "Test|测试验证和质量保证" ;;
        "P5") echo "Review|代码审查和质量评估" ;;
        "P6") echo "Docs & Release|文档完善和发布部署" ;;
        *) echo "Unknown|未知阶段" ;;
    esac
}

# 检查并行任务状态（模拟）
get_parallel_tasks_status() {
    local current_phase=$(get_current_phase)
    local max_parallel=4

    case $current_phase in
        "P1") max_parallel=4 ;;
        "P2") max_parallel=6 ;;
        "P3") max_parallel=8 ;;
        "P4") max_parallel=6 ;;
        "P5") max_parallel=4 ;;
        "P6") max_parallel=2 ;;
    esac

    # 模拟并行任务状态
    local running=0
    local completed=0
    local failed=0

    # 根据当前时间生成模拟数据
    local timestamp=$(date +%s)
    local seed=$((timestamp % 10))

    case $seed in
        0|1|2) running=2; completed=$((max_parallel - 3)); failed=1 ;;
        3|4|5) running=1; completed=$((max_parallel - 1)); failed=0 ;;
        6|7) running=3; completed=$((max_parallel - 4)); failed=1 ;;
        8|9) running=0; completed=$max_parallel; failed=0 ;;
    esac

    echo "$running|$completed|$failed|$max_parallel"
}

# 获取最新的日志条目
get_recent_logs() {
    local lines=${1:-$LOG_LINES}
    if [[ -f "$WORKFLOW_LOG" ]]; then
        tail -n "$lines" "$WORKFLOW_LOG" 2>/dev/null || echo "暂无日志数据"
    else
        echo "日志文件不存在"
    fi
}

# 分析日志中的错误和警告
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

# ═══════════════════════════════════════════════════════════════════
# 显示模块
# ═══════════════════════════════════════════════════════════════════

# 显示系统状态概览
show_system_overview() {
    local current_phase=$(get_current_phase)
    local progress=$(get_phase_progress)
    local gates_status=$(get_gates_status)
    local phase_info=$(get_phase_info "$current_phase")
    local phase_name=$(echo "$phase_info" | cut -d'|' -f1)
    local phase_desc=$(echo "$phase_info" | cut -d'|' -f2)

    echo -e "${BOLD}${WHITE}📊 系统概览${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} 当前阶段: ${BOLD}${YELLOW}$current_phase - $phase_name${NC} ${DIM}($phase_desc)${NC}"
    echo -e "${CYAN}│${NC} 总进度:   $(draw_progress_bar $progress 40)"
    echo -e "${CYAN}│${NC} Gates状态: ${GREEN}$gates_status${NC} 已通过"
    echo -e "${CYAN}│${NC} 更新时间: ${WHITE}$(get_timestamp)${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示阶段详细状态
show_phase_details() {
    echo -e "${BOLD}${WHITE}🔄 阶段状态详情${NC}"
    echo -e "${CYAN}┌─────┬──────────────────┬──────────┬─────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}${BOLD} 阶段${NC} ${CYAN}│${NC}${BOLD} 名称             ${NC}${CYAN}│${NC}${BOLD} 状态     ${NC}${CYAN}│${NC}${BOLD} 描述                                     ${NC}${CYAN}│${NC}"
    echo -e "${CYAN}├─────┼──────────────────┼──────────┼─────────────────────────────────────────────┤${NC}"

    local current_phase=$(get_current_phase)

    for phase in P0 P1 P2 P3 P4 P5 P6; do
        local phase_info=$(get_phase_info "$phase")
        local phase_name=$(echo "$phase_info" | cut -d'|' -f1)
        local phase_desc=$(echo "$phase_info" | cut -d'|' -f2)

        # 截断描述以适应表格宽度
        if [[ ${#phase_desc} -gt 39 ]]; then
            phase_desc="${phase_desc:0:36}..."
        fi

        local status_color=""
        local status_icon=""
        local status_text=""

        if [[ "$phase" == "$current_phase" ]]; then
            status_color="${YELLOW}"
            status_icon="${RUNNING}"
            status_text="进行中"
        elif [[ -f "$GATES_DIR/${phase:1:1}.ok" ]] || [[ "$phase" < "$current_phase" ]]; then
            status_color="${GREEN}"
            status_icon="${SUCCESS}"
            status_text="已完成"
        else
            status_color="${DIM}"
            status_icon="${WAITING}"
            status_text="等待中"
        fi

        printf "${CYAN}│${NC} %-3s ${CYAN}│${NC} %-16s ${CYAN}│${NC} %s%-8s ${CYAN}│${NC} %-39s ${CYAN}│${NC}\n" \
               "$phase" "$phase_name" "$status_color$status_icon $status_text${NC}" "$phase_desc"
    done

    echo -e "${CYAN}└─────┴──────────────────┴──────────┴─────────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示并行任务状态
show_parallel_tasks() {
    local current_phase=$(get_current_phase)
    local task_status=$(get_parallel_tasks_status)
    local running=$(echo "$task_status" | cut -d'|' -f1)
    local completed=$(echo "$task_status" | cut -d'|' -f2)
    local failed=$(echo "$task_status" | cut -d'|' -f3)
    local max_parallel=$(echo "$task_status" | cut -d'|' -f4)

    echo -e "${BOLD}${WHITE}⚡ 并行任务状态 (阶段 $current_phase)${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} 最大并行数: ${BOLD}${WHITE}$max_parallel${NC} 个Agent"

    # 任务状态可视化
    local total_tasks=$((running + completed + failed))
    if [[ $total_tasks -gt 0 ]]; then
        echo -e "${CYAN}│${NC} 任务分布:"
        echo -e "${CYAN}│${NC}   ${GREEN}${CHECK} 已完成: $completed${NC}"
        echo -e "${CYAN}│${NC}   ${YELLOW}${RUNNING} 运行中: $running${NC}"
        if [[ $failed -gt 0 ]]; then
            echo -e "${CYAN}│${NC}   ${RED}${CROSS} 失败: $failed${NC}"
        fi

        # 任务状态进度条
        local completed_pct=$((completed * 100 / max_parallel))
        local running_pct=$((running * 100 / max_parallel))
        local failed_pct=$((failed * 100 / max_parallel))

        echo -e "${CYAN}│${NC}"
        echo -e "${CYAN}│${NC} 进度可视化:"
        local bar_width=60
        local completed_blocks=$((completed * bar_width / max_parallel))
        local running_blocks=$((running * bar_width / max_parallel))
        local failed_blocks=$((failed * bar_width / max_parallel))
        local empty_blocks=$((bar_width - completed_blocks - running_blocks - failed_blocks))

        local visual_bar="${GREEN}"
        for ((i=0; i<completed_blocks; i++)); do visual_bar+="█"; done
        visual_bar+="${YELLOW}"
        for ((i=0; i<running_blocks; i++)); do visual_bar+="█"; done
        visual_bar+="${RED}"
        for ((i=0; i<failed_blocks; i++)); do visual_bar+="█"; done
        visual_bar+="${DIM}"
        for ((i=0; i<empty_blocks; i++)); do visual_bar+="░"; done
        visual_bar+="${NC}"

        echo -e "${CYAN}│${NC} [$visual_bar] ($total_tasks/$max_parallel)"
    else
        echo -e "${CYAN}│${NC} ${DIM}当前阶段暂无并行任务${NC}"
    fi

    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示Gates验证结果
show_gates_validation() {
    echo -e "${BOLD}${WHITE}🛡️ Gates验证状态${NC}"
    echo -e "${CYAN}┌─────┬─────────────────────┬──────────┬─────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC}${BOLD} Gate${NC} ${CYAN}│${NC}${BOLD} 阶段                ${NC}${CYAN}│${NC}${BOLD} 状态     ${NC}${CYAN}│${NC}${BOLD} 描述                                 ${NC}${CYAN}│${NC}"
    echo -e "${CYAN}├─────┼─────────────────────┼──────────┼─────────────────────────────────────────┤${NC}"

    local gates_info=(
        "01|Plan|文档结构和任务规划验证"
        "02|Skeleton|架构骨架和接口定义验证"
        "03|Implement|功能实现和代码质量验证"
        "04|Test|测试覆盖和质量保证验证"
        "05|Review|代码审查和风险评估验证"
        "06|Release|文档完善和发布准备验证"
    )

    for gate_info in "${gates_info[@]}"; do
        local gate_num=$(echo "$gate_info" | cut -d'|' -f1)
        local gate_phase=$(echo "$gate_info" | cut -d'|' -f2)
        local gate_desc=$(echo "$gate_info" | cut -d'|' -f3)

        # 截断描述
        if [[ ${#gate_desc} -gt 37 ]]; then
            gate_desc="${gate_desc:0:34}..."
        fi

        local status_color=""
        local status_icon=""
        local status_text=""

        if [[ -f "$GATES_DIR/${gate_num}.ok" ]]; then
            status_color="${GREEN}"
            status_icon="${CHECK}"
            status_text="已通过"
        else
            status_color="${DIM}"
            status_icon="${WAITING}"
            status_text="等待中"
        fi

        printf "${CYAN}│${NC} G%-2s ${CYAN}│${NC} %-19s ${CYAN}│${NC} %s%-8s ${CYAN}│${NC} %-37s ${CYAN}│${NC}\n" \
               "$gate_num" "$gate_phase" "$status_color$status_icon $status_text${NC}" "$gate_desc"
    done

    echo -e "${CYAN}└─────┴─────────────────────┴──────────┴─────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示性能监控统计
show_performance_stats() {
    local log_analysis=$(analyze_log_issues)
    local errors=$(echo "$log_analysis" | cut -d'|' -f1)
    local warnings=$(echo "$log_analysis" | cut -d'|' -f2)
    local successes=$(echo "$log_analysis" | cut -d'|' -f3)

    echo -e "${BOLD}${WHITE}📈 性能统计${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} 操作统计:"
    echo -e "${CYAN}│${NC}   ${GREEN}${SUCCESS} 成功操作: ${BOLD}$successes${NC}"
    echo -e "${CYAN}│${NC}   ${YELLOW}${WARNING} 警告信息: ${BOLD}$warnings${NC}"
    echo -e "${CYAN}│${NC}   ${RED}${ERROR} 错误事件: ${BOLD}$errors${NC}"

    # 成功率计算
    local total_ops=$((successes + warnings + errors))
    if [[ $total_ops -gt 0 ]]; then
        local success_rate=$((successes * 100 / total_ops))
        echo -e "${CYAN}│${NC}"
        echo -e "${CYAN}│${NC} 成功率: $(draw_progress_bar $success_rate 30) (${success_rate}%)"
    fi

    # 系统健康度
    local health_score=100
    if [[ $errors -gt 5 ]]; then health_score=$((health_score - 30)); fi
    if [[ $warnings -gt 10 ]]; then health_score=$((health_score - 20)); fi

    local health_color="${GREEN}"
    local health_status="健康"
    if [[ $health_score -lt 70 ]]; then
        health_color="${YELLOW}"
        health_status="注意"
    fi
    if [[ $health_score -lt 50 ]]; then
        health_color="${RED}"
        health_status="警告"
    fi

    echo -e "${CYAN}│${NC} 系统健康度: ${health_color}${BOLD}$health_score% ($health_status)${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示实时日志
show_recent_logs() {
    echo -e "${BOLD}${WHITE}📋 实时日志 (最近${LOG_LINES}条)${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"

    local logs=$(get_recent_logs $LOG_LINES)

    if [[ "$logs" == "暂无日志数据" ]] || [[ "$logs" == "日志文件不存在" ]]; then
        echo -e "${CYAN}│${NC} ${DIM}$logs${NC}"
    else
        # 处理每行日志
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                # 添加颜色高亮
                local colored_line="$line"
                colored_line=$(echo "$colored_line" | sed "s/\[ERROR\]/${RED}[ERROR]${NC}/g")
                colored_line=$(echo "$colored_line" | sed "s/\[WARN\]/${YELLOW}[WARN]${NC}/g")
                colored_line=$(echo "$colored_line" | sed "s/\[SUCCESS\]/${GREEN}[SUCCESS]${NC}/g")
                colored_line=$(echo "$colored_line" | sed "s/\[INFO\]/${BLUE}[INFO]${NC}/g")

                # 截断过长的行
                if [[ ${#line} -gt 113 ]]; then
                    colored_line="${colored_line:0:110}..."
                fi

                echo -e "${CYAN}│${NC} $colored_line"
            fi
        done <<< "$logs"
    fi

    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# 显示控制说明
show_controls() {
    echo -e "${BOLD}${WHITE}⌨️ 控制说明${NC}"
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} ${BOLD}Ctrl+C${NC} - 退出监控  ${BOLD}R${NC} - 手动刷新  ${BOLD}L${NC} - 显示更多日志  ${BOLD}H${NC} - 帮助信息"
    echo -e "${CYAN}│${NC} 自动刷新间隔: ${YELLOW}${REFRESH_RATE}秒${NC}  监控文件: ${DIM}$WORKFLOW_LOG${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────────────────────────┘${NC}"
}

# ═══════════════════════════════════════════════════════════════════
# 主显示函数
# ═══════════════════════════════════════════════════════════════════

display_dashboard() {
    clear_screen
    show_system_overview
    show_phase_details
    show_parallel_tasks
    show_gates_validation
    show_performance_stats
    show_recent_logs
    show_controls
}

# ═══════════════════════════════════════════════════════════════════
# 交互处理
# ═══════════════════════════════════════════════════════════════════

handle_input() {
    local key
    read -t $REFRESH_RATE -n 1 key 2>/dev/null

    case "$key" in
        'r'|'R')
            echo -e "\n${GREEN}手动刷新...${NC}"
            sleep 0.5
            ;;
        'l'|'L')
            echo -e "\n${YELLOW}显示完整日志...${NC}"
            if [[ -f "$WORKFLOW_LOG" ]]; then
                less +G "$WORKFLOW_LOG"
            else
                echo -e "${RED}日志文件不存在${NC}"
                sleep 2
            fi
            ;;
        'h'|'H')
            show_help
            ;;
        'q'|'Q')
            echo -e "\n${GREEN}退出监控...${NC}"
            exit 0
            ;;
    esac
}

# 显示帮助信息
show_help() {
    clear
    echo -e "${BOLD}${CYAN}Claude Enhancer 5.0 - Workflow Dashboard 帮助${NC}\n"

    echo -e "${BOLD}基本信息:${NC}"
    echo -e "  这是Claude Enhancer 5.0的8-Phase工作流监控面板"
    echo -e "  实时显示当前开发阶段、Gates验证状态、并行任务执行情况\n"

    echo -e "${BOLD}阶段说明:${NC}"
    echo -e "  P0 - Branch Creation: 分支创建和环境准备"
    echo -e "  P1 - Plan: 需求分析和任务规划"
    echo -e "  P2 - Skeleton: 架构设计和骨架构建"
    echo -e "  P3 - Implement: 功能实现和代码开发"
    echo -e "  P4 - Test: 测试验证和质量保证"
    echo -e "  P5 - Review: 代码审查和质量评估"
    echo -e "  P6 - Docs & Release: 文档完善和发布部署\n"

    echo -e "${BOLD}交互操作:${NC}"
    echo -e "  ${BOLD}R${NC} - 立即刷新数据"
    echo -e "  ${BOLD}L${NC} - 查看完整日志"
    echo -e "  ${BOLD}H${NC} - 显示帮助信息"
    echo -e "  ${BOLD}Q${NC} - 退出监控程序"
    echo -e "  ${BOLD}Ctrl+C${NC} - 强制退出\n"

    echo -e "${BOLD}监控文件:${NC}"
    echo -e "  阶段状态: $PHASE_DIR/current"
    echo -e "  Gates状态: $GATES_DIR/"
    echo -e "  系统日志: $WORKFLOW_LOG\n"

    echo -e "${DIM}按任意键返回监控面板...${NC}"
    read -n 1
}

# ═══════════════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════════════

# 信号处理
trap 'echo -e "\n${GREEN}感谢使用Claude Enhancer 5.0 Workflow Dashboard!${NC}"; exit 0' INT TERM

# 启动信息
echo -e "${BOLD}${GREEN}启动Claude Enhancer 5.0 工作流监控面板...${NC}"
sleep 1

# 检查必要目录和文件
if [[ ! -d "$PROJECT_ROOT" ]]; then
    echo -e "${RED}错误: 项目根目录不存在: $PROJECT_ROOT${NC}"
    exit 1
fi

# 创建必要目录
mkdir -p "$PHASE_DIR" "$GATES_DIR" "$WORKFLOW_DIR"

# 主循环
while true; do
    display_dashboard
    handle_input
done