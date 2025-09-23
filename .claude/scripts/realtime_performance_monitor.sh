#!/bin/bash
# Claude Enhancer 实时性能监控系统 v3.0
# 实时监控系统资源、清理性能、Hook执行等

set -e

# ==================== 配置区 ====================
MONITOR_INTERVAL=0.1  # 100ms 采样间隔
DASHBOARD_REFRESH=1   # 1秒 仪表板刷新
MAX_HISTORY=1000      # 最大历史记录数
PERFORMANCE_LOG="/dev/shm/perfect21_realtime_perf.log"
DASHBOARD_CACHE="/dev/shm/perfect21_dashboard_cache"

# 系统配置
CORES=$(nproc)
MEMORY_TOTAL=$(free -m | awk '/^Mem:/{print $2}')

# 颜色配置
readonly C_RED='\033[0;31m'
readonly C_GREEN='\033[0;32m'
readonly C_YELLOW='\033[1;33m'
readonly C_BLUE='\033[0;34m'
readonly C_CYAN='\033[0;36m'
readonly C_MAGENTA='\033[0;35m'
readonly C_BOLD='\033[1m'
readonly C_RESET='\033[0m'

# ==================== 数据收集系统 ====================
declare -a CPU_HISTORY
declare -a MEMORY_HISTORY
declare -a CLEANUP_TIMES
declare -a HOOK_TIMES

# 实时数据采集器
collect_system_metrics() {
    local timestamp=$(date +%s.%N)

    # CPU使用率 (通过/proc/stat计算)
    local cpu_usage
    if [[ -r /proc/stat ]]; then
        local cpu_info=$(head -1 /proc/stat | awk '{print ($2+$3+$4+$5+$6+$7+$8+$9+$10+$11), ($5+$6)}')
        local total=$(echo $cpu_info | cut -d' ' -f1)
        local idle=$(echo $cpu_info | cut -d' ' -f2)
        cpu_usage=$(echo "scale=1; (100 - ($idle * 100 / $total))" | bc 2>/dev/null || echo "0")
    else
        cpu_usage="0"
    fi

    # 内存使用率
    local memory_info=$(free | awk '/^Mem:/{printf "%.1f", ($3/$2)*100}')

    # I/O统计
    local io_usage="0"
    if [[ -r /proc/diskstats ]]; then
        local io_total=$(awk '{sum+=$4+$8} END {print sum}' /proc/diskstats 2>/dev/null || echo "0")
        io_usage=$(echo "scale=1; $io_total / 1000" | bc 2>/dev/null || echo "0")
    fi

    # 网络使用 (简化)
    local network_rx=0
    local network_tx=0
    if [[ -r /proc/net/dev ]]; then
        local net_info=$(awk '/eth0|ens|wlan/{rx+=$2; tx+=$10} END {print rx, tx}' /proc/net/dev 2>/dev/null || echo "0 0")
        network_rx=$(echo $net_info | cut -d' ' -f1)
        network_tx=$(echo $net_info | cut -d' ' -f2)
    fi

    # 记录到历史
    CPU_HISTORY+=($cpu_usage)
    MEMORY_HISTORY+=($memory_info)

    # 限制历史记录长度
    if [[ ${#CPU_HISTORY[@]} -gt $MAX_HISTORY ]]; then
        CPU_HISTORY=("${CPU_HISTORY[@]:1}")
        MEMORY_HISTORY=("${MEMORY_HISTORY[@]:1}")
    fi

    # 输出当前指标
    echo "$timestamp,$cpu_usage,$memory_info,$io_usage,$network_rx,$network_tx"
}

# ==================== 清理性能监控 ====================
monitor_cleanup_performance() {
    local cleanup_script="$1"
    local start_time=$(date +%s.%N)

    echo "📊 开始监控清理性能: $cleanup_script"

    # 后台监控系统资源
    {
        while [[ -f "/tmp/cleanup_running" ]]; do
            collect_system_metrics >> "$PERFORMANCE_LOG"
            sleep $MONITOR_INTERVAL
        done
    } &
    local monitor_pid=$!

    # 执行清理脚本
    touch "/tmp/cleanup_running"
    local cleanup_output
    local cleanup_exit_code

    if timeout 30s bash "$cleanup_script" > "/tmp/cleanup_output.txt" 2>&1; then
        cleanup_exit_code=0
    else
        cleanup_exit_code=$?
    fi

    rm -f "/tmp/cleanup_running"
    kill $monitor_pid 2>/dev/null || true

    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)

    # 分析性能数据
    analyze_performance_data "$duration" "$cleanup_exit_code"

    CLEANUP_TIMES+=($duration)
}

# ==================== Hook执行监控 ====================
monitor_hook_execution() {
    local hook_name="$1"
    local hook_script="$2"
    local start_time=$(date +%s.%N)

    echo "🔗 监控Hook执行: $hook_name"

    # 执行Hook并监控
    local hook_output
    local hook_exit_code

    if timeout 10s bash "$hook_script" > "/tmp/hook_output_$hook_name.txt" 2>&1; then
        hook_exit_code=0
    else
        hook_exit_code=$?
    fi

    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)

    HOOK_TIMES+=("$hook_name:$duration")

    # 记录Hook性能
    echo "$(date +%s.%N),$hook_name,$duration,$hook_exit_code" >> "/dev/shm/hook_performance.log"

    echo "   ⏱️ $hook_name: ${duration}s (exit: $hook_exit_code)"
}

# ==================== 性能分析器 ====================
analyze_performance_data() {
    local total_duration="$1"
    local exit_code="$2"

    if [[ ! -f "$PERFORMANCE_LOG" ]]; then
        echo "⚠️ 无性能数据可分析"
        return
    fi

    # 计算资源使用统计
    local cpu_avg=$(awk -F, '{sum+=$2; count++} END {print sum/count}' "$PERFORMANCE_LOG")
    local cpu_max=$(awk -F, 'BEGIN{max=0} {if($2>max) max=$2} END {print max}' "$PERFORMANCE_LOG")
    local memory_avg=$(awk -F, '{sum+=$3; count++} END {print sum/count}' "$PERFORMANCE_LOG")
    local memory_max=$(awk -F, 'BEGIN{max=0} {if($3>max) max=$3} END {print max}' "$PERFORMANCE_LOG")

    echo ""
    echo "📈 性能分析结果:"
    echo "   ⏱️  总执行时间: ${total_duration}s"
    echo "   💻 CPU平均使用: ${cpu_avg}% (峰值: ${cpu_max}%)"
    echo "   💾 内存平均使用: ${memory_avg}% (峰值: ${memory_max}%)"
    echo "   🎯 执行状态: $([ $exit_code -eq 0 ] && echo "✅ 成功" || echo "❌ 失败 ($exit_code)")"

    # 性能评级
    local performance_score=$(echo "scale=0; (100 - $cpu_avg) * (100 - $memory_avg) / 100" | bc)
    local performance_grade
    if [[ $performance_score -gt 80 ]]; then
        performance_grade="${C_GREEN}A+ 优秀${C_RESET}"
    elif [[ $performance_score -gt 60 ]]; then
        performance_grade="${C_BLUE}B 良好${C_RESET}"
    elif [[ $performance_score -gt 40 ]]; then
        performance_grade="${C_YELLOW}C 一般${C_RESET}"
    else
        performance_grade="${C_RED}D 需优化${C_RESET}"
    fi

    echo -e "   📊 性能评级: $performance_grade (${performance_score}分)"
}

# ==================== 实时仪表板 ====================
generate_realtime_dashboard() {
    clear
    echo -e "${C_BOLD}${C_CYAN}┌─────────────────────────────────────────────────────────────────┐${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}│              Claude Enhancer 实时性能仪表板 v3.0                │${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}└─────────────────────────────────────────────────────────────────┘${C_RESET}"

    local current_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${C_BOLD}🕐 时间: $current_time${C_RESET}"
    echo ""

    # 系统概览
    echo -e "${C_BOLD}🖥️  系统概览${C_RESET}"
    echo "────────────────────────────────────────"

    # 当前资源使用
    local current_metrics=$(collect_system_metrics | tail -1)
    local cpu_current=$(echo $current_metrics | cut -d, -f2)
    local memory_current=$(echo $current_metrics | cut -d, -f3)

    # CPU状态条
    local cpu_bar=$(generate_progress_bar "$cpu_current" 100)
    echo -e "💻 CPU使用率: ${cpu_bar} ${cpu_current}%"

    # 内存状态条
    local memory_bar=$(generate_progress_bar "$memory_current" 100)
    echo -e "💾 内存使用率: ${memory_bar} ${memory_current}%"

    # 核心信息
    echo "🔧 CPU核心数: $CORES | 总内存: ${MEMORY_TOTAL}MB"
    echo ""

    # 清理性能历史
    if [[ ${#CLEANUP_TIMES[@]} -gt 0 ]]; then
        echo -e "${C_BOLD}🧹 清理性能历史${C_RESET}"
        echo "────────────────────────────────────────"

        local recent_cleanups=("${CLEANUP_TIMES[@]: -5}")  # 最近5次
        for i in "${!recent_cleanups[@]}"; do
            local duration="${recent_cleanups[$i]}"
            local duration_ms=$(echo "$duration * 1000" | bc | cut -d. -f1)
            echo "   🚀 清理 $((i+1)): ${duration_ms}ms"
        done

        # 计算平均性能
        local avg_cleanup=$(echo "${CLEANUP_TIMES[@]}" | tr ' ' '\n' | awk '{sum+=$1; count++} END {print sum/count}')
        local avg_cleanup_ms=$(echo "$avg_cleanup * 1000" | bc | cut -d. -f1)
        echo "   📊 平均耗时: ${avg_cleanup_ms}ms"
        echo ""
    fi

    # Hook性能
    if [[ ${#HOOK_TIMES[@]} -gt 0 ]]; then
        echo -e "${C_BOLD}🔗 Hook执行性能${C_RESET}"
        echo "────────────────────────────────────────"

        local recent_hooks=("${HOOK_TIMES[@]: -3}")  # 最近3个Hook
        for hook_info in "${recent_hooks[@]}"; do
            local hook_name=$(echo "$hook_info" | cut -d: -f1)
            local hook_duration=$(echo "$hook_info" | cut -d: -f2)
            local hook_duration_ms=$(echo "$hook_duration * 1000" | bc | cut -d. -f1)
            echo "   ⚡ $hook_name: ${hook_duration_ms}ms"
        done
        echo ""
    fi

    # 性能趋势
    echo -e "${C_BOLD}📈 性能趋势${C_RESET}"
    echo "────────────────────────────────────────"

    # 简化的图表 (最近10个数据点)
    if [[ ${#CPU_HISTORY[@]} -gt 0 ]]; then
        local recent_cpu=("${CPU_HISTORY[@]: -10}")
        echo -n "CPU:  "
        for cpu_val in "${recent_cpu[@]}"; do
            if (( $(echo "$cpu_val > 80" | bc -l) )); then
                echo -ne "${C_RED}█${C_RESET}"
            elif (( $(echo "$cpu_val > 50" | bc -l) )); then
                echo -ne "${C_YELLOW}█${C_RESET}"
            else
                echo -ne "${C_GREEN}█${C_RESET}"
            fi
        done
        echo ""

        local recent_memory=("${MEMORY_HISTORY[@]: -10}")
        echo -n "内存: "
        for mem_val in "${recent_memory[@]}"; do
            if (( $(echo "$mem_val > 80" | bc -l) )); then
                echo -ne "${C_RED}█${C_RESET}"
            elif (( $(echo "$mem_val > 50" | bc -l) )); then
                echo -ne "${C_YELLOW}█${C_RESET}"
            else
                echo -ne "${C_GREEN}█${C_RESET}"
            fi
        done
        echo ""
    fi

    echo ""
    echo -e "${C_BOLD}${C_CYAN}按 Ctrl+C 退出监控${C_RESET}"
}

# ==================== 辅助函数 ====================
generate_progress_bar() {
    local value="$1"
    local max_value="$2"
    local bar_length=20

    local progress=$(echo "scale=0; $value * $bar_length / $max_value" | bc)
    local filled_length=$progress
    local empty_length=$((bar_length - filled_length))

    local bar=""
    for ((i=0; i<filled_length; i++)); do
        if [[ $value -gt 80 ]]; then
            bar+="${C_RED}█${C_RESET}"
        elif [[ $value -gt 50 ]]; then
            bar+="${C_YELLOW}█${C_RESET}"
        else
            bar+="${C_GREEN}█${C_RESET}"
        fi
    done

    for ((i=0; i<empty_length; i++)); do
        bar+="░"
    done

    echo "[$bar]"
}

# ==================== 主监控函数 ====================
start_realtime_monitoring() {
    echo "🚀 启动实时性能监控..."

    # 清理旧的日志
    > "$PERFORMANCE_LOG"

    # 设置陷阱处理Ctrl+C
    trap 'echo -e "\n🛑 监控停止"; exit 0' INT

    while true; do
        generate_realtime_dashboard
        sleep $DASHBOARD_REFRESH
    done
}

monitor_cleanup_script() {
    local script_path="$1"

    if [[ ! -f "$script_path" ]]; then
        echo "❌ 清理脚本不存在: $script_path"
        return 1
    fi

    echo "🔍 开始监控清理脚本: $script_path"
    monitor_cleanup_performance "$script_path"
}

monitor_all_hooks() {
    local hooks_dir="$1"

    if [[ ! -d "$hooks_dir" ]]; then
        echo "❌ Hook目录不存在: $hooks_dir"
        return 1
    fi

    echo "🔗 监控所有Hook执行..."

    for hook_file in "$hooks_dir"/*.sh; do
        if [[ -f "$hook_file" && -x "$hook_file" ]]; then
            local hook_name=$(basename "$hook_file" .sh)
            monitor_hook_execution "$hook_name" "$hook_file"
        fi
    done
}

# ==================== 性能基准测试 ====================
run_performance_benchmark() {
    local iterations="${1:-10}"
    local cleanup_script="${2:-.claude/scripts/hyper_performance_cleanup.sh}"

    echo "🏃 运行性能基准测试 ($iterations 次迭代)..."

    if [[ ! -f "$cleanup_script" ]]; then
        echo "❌ 清理脚本不存在: $cleanup_script"
        return 1
    fi

    local total_time=0
    local times=()

    for ((i=1; i<=iterations; i++)); do
        echo "   🔄 迭代 $i/$iterations"

        local start_time=$(date +%s.%N)
        bash "$cleanup_script" &>/dev/null
        local end_time=$(date +%s.%N)

        local duration=$(echo "$end_time - $start_time" | bc)
        times+=($duration)
        total_time=$(echo "$total_time + $duration" | bc)

        # 显示进度
        local progress=$((i * 100 / iterations))
        echo "      Progress: $progress% (${duration}s)"
    done

    # 计算统计信息
    local avg_time=$(echo "$total_time / $iterations" | bc -l)
    local min_time=$(printf '%s\n' "${times[@]}" | sort -n | head -1)
    local max_time=$(printf '%s\n' "${times[@]}" | sort -n | tail -1)

    echo ""
    echo "📊 基准测试结果:"
    echo "   🔢 迭代次数: $iterations"
    echo "   ⏱️  平均时间: $(echo "scale=3; $avg_time" | bc)s"
    echo "   ⚡ 最快时间: ${min_time}s"
    echo "   🐌 最慢时间: ${max_time}s"
    echo "   🏆 吞吐量: $(echo "scale=1; $iterations / $total_time" | bc) 次/秒"
}

# ==================== 主函数 ====================
main() {
    case "${1:-dashboard}" in
        "dashboard"|"monitor")
            start_realtime_monitoring
            ;;
        "cleanup")
            local script_path="${2:-.claude/scripts/hyper_performance_cleanup.sh}"
            monitor_cleanup_script "$script_path"
            ;;
        "hooks")
            local hooks_dir="${2:-.claude/hooks}"
            monitor_all_hooks "$hooks_dir"
            ;;
        "benchmark")
            local iterations="${2:-10}"
            local script="${3:-.claude/scripts/hyper_performance_cleanup.sh}"
            run_performance_benchmark "$iterations" "$script"
            ;;
        "help"|"-h"|"--help")
            echo "Claude Enhancer 实时性能监控 v3.0"
            echo ""
            echo "用法: $0 <command> [options]"
            echo ""
            echo "命令:"
            echo "  dashboard               - 启动实时监控仪表板 (默认)"
            echo "  cleanup <script>        - 监控清理脚本执行"
            echo "  hooks <dir>            - 监控Hook目录执行"
            echo "  benchmark <n> <script> - 运行性能基准测试"
            echo "  help                   - 显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 dashboard                                    # 启动实时监控"
            echo "  $0 cleanup .claude/scripts/cleanup.sh          # 监控清理脚本"
            echo "  $0 benchmark 20                                # 运行20次基准测试"
            ;;
        *)
            echo "❌ 未知命令: $1"
            echo "使用 '$0 help' 查看帮助信息"
            exit 1
            ;;
    esac
}

# 检查依赖
if ! command -v bc &> /dev/null; then
    echo "❌ 需要安装 bc: sudo apt-get install bc"
    exit 1
fi

# 创建缓存目录
mkdir -p "$(dirname "$PERFORMANCE_LOG")"
mkdir -p "$(dirname "$DASHBOARD_CACHE")"

# 执行主函数
main "$@"