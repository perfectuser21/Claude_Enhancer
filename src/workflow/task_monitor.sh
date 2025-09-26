#!/bin/bash
# Claude Enhancer 5.0 - Task Monitor
# 任务监控工具，提供实时监控和性能分析
# Version: 1.0.0

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
readonly TASK_QUEUE_DIR="${PROJECT_ROOT}/.workflow/queue"
readonly TASK_LOGS_DIR="${PROJECT_ROOT}/.workflow/logs"
readonly TASK_STATE_DIR="${PROJECT_ROOT}/.workflow/state"

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[0;37m'
readonly NC='\033[0m' # No Color

# 实时监控界面
real_time_monitor() {
    local refresh_interval="${1:-2}"

    while true; do
        clear
        echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║                        Claude Enhancer 5.0 - 任务监控面板                         ║${NC}"
        echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
        echo

        # 系统资源状态
        show_system_resources

        echo -e "${BLUE}┌─────────────────────────── 任务队列状态 ────────────────────────────┐${NC}"

        # 队列统计
        local pending_count=$(ls "${TASK_QUEUE_DIR}/pending" 2>/dev/null | wc -l)
        local running_count=$(ls "${TASK_QUEUE_DIR}/running" 2>/dev/null | wc -l)
        local completed_count=$(ls "${TASK_QUEUE_DIR}/completed" 2>/dev/null | wc -l)
        local failed_count=$(ls "${TASK_QUEUE_DIR}/failed" 2>/dev/null | wc -l)

        printf "│ ${YELLOW}待执行:${NC} %-10s ${GREEN}运行中:${NC} %-10s ${BLUE}已完成:${NC} %-10s ${RED}失败:${NC} %-10s │\n" \
            "$pending_count" "$running_count" "$completed_count" "$failed_count"

        echo -e "${BLUE}├─────────────────────────── 运行中任务 ────────────────────────────┤${NC}"

        # 显示运行中的任务
        if [[ $running_count -gt 0 ]]; then
            for task_file in "${TASK_QUEUE_DIR}/running"/*.json; do
                [[ -f "$task_file" ]] || continue
                show_running_task_status "$task_file"
            done
        else
            printf "│ %-70s │\n" "  没有运行中的任务"
        fi

        echo -e "${BLUE}└─────────────────────────────────────────────────────────────────────┘${NC}"

        # 最近完成的任务
        echo
        echo -e "${GREEN}┌─────────────────────────── 最近完成 ────────────────────────────┐${NC}"
        show_recent_completed_tasks 5
        echo -e "${GREEN}└─────────────────────────────────────────────────────────────────────┘${NC}"

        # 错误任务
        if [[ $failed_count -gt 0 ]]; then
            echo
            echo -e "${RED}┌─────────────────────────── 失败任务 ────────────────────────────┐${NC}"
            show_failed_tasks 3
            echo -e "${RED}└─────────────────────────────────────────────────────────────────────┘${NC}"
        fi

        echo
        echo -e "${PURPLE}刷新间隔: ${refresh_interval}s | 按 Ctrl+C 退出${NC}"

        sleep "$refresh_interval"
    done
}

# 显示系统资源状态
show_system_resources() {
    # 获取系统信息
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}' | cut -d. -f1)
    local mem_info=$(free | grep Mem)
    local mem_total=$(echo "$mem_info" | awk '{print $2}')
    local mem_used=$(echo "$mem_info" | awk '{print $3}')
    local mem_usage=$(echo "$mem_used $mem_total" | awk '{printf "%.0f", ($1/$2)*100}')
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')

    echo -e "${WHITE}┌─────────────────────────── 系统资源 ────────────────────────────┐${NC}"

    # CPU状态条
    local cpu_bar=$(create_progress_bar "$cpu_usage" 50)
    local cpu_color=$GREEN
    [[ $cpu_usage -gt 70 ]] && cpu_color=$YELLOW
    [[ $cpu_usage -gt 85 ]] && cpu_color=$RED

    printf "│ ${WHITE}CPU:${NC} ${cpu_color}%3d%%${NC} │%s│ Load: %-6s │\n" \
        "$cpu_usage" "$cpu_bar" "$load_avg"

    # 内存状态条
    local mem_bar=$(create_progress_bar "$mem_usage" 50)
    local mem_color=$GREEN
    [[ $mem_usage -gt 75 ]] && mem_color=$YELLOW
    [[ $mem_usage -gt 85 ]] && mem_color=$RED

    printf "│ ${WHITE}MEM:${NC} ${mem_color}%3d%%${NC} │%s│ Free: %-6s │\n" \
        "$mem_usage" "$mem_bar" "$(echo "$(free -h | grep Mem | awk '{print $7}')")"

    echo -e "${WHITE}└─────────────────────────────────────────────────────────────────────┘${NC}"
    echo
}

# 创建进度条
create_progress_bar() {
    local percentage=$1
    local width=$2
    local filled=$(( percentage * width / 100 ))
    local empty=$(( width - filled ))

    local bar=""
    for ((i=1; i<=filled; i++)); do bar+="█"; done
    for ((i=1; i<=empty; i++)); do bar+="░"; done

    echo "$bar"
}

# 显示运行中任务状态
show_running_task_status() {
    local task_file="$1"
    local task_id=$(jq -r '.task_id' "$task_file")
    local task_name=$(jq -r '.task_name' "$task_file")
    local progress=$(jq -r '.progress // 0' "$task_file")
    local agents=$(jq -r '.agents | length' "$task_file")
    local started_at=$(jq -r '.started_at' "$task_file")

    # 计算运行时间
    local start_timestamp=$(date -d "$started_at" +%s 2>/dev/null || echo "0")
    local current_timestamp=$(date +%s)
    local duration=$((current_timestamp - start_timestamp))
    local duration_str=$(format_duration "$duration")

    # 进度条
    local progress_bar=$(create_progress_bar "$progress" 25)
    local progress_color=$YELLOW
    [[ $progress -gt 80 ]] && progress_color=$GREEN

    printf "│ ${WHITE}%-20s${NC} ${progress_color}%3d%%${NC} │%s│ %2dA %8s │\n" \
        "$(echo "$task_name" | cut -c1-20)" \
        "$progress" \
        "$progress_bar" \
        "$agents" \
        "$duration_str"

    # 显示Agent状态（如果有的话）
    show_agent_status "$task_id"
}

# 显示Agent状态
show_agent_status() {
    local task_id="$1"
    local agent_status_files=("${TASK_STATE_DIR}/agents/${task_id}_"*"_status.json")

    if [[ ${#agent_status_files[@]} -gt 0 && -f "${agent_status_files[0]}" ]]; then
        local agents_info=""
        local agent_count=0

        for status_file in "${agent_status_files[@]}"; do
            [[ -f "$status_file" ]] || continue

            local agent_name=$(jq -r '.agent' "$status_file" | cut -c1-8)
            local agent_progress=$(jq -r '.progress // 0' "$status_file")

            if [[ $agent_count -gt 0 ]]; then
                agents_info+=" "
            fi
            agents_info+="${agent_name}:${agent_progress}%"

            ((agent_count++))
            [[ $agent_count -ge 4 ]] && break  # 限制显示数量
        done

        if [[ -n "$agents_info" ]]; then
            printf "│ ${CYAN}  └─ Agents:${NC} %-55s │\n" "$agents_info"
        fi
    fi
}

# 显示最近完成的任务
show_recent_completed_tasks() {
    local limit="${1:-10}"
    local count=0

    # 按修改时间排序，最新的在前
    for task_file in $(ls -t "${TASK_QUEUE_DIR}/completed"/*.json 2>/dev/null | head -n "$limit"); do
        local task_name=$(jq -r '.task_name' "$task_file")
        local completed_at=$(jq -r '.completed_at' "$task_file")
        local agents=$(jq -r '.agents | length' "$task_file")

        local completed_time=$(date -d "$completed_at" +"%H:%M:%S" 2>/dev/null || echo "N/A")

        printf "│ ${GREEN}✓${NC} %-25s ${WHITE}%8s${NC} (%dA) %-20s │\n" \
            "$(echo "$task_name" | cut -c1-25)" \
            "$completed_time" \
            "$agents" \
            ""

        ((count++))
        [[ $count -ge "$limit" ]] && break
    done

    [[ $count -eq 0 ]] && printf "│ %-70s │\n" "  没有已完成的任务"
}

# 显示失败任务
show_failed_tasks() {
    local limit="${1:-5}"
    local count=0

    for task_file in $(ls -t "${TASK_QUEUE_DIR}/failed"/*.json 2>/dev/null | head -n "$limit"); do
        local task_name=$(jq -r '.task_name' "$task_file")
        local status=$(jq -r '.status' "$task_file")
        local completed_at=$(jq -r '.completed_at // .updated_at' "$task_file")

        local failed_time=$(date -d "$completed_at" +"%H:%M:%S" 2>/dev/null || echo "N/A")

        printf "│ ${RED}✗${NC} %-25s ${WHITE}%8s${NC} (${status}) %-15s │\n" \
            "$(echo "$task_name" | cut -c1-25)" \
            "$failed_time" \
            ""

        ((count++))
        [[ $count -ge "$limit" ]] && break
    done
}

# 格式化持续时间
format_duration() {
    local duration=$1
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))

    if [[ $hours -gt 0 ]]; then
        printf "%dh%02dm" "$hours" "$minutes"
    elif [[ $minutes -gt 0 ]]; then
        printf "%dm%02ds" "$minutes" "$seconds"
    else
        printf "%ds" "$seconds"
    fi
}

# 任务详细信息
show_task_details() {
    local task_id="$1"
    local task_file=""

    # 查找任务文件
    for dir in pending running completed failed; do
        local file="${TASK_QUEUE_DIR}/${dir}/${task_id}.json"
        if [[ -f "$file" ]]; then
            task_file="$file"
            break
        fi
    done

    if [[ -z "$task_file" ]]; then
        echo "任务未找到: $task_id"
        return 1
    fi

    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                               任务详细信息                                       ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo

    local task_name=$(jq -r '.task_name' "$task_file")
    local status=$(jq -r '.status' "$task_file")
    local progress=$(jq -r '.progress // 0' "$task_file")
    local created_at=$(jq -r '.created_at' "$task_file")
    local description=$(jq -r '.description // "无描述"' "$task_file")

    echo -e "${WHITE}任务ID:${NC}     $task_id"
    echo -e "${WHITE}任务名称:${NC}   $task_name"
    echo -e "${WHITE}状态:${NC}       $status"
    echo -e "${WHITE}进度:${NC}       ${progress}%"
    echo -e "${WHITE}创建时间:${NC}   $created_at"
    echo -e "${WHITE}描述:${NC}       $description"
    echo

    # 显示Agents
    echo -e "${BLUE}Agents:${NC}"
    jq -r '.agents[]' "$task_file" | while read -r agent; do
        echo "  - $agent"
    done
    echo

    # 显示依赖
    local dependencies=$(jq -r '.dependencies[]?' "$task_file" 2>/dev/null || echo "")
    if [[ -n "$dependencies" ]]; then
        echo -e "${YELLOW}依赖任务:${NC}"
        echo "$dependencies" | while read -r dep; do
            [[ -n "$dep" ]] && echo "  - $dep"
        done
        echo
    fi

    # 显示资源使用情况（如果有）
    local resource_usage=$(jq -r '.resource_usage // empty' "$task_file")
    if [[ -n "$resource_usage" && "$resource_usage" != "null" ]]; then
        echo -e "${GREEN}资源使用:${NC}"
        echo "$resource_usage" | jq -r 'to_entries[] | "  \(.key): \(.value)"'
        echo
    fi

    # 显示Agent结果（如果已完成）
    local agent_results=$(jq -r '.agent_results // empty' "$task_file")
    if [[ -n "$agent_results" && "$agent_results" != "null" && "$agent_results" != "[]" ]]; then
        echo -e "${PURPLE}Agent结果:${NC}"
        echo "$agent_results" | jq -r '.[] | "  \(.agent): \(.status) (\(.duration)s)"'
        echo
    fi
}

# 性能统计
show_performance_stats() {
    local time_period="${1:-24h}"

    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                            性能统计 (${time_period})                                    ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo

    # 计算时间范围
    local start_time
    case "$time_period" in
        "1h")  start_time=$(date -d "1 hour ago" +%s) ;;
        "24h") start_time=$(date -d "24 hours ago" +%s) ;;
        "7d")  start_time=$(date -d "7 days ago" +%s) ;;
        *)     start_time=$(date -d "24 hours ago" +%s) ;;
    esac

    # 统计完成的任务
    local total_completed=0
    local total_failed=0
    local total_duration=0
    local agent_usage=()

    for task_file in "${TASK_QUEUE_DIR}/completed"/*.json; do
        [[ -f "$task_file" ]] || continue

        local completed_at=$(jq -r '.completed_at' "$task_file")
        local completed_timestamp=$(date -d "$completed_at" +%s 2>/dev/null || echo "0")

        if [[ $completed_timestamp -ge $start_time ]]; then
            ((total_completed++))

            # 计算持续时间
            local started_at=$(jq -r '.started_at' "$task_file")
            local started_timestamp=$(date -d "$started_at" +%s 2>/dev/null || echo "0")
            local duration=$((completed_timestamp - started_timestamp))
            total_duration=$((total_duration + duration))

            # 统计Agent使用
            jq -r '.agents[]' "$task_file" | while read -r agent; do
                agent_usage["$agent"]=$((${agent_usage["$agent"]:-0} + 1))
            done
        fi
    done

    # 统计失败的任务
    for task_file in "${TASK_QUEUE_DIR}/failed"/*.json; do
        [[ -f "$task_file" ]] || continue

        local completed_at=$(jq -r '.completed_at // .updated_at' "$task_file")
        local completed_timestamp=$(date -d "$completed_at" +%s 2>/dev/null || echo "0")

        if [[ $completed_timestamp -ge $start_time ]]; then
            ((total_failed++))
        fi
    done

    # 显示统计结果
    local success_rate=0
    if (( total_completed + total_failed > 0 )); then
        success_rate=$(( (total_completed * 100) / (total_completed + total_failed) ))
    fi

    local avg_duration=0
    if (( total_completed > 0 )); then
        avg_duration=$(( total_duration / total_completed ))
    fi

    echo -e "${WHITE}任务统计:${NC}"
    echo "  完成任务: $total_completed"
    echo "  失败任务: $total_failed"
    echo "  成功率: ${success_rate}%"
    echo "  平均执行时间: $(format_duration $avg_duration)"
    echo

    echo -e "${WHITE}系统负载:${NC}"
    local current_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    echo "  当前负载: $current_load (核心数: $cpu_cores)"
    echo "  负载率: $(echo "$current_load $cpu_cores" | awk '{printf "%.1f%%", ($1/$2)*100}')"
    echo
}

# 日志查看器
view_logs() {
    local task_id="${1:-}"
    local lines="${2:-50}"

    if [[ -n "$task_id" ]]; then
        # 显示特定任务的日志
        echo -e "${CYAN}=== 任务日志: $task_id ===${NC}"

        # 任务主日志
        local main_log="${TASK_LOGS_DIR}/${task_id}.log"
        if [[ -f "$main_log" ]]; then
            echo -e "${WHITE}主日志:${NC}"
            tail -n "$lines" "$main_log"
            echo
        fi

        # Agent日志
        for agent_log in "${TASK_LOGS_DIR}/${task_id}_"*.log; do
            [[ -f "$agent_log" ]] || continue

            local agent_name=$(basename "$agent_log" .log | sed "s/${task_id}_//")
            echo -e "${BLUE}Agent日志 ($agent_name):${NC}"
            tail -n "$lines" "$agent_log"
            echo
        done
    else
        # 显示系统日志
        echo -e "${CYAN}=== 系统日志 ===${NC}"
        local system_log="${TASK_LOGS_DIR}/parallel_manager.log"
        if [[ -f "$system_log" ]]; then
            tail -n "$lines" "$system_log"
        else
            echo "系统日志文件不存在"
        fi
    fi
}

# 主函数
main() {
    case "${1:-}" in
        "monitor"|"")
            real_time_monitor "${2:-2}"
            ;;
        "details")
            if [[ -z "${2:-}" ]]; then
                echo "用法: $0 details <task_id>"
                exit 1
            fi
            show_task_details "$2"
            ;;
        "stats")
            show_performance_stats "${2:-24h}"
            ;;
        "logs")
            view_logs "${2:-}" "${3:-50}"
            ;;
        *)
            echo "用法: $0 {monitor|details|stats|logs}"
            echo
            echo "命令说明:"
            echo "  monitor [interval]     - 实时监控界面 (默认2秒刷新)"
            echo "  details <task_id>      - 显示任务详细信息"
            echo "  stats [period]         - 显示性能统计 (1h/24h/7d)"
            echo "  logs [task_id] [lines] - 查看日志"
            echo
            echo "示例:"
            echo "  $0 monitor             - 启动实时监控"
            echo "  $0 details task_123    - 显示task_123详情"
            echo "  $0 stats 7d           - 显示7天统计"
            echo "  $0 logs task_123 100   - 显示task_123最后100行日志"
            exit 1
            ;;
    esac
}

# 如果直接执行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi